/**
 * Discord-Style Chat Interface
 * 
 * WebSocket-powered real-time chat interface with Discord bot command support,
 * autocomplete, keyboard shortcuts, and typing indicators.
 * Now uses unified WebSocket Manager and DOM utilities.
 */

class DiscordChat {
    constructor(socketIO, visualizer) {
        // Use global WebSocket manager if available, fallback to provided socket
        this.socket = window.wsManager || socketIO;
        this.visualizer = visualizer;
        this.userId = this.generateUserId();
        this.username = 'User';
        this.sessionId = null;
        this.projectName = 'default';
        this.permissionLevel = 'contributor';
        
        // Project awareness
        this.setupProjectIntegration();
        this.collaborationEnabled = false;
        this.commandHistory = [];
        this.historyIndex = -1;
        this.currentInput = '';
        this.typingTimeout = null;
        this.lastTypingTime = 0;
        this.autocompleteResults = [];
        this.selectedAutocomplete = -1;
        this.isTyping = false;
        
        // Project-specific chat isolation
        this.projectChatHistory = new Map(); // project_name -> messages array
        this.projectCommandHistory = new Map(); // project_name -> commands array
        this.currentProjectRoom = null;
        this.projectTypingUsers = new Map(); // project_name -> Set of typing users
        
        // Initialize components with error handling
        try {
            this.initializeEventHandlers();
            this.setupWebSocketHandlers();
            this.initializeProjectIsolation();
            this.loadChatHistory();
            this.initializeCollaboration();
            
            console.log('Discord chat initialized with user ID:', this.userId);
        } catch (error) {
            if (window.ErrorManager) {
                window.ErrorManager.handleError(error, {
                    component: 'DiscordChat',
                    operation: 'initialization'
                });
            } else {
                console.error('Failed to initialize Discord chat:', error);
            }
        }
    }
    
    /**
     * Generate unique user ID for session
     */
    generateUserId() {
        return 'user_' + Math.random().toString(36).substr(2, 9);
    }
    
    /**
     * Initialize project-specific chat isolation
     */
    initializeProjectIsolation() {
        // Load project chat data from localStorage
        this.loadProjectData();
        
        // Set up project switching listener
        this.setupProjectSwitchListener();
        
        // Initialize current project room
        this.joinProjectRoom(this.projectName);
        
        console.log('Project isolation initialized for:', this.projectName);
    }
    
    /**
     * Load project-specific data from localStorage
     */
    loadProjectData() {
        try {
            const storedChatHistory = localStorage.getItem('agent_workflow_chat_history');
            if (storedChatHistory) {
                const data = JSON.parse(storedChatHistory);
                this.projectChatHistory = new Map(Object.entries(data));
            }
            
            const storedCommandHistory = localStorage.getItem('agent_workflow_command_history');
            if (storedCommandHistory) {
                const data = JSON.parse(storedCommandHistory);
                this.projectCommandHistory = new Map(Object.entries(data));
            }
            
            // Load current project's command history
            const currentCommands = this.projectCommandHistory.get(this.projectName) || [];
            this.commandHistory = [...currentCommands];
            
        } catch (error) {
            console.warn('Failed to load project data from localStorage:', error);
        }
    }
    
    /**
     * Save project-specific data to localStorage
     */
    saveProjectData() {
        try {
            // Save chat history
            const chatHistoryObj = Object.fromEntries(this.projectChatHistory);
            localStorage.setItem('agent_workflow_chat_history', JSON.stringify(chatHistoryObj));
            
            // Save command history for current project
            this.projectCommandHistory.set(this.projectName, this.commandHistory.slice(0, 20));
            const commandHistoryObj = Object.fromEntries(this.projectCommandHistory);
            localStorage.setItem('agent_workflow_command_history', JSON.stringify(commandHistoryObj));
            
        } catch (error) {
            console.warn('Failed to save project data to localStorage:', error);
        }
    }
    
    /**
     * Set up project switching listener
     */
    setupProjectSwitchListener() {
        // Listen for project changes from visualizer
        if (window.visualizer && window.visualizer.onProjectChange) {
            const originalOnProjectChange = window.visualizer.onProjectChange;
            window.visualizer.onProjectChange = (newProject, oldProject) => {
                this.switchProject(newProject, oldProject);
                if (originalOnProjectChange) {
                    originalOnProjectChange.call(window.visualizer, newProject, oldProject);
                }
            };
        }
        
        // Also listen for direct project changes on the chat instance
        document.addEventListener('projectChanged', (event) => {
            this.switchProject(event.detail.newProject, event.detail.oldProject);
        });
    }
    
