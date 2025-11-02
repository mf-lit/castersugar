document.addEventListener('DOMContentLoaded', function() {
    const refreshBtn = document.getElementById('refresh-btn');
    const loadingEl = document.getElementById('loading');
    const errorEl = document.getElementById('error');
    const devicesListEl = document.getElementById('devices-list');
    const cacheInfoEl = document.getElementById('cache-info');

    // Load devices on page load
    loadDevices(false);

    // Refresh button click handler
    refreshBtn.addEventListener('click', function() {
        loadDevices(true);
    });

    async function loadDevices(forceRefresh) {
        // Update UI state
        refreshBtn.disabled = true;
        loadingEl.style.display = 'block';
        errorEl.style.display = 'none';

        if (forceRefresh) {
            refreshBtn.textContent = 'Refreshing...';
        }

        try {
            const url = `/api/devices${forceRefresh ? '?refresh=true' : ''}`;
            const response = await fetch(url);
            const data = await response.json();

            if (!data.success) {
                throw new Error(data.error || 'Failed to load devices');
            }

            displayDevices(data.devices);
            displayCacheInfo(data.cache_info);

        } catch (error) {
            errorEl.textContent = `Error: ${error.message}`;
            errorEl.style.display = 'block';
            console.error('Error loading devices:', error);
        } finally {
            loadingEl.style.display = 'none';
            refreshBtn.disabled = false;
            refreshBtn.textContent = 'Refresh Devices';
        }
    }

    function displayCacheInfo(cacheInfo) {
        if (!cacheInfo.cached) {
            cacheInfoEl.textContent = 'No cached data';
            return;
        }

        const lastDiscovery = new Date(cacheInfo.last_discovery);

        cacheInfoEl.innerHTML = `
            <strong>Cache Status:</strong>
            Last discovery: ${lastDiscovery.toLocaleString()} |
            ${cacheInfo.device_count} device(s) in cache |
            <span style="color: #27ae60;">Cached indefinitely</span>
        `;
    }

    function displayDevices(devices) {
        if (devices.length === 0) {
            devicesListEl.innerHTML = `
                <div class="no-devices">
                    <h3>No devices found</h3>
                    <p>Make sure your Chromecast devices are powered on and connected to the same network.</p>
                </div>
            `;
            return;
        }

        // Sort devices: Audio devices first
        devices.sort((a, b) => {
            if (a.is_audio_device && !b.is_audio_device) return -1;
            if (!a.is_audio_device && b.is_audio_device) return 1;
            return a.name.localeCompare(b.name);
        });

        devicesListEl.innerHTML = devices.map(device => createDeviceCard(device)).join('');
    }

    function createDeviceCard(device) {
        const isAudio = device.is_audio_device;
        const icon = isAudio ? '🔊' : '📺';
        const badgeClass = isAudio ? 'badge-audio' : 'badge-video';
        const badgeText = isAudio ? 'Audio' : 'Video';
        const cardClass = isAudio ? 'audio-device' : '';

        return `
            <a href="/device/${encodeURIComponent(device.normalized_name)}" class="device-card-link">
                <div class="device-card ${cardClass}">
                    <div class="device-header">
                        <div class="device-icon">${icon}</div>
                        <div class="device-info">
                            <h3>${escapeHtml(device.name)}</h3>
                            <div class="device-model">${escapeHtml(device.model_name || 'Unknown Model')}</div>
                            <span class="device-badge ${badgeClass}">${badgeText}</span>
                        </div>
                    </div>
                    <div class="device-details">
                        <div class="device-detail">
                            <span class="detail-label">Host:</span>
                            <span class="detail-value">${escapeHtml(device.host)}:${device.port}</span>
                        </div>
                        <div class="device-detail">
                            <span class="detail-label">Manufacturer:</span>
                            <span class="detail-value">${escapeHtml(device.manufacturer)}</span>
                        </div>
                        <div class="device-detail">
                            <span class="detail-label">Type:</span>
                            <span class="detail-value">${escapeHtml(device.cast_type)}</span>
                        </div>
                    </div>
                </div>
            </a>
        `;
    }

    function escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
});
