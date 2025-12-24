# Authentication and Authorization

> **Relevant source files**
> * [src/mod_auth.c](https://github.com/lighttpd/lighttpd1.4/blob/3d550097/src/mod_auth.c)
> * [src/mod_authn_dbi.c](https://github.com/lighttpd/lighttpd1.4/blob/3d550097/src/mod_authn_dbi.c)
> * [src/mod_authn_file.c](https://github.com/lighttpd/lighttpd1.4/blob/3d550097/src/mod_authn_file.c)
> * [src/mod_authn_gssapi.c](https://github.com/lighttpd/lighttpd1.4/blob/3d550097/src/mod_authn_gssapi.c)
> * [src/mod_authn_ldap.c](https://github.com/lighttpd/lighttpd1.4/blob/3d550097/src/mod_authn_ldap.c)
> * [src/mod_authn_pam.c](https://github.com/lighttpd/lighttpd1.4/blob/3d550097/src/mod_authn_pam.c)
> * [src/mod_authn_sasl.c](https://github.com/lighttpd/lighttpd1.4/blob/3d550097/src/mod_authn_sasl.c)
> * [src/mod_vhostdb_dbi.c](https://github.com/lighttpd/lighttpd1.4/blob/3d550097/src/mod_vhostdb_dbi.c)
> * [src/mod_vhostdb_ldap.c](https://github.com/lighttpd/lighttpd1.4/blob/3d550097/src/mod_vhostdb_ldap.c)
> * [src/mod_vhostdb_mysql.c](https://github.com/lighttpd/lighttpd1.4/blob/3d550097/src/mod_vhostdb_mysql.c)
> * [src/mod_vhostdb_pgsql.c](https://github.com/lighttpd/lighttpd1.4/blob/3d550097/src/mod_vhostdb_pgsql.c)

This page documents the authentication and authorization subsystem in lighttpd, which allows the web server to verify user identities and control access to resources based on credentials and rules.

## Overview

The authentication and authorization system in lighttpd provides a flexible framework for controlling access to web resources. The system consists of:

1. A core authentication framework that handles HTTP auth protocols
2. Multiple authentication backends for credential storage and verification
3. Authorization rules for controlling access based on authenticated identities

The system is primarily implemented through `mod_auth.c` along with several backend-specific modules that support different credential storage mechanisms.

```mermaid
flowchart TD

UA["User Agent"]
MOD_AUTH["mod_auth.c - Core Framework"]
BASIC["Basic Auth"]
DIGEST["Digest Auth"]
NEGOTIATE["Negotiate (GSSAPI)"]
HTF["File-based (htpasswd/htdigest)"]
LDAP["LDAP"]
GSSAPI["GSSAPI/Kerberos"]
DBI["Database (DBI)"]
PAM["PAM"]
SASL["SASL"]
RULES["Access Rules"]
CACHE["Auth Cache"]
LDAPSERVER["LDAP Server"]
KDC["Kerberos KDC"]
DATABASE["Databases"]
PAMSERVICES["PAM Services"]

UA --> MOD_AUTH
LDAP --> LDAPSERVER
GSSAPI --> KDC
DBI --> DATABASE
PAM --> PAMSERVICES

subgraph subGraph5 ["External Systems"]
    LDAPSERVER
    KDC
    DATABASE
    PAMSERVICES
end

subgraph lighttpd ["lighttpd"]
    MOD_AUTH
    MOD_AUTH --> BASIC
    MOD_AUTH --> DIGEST
    MOD_AUTH --> NEGOTIATE
    BASIC --> HTF
    BASIC --> LDAP
    BASIC --> DBI
    BASIC --> PAM
    BASIC --> SASL
    DIGEST --> HTF
    NEGOTIATE --> GSSAPI
    HTF --> MOD_AUTH
    LDAP --> MOD_AUTH
    GSSAPI --> MOD_AUTH
    DBI --> MOD_AUTH
    PAM --> MOD_AUTH
    SASL --> MOD_AUTH
    MOD_AUTH --> RULES
    MOD_AUTH --> CACHE
    RULES --> MOD_AUTH

subgraph Authorization ["Authorization"]
    RULES
    CACHE
end

subgraph subGraph2 ["Authentication Backends"]
    HTF
    LDAP
    GSSAPI
    DBI
    PAM
    SASL
end

subgraph subGraph1 ["Authentication Schemes"]
    BASIC
    DIGEST
    NEGOTIATE
end
end

subgraph subGraph0 ["HTTP Client"]
    UA
end
```

Sources:

* [src/mod_auth.c](https://github.com/lighttpd/lighttpd1.4/blob/3d550097/src/mod_auth.c)
* [src/mod_authn_file.c](https://github.com/lighttpd/lighttpd1.4/blob/3d550097/src/mod_authn_file.c)
* [src/mod_authn_ldap.c](https://github.com/lighttpd/lighttpd1.4/blob/3d550097/src/mod_authn_ldap.c)
* [src/mod_authn_gssapi.c](https://github.com/lighttpd/lighttpd1.4/blob/3d550097/src/mod_authn_gssapi.c)
* [src/mod_authn_dbi.c](https://github.com/lighttpd/lighttpd1.4/blob/3d550097/src/mod_authn_dbi.c)
* [src/mod_authn_pam.c](https://github.com/lighttpd/lighttpd1.4/blob/3d550097/src/mod_authn_pam.c)
* [src/mod_authn_sasl.c](https://github.com/lighttpd/lighttpd1.4/blob/3d550097/src/mod_authn_sasl.c)

## Authentication Framework Architecture

The authentication framework in lighttpd is designed with a modular architecture that separates different aspects of the authentication process:

1. **Authentication Schemes**: Define how credentials are transmitted and processed (Basic, Digest, Negotiate)
2. **Authentication Backends**: Define where and how credentials are stored and verified
3. **Authorization Rules**: Define access control based on authenticated identity

```mermaid
classDiagram
    class http_auth_scheme_t {
        const char* name
        void* p_d
        handler_t (*checkfn)()
    }
    class http_auth_backend_t {
        const char* name
        void* p_d
        handler_t (*basic)()
        handler_t (*digest)()
    }
    class http_auth_require_t {
        const http_auth_scheme_t* scheme
        int algorithm
        const buffer* realm
        array* user
        array* group
        array* host
        int valid_user
        const buffer* nonce_secret
        int userhash
    }
    class http_auth_cache_entry {
        const http_auth_require_t* require
        unix_time64_t ctime
        int dalgo
        uint32_t dlen
        uint32_t ulen
        uint32_t klen
        char* k
        char* username
        char* pwdigest
    }
    class mod_auth {
    }
    mod_auth --> http_auth_scheme_t : registers
    mod_auth --> http_auth_backend_t : registers
    mod_auth --> http_auth_require_t : creates
    mod_auth --> http_auth_cache_entry : manages
    http_auth_scheme_t -- http_auth_require_t : used by
    http_auth_backend_t -- http_auth_require_t : used by
```

Sources:

* [src/mod_auth.c L28-L56](https://github.com/lighttpd/lighttpd1.4/blob/3d550097/src/mod_auth.c#L28-L56)
* [src/mod_auth.c L215-L230](https://github.com/lighttpd/lighttpd1.4/blob/3d550097/src/mod_auth.c#L215-L230)
* [src/mod_auth.c L259-L289](https://github.com/lighttpd/lighttpd1.4/blob/3d550097/src/mod_auth.c#L259-L289)

### Core Authentication Process

Lighttpd's authentication process follows a defined flow when a request requires authentication:

```mermaid
sequenceDiagram
  participant Client
  participant mod_auth
  participant AuthScheme
  participant AuthBackend
  participant Rules

  Client->>mod_auth: HTTP Request
  mod_auth->>mod_auth: mod_auth_uri_handler
  loop [Credentials valid]
    mod_auth->>Client: Continue processing (HANDLER_GO_ON)
    mod_auth->>Rules: Check authorization rules
    Rules->>mod_auth: Authorization result
    mod_auth->>AuthScheme: Call scheme->checkfn()
    AuthScheme->>Client: 401 Unauthorized with WWW-Authenticate
    AuthScheme->>AuthBackend: Verify credentials
    AuthBackend->>AuthScheme: Credential check result
    AuthScheme->>Rules: Check authorization rules
    Rules->>AuthScheme: Authorization result
    AuthScheme->>mod_auth: HANDLER_GO_ON or HANDLER_ERROR
    AuthScheme->>Client: 401 Unauthorized
    mod_auth->>Client: Continue to resource
    mod_auth->>Client: Return error response
  end
```

Sources:

* [src/mod_auth.c L677-L702](https://github.com/lighttpd/lighttpd1.4/blob/3d550097/src/mod_auth.c#L677-L702)
* [src/mod_auth.c L215-L218](https://github.com/lighttpd/lighttpd1.4/blob/3d550097/src/mod_auth.c#L215-L218)

## Authentication Schemes

Lighttpd supports multiple authentication schemes, each providing a different method for the client to authenticate:

### Basic Authentication

Basic authentication involves sending username:password in a Base64-encoded format. While simple, it's not secure over unencrypted connections as credentials are easily decoded.

The implementation in `mod_auth.c` handles Basic authentication through:

* `mod_auth_check_basic()`: Main handler for Basic auth
* `mod_auth_send_401_unauthorized_basic()`: Generates 401 responses for Basic auth

```mermaid
flowchart TD

A["mod_auth_check_basic()"]
B["Authorization header<br>present with 'Basic '?"]
C["Send 401 with<br>WWW-Authenticate: Basic"]
D["Decode Base64 token"]
E["Extract username:password"]
F["Auth cache hit?"]
G["Compare password using<br>constant-time comparison"]
H["Call backend->basic()"]
I["Set REMOTE_USER env var"]
J["Return HANDLER_GO_ON"]

A --> B
B --> C
B --> D
D --> E
E --> F
F --> G
F --> H
G --> I
G --> C
H --> I
H --> C
I --> J
```

Sources:

* [src/mod_auth.c L745-L871](https://github.com/lighttpd/lighttpd1.4/blob/3d550097/src/mod_auth.c#L745-L871)

### Digest Authentication

Digest authentication is more secure than Basic auth, as it doesn't send the password directly. Instead, it uses a hashing mechanism to prove knowledge of the password.

The implementation in `mod_auth.c` includes:

* `mod_auth_check_digest()`: Handles Digest auth
* `mod_auth_digest_mutate()`: Generates the proper digest for verification
* `mod_auth_digest_www_authenticate()`: Generates challenge responses

```mermaid
flowchart TD

A["mod_auth_check_digest()"]
B["Authorization header<br>present with 'Digest '?"]
C["Send 401 with<br>WWW-Authenticate: Digest"]
D["Parse digest parameters"]
E["Required parameters present?"]
F["Send 400 Bad Request"]
G["Call backend->digest()"]
H["Credentials valid?"]
I["Generate response digest"]
J["Request digest matches<br>response digest?"]
K["Set REMOTE_USER env var"]
L["Return HANDLER_GO_ON"]

A --> B
B --> C
B --> D
D --> E
E --> F
E --> G
G --> H
H --> C
H --> I
I --> J
J --> C
J --> K
K --> L
```

Sources:

* [src/mod_auth.c L874-L1152](https://github.com/lighttpd/lighttpd1.4/blob/3d550097/src/mod_auth.c#L874-L1152)

### Negotiate Authentication (GSSAPI/Kerberos)

Negotiate authentication is primarily used for Kerberos/GSSAPI authentication and is implemented in `mod_authn_gssapi.c`. This scheme provides single sign-on capabilities in environments like Active Directory.

```mermaid
flowchart TD

A["mod_authn_gssapi_check()"]
B["Authorization header<br>present with 'Negotiate '?"]
C["Send 401 with<br>WWW-Authenticate: Negotiate"]
D["mod_authn_gssapi_check_spnego()"]
E["Initialize GSSAPI"]
F["Import server principal name"]
G["Acquire server credentials"]
H["Accept security context"]
I["Context established?"]
J["Get client name"]
K["Matches auth rules?"]
L["Store credentials<br>if configured"]
M["Set REMOTE_USER env var"]
N["Return HANDLER_GO_ON"]

A --> B
B --> C
B --> D
D --> E
E --> F
F --> G
G --> H
H --> I
I --> C
I --> J
J --> K
K --> C
K --> L
L --> M
M --> N
```

Sources:

* [src/mod_authn_gssapi.c L254-L461](https://github.com/lighttpd/lighttpd1.4/blob/3d550097/src/mod_authn_gssapi.c#L254-L461)

## Authentication Backends

Lighttpd supports multiple authentication backends that store and verify credentials. Each backend implements at least one of the auth scheme verification functions.

### File-based Authentication (mod_authn_file)

This backend supports reading credentials from local files in htpasswd, htdigest, or plain text formats.

```mermaid
flowchart TD

A["mod_authn_file_init()"]
B["Register backends:<br>- htpasswd<br>- htdigest<br>- plain"]
C["mod_authn_file_htpasswd_basic()"]
D["Get password from file"]
E["Password format?"]
F["Verify SHA1 hash"]
G["Verify APR1-MD5 hash"]
H["Verify with crypt()"]
I["Password matches?"]
J["Return HANDLER_GO_ON"]
K["Return HANDLER_ERROR"]
L["mod_authn_file_htdigest_digest()"]
M["Search for username+realm in file"]
N["Found?"]
O["Extract stored digest"]
P["Return HANDLER_ERROR"]
Q["Return HANDLER_GO_ON"]
R["mod_authn_file_plain_basic()"]
S["Get password from file"]
T["Compare with plaintext"]
U["Password matches?"]
V["Return HANDLER_GO_ON"]
W["Return HANDLER_ERROR"]

A --> B
C --> D
D --> E
E --> F
E --> G
E --> H
F --> I
G --> I
H --> I
I --> J
I --> K
L --> M
M --> N
N --> O
N --> P
O --> Q
R --> S
S --> T
T --> U
U --> V
U --> W
```

Sources:

* [src/mod_authn_file.c L54-L59](https://github.com/lighttpd/lighttpd1.4/blob/3d550097/src/mod_authn_file.c#L54-L59)
* [src/mod_authn_file.c L60-L81](https://github.com/lighttpd/lighttpd1.4/blob/3d550097/src/mod_authn_file.c#L60-L81)
* [src/mod_authn_file.c L306-L335](https://github.com/lighttpd/lighttpd1.4/blob/3d550097/src/mod_authn_file.c#L306-L335)
* [src/mod_authn_file.c L397-L432](https://github.com/lighttpd/lighttpd1.4/blob/3d550097/src/mod_authn_file.c#L397-L432)
* [src/mod_authn_file.c L697-L740](https://github.com/lighttpd/lighttpd1.4/blob/3d550097/src/mod_authn_file.c#L697-L740)

### LDAP Authentication (mod_authn_ldap)

This backend queries an LDAP directory for user authentication, supporting both Basic and Digest authentication methods. It's particularly useful in enterprise environments with centralized user directories.

```mermaid
flowchart TD

A["mod_authn_ldap_basic()"]
B["Patch LDAP configuration"]
C["Connect to LDAP server"]
D["Build filter with username"]
E["LDAP search for user"]
F["User found?"]
G["Return HANDLER_ERROR"]
H["Extract password/hash"]
I["Verify password"]
J["Password verified?"]
K["Check authorization rules"]
L["Rules match?"]
M["Return HANDLER_GO_ON"]

A --> B
B --> C
C --> D
D --> E
E --> F
F --> G
F --> H
H --> I
I --> J
J --> G
J --> K
K --> L
L --> G
L --> M
```

Sources:

* [src/mod_authn_ldap.c L572-L664](https://github.com/lighttpd/lighttpd1.4/blob/3d550097/src/mod_authn_ldap.c#L572-L664)

### GSSAPI/Kerberos Authentication (mod_authn_gssapi)

This backend provides Kerberos authentication, supporting both the Negotiate scheme and Basic authentication with Kerberos backend verification.

```mermaid
flowchart TD

A["mod_authn_gssapi_basic()"]
B["Initialize Kerberos context"]
C["Create principal from username"]
D["Get/create krb5 ccache"]
E["Verify password with krb5_get_init_creds_password()"]
F["Password verified?"]
G["Return HANDLER_ERROR"]
H["Store credentials if configured"]
I["Check authorization rules"]
J["Rules match?"]
K["Return HANDLER_GO_ON"]

A --> B
B --> C
C --> D
D --> E
E --> F
F --> G
F --> H
H --> I
I --> J
J --> G
J --> K
```

Sources:

* [src/mod_authn_gssapi.c L626-L764](https://github.com/lighttpd/lighttpd1.4/blob/3d550097/src/mod_authn_gssapi.c#L626-L764)

### Database Authentication (mod_authn_dbi)

This backend uses libdbi to connect to various database systems for credential storage and verification, supporting both Basic and Digest authentication.

```mermaid
flowchart TD

A["mod_authn_dbi_basic()"]
B["Patch DBI configuration"]
C["Prepare SQL query"]
D["Execute query with username/realm"]
E["Password found?"]
F["Return HANDLER_ERROR"]
G["Compare password based on format"]
H["Password matches?"]
I["Check authorization rules"]
J["Rules match?"]
K["Return HANDLER_GO_ON"]

A --> B
B --> C
C --> D
D --> E
E --> F
E --> G
G --> H
H --> F
H --> I
I --> J
J --> F
J --> K
```

Sources:

* [src/mod_authn_dbi.c L398-L476](https://github.com/lighttpd/lighttpd1.4/blob/3d550097/src/mod_authn_dbi.c#L398-L476)

### Other Authentication Backends

Lighttpd also supports additional authentication backends:

* **PAM Authentication** (mod_authn_pam): Uses the Pluggable Authentication Modules system
* **SASL Authentication** (mod_authn_sasl): Implements the Simple Authentication and Security Layer framework

## Authorization Process

After a user is authenticated, the authorization process determines if the authenticated user has permission to access the requested resource based on configured rules.

### Rule-based Authorization

Authorization rules in lighttpd are specified in the `auth.require` configuration directive and can include:

* **user**: Specific usernames that are allowed access
* **group**: Group names that are allowed access
* **valid-user**: Any successfully authenticated user is allowed access

The authorization logic is implemented in `http_auth_match_rules()`:

```mermaid
flowchart TD

A["http_auth_match_rules()"]
B["valid_user set?"]
C["Return true<br>(access granted)"]
D["user list specified?"]
E["User in user list?"]
F["group list specified?"]
G["User in any<br>specified group?"]
H["Return false<br>(access denied)"]

A --> B
B --> C
B --> D
D --> E
E --> C
E --> F
D --> F
F --> G
G --> C
G --> H
F --> H
```

Sources:

* [src/mod_auth.c L352-L439](https://github.com/lighttpd/lighttpd1.4/blob/3d550097/src/mod_auth.c#L352-L439)
* [src/mod_auth.c L690-L701](https://github.com/lighttpd/lighttpd1.4/blob/3d550097/src/mod_auth.c#L690-L701)

## Authentication Cache

To improve performance, lighttpd can cache authentication results, reducing the need to repeatedly query backends for the same credentials. The cache is implemented in `http_auth_cache_*` functions:

```mermaid
flowchart TD

A["mod_auth_check_basic()"]
B["Cache configured?"]
C["Query auth backend"]
D["Cache entry exists?"]
E["Compare password with cached digest"]
F["Password verified?"]
G["Store in cache<br>if cache enabled"]
H["Return HANDLER_ERROR"]
I["Return HANDLER_GO_ON"]

A --> B
B --> C
B --> D
D --> E
D --> C
C --> F
F --> G
F --> H
E --> F
G --> I
```

The cache is periodically cleaned to remove expired entries through the `mod_auth_periodic` trigger function.

Sources:

* [src/mod_auth.c L59-L102](https://github.com/lighttpd/lighttpd1.4/blob/3d550097/src/mod_auth.c#L59-L102)
* [src/mod_auth.c L103-L210](https://github.com/lighttpd/lighttpd1.4/blob/3d550097/src/mod_auth.c#L103-L210)
* [src/mod_auth.c L788-L840](https://github.com/lighttpd/lighttpd1.4/blob/3d550097/src/mod_auth.c#L788-L840)

## Configuration Examples

### Basic Authentication with File Backend

```javascript
# Enable mod_auth
server.modules += ( "mod_auth" )

# Set up basic authentication for a directory
$HTTP["url"] =~ "^/protected/" {
    auth.backend = "htpasswd"
    auth.backend.htpasswd.userfile = "/path/to/.htpasswd"
    auth.require = (
        "" => (
            "method" => "basic",
            "realm" => "Protected Area",
            "require" => "valid-user"
        )
    )
}
```

### Digest Authentication with File Backend

```javascript
# Enable mod_auth
server.modules += ( "mod_auth" )

# Set up digest authentication for a directory
$HTTP["url"] =~ "^/protected/" {
    auth.backend = "htdigest"
    auth.backend.htdigest.userfile = "/path/to/.htdigest"
    auth.require = (
        "" => (
            "method" => "digest",
            "realm" => "Protected Area",
            "require" => "valid-user"
        )
    )
}
```

### LDAP Authentication

```javascript
# Enable mod_auth
server.modules += ( "mod_auth" )

# Set up LDAP authentication
$HTTP["url"] =~ "^/protected/" {
    auth.backend = "ldap"
    auth.backend.ldap.hostname = "ldap.example.com"
    auth.backend.ldap.base-dn = "ou=people,dc=example,dc=com"
    auth.backend.ldap.filter = "(&(uid=?)(objectClass=posixAccount))"
    auth.backend.ldap.ca-file = "/path/to/ca.pem"
    auth.backend.ldap.starttls = "enable"
    
    auth.require = (
        "" => (
            "method" => "basic",
            "realm" => "LDAP Protected Area",
            "require" => "valid-user"
        )
    )
}
```

### Kerberos Authentication (Negotiate)

```javascript
# Enable mod_auth
server.modules += ( "mod_auth" )

# Set up Kerberos/GSSAPI authentication
$HTTP["url"] =~ "^/protected/" {
    auth.backend = "gssapi"
    auth.backend.gssapi.keytab = "/path/to/keytab"
    auth.backend.gssapi.principal = "HTTP/server.example.com@EXAMPLE.COM"
    
    auth.require = (
        "" => (
            "method" => "gssapi",
            "realm" => "EXAMPLE.COM",
            "require" => "valid-user"
        )
    )
}
```

## Conclusion

The authentication and authorization subsystem in lighttpd provides a flexible and extensible framework for securing web resources. With support for multiple authentication schemes and backends, it can be adapted to various environments from simple file-based authentication to enterprise directory services.

The modular design allows for easy extension with additional backends while maintaining a consistent interface for the core authentication process. The caching mechanism enhances performance by reducing the need for repeated authentication requests.