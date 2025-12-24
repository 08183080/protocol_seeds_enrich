# File System Operations

> **Relevant source files**
> * [src/stat_cache.c](https://github.com/lighttpd/lighttpd1.4/blob/3d550097/src/stat_cache.c)
> * [src/stat_cache.h](https://github.com/lighttpd/lighttpd1.4/blob/3d550097/src/stat_cache.h)

This document details how lighttpd interacts with the file system, covering the stat cache system, file metadata handling, directory monitoring, and related file operations. The stat cache is a critical performance optimization that minimizes expensive file system calls by caching file metadata.

For information about buffer and memory management used by file operations, see [Memory Management](/lighttpd/lighttpd1.4/3.1-memory-management). For details on event-driven network I/O used alongside file operations, see [Event Handling and Networking](/lighttpd/lighttpd1.4/3.3-event-handling-and-networking).

## 1. Stat Cache System Overview

The stat cache system caches the results of `stat()` calls to reduce disk I/O and improve server performance. It maintains metadata about files and directories, provides file descriptors for open files, and monitors the file system for changes to invalidate stale cache entries.

```mermaid
flowchart TD

A["Request Processing"]
B["stat_cache_get_entry()"]
C["Cache Hit?"]
D["Return cached metadata"]
E["stat_cache_refresh_entry()"]
F["stat() and cache result"]
G["stat() file"]
H["Update cache entry"]
I["Periodic Cleanup"]
J["stat_cache_trigger_cleanup()"]
K["Remove entries older than threshold"]
L["File System Changes"]
M["Monitoring Engine<br>(FAM/inotify/kqueue)"]
N["Invalidate affected entries"]

A --> B
B --> C
C --> D
C --> E
C --> F
E --> G
G --> H
F --> H
H --> D
I --> J
J --> K
L --> M
M --> N
```

Sources: [src/stat_cache.c L42-L51](https://github.com/lighttpd/lighttpd1.4/blob/3d550097/src/stat_cache.c#L42-L51)

 [src/stat_cache.c L798-L828](https://github.com/lighttpd/lighttpd1.4/blob/3d550097/src/stat_cache.c#L798-L828)

 [src/stat_cache.c L1259-L1328](https://github.com/lighttpd/lighttpd1.4/blob/3d550097/src/stat_cache.c#L1259-L1328)

 [src/stat_cache.c L1330-L1381](https://github.com/lighttpd/lighttpd1.4/blob/3d550097/src/stat_cache.c#L1330-L1381)

 [src/stat_cache.c L1477-L1523](https://github.com/lighttpd/lighttpd1.4/blob/3d550097/src/stat_cache.c#L1477-L1523)

## 2. Stat Cache Entry Structure

The stat cache stores file metadata in `stat_cache_entry` structures organized in a splay tree for efficient lookups.

```mermaid
classDiagram
    class stat_cache {
        int stat_cache_engine
        splay_tree* files
        struct stat_cache_fam* scf
    }
    class stat_cache_entry {
        buffer name
        unix_time64_t stat_ts
        int fd
        int refcnt
        void* fam_dir
        buffer etag
        buffer content_type
        struct stat st
    }
    class splay_tree {
        int key
        void* data
        splay_tree* left
        splay_tree* right
    }
    stat_cache --> splay_tree : contains
    splay_tree --> stat_cache_entry : contains as data
```

Sources: [src/stat_cache.h L14-L25](https://github.com/lighttpd/lighttpd1.4/blob/3d550097/src/stat_cache.h#L14-L25)

 [src/stat_cache.c L44-L50](https://github.com/lighttpd/lighttpd1.4/blob/3d550097/src/stat_cache.c#L44-L50)

## 3. Cache Engines

The stat cache system supports multiple engines with different caching strategies:

| Engine | Description | Use Case |
| --- | --- | --- |
| Simple (default) | Caches entries for 2 seconds | Good balance of performance and freshness |
| None/Disable | No caching, always stat() | When absolute freshness is required |
| FAM/inotify/kqueue | Uses filesystem monitoring | For better performance with automatic invalidation |

The engine is selected during server configuration using the `server.stat-cache-engine` directive.

```mermaid
flowchart TD

A["stat_cache_choose_engine()"]
B["Engine Type"]
C["STAT_CACHE_ENGINE_SIMPLE"]
D["STAT_CACHE_ENGINE_NONE"]
E["STAT_CACHE_ENGINE_FAM"]
F["STAT_CACHE_ENGINE_INOTIFY"]
G["STAT_CACHE_ENGINE_KQUEUE"]
H["stat_cache_init_fam()"]
I["Initialize monitoring"]

A --> B
B --> C
B --> D
B --> E
B --> F
B --> G
E --> H
F --> H
G --> H
H --> I
```

Sources: [src/stat_cache.c L33-L40](https://github.com/lighttpd/lighttpd1.4/blob/3d550097/src/stat_cache.c#L33-L40)

 [src/stat_cache.c L881-L893](https://github.com/lighttpd/lighttpd1.4/blob/3d550097/src/stat_cache.c#L881-L893)

 [src/stat_cache.c L922-L959](https://github.com/lighttpd/lighttpd1.4/blob/3d550097/src/stat_cache.c#L922-L959)

 [src/stat_cache.c L575-L634](https://github.com/lighttpd/lighttpd1.4/blob/3d550097/src/stat_cache.c#L575-L634)

## 4. File System Monitoring

When using the FAM/inotify/kqueue engines, the stat cache monitors directories for changes to automatically invalidate affected cache entries.

```mermaid
flowchart TD

A["Directory Access"]
B["fam_dir_monitor()"]
C["Monitor Directory"]
D["Associate with stat_cache_entry"]
E["File System Event"]
F["stat_cache_handle_fdevent_in()"]
G["Process Event"]
H["Event Type"]
I["Invalidate File Entry"]
J["Delete Tree"]
K["Remove all entries in affected path"]

A --> B
B --> C
C --> D
E --> F
F --> G
G --> H
H --> I
H --> J
J --> K
```

The monitoring system handles several types of file system events:

* File/directory changes (content or attributes modified)
* File/directory deletion
* File/directory renaming/moving

Sources: [src/stat_cache.c L663-L795](https://github.com/lighttpd/lighttpd1.4/blob/3d550097/src/stat_cache.c#L663-L795)

 [src/stat_cache.c L362-L547](https://github.com/lighttpd/lighttpd1.4/blob/3d550097/src/stat_cache.c#L362-L547)

 [src/stat_cache.c L549-L573](https://github.com/lighttpd/lighttpd1.4/blob/3d550097/src/stat_cache.c#L549-L573)

## 5. Cache Entry Operations

The stat cache provides several operations for working with cached entries:

### 5.1. Retrieving Entries

```mermaid
flowchart TD

A["Request Handler"]
B["stat_cache_get_entry()"]
C["stat_cache_get_entry_open()"]
D["stat_cache_sptree_find()"]
E["Found?"]
F["Check freshness"]
G["stat() and cache"]
H["Open file if needed"]

A --> B
A --> C
B --> D
D --> E
E --> F
E --> G
C --> B
C --> H
```

Sources: [src/stat_cache.c L1330-L1381](https://github.com/lighttpd/lighttpd1.4/blob/3d550097/src/stat_cache.c#L1330-L1381)

 [src/stat_cache.c L1383-L1392](https://github.com/lighttpd/lighttpd1.4/blob/3d550097/src/stat_cache.c#L1383-L1392)

### 5.2. Updating and Invalidating Entries

```mermaid
flowchart TD

A["File Change Detected"]
B["stat_cache_update_entry()"]
C["Update metadata"]
D["File Deletion"]
E["stat_cache_delete_entry()"]
F["Remove from cache"]
G["Directory Change"]
H["stat_cache_delete_dir()"]
I["Invalidate directory tree"]
J["Manual Invalidation"]
K["stat_cache_invalidate_entry()"]
L["Mark as stale"]

A --> B
B --> C
D --> E
E --> F
G --> H
H --> I
J --> K
K --> L
```

Sources: [src/stat_cache.c L1109-L1142](https://github.com/lighttpd/lighttpd1.4/blob/3d550097/src/stat_cache.c#L1109-L1142)

 [src/stat_cache.c L1144-L1154](https://github.com/lighttpd/lighttpd1.4/blob/3d550097/src/stat_cache.c#L1144-L1154)

 [src/stat_cache.c L1156-L1169](https://github.com/lighttpd/lighttpd1.4/blob/3d550097/src/stat_cache.c#L1156-L1169)

 [src/stat_cache.c L1242-L1257](https://github.com/lighttpd/lighttpd1.4/blob/3d550097/src/stat_cache.c#L1242-L1257)

## 6. Content Type Detection

The stat cache helps determine file MIME types through:

1. Extended attributes (if supported and enabled)
2. File extension mapping from configuration

```mermaid
flowchart TD

A["Content Type Request"]
B["stat_cache_content_type_get_by_xattr()"]
C["stat_cache_content_type_get_by_ext()"]
D["Has cached type?"]
E["Return cached"]
F["Try xattr lookup"]
G["Found in xattr?"]
H["Return xattr type"]
I["Try extension lookup"]
J["Has cached type?"]
K["stat_cache_mimetype_by_ext()"]
L["Cache and return type"]

A --> B
A --> C
B --> D
D --> E
D --> F
F --> G
G --> H
G --> I
C --> J
J --> E
J --> I
I --> K
K --> L
```

Sources: [src/stat_cache.c L961-L1007](https://github.com/lighttpd/lighttpd1.4/blob/3d550097/src/stat_cache.c#L961-L1007)

 [src/stat_cache.c L1016-L1073](https://github.com/lighttpd/lighttpd1.4/blob/3d550097/src/stat_cache.c#L1016-L1073)

 [src/stat_cache.c L845-L879](https://github.com/lighttpd/lighttpd1.4/blob/3d550097/src/stat_cache.c#L845-L879)

## 7. ETag Generation

ETags are generated based on file metadata to support HTTP caching mechanisms:

```mermaid
flowchart TD

A["ETag Request"]
B["stat_cache_etag_get()"]
C["Has cached ETag?"]
D["Return cached ETag"]
E["http_etag_create()"]
F["Generate from file metadata"]
G["Cache and return ETag"]

A --> B
B --> C
C --> D
C --> E
E --> F
F --> G
```

The ETag generation uses various file attributes depending on configuration flags:

* File size
* Inode number
* Modification time
* Device ID

Sources: [src/stat_cache.c L1077-L1089](https://github.com/lighttpd/lighttpd1.4/blob/3d550097/src/stat_cache.c#L1077-L1089)

## 8. Symlink Handling

Lighttpd provides functions to safely handle symbolic links:

```mermaid
flowchart TD

A["stat_cache_path_contains_symlink()"]
B["Check path components"]
C["Contains symlink?"]
D["Return 1"]
E["Return 0"]
F["stat_cache_open_rdonly_fstat()"]
G["Symlinks allowed?"]
H["fdevent_open_cloexec()"]
I["fdevent_open_cloexec() with O_NOFOLLOW"]

A --> B
B --> C
C --> D
C --> E
F --> G
G --> H
G --> I
```

This provides security against symlink-based attacks when configured to restrict symlinks.

Sources: [src/stat_cache.c L1404-L1450](https://github.com/lighttpd/lighttpd1.4/blob/3d550097/src/stat_cache.c#L1404-L1450)

 [src/stat_cache.c L1452-L1466](https://github.com/lighttpd/lighttpd1.4/blob/3d550097/src/stat_cache.c#L1452-L1466)

## 9. Periodic Cleanup

To prevent the cache from growing too large, the stat cache periodically removes old entries:

```mermaid
flowchart TD

A["stat_cache_trigger_cleanup()"]
B["Check engine type"]
C["Remove entries older than 2 seconds"]
D["Remove entries older than 32 seconds"]
E["fam_dir_periodic_cleanup()"]
F["Remove directories no longer referenced"]

A --> B
B --> C
B --> D
D --> E
E --> F
```

Sources: [src/stat_cache.c L1477-L1523](https://github.com/lighttpd/lighttpd1.4/blob/3d550097/src/stat_cache.c#L1477-L1523)

 [src/stat_cache.c L285-L335](https://github.com/lighttpd/lighttpd1.4/blob/3d550097/src/stat_cache.c#L285-L335)

## 10. Implementation Considerations

### 10.1. Engine Selection Trade-offs

| Engine | Pros | Cons |
| --- | --- | --- |
| Simple | Low overhead, works everywhere | May serve stale data (up to 2s) |
| None | Always fresh data | Higher I/O load, potential performance impact |
| FAM/inotify/kqueue | Longer cache times with change detection | Platform-specific, more complex |

### 10.2. File System Monitoring Limitations

When using the FAM/inotify/kqueue engines:

1. Symlinks to files outside monitored directories may not trigger proper invalidation
2. Directory renames may cause stale cache entries in some cases
3. Very volatile directories (like /tmp) may cause excessive monitoring overhead

Sources: [src/stat_cache.c L80-L136](https://github.com/lighttpd/lighttpd1.4/blob/3d550097/src/stat_cache.c#L80-L136)

## 11. Performance Implications

The stat cache significantly improves performance by reducing file system calls. For static file serving, it can reduce disk operations by orders of magnitude. Key performance factors include:

1. Cache hit rate
2. File system characteristics
3. Selected cache engine
4. Monitoring overhead (for FAM/inotify/kqueue)

For optimal performance with frequently changing content, consider using the FAM/inotify/kqueue engines where supported.