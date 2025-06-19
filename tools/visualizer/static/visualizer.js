/**
 * TDD State Machine Visualizer Frontend
 * 
 * Real-time WebSocket client for visualizing workflow and TDD state transitions
 * with Mermaid diagram highlighting, TDD cycle management, and activity logging.
 */

class StateVisualizer {
    constructor() {
        this.socket = null;
        this.connected = false;
        this.autoScroll = true;
        this.currentWorkflowState = 'IDLE';
        this.activeTDDCycles = new Map();
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 5;
        this.reconnectDelay = 5000; // 5 seconds
        
        this.initializeSocketIO();
        this.initializeEventHandlers();
        this.initializeMermaid();
        this.updateConnectionStatus(false);
    }

    /**
     * Initialize SocketIO connection
     */
    initializeSocketIO() {
        try {
            this.socket = io({
                transports: ['websocket', 'polling'],
                upgrade: true,
                rememberUpgrade: true
            });

            this.socket.on('connect', () => {
                console.log('Connected to server');
                this.connected = true;
                this.reconnectAttempts = 0;
                this.updateConnectionStatus(true);
                this.addActivityLog('System', 'Connected to state broadcaster', 'success');
                
                // Request current state
                this.socket.emit('request_state');
            });

            this.socket.on('disconnect', (reason) => {
                console.log('Disconnected from server:', reason);
                this.connected = false;
                this.updateConnectionStatus(false);
                this.addActivityLog('System', `Disconnected: ${reason}`, 'error');
                
                // Attempt reconnection
                this.attemptReconnection();
            });

            this.socket.on('connect_error', (error) => {
                console.error('Connection error:', error);
                this.connected = false;
                this.updateConnectionStatus(false);
                this.addActivityLog('System', `Connection error: ${error.message}`, 'error');
            });

            // State update handlers
            this.socket.on('workflow_transition', (data) => {
                this.handleWorkflowTransition(data);
            });

            this.socket.on('tdd_transition', (data) => {
                this.handleTDDTransition(data);
            });

            this.socket.on('agent_activity', (data) => {
                this.handleAgentActivity(data);
            });

            this.socket.on('state_update', (data) => {
                this.handleStateUpdate(data);
            });

            this.socket.on('raw_update', (data) => {
                console.log('Raw update received:', data);
            });

        } catch (error) {
            console.error('Failed to initialize SocketIO:', error);
            this.handleConnectionFailure();
        }
    }

    /**
     * Attempt to reconnect with exponential backoff
     */
    attemptReconnection() {
        if (this.reconnectAttempts >= this.maxReconnectAttempts) {
            this.addActivityLog('System', 'Max reconnection attempts reached', 'error');
            return;
        }

        this.reconnectAttempts++;
        const delay = this.reconnectDelay * Math.pow(2, this.reconnectAttempts - 1);
        
        this.addActivityLog('System', `Reconnecting in ${delay/1000}s (attempt ${this.reconnectAttempts}/${this.maxReconnectAttempts})`, 'warning');
        
        setTimeout(() => {
            if (!this.connected) {
                this.socket.connect();
            }
        }, delay);
    }

    /**
     * Handle connection failure gracefully
     */
    handleConnectionFailure() {
        this.connected = false;
        this.updateConnectionStatus(false);
        this.addActivityLog('System', 'WebSocket connection failed - running in offline mode', 'error');
        
        // Show fallback message
        const workflowDiagram = document.getElementById('workflow-diagram');
        const tddDiagram = document.getElementById('tdd-diagram');
        
        if (workflowDiagram) {
            workflowDiagram.innerHTML = '<div class="offline-message">⚠️ Real-time updates unavailable<br>Check connection and refresh page</div>';
        }
        if (tddDiagram) {
            tddDiagram.innerHTML = '<div class="offline-message">⚠️ Real-time updates unavailable<br>Check connection and refresh page</div>';
        }
    }

    /**
     * Initialize Mermaid with configuration
     */
    initializeMermaid() {
        try {
            mermaid.initialize({
                startOnLoad: true,
                theme: 'default',
                themeVariables: {
                    primaryColor: '#4CAF50',
                    primaryTextColor: '#fff',
                    primaryBorderColor: '#333',
                    lineColor: '#333',
                    secondaryColor: '#f9f9f9',
                    tertiaryColor: '#fff'
                },
                flowchart: {
                    useMaxWidth: true,
                    htmlLabels: true
                },
                stateDiagram: {
                    useMaxWidth: true
                }
            });
            
            // Initial diagram render
            this.renderDiagrams();
        } catch (error) {
            console.error('Failed to initialize Mermaid:', error);
            this.addActivityLog('System', 'Failed to initialize diagrams', 'error');
        }
    }

