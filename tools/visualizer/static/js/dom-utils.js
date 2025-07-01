/**
 * DOM Utilities - Shared DOM manipulation and event handling utilities
 * 
 * Consolidates common DOM operations used across all JavaScript files:
 * - Element selection and creation
 * - Event handling and delegation
 * - Class manipulation
 * - Style management
 * - Message/Toast notifications
 * - Modal management
 */

class DOMUtils {
    constructor() {
        this.messageContainer = null;
        this.toastQueue = [];
        this.isProcessingToasts = false;
        
        // Initialize utilities
        this.setupMessageContainer();
        this.setupGlobalEventDelegation();
    }
    
    /**
     * Enhanced element selector with caching and null checks
     */
    static $(selector, context = document) {
        if (typeof selector === 'string') {
            return context.querySelector(selector);
        }
        return selector; // Already an element
    }
    
    static $$(selector, context = document) {
        if (typeof selector === 'string') {
            return Array.from(context.querySelectorAll(selector));
        }
        return Array.isArray(selector) ? selector : [selector];
    }
    
    /**
     * Safe element operations with existence checks
     */
    static safeOperation(selector, operation, ...args) {
        const element = this.$(selector);
        if (element && typeof element[operation] === 'function') {
            return element[operation](...args);
        }
        return null;
    }
    
    /**
     * Create element with attributes and content
     */
    static createElement(tag, attributes = {}, content = '') {
        const element = document.createElement(tag);
        
        // Set attributes
        Object.entries(attributes).forEach(([key, value]) => {
            if (key === 'class' || key === 'className') {
                element.className = value;
            } else if (key === 'style' && typeof value === 'object') {
                Object.assign(element.style, value);
            } else if (key.startsWith('data-')) {
                element.setAttribute(key, value);
            } else {
                element[key] = value;
            }
        });
        
        // Set content
        if (typeof content === 'string') {
            element.innerHTML = content;
        } else if (content instanceof Node) {
            element.appendChild(content);
        } else if (Array.isArray(content)) {
            content.forEach(child => {
                if (typeof child === 'string') {
                    element.appendChild(document.createTextNode(child));
                } else if (child instanceof Node) {
                    element.appendChild(child);
                }
            });
        }
        
        return element;
    }
    
    /**
     * Enhanced event handling with delegation and automatic cleanup
     */
    static on(element, event, handler, options = {}) {
        const target = this.$(element);
        if (!target) return null;
        
        const wrappedHandler = (e) => {
            try {
                return handler.call(target, e);
            } catch (error) {
                console.error('Event handler error:', error);
            }
        };
        
        target.addEventListener(event, wrappedHandler, options);
        
        // Return cleanup function
        return () => target.removeEventListener(event, wrappedHandler, options);
    }
    
    static off(element, event, handler, options = {}) {
        const target = this.$(element);
        if (target) {
            target.removeEventListener(event, handler, options);
        }
    }
    
    /**
     * Event delegation for dynamic content
     */
    static delegate(container, selector, event, handler) {
        const containerEl = this.$(container);
        if (!containerEl) return null;
        
        const delegatedHandler = (e) => {
            const target = e.target.closest(selector);
            if (target && containerEl.contains(target)) {
                return handler.call(target, e);
            }
        };
        
        containerEl.addEventListener(event, delegatedHandler);
        return () => containerEl.removeEventListener(event, delegatedHandler);
    }
    
    /**
     * Class manipulation utilities
     */
    static addClass(element, ...classes) {
        const el = this.$(element);
        if (el) el.classList.add(...classes);
        return el;
    }
    
    static removeClass(element, ...classes) {
        const el = this.$(element);
        if (el) el.classList.remove(...classes);
        return el;
    }
    
    static toggleClass(element, className, force) {
        const el = this.$(element);
        if (el) return el.classList.toggle(className, force);
        return false;
    }
    
    static hasClass(element, className) {
        const el = this.$(element);
        return el ? el.classList.contains(className) : false;
    }
    
    /**
     * Style utilities
     */
    static setStyle(element, styles) {
        const el = this.$(element);
        if (el && typeof styles === 'object') {
            Object.assign(el.style, styles);
        }
        return el;
    }
    
