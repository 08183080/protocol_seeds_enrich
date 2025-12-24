# Media Transcoding

> **Relevant source files**
> * [src/artwork.c](https://github.com/owntone/owntone-server/blob/23c67a3e/src/artwork.c)
> * [src/artwork.h](https://github.com/owntone/owntone-server/blob/23c67a3e/src/artwork.h)
> * [src/transcode.c](https://github.com/owntone/owntone-server/blob/23c67a3e/src/transcode.c)
> * [src/transcode.h](https://github.com/owntone/owntone-server/blob/23c67a3e/src/transcode.h)

Media transcoding in OwnTone is the process of converting audio and image files from one format to another on-the-fly. This is essential for ensuring compatibility between the media server and various client devices that support different formats and capabilities. The transcoding module serves as a bridge between the Player component and the Output System, allowing OwnTone to serve media in the most appropriate format for each client.

For information about the Player system that uses the transcoding module, see [Media Playback System](/owntone/owntone-server/3-media-playback-system) and [Player Core](/owntone/owntone-server/3.1-player-core). For details on audio output destinations, see [Audio Output System](/owntone/owntone-server/3.2-audio-output-system).

## Architecture Overview

The transcoding system in OwnTone is built around several key components that work together to form a complete transcoding pipeline:

```

```

The main components are:

1. **Decode Context** (`struct decode_ctx`): Handles opening, reading, and decoding from the source media
2. **Encode Context** (`struct encode_ctx`): Manages encoding and writing to the target format
3. **Transcode Context** (`struct transcode_ctx`): Combines both contexts for a complete pipeline
4. **Settings Context** (`struct settings_ctx`): Configures encoding/decoding parameters

This architecture allows for flexible conversion between various media formats while maintaining high quality and performance.

Sources: [src/transcode.c L121-L170](https://github.com/owntone/owntone-server/blob/23c67a3e/src/transcode.c#L121-L170)

 [src/transcode.h L52-L57](https://github.com/owntone/owntone-server/blob/23c67a3e/src/transcode.h#L52-L57)

## Transcoding Profiles

OwnTone defines a set of transcoding profiles that specify how media should be converted. Each profile configures specific encoding parameters based on the target format and quality requirements.

| Profile | Description | Use Case |
| --- | --- | --- |
| `XCODE_NONE` | No transcoding | Native format playback |
| `XCODE_PCM_NATIVE` | PCM with native sample rate/bit depth | High-quality local playback |
| `XCODE_WAV` | 16-bit PCM with WAV header | Universal compatibility |
| `XCODE_PCM16/24/32` | PCM with specified bit depth | Various quality levels |
| `XCODE_MP3` | MP3 format | Bandwidth-optimized streaming |
| `XCODE_OPUS` | Raw OPUS (no container) | Modern streaming |
| `XCODE_ALAC` | Raw ALAC (no container) | Apple ecosystem |
| `XCODE_MP4_ALAC` | ALAC in MP4 container | iTunes, iOS devices |
| `XCODE_OGG` | OGG format | OGG source compatibility |
| `XCODE_JPEG/PNG/VP8` | Image/video formats | Artwork extraction |

The `init_settings()` function configures the appropriate encoding parameters based on the selected profile. Additional quality parameters like sample rate, channel count, and bit rate can be specified to fine-tune the output.

Sources: [src/transcode.h L9-L39](https://github.com/owntone/owntone-server/blob/23c67a3e/src/transcode.h#L9-L39)

 [src/transcode.c L242-L395](https://github.com/owntone/owntone-server/blob/23c67a3e/src/transcode.c#L242-L395)

## Transcoding Process

The transcoding process involves several stages that transform media from the source format to the target format:

```

```

The main steps in this process are:

1. **Setup**: Initialize encoders and decoders based on profiles
2. **Read**: Extract packets from the input source
3. **Decode**: Convert packets to uncompressed frames
4. **Filter**: Apply processing like resampling or scaling
5. **Encode**: Convert frames to the target format
6. **Write**: Output the encoded data

This process continues until all input has been processed or an error occurs. The `transcode()` function orchestrates this entire process.

Sources: [src/transcode.c L738-L973](https://github.com/owntone/owntone-server/blob/23c67a3e/src/transcode.c#L738-L973)

 [src/transcode.h L161-L163](https://github.com/owntone/owntone-server/blob/23c67a3e/src/transcode.h#L161-L163)

## FFmpeg Integration

OwnTone relies heavily on FFmpeg libraries for the actual media processing capabilities. The integration between OwnTone and FFmpeg is shown below:

```

```

Key FFmpeg components used:

1. **libavcodec**: Provides encoders and decoders for various audio and video codecs
2. **libavformat**: Handles container formats (MP3, MP4, WAV, etc.)
3. **libavfilter**: Enables audio processing like resampling and video scaling
4. **libavutil**: Offers utility functions and data structures
5. **AVIOContext**: Handles I/O operations, extended by OwnTone for custom I/O

OwnTone wraps these libraries with a higher-level interface that integrates with its event-based architecture.

Sources: [src/transcode.c L28-L38](https://github.com/owntone/owntone-server/blob/23c67a3e/src/transcode.c#L28-L38)

 [src/transcode.c L310-L348](https://github.com/owntone/owntone-server/blob/23c67a3e/src/transcode.c#L310-L348)

## Custom I/O System

Instead of working directly with files, OwnTone implements custom I/O handlers that allow FFmpeg to work with `evbuffer` structures from the libevent library:

```

```

This custom I/O system consists of:

1. **avio_evbuffer_read()**: Reads data from an evbuffer
2. **avio_evbuffer_write()**: Writes encoded data to an evbuffer
3. **avio_evbuffer_seek()**: Provides seeking capability
4. **avio_evbuffer_open()**: Sets up the custom I/O context
5. **avio_evbuffer_close()**: Cleans up the I/O context

This approach allows transcoding to operate on memory buffers rather than temporary files, improving performance and reducing disk I/O.

Sources: [src/transcode.c L976-L1087](https://github.com/owntone/owntone-server/blob/23c67a3e/src/transcode.c#L976-L1087)

 [src/transcode.h L59-L66](https://github.com/owntone/owntone-server/blob/23c67a3e/src/transcode.h#L59-L66)

## API and Usage

The transcoding API provides functions for setting up, performing, and cleaning up transcoding operations:

### Setup Functions

* `transcode_decode_setup()`: Creates and initializes a decode context
* `transcode_encode_setup()`: Creates and initializes an encode context
* `transcode_setup()`: Sets up a complete transcoding pipeline

### Transcoding Functions

* `transcode()`: Main function that performs the entire transcoding process
* `transcode_decode()`: Decodes a single frame from the source
* `transcode_encode()`: Encodes a single frame to the target format

### Cleanup Functions

* `transcode_decode_cleanup()`: Frees resources used by the decode context
* `transcode_encode_cleanup()`: Frees resources used by the encode context
* `transcode_cleanup()`: Cleans up the entire transcoding context

### Helper Functions

* `transcode_needed()`: Determines if transcoding is required based on client capabilities
* `transcode_seek()`: Seeks to a specific position in the media
* `transcode_metadata()`: Extracts and provides metadata

Example usage pattern:

1. Determine if transcoding is needed with `transcode_needed()`
2. Set up transcoding with appropriate profile
3. Process media in chunks using `transcode()`
4. Clean up resources when finished

Sources: [src/transcode.h L101-L232](https://github.com/owntone/owntone-server/blob/23c67a3e/src/transcode.h#L101-L232)

## Specialized Transcoding Features

OwnTone's transcoding system includes several specialized features for specific use cases:

### Artwork Transcoding

The transcoding module is used by the artwork subsystem to resize and convert artwork images. This allows OwnTone to provide appropriately sized artwork to different clients:

```

```

The artwork system uses profiles like `XCODE_JPEG`, `XCODE_PNG`, and `XCODE_VP8` to process images.

Sources: [src/artwork.c L605-L761](https://github.com/owntone/owntone-server/blob/23c67a3e/src/artwork.c#L605-L761)

### Custom Headers

For certain formats like WAV and MP4, OwnTone can generate custom headers to ensure compatibility with specific clients:

1. **WAV Headers**: Generated by `make_wav_header()` function
2. **MP4 Headers**: Created by `make_mp4_header()` function

These headers ensure that clients like iTunes can properly interpret the transcoded media.

Sources: [src/transcode.c L1092-L1304](https://github.com/owntone/owntone-server/blob/23c67a3e/src/transcode.c#L1092-L1304)

### Stream Adaptation

The transcoding system can adapt to streaming sources, handling issues like connection interruptions and metadata updates:

* **Timeout Handling**: The `decode_interrupt_cb()` function prevents hanging on network issues
* **ICY Metadata**: Support for extracting and processing stream metadata

This makes OwnTone robust when dealing with internet radio and other streaming sources.

Sources: [src/transcode.c L712-L729](https://github.com/owntone/owntone-server/blob/23c67a3e/src/transcode.c#L712-L729)

## Conclusion

The media transcoding system is a critical component of OwnTone that enables compatibility across diverse client devices and network conditions. By leveraging FFmpeg libraries with a custom I/O layer, it provides flexible, high-performance transcoding capabilities for both audio files and artwork images.

The modular architecture with separate decode and encode contexts allows for easy extension and maintenance, while the profile-based configuration system makes it straightforward to support new formats and quality requirements.