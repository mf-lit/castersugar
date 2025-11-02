import boto3
from typing import List, Dict, Optional
from botocore.exceptions import ClientError
import time
import requests
import base64


class DynamoDBService:
    """Service for managing radio state and stations in DynamoDB."""

    def __init__(self, endpoint_url: str = 'http://192.168.1.1:8001'):
        self.dynamodb = boto3.resource(
            'dynamodb',
            endpoint_url=endpoint_url,
            region_name='us-east-1',
            aws_access_key_id='dummy',
            aws_secret_access_key='dummy'
        )
        self.state_table_name = 'castersugar_state'
        self.stations_table_name = 'castersugar_stations'
        self.logo_cache_table_name = 'castersugar_logo_cache'
        self._ensure_tables()

    def _ensure_tables(self):
        """Create tables if they don't exist."""
        try:
            # Create state table
            try:
                self.state_table = self.dynamodb.Table(self.state_table_name)
                self.state_table.load()
            except ClientError:
                self.state_table = self.dynamodb.create_table(
                    TableName=self.state_table_name,
                    KeySchema=[
                        {'AttributeName': 'key', 'KeyType': 'HASH'}
                    ],
                    AttributeDefinitions=[
                        {'AttributeName': 'key', 'AttributeType': 'S'}
                    ],
                    BillingMode='PAY_PER_REQUEST'
                )
                self.state_table.wait_until_exists()

            # Create stations table
            try:
                self.stations_table = self.dynamodb.Table(self.stations_table_name)
                self.stations_table.load()
            except ClientError:
                self.stations_table = self.dynamodb.create_table(
                    TableName=self.stations_table_name,
                    KeySchema=[
                        {'AttributeName': 'id', 'KeyType': 'HASH'}
                    ],
                    AttributeDefinitions=[
                        {'AttributeName': 'id', 'AttributeType': 'S'}
                    ],
                    BillingMode='PAY_PER_REQUEST'
                )
                self.stations_table.wait_until_exists()

            # Create logo cache table with TTL
            try:
                self.logo_cache_table = self.dynamodb.Table(self.logo_cache_table_name)
                self.logo_cache_table.load()
            except ClientError:
                self.logo_cache_table = self.dynamodb.create_table(
                    TableName=self.logo_cache_table_name,
                    KeySchema=[
                        {'AttributeName': 'url', 'KeyType': 'HASH'}
                    ],
                    AttributeDefinitions=[
                        {'AttributeName': 'url', 'AttributeType': 'S'}
                    ],
                    BillingMode='PAY_PER_REQUEST'
                )
                self.logo_cache_table.wait_until_exists()

                # Enable TTL on the cache table
                try:
                    self.dynamodb.meta.client.update_time_to_live(
                        TableName=self.logo_cache_table_name,
                        TimeToLiveSpecification={
                            'Enabled': True,
                            'AttributeName': 'ttl'
                        }
                    )
                except Exception as ttl_error:
                    print(f"Warning: Could not enable TTL on logo cache: {ttl_error}")

        except Exception as e:
            print(f"Warning: Could not initialize DynamoDB tables: {e}")
            # Tables might already exist, try to use them
            self.state_table = self.dynamodb.Table(self.state_table_name)
            self.stations_table = self.dynamodb.Table(self.stations_table_name)
            self.logo_cache_table = self.dynamodb.Table(self.logo_cache_table_name)

    # State management
    def get_last_selected_device(self) -> Optional[str]:
        """Get the last selected device identifier."""
        try:
            response = self.state_table.get_item(Key={'key': 'last_selected_device'})
            return response.get('Item', {}).get('value')
        except Exception as e:
            print(f"Error getting last selected device: {e}")
            return None

    def set_last_selected_device(self, device_identifier: str):
        """Set the last selected device identifier."""
        try:
            self.state_table.put_item(Item={
                'key': 'last_selected_device',
                'value': device_identifier
            })
        except Exception as e:
            print(f"Error setting last selected device: {e}")

    # Station management
    def get_all_stations(self) -> List[Dict]:
        """Get all radio stations."""
        try:
            response = self.stations_table.scan()
            stations = response.get('Items', [])
            # Sort by name
            stations.sort(key=lambda x: x.get('name', '').lower())
            return stations
        except Exception as e:
            print(f"Error getting stations: {e}")
            return []

    def get_station(self, station_id: str) -> Optional[Dict]:
        """Get a specific station by ID."""
        try:
            response = self.stations_table.get_item(Key={'id': station_id})
            return response.get('Item')
        except Exception as e:
            print(f"Error getting station {station_id}: {e}")
            return None

    def create_station(self, station_id: str, name: str, url: str, icon_url: str) -> Dict:
        """Create a new radio station."""
        try:
            item = {
                'id': station_id,
                'name': name,
                'url': url,
                'icon_url': icon_url
            }
            self.stations_table.put_item(Item=item)
            return {'success': True, 'station': item}
        except Exception as e:
            print(f"Error creating station: {e}")
            return {'success': False, 'error': str(e)}

    def update_station(self, station_id: str, name: str, url: str, icon_url: str) -> Dict:
        """Update an existing radio station."""
        try:
            item = {
                'id': station_id,
                'name': name,
                'url': url,
                'icon_url': icon_url
            }
            self.stations_table.put_item(Item=item)
            return {'success': True, 'station': item}
        except Exception as e:
            print(f"Error updating station: {e}")
            return {'success': False, 'error': str(e)}

    def delete_station(self, station_id: str) -> Dict:
        """Delete a radio station."""
        try:
            self.stations_table.delete_item(Key={'id': station_id})
            return {'success': True}
        except Exception as e:
            print(f"Error deleting station: {e}")
            return {'success': False, 'error': str(e)}

    # Logo caching methods
    def get_cached_logo(self, url: str) -> Optional[Dict]:
        """Get a cached logo by URL."""
        try:
            response = self.logo_cache_table.get_item(Key={'url': url})
            item = response.get('Item')

            if not item:
                return None

            # Check if expired (even though DynamoDB TTL should handle this)
            current_time = int(time.time())
            if item.get('ttl', 0) < current_time:
                return None

            return {
                'data': item.get('data'),
                'content_type': item.get('content_type'),
                'cached_at': item.get('cached_at')
            }
        except Exception as e:
            print(f"Error getting cached logo: {e}")
            return None

    def cache_logo(self, url: str, force_refresh: bool = False) -> Dict:
        """Fetch and cache a logo from URL."""
        try:
            # Check if already cached and not forcing refresh
            if not force_refresh:
                cached = self.get_cached_logo(url)
                if cached:
                    return {
                        'success': True,
                        'data': cached['data'],
                        'content_type': cached['content_type'],
                        'from_cache': True
                    }

            # Fetch the logo
            response = requests.get(url, timeout=10)
            response.raise_for_status()

            # Encode as base64
            logo_data = base64.b64encode(response.content).decode('utf-8')
            content_type = response.headers.get('Content-Type', 'image/jpeg')

            # Calculate TTL (28 days from now)
            ttl = int(time.time()) + (28 * 24 * 60 * 60)

            # Cache in DynamoDB
            self.logo_cache_table.put_item(Item={
                'url': url,
                'data': logo_data,
                'content_type': content_type,
                'cached_at': int(time.time()),
                'ttl': ttl
            })

            return {
                'success': True,
                'data': logo_data,
                'content_type': content_type,
                'from_cache': False
            }

        except Exception as e:
            print(f"Error caching logo from {url}: {e}")
            return {'success': False, 'error': str(e)}


# Global service instance
dynamodb_service = DynamoDBService()
