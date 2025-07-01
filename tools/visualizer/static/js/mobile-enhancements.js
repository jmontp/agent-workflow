/**
 * Mobile Enhancements - Touch interactions, swipe gestures, and mobile optimizations
 * 
 * This module enhances the Discord web visualizer for mobile devices with:
 * - Touch-friendly interactions
 * - Swipe gestures for navigation
 * - Mobile-specific UI optimizations
 * - Viewport handling
 * - Touch keyboard management
 */

class MobileEnhancements {
    constructor() {
        this.isMobile = this.detectMobile();
        this.isTablet = this.detectTablet();
        this.touchStartX = 0;
        this.touchStartY = 0;
        this.touchEndX = 0;
        this.touchEndY = 0;
        this.lastTap = 0;
        this.swipeThreshold = 50;
        this.swipeTimeout = 300;
        this.isInitialized = false;
        this.isScrolling = false;
        this.scrollTimeout = null;
        
        // Touch gesture state
        this.gestureState = {
            isScrolling: false,
            isPinching: false,
            initialDistance: 0,
            currentScale: 1
        };
        
        // Viewport management
        this.viewportHeight = window.innerHeight;
        this.keyboardOpen = false;
        
        this.initialize();
    }
    
    /**
     * Initialize mobile enhancements
     */
    initialize() {
        console.log('📱 Initializing MobileEnhancements...');
        
        // Always setup basic touch detection
        document.body.classList.toggle('touch-device', 'ontouchstart' in window);
        
        if (this.isMobile || this.isTablet) {
            this.setupTouchEvents();
            this.setupSwipeGestures();
            this.setupViewportHandling();
            this.setupTouchOptimizations();
            this.setupKeyboardHandling();
            this.addMobileCSS();
            this.optimizeForMobile();
            this.setupAccessibilityEnhancements();
            
            console.log('✅ Mobile enhancements active');
        } else {
            console.log('🖥️ Desktop detected, mobile enhancements in standby mode');
            // Still provide basic touch support for touch-enabled desktops
            this.setupBasicTouchSupport();
        }
        
        // Listen for orientation changes
        this.setupOrientationHandling();
        
        this.isInitialized = true;
    }
    
    /**
     * Detect if device is mobile
     */
    detectMobile() {
        const userAgent = navigator.userAgent.toLowerCase();
        const mobileKeywords = [
            'android', 'webos', 'iphone', 'ipad', 'ipod', 'blackberry', 
            'windows phone', 'mobile', 'opera mini'
        ];
        
        const isMobileUserAgent = mobileKeywords.some(keyword => 
            userAgent.includes(keyword)
        );
        
        const isTouchDevice = 'ontouchstart' in window || 
                             navigator.maxTouchPoints > 0 || 
                             navigator.msMaxTouchPoints > 0;
        
        const isSmallScreen = window.innerWidth <= 768;
        
        return isMobileUserAgent || (isTouchDevice && isSmallScreen);
    }
    
    /**
     * Detect if device is tablet
     */
    detectTablet() {
        const userAgent = navigator.userAgent.toLowerCase();
        const isTabletUserAgent = userAgent.includes('ipad') || 
                                 (userAgent.includes('android') && !userAgent.includes('mobile'));
        
        const isTouchDevice = 'ontouchstart' in window;
        const isTabletScreen = window.innerWidth >= 768 && window.innerWidth <= 1024;
        
        return isTabletUserAgent || (isTouchDevice && isTabletScreen);
    }
    
    /**
     * Setup touch event handlers
     */
    setupTouchEvents() {
        document.addEventListener('touchstart', this.handleTouchStart.bind(this), { passive: true });
        document.addEventListener('touchmove', this.handleTouchMove.bind(this), { passive: false });
        document.addEventListener('touchend', this.handleTouchEnd.bind(this), { passive: true });
        
        // Prevent double-tap zoom on buttons
        const buttons = document.querySelectorAll('button, .tab-control-btn, .mobile-control-btn');
        buttons.forEach(button => {
            button.addEventListener('touchend', this.preventDoubleTabZoom.bind(this));
        });
        
        // Handle pinch-to-zoom for diagrams
        document.addEventListener('gesturestart', this.handleGestureStart.bind(this), { passive: false });
        document.addEventListener('gesturechange', this.handleGestureChange.bind(this), { passive: false });
        document.addEventListener('gestureend', this.handleGestureEnd.bind(this), { passive: false });
    }
    
    /**
     * Setup swipe gesture detection
     */
    setupSwipeGestures() {
        // Chat panel swipe gestures
        const mainContent = document.getElementById('main-content');
        const chatPanel = document.querySelector('.chat-panel');
        
        if (mainContent && chatPanel) {
            this.setupAdvancedSwipeGestures(mainContent, chatPanel);
        }
        
        // Project tab swipe navigation
        const projectTabList = document.getElementById('project-tab-list');
        if (projectTabList) {
            this.setupTabSwipeNavigation(projectTabList);
        }
    }
    
