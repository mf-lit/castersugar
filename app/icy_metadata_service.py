"""Service for fetching ICY metadata from radio streams."""
import requests
import threading
import time
import re
from typing import Optional, Dict


class ICYMetadataService:
    """Service for monitoring radio streams and extracting ICY metadata."""

    def __init__(self):
        self.metadata_cache = {}  # {stream_url: {artist, title, timestamp, history}}
        self.active_streams = {}  # {stream_url: stop_event}
        self.monitoring_start_times = {}  # {stream_url: start_timestamp}
        self.lock = threading.Lock()

    def start_monitoring(self, stream_url: str):
        """Start monitoring a stream for metadata."""
        with self.lock:
            # Don't start if already monitoring
            if stream_url in self.active_streams:
                return

            # Create stop event
            stop_event = threading.Event()
            self.active_streams[stream_url] = stop_event

            # Record start time
            self.monitoring_start_times[stream_url] = time.time()

            # Start background thread
            thread = threading.Thread(
                target=self._monitor_stream,
                args=(stream_url, stop_event),
                daemon=True
            )
            thread.start()
            print(f"Started ICY metadata monitoring for: {stream_url}")

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
                print(f"Stopped ICY metadata monitoring for: {stream_url}")

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

    def _monitor_stream(self, stream_url: str, stop_event: threading.Event):
        """Background thread that monitors stream for metadata."""
        while not stop_event.is_set():
            try:
                metadata = self._fetch_icy_metadata(stream_url)
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
                            print(f"ICY metadata updated for {stream_url}: {metadata.get('artist')} - {metadata.get('title')}")
            except Exception as e:
                print(f"Error fetching ICY metadata for {stream_url}: {e}")

            # Wait before next check (or until stopped)
            stop_event.wait(15)  # Check every 15 seconds

    def _fetch_icy_metadata(self, stream_url: str) -> Optional[Dict]:
        """Fetch ICY metadata from stream."""
        response = None
        try:
            # Request with ICY metadata
            headers = {
                'Icy-MetaData': '1',
                'User-Agent': 'Castersugar/1.0'
            }

            response = requests.get(
                stream_url,
                headers=headers,
                stream=True,
                timeout=10
            )

            # Check if server supports ICY metadata
            metaint = response.headers.get('icy-metaint')
            if not metaint:
                # Try lowercase variant
                metaint = response.headers.get('Icy-MetaInt')

            if not metaint:
                print(f"Stream {stream_url} does not support ICY metadata")
                return None

            metaint = int(metaint)

            # Read audio data up to metadata block
            response.raw.read(metaint)

            # Read metadata length (1 byte, multiply by 16 to get actual length)
            meta_length_byte = response.raw.read(1)
            if not meta_length_byte:
                return None

            meta_length = ord(meta_length_byte) * 16

            if meta_length > 0:
                # Read metadata
                metadata_bytes = response.raw.read(meta_length)
                metadata_str = metadata_bytes.decode('utf-8', errors='ignore').rstrip('\x00')

                # Parse StreamTitle='Artist - Title';
                return self._parse_icy_metadata(metadata_str)

            return None

        finally:
            # Always close the connection
            if response:
                response.close()

    def _parse_icy_metadata(self, metadata_str: str) -> Optional[Dict]:
        """Parse ICY metadata string."""
        # Extract StreamTitle
        match = re.search(r"StreamTitle='([^']+)'", metadata_str)
        if not match:
            return None

        stream_title = match.group(1)

        # Try to parse "Artist - Title" format
        if ' - ' in stream_title:
            parts = stream_title.split(' - ', 1)
            return {
                'artist': parts[0].strip(),
                'title': parts[1].strip(),
                'raw': stream_title
            }
        else:
            # Couldn't parse, return as title
            return {
                'artist': None,
                'title': stream_title,
                'raw': stream_title
            }


# Global instance
icy_metadata_service = ICYMetadataService()