    static getStyle(element, property) {
        const el = this.$(element);
        if (el) {
            return window.getComputedStyle(el).getPropertyValue(property);
        }
        return null;
    }
    
    /**
     * Visibility utilities
     */
    static show(element) {
        const el = this.$(element);
        if (el) {
            el.style.display = '';
            el.style.visibility = 'visible';
            el.style.opacity = '1';
        }
        return el;
    }
    
    static hide(element) {
        const el = this.$(element);
        if (el) {
            el.style.display = 'none';
        }
        return el;
    }
    
    static toggle(element, force) {
        const el = this.$(element);
        if (el) {
            const isHidden = el.style.display === 'none' || 
                           window.getComputedStyle(el).display === 'none';
            if (force !== undefined) {
                return force ? this.show(el) : this.hide(el);
            }
            return isHidden ? this.show(el) : this.hide(el);
        }
        return el;
    }
    
    /**
     * Text and content utilities
     */
    static setText(element, text) {
        const el = this.$(element);
        if (el) el.textContent = text;
        return el;
    }
    
    static setHTML(element, html) {
        const el = this.$(element);
        if (el) el.innerHTML = html;
        return el;
    }
    
    static getText(element) {
        const el = this.$(element);
        return el ? el.textContent : '';
    }
    
    static getHTML(element) {
        const el = this.$(element);
        return el ? el.innerHTML : '';
    }
    
    /**
     * Form utilities
     */
    static getValue(element) {
        const el = this.$(element);
        if (!el) return '';
        
        if (el.type === 'checkbox' || el.type === 'radio') {
            return el.checked;
        }
        return el.value || '';
    }
    
    static setValue(element, value) {
        const el = this.$(element);
        if (!el) return;
        
        if (el.type === 'checkbox' || el.type === 'radio') {
            el.checked = Boolean(value);
        } else {
            el.value = value;
        }
        return el;
    }
    
    static getFormData(form) {
        const formEl = this.$(form);
        if (!formEl) return {};
        
        const formData = new FormData(formEl);
        const data = {};
        
        for (const [key, value] of formData.entries()) {
            if (data[key]) {
                // Convert to array if multiple values
                if (!Array.isArray(data[key])) {
                    data[key] = [data[key]];
                }
                data[key].push(value);
            } else {
                data[key] = value;
            }
        }
        
        return data;
    }
    
    /**
     * Animation utilities
     */
    static fadeIn(element, duration = 300) {
        const el = this.$(element);
        if (!el) return Promise.resolve();
        
        return new Promise(resolve => {
            el.style.opacity = '0';
            el.style.display = '';
            el.style.transition = `opacity ${duration}ms ease-in-out`;
            
            requestAnimationFrame(() => {
                el.style.opacity = '1';
                setTimeout(() => {
                    el.style.transition = '';
                    resolve(el);
                }, duration);
            });
        });
    }
    
    static fadeOut(element, duration = 300) {
        const el = this.$(element);
        if (!el) return Promise.resolve();
        
        return new Promise(resolve => {
            el.style.transition = `opacity ${duration}ms ease-in-out`;
            el.style.opacity = '0';
            
            setTimeout(() => {
                el.style.display = 'none';
                el.style.transition = '';
                resolve(el);
            }, duration);
        });
    }
    
    static slideUp(element, duration = 300) {
        const el = this.$(element);
        if (!el) return Promise.resolve();
        
        return new Promise(resolve => {
            const height = el.offsetHeight;
            el.style.transition = `height ${duration}ms ease-in-out, padding ${duration}ms ease-in-out, margin ${duration}ms ease-in-out`;
            el.style.height = height + 'px';
            el.style.overflow = 'hidden';
            
            requestAnimationFrame(() => {
                el.style.height = '0';
                el.style.paddingTop = '0';
                el.style.paddingBottom = '0';
                el.style.marginTop = '0';
                el.style.marginBottom = '0';
                
                setTimeout(() => {
                    el.style.display = 'none';
                    el.style.height = '';
                    el.style.padding = '';
                    el.style.margin = '';
                    el.style.overflow = '';
                    el.style.transition = '';
                    resolve(el);
                }, duration);
            });
        });
    }
    
