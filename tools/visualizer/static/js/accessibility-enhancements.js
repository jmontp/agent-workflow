/**
 * Accessibility Enhancements for TDD State Visualizer
 * Provides comprehensive keyboard navigation, ARIA support, and WCAG compliance
 */

class AccessibilityManager {
    constructor() {
        this.focusableElements = [];
        this.currentFocusIndex = -1;
        this.announcer = null;
        this.keyboardShortcuts = new Map();
        this.ariaLiveRegion = null;
        this.focusHistory = [];
        this.highContrastMode = false;
        this.reducedMotionMode = false;
        
        this.init();
    }

    init() {
        this.createAriaLiveRegion();
        this.setupKeyboardNavigation();
        this.setupKeyboardShortcuts();
        this.enhanceFormElements();
        this.addAriaLabels();
        this.setupFocusManagement();
        this.detectUserPreferences();
        this.setupScreenReaderSupport();
        this.addSkipLinks();
        this.enhanceErrorHandling();
        
        // Initialize on DOM ready
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', () => this.onDOMReady());
        } else {
            this.onDOMReady();
        }
        
        console.log('♿ Accessibility enhancements initialized');
    }

    onDOMReady() {
        this.updateFocusableElements();
        this.addTabIndex();
        this.setupDynamicContentAnnouncements();
        this.enhanceChatAccessibility();
        this.setupProjectTabAccessibility();
    }

    createAriaLiveRegion() {
        // Create invisible ARIA live region for announcements
        this.ariaLiveRegion = document.createElement('div');
        this.ariaLiveRegion.setAttribute('aria-live', 'polite');
        this.ariaLiveRegion.setAttribute('aria-atomic', 'true');
        this.ariaLiveRegion.className = 'sr-only';
        this.ariaLiveRegion.style.cssText = `
            position: absolute !important;
            width: 1px !important;
            height: 1px !important;
            padding: 0 !important;
            margin: -1px !important;
            overflow: hidden !important;
            clip: rect(0, 0, 0, 0) !important;
            white-space: nowrap !important;
            border: 0 !important;
        `;
        document.body.appendChild(this.ariaLiveRegion);

        // Create urgent announcements region
        this.urgentAnnouncer = document.createElement('div');
        this.urgentAnnouncer.setAttribute('aria-live', 'assertive');
        this.urgentAnnouncer.setAttribute('aria-atomic', 'true');
        this.urgentAnnouncer.className = 'sr-only';
        this.urgentAnnouncer.style.cssText = this.ariaLiveRegion.style.cssText;
        document.body.appendChild(this.urgentAnnouncer);
    }

    announce(message, priority = 'polite') {
        const announcer = priority === 'assertive' ? this.urgentAnnouncer : this.ariaLiveRegion;
        
        // Clear previous announcement
        announcer.textContent = '';
        
        // Use requestAnimationFrame to ensure screen readers pick up the change
        requestAnimationFrame(() => {
            announcer.textContent = message;
        });

        console.log(`♿ Announced (${priority}):`, message);
    }

    setupKeyboardNavigation() {
        document.addEventListener('keydown', (e) => this.handleGlobalKeydown(e));
        
        // Add focus indicators
        const style = document.createElement('style');
        style.textContent = `
            .focus-visible {
                outline: 3px solid #4CAF50 !important;
                outline-offset: 2px !important;
                box-shadow: 0 0 0 1px rgba(76, 175, 80, 0.3) !important;
            }
            
            .keyboard-focused {
                background: rgba(76, 175, 80, 0.1) !important;
                border-color: #4CAF50 !important;
            }
            
            .sr-only {
                position: absolute !important;
                width: 1px !important;
                height: 1px !important;
                padding: 0 !important;
                margin: -1px !important;
                overflow: hidden !important;
                clip: rect(0, 0, 0, 0) !important;
                white-space: nowrap !important;
                border: 0 !important;
            }
            
            .skip-link {
                position: absolute;
                top: -40px;
                left: 6px;
                background: #000;
                color: #fff;
                padding: 8px;
                text-decoration: none;
                z-index: 9999;
                border-radius: 4px;
                transition: top 0.2s ease;
            }
            
            .skip-link:focus {
                top: 6px;
            }
            
            /* High contrast mode styles */
            .high-contrast-mode {
                filter: contrast(150%) !important;
            }
            
            .high-contrast-mode * {
                border-color: #000 !important;
                text-shadow: none !important;
                box-shadow: none !important;
            }
            
            /* Reduced motion styles */
            .reduced-motion-mode * {
                animation-duration: 0.01ms !important;
                animation-iteration-count: 1 !important;
                transition-duration: 0.01ms !important;
                scroll-behavior: auto !important;
            }
        `;
        document.head.appendChild(style);
    }

    setupKeyboardShortcuts() {
        // Global keyboard shortcuts
        this.keyboardShortcuts.set('Alt+K', () => this.focusProjectSearch());
        this.keyboardShortcuts.set('Alt+C', () => this.toggleChatPanel());
        this.keyboardShortcuts.set('Alt+H', () => this.showKeyboardHelp());
        this.keyboardShortcuts.set('Alt+T', () => this.toggleHighContrast());
        this.keyboardShortcuts.set('Alt+M', () => this.toggleReducedMotion());
        this.keyboardShortcuts.set('Alt+S', () => this.focusSearchInput());
        this.keyboardShortcuts.set('Escape', () => this.handleEscape());
        this.keyboardShortcuts.set('F1', () => this.showAccessibilityHelp());
        
        // Navigation shortcuts
        this.keyboardShortcuts.set('Alt+1', () => this.focusMainContent());
        this.keyboardShortcuts.set('Alt+2', () => this.focusChatPanel());
        this.keyboardShortcuts.set('Alt+3', () => this.focusStatusBar());
        
        // TDD workflow shortcuts
        this.keyboardShortcuts.set('Alt+R', () => this.triggerRefresh());
        this.keyboardShortcuts.set('Alt+P', () => this.pauseWorkflow());
    }

    handleGlobalKeydown(e) {
        const shortcut = this.getKeyboardShortcut(e);
        
        if (this.keyboardShortcuts.has(shortcut) && !this.isInputFocused()) {
            e.preventDefault();
            const action = this.keyboardShortcuts.get(shortcut);
            action();
            return;
        }

        // Handle tab navigation
        if (e.key === 'Tab') {
            this.handleTabNavigation(e);
        }
        
        // Handle arrow key navigation in grids/lists
        if (['ArrowUp', 'ArrowDown', 'ArrowLeft', 'ArrowRight'].includes(e.key)) {
            this.handleArrowNavigation(e);
        }
        
        // Handle Enter/Space activation
        if (e.key === 'Enter' || e.key === ' ') {
            this.handleActivation(e);
        }
    }

    getKeyboardShortcut(e) {
        const modifiers = [];
        if (e.ctrlKey) modifiers.push('Ctrl');
        if (e.altKey) modifiers.push('Alt');
        if (e.shiftKey) modifiers.push('Shift');
        if (e.metaKey) modifiers.push('Meta');
        
        if (modifiers.length > 0) {
            return `${modifiers.join('+')}+${e.key}`;
        }
        return e.key;
    }

    isInputFocused() {
        const activeElement = document.activeElement;
        return activeElement && (
            activeElement.tagName === 'INPUT' ||
            activeElement.tagName === 'TEXTAREA' ||
            activeElement.tagName === 'SELECT' ||
            activeElement.contentEditable === 'true'
        );
    }

    updateFocusableElements() {
        const focusableSelectors = [
            'button:not([disabled])',
            'input:not([disabled])',
            'textarea:not([disabled])',
            'select:not([disabled])',
            'a[href]',
            '[tabindex]:not([tabindex="-1"])',
            '[contenteditable="true"]',
            '.project-tab',
            '.chat-message',
            '.message-reaction',
            '.autocomplete-item'
        ];
        
        this.focusableElements = Array.from(
            document.querySelectorAll(focusableSelectors.join(', '))
        ).filter(el => this.isVisible(el));
    }

    isVisible(element) {
        if (!element) return false;
        const style = window.getComputedStyle(element);
        return style.display !== 'none' && 
               style.visibility !== 'hidden' && 
               style.opacity !== '0' &&
               element.offsetWidth > 0 && 
               element.offsetHeight > 0;
    }

    addTabIndex() {
        // Add tabindex to interactive elements that don't have it
        const elements = document.querySelectorAll('.project-tab, .chat-message, .diagram-container');
        elements.forEach((el, index) => {
            if (!el.hasAttribute('tabindex')) {
                el.setAttribute('tabindex', '0');
            }
        });
    }

    addAriaLabels() {
        // Add ARIA labels to all interactive elements
        this.addProjectTabAriaLabels();
        this.addChatAriaLabels();
        this.addDiagramAriaLabels();
        this.addStatusBarAriaLabels();
        this.addButtonAriaLabels();
    }

    addProjectTabAriaLabels() {
        const projectTabs = document.querySelectorAll('.project-tab');
        projectTabs.forEach(tab => {
            const projectName = tab.querySelector('.project-name')?.textContent || 'Unknown Project';
            const statusDot = tab.querySelector('.project-status-dot');
            const status = statusDot?.getAttribute('data-status') || 'unknown';
            
            tab.setAttribute('role', 'tab');
            tab.setAttribute('aria-label', `${projectName} project, status: ${status}`);
            tab.setAttribute('aria-selected', tab.classList.contains('active').toString());
            
            // Add keyboard event handlers
            tab.addEventListener('keydown', (e) => {
                if (e.key === 'Enter' || e.key === ' ') {
                    e.preventDefault();
                    tab.click();
                    this.announce(`Switched to ${projectName} project`);
                }
            });
        });

        // Add tab list role
        const tabList = document.querySelector('.tab-list');
        if (tabList) {
            tabList.setAttribute('role', 'tablist');
            tabList.setAttribute('aria-label', 'Project tabs');
        }
    }

    addChatAriaLabels() {
        const chatPanel = document.querySelector('.chat-panel');
        if (chatPanel) {
            chatPanel.setAttribute('role', 'complementary');
            chatPanel.setAttribute('aria-label', 'Chat interface');
        }

        const chatMessages = document.querySelector('.chat-messages');
        if (chatMessages) {
            chatMessages.setAttribute('role', 'log');
            chatMessages.setAttribute('aria-label', 'Chat messages');
            chatMessages.setAttribute('aria-live', 'polite');
        }

        const chatInput = document.querySelector('.chat-input-field');
        if (chatInput) {
            chatInput.setAttribute('aria-label', 'Type your message here');
            chatInput.setAttribute('aria-describedby', 'chat-input-help');
            
            // Add help text
            const helpText = document.createElement('div');
            helpText.id = 'chat-input-help';
            helpText.className = 'sr-only';
            helpText.textContent = 'Type your message and press Enter to send, or use Tab to navigate to send button';
            chatInput.parentNode.appendChild(helpText);
        }

        const sendButton = document.querySelector('.chat-send-btn');
        if (sendButton) {
            sendButton.setAttribute('aria-label', 'Send message');
        }
    }

    addDiagramAriaLabels() {
        const diagrams = document.querySelectorAll('.diagram-container');
        diagrams.forEach((container, index) => {
            const title = container.querySelector('h2')?.textContent || `Diagram ${index + 1}`;
            container.setAttribute('role', 'img');
            container.setAttribute('aria-label', `${title} - Interactive state diagram`);
            container.setAttribute('tabindex', '0');
            
            // Add description
            const description = document.createElement('div');
            description.className = 'sr-only';
            description.textContent = `Navigate through ${title} using arrow keys. Press Enter for more details.`;
            container.appendChild(description);
        });
    }

    addStatusBarAriaLabels() {
        const statusBar = document.querySelector('.status-bar');
        if (statusBar) {
            statusBar.setAttribute('role', 'status');
            statusBar.setAttribute('aria-label', 'System status information');
        }

        const statusItems = document.querySelectorAll('.status-item');
        statusItems.forEach(item => {
            const label = item.querySelector('.label')?.textContent || '';
            const value = item.querySelector('.status, .interface, .state, .count, .timestamp')?.textContent || '';
            item.setAttribute('aria-label', `${label} ${value}`);
        });
    }

    addButtonAriaLabels() {
        const buttons = document.querySelectorAll('button:not([aria-label]):not([aria-labelledby])');
        buttons.forEach(button => {
            const text = button.textContent.trim() || button.title || button.getAttribute('data-tooltip');
            if (text) {
                button.setAttribute('aria-label', text);
            }
        });
    }

    setupFocusManagement() {
        // Track focus changes
        document.addEventListener('focusin', (e) => {
            this.focusHistory.push(e.target);
            if (this.focusHistory.length > 10) {
                this.focusHistory.shift();
            }
            
            // Add visual focus indicator
            e.target.classList.add('keyboard-focused');
        });

        document.addEventListener('focusout', (e) => {
            e.target.classList.remove('keyboard-focused');
        });

        // Handle focus trapping in modals
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Tab') {
                const modal = document.querySelector('.modal:not(.hidden)');
                if (modal) {
                    this.trapFocus(e, modal);
                }
            }
        });
    }

    trapFocus(e, container) {
        const focusableElements = container.querySelectorAll(
            'button:not([disabled]), input:not([disabled]), textarea:not([disabled]), select:not([disabled]), a[href], [tabindex]:not([tabindex="-1"])'
        );
        
        const firstElement = focusableElements[0];
        const lastElement = focusableElements[focusableElements.length - 1];

        if (e.shiftKey) {
            if (document.activeElement === firstElement) {
                e.preventDefault();
                lastElement.focus();
            }
        } else {
            if (document.activeElement === lastElement) {
                e.preventDefault();
                firstElement.focus();
            }
        }
    }

    detectUserPreferences() {
        // Detect user preferences from system
        this.reducedMotionMode = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
        this.highContrastMode = window.matchMedia('(prefers-contrast: high)').matches;

        // Apply preferences
        if (this.reducedMotionMode) {
            document.body.classList.add('reduced-motion-mode');
        }

        if (this.highContrastMode) {
            document.body.classList.add('high-contrast-mode');
        }

        // Listen for changes
        window.matchMedia('(prefers-reduced-motion: reduce)').addEventListener('change', (e) => {
            this.reducedMotionMode = e.matches;
            document.body.classList.toggle('reduced-motion-mode', e.matches);
            this.announce(e.matches ? 'Reduced motion enabled' : 'Reduced motion disabled');
        });

        window.matchMedia('(prefers-contrast: high)').addEventListener('change', (e) => {
            this.highContrastMode = e.matches;
            document.body.classList.toggle('high-contrast-mode', e.matches);
            this.announce(e.matches ? 'High contrast mode enabled' : 'High contrast mode disabled');
        });
    }

    setupScreenReaderSupport() {
        // Enhance dynamic content for screen readers
        const observer = new MutationObserver((mutations) => {
            mutations.forEach((mutation) => {
                if (mutation.type === 'childList') {
                    mutation.addedNodes.forEach((node) => {
                        if (node.nodeType === Node.ELEMENT_NODE) {
                            this.enhanceNewElement(node);
                        }
                    });
                }
            });
        });

        observer.observe(document.body, {
            childList: true,
            subtree: true
        });
    }

    enhanceNewElement(element) {
        // Add accessibility attributes to new elements
        if (element.classList?.contains('chat-message')) {
            this.enhanceChatMessage(element);
        }
        
        if (element.classList?.contains('project-tab')) {
            this.addProjectTabAriaLabels();
        }
        
        if (element.tagName === 'BUTTON' && !element.hasAttribute('aria-label')) {
            this.addButtonAriaLabels();
        }
    }

    enhanceChatMessage(message) {
        const username = message.querySelector('.message-username')?.textContent || 'System';
        const content = message.querySelector('.message-content')?.textContent || '';
        const timestamp = message.querySelector('.message-timestamp')?.textContent || '';
        
        message.setAttribute('role', 'article');
        message.setAttribute('aria-label', `Message from ${username} at ${timestamp}: ${content}`);
        message.setAttribute('tabindex', '0');
        
        // Announce new messages
        this.announce(`New message from ${username}: ${content}`);
    }

    addSkipLinks() {
        const skipLinks = [
            { href: '#main-content', text: 'Skip to main content' },
            { href: '#chat-panel', text: 'Skip to chat' },
            { href: '#status-bar', text: 'Skip to status' }
        ];

        const skipLinkContainer = document.createElement('div');
        skipLinkContainer.className = 'skip-links';
        
        skipLinks.forEach(link => {
            const skipLink = document.createElement('a');
            skipLink.href = link.href;
            skipLink.className = 'skip-link';
            skipLink.textContent = link.text;
            skipLink.addEventListener('click', (e) => {
                e.preventDefault();
                const target = document.querySelector(link.href);
                if (target) {
                    target.focus();
                    target.scrollIntoView({ behavior: 'smooth' });
                    this.announce(`Skipped to ${link.text.toLowerCase()}`);
                }
            });
            skipLinkContainer.appendChild(skipLink);
        });

        document.body.insertBefore(skipLinkContainer, document.body.firstChild);
    }

    enhanceErrorHandling() {
        // Enhance error messages for accessibility
        window.addEventListener('error', (e) => {
            this.announce(`Error occurred: ${e.message}`, 'assertive');
        });

        // Monitor connection status changes
        const connectionStatus = document.querySelector('#connection-status');
        if (connectionStatus) {
            const observer = new MutationObserver(() => {
                const status = connectionStatus.textContent.trim();
                this.announce(`Connection status: ${status}`, 'assertive');
            });
            
            observer.observe(connectionStatus, {
                childList: true,
                characterData: true,
                subtree: true
            });
        }
    }

    setupDynamicContentAnnouncements() {
        // Announce workflow state changes
        const workflowState = document.querySelector('#workflow-state');
        if (workflowState) {
            const observer = new MutationObserver(() => {
                const state = workflowState.textContent.trim();
                this.announce(`Workflow state changed to ${state}`);
            });
            
            observer.observe(workflowState, {
                childList: true,
                characterData: true,
                subtree: true
            });
        }

        // Announce TDD cycle updates
        const tddCycles = document.querySelector('#tdd-cycles');
        if (tddCycles) {
            const observer = new MutationObserver(() => {
                const cycleCount = tddCycles.querySelectorAll('.tdd-cycle-card').length;
                this.announce(`TDD cycles updated: ${cycleCount} active cycles`);
            });
            
            observer.observe(tddCycles, {
                childList: true,
                subtree: true
            });
        }
    }

    enhanceChatAccessibility() {
        const chatInput = document.querySelector('.chat-input-field');
        if (chatInput) {
            // Add command autocomplete accessibility
            chatInput.addEventListener('input', (e) => {
                const value = e.target.value;
                if (value.startsWith('/')) {
                    const autocomplete = document.querySelector('.chat-autocomplete');
                    if (autocomplete && autocomplete.classList.contains('show')) {
                        autocomplete.setAttribute('role', 'listbox');
                        autocomplete.setAttribute('aria-label', 'Command suggestions');
                        
                        const items = autocomplete.querySelectorAll('.autocomplete-item');
                        items.forEach((item, index) => {
                            item.setAttribute('role', 'option');
                            item.setAttribute('aria-selected', 'false');
                            item.setAttribute('id', `autocomplete-option-${index}`);
                        });
                        
                        chatInput.setAttribute('aria-expanded', 'true');
                        chatInput.setAttribute('aria-owns', 'chat-autocomplete');
                        if (items.length > 0) {
                            chatInput.setAttribute('aria-activedescendant', items[0].id);
                        }
                    }
                } else {
                    chatInput.removeAttribute('aria-expanded');
                    chatInput.removeAttribute('aria-activedescendant');
                }
            });

            // Handle arrow key navigation in autocomplete
            chatInput.addEventListener('keydown', (e) => {
                const autocomplete = document.querySelector('.chat-autocomplete.show');
                if (autocomplete && ['ArrowUp', 'ArrowDown', 'Enter', 'Escape'].includes(e.key)) {
                    this.handleAutocompleteNavigation(e, autocomplete, chatInput);
                }
            });
        }
    }

    handleAutocompleteNavigation(e, autocomplete, input) {
        const items = Array.from(autocomplete.querySelectorAll('.autocomplete-item'));
        let selectedIndex = items.findIndex(item => item.classList.contains('selected'));

        switch (e.key) {
            case 'ArrowDown':
                e.preventDefault();
                selectedIndex = Math.min(selectedIndex + 1, items.length - 1);
                break;
            case 'ArrowUp':
                e.preventDefault();
                selectedIndex = Math.max(selectedIndex - 1, 0);
                break;
            case 'Enter':
                e.preventDefault();
                if (selectedIndex >= 0) {
                    items[selectedIndex].click();
                }
                return;
            case 'Escape':
                e.preventDefault();
                autocomplete.classList.remove('show');
                input.removeAttribute('aria-expanded');
                return;
        }

        // Update selection
        items.forEach((item, index) => {
            item.classList.toggle('selected', index === selectedIndex);
            item.setAttribute('aria-selected', (index === selectedIndex).toString());
        });

        if (selectedIndex >= 0) {
            input.setAttribute('aria-activedescendant', items[selectedIndex].id);
            const command = items[selectedIndex].querySelector('.autocomplete-command')?.textContent || '';
            this.announce(`Command suggestion: ${command}`);
        }
    }

    setupProjectTabAccessibility() {
        const tabList = document.querySelector('.tab-list');
        if (tabList) {
            tabList.addEventListener('keydown', (e) => {
                const tabs = Array.from(tabList.querySelectorAll('.project-tab'));
                const currentIndex = tabs.findIndex(tab => tab === document.activeElement);

                if (e.key === 'ArrowLeft' || e.key === 'ArrowRight') {
                    e.preventDefault();
                    let newIndex = currentIndex;
                    
                    if (e.key === 'ArrowLeft') {
                        newIndex = currentIndex > 0 ? currentIndex - 1 : tabs.length - 1;
                    } else {
                        newIndex = currentIndex < tabs.length - 1 ? currentIndex + 1 : 0;
                    }
                    
                    tabs[newIndex].focus();
                } else if (e.key === 'Home') {
                    e.preventDefault();
                    tabs[0].focus();
                } else if (e.key === 'End') {
                    e.preventDefault();
                    tabs[tabs.length - 1].focus();
                }
            });
        }
    }

    // Keyboard shortcut implementations
    focusProjectSearch() {
        const searchInput = document.querySelector('#mobile-project-select, .project-tab');
        if (searchInput) {
            searchInput.focus();
            this.announce('Project search focused');
        }
    }

    toggleChatPanel() {
        const toggleBtn = document.querySelector('#panel-toggle-btn, .chat-toggle-btn');
        if (toggleBtn) {
            toggleBtn.click();
            const chatPanel = document.querySelector('.chat-panel');
            const isOpen = chatPanel?.classList.contains('open');
            this.announce(isOpen ? 'Chat panel opened' : 'Chat panel closed');
        }
    }

    showKeyboardHelp() {
        const helpMessage = `
            Keyboard shortcuts:
            Alt+K - Focus project search
            Alt+C - Toggle chat panel
            Alt+H - Show this help
            Alt+T - Toggle high contrast
            Alt+M - Toggle reduced motion
            Alt+S - Focus search
            Alt+1 - Focus main content
            Alt+2 - Focus chat panel
            Alt+3 - Focus status bar
            Tab - Navigate forward
            Shift+Tab - Navigate backward
            Enter/Space - Activate elements
            Escape - Close dialogs
            Arrow keys - Navigate within components
        `;
        
        this.announce(helpMessage, 'assertive');
        
        // Show visual help if available
        if (window.UI && window.UI.showToast) {
            window.UI.showToast('Keyboard Shortcuts', helpMessage.replace(/\n/g, '<br>'), 'info', 10000);
        }
    }

    toggleHighContrast() {
        this.highContrastMode = !this.highContrastMode;
        document.body.classList.toggle('high-contrast-mode', this.highContrastMode);
        localStorage.setItem('high-contrast-mode', this.highContrastMode.toString());
        this.announce(this.highContrastMode ? 'High contrast mode enabled' : 'High contrast mode disabled');
    }

    toggleReducedMotion() {
        this.reducedMotionMode = !this.reducedMotionMode;
        document.body.classList.toggle('reduced-motion-mode', this.reducedMotionMode);
        localStorage.setItem('reduced-motion-mode', this.reducedMotionMode.toString());
        this.announce(this.reducedMotionMode ? 'Reduced motion enabled' : 'Reduced motion disabled');
    }

    focusSearchInput() {
        const searchInput = document.querySelector('input[type="search"], input[placeholder*="search"]');
        if (searchInput) {
            searchInput.focus();
            this.announce('Search input focused');
        }
    }

    handleEscape() {
        // Close open modals
        const modal = document.querySelector('.modal:not(.hidden)');
        if (modal) {
            const closeBtn = modal.querySelector('.close-btn, [data-dismiss="modal"]');
            if (closeBtn) {
                closeBtn.click();
                return;
            }
        }

        // Close autocomplete
        const autocomplete = document.querySelector('.chat-autocomplete.show');
        if (autocomplete) {
            autocomplete.classList.remove('show');
            return;
        }

        // Return focus to previous element
        if (this.focusHistory.length > 1) {
            const previousElement = this.focusHistory[this.focusHistory.length - 2];
            if (previousElement && document.contains(previousElement)) {
                previousElement.focus();
            }
        }
    }

    showAccessibilityHelp() {
        const helpMessage = `
            Accessibility Features:
            - Full keyboard navigation support
            - Screen reader compatibility
            - High contrast mode (Alt+T)
            - Reduced motion mode (Alt+M)
            - Focus management
            - Live region announcements
            - Skip links
            - ARIA labels and landmarks
            
            For support, press F1 or contact support.
        `;
        
        this.announce(helpMessage, 'assertive');
    }

    focusMainContent() {
        const mainContent = document.querySelector('#main-content, main, .main-content');
        if (mainContent) {
            mainContent.focus();
            this.announce('Main content focused');
        }
    }

    focusChatPanel() {
        const chatPanel = document.querySelector('.chat-panel');
        if (chatPanel && !chatPanel.classList.contains('hidden')) {
            const chatInput = chatPanel.querySelector('.chat-input-field');
            if (chatInput) {
                chatInput.focus();
                this.announce('Chat input focused');
            }
        } else {
            this.announce('Chat panel is not visible');
        }
    }

    focusStatusBar() {
        const statusBar = document.querySelector('.status-bar');
        if (statusBar) {
            statusBar.focus();
            this.announce('Status bar focused');
        }
    }

    triggerRefresh() {
        // Trigger a refresh of the current state
        if (window.visualizer && window.visualizer.refreshState) {
            window.visualizer.refreshState();
            this.announce('State refreshed');
        }
    }

    pauseWorkflow() {
        // Pause the current workflow if possible
        this.announce('Workflow pause requested');
    }

    handleTabNavigation(e) {
        // Custom tab navigation logic for complex components
        const activeElement = document.activeElement;
        
        // Handle project tab navigation
        if (activeElement?.classList.contains('project-tab')) {
            const tabs = Array.from(document.querySelectorAll('.project-tab'));
            const currentIndex = tabs.indexOf(activeElement);
            
            if (!e.shiftKey && currentIndex === tabs.length - 1) {
                // Tab from last project tab should go to tab controls
                e.preventDefault();
                const controls = document.querySelector('.tab-controls button');
                if (controls) controls.focus();
            }
        }
    }

    handleArrowNavigation(e) {
        const activeElement = document.activeElement;
        
        // Handle diagram navigation
        if (activeElement?.closest('.diagram-container')) {
            e.preventDefault();
            // Announce diagram navigation
            this.announce(`Navigating diagram with ${e.key}`);
        }
        
        // Handle project tab navigation with arrows
        if (activeElement?.classList.contains('project-tab')) {
            const tabs = Array.from(document.querySelectorAll('.project-tab'));
            const currentIndex = tabs.indexOf(activeElement);
            let newIndex = currentIndex;
            
            if (e.key === 'ArrowLeft' && currentIndex > 0) {
                newIndex = currentIndex - 1;
            } else if (e.key === 'ArrowRight' && currentIndex < tabs.length - 1) {
                newIndex = currentIndex + 1;
            }
            
            if (newIndex !== currentIndex) {
                e.preventDefault();
                tabs[newIndex].focus();
            }
        }
    }

    handleActivation(e) {
        const activeElement = document.activeElement;
        
        // Handle activation of custom interactive elements
        if (activeElement?.classList.contains('project-tab') ||
            activeElement?.classList.contains('message-reaction') ||
            activeElement?.classList.contains('autocomplete-item')) {
            
            if (e.key === ' ') {
                e.preventDefault(); // Prevent scrolling
            }
            
            // Trigger click
            activeElement.click();
        }
    }

    // Public API methods
    static create() {
        return new AccessibilityManager();
    }

    // Integration with existing visualizer
    integrateWithVisualizer(visualizer) {
        if (!visualizer) return;

        // Enhance state change announcements
        const originalUpdateWorkflowState = visualizer.updateWorkflowState;
        if (originalUpdateWorkflowState) {
            visualizer.updateWorkflowState = (state) => {
                originalUpdateWorkflowState.call(visualizer, state);
                this.announce(`Workflow state changed to ${state}`);
            };
        }

        // Enhance connection status announcements
        const originalUpdateConnectionStatus = visualizer.updateConnectionStatus;
        if (originalUpdateConnectionStatus) {
            visualizer.updateConnectionStatus = (connected) => {
                originalUpdateConnectionStatus.call(visualizer, connected);
                this.announce(connected ? 'Connected to server' : 'Disconnected from server', 'assertive');
            };
        }

        console.log('♿ Accessibility integrated with visualizer');
    }
}

// Initialize accessibility when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        window.AccessibilityManager = AccessibilityManager.create();
        
        // Integrate with existing visualizer if available
        if (window.visualizer) {
            window.AccessibilityManager.integrateWithVisualizer(window.visualizer);
        }
    });
} else {
    window.AccessibilityManager = AccessibilityManager.create();
    
    // Integrate with existing visualizer if available
    if (window.visualizer) {
        window.AccessibilityManager.integrateWithVisualizer(window.visualizer);
    }
}

// Export for module systems
if (typeof module !== 'undefined' && module.exports) {
    module.exports = AccessibilityManager;
}