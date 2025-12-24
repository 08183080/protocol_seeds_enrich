# Build System

> **Relevant source files**
> * [CMakeLists.txt](https://github.com/kamailio/kamailio/blob/2b4e9f8b/CMakeLists.txt)
> * [Makefile](https://github.com/kamailio/kamailio/blob/2b4e9f8b/Makefile)
> * [cmake/cmake-uninstall.cmake.in](https://github.com/kamailio/kamailio/blob/2b4e9f8b/cmake/cmake-uninstall.cmake.in)
> * [src/Makefile](https://github.com/kamailio/kamailio/blob/2b4e9f8b/src/Makefile)
> * [src/Makefile.defs](https://github.com/kamailio/kamailio/blob/2b4e9f8b/src/Makefile.defs)
> * [src/Makefile.groups](https://github.com/kamailio/kamailio/blob/2b4e9f8b/src/Makefile.groups)
> * [src/Makefile.modules](https://github.com/kamailio/kamailio/blob/2b4e9f8b/src/Makefile.modules)
> * [src/Makefile.shared](https://github.com/kamailio/kamailio/blob/2b4e9f8b/src/Makefile.shared)
> * [src/Makefile.targets](https://github.com/kamailio/kamailio/blob/2b4e9f8b/src/Makefile.targets)
> * [src/Makefile.utils](https://github.com/kamailio/kamailio/blob/2b4e9f8b/src/Makefile.utils)
> * [src/modules/auth_radius/Makefile](https://github.com/kamailio/kamailio/blob/2b4e9f8b/src/modules/auth_radius/Makefile)
> * [src/modules/auth_radius/cfg/dictionary.kamailio](https://github.com/kamailio/kamailio/blob/2b4e9f8b/src/modules/auth_radius/cfg/dictionary.kamailio)
> * [src/modules/auth_radius/cfg/dictionary.sip-router](https://github.com/kamailio/kamailio/blob/2b4e9f8b/src/modules/auth_radius/cfg/dictionary.sip-router)
> * [src/modules/topos_htable/Makefile](https://github.com/kamailio/kamailio/blob/2b4e9f8b/src/modules/topos_htable/Makefile)
> * [src/modules/topos_htable/doc/Makefile](https://github.com/kamailio/kamailio/blob/2b4e9f8b/src/modules/topos_htable/doc/Makefile)
> * [src/modules/topos_htable/doc/topos_htable.xml](https://github.com/kamailio/kamailio/blob/2b4e9f8b/src/modules/topos_htable/doc/topos_htable.xml)
> * [src/modules/topos_htable/doc/topos_htable_admin.xml](https://github.com/kamailio/kamailio/blob/2b4e9f8b/src/modules/topos_htable/doc/topos_htable_admin.xml)
> * [src/modules/topos_htable/topos_htable_mod.c](https://github.com/kamailio/kamailio/blob/2b4e9f8b/src/modules/topos_htable/topos_htable_mod.c)
> * [src/modules/topos_htable/topos_htable_storage.c](https://github.com/kamailio/kamailio/blob/2b4e9f8b/src/modules/topos_htable/topos_htable_storage.c)
> * [src/modules/topos_htable/topos_htable_storage.h](https://github.com/kamailio/kamailio/blob/2b4e9f8b/src/modules/topos_htable/topos_htable_storage.h)

The Kamailio build system provides the framework for compiling, installing, and packaging the SIP server. It leverages GNU Make as its primary build tool, with additional support for CMake. This document explains the architecture and components of the build system, how modules are compiled and grouped, and the configuration options available.

For information about compiling specific modules, see [Module Compilation System](/kamailio/kamailio/5.2-module-compilation-system). For packaging and deployment details, see [Packaging and Deployment](/kamailio/kamailio/6-packaging-and-deployment).

## Overview of the Build System

Kamailio's build system is designed to be flexible and extensible, allowing users to customize their builds according to their specific needs. The system is primarily make-based with a hierarchical structure of makefiles that handle different aspects of the build process.

```mermaid
flowchart TD

root["Root Makefile"]
src["src/Makefile"]
defs["src/Makefile.defs"]
groups["src/Makefile.groups"]
modules["src/Makefile.modules"]
utils["src/Makefile.utils"]
shared["src/Makefile.shared"]
targets["src/Makefile.targets"]
rules["src/Makefile.rules"]
dirs["src/Makefile.dirs"]
configmak["config.mak"]
moduleslst["modules.lst"]
mod1["Module 1 Makefile"]
mod2["Module 2 Makefile"]
mod3["Module 3 Makefile"]

root --> src
src --> defs
src --> groups
src --> modules
src --> utils
src --> shared
src --> targets
src --> rules
src --> dirs
defs --> configmak
groups --> moduleslst
modules --> mod1
modules --> mod2
modules --> mod3

subgraph subGraph1 ["Module Build"]
    mod1
    mod2
    mod3
end

subgraph Configuration ["Configuration"]
    configmak
    moduleslst
end
```

Sources: [Makefile L1-L57](https://github.com/kamailio/kamailio/blob/2b4e9f8b/Makefile#L1-L57)

 [src/Makefile L1-L772](https://github.com/kamailio/kamailio/blob/2b4e9f8b/src/Makefile#L1-L772)

 [src/Makefile.defs L1-L1317](https://github.com/kamailio/kamailio/blob/2b4e9f8b/src/Makefile.defs#L1-L1317)

 [src/Makefile.groups L1-L552](https://github.com/kamailio/kamailio/blob/2b4e9f8b/src/Makefile.groups#L1-L552)

 [src/Makefile.modules L1-L294](https://github.com/kamailio/kamailio/blob/2b4e9f8b/src/Makefile.modules#L1-L294)

## Key Components

The build system consists of several key components:

1. **Root Makefile**: Acts as an entry point, forwarding commands to the src directory.
2. **src/Makefile**: The main makefile that orchestrates the build process.
3. **Makefile.defs**: Defines compiler options, platform-specific settings, and build flags.
4. **Makefile.groups**: Defines module groups for organizing and building related modules.
5. **Makefile.modules**: Template for building individual modules.
6. **config.mak**: Generated file that stores build configuration.
7. **modules.lst**: Generated file that stores the list of modules to be built.

### Makefile Hierarchy and Relationships

```mermaid
flowchart TD

root["Root Makefile"]
src["src/Makefile"]
configmak["config.mak"]
moduleslst["modules.lst"]
defs["Makefile.defs<br>Compiler settings,<br>platform detection"]
dirs["Makefile.dirs<br>Installation directories"]
rules["Makefile.rules<br>Compilation rules"]
targets["Makefile.targets<br>Build targets"]
groups["Makefile.groups<br>Module grouping"]
modmk["Makefile.modules<br>Module build template"]
shared["Makefile.shared<br>Helper functions"]
utils["Makefile.utils<br>Utility build template"]
mod1["modules/*/Makefile"]
util1["utils/*/Makefile"]

root --> src
src --> defs
src --> dirs
src --> rules
src --> targets
src --> groups
src --> shared
defs --> configmak
groups --> moduleslst
modmk --> mod1
utils --> util1

subgraph Utilities ["Utilities"]
    shared
    utils
end

subgraph subGraph3 ["Module Management"]
    groups
    modmk
end

subgraph subGraph2 ["Build Definitions"]
    defs
    dirs
    rules
    targets
end

subgraph subGraph1 ["Core Build Control"]
    src
    configmak
    moduleslst
end

subgraph subGraph0 ["Entry Point"]
    root
end
```

Sources: [Makefile L1-L57](https://github.com/kamailio/kamailio/blob/2b4e9f8b/Makefile#L1-L57)

 [src/Makefile L1-L772](https://github.com/kamailio/kamailio/blob/2b4e9f8b/src/Makefile#L1-L772)

 [src/Makefile.defs L1-L1317](https://github.com/kamailio/kamailio/blob/2b4e9f8b/src/Makefile.defs#L1-L1317)

 [src/Makefile.groups L1-L552](https://github.com/kamailio/kamailio/blob/2b4e9f8b/src/Makefile.groups#L1-L552)

 [src/Makefile.modules L1-L294](https://github.com/kamailio/kamailio/blob/2b4e9f8b/src/Makefile.modules#L1-L294)

 [src/Makefile.utils L1-L154](https://github.com/kamailio/kamailio/blob/2b4e9f8b/src/Makefile.utils#L1-L154)

## Build Process Flow

The build process follows a specific sequence to ensure proper dependency resolution and compilation.

```mermaid
flowchart TD

start["make"]
loadcfg["Load configuration<br>config.mak"]
modinit["Initialize modules<br>modules.lst"]
compile["Compile core"]
compilemods["Compile modules"]
link["Link executables"]
install["Install"]
cfg["make cfg<br>Generate config.mak"]
modcfg["make modules-cfg<br>Generate modules.lst"]

start --> loadcfg
loadcfg --> modinit
modinit --> compile
compile --> compilemods
compilemods --> link
link --> install
start --> cfg
modcfg --> loadcfg

subgraph subGraph0 ["Configuration Phase"]
    cfg
    modcfg
    cfg --> modcfg
end
```

Sources: [src/Makefile L94-L137](https://github.com/kamailio/kamailio/blob/2b4e9f8b/src/Makefile#L94-L137)

 [src/Makefile L283-L340](https://github.com/kamailio/kamailio/blob/2b4e9f8b/src/Makefile#L283-L340)

 [src/Makefile L342-L383](https://github.com/kamailio/kamailio/blob/2b4e9f8b/src/Makefile#L342-L383)

## Module Management System

Kamailio organizes modules into groups to simplify building related functionality. The module system allows for:

1. Selecting which modules to compile based on functionality
2. Handling module dependencies
3. Grouping modules for packaging

### Module Groups

Modules are organized into logical groups in `Makefile.groups`, which allows for easy selection of related modules.

```mermaid
flowchart TD

basic["Basic Modules<br>core functionality"]
db["Database Modules<br>storage backends"]
presence["Presence Modules<br>SIP presence extensions"]
utils["Utility Modules<br>additional features"]
tls["TLS Modules<br>secure communications"]
default["Default Group<br>compiled by default"]
standard["Standard Group<br>no external dependencies"]
common["Common Group<br>widespread use modules"]
kstandard["Standard Package<br>main package"]
kmysql["MySQL Package"]
kpresence["Presence Package"]
ktls["TLS Package"]

basic --> default
basic --> standard
basic --> kstandard
db --> default
db --> common
tls --> common
tls --> ktls
presence --> common
presence --> kpresence

subgraph subGraph2 ["Package Groups"]
    kstandard
    kmysql
    kpresence
    ktls
end

subgraph subGraph1 ["Build Groups"]
    default
    standard
    common
end

subgraph subGraph0 ["Module Groups Definitions"]
    basic
    db
    presence
    utils
    tls
end
```

Sources: [src/Makefile.groups L12-L290](https://github.com/kamailio/kamailio/blob/2b4e9f8b/src/Makefile.groups#L12-L290)

 [src/Makefile.groups L295-L346](https://github.com/kamailio/kamailio/blob/2b4e9f8b/src/Makefile.groups#L295-L346)

 [src/Makefile.groups L350-L550](https://github.com/kamailio/kamailio/blob/2b4e9f8b/src/Makefile.groups#L350-L550)

### Module Compilation Flow

The compilation of modules follows this process:

```mermaid
flowchart TD

modules["List of modules<br>from modules.lst"]
exclude["Apply exclude_modules<br>filter out modules"]
include["Apply include_modules<br>add specific modules"]
static["Handle static_modules<br>compile into core"]
dynamic["Compile dynamic modules<br>.so files"]
excludevar["exclude_modules<br>modules to skip"]
includevar["include_modules<br>modules to add"]
staticvar["static_modules<br>modules for static linking"]
groupinclude["group_include<br>predefined module groups"]

modules --> exclude
exclude --> include
include --> static
include --> dynamic
excludevar --> exclude
includevar --> include
staticvar --> static
groupinclude --> include

subgraph subGraph0 ["Module Selection Variables"]
    excludevar
    includevar
    staticvar
    groupinclude
end
```

Sources: [src/Makefile L62-L83](https://github.com/kamailio/kamailio/blob/2b4e9f8b/src/Makefile#L62-L83)

 [src/Makefile L142-L183](https://github.com/kamailio/kamailio/blob/2b4e9f8b/src/Makefile#L142-L183)

 [src/Makefile L398-L505](https://github.com/kamailio/kamailio/blob/2b4e9f8b/src/Makefile#L398-L505)

## Build Configuration System

The build configuration system allows customizing the compilation process through various mechanisms.

### Key Configuration Variables

| Variable | Description | Example |
| --- | --- | --- |
| FLAVOUR | SIP server flavor | kamailio |
| CC | C compiler | gcc |
| CFLAGS | C compiler flags | -O2 -g |
| exclude_modules | Modules to exclude from build | db_mysql |
| include_modules | Modules to include in build | dialog |
| PREFIX | Installation prefix | /usr/local |
| DESTDIR | Destination directory for staged installs | /tmp/package |
| LIBDIR | Library directory name | lib64 |
| MAIN_NAME | Main binary name | kamailio |

Sources: [src/Makefile.defs L63-L91](https://github.com/kamailio/kamailio/blob/2b4e9f8b/src/Makefile.defs#L63-L91)

 [src/Makefile.defs L543-L562](https://github.com/kamailio/kamailio/blob/2b4e9f8b/src/Makefile.defs#L543-L562)

### Configuration Generation

The build system generates two main configuration files:

1. **config.mak**: Contains build settings like compiler flags, paths, etc.
2. **modules.lst**: Contains the list of modules to compile.

These files are generated with the `make cfg` and `make modules-cfg` commands respectively.

```mermaid
flowchart TD

cfg["make cfg"]
modcfg["make modules-cfg"]
configmak["config.mak"]
moduleslst["modules.lst"]
compiler["Compiler settings<br>CC, CFLAGS, LDFLAGS"]
paths["Path settings<br>PREFIX, LIBDIR"]
features["Feature flags<br>TLS_HOOKS, SCTP"]
groups["Module groups<br>basic, db, presence, etc."]
modules["Module lists<br>include_modules, exclude_modules"]

cfg --> configmak
modcfg --> moduleslst
compiler --> configmak
paths --> configmak
features --> configmak
groups --> moduleslst
modules --> moduleslst

subgraph subGraph1 ["Variables from Makefile.groups"]
    groups
    modules
end

subgraph subGraph0 ["Variables from Makefile.defs"]
    compiler
    paths
    features
end
```

Sources: [src/Makefile L283-L340](https://github.com/kamailio/kamailio/blob/2b4e9f8b/src/Makefile#L283-L340)

 [src/Makefile L311-L339](https://github.com/kamailio/kamailio/blob/2b4e9f8b/src/Makefile#L311-L339)

## Platform Support

The build system detects the host architecture and operating system to apply platform-specific optimizations and settings.

```mermaid
flowchart TD

detect["Platform Detection"]
compiler["Compiler Detection"]
arch["Architecture Detection"]
os["OS Detection"]
gcc["GCC Options"]
clang["Clang Options"]
icc["Intel Compiler Options"]
suncc["Sun Compiler Options"]
x86["i386 Optimizations"]
x86_64["x86_64 Optimizations"]
arm["ARM Settings"]
sparc["SPARC Settings"]
linux["Linux Paths"]
bsd["BSD Paths"]
solaris["Solaris Settings"]
darwin["macOS Settings"]

detect --> compiler
detect --> arch
detect --> os
compiler --> gcc
compiler --> clang
compiler --> icc
compiler --> suncc
arch --> x86
arch --> x86_64
arch --> arm
arch --> sparc
os --> linux
os --> bsd
os --> solaris
os --> darwin

subgraph subGraph2 ["OS-specific Settings"]
    linux
    bsd
    solaris
    darwin
end

subgraph subGraph1 ["Architecture-specific Settings"]
    x86
    x86_64
    arm
    sparc
end

subgraph subGraph0 ["Compiler-specific Settings"]
    gcc
    clang
    icc
    suncc
end
```

Sources: [src/Makefile.defs L126-L151](https://github.com/kamailio/kamailio/blob/2b4e9f8b/src/Makefile.defs#L126-L151)

 [src/Makefile.defs L273-L355](https://github.com/kamailio/kamailio/blob/2b4e9f8b/src/Makefile.defs#L273-L355)

 [src/Makefile.defs L358-L452](https://github.com/kamailio/kamailio/blob/2b4e9f8b/src/Makefile.defs#L358-L452)

 [src/Makefile.defs L479-L531](https://github.com/kamailio/kamailio/blob/2b4e9f8b/src/Makefile.defs#L479-L531)

## Installation System

The installation process handles placing files in their appropriate directories based on the configured paths.

### Installation Directory Structure

```mermaid
flowchart TD

prefix["Installation Prefix<br>PREFIX=/usr/local"]
bin["bin_dir<br>sbin/"]
lib["lib_dir<br>lib/kamailio/"]
cfg["cfg_dir<br>etc/kamailio/"]
share["share_dir<br>share/kamailio/"]
doc["doc_dir<br>share/doc/kamailio/"]
man["man_dir<br>share/man/"]
modules["modules_dir<br>lib/kamailio/modules/"]
binaries["Binary Files<br>kamailio executable"]
modfiles["Module Files<br>.so shared libraries"]
cfgs["Config Files<br>kamailio.cfg"]
docs["Documentation<br>README, man pages"]

prefix --> bin
prefix --> lib
prefix --> cfg
prefix --> share
prefix --> doc
prefix --> man
lib --> modules
bin --> binaries
modules --> modfiles
cfg --> cfgs
doc --> docs
man --> docs

subgraph subGraph0 ["Installation Targets"]
    binaries
    modfiles
    cfgs
    docs
end
```

Sources: [src/Makefile.defs L468-L511](https://github.com/kamailio/kamailio/blob/2b4e9f8b/src/Makefile.defs#L468-L511)

 [src/Makefile L653-L700](https://github.com/kamailio/kamailio/blob/2b4e9f8b/src/Makefile#L653-L700)

 [src/Makefile L702-L746](https://github.com/kamailio/kamailio/blob/2b4e9f8b/src/Makefile#L702-L746)

 [src/Makefile L789-L792](https://github.com/kamailio/kamailio/blob/2b4e9f8b/src/Makefile#L789-L792)

## Build Targets

The build system provides various targets for different tasks:

| Target | Description |
| --- | --- |
| all | Build the core and all modules |
| modules | Build all modules |
| modules-list | List all modules to be built |
| install | Install binaries, modules, and config files |
| clean | Remove compiled objects and binaries |
| proper | More thorough clean |
| distclean | Completely clean the build system |
| tar | Create a source tarball |
| deb | Build Debian package |
| sunpkg | Build Solaris package |

Sources: [src/Makefile.targets L1-L41](https://github.com/kamailio/kamailio/blob/2b4e9f8b/src/Makefile.targets#L1-L41)

 [src/Makefile L382-L383](https://github.com/kamailio/kamailio/blob/2b4e9f8b/src/Makefile#L382-L383)

 [src/Makefile L558-L647](https://github.com/kamailio/kamailio/blob/2b4e9f8b/src/Makefile#L558-L647)

## CMake Support

In addition to the Make-based build system, Kamailio also provides a CMake build system for platforms where CMake is preferred.

```mermaid
flowchart TD

cmake["CMake Build System"]
makesys["Make Build System"]
cmakelists["CMakeLists.txt"]
makefiles["Makefile hierarchy"]
cmakemodules["cmake/modules/"]
cmakebuildtype["cmake/BuildType.cmake"]
findmodules["Find modules for dependencies"]
configtypes["Build configuration types"]
install["Installation rules"]
uninstall["Uninstall support"]
packaging["CPack packaging support"]

cmake --> cmakelists
makesys --> makefiles
cmakelists --> cmakemodules
cmakelists --> cmakebuildtype
cmakemodules --> findmodules
cmake --> configtypes
cmake --> install
cmake --> uninstall
cmake --> packaging

subgraph subGraph0 ["CMake Features"]
    configtypes
    install
    uninstall
    packaging
end
```

Sources: [CMakeLists.txt L1-L86](https://github.com/kamailio/kamailio/blob/2b4e9f8b/CMakeLists.txt#L1-L86)

 [cmake/cmake-uninstall.cmake.in L1-L35](https://github.com/kamailio/kamailio/blob/2b4e9f8b/cmake/cmake-uninstall.cmake.in#L1-L35)

## Summary

The Kamailio build system provides a flexible and powerful framework for compiling, customizing, and installing the SIP server. It handles platform detection, module management, dependency resolution, and installation through a hierarchical structure of makefiles. By understanding the components and flow of the build system, users can customize their Kamailio builds to meet their specific requirements.

Sources: [Makefile L1-L57](https://github.com/kamailio/kamailio/blob/2b4e9f8b/Makefile#L1-L57)

 [src/Makefile L1-L772](https://github.com/kamailio/kamailio/blob/2b4e9f8b/src/Makefile#L1-L772)

 [src/Makefile.defs L1-L1317](https://github.com/kamailio/kamailio/blob/2b4e9f8b/src/Makefile.defs#L1-L1317)

 [src/Makefile.groups L1-L552](https://github.com/kamailio/kamailio/blob/2b4e9f8b/src/Makefile.groups#L1-L552)

 [src/Makefile.modules L1-L294](https://github.com/kamailio/kamailio/blob/2b4e9f8b/src/Makefile.modules#L1-L294)