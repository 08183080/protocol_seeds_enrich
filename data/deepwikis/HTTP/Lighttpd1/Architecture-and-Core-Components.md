# Architecture and Core Components

> **Relevant source files**
> * [NEWS](https://github.com/lighttpd/lighttpd1.4/blob/3d550097/NEWS)
> * [src/base.h](https://github.com/lighttpd/lighttpd1.4/blob/3d550097/src/base.h)
> * [src/configfile.c](https://github.com/lighttpd/lighttpd1.4/blob/3d550097/src/configfile.c)
> * [src/connections.c](https://github.com/lighttpd/lighttpd1.4/blob/3d550097/src/connections.c)
> * [src/network.c](https://github.com/lighttpd/lighttpd1.4/blob/3d550097/src/network.c)
> * [src/plugin.c](https://github.com/lighttpd/lighttpd1.4/blob/3d550097/src/plugin.c)
> * [src/plugin.h](https://github.com/lighttpd/lighttpd1.4/blob/3d550097/src/plugin.h)
> * [src/server.c](https://github.com/lighttpd/lighttpd1.4/blob/3d550097/src/server.c)

This document describes the core architecture of lighttpd, explaining the main components and their relationships within the web server system. We'll cover the fundamental structures, their interactions, and the flow of control through the system. For details about HTTP request processing specifically, see [HTTP Request Processing](/lighttpd/lighttpd1.4/1.2-http-request-processing).

## High-Level Architecture Overview

```mermaid
flowchart TD

A["server"]
B["connections"]
C["plugins"]
D["fdevent"]
E["config"]
F["request_st"]
G["buffer"]
H["chunkqueue"]
I["plugin_data"]
J["event loop"]
K["connection state machine"]
L["request processing"]
M["module hooks"]
N["network"]
O["file chunks"]
P["memory chunks"]
Q["socket operations"]

D --> J
H --> O
H --> P
D --> N
K --> F
F --> N

subgraph subGraph2 ["I/O Handling"]
    N
    O
    P
    Q
    N --> Q
end

subgraph subGraph1 ["Event Processing"]
    J
    K
    L
    M
    J --> K
    K --> L
    L --> M
end

subgraph subGraph0 ["Core Components"]
    A
    B
    C
    D
    E
    F
    G
    H
    I
    A --> B
    A --> C
    A --> D
    A --> E
    B --> F
    F --> G
    F --> H
    C --> I
end
```

Sources: [src/base.h L1-L209](https://github.com/lighttpd/lighttpd1.4/blob/3d550097/src/base.h#L1-L209)

 [src/server.c L1-L99](https://github.com/lighttpd/lighttpd1.4/blob/3d550097/src/server.c#L1-L99)

 [src/connections.c L1-L50](https://github.com/lighttpd/lighttpd1.4/blob/3d550097/src/connections.c#L1-L50)

## Core Components

### Server Structure

The `server` structure is the central component of lighttpd, containing all global state and configurations. It manages connections, plugins, event handling, and configuration data.

```mermaid
classDiagram
    class server {
        +struct fdevents* ev
        +connection* conns
        +void* plugin_slots
        +server_config srvconf
        +server_socket_array srv_sockets
        +void* plugins
        +unix_time64_t startup_ts
        +log_error_st* errh
    }
    class server_config {
        +array* modules
        +unsigned short max_worker
        +unsigned short max_fds
        +buffer* pid_file
        +unsigned char h2proto
    }
    class server_socket {
        +sock_addr addr
        +int fd
        +uint8_t is_ssl
        +buffer* srv_token
        +server* srv
    }
    server --> server_config : contains
    server --> server_socket : manages
```

Sources: [src/base.h L155-L206](https://github.com/lighttpd/lighttpd1.4/blob/3d550097/src/base.h#L155-L206)

 [src/server.c L494-L545](https://github.com/lighttpd/lighttpd1.4/blob/3d550097/src/server.c#L494-L545)

The `server` structure is initialized in the `server_init()` function in [src/server.c L494-L545](https://github.com/lighttpd/lighttpd1.4/blob/3d550097/src/server.c#L494-L545)

 which:

1. Initializes core buffers and data structures
2. Sets up error handling
3. Initializes configuration
4. Sets up connection management

### Connection Management

Connections are managed through the `connection` structure which represents a client connection to the server.

```mermaid
classDiagram
    class connection {
        +request_st request
        +int fd
        +fdnode* fdn
        +chunkqueue* write_queue
        +chunkqueue* read_queue
        +server* srv
        +sock_addr dst_addr
        +const server_socket* srv_socket
        +unix_time64_t connection_start
        +uint32_t request_count
        +int (* network_write)()
        +int (* network_read)()
    }
    class request_st {
        +http_method_t http_method
        +http_version_t http_version
        +request_state_t state
        +buffer uri
        +buffer physical
        +request_config conf
        +array* headers
    }
    class fdnode {
    }
    connection --> request_st : contains
    connection --> fdnode : event_registration
```

Sources: [src/base.h L30-L77](https://github.com/lighttpd/lighttpd1.4/blob/3d550097/src/base.h#L30-L77)

 [src/connections.c L372-L390](https://github.com/lighttpd/lighttpd1.4/blob/3d550097/src/connections.c#L372-L390)

 [src/connections.c L74-L100](https://github.com/lighttpd/lighttpd1.4/blob/3d550097/src/connections.c#L74-L100)

Key connection management functions:

* `connection_accepted()` - Creates a new connection after accepting a socket
* `connection_state_machine()` - Drives the state transitions of a connection
* `connection_close()` - Cleans up and closes a connection

### Connection State Machine

The connection state machine drives the request handling process through various states:

```mermaid
stateDiagram-v2
    [*] --> CON_STATE_REQUEST_START
    CON_STATE_REQUEST_START --> CON_STATE_READ : "if request has body"
    CON_STATE_READ --> CON_STATE_READ_POST : "if request has body"
    CON_STATE_READ --> CON_STATE_HANDLE_REQUEST : "if no request body"
    CON_STATE_READ_POST --> CON_STATE_HANDLE_REQUEST : "body read complete"
    CON_STATE_HANDLE_REQUEST --> CON_STATE_RESPONSE_START : "after processing"
    CON_STATE_RESPONSE_START --> CON_STATE_WRITE : "after processing"
    CON_STATE_WRITE --> CON_STATE_RESPONSE_END : "writing complete"
    CON_STATE_RESPONSE_END --> CON_STATE_REQUEST_START : "if keep-alive"
    CON_STATE_RESPONSE_END --> CON_STATE_CLOSE : "if no keep-alive"
    CON_STATE_CLOSE --> [*] : "if no keep-alive"
    CON_STATE_ERROR --> CON_STATE_RESPONSE_END : "if no keep-alive"
```

Sources: [src/connections.c L632-L704](https://github.com/lighttpd/lighttpd1.4/blob/3d550097/src/connections.c#L632-L704)

 [src/connections.c L174-L217](https://github.com/lighttpd/lighttpd1.4/blob/3d550097/src/connections.c#L174-L217)

The connection state machine is implemented in `connection_state_machine_loop()` which processes the state transitions based on the current state and the result of the handling functions for each state.

### Event Handling System

The event handling system is based on the `fdevent` subsystem which provides abstraction over different event notification mechanisms (select, poll, epoll, etc).

```mermaid
flowchart TD

A["fdevent system"]
B["register fd/callback"]
C["handle events"]
D["wait for events"]
E["fdnode registration"]
F["connection_handle_fdevent()"]
G["event loop"]
H["joblist processing"]
I["connection_state_machine()"]

A --> B
A --> C
A --> D
B --> E
C --> F
D --> G
G --> H
H --> I
```

Sources: [src/server.c L474-L493](https://github.com/lighttpd/lighttpd1.4/blob/3d550097/src/server.c#L474-L493)

 [src/connections.c L473-L494](https://github.com/lighttpd/lighttpd1.4/blob/3d550097/src/connections.c#L473-L494)

Key aspects:

* `fdevent` registers file descriptors for event notification
* Events trigger callbacks like `connection_handle_fdevent()`
* The event loop in the server main function processes these events
* `joblist_append()` is used to queue connections for processing

### Plugin System

The plugin system provides extensibility to lighttpd. Plugins can register handlers for various hooks in the request processing cycle.

```mermaid
classDiagram
    class plugin {
        +void* data
        +const char* name
        +size_t version
        +handler_t (*handle_uri_clean)()
        +handler_t (*handle_physical)()
        +handler_t (*handle_subrequest)()
        +handler_t (*handle_response_start)()
        +handler_t (*handle_connection_close)()
        +void* (*init)()
        +handler_t (*set_defaults)()
        +void (*cleanup)()
    }
    class plugin_data_base {
        +int id
        +int nconfig
        +config_plugin_value_t* cvlist
        +struct plugin* self
    }
    plugin --> plugin_data_base : references
```

Sources: [src/plugin.h L40-L75](https://github.com/lighttpd/lighttpd1.4/blob/3d550097/src/plugin.h#L40-L75)

 [src/plugin.c L57-L59](https://github.com/lighttpd/lighttpd1.4/blob/3d550097/src/plugin.c#L57-L59)

 [src/plugin.c L447-L579](https://github.com/lighttpd/lighttpd1.4/blob/3d550097/src/plugin.c#L447-L579)

The plugin system works as follows:

1. Plugins are loaded at server startup (`plugins_load()`)
2. Each plugin registers callbacks for various hooks (`plugins_call_init()`)
3. During request processing, the server calls these hooks at appropriate times
4. The plugin API provides different hook types for various phases of processing

## Request Processing Flow

The following diagram illustrates how HTTP requests flow through the system:

```mermaid
sequenceDiagram
  participant Client
  participant server
  participant connection
  participant connection_state_machine
  participant http_response_handler
  participant plugin_hooks

  Client->>server: TCP Connection
  server->>connection: connection_accepted()
  connection->>connection_state_machine: connection_state_machine()
  connection_state_machine->>connection_state_machine: CON_STATE_REQUEST_START
  connection_state_machine->>connection_state_machine: CON_STATE_READ
  connection_state_machine->>plugin_hooks: plugins_call_handle_uri_clean()
  connection_state_machine->>connection_state_machine: CON_STATE_HANDLE_REQUEST
  connection_state_machine->>http_response_handler: http_response_handler()
  http_response_handler->>plugin_hooks: plugins_call_handle_subrequest_start()
  loop [Found Handler]
    plugin_hooks-->>http_response_handler: HANDLER_GO_ON
    http_response_handler->>connection_state_machine: prepare response
    plugin_hooks-->>http_response_handler: HANDLER_ERROR
    http_response_handler->>connection_state_machine: error response
    connection_state_machine->>connection_state_machine: CON_STATE_WRITE
    connection_state_machine->>Client: send response
    connection_state_machine->>connection_state_machine: CON_STATE_RESPONSE_END
    connection_state_machine->>plugin_hooks: plugins_call_handle_request_done()
    connection_state_machine->>connection_state_machine: reset for next request
    connection_state_machine->>connection_state_machine: CON_STATE_CLOSE
    connection_state_machine->>connection: connection_close()
  end
```

Sources: [src/connections.c L632-L704](https://github.com/lighttpd/lighttpd1.4/blob/3d550097/src/connections.c#L632-L704)

 [src/plugin.c L287-L352](https://github.com/lighttpd/lighttpd1.4/blob/3d550097/src/plugin.c#L287-L352)

## Memory Management

lighttpd uses specialized memory management components to efficiently handle data:

### Buffer System

Buffers (`buffer`) are used for string manipulation and storage.

```mermaid
classDiagram
    class buffer {
        +char* ptr
        +size_t used
        +size_t size
    }
```

Sources: [src/base.h L9](https://github.com/lighttpd/lighttpd1.4/blob/3d550097/src/base.h#L9-L9)

 (imported from buffer.h)

### Chunk System

The `chunkqueue` system is used for efficient I/O operations and data handling:

```mermaid
classDiagram
    class chunkqueue {
        +chunk* first
        +chunk* last
        +off_t bytes_in
        +off_t bytes_out
    }
    class chunk {
        +enum chunk_type type
        +chunk* next
        +off_t offset
        +off_t file.length
        +buffer* mem
        +buffer* file.name
        +int file.fd
    }
    chunkqueue --> chunk : contains
```

Sources: [src/base.h L10](https://github.com/lighttpd/lighttpd1.4/blob/3d550097/src/base.h#L10-L10)

 (imported from chunk.h)

Chunkqueues can contain different types of chunks:

* Memory chunks (`MEM_CHUNK`) for in-memory data
* File chunks (`FILE_CHUNK`) for file-based data
* This design allows efficient handling of both small in-memory data and large files

## Initialization Process

The server initialization process follows these steps:

```mermaid
flowchart TD

A["server_init()"]
B["Initialize core structures"]
C["Configure event system"]
D["plugins_load()"]
E["plugins_call_init()"]
F["network_init()"]
G["Start event loop"]
D1["Load plugin modules"]
D2["Call plugin init()"]
D3["Register hooks"]

A --> B
B --> C
C --> D
D --> E
E --> F
F --> G
D --> D1

subgraph subGraph0 ["Plugin Initialization"]
    D1
    D2
    D3
    D1 --> D2
    D2 --> D3
end
```

Sources: [src/server.c L494-L545](https://github.com/lighttpd/lighttpd1.4/blob/3d550097/src/server.c#L494-L545)

 [src/plugin.c L447-L579](https://github.com/lighttpd/lighttpd1.4/blob/3d550097/src/plugin.c#L447-L579)

## Event Loop

The main event loop is the heart of the server's operation:

```mermaid
flowchart TD

A["fdevent_poll()"]
B["Process events"]
C["Process connection jobs"]
D["Check timeouts"]
E["Graceful shutdown check"]
F["connection_state_machine()"]
G["process request states"]
H["call appropriate handlers"]

A --> B
B --> C
C --> D
D --> E
E --> A
C --> F
F --> G
G --> H
```

Sources: [src/server.c L474-L493](https://github.com/lighttpd/lighttpd1.4/blob/3d550097/src/server.c#L474-L493)

 [src/connections.c L826-L835](https://github.com/lighttpd/lighttpd1.4/blob/3d550097/src/connections.c#L826-L835)

The event loop:

1. Waits for network events using the configured event mechanism
2. Processes triggered events, generally related to socket activity
3. Runs the state machine for connections that have pending work
4. Checks for timeouts and other periodic tasks
5. Repeats until server shutdown is requested

This design allows lighttpd to efficiently handle many concurrent connections with minimal resource usage.