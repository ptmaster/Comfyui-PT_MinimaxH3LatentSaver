# Comfyui-PT_MinimaxH3LatentSaver
MiniMax H3 Latent Saver &amp; loader

latent 在手, 天下任我走. With latent power in hand, I shall command this land.

<img width="1342" height="1266" alt="E9349A66B29ADE1C82DB016EE543A80C" src="https://github.com/user-attachments/assets/9df8731c-5b93-44e1-9056-5309930484a1" />

<img width="1458" height="1279" alt="89EE03DDFA92D0216E0DA81ACAE41F20" src="https://github.com/user-attachments/assets/31efa770-58c7-4b58-9490-ccb8d65e6675" />


🎮 使用指南
1. 保存 Latent (Save)
在节点菜单搜索并添加 💾 PT Save Latent (MiniMax H3 AV)。
将 MiniMax H3 采样器的 LATENT 输出连入该节点。
设置 filename_prefix（支持中文，自动过滤非法字符）。
选择保存目录（强烈建议选择 input，方便后续直接加载）。
点击 Queue Prompt。节点会在后台完成解包、校验、保存，并将原始 Latent 透传给下游。
2. 加载 Latent (Load)
添加 📂 PT Load Latent (MiniMax H3 AV) 节点。
方式 A (点击)：点击节点上的 📂 点击选择 .latent 文件 按钮，从电脑任意位置选择文件。
方式 B (拖拽)：直接将 .latent 文件从文件夹拖拽到节点上。
节点会自动上传、解析并重建 Nested Tensor。将 LATENT 输出连入 VAE Decode 即可直接解码！
这个节点非常适合对视频进行无损保存,请同时备份好您的参考图,参考音频, 提示词和参数,尤其是帧率用于在任何地点解码视频.

# Comfyui‑PT_MinimaxH3LatentSaver
MiniMax H3 Latent Saver & loader
🎮 User Guide
1. Save Latent (Save)
Search for and add the 💾 PT Save Latent (MiniMax H3 AV) node in the node menu.
Connect the LATENT output of the MiniMax H3 sampler to this node.
Set filename_prefix (Chinese characters are supported; invalid characters will be filtered automatically).
Select a save directory (input is strongly recommended for easy subsequent loading).
Click Queue Prompt. The node will unpack, verify and save in the background, and pass the original Latent through to downstream nodes.
3. Load Latent (Load)
Add the 📂 PT Load Latent (MiniMax H3 AV) node.
Method A (Click): Click the 📂 Click to select .latent file button on the node and pick the file from any location on your computer.
Method B (Drag‑and‑Drop): Directly drag the .latent file from your folder onto the node.
The node will automatically upload, parse and reconstruct the Nested Tensor. Connect the LATENT output to VAE Decode for direct decoding!
This node is ideal for lossless video saving. Please also back up your reference images, reference audio, prompts and parameters, especially the frame rate for video decoding anywhere.

📜 License
MIT License. 自由使用，自由分发，但请保留作者署名。
Made with ❤️ and lots of ☕ by PT.
