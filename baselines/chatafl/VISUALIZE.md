# ChatAFL 种子可视化工具

极简的Web可视化工具，用于对比展示初始种子和丰富后种子的差异。

## 使用方法

1. 安装依赖：
```bash
pip install -r requirements.txt
```

2. 启动服务器：
```bash
python visualize.py
```

3. 在浏览器中访问：`http://localhost:5000`

4. 点击"从配置文件加载"按钮自动加载config.yaml中的路径，或手动输入：
   - 初始种子目录
   - 丰富后种子目录
   - 协议类型（HTTP/FTP/RTSP等）

## 功能特性

- 自动对比初始种子和丰富后种子
- 高亮显示新增的命令和消息类型
- 展示命令数量、类型数量的增加情况
- 并排显示原始和丰富后的内容

