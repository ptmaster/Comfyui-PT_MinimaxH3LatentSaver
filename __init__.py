from .pt_minimax_h3_latent_io import NODE_CLASS_MAPPINGS, NODE_DISPLAY_NAME_MAPPINGS

# 关键：指定 JS 文件所在的目录，ComfyUI 启动时会自动加载该目录下的所有 .js 文件
WEB_DIRECTORY = "./js"

__all__ = ["NODE_CLASS_MAPPINGS", "NODE_DISPLAY_NAME_MAPPINGS", "WEB_DIRECTORY"]