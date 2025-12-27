# ChatAFL 种子丰富逻辑详解

## 整体流程概览

```
输入: 种子目录 + 协议名称
  ↓
步骤1: 获取协议的所有消息类型（硬编码字典）
  ↓
步骤2: 分析现有种子，提取已使用的消息类型
  ↓
步骤3: 计算缺失的消息类型 = 所有类型 - 已使用类型
  ↓
步骤4: 对每个种子进行丰富
  ├─ 提取当前种子的消息类型
  ├─ 计算当前种子缺失的类型
  ├─ 调用 LLM 添加缺失类型
  ├─ 验证生成结果
  └─ 保存丰富后的种子
  ↓
输出: 丰富后的种子文件
```

## 详细步骤说明

### 步骤1: 获取协议的所有消息类型

**方法**: `get_protocol_message_types(protocol_name)`

**逻辑**:
- 从硬编码字典 `PROTOCOL_MESSAGE_TYPES` 中获取
- 不再调用 LLM，直接返回预定义的消息类型集合

**示例（FTP）**:
```python
all_message_types = {
    "USER", "PASS", "RETR", "STOR", "LIST", "QUIT",
    "CWD", "PWD", "MKD", "RMD", "DELE", ...
}
```

### 步骤2: 分析现有种子中的消息类型

**方法**: `extract_message_types_from_seeds(seed_files, protocol_name)`

**逻辑**:
1. 遍历种子文件（最多检查 `MAX_ENRICHMENT_CORPUS_SIZE` 个）
2. 对每个种子文件：
   - 读取文件内容
   - 使用正则表达式提取消息类型
   - 对于 FTP：提取行首的大写命令（如 `USER`, `PASS`）
3. 合并所有种子中的消息类型

**示例**:
```
种子1: USER, PASS, RETR, QUIT
种子2: USER, PASS, LIST, QUIT
种子3: USER, PASS, CWD, PWD

合并后: {USER, PASS, RETR, LIST, QUIT, CWD, PWD}
```

### 步骤3: 计算缺失的消息类型

**逻辑**:
```python
missing_types = all_message_types - used_message_types
```

**示例**:
```
所有类型: {USER, PASS, RETR, STOR, LIST, QUIT, CWD, PWD, MKD, RMD, ...}
已使用:   {USER, PASS, RETR, LIST, QUIT, CWD, PWD}
缺失:     {STOR, MKD, RMD, DELE, ...}
```

### 步骤4: 对每个种子进行丰富

#### 4.1 提取当前种子的消息类型

**方法**: `extract_message_types_from_seed(content, protocol_name)`

**逻辑**:
- 从当前种子内容中提取已使用的消息类型
- 使用协议特定的正则表达式模式

#### 4.2 计算当前种子缺失的类型

**逻辑**:
```python
seed_missing_types = missing_types - seed_used_types
```

**示例**:
```
全局缺失: {STOR, MKD, RMD, DELE, STAT, ABOR}
当前种子已用: {USER, PASS, RETR}
当前种子缺失: {STOR, MKD, RMD, DELE, STAT, ABOR}
```

#### 4.3 限制添加的消息类型数量

**逻辑**:
```python
# 每次最多添加 MAX_ENRICHMENT_MESSAGE_TYPES 个（默认: 2）
seed_missing_types = seed_missing_types[:MAX_ENRICHMENT_MESSAGE_TYPES]
```

**原因**: 
- 避免一次性添加太多类型导致序列过长
- 提高 LLM 生成质量
- 控制 token 使用量

#### 4.4 构建提示词

**方法**: `construct_enrichment_prompt(sequence, missing_message_types, protocol_name)`

**提示词结构**:
```
系统消息: 你是网络协议专家，生成协议客户端请求序列...

用户消息:
1. 协议格式示例（FTP/RTSP等）
2. 原始序列
3. 需要添加的缺失类型
4. 严格的要求（格式、禁止占位符等）
```

**关键约束**:
- ✅ 只返回修改后的序列
- ✅ 使用与原始序列相同的格式
- ✅ 使用实际的协议命令（如 `USER ubuntu`）
- ❌ 禁止使用占位符（如 `COMMAND USER`）
- ❌ 禁止包含解释性文字
- ❌ 禁止包含服务器响应

#### 4.5 调用 LLM 生成

**方法**: `enrich_sequence(sequence, missing_message_types, protocol_name)`