    /**
     * Initialize DOM event handlers using shared utilities
     */
    initializeEventHandlers() {
        console.log('🔧 Initializing DiscordChat event handlers...');
        
        const messageInput = $('#chat-input-field');
        const sendButton = $('#chat-send-btn');
        const chatMessages = $('#chat-messages');
        const autocompleteDropdown = $('#chat-autocomplete');
        
        console.log('Elements found:', {
            messageInput: !!messageInput,
            sendButton: !!sendButton,
            chatMessages: !!chatMessages,
            autocompleteDropdown: !!autocompleteDropdown
        });
        
        if (!messageInput || !sendButton || !chatMessages) {
            console.warn('Chat elements not found - chat interface may not be loaded');
            console.log('Missing elements:', {
                messageInput: !messageInput ? 'MISSING' : 'found',
                sendButton: !sendButton ? 'MISSING' : 'found',
                chatMessages: !chatMessages ? 'MISSING' : 'found'
            });
            return;
        }
        
        // Message input handlers using DOM utilities
        DOMUtils.on(messageInput, 'keydown', (e) => this.handleKeyDown(e));
        DOMUtils.on(messageInput, 'keyup', (e) => this.handleKeyUp(e));
        DOMUtils.on(messageInput, 'input', (e) => {
            // Handle input for autocomplete
            this.handleInput(e);
            
            // Enable/disable send button based on input
            const hasContent = e.target.value.trim().length > 0;
            sendButton.disabled = !hasContent;
            console.log('Input changed, has content:', hasContent, 'button disabled:', !hasContent);
        });
        DOMUtils.on(messageInput, 'blur', () => this.hideAutocomplete());
        
        // Initial state - disable send button if input is empty
        sendButton.disabled = messageInput.value.trim().length === 0;
        
        // Send button
        DOMUtils.on(sendButton, 'click', () => {
            console.log('Send button clicked');
            this.sendMessage();
        });
        
        console.log('✅ Event handlers attached successfully');
        
        // Auto-scroll on new messages
        const resizeObserver = new ResizeObserver(() => {
            if (this.shouldAutoScroll(chatMessages)) {
                this.scrollToBottom(chatMessages);
            }
        });
        resizeObserver.observe(chatMessages);
        
        // Panel resizing
        this.initializePanelResizing();
        
        // Panel toggle functionality
        const panelToggleBtn = document.getElementById('panel-toggle-btn');
        const chatPanel = document.getElementById('chat-panel');
        const mainContent = document.getElementById('main-content');
        
        if (panelToggleBtn && chatPanel && mainContent) {
            panelToggleBtn.addEventListener('click', () => {
                console.log('Panel toggle clicked');
                chatPanel.classList.toggle('hidden');
                mainContent.classList.toggle('full-width');
                
                // Update button appearance
                if (chatPanel.classList.contains('hidden')) {
                    panelToggleBtn.textContent = '💬';
                    panelToggleBtn.title = 'Show Chat Panel';
                } else {
                    panelToggleBtn.textContent = '❌';
                    panelToggleBtn.title = 'Hide Chat Panel';
                }
            });
        }
        
        // Chat close button functionality
        const chatCloseBtn = document.getElementById('chat-close-btn');
        if (chatCloseBtn && chatPanel) {
            chatCloseBtn.addEventListener('click', () => {
                console.log('Chat close button clicked');
                chatPanel.classList.remove('open');
                chatPanel.classList.add('hidden');
                
                // Also update the main content if needed
                if (mainContent) {
                    mainContent.classList.remove('chat-open');
                }
                
                // Update panel toggle button if it exists
                if (panelToggleBtn) {
                    panelToggleBtn.textContent = '💬';
                    panelToggleBtn.title = 'Show Chat Panel';
                }
            });
        }
    }
    
    /**
     * Initialize panel resizing functionality
     */
    initializePanelResizing() {
        const resizeHandle = document.querySelector('.resize-handle');
        const leftPanel = document.querySelector('.left-panel');
        const rightPanel = document.querySelector('.right-panel');
        
        if (!resizeHandle || !leftPanel || !rightPanel) return;
        
        let isResizing = false;
        
        resizeHandle.addEventListener('mousedown', (e) => {
            isResizing = true;
            document.body.style.cursor = 'col-resize';
            document.body.style.userSelect = 'none';
        });
        
        document.addEventListener('mousemove', (e) => {
            if (!isResizing) return;
            
            const containerRect = document.querySelector('.main-content').getBoundingClientRect();
            const newLeftWidth = ((e.clientX - containerRect.left) / containerRect.width) * 100;
            
            // Constrain between 30% and 70%
            if (newLeftWidth >= 30 && newLeftWidth <= 70) {
                leftPanel.style.width = `${newLeftWidth}%`;
                rightPanel.style.width = `${100 - newLeftWidth}%`;
            }
        });
        
        document.addEventListener('mouseup', () => {
            if (isResizing) {
                isResizing = false;
                document.body.style.cursor = '';
                document.body.style.userSelect = '';
            }
        });
    }
    
    /**
     * Setup WebSocket event handlers for chat using unified manager
     */
    setupWebSocketHandlers() {
        // Use WebSocket manager if available
        const socketManager = this.socket;
        
        // New chat message - now project-aware
        socketManager.on('new_chat_message', (data) => {
            console.log('Received new_chat_message:', data);
            this.handleProjectMessage(data);
        });
        
        // Command response - now project-aware
        socketManager.on('command_response', (data) => {
            console.log('Received command_response:', data);
            this.handleProjectMessage(data);
            this.highlightStateChange(data);
        });
        
        // Project-specific typing indicators
        socketManager.on('typing_indicator', (data) => {
            this.handleProjectTypingIndicator(data);
        });
        
        // Bot typing - project-aware
        socketManager.on('bot_typing', (data) => {
            this.handleProjectBotTyping(data);
        });
        
        // Project-specific chat history response
        socketManager.on('chat_history', (data) => {
            this.loadProjectHistoryMessages(data.messages, data.project_name);
        });
        
        // Project-specific user presence
        this.socket.on('user_joined', (data) => {
            this.showProjectUserPresence(data, 'joined');
        });
        
        this.socket.on('user_left', (data) => {
            this.showProjectUserPresence(data, 'left');
        });
        
        // Project switching event
        this.socket.on('project_switched', (data) => {
            this.handleProjectSwitch(data.project_name, data.previous_project);
        });
        
        // Room joined/left confirmations
        this.socket.on('room_joined', (data) => {
            console.log('Joined project room:', data.room);
            this.currentProjectRoom = data.room;
        });
        
        this.socket.on('room_left', (data) => {
            console.log('Left project room:', data.room);
        });
        
        // Project-aware error handling
        this.socket.on('command_error', (data) => {
            this.showProjectError(data.error, data.project_name);
        });
        
        this.socket.on('chat_error', (data) => {
            this.showProjectError(data.error, data.project_name);
        });
    }
    
