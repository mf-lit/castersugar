#!/usr/bin/env python3
"""Import radio stations from streams.json into DynamoDB."""

import json
import uuid
from app.dynamodb_service import dynamodb_service

def import_stations():
    """Import stations from streams.json."""

    # Read the streams.json file
    with open('streams.json', 'r') as f:
        data = json.load(f)

    streams = data.get('Streams', [])

    print(f"Found {len(streams)} stations to import...")

    success_count = 0
    error_count = 0

    for stream in streams:
        name = stream.get('Name', '')
        stream_url = stream.get('StreamURL', '').replace('\\/', '/')
        logo_url = stream.get('LogoURL', '').replace('\\/', '/')
        guid = stream.get('GUID', '')

        if not name or not stream_url:
            print(f"Skipping invalid entry: {stream}")
            error_count += 1
            continue

        print(f"Importing: {name}")

        # Use the GUID from the file, or generate a new one if it's the null GUID
        station_id = guid if guid != "00000000-0000-0000-0000-000000000000" else str(uuid.uuid4())

        try:
            result = dynamodb_service.create_station(
                station_id=station_id,
                name=name,
                url=stream_url,
                icon_url=logo_url
            )

            if result.get('success'):
                success_count += 1
                print(f"  ✓ Success")
            else:
                error_count += 1
                print(f"  ✗ Failed: {result.get('error')}")
        except Exception as e:
            error_count += 1
            print(f"  ✗ Error: {e}")

    print(f"\nImport complete!")
    print(f"  Successfully imported: {success_count}")
    print(f"  Failed: {error_count}")
    print(f"  Total: {len(streams)}")

if __name__ == '__main__':
    import_stations()
