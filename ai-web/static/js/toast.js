/**
 * Toast Notification System
 * Modern toast notifications for AI-WRTS System
 */

class ToastManager {
    constructor() {
        this.container = document.querySelector('.toast-container');
        if (!this.container) {
            this.container = document.createElement('div');
            this.container.className = 'toast-container';
            document.body.appendChild(this.container);
        }
        this.toastTemplate = document.getElementById('toast-template');
        this.defaultDuration = 5000; // 5 seconds
    }

    /**
     * Show a toast notification
     * @param {string} message - The message to display
     * @param {string} type - Type: 'success', 'error', 'warning', 'info'
     * @param {number} duration - Duration in milliseconds (0 = no auto-dismiss)
     */
    show(message, type = 'info', duration = null) {
        if (!message) return;

        const toast = this.createToast(message, type);
        this.container.appendChild(toast);

        const bsToast = new bootstrap.Toast(toast, {
            autohide: duration !== 0,
            delay: duration || this.defaultDuration
        });

        bsToast.show();

        // Remove from DOM after hiding
        toast.addEventListener('hidden.bs.toast', () => {
            toast.remove();
        });

        return toast;
    }

    /**
     * Create toast element
     */
    createToast(message, type) {
        const template = this.toastTemplate ? this.toastTemplate.content.cloneNode(true) : this.createFallbackTemplate();
        const toast = template.querySelector('.toast');
        
        // Set type-specific classes and icon
        const config = this.getTypeConfig(type);
        toast.classList.add(config.bgClass);
        toast.querySelector('.toast-icon').className = `toast-icon ${config.icon}`;
        toast.querySelector('.toast-message').textContent = message;

        return toast;
    }

    /**
     * Create fallback template if template element doesn't exist
     */
    createFallbackTemplate() {
        const div = document.createElement('div');
        div.innerHTML = `
            <div class="toast align-items-center text-white border-0" role="alert">
                <div class="d-flex">
                    <div class="toast-body">
                        <div class="d-flex align-items-center gap-2">
                            <i class="toast-icon"></i>
                            <span class="toast-message"></span>
                        </div>
                    </div>
                    <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
                </div>
            </div>
        `;
        return div;
    }

    /**
     * Get configuration for toast type
     */
    getTypeConfig(type) {
        const configs = {
            success: {
                bgClass: 'bg-success',
                icon: 'fas fa-check-circle'
            },
            error: {
                bgClass: 'bg-danger',
                icon: 'fas fa-exclamation-circle'
            },
            warning: {
                bgClass: 'bg-warning',
                icon: 'fas fa-exclamation-triangle'
            },
            info: {
                bgClass: 'bg-info',
                icon: 'fas fa-info-circle'
            }
        };

        return configs[type] || configs.info;
    }

    /**
     * Show success toast
     */
    success(message, duration = null) {
        return this.show(message, 'success', duration);
    }

    /**
     * Show error toast
     */
    error(message, duration = null) {
        return this.show(message, 'error', duration);
    }

    /**
     * Show warning toast
     */
    warning(message, duration = null) {
        return this.show(message, 'warning', duration);
    }

    /**
     * Show info toast
     */
    info(message, duration = null) {
        return this.show(message, 'info', duration);
    }
}

// Initialize global toast manager
const toastManager = new ToastManager();

// Global function for easy access
function showToast(message, type = 'info', duration = null) {
    return toastManager.show(message, type, duration);
}

// Auto-convert Flask flash messages to toasts
document.addEventListener('DOMContentLoaded', function() {
    // Find all flash messages
    const flashMessages = document.querySelectorAll('.alert[role="alert"]');
    
    flashMessages.forEach(alert => {
        // Determine type from alert classes
        let type = 'info';
        if (alert.classList.contains('alert-success')) type = 'success';
        else if (alert.classList.contains('alert-danger') || alert.classList.contains('alert-error')) type = 'error';
        else if (alert.classList.contains('alert-warning')) type = 'warning';
        else if (alert.classList.contains('alert-info')) type = 'info';

        // Extract message
        const message = alert.textContent.trim();
        
        // Show toast
        if (message) {
            showToast(message, type);
        }

        // Hide original alert
        alert.style.display = 'none';
    });
});

