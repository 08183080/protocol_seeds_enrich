# ChatAFL 种子丰富方法实现总结

## 实现概述

本文档详细说明了 ChatAFL 种子丰富方法的复现实现过程。

## 核心原理

ChatAFL 的种子丰富方法基于以下核心思想：

1. **协议消息类型识别**：通过 LLM 获取协议的所有可能消息类型
2. **种子分析**：从现有种子中提取已使用的消息类型
3. **缺失识别**：计算缺失的消息类型
4. **智能丰富**：使用 LLM 在合适位置添加缺失的消息类型

## 实现步骤

### 步骤 1: 获取协议消息类型

**方法**: `get_protocol_message_types(protocol_name)`

**流程**:
1. 构建提示词，要求 LLM 返回协议的所有消息类型
2. 进行多次查询（默认 3 次）以确保一致性
3. 使用投票机制：只保留出现次数 >= 阈值 的消息类型

**提示词模板**:
```
In the [协议名称] protocol, the message types are: 

Desired format:
<comma_separated_list_of_states_in_uppercase_and_without_whitespaces>
```

**示例输出** (RTSP):
- DESCRIBE, SETUP, PLAY, PAUSE, TEARDOWN, OPTIONS, ANNOUNCE, RECORD

### 步骤 2: 分析现有种子

**方法**: `extract_message_types_from_seeds(seed_files, protocol_name)`

**流程**:
1. 读取种子文件（最多检查 MAX_ENRICHMENT_CORPUS_SIZE 个）
2. 使用正则表达式提取每行的消息类型
3. 合并所有种子中的消息类型

**提取规则**:
- RTSP: 提取第一行的命令（如 `DESCRIBE rtsp://...`）
- HTTP: 提取 HTTP 方法（如 `GET /path HTTP/1.1`）
- FTP: 提取 FTP 命令（如 `USER username`）
- 其他协议: 使用通用模式提取行首的大写单词

### 步骤 3: 识别缺失类型

**计算**:
```python
missing_types = all_message_types - used_message_types
```

### 步骤 4: 丰富种子序列

**方法**: `enrich_sequence(sequence, missing_message_types)`

**流程**:
1. 限制缺失类型数量（最多 MAX_ENRICHMENT_MESSAGE_TYPES 个）
2. 构建提示词，包含原始序列和缺失类型
3. 调用 LLM 生成丰富后的序列
4. 格式化输出

**提示词模板**:
```
The following is one sequence of client requests:
[原始序列（JSON 转义）]

Please add the [缺失类型1], [缺失类型2] client requests in the proper locations, 
and the modified sequence of client requests is:
```

## 关键设计决策

### 1. 一致性检查

**问题**: LLM 输出可能不稳定

**解决方案**: 
- 多次查询（CONFIDENT_TIMES = 3）
- 投票机制：只保留出现频率 >= 50% 的结果

### 2. Token 限制管理

**问题**: OpenAI API 有 token 限制（2048 tokens）

**解决方案**:
- 动态计算允许的序列长度
- 自动截断过长的序列
- 保留安全边距

### 3. 批量处理限制

**问题**: 处理所有种子可能成本过高

**解决方案**:
- 限制检查的种子数量（MAX_ENRICHMENT_CORPUS_SIZE = 10）
- 每次最多添加的消息类型数（MAX_ENRICHMENT_MESSAGE_TYPES = 2）

### 4. 错误处理

**策略**:
- 所有 LLM 调用都有重试机制
- 失败时返回 None，不中断整个流程
- 详细的错误日志

## 代码结构

```
chatafl_enricher.py
├── ChatAFLEnricher (主类)
│   ├── __init__()                    # 初始化
│   ├── chat_with_llm()               # LLM 交互
│   ├── construct_prompt_*()          # 提示词构建
│   ├── get_protocol_message_types()  # 获取消息类型
│   ├── extract_message_types_*()     # 提取消息类型
│   ├── enrich_sequence()             # 丰富序列
│   └── enrich_seeds()                # 批量丰富
```

## 使用流程

### 1. 初始化

```python
enricher = ChatAFLEnricher(api_key="your-key")
```

### 2. 执行丰富

```python
enriched_seeds = enricher.enrich_seeds(
    seed_dir="../seeds/RTSP",
    protocol_name="RTSP",
    output_dir="./enriched_seeds"
)
```

### 3. 内部流程

```
enrich_seeds()
├── get_protocol_message_types()      # 步骤 1
├── extract_message_types_from_seeds() # 步骤 2
├── 计算缺失类型                        # 步骤 3
└── 对每个种子:
    └── enrich_sequence()              # 步骤 4
```

## 配置参数

可在 `ChatAFLEnricher` 类中调整：

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `CONFIDENT_TIMES` | 3 | 一致性检查的查询次数 |
| `MAX_ENRICHMENT_MESSAGE_TYPES` | 2 | 每次最多添加的消息类型数 |
| `MAX_ENRICHMENT_CORPUS_SIZE` | 10 | 最多检查的种子数 |
| `ENRICHMENT_RETRIES` | 5 | 丰富操作的最大重试次数 |
| `MESSAGE_TYPE_RETRIES` | 5 | 获取消息类型的最大重试次数 |
| `MAX_TOKENS` | 2048 | LLM 最大 token 数 |

## 与原始实现的对应关系

| 原始 C 函数 | Python 方法 | 说明 |
|------------|------------|------|
| `get_protocol_message_types()` | `get_protocol_message_types()` | 获取协议消息类型 |
| `extract_message_types_from_seed()` | `extract_message_types_from_seed()` | 从种子提取类型 |
| `enrich_sequence()` | `enrich_sequence()` | 丰富序列 |
| `chat_with_llm()` | `chat_with_llm()` | LLM 交互 |
| `construct_prompt_*()` | `construct_prompt_*()` | 提示词构建 |

## 测试建议

### 1. 单元测试

- 测试消息类型提取（不同协议）
- 测试提示词构建
- 测试序列丰富（使用 mock LLM）

### 2. 集成测试

- 使用真实种子文件测试完整流程
- 验证输出格式正确性
- 检查错误处理

### 3. 性能测试

- 测量 API 调用次数
- 评估处理时间
- 计算成本

## 已知限制

1. **协议特定性**: 消息类型提取依赖于协议格式，可能需要针对特定协议调整
2. **API 成本**: 大量使用会产生费用
3. **网络依赖**: 需要稳定的网络连接访问 OpenAI API
4. **LLM 输出质量**: 依赖 LLM 的输出质量，可能需要后处理

## 改进方向

1. **支持更多协议**: 扩展消息类型提取规则
2. **缓存机制**: 缓存协议消息类型，避免重复查询
3. **并行处理**: 并行处理多个种子
4. **质量评估**: 添加种子质量评估机制
5. **本地模型支持**: 支持使用本地 LLM 模型

## 参考文献

- ChatAFL 原始实现（C 代码）
- OpenAI API 文档
- 相关协议规范（RFC 文档）

