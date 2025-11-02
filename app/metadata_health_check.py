"""Health check service for monitoring metadata collection and cleanup."""
import threading
import time
import sys
from typing import Optional


class MetadataHealthCheckService:
    """Service for monitoring and cleaning up stale metadata monitoring threads."""

    def __init__(self, chromecast_service, dynamodb_service, icy_metadata_service, bbc_metadata_service):
        """
        Initialize the health check service.

        Args:
            chromecast_service: ChromecastService instance
            dynamodb_service: DynamoDBService instance
            icy_metadata_service: ICYMetadataService instance
            bbc_metadata_service: BBCMetadataService instance
        """
        self.chromecast_service = chromecast_service
        self.dynamodb_service = dynamodb_service
        self.icy_metadata_service = icy_metadata_service
        self.bbc_metadata_service = bbc_metadata_service
        self.stop_event = threading.Event()
        self.health_check_thread: Optional[threading.Thread] = None
        self.check_interval_seconds = 60  # Check every 60 seconds
        self.max_monitoring_duration_seconds = 600  # 10 minutes

    def start(self):
        """Start the health check service."""
        if self.health_check_thread and self.health_check_thread.is_alive():
            print("Health check service is already running")
            return

        self.stop_event.clear()
        self.health_check_thread = threading.Thread(
            target=self._health_check_loop,
            daemon=True
        )
        self.health_check_thread.start()
        print("Metadata health check service started")

    def stop(self):
        """Stop the health check service."""
        if self.health_check_thread and self.health_check_thread.is_alive():
            self.stop_event.set()
            self.health_check_thread.join(timeout=5)
            print("Metadata health check service stopped")

    def _health_check_loop(self):
        """Main loop for health checking."""
        while not self.stop_event.is_set():
            try:
                self._perform_health_check()
            except Exception as e:
                print(f"Error in metadata health check: {e}")

            # Wait for the next check interval or until stopped
            self.stop_event.wait(self.check_interval_seconds)

    def _perform_health_check(self):
        """Perform a health check on all monitored streams."""
        print("[HEALTH CHECK] Starting metadata health check...", flush=True)

        # Get all device streams from DynamoDB
        device_streams = self.dynamodb_service.get_all_device_streams()
        print(f"[HEALTH CHECK] Found {len(device_streams)} tracked device streams", flush=True)

        # Check each device
        for device_uuid, stream_url in list(device_streams.items()):
            try:
                self._check_device_stream(device_uuid, stream_url)
            except Exception as e:
                print(f"[HEALTH CHECK] Error checking device {device_uuid}: {e}")

        # Check all active monitoring streams for timeout (10 minutes)
        self._check_monitoring_timeouts()

        print("[HEALTH CHECK] Metadata health check completed", flush=True)

    def _check_device_stream(self, device_uuid: str, stream_url: str):
        """Check if a device is still playing and cleanup if not."""
        # Get device status from Chromecast
        device_status = self.chromecast_service.get_device_status(device_uuid)

        if 'error' in device_status:
            print(f"[HEALTH CHECK] Device {device_uuid} not found, cleaning up stream tracking")
            self._cleanup_stream(device_uuid, stream_url, "device not found")
            return

        # Check if device is idle
        is_idle = device_status.get('is_idle', True)
        player_state = device_status.get('media_status', {}).get('state', 'UNKNOWN') if device_status.get('media_status') else 'UNKNOWN'

        print(f"[HEALTH CHECK] Device {device_uuid}: is_idle={is_idle}, player_state={player_state}")

        # If device is idle or not playing, stop monitoring
        if is_idle or player_state in ['IDLE', 'UNKNOWN']:
            print(f"[HEALTH CHECK] Device {device_uuid} is idle, cleaning up")
            self._cleanup_stream(device_uuid, stream_url, "device idle")

    def _check_monitoring_timeouts(self):
        """Check all active monitoring streams and stop those exceeding the timeout."""
        # Check ICY metadata service
        icy_streams = self.icy_metadata_service.get_active_streams()
        for stream_url, duration in icy_streams.items():
            if duration > self.max_monitoring_duration_seconds:
                print(f"[HEALTH CHECK] ICY stream {stream_url} exceeded timeout ({duration:.0f}s), stopping monitoring")
                self.icy_metadata_service.stop_monitoring(stream_url)

                # Find and clear the device stream mapping
                self._clear_device_mapping_for_stream(stream_url)

        # Check BBC metadata service
        bbc_streams = self.bbc_metadata_service.get_active_streams()
        for stream_url, duration in bbc_streams.items():
            if duration > self.max_monitoring_duration_seconds:
                print(f"[HEALTH CHECK] BBC stream {stream_url} exceeded timeout ({duration:.0f}s), stopping monitoring")
                self.bbc_metadata_service.stop_monitoring(stream_url)

                # Find and clear the device stream mapping
                self._clear_device_mapping_for_stream(stream_url)

    def _cleanup_stream(self, device_uuid: str, stream_url: str, reason: str):
        """Clean up monitoring for a stream."""
        print(f"[HEALTH CHECK] Cleaning up stream monitoring for device {device_uuid}: {reason}")

        # Stop monitoring on both services (safe to call even if not monitoring)
        self.icy_metadata_service.stop_monitoring(stream_url)
        self.bbc_metadata_service.stop_monitoring(stream_url)

        # Clear the device stream mapping
        self.dynamodb_service.clear_device_stream(device_uuid)

    def _clear_device_mapping_for_stream(self, stream_url: str):
        """Find and clear any device mappings for a given stream URL."""
        device_streams = self.dynamodb_service.get_all_device_streams()
        for device_uuid, mapped_stream_url in device_streams.items():
            if mapped_stream_url == stream_url:
                print(f"[HEALTH CHECK] Clearing device mapping for {device_uuid}")
                self.dynamodb_service.clear_device_stream(device_uuid)


# Global instance (will be initialized in app/__init__.py)
metadata_health_check_service: Optional[MetadataHealthCheckService] = None
