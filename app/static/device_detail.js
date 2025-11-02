document.addEventListener('DOMContentLoaded', function() {
    let currentStatus = null;
    let statusInterval = null;

    const elements = {
        loadingStatus: document.getElementById('loading-status'),
        deviceStatus: document.getElementById('device-status'),
        errorMessage: document.getElementById('error-message'),
        appName: document.getElementById('app-name'),
        trackTitle: document.getElementById('track-title'),
        trackArtist: document.getElementById('track-artist'),
        trackAlbum: document.getElementById('track-album'),
        albumArt: document.getElementById('album-art'),
        albumArtIcon: document.getElementById('album-art-icon'),
        progressContainer: document.getElementById('progress-container'),
        currentTime: document.getElementById('current-time'),
        duration: document.getElementById('duration'),
        progressFill: document.getElementById('progress-fill'),
        playPauseBtn: document.getElementById('play-pause-btn'),
        playPauseIcon: document.getElementById('play-pause-icon'),
        stopBtn: document.getElementById('stop-btn'),
        prevBtn: document.getElementById('prev-btn'),
        nextBtn: document.getElementById('next-btn'),
        volumeSlider: document.getElementById('volume-slider'),
        volumeValue: document.getElementById('volume-value'),
        muteBtn: document.getElementById('mute-btn'),
        muteIcon: document.getElementById('mute-icon')
    };

    // Load status initially
    loadStatus();

    // Refresh status every 2 seconds
    statusInterval = setInterval(loadStatus, 2000);

    // Control button event listeners
    elements.playPauseBtn.addEventListener('click', togglePlayPause);
    elements.stopBtn.addEventListener('click', stop);
    elements.prevBtn.addEventListener('click', previous);
    elements.nextBtn.addEventListener('click', next);
    elements.volumeSlider.addEventListener('input', updateVolume);
    elements.muteBtn.addEventListener('click', toggleMute);

    async function loadStatus() {
        try {
            const response = await fetch(`/api/device/${deviceUuid}/status`);
            const status = await response.json();

            if (status.error) {
                showError(status.error);
                return;
            }

            currentStatus = status;
            updateUI(status);
            hideError();

            // Show device status, hide loading
            elements.loadingStatus.style.display = 'none';
            elements.deviceStatus.style.display = 'block';

        } catch (error) {
            showError(`Failed to load status: ${error.message}`);
        }
    }

    function updateUI(status) {
        // Update app name
        if (status.app_display_name) {
            elements.appName.textContent = status.app_display_name;
        } else if (status.is_idle) {
            elements.appName.textContent = 'Idle';
        } else {
            elements.appName.textContent = 'Unknown App';
        }

        // Update volume
        const volumePercent = Math.round(status.volume_level * 100);
        elements.volumeSlider.value = volumePercent;
        elements.volumeValue.textContent = `${volumePercent}%`;
        elements.muteIcon.textContent = status.volume_muted ? '🔇' : '🔊';

        // Update media status
        const media = status.media_status;
        if (media && media.state !== 'UNKNOWN' && media.state !== 'IDLE') {
            // Update track info
            elements.trackTitle.textContent = media.title || 'Unknown Title';
            elements.trackArtist.textContent = media.artist || '';
            elements.trackAlbum.textContent = media.album_name || '';

            // Update album art
            if (media.images && media.images.length > 0) {
                elements.albumArt.style.backgroundImage = `url(${media.images[0].url})`;
                elements.albumArt.classList.remove('album-art-placeholder');
                elements.albumArtIcon.style.display = 'none';
            } else {
                elements.albumArt.style.backgroundImage = '';
                elements.albumArt.classList.add('album-art-placeholder');
                elements.albumArtIcon.style.display = 'block';
            }

            // Update progress
            if (media.duration && media.current_time !== null) {
                elements.progressContainer.style.display = 'block';
                elements.currentTime.textContent = formatTime(media.current_time);
                elements.duration.textContent = formatTime(media.duration);
                const progress = (media.current_time / media.duration) * 100;
                elements.progressFill.style.width = `${progress}%`;
            } else {
                elements.progressContainer.style.display = 'none';
            }

            // Update play/pause button
            if (media.state === 'PLAYING') {
                elements.playPauseIcon.textContent = '⏸';
                elements.playPauseBtn.title = 'Pause';
            } else {
                elements.playPauseIcon.textContent = '▶';
                elements.playPauseBtn.title = 'Play';
            }

            // Enable/disable buttons based on capabilities
            elements.playPauseBtn.disabled = !media.supports_pause;
            elements.prevBtn.disabled = !media.supports_skip_backward;
            elements.nextBtn.disabled = !media.supports_skip_forward;
            elements.stopBtn.disabled = false;

        } else {
            // No media playing
            elements.trackTitle.textContent = 'No media playing';
            elements.trackArtist.textContent = '';
            elements.trackAlbum.textContent = '';
            elements.albumArt.style.backgroundImage = '';
            elements.albumArt.classList.add('album-art-placeholder');
            elements.albumArtIcon.style.display = 'block';
            elements.progressContainer.style.display = 'none';
            elements.playPauseIcon.textContent = '▶';

            // Disable control buttons when idle
            elements.playPauseBtn.disabled = true;
            elements.stopBtn.disabled = true;
            elements.prevBtn.disabled = true;
            elements.nextBtn.disabled = true;
        }
    }

    async function togglePlayPause() {
        if (!currentStatus || !currentStatus.media_status) return;

        const isPlaying = currentStatus.media_status.state === 'PLAYING';
        const endpoint = isPlaying ? 'pause' : 'play';

        try {
            const response = await fetch(`/api/device/${deviceUuid}/${endpoint}`, {
                method: 'POST'
            });
            const result = await response.json();

            if (!result.success) {
                showError(result.error || 'Failed to control playback');
            } else {
                // Immediately refresh status
                loadStatus();
            }
        } catch (error) {
            showError(`Failed to control playback: ${error.message}`);
        }
    }

    async function stop() {
        try {
            const response = await fetch(`/api/device/${deviceUuid}/stop`, {
                method: 'POST'
            });
            const result = await response.json();

            if (!result.success) {
                showError(result.error || 'Failed to stop playback');
            } else {
                loadStatus();
            }
        } catch (error) {
            showError(`Failed to stop playback: ${error.message}`);
        }
    }

    async function previous() {
        try {
            const response = await fetch(`/api/device/${deviceUuid}/previous`, {
                method: 'POST'
            });
            const result = await response.json();

            if (!result.success) {
                showError(result.error || 'Failed to skip to previous');
            } else {
                loadStatus();
            }
        } catch (error) {
            showError(`Failed to skip to previous: ${error.message}`);
        }
    }

    async function next() {
        try {
            const response = await fetch(`/api/device/${deviceUuid}/next`, {
                method: 'POST'
            });
            const result = await response.json();

            if (!result.success) {
                showError(result.error || 'Failed to skip to next');
            } else {
                loadStatus();
            }
        } catch (error) {
            showError(`Failed to skip to next: ${error.message}`);
        }
    }

    async function updateVolume() {
        const volume = parseInt(elements.volumeSlider.value) / 100;
        elements.volumeValue.textContent = `${Math.round(volume * 100)}%`;

        try {
            const response = await fetch(`/api/device/${deviceUuid}/volume`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ volume })
            });
            const result = await response.json();

            if (!result.success) {
                showError(result.error || 'Failed to set volume');
            }
        } catch (error) {
            showError(`Failed to set volume: ${error.message}`);
        }
    }

    async function toggleMute() {
        try {
            const response = await fetch(`/api/device/${deviceUuid}/mute`, {
                method: 'POST'
            });
            const result = await response.json();

            if (!result.success) {
                showError(result.error || 'Failed to toggle mute');
            } else {
                loadStatus();
            }
        } catch (error) {
            showError(`Failed to toggle mute: ${error.message}`);
        }
    }

    function formatTime(seconds) {
        if (!seconds || seconds < 0) return '0:00';
        const mins = Math.floor(seconds / 60);
        const secs = Math.floor(seconds % 60);
        return `${mins}:${secs.toString().padStart(2, '0')}`;
    }

    function showError(message) {
        elements.errorMessage.textContent = message;
        elements.errorMessage.style.display = 'block';
    }

    function hideError() {
        elements.errorMessage.style.display = 'none';
    }

    // Cleanup on page unload
    window.addEventListener('beforeunload', function() {
        if (statusInterval) {
            clearInterval(statusInterval);
        }
    });
});
