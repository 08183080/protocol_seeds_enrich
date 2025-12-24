# DeepWiki 文档清洗与知识提取策略

## 概述

DeepWiki 文档是代码库的实现文档，与 RFC 规范文档不同，它描述了**具体实现的行为、架构和代码细节**。从 DeepWiki 提取的知识主要用于发现**实现特定的漏洞**和**代码路径相关的测试用例**。

## DeepWiki vs RFC 知识提取的差异

| 维度 | RFC 知识提取 | DeepWiki 知识提取 |
|------|-------------|------------------|
| **目标** | 协议规范、标准行为 | 实现细节、代码行为 |
| **关注点** | 协议语法、状态机、规范约束 | 代码路径、函数调用、实现约束 |
| **漏洞类型** | 规范实现偏差、协议逻辑漏洞 | 缓冲区溢出、状态混淆、实现缺陷 |
| **测试用例** | 符合/违反规范的输入 | 触发特定代码路径的输入 |

## 提取维度

### 1. 实现特定的协议处理逻辑

**目标**：识别实现如何处理协议消息，特别是与标准规范不同的地方。

**提取内容**：
- 消息解析函数和解析顺序
- 参数验证逻辑（长度检查、格式检查）
- 错误处理机制（如何处理无效输入）
- 实现特定的状态转换

**示例**：
```json
{
  "implementation_details": {
    "message_parsing": {
      "function": "handleCmd_SETUP()",
      "parsing_order": ["method", "url", "headers"],
      "validation_checks": [
        "Transport header format validation",
        "Session ID length check (min 8 bytes)"
      ],
      "error_handling": "Returns 400 Bad Request on validation failure"
    }
  }
}
```

### 2. 代码路径和函数调用序列

**目标**：识别关键代码路径，用于生成能触发特定代码分支的测试用例。

**提取内容**：
- 关键函数的调用链
- 条件分支和决策点
- 数据流路径（从输入到处理到输出）

**示例**：
```json
{
  "code_paths": [
    {
      "trigger": "RTSP SETUP with invalid Transport header",
      "path": [
        "RTSPServer::handleCmd_SETUP()",
        "parseTransportHeader()",
        "validateTransportParams()",
        "return 400 Bad Request"
      ],
      "fuzz_strategy": "Generate malformed Transport headers to test validation logic"
    }
  ]
}
```

### 3. 缓冲区管理和内存操作

**目标**：识别潜在的缓冲区溢出、越界读取等内存安全问题。

**提取内容**：
- 缓冲区大小限制
- 字符串处理函数（strcpy, sprintf 等）
- 长度检查和边界验证
- 动态内存分配点

**示例**：
```json
{
  "memory_operations": [
    {
      "location": "parseSessionID()",
      "buffer_size": "No explicit limit",
      "operation": "strcpy(session_id, input)",
      "risk": "Potential buffer overflow if input exceeds buffer size",
      "fuzz_strategy": "Generate extremely long session IDs (>1024 bytes)"
    }
  ]
}
```

### 4. 状态机实现细节

**目标**：理解实现的状态机，发现状态转换中的漏洞。

**提取内容**：
- 状态定义（可能与 RFC 不同）
- 状态转换条件（代码中的实际判断）
- 状态持久化机制
- 状态清理和资源释放

**示例**：
```json
{
  "state_machine_implementation": {
    "states": ["INIT", "SETUP_SENT", "READY", "PLAYING"],
    "transitions": [
      {
        "from": "INIT",
        "trigger": "SETUP command",
        "code_check": "if (response_code == 200)",
        "to": "READY",
        "implementation_note": "Session ID stored in hash table"
      }
    ],
    "state_cleanup": "Session timeout after 65 seconds of inactivity"
  }
}
```

### 5. 实现特定的约束和限制

**目标**：发现实现中的硬编码限制、配置选项等。

**提取内容**：
- 最大长度限制
- 超时设置
- 并发连接限制
- 配置选项的影响

**示例**：
```json
{
  "implementation_constraints": [
    {
      "constraint": "Maximum URL length: 2048 bytes",
      "location": "URL parsing",
      "fuzz_strategy": "Generate URLs of length 2049, 4096, 8192 bytes"
    },
    {
      "constraint": "Session reclamation time: 65 seconds",
      "location": "Session management",
      "fuzz_strategy": "Test session reuse after timeout boundary"
    }
  ]
}
```

### 6. 错误处理和异常路径

**目标**：识别错误处理中的漏洞，如资源泄漏、双重释放等。

**提取内容**：
- 错误码映射
- 错误处理路径
- 资源清理逻辑
- 异常情况处理

**示例**：
```json
{
  "error_handling": [
    {
      "error_condition": "Invalid Session ID in PLAY command",
      "handling": "Returns 454 Session Not Found",
      "resource_cleanup": "No cleanup performed",
      "fuzz_strategy": "Send PLAY with invalid session ID, then valid session ID to test state corruption"
    }
  ]
}
```

### 7. 协议扩展和自定义特性

**目标**：识别实现添加的非标准特性，这些可能是漏洞点。

**提取内容**：
- 自定义命令或头部
- 协议扩展
- 实现特定的选项

**示例**：
```json
{
  "custom_features": [
    {
      "feature": "HTTP tunneling support",
      "implementation": "RTSP over HTTP",
      "fuzz_strategy": "Test HTTP tunneling with malformed RTSP messages embedded"
    }
  ]
}
```

## 清洗策略

