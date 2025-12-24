# Database Schema and Upgrades

> **Relevant source files**
> * [src/db.c](https://github.com/owntone/owntone-server/blob/23c67a3e/src/db.c)
> * [src/db.h](https://github.com/owntone/owntone-server/blob/23c67a3e/src/db.h)
> * [src/db_init.c](https://github.com/owntone/owntone-server/blob/23c67a3e/src/db_init.c)
> * [src/db_init.h](https://github.com/owntone/owntone-server/blob/23c67a3e/src/db_init.h)
> * [src/db_upgrade.c](https://github.com/owntone/owntone-server/blob/23c67a3e/src/db_upgrade.c)
> * [src/httpd_dacp.c](https://github.com/owntone/owntone-server/blob/23c67a3e/src/httpd_dacp.c)
> * [src/mpd.c](https://github.com/owntone/owntone-server/blob/23c67a3e/src/mpd.c)
> * [src/player.c](https://github.com/owntone/owntone-server/blob/23c67a3e/src/player.c)
> * [src/player.h](https://github.com/owntone/owntone-server/blob/23c67a3e/src/player.h)

This document describes the database schema used by OwnTone Server and the mechanisms for upgrading the database schema between versions. It details the structure of the database tables, their relationships, and how schema changes are managed during version upgrades.

## Database Overview

OwnTone uses a SQLite database to store media metadata, playlists, playback state, and other operational data. The database is a critical component that forms the backbone of the system's data persistence layer, linking the media library with playback functionality.

## Database Schema Structure

The database schema consists of several key tables that store different aspects of the server's data.

### Core Tables

Here's a diagram showing the main tables and their relationships:

```css
#mermaid-mv697t709mc{font-family:ui-sans-serif,-apple-system,system-ui,Segoe UI,Helvetica;font-size:16px;fill:#ccc;}@keyframes edge-animation-frame{from{stroke-dashoffset:0;}}@keyframes dash{to{stroke-dashoffset:0;}}#mermaid-mv697t709mc .edge-animation-slow{stroke-dasharray:9,5!important;stroke-dashoffset:900;animation:dash 50s linear infinite;stroke-linecap:round;}#mermaid-mv697t709mc .edge-animation-fast{stroke-dasharray:9,5!important;stroke-dashoffset:900;animation:dash 20s linear infinite;stroke-linecap:round;}#mermaid-mv697t709mc .error-icon{fill:#333;}#mermaid-mv697t709mc .error-text{fill:#cccccc;stroke:#cccccc;}#mermaid-mv697t709mc .edge-thickness-normal{stroke-width:1px;}#mermaid-mv697t709mc .edge-thickness-thick{stroke-width:3.5px;}#mermaid-mv697t709mc .edge-pattern-solid{stroke-dasharray:0;}#mermaid-mv697t709mc .edge-thickness-invisible{stroke-width:0;fill:none;}#mermaid-mv697t709mc .edge-pattern-dashed{stroke-dasharray:3;}#mermaid-mv697t709mc .edge-pattern-dotted{stroke-dasharray:2;}#mermaid-mv697t709mc .marker{fill:#666;stroke:#666;}#mermaid-mv697t709mc .marker.cross{stroke:#666;}#mermaid-mv697t709mc svg{font-family:ui-sans-serif,-apple-system,system-ui,Segoe UI,Helvetica;font-size:16px;}#mermaid-mv697t709mc p{margin:0;}#mermaid-mv697t709mc .entityBox{fill:#111;stroke:#222;}#mermaid-mv697t709mc .relationshipLabelBox{fill:#333;opacity:0.7;background-color:#333;}#mermaid-mv697t709mc .relationshipLabelBox rect{opacity:0.5;}#mermaid-mv697t709mc .labelBkg{background-color:rgba(51, 51, 51, 0.5);}#mermaid-mv697t709mc .edgeLabel .label{fill:#222;font-size:14px;}#mermaid-mv697t709mc .label{font-family:ui-sans-serif,-apple-system,system-ui,Segoe UI,Helvetica;color:#fff;}#mermaid-mv697t709mc .edge-pattern-dashed{stroke-dasharray:8,8;}#mermaid-mv697t709mc .node rect,#mermaid-mv697t709mc .node circle,#mermaid-mv697t709mc .node ellipse,#mermaid-mv697t709mc .node polygon{fill:#111;stroke:#222;stroke-width:1px;}#mermaid-mv697t709mc .relationshipLine{stroke:#666;stroke-width:1;fill:none;}#mermaid-mv697t709mc .marker{fill:none!important;stroke:#666!important;stroke-width:1;}#mermaid-mv697t709mc :root{--mermaid-font-family:"trebuchet ms",verdana,arial,sans-serif;}contained_inhasqueued_ascontainscontainshas_subdirectoryfilesintegeridPRIMARY KEYstringpathstringvirtual_pathstringtitlestringartiststringalbumstringalbum_artistintegerdirectory_idFKintegermedia_kindintegerdata_kindintegertime_modifiedintegerdisabledplaylistitemsintegeridPRIMARY KEYintegerplaylistidFKstringfilepathplaylistsintegeridPRIMARY KEYstringtitleintegertypestringquerystringvirtual_pathintegerdirectory_idFKintegerdisabledqueueintegeridPRIMARY KEYintegerfile_idFKintegerposintegershuffle_posstringpathstringtitlestringartiststringalbumdirectoriesintegeridPRIMARY KEYstringvirtual_pathstringpathintegerparent_idFKintegerdisabledadminstringkeyPRIMARY KEYstringvaluespeakersintegeridPRIMARY KEYintegerselectedintegervolumestringnamegroupsintegeridPRIMARY KEYintegertypestringnameintegerpersistentid
```

Sources: [src/db_init.c L103-L209](https://github.com/owntone/owntone-server/blob/23c67a3e/src/db_init.c#L103-L209)

 [src/db.h L166-L560](https://github.com/owntone/owntone-server/blob/23c67a3e/src/db.h#L166-L560)

### Table Descriptions

#### Admin Table

The `admin` table stores system-wide settings and configuration values including the database schema version.

```
+---------------+--------------+
| Key           | Value        |
+---------------+--------------+
| schema_version_major | 22    |
| schema_version_minor | 2     |
| queue_version | 152          |
| ...           | ...          |
+---------------+--------------+
```

Key admin entries include:

* `schema_version_major` and `schema_version_minor` - Track the database schema version
* `queue_version` - Tracks changes to the playback queue
* `db_update` - Timestamp of the last library update
* `db_modified` - Timestamp of the last database modification

Sources: [src/db_init.c L29-L33](https://github.com/owntone/owntone-server/blob/23c67a3e/src/db_init.c#L29-L33)

 [src/db.h L66-L76](https://github.com/owntone/owntone-server/blob/23c67a3e/src/db.h#L66-L76)

#### Files Table

The `files` table stores metadata for all media files in the library. It contains a comprehensive set of fields for storing media metadata, including file paths, audio properties, and tags.

Key fields include:

* `id` - Unique identifier for the file
* `path` - Filesystem path to the media file
* `virtual_path` - Virtual path within OwnTone's structure
* `directory_id` - References the directory containing the file
* `title`, `artist`, `album`, etc. - Media metadata
* `media_kind` - Type of media (music, movie, podcast, etc.)
* `data_kind` - Source type (file, URL, spotify, pipe)
* `disabled` - Flag indicating if the file is temporarily disabled

Sources: [src/db_init.c L35-L103](https://github.com/owntone/owntone-server/blob/23c67a3e/src/db_init.c#L35-L103)

 [src/db.h L168-L253](https://github.com/owntone/owntone-server/blob/23c67a3e/src/db.h#L168-L253)

#### Playlists Table

The `playlists` table stores information about playlists, including smart playlists.

Key fields include:

* `id` - Unique identifier
* `title` - Playlist name
* `type` - Playlist type (smart, plain, etc.)
* `query` - Query for smart playlists
* `virtual_path` - Virtual path in OwnTone's structure
* `directory_id` - References the containing directory

Sources: [src/db_init.c L105-L124](https://github.com/owntone/owntone-server/blob/23c67a3e/src/db_init.c#L105-L124)

 [src/db.h L271-L291](https://github.com/owntone/owntone-server/blob/23c67a3e/src/db.h#L271-L291)

#### Directories Table

The `directories` table represents the hierarchy of directories in the system.

Key fields include:

* `id` - Unique identifier
* `virtual_path` - Virtual path in OwnTone's structure
* `path` - Filesystem path if applicable
* `parent_id` - Parent directory identifier
* `disabled` - Flag indicating if the directory is disabled

Sources: [src/db_init.c L166-L175](https://github.com/owntone/owntone-server/blob/23c67a3e/src/db_init.c#L166-L175)

 [src/db.h L492-L500](https://github.com/owntone/owntone-server/blob/23c67a3e/src/db.h#L492-L500)

#### Queue Table

The `queue` table stores the playback queue state, including position and shuffle order.

Key fields include:

* `id` - Unique identifier
* `file_id` - References the file being queued
* `pos` - Position in the playback queue
* `shuffle_pos` - Position in the shuffle order
* `title`, `artist`, `album`, etc. - Denormalized metadata for quick access

Sources: [src/db_init.c L177-L209](https://github.com/owntone/owntone-server/blob/23c67a3e/src/db_init.c#L177-L209)

 [src/db.h L509-L563](https://github.com/owntone/owntone-server/blob/23c67a3e/src/db.h#L509-L563)

## Schema Versioning

OwnTone uses a two-part versioning system for its database schema:

```

```

* **Major Version**: Incremented for significant, incompatible schema changes that require migration
* **Minor Version**: Incremented for smaller, backward-compatible changes

The current schema version is stored in `src/db_init.h`:

```
#define SCHEMA_VERSION_MAJOR 22
#define SCHEMA_VERSION_MINOR 2
```

These values are stored in the `admin` table with keys `schema_version_major` and `schema_version_minor`.

Sources: [src/db_init.h L28-L29](https://github.com/owntone/owntone-server/blob/23c67a3e/src/db_init.h#L28-L29)

 [src/db_init.c L258-L261](https://github.com/owntone/owntone-server/blob/23c67a3e/src/db_init.c#L258-L261)

## Database Upgrade Process

When OwnTone starts, it checks the schema version in the database against the expected version. If an upgrade is needed, the upgrade process is initiated.

```

```

The upgrade is performed in a transaction to ensure database consistency. If any part of the upgrade fails, the entire transaction is rolled back.

Sources: [src/db_upgrade.c L116-L137](https://github.com/owntone/owntone-server/blob/23c67a3e/src/db_upgrade.c#L116-L137)

 [src/db.c L4254-L4290](https://github.com/owntone/owntone-server/blob/23c67a3e/src/db.c#L4254-L4290)

### Table Upgrade Mechanism

Altering tables in SQLite is complex because it has limited `ALTER TABLE` support. OwnTone implements the 12-step process recommended by SQLite for altering tables:

```

```

The implementation is in `db_table_upgrade()` function which:

1. Creates a new table with the desired schema
2. Transfers data from the old table
3. Drops the old table
4. Renames the new table to the original name

Sources: [src/db_upgrade.c L171-L263](https://github.com/owntone/owntone-server/blob/23c67a3e/src/db_upgrade.c#L171-L263)

### Upgrade Queries

For each version upgrade, there is a set of SQL queries to be executed. These queries are defined in arrays like `db_upgrade_v18_queries`, `db_upgrade_v1801_queries`, etc.

Example upgrade from 18.00 to 18.01:

```javascript
static const struct db_upgrade_query db_upgrade_v1801_queries[] = {
  { U_V1801_UPDATE_PLAYLISTS_M3U, "update table playlists" },
  { U_V1801_UPDATE_PLAYLISTS_PLS, "update table playlists" },
  { U_V1801_UPDATE_PLAYLISTS_SMARTPL, "update table playlists" },
  { U_V1801_SCVER_MAJOR, "set schema_version_major to 18" },
  { U_V1801_SCVER_MINOR, "set schema_version_minor to 01" },
};
```

Sources: [src/db_upgrade.c L320-L328](https://github.com/owntone/owntone-server/blob/23c67a3e/src/db_upgrade.c#L320-L328)

## Index Management

Indices are crucial for database performance. OwnTone maintains a set of indices on various tables to optimize common queries.

Key indices include:

* `idx_rescan` - Used during library rescan
* `idx_album`, `idx_albumartist`, etc. - Optimize browsing and grouping
* `idx_file_dir` - Links files to directories
* `idx_queue_pos`, `idx_queue_shufflepos` - Optimize queue operations

All indices are defined in `db_init.c` and are prefixed with `idx_` for identification during maintenance.

Sources: [src/db_init.c L299-L380](https://github.com/owntone/owntone-server/blob/23c67a3e/src/db_init.c#L299-L380)

## Triggers

OwnTone uses SQLite triggers to maintain integrity constraints and derived data.

For example, the `trg_groups_insert` and `trg_groups_update` triggers maintain the `groups` table automatically when files are added or updated:

```sql
CREATE TRIGGER trg_groups_insert AFTER INSERT ON files FOR EACH ROW
BEGIN
  INSERT OR IGNORE INTO groups (type, name, persistentid) VALUES (1, NEW.album, NEW.songalbumid);
  INSERT OR IGNORE INTO groups (type, name, persistentid) VALUES (2, NEW.album_artist, NEW.songartistid);
END;
```

Sources: [src/db_init.c L420-L432](https://github.com/owntone/owntone-server/blob/23c67a3e/src/db_init.c#L420-L432)

## Database Upgrade History

The database schema has evolved over time. Each upgrade is documented in `db_upgrade.c` with specific upgrade steps. Notable upgrades include:

* **17.00 → 18.00**: Changed playlist type enumeration and recreated filelist view
* **18.00 → 18.01**: Changed virtual_path for playlists to remove file extensions
* **18.01 → 19.00**: Replaced 'filelist' view with new 'directories' table
* **19.00 → 19.01**: Added persistent playqueue table
* **Various up to 22.02**: Added support for additional features and optimizations

Sources: [src/db_upgrade.c L266-L292](https://github.com/owntone/owntone-server/blob/23c67a3e/src/db_upgrade.c#L266-L292)

 [src/db_upgrade.c L305-L328](https://github.com/owntone/owntone-server/blob/23c67a3e/src/db_upgrade.c#L305-L328)

 [src/db_upgrade.c L330-L386](https://github.com/owntone/owntone-server/blob/23c67a3e/src/db_upgrade.c#L330-L386)

## Best Practices

When making changes to the database schema:

1. Always increment the schema version in `db_init.h`
2. Create appropriate upgrade queries in `db_upgrade.c`
3. Follow the 12-step SQLite table alteration process for complex changes
4. Create appropriate indices for new query patterns
5. Use transactions to ensure consistency during upgrades

## Related Topics

For information about how database fields are used in the media library, see [Media File Information and Metadata](/owntone/owntone-server/2.1-media-file-information-and-metadata).

For details on playlist and queue management, see [Playlists and Queue Management](/owntone/owntone-server/2.2-playlists-and-queue-management).