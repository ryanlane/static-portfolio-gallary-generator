/**
 * Modal System - Reusable modal component
 * Usage: ModalSystem.show(options)
 */

console.log('Loading modal system...');

class ModalSystem {
    constructor() {
        console.log('ModalSystem constructor called');
        this.currentModal = null;
        this.init();
    }

    init() {
        console.log('ModalSystem init called');
        // Create modal container if it doesn't exist
        if (!document.getElementById('modal-container')) {
            const container = document.createElement('div');
            container.id = 'modal-container';
            document.body.appendChild(container);
            console.log('Created modal container');
        } else {
            console.log('Modal container already exists');
        }

        // Create toast container if it doesn't exist
        if (!document.getElementById('toast-container')) {
            const toastContainer = document.createElement('div');
            toastContainer.id = 'toast-container';
            toastContainer.style.cssText = `
                position: fixed;
                top: 20px;
                right: 20px;
                z-index: 10000;
                display: flex;
                flex-direction: column;
                gap: 10px;
                pointer-events: none;
            `;
            document.body.appendChild(toastContainer);
            console.log('Created toast container');
        }

        // Add global event listeners
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape' && this.currentModal) {
                this.hide();
            }
        });
        console.log('ModalSystem initialized');
    }

    /**
     * Show a modal
     * @param {Object} options - Modal configuration
     * @param {string} options.id - Unique modal ID
     * @param {string} options.type - Modal type: 'warning', 'success', or null for normal
     * @param {string} options.title - Modal title
     * @param {string} options.body - Modal body content (HTML)
     * @param {string} options.confirmText - Confirm button text
     * @param {string} options.confirmClass - Confirm button CSS class
     * @param {string} options.confirmIcon - Confirm button icon
     * @param {string} options.cancelText - Cancel button text
     * @param {Function} options.onConfirm - Callback for confirm action
     * @param {Function} options.onCancel - Callback for cancel action
     * @param {boolean} options.showCancel - Whether to show cancel button (default: true)
     */
    show(options) {
        const {
            id = 'dynamic-modal',
            type = '',
            title = 'Confirm',
            body = '',
            confirmText = 'Confirm',
            confirmClass = 'btn-primary',
            confirmIcon = '',
            cancelText = 'Cancel',
            onConfirm = null,
            onCancel = null,
            showCancel = true
        } = options;

        // Create modal HTML
        const modalHTML = `
            <div id="${id}" class="modal${type ? ' ' + type : ''}">
                <div class="modal-content">
                    <div class="modal-header">
                        <h3>${title}</h3>
                        <button class="modal-close" onclick="window.ModalSystem.hide()">&times;</button>
                    </div>
                    <div class="modal-body">
                        ${body}
                    </div>
                    <div class="modal-footer">
                        ${showCancel ? `<button class="btn btn-secondary" onclick="window.ModalSystem.cancel()">${cancelText}</button>` : ''}
                        <button class="btn ${confirmClass}" onclick="window.ModalSystem.confirmAction()">
                            ${confirmIcon ? `<i class="icon">${confirmIcon}</i>` : ''}
                            ${confirmText}
                        </button>
                    </div>
                </div>
            </div>
        `;

        // Add modal to container
        const container = document.getElementById('modal-container');
        container.innerHTML = modalHTML;

        // Store callbacks
        this.currentModal = {
            id,
            onConfirm,
            onCancel
        };

        // Show modal
        document.getElementById(id).style.display = 'block';

        // Add click outside to close
        document.getElementById(id).addEventListener('click', (e) => {
            if (e.target.id === id) {
                this.hide();
            }
        });
    }

    /**
     * Hide the current modal
     */
    hide() {
        if (this.currentModal) {
            const modal = document.getElementById(this.currentModal.id);
            if (modal) {
                modal.style.display = 'none';
                // Remove modal after animation
                setTimeout(() => {
                    const container = document.getElementById('modal-container');
                    container.innerHTML = '';
                }, 300);
            }
            this.currentModal = null;
        }
    }

    /**
     * Handle confirm action
     */
    confirmAction() {
        if (this.currentModal && this.currentModal.onConfirm) {
            const result = this.currentModal.onConfirm();
            // Only close modal if callback doesn't return false
            if (result !== false) {
                this.hide();
            }
        } else {
            this.hide();
        }
    }

    /**
     * Handle cancel action
     */
    cancel() {
        if (this.currentModal && this.currentModal.onCancel) {
            this.currentModal.onCancel();
        }
        this.hide();
    }

    /**
     * Show a confirmation dialog
     * @param {string} message - Confirmation message
     * @param {Function} onConfirm - Callback for confirm
     * @param {Object} options - Additional options
     */
    confirmDialog(message, onConfirm, options = {}) {
        this.show({
            type: 'warning',
            title: '⚠️ Confirm Action',
            body: `<p>${message}</p>`,
            confirmText: 'Confirm',
            confirmClass: 'btn-danger',
            onConfirm,
            ...options
        });
    }

    /**
     * Show a delete confirmation dialog
     * @param {string} itemName - Name of item to delete
     * @param {Function} onConfirm - Callback for confirm
     * @param {Object} options - Additional options
     */
    confirmDelete(itemName, onConfirm, options = {}) {
        this.show({
            type: 'warning',
            title: '⚠️ Delete Confirmation',
            body: `<p>Are you sure you want to delete "${itemName}"?</p><p>This action cannot be undone.</p>`,
            confirmText: 'Delete',
            confirmClass: 'btn-danger',
            confirmIcon: '🗑️',
            onConfirm,
            ...options
        });
    }

    /**
     * Show a success message
     * @param {string} message - Success message
     * @param {Function} onConfirm - Callback for confirm
     * @param {Object} options - Additional options
     */
    success(message, onConfirm = null, options = {}) {
        this.show({
            type: 'success',
            title: '✅ Success',
            body: `<p>${message}</p>`,
            confirmText: 'OK',
            confirmClass: 'btn-success',
            showCancel: false,
            onConfirm,
            ...options
        });
    }

    /**
     * Show a toast notification
     * @param {string} message - Toast message
     * @param {string} type - Toast type: 'success', 'error', 'warning', 'info'
     * @param {number} duration - Duration in milliseconds (default: 3000)
     */
    toast(message, type = 'success', duration = 3000) {
        const toastId = 'toast-' + Date.now();
        const icons = {
            success: '✅',
            error: '❌',
            warning: '⚠️',
            info: 'ℹ️'
        };
        
        const colors = {
            success: '#d4edda',
            error: '#f8d7da',
            warning: '#fff3cd',
            info: '#d1ecf1'
        };

        const borderColors = {
            success: '#c3e6cb',
            error: '#f5c6cb',
            warning: '#ffeaa7',
            info: '#bee5eb'
        };

        const textColors = {
            success: '#155724',
            error: '#721c24',
            warning: '#856404',
            info: '#0c5460'
        };

        const toastHTML = `
            <div id="${toastId}" class="toast" style="
                background-color: ${colors[type]};
                border: 1px solid ${borderColors[type]};
                color: ${textColors[type]};
                padding: 12px 16px;
                border-radius: 6px;
                box-shadow: 0 2px 8px rgba(0,0,0,0.1);
                min-width: 300px;
                max-width: 400px;
                pointer-events: auto;
                cursor: pointer;
                opacity: 0;
                transform: translateX(100%);
                transition: all 0.3s ease-in-out;
                display: flex;
                align-items: center;
                gap: 8px;
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                font-size: 14px;
                line-height: 1.4;
            ">
                <span style="font-size: 16px;">${icons[type]}</span>
                <span style="flex: 1;">${message}</span>
                <button style="
                    background: none;
                    border: none;
                    color: ${textColors[type]};
                    cursor: pointer;
                    font-size: 18px;
                    line-height: 1;
                    padding: 0;
                    margin-left: 8px;
                    opacity: 0.7;
                " onclick="window.ModalSystem.removeToast('${toastId}')">&times;</button>
            </div>
        `;

        const container = document.getElementById('toast-container');
        container.insertAdjacentHTML('beforeend', toastHTML);

        const toastElement = document.getElementById(toastId);
        
        // Animate in
        setTimeout(() => {
            toastElement.style.opacity = '1';
            toastElement.style.transform = 'translateX(0)';
        }, 10);

        // Auto remove after duration
        setTimeout(() => {
            this.removeToast(toastId);
        }, duration);

        // Click to dismiss
        toastElement.addEventListener('click', () => {
            this.removeToast(toastId);
        });

        return toastId;
    }

    /**
     * Remove a toast notification
     * @param {string} toastId - Toast ID to remove
     */
    removeToast(toastId) {
        const toast = document.getElementById(toastId);
        if (toast) {
            toast.style.opacity = '0';
            toast.style.transform = 'translateX(100%)';
            setTimeout(() => {
                if (toast.parentNode) {
                    toast.parentNode.removeChild(toast);
                }
            }, 300);
        }
    }
}

// Create global instance
console.log('Creating global ModalSystem instance...');
window.ModalSystem = new ModalSystem();
console.log('ModalSystem created:', window.ModalSystem);

// Convenience functions for common use cases
console.log('Setting up convenience functions...');
window.showConfirmDialog = (message, onConfirm, options) => {
    console.log('showConfirmDialog called:', message);
    return window.ModalSystem.confirmDialog(message, onConfirm, options);
};
window.showDeleteDialog = (itemName, onConfirm, options) => {
    console.log('showDeleteDialog called:', itemName);
    return window.ModalSystem.confirmDelete(itemName, onConfirm, options);
};
window.showSuccessDialog = (message, onConfirm, options) => {
    console.log('showSuccessDialog called:', message);
    return window.ModalSystem.success(message, onConfirm, options);
};
window.showToast = (message, type, duration) => {
    console.log('showToast called:', message, type);
    return window.ModalSystem.toast(message, type, duration);
};

console.log('Modal system setup complete!');
