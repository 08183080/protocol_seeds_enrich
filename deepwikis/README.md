# DeepWiki 文档知识提取指南

## 概述

本目录包含从 DeepWiki 实现文档中提取协议实现知识的工具和指南。DeepWiki 文档描述了**代码实现细节**，与 RFC 规范文档不同，它提供了**实现特定的行为、架构和代码路径**信息。

## 文件说明

### 核心文档

1. **`deepwiki_extraction_strategy.md`**
   - 详细的提取策略文档
   - 说明 DeepWiki 与 RFC 知识提取的差异
   - 定义 7 个关键提取维度
   - 提供清洗策略和输出格式建议

2. **`prompt_deepwiki_extraction.md`**
   - 用于指导 LLM 提取知识的 Prompt 模板
   - 包含详细的角色定义、分析维度和输出格式
   - 可直接用于 LLM 辅助提取

3. **`example_rtsp_live555_knowledge.json`**
   - 基于 live555 RTSP 实现的完整示例输出
   - 展示了如何从 DeepWiki 文档提取实现知识
   - 可作为其他协议提取的参考模板

## 快速开始

### 步骤 1：选择目标文档

从 `protocol_deepwikis/` 目录中选择要分析的实现文档。优先选择：
- 直接描述协议处理的文档（如 `RTSP-Media-Server.md`, `Protocol-Implementations.md`）
- 描述网络协议实现的文档（如 `Network-Protocol-Implementation.md`）
- 描述核心架构的文档（如 `Core-Architecture.md`）

### 步骤 2：使用 Prompt 提取知识

使用 `prompt_deepwiki_extraction.md` 中的 Prompt，结合选定的 DeepWiki 文档，让 LLM 提取实现知识。

**示例命令**（假设使用 CLI 工具）：
```bash
# 使用 prompt 提取知识
llm-extract \
  --prompt protocol_deepwikis/prompt_deepwiki_extraction.md \
  --input protocol_deepwikis/rgaufman-live555-DeepWiki/RTSP-Media-Server.md \
  --output protocol_deepwikis/rtsp_live555_knowledge.json
```

### 步骤 3：验证和补充

1. **检查完整性**：确保所有关键函数、调用链、状态转换都被提取
2. **补充代码位置**：从文档中的 "Sources:" 链接提取具体代码位置
3. **验证准确性**：对照原始文档验证提取的知识

### 步骤 4：与 RFC 知识融合

将 DeepWiki 知识与对应的 RFC 知识（如 `protocol_rfcs/rtsp_knowledge_1.0.json`）结合使用：

```python
# 伪代码示例
rfc_knowledge = load_json("protocol_rfcs/rtsp_knowledge_1.0.json")
deepwiki_knowledge = load_json("protocol_deepwikis/rtsp_live555_knowledge.json")

# 融合知识
combined_knowledge = {
    "rfc_constraints": rfc_knowledge["message_model"],
    "implementation_details": deepwiki_knowledge["implementation_knowledge"],
    "fuzzing_strategies": merge_strategies(
        rfc_knowledge["fuzzing_guidance"],
        deepwiki_knowledge["fuzzing_guidance"]
    )
}
```

## 提取维度检查清单

在提取知识时，确保覆盖以下维度：

- [ ] **代码结构**：关键函数、调用链
- [ ] **解析逻辑**：消息解析顺序、验证检查点
- [ ] **内存操作**：缓冲区类型、大小限制、字符串操作
- [ ] **状态管理**：状态存储、转换、清理
- [ ] **错误处理**：错误检测、响应、资源清理
- [ ] **实现约束**：硬编码限制、配置选项
- [ ] **自定义特性**：非标准命令、协议扩展

## 输出格式

提取的知识应遵循 `example_rtsp_live555_knowledge.json` 中的格式：

```json
{
  "meta": {
    "protocol": "协议名",
    "implementation": "实现名称",
    "source_repo": "仓库名",
    "documentation_source": "文档路径"
  },
  "implementation_knowledge": {
    "code_structure": { ... },
    "parsing_logic": [ ... ],
    "state_management": { ... },
    "memory_operations": [ ... ],
    "implementation_constraints": [ ... ],
    "error_handling": [ ... ],
    "custom_features": [ ... ]
  },
  "fuzzing_guidance": {
    "high_priority_targets": [ ... ],
    "test_case_templates": [ ... ],
    "code_path_coverage": [ ... ]
  }
}
```

## 与 RFC 知识的区别

| 方面 | RFC 知识 | DeepWiki 知识 |
|------|---------|--------------|
| **来源** | RFC 规范文档 | 代码实现文档 |
| **关注点** | 协议规范、标准行为 | 实现细节、代码行为 |
| **用途** | 发现规范实现偏差 | 发现实现特定漏洞 |
| **测试用例** | 符合/违反规范的输入 | 触发特定代码路径的输入 |

## 使用场景

### 场景 1：发现实现特定的缓冲区漏洞

**RFC 知识**：`Session ID must be at least 8 bytes`
**DeepWiki 知识**：`Implementation stores Session ID in unbounded buffer`
**测试策略**：生成 10000 字节的 Session ID 测试缓冲区溢出

### 场景 2：发现状态机实现漏洞

**RFC 知识**：`PLAY must follow SETUP`
**DeepWiki 知识**：`State stored in hash table, timeout 65 seconds`
**测试策略**：在超时边界测试状态混淆，使用过期 Session ID

### 场景 3：发现解析逻辑漏洞

**RFC 知识**：`Transport header format: transport-protocol/profile[/lower-transport]`
**DeepWiki 知识**：`Parsing order: transport-protocol -> profile -> parameters, validation at each step`
**测试策略**：生成畸形 Transport 头部，测试解析器的边界条件

## 最佳实践

1. **优先提取协议处理相关文档**：忽略构建、配置等非协议相关的文档
2. **关注安全相关细节**：缓冲区操作、状态管理、错误处理
3. **提取代码位置**：尽可能从文档中提取具体的代码文件路径和行号
4. **验证实现行为**：如果文档描述与 RFC 不同，明确标注
5. **设计针对性测试**：基于实现细节设计能触发特定代码路径的测试用例

## 目录结构

```
protocol_deepwikis/
├── README.md (本文件)
├── deepwiki_extraction_strategy.md (提取策略)
├── prompt_deepwiki_extraction.md (提取 Prompt)
├── example_rtsp_live555_knowledge.json (示例输出)
└── [各协议的 DeepWiki 文档目录]/
    ├── Protocol-Implementations.md
    ├── Network-Protocol-Implementation.md
    └── ...
```

## 下一步

1. **自动化提取**：开发脚本自动从 DeepWiki 文档提取知识
2. **知识融合**：开发工具将 RFC 知识和 DeepWiki 知识融合
3. **测试用例生成**：基于融合知识自动生成测试用例
4. **持续更新**：随着代码库更新，定期更新提取的知识

## 相关资源

- RFC 知识提取：`../protocol_rfcs/prompt_2.0.md`
- RFC 知识示例：`../protocol_rfcs/rtsp_knowledge_1.0.json`
- CVE 知识：`../protocol_cve_docs/cve_knowledge_1.0.json`
