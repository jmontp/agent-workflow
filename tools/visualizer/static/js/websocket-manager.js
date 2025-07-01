/**
 * WebSocket Manager - Unified WebSocket connection management
 * 
 * Consolidates WebSocket handling from discord-chat.js and visualizer.js:
 * - Single connection management
 * - Automatic reconnection with exponential backoff
 * - Event routing and handling
 * - Connection state management
 * - Error handling and recovery
 */

class WebSocketManager {
    constructor() {
        this.socket = null;
        this.connected = false;
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 5;
        this.reconnectDelay = 5000;
        this.eventHandlers = new Map();
        this.connectionStateCallbacks = [];
        
        // Room management for project isolation
        this.currentRooms = new Set();
        this.projectContext = null;
        
        // Message queue for offline scenarios
        this.messageQueue = [];
        this.maxQueueSize = 100;
        
        this.initialize();
    }
    
    /**
     * Initialize WebSocket connection
     */
    initialize() {
        try {
            // Check if Socket.IO is available
            if (typeof io === 'undefined') {
                throw new Error('Socket.IO library not loaded - check CDN connectivity');
            }
            
            this.socket = io({
                transports: ['websocket', 'polling'],
                upgrade: true,
                rememberUpgrade: true,
                timeout: 10000,
                forceNew: false
            });
            
            this.setupCoreEventHandlers();
            console.log('🔌 WebSocket Manager initialized');
            
        } catch (error) {
            console.error('Failed to initialize WebSocket:', error);
            this.handleConnectionFailure();
        }
    }
    
    /**
     * Setup core Socket.IO event handlers
     */
    setupCoreEventHandlers() {
        this.socket.on('connect', () => {
            console.log('🔌 Connected to server');
            this.connected = true;
            this.reconnectAttempts = 0;
            
            // Process queued messages
            this.processMessageQueue();
            
            // Rejoin rooms
            this.rejoinRooms();
            
            // Notify all listeners
            this.notifyConnectionState(true);
            
            // Request initial state
            this.emit('request_state');
            this.emit('request_interface_status');
        });
        
        this.socket.on('disconnect', (reason) => {
            console.log('🔌 Disconnected from server:', reason);
            this.connected = false;
            this.notifyConnectionState(false);
            
            // Attempt reconnection for client-side disconnects
            if (reason === 'io client disconnect') {
                // Manual disconnect, don't auto-reconnect
                return;
            }
            
            this.attemptReconnection();
        });
        
        this.socket.on('connect_error', (error) => {
            console.error('🔌 Connection error:', error);
            this.connected = false;
            this.notifyConnectionState(false);
        });
        
        this.socket.on('reconnect', (attemptNumber) => {
            console.log(`🔌 Reconnected after ${attemptNumber} attempts`);
        });
        
        this.socket.on('reconnect_attempt', (attemptNumber) => {
            console.log(`🔌 Reconnection attempt ${attemptNumber}`);
        });
        
        this.socket.on('reconnect_error', (error) => {
            console.error('🔌 Reconnection error:', error);
        });
        
        this.socket.on('reconnect_failed', () => {
            console.error('🔌 Reconnection failed - max attempts reached');
            this.handleConnectionFailure();
        });
        
        // Room management events
        this.socket.on('room_joined', (data) => {
            console.log('🏠 Joined room:', data.room);
            this.currentRooms.add(data.room);
        });
        
        this.socket.on('room_left', (data) => {
            console.log('🏠 Left room:', data.room);
            this.currentRooms.delete(data.room);
        });
        
        // Error handling
        this.socket.on('error', (error) => {
            console.error('🔌 Socket error:', error);
            this.emit('socket_error', { error: error.message || 'Unknown socket error' });
        });
    }
    
    /**
     * Event subscription system
     */
    on(eventName, handler) {
        if (!this.eventHandlers.has(eventName)) {
            this.eventHandlers.set(eventName, new Set());
            
            // Setup Socket.IO listener
            this.socket.on(eventName, (data) => {
                this.notifyEventHandlers(eventName, data);
            });
        }
        
        this.eventHandlers.get(eventName).add(handler);
        
        // Return unsubscribe function
        return () => {
            const handlers = this.eventHandlers.get(eventName);
            if (handlers) {
                handlers.delete(handler);
                if (handlers.size === 0) {
                    this.eventHandlers.delete(eventName);
                    this.socket.off(eventName);
                }
            }
        };
    }
    
    /**
     * Remove event handler
     */
    off(eventName, handler) {
        const handlers = this.eventHandlers.get(eventName);
        if (handlers) {
            handlers.delete(handler);
            if (handlers.size === 0) {
                this.eventHandlers.delete(eventName);
                this.socket.off(eventName);
            }
        }
    }
    
