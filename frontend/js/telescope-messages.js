// ==========================================
// TELESCOPE MESSAGES LOGGER
// Logs all telescope communications to the messages panel
// ==========================================

const TelescopeMessages = {
    maxMessages: 100,
    messages: [],

    init() {
        this.setupClearButton();
        console.log('TelescopeMessages: Initialized');
    },

    setupClearButton() {
        const clearBtn = document.getElementById('clear-messages-btn');
        if (clearBtn) {
            clearBtn.addEventListener('click', () => this.clear());
        }
    },

    log(type, message, data = null) {
        const timestamp = new Date().toLocaleTimeString('en-US', { hour12: false });

        const entry = {
            timestamp,
            type, // 'command', 'response', 'event', 'error'
            message,
            data
        };

        this.messages.push(entry);

        // Limit message history
        if (this.messages.length > this.maxMessages) {
            this.messages.shift();
        }

        this.display();
    },

    logCommand(command, params = {}) {
        const msg = `→ ${command}`;
        this.log('command', msg, params);
    },

    logResponse(command, result, success = true) {
        const icon = success ? '✓' : '✗';
        const msg = `← ${icon} ${command}`;
        this.log(success ? 'response' : 'error', msg, result);
    },

    logEvent(event, details) {
        const msg = `⚡ ${event}`;
        this.log('event', msg, details);
    },

    logError(error) {
        this.log('error', `✗ Error: ${error}`, null);
    },

    display() {
        const container = document.getElementById('telescope-messages');
        if (!container) return;

        if (this.messages.length === 0) {
            container.innerHTML = '<div class="empty-state" style="color: #888; padding: 8px;">No messages</div>';
            return;
        }

        // Build HTML for all messages
        const html = this.messages.map(msg => {
            let colorClass = '';
            switch (msg.type) {
                case 'command':
                    colorClass = 'color: #4a9eff;'; // Blue
                    break;
                case 'response':
                    colorClass = 'color: #5cb85c;'; // Green
                    break;
                case 'event':
                    colorClass = 'color: #f0ad4e;'; // Yellow/Orange
                    break;
                case 'error':
                    colorClass = 'color: #d9534f;'; // Red
                    break;
            }

            return `
                <div style="padding: 2px 4px; ${colorClass}">
                    <span style="color: #888;">[${msg.timestamp}]</span> ${msg.message}
                </div>
            `;
        }).join('');

        container.innerHTML = html;

        // Auto-scroll to bottom
        container.scrollTop = container.scrollHeight;
    },

    clear() {
        this.messages = [];
        this.display();
    }
};

// Initialize when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => TelescopeMessages.init());
} else {
    TelescopeMessages.init();
}
