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
        
        // Interface management
        this.interfaceStatus = {};
        this.activeInterface = null;
        this.interfaceTypes = [];
        this.agentTypes = [];
        
        // Initialize components with error isolation
        this.initializeSocketIO();
        this.initializeEventHandlers();
        
        // Non-critical initializations (don't fail constructor)
        try {
            this.initializeInterfaceManagement();
        } catch (e) {
            console.warn('Interface management initialization failed:', e);
        }
        
        try {
            this.initializeMermaid();
        } catch (e) {
            console.warn('Mermaid initialization failed:', e);
        }
        
        this.updateConnectionStatus(false);
    }

    /**
     * Initialize SocketIO connection
     */
    initializeSocketIO() {
        try {
            // Check if Socket.IO is available
            if (typeof io === 'undefined') {
                throw new Error('Socket.IO library not loaded - check CDN connectivity');
            }
            
            this.socket = io({
                transports: ['websocket', 'polling'],
                upgrade: true,
                rememberUpgrade: true,
                timeout: 10000
            });

            this.socket.on('connect', () => {
                console.log('Connected to server');
                this.connected = true;
                this.reconnectAttempts = 0;
                this.updateConnectionStatus(true);
                this.addActivityLog('System', 'Connected to state broadcaster', 'success');
                
                // Request current state and interface status
                this.socket.emit('request_state');
                this.socket.emit('request_interface_status');
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

            // Interface management events
            this.socket.on('interface_changed', (data) => {
                this.handleInterfaceChanged(data);
            });

            this.socket.on('interface_status', (data) => {
                this.handleInterfaceStatus(data);
            });

            this.socket.on('interface_error', (data) => {
                this.handleInterfaceError(data);
            });

            this.socket.on('interface_switch_result', (data) => {
                this.handleInterfaceSwitchResult(data);
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
            // Check if Mermaid is available
            if (typeof mermaid === 'undefined') {
                console.warn('Mermaid library not loaded - diagrams will not be available');
                this.addActivityLog('System', 'Mermaid diagrams unavailable - check CDN connectivity', 'warning');
                return;
            }
            
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
     * Update workflow state display with TDD cycle indicators
     */
    updateWorkflowState(state) {
        this.currentWorkflowState = state;
        const stateElement = document.getElementById('workflow-state');
        if (stateElement) {
            const activeCycles = this.activeTDDCycles.size;
            stateElement.textContent = state;
            
            // Add TDD cycle indicator for SPRINT_ACTIVE state
            if (state === 'SPRINT_ACTIVE' && activeCycles > 0) {
                stateElement.textContent += ` (${activeCycles} TDD cycles)`;
                stateElement.style.color = '#FF5722'; // Orange for active with cycles
            } else if (state === 'SPRINT_REVIEW' && activeCycles > 0) {
                stateElement.style.color = '#F44336'; // Red for review with blocking cycles
            } else {
                stateElement.style.color = ''; // Default color
            }
        }
        
        this.highlightWorkflowState(state);
        this.updateTDDConstraintIndicators(state);
    }
    
    /**
     * Update TDD constraint visual indicators
     */
    updateTDDConstraintIndicators(state) {
        const activeCycles = this.activeTDDCycles.size;
        
        // Update status bar with constraint information
        const lastUpdateElement = document.getElementById('last-update');
        if (lastUpdateElement && state === 'SPRINT_REVIEW' && activeCycles > 0) {
            lastUpdateElement.style.color = '#F44336';
            lastUpdateElement.title = `Cannot complete review: ${activeCycles} TDD cycles still active`;
        } else if (lastUpdateElement) {
            lastUpdateElement.style.color = '';
            lastUpdateElement.title = '';
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

    /**
     * Initialize interface management functionality
     */
    async initializeInterfaceManagement() {
        try {
            // Load interface types and agent types
            await this.loadInterfaceTypes();
            
            // Load current interface status
            await this.loadInterfaceStatus();
            
            // Setup interface management event handlers
            this.setupInterfaceEventHandlers();
            
            console.log('Interface management initialized');
        } catch (error) {
            console.error('Failed to initialize interface management:', error);
        }
    }

    /**
     * Load available interface and agent types
     */
    async loadInterfaceTypes() {
        try {
            const response = await fetch('/api/interfaces/types');
            const data = await response.json();
            
            this.interfaceTypes = data.interface_types || [];
            this.agentTypes = data.agent_types || [];
            
            // Populate interface selector
            this.populateInterfaceSelector();
            
            // Populate agent type selector
            this.populateAgentTypeSelector();
            
        } catch (error) {
            console.error('Failed to load interface types:', error);
        }
    }

    /**
     * Load current interface status
     */
    async loadInterfaceStatus() {
        try {
            const response = await fetch('/api/interfaces');
            const data = await response.json();
            
            this.interfaceStatus = data.interfaces || {};
            this.activeInterface = data.active_interface;
            
            // Update UI
            this.updateInterfaceStatusDisplay();
            this.updateActiveInterfaceDisplay();
            
        } catch (error) {
            console.error('Failed to load interface status:', error);
        }
    }

    /**
     * Setup interface management event handlers
     */
    setupInterfaceEventHandlers() {
        // Interface selector
        const interfaceSelect = document.getElementById('interface-select');
        const switchBtn = document.getElementById('switch-interface-btn');
        const testBtn = document.getElementById('test-interface-btn');
        
        if (switchBtn) {
            switchBtn.addEventListener('click', () => {
                const selectedInterface = interfaceSelect.value;
                if (selectedInterface && selectedInterface !== this.activeInterface) {
                    this.switchInterface(selectedInterface);
                }
            });
        }
        
        if (testBtn) {
            testBtn.addEventListener('click', () => {
                const selectedInterface = interfaceSelect.value;
                if (selectedInterface) {
                    this.testInterface(selectedInterface);
                }
            });
        }

        // Configuration modal
        const configBtn = document.getElementById('interface-config-btn');
        const configModal = document.getElementById('interface-config-modal');
        const closeModalBtn = document.getElementById('close-config-modal');
        const cancelBtn = document.getElementById('cancel-config-btn');
        const saveBtn = document.getElementById('save-config-btn');
        
        if (configBtn) {
            configBtn.addEventListener('click', () => {
                this.openConfigurationModal();
            });
        }
        
        if (closeModalBtn) {
            closeModalBtn.addEventListener('click', () => {
                this.closeConfigurationModal();
            });
        }
        
        if (cancelBtn) {
            cancelBtn.addEventListener('click', () => {
                this.closeConfigurationModal();
            });
        }
        
        if (saveBtn) {
            saveBtn.addEventListener('click', () => {
                this.saveConfiguration();
            });
        }

        // Configuration tabs
        const tabBtns = document.querySelectorAll('.tab-btn');
        tabBtns.forEach(btn => {
            btn.addEventListener('click', () => {
                const targetTab = btn.getAttribute('data-tab');
                this.switchConfigTab(targetTab);
            });
        });

        // Agent testing
        const generateBtn = document.getElementById('test-generate-btn');
        const clearBtn = document.getElementById('clear-response-btn');
        
        if (generateBtn) {
            generateBtn.addEventListener('click', () => {
                this.testAgentGeneration();
            });
        }
        
        if (clearBtn) {
            clearBtn.addEventListener('click', () => {
                this.clearTestResponse();
            });
        }

        // Range input updates
        const temperatureRange = document.getElementById('anthropic-temperature');
        const temperatureValue = document.getElementById('temperature-value');
        if (temperatureRange && temperatureValue) {
            temperatureRange.addEventListener('input', (e) => {
                temperatureValue.textContent = e.target.value;
            });
        }

        const delayRange = document.getElementById('mock-response-delay');
        const delayValue = document.getElementById('delay-value');
        if (delayRange && delayValue) {
            delayRange.addEventListener('input', (e) => {
                delayValue.textContent = parseFloat(e.target.value).toFixed(1);
            });
        }

        const failureRange = document.getElementById('mock-failure-rate');
        const failureValue = document.getElementById('failure-value');
        if (failureRange && failureValue) {
            failureRange.addEventListener('input', (e) => {
                failureValue.textContent = parseFloat(e.target.value).toFixed(2);
            });
        }

        // Close modal on outside click
        if (configModal) {
            configModal.addEventListener('click', (e) => {
                if (e.target === configModal) {
                    this.closeConfigurationModal();
                }
            });
        }
    }

    /**
     * Populate interface selector dropdown
     */
    populateInterfaceSelector() {
        const select = document.getElementById('interface-select');
        if (!select) return;
        
        select.innerHTML = '';
        
        this.interfaceTypes.forEach(interfaceType => {
            const option = document.createElement('option');
            option.value = interfaceType.type;
            option.textContent = interfaceType.name;
            if (interfaceType.type === this.activeInterface) {
                option.selected = true;
            }
            select.appendChild(option);
        });
    }

    /**
     * Populate agent type selector
     */
    populateAgentTypeSelector() {
        const select = document.getElementById('agent-type-select');
        if (!select) return;
        
        // Keep existing options but ensure they match our agent types
        select.innerHTML = '';
        
        this.agentTypes.forEach(agentType => {
            const option = document.createElement('option');
            option.value = agentType.type;
            option.textContent = agentType.name;
            select.appendChild(option);
        });
    }

    /**
     * Update interface status display
     */
    updateInterfaceStatusDisplay() {
        const interfaceMap = {
            'claude_code': 'claude',
            'anthropic_api': 'anthropic',
            'mock': 'mock'
        };
        
        Object.entries(this.interfaceStatus).forEach(([interfaceType, status]) => {
            const cardId = interfaceMap[interfaceType];
            if (!cardId) return;
            
            const card = document.getElementById(`interface-status-${cardId}`);
            if (!card) return;
            
            const indicator = card.querySelector('.status-indicator');
            const text = card.querySelector('.status-text');
            
            if (indicator && text) {
                const statusValue = status.status || 'unknown';
                indicator.setAttribute('data-status', statusValue);
                
                let displayText = statusValue.charAt(0).toUpperCase() + statusValue.slice(1);
                if (status.request_count > 0) {
                    displayText += ` (${status.request_count} requests)`;
                }
                if (status.error_count > 0) {
                    displayText += ` [${status.error_count} errors]`;
                }
                
                text.textContent = displayText;
            }
        });
    }

    /**
     * Update active interface display
     */
    updateActiveInterfaceDisplay() {
        const interfaceElement = document.getElementById('active-interface');
        if (!interfaceElement) return;
        
        if (this.activeInterface) {
            const interfaceType = this.interfaceTypes.find(type => type.type === this.activeInterface);
            const displayName = interfaceType ? interfaceType.name : this.activeInterface;
            interfaceElement.textContent = displayName;
            
            // Update interface selector
            const select = document.getElementById('interface-select');
            if (select) {
                select.value = this.activeInterface;
            }
        } else {
            interfaceElement.textContent = 'None';
        }
    }

    /**
     * Switch to a different interface
     */
    async switchInterface(interfaceType) {
        try {
            const switchBtn = document.getElementById('switch-interface-btn');
            if (switchBtn) {
                switchBtn.disabled = true;
                switchBtn.innerHTML = '<span class="loading-spinner"></span>Switching...';
            }
            
            const response = await fetch(`/api/interfaces/${interfaceType}/switch`, {
                method: 'POST'
            });
            
            const result = await response.json();
            
            if (result.success) {
                this.activeInterface = result.active_interface;
                this.updateActiveInterfaceDisplay();
                this.addActivityLog('Interface', `Switched to ${interfaceType}`, 'success');
                
                // Update interface status
                await this.loadInterfaceStatus();
            } else {
                this.addActivityLog('Interface', `Failed to switch: ${result.error}`, 'error');
                this.showMessage(result.error, 'error');
            }
            
        } catch (error) {
            console.error('Failed to switch interface:', error);
            this.addActivityLog('Interface', `Switch error: ${error.message}`, 'error');
            this.showMessage('Failed to switch interface', 'error');
        } finally {
            const switchBtn = document.getElementById('switch-interface-btn');
            if (switchBtn) {
                switchBtn.disabled = false;
                switchBtn.innerHTML = 'Switch';
            }
        }
    }

    /**
     * Test an interface connection
     */
    async testInterface(interfaceType) {
        try {
            const testBtn = document.getElementById('test-interface-btn');
            if (testBtn) {
                testBtn.disabled = true;
                testBtn.innerHTML = '<span class="loading-spinner"></span>Testing...';
            }
            
            const response = await fetch(`/api/interfaces/${interfaceType}/test`, {
                method: 'POST'
            });
            
            const result = await response.json();
            
            if (result.success) {
                this.addActivityLog('Interface', `Test passed: ${interfaceType}`, 'success');
                this.showMessage(`${interfaceType} test successful`, 'success');
            } else {
                this.addActivityLog('Interface', `Test failed: ${result.error}`, 'error');
                this.showMessage(`Test failed: ${result.error}`, 'error');
            }
            
            // Update interface status
            await this.loadInterfaceStatus();
            
        } catch (error) {
            console.error('Failed to test interface:', error);
            this.addActivityLog('Interface', `Test error: ${error.message}`, 'error');
            this.showMessage('Failed to test interface', 'error');
        } finally {
            const testBtn = document.getElementById('test-interface-btn');
            if (testBtn) {
                testBtn.disabled = false;
                testBtn.innerHTML = 'Test';
            }
        }
    }

    /**
     * Test agent generation
     */
    async testAgentGeneration() {
        try {
            const promptTextarea = document.getElementById('test-prompt');
            const agentSelect = document.getElementById('agent-type-select');
            const responseDiv = document.getElementById('test-response');
            const generateBtn = document.getElementById('test-generate-btn');
            
            if (!promptTextarea || !agentSelect || !responseDiv) return;
            
            const prompt = promptTextarea.value.trim();
            const agentType = agentSelect.value;
            
            if (!prompt) {
                this.showMessage('Please enter a test prompt', 'warning');
                return;
            }
            
            // Show loading state
            generateBtn.disabled = true;
            generateBtn.innerHTML = '<span class="loading-spinner"></span>Generating...';
            responseDiv.classList.add('loading');
            responseDiv.innerHTML = '';
            
            const response = await fetch('/api/interfaces/generate', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    prompt: prompt,
                    agent_type: agentType,
                    context: {}
                })
            });
            
            const result = await response.json();
            
            if (result.success) {
                responseDiv.textContent = result.response;
                this.addActivityLog('Agent Test', `Generated response using ${result.interface_type}`, 'success');
            } else {
                responseDiv.textContent = `Error: ${result.error}`;
                responseDiv.classList.add('error');
                this.addActivityLog('Agent Test', `Generation failed: ${result.error}`, 'error');
            }
            
        } catch (error) {
            console.error('Failed to generate response:', error);
            const responseDiv = document.getElementById('test-response');
            if (responseDiv) {
                responseDiv.textContent = `Error: ${error.message}`;
                responseDiv.classList.add('error');
            }
            this.addActivityLog('Agent Test', `Generation error: ${error.message}`, 'error');
        } finally {
            const generateBtn = document.getElementById('test-generate-btn');
            const responseDiv = document.getElementById('test-response');
            
            if (generateBtn) {
                generateBtn.disabled = false;
                generateBtn.innerHTML = 'Generate Response';
            }
            
            if (responseDiv) {
                responseDiv.classList.remove('loading');
            }
        }
    }

    /**
     * Clear test response
     */
    clearTestResponse() {
        const responseDiv = document.getElementById('test-response');
        if (responseDiv) {
            responseDiv.innerHTML = '<div class="response-placeholder">Test responses will appear here...</div>';
            responseDiv.classList.remove('error');
        }
    }

    /**
     * Open configuration modal
     */
    async openConfigurationModal() {
        const modal = document.getElementById('interface-config-modal');
        if (!modal) return;
        
        // Load current configurations
        await this.loadConfigurationData();
        
        modal.classList.add('show');
    }

    /**
     * Close configuration modal
     */
    closeConfigurationModal() {
        const modal = document.getElementById('interface-config-modal');
        if (modal) {
            modal.classList.remove('show');
        }
    }

    /**
     * Switch configuration tab
     */
    switchConfigTab(targetTab) {
        // Update tab buttons
        const tabBtns = document.querySelectorAll('.tab-btn');
        tabBtns.forEach(btn => {
            if (btn.getAttribute('data-tab') === targetTab) {
                btn.classList.add('active');
            } else {
                btn.classList.remove('active');
            }
        });
        
        // Update panels
        const panels = document.querySelectorAll('.config-panel');
        panels.forEach(panel => {
            if (panel.id === targetTab) {
                panel.classList.add('active');
            } else {
                panel.classList.remove('active');
            }
        });
    }

    /**
     * Load configuration data into modal
     */
    async loadConfigurationData() {
        const interfaceTypes = ['claude_code', 'anthropic_api', 'mock'];
        
        for (const interfaceType of interfaceTypes) {
            try {
                const response = await fetch(`/api/interfaces/${interfaceType}/config`);
                const config = await response.json();
                
                this.populateConfigurationForm(interfaceType, config);
            } catch (error) {
                console.error(`Failed to load config for ${interfaceType}:`, error);
            }
        }
    }

    /**
     * Populate configuration form with data
     */
    populateConfigurationForm(interfaceType, config) {
        const prefix = interfaceType.replace('_', '-');
        
        // Common fields
        const enabledCheckbox = document.getElementById(`${prefix}-enabled`);
        if (enabledCheckbox) {
            enabledCheckbox.checked = config.enabled || false;
        }
        
        if (interfaceType === 'claude_code') {
            const timeoutInput = document.getElementById('claude-timeout');
            if (timeoutInput) {
                timeoutInput.value = config.timeout || 300;
            }
        } else if (interfaceType === 'anthropic_api') {
            const apiKeyInput = document.getElementById('anthropic-api-key');
            const modelSelect = document.getElementById('anthropic-model');
            const maxTokensInput = document.getElementById('anthropic-max-tokens');
            const temperatureInput = document.getElementById('anthropic-temperature');
            const temperatureValue = document.getElementById('temperature-value');
            
            if (apiKeyInput) {
                apiKeyInput.value = config.api_key || '';
            }
            if (modelSelect) {
                modelSelect.value = config.model || 'claude-3-sonnet-20240229';
            }
            if (maxTokensInput) {
                maxTokensInput.value = config.max_tokens || 4000;
            }
            if (temperatureInput && temperatureValue) {
                temperatureInput.value = config.temperature || 0.7;
                temperatureValue.textContent = config.temperature || 0.7;
            }
        } else if (interfaceType === 'mock') {
            const delayInput = document.getElementById('mock-response-delay');
            const delayValue = document.getElementById('delay-value');
            const failureInput = document.getElementById('mock-failure-rate');
            const failureValue = document.getElementById('failure-value');
            
            const customSettings = config.custom_settings || {};
            
            if (delayInput && delayValue) {
                const delay = customSettings.response_delay || 1.0;
                delayInput.value = delay;
                delayValue.textContent = delay.toFixed(1);
            }
            if (failureInput && failureValue) {
                const failure = customSettings.failure_rate || 0.05;
                failureInput.value = failure;
                failureValue.textContent = failure.toFixed(2);
            }
        }
    }

    /**
     * Save configuration
     */
    async saveConfiguration() {
        try {
            const saveBtn = document.getElementById('save-config-btn');
            if (saveBtn) {
                saveBtn.disabled = true;
                saveBtn.innerHTML = '<span class="loading-spinner"></span>Saving...';
            }
            
            const configs = this.gatherConfigurationData();
            const results = [];
            
            for (const [interfaceType, config] of Object.entries(configs)) {
                try {
                    const response = await fetch(`/api/interfaces/${interfaceType}/config`, {
                        method: 'PUT',
                        headers: {
                            'Content-Type': 'application/json'
                        },
                        body: JSON.stringify(config)
                    });
                    
                    const result = await response.json();
                    results.push({interfaceType, result});
                } catch (error) {
                    results.push({interfaceType, result: {success: false, error: error.message}});
                }
            }
            
            // Check results
            const failures = results.filter(r => !r.result.success);
            if (failures.length === 0) {
                this.showMessage('Configuration saved successfully', 'success');
                this.closeConfigurationModal();
                
                // Reload interface status
                await this.loadInterfaceStatus();
            } else {
                const errorMsg = failures.map(f => `${f.interfaceType}: ${f.result.error}`).join('; ');
                this.showMessage(`Some configurations failed: ${errorMsg}`, 'error');
            }
            
        } catch (error) {
            console.error('Failed to save configuration:', error);
            this.showMessage('Failed to save configuration', 'error');
        } finally {
            const saveBtn = document.getElementById('save-config-btn');
            if (saveBtn) {
                saveBtn.disabled = false;
                saveBtn.innerHTML = 'Save Configuration';
            }
        }
    }

    /**
     * Gather configuration data from forms
     */
    gatherConfigurationData() {
        const configs = {};
        
        // Claude Code configuration
        const claudeEnabled = document.getElementById('claude-enabled')?.checked || false;
        const claudeTimeout = parseInt(document.getElementById('claude-timeout')?.value) || 300;
        
        configs.claude_code = {
            enabled: claudeEnabled,
            timeout: claudeTimeout
        };
        
        // Anthropic API configuration
        const anthropicEnabled = document.getElementById('anthropic-enabled')?.checked || false;
        const anthropicApiKey = document.getElementById('anthropic-api-key')?.value || '';
        const anthropicModel = document.getElementById('anthropic-model')?.value || 'claude-3-sonnet-20240229';
        const anthropicMaxTokens = parseInt(document.getElementById('anthropic-max-tokens')?.value) || 4000;
        const anthropicTemperature = parseFloat(document.getElementById('anthropic-temperature')?.value) || 0.7;
        
        configs.anthropic_api = {
            enabled: anthropicEnabled,
            api_key: anthropicApiKey,
            model: anthropicModel,
            max_tokens: anthropicMaxTokens,
            temperature: anthropicTemperature
        };
        
        // Mock configuration
        const mockEnabled = document.getElementById('mock-enabled')?.checked || false;
        const mockDelay = parseFloat(document.getElementById('mock-response-delay')?.value) || 1.0;
        const mockFailure = parseFloat(document.getElementById('mock-failure-rate')?.value) || 0.05;
        
        configs.mock = {
            enabled: mockEnabled,
            custom_response_delay: mockDelay,
            custom_failure_rate: mockFailure
        };
        
        return configs;
    }

    /**
     * Show message to user
     */
    showMessage(message, type = 'info') {
        // Create message element
        const messageDiv = document.createElement('div');
        messageDiv.className = `${type}-message`;
        messageDiv.textContent = message;
        
        // Add to activity log
        this.addActivityLog('System', message, type);
        
        // Show temporarily in header
        const header = document.querySelector('header');
        if (header) {
            header.appendChild(messageDiv);
            
            setTimeout(() => {
                if (messageDiv.parentNode) {
                    messageDiv.parentNode.removeChild(messageDiv);
                }
            }, 5000);
        }
    }

    /**
     * Handle interface changed event
     */
    handleInterfaceChanged(data) {
        console.log('Interface changed:', data);
        this.activeInterface = data.new_interface;
        this.updateActiveInterfaceDisplay();
        this.addActivityLog('Interface', `Switched from ${data.old_interface} to ${data.new_interface}`, 'info');
    }

    /**
     * Handle interface status event
     */
    handleInterfaceStatus(data) {
        console.log('Interface status update:', data);
        this.interfaceStatus = data.interfaces || {};
        this.activeInterface = data.active_interface;
        this.updateInterfaceStatusDisplay();
        this.updateActiveInterfaceDisplay();
    }

    /**
     * Handle interface error event
     */
    handleInterfaceError(data) {
        console.error('Interface error:', data);
        this.addActivityLog('Interface', `Error: ${data.error}`, 'error');
        this.showMessage(data.error, 'error');
    }

    /**
     * Handle interface switch result
     */
    handleInterfaceSwitchResult(data) {
        console.log('Interface switch result:', data);
        if (data.success) {
            this.showMessage(`Successfully switched to ${data.active_interface}`, 'success');
        } else {
            this.showMessage(`Failed to switch: ${data.error}`, 'error');
        }
    }
}

// Global instances
let visualizer;
let discordChat;
let chatComponents;

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    console.log('Initializing TDD State Visualizer...');
    
    try {
        visualizer = new StateVisualizer();
        
        // Initialize chat system if available
        if (typeof DiscordChat !== 'undefined' && typeof ChatComponents !== 'undefined') {
            chatComponents = new ChatComponents();
            discordChat = new DiscordChat(visualizer.socket, visualizer);
            
            // Integrate chat with visualizer
            integrateChatWithVisualizer();
            
            console.log('Discord chat system initialized');
        } else {
            console.warn('Chat system not available - running in visualizer-only mode');
        }
        
        // Expose to global scope for debugging
        window.visualizer = visualizer;
        window.discordChat = discordChat;
        window.chatComponents = chatComponents;
        
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

/**
 * Integrate chat system with state visualizer
 */
function integrateChatWithVisualizer() {
    if (!visualizer || !discordChat) return;
    
    // Sync state changes from visualizer to chat
    const originalHandleWorkflowTransition = visualizer.handleWorkflowTransition;
    visualizer.handleWorkflowTransition = function(data) {
        originalHandleWorkflowTransition.call(this, data);
        
        // Notify chat of state change
        if (discordChat) {
            const stateChangeMessage = {
                id: 'state_change_' + Date.now(),
                user_id: 'system',
                username: 'State Machine',
                message: `Workflow transitioned: ${data.old_state} → ${data.new_state}`,
                timestamp: new Date().toISOString(),
                type: 'system',
                state_change: {
                    type: 'workflow',
                    old_state: data.old_state,
                    new_state: data.new_state,
                    project: data.project
                }
            };
            
            // Add to chat if chat panel is visible
            const chatPanel = document.querySelector('.right-panel');
            if (chatPanel && !chatPanel.classList.contains('hidden')) {
                discordChat.addMessageToChat(stateChangeMessage);
            }
        }
    };
    
    // Sync TDD transitions
    const originalHandleTDDTransition = visualizer.handleTDDTransition;
    visualizer.handleTDDTransition = function(data) {
        originalHandleTDDTransition.call(this, data);
        
        // Notify chat of TDD state change
        if (discordChat) {
            const tddChangeMessage = {
                id: 'tdd_change_' + Date.now(),
                user_id: 'system',
                username: 'TDD Engine',
                message: `Story ${data.story_id}: ${data.old_state} → ${data.new_state}`,
                timestamp: new Date().toISOString(),
                type: 'system',
                state_change: {
                    type: 'tdd',
                    story_id: data.story_id,
                    old_state: data.old_state,
                    new_state: data.new_state,
                    project: data.project
                }
            };
            
            // Add to chat if chat panel is visible
            const chatPanel = document.querySelector('.right-panel');
            if (chatPanel && !chatPanel.classList.contains('hidden')) {
                discordChat.addMessageToChat(tddChangeMessage);
            }
        }
    };
    
    // Add command execution feedback
    visualizer.addCommandExecutionHandler = function(command, result) {
        if (discordChat && result) {
            // Highlight state elements when commands execute
            if (result.workflow_state) {
                this.highlightWorkflowState(result.workflow_state);
                
                // Flash highlight effect
                const stateElement = document.getElementById('workflow-state');
                if (stateElement) {
                    stateElement.classList.add('command-highlight');
                    setTimeout(() => {
                        stateElement.classList.remove('command-highlight');
                    }, 2000);
                }
            }
            
            if (result.tdd_state) {
                this.highlightTDDState(result.tdd_state);
            }
            
            // Update visualizer after command execution
            setTimeout(() => {
                this.requestStateUpdate();
            }, 500);
        }
    };
    
    // Add panel management
    setupPanelManagement();
    
    // Add keyboard shortcuts
    setupKeyboardShortcuts();
    
    console.log('Chat and visualizer integration complete');
}

/**
 * Setup panel management for responsive layout
 */
function setupPanelManagement() {
    const leftPanel = document.querySelector('.left-panel');
    const rightPanel = document.querySelector('.right-panel');
    const resizeHandle = document.querySelector('.resize-handle');
    
    if (!leftPanel || !rightPanel) return;
    
    // Panel toggle functionality
    window.toggleChatPanel = function() {
        rightPanel.classList.toggle('hidden');
        
        if (rightPanel.classList.contains('hidden')) {
            leftPanel.style.width = '100%';
        } else {
            leftPanel.style.width = '60%';
            rightPanel.style.width = '40%';
        }
    };
    
    window.toggleVisualizerPanel = function() {
        leftPanel.classList.toggle('hidden');
        
        if (leftPanel.classList.contains('hidden')) {
            rightPanel.style.width = '100%';
        } else {
            leftPanel.style.width = '60%';
            rightPanel.style.width = '40%';
        }
    };
    
    // Add toggle buttons to header if they don't exist
    const header = document.querySelector('header .status-bar');
    if (header && !document.getElementById('panel-toggles')) {
        const togglesDiv = document.createElement('div');
        togglesDiv.id = 'panel-toggles';
        togglesDiv.className = 'status-item';
        togglesDiv.innerHTML = `
            <button id="toggle-chat" class="btn btn-small" onclick="toggleChatPanel()" title="Toggle Chat Panel">
                💬
            </button>
            <button id="toggle-visualizer" class="btn btn-small" onclick="toggleVisualizerPanel()" title="Toggle Visualizer Panel">
                📊
            </button>
        `;
        header.appendChild(togglesDiv);
    }
}

/**
 * Setup keyboard shortcuts
 */
function setupKeyboardShortcuts() {
    document.addEventListener('keydown', (event) => {
        // Only handle shortcuts when not typing in inputs
        if (event.target.tagName === 'INPUT' || event.target.tagName === 'TEXTAREA') {
            return;
        }
        
        if (event.ctrlKey || event.metaKey) {
            switch (event.key) {
                case 'l': // Ctrl+L - Focus chat input
                    event.preventDefault();
                    const messageInput = document.getElementById('chat-input-field');
                    if (messageInput) {
                        messageInput.focus();
                    }
                    break;
                    
                case 'k': // Ctrl+K - Toggle chat panel
                    event.preventDefault();
                    if (typeof toggleChatPanel === 'function') {
                        toggleChatPanel();
                    }
                    break;
                    
                case 'm': // Ctrl+M - Toggle visualizer panel
                    event.preventDefault();
                    if (typeof toggleVisualizerPanel === 'function') {
                        toggleVisualizerPanel();
                    }
                    break;
                    
                case '/': // Ctrl+/ - Show help
                    event.preventDefault();
                    showKeyboardShortcuts();
                    break;
            }
        }
    });
}

/**
 * Show keyboard shortcuts help
 */
function showKeyboardShortcuts() {
    const helpMessage = {
        id: 'help_' + Date.now(),
        user_id: 'system',
        username: 'System',
        message: `**Keyboard Shortcuts:**
• \`Ctrl+L\` - Focus chat input
• \`Ctrl+K\` - Toggle chat panel
• \`Ctrl+M\` - Toggle visualizer panel
• \`Ctrl+R\` - Refresh state
• \`Ctrl+/\` - Show this help
• \`↑/↓\` - Navigate command history (in chat)
• \`Tab\` - Accept autocomplete suggestion`,
        timestamp: new Date().toISOString(),
        type: 'system'
    };
    
    if (discordChat) {
        discordChat.addMessageToChat(helpMessage);
    }
}

/**
 * Enhanced state highlighting with command feedback
 */
function addCommandHighlighting() {
    // Add CSS for command highlighting
    const style = document.createElement('style');
    style.textContent = `
        .command-highlight {
            animation: commandPulse 2s ease-in-out;
        }
        
        @keyframes commandPulse {
            0%, 100% { background-color: transparent; }
            50% { background-color: rgba(76, 175, 80, 0.3); }
        }
        
        .state-transition {
            animation: stateTransition 1s ease-in-out;
        }
        
        @keyframes stateTransition {
            0% { transform: scale(1); }
            50% { transform: scale(1.05); }
            100% { transform: scale(1); }
        }
    `;
    document.head.appendChild(style);
}

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
    
    if (discordChat) {
        discordChat.leaveChat();
    }
});

// Initialize command highlighting after DOM load
document.addEventListener('DOMContentLoaded', () => {
    addCommandHighlighting();
});

// Add utility functions for external access
window.VisualizerUtils = {
    /**
     * Send a command to the chat interface
     */
    sendCommand: function(command) {
        if (discordChat) {
            const messageInput = document.getElementById('chat-input-field');
            if (messageInput) {
                messageInput.value = command;
                discordChat.sendMessage();
            }
        }
    },
    
    /**
     * Focus the chat input
     */
    focusChat: function() {
        const messageInput = document.getElementById('chat-input-field');
        if (messageInput) {
            messageInput.focus();
        }
    },
    
    /**
     * Get current state from visualizer
     */
    getCurrentState: function() {
        return visualizer ? {
            workflow_state: visualizer.currentWorkflowState,
            tdd_cycles: Array.from(visualizer.activeTDDCycles.values()),
            connected: visualizer.connected
        } : null;
    },
    
    /**
     * Manually trigger state update
     */
    refreshState: function() {
        if (visualizer) {
            visualizer.requestStateUpdate();
        }
    },
    
    /**
     * Toggle panel visibility
     */
    togglePanels: {
        chat: function() { if (typeof toggleChatPanel === 'function') toggleChatPanel(); },
        visualizer: function() { if (typeof toggleVisualizerPanel === 'function') toggleVisualizerPanel(); }
    }
};

// Initialize chat panel visibility on page load
document.addEventListener('DOMContentLoaded', function() {
    // Show chat panel by default
    const chatPanel = document.getElementById('chat-panel');
    if (chatPanel) {
        console.log('Showing chat panel');
        chatPanel.classList.add('show', 'open');
    } else {
        console.warn('Chat panel element not found');
    }
});