# Castersugar Development Session Summary

## Project Overview
Castersugar is a Flask web application for managing and controlling Chromecast devices, with a focus on playing radio stations.

## Recent Work Completed

### 1. ICY Metadata Implementation
Added support for displaying "Now Playing" track information from radio streams using ICY metadata parsing.

#### Files Created:
- `app/icy_metadata_service.py` - Service that monitors radio streams and extracts ICY metadata (artist/title)
  - Uses background threading to poll streams every 15 seconds
  - Parses ICY metadata from HTTP streams
  - Caches metadata for each monitored stream

#### Files Modified:

**Backend:**
- `app/routes.py`:
  - Added ICY metadata endpoint: `/api/device/<identifier>/icy-metadata`
  - Updated radio play/stop endpoints to track which stream is playing on which device
  - Stores stream URL mapping in DynamoDB using device UUID as key
  - Starts/stops ICY metadata monitoring when playback starts/stops

- `app/dynamodb_service.py`:
  - Added methods: `set_device_stream()`, `get_device_stream()`, `clear_device_stream()`
  - Tracks which stream URL is playing on each device using device UUID as key

**Frontend - Device Detail Page:**
- `app/static/device_detail.js`:
  - Added `cachedICYMetadata` variable to prevent flickering
  - Modified `updateUI()` to prefer cached ICY metadata over Chromecast status
  - Added `loadICYMetadata()` function that polls every 10 seconds
  - Metadata polling starts automatically when radio is playing without artist/album info
  - Caches metadata to ensure consistent display (no flickering between updates)

**Frontend - Radio Page:**
- `app/templates/radio.html`:
  - Moved "Now Playing" section outside device controls (between controls and stations list)
  - Added track info display container (single div, no nested spans)

- `app/static/radio.js`:
  - Added `checkCurrentlyPlaying()` function to detect already-playing streams on page load
  - Integrated with device selection dropdown to update "Now Playing" when switching devices
  - Added ICY metadata polling functions: `startICYMetadataPolling()`, `stopICYMetadataPolling()`, `loadICYMetadata()`
  - Displays track info as plain text: "Artist - Title"

- `app/static/style.css`:
  - Added styling for `.now-playing-track-info`
  - Uses uniform styling: 0.85rem font size, weight 400, color #2c3e50

### 2. Key Technical Details

**ICY Metadata Parsing:**
- Connects to stream with `Icy-MetaData: 1` header
- Reads `icy-metaint` bytes of audio data
- Extracts metadata block and parses `StreamTitle='Artist - Title'` format
- Background threads monitor streams with threading.Event for clean shutdown

**Device Stream Tracking:**
- Always uses device UUID as the key for tracking streams (not normalized name)
- This ensures consistent lookups whether accessing by UUID or normalized name
- The `resolve_device_identifier()` function converts any identifier to UUID

**Frontend Polling:**
- Device detail page: Polls ICY metadata every 10 seconds when playing radio
- Radio page: Polls ICY metadata every 10 seconds when a station is playing
- Stops polling automatically when playback stops or device is switched

### 3. Bug Fixes
- Fixed flickering issue on device detail page by caching ICY metadata
- Fixed device stream tracking by always using UUID as key
- Fixed "Now Playing" not appearing when loading radio page with already-playing station
- Simplified track info styling by using plain text instead of nested spans

### 4. Current State
The application now successfully:
- Displays ICY metadata (artist/title) on both device detail pages and radio page
- Updates track information every 10-15 seconds automatically
- Handles device switching gracefully
- Shows "Now Playing" information when page loads with active playback
- Maintains uniform text styling throughout

## Testing
Tested with:
- SomaFM Groove Salad stream (confirmed ICY metadata working)
- Multiple devices
- Device switching
- Page reloads with active playback

## File Structure
```
castersugar/
├── app/
│   ├── __init__.py
│   ├── routes.py (updated)
│   ├── chromecast_service.py
│   ├── dynamodb_service.py (updated)
│   ├── icy_metadata_service.py (NEW)
│   ├── static/
│   │   ├── style.css (updated)
│   │   ├── radio.js (updated)
│   │   ├── device_detail.js (updated)
│   │   └── devices.js
│   └── templates/
│       ├── radio.html (updated)
│       ├── device_detail.html
│       └── devices.html
├── main.py
├── pyproject.toml
└── uv.lock
```

## Environment
- Python 3.x with uv package manager
- Flask web framework
- Local DynamoDB at http://192.168.1.1:8001
- pychromecast library for Chromecast control

## Next Steps / Future Enhancements
Potential improvements:
- Add album art display for streams that provide it
- Add configuration for metadata polling interval
- Support for additional metadata fields (album, year, etc.)
- Better error handling for streams that don't support ICY metadata
- Persistent storage of which streams support metadata to avoid unnecessary polling

## Debug Notes
- Server logs show ICY metadata monitoring start/stop messages
- Test scripts available: `test_icy_tracking.py`, `test_somafm.py`
- Server runs on http://127.0.0.1:5000 and http://192.168.1.158:5000
