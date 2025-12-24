# Hash Table Module

> **Relevant source files**
> * [src/modules/htable/Makefile](https://github.com/kamailio/kamailio/blob/2b4e9f8b/src/modules/htable/Makefile)
> * [src/modules/htable/api.c](https://github.com/kamailio/kamailio/blob/2b4e9f8b/src/modules/htable/api.c)
> * [src/modules/htable/api.h](https://github.com/kamailio/kamailio/blob/2b4e9f8b/src/modules/htable/api.h)
> * [src/modules/htable/doc/htable.xml](https://github.com/kamailio/kamailio/blob/2b4e9f8b/src/modules/htable/doc/htable.xml)
> * [src/modules/htable/doc/htable_admin.xml](https://github.com/kamailio/kamailio/blob/2b4e9f8b/src/modules/htable/doc/htable_admin.xml)
> * [src/modules/htable/ht_api.c](https://github.com/kamailio/kamailio/blob/2b4e9f8b/src/modules/htable/ht_api.c)
> * [src/modules/htable/ht_api.h](https://github.com/kamailio/kamailio/blob/2b4e9f8b/src/modules/htable/ht_api.h)
> * [src/modules/htable/ht_db.c](https://github.com/kamailio/kamailio/blob/2b4e9f8b/src/modules/htable/ht_db.c)
> * [src/modules/htable/ht_db.h](https://github.com/kamailio/kamailio/blob/2b4e9f8b/src/modules/htable/ht_db.h)
> * [src/modules/htable/ht_dmq.c](https://github.com/kamailio/kamailio/blob/2b4e9f8b/src/modules/htable/ht_dmq.c)
> * [src/modules/htable/ht_dmq.h](https://github.com/kamailio/kamailio/blob/2b4e9f8b/src/modules/htable/ht_dmq.h)
> * [src/modules/htable/ht_var.c](https://github.com/kamailio/kamailio/blob/2b4e9f8b/src/modules/htable/ht_var.c)
> * [src/modules/htable/ht_var.h](https://github.com/kamailio/kamailio/blob/2b4e9f8b/src/modules/htable/ht_var.h)
> * [src/modules/htable/htable.c](https://github.com/kamailio/kamailio/blob/2b4e9f8b/src/modules/htable/htable.c)
> * [src/modules/ratelimit/doc/ratelimit.xml](https://github.com/kamailio/kamailio/blob/2b4e9f8b/src/modules/ratelimit/doc/ratelimit.xml)
> * [src/modules/ratelimit/doc/ratelimit_admin.xml](https://github.com/kamailio/kamailio/blob/2b4e9f8b/src/modules/ratelimit/doc/ratelimit_admin.xml)

The Hash Table Module provides an in-memory key-value storage system for Kamailio. It allows defining multiple hash tables that can be accessed via pseudo-variables in the configuration script. The module supports features such as automated expiration of entries, database persistence, and distributed replication via the DMQ module.

## 1. Module Architecture

The hash table module is designed to provide efficient in-memory storage with various access methods and optional persistence capabilities.

```mermaid
flowchart TD

CONF["Config Script"]
HTAPI["Hash Table API<br>ht_api.c/h"]
HTVAR["PV Interface<br>ht_var.c/h"]
HTDB["Database Interface<br>ht_db.c/h"]
HTDMQ["DMQ Interface<br>ht_dmq.c/h"]
HTMAIN["Module Core<br>htable.c"]
HTEXAPI["External API<br>api.c/h"]
DMQ["DMQ Module"]
DB["Database"]
OTHMOD["Other Modules"]

CONF --> HTVAR
CONF --> HTMAIN
OTHMOD --> HTEXAPI
HTDMQ --> DMQ
HTDB --> DB

subgraph subGraph2 ["External Components"]
    DMQ
    DB
    OTHMOD
end

subgraph subGraph1 ["Hash Table Module"]
    HTAPI
    HTVAR
    HTDB
    HTDMQ
    HTMAIN
    HTEXAPI
    HTVAR --> HTAPI
    HTMAIN --> HTAPI
    HTDB --> HTAPI
    HTDMQ --> HTAPI
    HTAPI --> HTDMQ
    HTEXAPI --> HTAPI
end

subgraph subGraph0 ["Kamailio Configuration"]
    CONF
end
```

Sources: [src/modules/htable/htable.c L43-L48](https://github.com/kamailio/kamailio/blob/2b4e9f8b/src/modules/htable/htable.c#L43-L48)

 [src/modules/htable/htable.c L192-L203](https://github.com/kamailio/kamailio/blob/2b4e9f8b/src/modules/htable/htable.c#L192-L203)

 [src/modules/htable/ht_api.h L21-L161](https://github.com/kamailio/kamailio/blob/2b4e9f8b/src/modules/htable/ht_api.h#L21-L161)

## 2. Hash Table Data Structures

The hash table implementation uses a multi-level structure with hash tables containing slots (entries) which contain linked lists of cells.

```mermaid
flowchart TD

HT["Hash Table (ht_t)"]
SLOT1["Slot 1 (ht_entry_t)"]
SLOT2["Slot 2 (ht_entry_t)"]
SLOT3["Slot 3 (ht_entry_t)"]
SLOTN["Slot N (ht_entry_t)"]
CELL1["Cell 1 (ht_cell_t)<br>name: key1<br>value: val1<br>expire: timestamp"]
CELL2["Cell 2 (ht_cell_t)<br>name: key2<br>value: val2<br>expire: timestamp"]
CELL3["Cell 3 (ht_cell_t)<br>name: key3<br>value: val3<br>expire: timestamp"]
CELLN["Cell N (ht_cell_t)<br>name: keyN<br>value: valN<br>expire: timestamp"]

subgraph subGraph0 ["Hash Table Structure (in Memory)"]
    HT
    SLOT1
    SLOT2
    SLOT3
    SLOTN
    CELL1
    CELL2
    CELL3
    CELLN
    HT --> SLOT1
    HT --> SLOT2
    HT --> SLOT3
    HT --> SLOTN
    SLOT1 --> CELL1
    SLOT1 --> CELL2
    SLOT2 --> CELL3
    SLOTN --> CELLN
end
```

Sources: [src/modules/htable/ht_api.h L35-L80](https://github.com/kamailio/kamailio/blob/2b4e9f8b/src/modules/htable/ht_api.h#L35-L80)

 [src/modules/htable/ht_api.c L175-L208](https://github.com/kamailio/kamailio/blob/2b4e9f8b/src/modules/htable/ht_api.c#L175-L208)

## 3. Module Configuration

### 3.1 Hash Table Definition

The main parameter for the module is `htable` which defines the hash tables to be created. Multiple hash tables can be defined by setting this parameter multiple times.

```javascript
modparam("htable", "htable", "name=>size=8;autoexpire=3600;dbtable=htable_name")
```

Key parameters for htable definition:

* `size`: Number of slots in the hash table (2^size)
* `autoexpire`: Time in seconds after which entries expire
* `dbtable`: Database table to load/store data
* `dbmode`: Whether to write back to database on server stop
* `initval`: Default integer value for non-existent keys
* `dmqreplicate`: Whether to replicate changes via DMQ

Sources: [src/modules/htable/htable_admin.xml L317-L468](https://github.com/kamailio/kamailio/blob/2b4e9f8b/src/modules/htable/htable_admin.xml#L317-L468)

 [src/modules/htable/htable.c L170-L187](https://github.com/kamailio/kamailio/blob/2b4e9f8b/src/modules/htable/htable.c#L170-L187)

### 3.2 Database Configuration

To enable database persistence, configure the database connection:

```
modparam("htable", "db_url", "mysql://username:password@localhost/kamailio")
modparam("htable", "key_name_column", "key_name")
modparam("htable", "key_type_column", "key_type")
modparam("htable", "value_type_column", "value_type")
modparam("htable", "key_value_column", "key_value")
modparam("htable", "expires_column", "expires")
```

Sources: [src/modules/htable/htable_admin.xml L470-L584](https://github.com/kamailio/kamailio/blob/2b4e9f8b/src/modules/htable/htable_admin.xml#L470-L584)

 [src/modules/htable/ht_db.c L30-L44](https://github.com/kamailio/kamailio/blob/2b4e9f8b/src/modules/htable/ht_db.c#L30-L44)

### 3.3 DMQ Replication

To enable replication between multiple servers:

```
modparam("htable", "enable_dmq", 1)
modparam("htable", "dmq_init_sync", 1)
```

Note: The DMQ module must be loaded before the htable module when DMQ replication is enabled.

Sources: [src/modules/htable/htable_admin.xml L671-L723](https://github.com/kamailio/kamailio/blob/2b4e9f8b/src/modules/htable/htable_admin.xml#L671-L723)

 [src/modules/htable/htable.c L186](https://github.com/kamailio/kamailio/blob/2b4e9f8b/src/modules/htable/htable.c#L186-L186)

 [src/modules/htable/ht_dmq.c L208-L237](https://github.com/kamailio/kamailio/blob/2b4e9f8b/src/modules/htable/ht_dmq.c#L208-L237)

## 4. Accessing Hash Tables

### 4.1 Pseudo-Variables

The module provides several pseudo-variables for accessing and manipulating hash table data:

| Pseudo-Variable | Description |
| --- | --- |
| `$sht(htname=>key)` | Access or modify value in hash table |
| `$shtex(htname=>key)` | Access or modify expiration time |
| `$shtcn(htname=>re)` | Count cells with name matching regex |
| `$shtcv(htname=>re)` | Count cells with value matching regex |
| `$shtinc(htname=>key)` | Increment integer value and return result |
| `$shtdec(htname=>key)` | Decrement integer value and return result |
| `$shtitkey(iname)` | Get current key from iterator |
| `$shtitval(iname)` | Get current value from iterator |

Example:

```javascript
$sht(users=>alice) = "active";
if($sht(users=>alice) == "active") {
    # Do something with active user
}
```

Sources: [src/modules/htable/htable.c L100-L119](https://github.com/kamailio/kamailio/blob/2b4e9f8b/src/modules/htable/htable.c#L100-L119)

 [src/modules/htable/ht_var.c L30-L129](https://github.com/kamailio/kamailio/blob/2b4e9f8b/src/modules/htable/ht_var.c#L30-L129)

### 4.2 Key-Value Operations Flow

```mermaid
sequenceDiagram
  participant Kamailio Script
  participant PV System
  participant Hash Table API
  participant Hash Table
  participant DMQ System

  Kamailio Script->>PV System: $sht(table=>key) = value
  PV System->>Hash Table API: pv_set_ht_cell()
  Hash Table API->>Hash Table: ht_set_cell()
  Hash Table API->>DMQ System: ht_dmq_replicate_action()
  DMQ System-->>Hash Table API: Acknowledgment
  Hash Table API-->>PV System: Operation result
  PV System-->>Kamailio Script: Return value/status
  Kamailio Script->>PV System: val = $sht(table=>key)
  PV System->>Hash Table API: pv_get_ht_cell()
  Hash Table API->>Hash Table: ht_cell_pkg_copy()
  Hash Table-->>Hash Table API: Cell value
  Hash Table API-->>PV System: Value/status
  PV System-->>Kamailio Script: Return value/status
```

Sources: [src/modules/htable/ht_var.c L30-L129](https://github.com/kamailio/kamailio/blob/2b4e9f8b/src/modules/htable/ht_var.c#L30-L129)

 [src/modules/htable/ht_api.c L614-L617](https://github.com/kamailio/kamailio/blob/2b4e9f8b/src/modules/htable/ht_api.c#L614-L617)

## 5. API Functions

The module exports several functions for use in the Kamailio configuration:

| Function | Description |
| --- | --- |
| `sht_print()` | Print hash table content (debug) |
| `sht_rm(htname, key)` | Remove entry from hash table |
| `sht_rm_name_re(htable=>regexp)` | Remove entries with name matching regex |
| `sht_rm_value_re(htable=>regexp)` | Remove entries with value matching regex |
| `sht_lock(htable=>key)` | Lock hash table slot for key |
| `sht_unlock(htable=>key)` | Unlock hash table slot for key |
| `sht_reset(htname)` | Remove all entries from hash table |
| `sht_iterator_start(iname, htname)` | Start iterator for hash table |
| `sht_iterator_next(iname)` | Move iterator to next item |
| `sht_iterator_end(iname)` | End iterator |

Example:

```javascript
sht_lock("users=>alice");
$sht(users=>alice) = $sht(users=>alice) + 10;
sht_unlock("users=>alice");
```

Sources: [src/modules/htable/htable.c L123-L167](https://github.com/kamailio/kamailio/blob/2b4e9f8b/src/modules/htable/htable.c#L123-L167)

 [src/modules/htable/htable_admin.xml L806-L1437](https://github.com/kamailio/kamailio/blob/2b4e9f8b/src/modules/htable/htable_admin.xml#L806-L1437)

## 6. Expiration Mechanism

The hash table module supports automatic expiration of entries. When a cell is added to a hash table with `autoexpire` set, it receives an expiration timestamp. A timer periodically checks for and removes expired entries.

```mermaid
flowchart TD

A["Server Start"]
B["Initialize Timer"]
C["Wait for timer_interval"]
D["Scan all hash tables"]
E["Check each entry for expiration"]
F["Is entry expired?"]
G["Call event route if configured"]
I["Continue to next entry"]
H["Remove expired entry"]
J["More entries?"]
K["More hash tables?"]

A --> B
B --> C
C --> D
D --> E
E --> F
F --> G
F --> I
G --> H
H --> I
I --> J
J --> E
J --> K
K --> D
K --> C
```

A special event route can be triggered when entries expire:

```
event_route[htable:expired:users] {
    xlog("L_INFO", "Key $shtrecord(key) with value $shtrecord(value) expired\n");
}
```

Sources: [src/modules/htable/htable.c L231-L243](https://github.com/kamailio/kamailio/blob/2b4e9f8b/src/modules/htable/htable.c#L231-L243)

 [src/modules/htable/htable.c L358-L371](https://github.com/kamailio/kamailio/blob/2b4e9f8b/src/modules/htable/htable.c#L358-L371)

 [src/modules/htable/ht_api.c L110-L141](https://github.com/kamailio/kamailio/blob/2b4e9f8b/src/modules/htable/ht_api.c#L110-L141)

## 7. Database Integration

The hash table module can load values from and store values to a database table. This provides persistence across restarts.

```mermaid
sequenceDiagram
  participant Kamailio
  participant Hash Table Module
  participant Database

  Kamailio->>Hash Table Module: mod_init()
  Hash Table Module->>Database: ht_db_open_con()
  Hash Table Module->>Database: ht_db_load_tables()
  Database-->>Hash Table Module: Table Data
  Hash Table Module-->>Kamailio: Tables initialized
  note over Kamailio,Hash Table Module: During operation
  Kamailio->>Hash Table Module: destroy()
  Hash Table Module->>Database: ht_db_open_con()
  Hash Table Module->>Database: ht_db_sync_tables()
  Database-->>Hash Table Module: Sync confirmed
  Hash Table Module-->>Kamailio: Tables synchronized
```

The database table should have the following structure:

* `key_name`: String containing the name of the key
* `key_type`: Type of key (0=simple key, 1=array key)
* `value_type`: Type of value (0=string, 1=integer)
* `key_value`: String containing the value
* `expires`: Expiration time (optional)

Sources: [src/modules/htable/ht_db.c L190-L542](https://github.com/kamailio/kamailio/blob/2b4e9f8b/src/modules/htable/ht_db.c#L190-L542)

 [src/modules/htable/htable.c L215-L230](https://github.com/kamailio/kamailio/blob/2b4e9f8b/src/modules/htable/htable.c#L215-L230)

 [src/modules/htable/htable.c L336-L346](https://github.com/kamailio/kamailio/blob/2b4e9f8b/src/modules/htable/htable.c#L336-L346)

## 8. DMQ Replication

When DMQ replication is enabled, changes to a hash table with `dmqreplicate=1` will be propagated to other Kamailio instances in the cluster.

```mermaid
sequenceDiagram
  participant Kamailio Instance 1
  participant DMQ Module (1)
  participant DMQ Module (2)
  participant Kamailio Instance 2

  Kamailio Instance 1->>DMQ Module (1): ht_dmq_replicate_action()
  DMQ Module (1)->>DMQ Module (2): Send via DMQ channel
  DMQ Module (2)->>Kamailio Instance 2: ht_dmq_handle_msg()
  Kamailio Instance 2->>Kamailio Instance 2: ht_dmq_replay_action()
  Kamailio Instance 2-->>DMQ Module (2): Acknowledge
  DMQ Module (2)-->>DMQ Module (1): Forward acknowledgment
  DMQ Module (1)-->>Kamailio Instance 1: Operation complete
```

Sources: [src/modules/htable/ht_dmq.c L260-L264](https://github.com/kamailio/kamailio/blob/2b4e9f8b/src/modules/htable/ht_dmq.c#L260-L264)

 [src/modules/htable/ht_dmq.c L367-L416](https://github.com/kamailio/kamailio/blob/2b4e9f8b/src/modules/htable/ht_dmq.c#L367-L416)

 [src/modules/htable/ht_dmq.c L431-L458](https://github.com/kamailio/kamailio/blob/2b4e9f8b/src/modules/htable/ht_dmq.c#L431-L458)

## 9. Iterator Functionality

The module provides iterator functionality to traverse hash table entries sequentially:

```css
# Start iteration over "users" hash table with iterator named "it1"
sht_iterator_start("it1", "users");

# Loop while we have more items
while(sht_iterator_next("it1")) {
    xlog("L_INFO", "Key: $shtitkey(it1) Value: $shtitval(it1)\n");
    
    # Modify current item
    sht_iterator_sets("it1", "modified");
}

# End the iterator
sht_iterator_end("it1");
```

Sources: [src/modules/htable/htable.c L147-L159](https://github.com/kamailio/kamailio/blob/2b4e9f8b/src/modules/htable/htable.c#L147-L159)

 [src/modules/htable/htable_admin.xml L1439-L1713](https://github.com/kamailio/kamailio/blob/2b4e9f8b/src/modules/htable/htable_admin.xml#L1439-L1713)

## 10. Array Management

The hash table module supports array-like structures, where keys can be identified as `name[0]`, `name[1]`, etc., with a special entry `name::size` storing the array size.

```typescript
# Example with automatic array loading from database
# Database contains multiple rows with the same key_name
# and key_type = 1 (array)

# Access an array element
$var(value) = $sht(phonebook=>number[0]);

# Get array size
$var(size) = $sht(phonebook=>number::size);

# Loop through array
$var(i) = 0;
while($var(i) < $sht(phonebook=>number::size)) {
    xlog("L_INFO", "Number[$var(i)]: $sht(phonebook=>number[$var(i)])\n");
    $var(i) = $var(i) + 1;
}
```

Sources: [src/modules/htable/htable_admin.xml L130-L218](https://github.com/kamailio/kamailio/blob/2b4e9f8b/src/modules/htable/htable_admin.xml#L130-L218)

 [src/modules/htable/ht_db.c L124-L141](https://github.com/kamailio/kamailio/blob/2b4e9f8b/src/modules/htable/ht_db.c#L124-L141)

## 11. Performance Considerations

* **Hash Table Size**: Larger hash tables use more memory but reduce collisions and improve lookup performance
* **Expiration**: Setting a reasonable expiration time prevents memory leaks and excessive memory usage
* **Timer Interval**: The `timer_interval` parameter affects how frequently expired entries are checked
* **Timer Processes**: For heavily used hash tables, dedicated timer processes (`timer_procs`) can improve performance

Sources: [src/modules/htable/htable_admin.xml L624-L646](https://github.com/kamailio/kamailio/blob/2b4e9f8b/src/modules/htable/htable_admin.xml#L624-L646)

 [src/modules/htable/htable_admin.xml L725-L746](https://github.com/kamailio/kamailio/blob/2b4e9f8b/src/modules/htable/htable_admin.xml#L725-L746)

## 12. Example Use Cases

### Blocking Repeated Authentication Failures

```javascript
# Count failed authentications by username
if (auth_check_failed()) {
    if($sht(auth_failures=>$au) == $null) $sht(auth_failures=>$au) = 0;
    $sht(auth_failures=>$au) = $sht(auth_failures=>$au) + 1;
    $shtex(auth_failures=>$au) = 3600; # Expires in 1 hour
    
    if($sht(auth_failures=>$au) >= 3) {
        # Blocked for too many failures
        sl_send_reply("403", "Temporarily blocked");
        exit;
    }
}
```

### Rate Limiting

```javascript
# Simple rate limiting for REGISTER requests per IP
if (is_method("REGISTER")) {
    $var(ip) = $si;
    $var(count) = $shtinc(regcounts=>$var(ip));
    
    if($var(count) == 1) {
        # First request, set expiration to 1 minute
        $shtex(regcounts=>$var(ip)) = 60;
    }
    
    if($var(count) > 10) {
        # More than 10 REGISTERs from this IP in 1 minute
        sl_send_reply("503", "Too Many Requests");
        exit;
    }
}
```

Sources: [src/modules/htable/htable_admin.xml L57-L133](https://github.com/kamailio/kamailio/blob/2b4e9f8b/src/modules/htable/htable_admin.xml#L57-L133)

 [src/modules/ratelimit/doc/ratelimit_admin.xml L47-L57](https://github.com/kamailio/kamailio/blob/2b4e9f8b/src/modules/ratelimit/doc/ratelimit_admin.xml#L47-L57)