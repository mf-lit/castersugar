#!/usr/bin/env python3
"""Test ICY metadata with SomaFM Groove Salad."""
import requests
import time

BASE_URL = "http://127.0.0.1:5000"
SOMAFM_URL = "http://ice1.somafm.com/groovesalad-256-mp3"

# Get devices
print("Getting devices...")
resp = requests.get(f"{BASE_URL}/api/devices")
devices = resp.json()['devices']
print(f"Found {len(devices)} devices")

if devices:
    device = devices[0]
    print(f"\nSelected device: {device['name']}")
    print(f"UUID: {device['uuid']}")

    # Play SomaFM Groove Salad
    print(f"\n=== Playing SomaFM Groove Salad ===")
    resp = requests.post(f"{BASE_URL}/api/radio/play", json={
        'device': device['uuid'],
        'url': SOMAFM_URL,
        'name': 'SomaFM Groove Salad'
    })
    result = resp.json()
    print(f"Play result: {result}")

    # Wait for ICY metadata to be fetched (up to 20 seconds)
    for i in range(4):
        wait_time = 5 * (i + 1)
        print(f"\nWaiting {wait_time} seconds total...")
        time.sleep(5)

        print(f"=== Checking ICY metadata (attempt {i+1}) ===")
        resp = requests.get(f"{BASE_URL}/api/device/{device['uuid']}/icy-metadata")
        result = resp.json()

        if result.get('success'):
            metadata = result.get('metadata', {})
            print(f"SUCCESS! Got metadata:")
            print(f"  Artist: {metadata.get('artist')}")
            print(f"  Title: {metadata.get('title')}")
            print(f"  Raw: {metadata.get('raw')}")
            break
        else:
            print(f"  Error: {result.get('error')}")
    else:
        print("\nFailed to get metadata after 20 seconds")
