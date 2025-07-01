/**
 * Discord-Style Chat Interface
 * 
 * WebSocket-powered real-time chat interface with Discord bot command support,
 * autocomplete, keyboard shortcuts, and typing indicators.
 */

class DiscordChat {
    constructor(socketIO, visualizer) {
        this.socket = socketIO;
        this.visualizer = visualizer;
        this.userId = this.generateUserId();
        this.username = 'User';
        this.sessionId = null;
        this.projectName = 'default';
        this.permissionLevel = 'contributor';
        this.collaborationEnabled = false;
        this.commandHistory = [];
        this.historyIndex = -1;
        this.currentInput = '';
        this.typingTimeout = null;
        this.lastTypingTime = 0;
        this.autocompleteResults = [];
        this.selectedAutocomplete = -1;
        this.isTyping = false;
        
        // Initialize components
        this.initializeEventHandlers();
        this.setupWebSocketHandlers();
        this.loadChatHistory();
        this.initializeCollaboration();
        
        console.log('Discord chat initialized with user ID:', this.userId);
    }
    
    /**
     * Generate unique user ID for session
     */
    generateUserId() {
        return 'user_' + Math.random().toString(36).substr(2, 9);
    }
    
    /**
     * Initialize DOM event handlers
     */
    initializeEventHandlers() {
        const messageInput = document.getElementById('chat-input-field');
        const sendButton = document.getElementById('chat-send-btn');
        const chatMessages = document.getElementById('chat-messages');
        const autocompleteDropdown = document.getElementById('chat-autocomplete');
        
        if (!messageInput || !sendButton || !chatMessages) {
            console.warn('Chat elements not found - chat interface may not be loaded');
            return;
        }
        
        // Message input handlers
        messageInput.addEventListener('keydown', (e) => this.handleKeyDown(e));
        messageInput.addEventListener('keyup', (e) => this.handleKeyUp(e));
        messageInput.addEventListener('input', (e) => this.handleInput(e));
        messageInput.addEventListener('blur', () => this.hideAutocomplete());
        
        // Send button
        sendButton.addEventListener('click', () => this.sendMessage());
        
        // Auto-scroll on new messages
        const resizeObserver = new ResizeObserver(() => {
            if (this.shouldAutoScroll(chatMessages)) {
                this.scrollToBottom(chatMessages);
            }
        });
        resizeObserver.observe(chatMessages);
        
        // Panel resizing
        this.initializePanelResizing();
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
     * Setup WebSocket event handlers for chat
     */
    setupWebSocketHandlers() {
        // New chat message
        this.socket.on('new_chat_message', (data) => {
            this.addMessageToChat(data);
        });
        
        // Command response
        this.socket.on('command_response', (data) => {
            this.addMessageToChat(data);
            this.highlightStateChange(data);
        });
        
        // Typing indicators
        this.socket.on('typing_indicator', (data) => {
            this.handleTypingIndicator(data);
        });
        
        // Bot typing
        this.socket.on('bot_typing', (data) => {
            this.handleBotTyping(data);
        });
        
        // Chat history response
        this.socket.on('chat_history', (data) => {
            this.loadHistoryMessages(data.messages);
        });
        
        // User presence
        this.socket.on('user_joined', (data) => {
            this.showUserPresence(data, 'joined');
        });
        
        this.socket.on('user_left', (data) => {
            this.showUserPresence(data, 'left');
        });
        
        // Error handling
        this.socket.on('command_error', (data) => {
            this.showError(data.error);
        });
        
        this.socket.on('chat_error', (data) => {
            this.showError(data.error);
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
        const messageInput = document.getElementById('chat-input-field');
        const message = messageInput.value.trim();
        
        if (!message) return;
        
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
        this.socket.emit('chat_command', {
            message: message,
            user_id: this.userId,
            username: this.username,
            session_id: this.sessionId,
            project_name: this.projectName || 'default'
        });
        
        // Clear input
        messageInput.value = '';
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
        const dropdown = document.getElementById('autocomplete-dropdown');
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
        const dropdown = document.getElementById('autocomplete-dropdown');
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
                project_name: this.projectName
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
                project_name: this.projectName
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
     * Show error message
     */
    showError(errorMessage) {
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
            this.socket.emit('request_chat_history', { limit: 50 });
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
            project_name: this.projectName
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
}

// Export for module usage
if (typeof module !== 'undefined' && module.exports) {
    module.exports = DiscordChat;
}

// Also expose to window for browser usage
if (typeof window !== 'undefined') {
    window.DiscordChat = DiscordChat;
}