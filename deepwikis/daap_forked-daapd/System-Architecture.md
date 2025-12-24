# System Architecture

> **Relevant source files**
> * [configure.ac](https://github.com/owntone/owntone-server/blob/23c67a3e/configure.ac)
> * [htdocs/assets/index.css](https://github.com/owntone/owntone-server/blob/23c67a3e/htdocs/assets/index.css)
> * [htdocs/assets/index.js](https://github.com/owntone/owntone-server/blob/23c67a3e/htdocs/assets/index.js)
> * [htdocs/index.html](https://github.com/owntone/owntone-server/blob/23c67a3e/htdocs/index.html)
> * [src/Makefile.am](https://github.com/owntone/owntone-server/blob/23c67a3e/src/Makefile.am)
> * [src/db.c](https://github.com/owntone/owntone-server/blob/23c67a3e/src/db.c)
> * [src/db.h](https://github.com/owntone/owntone-server/blob/23c67a3e/src/db.h)
> * [src/httpd.c](https://github.com/owntone/owntone-server/blob/23c67a3e/src/httpd.c)
> * [src/httpd.h](https://github.com/owntone/owntone-server/blob/23c67a3e/src/httpd.h)
> * [src/httpd_artworkapi.c](https://github.com/owntone/owntone-server/blob/23c67a3e/src/httpd_artworkapi.c)
> * [src/httpd_daap.c](https://github.com/owntone/owntone-server/blob/23c67a3e/src/httpd_daap.c)
> * [src/httpd_daap.h](https://github.com/owntone/owntone-server/blob/23c67a3e/src/httpd_daap.h)
> * [src/httpd_dacp.c](https://github.com/owntone/owntone-server/blob/23c67a3e/src/httpd_dacp.c)
> * [src/httpd_internal.h](https://github.com/owntone/owntone-server/blob/23c67a3e/src/httpd_internal.h)
> * [src/httpd_oauth.c](https://github.com/owntone/owntone-server/blob/23c67a3e/src/httpd_oauth.c)
> * [src/httpd_rsp.c](https://github.com/owntone/owntone-server/blob/23c67a3e/src/httpd_rsp.c)
> * [src/main.c](https://github.com/owntone/owntone-server/blob/23c67a3e/src/main.c)
> * [src/mpd.c](https://github.com/owntone/owntone-server/blob/23c67a3e/src/mpd.c)
> * [src/outputs.c](https://github.com/owntone/owntone-server/blob/23c67a3e/src/outputs.c)
> * [src/outputs.h](https://github.com/owntone/owntone-server/blob/23c67a3e/src/outputs.h)
> * [src/outputs/airplay.c](https://github.com/owntone/owntone-server/blob/23c67a3e/src/outputs/airplay.c)
> * [src/outputs/alsa.c](https://github.com/owntone/owntone-server/blob/23c67a3e/src/outputs/alsa.c)
> * [src/outputs/cast.c](https://github.com/owntone/owntone-server/blob/23c67a3e/src/outputs/cast.c)
> * [src/outputs/dummy.c](https://github.com/owntone/owntone-server/blob/23c67a3e/src/outputs/dummy.c)
> * [src/outputs/fifo.c](https://github.com/owntone/owntone-server/blob/23c67a3e/src/outputs/fifo.c)
> * [src/outputs/pulse.c](https://github.com/owntone/owntone-server/blob/23c67a3e/src/outputs/pulse.c)
> * [src/outputs/raop.c](https://github.com/owntone/owntone-server/blob/23c67a3e/src/outputs/raop.c)
> * [src/player.c](https://github.com/owntone/owntone-server/blob/23c67a3e/src/player.c)
> * [src/player.h](https://github.com/owntone/owntone-server/blob/23c67a3e/src/player.h)
> * [web-src/package-lock.json](https://github.com/owntone/owntone-server/blob/23c67a3e/web-src/package-lock.json)
> * [web-src/package.json](https://github.com/owntone/owntone-server/blob/23c67a3e/web-src/package.json)
> * [web-src/src/main.js](https://github.com/owntone/owntone-server/blob/23c67a3e/web-src/src/main.js)
> * [web-src/src/mystyles.scss](https://github.com/owntone/owntone-server/blob/23c67a3e/web-src/src/mystyles.scss)
> * [web-src/src/templates/ContentWithHero.vue](https://github.com/owntone/owntone-server/blob/23c67a3e/web-src/src/templates/ContentWithHero.vue)

This document provides a comprehensive overview of the OwnTone server architecture, explaining how the major components interact to form a complete media server system. It covers the core architecture, components, and data flows that make up the system.

For information about installation and configuration, see [Installation and Configuration](/owntone/owntone-server/1.2-installation-and-configuration).

## Overview

OwnTone is a media server designed to stream audio from various sources to multiple output devices. It implements several network protocols like DAAP (Digital Audio Access Protocol) for iTunes compatibility, DACP (Digital Audio Control Protocol) for remote control, and MPD (Music Player Daemon) protocol, while also providing a modern web interface and JSON API.

The server follows an event-driven architecture built around the libevent library, with a multi-threaded design that ensures responsive operation even under heavy load.

```mermaid
flowchart TD

iTunes["iTunes/Apple Music"]
RemoteApp["Remote Apps"]
MPDClients["MPD Clients"]
WebBrowser["Web Browser"]
Server["Main Server Process"]
EventLoop["Event Loop<br>(libevent)"]
ThreadPool["Worker Thread Pool"]
Player["Player<br>(playback control)"]
DB["Database<br>(SQLite)"]
Library["Library Scanner"]
DAAP["DAAP<br>(iTunes protocol)"]
DACP["DACP<br>(Remote control)"]
MPD["MPD<br>(Music Player Daemon)"]
HTTP["HTTP Server<br>(Web UI + JSON API)"]
MDNS["mDNS<br>(Service Discovery)"]
Inputs["Input Sources<br>(Files, HTTP, Spotify)"]
Transcode["Transcoding<br>(Format conversion)"]
Outputs["Output Devices"]
AirPlay["AirPlay Devices"]
Chromecast["Chromecast Devices"]
LocalAudio["Local Audio<br>(ALSA/Pulse)"]
RemoteStream["HTTP Stream Clients"]

iTunes --> DAAP
RemoteApp --> DACP
MPDClients --> MPD
WebBrowser --> HTTP
Outputs --> AirPlay
Outputs --> Chromecast
Outputs --> LocalAudio
Outputs --> RemoteStream

subgraph subGraph5 ["Output Destinations"]
    AirPlay
    Chromecast
    LocalAudio
    RemoteStream
end

subgraph subGraph4 ["OwnTone Server"]
    Server
    Server --> EventLoop
    Server --> ThreadPool
    DAAP --> Player
    DACP --> Player
    MPD --> Player
    HTTP --> Player
    Player --> Inputs
    Player --> Transcode
    Player --> Outputs

subgraph subGraph3 ["Media Handling"]
    Inputs
    Transcode
    Outputs
end

subgraph subGraph2 ["Network Protocols"]
    DAAP
    DACP
    MPD
    HTTP
    MDNS
    MDNS --> DAAP
    MDNS --> DACP
end

subgraph subGraph1 ["Core Components"]
    EventLoop
    ThreadPool
    Player
    DB
    Library
    Player --> DB
    Library --> DB
end
end

subgraph subGraph0 ["Client Applications"]
    iTunes
    RemoteApp
    MPDClients
    WebBrowser
end
```

Sources: [src/main.c L482-L741](https://github.com/owntone/owntone-server/blob/23c67a3e/src/main.c#L482-L741)

 [src/player.c L17-L45](https://github.com/owntone/owntone-server/blob/23c67a3e/src/player.c#L17-L45)

 [src/httpd.c L18-L76](https://github.com/owntone/owntone-server/blob/23c67a3e/src/httpd.c#L18-L76)

## Core Components

### Event-Driven Architecture

OwnTone uses libevent as its core event handling system, which allows it to efficiently handle multiple concurrent operations without blocking. The main event loop processes events for timer callbacks, network I/O, and inter-thread communication.

```mermaid
flowchart TD

evbase_player["evbase_player<br>(Player Event Base)"]
pb_timer_ev["Playback Timer Event"]
evbase_main["evbase_main<br>(Main Event Base)"]
sig_event["Signal Event Handler"]
httpd_threadpool["HTTP Thread Pool"]
Worker["Worker Thread Pool"]

evbase_main --> Worker
httpd_threadpool --> Worker

subgraph subGraph2 ["HTTP Thread"]
    httpd_threadpool
end

subgraph subGraph0 ["Main Thread"]
    evbase_main
    sig_event
    evbase_main --> sig_event
end

subgraph subGraph1 ["Player Thread"]
    evbase_player
    pb_timer_ev
    evbase_player --> pb_timer_ev
end
```

Sources: [src/main.c L81](https://github.com/owntone/owntone-server/blob/23c67a3e/src/main.c#L81-L81)

 [src/main.c L299-L301](https://github.com/owntone/owntone-server/blob/23c67a3e/src/main.c#L299-L301)

 [src/player.c L299-L300](https://github.com/owntone/owntone-server/blob/23c67a3e/src/player.c#L299-L300)

### Threading Model

OwnTone uses several threads to handle different aspects of the system:

1. **Main Thread**: Handles the main event loop and coordinates system operations
2. **Player Thread**: Manages audio playback and streaming
3. **HTTP Thread**: Handles incoming HTTP requests
4. **Worker Threads**: Execute potentially blocking operations (like database queries)

The worker thread pool is used extensively to ensure that the main thread and player thread remain responsive, even when performing operations that might block. For example, database operations are typically dispatched to worker threads.

Sources: [src/player.c L302-L304](https://github.com/owntone/owntone-server/blob/23c67a3e/src/player.c#L302-L304)

 [src/httpd.c L146-L147](https://github.com/owntone/owntone-server/blob/23c67a3e/src/httpd.c#L146-L147)

### Command System

The command system allows different components to schedule and execute operations, potentially in different threads. This is used for both the player and HTTP modules to ensure that slow operations don't block the event loop.

```mermaid
sequenceDiagram
  participant Client (e.g., Remote App)
  participant HTTP Server
  participant Worker Thread
  participant Player
  participant Output System

  Client (e.g., Remote App)->>HTTP Server: Send play command
  HTTP Server->>Worker Thread: Schedule play operation
  Worker Thread->>Player: Execute player_playback_start()
  Player->>Player: Update state
  Player->>Output System: Start audio output
  Player-->>HTTP Server: Command completed
  HTTP Server-->>Client (e.g., Remote App): Success response
```

Sources: [src/player.c L107-L116](https://github.com/owntone/owntone-server/blob/23c67a3e/src/player.c#L107-L116)

 [src/commands.c](https://github.com/owntone/owntone-server/blob/23c67a3e/src/commands.c)

## Database System

OwnTone uses SQLite as its core database engine for storing and retrieving metadata about media files, playlists, and the playback queue.

### Database Schema

The database includes tables for:

* Media files (tracks, albums, artists)
* Playlists and playlist items
* Playback queue
* Pairing information (for remote control)
* Speaker (output device) settings

```css
#mermaid-o8hds8z47xb{font-family:ui-sans-serif,-apple-system,system-ui,Segoe UI,Helvetica;font-size:16px;fill:#ccc;}@keyframes edge-animation-frame{from{stroke-dashoffset:0;}}@keyframes dash{to{stroke-dashoffset:0;}}#mermaid-o8hds8z47xb .edge-animation-slow{stroke-dasharray:9,5!important;stroke-dashoffset:900;animation:dash 50s linear infinite;stroke-linecap:round;}#mermaid-o8hds8z47xb .edge-animation-fast{stroke-dasharray:9,5!important;stroke-dashoffset:900;animation:dash 20s linear infinite;stroke-linecap:round;}#mermaid-o8hds8z47xb .error-icon{fill:#333;}#mermaid-o8hds8z47xb .error-text{fill:#cccccc;stroke:#cccccc;}#mermaid-o8hds8z47xb .edge-thickness-normal{stroke-width:1px;}#mermaid-o8hds8z47xb .edge-thickness-thick{stroke-width:3.5px;}#mermaid-o8hds8z47xb .edge-pattern-solid{stroke-dasharray:0;}#mermaid-o8hds8z47xb .edge-thickness-invisible{stroke-width:0;fill:none;}#mermaid-o8hds8z47xb .edge-pattern-dashed{stroke-dasharray:3;}#mermaid-o8hds8z47xb .edge-pattern-dotted{stroke-dasharray:2;}#mermaid-o8hds8z47xb .marker{fill:#666;stroke:#666;}#mermaid-o8hds8z47xb .marker.cross{stroke:#666;}#mermaid-o8hds8z47xb svg{font-family:ui-sans-serif,-apple-system,system-ui,Segoe UI,Helvetica;font-size:16px;}#mermaid-o8hds8z47xb p{margin:0;}#mermaid-o8hds8z47xb .entityBox{fill:#111;stroke:#222;}#mermaid-o8hds8z47xb .relationshipLabelBox{fill:#333;opacity:0.7;background-color:#333;}#mermaid-o8hds8z47xb .relationshipLabelBox rect{opacity:0.5;}#mermaid-o8hds8z47xb .labelBkg{background-color:rgba(51, 51, 51, 0.5);}#mermaid-o8hds8z47xb .edgeLabel .label{fill:#222;font-size:14px;}#mermaid-o8hds8z47xb .label{font-family:ui-sans-serif,-apple-system,system-ui,Segoe UI,Helvetica;color:#fff;}#mermaid-o8hds8z47xb .edge-pattern-dashed{stroke-dasharray:8,8;}#mermaid-o8hds8z47xb .node rect,#mermaid-o8hds8z47xb .node circle,#mermaid-o8hds8z47xb .node ellipse,#mermaid-o8hds8z47xb .node polygon{fill:#111;stroke:#222;stroke-width:1px;}#mermaid-o8hds8z47xb .relationshipLine{stroke:#666;stroke-width:1;fill:none;}#mermaid-o8hds8z47xb .marker{fill:none!important;stroke:#666!important;stroke-width:1;}#mermaid-o8hds8z47xb :root{--mermaid-font-family:"trebuchet ms",verdana,arial,sans-serif;}referenced bycontainsreferenced byfilesintidPKstringpathstringtitlestringartiststringalbumstringgenreintdata_kindintmedia_kindplaylistsintidPKstringtitleinttypestringqueryqueueintidPKintfile_idFKintposintshuffle_posplaylistitemsintidPKintplaylistidFKstringfilepathspeakersintidPKstringnamestringtypeintvolume
```

The database system uses various prepared statements for efficient querying and updates, and provides a query builder interface for constructing complex queries based on parameters.

Sources: [src/db.c L168-L235](https://github.com/owntone/owntone-server/blob/23c67a3e/src/db.c#L168-L235)

 [src/db.h L167-L253](https://github.com/owntone/owntone-server/blob/23c67a3e/src/db.h#L167-L253)

## Media Playback System

### Player Subsystem

The player subsystem is responsible for managing the playback queue, controlling playback, and routing audio data to outputs. It operates on a timer-based model, reading frames of audio data at fixed intervals and sending them to output devices.

```mermaid
flowchart TD

Player["Player Core"]
Session["Playback Session"]
Sources["Player Sources<br>(Queue Items)"]
Buffer["Audio Buffer"]
Input["Input Module"]
File["File Input"]
HTTP["HTTP Input"]
Spotify["Spotify Input"]
OutputManager["Output Manager"]
RAOP["AirPlay/RAOP Output"]
Cast["Chromecast Output"]
ALSA["ALSA Output"]
Pulse["PulseAudio Output"]

Player --> Input
Player --> OutputManager
Buffer --> OutputManager

subgraph subGraph2 ["Output System"]
    OutputManager
    RAOP
    Cast
    ALSA
    Pulse
    OutputManager --> RAOP
    OutputManager --> Cast
    OutputManager --> ALSA
    OutputManager --> Pulse
end

subgraph subGraph1 ["Input System"]
    Input
    File
    HTTP
    Spotify
    Input --> File
    Input --> HTTP
    Input --> Spotify
end

subgraph subGraph0 ["Player Components"]
    Player
    Session
    Sources
    Buffer
    Player --> Session
    Session --> Sources
    Session --> Buffer
end
```

The player operates with a concept of "ticks" that occur at regular intervals (typically 10ms). During each tick, it:

1. Reads audio data from the input source
2. Updates the playback position
3. Sends audio data to outputs

Sources: [src/player.c L96-L116](https://github.com/owntone/owntone-server/blob/23c67a3e/src/player.c#L96-L116)

 [src/player.c L194-L245](https://github.com/owntone/owntone-server/blob/23c67a3e/src/player.c#L194-L245)

### Audio Data Flow

```mermaid
flowchart TD

Files["Local Files"]
Streams["Internet Streams"]
Spotify["Spotify"]
Input["Input Module"]
Player["Player Core"]
Transcode["Transcoder"]
RAOP["AirPlay/RAOP"]
Cast["Chromecast"]
Local["Local Audio<br>(ALSA/Pulse)"]
HTTP["HTTP Streaming"]

Files --> Input
Streams --> Input
Spotify --> Input
Transcode --> RAOP
Transcode --> Cast
Transcode --> Local
Transcode --> HTTP

subgraph Outputs ["Outputs"]
    RAOP
    Cast
    Local
    HTTP
end

subgraph Processing ["Processing"]
    Input
    Player
    Transcode
    Input --> Player
    Player --> Transcode
end

subgraph subGraph0 ["Input Sources"]
    Files
    Streams
    Spotify
end
```

Sources: [src/player.c L89-L102](https://github.com/owntone/owntone-server/blob/23c67a3e/src/player.c#L89-L102)

 [src/outputs.c](https://github.com/owntone/owntone-server/blob/23c67a3e/src/outputs.c)

## Network Protocols

OwnTone implements several network protocols to provide compatibility with different client applications:

### DAAP (Digital Audio Access Protocol)

The DAAP protocol allows iTunes and compatible clients to browse and play music from OwnTone. It includes:

* Session management
* Library browsing (artists, albums, genres)
* Playlist management
* Media streaming

Sources: [src/httpd_daap.c L18-L22](https://github.com/owntone/owntone-server/blob/23c67a3e/src/httpd_daap.c#L18-L22)

### DACP (Digital Audio Control Protocol)

The DACP protocol enables remote control of OwnTone's playback, used by apps like Apple Remote:

* Playback control (play, pause, next, previous)
* Volume control
* Queue management
* Now playing information

Sources: [src/httpd_dacp.c L18-L22](https://github.com/owntone/owntone-server/blob/23c67a3e/src/httpd_dacp.c#L18-L22)

### MPD (Music Player Daemon) Protocol

The MPD protocol provides compatibility with MPD clients:

* Command-based text protocol
* Library browsing
* Playlist management
* Playback control

Sources: [src/mpd.c L19-L24](https://github.com/owntone/owntone-server/blob/23c67a3e/src/mpd.c#L19-L24)

 [src/mpd.c L97-L131](https://github.com/owntone/owntone-server/blob/23c67a3e/src/mpd.c#L97-L131)

### JSON API

The JSON API provides a modern interface for web applications:

* RESTful API design
* Library browsing
* Playback control
* Playlist management

Sources: [src/httpd_jsonapi.c](https://github.com/owntone/owntone-server/blob/23c67a3e/src/httpd_jsonapi.c)

## HTTP Server Architecture

The HTTP server is built on libevent's HTTP module and uses a modular design to handle different protocols:

```mermaid
flowchart TD

Listener["HTTP Listener"]
ThreadPool["HTTP Thread Pool"]
DAAP["DAAP Module"]
DACP["DACP Module"]
JSON["JSON API Module"]
Artwork["Artwork Module"]
Stream["Streaming Module"]
OAuth["OAuth Module"]
RSP["RSP Module"]
RequestHandler["Request Handler"]
Client["Client"]

Client --> Listener

subgraph subGraph1 ["HTTP Server"]
    Listener
    ThreadPool
    RequestHandler
    Listener --> RequestHandler
    RequestHandler --> ThreadPool
    ThreadPool --> DAAP
    ThreadPool --> DACP
    ThreadPool --> JSON
    ThreadPool --> Artwork
    ThreadPool --> Stream
    ThreadPool --> OAuth
    ThreadPool --> RSP

subgraph subGraph0 ["URI Handlers"]
    DAAP
    DACP
    JSON
    Artwork
    Stream
    OAuth
    RSP
end
end
```

The HTTP server uses a relatively small thread pool (by default, just 1 thread) because most operations should be non-blocking. For long-running operations, the handler should set up events rather than blocking the thread.

Sources: [src/httpd.c L69-L87](https://github.com/owntone/owntone-server/blob/23c67a3e/src/httpd.c#L69-L87)

 [src/httpd.c L144-L147](https://github.com/owntone/owntone-server/blob/23c67a3e/src/httpd.c#L144-L147)

## Output System

The output system is responsible for sending audio data to various output devices:

### Output Types

* **AirPlay/RAOP**: Streams to Apple AirPlay devices
* **Chromecast**: Streams to Google Chromecast devices
* **ALSA**: Local audio output on Linux systems
* **PulseAudio**: Local audio output using PulseAudio
* **HTTP Streaming**: Provides audio streams over HTTP

Each output type is implemented as a module with a consistent interface for device discovery, initialization, and audio data handling.

```mermaid
flowchart TD

Manager["Output Manager"]
DeviceList["Device List"]
Sessions["Output Sessions"]
RAOP["AirPlay/RAOP Output"]
Cast["Chromecast Output"]
ALSA["ALSA Output"]
Pulse["PulseAudio Output"]
HTTP["HTTP Streaming"]
AirPlayDevices["AirPlay Speakers"]
ChromecastDevices["Chromecast Devices"]
LocalSpeakers["Local Speakers"]
PulseSpeakers["PulseAudio Sinks"]
StreamClients["Stream Clients"]

Manager --> RAOP
Manager --> Cast
Manager --> ALSA
Manager --> Pulse
Manager --> HTTP
RAOP --> AirPlayDevices
Cast --> ChromecastDevices
ALSA --> LocalSpeakers
Pulse --> PulseSpeakers
HTTP --> StreamClients

subgraph subGraph1 ["Output Types"]
    RAOP
    Cast
    ALSA
    Pulse
    HTTP
end

subgraph subGraph0 ["Output System"]
    Manager
    DeviceList
    Sessions
    Manager --> DeviceList
    Manager --> Sessions
end
```

Sources: [src/outputs.h L11-L156](https://github.com/owntone/owntone-server/blob/23c67a3e/src/outputs.h#L11-L156)

 [src/outputs.c](https://github.com/owntone/owntone-server/blob/23c67a3e/src/outputs.c)

## Service Discovery

OwnTone uses mDNS (multicast DNS) for service discovery, allowing clients to find the server on the local network:

* Announces DAAP service for iTunes compatibility
* Announces DACP service for remote control
* Announces RSP service for Roku devices
* Announces HTTP service for web interface
* Optionally announces MPD service

```mermaid
sequenceDiagram
  participant OwnTone Server
  participant mDNS Responder
  participant Local Network
  participant Client Device

  OwnTone Server->>mDNS Responder: Register services
  mDNS Responder->>Local Network: Announce _daap._tcp
  mDNS Responder->>Local Network: Announce _dacp._tcp
  mDNS Responder->>Local Network: Announce _rsp._tcp
  mDNS Responder->>Local Network: Announce _http._tcp
  mDNS Responder->>Local Network: Announce _mpd._tcp
  Client Device->>Local Network: Browse for _daap._tcp
  Local Network->>Client Device: Return OwnTone server info
  Client Device->>OwnTone Server: Connect to service
```

Sources: [src/main.c L227-L360](https://github.com/owntone/owntone-server/blob/23c67a3e/src/main.c#L227-L360)

 [src/mdns.h](https://github.com/owntone/owntone-server/blob/23c67a3e/src/mdns.h)

## Initialization Sequence

The following diagram shows the initialization sequence of OwnTone:

```mermaid
sequenceDiagram
  participant Main Process
  participant Database
  participant Player
  participant HTTP Server
  participant mDNS
  participant Library

  Main Process->>Main Process: Parse command line args
  Main Process->>Main Process: Load configuration
  Main Process->>Database: Initialize database
  Database-->>Main Process: Database ready
  Main Process->>mDNS: Initialize mDNS
  mDNS-->>Main Process: mDNS ready
  Main Process->>Player: Initialize player
  Player-->>Main Process: Player ready
  Main Process->>HTTP Server: Initialize HTTP server
  HTTP Server->>HTTP Server: Register modules
  HTTP Server-->>Main Process: HTTP server ready
  Main Process->>Library: Initialize library
  Library->>Database: Check schema version
  Library->>Library: Start file scanner
  Library-->>Main Process: Library ready
  Main Process->>mDNS: Register services
  mDNS-->>Main Process: Services registered
  Main Process->>Main Process: Enter main event loop
```

Sources: [src/main.c L482-L885](https://github.com/owntone/owntone-server/blob/23c67a3e/src/main.c#L482-L885)

## Web Frontend Architecture

The web frontend is built with Vue.js and communicates with the server through the JSON API:

```mermaid
flowchart TD

App["App (Vue.js)"]
Router["Vue Router"]
Store["Pinia Store"]
Components["UI Components"]
API["JSON API Client"]
WS["WebSocket Client"]
JSONEndpoints["JSON API Endpoints"]
WebSocket["WebSocket Server"]

Store --> API
Store --> WS
API --> JSONEndpoints
WS --> WebSocket

subgraph Server ["Server"]
    JSONEndpoints
    WebSocket
end

subgraph subGraph1 ["Backend Communication"]
    API
    WS
end

subgraph subGraph0 ["Frontend Components"]
    App
    Router
    Store
    Components
    App --> Router
    App --> Store
    App --> Components
end
```

Sources: [web-src/package.json L13-L32](https://github.com/owntone/owntone-server/blob/23c67a3e/web-src/package.json#L13-L32)

 [htdocs/assets/index.js](https://github.com/owntone/owntone-server/blob/23c67a3e/htdocs/assets/index.js)

## Summary

OwnTone's architecture is designed for flexibility and extensibility, allowing it to support multiple input sources, output types, and client protocols. The event-driven design with a multi-threaded approach enables efficient handling of media streaming and playback control operations, while the modular structure makes it easy to add new features and capabilities.

The core components - database, player, outputs, and HTTP server - work together to provide a complete media server solution that can integrate with various audio ecosystems.