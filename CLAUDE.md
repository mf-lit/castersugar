# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

castersugar is a Flask web application for managing and casting to Chromecast devices, with an emphasis on Chromecast Audio. The application provides device discovery, caching, and a web interface for managing devices.

## Development Setup

This project uses `uv` for dependency management.

**Install dependencies:**
```bash
uv sync
```

**Run the development server:**
```bash
uv run python main.py
```

The application will be available at http://localhost:5000

**Activate virtual environment (if needed):**
```bash
source .venv/bin/activate  # On macOS/Linux
```

## Requirements

- Python 3.13+
- Dependencies managed via `pyproject.toml` and locked in `uv.lock`
- Network access to discover Chromecast devices on the local network

## Key Dependencies

- `pychromecast` (>=14.0.9): Python library to interact with Chromecast devices
- `flask` (>=3.1.0): Web framework for the application

## Project Structure

```
castersugar/
├── main.py                 # Application entry point
├── app/
│   ├── __init__.py        # Flask app factory
│   ├── routes.py          # Web routes and API endpoints
│   ├── chromecast_service.py  # Chromecast discovery and caching service
│   ├── templates/         # HTML templates
│   │   ├── base.html
│   │   ├── index.html
│   │   └── devices.html
│   └── static/            # Static assets
│       ├── style.css
│       └── devices.js
├── pyproject.toml
└── uv.lock
```

## Architecture

### Chromecast Service (app/chromecast_service.py)

The `ChromecastService` class handles device discovery with built-in caching:
- Caches discovered devices for 60 minutes by default
- Thread-safe implementation using locks
- Supports forced refresh to bypass cache
- Returns serialized device information including name, model, host, and type

### Routes (app/routes.py)

- `/` - Home page
- `/devices` - Device listing page
- `/api/devices` - API endpoint for device discovery (supports `?refresh=true` parameter)

### Frontend

The devices page automatically loads cached devices on page load and provides a refresh button to force new discovery. Devices are displayed in a grid with Audio devices highlighted and sorted first.
