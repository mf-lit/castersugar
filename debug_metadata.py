#!/usr/bin/env python3
"""Debug script to inspect all available metadata from a Chromecast."""
import pychromecast
import time
import json

# Discover devices
print("Discovering Chromecasts...")
chromecasts, browser = pychromecast.get_listed_chromecasts(friendly_names=["Kitchen HiFi"])

if not chromecasts:
    print("No Chromecast found with name 'Kitchen HiFi'")
    exit(1)

cast = chromecasts[0]
cast.wait()

print(f"\nConnected to: {cast.name}")
print(f"Status: {cast.status}")
print(f"App ID: {cast.app_id}")
print(f"App Display Name: {cast.app_display_name}")
print(f"Is Idle: {cast.is_idle}")

# Check cast.status attributes
print("\n=== Cast Status Attributes ===")
for attr in dir(cast.status):
    if not attr.startswith('_'):
        try:
            value = getattr(cast.status, attr)
            if not callable(value):
                print(f"cast.status.{attr}: {value}")
        except Exception as e:
            print(f"cast.status.{attr}: <error: {e}>")

# Get media controller
mc = cast.media_controller
print(f"\nMedia Controller Status: {mc.status}")

if mc.status:
    print("\n=== All Status Attributes ===")
    status_dict = {}
    for attr in dir(mc.status):
        if not attr.startswith('_'):
            try:
                value = getattr(mc.status, attr)
                if not callable(value):
                    status_dict[attr] = value
                    print(f"{attr}: {value}")
            except Exception as e:
                print(f"{attr}: <error: {e}>")

    print("\n=== JSON Representation ===")
    # Try to serialize what we can
    serializable = {}
    for key, value in status_dict.items():
        try:
            json.dumps(value)
            serializable[key] = value
        except:
            serializable[key] = str(value)

    print(json.dumps(serializable, indent=2))

    # Look specifically for "Now Playing" metadata
    print("\n=== Looking for 'Now Playing' metadata ===")
    if hasattr(mc.status, 'media_metadata'):
        print(f"media_metadata: {mc.status.media_metadata}")
        if 'now_playing' in str(mc.status.media_metadata).lower():
            print("Found 'now_playing' in media_metadata!")

    if hasattr(mc.status, 'media_custom_data'):
        print(f"media_custom_data: {mc.status.media_custom_data}")
        if 'now_playing' in str(mc.status.media_custom_data).lower():
            print("Found 'now_playing' in media_custom_data!")

    # Check all attributes for "now" or "playing"
    print("\n=== Attributes containing 'now' or 'playing' ===")
    for attr in dir(mc.status):
        if not attr.startswith('_'):
            attr_lower = attr.lower()
            if 'now' in attr_lower or 'playing' in attr_lower or 'current' in attr_lower:
                try:
                    value = getattr(mc.status, attr)
                    if not callable(value):
                        print(f"{attr}: {value}")
                except:
                    pass

browser.stop_discovery()