    /**
     * Unified message/toast system used across all components
     */
    setupMessageContainer() {
        this.messageContainer = document.createElement('div');
        this.messageContainer.id = 'global-message-container';
        this.messageContainer.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            z-index: 10000;
            pointer-events: none;
        `;
        document.body.appendChild(this.messageContainer);
    }
    
    showMessage(message, type = 'info', duration = 4000) {
        const toast = {
            message,
            type,
            duration,
            id: Date.now() + Math.random()
        };
        
        this.toastQueue.push(toast);
        
        if (!this.isProcessingToasts) {
            this.processToastQueue();
        }
        
        return toast.id;
    }
    
    processToastQueue() {
        if (this.toastQueue.length === 0) {
            this.isProcessingToasts = false;
            return;
        }
        
        this.isProcessingToasts = true;
        const toast = this.toastQueue.shift();
        
        const toastElement = this.createToastElement(toast);
        this.messageContainer.appendChild(toastElement);
        
        // Animate in
        this.fadeIn(toastElement, 300);
        
        // Auto remove
        setTimeout(() => {
            this.removeToast(toastElement);
        }, toast.duration);
        
        // Process next toast
        setTimeout(() => {
            this.processToastQueue();
        }, 150);
    }
    
    createToastElement(toast) {
        const colors = {
            success: '#4CAF50',
            error: '#f44336',
            warning: '#ff9800',
            info: '#2196F3'
        };
        
        const element = this.constructor.createElement('div', {
            class: `message-toast ${toast.type}`,
            'data-toast-id': toast.id
        });
        
        element.style.cssText = `
            background: ${colors[toast.type] || colors.info};
            color: white;
            padding: 12px 16px;
            border-radius: 4px;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
            margin-bottom: 8px;
            opacity: 0;
            transform: translateX(100%);
            transition: all 0.3s ease-out;
            pointer-events: auto;
            cursor: pointer;
            max-width: 300px;
            word-wrap: break-word;
        `;
        
        element.textContent = toast.message;
        
        // Click to dismiss
        element.addEventListener('click', () => {
            this.removeToast(element);
        });
        
        return element;
    }
    
    removeToast(element) {
        element.style.transform = 'translateX(100%)';
        element.style.opacity = '0';
        
        setTimeout(() => {
            if (element.parentNode) {
                element.parentNode.removeChild(element);
            }
        }, 300);
    }
    
    /**
     * Modal utilities used across components
     */
    static createModal(content, options = {}) {
        const {
            title = '',
            size = 'medium',
            closable = true,
            className = ''
        } = options;
        
        const modal = this.createElement('div', {
            class: `modal ${className}`,
            style: {
                position: 'fixed',
                top: '0',
                left: '0',
                width: '100%',
                height: '100%',
                background: 'rgba(0, 0, 0, 0.5)',
                zIndex: '10000',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center'
            }
        });
        
        const modalContent = this.createElement('div', {
            class: `modal-content ${size}`,
            style: {
                background: 'var(--chat-bg, #fff)',
                borderRadius: '8px',
                boxShadow: '0 4px 20px rgba(0, 0, 0, 0.15)',
                maxWidth: size === 'large' ? '800px' : size === 'small' ? '400px' : '600px',
                width: '90%',
                maxHeight: '90vh',
                overflow: 'auto'
            }
        });
        
        if (title) {
            const header = this.createElement('div', {
                class: 'modal-header',
                style: {
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                    padding: '20px',
                    borderBottom: '1px solid var(--chat-border, #eee)'
                }
            });
            
            const titleElement = this.createElement('h3', {
                style: { margin: '0', color: 'var(--chat-text, #333)' }
            }, title);
            
            header.appendChild(titleElement);
            
            if (closable) {
                const closeButton = this.createElement('button', {
                    class: 'modal-close-btn',
                    style: {
                        background: 'none',
                        border: 'none',
                        fontSize: '18px',
                        cursor: 'pointer',
                        padding: '4px',
                        color: 'var(--chat-text-muted, #666)'
                    }
                }, '×');
                
                closeButton.addEventListener('click', () => modal.remove());
                header.appendChild(closeButton);
            }
            
            modalContent.appendChild(header);
        }
        
        const body = this.createElement('div', {
            class: 'modal-body',
            style: { padding: '20px' }
        });
        
        if (typeof content === 'string') {
            body.innerHTML = content;
        } else if (content instanceof Node) {
            body.appendChild(content);
        }
        
        modalContent.appendChild(body);
        modal.appendChild(modalContent);
        
        // Close on backdrop click
        if (closable) {
            modal.addEventListener('click', (e) => {
                if (e.target === modal) {
                    modal.remove();
                }
            });
            
            // ESC key to close
            const escHandler = (e) => {
                if (e.key === 'Escape') {
                    modal.remove();
                    document.removeEventListener('keydown', escHandler);
                }
            };
            document.addEventListener('keydown', escHandler);
        }
        
        return modal;
    }
    
    static showModal(content, options = {}) {
        const modal = this.createModal(content, options);
        document.body.appendChild(modal);
        
        // Animate in
        modal.style.opacity = '0';
        requestAnimationFrame(() => {
            modal.style.transition = 'opacity 0.3s ease-out';
            modal.style.opacity = '1';
        });
        
        return modal;
    }
    
    static closeAllModals() {
        const modals = this.$$('.modal');
        modals.forEach(modal => {
            modal.style.opacity = '0';
            setTimeout(() => modal.remove(), 300);
        });
    }
    
    /**
     * Global event delegation setup
     */
    setupGlobalEventDelegation() {
        // Auto-handle common UI patterns
        this.constructor.delegate(document, '[data-toggle]', 'click', (e) => {
            const target = e.currentTarget;
            const toggleTarget = target.getAttribute('data-toggle');
            const element = this.constructor.$(toggleTarget);
            
            if (element) {
                this.constructor.toggle(element);
            }
        });
        
        this.constructor.delegate(document, '[data-dismiss="modal"]', 'click', (e) => {
            const modal = e.currentTarget.closest('.modal');
            if (modal) {
                modal.remove();
            }
        });
        
        this.constructor.delegate(document, '[data-message]', 'click', (e) => {
            const target = e.currentTarget;
            const message = target.getAttribute('data-message');
            const type = target.getAttribute('data-type') || 'info';
            
            if (message) {
                this.showMessage(message, type);
            }
        });
    }
    
    /**
     * Utility methods for common operations
     */
    static ready(callback) {
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', callback);
        } else {
            callback();
        }
    }
    
    static debounce(func, wait, immediate = false) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                timeout = null;
                if (!immediate) func.apply(this, args);
            };
            const callNow = immediate && !timeout;
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
            if (callNow) func.apply(this, args);
        };
    }
    
    static throttle(func, limit) {
        let inThrottle;
        return function(...args) {
            if (!inThrottle) {
                func.apply(this, args);
                inThrottle = true;
                setTimeout(() => inThrottle = false, limit);
            }
        };
    }
    
    static scrollToElement(element, options = {}) {
        const el = this.$(element);
        if (el) {
            el.scrollIntoView({
                behavior: 'smooth',
                block: 'center',
                inline: 'nearest',
                ...options
            });
        }
    }
    
    static getElementPosition(element) {
        const el = this.$(element);
        if (!el) return null;
        
        const rect = el.getBoundingClientRect();
        return {
            top: rect.top + window.pageYOffset,
            left: rect.left + window.pageXOffset,
            width: rect.width,
            height: rect.height,
            bottom: rect.bottom + window.pageYOffset,
            right: rect.right + window.pageXOffset
        };
    }
    
    static isElementInViewport(element) {
        const el = this.$(element);
        if (!el) return false;
        
        const rect = el.getBoundingClientRect();
        return (
            rect.top >= 0 &&
            rect.left >= 0 &&
            rect.bottom <= (window.innerHeight || document.documentElement.clientHeight) &&
            rect.right <= (window.innerWidth || document.documentElement.clientWidth)
        );
    }
}

// Create global instance
const domUtils = new DOMUtils();

// Expose utilities globally
window.DOMUtils = DOMUtils;
window.domUtils = domUtils;

// Convenience shortcuts
window.$ = DOMUtils.$;
window.$$ = DOMUtils.$$;

// Export for module usage
if (typeof module !== 'undefined' && module.exports) {
    module.exports = DOMUtils;
}

console.log('🛠️ DOM Utilities loaded and ready');