# ChatAFL 快速开始指南

## 5 分钟快速上手

### 1. 安装依赖

```bash
cd baselines/chatafl
pip install -r requirements.txt
```

### 2. 设置 API Key

```bash
export OPENAI_API_KEY="sk-your-api-key-here"
```

### 3. 配置并运行（推荐方式）

```bash
# 复制配置文件示例
cp config.yaml.example config.yaml

# 编辑配置文件，设置协议和种子目录
vim config.yaml

# 运行
python run.py
```

### 4. 或使用命令行方式

```bash
# 丰富 RTSP 协议的种子
python main.py --protocol RTSP --seed_dir ../../seeds/RTSP --output_dir ./enriched_seeds
```

## 详细步骤

### 步骤 1: 准备环境

确保已安装 Python 3.7+ 和 pip。

### 步骤 2: 安装依赖

```bash
pip install -r requirements.txt
```

依赖包括：
- `openai`: OpenAI API 客户端

### 步骤 3: 获取 API Key

1. 访问 [OpenAI Platform](https://platform.openai.com/)
2. 创建账户并获取 API key
3. 设置环境变量：

```bash
export OPENAI_API_KEY="sk-xxxxxxxxxxxxx"
```

### 步骤 4: 准备种子文件

确保种子文件目录存在，例如：
```
seeds/
└── RTSP/
    ├── seed1.txt
    ├── seed2.txt
    └── ...
```

### 步骤 5: 运行

```bash
python main.py \
    --protocol RTSP \
    --seed_dir ../../seeds/RTSP \
    --output_dir ./enriched_seeds
```

### 步骤 6: 查看结果

丰富后的种子将保存在 `output_dir` 目录中，文件名格式为 `enriched_<原文件名>`。

## 常见问题

### Q: API key 错误

**A**: 检查环境变量是否正确设置：
```bash
echo $OPENAI_API_KEY
```

或使用命令行参数：
```bash
python main.py --protocol RTSP --seed_dir ... --api_key sk-xxx
```

### Q: 找不到种子文件

**A**: 检查路径是否正确，使用绝对路径：
```bash
python main.py --protocol RTSP --seed_dir /absolute/path/to/seeds/RTSP
```

### Q: API 调用失败

**A**: 
1. 检查网络连接
2. 检查 API key 是否有效
3. 检查账户余额

### Q: 如何调整参数？

**A**: 编辑 `chatafl_enricher.py` 中的类常量，例如：
```python
MAX_ENRICHMENT_MESSAGE_TYPES = 3  # 改为每次添加 3 个类型
```

## 下一步

- 查看 [README.md](README.md) 了解详细功能
- 查看 [IMPLEMENTATION.md](IMPLEMENTATION.md) 了解实现细节
- 运行 [example_usage.py](example_usage.py) 查看更多示例

## 支持

如有问题，请查看项目主 README 或提交 issue。

