# Topology Hiding Module

> **Relevant source files**
> * [src/modules/topos/Makefile](https://github.com/kamailio/kamailio/blob/2b4e9f8b/src/modules/topos/Makefile)
> * [src/modules/topos/api.h](https://github.com/kamailio/kamailio/blob/2b4e9f8b/src/modules/topos/api.h)
> * [src/modules/topos/doc/topos.xml](https://github.com/kamailio/kamailio/blob/2b4e9f8b/src/modules/topos/doc/topos.xml)
> * [src/modules/topos/doc/topos_admin.xml](https://github.com/kamailio/kamailio/blob/2b4e9f8b/src/modules/topos/doc/topos_admin.xml)
> * [src/modules/topos/topos_mod.c](https://github.com/kamailio/kamailio/blob/2b4e9f8b/src/modules/topos/topos_mod.c)
> * [src/modules/topos/tps_msg.c](https://github.com/kamailio/kamailio/blob/2b4e9f8b/src/modules/topos/tps_msg.c)
> * [src/modules/topos/tps_msg.h](https://github.com/kamailio/kamailio/blob/2b4e9f8b/src/modules/topos/tps_msg.h)
> * [src/modules/topos/tps_storage.c](https://github.com/kamailio/kamailio/blob/2b4e9f8b/src/modules/topos/tps_storage.c)
> * [src/modules/topos/tps_storage.h](https://github.com/kamailio/kamailio/blob/2b4e9f8b/src/modules/topos/tps_storage.h)

## Introduction

The Topology Hiding Module (topos) provides mechanisms to hide the network topology details in SIP messages while preserving the full functionality of the SIP server. It works by manipulating SIP routing headers (Via, Record-Route, Route) to prevent external entities from seeing the internal network architecture. This is particularly useful for security, privacy, and interoperability purposes.

The module is designed to work transparently, requiring minimal configuration, and supports various storage backends for maintaining state across SIP transactions and dialogs.

For information about general SIP topology hiding concepts, see the [Core Architecture](/kamailio/kamailio/2-core-architecture). For details on the similar but different topoh module (dealing with more general topology hiding), see the [Key Modules](/kamailio/kamailio/4-key-modules) section.

Sources: [src/modules/topos/topos_mod.c L22-L35](https://github.com/kamailio/kamailio/blob/2b4e9f8b/src/modules/topos/topos_mod.c#L22-L35)

 [src/modules/topos/doc/topos_admin.xml L16-L38](https://github.com/kamailio/kamailio/blob/2b4e9f8b/src/modules/topos/doc/topos_admin.xml#L16-L38)

## Architecture Overview

The Topology Hiding Module processes SIP messages at two critical points:

1. When messages are received from the network
2. When messages are sent to the network

At these points, the module manipulates headers to hide internal topology details while preserving the routing information needed for proper message delivery.

```mermaid
flowchart TD

SIP["SIP Traffic"]
NET_IN["Network Layer<br>(Incoming)"]
TOPOS_IN["Topos Module<br>(Message Received)"]
CORE["Kamailio Core Processing"]
TOPOS_OUT["Topos Module<br>(Message Sent)"]
NET_OUT["Network Layer<br>(Outgoing)"]
SIP2["SIP Traffic"]
STORAGE["Storage<br>(DB/Redis/HTable)"]

SIP --> NET_IN
NET_IN --> TOPOS_IN
TOPOS_IN --> CORE
CORE --> TOPOS_OUT
TOPOS_OUT --> NET_OUT
NET_OUT --> SIP2

subgraph subGraph0 ["Topology Hiding Process"]
    TOPOS_IN
    TOPOS_OUT
    STORAGE
    TOPOS_IN --> STORAGE
    TOPOS_OUT --> STORAGE
end
```

The module registers callbacks for SIP message events:

* `tps_msg_received()` - Processes incoming messages
* `tps_msg_sent()` - Processes outgoing messages

In both cases, the module may modify multiple headers to hide topology information.

Sources: [src/modules/topos/topos_mod.c L332-L334](https://github.com/kamailio/kamailio/blob/2b4e9f8b/src/modules/topos/topos_mod.c#L332-L334)

 [src/modules/topos/topos_mod.c L506-L659](https://github.com/kamailio/kamailio/blob/2b4e9f8b/src/modules/topos/topos_mod.c#L506-L659)

## Data Structures

The primary data structure used by the module is `tps_data_t`, which stores all the information needed to track and manipulate SIP messages:

```mermaid
classDiagram
    class tps_data_t {
        +char cbuf[TPS_DATA_SIZE]
        +char *cp
        +str a_uuid
        +str b_uuid
        +str a_callid
        +str a_rr
        +str b_rr
        +str s_rr
        +str a_contact
        +str b_contact
        +str as_contact
        +str bs_contact
        +str a_tag
        +str b_tag
        +str x_via1
        +str x_via2
        +str x_vbranch1
        +str x_via
        +str x_tag
        +str x_rr
        +str y_rr
        +str direction
        +uint32_t s_method_id
    }
```

The data structure stores information for both sides of a SIP dialog:

* "a" prefixed fields represent the caller side
* "b" prefixed fields represent the callee side
* "x" prefixed fields are used for temporary or encoded values
* "as" and "bs" fields hold encoded contact information

Sources: [src/modules/topos/tps_storage.h L52-L90](https://github.com/kamailio/kamailio/blob/2b4e9f8b/src/modules/topos/tps_storage.h#L52-L90)

## Message Processing Flow

The topology hiding process modifies SIP messages in different ways depending on whether it's a request or response, and whether it's part of an existing dialog.

### Request Processing

```mermaid
sequenceDiagram
  participant User Agent
  participant Kamailio with Topos
  participant Topos Storage

  User Agent->>Kamailio with Topos: SIP Request
  Kamailio with Topos->>Kamailio with Topos: tps_msg_received()
  Kamailio with Topos->>Kamailio with Topos: Check if message should be processed
  Kamailio with Topos->>Kamailio with Topos: tps_request_received()
  loop [Dialog Request (To tag exists)]
    Kamailio with Topos->>Topos Storage: tps_storage_load_dialog()
    Topos Storage-->>Kamailio with Topos: Dialog Data
    Kamailio with Topos->>Kamailio with Topos: Detect direction
    Kamailio with Topos->>Kamailio with Topos: Update R-URI
    Kamailio with Topos->>Kamailio with Topos: Restore Route headers
  end
  Kamailio with Topos->>User Agent: Modified SIP Request
```

For incoming requests, the module:

1. Unmasks the Call-ID if Call-ID masking is enabled
2. Extracts headers from the request
3. For in-dialog requests, loads dialog data from storage
4. Detects the direction (upstream/downstream)
5. Updates the R-URI and routing headers

Sources: [src/modules/topos/tps_msg.c L869-L1023](https://github.com/kamailio/kamailio/blob/2b4e9f8b/src/modules/topos/tps_msg.c#L869-L1023)

### Response Processing

```mermaid
sequenceDiagram
  participant User Agent
  participant Kamailio with Topos
  participant Topos Storage

  User Agent->>Kamailio with Topos: SIP Response
  Kamailio with Topos->>Kamailio with Topos: tps_msg_received()
  Kamailio with Topos->>Kamailio with Topos: Check if message should be processed
  Kamailio with Topos->>Kamailio with Topos: tps_response_received()
  Kamailio with Topos->>Topos Storage: tps_storage_load_branch()
  Topos Storage-->>Kamailio with Topos: Branch Data
  Kamailio with Topos->>Topos Storage: tps_storage_load_dialog()
  Topos Storage-->>Kamailio with Topos: Dialog Data
  Kamailio with Topos->>Kamailio with Topos: Detect direction
  Kamailio with Topos->>Kamailio with Topos: Update dialog and branch data
  Kamailio with Topos->>Kamailio with Topos: Reinsert Via, RR headers
  Kamailio with Topos->>User Agent: Modified SIP Response
```

For responses, the module:

1. Loads branch and dialog data
2. Detects the direction
3. Updates the stored data
4. Reinserts Via and Record-Route headers
5. If it's a final failure response (>299) for INVITE or SUBSCRIBE, marks the dialog as completed

Sources: [src/modules/topos/tps_msg.c L1029-L1097](https://github.com/kamailio/kamailio/blob/2b4e9f8b/src/modules/topos/tps_msg.c#L1029-L1097)

## Storage System

The module supports multiple storage backends for maintaining dialog and transaction state:

```mermaid
flowchart TD

TOPOS["Topos Module"]
STORAGE_API["Storage API"]
DB["Database Backend<br>(Default)"]
REDIS["Redis Backend"]
HTABLE["Htable Backend"]
TD["Dialog Table<br>(topos_d)"]
TT["Transaction Table<br>(topos_t)"]

TOPOS --> STORAGE_API
STORAGE_API --> DB
STORAGE_API --> REDIS
STORAGE_API --> HTABLE
DB --> TD
DB --> TT
```

The storage system maintains two types of records:

1. **Dialog records** - Store information about SIP dialogs
2. **Branch/Transaction records** - Store information about individual SIP transactions

The module uses a flexible storage API that can be extended to support different backends:

```python
typedef struct tps_storage_api {
    tps_insert_dialog_f insert_dialog;
    tps_clean_dialogs_f clean_dialogs;
    tps_insert_branch_f insert_branch;
    tps_clean_branches_f clean_branches;
    tps_load_branch_f load_branch;
    tps_load_dialog_f load_dialog;
    tps_update_branch_f update_branch;
    tps_update_dialog_f update_dialog;
    tps_end_dialog_f end_dialog;
} tps_storage_api_t;
```

Sources: [src/modules/topos/tps_storage.c L91-L100](https://github.com/kamailio/kamailio/blob/2b4e9f8b/src/modules/topos/tps_storage.c#L91-L100)

 [src/modules/topos/api.h L49-L60](https://github.com/kamailio/kamailio/blob/2b4e9f8b/src/modules/topos/api.h#L49-L60)

## Contact Header Management

The module provides three methods for handling Contact headers (`contact_mode` parameter):

1. **Mode 0 (SKEYUSER)**: Replace the Contact user part with an encoded key
2. **Mode 1 (RURIUSER)**: Keep the original Contact user part but add a URI parameter
3. **Mode 2 (XAVPUSER)**: Use user parts stored in AVP variables

```mermaid
flowchart TD

CM["contact_mode parameter"]
SKEYUSER["Replace user part<br>with encoded key"]
RURIUSER["Keep user part<br>add URI parameter"]
XAVPUSER["Use user parts<br>from XAVP variables"]
CH["Contact Host Selection"]
RR["Use Record-Route host"]
TH["Use contact_host parameter"]
XV["Use host from XAVP variable"]

subgraph subGraph0 ["Contact Header Processing"]
    CM
    SKEYUSER
    RURIUSER
    XAVPUSER
    CH
    RR
    TH
    XV
    CM --> SKEYUSER
    CM --> RURIUSER
    CM --> XAVPUSER
    SKEYUSER --> CH
    RURIUSER --> CH
    XAVPUSER --> CH
    CH --> RR
    CH --> TH
    CH --> XV
end
```

This flexibility allows the module to work in various environments where specific Contact header formats may be required.

Sources: [src/modules/topos/tps_storage.c L218-L483](https://github.com/kamailio/kamailio/blob/2b4e9f8b/src/modules/topos/tps_storage.c#L218-L483)

## Call-ID Masking

The module can optionally mask the Call-ID header to further hide topology information:

```mermaid
sequenceDiagram
  participant User Agent 1
  participant Kamailio with Topos
  participant User Agent 2

  User Agent 1->>Kamailio with Topos: INVITE (Call-ID: abc123)
  Kamailio with Topos->>Kamailio with Topos: Process message
  loop [Call-ID
    Kamailio with Topos->>Kamailio with Topos: Mask Call-ID
    Kamailio with Topos->>User Agent 2: INVITE (Call-ID: masked-xyz789)
    User Agent 2->>Kamailio with Topos: 200 OK (Call-ID: masked-xyz789)
    Kamailio with Topos->>Kamailio with Topos: Process message
    Kamailio with Topos->>Kamailio with Topos: Unmask Call-ID
  end
  Kamailio with Topos->>User Agent 1: 200 OK (Call-ID: abc123)
```

Call-ID masking requires the topoh module to be loaded with appropriate parameters.

Sources: [src/modules/topos/topos_mod.c L804-L898](https://github.com/kamailio/kamailio/blob/2b4e9f8b/src/modules/topos/topos_mod.c#L804-L898)

## Module Parameters

The module provides numerous configuration parameters to customize its behavior:

| Parameter | Type | Default | Description |
| --- | --- | --- | --- |
| storage | string | "db" | Storage backend type (db, redis, htable) |
| db_url | string | DEFAULT_DB_URL | Database URL for db storage |
| mask_callid | int | 0 | Whether to mask Call-ID headers |
| sanity_checks | int | 0 | Enable sanity checks on received messages |
| branch_expire | int | 180 | Expiration time for branch records (seconds) |
| dialog_expire | int | 10800 | Expiration time for dialog records (seconds) |
| clean_interval | int | 60 | Interval for cleaning expired records (seconds) |
| contact_host | string | "" | Host to use in Contact headers |
| contact_mode | int | 0 | Method for handling Contact headers |
| rr_update | int | 0 | Track and update record-route changes on re-invite |
| header_mode | int | 0 | Mode for header processing (compact vs. verbose) |

Sources: [src/modules/topos/doc/topos_admin.xml L85-L623](https://github.com/kamailio/kamailio/blob/2b4e9f8b/src/modules/topos/doc/topos_admin.xml#L85-L623)

## Integration with Other Modules

The Topology Hiding Module integrates with several other Kamailio modules:

1. **rr module**: Required for record-routing to ensure in-dialog requests are processed correctly
2. **sanity module**: Optional integration for SIP message validation
3. **topoh module**: Required if Call-ID masking is enabled

```mermaid
flowchart TD

TOPOS["Topos Module"]
RR["Record-Route Module<br>(Required)"]
SANITY["Sanity Module"]
TOPOH["TopOH Module"]
DB["DB Module<br>(Default)"]

TOPOS --> RR
TOPOS --> SANITY
TOPOS --> TOPOH
TOPOS --> DB
```

Sources: [src/modules/topos/doc/topos_admin.xml L42-L66](https://github.com/kamailio/kamailio/blob/2b4e9f8b/src/modules/topos/doc/topos_admin.xml#L42-L66)

 [src/modules/topos/topos_mod.c L302-L330](https://github.com/kamailio/kamailio/blob/2b4e9f8b/src/modules/topos/topos_mod.c#L302-L330)

## Module API

The module provides an API that can be used by other modules to extend its functionality:

```python
typedef struct topos_api {
    tps_set_storage_api_f set_storage_api;
    tps_get_dialog_expire_f get_dialog_expire;
    tps_get_branch_expire_f get_branch_expire;
} topos_api_t;
```

This API allows:

1. Setting a custom storage backend
2. Retrieving dialog and branch expiration times

To use the API, other modules must load it using the `topos_load_api()` function.

Sources: [src/modules/topos/api.h L72-L97](https://github.com/kamailio/kamailio/blob/2b4e9f8b/src/modules/topos/api.h#L72-L97)

## Event Routes

The module defines several event routes that can be used to execute custom logic at specific points in message processing:

* `event_route[topos:msg-outgoing]` - Executed before an outgoing message is processed
* `event_route[topos:msg-sending]` - Executed after an outgoing message is processed
* `event_route[topos:msg-incoming]` - Executed before an incoming message is processed
* `event_route[topos:msg-receiving]` - Executed after an incoming message is processed

These event routes provide flexibility for implementing custom logic without modifying the module itself.

Sources: [src/modules/topos/topos_mod.c L117-L124](https://github.com/kamailio/kamailio/blob/2b4e9f8b/src/modules/topos/topos_mod.c#L117-L124)

 [src/modules/topos/topos_mod.c L682-L757](https://github.com/kamailio/kamailio/blob/2b4e9f8b/src/modules/topos/topos_mod.c#L682-L757)

## Limitations and Considerations

When using the Topology Hiding Module, consider the following:

1. **Performance Impact**: The module adds processing overhead for each SIP message and requires storage operations
2. **Dialog Expiration**: Set the dialog_expire parameter to a value larger than your longest expected call duration
3. **Special SIP Extensions**: Some SIP extensions include Call-ID in message bodies, which may require special handling
4. **REGISTER and PUBLISH**: These requests are skipped by the module as they are expected to be handled by local servers

Sources: [src/modules/topos/doc/topos_admin.xml L207-L218](https://github.com/kamailio/kamailio/blob/2b4e9f8b/src/modules/topos/doc/topos_admin.xml#L207-L218)

 [src/modules/topos/tps_msg.c L263-L281](https://github.com/kamailio/kamailio/blob/2b4e9f8b/src/modules/topos/tps_msg.c#L263-L281)

## Example Usage

To enable basic topology hiding in Kamailio:

1. Load the module in the configuration file:

```
loadmodule "topos.so"
```

1. Optional: Configure the storage backend:

```
modparam("topos", "storage", "db")
modparam("topos", "db_url", "mysql://user:password@localhost/kamailio")
```

1. Optional: Enable Call-ID masking (requires topoh module):

```
loadmodule "topoh.so"
modparam("topoh", "use_mode", 1)
modparam("topos", "mask_callid", 1)
```

1. Ensure record-routing is enabled for messages:

```
record_route();
```

The module will automatically process SIP messages to hide topology information.

Sources: [src/modules/topos/doc/topos_admin.xml L115-L118](https://github.com/kamailio/kamailio/blob/2b4e9f8b/src/modules/topos/doc/topos_admin.xml#L115-L118)

 [src/modules/topos/doc/topos_admin.xml L159-L164](https://github.com/kamailio/kamailio/blob/2b4e9f8b/src/modules/topos/doc/topos_admin.xml#L159-L164)