    /**
     * Setup advanced swipe gestures with progressive feedback
     */
    setupAdvancedSwipeGestures(mainContent, chatPanel) {
        let startX = 0;
        let startY = 0;
        let currentX = 0;
        let isDragging = false;
        let startTime = 0;
        
        const handleTouchStart = (e) => {
            if (e.touches.length === 1) {
                startX = e.touches[0].clientX;
                startY = e.touches[0].clientY;
                currentX = startX;
                startTime = Date.now();
                isDragging = false;
                
                // Reset scroll detection
                this.isScrolling = false;
                clearTimeout(this.scrollTimeout);
            }
        };
        
        const handleTouchMove = (e) => {
            if (e.touches.length !== 1) return;
            
            currentX = e.touches[0].clientX;
            const currentY = e.touches[0].clientY;
            const deltaX = currentX - startX;
            const deltaY = currentY - startY;
            
            // Detect if this is a vertical scroll
            if (Math.abs(deltaY) > Math.abs(deltaX) && Math.abs(deltaY) > 20) {
                this.isScrolling = true;
                return;
            }
            
            // Only handle horizontal swipes
            if (Math.abs(deltaX) > 20 && !this.isScrolling) {
                isDragging = true;
                e.preventDefault();
                
                // Progressive visual feedback
                this.updateSwipeProgress(deltaX, chatPanel, mainContent);
            }
        };
        
        const handleTouchEnd = (e) => {
            if (!isDragging || this.isScrolling) {
                this.resetSwipeProgress(chatPanel, mainContent);
                return;
            }
            
            const deltaX = currentX - startX;
            const deltaTime = Date.now() - startTime;
            const velocity = Math.abs(deltaX) / deltaTime;
            
            // Determine if swipe should trigger action
            const shouldTrigger = Math.abs(deltaX) > this.swipeThreshold || velocity > 0.5;
            
            if (shouldTrigger) {
                if (deltaX > 0 && !chatPanel.classList.contains('open')) {
                    // Swipe right to open
                    this.handleSwipeRight();
                } else if (deltaX < 0 && chatPanel.classList.contains('open')) {
                    // Swipe left to close
                    this.handleSwipeLeft();
                }
            }
            
            // Reset state
            this.resetSwipeProgress(chatPanel, mainContent);
            isDragging = false;
            
            // Clear scroll detection after a delay
            this.scrollTimeout = setTimeout(() => {
                this.isScrolling = false;
            }, 100);
        };
        
        mainContent.addEventListener('touchstart', handleTouchStart, { passive: true });
        mainContent.addEventListener('touchmove', handleTouchMove, { passive: false });
        mainContent.addEventListener('touchend', handleTouchEnd, { passive: true });
        
        // Also listen on chat panel for closing gestures
        chatPanel.addEventListener('touchstart', handleTouchStart, { passive: true });
        chatPanel.addEventListener('touchmove', handleTouchMove, { passive: false });
        chatPanel.addEventListener('touchend', handleTouchEnd, { passive: true });
    }
    
    /**
     * Update visual feedback during swipe
     */
    updateSwipeProgress(deltaX, chatPanel, mainContent) {
        const maxDistance = 100;
        const progress = Math.min(Math.abs(deltaX) / maxDistance, 1);
        
        if (deltaX > 0 && !chatPanel.classList.contains('open')) {
            // Opening gesture
            chatPanel.classList.add('swipe-active');
            mainContent.classList.add('swipe-preview');
            
            // Progressive transformation
            const translateX = Math.min(deltaX * 0.3, 20);
            mainContent.style.transform = `translateX(-${translateX}px)`;
            chatPanel.style.transform = `translateX(${100 - progress * 20}%)`;
            
        } else if (deltaX < 0 && chatPanel.classList.contains('open')) {
            // Closing gesture
            const translateX = Math.max(deltaX * 0.8, -100);
            chatPanel.style.transform = `translateX(${Math.abs(translateX)}%)`;
        }
    }
    
    /**
     * Reset swipe progress
     */
    resetSwipeProgress(chatPanel, mainContent) {
        chatPanel.classList.remove('swipe-active');
        mainContent.classList.remove('swipe-preview');
        
        // Reset transforms
        chatPanel.style.transform = '';
        mainContent.style.transform = '';
    }
    
    /**
     * Setup project tab swipe navigation
     */
    setupTabSwipeNavigation(tabList) {
        let startX = 0;
        let scrollLeft = 0;
        let isDown = false;
        
        tabList.addEventListener('touchstart', (e) => {
            isDown = true;
            startX = e.touches[0].pageX - tabList.offsetLeft;
            scrollLeft = tabList.scrollLeft;
        }, { passive: true });
        
        tabList.addEventListener('touchmove', (e) => {
            if (!isDown) return;
            e.preventDefault();
            const x = e.touches[0].pageX - tabList.offsetLeft;
            const walk = (x - startX) * 2;
            tabList.scrollLeft = scrollLeft - walk;
        });
        
        tabList.addEventListener('touchend', () => {
            isDown = false;
        }, { passive: true });
    }
    
    /**
     * Setup viewport handling for mobile keyboards
     */
    setupViewportHandling() {
        // Store initial viewport height
        this.viewportHeight = window.visualViewport ? 
                             window.visualViewport.height : 
                             window.innerHeight;
        
        // Listen for viewport changes (keyboard open/close)
        if (window.visualViewport) {
            window.visualViewport.addEventListener('resize', this.handleViewportResize.bind(this));
        } else {
            window.addEventListener('resize', this.handleViewportResize.bind(this));
        }
        
        // Set CSS custom property for viewport height
        this.updateViewportHeight();
    }
    
