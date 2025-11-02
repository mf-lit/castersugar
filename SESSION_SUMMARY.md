# Castersugar Development Session Summary

## Project Overview
Castersugar is a Flask web application for managing and controlling Chromecast devices, with a focus on playing radio stations.

## Recent Work Completed

### 1. ICY Metadata Song History (Latest Session)
Added song history tracking to display the previous 2 songs on the radio page.

#### Files Modified:
- `app/icy_metadata_service.py`:
  - Modified `_monitor_stream()` to track song changes
  - Stores previous 2 songs in history array
  - Detects new songs by comparing artist/title
  - History is maintained per stream URL

- `app/templates/radio.html`:
  - Added containers for previous tracks (previous-track-1 and previous-track-2)
  - Current song displayed at top, history below

- `app/static/radio.js`:
  - Updated `loadICYMetadata()` to display history from API response
  - Shows previous tracks with appropriate styling
  - Handles hiding/showing history sections

- `app/static/style.css`:
  - Current song: 0.85rem font, #2c3e50 color
  - Previous song 1: 0.75rem font, #7f8c8d color (grey)
  - Previous song 2: 0.7rem font, #95a5a6 color (lighter grey)
  - Added word-wrap CSS to prevent text truncation
  - Removed separator lines between songs

### 2. Chromecast Device Caching (Latest Session)
Changed device caching from time-based (60 minutes) to indefinite caching.

#### Files Modified:
- `app/chromecast_service.py`:
  - Removed `cache_duration_minutes` parameter
  - Removed `timedelta` import
  - Modified `discover_devices()` to only refresh when `force_refresh=True`
  - Updated `get_cache_info()` to remove expiration fields
  - Cache now persists indefinitely until manually refreshed or app restarts

- `app/static/devices.js`:
  - Updated `displayCacheInfo()` to show "Cached indefinitely" status
  - Removed expiration countdown logic

### 3. UI/UX Improvements (Latest Session)

#### Navigation and Page Titles:
- **Removed page titles** from all templates (index.html, devices.html, radio.html)
- **Added active navigation highlighting**:
  - `app/templates/base.html`: Added active page logic
  - `app/routes.py`: All routes now pass `active_page` parameter
  - `app/static/style.css`: Active nav links have highlighted background and bold text

#### Station Cards:
- Reduced station card width from 250px to 180px minimum
- Reduced gap between cards from 1.5rem to 1rem
- Reduced internal padding from 1rem to 0.75rem
- Allows 30-40% more stations per row

#### Text Display:
- Fixed text truncation by adding `word-break` and `overflow-wrap` CSS
- Station names, track titles, and artist names now wrap properly
- Removed all separator lines between songs for cleaner look

### 4. Docker Deployment (Latest Session)
Created complete Docker setup for easy deployment.

#### Files Created:
- `Dockerfile`:
  - Based on Python 3.13 slim
  - Uses `uv` for fast dependency management
  - Multi-stage build for efficient caching
  - Exposes port 5005

- `docker-compose.yml`:
  - Single service configuration
  - Uses `network_mode: host` for Chromecast discovery
  - Auto-restart policy
  - Development volume mounts (commented)

- `.dockerignore`:
  - Excludes Python cache, virtual environments, Git files, IDEs
  - Reduces image size and build time

- `DOCKER.md`:
  - Complete deployment documentation
  - Quick start guide
  - Troubleshooting tips

### 5. Previous Session: ICY Metadata Implementation
Added support for displaying "Now Playing" track information from radio streams using ICY metadata parsing.

#### Files Created:
- `app/icy_metadata_service.py` - Service that monitors radio streams and extracts ICY metadata (artist/title)
  - Uses background threading to poll streams every 15 seconds
  - Parses ICY metadata from HTTP streams
  - Caches metadata for each monitored stream
  - Tracks song history (previous 2 songs)

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
  - Added track info display container
  - Added history containers for previous tracks

- `app/static/radio.js`:
  - Added `checkCurrentlyPlaying()` function to detect already-playing streams on page load
  - Integrated with device selection dropdown to update "Now Playing" when switching devices
  - Added ICY metadata polling functions: `startICYMetadataPolling()`, `stopICYMetadataPolling()`, `loadICYMetadata()`
  - Displays track info as plain text: "Artist - Title"
  - Displays previous song history

## Key Technical Details

**ICY Metadata Parsing:**
- Connects to stream with `Icy-MetaData: 1` header
- Reads `icy-metaint` bytes of audio data
- Extracts metadata block and parses `StreamTitle='Artist - Title'` format
- Background threads monitor streams with threading.Event for clean shutdown
- Tracks previous 2 songs in history array

**Device Stream Tracking:**
- Always uses device UUID as the key for tracking streams (not normalized name)
- This ensures consistent lookups whether accessing by UUID or normalized name
- The `resolve_device_identifier()` function converts any identifier to UUID

**Frontend Polling:**
- Device detail page: Polls ICY metadata every 10 seconds when playing radio
- Radio page: Polls ICY metadata every 10 seconds when a station is playing
- Stops polling automatically when playback stops or device is switched

**Chromecast Caching:**
- Devices cached indefinitely
- Only refreshes when user clicks "Refresh Devices" button
- Reduces network traffic and improves page load times

## Bug Fixes
- Fixed flickering issue on device detail page by caching ICY metadata
- Fixed device stream tracking by always using UUID as key
- Fixed "Now Playing" not appearing when loading radio page with already-playing station
- Simplified track info styling by using plain text instead of nested spans
- Fixed text truncation issues with proper word-wrapping CSS

## Current State
The application now successfully:
- Displays ICY metadata (artist/title) on both device detail pages and radio page
- Shows song history (previous 2 tracks) on radio page
- Updates track information every 10-15 seconds automatically
- Handles device switching gracefully
- Shows "Now Playing" information when page loads with active playback
- Maintains uniform text styling throughout
- Caches Chromecast devices indefinitely
- Highlights active page in navigation menu
- Supports Docker deployment

## File Structure
```
castersugar/
├── app/
│   ├── __init__.py
│   ├── routes.py (updated)
│   ├── chromecast_service.py (updated)
│   ├── dynamodb_service.py (updated)
│   ├── icy_metadata_service.py (NEW)
│   ├── static/
│   │   ├── style.css (updated)
│   │   ├── radio.js (updated)
│   │   ├── device_detail.js (updated)
│   │   └── devices.js (updated)
│   └── templates/
│       ├── base.html (updated)
│       ├── index.html (updated)
│       ├── radio.html (updated)
│       ├── device_detail.html
│       └── devices.html (updated)
├── main.py
├── pyproject.toml
├── uv.lock
├── Dockerfile (NEW)
├── docker-compose.yml (NEW)
├── .dockerignore (NEW)
├── DOCKER.md (NEW)
└── CLAUDE.md
```

## Environment
- Python 3.13 with uv package manager
- Flask web framework
- Local DynamoDB at http://192.168.1.1:8001
- pychromecast library for Chromecast control
- Server runs on http://127.0.0.1:5005 and http://192.168.1.158:5005

## Docker Deployment
Application can now be deployed using Docker:
```bash
docker-compose up -d
```
Access at: http://localhost:5005

See DOCKER.md for complete deployment guide.

## Next Steps / Future Enhancements
Potential improvements:
- Add album art display for streams that provide it
- Add configuration for metadata polling interval
- Support for additional metadata fields (album, year, etc.)
- Better error handling for streams that don't support ICY metadata
- Persistent storage of which streams support metadata to avoid unnecessary polling
- Production WSGI server configuration (gunicorn/uwsgi)
- Environment variable configuration
