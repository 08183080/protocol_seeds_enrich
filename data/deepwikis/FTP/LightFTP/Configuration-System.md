# Configuration System

> **Relevant source files**
> * [Source/cfgparse.c](https://github.com/hfiref0x/LightFTP/blob/8b453c22/Source/cfgparse.c)
> * [Source/cfgparse.h](https://github.com/hfiref0x/LightFTP/blob/8b453c22/Source/cfgparse.h)

This document covers LightFTP's configuration parsing system, which reads and processes the `fftp.conf` configuration file during server initialization. The system provides a simple INI-style parser that extracts server settings and user account definitions for use throughout the application.

For information about the specific configuration options and file format, see [Configuration Reference](/hfiref0x/LightFTP/2.2-configuration-reference). For details on how the parsed configuration is used during server initialization, see [Core Server Implementation](/hfiref0x/LightFTP/4-core-server-implementation).

## Overview

The configuration system consists of two main components: a file loader that reads the entire configuration file into memory, and a parser that extracts specific key-value pairs from named sections. The system uses a streaming parser approach that processes the configuration text character by character to locate sections and extract values.

```

```

*Sources: Source/cfgparse.c, Source/cfgparse.h*

## Configuration File Format

The configuration parser expects an INI-style format with sections defined by square brackets and key-value pairs separated by equals signs. The parser supports comments beginning with `#` and automatically skips whitespace and blank lines.

```

```

*Sources: Source/cfgparse.c:17-45, Source/cfgparse.c:49-200*

## Core API Functions

The configuration system exposes two primary functions through its public interface:

| Function | Purpose | Return Value |
| --- | --- | --- |
| `config_init()` | Load entire configuration file into memory | Pointer to allocated buffer or NULL on failure |
| `config_parse()` | Extract specific key value from named section | 1 on success, 0 on failure |

### config_init Function

The `config_init()` function handles file I/O operations to load the configuration file into a dynamically allocated buffer.

```

```

*Sources: Source/cfgparse.c:202-225*

### config_parse Function

The `config_parse()` function implements a state machine parser that locates the requested section and extracts the specified key's value.

```

```

*Sources: Source/cfgparse.c:49-200*

## Implementation Details

### Comment and Whitespace Handling

The `skip_comments_and_blanks()` function provides preprocessing to handle formatting elements in the configuration file. It processes characters in sequence, skipping spaces and newlines, and when it encounters a `#` character, it skips all characters until the next newline.

```

```

*Sources: Source/cfgparse.c:17-45*

### Memory Management Integration

The configuration system integrates with LightFTP's custom memory management through the `x_malloc()` function, ensuring consistent error handling and memory allocation patterns throughout the application.

| Component | Memory Usage | Error Handling |
| --- | --- | --- |
| File buffer | `x_malloc(file_size + 1)` | Returns NULL on allocation failure |
| Value extraction | Stack-allocated temporary buffers | Bounds checking with `value_size_max` |
| String operations | In-place parsing with pointer arithmetic | Length validation to prevent overflows |

*Sources: Source/cfgparse.c:214, Source/cfgparse.h:14-15*

## Integration with Application

The configuration system serves as a foundation component used during application initialization. The typical usage pattern involves loading the configuration file once during startup and then making multiple parsing calls to extract different configuration values.

```

```

*Sources: Source/cfgparse.c:202-225, Source/cfgparse.c:49-200*

The configuration values extracted through this system populate the server's runtime configuration structures and user account definitions, which are then used throughout the FTP server's operation for access control, network settings, and feature enablement.