    /**
     * Handle viewport resize (keyboard detection)
     */
    handleViewportResize() {
        const currentHeight = window.visualViewport ? 
                             window.visualViewport.height : 
                             window.innerHeight;
        
        const heightDifference = this.viewportHeight - currentHeight;
        const wasKeyboardOpen = this.keyboardOpen;
        
        // Detect keyboard open/close (threshold of 150px)
        this.keyboardOpen = heightDifference > 150;
        
        if (this.keyboardOpen !== wasKeyboardOpen) {
            this.handleKeyboardToggle(this.keyboardOpen);
        }
        
        this.updateViewportHeight();
    }
    
    /**
     * Update CSS viewport height variable
     */
    updateViewportHeight() {
        const vh = (window.visualViewport?.height || window.innerHeight) * 0.01;
        document.documentElement.style.setProperty('--vh', `${vh}px`);
    }
    
    /**
     * Handle keyboard open/close
     */
    handleKeyboardToggle(isOpen) {
        document.body.classList.toggle('keyboard-open', isOpen);
        
        if (isOpen) {
            // Keyboard opened - adjust chat input
            const chatInput = document.querySelector('.chat-input');
            if (chatInput) {
                chatInput.classList.add('keyboard-visible');
            }
            
            // Scroll active input into view
            const activeInput = document.activeElement;
            if (activeInput && (activeInput.tagName === 'INPUT' || activeInput.tagName === 'TEXTAREA')) {
                setTimeout(() => {
                    activeInput.scrollIntoView({ behavior: 'smooth', block: 'center' });
                }, 300);
            }
        } else {
            // Keyboard closed - reset adjustments
            const chatInput = document.querySelector('.chat-input');
            if (chatInput) {
                chatInput.classList.remove('keyboard-visible');
            }
        }
        
        console.log(`📱 Mobile keyboard ${isOpen ? 'opened' : 'closed'}`);
    }
    
    /**
     * Setup touch-specific optimizations
     */
    setupTouchOptimizations() {
        // Add touch-friendly hover states
        document.addEventListener('touchstart', this.addTouchHover.bind(this), { passive: true });
        document.addEventListener('touchend', this.removeTouchHover.bind(this), { passive: true });
        
        // Improve scrolling performance
        this.optimizeScrolling();
        
        // Add pull-to-refresh for activity log
        this.setupPullToRefresh();
        
        // Optimize long press actions
        this.setupLongPressActions();
    }
    
    /**
     * Add touch hover effect
     */
    addTouchHover(e) {
        const target = e.target.closest('button, .project-tab, .message-reaction, .autocomplete-item');
        if (target) {
            target.classList.add('touch-hover');
        }
    }
    
    /**
     * Remove touch hover effect
     */
    removeTouchHover(e) {
        const target = e.target.closest('button, .project-tab, .message-reaction, .autocomplete-item');
        if (target) {
            setTimeout(() => {
                target.classList.remove('touch-hover');
            }, 150);
        }
    }
    
    /**
     * Optimize scrolling performance
     */
    optimizeScrolling() {
        const scrollableElements = document.querySelectorAll(
            '.chat-messages, .activity-log, .project-tab-list, .cycles-container'
        );
        
        scrollableElements.forEach(element => {
            element.style.webkitOverflowScrolling = 'touch';
            element.style.overflowBehavior = 'contain';
        });
    }
    
    /**
     * Setup pull-to-refresh for activity log
     */
    setupPullToRefresh() {
        const activityLog = document.getElementById('activity-log');
        if (!activityLog) return;
        
        let startY = 0;
        let isPulling = false;
        let pullDistance = 0;
        const maxPullDistance = 80;
        
        activityLog.addEventListener('touchstart', (e) => {
            if (activityLog.scrollTop === 0) {
                startY = e.touches[0].clientY;
                isPulling = true;
            }
        }, { passive: true });
        
        activityLog.addEventListener('touchmove', (e) => {
            if (!isPulling) return;
            
            const currentY = e.touches[0].clientY;
            pullDistance = Math.min(currentY - startY, maxPullDistance);
            
            if (pullDistance > 0) {
                e.preventDefault();
                const opacity = Math.min(pullDistance / maxPullDistance, 1);
                activityLog.style.transform = `translateY(${pullDistance}px)`;
                activityLog.style.opacity = 1 - opacity * 0.3;
                
                // Show refresh indicator
                if (pullDistance > maxPullDistance * 0.7) {
                    this.showPullToRefreshIndicator(true);
                } else {
                    this.showPullToRefreshIndicator(false);
                }
            }
        });
        
        activityLog.addEventListener('touchend', () => {
            if (isPulling && pullDistance > maxPullDistance * 0.7) {
                this.triggerActivityRefresh();
            }
            
            // Reset
            isPulling = false;
            pullDistance = 0;
            activityLog.style.transform = '';
            activityLog.style.opacity = '';
            this.showPullToRefreshIndicator(false);
        }, { passive: true });
    }
    
    /**
     * Show/hide pull-to-refresh indicator
     */
    showPullToRefreshIndicator(show) {
        let indicator = document.getElementById('pull-refresh-indicator');
        
        if (show && !indicator) {
            indicator = document.createElement('div');
            indicator.id = 'pull-refresh-indicator';
            indicator.innerHTML = '🔄 Release to refresh';
            indicator.style.cssText = `
                position: absolute;
                top: -40px;
                left: 50%;
                transform: translateX(-50%);
                background: var(--chat-accent);
                color: white;
                padding: 8px 12px;
                border-radius: 20px;
                font-size: 14px;
                z-index: 1000;
                transition: opacity 0.2s;
            `;
            document.getElementById('activity-log').appendChild(indicator);
        } else if (!show && indicator) {
            indicator.remove();
        }
    }
    
