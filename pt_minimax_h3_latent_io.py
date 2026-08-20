import os
import json
import torch
import hashlib
import folder_paths
import safetensors.torch
from datetime import datetime

# ==========================================
# 辅助函数：健壮地重建 MiniMax H3 Nested Tensor
# ==========================================
def _rebuild_h3_nested_tensor(video_tensor: torch.Tensor, audio_tensor: torch.Tensor):
    try:
        import comfy.nested_tensor
        return comfy.nested_tensor.NestedTensor((video_tensor, audio_tensor))
    except Exception:
        pass

    class _FallbackNestedTensor:
        def __init__(self, tensors):
            self.tensors = tensors
            self.is_nested = True
        
        def unbind(self):
            return self.tensors
        
        def __getitem__(self, idx):
            return self.tensors[idx]
            
        @property
        def shape(self):
            return (self.tensors[0].shape[0],) 

    return _FallbackNestedTensor((video_tensor.contiguous(), audio_tensor.contiguous()))


# ==========================================
# 1. 保存节点
# ==========================================
class PT_MinimaxH3LatentSaver:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "latent": ("LATENT",),
                "filename_prefix": ("STRING", {"default": "minimax_h3_av", "tooltip": "文件名前缀"}),
                "save_directory": (["output", "input", "temp"], {"default": "input", "tooltip": "推荐选 input，方便后续直接拖拽加载"}),
            },
            "hidden": {"prompt": "PROMPT", "extra_pnginfo": "EXTRA_PNGINFO"}
        }

    RETURN_TYPES = ("LATENT", "STRING")
    RETURN_NAMES = ("latent_passthrough", "saved_path")
    FUNCTION = "save_h3_latent"
    OUTPUT_NODE = True
    CATEGORY = "PT/MiniMax H3"

    def save_h3_latent(self, latent, filename_prefix, save_directory, prompt=None, extra_pnginfo=None):
        if not isinstance(latent, dict) or "samples" not in latent:
            raise ValueError("输入必须是标准的 ComfyUI LATENT 字典格式。")
        
        samples = latent["samples"]
        is_nested = getattr(samples, "is_nested", False)
        output_data = {}
        metadata = {"model_type": "MiniMax H3"}

        if is_nested:
            streams = tuple(samples.unbind())
            if len(streams) != 2:
                raise ValueError("Nested Tensor 必须包含恰好两个流 (视频和音频)。")
            
            video_tensor, audio_tensor = streams
            
            if video_tensor.ndim != 5 or video_tensor.shape[1] != 24:
                raise ValueError(f"视频流形状异常，预期 [B, 24, Tv, H, W]，实际: {video_tensor.shape}")
            if audio_tensor.ndim != 4 or audio_tensor.shape[1] != 32 or audio_tensor.shape[2] != 2:
                raise ValueError(f"音频流形状异常，预期 [B, 32, 2, Ta]，实际: {audio_tensor.shape}")

            output_data["minimax_h3_video"] = video_tensor.contiguous()
            output_data["minimax_h3_audio"] = audio_tensor.contiguous()
            output_data["format_flag"] = torch.tensor([1.0])
            
            metadata["format"] = "nested_av"
            metadata["video_steps"] = str(int(video_tensor.shape[2]))
            metadata["audio_steps"] = str(int(audio_tensor.shape[3]))
        else:
            raise ValueError("此节点专为包含音视频的 MiniMax H3 Nested Latent 设计。")

        if save_directory == "output": base_dir = folder_paths.get_output_directory()
        elif save_directory == "input": base_dir = folder_paths.get_input_directory()
        else: base_dir = folder_paths.get_temp_directory()
        os.makedirs(base_dir, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_prefix = "".join(c for c in filename_prefix if c.isalnum() or c in ('-', '_', ' ', '\u4e00-\u9fff')).rstrip()
        if not safe_prefix: safe_prefix = "minimax_h3_av"
            
        filename = f"{safe_prefix}_{timestamp}.latent"
        full_path = os.path.join(base_dir, filename)

        if prompt is not None: metadata["prompt"] = json.dumps(prompt)
        if extra_pnginfo is not None:
            for key, value in extra_pnginfo.items():
                metadata[key] = json.dumps(value)

        safetensors.torch.save_file(output_data, full_path, metadata=metadata)
        print(f"[PT_Save H3] 💾 已保存至: {full_path}")

        return {"ui": {"text": [full_path]}, "result": (latent, full_path)}


# ==========================================
# 2. 加载节点 (配合前端 JS 使用)
# ==========================================
class PT_MinimaxH3LatentLoader:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                # 改为 STRING 类型，前端 JS 会直接修改这个 widget 的值
                "latent_file": ("STRING", {"default": "", "multiline": False, "tooltip": "点击节点上的按钮上传，或直接拖拽 .latent 文件到节点上"}),
            }
        }

    RETURN_TYPES = ("LATENT",)
    RETURN_NAMES = ("latent",)
    FUNCTION = "load_h3_latent"
    CATEGORY = "PT/MiniMax H3"

    def _resolve_path(self, file_path):
        if not file_path or file_path.strip() == "":
            return None
            
        # 1. 尝试 ComfyUI 标准解析 (处理 input/output/temp 目录及 subfolder)
        try:
            resolved = folder_paths.get_annotated_filepath(file_path)
            if os.path.exists(resolved):
                return resolved
        except Exception:
            pass
            
        # 2. 尝试作为绝对路径或相对路径
        if os.path.exists(file_path):
            return os.path.abspath(file_path)
            
        # 3. 尝试在 input 目录中查找
        input_dir = folder_paths.get_input_directory()
        input_path = os.path.join(input_dir, file_path)
        if os.path.exists(input_path):
            return input_path
            
        return None

    def load_h3_latent(self, latent_file):
        if not latent_file or not latent_file.strip():
            raise ValueError("请先通过节点上的按钮上传 .latent 文件，或拖拽文件到节点上。")
            
        latent_path = self._resolve_path(latent_file)
        if not latent_path:
            raise FileNotFoundError(f"找不到文件: {latent_file}")

        try:
            data = safetensors.torch.load_file(latent_path, device="cpu")
        except Exception as e:
            raise RuntimeError(f"加载 .latent 文件失败: {e}")

        format_flag = data.get("format_flag", None)
        if format_flag is None or float(format_flag.item()) != 1.0:
            raise ValueError("此文件不是由 PT_MinimaxH3LatentSaver 保存的完整音视频 Latent。")

        if "minimax_h3_video" not in data or "minimax_h3_audio" not in data:
            raise ValueError("文件损坏：缺少必要的视频或音频张量。")

        video_tensor = data["minimax_h3_video"]
        audio_tensor = data["minimax_h3_audio"]

        nested_samples = _rebuild_h3_nested_tensor(video_tensor, audio_tensor)
        print(f"[PT_Load H3] ✅ 成功重建 Nested Latent: 视频 {tuple(video_tensor.shape)}, 音频 {tuple(audio_tensor.shape)}")

        return ({"samples": nested_samples},)

    @classmethod
    def IS_CHANGED(cls, latent_file):
        if not latent_file: return ""
        input_dir = folder_paths.get_input_directory()
        possible_paths = [
            folder_paths.get_annotated_filepath(latent_file) if latent_file else "",
            os.path.abspath(latent_file),
            os.path.join(input_dir, latent_file)
        ]
        for p in possible_paths:
            if p and os.path.exists(p):
                m = hashlib.sha256()
                with open(p, 'rb') as f: m.update(f.read())
                return m.digest().hex()
        return ""

    @classmethod
    def VALIDATE_INPUTS(cls, latent_file):
        if not latent_file or not latent_file.strip():
            return "请上传或拖拽 .latent 文件到节点上。"
        return True


# ==========================================
# 3. 节点注册
# ==========================================
NODE_CLASS_MAPPINGS = {
    "PT_MinimaxH3LatentSaver": PT_MinimaxH3LatentSaver,
    "PT_MinimaxH3LatentLoader": PT_MinimaxH3LatentLoader,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "PT_MinimaxH3LatentSaver": "💾 PT Save Latent (MiniMax H3 AV)",
    "PT_MinimaxH3LatentLoader": "📂 PT Load Latent (MiniMax H3 AV)",
}