    /**
     * Handle keyboard input
     */
    handleKeyDown(event) {
        const messageInput = event.target;
        
        switch (event.key) {
            case 'Enter':
                if (event.shiftKey) {
                    // Allow new line with Shift+Enter
                    return;
                }
                event.preventDefault();
                this.sendMessage();
                break;
                
            case 'ArrowUp':
                event.preventDefault();
                this.navigateHistory('up');
                break;
                
            case 'ArrowDown':
                event.preventDefault();
                this.navigateHistory('down');
                break;
                
            case 'Tab':
                if (this.autocompleteResults.length > 0) {
                    event.preventDefault();
                    this.selectAutocomplete();
                }
                break;
                
            case 'Escape':
                this.hideAutocomplete();
                break;
                
            case 'ArrowUp':
            case 'ArrowDown':
                if (this.autocompleteResults.length > 0) {
                    event.preventDefault();
                    this.navigateAutocomplete(event.key === 'ArrowUp' ? 'up' : 'down');
                }
                break;
        }
    }
    
    /**
     * Handle key up events
     */
    handleKeyUp(event) {
        // Update typing indicator
        this.updateTypingIndicator();
    }
    
    /**
     * Handle input changes
     */
    handleInput(event) {
        const input = event.target.value;
        
        // Show autocomplete for commands
        if (input.startsWith('/')) {
            this.showAutocomplete(input);
        } else {
            this.hideAutocomplete();
        }
    }
    
    /**
     * Send message to chat
     */
    sendMessage() {
        console.log('sendMessage called');
        const messageInput = document.getElementById('chat-input-field');
        const sendButton = document.getElementById('chat-send-btn');
        const message = messageInput.value.trim();
        
        console.log('Message to send:', message);
        if (!message) {
            console.log('Empty message, returning');
            return;
        }
        
        // Add to command history
        if (message.startsWith('/')) {
            this.commandHistory.unshift(message);
            // Keep only last 20 commands
            if (this.commandHistory.length > 20) {
                this.commandHistory.pop();
            }
        }
        
        // Reset history navigation
        this.historyIndex = -1;
        this.currentInput = '';
        
        // Send via WebSocket with collaboration data
        console.log('Sending message via socket.emit');
        console.log('Socket available:', !!this.socket);
        console.log('Socket connected:', this.socket && this.socket.connected);
        
        try {
            // Use WebSocket manager's sendChatMessage method if available
            if (this.socket.sendChatMessage) {
                this.socket.sendChatMessage(message, {
                    user_id: this.userId,
                    username: this.username,
                    session_id: this.sessionId
                });
            } else {
                this.socket.emit('chat_command', {
                    message: message,
                    user_id: this.userId,
                    username: this.username,
                    session_id: this.sessionId,
                    project_name: this.projectName || 'default',
                    room: this.currentProjectRoom
                });
            }
            console.log('Message sent successfully for project:', this.projectName);
            
            // Save command to project-specific history
            this.saveProjectData();
        } catch (error) {
            console.error('Error sending message:', error);
        }
        
        // Clear input and disable send button
        messageInput.value = '';
        sendButton.disabled = true;
        this.hideAutocomplete();
        
        // Stop typing indicator
        this.stopTypingIndicator();
    }
    
    /**
     * Navigate command history
     */
    navigateHistory(direction) {
        const messageInput = document.getElementById('chat-input-field');
        
        if (direction === 'up') {
            if (this.historyIndex === -1) {
                this.currentInput = messageInput.value;
                this.historyIndex = 0;
            } else if (this.historyIndex < this.commandHistory.length - 1) {
                this.historyIndex++;
            }
            
            if (this.historyIndex < this.commandHistory.length) {
                messageInput.value = this.commandHistory[this.historyIndex];
            }
        } else if (direction === 'down') {
            if (this.historyIndex > 0) {
                this.historyIndex--;
                messageInput.value = this.commandHistory[this.historyIndex];
            } else if (this.historyIndex === 0) {
                this.historyIndex = -1;
                messageInput.value = this.currentInput;
            }
        }
        
        // Move cursor to end
        messageInput.setSelectionRange(messageInput.value.length, messageInput.value.length);
    }
    
