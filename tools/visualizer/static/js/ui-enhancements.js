/**
 * UI Enhancements - Professional Finishing Touches
 * 
 * Adds theme switching, keyboard navigation, accessibility features,
 * animations, and responsive behavior enhancements.
 */

class UIEnhancements {
    constructor() {
        this.currentTheme = 'light';
        this.keyboardHintsVisible = false;
        this.toastContainer = null;
        this.loadingOverlay = null;
        this.animations = {
            fast: 150,
            normal: 300,
            slow: 500
        };
        
        this.init();
    }
    
    /**
     * Initialize all UI enhancements
     */
    init() {
        this.createThemeToggle();
        this.setupKeyboardNavigation();
        this.setupAccessibility();
        this.setupToastSystem();
        this.setupLoadingSystem();
        this.setupResponsiveEnhancements();
        this.initializeTheme();
        this.setupAnimationHelpers();
        this.setupGestureSupport();
        
        console.log('UI Enhancements initialized');
    }
    
    /**
     * Create and setup theme toggle button
     */
    createThemeToggle() {
        const themeToggle = document.createElement('button');
        themeToggle.className = 'theme-toggle';
        themeToggle.innerHTML = '🌙';
        themeToggle.title = 'Toggle Dark Mode (Alt+T)';
        themeToggle.setAttribute('aria-label', 'Toggle dark mode');
        
        themeToggle.addEventListener('click', () => this.toggleTheme());
        
        document.body.appendChild(themeToggle);
        this.themeToggle = themeToggle;
    }
    
    /**
     * Toggle between light and dark themes
     */
    toggleTheme() {
        this.themeToggle.classList.add('rotating');
        document.body.classList.add('theme-transitioning');
        
        setTimeout(() => {
            this.currentTheme = this.currentTheme === 'light' ? 'dark' : 'light';
            document.documentElement.setAttribute('data-theme', this.currentTheme);
            document.body.classList.toggle('dark-theme', this.currentTheme === 'dark');
            
            // Update toggle icon
            this.themeToggle.innerHTML = this.currentTheme === 'dark' ? '☀️' : '🌙';
            this.themeToggle.title = `Toggle ${this.currentTheme === 'dark' ? 'Light' : 'Dark'} Mode (Alt+T)`;
            
            // Save preference
            localStorage.setItem('theme-preference', this.currentTheme);
            
            this.showToast('Theme Changed', `Switched to ${this.currentTheme} mode`, 'success');
        }, this.animations.fast);
        
        setTimeout(() => {
            this.themeToggle.classList.remove('rotating');
            document.body.classList.remove('theme-transitioning');
        }, this.animations.slow);
    }
    
