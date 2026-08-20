import { app } from "../../scripts/app.js";

app.registerExtension({
    name: "PT.MiniMaxH3LatentLoaderUI",
    
    async beforeRegisterNodeDef(nodeType, nodeData, app) {
        // 仅针对我们的加载节点生效
        if (nodeData.name === "PT_MinimaxH3LatentLoader") {
            
            const onNodeCreated = nodeType.prototype.onNodeCreated;
            
            nodeType.prototype.onNodeCreated = function() {
                // 调用原有的初始化
                if (onNodeCreated) onNodeCreated.apply(this, arguments);

                // 找到后端的 latent_file 输入框 (STRING widget)
                const fileWidget = this.widgets.find(w => w.name === "latent_file");
                if (!fileWidget) return;

                // 将原本的输入框设置为只读，防止用户手动输入错误路径，同时避免隐藏 widget 导致节点高度计算错误
                fileWidget.disabled = true; 
                fileWidget.value = "请使用下方按钮上传";

                // 创建一个隐藏的原生文件选择器 (挂载到 body 防止被节点裁剪)
                const fileInput = document.createElement("input");
                fileInput.type = "file";
                fileInput.accept = ".latent";
                fileInput.style.display = "none";
                document.body.appendChild(fileInput);

                // 处理文件上传的核心函数
                const handleFileUpload = async (file) => {
                    if (!file || !file.name.endsWith(".latent")) {
                        alert("请选择 .latent 格式的文件！");
                        return;
                    }

                    // 更新按钮状态为加载中
                    uploadBtn.name = "⏳ 正在上传...";
                    this.setDirtyCanvas(true, true);

                    const formData = new FormData();
                    formData.append("image", file); // ComfyUI 标准上传接口字段名为 image
                    formData.append("subfolder", "minimax_h3_latents"); // 保存在 input/minimax_h3_latents/ 下
                    formData.append("type", "input");
                    formData.append("overwrite", "true");

                    try {
                        const resp = await fetch("/upload/image", {
                            method: "POST",
                            body: formData
                        });

                        if (resp.status === 200) {
                            const data = await resp.json();
                            let savedName = data.name;
                            if (data.subfolder) {
                                savedName = data.subfolder + "/" + data.name;
                            }
                            
                            // 更新后端 widget 的值，触发 Python 端更新
                            fileWidget.value = savedName;
                            if (fileWidget.callback) fileWidget.callback(savedName);
                            
                            // 更新按钮显示
                            uploadBtn.name = `✅ ${data.name}`;
                        } else {
                            throw new Error("上传失败: " + resp.statusText);
                        }
                    } catch (err) {
                        alert("上传出错: " + err.message);
                        uploadBtn.name = "❌ 上传失败，点击重试";
                    } finally {
                        this.setDirtyCanvas(true, true);
                    }
                };

                // 监听文件选择
                fileInput.addEventListener("change", (e) => {
                    if (e.target.files.length > 0) {
                        handleFileUpload(e.target.files[0]);
                        fileInput.value = ""; // 清空以允许重复选择同一文件
                    }
                });

                // 【核心修复】使用 LiteGraph 原生按钮，彻底解决点击失效问题
                const uploadBtn = this.addWidget("button", "📂 点击选择 .latent 文件", null, () => {
                    fileInput.click();
                });

                // 【核心修复】使用 LiteGraph 原生拖拽事件，避免与 ComfyUI 全局拖拽冲突
                this.onDragOver = function(e) {
                    return true; // 允许拖拽
                };

                this.onDrop = function(e) {
                    const files = e.dataTransfer.files;
                    if (files.length > 0) {
                        handleFileUpload(files[0]);
                        return true;
                    }
                    return false;
                };
            };
        }
    }
});