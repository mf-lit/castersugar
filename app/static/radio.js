document.addEventListener('DOMContentLoaded', function() {
    let stations = [];
    let selectedStation = null;
    let playingStation = null;

    const elements = {
        deviceSelect: document.getElementById('device-select'),
        playBtn: document.getElementById('play-btn'),
        stopBtn: document.getElementById('stop-btn'),
        stationsList: document.getElementById('stations-list'),
        loadingStations: document.getElementById('loading-stations'),
        addStationBtn: document.getElementById('add-station-btn'),
        stationModal: document.getElementById('station-modal'),
        modalBackdrop: document.getElementById('modal-backdrop'),
        stationForm: document.getElementById('station-form'),
        modalTitle: document.getElementById('modal-title'),
        stationId: document.getElementById('station-id'),
        stationName: document.getElementById('station-name'),
        stationUrl: document.getElementById('station-url'),
        stationIcon: document.getElementById('station-icon'),
        refreshIconBtn: document.getElementById('refresh-icon-btn'),
        closeModal: document.getElementById('close-modal'),
        cancelBtn: document.getElementById('cancel-btn'),
        errorMessage: document.getElementById('error-message'),
        volumeSlider: document.getElementById('volume-slider'),
        volumeIcon: document.getElementById('volume-icon'),
        nowPlaying: document.getElementById('now-playing'),
        nowPlayingStation: document.getElementById('now-playing-station')
    };

    // Initialize
    loadDevices();
    loadStations();
    loadLastDevice();

    // Event listeners
    elements.playBtn.addEventListener('click', playStation);
    elements.stopBtn.addEventListener('click', stopPlayback);
    elements.addStationBtn.addEventListener('click', () => openModal());
    elements.closeModal.addEventListener('click', closeModal);
    elements.cancelBtn.addEventListener('click', closeModal);
    elements.modalBackdrop.addEventListener('click', closeModal);
    elements.stationForm.addEventListener('submit', saveStation);
    elements.deviceSelect.addEventListener('change', () => {
        updateControlButtons();
        updateVolumeSlider();
    });
    elements.refreshIconBtn.addEventListener('click', refreshIconCache);
    elements.volumeSlider.addEventListener('input', handleVolumeChange);
    elements.volumeIcon.addEventListener('click', toggleMute);

    async function loadDevices() {
        try {
            const response = await fetch('/api/devices');
            const data = await response.json();

            if (data.success) {
                elements.deviceSelect.innerHTML = '<option value="">Select a device...</option>';
                data.devices.forEach(device => {
                    const option = document.createElement('option');
                    option.value = device.normalized_name;
                    option.textContent = `${device.name} (${device.model_name})`;
                    elements.deviceSelect.appendChild(option);
                });
            }
        } catch (error) {
            showError(`Failed to load devices: ${error.message}`);
        }
    }

    async function loadLastDevice() {
        try {
            const response = await fetch('/api/radio/last-device');
            const data = await response.json();

            if (data.success && data.device) {
                elements.deviceSelect.value = data.device;
                updateControlButtons();
            }
        } catch (error) {
            // Silently fail - not critical
            console.error('Failed to load last device:', error);
        }
    }

    async function loadStations() {
        elements.loadingStations.style.display = 'block';

        try {
            const response = await fetch('/api/radio/stations');
            const data = await response.json();

            if (data.success) {
                stations = data.stations;
                renderStations();
            } else {
                showError(data.error || 'Failed to load stations');
            }
        } catch (error) {
            showError(`Failed to load stations: ${error.message}`);
        } finally {
            elements.loadingStations.style.display = 'none';
        }
    }

    function renderStations() {
        if (stations.length === 0) {
            elements.stationsList.innerHTML = `
                <div class="no-stations">
                    <p>No stations yet. Click "Add Station" to get started!</p>
                </div>
            `;
            return;
        }

        elements.stationsList.innerHTML = stations.map(station => `
            <div class="station-card ${selectedStation === station.id ? 'selected' : ''} ${playingStation === station.id ? 'playing' : ''}"
                 data-station-id="${station.id}">
                <div class="station-icon">
                    ${station.icon_url
                        ? `<img src="${escapeHtml(station.icon_url)}" alt="${escapeHtml(station.name)}">`
                        : '<span class="default-icon">📻</span>'
                    }
                </div>
                <div class="station-info">
                    <div class="station-name">${escapeHtml(station.name)}</div>
                </div>
                <div class="station-actions">
                    <button class="action-btn edit-btn" title="Edit" data-id="${station.id}">
                        <span>✏️</span>
                    </button>
                    <button class="action-btn delete-btn" title="Delete" data-id="${station.id}">
                        <span>🗑️</span>
                    </button>
                </div>
            </div>
        `).join('');

        // Add event listeners to station cards
        document.querySelectorAll('.station-card').forEach(card => {
            card.addEventListener('click', (e) => {
                if (!e.target.closest('.station-actions')) {
                    selectAndPlayStation(card.dataset.stationId);
                }
            });
        });

        // Add event listeners to action buttons
        document.querySelectorAll('.edit-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                e.stopPropagation();
                editStation(btn.dataset.id);
            });
        });

        document.querySelectorAll('.delete-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                e.stopPropagation();
                deleteStation(btn.dataset.id);
            });
        });
    }

    function selectStation(stationId) {
        selectedStation = stationId;
        renderStations();
        updateControlButtons();
    }

    function selectAndPlayStation(stationId) {
        selectedStation = stationId;
        renderStations();
        updateControlButtons();

        // Check if device is selected
        const device = elements.deviceSelect.value;
        if (!device) {
            showError('Please select a device first');
            return;
        }

        // Auto-play the station
        playStation();
    }

    function updateControlButtons() {
        const deviceSelected = elements.deviceSelect.value !== '';
        const stationSelected = selectedStation !== null;

        elements.playBtn.disabled = !(deviceSelected && stationSelected);
        elements.stopBtn.disabled = !deviceSelected;
    }

    async function playStation() {
        const station = stations.find(s => s.id === selectedStation);
        if (!station) return;

        const device = elements.deviceSelect.value;
        if (!device) {
            showError('Please select a device');
            return;
        }

        try {
            elements.playBtn.disabled = true;
            elements.playBtn.innerHTML = '<span>⏳</span> Playing...';

            const response = await fetch('/api/radio/play', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    device: device,
                    url: station.url,
                    name: station.name
                })
            });

            const result = await response.json();

            if (!result.success) {
                showError(result.error || 'Failed to start playback');
            } else {
                playingStation = selectedStation;
                renderStations();
                updateNowPlaying();
                hideError();
            }
        } catch (error) {
            showError(`Failed to start playback: ${error.message}`);
        } finally {
            elements.playBtn.innerHTML = '<span>▶</span> Play';
            updateControlButtons();
        }
    }

    async function stopPlayback() {
        const device = elements.deviceSelect.value;
        if (!device) return;

        try {
            elements.stopBtn.disabled = true;

            const response = await fetch('/api/radio/stop', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ device: device })
            });

            const result = await response.json();

            if (!result.success) {
                showError(result.error || 'Failed to stop playback');
            } else {
                playingStation = null;
                renderStations();
                updateNowPlaying();
                hideError();
            }
        } catch (error) {
            showError(`Failed to stop playback: ${error.message}`);
        } finally {
            updateControlButtons();
        }
    }

    function openModal(station = null) {
        if (station) {
            elements.modalTitle.textContent = 'Edit Station';
            elements.stationId.value = station.id;
            elements.stationName.value = station.name;
            elements.stationUrl.value = station.url;
            elements.stationIcon.value = station.icon_url || '';
        } else {
            elements.modalTitle.textContent = 'Add Station';
            elements.stationForm.reset();
            elements.stationId.value = '';
        }

        elements.stationModal.style.display = 'block';
        elements.modalBackdrop.style.display = 'block';
        elements.stationName.focus();
    }

    function closeModal() {
        elements.stationModal.style.display = 'none';
        elements.modalBackdrop.style.display = 'none';
        elements.stationForm.reset();
    }

    async function saveStation(e) {
        e.preventDefault();

        const stationId = elements.stationId.value;
        const data = {
            name: elements.stationName.value,
            url: elements.stationUrl.value,
            icon_url: elements.stationIcon.value
        };

        try {
            const url = stationId
                ? `/api/radio/stations/${stationId}`
                : '/api/radio/stations';
            const method = stationId ? 'PUT' : 'POST';

            const response = await fetch(url, {
                method: method,
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(data)
            });

            const result = await response.json();

            if (result.success) {
                closeModal();
                await loadStations();
                hideError();
            } else {
                showError(result.error || 'Failed to save station');
            }
        } catch (error) {
            showError(`Failed to save station: ${error.message}`);
        }
    }

    function editStation(stationId) {
        const station = stations.find(s => s.id === stationId);
        if (station) {
            openModal(station);
        }
    }

    async function deleteStation(stationId) {
        const station = stations.find(s => s.id === stationId);
        if (!station) return;

        if (!confirm(`Delete station "${station.name}"?`)) {
            return;
        }

        try {
            const response = await fetch(`/api/radio/stations/${stationId}`, {
                method: 'DELETE'
            });

            const result = await response.json();

            if (result.success) {
                if (selectedStation === stationId) {
                    selectedStation = null;
                    updateControlButtons();
                }
                await loadStations();
                hideError();
            } else {
                showError(result.error || 'Failed to delete station');
            }
        } catch (error) {
            showError(`Failed to delete station: ${error.message}`);
        }
    }

    function showError(message) {
        elements.errorMessage.textContent = message;
        elements.errorMessage.style.display = 'block';
    }

    function hideError() {
        elements.errorMessage.style.display = 'none';
    }

    async function refreshIconCache() {
        const iconUrl = elements.stationIcon.value.trim();

        if (!iconUrl) {
            showError('Please enter an icon URL first');
            return;
        }

        try {
            elements.refreshIconBtn.disabled = true;
            elements.refreshIconBtn.textContent = '⏳';

            const response = await fetch('/api/radio/logo-cache', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    url: iconUrl,
                    force_refresh: true
                })
            });

            const result = await response.json();

            if (result.success) {
                // Show success feedback
                elements.refreshIconBtn.textContent = '✓';
                setTimeout(() => {
                    elements.refreshIconBtn.textContent = '🔄';
                }, 2000);
                hideError();
            } else {
                showError(result.error || 'Failed to cache icon');
                elements.refreshIconBtn.textContent = '🔄';
            }
        } catch (error) {
            showError(`Failed to cache icon: ${error.message}`);
            elements.refreshIconBtn.textContent = '🔄';
        } finally {
            elements.refreshIconBtn.disabled = false;
        }
    }

    function escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    function updateNowPlaying() {
        if (playingStation) {
            const station = stations.find(s => s.id === playingStation);
            if (station) {
                elements.nowPlayingStation.textContent = station.name;
                elements.nowPlaying.style.display = 'block';
            } else {
                elements.nowPlaying.style.display = 'none';
            }
        } else {
            elements.nowPlaying.style.display = 'none';
        }
    }

    async function updateVolumeSlider() {
        const device = elements.deviceSelect.value;
        if (!device) {
            elements.volumeSlider.value = 50; // Default to 50%
            return;
        }

        try {
            const response = await fetch(`/api/device/${device}/status`);
            const status = await response.json();

            if (status.volume_level !== undefined) {
                // Convert 0.0-1.0 to 0-100
                const volumePercent = Math.round(status.volume_level * 100);
                elements.volumeSlider.value = volumePercent;

                // Update icon based on mute state
                if (status.volume_muted) {
                    elements.volumeIcon.textContent = '🔇';
                } else if (volumePercent === 0) {
                    elements.volumeIcon.textContent = '🔈';
                } else if (volumePercent < 50) {
                    elements.volumeIcon.textContent = '🔉';
                } else {
                    elements.volumeIcon.textContent = '🔊';
                }
            }
        } catch (error) {
            console.error('Failed to get volume:', error);
            elements.volumeSlider.value = 50; // Default to 50%
        }
    }

    async function handleVolumeChange(e) {
        const device = elements.deviceSelect.value;
        if (!device) return;

        const volume = parseInt(e.target.value) / 100; // Convert 0-100 to 0.0-1.0

        // Update icon based on volume level
        const volumePercent = parseInt(e.target.value);
        if (volumePercent === 0) {
            elements.volumeIcon.textContent = '🔈';
        } else if (volumePercent < 50) {
            elements.volumeIcon.textContent = '🔉';
        } else {
            elements.volumeIcon.textContent = '🔊';
        }

        try {
            const response = await fetch(`/api/device/${device}/volume`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ volume: volume })
            });

            const result = await response.json();

            if (!result.success) {
                console.error('Failed to set volume:', result.error);
            }
        } catch (error) {
            console.error('Failed to set volume:', error);
        }
    }

    async function toggleMute() {
        const device = elements.deviceSelect.value;
        if (!device) {
            showError('Please select a device first');
            return;
        }

        try {
            const response = await fetch(`/api/device/${device}/mute`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' }
            });

            const result = await response.json();

            if (result.success) {
                // Update volume slider to reflect mute state
                await updateVolumeSlider();
                hideError();
            } else {
                showError(result.error || 'Failed to toggle mute');
            }
        } catch (error) {
            showError(`Failed to toggle mute: ${error.message}`);
        }
    }
});