    /**
     * Show autocomplete dropdown
     */
    async showAutocomplete(query) {
        try {
            const response = await fetch(`/api/chat/autocomplete?query=${encodeURIComponent(query)}`);
            const data = await response.json();
            
            this.autocompleteResults = data.suggestions || [];
            this.selectedAutocomplete = -1;
            
            const dropdown = document.getElementById('chat-autocomplete');
            if (!dropdown) return;
            
            if (this.autocompleteResults.length === 0) {
                dropdown.style.display = 'none';
                return;
            }
            
            // Build dropdown HTML
            const html = this.autocompleteResults.map((suggestion, index) => `
                <div class="autocomplete-item ${index === this.selectedAutocomplete ? 'selected' : ''}"
                     data-index="${index}">
                    <div class="command">${suggestion.command}</div>
                    <div class="description">${suggestion.description}</div>
                </div>
            `).join('');
            
            dropdown.innerHTML = html;
            dropdown.style.display = 'block';
            
            // Add click handlers
            dropdown.querySelectorAll('.autocomplete-item').forEach((item, index) => {
                item.addEventListener('click', () => {
                    this.selectedAutocomplete = index;
                    this.selectAutocomplete();
                });
            });
            
        } catch (error) {
            console.error('Error fetching autocomplete:', error);
            this.hideAutocomplete();
        }
    }
    
    /**
     * Hide autocomplete dropdown
     */
    hideAutocomplete() {
        const dropdown = document.getElementById('chat-autocomplete');
        if (dropdown) {
            dropdown.style.display = 'none';
        }
        this.autocompleteResults = [];
        this.selectedAutocomplete = -1;
    }
    
    /**
     * Navigate autocomplete selection
     */
    navigateAutocomplete(direction) {
        if (this.autocompleteResults.length === 0) return;
        
        if (direction === 'up') {
            this.selectedAutocomplete = this.selectedAutocomplete <= 0 
                ? this.autocompleteResults.length - 1 
                : this.selectedAutocomplete - 1;
        } else {
            this.selectedAutocomplete = this.selectedAutocomplete >= this.autocompleteResults.length - 1 
                ? 0 
                : this.selectedAutocomplete + 1;
        }
        
        // Update dropdown display
        const dropdown = document.getElementById('chat-autocomplete');
        if (dropdown) {
            const items = dropdown.querySelectorAll('.autocomplete-item');
            items.forEach((item, index) => {
                item.classList.toggle('selected', index === this.selectedAutocomplete);
            });
        }
    }
    
    /**
     * Select autocomplete suggestion
     */
    selectAutocomplete() {
        if (this.selectedAutocomplete >= 0 && this.selectedAutocomplete < this.autocompleteResults.length) {
            const suggestion = this.autocompleteResults[this.selectedAutocomplete];
            const messageInput = document.getElementById('chat-input-field');
            
            messageInput.value = suggestion.command + ' ';
            messageInput.focus();
            messageInput.setSelectionRange(messageInput.value.length, messageInput.value.length);
            
            this.hideAutocomplete();
        }
    }
    
    /**
     * Update typing indicator
     */
    updateTypingIndicator() {
        const now = Date.now();
        
        if (!this.isTyping) {
            this.isTyping = true;
            this.socket.emit('start_typing', {
                user_id: this.userId,
                username: this.username,
                project_name: this.projectName,
                room: this.currentProjectRoom
            });
        }
        
        this.lastTypingTime = now;
        
        // Clear existing timeout
        if (this.typingTimeout) {
            clearTimeout(this.typingTimeout);
        }
        
        // Set timeout to stop typing indicator
        this.typingTimeout = setTimeout(() => {
            this.stopTypingIndicator();
        }, 3000);
    }
    
    /**
     * Stop typing indicator
     */
    stopTypingIndicator() {
        if (this.isTyping) {
            this.isTyping = false;
            this.socket.emit('stop_typing', {
                user_id: this.userId,
                username: this.username,
                project_name: this.projectName,
                room: this.currentProjectRoom
            });
        }
        
        if (this.typingTimeout) {
            clearTimeout(this.typingTimeout);
            this.typingTimeout = null;
        }
    }
    
    /**
     * Handle typing indicator from other users
     */
    handleTypingIndicator(data) {
        if (data.user_id === this.userId) return; // Ignore own typing
        
        const indicator = document.getElementById('typing-indicators');
        if (!indicator) return;
        
        if (data.typing) {
            indicator.textContent = `${data.username} is typing...`;
            indicator.style.display = 'block';
        } else {
            indicator.style.display = 'none';
        }
    }
    
    /**
     * Handle bot typing indicator
     */
    handleBotTyping(data) {
        const indicator = document.getElementById('typing-indicators');
        if (!indicator) return;
        
        if (data.typing) {
            indicator.innerHTML = '🤖 Agent Bot is thinking...';
            indicator.style.display = 'block';
        } else {
            indicator.style.display = 'none';
        }
    }
    
    /**
     * Switch to a different project
     */
    switchProject(newProject, oldProject) {
        console.log(`Switching from project '${oldProject}' to '${newProject}'`);
        
        // Save current project's chat state
        if (oldProject && oldProject !== newProject) {
            this.saveCurrentProjectState();
            this.leaveProjectRoom(oldProject);
        }
        
        // Update current project
        this.projectName = newProject;
        
        // Load new project's chat state
        this.loadProjectState(newProject);
        
        // Join new project room
        this.joinProjectRoom(newProject);
        
        // Update UI to show current project
        this.updateProjectDisplay(newProject);
        
        // Clear typing indicators for old project
        this.clearTypingIndicators();
        
        // Emit project switch event to server
        this.socket.emit('switch_project', {
            user_id: this.userId,
            new_project: newProject,
            old_project: oldProject
        });
        
        console.log('Project switched successfully to:', newProject);
    }
    
