// Agent workflow state machine client
const socket = io();

// Initialize Mermaid
mermaid.initialize({ 
    startOnLoad: true,
    theme: 'dark',
    themeVariables: {
        primaryColor: '#0066ff',
        primaryTextColor: '#fff',
        primaryBorderColor: '#0052cc',
        lineColor: '#5e6c84',
        secondaryColor: '#172b4d',
        tertiaryColor: '#fff'
    }
});

// DOM elements
const workflowState = document.getElementById('workflow-state');
const executionState = document.getElementById('execution-state');
const workflowDiagram = document.querySelector('#workflow-diagram .mermaid');
const executionDiagram = document.querySelector('#execution-diagram .mermaid');
const commandInput = document.getElementById('command-input');
const sendBtn = document.getElementById('send-btn');
const errorMessage = document.getElementById('error-message');
const historyLog = document.getElementById('history-log');

// Load initial state
async function loadInitialState() {
    try {
        const response = await fetch('/api/state');
        const data = await response.json();
        
        updateDiagram('workflow', data.workflow.diagram);
        updateDiagram('execution', data.execution.diagram);
        updateStateDisplay(workflowState, data.workflow.current);
        updateStateDisplay(executionState, data.execution.current);
    } catch (error) {
        console.error('Failed to load initial state:', error);
    }
}

// Update diagram
function updateDiagram(type, diagramCode) {
    const element = type === 'workflow' ? workflowDiagram : executionDiagram;
    element.textContent = diagramCode;
    element.removeAttribute('data-processed');
    mermaid.run();
}

// Update state display
function updateStateDisplay(element, state) {
    element.textContent = state;
    element.className = 'current-state state-' + state.toLowerCase().replace('_', '-');
}

// Send command
function sendCommand() {
    const command = commandInput.value.trim();
    if (!command) return;
    
    socket.emit('command', { command });
    commandInput.value = '';
    errorMessage.textContent = '';
}

// Socket event handlers
socket.on('connect', () => {
    console.log('Connected to server');
    loadInitialState();
});

socket.on('state_update', (data) => {
    updateStateDisplay(workflowState, data.workflow);
    updateStateDisplay(executionState, data.execution);
});

socket.on('state_change', (data) => {
    if (data.machine === 'workflow') {
        updateStateDisplay(workflowState, data.new_state);
        updateDiagram('workflow', data.diagram);
    } else {
        updateStateDisplay(executionState, data.new_state);
        updateDiagram('execution', data.diagram);
    }
    
    // Add to history
    addToHistory(`${data.machine}: → ${data.new_state}`);
});

socket.on('error', (data) => {
    errorMessage.textContent = data.message;
    setTimeout(() => {
        errorMessage.textContent = '';
    }, 5000);
});

// Add to history log
function addToHistory(message) {
    const entry = document.createElement('div');
    entry.className = 'history-entry';
    entry.textContent = `${new Date().toLocaleTimeString()} - ${message}`;
    historyLog.insertBefore(entry, historyLog.firstChild);
    
    // Keep only last 10 entries
    while (historyLog.children.length > 10) {
        historyLog.removeChild(historyLog.lastChild);
    }
}

// Event listeners
sendBtn.addEventListener('click', sendCommand);
commandInput.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') sendCommand();
});

// Initialize on load
window.addEventListener('DOMContentLoaded', loadInitialState);