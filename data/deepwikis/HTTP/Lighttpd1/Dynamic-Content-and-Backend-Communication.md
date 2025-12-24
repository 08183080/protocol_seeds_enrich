# Dynamic Content and Backend Communication

> **Relevant source files**
> * [src/fdevent.c](https://github.com/lighttpd/lighttpd1.4/blob/3d550097/src/fdevent.c)
> * [src/fdevent.h](https://github.com/lighttpd/lighttpd1.4/blob/3d550097/src/fdevent.h)
> * [src/gw_backend.c](https://github.com/lighttpd/lighttpd1.4/blob/3d550097/src/gw_backend.c)
> * [src/gw_backend.h](https://github.com/lighttpd/lighttpd1.4/blob/3d550097/src/gw_backend.h)
> * [src/mod_cgi.c](https://github.com/lighttpd/lighttpd1.4/blob/3d550097/src/mod_cgi.c)
> * [src/mod_fastcgi.c](https://github.com/lighttpd/lighttpd1.4/blob/3d550097/src/mod_fastcgi.c)
> * [src/mod_proxy.c](https://github.com/lighttpd/lighttpd1.4/blob/3d550097/src/mod_proxy.c)
> * [src/mod_scgi.c](https://github.com/lighttpd/lighttpd1.4/blob/3d550097/src/mod_scgi.c)

This document explains how lighttpd handles dynamic content generation and communicates with backend application servers. It covers the gateway architecture, supported protocols (FastCGI, CGI, SCGI, and HTTP proxy), and the request/response flow between lighttpd and backend application servers.

For information about static content serving, see [Static Content Serving](/lighttpd/lighttpd1.4/4.1-static-content-serving).

## 1. Gateway Architecture Overview

Lighttpd uses a unified gateway architecture for backend communication across different protocols. This architecture provides common functionality for process management, connection handling, and load balancing while allowing protocol-specific implementations.

```mermaid
flowchart TD

L["gw_proc Management"]
M["Process Spawning (Local)"]
N["Connection Pooling"]
O["Load Balancing"]
P["Health Monitoring"]
A["HTTP Request"]
B["Request Routing"]
C["Extension/Path Match?"]
D["Handler Selection"]
E["gw_handler_ctx Creation"]
F["Backend Selection"]
G["Connection Setup"]
H["Protocol-specific Processing"]
I["Send to Backend"]
J["Receive Response"]
K["Forward to Client"]

subgraph subGraph1 ["Backend Process Management"]
    L
    M
    N
    O
    P
    L --> M
    L --> N
    L --> O
    L --> P
end

subgraph subGraph0 ["Client Request Processing"]
    A
    B
    C
    D
    E
    F
    G
    H
    I
    J
    K
    A --> B
    B --> C
    C --> D
    D --> E
    E --> F
    F --> G
    G --> H
    H --> I
    I --> J
    J --> K
end
```

Sources: [src/gw_backend.h L242-L343](https://github.com/lighttpd/lighttpd1.4/blob/3d550097/src/gw_backend.h#L242-L343)

 [src/gw_backend.c L46-L131](https://github.com/lighttpd/lighttpd1.4/blob/3d550097/src/gw_backend.c#L46-L131)

### 1.1 Common Gateway Components

The gateway system is built around several key data structures that work together to manage backend connections:

```mermaid
classDiagram
    class gw_exts {
        +gw_extension* exts
        +uint32_t used
        +uint32_t size
    }
    class gw_extension {
        +buffer key
        +gw_host** hosts
        +uint32_t used
        +uint32_t size
        +int last_used_ndx
    }
    class gw_host {
        +gw_proc* first
        +uint32_t active_procs
        +buffer* id
        +buffer* host
        +unsigned short port
        +buffer* unixsocket
        +buffer* bin_path
        +array* bin_env
        +uint32_t num_procs
        +unsigned short min_procs
        +unsigned short max_procs
    }
    class gw_proc {
        +enum state
        +uint32_t load
        +pid_t pid
        +int is_local
        +buffer* connection_name
        +buffer* unixsocket
        +unsigned short port
    }
    class gw_handler_ctx {
        +gw_proc* proc
        +gw_host* host
        +gw_extension* ext
        +chunkqueue wb
        +chunkqueue* rb
        +int fd
        +pid_t pid
        +request_st* r
    }
    gw_exts --> gw_extension : contains
    gw_extension --> gw_host : references
    gw_host --> gw_proc : manages
    gw_handler_ctx --> gw_proc : uses
    gw_handler_ctx --> gw_host : references
    gw_handler_ctx --> gw_extension : references
```

Sources: [src/gw_backend.h L12-L343](https://github.com/lighttpd/lighttpd1.4/blob/3d550097/src/gw_backend.h#L12-L343)

Each module (FastCGI, CGI, SCGI, Proxy) builds on this shared framework by:

1. Implementing protocol-specific environment creation
2. Defining communication formats
3. Providing custom response parsing

## 2. Supported Backend Protocols

Lighttpd supports multiple protocols for communicating with backend application servers:

| Protocol | Module | Description | Key Features |
| --- | --- | --- | --- |
| FastCGI | mod_fastcgi | Binary protocol for persistent app servers | Multiplexing, connection pooling, local spawning |
| CGI | mod_cgi | Traditional CGI for executing scripts | Process per request, simple integration |
| SCGI | mod_scgi | Simple CGI - streamlined FastCGI alternative | Simpler than FastCGI, persistent connections |
| HTTP Proxy | mod_proxy | Forward requests to HTTP servers | Header manipulation, URL rewriting, SSL |

### 2.1 FastCGI

FastCGI is a binary protocol that allows persistent application servers to handle multiple requests over a single connection. It's significantly more efficient than traditional CGI.

```mermaid
sequenceDiagram
  participant Client
  participant Lighttpd
  participant FastCGI_Process

  Client->>Lighttpd: HTTP Request
  note over Lighttpd: fcgi_check_extension
  Lighttpd->>FastCGI_Process: FCGI_BEGIN_REQUEST
  Lighttpd->>FastCGI_Process: FCGI_PARAMS
  Lighttpd->>FastCGI_Process: FCGI_STDIN (request body)
  Lighttpd->>FastCGI_Process: FCGI_STDIN (empty, to signal end)
  FastCGI_Process->>Lighttpd: FCGI_STDOUT (response headers)
  FastCGI_Process->>Lighttpd: FCGI_STDOUT (response body)
  FastCGI_Process->>Lighttpd: FCGI_STDOUT (empty, to signal end)
  FastCGI_Process->>Lighttpd: FCGI_END_REQUEST
  Lighttpd->>Client: HTTP Response
```

Key implementation details:

* FastCGI protocol constants defined in [src/mod_fastcgi.c L19-L29](https://github.com/lighttpd/lighttpd1.4/blob/3d550097/src/mod_fastcgi.c#L19-L29)
* Environment setup in [src/mod_fastcgi.c L227-L296](https://github.com/lighttpd/lighttpd1.4/blob/3d550097/src/mod_fastcgi.c#L227-L296)
* Response parsing in [src/mod_fastcgi.c L363-L468](https://github.com/lighttpd/lighttpd1.4/blob/3d550097/src/mod_fastcgi.c#L363-L468)

Sources: [src/mod_fastcgi.c L1-L558](https://github.com/lighttpd/lighttpd1.4/blob/3d550097/src/mod_fastcgi.c#L1-L558)

### 2.2 CGI

The Common Gateway Interface (CGI) is the traditional method for executing server-side scripts. It spawns a new process for each request.

```mermaid
sequenceDiagram
  participant Client
  participant Lighttpd
  participant CGI_Script

  Client->>Lighttpd: HTTP Request
  note over Lighttpd: cgi_is_handled
  Lighttpd->>CGI_Script: fork/exec process
  Lighttpd->>CGI_Script: Write request body to STDIN
  CGI_Script->>Lighttpd: Write response headers to STDOUT
  CGI_Script->>Lighttpd: Write response body to STDOUT
  CGI_Script->>Lighttpd: Process exits
  Lighttpd->>Client: HTTP Response
```

Key implementation details:

* Process creation in [src/mod_cgi.c L808-L1037](https://github.com/lighttpd/lighttpd1.4/blob/3d550097/src/mod_cgi.c#L808-L1037)
* Environment setup in [src/mod_cgi.c L664-L680](https://github.com/lighttpd/lighttpd1.4/blob/3d550097/src/mod_cgi.c#L664-L680)
* Response parsing in [src/mod_cgi.c L584-L602](https://github.com/lighttpd/lighttpd1.4/blob/3d550097/src/mod_cgi.c#L584-L602)

Sources: [src/mod_cgi.c L1-L1072](https://github.com/lighttpd/lighttpd1.4/blob/3d550097/src/mod_cgi.c#L1-L1072)

### 2.3 SCGI

The Simple Common Gateway Interface (SCGI) is a simpler alternative to FastCGI that's easier to implement in application servers.

```mermaid
sequenceDiagram
  participant Client
  participant Lighttpd
  participant SCGI_Server

  Client->>Lighttpd: HTTP Request
  note over Lighttpd: scgi_check_extension
  Lighttpd->>SCGI_Server: Connect
  Lighttpd->>SCGI_Server: Send SCGI header (netstring format)
  Lighttpd->>SCGI_Server: Send request body
  SCGI_Server->>Lighttpd: Send response headers
  SCGI_Server->>Lighttpd: Send response body
  Lighttpd->>Client: HTTP Response
```

Key implementation details:

* SCGI environment creation in [src/mod_scgi.c L144-L248](https://github.com/lighttpd/lighttpd1.4/blob/3d550097/src/mod_scgi.c#L144-L248)
* Protocol selection (SCGI or UWSGI) in [src/mod_scgi.c L112-L123](https://github.com/lighttpd/lighttpd1.4/blob/3d550097/src/mod_scgi.c#L112-L123)

Sources: [src/mod_scgi.c L1-L303](https://github.com/lighttpd/lighttpd1.4/blob/3d550097/src/mod_scgi.c#L1-L303)

### 2.4 HTTP Proxy

The HTTP proxy module forwards requests to other HTTP servers and returns their responses to the client.

```mermaid
sequenceDiagram
  participant Client
  participant Lighttpd
  participant HTTP_Backend

  Client->>Lighttpd: HTTP Request
  note over Lighttpd: proxy_check_extension
  note over Lighttpd: Process Forwarded headers
  note over Lighttpd: Rewrite headers/URL if configured
  Lighttpd->>HTTP_Backend: HTTP Request
  HTTP_Backend->>Lighttpd: HTTP Response
  note over Lighttpd: Process response headers
  Lighttpd->>Client: HTTP Response
```

Key implementation details:

* Header forwarding in [src/mod_proxy.c L612-L709](https://github.com/lighttpd/lighttpd1.4/blob/3d550097/src/mod_proxy.c#L612-L709)
* URL path remapping in [src/mod_proxy.c L443-L481](https://github.com/lighttpd/lighttpd1.4/blob/3d550097/src/mod_proxy.c#L443-L481)
* Host header manipulation in [src/mod_proxy.c L430-L439](https://github.com/lighttpd/lighttpd1.4/blob/3d550097/src/mod_proxy.c#L430-L439)

Sources: [src/mod_proxy.c L1-L2824](https://github.com/lighttpd/lighttpd1.4/blob/3d550097/src/mod_proxy.c#L1-L2824)

## 3. Request Processing Flow

The following diagram illustrates how a request flows through lighttpd and to a backend application server:

```mermaid
flowchart TD

A["HTTP Request"]
B["http_response_prepare()"]
C["Module Hook: handle_uri_clean"]
D["Module Hook: handle_subrequest_start"]
E["Match extension/path?"]
F["gw_check_extension()"]
G["Initialize handler_ctx"]
H["Select backend host/proc"]
I["Connect to backend"]
J["Create environment (protocol-specific)"]
K["Send request to backend"]
L["Wait for response"]
M["Parse response headers"]
N["Stream response body"]
O["Handle connection end"]
P["Finalize response"]
Q["HTTP Response"]

I --> J
O --> P

subgraph subGraph2 ["Response Processing"]
    P
    Q
    P --> Q
end

subgraph subGraph1 ["Backend Communication"]
    J
    K
    L
    M
    N
    O
    J --> K
    K --> L
    L --> M
    M --> N
    N --> O
end

subgraph subGraph0 ["Request Processing"]
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
    B --> C
    C --> D
    D --> E
    E --> F
    F --> G
    G --> H
    H --> I
end
```

Sources: [src/mod_fastcgi.c L496-L526](https://github.com/lighttpd/lighttpd1.4/blob/3d550097/src/mod_fastcgi.c#L496-L526)

 [src/mod_cgi.c L1039-L1072](https://github.com/lighttpd/lighttpd1.4/blob/3d550097/src/mod_cgi.c#L1039-L1072)

 [src/gw_backend.c L267-L346](https://github.com/lighttpd/lighttpd1.4/blob/3d550097/src/gw_backend.c#L267-L346)

### 3.1 Extension Matching and Handler Selection

All gateway modules use a similar approach to determine if they should handle a request:

1. Check if the request URI or physical path matches configured extensions
2. If matched, create a handler context
3. Set protocol-specific handlers
4. Register for the appropriate request hooks

```mermaid
flowchart TD

A["Request"]
B["*_check_extension"]
C["Extension match?"]
D["HANDLER_GO_ON"]
E["Create handler_ctx"]
F["Set protocol handlers"]
G["Set backend type"]
H["HANDLER_GO_ON"]

A --> B
B --> C
C --> D
C --> E
E --> F
F --> G
G --> H
```

Sources: [src/mod_fastcgi.c L496-L526](https://github.com/lighttpd/lighttpd1.4/blob/3d550097/src/mod_fastcgi.c#L496-L526)

 [src/mod_cgi.c L1039-L1072](https://github.com/lighttpd/lighttpd1.4/blob/3d550097/src/mod_cgi.c#L1039-L1072)

 [src/mod_scgi.c L251-L271](https://github.com/lighttpd/lighttpd1.4/blob/3d550097/src/mod_scgi.c#L251-L271)

 [src/mod_proxy.c L1788-L1830](https://github.com/lighttpd/lighttpd1.4/blob/3d550097/src/mod_proxy.c#L1788-L1830)

### 3.2 Backend Process Management

For local backends (FastCGI, CGI, SCGI), lighttpd can spawn and manage the backend processes:

```mermaid
flowchart TD

A["gw_spawn_connection()"]
B["Local backend?"]
C["Create socket"]
D["Bind socket"]
E["Setup environment"]
F["Protocol?"]
G["Socket as FCGI_LISTENSOCK_FILENO"]
H["Setup stdin/stdout/stderr"]
I["Socket as STDIN_FILENO"]
J["fork/exec process"]
K["Monitor process state"]
L["Connect to remote socket"]

A --> B
B --> C
C --> D
D --> E
E --> F
F --> G
F --> H
F --> I
G --> J
H --> J
I --> J
J --> K
B --> L
```

Sources: [src/gw_backend.c L504-L710](https://github.com/lighttpd/lighttpd1.4/blob/3d550097/src/gw_backend.c#L504-L710)

 [src/mod_cgi.c L808-L1037](https://github.com/lighttpd/lighttpd1.4/blob/3d550097/src/mod_cgi.c#L808-L1037)

### 3.3 Load Balancing

The gateway architecture includes load balancing capabilities across multiple backend processes:

```mermaid
flowchart TD

A["gw_check_extension()"]
B["Find extension"]
C["Get available hosts"]
D["Balance mode?"]
E["Select next host"]
F["Select least loaded host"]
G["Select/start process"]
H["Increment load counters"]
I["Return handler"]

A --> B
B --> C
C --> D
D --> E
D --> F
E --> G
F --> G
G --> H
H --> I
```

Load balancing modes:

* Round Robin: Distribute requests evenly across backends
* Least Connection: Send to the backend with the fewest active connections

Sources: [src/gw_backend.c L267-L346](https://github.com/lighttpd/lighttpd1.4/blob/3d550097/src/gw_backend.c#L267-L346)

 [src/gw_backend.c L97-L108](https://github.com/lighttpd/lighttpd1.4/blob/3d550097/src/gw_backend.c#L97-L108)

## 4. Protocol-Specific Details

### 4.1 FastCGI Protocol

FastCGI uses a binary protocol with different record types:

| Record Type | Value | Purpose |
| --- | --- | --- |
| FCGI_BEGIN_REQUEST | 1 | Start a new request |
| FCGI_PARAMS | 4 | Send environment variables |
| FCGI_STDIN | 5 | Send request body |
| FCGI_STDOUT | 6 | Receive response data |
| FCGI_STDERR | 7 | Receive error messages |
| FCGI_END_REQUEST | 3 | End the request |

Each record has a header with:

* Version (1 byte)
* Type (1 byte)
* Request ID (2 bytes)
* Content Length (2 bytes)
* Padding Length (1 byte)
* Reserved (1 byte)

Sources: [src/mod_fastcgi.c L170-L181](https://github.com/lighttpd/lighttpd1.4/blob/3d550097/src/mod_fastcgi.c#L170-L181)

 [src/mod_fastcgi.c L305-L338](https://github.com/lighttpd/lighttpd1.4/blob/3d550097/src/mod_fastcgi.c#L305-L338)

### 4.2 SCGI Protocol

SCGI uses a simpler protocol than FastCGI:

1. A length prefix, followed by a colon (netstring format)
2. Key-value pairs as null-terminated strings
3. A comma terminator
4. Request body

For example: `"72:CONTENT_LENGTH\0" + "27\0" + "SCGI\0" + "1\0" + "REQUEST_METHOD\0" + "GET\0" + ","`

Sources: [src/mod_scgi.c L144-L177](https://github.com/lighttpd/lighttpd1.4/blob/3d550097/src/mod_scgi.c#L144-L177)

### 4.3 HTTP Proxy Header Handling

The proxy module has several options for handling HTTP headers:

* Forwarded headers (RFC 7239) [src/mod_proxy.c L612-L709](https://github.com/lighttpd/lighttpd1.4/blob/3d550097/src/mod_proxy.c#L612-L709)
* X-Forwarded-* compatibility [src/mod_proxy.c L624-L655](https://github.com/lighttpd/lighttpd1.4/blob/3d550097/src/mod_proxy.c#L624-L655)
* Host header rewriting [src/mod_proxy.c L430-L439](https://github.com/lighttpd/lighttpd1.4/blob/3d550097/src/mod_proxy.c#L430-L439)
* URL path remapping [src/mod_proxy.c L443-L481](https://github.com/lighttpd/lighttpd1.4/blob/3d550097/src/mod_proxy.c#L443-L481)

## 5. Configuration Examples

Each protocol has its own configuration directives. Here are examples for each:

### 5.1 FastCGI Configuration

```javascript
fastcgi.server = (
  ".php" => (
    "localhost" => (
      "socket" => "/tmp/php-fastcgi.sock",
      "bin-path" => "/usr/bin/php-cgi",
      "min-procs" => 2,
      "max-procs" => 4,
      "max-load-per-proc" => 50,
      "idle-timeout" => 60
    )
  )
)
```

### 5.2 CGI Configuration

```javascript
cgi.assign = (
  ".cgi" => "",
  ".pl" => "/usr/bin/perl",
  ".py" => "/usr/bin/python"
)
```

### 5.3 SCGI Configuration

```javascript
scgi.server = (
  ".php" => (
    "localhost" => (
      "host" => "127.0.0.1",
      "port" => 4000,
      "check-local" => "disable"
    )
  )
)
```

### 5.4 HTTP Proxy Configuration

```javascript
proxy.server = (
  "/api/" => (
    "backend" => (
      "host" => "127.0.0.1",
      "port" => 8080
    )
  )
)
```

## 6. Advanced Features

### 6.1 Protocol Upgrades

Lighttpd supports WebSocket and other protocol upgrades through specific gateway configurations:

```mermaid
sequenceDiagram
  participant Client
  participant Lighttpd
  participant Backend

  Client->>Lighttpd: HTTP Request with Upgrade header
  Lighttpd->>Backend: Forward request with Upgrade header
  Backend->>Lighttpd: 101 Switching Protocols
  note over Lighttpd: Detect protocol upgrade
  note over Lighttpd: Switch to transparent mode
  Client->>Lighttpd: WebSocket frames
  Lighttpd->>Backend: Forward frames unchanged
  Backend->>Lighttpd: WebSocket frames
  Lighttpd->>Client: Forward frames unchanged
```

Upgrade support is implemented in:

* FastCGI: [src/mod_fastcgi.c L470-L494](https://github.com/lighttpd/lighttpd1.4/blob/3d550097/src/mod_fastcgi.c#L470-L494)
* CGI: [src/mod_cgi.c L555-L570](https://github.com/lighttpd/lighttpd1.4/blob/3d550097/src/mod_cgi.c#L555-L570)
* HTTP Proxy: [src/mod_proxy.c L222-L241](https://github.com/lighttpd/lighttpd1.4/blob/3d550097/src/mod_proxy.c#L222-L241)

Sources: [src/gw_backend.h L211-L212](https://github.com/lighttpd/lighttpd1.4/blob/3d550097/src/gw_backend.h#L211-L212)

### 6.2 Error Handling and Recovery

The gateway architecture includes error handling to manage backend failures:

1. Connection failures trigger backend marking as overloaded
2. Overloaded backends get a timeout before retry
3. Dead processes are detected and can be restarted
4. Health monitoring tracks backend status

```mermaid
flowchart TD

A["Connection Attempt"]
B["Success?"]
C["Process Request"]
D["Mark as overloaded"]
E["Set disabled_until time"]
F["Try different backend if available"]
G["Retry after timeout"]

A --> B
B --> C
B --> D
D --> E
E --> F
F --> G
```

Sources: [src/gw_backend.c L279-L346](https://github.com/lighttpd/lighttpd1.4/blob/3d550097/src/gw_backend.c#L279-L346)

 [src/gw_backend.c L358-L370](https://github.com/lighttpd/lighttpd1.4/blob/3d550097/src/gw_backend.c#L358-L370)

## 7. Internal Communication Mechanisms

Lighttpd uses file descriptors and event-based I/O to communicate with backend processes:

```mermaid
flowchart TD

A["fdevent_register()"]
B["Create fdnode"]
C["Set handler function"]
D["Add to event system"]
E["Wait for events"]
F["Call handler"]
G["Unix Domain Socket / TCP Socket"]
H["Write Request"]
I["Read Response"]
J["Process Data"]

E --> G
J --> F

subgraph subGraph1 ["Backend Communication"]
    G
    H
    I
    J
    G --> H
    H --> I
    I --> J
end

subgraph subGraph0 ["Lighttpd File Descriptor Management"]
    A
    B
    C
    D
    E
    F
    A --> B
    B --> C
    C --> D
    D --> E
    E --> F
end
```

Key file descriptor functions:

* Socket creation: [src/fdevent.c L93-L132](https://github.com/lighttpd/lighttpd1.4/blob/3d550097/src/fdevent.c#L93-L132)
* Event registration: [src/fdevent.h L92-L96](https://github.com/lighttpd/lighttpd1.4/blob/3d550097/src/fdevent.h#L92-L96)
* Pipe creation for CGI: [src/fdevent.c L252-L272](https://github.com/lighttpd/lighttpd1.4/blob/3d550097/src/fdevent.c#L252-L272)

Sources: [src/fdevent.c L1-L796](https://github.com/lighttpd/lighttpd1.4/blob/3d550097/src/fdevent.c#L1-L796)

 [src/fdevent.h L1-L179](https://github.com/lighttpd/lighttpd1.4/blob/3d550097/src/fdevent.h#L1-L179)

### 7.1 Process Spawning (For Local Backends)

For local backends like FastCGI and CGI, lighttpd spawns processes using:

```mermaid
flowchart TD

A["gw_spawn_connection() / cgi_create_env()"]
B["Create socket pair"]
C["Set up environment"]
D["Use POSIX spawn?"]
E["posix_spawn()"]
F["fork()"]
G["child process"]
H["exec backend"]
I["parent process"]
J["Close unneeded FDs"]
K["Register FDs with event system"]

A --> B
B --> C
C --> D
D --> E
D --> F
F --> G
G --> H
F --> I
I --> J
J --> K
E --> K
```

Sources: [src/fdevent.c L475-L678](https://github.com/lighttpd/lighttpd1.4/blob/3d550097/src/fdevent.c#L475-L678)

 [src/gw_backend.c L504-L710](https://github.com/lighttpd/lighttpd1.4/blob/3d550097/src/gw_backend.c#L504-L710)

 [src/mod_cgi.c L808-L1037](https://github.com/lighttpd/lighttpd1.4/blob/3d550097/src/mod_cgi.c#L808-L1037)

## Summary

Lighttpd's dynamic content handling framework provides a flexible and efficient way to connect with various backend application servers. The shared gateway architecture handles the common functionality of process management, connection handling, and load balancing, while protocol-specific modules implement the details of each communication protocol.

This design allows for consistent behavior across different backend types while enabling optimizations specific to each protocol. The event-driven I/O system ensures efficient resource usage, and the process management capabilities simplify deployment of application servers.