    /**
     * Save current project's chat state
     */
    saveCurrentProjectState() {
        const currentMessages = this.getCurrentChatMessages();
        this.projectChatHistory.set(this.projectName, currentMessages);
        this.projectCommandHistory.set(this.projectName, [...this.commandHistory]);
        this.saveProjectData();
    }
    
    /**
     * Load project-specific chat state
     */
    loadProjectState(projectName) {
        // Load project's command history
        const projectCommands = this.projectCommandHistory.get(projectName) || [];
        this.commandHistory = [...projectCommands];
        
        // Load and display project's chat history
        const projectMessages = this.projectChatHistory.get(projectName) || [];
        this.displayProjectMessages(projectMessages);
        
        // Reset history navigation
        this.historyIndex = -1;
        this.currentInput = '';
    }
    
    /**
     * Get current chat messages from DOM
     */
    getCurrentChatMessages() {
        const chatMessages = document.getElementById('chat-messages');
        if (!chatMessages) return [];
        
        const messages = [];
        const messageElements = chatMessages.querySelectorAll('.message');
        
        messageElements.forEach(element => {
            const messageId = element.getAttribute('data-message-id');
            if (messageId) {
                // Extract message data from DOM (simplified approach)
                const timestamp = element.querySelector('.timestamp')?.textContent || new Date().toISOString();
                const username = element.querySelector('.username')?.textContent || 'Unknown';
                const messageContent = element.querySelector('.message-content')?.textContent || '';
                const messageType = element.classList.contains('bot') ? 'bot' : 
                                 element.classList.contains('system') ? 'system' : 'user';
                
                messages.push({
                    id: messageId,
                    username: username,
                    message: messageContent,
                    timestamp: timestamp,
                    type: messageType,
                    project_name: this.projectName
                });
            }
        });
        
        return messages;
    }
    
    /**
     * Display project-specific messages
     */
    displayProjectMessages(messages) {
        const chatMessages = document.getElementById('chat-messages');
        if (!chatMessages) return;
        
        // Clear current chat
        chatMessages.innerHTML = '';
        
        // Add project messages
        messages.forEach(message => {
            this.addMessageToChat(message);
        });
        
        // Scroll to bottom
        this.scrollToBottom(chatMessages);
    }
    
    /**
     * Join project-specific WebSocket room
     */
    joinProjectRoom(projectName) {
        if (!projectName) return;
        
        this.socket.emit('join_project_room', {
            user_id: this.userId,
            username: this.username,
            project_name: projectName,
            session_id: this.sessionId
        });
        
        console.log('Joining project room:', projectName);
    }
    
    /**
     * Leave project-specific WebSocket room
     */
    leaveProjectRoom(projectName) {
        if (!projectName) return;
        
        this.socket.emit('leave_project_room', {
            user_id: this.userId,
            project_name: projectName
        });
        
        console.log('Leaving project room:', projectName);
    }
    
    /**
     * Update project display in UI
     */
    updateProjectDisplay(projectName) {
        // Update project name in chat header
        const projectHeader = document.getElementById('chat-project-name');
        if (projectHeader) {
            projectHeader.textContent = projectName;
        }
        
        // Update chat title
        const chatTitle = document.querySelector('.chat-header h3');
        if (chatTitle) {
            chatTitle.textContent = `Discord Chat - ${projectName}`;
        }
        
        // Update status text
        const statusElement = document.getElementById('chat-status-text');
        if (statusElement) {
            statusElement.title = `Active project: ${projectName}`;
        }
    }
    
    /**
     * Handle project-specific messages
     */
    handleProjectMessage(messageData) {
        // Only display messages for current project
        if (messageData.project_name && messageData.project_name !== this.projectName) {
            console.log('Message for different project, storing but not displaying:', messageData.project_name);
            // Store message for the correct project
            const projectMessages = this.projectChatHistory.get(messageData.project_name) || [];
            projectMessages.push(messageData);
            this.projectChatHistory.set(messageData.project_name, projectMessages);
            return;
        }
        
        // Display message for current project
        this.addMessageToChat(messageData);
    }
    
    /**
     * Handle project-specific typing indicators
     */
    handleProjectTypingIndicator(data) {
        // Only show typing indicators for current project
        if (data.project_name && data.project_name !== this.projectName) {
            return;
        }
        
        if (data.user_id === this.userId) return; // Ignore own typing
        
        const indicator = document.getElementById('typing-indicators');
        if (!indicator) return;
        
        if (data.typing) {
            indicator.textContent = `${data.username} is typing...`;
            indicator.style.display = 'block';
        } else {
            indicator.style.display = 'none';
        }
    }
    
    /**
     * Handle project-specific bot typing
     */
    handleProjectBotTyping(data) {
        // Only show bot typing for current project
        if (data.project_name && data.project_name !== this.projectName) {
            return;
        }
        
        const indicator = document.getElementById('typing-indicators');
        if (!indicator) return;
        
        if (data.typing) {
            indicator.innerHTML = '🤖 Agent Bot is thinking...';
            indicator.style.display = 'block';
        } else {
            indicator.style.display = 'none';
        }
    }
    
    /**
     * Handle project switch event from server
     */
    handleProjectSwitch(newProject, oldProject) {
        console.log('Server initiated project switch:', { newProject, oldProject });
        this.switchProject(newProject, oldProject);
    }
    
