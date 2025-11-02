#!/usr/bin/env python3
"""Test script to verify ICY metadata tracking."""
import requests
import time

BASE_URL = "http://127.0.0.1:5000"

# Get stations
print("Getting stations...")
resp = requests.get(f"{BASE_URL}/api/radio/stations")
stations = resp.json()['stations']
print(f"Found {len(stations)} stations")

if stations:
    station = stations[0]
    print(f"\nSelected station: {station['name']}")
    print(f"URL: {station['url']}")

    # Get devices
    print("\nGetting devices...")
    resp = requests.get(f"{BASE_URL}/api/devices")
    devices = resp.json()['devices']
    print(f"Found {len(devices)} devices")

    if devices:
        device = devices[0]
        print(f"\nSelected device: {device['name']}")
        print(f"UUID: {device['uuid']}")
        print(f"Normalized name: {device['normalized_name']}")

        # Play station
        print("\n=== Playing station ===")
        resp = requests.post(f"{BASE_URL}/api/radio/play", json={
            'device': device['normalized_name'],
            'url': station['url'],
            'name': station['name']
        })
        result = resp.json()
        print(f"Play result: {result}")

        # Wait a bit
        print("\nWaiting 5 seconds...")
        time.sleep(5)

        # Try to get ICY metadata using normalized name
        print(f"\n=== Checking ICY metadata (normalized name: {device['normalized_name']}) ===")
        resp = requests.get(f"{BASE_URL}/api/device/{device['normalized_name']}/icy-metadata")
        result = resp.json()
        print(f"ICY metadata result: {result}")

        # Try to get ICY metadata using UUID
        print(f"\n=== Checking ICY metadata (UUID: {device['uuid']}) ===")
        resp = requests.get(f"{BASE_URL}/api/device/{device['uuid']}/icy-metadata")
        result = resp.json()
        print(f"ICY metadata result: {result}")
