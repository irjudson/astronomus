// ==========================================
// SIMPLIFIED TELESCOPE CONTROLS
// Clean, focused UX for Seestar telescope
// ==========================================

const TelescopeControls = {
    isConnected: false,
    currentTarget: null,
    selectedTarget: null,
    telemetryInterval: null,
    previewRefreshInterval: null,

    init() {
        console.log('TelescopeControls: Initializing...');
        this.setupEventListeners();
        this.setupControlHandlers();
        this.setupStatusConsole();
        this.setupTargetAutocomplete();
        this.disableAllControls();
        console.log('TelescopeControls: Initialized');
    },

    setupStatusConsole() {
        const clearBtn = document.getElementById('clear-status-console-btn');
        if (clearBtn) {
            clearBtn.addEventListener('click', () => {
                const consoleMessages = document.getElementById('status-console-messages');
                if (consoleMessages) {
                    consoleMessages.innerHTML = '<div style="color: #888;">Ready</div>';
                }
            });
        }
    },

    setupTargetAutocomplete() {
        const targetNameInput = document.getElementById('target-name');
        const autocompleteDiv = document.getElementById('target-autocomplete');
        let searchTimeout = null;

        if (!targetNameInput || !autocompleteDiv) return;

        // Search as user types
        targetNameInput.addEventListener('input', async (e) => {
            const query = e.target.value.trim();

            // Clear selected target when user starts typing again
            if (this.selectedTarget && query !== this.selectedTarget.name) {
                this.selectedTarget = null;
                const targetRaInput = document.getElementById('target-ra');
                const targetDecInput = document.getElementById('target-dec');
                if (targetRaInput) targetRaInput.value = '';
                if (targetDecInput) targetDecInput.value = '';
            }

            if (query.length < 2) {
                autocompleteDiv.style.display = 'none';
                return;
            }

            // Debounce search
            clearTimeout(searchTimeout);
            searchTimeout = setTimeout(async () => {
                try {
                    // Show loading indicator
                    autocompleteDiv.innerHTML = `
                        <div style="padding: 12px; text-align: center; color: #888;">
                            <div class="spinner-border spinner-border-sm" role="status" style="margin-right: 8px;"></div>
                            Searching...
                        </div>
                    `;
                    autocompleteDiv.style.display = 'block';

                    // Add visible_now=true to only show targets visible right now
                    const response = await fetch(`/api/catalog/search?search=${encodeURIComponent(query)}&visible_now=true&page_size=10`);
                    if (!response.ok) {
                        autocompleteDiv.innerHTML = `
                            <div style="padding: 12px; text-align: center; color: #dc3545;">
                                Search failed. Please try again.
                            </div>
                        `;
                        return;
                    }

                    const data = await response.json();
                    const results = data.items || [];

                    if (results.length === 0) {
                        autocompleteDiv.innerHTML = `
                            <div style="padding: 12px; text-align: center; color: #888;">
                                No results found for "${query}"
                            </div>
                        `;
                        return;
                    }

                    // Build autocomplete list
                    // Note: API returns ra in degrees, need to convert to hours for storage
                    autocompleteDiv.innerHTML = results.map(target => `
                        <div class="autocomplete-item" data-id="${target.id}" data-name="${target.name}"
                             data-ra="${target.ra / 15}" data-dec="${target.dec}"
                             style="padding: 8px 12px; cursor: pointer; border-bottom: 1px solid #333;">
                            <div style="font-weight: bold; color: #4a9eff;">${target.name}</div>
                            <div style="font-size: 0.85em; color: #888;">
                                ${target.type || 'Unknown'} • RA: ${this.formatRA(target.ra / 15)} • Dec: ${this.formatDec(target.dec)}
                            </div>
                        </div>
                    `).join('');

                    autocompleteDiv.style.display = 'block';

                    // Add click handlers
                    autocompleteDiv.querySelectorAll('.autocomplete-item').forEach(item => {
                        item.addEventListener('mouseenter', () => {
                            item.style.background = '#3a3a3a';
                        });
                        item.addEventListener('mouseleave', () => {
                            item.style.background = 'transparent';
                        });
                        item.addEventListener('click', () => {
                            this.selectTarget({
                                id: item.dataset.id,
                                name: item.dataset.name,
                                ra: parseFloat(item.dataset.ra),
                                dec: parseFloat(item.dataset.dec)
                            });
                        });
                    });
                } catch (error) {
                    console.error('Autocomplete search failed:', error);
                }
            }, 300);
        });

        // Handle Enter key
        targetNameInput.addEventListener('keydown', (e) => {
            if (e.key === 'Enter') {
                e.preventDefault();
                // Select first item if autocomplete is showing
                const firstItem = autocompleteDiv.querySelector('.autocomplete-item');
                if (firstItem && autocompleteDiv.style.display === 'block') {
                    this.selectTarget({
                        id: firstItem.dataset.id,
                        name: firstItem.dataset.name,
                        ra: parseFloat(firstItem.dataset.ra),
                        dec: parseFloat(firstItem.dataset.dec)
                    });
                }
            } else if (e.key === 'Escape') {
                autocompleteDiv.style.display = 'none';
            }
        });

        // Close autocomplete when clicking outside
        document.addEventListener('click', (e) => {
            if (!targetNameInput.contains(e.target) && !autocompleteDiv.contains(e.target)) {
                autocompleteDiv.style.display = 'none';
            }
        });
    },

    selectTarget(target) {
        const targetNameInput = document.getElementById('target-name');
        const targetRaInput = document.getElementById('target-ra');
        const targetDecInput = document.getElementById('target-dec');
        const autocompleteDiv = document.getElementById('target-autocomplete');

        if (targetNameInput) targetNameInput.value = target.name;
        if (targetRaInput) targetRaInput.value = this.formatRA(target.ra);
        if (targetDecInput) targetDecInput.value = this.formatDec(target.dec);

        // Store the selected target data
        this.selectedTarget = target;

        // Close autocomplete
        if (autocompleteDiv) autocompleteDiv.style.display = 'none';

        // Log to console
        this.showStatus(`Selected target: ${target.name}`, 'success');
    },

    setupEventListeners() {
        // Connection events
        document.addEventListener('telescope-connected', () => this.onConnected());
        document.addEventListener('telescope-disconnected', () => this.onDisconnected());

        // Telemetry updates
        document.addEventListener('telescope-telemetry-update', (e) => {
            this.updateTelemetry(e.detail);
        });
    },

    setupControlHandlers() {
        // Connection - use compact status bar button
        this.on('connect-btn-compact', () => {
            if (this.isConnected) {
                this.handleDisconnect();
            } else {
                this.handleConnect();
            }
        });

        // Telescope control - main panel
        this.on('slew-to-target-btn', () => this.handleSlewToTarget());
        this.on('stop-motion-btn', () => this.handleStopMotion());
        this.on('unpark-telescope-btn', () => this.handleUnpark());
        this.on('park-telescope-btn', () => this.handlePark());

        // Telescope control - sidebar
        this.on('sidebar-goto-target-btn', () => this.handleSlewToTarget());
        this.on('sidebar-unpark-telescope-btn', () => this.handleUnpark());
        this.on('sidebar-park-telescope-btn', () => this.handlePark());

        // Imaging
        this.on('start-imaging-btn', () => this.handleStartImaging());
        this.on('stop-imaging-btn', () => this.handleStopImaging());
        this.on('auto-focus-btn', () => this.handleAutoFocus());

        // Advanced controls (in bottom drawer)
        this.on('dew-heater-toggle', () => this.handleDewHeater());
        this.on('toggle-dew-heater-btn', () => this.handleDewHeater());
        this.on('refresh-images-btn', () => this.handleRefreshImages());

        // Navigation controls
        this.on('nav-up-btn', () => this.handleNavigation('up'));
        this.on('nav-down-btn', () => this.handleNavigation('down'));
        this.on('nav-left-btn', () => this.handleNavigation('left'));
        this.on('nav-right-btn', () => this.handleNavigation('right'));
        this.on('nav-stop-btn', () => this.handleStopMotion()); // Use same endpoint as STOP MOTION button
        this.on('start-preview-btn', () => this.handleStartPreview());
        this.on('stop-preview-btn', () => this.handleStopPreview());
    },

    // Helper to add event listener
    on(id, handler) {
        const el = document.getElementById(id);
        if (el) {
            el.addEventListener('click', handler);
        }
    },

    // ==========================================
    // CONNECTION
    // ==========================================

    async handleConnect() {
        // Use default host from preferences or hardcoded default
        const host = '192.168.2.47'; // TODO: Get from preferences

        try {
            const response = await fetch('/api/telescope/connect', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ host, port: 4700 })
            });

            if (!response.ok) throw new Error('Connection failed');

            const data = await response.json();
            console.log('Connected:', data);
            this.showStatus('Connected to telescope', 'success');
        } catch (error) {
            console.error('Connection error:', error);
            this.showStatus(`Failed to connect: ${error.message}`, 'error');
        }
    },

    async handleDisconnect() {
        try {
            await fetch('/api/telescope/disconnect', { method: 'POST' });
            this.showStatus('Disconnected', 'info');
        } catch (error) {
            console.error('Disconnect error:', error);
        }
    },

    onConnected() {
        this.isConnected = true;
        // Keep all controls disabled until first status arrives
        // First telemetry update will enable correct controls based on actual state
        this.disableAllControls();
        this.startTelemetryPolling();
        // Preview is now manually started with Start Preview button
        this.showStatus('Telescope connected', 'success');

        // Update status bar
        const statusLabel = document.querySelector('#connection-status-compact .status-label');
        if (statusLabel) statusLabel.textContent = 'Connected';
        const statusIndicator = document.querySelector('#connection-status-compact .status-indicator');
        if (statusIndicator) {
            statusIndicator.classList.remove('disconnected');
            statusIndicator.classList.add('connected');
            statusIndicator.textContent = '🟢'; // Green circle for connected
        }
        this.setText('telescope-ip-display', '192.168.2.47'); // TODO: Get from actual connection

        // Update connect button to disconnect
        const connectBtn = document.getElementById('connect-btn-compact');
        if (connectBtn) {
            connectBtn.disabled = false;
            connectBtn.title = 'Disconnect';
            connectBtn.textContent = '🔌'; // Plug icon for disconnect
        }
    },

    onDisconnected() {
        this.isConnected = false;
        this.disableAllControls();
        this.stopTelemetryPolling();
        // Preview cleanup handled by handleStopPreview() if active

        // Update UI with disconnected state
        this.setText('telescope-ip-display', '--');
        this.setText('telescope-target-display', 'No Target');
        this.setText('tracking-status', 'Not tracking');
        this.setText('current-ra', '--:--:--');
        this.setText('current-dec', '--°--\'--"');

        // Update status bar
        const statusLabel = document.querySelector('#connection-status-compact .status-label');
        if (statusLabel) statusLabel.textContent = 'Disconnected';
        const statusIndicator = document.querySelector('#connection-status-compact .status-indicator');
        if (statusIndicator) {
            statusIndicator.classList.remove('connected');
            statusIndicator.classList.add('disconnected');
            statusIndicator.textContent = '🔴'; // Red circle for disconnected
        }

        // Update connect button
        const connectBtn = document.getElementById('connect-btn-compact');
        if (connectBtn) {
            connectBtn.disabled = false;
            connectBtn.title = 'Connect';
            connectBtn.textContent = '⚡'; // Lightning icon for connect
        }

        this.showStatus('Telescope disconnected', 'warning');
    },

    // ==========================================
    // TELESCOPE CONTROL
    // ==========================================

    async handleSlewToTarget() {
        const nameInput = document.getElementById('target-name');
        const name = nameInput?.value || 'Target';

        console.log('[SLEW DIAGNOSTIC] handleSlewToTarget called');
        console.log('[SLEW DIAGNOSTIC] selectedTarget:', this.selectedTarget);

        // Use selectedTarget data if available (from autocomplete)
        if (this.selectedTarget) {
            try {
                if (window.TelescopeMessages) {
                    TelescopeMessages.logCommand('goto', {
                        target: this.selectedTarget.name,
                        ra: this.selectedTarget.ra,
                        dec: this.selectedTarget.dec
                    });
                }

                // IMPORTANT: Stop any active viewing session first
                // iscope_start_view won't interrupt an active view, so we must stop it first
                console.log('[SLEW DIAGNOSTIC] Stopping current view...');
                this.showStatus('Stopping current view...', 'info');
                const stopResponse = await fetch('/api/telescope/stop-imaging', { method: 'POST' });
                console.log('[SLEW DIAGNOSTIC] Stop response status:', stopResponse.status);
                await new Promise(resolve => setTimeout(resolve, 1000)); // Wait 1s for view to stop

                const gotoPayload = {
                    ra: this.selectedTarget.ra,
                    dec: this.selectedTarget.dec,
                    target_name: this.selectedTarget.name
                };
                console.log('[SLEW DIAGNOSTIC] Sending goto request with payload:', gotoPayload);

                const response = await fetch('/api/telescope/goto', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(gotoPayload)
                });

                console.log('[SLEW DIAGNOSTIC] Goto response status:', response.status);

                if (!response.ok) {
                    const errorData = await response.json();
                    console.error('[SLEW DIAGNOSTIC] Goto failed with error:', errorData);
                    if (window.TelescopeMessages) {
                        TelescopeMessages.logError(`Slew failed: ${errorData.detail}`);
                    }
                    throw new Error(errorData.detail || 'Slew command failed');
                }

                const responseData = await response.json();
                console.log('[SLEW DIAGNOSTIC] Goto response data:', responseData);

                if (window.TelescopeMessages) {
                    TelescopeMessages.logResponse('goto', `Slewing to ${this.selectedTarget.name}`, true);
                }

                this.showStatus(`Slewing to ${this.selectedTarget.name}...`, 'info');
                this.currentTarget = this.selectedTarget.name;
            } catch (error) {
                console.error('[SLEW DIAGNOSTIC] Exception in handleSlewToTarget:', error);
                this.showStatus(`Slew failed: ${error.message}`, 'error');
            }
        } else {
            console.warn('[SLEW DIAGNOSTIC] No selectedTarget available');
            this.showStatus('Please select a target from the search', 'warning');
        }
    },

    async handleStopMotion() {
        try {
            await fetch('/api/telescope/stop', { method: 'POST' });
            this.showStatus('Motion stopped', 'info');
        } catch (error) {
            console.error('Stop error:', error);
        }
    },

    async handleUnpark() {
        try {
            console.log('[UNPARK] Starting unpark command...');
            if (window.TelescopeMessages) {
                TelescopeMessages.logCommand('unpark', { azimuth: 180, altitude: 45 });
            }

            const response = await fetch('/api/telescope/unpark', { method: 'POST' });
            console.log('[UNPARK] Response status:', response.status, response.statusText);

            if (!response.ok) {
                const errorText = await response.text();
                console.error('[UNPARK] Error response:', errorText);
                if (window.TelescopeMessages) {
                    TelescopeMessages.logError(`Unpark failed: ${errorText}`);
                }
                throw new Error(`Unpark command failed: ${errorText}`);
            }

            const data = await response.json();
            console.log('[UNPARK] Success response:', data);

            if (window.TelescopeMessages) {
                TelescopeMessages.logResponse('unpark', 'Unparking...', true);
            }

            this.showStatus('Unparking telescope...', 'info');
        } catch (error) {
            console.error('[UNPARK ERROR]', error);
            this.showStatus(`Unpark failed: ${error.message}`, 'error');
            if (window.TelescopeMessages) {
                TelescopeMessages.logError(`Unpark exception: ${error.message}`);
            }
        }
    },

    async handlePark() {
        try {
            if (window.TelescopeMessages) {
                TelescopeMessages.logCommand('park');
            }

            const response = await fetch('/api/telescope/park', { method: 'POST' });

            if (!response.ok) {
                if (window.TelescopeMessages) {
                    TelescopeMessages.logError('Park command failed');
                }
                throw new Error('Park command failed');
            }

            if (window.TelescopeMessages) {
                TelescopeMessages.logResponse('park', 'Parking...', true);
            }

            this.showStatus('Parking telescope...', 'info');
        } catch (error) {
            console.error('Park error:', error);
            this.showStatus(`Park failed: ${error.message}`, 'error');
        }
    },

    // ==========================================
    // IMAGING
    // ==========================================

    async handleStartImaging() {
        const exposure = document.getElementById('exposure-time')?.value || 10;
        const gain = document.getElementById('gain-value')?.value || 80;

        try {
            const response = await fetch('/api/telescope/start-imaging', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ exposure_ms: exposure * 1000, gain, restart: true })
            });

            if (!response.ok) throw new Error('Failed to start imaging');

            this.showStatus('Imaging started', 'success');
            // Button state will be managed by updateControlStates() based on telescope state
        } catch (error) {
            console.error('Imaging error:', error);
            this.showStatus(`Imaging failed: ${error.message}`, 'error');
        }
    },

    async handleStopImaging() {
        try {
            await fetch('/api/telescope/stop-imaging', { method: 'POST' });
            this.showStatus('Imaging stopped', 'info');
            // Button state will be managed by updateControlStates() based on telescope state
        } catch (error) {
            console.error('Stop imaging error:', error);
        }
    },

    async handleAutoFocus() {
        try {
            const response = await fetch('/api/telescope/features/imaging/autofocus', { method: 'POST' });
            if (!response.ok) throw new Error('Failed to start autofocus');
            this.showStatus('Auto focus started...', 'info');
        } catch (error) {
            console.error('Auto focus error:', error);
            this.showStatus(`Auto focus failed: ${error.message}`, 'error');
        }
    },

    // ==========================================
    // ADVANCED CONTROLS
    // ==========================================

    async handleDewHeater() {
        const toggle = document.getElementById('dew-heater-toggle');
        const enabled = toggle?.checked || false;

        try {
            await fetch('/api/telescope/features/hardware/dew-heater', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ enabled, power_level: 90 })
            });

            this.showStatus(`Dew heater ${enabled ? 'on' : 'off'}`, 'info');
        } catch (error) {
            console.error('Dew heater error:', error);
        }
    },

    async handleRefreshImages() {
        try {
            const response = await fetch('/api/telescope/images');
            const images = await response.json();

            this.updateImageList(images);
            this.showStatus(`Found ${images.length} images`, 'info');
        } catch (error) {
            console.error('Image list error:', error);
        }
    },

    // ==========================================
    // NAVIGATION & PREVIEW
    // ==========================================

    async handleNavigation(direction) {
        try {
            const speed = 5.0; // Increased speed (50% power for visible movement)
            const response = await fetch('/api/telescope/move', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ action: direction, speed: speed })
            });

            const result = await response.json();

            if (result.status === 'error') {
                this.showStatus(`Navigation failed: ${result.message}`, 'error');
            } else if (direction === 'stop') {
                this.showStatus('Movement stopped', 'info');
            } else {
                this.showStatus(`Moving ${direction}...`, 'info');
            }
        } catch (error) {
            console.error('Navigation error:', error);
            this.showStatus('Navigation command failed', 'error');
        }
    },

    async handleStartPreview() {
        try {
            const mode = document.getElementById('preview-mode')?.value || 'scenery';
            this.showStatus(`Starting ${mode} preview...`, 'info');

            const response = await fetch('/api/telescope/start-preview', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ mode, brightness: 50.0 })
            });

            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.detail || 'Failed to start preview');
            }

            const result = await response.json();
            this.showStatus(`Preview started - ${result.message}`, 'success');

            // Start RTMP preview refresh if in scenery mode
            if (mode === 'scenery') {
                this.startRTMPPreviewRefresh();
            }
        } catch (error) {
            console.error('Start preview error:', error);
            this.showStatus(`Failed to start preview: ${error.message}`, 'error');
        }
    },

    async handleStopPreview() {
        try {
            this.showStatus('Stopping preview...', 'info');

            const response = await fetch('/api/telescope/stop-imaging', { method: 'POST' });

            if (!response.ok) {
                throw new Error('Failed to stop preview');
            }

            // Stop RTMP refresh if running
            this.stopRTMPPreviewRefresh();

            this.showStatus('Preview stopped', 'success');
        } catch (error) {
            console.error('Stop preview error:', error);
            this.showStatus(`Failed to stop preview: ${error.message}`, 'error');
        }
    },

    async startRTMPPreviewRefresh() {
        // Stop any existing interval
        this.stopRTMPPreviewRefresh();

        // First, fetch preview info to get frame dimensions
        try {
            const infoResponse = await fetch('/api/telescope/preview-info');
            if (infoResponse.ok) {
                const info = await infoResponse.json();
                if (info.available) {
                    console.log(`RTSP stream dimensions: ${info.width}x${info.height}`);

                    // Calculate aspect ratio
                    const aspectRatio = info.width / info.height;
                    console.log(`Aspect ratio: ${aspectRatio.toFixed(2)} (${info.width}:${info.height})`);

                    // Adjust container aspect ratio if needed
                    const container = document.querySelector('.preview-image-container');
                    if (container) {
                        // If aspect ratio is portrait (height > width), adjust the container
                        if (aspectRatio < 1) {
                            console.log('Portrait video detected, adjusting container');
                            container.style.aspectRatio = `${info.width}/${info.height}`;
                        } else if (aspectRatio > 1.5) {
                            // Wide aspect ratio (16:9 ish)
                            console.log('Wide aspect ratio detected');
                            container.style.aspectRatio = `${info.width}/${info.height}`;
                        }
                    }
                }
            }
        } catch (error) {
            console.warn('Could not fetch preview info:', error);
        }

        // Start fetching RTSP frames
        this.rtmpPreviewInterval = setInterval(async () => {
            try {
                const response = await fetch('/api/telescope/live-preview');
                if (response.ok) {
                    const blob = await response.blob();
                    const previewImg = document.getElementById('preview-image');
                    const placeholder = document.getElementById('preview-placeholder');

                    if (previewImg && placeholder) {
                        const imageUrl = URL.createObjectURL(blob);
                        if (previewImg.src && previewImg.src.startsWith('blob:')) {
                            URL.revokeObjectURL(previewImg.src);
                        }
                        previewImg.src = imageUrl;
                        previewImg.style.display = 'block';
                        placeholder.style.display = 'none';
                    }
                }
            } catch (error) {
                console.error('RTSP preview refresh error:', error);
            }
        }, 1000); // Refresh every second for live preview
    },

    stopRTMPPreviewRefresh() {
        if (this.rtmpPreviewInterval) {
            clearInterval(this.rtmpPreviewInterval);
            this.rtmpPreviewInterval = null;
        }
    },

    async startPreviewStream() {
        // Start auto-refresh of preview images every 5 seconds
        // (stacked images don't update as frequently as video)
        console.log('Starting preview auto-refresh');
        this.startPreviewRefresh();
    },

    async stopPreviewStream() {
        // Stop auto-refresh
        console.log('Stopping preview auto-refresh');
        this.stopPreviewRefresh();

        // Clear the preview image
        const previewImg = document.getElementById('preview-image');
        const placeholder = document.getElementById('preview-placeholder');
        if (previewImg && placeholder) {
            if (previewImg.src && previewImg.src.startsWith('blob:')) {
                URL.revokeObjectURL(previewImg.src);
            }
            previewImg.src = '';
            previewImg.style.display = 'none';
            placeholder.style.display = 'flex';
        }
    },

    startPreviewRefresh() {
        if (this.previewRefreshInterval) {
            return; // Already running
        }
        // Refresh every 5 seconds (stacked images update slower than video)
        this.previewRefreshInterval = setInterval(() => this.handleRefreshPreview(), 5000);
        // Do an immediate refresh
        this.handleRefreshPreview();
    },

    stopPreviewRefresh() {
        if (this.previewRefreshInterval) {
            clearInterval(this.previewRefreshInterval);
            this.previewRefreshInterval = null;
        }
    },

    // ==========================================
    // TELEMETRY & STATUS
    // ==========================================

    startTelemetryPolling() {
        this.stopTelemetryPolling();
        this.telemetryInterval = setInterval(() => this.fetchTelemetry(), 2000);
        this.fetchTelemetry(); // Initial fetch
    },

    stopTelemetryPolling() {
        if (this.telemetryInterval) {
            clearInterval(this.telemetryInterval);
            this.telemetryInterval = null;
        }
    },

    async fetchTelemetry() {
        try {
            const response = await fetch('/api/telescope/status');
            if (!response.ok) {
                console.error('[TELEMETRY ERROR] HTTP', response.status, response.statusText);
                // If we get consistent errors, trigger disconnect
                if (!this.telemetryErrorCount) this.telemetryErrorCount = 0;
                this.telemetryErrorCount++;
                if (this.telemetryErrorCount >= 3) {
                    console.error('[TELEMETRY ERROR] 3 consecutive failures, triggering disconnect');
                    this.onDisconnected();
                    // Trigger auto-reconnect if enabled
                    if (window.ConnectionManager) {
                        ConnectionManager.autoReconnect();
                    }
                }
                return;
            }
            const status = await response.json();
            // Reset error count on success
            this.telemetryErrorCount = 0;
            this.updateTelemetry(status);
        } catch (error) {
            console.error('[TELEMETRY ERROR]', error);
            // Network error or JSON parse error
            if (!this.telemetryErrorCount) this.telemetryErrorCount = 0;
            this.telemetryErrorCount++;
            if (this.telemetryErrorCount >= 3) {
                console.error('[TELEMETRY ERROR] 3 consecutive failures, triggering disconnect');
                this.onDisconnected();
                // Trigger auto-reconnect if enabled
                if (window.ConnectionManager) {
                    ConnectionManager.autoReconnect();
                }
            }
        }
    },

    updateTelemetry(status) {
        // Log all telescope status updates to browser console
        console.log('[TELESCOPE STATUS]', status);

        // Check if telescope is disconnected
        if (!status.connected) {
            this.onDisconnected();
            return;
        }

        // State and tracking
        this.setText('tracking-status', status.is_tracking ? 'Tracking' : 'Not tracking');

        // Coordinates
        if (status.current_ra_hours != null && status.current_dec_degrees != null) {
            this.setText('current-ra', this.formatRA(status.current_ra_hours));
            this.setText('current-dec', this.formatDec(status.current_dec_degrees));
        } else {
            console.log('[TELESCOPE STATUS] Coordinates not available:', status.current_ra_hours, status.current_dec_degrees);
        }

        // Target - update status bar
        this.setText('telescope-target-display', status.current_target || 'No Target');

        // Update status bar with telescope state (not just "Connected")
        const statusLabel = document.querySelector('#connection-status-compact .status-label');
        if (statusLabel && status.state) {
            // Format state nicely (capitalize first letter)
            const formattedState = status.state.charAt(0).toUpperCase() + status.state.slice(1);
            statusLabel.textContent = formattedState;
        }

        // Update control states based on telescope state
        this.updateControlStates(status.state);
    },

    updateControlStates(state) {
        // Define which states allow which operations
        const isParked = state === 'parked';
        const isUnparkedIdle = ['connected', 'tracking'].includes(state);
        const busyStates = ['slewing', 'focusing', 'imaging', 'parking'];
        const isBusy = busyStates.includes(state);
        const isImaging = state === 'imaging';
        const isSlewing = state === 'slewing';

        console.log('[CONTROL STATES]', {
            state,
            isParked,
            isUnparkedIdle,
            isBusy,
            isImaging,
            isSlewing
        });

        // When parked: ONLY unpark button enabled, everything else disabled
        if (isParked) {
            console.log('[PARKED STATE] Disabling all controls except unpark');
            this.setDisabled('slew-to-target-btn', true);
            this.setDisabled('unpark-telescope-btn', false);
            this.setDisabled('park-telescope-btn', true);
            this.setDisabled('stop-motion-btn', true);
            this.setDisabled('start-imaging-btn', true);
            this.setDisabled('stop-imaging-btn', true);
            this.setDisabled('auto-focus-btn', true);

            // Preview controls
            this.setDisabled('start-preview-btn', true);
            this.setDisabled('stop-preview-btn', true);

            // Sidebar controls
            this.setDisabled('sidebar-goto-target-btn', true);
            this.setDisabled('sidebar-unpark-telescope-btn', false);
            this.setDisabled('sidebar-park-telescope-btn', true);

            // Log button states
            const unparkBtn = document.getElementById('unpark-telescope-btn');
            const parkBtn = document.getElementById('park-telescope-btn');
            console.log('[PARKED STATE] unpark-telescope-btn exists:', !!unparkBtn, 'disabled:', unparkBtn?.disabled);
            console.log('[PARKED STATE] park-telescope-btn exists:', !!parkBtn, 'disabled:', parkBtn?.disabled);
            return;
        }

        // Normal operation (not parked)
        // Movement controls (enabled when unparked and idle)
        this.setDisabled('slew-to-target-btn', !isUnparkedIdle);

        // Unpark button: only enabled when parked
        this.setDisabled('unpark-telescope-btn', true);

        // Park button: only enabled when unparked and idle
        this.setDisabled('park-telescope-btn', !isUnparkedIdle);

        // Stop motion (enabled when slewing)
        this.setDisabled('stop-motion-btn', !isSlewing);

        // Imaging controls (only when unparked and idle)
        this.setDisabled('start-imaging-btn', !isUnparkedIdle || isImaging);
        this.setDisabled('stop-imaging-btn', !isImaging);
        this.setDisabled('auto-focus-btn', !isUnparkedIdle);

        // Preview controls (always enabled when connected)
        this.setDisabled('start-preview-btn', false);
        this.setDisabled('stop-preview-btn', false);

        // Sidebar controls (if they exist)
        this.setDisabled('sidebar-goto-target-btn', !isUnparkedIdle);
        this.setDisabled('sidebar-unpark-telescope-btn', true);
        this.setDisabled('sidebar-park-telescope-btn', !isUnparkedIdle);
    },

    formatRA(hours) {
        const h = Math.floor(hours);
        const m = Math.floor((hours - h) * 60);
        const s = Math.floor(((hours - h) * 60 - m) * 60);
        return `${h.toString().padStart(2, '0')}:${m.toString().padStart(2, '0')}:${s.toString().padStart(2, '0')}`;
    },

    formatDec(degrees) {
        const sign = degrees >= 0 ? '+' : '-';
        const absDeg = Math.abs(degrees);
        const d = Math.floor(absDeg);
        const m = Math.floor((absDeg - d) * 60);
        const s = Math.floor(((absDeg - d) * 60 - m) * 60);
        return `${sign}${d.toString().padStart(2, '0')}°${m.toString().padStart(2, '0')}'${s.toString().padStart(2, '0')}"`;
    },

    // ==========================================
    // UI HELPERS
    // ==========================================

    enableControls() {
        this.setDisabled('slew-to-target-btn', false);
        this.setDisabled('stop-motion-btn', false);
        this.setDisabled('unpark-telescope-btn', false);
        this.setDisabled('park-telescope-btn', false);
        this.setDisabled('start-imaging-btn', false);
        this.setDisabled('auto-focus-btn', false);
    },

    disableAllControls() {
        this.setDisabled('slew-to-target-btn', true);
        this.setDisabled('stop-motion-btn', true);
        this.setDisabled('unpark-telescope-btn', true);
        this.setDisabled('park-telescope-btn', true);
        this.setDisabled('start-imaging-btn', true);
        this.setDisabled('stop-imaging-btn', true);
        this.setDisabled('auto-focus-btn', true);
        this.setDisabled('start-preview-btn', true);
        this.setDisabled('stop-preview-btn', true);

        // Stop RTMP preview refresh if running
        this.stopRTMPPreviewRefresh();
    },

    setText(id, text) {
        const el = document.getElementById(id);
        if (el) el.textContent = text;
    },

    setDisabled(id, disabled) {
        const el = document.getElementById(id);
        if (el) {
            el.disabled = disabled;
        } else {
            // Log if button doesn't exist (only for park/unpark buttons)
            if (id.includes('park')) {
                console.warn(`[setDisabled] Button not found: ${id}`);
            }
        }
    },

    showStatus(message, type = 'info') {
        // Log to main status console (persistent, always visible)
        const consoleMessages = document.getElementById('status-console-messages');
        if (!consoleMessages) return;

        const timestamp = new Date().toLocaleTimeString('en-US', { hour12: false });
        const line = document.createElement('div');
        line.style.padding = '2px 0';

        let color = '#ccc';
        let icon = '';
        if (type === 'error') {
            color = '#d9534f';
            icon = '✗ ';
        } else if (type === 'success') {
            color = '#5cb85c';
            icon = '✓ ';
        } else if (type === 'info') {
            color = '#4a9eff';
            icon = '⚡ ';
        }

        line.style.color = color;
        line.innerHTML = `<span style="color: #888;">[${timestamp}]</span> ${icon}${message}`;

        consoleMessages.appendChild(line);

        // Keep max 50 messages (shows ~5-7 visible lines with scrollbar for older messages)
        const messages = consoleMessages.children;
        if (messages.length > 50) {
            consoleMessages.removeChild(messages[0]);
        }

        // Auto-scroll to bottom of messages div
        consoleMessages.scrollTop = consoleMessages.scrollHeight;
    },

    updateImageList(images) {
        const listEl = document.getElementById('image-list');
        if (!listEl) return;

        if (images.length === 0) {
            listEl.innerHTML = '<p class="text-secondary">No images available</p>';
            return;
        }

        listEl.innerHTML = images.map(img => `
            <div class="image-item">
                <span>${img.filename}</span>
                <button class="btn btn-sm btn-secondary" onclick="TelescopeControls.downloadImage('${img.filename}')">Download</button>
            </div>
        `).join('');
    },

    async downloadImage(filename) {
        window.open(`/api/telescope/images/download?filename=${encodeURIComponent(filename)}`, '_blank');
    }
};

// Initialize when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => TelescopeControls.init());
} else {
    TelescopeControls.init();
}
