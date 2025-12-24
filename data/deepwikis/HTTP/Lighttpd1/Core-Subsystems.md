# Core Subsystems

> **Relevant source files**
> * [NEWS](https://github.com/lighttpd/lighttpd1.4/blob/3d550097/NEWS)
> * [src/base.h](https://github.com/lighttpd/lighttpd1.4/blob/3d550097/src/base.h)
> * [src/configfile.c](https://github.com/lighttpd/lighttpd1.4/blob/3d550097/src/configfile.c)
> * [src/connections.c](https://github.com/lighttpd/lighttpd1.4/blob/3d550097/src/connections.c)
> * [src/network.c](https://github.com/lighttpd/lighttpd1.4/blob/3d550097/src/network.c)
> * [src/plugin.c](https://github.com/lighttpd/lighttpd1.4/blob/3d550097/src/plugin.c)
> * [src/plugin.h](https://github.com/lighttpd/lighttpd1.4/blob/3d550097/src/plugin.h)
> * [src/server.c](https://github.com/lighttpd/lighttpd1.4/blob/3d550097/src/server.c)

This page describes the foundational subsystems that power the lighttpd web server. These core components work together to provide a lightweight, high-performance HTTP server with an event-driven architecture. For information about individual modules and extensions, see [Module System](/lighttpd/lighttpd1.4/4-module-system).

## Overview

Lighttpd's architecture is built around several key subsystems that handle different aspects of web server functionality:

```mermaid
flowchart TD

C["Connection Management"]
E["Event Handling"]
R["Request Processing"]
P["Plugin Architecture"]
N["Network I/O"]
CFG["Configuration System"]
M["Memory Management"]

subgraph subGraph0 ["Core Subsystems"]
    C
    E
    R
    P
    N
    CFG
    M
    C --> E
    E --> R
    R --> P
    N --> C
    N --> CFG
    M --> C
    M --> R
    CFG --> P
    CFG --> C
end
```

These subsystems work together to enable lighttpd's efficient handling of thousands of concurrent connections with minimal resource usage.

Sources: [src/server.c L494-L544](https://github.com/lighttpd/lighttpd1.4/blob/3d550097/src/server.c#L494-L544)

 [src/base.h L30-L77](https://github.com/lighttpd/lighttpd1.4/blob/3d550097/src/base.h#L30-L77)

 [src/base.h L154-L206](https://github.com/lighttpd/lighttpd1.4/blob/3d550097/src/base.h#L154-L206)

## Connection Management

The connection management subsystem handles the lifecycle of client connections from acceptance to closure.

```mermaid
classDiagram
    class connection {
        request_st request
        int fd
        fdnode *fdn
        chunkqueue *write_queue
        chunkqueue *read_queue
        connection *next
        connection *prev
        int network_write()
        int network_read()
        handler_t reqbody_read()
    }
    class server {
        connection *conns
        connection *conns_pool
        uint32_t lim_conns
        struct fdevents *ev
    }
    server --> connection : manages
```

The `connection` structure is the central data structure for client connections. Each connection contains:

* File descriptor (`fd`) for the socket
* Buffers for reading and writing data (`read_queue`, `write_queue`)
* Request state (`request`)
* Function pointers for I/O operations (`network_read`, `network_write`)

Key functions:

* `connection_accepted()`: Sets up a new client connection
* `connection_state_machine()`: Drives connection processing
* `connection_state_machine_loop()`: Handles state transitions
* `connection_close()`: Cleans up and releases connections

For efficiency, lighttpd uses a connection pool to reuse connection structures:

* `connections_get_new_connection()`: Gets a connection from the pool
* `connection_del()`: Returns a connection to the pool
* `connections_pool_clear()`: Frees all pooled connections

Sources: [src/connections.c L37-L103](https://github.com/lighttpd/lighttpd1.4/blob/3d550097/src/connections.c#L37-L103)

 [src/connections.c L372-L406](https://github.com/lighttpd/lighttpd1.4/blob/3d550097/src/connections.c#L372-L406)

 [src/connections.c L589-L628](https://github.com/lighttpd/lighttpd1.4/blob/3d550097/src/connections.c#L589-L628)

## Request Processing

The request processing subsystem manages HTTP request parsing, routing, and response generation.

```mermaid
stateDiagram-v2
    [*] --> REQUEST_START : "New request"
    REQUEST_START --> READ : "Initialize"
    READ --> READ_POST : "Body detected"
    READ --> HANDLE_REQUEST : "No body"
    READ_POST --> HANDLE_REQUEST : "Body read"
    HANDLE_REQUEST --> RESPONSE_START : "Begin response"
    RESPONSE_START --> WRITE : "Send headers"
    WRITE --> RESPONSE_END : "Complete"
    RESPONSE_END --> REQUEST_START : "Begin response"
    RESPONSE_END --> [*] : "Connection close"
```

The request processing flow:

1. Initialize a new request (`CON_STATE_REQUEST_START`)
2. Read and parse headers (`CON_STATE_READ`)
3. Read request body if present (`CON_STATE_READ_POST`)
4. Process the request through plugins (`CON_STATE_HANDLE_REQUEST`)
5. Generate response headers (`CON_STATE_RESPONSE_START`)
6. Send response body (`CON_STATE_WRITE`)
7. Finalize the request (`CON_STATE_RESPONSE_END`)
8. Either close the connection or prepare for another request

Key functions:

* `connection_handle_request_start_state()`: Initializes request processing
* `h1_recv_headers()`: Parses HTTP headers
* `http_response_handler()`: Routes request to appropriate handler
* `connection_handle_write_state()`: Manages response transmission
* `connection_handle_response_end_state()`: Finalizes requests

Sources: [src/connections.c L162-L217](https://github.com/lighttpd/lighttpd1.4/blob/3d550097/src/connections.c#L162-L217)

 [src/connections.c L631-L704](https://github.com/lighttpd/lighttpd1.4/blob/3d550097/src/connections.c#L631-L704)

 [src/connections.c L315-L369](https://github.com/lighttpd/lighttpd1.4/blob/3d550097/src/connections.c#L315-L369)

## Event Handling

The event handling subsystem provides an event-driven architecture that efficiently manages I/O operations.

```mermaid
flowchart TD

fdevent_loop["fdevent_loop"]
fdevent_poll["fdevent_poll (select/epoll/kqueue)"]
event_handlers["Event Callbacks"]
connection_handle_fdevent["connection_handle_fdevent()"]
connection_state_machine["connection_state_machine()"]
in["FDEVENT_IN (Read Ready)"]
out["FDEVENT_OUT (Write Ready)"]
err["FDEVENT_ERR (Error)"]
hup["FDEVENT_HUP (Hang Up)"]
rdhup["FDEVENT_RDHUP (Read Hang Up)"]

fdevent_poll --> in
fdevent_poll --> out
fdevent_poll --> err
fdevent_poll --> hup
fdevent_poll --> rdhup
in --> connection_handle_fdevent
out --> connection_handle_fdevent

subgraph subGraph1 ["Event Types"]
    in
    out
    err
    hup
    rdhup
end

subgraph subGraph0 ["Event Subsystem"]
    fdevent_loop
    fdevent_poll
    event_handlers
    connection_handle_fdevent
    connection_state_machine
    fdevent_loop --> fdevent_poll
    fdevent_poll --> event_handlers
    event_handlers --> connection_handle_fdevent
    connection_handle_fdevent --> connection_state_machine
end
```

The event system:

* Uses various backend implementations (epoll, kqueue, poll) depending on platform
* Manages interest in different types of events (read, write, error)
* Associates file descriptors with callback functions
* Efficiently handles thousands of concurrent connections

Key functions:

* `fdevent_register()`: Registers file descriptors with the event system
* `fdevent_fdnode_event_set()`: Sets interest in specific events
* `connection_handle_fdevent()`: Processes events for connections
* `connection_set_fdevent_interest()`: Updates event interests based on connection state

Sources: [src/connections.c L473-L494](https://github.com/lighttpd/lighttpd1.4/blob/3d550097/src/connections.c#L473-L494)

 [src/connections.c L764-L823](https://github.com/lighttpd/lighttpd1.4/blob/3d550097/src/connections.c#L764-L823)

## Plugin Architecture

The plugin architecture provides an extensible framework for adding functionality to the server.

```mermaid
flowchart TD

plugin_dispatch["Plugin Dispatch Tables"]
plugin_slots["plugin_slots Array"]
plugins_call_fn_req_data["plugins_call_fn_req_data()"]
plugins_load["plugins_load()"]
plugins_call_init["plugins_call_init()"]
hook_registration["Hook Registration"]
uri_hooks["URI Processing Hooks"]
request_hooks["Request Processing Hooks"]
response_hooks["Response Generation Hooks"]
connection_hooks["Connection Lifecycle Hooks"]
plugins_free["plugins_free()"]
plugins_call_cleanup["plugins_call_cleanup()"]

subgraph subGraph1 ["Hook Invocation"]
    plugin_dispatch
    plugin_slots
    plugins_call_fn_req_data
    plugin_dispatch --> plugin_slots
    plugin_slots --> plugins_call_fn_req_data
end

subgraph subGraph0 ["Plugin System"]
    plugins_load
    plugins_call_init
    hook_registration
    uri_hooks
    request_hooks
    response_hooks
    connection_hooks
    plugins_free
    plugins_call_cleanup
    plugins_load --> plugins_call_init
    plugins_call_init --> hook_registration
    hook_registration --> uri_hooks
    hook_registration --> request_hooks
    hook_registration --> response_hooks
    hook_registration --> connection_hooks
    plugins_free --> plugins_call_cleanup
end
```

The plugin system features:

* Dynamic loading of modules (with `dlopen()`) or static compilation
* Extensive hook points throughout the request lifecycle
* Plugin-specific configuration data
* Efficient hook dispatch through function tables

Key structures:

* `plugin`: Defines module operations with function pointers for various hooks
* `plugin_data_base`: Base structure for plugin-specific data

Key functions:

* `plugins_load()`: Loads and initializes modules
* `plugins_call_init()`: Sets up plugin hook dispatch tables
* `plugins_call_handle_*()`: Invokes plugin hooks at specific points

Sources: [src/plugin.c L31-L53](https://github.com/lighttpd/lighttpd1.4/blob/3d550097/src/plugin.c#L31-L53)

 [src/plugin.c L446-L579](https://github.com/lighttpd/lighttpd1.4/blob/3d550097/src/plugin.c#L446-L579)

 [src/plugin.h L8-L75](https://github.com/lighttpd/lighttpd1.4/blob/3d550097/src/plugin.h#L8-L75)

## Network I/O

The network I/O subsystem handles socket operations and data transfer.

```mermaid
flowchart TD

socket_creation["Socket Creation"]
socket_config["Socket Configuration (TCP_NODELAY, etc.)"]
socket_accept["Accept Connections"]
socket_io["Socket I/O"]
network_server_init["network_server_init()"]
network_server_socket_init["network_srv_socket_init_token()"]
network_srv_sockets_append["network_srv_sockets_append()"]
network_server_handle_fdevent["network_server_handle_fdevent()"]
connection_accepted["connection_accepted()"]
connection_write_chunkqueue["connection_write_chunkqueue()"]
network_backend_write["network_backend_write()"]
connection_read_cq["connection_read_cq()"]
socket_read["Socket Read Operations"]

subgraph subGraph1 ["Socket Operations"]
    socket_creation
    socket_config
    socket_accept
    socket_io
    socket_creation --> socket_config
    socket_config --> socket_accept
    socket_accept --> socket_io
end

subgraph subGraph0 ["Network I/O"]
    network_server_init
    network_server_socket_init
    network_srv_sockets_append
    network_server_handle_fdevent
    connection_accepted
    connection_write_chunkqueue
    network_backend_write
    connection_read_cq
    socket_read
    network_server_init --> network_server_socket_init
    network_server_socket_init --> network_srv_sockets_append
    network_server_handle_fdevent --> connection_accepted
    connection_write_chunkqueue --> network_backend_write
    connection_read_cq --> socket_read
end
```

The network system includes:

* Socket creation and configuration
* Support for IPv4, IPv6, and Unix domain sockets
* Efficient data transfer mechanisms
* Throttling and rate limiting
* SSL/TLS integration
* Abstract network backend implementation

Key functions:

* `network_server_init()`: Sets up server sockets
* `network_server_handle_fdevent()`: Handles connection acceptance
* `connection_write_chunkqueue()`: Writes data to clients
* `connection_read_cq()`: Reads data from clients
* `network_write_throttle()`: Implements rate limiting for outgoing data

Sources: [src/network.c L57-L133](https://github.com/lighttpd/lighttpd1.4/blob/3d550097/src/network.c#L57-L133)

 [src/network.c L388-L580](https://github.com/lighttpd/lighttpd1.4/blob/3d550097/src/network.c#L388-L580)

 [src/connections.c L248-L313](https://github.com/lighttpd/lighttpd1.4/blob/3d550097/src/connections.c#L248-L313)

 [src/connections.c L544-L580](https://github.com/lighttpd/lighttpd1.4/blob/3d550097/src/connections.c#L544-L580)

## Configuration System

The configuration system parses server configuration files and applies settings to requests.

```mermaid
flowchart TD

server_config["server_config"]
request_config["request_config"]
config_plugin_value_t["config_plugin_value_t"]
config_patch_config["config_patch_config()"]
config_check_cond["config_check_cond()"]
config_merge_config["config_merge_config()"]
config_merge_config_cpv["config_merge_config_cpv()"]
config_parse_file["config_parse_file()"]
config_setup_connection["config_setup_connection()"]
config_check["config_check()"]
config_plugins_setup["config_plugins_setup()"]

subgraph subGraph2 ["Configuration Data Structures"]
    server_config
    request_config
    config_plugin_value_t
    server_config --> request_config
    config_plugin_value_t --> request_config
end

subgraph subGraph1 ["Configuration Application"]
    config_patch_config
    config_check_cond
    config_merge_config
    config_merge_config_cpv
    config_patch_config --> config_check_cond
    config_check_cond --> config_merge_config
    config_merge_config --> config_merge_config_cpv
end

subgraph subGraph0 ["Configuration Processing"]
    config_parse_file
    config_setup_connection
    config_check
    config_plugins_setup
    config_parse_file --> config_setup_connection
    config_setup_connection --> config_check
    config_check --> config_plugins_setup
end
```

The configuration system features:

* Hierarchical configuration structure
* Conditional configurations based on request attributes
* Plugin-specific configuration
* Configuration inheritance and overrides

Key structures:

* `server_config`: Global server configuration
* `request_config`: Per-request configuration
* `config_plugin_value_t`: Configuration values for plugins

Key functions:

* `config_patch_config()`: Applies configuration to a request
* `config_merge_config()`: Merges configuration values
* `config_check_cond()`: Evaluates configuration conditions

Sources: [src/configfile.c L207-L223](https://github.com/lighttpd/lighttpd1.4/blob/3d550097/src/configfile.c#L207-L223)

 [src/configfile.c L91-L205](https://github.com/lighttpd/lighttpd1.4/blob/3d550097/src/configfile.c#L91-L205)

## Memory Management

The memory management subsystem provides efficient memory operations for strings, data chunks, and request structures.

```mermaid
flowchart TD

buffer_system["Buffer System"]
buffer_functions["buffer_init(), buffer_copy_string(), etc."]
chunk_system["Chunk System"]
chunk_functions["chunk_init(), chunkqueue_append_mem(), etc."]
request_pool["Request Pool"]
request_functions["request_pool_get(), request_reset(), etc."]
buffer["buffer: {ptr, used, size}"]
chunk["chunk: {type, mem, file, offset, length}"]
chunkqueue["chunkqueue: {first, last, bytes_in, bytes_out}"]
request_st["request_st: {state, http_version, uri, headers, etc.}"]

buffer_system --> buffer
chunk_system --> chunk
chunk_system --> chunkqueue
request_pool --> request_st

subgraph subGraph1 ["Data Structures"]
    buffer
    chunk
    chunkqueue
    request_st
end

subgraph subGraph0 ["Memory Subsystems"]
    buffer_system
    buffer_functions
    chunk_system
    chunk_functions
    request_pool
    request_functions
    buffer_system --> buffer_functions
    chunk_system --> chunk_functions
    request_pool --> request_functions
end
```

Key memory management components:

1. **Buffer System** * Dynamically resizable string buffers * Optimized string operations * Memory reuse for efficiency
2. **Chunk System** * Represents data as memory blocks or file references * `chunkqueue` for efficient I/O operations * Minimizes memory copying during file transfers
3. **Request Pool** * Reuses request structures to reduce allocations * Resets request state between uses * Improves memory locality and cache efficiency

Key functions:

* `buffer_init()`, `buffer_free()`: Manage string buffers
* `chunkqueue_append_mem()`, `chunkqueue_append_file()`: Add data to chunk queues
* `request_reset()`, `request_config_reset()`: Reset request state for reuse

Sources: [src/connections.c L393-L406](https://github.com/lighttpd/lighttpd1.4/blob/3d550097/src/connections.c#L393-L406)

 [src/connections.c L407-L424](https://github.com/lighttpd/lighttpd1.4/blob/3d550097/src/connections.c#L407-L424)

 [src/connections.c L427-L433](https://github.com/lighttpd/lighttpd1.4/blob/3d550097/src/connections.c#L427-L433)

## Subsystem Integration

The integration between subsystems creates a complete request processing pipeline:

```mermaid
sequenceDiagram
  participant Client
  participant Network I/O
  participant Connection Management
  participant Event Handling
  participant Request Processing
  participant Plugin System
  participant Configuration
  participant Memory Management

  Client->>Network I/O: Connect
  Network I/O->>Connection Management: connection_accepted()
  Connection Management->>Event Handling: Register events
  loop [For each request]
    Event Handling->>Connection Management: connection_handle_fdevent()
    Connection Management->>Request Processing: connection_state_machine()
    Request Processing->>Memory Management: Get buffers/chunks
    Request Processing->>Configuration: config_patch_config()
    Request Processing->>Plugin System: plugins_call_handle_*()
    Plugin System->>Request Processing: Generate response
    Request Processing->>Connection Management: Write response
    Connection Management->>Network I/O: Send to client
  end
  Network I/O->>Client: Response data
  Client->>Network I/O: Disconnect
  Network I/O->>Connection Management: connection_close()
  Connection Management->>Memory Management: Return resources
```

This integrated pipeline demonstrates how the subsystems work together to:

1. Accept client connections (Network I/O)
2. Manage connection states (Connection Management)
3. Handle I/O events efficiently (Event Handling)
4. Process HTTP requests (Request Processing)
5. Apply plugin hooks (Plugin Architecture)
6. Configure behavior (Configuration System)
7. Manage memory resources (Memory Management)

The coordination between these subsystems enables lighttpd to efficiently handle high-concurrency workloads while maintaining a small memory footprint.

Sources: [src/server.c L494-L544](https://github.com/lighttpd/lighttpd1.4/blob/3d550097/src/server.c#L494-L544)

 [src/connections.c L589-L628](https://github.com/lighttpd/lighttpd1.4/blob/3d550097/src/connections.c#L589-L628)

 [src/connections.c L826-L835](https://github.com/lighttpd/lighttpd1.4/blob/3d550097/src/connections.c#L826-L835)

## Summary

Lighttpd's core subsystems form a tightly integrated foundation that enables:

| Subsystem | Main Responsibility | Key Components |
| --- | --- | --- |
| Connection Management | Client connection lifecycle | `connection` structure, state machine |
| Request Processing | HTTP protocol handling | Request states, HTTP parsing |
| Event Handling | I/O multiplexing | Event loop, callbacks |
| Plugin Architecture | Extensibility | Hook system, plugin interface |
| Network I/O | Socket operations | Socket handling, data transfer |
| Configuration | Server behavior | Config parsing, conditions |
| Memory Management | Efficient resource use | Buffer, chunk, request pools |

These core subsystems provide the foundational capabilities upon which the entire web server is built, enabling lighttpd's reputation for efficiency, performance, and scalability.