    /**
     * Clear typing indicators
     */
    clearTypingIndicators() {
        const indicator = document.getElementById('typing-indicators');
        if (indicator) {
            indicator.style.display = 'none';
        }
    }
    
    /**
     * Show project-specific user presence
     */
    showProjectUserPresence(data, action) {
        // Only show presence for current project
        if (data.project_name && data.project_name !== this.projectName) {
            return;
        }
        
        if (data.user_id === this.userId) return; // Don't show own presence
        
        const systemMessage = {
            id: 'presence_' + Date.now(),
            user_id: 'system',
            username: 'System',
            message: `${data.username} ${action} the ${data.project_name} project chat`,
            timestamp: new Date().toISOString(),
            type: 'system',
            project_name: this.projectName
        };
        
        this.addMessageToChat(systemMessage);
    }
    
    /**
     * Show project-specific error messages
     */
    showProjectError(errorMessage, projectName) {
        // Only show errors for current project
        if (projectName && projectName !== this.projectName) {
            return;
        }
        
        const errorMsg = {
            id: 'error_' + Date.now(),
            user_id: 'system',
            username: 'System',
            message: `Error: ${errorMessage}`,
            timestamp: new Date().toISOString(),
            type: 'system',
            error: true,
            project_name: this.projectName
        };
        
        this.addMessageToChat(errorMsg);
    }
    
    /**
     * Load project-specific chat history
     */
    loadProjectHistoryMessages(messages, projectName) {
        if (!messages) return;
        
        // Store messages for the specified project
        const targetProject = projectName || this.projectName;
        this.projectChatHistory.set(targetProject, messages);
        
        // Only display if it's for the current project
        if (targetProject === this.projectName) {
            this.displayProjectMessages(messages);
        }
        
        // Save to localStorage
        this.saveProjectData();
    }
    
    /**
     * Add message to chat display
     */
    addMessageToChat(messageData) {
        const chatMessages = document.getElementById('chat-messages');
        if (!chatMessages) return;
        
        const messageElement = this.createMessageElement(messageData);
        
        // Check if we should auto-scroll
        const shouldAutoScroll = this.shouldAutoScroll(chatMessages);
        
        // Add message
        chatMessages.appendChild(messageElement);
        
        // Auto-scroll if needed
        if (shouldAutoScroll) {
            this.scrollToBottom(chatMessages);
        }
        
        // Limit message count
        this.limitMessageCount(chatMessages);
        
        // Add sound notification for new messages (except own)
        if (messageData.user_id !== this.userId) {
            this.playMessageSound();
        }
    }
    
    /**
     * Create message element
     */
    createMessageElement(messageData) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${messageData.type}`;
        messageDiv.setAttribute('data-message-id', messageData.id);
        
        const timestamp = new Date(messageData.timestamp).toLocaleTimeString();
        
        if (messageData.type === 'bot') {
            return this.createBotMessage(messageData, timestamp);
        } else if (messageData.type === 'user') {
            return this.createUserMessage(messageData, timestamp);
        } else if (messageData.type === 'system') {
            return this.createSystemMessage(messageData, timestamp);
        }
        
        return messageDiv;
    }
    
    /**
     * Create bot message element
     */
    createBotMessage(messageData, timestamp) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message bot ${messageData.error ? 'error' : ''}`;
        messageDiv.setAttribute('data-message-id', messageData.id);
        
        const isCommand = messageData.command_result && messageData.command_result.command;
        const content = messageData.message || 'Command processed';
        
        messageDiv.innerHTML = `
            <div class="message-header">
                <div class="avatar bot-avatar">🤖</div>
                <div class="message-info">
                    <span class="username bot-name">Agent Bot</span>
                    <span class="timestamp">${timestamp}</span>
                </div>
            </div>
            <div class="message-content">
                ${isCommand ? this.formatCommandResponse(messageData.command_result) : this.formatMessage(content)}
            </div>
        `;
        
