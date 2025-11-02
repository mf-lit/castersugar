import pychromecast
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import threading
import time


class ChromecastService:
    """Service for discovering and caching Chromecast devices."""

    def __init__(self, cache_duration_minutes: int = 60):
        self.cache_duration = timedelta(minutes=cache_duration_minutes)
        self._devices: List[Dict] = []
        self._last_discovery: Optional[datetime] = None
        self._lock = threading.Lock()
        self._chromecasts_cache = {}  # Cache chromecast objects by UUID
        self._name_to_uuid = {}  # Map device names (normalized) to UUIDs
        self._browser = None  # Keep browser alive for reconnections

    @staticmethod
    def normalize_device_name(name: str) -> str:
        """Normalize device name to create URL-safe alias."""
        return name.lower().replace(' ', '_')

    def discover_devices(self, force_refresh: bool = False) -> List[Dict]:
        """
        Discover Chromecast devices on the network.

        Args:
            force_refresh: If True, bypass cache and force new discovery

        Returns:
            List of device information dictionaries
        """
        with self._lock:
            now = datetime.now()

            # Check if we need to refresh the cache
            if (not force_refresh and
                self._last_discovery and
                now - self._last_discovery < self.cache_duration and
                self._devices):
                return self._devices

            # Perform discovery
            print(f"Discovering Chromecast devices... (forced: {force_refresh})")

            # Stop old browser if exists
            if self._browser:
                try:
                    pychromecast.discovery.stop_discovery(self._browser)
                except:
                    pass

            chromecasts, browser = pychromecast.get_chromecasts()
            self._browser = browser  # Keep browser alive

            # Convert to serializable format
            self._devices = []
            self._chromecasts_cache = {}  # Clear old cache
            self._name_to_uuid = {}  # Clear old name mapping

            for cast in chromecasts:
                # Wait for cast to be ready
                try:
                    cast.wait(timeout=5)
                except:
                    print(f"Warning: Could not connect to {cast.name}")
                    continue

                # Get host and port from socket_client
                host = cast.socket_client.host if hasattr(cast.socket_client, 'host') else 'unknown'
                port = cast.socket_client.port if hasattr(cast.socket_client, 'port') else 8009

                uuid = str(cast.uuid)
                normalized_name = self.normalize_device_name(cast.name)

                device_info = {
                    'name': cast.name,
                    'normalized_name': normalized_name,
                    'model_name': cast.model_name,
                    'uuid': uuid,
                    'host': host,
                    'port': port,
                    'cast_type': cast.cast_type,
                    'manufacturer': getattr(cast.cast_info, 'manufacturer', 'Unknown') if hasattr(cast, 'cast_info') else 'Unknown',
                    'is_audio_device': 'Audio' in cast.model_name if cast.model_name else False
                }
                self._devices.append(device_info)

                # Cache the chromecast object for later use
                self._chromecasts_cache[uuid] = cast

                # Map normalized name to UUID
                self._name_to_uuid[normalized_name] = uuid

            self._last_discovery = now
            print(f"Found {len(self._devices)} devices")

            return self._devices

    def get_cache_info(self) -> Dict:
        """Get information about the current cache status."""
        with self._lock:
            if not self._last_discovery:
                return {
                    'cached': False,
                    'last_discovery': None,
                    'expires_at': None,
                    'device_count': 0
                }

            expires_at = self._last_discovery + self.cache_duration
            now = datetime.now()

            return {
                'cached': True,
                'last_discovery': self._last_discovery.isoformat(),
                'expires_at': expires_at.isoformat(),
                'is_expired': now >= expires_at,
                'device_count': len(self._devices)
            }

    def get_device_by_uuid(self, uuid: str) -> Optional[Dict]:
        """Get device info by UUID."""
        with self._lock:
            for device in self._devices:
                if device['uuid'] == uuid:
                    return device
            return None

    def get_uuid_by_name(self, normalized_name: str) -> Optional[str]:
        """Get UUID from normalized device name."""
        return self._name_to_uuid.get(normalized_name)

    def get_device_by_name(self, normalized_name: str) -> Optional[Dict]:
        """Get device info by normalized name."""
        uuid = self.get_uuid_by_name(normalized_name)
        if uuid:
            return self.get_device_by_uuid(uuid)
        return None

    def get_chromecast(self, uuid: str):
        """Get a connected Chromecast object by UUID."""
        # Check if we have it cached
        if uuid in self._chromecasts_cache:
            return self._chromecasts_cache[uuid]

        # If not cached, device might not have been discovered yet
        return None

    def get_device_status(self, uuid: str) -> Dict:
        """Get the current status of a Chromecast device."""
        cast = self.get_chromecast(uuid)
        if not cast:
            return {'error': 'Device not found'}

        try:
            media_controller = cast.media_controller
            status = media_controller.status

            return {
                'app_id': cast.app_id,
                'app_display_name': cast.app_display_name,
                'volume_level': cast.status.volume_level,
                'volume_muted': cast.status.volume_muted,
                'is_idle': cast.is_idle,
                'media_status': {
                    'state': status.player_state if status else 'UNKNOWN',
                    'title': status.title if status else None,
                    'artist': status.artist if status else None,
                    'album_name': status.album_name if status else None,
                    'album_artist': status.album_artist if status else None,
                    'track_number': status.track if status else None,
                    'images': [{'url': img.url} for img in status.images] if status and status.images else [],
                    'content_type': status.content_type if status else None,
                    'duration': status.duration if status else None,
                    'current_time': status.current_time if status else None,
                    'supports_pause': status.supports_pause if status else False,
                    'supports_seek': status.supports_seek if status else False,
                    'supports_skip_forward': status.supports_skip_forward if status else False,
                    'supports_skip_backward': status.supports_skip_backward if status else False,
                } if media_controller else None
            }
        except Exception as e:
            return {'error': f'Failed to get status: {str(e)}'}

    def play(self, uuid: str) -> Dict:
        """Resume playback."""
        cast = self.get_chromecast(uuid)
        if not cast:
            return {'success': False, 'error': 'Device not found'}
        try:
            cast.media_controller.play()
            return {'success': True}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def pause(self, uuid: str) -> Dict:
        """Pause playback."""
        cast = self.get_chromecast(uuid)
        if not cast:
            return {'success': False, 'error': 'Device not found'}
        try:
            cast.media_controller.pause()
            return {'success': True}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def stop(self, uuid: str) -> Dict:
        """Stop playback."""
        cast = self.get_chromecast(uuid)
        if not cast:
            return {'success': False, 'error': 'Device not found'}
        try:
            cast.media_controller.stop()
            return {'success': True}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def skip_forward(self, uuid: str) -> Dict:
        """Skip to next track."""
        cast = self.get_chromecast(uuid)
        if not cast:
            return {'success': False, 'error': 'Device not found'}
        try:
            cast.media_controller.queue_next()
            return {'success': True}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def skip_backward(self, uuid: str) -> Dict:
        """Skip to previous track."""
        cast = self.get_chromecast(uuid)
        if not cast:
            return {'success': False, 'error': 'Device not found'}
        try:
            cast.media_controller.queue_prev()
            return {'success': True}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def set_volume(self, uuid: str, volume: float) -> Dict:
        """Set volume level (0.0 to 1.0)."""
        cast = self.get_chromecast(uuid)
        if not cast:
            return {'success': False, 'error': 'Device not found'}
        try:
            cast.set_volume(volume)
            return {'success': True}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def toggle_mute(self, uuid: str) -> Dict:
        """Toggle mute status."""
        cast = self.get_chromecast(uuid)
        if not cast:
            return {'success': False, 'error': 'Device not found'}
        try:
            cast.set_volume_muted(not cast.status.volume_muted)
            return {'success': True}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def play_url(self, uuid: str, url: str, content_type: str = 'audio/mpeg', title: str = None) -> Dict:
        """Play a media URL on the device."""
        cast = self.get_chromecast(uuid)
        if not cast:
            return {'success': False, 'error': 'Device not found'}
        try:
            media_controller = cast.media_controller
            media_controller.play_media(url, content_type, title=title)
            media_controller.block_until_active()
            return {'success': True}
        except Exception as e:
            return {'success': False, 'error': str(e)}


# Global service instance
chromecast_service = ChromecastService()