    /**
     * Trigger activity log refresh
     */
    triggerActivityRefresh() {
        console.log('🔄 Pull-to-refresh triggered');
        
        if (window.visualizer && typeof window.visualizer.refreshActivityLog === 'function') {
            window.visualizer.refreshActivityLog();
        }
        
        // Show success feedback
        if (window.UI) {
            window.UI.showToast('Activity Log', 'Refreshed', 'success', 2000);
        }
    }
    
    /**
     * Setup long press actions
     */
    setupLongPressActions() {
        let longPressTimer;
        let longPressTarget;
        
        document.addEventListener('touchstart', (e) => {
            longPressTarget = e.target.closest('.project-tab, .chat-message');
            if (longPressTarget) {
                longPressTimer = setTimeout(() => {
                    this.handleLongPress(longPressTarget, e.touches[0]);
                }, 600);
            }
        }, { passive: true });
        
        document.addEventListener('touchmove', () => {
            if (longPressTimer) {
                clearTimeout(longPressTimer);
                longPressTimer = null;
            }
        }, { passive: true });
        
        document.addEventListener('touchend', () => {
            if (longPressTimer) {
                clearTimeout(longPressTimer);
                longPressTimer = null;
            }
        }, { passive: true });
    }
    
    /**
     * Handle long press actions
     */
    handleLongPress(target, touch) {
        console.log('👆 Long press detected:', target);
        
        // Add haptic feedback if available
        if (navigator.vibrate) {
            navigator.vibrate(50);
        }
        
        if (target.classList.contains('project-tab')) {
            // Show project context menu
            const projectId = target.getAttribute('data-project');
            if (window.projectManager) {
                window.projectManager.showContextMenu(touch.clientX, touch.clientY, projectId);
            }
        } else if (target.classList.contains('chat-message')) {
            // Show message actions
            this.showMessageActions(target, touch.clientX, touch.clientY);
        }
    }
    
    /**
     * Show message actions menu
     */
    showMessageActions(messageElement, x, y) {
        // Create context menu for message actions
        const menu = document.createElement('div');
        menu.className = 'message-context-menu';
        menu.style.cssText = `
            position: fixed;
            left: ${x}px;
            top: ${y}px;
            background: var(--chat-bg);
            border: 1px solid var(--chat-border);
            border-radius: var(--chat-border-radius);
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
            padding: 4px 0;
            min-width: 140px;
            z-index: 1000;
            font-size: 14px;
        `;
        
        menu.innerHTML = `
            <div class="context-menu-item" data-action="copy">
                <span>📋</span>
                <span>Copy Message</span>
            </div>
            <div class="context-menu-item" data-action="react">
                <span>👍</span>
                <span>Add Reaction</span>
            </div>
            <div class="context-menu-item" data-action="reply">
                <span>↩️</span>
                <span>Reply</span>
            </div>
        `;
        
        // Handle menu actions
        menu.addEventListener('click', (e) => {
            const item = e.target.closest('.context-menu-item');
            if (item) {
                const action = item.getAttribute('data-action');
                this.handleMessageAction(action, messageElement);
                menu.remove();
            }
        });
        
        // Remove menu on outside click
        setTimeout(() => {
            document.addEventListener('click', () => menu.remove(), { once: true });
        }, 100);
        
        document.body.appendChild(menu);
        
        // Position menu within viewport
        const menuRect = menu.getBoundingClientRect();
        if (menuRect.right > window.innerWidth) {
            menu.style.left = `${x - menuRect.width}px`;
        }
        if (menuRect.bottom > window.innerHeight) {
            menu.style.top = `${y - menuRect.height}px`;
        }
    }
    
    /**
     * Handle message context actions
     */
    handleMessageAction(action, messageElement) {
        const messageContent = messageElement.querySelector('.message-content');
        const messageText = messageContent ? messageContent.textContent : '';
        
        switch (action) {
            case 'copy':
                if (navigator.clipboard) {
                    navigator.clipboard.writeText(messageText).then(() => {
                        if (window.UI) {
                            window.UI.showToast('Message', 'Copied to clipboard', 'success', 2000);
                        }
                    });
                }
                break;
                
            case 'react':
                // Add reaction (simplified - would integrate with discord system)
                if (window.UI) {
                    window.UI.showToast('Reaction', 'Feature coming soon!', 'info', 2000);
                }
                break;
                
            case 'reply':
                // Set reply context in chat input
                const chatInput = document.querySelector('.chat-input-field');
                if (chatInput) {
                    chatInput.focus();
                    const preview = messageText.substring(0, 50) + (messageText.length > 50 ? '...' : '');
                    chatInput.placeholder = `Replying to: ${preview}`;
                }
                break;
        }
    }
    
    /**
     * Setup orientation change handling
     */
    setupOrientationHandling() {
        window.addEventListener('orientationchange', () => {
            setTimeout(() => {
                this.handleOrientationChange();
                this.updateViewportHeight();
            }, 100);
        });
        
        // Also listen for resize events
        window.addEventListener('resize', () => {
            clearTimeout(this.resizeTimer);
            this.resizeTimer = setTimeout(() => {
                this.handleOrientationChange();
            }, 250);
        });
    }
    
