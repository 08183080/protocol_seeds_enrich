# ChatAFL 种子丰富方法复现

本目录包含 ChatAFL 种子丰富方法的完整复现实现。

## 概述

ChatAFL 是一种基于大语言模型（LLM）的网络协议种子丰富化方法。其核心思想是：

1. **类型推断**：通过 LLM 获取协议的所有消息类型
2. **缺失识别**：分析现有种子，识别缺失的消息类型
3. **序列丰富**：使用 LLM 在合适位置添加缺失的消息类型

## 核心流程

```
1. 获取协议消息类型
   └─> 使用 LLM 查询协议的所有消息类型（如 RTSP: DESCRIBE, SETUP, PLAY, TEARDOWN...）
   
2. 分析现有种子
   └─> 从种子文件中提取已使用的消息类型
   
3. 识别缺失类型
   └─> 计算：缺失类型 = 所有类型 - 已使用类型
   
4. 丰富种子序列
   └─> 使用 LLM 在合适位置添加缺失的消息类型
```

## 安装

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 设置 API Key（如果使用远程模型）

**使用 OpenAI**:
```bash
export OPENAI_API_KEY="your-api-key-here"
```

**使用本地模型（如 Ollama）**:
- 不需要 API key
- 需要先安装并启动 Ollama 服务
- 详见 [本地模型使用指南](LOCAL_MODEL_GUIDE.md)

## 使用方法

### 方法 1: 使用 YAML 配置文件（推荐）

这是最简单的方式，只需配置一次即可重复使用。

#### 步骤 1: 创建配置文件

复制示例配置文件并修改：

```bash
cp config.yaml.example config.yaml
```

编辑 `config.yaml`，设置协议和种子目录：

```yaml
protocol: RTSP
seed_dir: ../seeds/RTSP
output_dir: ./enriched_seeds/RTSP
```

#### 步骤 2: 运行

```bash
python run.py
```

或使用自定义配置文件：

```bash
python run.py my_config.yaml
```

### 方法 2: 使用命令行参数

```bash
python main.py --protocol RTSP --seed_dir ../seeds/RTSP --output_dir ./enriched_seeds
```

#### 参数说明

- `--protocol`: 协议名称（必需），如 `RTSP`, `FTP`, `HTTP`, `SMTP`, `SIP`
- `--seed_dir`: 种子文件目录路径（必需）
- `--output_dir`: 输出目录路径（可选，默认为 `seed_dir/enriched`）
- `--api_key`: OpenAI API key（可选，也可通过环境变量设置）
- `--model`: 使用的模型（可选，默认 `gpt-3.5-turbo-instruct`）

### 使用示例

#### 示例 1: 使用配置文件（推荐）

```bash
# 1. 编辑配置文件
vim config.yaml

# 2. 运行
python run.py
```

#### 示例 2: 命令行方式

```bash
python main.py \
    --protocol RTSP \
    --seed_dir ../seeds/RTSP \
    --output_dir ./enriched_seeds/RTSP
```

#### 示例 3: 在 Python 代码中使用

```python
from chatafl_enricher import ChatAFLEnricher

# 初始化丰富器
enricher = ChatAFLEnricher(api_key="your-api-key")

# 丰富种子
enriched_seeds = enricher.enrich_seeds(
    seed_dir="../seeds/RTSP",
    protocol_name="RTSP",
    output_dir="./enriched_seeds"
)
```

### 配置文件说明

配置文件支持以下字段：

**必需字段：**
- `protocol`: 协议名称
- `seed_dir`: 种子目录路径

**可选字段：**
- `output_dir`: 输出目录（默认: `seed_dir/enriched`）
- `api_key`: OpenAI API key（也可通过环境变量设置）
- `model`: 使用的模型（默认: `gpt-3.5-turbo-instruct`）