### 步骤 1：文档分类

将 DeepWiki 文档按主题分类：
- **协议实现类**：直接描述协议处理的文档（如 RTSP-Media-Server.md, Protocol-Implementations.md）
- **架构类**：描述整体架构的文档（如 Core-Architecture.md）
- **功能类**：描述特定功能的文档（如 Authentication-Systems.md）
- **工具类**：描述构建、配置等的文档（可忽略）

**优先级**：协议实现类 > 架构类 > 功能类

### 步骤 2：内容过滤

**保留**：
- 函数调用序列和代码路径
- 数据结构和状态定义
- 解析和验证逻辑
- 错误处理机制
- 配置选项和限制

**过滤**：
- 构建系统细节
- 安装配置步骤
- 不涉及协议处理的工具函数
- 纯架构描述（无具体实现细节）

### 步骤 3：关键信息提取

对每个文档提取：
1. **相关源文件**：从文档头部的 "Relevant source files" 提取
2. **关键函数**：识别处理协议消息的函数
3. **数据流**：从序列图和流程图提取
4. **约束条件**：从代码注释和描述中提取
5. **状态转换**：从状态机图提取

## 输出格式建议

建议创建一个新的 JSON 格式，专门用于实现知识：

```json
{
  "meta": {
    "protocol": "RTSP",
    "implementation": "live555",
    "source_repo": "rgaufman/live555",
    "extraction_date": "2025-01-XX"
  },
  "implementation_knowledge": {
    "code_structure": {
      "key_functions": [
        {
          "name": "handleCmd_SETUP",
          "file": "RTSPServer.cpp",
          "purpose": "Process RTSP SETUP command",
          "parameters": ["command", "url", "headers"],
          "return_codes": [200, 400, 454, 459]
        }
      ],
      "call_chains": [
        {
          "trigger": "SETUP command",
          "chain": [
            "RTSPServer::handleCmd_SETUP()",
            "lookupServerMediaSession()",
            "createNewClientSession()",
            "setupTransport()"
          ]
        }
      ]
    },
    "parsing_logic": [
      {
        "target": "Transport header",
        "function": "parseTransportHeader()",
        "validation": [
          "Must contain transport-protocol",
          "Must specify unicast or multicast",
          "Port range validation"
        ],
        "error_cases": [
          "Missing transport-protocol -> 400",
          "Invalid port range -> 400"
        ]
      }
    ],
    "state_management": {
      "session_storage": "Hash table keyed by Session ID",
      "session_lifecycle": {
        "creation": "On successful SETUP",
        "timeout": "65 seconds of inactivity",
        "cleanup": "Automatic on timeout or TEARDOWN"
      },
      "state_transitions": [
        {
          "from": "INIT",
          "command": "SETUP",
          "condition": "response_code == 200",
          "to": "READY",
          "code_location": "RTSPServer.cpp:463"
        }
      ]
    },
    "memory_operations": [
      {
        "location": "Session ID storage",
        "buffer_type": "Dynamic string",
        "max_length": "No explicit limit in code",
        "risk": "Potential DoS with extremely long session IDs",
        "fuzz_target": "Generate session IDs of various lengths (8, 100, 1000, 10000 bytes)"
      }
    ],
    "implementation_constraints": [
      {
        "constraint": "URL path length",
        "limit": "2048 bytes (implied by buffer size)",
        "fuzz_strategy": "Test with 2049, 4096, 8192 byte URLs"
      }
    ],
    "error_handling": [
      {
        "error": "Invalid Session ID",
        "detection": "Hash table lookup fails",
        "response": "454 Session Not Found",
        "resource_impact": "No resource cleanup needed",
        "fuzz_strategy": "Test with random session IDs, reused session IDs"
      }
    ],
    "custom_features": [
      {
        "feature": "HTTP Tunneling",
        "description": "RTSP over HTTP",
        "implementation": "setUpTunnelingOverHTTP()",
        "fuzz_strategy": "Embed malformed RTSP in HTTP requests"
      }
    ]
  },
  "fuzzing_guidance": {
    "high_priority_targets": [
      "Transport header parsing (complex validation logic)",
      "Session ID handling (no length limit)",
      "URL parsing (buffer management)"
    ],
    "test_case_templates": [
      {
        "name": "Long Session ID",
        "template": "SETUP rtsp://server/file RTSP/1.0\r\nCSeq: 1\r\nTransport: RTP/AVP/TCP\r\nSession: {LONG_STRING}\r\n\r\n",
        "variations": ["8 bytes", "100 bytes", "1000 bytes", "10000 bytes"]
      }
    ]
  }
}
```

## 与 RFC 知识的结合

DeepWiki 知识应该与 RFC 知识**互补使用**：

1. **RFC 知识**：生成符合/违反规范的测试用例
2. **DeepWiki 知识**：生成触发特定代码路径的测试用例
3. **结合使用**：生成既违反规范又能触发特定实现的测试用例

**示例**：
- RFC 知识：`Session ID must be at least 8 bytes`
- DeepWiki 知识：`Implementation stores Session ID in unbounded buffer`
- 结合测试：生成 7 字节的 Session ID（违反规范）和 10000 字节的 Session ID（触发实现漏洞）

## 工具建议

1. **文档解析器**：自动提取 mermaid 图表、代码块、函数名
2. **代码引用提取器**：从 "Sources:" 链接提取代码位置
3. **知识融合器**：将 DeepWiki 知识与 RFC 知识合并
