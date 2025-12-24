# Development and Building

> **Relevant source files**
> * [Source/Debug/subdir.mk](https://github.com/hfiref0x/LightFTP/blob/8b453c22/Source/Debug/subdir.mk)
> * [Source/Release/makefile](https://github.com/hfiref0x/LightFTP/blob/8b453c22/Source/Release/makefile)
> * [Source/Release/subdir.mk](https://github.com/hfiref0x/LightFTP/blob/8b453c22/Source/Release/subdir.mk)
> * [appveyor.yml](https://github.com/hfiref0x/LightFTP/blob/8b453c22/appveyor.yml)

This page provides an overview of the LightFTP development environment, build system, and development workflow. It covers the essential information needed to compile, modify, and contribute to the LightFTP codebase.

For detailed build system internals and makefile structure, see [Build System](/hfiref0x/LightFTP/7.1-build-system). For debugging techniques and development best practices, see [Debugging and Development](/hfiref0x/LightFTP/7.2-debugging-and-development).

## Build System Overview

LightFTP uses a traditional makefile-based build system with separate configurations for debug and release builds. The build system is organized around Eclipse CDT auto-generated makefiles that provide standardized compilation rules and dependency tracking.

### Build Structure

```

```

Sources: [Source/Release/subdir.mk L6-L12](https://github.com/hfiref0x/LightFTP/blob/8b453c22/Source/Release/subdir.mk#L6-L12)

 [Source/Debug/subdir.mk L6-L12](https://github.com/hfiref0x/LightFTP/blob/8b453c22/Source/Debug/subdir.mk#L6-L12)

 [Source/Release/makefile L28-L31](https://github.com/hfiref0x/LightFTP/blob/8b453c22/Source/Release/makefile#L28-L31)

### Core Source Files

The build system compiles six primary C source files into the final `fftp` executable:

| Source File | Purpose |
| --- | --- |
| `main.c` | Application entry point and initialization |
| `ftpserv.c` | Core FTP server implementation |
| `cfgparse.c` | Configuration file parsing |
| `fspathtools.c` | File system path validation and security |
| `ftpconst.c` | FTP protocol constants and responses |
| `x_malloc.c` | Memory management utilities |

Sources: [Source/Release/subdir.mk L6-L12](https://github.com/hfiref0x/LightFTP/blob/8b453c22/Source/Release/subdir.mk#L6-L12)

 [Source/Debug/subdir.mk L6-L12](https://github.com/hfiref0x/LightFTP/blob/8b453c22/Source/Debug/subdir.mk#L6-L12)

## Dependencies and Requirements

### System Dependencies

LightFTP requires the following system libraries and tools:

* **GCC Compiler**: C99 compliant compiler with GNU extensions
* **libgnutls28-dev**: GnuTLS library for TLS/SSL support
* **pthread**: POSIX threads library for concurrent client handling

### Compiler Requirements

The build system requires specific compiler capabilities and standards:

```

```

Sources: [Source/Release/subdir.mk L35](https://github.com/hfiref0x/LightFTP/blob/8b453c22/Source/Release/subdir.mk#L35-L35)

 [Source/Debug/subdir.mk L35](https://github.com/hfiref0x/LightFTP/blob/8b453c22/Source/Debug/subdir.mk#L35-L35)

 [appveyor.yml L9](https://github.com/hfiref0x/LightFTP/blob/8b453c22/appveyor.yml#L9-L9)

## Build Configurations

### Release Configuration

The release build optimizes for performance and production deployment:

**Compiler Flags:**

* `-O3`: Maximum optimization level
* `-fno-ident`: Remove compiler identification
* `-Wno-unused-parameter -Wno-unused-result`: Suppress specific warnings

**Location:** [Source/Release/subdir.mk L35](https://github.com/hfiref0x/LightFTP/blob/8b453c22/Source/Release/subdir.mk#L35-L35)

### Debug Configuration

The debug build includes debugging symbols and disables optimization:

**Compiler Flags:**

* `-O0`: No optimization
* `-g3`: Maximum debugging information
* Additional `-D_GNU_SOURCE` define

**Location:** [Source/Debug/subdir.mk L35](https://github.com/hfiref0x/LightFTP/blob/8b453c22/Source/Debug/subdir.mk#L35-L35)

### Build Process Flow

```

```

Sources: [Source/Release/makefile L28-L31](https://github.com/hfiref0x/LightFTP/blob/8b453c22/Source/Release/makefile#L28-L31)

 [Source/Release/subdir.mk L32-L37](https://github.com/hfiref0x/LightFTP/blob/8b453c22/Source/Release/subdir.mk#L32-L37)

## CI/CD Pipeline

### AppVeyor Configuration

LightFTP uses AppVeyor for continuous integration on Ubuntu 18.04:

**Build Environment:**

* Image: `Ubuntu1804`
* Version pattern: `2.0.1.{build}`
* Dependency installation: `sudo apt-get install libgnutls28-dev`

**Build Process:**

1. Navigate to `Source/Release` directory
2. Execute `CC=gcc make` command

```

```

Sources: [appveyor.yml L1-L15](https://github.com/hfiref0x/LightFTP/blob/8b453c22/appveyor.yml#L1-L15)

## Development Workflow

### Building the Project

**Release Build:**

```

```

**Debug Build:**

```

```

**Clean Build:**

```

```

### Build Targets

| Target | Description | Location |
| --- | --- | --- |
| `all` | Default target, builds `fftp` executable | [Source/Release/makefile L25](https://github.com/hfiref0x/LightFTP/blob/8b453c22/Source/Release/makefile#L25-L25) |
| `fftp` | Links object files into final executable | [Source/Release/makefile L28](https://github.com/hfiref0x/LightFTP/blob/8b453c22/Source/Release/makefile#L28-L28) |
| `clean` | Removes build artifacts and executables | [Source/Release/makefile L36](https://github.com/hfiref0x/LightFTP/blob/8b453c22/Source/Release/makefile#L36-L36) |

### Dependency Tracking

The build system automatically generates dependency files (`.d` extension) for each source file to track header dependencies and enable incremental builds. These files are included conditionally to avoid errors during clean builds.

Sources: [Source/Release/makefile L14-L18](https://github.com/hfiref0x/LightFTP/blob/8b453c22/Source/Release/makefile#L14-L18)

 [Source/Release/subdir.mk L22-L28](https://github.com/hfiref0x/LightFTP/blob/8b453c22/Source/Release/subdir.mk#L22-L28)