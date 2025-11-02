#!/usr/bin/env python3
"""Test script to listen for media status updates."""
import pychromecast
import time

class StatusListener:
    def __init__(self, name):
        self.name = name

    def new_cast_status(self, status):
        print(f"\n[{self.name}] NEW CAST STATUS:")
        print(f"  status_text: {status.status_text if hasattr(status, 'status_text') else 'N/A'}")
        print(f"  app: {status.display_name if hasattr(status, 'display_name') else 'N/A'}")

    def new_media_status(self, status):
        print(f"\n[{self.name}] NEW MEDIA STATUS:")
        print(f"  title: {status.title}")
        print(f"  artist: {status.artist}")
        print(f"  album: {status.album_name}")
        print(f"  player_state: {status.player_state}")
        print(f"  media_metadata: {status.media_metadata}")
        print(f"  media_custom_data: {status.media_custom_data}")

print("Discovering Chromecasts...")
chromecasts, browser = pychromecast.get_listed_chromecasts(friendly_names=["Kitchen HiFi"])

if not chromecasts:
    print("No Chromecast found")
    exit(1)

cast = chromecasts[0]
cast.wait()

print(f"\nConnected to: {cast.name}")
print("Registering status listeners...")

# Register listeners
listener = StatusListener("Kitchen HiFi")
cast.register_status_listener(listener)
cast.media_controller.register_status_listener(listener)

print("\nListening for status updates for 60 seconds...")
print("(Play different songs/stations to see metadata updates)\n")

try:
    time.sleep(60)
except KeyboardInterrupt:
    print("\nStopped")

browser.stop_discovery()