    /**
     * Initialize theme from saved preference or system preference
     */
    initializeTheme() {
        const savedTheme = localStorage.getItem('theme-preference');
        const systemPrefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
        
        this.currentTheme = savedTheme || (systemPrefersDark ? 'dark' : 'light');
        
        if (this.currentTheme === 'dark') {
            document.documentElement.setAttribute('data-theme', 'dark');
            document.body.classList.add('dark-theme');
            this.themeToggle.innerHTML = '☀️';
        }
        
        // Listen for system theme changes
        window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', (e) => {
            if (!localStorage.getItem('theme-preference')) {
                this.currentTheme = e.matches ? 'dark' : 'light';
                document.documentElement.setAttribute('data-theme', this.currentTheme);
                document.body.classList.toggle('dark-theme', this.currentTheme === 'dark');
                this.themeToggle.innerHTML = this.currentTheme === 'dark' ? '☀️' : '🌙';
            }
        });
    }
    
    /**
     * Setup comprehensive keyboard navigation
     */
    setupKeyboardNavigation() {
        // Add skip link for accessibility
        this.createSkipLink();
        
        // Global keyboard shortcuts
        document.addEventListener('keydown', (e) => {
            // Don't interfere with form inputs
            if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA') {
                return;
            }
            
            // Alt key combinations
            if (e.altKey) {
                switch (e.key.toLowerCase()) {
                    case 't':
                        e.preventDefault();
                        this.toggleTheme();
                        break;
                    case 'h':
                        e.preventDefault();
                        this.toggleKeyboardHints();
                        break;
                    case 'k':
                        e.preventDefault();
                        this.focusNextFocusable();
                        break;
                    case 'j':
                        e.preventDefault();
                        this.focusPreviousFocusable();
                        break;
                }
            }
            
            // Escape key actions
            if (e.key === 'Escape') {
                this.hideKeyboardHints();
                this.hideAllToasts();
                this.closeModals();
            }
            
            // Tab navigation enhancement
            if (e.key === 'Tab') {
                this.highlightFocusedElement(e);
            }
        });
        
        // Show keyboard hints when user starts using keyboard navigation
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Tab' && !this.keyboardHintsVisible) {
                setTimeout(() => this.showKeyboardHints(), 1000);
            }
        });
    }
    
    /**
     * Create skip link for screen readers
     */
    createSkipLink() {
        const skipLink = document.createElement('a');
        skipLink.href = '#main-content';
        skipLink.textContent = 'Skip to main content';
        skipLink.className = 'skip-link';
        document.body.insertBefore(skipLink, document.body.firstChild);
    }
    
    /**
     * Focus next focusable element
     */
    focusNextFocusable() {
        const focusableElements = this.getFocusableElements();
        const currentIndex = focusableElements.indexOf(document.activeElement);
        const nextIndex = (currentIndex + 1) % focusableElements.length;
        
        focusableElements[nextIndex]?.focus();
        this.announceToScreenReader(`Focused: ${this.getElementDescription(focusableElements[nextIndex])}`);
    }
    
    /**
     * Focus previous focusable element
     */
    focusPreviousFocusable() {
        const focusableElements = this.getFocusableElements();
        const currentIndex = focusableElements.indexOf(document.activeElement);
        const prevIndex = currentIndex <= 0 ? focusableElements.length - 1 : currentIndex - 1;
        
        focusableElements[prevIndex]?.focus();
        this.announceToScreenReader(`Focused: ${this.getElementDescription(focusableElements[prevIndex])}`);
    }
    
    /**
     * Get all focusable elements
     */
    getFocusableElements() {
        const selector = 'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])';
        return Array.from(document.querySelectorAll(selector)).filter(el => 
            el.offsetWidth > 0 && el.offsetHeight > 0 && !el.disabled
        );
    }
    
    /**
     * Get descriptive text for an element
     */
    getElementDescription(element) {
        if (!element) return 'Unknown element';
        
        return element.getAttribute('aria-label') ||
               element.title ||
               element.textContent?.trim() ||
               element.tagName.toLowerCase();
    }
    
    /**
     * Highlight focused element for visibility
     */
    highlightFocusedElement(e) {
        // Remove existing highlights
        document.querySelectorAll('.keyboard-focused').forEach(el => {
            el.classList.remove('keyboard-focused');
        });
        
        // Add highlight to newly focused element
        setTimeout(() => {
            if (document.activeElement) {
                document.activeElement.classList.add('keyboard-focused');
            }
        }, 50);
    }
    
    /**
     * Show/hide keyboard navigation hints
     */
    toggleKeyboardHints() {
        if (this.keyboardHintsVisible) {
            this.hideKeyboardHints();
        } else {
            this.showKeyboardHints();
        }
    }
    
    /**
     * Show keyboard navigation hints
     */
    showKeyboardHints() {
        if (this.keyboardHintsVisible) return;
        
        const hints = document.createElement('div');
        hints.className = 'keyboard-hint';
        hints.innerHTML = `
            <div><strong>Keyboard Shortcuts:</strong></div>
            <div><kbd>Alt+T</kbd> Toggle theme</div>
            <div><kbd>Alt+H</kbd> Toggle this help</div>
            <div><kbd>Alt+K</kbd>/<kbd>Alt+J</kbd> Navigate elements</div>
            <div><kbd>Tab</kbd>/<kbd>Shift+Tab</kbd> Standard navigation</div>
            <div><kbd>Esc</kbd> Close dialogs/hints</div>
        `;
        
        document.body.appendChild(hints);
        this.keyboardHints = hints;
        
        setTimeout(() => hints.classList.add('show'), 100);
        this.keyboardHintsVisible = true;
        
        // Auto-hide after 10 seconds
        setTimeout(() => this.hideKeyboardHints(), 10000);
    }
    
    /**
     * Hide keyboard navigation hints
     */
    hideKeyboardHints() {
        if (!this.keyboardHintsVisible || !this.keyboardHints) return;
        
        this.keyboardHints.classList.remove('show');
        setTimeout(() => {
            if (this.keyboardHints) {
                this.keyboardHints.remove();
                this.keyboardHints = null;
            }
        }, this.animations.normal);
        
        this.keyboardHintsVisible = false;
    }
    
    /**
     * Setup accessibility enhancements
     */
    setupAccessibility() {
        // Create screen reader announcement area
        const announcements = document.createElement('div');
        announcements.id = 'accessibility-announcements';
        announcements.setAttribute('aria-live', 'polite');
        announcements.setAttribute('aria-atomic', 'true');
        announcements.style.cssText = `
            position: absolute;
            left: -10000px;
            width: 1px;
            height: 1px;
            overflow: hidden;
        `;
        document.body.appendChild(announcements);
        this.announcements = announcements;
        
        // Enhance existing elements with ARIA labels
        this.enhanceAccessibility();
        
        // Monitor for new elements
        const observer = new MutationObserver(() => {
            this.enhanceAccessibility();
        });
        
        observer.observe(document.body, {
            childList: true,
            subtree: true
        });
    }
    
    /**
     * Enhance elements with accessibility attributes
     */
    enhanceAccessibility() {
        // Add labels to buttons without them
        document.querySelectorAll('button:not([aria-label]):not([title])').forEach(btn => {
            const text = btn.textContent?.trim() || btn.innerHTML.replace(/<[^>]*>/g, '').trim();
            if (text) {
                btn.setAttribute('aria-label', text);
            }
        });
        
        // Enhance status indicators
        document.querySelectorAll('.status').forEach(status => {
            const statusText = status.textContent;
            status.setAttribute('aria-label', `Status: ${statusText}`);
        });
        
        // Enhance interactive cards
        document.querySelectorAll('.tdd-cycle-card').forEach((card, index) => {
            if (!card.hasAttribute('tabindex')) {
                card.setAttribute('tabindex', '0');
                card.setAttribute('role', 'button');
                const storyId = card.querySelector('.story-id')?.textContent;
                const state = card.querySelector('.cycle-state')?.textContent;
                card.setAttribute('aria-label', `TDD Cycle: ${storyId}, State: ${state}`);
            }
        });
    }
    
    /**
     * Announce message to screen readers
     */
    announceToScreenReader(message) {
        if (this.announcements) {
            this.announcements.textContent = message;
            setTimeout(() => {
                this.announcements.textContent = '';
            }, 1000);
        }
    }
    
    /**
     * Setup toast notification system
     */
    setupToastSystem() {
        this.toastContainer = document.createElement('div');
        this.toastContainer.className = 'toast-container';
        document.body.appendChild(this.toastContainer);
    }
    
    /**
     * Show toast notification
     */
    showToast(title, message, type = 'info', duration = 5000) {
        const toast = document.createElement('div');
        toast.className = `toast ${type}`;
        
        const toastId = 'toast-' + Date.now();
        toast.innerHTML = `
            <div class="toast-title">${title}</div>
            <div class="toast-message">${message}</div>
            <button class="toast-close" aria-label="Close notification">×</button>
        `;
        
        const closeBtn = toast.querySelector('.toast-close');
        closeBtn.addEventListener('click', () => this.removeToast(toast));
        
        this.toastContainer.appendChild(toast);
        
        // Auto-remove after duration
        if (duration > 0) {
            setTimeout(() => this.removeToast(toast), duration);
        }
        
        // Announce to screen readers
        this.announceToScreenReader(`${title}: ${message}`);
        
        return toast;
    }
    
    /**
     * Remove toast notification
     */
    removeToast(toast) {
        if (!toast || !toast.parentNode) return;
        
        toast.classList.add('removing');
        setTimeout(() => {
            if (toast.parentNode) {
                toast.parentNode.removeChild(toast);
            }
        }, this.animations.normal);
    }
    
    /**
     * Hide all toast notifications
     */
    hideAllToasts() {
        const toasts = this.toastContainer.querySelectorAll('.toast');
        toasts.forEach(toast => this.removeToast(toast));
    }
    
    /**
     * Setup loading overlay system
     */
    setupLoadingSystem() {
        // Create loading overlay
        this.loadingOverlay = document.createElement('div');
        this.loadingOverlay.className = 'loading-overlay';
        this.loadingOverlay.style.display = 'none';
        this.loadingOverlay.innerHTML = `
            <div class="loading-content">
                <div class="loading-spinner-large"></div>
                <div class="loading-text">Loading...</div>
            </div>
        `;
        document.body.appendChild(this.loadingOverlay);
    }
    
    /**
     * Show loading overlay
     */
    showLoading(text = 'Loading...') {
        if (this.loadingOverlay) {
            this.loadingOverlay.querySelector('.loading-text').textContent = text;
            this.loadingOverlay.style.display = 'flex';
            this.announceToScreenReader(`Loading: ${text}`);
        }
    }
    
    /**
     * Hide loading overlay
     */
    hideLoading() {
        if (this.loadingOverlay) {
            this.loadingOverlay.classList.add('hide');
            setTimeout(() => {
                this.loadingOverlay.style.display = 'none';
                this.loadingOverlay.classList.remove('hide');
            }, this.animations.normal);
        }
    }
    
    /**
     * Setup responsive behavior enhancements
     */
    setupResponsiveEnhancements() {
        // Viewport size monitoring
        let resizeTimeout;
        window.addEventListener('resize', () => {
            clearTimeout(resizeTimeout);
            resizeTimeout = setTimeout(() => {
                this.handleViewportChange();
            }, 250);
        });
        
        // Initial setup
        this.handleViewportChange();
        
        // Orientation change handling
        window.addEventListener('orientationchange', () => {
            setTimeout(() => this.handleViewportChange(), 500);
        });
    }
    
    /**
     * Handle viewport size changes
     */
    handleViewportChange() {
        const width = window.innerWidth;
        const height = window.innerHeight;
        
        // Update CSS custom properties for JavaScript access
        document.documentElement.style.setProperty('--viewport-width', width + 'px');
        document.documentElement.style.setProperty('--viewport-height', height + 'px');
        
        // Adjust UI for small screens
        if (width < 768) {
            document.body.classList.add('mobile-layout');
            this.adjustForMobile();
        } else {
            document.body.classList.remove('mobile-layout');
            this.adjustForDesktop();
        }
        
        // Handle very small screens
        if (width < 576) {
            document.body.classList.add('small-screen');
        } else {
            document.body.classList.remove('small-screen');
        }
    }
    
    /**
     * Adjust UI for mobile devices
     */
    adjustForMobile() {
        // Move theme toggle for mobile
        if (this.themeToggle) {
            this.themeToggle.style.top = '10px';
            this.themeToggle.style.right = '10px';
            this.themeToggle.style.width = '44px';
            this.themeToggle.style.height = '44px';
        }
        
        // Adjust toast container for mobile
        if (this.toastContainer) {
            this.toastContainer.style.left = '10px';
            this.toastContainer.style.right = '10px';
            this.toastContainer.style.maxWidth = 'none';
        }
    }
    
    /**
     * Adjust UI for desktop
     */
    adjustForDesktop() {
        // Reset theme toggle position
        if (this.themeToggle) {
            this.themeToggle.style.top = '20px';
            this.themeToggle.style.right = '20px';
            this.themeToggle.style.width = '50px';
            this.themeToggle.style.height = '50px';
        }
        
        // Reset toast container
        if (this.toastContainer) {
            this.toastContainer.style.left = '';
            this.toastContainer.style.right = '20px';
            this.toastContainer.style.maxWidth = '400px';
        }
    }
    
    /**
     * Setup animation helpers
     */
    setupAnimationHelpers() {
        // Intersection Observer for scroll animations
        if ('IntersectionObserver' in window) {
            const observerOptions = {
                threshold: 0.1,
                rootMargin: '0px 0px -50px 0px'
            };
            
            const observer = new IntersectionObserver((entries) => {
                entries.forEach(entry => {
                    if (entry.isIntersecting) {
                        entry.target.classList.add('in-view');
                        this.triggerAnimation(entry.target);
                    }
                });
            }, observerOptions);
            
            // Observe animated elements
            document.querySelectorAll('.diagram-container, .tdd-cycle-card, .status-item').forEach(el => {
                observer.observe(el);
            });
        }
        
        // Reduced motion support
        if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
            document.body.classList.add('reduced-motion');
        }
    }
    
    /**
     * Trigger animation for element
     */
    triggerAnimation(element) {
        // Add staggered animation delays for groups
        const siblings = Array.from(element.parentNode.children);
        const index = siblings.indexOf(element);
        
        element.style.animationDelay = `${index * 100}ms`;
        element.classList.add('animate');
    }
    
    /**
     * Setup gesture support for touch devices
     */
    setupGestureSupport() {
        if ('ontouchstart' in window) {
            let startX, startY, startTime;
            
            document.addEventListener('touchstart', (e) => {
                const touch = e.touches[0];
                startX = touch.clientX;
                startY = touch.clientY;
                startTime = Date.now();
            }, { passive: true });
            
            document.addEventListener('touchend', (e) => {
                if (!startX || !startY) return;
                
                const touch = e.changedTouches[0];
                const endX = touch.clientX;
                const endY = touch.clientY;
                const endTime = Date.now();
                
                const deltaX = endX - startX;
                const deltaY = endY - startY;
                const deltaTime = endTime - startTime;
                
                // Detect swipe gestures
                if (Math.abs(deltaX) > 50 && Math.abs(deltaY) < 100 && deltaTime < 300) {
                    if (deltaX > 0) {
                        this.handleSwipeRight();
                    } else {
                        this.handleSwipeLeft();
                    }
                }
                
                // Reset
                startX = startY = null;
            }, { passive: true });
        }
    }
    
    /**
     * Handle swipe right gesture
     */
    handleSwipeRight() {
        // Could open chat panel on mobile
        this.announceToScreenReader('Swipe right detected');
    }
    
    /**
     * Handle swipe left gesture
     */
    handleSwipeLeft() {
        // Could close chat panel on mobile
        this.announceToScreenReader('Swipe left detected');
    }
    
    /**
     * Close any open modals
     */
    closeModals() {
        document.querySelectorAll('.modal.show').forEach(modal => {
            modal.classList.remove('show');
        });
    }
    
    /**
     * Add CSS class with animation
     */
    addClassWithAnimation(element, className, duration = this.animations.normal) {
        element.classList.add(className);
        if (duration > 0) {
            setTimeout(() => element.classList.remove(className), duration);
        }
    }
    
    /**
     * Smooth scroll to element
     */
    scrollToElement(element, offset = 0) {
        if (!element) return;
        
        const rect = element.getBoundingClientRect();
        const scrollTop = window.pageYOffset + rect.top - offset;
        
        window.scrollTo({
            top: scrollTop,
            behavior: 'smooth'
        });
    }
    
    /**
     * Public API for other components
     */
    getAPI() {
        return {
            showToast: this.showToast.bind(this),
            hideToast: this.removeToast.bind(this),
            showLoading: this.showLoading.bind(this),
            hideLoading: this.hideLoading.bind(this),
            toggleTheme: this.toggleTheme.bind(this),
            announce: this.announceToScreenReader.bind(this),
            animate: this.addClassWithAnimation.bind(this),
            scrollTo: this.scrollToElement.bind(this),
            currentTheme: () => this.currentTheme
        };
    }
}

// Initialize UI enhancements when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        window.uiEnhancements = new UIEnhancements();
        window.UI = window.uiEnhancements.getAPI();
    });
} else {
    window.uiEnhancements = new UIEnhancements();
    window.UI = window.uiEnhancements.getAPI();
}

// Export for module usage
if (typeof module !== 'undefined' && module.exports) {
    module.exports = UIEnhancements;
}