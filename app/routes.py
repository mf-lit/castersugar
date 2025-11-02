from flask import Blueprint, render_template, jsonify, request
from app.chromecast_service import chromecast_service
from app.dynamodb_service import dynamodb_service
import uuid as uuid_lib

bp = Blueprint('main', __name__)


@bp.route('/')
def index():
    """Redirect to devices page."""
    return render_template('index.html')


@bp.route('/devices')
def devices():
    """Display the devices page."""
    return render_template('devices.html')


@bp.route('/device/<identifier>')
def device_detail(identifier):
    """Display the device detail page (supports UUID or name)."""
    # Try UUID first
    device = chromecast_service.get_device_by_uuid(identifier)

    # If not found, try normalized name
    if not device:
        device = chromecast_service.get_device_by_name(identifier)

    if not device:
        return "Device not found", 404

    return render_template('device_detail.html', device=device)


@bp.route('/api/devices')
def api_devices():
    """API endpoint to get Chromecast devices."""
    force_refresh = request.args.get('refresh', 'false').lower() == 'true'

    try:
        devices = chromecast_service.discover_devices(force_refresh=force_refresh)
        cache_info = chromecast_service.get_cache_info()

        return jsonify({
            'success': True,
            'devices': devices,
            'cache_info': cache_info
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


def resolve_device_identifier(identifier: str) -> str:
    """Resolve device identifier (UUID or name) to UUID."""
    # Try as UUID first
    device = chromecast_service.get_device_by_uuid(identifier)
    if device:
        return identifier

    # Try as normalized name
    uuid = chromecast_service.get_uuid_by_name(identifier)
    if uuid:
        return uuid

    return identifier  # Return as-is if not found (will fail downstream)


@bp.route('/api/device/<identifier>/status')
def api_device_status(identifier):
    """API endpoint to get device status (supports UUID or name)."""
    try:
        uuid = resolve_device_identifier(identifier)
        status = chromecast_service.get_device_status(uuid)
        return jsonify(status)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@bp.route('/api/device/<identifier>/play', methods=['POST'])
def api_play(identifier):
    """API endpoint to play (supports UUID or name)."""
    uuid = resolve_device_identifier(identifier)
    return jsonify(chromecast_service.play(uuid))


@bp.route('/api/device/<identifier>/pause', methods=['POST'])
def api_pause(identifier):
    """API endpoint to pause (supports UUID or name)."""
    uuid = resolve_device_identifier(identifier)
    return jsonify(chromecast_service.pause(uuid))


@bp.route('/api/device/<identifier>/stop', methods=['POST'])
def api_stop(identifier):
    """API endpoint to stop (supports UUID or name)."""
    uuid = resolve_device_identifier(identifier)
    return jsonify(chromecast_service.stop(uuid))


@bp.route('/api/device/<identifier>/next', methods=['POST'])
def api_next(identifier):
    """API endpoint to skip forward (supports UUID or name)."""
    uuid = resolve_device_identifier(identifier)
    return jsonify(chromecast_service.skip_forward(uuid))


@bp.route('/api/device/<identifier>/previous', methods=['POST'])
def api_previous(identifier):
    """API endpoint to skip backward (supports UUID or name)."""
    uuid = resolve_device_identifier(identifier)
    return jsonify(chromecast_service.skip_backward(uuid))


@bp.route('/api/device/<identifier>/volume', methods=['POST'])
def api_volume(identifier):
    """API endpoint to set volume (supports UUID or name)."""
    uuid = resolve_device_identifier(identifier)
    data = request.get_json()
    volume = float(data.get('volume', 0.5))
    return jsonify(chromecast_service.set_volume(uuid, volume))


@bp.route('/api/device/<identifier>/mute', methods=['POST'])
def api_mute(identifier):
    """API endpoint to toggle mute (supports UUID or name)."""
    uuid = resolve_device_identifier(identifier)
    return jsonify(chromecast_service.toggle_mute(uuid))


# Radio page routes
@bp.route('/radio')
def radio():
    """Display the radio page."""
    return render_template('radio.html')


@bp.route('/api/radio/stations')
def api_get_stations():
    """Get all radio stations."""
    try:
        stations = dynamodb_service.get_all_stations()
        return jsonify({'success': True, 'stations': stations})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@bp.route('/api/radio/stations', methods=['POST'])
def api_create_station():
    """Create a new radio station."""
    try:
        data = request.get_json()
        station_id = str(uuid_lib.uuid4())
        result = dynamodb_service.create_station(
            station_id=station_id,
            name=data['name'],
            url=data['url'],
            icon_url=data.get('icon_url', '')
        )
        return jsonify(result)
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@bp.route('/api/radio/stations/<station_id>', methods=['PUT'])
def api_update_station(station_id):
    """Update a radio station."""
    try:
        data = request.get_json()
        result = dynamodb_service.update_station(
            station_id=station_id,
            name=data['name'],
            url=data['url'],
            icon_url=data.get('icon_url', '')
        )
        return jsonify(result)
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@bp.route('/api/radio/stations/<station_id>', methods=['DELETE'])
def api_delete_station(station_id):
    """Delete a radio station."""
    try:
        result = dynamodb_service.delete_station(station_id)
        return jsonify(result)
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@bp.route('/api/radio/play', methods=['POST'])
def api_radio_play():
    """Play a radio station on a device."""
    try:
        data = request.get_json()
        device_identifier = data['device']
        station_url = data['url']
        station_name = data.get('name', 'Radio')

        # Resolve device identifier to UUID
        uuid = resolve_device_identifier(device_identifier)

        # Play the URL
        result = chromecast_service.play_url(uuid, station_url, title=station_name)

        # Save last selected device if successful
        if result.get('success'):
            dynamodb_service.set_last_selected_device(device_identifier)

        return jsonify(result)
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@bp.route('/api/radio/stop', methods=['POST'])
def api_radio_stop():
    """Stop playback on a device."""
    try:
        data = request.get_json()
        device_identifier = data['device']
        uuid = resolve_device_identifier(device_identifier)
        return jsonify(chromecast_service.stop(uuid))
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@bp.route('/api/radio/last-device')
def api_get_last_device():
    """Get the last selected device."""
    try:
        device = dynamodb_service.get_last_selected_device()
        return jsonify({'success': True, 'device': device})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@bp.route('/api/radio/logo-cache', methods=['POST'])
def api_cache_logo():
    """Cache a logo from URL."""
    try:
        data = request.get_json()
        url = data.get('url')
        force_refresh = data.get('force_refresh', False)

        if not url:
            return jsonify({'success': False, 'error': 'URL is required'}), 400

        result = dynamodb_service.cache_logo(url, force_refresh=force_refresh)
        return jsonify(result)
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