**流程**:
1. 构建 chat 格式的提示词（messages）
2. 调用 LLM API（支持 OpenAI 和本地模型如 Ollama）
3. 获取响应

#### 4.6 提取和清理响应

**方法**: `extract_sequence_from_response(response, protocol_name)`

**清理步骤**:
1. 移除代码块标记（```）
2. 过滤占位符关键词（COMMAND, RESPONSE 等）
3. 过滤解释性文字
4. 提取协议命令行
5. 移除服务器响应（FTP 状态码等）

#### 4.7 验证生成结果

**方法**: `validate_enriched_sequence(sequence, protocol_name, original_sequence)`

**验证项**:
- ✅ 序列不为空
- ✅ 不包含占位符关键词
- ✅ 不包含解释性文字
- ✅ 符合协议格式（如 FTP 命令格式）

**如果验证失败**: 返回 `None`，不保存

#### 4.8 保存丰富后的种子

**逻辑**:
- 每个种子可以生成多个变体（`max_enriched_per_file`）
- 立即保存，不等待所有种子处理完成
- 文件名格式：
  - 单个变体: `enriched_seed_1.raw`
  - 多个变体: `enriched_seed_1_v1.raw`, `enriched_seed_1_v2.raw`, ...

## 关键配置参数

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `MAX_ENRICHMENT_MESSAGE_TYPES` | 2 | 每次最多添加的消息类型数 |
| `MAX_ENRICHED_SEEDS_PER_FILE` | 1 | 每个种子最多生成的变体数 |
| `MAX_ENRICHMENT_CORPUS_SIZE` | 10 | 最多检查的种子数（用于分析） |
| `ENRICHMENT_RETRIES` | 5 | LLM 调用失败时的重试次数 |

## 示例流程

### 输入
- 协议: FTP
- 种子目录: `seeds/FTP/`
- 种子文件: `seed_1.raw` (包含: USER, PASS, RETR, QUIT)

### 执行过程

1. **获取所有 FTP 消息类型**
   ```
   所有类型: {USER, PASS, RETR, STOR, LIST, QUIT, CWD, PWD, MKD, RMD, ...}
   ```

2. **分析现有种子**
   ```
   已使用: {USER, PASS, RETR, QUIT}
   ```

3. **计算缺失类型**
   ```
   缺失: {STOR, LIST, CWD, PWD, MKD, RMD, ...}
   ```

4. **处理 seed_1.raw**
   - 当前种子已用: {USER, PASS, RETR, QUIT}
   - 当前种子缺失: {STOR, LIST, CWD, PWD, MKD, RMD, ...}
   - 限制为前 2 个: {STOR, LIST}
   - 调用 LLM 添加 STOR 和 LIST

5. **LLM 生成**
   ```
   原始序列:
   USER ubuntu
   PASS ubuntu
   RETR test.txt
   QUIT
   
   LLM 生成（添加 STOR 和 LIST）:
   USER ubuntu
   PASS ubuntu
   LIST
   RETR test.txt
   STOR upload.txt
   QUIT
   ```

6. **验证和保存**
   - 验证通过 ✅
   - 保存为 `enriched_seed_1.raw`

## 设计特点

### 1. **增量丰富**
- 不是生成全新序列，而是在现有序列基础上添加缺失类型
- 保持原始序列的结构和格式

### 2. **质量保证**
- 多层验证：格式验证、占位符检测、协议格式检查
- 验证失败不保存，避免低质量种子

### 3. **立即保存**
- 每个种子丰富后立即保存
- 避免因中途出错导致所有结果丢失

### 4. **变体生成**
- 支持为每个种子生成多个变体
- 利用 LLM 的随机性产生不同结果

### 5. **协议特定处理**
- 不同协议有不同的消息类型提取规则
- 不同协议有不同的格式验证规则

## 局限性

1. **机械性**: 只是添加缺失类型，不深入理解协议状态机
2. **位置选择**: 依赖 LLM 判断添加位置，可能不够准确
3. **参数不变**: 只添加消息类型，不改变参数内容
4. **顺序依赖**: 添加顺序可能不符合协议逻辑

## 改进方向

1. **协议状态机**: 基于协议状态机决定添加位置
2. **参数丰富**: 不仅添加类型，还丰富参数值
3. **序列验证**: 验证生成序列的协议逻辑正确性
4. **智能排序**: 基于协议规范优化消息顺序