        return messageDiv;
    }
    
    /**
     * Create user message element
     */
    createUserMessage(messageData, timestamp) {
        const messageDiv = document.createElement('div');
        messageDiv.className = 'message user';
        messageDiv.setAttribute('data-message-id', messageData.id);
        
        const isCommand = messageData.message.startsWith('/');
        
        messageDiv.innerHTML = `
            <div class="message-header">
                <div class="avatar user-avatar">👤</div>
                <div class="message-info">
                    <span class="username">${messageData.username}</span>
                    <span class="timestamp">${timestamp}</span>
                </div>
            </div>
            <div class="message-content ${isCommand ? 'command' : ''}">
                ${this.formatMessage(messageData.message)}
            </div>
        `;
        
        return messageDiv;
    }
    
    /**
     * Create system message element
     */
    createSystemMessage(messageData, timestamp) {
        const messageDiv = document.createElement('div');
        messageDiv.className = 'message system';
        messageDiv.setAttribute('data-message-id', messageData.id);
        
        messageDiv.innerHTML = `
            <div class="system-content">
                <span class="system-icon">ℹ️</span>
                <span class="system-text">${messageData.message}</span>
                <span class="timestamp">${timestamp}</span>
            </div>
        `;
        
        return messageDiv;
    }
    
    /**
     * Format command response with rich display
     */
    formatCommandResponse(commandResult) {
        if (!commandResult) return 'Command processed';
        
        let html = `<div class="command-response">`;
        
        if (commandResult.command) {
            html += `<div class="command-echo">Command: <code>${commandResult.command}</code></div>`;
        }
        
        if (commandResult.success !== undefined) {
            const statusIcon = commandResult.success ? '✅' : '❌';
            const statusClass = commandResult.success ? 'success' : 'error';
            html += `<div class="command-status ${statusClass}">${statusIcon} ${commandResult.success ? 'Success' : 'Error'}</div>`;
        }
        
        if (commandResult.response) {
            html += `<div class="command-output">${this.formatMessage(commandResult.response)}</div>`;
        }
        
        if (commandResult.data && typeof commandResult.data === 'object') {
            html += `<div class="command-data"><pre>${JSON.stringify(commandResult.data, null, 2)}</pre></div>`;
        }
        
        html += `</div>`;
        return html;
    }
    
    /**
     * Format message content (handle markdown, links, etc.)
     */
    formatMessage(content) {
        if (!content) return '';
        
        // Escape HTML
        let formatted = content.replace(/[<>&"']/g, (match) => {
            const escapeChars = {
                '<': '&lt;',
                '>': '&gt;',
                '&': '&amp;',
                '"': '&quot;',
                "'": '&#39;'
            };
            return escapeChars[match];
        });
        
        // Convert line breaks
        formatted = formatted.replace(/\n/g, '<br>');
        
        // Format inline code
        formatted = formatted.replace(/`([^`]+)`/g, '<code>$1</code>');
        
        // Format URLs
        const urlRegex = /(https?:\/\/[^\s<>"{}|\\^`[\]]+)/g;
        formatted = formatted.replace(urlRegex, '<a href="$1" target="_blank" rel="noopener">$1</a>');
        
        return formatted;
    }
    
    /**
     * Check if chat should auto-scroll
     */
    shouldAutoScroll(container) {
        const threshold = 50; // pixels from bottom
        return (container.scrollTop + container.clientHeight + threshold) >= container.scrollHeight;
    }
    
    /**
     * Scroll to bottom of chat
     */
    scrollToBottom(container) {
        container.scrollTop = container.scrollHeight;
    }
    
    /**
     * Limit number of messages displayed
     */
    limitMessageCount(container, maxMessages = 100) {
        const messages = container.children;
        while (messages.length > maxMessages) {
            container.removeChild(messages[0]);
        }
    }
    
    /**
     * Play message notification sound
     */
    playMessageSound() {
        // Simple audio notification
        try {
            const audio = new Audio('data:audio/wav;base64,UklGRnoGAABXQVZFZm10IBAAAAABAAEAQB8AAEAfAAABAAgAZGF0YQoGAACBhYqFbF1fdJivrJBhNjVgodDbq2EcBj+a2/LDciUFLIHO8tiJNwgZaLvt559NEAxQp+PwtmMcBjiR1/LMeSwFJHfH8N2QQAoUXrTp66hVFApGn+DyvmoeETSH0fPTgjMGHm7A7+OYSQwKUKXh9LJlHgg2jdXzzHkpBSl+zPLZizoIGGG26+OZUQ4LTKXi9LNmHgk5ktTM6Yn9jdN0');
            audio.volume = 0.1;
            audio.play().catch(() => {}); // Ignore errors
        } catch (error) {
            // Ignore audio errors
        }
    }
    
    /**
     * Show user presence notification
     */
    showUserPresence(data, action) {
        if (data.user_id === this.userId) return; // Don't show own presence
        
        const systemMessage = {
            id: 'presence_' + Date.now(),
            user_id: 'system',
            username: 'System',
            message: `${data.username} ${action} the chat`,
            timestamp: new Date().toISOString(),
            type: 'system'
        };
        
        this.addMessageToChat(systemMessage);
    }
    
    /**
     * Show error message using unified system
     */
    showError(errorMessage) {
        // Use global message system first
        if (window.domUtils) {
            window.domUtils.showMessage(errorMessage, 'error');
        }
        
        // Also add to chat
        const errorMsg = {
            id: 'error_' + Date.now(),
            user_id: 'system',
            username: 'System',
            message: `Error: ${errorMessage}`,
            timestamp: new Date().toISOString(),
            type: 'system',
            error: true
        };
        
        this.addMessageToChat(errorMsg);
    }
    
    /**
     * Highlight state changes in visualizer
     */
    highlightStateChange(messageData) {
        if (!messageData.command_result || !this.visualizer) return;
        
        const result = messageData.command_result;
        
        // Highlight workflow state changes
        if (result.workflow_state) {
            this.visualizer.highlightWorkflowState(result.workflow_state);
        }
        
        // Highlight TDD state changes
        if (result.tdd_state) {
            this.visualizer.highlightTDDState(result.tdd_state);
        }
        
        // Trigger state synchronization
        setTimeout(() => {
            if (this.visualizer.requestStateUpdate) {
                this.visualizer.requestStateUpdate();
            }
        }, 500);
    }
    
    /**
     * Load chat history on initialization
     */
    async loadChatHistory() {
        try {
            this.socket.emit('request_chat_history', { 
                limit: 50,
                project_name: this.projectName,
                room: this.currentProjectRoom
            });
        } catch (error) {
            console.error('Error loading chat history:', error);
        }
    }
    
    /**
     * Load history messages into chat
     */
    loadHistoryMessages(messages) {
        const chatMessages = document.getElementById('chat-messages');
        if (!chatMessages || !messages) return;
        
        // Clear existing messages
        chatMessages.innerHTML = '';
        
        // Add history messages
        messages.forEach(message => {
            this.addMessageToChat(message);
        });
        
        // Scroll to bottom
        this.scrollToBottom(chatMessages);
    }
    
    /**
     * Initialize collaboration features
     */
    async initializeCollaboration() {
        try {
            // Try to join collaboration session
            const response = await fetch('/api/collaboration/join', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    user_id: this.userId,
                    project_name: this.projectName,
                    permission_level: this.permissionLevel
                })
            });
            
            if (response.ok) {
                const data = await response.json();
                if (data.success) {
                    this.sessionId = data.session_id;
                    this.collaborationEnabled = true;
                    console.log('Collaboration session joined:', this.sessionId);
                    
                    // Update UI to show collaboration status
                    this.updateCollaborationStatus(true);
                }
            } else {
                console.warn('Collaboration not available - using basic chat mode');
                this.collaborationEnabled = false;
            }
        } catch (error) {
            console.warn('Collaboration initialization failed:', error);
            this.collaborationEnabled = false;
        }
        
        // Join basic chat regardless
        this.joinChat();
    }
    
    /**
     * Join chat session
     */
    joinChat() {
        this.socket.emit('join_chat', {
            user_id: this.userId,
            username: this.username,
            session_id: this.sessionId,
            project_name: this.projectName,
            room: this.currentProjectRoom
        });
    }
    
    /**
     * Update collaboration status in UI
     */
    updateCollaborationStatus(enabled) {
        const statusElement = document.getElementById('chat-status-text');
        if (statusElement) {
            if (enabled) {
                statusElement.textContent = 'Collaborative';
                statusElement.title = `Collaboration enabled (${this.permissionLevel})`;
            } else {
                statusElement.textContent = 'Connected';
                statusElement.title = 'Basic chat mode';
            }
        }
    }
    
    /**
     * Leave chat session
     */
    leaveChat() {
        this.socket.emit('leave_chat', {
            user_id: this.userId,
            username: this.username
        });
    }
    
    /**
     * Update username
     */
    setUsername(newUsername) {
        this.username = newUsername || 'User';
    }
    
    /**
     * Get current username
     */
    getUsername() {
        return this.username;
    }
    
    /**
     * Get user ID
     */
    getUserId() {
        return this.userId;
    }
    
    /**
     * Set current project (external API)
     */
    setProject(projectName) {
        if (projectName && projectName !== this.projectName) {
            this.switchProject(projectName, this.projectName);
        }
    }
    
    /**
     * Get current project name
     */
    getProject() {
        return this.projectName;
    }
    
    /**
     * Get project chat history (external API)
     */
    getProjectHistory(projectName) {
        return this.projectChatHistory.get(projectName) || [];
    }
    
    /**
     * Clear project chat history (external API)
     */
    clearProjectHistory(projectName) {
        if (projectName) {
            this.projectChatHistory.delete(projectName);
            this.projectCommandHistory.delete(projectName);
            this.saveProjectData();
            
            // If it's current project, clear display
            if (projectName === this.projectName) {
                const chatMessages = document.getElementById('chat-messages');
                if (chatMessages) {
                    chatMessages.innerHTML = '';
                }
            }
        }
    }
    
    /**
     * Setup project integration
     */
    setupProjectIntegration() {
        // Listen for project switch events
        window.addEventListener('projectSwitch', (event) => {
            const { projectId } = event.detail;
            console.log(`💬 Chat switching to project: ${projectId}`);
            
            this.projectName = projectId;
            
            // Update chat title to reflect active project
            this.updateChatTitle(projectId);
            
            // Clear chat and reload history for new project
            this.clearChatForProjectSwitch();
            this.loadChatHistory();
            
            // Re-join chat with new project context
            this.joinChat();
        });
    }
    
    /**
     * Update chat title to show current project
     */
    updateChatTitle(projectId) {
        const chatTitle = document.querySelector('.chat-title');
        if (chatTitle && window.projectManager) {
            const project = window.projectManager.projects.get(projectId);
            const projectName = project ? project.name : projectId;
            chatTitle.innerHTML = `
                💬 Discord Chat
                <span style="font-size: 12px; opacity: 0.7; margin-left: 8px;">
                    ${project ? project.icon : '📁'} ${projectName}
                </span>
            `;
        }
    }
    
    /**
     * Clear chat for project switch
     */
    clearChatForProjectSwitch() {
        const chatMessages = document.getElementById('chat-messages');
        if (chatMessages) {
            chatMessages.innerHTML = '';
            
            // Add project switch indicator
            const switchMessage = {
                id: 'project_switch_' + Date.now(),
                user_id: 'system',
                username: 'System',
                message: `Switched to project: ${this.projectName}`,
                timestamp: new Date().toISOString(),
                type: 'system'
            };
            
            this.addMessageToChat(switchMessage);
        }
    }
    
    /**
     * Get current project name for display
     */
    getCurrentProjectName() {
        if (window.projectManager) {
            const project = window.projectManager.projects.get(this.projectName);
            return project ? project.name : this.projectName;
        }
        return this.projectName;
    }
}

// Export for module usage
if (typeof module !== 'undefined' && module.exports) {
    module.exports = DiscordChat;
}

// Also expose to window for browser usage
if (typeof window !== 'undefined') {
    window.DiscordChat = DiscordChat;
}