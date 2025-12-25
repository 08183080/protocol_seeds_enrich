# 本地模型使用指南

本指南说明如何使用本地部署的模型（如 Ollama）进行种子丰富。

## 前置要求

### 1. 安装 Ollama

访问 [Ollama 官网](https://ollama.ai/) 下载并安装：

```bash
# Linux/macOS
curl -fsSL https://ollama.ai/install.sh | sh

# 或使用包管理器
# macOS
brew install ollama

# Ubuntu/Debian
# 下载安装脚本或使用 snap
```

### 2. 启动 Ollama 服务

```bash
ollama serve
```

服务默认运行在 `http://localhost:11434`

**注意（WSL 用户）**：
- 如果 Ollama 运行在 Windows 宿主机上，程序会自动检测 WSL 宿主机 IP
- 只需在配置文件中设置 `api_url: http://localhost:11434/v1` 或留空
- 程序会自动将 `localhost` 替换为检测到的宿主机 IP

### 3. 下载模型

```bash
# 下载常用模型
ollama pull llama2
ollama pull mistral
ollama pull qwen
ollama pull llama3

# 查看已下载的模型
ollama list
```

## 配置使用本地模型

### 方法 1: 修改配置文件

编辑 `config.yaml`：

```yaml
# 启用本地模型
use_local: true

# Ollama API URL
api_url: http://localhost:11434/v1

# API Key（Ollama 不需要，可以为空）
api_key: ollama

# 使用的模型名称
model: llama2
```

### 方法 2: 使用示例配置文件

```bash
# 复制本地模型配置示例
cp config.local.yaml.example config.yaml

# 编辑配置
vim config.yaml

# 运行
python run.py
```

## 配置示例

### 示例 1: 使用 Llama2

```yaml
protocol: RTSP
seed_dir: ../seeds/RTSP
use_local: true
api_url: http://localhost:11434/v1  # WSL 环境下会自动检测宿主机 IP
api_key: ollama
model: llama2
```

**WSL 环境说明**：
- 如果 Ollama 运行在 Windows 宿主机上，设置 `api_url: http://localhost:11434/v1` 即可
- 程序会自动检测并替换为宿主机 IP（如 `http://172.x.x.x:11434/v1`）
- 也可以直接留空 `api_url`，程序会自动检测

### 示例 2: 使用 Mistral

```yaml
protocol: FTP
seed_dir: ../seeds/FTP
use_local: true
api_url: http://localhost:11434/v1
api_key: ollama
model: mistral
```

### 示例 3: 自定义端口

如果 Ollama 运行在不同端口：

```yaml
use_local: true
api_url: http://localhost:8080/v1  # 自定义端口
model: llama2
```

## 常见问题

### Q: 如何检查 Ollama 是否运行？

**A**: 

```bash
# 检查服务状态
curl http://localhost:11434/api/tags

# 或使用 ollama 命令
ollama list
```

### Q: 模型响应慢怎么办？

**A**: 
1. 使用更小的模型（如 `phi` 而不是 `llama2`）
2. 调整 `advanced.max_enrichment_message_types` 减少每次添加的类型数
3. 检查系统资源（CPU/内存）

### Q: 如何测试本地模型连接？

**A**: 

```python
from chatafl_enricher import ChatAFLEnricher

enricher = ChatAFLEnricher(
    api_key="ollama",
    model="llama2",
    api_url="http://localhost:11434/v1",
    use_local=True
)

# 测试调用
response = enricher.chat_with_llm("Hello, how are you?", model_type="instruct")
print(response)
```

### Q: 支持哪些本地模型？

**A**: 支持所有兼容 OpenAI API 格式的模型，包括：
- **Ollama**: llama2, mistral, qwen, llama3, phi, gemma 等
- **其他兼容 API**: 任何实现 OpenAI 兼容接口的服务

### Q: 本地模型和远程模型的区别？

**A**: 

| 特性 | 本地模型 | 远程模型（OpenAI） |
|------|---------|-------------------|
| 成本 | 免费 | 按使用量收费 |
| 速度 | 取决于硬件 | 通常较快 |
| 隐私 | 数据不离开本地 | 数据发送到云端 |
| 配置 | 需要安装和下载模型 | 只需 API key |

## 性能优化建议

1. **选择合适的模型大小**：
   - 小模型（phi, gemma-2b）：速度快，但质量可能较低
   - 中等模型（llama2-7b, mistral-7b）：平衡速度和质量
   - 大模型（llama2-13b, qwen-14b）：质量高，但速度慢

2. **调整配置参数**：
   ```yaml
   advanced:
     max_enrichment_message_types: 1  # 减少每次添加的类型数
     max_enrichment_corpus_size: 5    # 减少检查的种子数
   ```

3. **使用 GPU 加速**：
   - 确保 Ollama 使用 GPU（如果可用）
   - 检查：`ollama show llama2` 查看是否使用 GPU

## 故障排除

### 问题 1: 连接失败

```
错误: Connection refused
```

**解决方案**：
1. 确保 Ollama 服务正在运行：`ollama serve`
2. 检查端口是否正确
3. 检查防火墙设置

### 问题 2: 模型不存在

```
错误: model not found
```

**解决方案**：
1. 下载模型：`ollama pull <model_name>`
2. 检查模型名称是否正确：`ollama list`

### 问题 3: 响应超时

**解决方案**：
1. 使用更小的模型
2. 增加超时时间（需要修改代码）
3. 检查系统资源

## 下一步

- 查看 [README.md](README.md) 了解完整功能
- 查看 [CONFIG_GUIDE.md](CONFIG_GUIDE.md) 了解配置选项
- 查看 [QUICKSTART.md](QUICKSTART.md) 快速开始

