# Path Validation and Security

> **Relevant source files**
> * [Source/fspathtools.c](https://github.com/hfiref0x/LightFTP/blob/8b453c22/Source/fspathtools.c)
> * [Source/fspathtools.h](https://github.com/hfiref0x/LightFTP/blob/8b453c22/Source/fspathtools.h)

This document covers LightFTP's path validation and security mechanisms that prevent directory traversal attacks and ensure safe file system access. The implementation centers around the `fspathtools` module which provides robust path normalization and validation functions used throughout the FTP server.

For TLS/SSL security features, see [TLS/SSL Implementation](/hfiref0x/LightFTP/5.2-tlsssl-implementation). For overall security architecture, see [Security and Path Handling](/hfiref0x/LightFTP/5-security-and-path-handling).

## Path Security Overview

LightFTP implements multiple layers of path security to prevent unauthorized file system access:

| Security Layer | Function | Implementation |
| --- | --- | --- |
| Path Normalization | Resolves `.`, `..`, and duplicate separators | `ftp_normalize_path()` |
| Root Containment | Ensures paths stay within configured root | `ftp_effective_path()` |
| Directory Traversal Prevention | Blocks attempts to escape chroot | Path node processing |

The path validation system processes all file operations before they reach the underlying file system, creating a security barrier between FTP commands and file system access.

```

```

**Path Validation Process Flow**

Sources: [Source/fspathtools.c L52-L161](https://github.com/hfiref0x/LightFTP/blob/8b453c22/Source/fspathtools.c#L52-L161)

 [Source/fspathtools.h L11-L14](https://github.com/hfiref0x/LightFTP/blob/8b453c22/Source/fspathtools.h#L11-L14)

## Core Path Validation Functions

The `fspathtools` module provides three primary functions for path security:

### filepath()

Extracts the directory portion from a file path by finding the last path separator.

```

```

**filepath() Operation**

### ftp_normalize_path()

The core normalization function that processes path components using a linked list of `ftp_path_node` structures:

```

```

### ftp_effective_path()

Combines root directory, current working directory, and requested file path into a final normalized path.

Sources: [Source/fspathtools.c L15-L39](https://github.com/hfiref0x/LightFTP/blob/8b453c22/Source/fspathtools.c#L15-L39)

 [Source/fspathtools.c L41-L46](https://github.com/hfiref0x/LightFTP/blob/8b453c22/Source/fspathtools.c#L41-L46)

 [Source/fspathtools.c L163-L200](https://github.com/hfiref0x/LightFTP/blob/8b453c22/Source/fspathtools.c#L163-L200)

## Path Normalization Algorithm

The path normalization process uses a doubly-linked list to track path components and resolve directory navigation:

```

```

**Path Normalization State Machine**

The algorithm handles these specific cases:

| Input Component | Action | Security Benefit |
| --- | --- | --- |
| `.` | Skip entirely | Removes redundant current directory references |
| `..` | Remove previous node from list | Prevents traversal above intended directory |
| Normal directory | Add to node list | Preserves legitimate path components |
| Empty (from `//`) | Skip during parsing | Eliminates duplicate separators |

Sources: [Source/fspathtools.c L71-L160](https://github.com/hfiref0x/LightFTP/blob/8b453c22/Source/fspathtools.c#L71-L160)

## Directory Traversal Prevention

The normalization algorithm specifically prevents directory traversal attacks through its handling of `..` components:

```

```

**Directory Traversal Attack Mitigation**

Key security features:

* **Node-based processing**: Each `..` can only remove one previous directory level
* **Boundary enforcement**: Cannot traverse above the root directory
* **Memory safety**: Uses `x_malloc()` for safe memory allocation
* **Buffer protection**: Validates output buffer size before writing

Sources: [Source/fspathtools.c L86-L97](https://github.com/hfiref0x/LightFTP/blob/8b453c22/Source/fspathtools.c#L86-L97)

 [Source/fspathtools.c L129-L160](https://github.com/hfiref0x/LightFTP/blob/8b453c22/Source/fspathtools.c#L129-L160)

## Integration with FTP Server

The path validation functions integrate with the main FTP server through `ftp_effective_path()`, which is called for all file operations:

```

```

**Path Validation Integration Flow**

The `ftp_effective_path()` function ensures that:

1. **Absolute paths** (starting with `/`) are normalized relative to the FTP root
2. **Relative paths** are combined with the current working directory first
3. **Final paths** are always contained within the configured root directory
4. **Buffer overflow protection** prevents writing beyond allocated memory

Sources: [Source/fspathtools.c L163-L200](https://github.com/hfiref0x/LightFTP/blob/8b453c22/Source/fspathtools.c#L163-L200)

 [Source/fspathtools.h L13-L14](https://github.com/hfiref0x/LightFTP/blob/8b453c22/Source/fspathtools.h#L13-L14)

## Error Handling and Edge Cases

The path validation system handles several edge cases and error conditions:

| Condition | Handling | Function |
| --- | --- | --- |
| NULL pointers | Return 0 (failure) | All functions |
| Insufficient buffer | Return 0, free nodes | `ftp_normalize_path()` |
| Empty paths | Handle gracefully | `ftp_effective_path()` |
| Root-only result | Remove trailing slash | `ftp_effective_path()` |
| Memory allocation failure | Handled by `x_malloc()` | Node creation |

The implementation ensures memory cleanup even in error conditions by freeing allocated `ftp_path_node` structures when operations fail.

Sources: [Source/fspathtools.c L60-L61](https://github.com/hfiref0x/LightFTP/blob/8b453c22/Source/fspathtools.c#L60-L61)

 [Source/fspathtools.c L148-L154](https://github.com/hfiref0x/LightFTP/blob/8b453c22/Source/fspathtools.c#L148-L154)

 [Source/fspathtools.c L191-L197](https://github.com/hfiref0x/LightFTP/blob/8b453c22/Source/fspathtools.c#L191-L197)