    /**
     * Emit event to server
     */
    emit(eventName, data = {}) {
        if (this.connected && this.socket) {
            // Add project context if available
            const enrichedData = {
                ...data,
                project_name: this.projectContext || data.project_name,
                timestamp: new Date().toISOString()
            };
            
            this.socket.emit(eventName, enrichedData);
            console.log(`📤 Emitted ${eventName}:`, enrichedData);
        } else {
            // Queue message for later
            this.queueMessage(eventName, data);
            console.warn(`📤 Queued ${eventName} (not connected):`, data);
        }
    }
    
    /**
     * Queue messages when disconnected
     */
    queueMessage(eventName, data) {
        if (this.messageQueue.length >= this.maxQueueSize) {
            this.messageQueue.shift(); // Remove oldest message
        }
        
        this.messageQueue.push({
            eventName,
            data,
            timestamp: Date.now()
        });
    }
    
    /**
     * Process queued messages after reconnection
     */
    processMessageQueue() {
        console.log(`📤 Processing ${this.messageQueue.length} queued messages`);
        
        while (this.messageQueue.length > 0) {
            const message = this.messageQueue.shift();
            
            // Only process messages less than 5 minutes old
            if (Date.now() - message.timestamp < 5 * 60 * 1000) {
                this.emit(message.eventName, message.data);
            }
        }
    }
    
    /**
     * Notify event handlers
     */
    notifyEventHandlers(eventName, data) {
        const handlers = this.eventHandlers.get(eventName);
        if (handlers) {
            handlers.forEach(handler => {
                try {
                    handler(data);
                } catch (error) {
                    console.error(`Error in ${eventName} handler:`, error);
                }
            });
        }
    }
    
    /**
     * Connection state management
     */
    onConnectionStateChange(callback) {
        this.connectionStateCallbacks.push(callback);
        
        // Return unsubscribe function
        return () => {
            const index = this.connectionStateCallbacks.indexOf(callback);
            if (index > -1) {
                this.connectionStateCallbacks.splice(index, 1);
            }
        };
    }
    
    notifyConnectionState(connected) {
        this.connectionStateCallbacks.forEach(callback => {
            try {
                callback(connected);
            } catch (error) {
                console.error('Error in connection state callback:', error);
            }
        });
    }
    
    /**
     * Room management for project isolation
     */
    joinRoom(roomName, userData = {}) {
        const joinData = {
            room: roomName,
            ...userData,
            project_name: this.projectContext
        };
        
        this.emit('join_room', joinData);
        console.log('🏠 Joining room:', roomName);
    }
    
    leaveRoom(roomName) {
        this.emit('leave_room', { room: roomName });
        this.currentRooms.delete(roomName);
        console.log('🏠 Leaving room:', roomName);
    }
    
    rejoinRooms() {
        console.log('🏠 Rejoining rooms after reconnection');
        this.currentRooms.forEach(room => {
            this.joinRoom(room);
        });
    }
    
    /**
     * Project context management
     */
    setProjectContext(projectName) {
        const oldProject = this.projectContext;
        this.projectContext = projectName;
        
        console.log(`📁 Project context changed: ${oldProject} → ${projectName}`);
        
        // Emit project switch event
        this.emit('switch_project', {
            old_project: oldProject,
            new_project: projectName
        });
        
        return oldProject;
    }
    
    getProjectContext() {
        return this.projectContext;
    }
    
    /**
     * Chat-specific methods (consolidated from discord-chat.js)
     */
    sendChatMessage(message, userData = {}) {
        const chatData = {
            message: message,
            user_id: userData.user_id || 'anonymous',
            username: userData.username || 'User',
            session_id: userData.session_id,
            project_name: this.projectContext,
            room: this.getCurrentProjectRoom()
        };
        
        this.emit('chat_command', chatData);
    }
    
    startTyping(userData = {}) {
        const typingData = {
            user_id: userData.user_id || 'anonymous',
            username: userData.username || 'User',
            project_name: this.projectContext,
            room: this.getCurrentProjectRoom()
        };
        
        this.emit('start_typing', typingData);
    }
    
    stopTyping(userData = {}) {
        const typingData = {
            user_id: userData.user_id || 'anonymous',
            username: userData.username || 'User',
            project_name: this.projectContext,
            room: this.getCurrentProjectRoom()
        };
        
        this.emit('stop_typing', typingData);
    }
    
    joinProjectRoom(projectName, userData = {}) {
        const roomName = `project_${projectName}`;
        const joinData = {
            user_id: userData.user_id || 'anonymous',
            username: userData.username || 'User',
            project_name: projectName,
            session_id: userData.session_id
        };
        
        this.joinRoom(roomName, joinData);
        return roomName;
    }
    
    leaveProjectRoom(projectName) {
        const roomName = `project_${projectName}`;
        this.leaveRoom(roomName);
    }
    
