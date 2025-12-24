# ChatAFL 协议分析提示词提取文档

## 1. 核心机制说明

ChatAFL 的工作流程主要基于以下逻辑：

* **类型推断**：通过获取协议的消息模板来推断现有的消息类型。
* **缺失补偿**：通过已知类型计算出缺失的消息类型，并进行组合补充。
* **局限性**：
* 动作较为**机械**，缺乏对协议状态机的深层理解。
* 仅针对消息结构的丰富，**不对参数内容进行变动**。



---

## 2. 消息模板获取提示词 (Message Template Prompt)

该提示词通过 Few-shot（少样本）方式引导大模型生成特定协议的所有客户端请求模板。

### 提示词结构

```text
For the RTSP protocol, the DESCRIBE client request template is:
DESCRIBE: ["DESCRIBE <<VALUE>>\r\n", "CSeq: <<VALUE>>\r\n", "User-Agent: <<VALUE>>\r\n", "Accept: <<VALUE>>\r\n", "\r\n"]

For the HTTP protocol, the GET client request template is:
GET: ["GET <<VALUE>>\r\n"]

For the [协议名称] protocol, all of client request templates are :

```

---

## 3. 消息类型获取提示词 (Message Type Prompt)

该提示词用于获取协议中所有可能的消息类型列表，并强制要求特定的输出格式。

### 提示词内容

```text
In the [协议名称] protocol, the message types are: 

Desired format:
<comma_separated_list_of_states_in_uppercase_and_without_whitespaces>

```

### 格式要求说明

* **全大写** (UPPERCASE)
* **无空格** (WITHOUT WHITESPACES)
* **逗号分隔** (COMMA SEPARATED)