    /**
     * Handle orientation changes
     */
    handleOrientationChange() {
        const isPortrait = window.innerHeight > window.innerWidth;
        const wasPortrait = document.body.classList.contains('portrait');
        
        document.body.classList.toggle('portrait', isPortrait);
        document.body.classList.toggle('landscape', !isPortrait);
        
        if (isPortrait !== wasPortrait) {
            console.log(`📱 Orientation changed to ${isPortrait ? 'portrait' : 'landscape'}`);
            
            // Adjust layout for orientation
            this.adjustLayoutForOrientation(isPortrait);
            
            // Update scroll indicators
            if (window.projectManager) {
                setTimeout(() => {
                    window.projectManager.updateScrollIndicators();
                }, 100);
            }
        }
    }
    
    /**
     * Adjust layout for orientation
     */
    adjustLayoutForOrientation(isPortrait) {
        const chatPanel = document.querySelector('.chat-panel');
        const mainContent = document.getElementById('main-content');
        
        if (this.isMobile && chatPanel && mainContent) {
            if (isPortrait) {
                // Portrait: chat panel takes full width
                chatPanel.style.width = '100vw';
            } else {
                // Landscape: chat panel takes 60% width
                chatPanel.style.width = '60vw';
            }
        }
    }
    
    /**
     * Setup keyboard input handling
     */
    setupKeyboardHandling() {
        // Prevent zoom on input focus
        const inputs = document.querySelectorAll('input, textarea, select');
        inputs.forEach(input => {
            input.addEventListener('focus', this.preventZoomOnFocus.bind(this));
            input.addEventListener('blur', this.restoreZoomOnBlur.bind(this));
        });
        
        // Handle Enter key in chat input
        const chatInput = document.querySelector('.chat-input-field');
        if (chatInput) {
            chatInput.addEventListener('keydown', (e) => {
                if (e.key === 'Enter' && !e.shiftKey) {
                    e.preventDefault();
                    const event = new Event('submit');
                    chatInput.closest('form')?.dispatchEvent(event);
                }
            });
        }
    }
    
    /**
     * Prevent zoom on input focus (iOS Safari)
     */
    preventZoomOnFocus(e) {
        if (this.isMobile) {
            const viewport = document.querySelector('meta[name="viewport"]');
            if (viewport) {
                viewport.setAttribute('content', 
                    'width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no'
                );
            }
        }
    }
    
    /**
     * Restore zoom capability on input blur
     */
    restoreZoomOnBlur(e) {
        if (this.isMobile) {
            setTimeout(() => {
                const viewport = document.querySelector('meta[name="viewport"]');
                if (viewport) {
                    viewport.setAttribute('content', 
                        'width=device-width, initial-scale=1.0, user-scalable=yes'
                    );
                }
            }, 100);
        }
    }
    
    /**
     * Touch event handlers
     */
    handleTouchStart(e) {
        if (e.touches.length === 1) {
            this.touchStartX = e.touches[0].clientX;
            this.touchStartY = e.touches[0].clientY;
        } else if (e.touches.length === 2) {
            // Pinch gesture
            const touch1 = e.touches[0];
            const touch2 = e.touches[1];
            this.gestureState.initialDistance = this.getDistance(touch1, touch2);
            this.gestureState.isPinching = true;
        }
    }
    
    handleTouchMove(e) {
        if (this.gestureState.isPinching && e.touches.length === 2) {
            e.preventDefault();
            const touch1 = e.touches[0];
            const touch2 = e.touches[1];
            const currentDistance = this.getDistance(touch1, touch2);
            const scale = currentDistance / this.gestureState.initialDistance;
            
            // Apply zoom to diagram containers
            const diagrams = document.querySelectorAll('.diagram-wrapper');
            diagrams.forEach(diagram => {
                diagram.style.transform = `scale(${Math.min(Math.max(scale, 0.5), 3)})`;
            });
        }
    }
    
    handleTouchEnd(e) {
        if (e.changedTouches.length === 1) {
            this.touchEndX = e.changedTouches[0].clientX;
            this.touchEndY = e.changedTouches[0].clientY;
        }
        
        // Reset pinch state
        if (e.touches.length < 2) {
            this.gestureState.isPinching = false;
        }
        
        this.handleDoubleTap(e);
    }
    
    /**
     * Handle swipe gestures
     */
    handleSwipeGesture() {
        const xDiff = this.touchEndX - this.touchStartX;
        const yDiff = this.touchEndY - this.touchStartY;
        
        // Check if swipe distance meets threshold
        if (Math.abs(xDiff) < this.swipeThreshold && Math.abs(yDiff) < this.swipeThreshold) {
            return;
        }
        
        // Determine swipe direction
        if (Math.abs(xDiff) > Math.abs(yDiff)) {
            // Horizontal swipe
            if (xDiff > 0) {
                this.handleSwipeRight();
            } else {
                this.handleSwipeLeft();
            }
        } else {
            // Vertical swipe
            if (yDiff > 0) {
                this.handleSwipeDown();
            } else {
                this.handleSwipeUp();
            }
        }
    }
    
    /**
     * Handle swipe right (open chat)
     */
    handleSwipeRight() {
        if (this.isMobile) {
            const chatPanel = document.querySelector('.chat-panel');
            if (chatPanel && !chatPanel.classList.contains('open')) {
                if (window.discordChat) {
                    window.discordChat.togglePanel();
                }
                console.log('📱 Swipe right: opened chat');
            }
        }
    }
    