    getCurrentProjectRoom() {
        return this.projectContext ? `project_${this.projectContext}` : null;
    }
    
    /**
     * State management methods (consolidated from visualizer.js)
     */
    requestStateUpdate() {
        this.emit('request_state');
    }
    
    requestProjectState(projectName) {
        this.emit('request_project_state', { project: projectName });
    }
    
    requestInterfaceStatus() {
        this.emit('request_interface_status');
    }
    
    requestChatHistory(limit = 50) {
        this.emit('request_chat_history', {
            limit: limit,
            project_name: this.projectContext,
            room: this.getCurrentProjectRoom()
        });
    }
    
    /**
     * Reconnection logic with exponential backoff
     */
    attemptReconnection() {
        if (this.reconnectAttempts >= this.maxReconnectAttempts) {
            console.error('🔌 Max reconnection attempts reached');
            this.handleConnectionFailure();
            return;
        }
        
        this.reconnectAttempts++;
        const delay = this.reconnectDelay * Math.pow(2, this.reconnectAttempts - 1);
        
        console.log(`🔌 Reconnecting in ${delay/1000}s (attempt ${this.reconnectAttempts}/${this.maxReconnectAttempts})`);
        
        setTimeout(() => {
            if (!this.connected && this.socket) {
                this.socket.connect();
            }
        }, delay);
    }
    
    /**
     * Handle connection failure gracefully
     */
    handleConnectionFailure() {
        console.error('🔌 WebSocket connection failed - running in offline mode');
        
        // Notify listeners
        this.notifyEventHandlers('connection_failed', {
            error: 'Connection failed after maximum retry attempts'
        });
        
        // Show user-friendly error
        if (window.domUtils) {
            window.domUtils.showMessage(
                'Connection lost. Some features may be unavailable. Please refresh the page.',
                'error',
                10000
            );
        }
    }
    
    /**
     * Manual connection control
     */
    connect() {
        if (this.socket && !this.connected) {
            this.socket.connect();
            console.log('🔌 Manual connection attempt');
        }
    }
    
    disconnect() {
        if (this.socket && this.connected) {
            this.socket.disconnect();
            console.log('🔌 Manual disconnect');
        }
    }
    
    /**
     * Get connection status
     */
    isConnected() {
        return this.connected && this.socket && this.socket.connected;
    }
    
    /**
     * Get connection info
     */
    getConnectionInfo() {
        return {
            connected: this.connected,
            reconnectAttempts: this.reconnectAttempts,
            currentRooms: Array.from(this.currentRooms),
            projectContext: this.projectContext,
            queuedMessages: this.messageQueue.length,
            socketId: this.socket ? this.socket.id : null
        };
    }
    
    /**
     * Cleanup and destroy
     */
    destroy() {
        console.log('🔌 Destroying WebSocket Manager');
        
        // Clear all event handlers
        this.eventHandlers.clear();
        this.connectionStateCallbacks.length = 0;
        
        // Clear message queue
        this.messageQueue.length = 0;
        
        // Disconnect socket
        if (this.socket) {
            this.socket.disconnect();
            this.socket = null;
        }
        
        this.connected = false;
    }
    
    /**
     * Utility methods for common patterns
     */
    once(eventName, handler) {
        const unsubscribe = this.on(eventName, (data) => {
            handler(data);
            unsubscribe();
        });
        return unsubscribe;
    }
    
    waitForConnection(timeout = 10000) {
        return new Promise((resolve, reject) => {
            if (this.connected) {
                resolve();
                return;
            }
            
            const timeoutId = setTimeout(() => {
                reject(new Error('Connection timeout'));
            }, timeout);
            
            const unsubscribe = this.onConnectionStateChange((connected) => {
                if (connected) {
                    clearTimeout(timeoutId);
                    unsubscribe();
                    resolve();
                }
            });
        });
    }
    
    emitAndWaitForResponse(eventName, data = {}, responseEvent = null, timeout = 5000) {
        return new Promise((resolve, reject) => {
            const actualResponseEvent = responseEvent || `${eventName}_response`;
            
            const timeoutId = setTimeout(() => {
                reject(new Error(`Timeout waiting for ${actualResponseEvent}`));
            }, timeout);
            
            const unsubscribe = this.once(actualResponseEvent, (responseData) => {
                clearTimeout(timeoutId);
                resolve(responseData);
            });
            
            this.emit(eventName, data);
        });
    }
}

// Create global instance
const wsManager = new WebSocketManager();

// Expose globally
window.WebSocketManager = WebSocketManager;
window.wsManager = wsManager;

// Export for module usage
if (typeof module !== 'undefined' && module.exports) {
    module.exports = WebSocketManager;
}

console.log('🔌 WebSocket Manager loaded and ready');