    /**
     * Initialize UI event handlers
     */
    initializeEventHandlers() {
        // Clear log button
        const clearLogBtn = document.getElementById('clear-log');
        if (clearLogBtn) {
            clearLogBtn.addEventListener('click', () => {
                this.clearActivityLog();
            });
        }

        // Auto-scroll toggle
        const autoScrollBtn = document.getElementById('auto-scroll-toggle');
        if (autoScrollBtn) {
            autoScrollBtn.addEventListener('click', () => {
                this.toggleAutoScroll();
            });
        }

        // Manual refresh button (could be added to UI)
        document.addEventListener('keydown', (event) => {
            if (event.ctrlKey && event.key === 'r') {
                event.preventDefault();
                this.requestStateUpdate();
            }
        });
    }

    /**
     * Handle workflow state transitions
     */
    handleWorkflowTransition(data) {
        console.log('Workflow transition:', data);
        
        const oldState = data.old_state;
        const newState = data.new_state;
        const project = data.project || 'default';
        
        this.currentWorkflowState = newState;
        this.updateWorkflowState(newState);
        this.highlightWorkflowState(newState);
        this.updateLastUpdateTime();
        
        this.addActivityLog(
            'Workflow',
            `${project}: ${oldState} → ${newState}`,
            'workflow'
        );
    }

    /**
     * Handle TDD state transitions
     */
    handleTDDTransition(data) {
        console.log('TDD transition:', data);
        
        const storyId = data.story_id;
        const oldState = data.old_state;
        const newState = data.new_state;
        const project = data.project || 'default';
        
        // Update TDD cycle tracking
        this.activeTDDCycles.set(storyId, {
            storyId: storyId,
            currentState: newState,
            lastUpdated: new Date().toISOString(),
            project: project
        });
        
        this.updateTDDCycles();
        this.highlightTDDState(newState);
        this.updateActiveCyclesCount();
        this.updateLastUpdateTime();
        
        const transition = oldState ? `${oldState} → ${newState}` : `Started: ${newState}`;
        this.addActivityLog(
            'TDD',
            `Story ${storyId}: ${transition}`,
            'tdd'
        );
    }

    /**
     * Handle agent activity events
     */
    handleAgentActivity(data) {
        console.log('Agent activity:', data);
        
        const agentType = data.agent_type;
        const storyId = data.story_id;
        const action = data.action;
        const status = data.status;
        const project = data.project || 'default';
        
        const statusEmoji = {
            'started': '🔄',
            'completed': '✅',
            'failed': '❌',
            'in_progress': '⏳'
        };
        
        const emoji = statusEmoji[status] || '📝';
        
        this.addActivityLog(
            'Agent',
            `${emoji} ${agentType} ${action} (Story ${storyId}) - ${status}`,
            'agent'
        );
        
        this.updateLastUpdateTime();
    }

    /**
     * Handle full state updates
     */
    handleStateUpdate(data) {
        console.log('State update:', data);
        
        // Update workflow state
        if (data.workflow_state) {
            this.currentWorkflowState = data.workflow_state;
            this.updateWorkflowState(data.workflow_state);
            this.highlightWorkflowState(data.workflow_state);
        }
        
        // Update TDD cycles
        if (data.tdd_cycles) {
            this.activeTDDCycles.clear();
            Object.entries(data.tdd_cycles).forEach(([storyId, cycleData]) => {
                this.activeTDDCycles.set(storyId, {
                    storyId: storyId,
                    currentState: cycleData.current_state,
                    lastUpdated: cycleData.last_updated,
                    project: cycleData.project || 'default'
                });
            });
            this.updateTDDCycles();
        }
        
        // Update counts
        this.updateActiveCyclesCount();
        this.updateLastUpdateTime();
        
        this.addActivityLog(
            'System',
            'Full state update received',
            'success'
        );
    }

