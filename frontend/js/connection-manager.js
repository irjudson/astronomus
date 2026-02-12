// ==========================================
// CONNECTION MANAGER
// ==========================================

const ConnectionManager = {
    reconnectAttempts: 0,
    maxReconnectAttempts: 5,
    reconnectTimeout: null,

    init() {
        this.loadDevices();
        this.setupEventListeners();
    },

    setupEventListeners() {
        const deviceSelect = document.getElementById('device-select');
        const connectBtnCompact = document.getElementById('connect-btn-compact');

        if (deviceSelect) {
            deviceSelect.addEventListener('change', (e) => {
                const deviceId = e.target.value;
                if (connectBtnCompact) connectBtnCompact.disabled = !deviceId;
                AppState.connection.deviceId = deviceId;
            });
        }

        if (connectBtnCompact) {
            connectBtnCompact.addEventListener('click', () => {
                if (AppState.connection.isConnected) {
                    this.disconnect();
                } else {
                    this.connect();
                }
            });
        }
    },

    async loadDevices() {
        try {
            const response = await fetch('/api/settings/devices');

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}`);
            }

            const devices = await response.json();

            const select = document.getElementById('device-select');
            if (!select) return;

            select.innerHTML = '<option value="">Select device...</option>';

            let defaultDeviceId = null;
            devices.forEach(device => {
                const option = document.createElement('option');
                option.value = device.id;
                option.dataset.host = device.control_host;
                option.dataset.port = device.control_port || 4700;
                option.textContent = `${device.name} (${device.control_host})`;
                select.appendChild(option);

                if (device.is_default) {
                    defaultDeviceId = device.id;
                }
            });

            // Auto-select default device if no device is already selected
            if (!AppState.connection.deviceId && defaultDeviceId) {
                AppState.connection.deviceId = defaultDeviceId;
            }

            // Restore or select default device
            if (AppState.connection.deviceId) {
                select.value = AppState.connection.deviceId;
                const connectBtnCompact = document.getElementById('connect-btn-compact');
                if (connectBtnCompact) connectBtnCompact.disabled = false;

                // Auto-connect if enabled and not already connected
                if (AppState.preferences.autoConnect && !AppState.connection.isConnected) {
                    console.log('ConnectionManager: Auto-connecting to default device...');
                    // Small delay to ensure UI is ready
                    setTimeout(() => {
                        this.connect();
                    }, 500);
                }
            }
        } catch (error) {
            console.error('Failed to load devices:', error);
            this.showError('Failed to load devices');
        }
    },

    async connect() {
        const deviceId = AppState.connection.deviceId;
        if (!deviceId) return;

        this.updateStatus('connecting', 'Connecting...');

        try {
            if (window.TelescopeMessages) {
                TelescopeMessages.logCommand('connect', { device_id: deviceId });
            }

            const response = await fetch('/api/telescope/connect', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ device_id: parseInt(deviceId) })
            });

            if (!response.ok) {
                const errorData = await response.json();
                if (window.TelescopeMessages) {
                    TelescopeMessages.logError(`Connection failed: ${errorData.detail}`);
                }
                throw new Error(errorData.detail || 'Connection failed');
            }

            const data = await response.json();

            if (window.TelescopeMessages) {
                TelescopeMessages.logResponse('connect', 'Connected successfully', true);
            }

            AppState.connection.isConnected = true;
            AppState.connection.status = 'connected';
            this.updateStatus('connected', 'Connected');

            const connectBtnCompact = document.getElementById('connect-btn-compact');
            if (connectBtnCompact) {
                connectBtnCompact.title = 'Disconnect';
                connectBtnCompact.textContent = '⏏';
            }

            // Switch to execution context when device connects
            if (window.AppContext) {
                AppContext.switchContext('execution');
            }

            // Dispatch event for other components
            document.dispatchEvent(new Event('telescope-connected'));
        } catch (error) {
            console.error('Connection error:', error);
            this.updateStatus('error', 'Connection failed');
            this.showError(error.message || 'Failed to connect to device');
            AppState.connection.isConnected = false;
        }
    },

    async disconnect() {
        // Cancel any pending auto-reconnect when manually disconnecting
        this.cancelAutoReconnect();

        try {
            if (window.TelescopeMessages) {
                TelescopeMessages.logCommand('disconnect');
            }

            const response = await fetch('/api/telescope/disconnect', {
                method: 'POST'
            });

            if (!response.ok) {
                if (window.TelescopeMessages) {
                    TelescopeMessages.logError('Disconnect failed');
                }
                throw new Error('Disconnect failed');
            }

            if (window.TelescopeMessages) {
                TelescopeMessages.logResponse('disconnect', 'Disconnected successfully', true);
            }

            AppState.connection.isConnected = false;
            AppState.connection.status = 'disconnected';
            this.updateStatus('disconnected', 'Disconnected');

            const connectBtnCompact = document.getElementById('connect-btn-compact');
            if (connectBtnCompact) {
                connectBtnCompact.title = 'Connect';
                connectBtnCompact.textContent = '⚡';
            }

            // Dispatch event for other components
            document.dispatchEvent(new Event('telescope-disconnected'));
        } catch (error) {
            console.error('Disconnect error:', error);
            this.showError(error.message || 'Failed to disconnect');
        }
    },

    autoReconnect() {
        // Check if auto-reconnect is enabled
        if (!AppState.preferences.autoReconnect) {
            console.log('Auto-reconnect disabled, not attempting reconnection');
            return;
        }

        // Check if we've exceeded max attempts
        if (this.reconnectAttempts >= this.maxReconnectAttempts) {
            console.log(`Auto-reconnect: Max attempts (${this.maxReconnectAttempts}) reached`);
            if (window.TelescopeControls) {
                TelescopeControls.showStatus('Reconnection failed after ' + this.maxReconnectAttempts + ' attempts', 'error');
            }
            this.reconnectAttempts = 0;
            return;
        }

        // Clear any pending reconnect timeout
        if (this.reconnectTimeout) {
            clearTimeout(this.reconnectTimeout);
        }

        this.reconnectAttempts++;

        // Exponential backoff: 2s, 4s, 8s, 16s, 32s
        const delay = Math.min(2000 * Math.pow(2, this.reconnectAttempts - 1), 32000);

        console.log(`Auto-reconnect: Attempt ${this.reconnectAttempts}/${this.maxReconnectAttempts} in ${delay/1000}s`);

        if (window.TelescopeControls) {
            TelescopeControls.showStatus(`Reconnecting in ${delay/1000}s (attempt ${this.reconnectAttempts}/${this.maxReconnectAttempts})`, 'info');
        }

        this.reconnectTimeout = setTimeout(async () => {
            console.log(`Auto-reconnect: Attempting reconnection (attempt ${this.reconnectAttempts})`);

            try {
                await this.connect();

                // If successful, reset attempt counter
                if (AppState.connection.isConnected) {
                    console.log('Auto-reconnect: Successfully reconnected');
                    if (window.TelescopeControls) {
                        TelescopeControls.showStatus('Reconnected successfully', 'success');
                    }
                    this.reconnectAttempts = 0;
                }
            } catch (error) {
                console.error('Auto-reconnect: Connection attempt failed:', error);
                // Try again with next delay
                this.autoReconnect();
            }
        }, delay);
    },

    cancelAutoReconnect() {
        if (this.reconnectTimeout) {
            clearTimeout(this.reconnectTimeout);
            this.reconnectTimeout = null;
        }
        this.reconnectAttempts = 0;
    },

    updateStatus(state, text) {
        // Update compact status bar
        const compactIndicator = document.querySelector('#connection-status-compact .status-indicator');
        const compactLabel = document.querySelector('#connection-status-compact .status-label');

        if (compactIndicator) {
            compactIndicator.className = 'status-indicator ' + state;
        }

        if (compactLabel) {
            compactLabel.textContent = text;
        }
    },

    showError(message) {
        // Simple error display for now
        alert(message);
    }
};

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    ConnectionManager.init();
});
