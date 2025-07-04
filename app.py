#!/usr/bin/env python3
"""
Ultra-minimal state machine demo with web interface.
Demonstrates core concepts with ~150 lines of code.
"""

from flask import Flask, render_template, jsonify, request
from flask_socketio import SocketIO, emit
from enum import Enum
from dataclasses import dataclass
from typing import Optional, Dict, Any
from datetime import datetime

app = Flask(__name__)
app.config['SECRET_KEY'] = 'demo-secret-key'
socketio = SocketIO(app, cors_allowed_origins="*")

# Main Workflow States
class WorkflowState(Enum):
    IDLE = "IDLE"
    BACKLOG_READY = "BACKLOG_READY"
    SPRINT_ACTIVE = "SPRINT_ACTIVE"

# TDD States
class TDDState(Enum):
    DESIGN = "DESIGN"
    TEST_RED = "TEST_RED"
    TEST_GREEN = "TEST_GREEN"
    REFACTOR = "REFACTOR"

@dataclass
class StateMachine:
    """Simple state machine with allowed transitions."""
    current_state: Enum
    transitions: Dict[Enum, list]
    history: list = None
    
    def __post_init__(self):
        if self.history is None:
            self.history = []
    
    def can_transition(self, new_state: Enum) -> bool:
        """Check if transition is allowed."""
        return new_state in self.transitions.get(self.current_state, [])
    
    def transition(self, new_state: Enum) -> bool:
        """Perform state transition if allowed."""
        if self.can_transition(new_state):
            old_state = self.current_state
            self.current_state = new_state
            self.history.append({
                'from': old_state.value,
                'to': new_state.value,
                'timestamp': datetime.now().isoformat()
            })
            return True
        return False
    
    def get_diagram(self) -> str:
        """Generate Mermaid diagram."""
        lines = ["stateDiagram-v2"]
        for state, targets in self.transitions.items():
            for target in targets:
                lines.append(f"    {state.value} --> {target.value}")
        lines.append(f"    {self.current_state.value}:::current")
        lines.append("    classDef current fill:#0066ff,stroke:#fff,stroke-width:2px")
        return "\n".join(lines)

# Initialize state machines
workflow_sm = StateMachine(
    current_state=WorkflowState.IDLE,
    transitions={
        WorkflowState.IDLE: [WorkflowState.BACKLOG_READY],
        WorkflowState.BACKLOG_READY: [WorkflowState.SPRINT_ACTIVE, WorkflowState.IDLE],
        WorkflowState.SPRINT_ACTIVE: [WorkflowState.IDLE]
    }
)

tdd_sm = StateMachine(
    current_state=TDDState.DESIGN,
    transitions={
        TDDState.DESIGN: [TDDState.TEST_RED],
        TDDState.TEST_RED: [TDDState.TEST_GREEN],
        TDDState.TEST_GREEN: [TDDState.REFACTOR],
        TDDState.REFACTOR: [TDDState.DESIGN]
    }
)

# Command mapping
COMMANDS = {
    '/backlog': WorkflowState.BACKLOG_READY,
    '/sprint': WorkflowState.SPRINT_ACTIVE,
    '/idle': WorkflowState.IDLE,
    '/design': TDDState.DESIGN,
    '/test-red': TDDState.TEST_RED,
    '/test-green': TDDState.TEST_GREEN,
    '/refactor': TDDState.REFACTOR
}

@app.route('/')
def index():
    """Serve main interface."""
    return render_template('index.html')

@app.route('/api/state')
def get_state():
    """Get current state of both machines."""
    return jsonify({
        'workflow': {
            'current': workflow_sm.current_state.value,
            'diagram': workflow_sm.get_diagram(),
            'history': workflow_sm.history[-5:]  # Last 5 transitions
        },
        'tdd': {
            'current': tdd_sm.current_state.value,
            'diagram': tdd_sm.get_diagram(),
            'history': tdd_sm.history[-5:]
        }
    })

@socketio.on('connect')
def handle_connect():
    """Handle client connection."""
    emit('state_update', {
        'workflow': workflow_sm.current_state.value,
        'tdd': tdd_sm.current_state.value
    })

@socketio.on('command')
def handle_command(data):
    """Process commands from client."""
    command = data.get('command', '').lower()
    
    if command not in COMMANDS:
        emit('error', {'message': f'Unknown command: {command}'})
        return
    
    target_state = COMMANDS[command]
    
    # Determine which state machine to use
    if isinstance(target_state, WorkflowState):
        success = workflow_sm.transition(target_state)
        machine = 'workflow'
    else:
        success = tdd_sm.transition(target_state)
        machine = 'tdd'
    
    if success:
        # Broadcast state change to all clients
        socketio.emit('state_change', {
            'machine': machine,
            'new_state': target_state.value,
            'diagram': workflow_sm.get_diagram() if machine == 'workflow' else tdd_sm.get_diagram()
        })
    else:
        current = workflow_sm.current_state.value if machine == 'workflow' else tdd_sm.current_state.value
        emit('error', {
            'message': f'Cannot transition from {current} to {target_state.value}'
        })

if __name__ == '__main__':
    print("Starting ultra-minimal state machine demo...")
    print("Open http://localhost:5000 in your browser")
    socketio.run(app, debug=True, host='0.0.0.0', port=5000)