    /**
     * Update connection status in UI
     */
    updateConnectionStatus(connected) {
        const statusElement = document.getElementById('connection-status');
        if (statusElement) {
            statusElement.textContent = connected ? 'Connected' : 'Disconnected';
            statusElement.className = `status ${connected ? 'connected' : 'disconnected'}`;
        }
    }

    /**
     * Update workflow state display
     */
    updateWorkflowState(state) {
        const stateElement = document.getElementById('workflow-state');
        if (stateElement) {
            stateElement.textContent = state;
        }
    }

    /**
     * Update active cycles count
     */
    updateActiveCyclesCount() {
        const countElement = document.getElementById('active-cycles');
        if (countElement) {
            countElement.textContent = this.activeTDDCycles.size;
        }
    }

    /**
     * Update last update timestamp
     */
    updateLastUpdateTime() {
        const timestampElement = document.getElementById('last-update');
        if (timestampElement) {
            timestampElement.textContent = new Date().toLocaleTimeString();
        }
    }

    /**
     * Highlight current state in workflow diagram
     */
    highlightWorkflowState(currentState) {
        try {
            // Remove existing highlighting
            const workflowNodes = document.querySelectorAll('#workflow-diagram .node');
            workflowNodes.forEach(node => {
                node.classList.remove('current');
                node.classList.add('inactive');
            });

            // Add current state highlighting
            const currentNode = document.querySelector(`#workflow-diagram .node[id*="${currentState}"]`);
            if (currentNode) {
                currentNode.classList.remove('inactive');
                currentNode.classList.add('current');
            }
        } catch (error) {
            console.error('Error highlighting workflow state:', error);
        }
    }

    /**
     * Highlight current state in TDD diagram
     */
    highlightTDDState(currentState) {
        try {
            // Remove existing highlighting
            const tddNodes = document.querySelectorAll('#tdd-diagram .node');
            tddNodes.forEach(node => {
                node.classList.remove('current');
                node.classList.add('inactive');
            });

            // Add current state highlighting
            const currentNode = document.querySelector(`#tdd-diagram .node[id*="${currentState}"]`);
            if (currentNode) {
                currentNode.classList.remove('inactive');
                currentNode.classList.add('current');
            }
        } catch (error) {
            console.error('Error highlighting TDD state:', error);
        }
    }

    /**
     * Update TDD cycles display
     */
    updateTDDCycles() {
        const cyclesContainer = document.getElementById('tdd-cycles');
        if (!cyclesContainer) return;

        // Clear existing cycles
        cyclesContainer.innerHTML = '';

        if (this.activeTDDCycles.size === 0) {
            cyclesContainer.innerHTML = '<div class="no-cycles">No active TDD cycles</div>';
            return;
        }

        // Create cycle cards
        this.activeTDDCycles.forEach((cycle, storyId) => {
            const cycleCard = this.createTDDCycleCard(cycle);
            cyclesContainer.appendChild(cycleCard);
        });
    }

    /**
     * Create a TDD cycle card element
     */
    createTDDCycleCard(cycle) {
        const card = document.createElement('div');
        card.className = 'tdd-cycle-card';
        card.setAttribute('data-story-id', cycle.storyId);

        const lastUpdated = new Date(cycle.lastUpdated).toLocaleTimeString();
        
        card.innerHTML = `
            <div class="cycle-header">
                <span class="story-id">Story ${cycle.storyId}</span>
                <span class="cycle-state ${cycle.currentState}">${cycle.currentState}</span>
            </div>
            <div class="cycle-details">
                <div>Project: ${cycle.project}</div>
                <div>Updated: ${lastUpdated}</div>
            </div>
        `;

        return card;
    }

    /**
     * Add entry to activity log
     */
    addActivityLog(category, message, type = 'info') {
        const logContainer = document.getElementById('activity-log');
        if (!logContainer) return;

        const timestamp = new Date().toLocaleTimeString();
        const logEntry = document.createElement('div');
        logEntry.className = `log-entry ${type}`;
        
        logEntry.innerHTML = `
            <span class="log-timestamp">[${timestamp}]</span>
            <span class="log-content"><strong>${category}:</strong> ${message}</span>
        `;

        logContainer.appendChild(logEntry);

        // Auto-scroll if enabled
        if (this.autoScroll) {
            logContainer.scrollTop = logContainer.scrollHeight;
        }

        // Limit log entries to prevent memory issues
        const entries = logContainer.children;
        if (entries.length > 100) {
            logContainer.removeChild(entries[0]);
        }
    }