**API 配置：**
```yaml
# 使用本地模型（如 Ollama）
use_local: true
api_url: http://localhost:11434/v1
api_key: ollama  # 本地模型可以为空
model: llama2

# 或使用远程模型（OpenAI）
use_local: false
api_url: https://api.openai.com/v1  # 可选，默认值
api_key: sk-xxx
model: gpt-3.5-turbo-instruct
```

**高级配置（可选）：**
```yaml
advanced:
  confident_times: 3                    # 一致性检查次数
  max_enrichment_message_types: 2        # 每次最多添加的类型数
  max_enrichment_corpus_size: 10        # 最多检查的种子数
  enrichment_retries: 5                 # 丰富操作重试次数
  message_type_retries: 5               # 消息类型获取重试次数
```

详细配置示例请参考：
- `config.yaml.example` - 远程模型配置
- `config.local.yaml.example` - 本地模型配置
- [本地模型使用指南](LOCAL_MODEL_GUIDE.md) - 本地模型详细说明

## 实现细节

### 核心模块

- `chatafl_enricher.py`: 核心实现模块
  - `ChatAFLEnricher`: 主类，包含所有功能
  - `get_protocol_message_types()`: 获取协议消息类型（带一致性检查）
  - `extract_message_types_from_seeds()`: 从种子中提取消息类型
  - `enrich_sequence()`: 丰富种子序列

### 关键特性

1. **一致性检查**: 多次查询 LLM 以确保消息类型的准确性
2. **Token 限制管理**: 自动处理 token 限制，确保提示词在限制内
3. **批量处理**: 支持批量处理多个种子文件
4. **错误处理**: 完善的错误处理和重试机制

### 配置参数

可在 `ChatAFLEnricher` 类中调整以下参数：

- `CONFIDENT_TIMES = 3`: 一致性检查的查询次数
- `MAX_ENRICHMENT_MESSAGE_TYPES = 2`: 每次最多添加的消息类型数
- `MAX_ENRICHMENT_CORPUS_SIZE = 10`: 最多检查的种子数
- `ENRICHMENT_RETRIES = 5`: 丰富操作的最大重试次数
- `MESSAGE_TYPE_RETRIES = 5`: 获取消息类型的最大重试次数

## 提示词设计

### 消息类型获取提示词

```
In the [协议名称] protocol, the message types are: 

Desired format:
<comma_separated_list_of_states_in_uppercase_and_without_whitespaces>
```

### 种子丰富提示词

```
The following is one sequence of client requests:
[原始序列]

Please add the [缺失类型1], [缺失类型2] client requests in the proper locations, 
and the modified sequence of client requests is:
```

## 文件结构

```
baselines/chatafl/
├── core/                    # 原始 C 代码实现
│   ├── chat-llm.c
│   └── chat-llm.h
├── prompts/                 # 提示词文档
│   └── pronpts.md
├── chatafl_enricher.py      # Python 核心实现
├── run.py                   # 基于 YAML 配置的运行脚本 ⭐
├── main.py                  # 命令行参数方式的主程序
├── config.yaml              # 配置文件（需要创建）
├── config.yaml.example      # 配置文件示例 ⭐
├── requirements.txt         # 依赖列表
├── example_usage.py         # 使用示例
└── README.md               # 本文档
```

## 注意事项

1. **API 成本**: 使用 OpenAI API 会产生费用，请注意使用量
2. **网络要求**: 需要能够访问 OpenAI API
3. **协议支持**: 当前支持文本协议（RTSP, FTP, HTTP, SMTP, SIP 等）
4. **种子格式**: 种子文件应为纯文本格式，包含协议消息

## 与原始实现的差异

本实现基于原始 C 代码的逻辑，但有以下改进：

1. **Python 实现**: 更易维护和扩展
2. **更好的错误处理**: 完善的异常处理机制
3. **更清晰的接口**: 面向对象的 API 设计
4. **文档完善**: 详细的代码注释和使用文档

## 参考文献

- ChatAFL 原始论文/实现
- 相关协议规范（RFC 文档）

## 许可证

与主项目保持一致。