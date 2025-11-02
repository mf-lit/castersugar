"""Service for fetching metadata from BBC radio streams via RMS API."""
import requests
import threading
import time
from typing import Optional, Dict
from urllib.parse import urlparse, parse_qs


class BBCMetadataService:
    """Service for monitoring BBC radio streams and extracting metadata from RMS API."""

    def __init__(self):
        self.metadata_cache = {}  # {stream_url: {artist, title, timestamp, history}}
        self.active_streams = {}  # {stream_url: stop_event}
        self.monitoring_start_times = {}  # {stream_url: start_timestamp}
        self.lock = threading.Lock()

    def is_bbc_stream(self, stream_url: str) -> bool:
        """Check if URL is a BBC stream (lsn.lv or lstn.lv)."""
        return (stream_url.startswith('http://lsn.lv/') or
                stream_url.startswith('https://lsn.lv/') or
                stream_url.startswith('http://lstn.lv/') or
                stream_url.startswith('https://lstn.lv/'))

    def extract_station_id(self, stream_url: str) -> Optional[str]:
        """Extract BBC station ID from lstn.lv URL."""
        try:
            parsed = urlparse(stream_url)
            params = parse_qs(parsed.query)
            station_id = params.get('station', [None])[0]
            return station_id
        except Exception as e:
            print(f"Error extracting station ID from {stream_url}: {e}")
            return None

    def start_monitoring(self, stream_url: str):
        """Start monitoring a BBC stream for metadata."""
        with self.lock:
            # Don't start if already monitoring
            if stream_url in self.active_streams:
                return

            # Extract station ID
            station_id = self.extract_station_id(stream_url)
            if not station_id:
                print(f"Could not extract station ID from BBC stream: {stream_url}")
                return

            # Create stop event
            stop_event = threading.Event()
            self.active_streams[stream_url] = stop_event

            # Record start time
            self.monitoring_start_times[stream_url] = time.time()

            # Start background thread
            thread = threading.Thread(
                target=self._monitor_stream,
                args=(stream_url, station_id, stop_event),
                daemon=True
            )
            thread.start()
            print(f"Started BBC metadata monitoring for: {stream_url} (station: {station_id})")

    def stop_monitoring(self, stream_url: str):
        """Stop monitoring a stream."""
        with self.lock:
            if stream_url in self.active_streams:
                # Signal thread to stop
                self.active_streams[stream_url].set()
                del self.active_streams[stream_url]
                # Clean up start time tracking
                if stream_url in self.monitoring_start_times:
                    del self.monitoring_start_times[stream_url]
                print(f"Stopped BBC metadata monitoring for: {stream_url}")

    def get_metadata(self, stream_url: str) -> Optional[Dict]:
        """Get cached metadata for a stream."""
        with self.lock:
            return self.metadata_cache.get(stream_url)

    def get_active_streams(self) -> Dict[str, float]:
        """Get all active streams and their monitoring durations in seconds."""
        with self.lock:
            current_time = time.time()
            return {
                stream_url: current_time - start_time
                for stream_url, start_time in self.monitoring_start_times.items()
            }

    def _monitor_stream(self, stream_url: str, station_id: str, stop_event: threading.Event):
        """Background thread that monitors stream for metadata via BBC RMS API."""
        while not stop_event.is_set():
            try:
                metadata = self._fetch_bbc_metadata(station_id)
                if metadata:
                    with self.lock:
                        # Get existing cache for this stream
                        existing = self.metadata_cache.get(stream_url)

                        # Check if this is a new song
                        is_new_song = True
                        if existing:
                            is_new_song = (
                                existing.get('artist') != metadata.get('artist') or
                                existing.get('title') != metadata.get('title')
                            )

                        # If it's a new song, add current to history
                        history = []
                        if is_new_song and existing:
                            # Add the previous current song to history
                            history_entry = {
                                'artist': existing.get('artist'),
                                'title': existing.get('title'),
                                'timestamp': existing.get('timestamp')
                            }
                            # Get existing history and prepend new entry
                            old_history = existing.get('history', [])
                            history = [history_entry] + old_history[:1]  # Keep only last 2 songs in history
                        elif existing:
                            # Not a new song, keep existing history
                            history = existing.get('history', [])

                        # Update cache with new metadata and history
                        self.metadata_cache[stream_url] = {
                            **metadata,
                            'timestamp': time.time(),
                            'history': history
                        }

                        if is_new_song:
                            print(f"BBC metadata updated for {stream_url}: {metadata.get('artist')} - {metadata.get('title')}")
            except Exception as e:
                print(f"Error fetching BBC metadata for {stream_url}: {e}")

            # Wait before next check (or until stopped)
            stop_event.wait(15)  # Check every 15 seconds

    def _fetch_bbc_metadata(self, station_id: str) -> Optional[Dict]:
        """Fetch metadata from BBC RMS API."""
        try:
            # BBC RMS API endpoint
            url = f"https://rms.api.bbc.co.uk/v2/services/{station_id}/segments/latest"
            params = {
                'experience': 'domestic',
                'offset': '0',
                'limit': '1'
            }
            headers = {
                'User-Agent': 'Castersugar/1.0'
            }

            response = requests.get(url, params=params, headers=headers, timeout=10)
            response.raise_for_status()

            data = response.json()

            # Extract metadata from response
            if 'data' in data and len(data['data']) > 0:
                segment = data['data'][0]

                # Check if it's a music segment
                if segment.get('type') == 'music' or 'titles' in segment:
                    titles = segment.get('titles', {})
                    artist = titles.get('primary', '').strip()
                    title = titles.get('secondary', '').strip()

                    if artist or title:
                        return {
                            'artist': artist if artist else None,
                            'title': title if title else None,
                            'raw': f"{artist} - {title}" if artist and title else (artist or title)
                        }

            return None

        except requests.exceptions.RequestException as e:
            print(f"Error fetching BBC RMS API for {station_id}: {e}")
            return None
        except Exception as e:
            print(f"Error parsing BBC metadata response for {station_id}: {e}")
            return None


# Global instance
bbc_metadata_service = BBCMetadataService()