    /**
     * Clear activity log
     */
    clearActivityLog() {
        const logContainer = document.getElementById('activity-log');
        if (logContainer) {
            logContainer.innerHTML = '';
            this.addActivityLog('System', 'Activity log cleared', 'info');
        }
    }

    /**
     * Toggle auto-scroll functionality
     */
    toggleAutoScroll() {
        this.autoScroll = !this.autoScroll;
        
        const toggleBtn = document.getElementById('auto-scroll-toggle');
        if (toggleBtn) {
            if (this.autoScroll) {
                toggleBtn.classList.add('active');
                toggleBtn.textContent = 'Auto Scroll';
            } else {
                toggleBtn.classList.remove('active');
                toggleBtn.textContent = 'Manual Scroll';
            }
        }
        
        this.addActivityLog('System', `Auto-scroll ${this.autoScroll ? 'enabled' : 'disabled'}`, 'info');
        
        // Scroll to bottom if auto-scroll was enabled
        if (this.autoScroll) {
            const logContainer = document.getElementById('activity-log');
            if (logContainer) {
                logContainer.scrollTop = logContainer.scrollHeight;
            }
        }
    }

    /**
     * Request state update from server
     */
    requestStateUpdate() {
        if (this.connected && this.socket) {
            this.socket.emit('request_state');
            this.addActivityLog('System', 'Requested state update', 'info');
        } else {
            this.addActivityLog('System', 'Cannot request update - not connected', 'error');
        }
    }

    /**
     * Render Mermaid diagrams
     */
    renderDiagrams() {
        try {
            // Force re-render of Mermaid diagrams
            const workflowDiagram = document.getElementById('workflow-diagram');
            const tddDiagram = document.getElementById('tdd-diagram');
            
            if (workflowDiagram && tddDiagram) {
                mermaid.init(undefined, workflowDiagram);
                mermaid.init(undefined, tddDiagram);
                
                // Apply initial state highlighting
                setTimeout(() => {
                    this.highlightWorkflowState(this.currentWorkflowState);
                }, 500);
            }
        } catch (error) {
            console.error('Error rendering diagrams:', error);
        }
    }

    /**
     * Get connection status
     */
    isConnected() {
        return this.connected;
    }

    /**
     * Manually disconnect
     */
    disconnect() {
        if (this.socket) {
            this.socket.disconnect();
            this.addActivityLog('System', 'Manually disconnected', 'info');
        }
    }

    /**
     * Manually connect
     */
    connect() {
        if (this.socket && !this.connected) {
            this.socket.connect();
            this.addActivityLog('System', 'Attempting to connect...', 'info');
        }
    }
}

// Global visualizer instance
let visualizer;

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    console.log('Initializing TDD State Visualizer...');
    
    try {
        visualizer = new StateVisualizer();
        
        // Expose to global scope for debugging
        window.visualizer = visualizer;
        
        console.log('TDD State Visualizer initialized successfully');
    } catch (error) {
        console.error('Failed to initialize visualizer:', error);
        
        // Show error message in UI
        const container = document.querySelector('.container');
        if (container) {
            const errorMsg = document.createElement('div');
            errorMsg.className = 'error-banner';
            errorMsg.innerHTML = `
                <h3>⚠️ Initialization Error</h3>
                <p>Failed to initialize the state visualizer. Please refresh the page or check the console for details.</p>
                <button onclick="location.reload()">Reload Page</button>
            `;
            errorMsg.style.cssText = `
                background: #ffebee;
                border: 1px solid #f44336;
                border-radius: 8px;
                padding: 20px;
                margin: 20px 0;
                text-align: center;
                color: #d32f2f;
            `;
            container.insertBefore(errorMsg, container.firstChild);
        }
    }
});

// Handle page visibility changes to manage connection
document.addEventListener('visibilitychange', () => {
    if (visualizer) {
        if (document.hidden) {
            console.log('Page hidden - maintaining connection');
        } else {
            console.log('Page visible - requesting state update');
            visualizer.requestStateUpdate();
        }
    }
});

// Handle before unload
window.addEventListener('beforeunload', () => {
    if (visualizer) {
        visualizer.disconnect();
    }
});