    /**
     * Handle swipe left (close chat)
     */
    handleSwipeLeft() {
        if (this.isMobile) {
            const chatPanel = document.querySelector('.chat-panel');
            if (chatPanel && chatPanel.classList.contains('open')) {
                if (window.discordChat) {
                    window.discordChat.togglePanel();
                }
                console.log('📱 Swipe left: closed chat');
            }
        }
    }
    
    /**
     * Handle swipe up/down (could be used for other features)
     */
    handleSwipeUp() {
        // Could be used for showing/hiding panels
        console.log('📱 Swipe up detected');
    }
    
    handleSwipeDown() {
        // Could be used for pull-to-refresh
        console.log('📱 Swipe down detected');
    }
    
    /**
     * Handle double tap events
     */
    handleDoubleTap(e) {
        const currentTime = new Date().getTime();
        const tapLength = currentTime - this.lastTap;
        
        if (tapLength < 500 && tapLength > 0) {
            // Double tap detected
            const target = e.target.closest('.diagram-wrapper');
            if (target) {
                this.handleDiagramDoubleTap(target);
            }
        }
        
        this.lastTap = currentTime;
    }
    
    /**
     * Handle double tap on diagrams (zoom reset)
     */
    handleDiagramDoubleTap(diagram) {
        diagram.style.transform = '';
        console.log('📱 Double tap: reset diagram zoom');
        
        if (window.UI) {
            window.UI.showToast('Diagram', 'Zoom reset', 'info', 1500);
        }
    }
    
    /**
     * Prevent double-tap zoom
     */
    preventDoubleTabZoom(e) {
        const currentTime = new Date().getTime();
        const tapLength = currentTime - this.lastTap;
        
        if (tapLength < 500 && tapLength > 0) {
            e.preventDefault();
        }
        
        this.lastTap = currentTime;
    }
    
    /**
     * Gesture handlers for pinch-to-zoom
     */
    handleGestureStart(e) {
        e.preventDefault();
        this.gestureState.currentScale = 1;
    }
    
    handleGestureChange(e) {
        e.preventDefault();
        const target = e.target.closest('.diagram-wrapper');
        if (target) {
            const scale = Math.min(Math.max(e.scale, 0.5), 3);
            target.style.transform = `scale(${scale})`;
            this.gestureState.currentScale = scale;
        }
    }
    
    handleGestureEnd(e) {
        e.preventDefault();
        console.log(`📱 Pinch gesture ended, final scale: ${this.gestureState.currentScale}`);
    }
    
    /**
     * Get distance between two touch points
     */
    getDistance(touch1, touch2) {
        const dx = touch1.clientX - touch2.clientX;
        const dy = touch1.clientY - touch2.clientY;
        return Math.sqrt(dx * dx + dy * dy);
    }
    
    /**
     * Optimize interface for mobile
     */
    optimizeForMobile() {
        document.body.classList.add('mobile-optimized');
        
        // Add mobile-specific classes
        if (this.isMobile) {
            document.body.classList.add('mobile-device');
        }
        if (this.isTablet) {
            document.body.classList.add('tablet-device');
        }
        
        // Optimize touch targets
        this.optimizeTouchTargets();
        
        // Improve accessibility
        this.improveAccessibility();
    }
    
    /**
     * Optimize touch targets for mobile
     */
    optimizeTouchTargets() {
        const touchTargets = document.querySelectorAll(
            'button, .project-tab, .tab-control-btn, .mobile-control-btn, .autocomplete-item'
        );
        
        touchTargets.forEach(target => {
            const computedStyle = window.getComputedStyle(target);
            const height = parseInt(computedStyle.height);
            const width = parseInt(computedStyle.width);
            
            // Ensure minimum touch target size (44px)
            if (height < 44) {
                target.style.minHeight = '44px';
                target.style.display = 'flex';
                target.style.alignItems = 'center';
                target.style.justifyContent = 'center';
            }
            
            if (width < 44) {
                target.style.minWidth = '44px';
            }
        });
    }
    
    /**
     * Improve accessibility for mobile
     */
    improveAccessibility() {
        // Add aria labels for mobile-specific actions
        const chatToggle = document.querySelector('.chat-toggle-btn');
        if (chatToggle) {
            chatToggle.setAttribute('aria-label', 'Toggle chat panel (swipe right/left)');
        }
        
        // Add touch hints
        const projectTabs = document.querySelectorAll('.project-tab');
        projectTabs.forEach(tab => {
            const currentLabel = tab.getAttribute('aria-label') || tab.title;
            tab.setAttribute('aria-label', `${currentLabel} (long press for options)`);
        });
        
        // Add swipe hints for first-time users
        if (!localStorage.getItem('mobile-hints-shown')) {
            this.showMobileHints();
            localStorage.setItem('mobile-hints-shown', 'true');
        }
    }
    
    /**
     * Show mobile usage hints
     */
    showMobileHints() {
        if (!window.UI) return;
        
        const hints = [
            'Swipe right to open chat panel',
            'Swipe left to close chat panel',
            'Long press project tabs for options',
            'Double tap diagrams to reset zoom',
            'Pull down activity log to refresh'
        ];
        
        hints.forEach((hint, index) => {
            setTimeout(() => {
                window.UI.showToast('Mobile Tip', hint, 'info', 3000);
            }, (index + 1) * 1000);
        });
    }
    
    /**
     * Add mobile-specific CSS
     */
    addMobileCSS() {
        const style = document.createElement('style');
        style.textContent = `
            /* Mobile touch optimizations */
            .mobile-optimized {
                -webkit-touch-callout: none;
                -webkit-user-select: none;
                -khtml-user-select: none;
                -moz-user-select: none;
                -ms-user-select: none;
                user-select: none;
                -webkit-tap-highlight-color: transparent;
            }
            
            /* Allow text selection in content areas */
            .mobile-optimized .message-content,
            .mobile-optimized .activity-log,
            .mobile-optimized input,
            .mobile-optimized textarea {
                -webkit-user-select: text;
                -moz-user-select: text;
                -ms-user-select: text;
                user-select: text;
            }
            
            /* Touch hover states */
            .touch-hover {
                transform: scale(1.05);
                opacity: 0.8;
                transition: all 0.1s ease;
            }
            
            button.touch-hover,
            .project-tab.touch-hover {
                background-color: var(--chat-accent);
                color: white;
            }
            
            /* Keyboard open adjustments */
            .keyboard-open .chat-input.keyboard-visible {
                position: fixed;
                bottom: 0;
                left: 0;
                right: 0;
                z-index: 1001;
                background: var(--chat-bg);
                border-top: 2px solid var(--chat-accent);
                box-shadow: 0 -4px 12px rgba(0, 0, 0, 0.15);
            }
            
            /* Viewport height using CSS custom property */
            .mobile-device .app-layout {
                height: calc(var(--vh, 1vh) * 100);
            }
            
            /* Portrait/Landscape specific styles */
            .portrait .status-bar {
                flex-wrap: wrap;
                gap: 8px;
            }
            
            .landscape .project-tab-bar {
                padding: 4px 8px;
            }
            
            .landscape .project-tab {
                min-width: 100px;
                max-width: 150px;
            }
            
            /* Touch target improvements */
            .mobile-device button,
            .mobile-device .project-tab,
            .mobile-device .autocomplete-item {
                min-height: 44px;
                min-width: 44px;
            }
            
            /* Diagram zoom optimizations */
            .mobile-device .diagram-wrapper {
                transform-origin: center center;
                transition: transform 0.3s ease;
                overflow: hidden;
            }
            
            /* Pull-to-refresh indicator */
            .mobile-device .activity-log {
                position: relative;
                transition: transform 0.2s ease, opacity 0.2s ease;
            }
            
            /* Message context menu */
            .message-context-menu .context-menu-item {
                display: flex;
                align-items: center;
                gap: 8px;
                padding: 12px 16px;
                cursor: pointer;
                transition: background-color 0.2s ease;
                color: var(--chat-text);
                min-height: 44px;
            }
            
            .message-context-menu .context-menu-item:hover,
            .message-context-menu .context-menu-item.touch-hover {
                background: var(--chat-message-bg);
            }
            
            /* Improved scrollbar for mobile */
            .mobile-device ::-webkit-scrollbar {
                width: 8px;
                height: 8px;
            }
            
            .mobile-device ::-webkit-scrollbar-thumb {
                background: rgba(0, 0, 0, 0.3);
                border-radius: 4px;
            }
            
            .mobile-device ::-webkit-scrollbar-track {
                background: transparent;
            }
            
            /* Accessibility improvements */
            @media (prefers-reduced-motion: reduce) {
                .mobile-device * {
                    transition-duration: 0.01ms !important;
                    animation-duration: 0.01ms !important;
                }
            }
            
            /* High contrast support */
            @media (prefers-contrast: high) {
                .mobile-device .touch-hover {
                    border: 2px solid currentColor;
                }
            }
        `;
        
        document.head.appendChild(style);
    }
    
    /**
     * Get device info
     */
    getDeviceInfo() {
        return {
            isMobile: this.isMobile,
            isTablet: this.isTablet,
            userAgent: navigator.userAgent,
            touchSupport: 'ontouchstart' in window,
            screenSize: {
                width: window.innerWidth,
                height: window.innerHeight
            },
            orientation: window.innerHeight > window.innerWidth ? 'portrait' : 'landscape',
            pixelRatio: window.devicePixelRatio || 1
        };
    }
    
    /**
     * Setup basic touch support for desktop touch devices
     */
    setupBasicTouchSupport() {
        // Add touch hover effects for touch-enabled desktops
        document.addEventListener('touchstart', this.addTouchHover.bind(this), { passive: true });
        document.addEventListener('touchend', this.removeTouchHover.bind(this), { passive: true });
        
        // Improve scrolling on touch devices
        this.optimizeScrolling();
        
        console.log('🖱️ Basic touch support enabled for desktop');
    }
    
    /**
     * Setup enhanced accessibility features
     */
    setupAccessibilityEnhancements() {
        // Add ARIA labels for mobile-specific interactions
        this.enhanceAriaLabels();
        
        // Setup focus management for mobile
        this.setupMobileFocusManagement();
        
        // Add voice-over support improvements
        this.improveVoiceOverSupport();
        
        // Setup high contrast mode detection
        this.setupHighContrastMode();
        
        console.log('♿ Accessibility enhancements enabled');
    }
    
    /**
     * Enhance ARIA labels for mobile interactions
     */
    enhanceAriaLabels() {
        // Update chat toggle button
        const chatToggle = document.querySelector('.chat-toggle-btn');
        if (chatToggle) {
            chatToggle.setAttribute('aria-label', 'Toggle chat panel. Swipe right to open, left to close.');
            chatToggle.setAttribute('role', 'button');
        }
        
        // Update project tabs
        const projectTabs = document.querySelectorAll('.project-tab');
        projectTabs.forEach(tab => {
            tab.setAttribute('aria-label', `${tab.textContent}. Long press for options, swipe to navigate.`);
            tab.setAttribute('role', 'tab');
        });
        
        // Update mobile controls
        const mobileControls = document.querySelectorAll('.mobile-control-btn');
        mobileControls.forEach((control, index) => {
            const actions = ['Add project', 'Project settings', 'Global view'];
            if (actions[index]) {
                control.setAttribute('aria-label', actions[index]);
            }
        });
    }
    
    /**
     * Setup mobile-specific focus management
     */
    setupMobileFocusManagement() {
        // Track focus for keyboard users on mobile
        let isUsingKeyboard = false;
        
        document.addEventListener('keydown', () => {
            isUsingKeyboard = true;
            document.body.classList.add('keyboard-navigation');
        });
        
        document.addEventListener('touchstart', () => {
            isUsingKeyboard = false;
            document.body.classList.remove('keyboard-navigation');
        });
        
        // Improve focus visibility on mobile
        const focusableElements = document.querySelectorAll(
            'button, input, select, textarea, [tabindex]:not([tabindex=\"-1\"])'
        );
        
        focusableElements.forEach(element => {
            element.addEventListener('focus', () => {
                if (isUsingKeyboard) {
                    element.classList.add('keyboard-focus');
                }
            });
            
            element.addEventListener('blur', () => {
                element.classList.remove('keyboard-focus');
            });
        });
    }
    
    /**
     * Improve VoiceOver support for iOS
     */
    improveVoiceOverSupport() {
        // Add live regions for dynamic content
        const statusElements = document.querySelectorAll('#workflow-state, #connection-status');
        statusElements.forEach(element => {
            element.setAttribute('aria-live', 'polite');
            element.setAttribute('aria-atomic', 'true');
        });
        
        // Improve chat message announcements
        const chatMessages = document.querySelector('.chat-messages');
        if (chatMessages) {
            chatMessages.setAttribute('aria-live', 'polite');
            chatMessages.setAttribute('aria-label', 'Chat conversation');
        }
        
        // Add skip links for mobile navigation
        this.addSkipLinks();
    }
    
    /**
     * Add skip navigation links
     */
    addSkipLinks() {
        const skipLinks = document.createElement('div');
        skipLinks.className = 'skip-links';
        skipLinks.innerHTML = `
            <a href="#main-content" class="skip-link">Skip to main content</a>
            <a href="#project-tab-bar" class="skip-link">Skip to projects</a>
            <a href="#chat-panel" class="skip-link">Skip to chat</a>
        `;
        
        const style = document.createElement('style');
        style.textContent = `
            .skip-links {
                position: absolute;
                top: -40px;
                left: 6px;
                z-index: 2000;
            }
            
            .skip-link {
                position: absolute;
                top: -40px;
                left: 6px;
                background: var(--chat-accent);
                color: white;
                padding: 8px;
                text-decoration: none;
                border-radius: 4px;
                transition: top 0.3s;
            }
            
            .skip-link:focus {
                top: 6px;
            }
        `;
        
        document.head.appendChild(style);
        document.body.insertBefore(skipLinks, document.body.firstChild);
    }
    
    /**
     * Setup high contrast mode detection
     */
    setupHighContrastMode() {
        const highContrastQuery = window.matchMedia('(prefers-contrast: high)');
        
        const handleHighContrast = (e) => {
            document.body.classList.toggle('high-contrast', e.matches);
            
            if (e.matches) {
                console.log('♿ High contrast mode enabled');
                // Enhance contrast for mobile elements
                this.enhanceContrastForMobile();
            }
        };
        
        highContrastQuery.addListener(handleHighContrast);
        handleHighContrast(highContrastQuery);
    }
    
    /**
     * Enhance contrast for mobile elements
     */
    enhanceContrastForMobile() {
        const style = document.createElement('style');
        style.id = 'mobile-high-contrast';
        style.textContent = `
            .high-contrast .mobile-device button,
            .high-contrast .mobile-device .project-tab,
            .high-contrast .mobile-device .mobile-control-btn {
                border: 2px solid currentColor !important;
                font-weight: bold !important;
            }
            
            .high-contrast .mobile-device .chat-panel {
                border: 3px solid currentColor !important;
            }
            
            .high-contrast .mobile-device .touch-hover {
                outline: 3px solid currentColor !important;
            }
        `;
        
        document.head.appendChild(style);
    }
    
    /**
     * Check if mobile enhancements are active
     */
    isActive() {
        return this.isInitialized && (this.isMobile || this.isTablet);
    }
}

// Initialize mobile enhancements
let mobileEnhancements;

document.addEventListener('DOMContentLoaded', () => {
    console.log('📱 Initializing Mobile Enhancements...');
    mobileEnhancements = new MobileEnhancements();
    
    // Expose to global scope
    window.mobileEnhancements = mobileEnhancements;
    
    // Log device info
    console.log('📱 Device Info:', mobileEnhancements.getDeviceInfo());
});

// Export for module usage
if (typeof module !== 'undefined' && module.exports) {
    module.exports = MobileEnhancements;
}

// Also expose to window for browser usage
if (typeof window !== 'undefined') {
    window.MobileEnhancements = MobileEnhancements;
}