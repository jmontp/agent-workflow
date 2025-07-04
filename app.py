#!/usr/bin/env python3
"""
Agent workflow state machine with meaningful execution stages.
Tracks the actual flow of agent task execution.
"""

from flask import Flask, render_template, jsonify, request
from flask_socketio import SocketIO, emit
from enum import Enum
from dataclasses import dataclass
from typing import Optional, Dict, Any, List
from datetime import datetime
from context_manager import ContextManager, Context, ContextType

app = Flask(__name__)
app.config['SECRET_KEY'] = 'demo-secret-key'
socketio = SocketIO(app, cors_allowed_origins="*")

# Agent Execution States
class WorkflowState(Enum):
    IDLE = "IDLE"                           # No active request
    REQUEST_RECEIVED = "REQUEST_RECEIVED"   # User submitted request
    CONTEXT_SEARCH = "CONTEXT_SEARCH"       # Searching for relevant patterns
    EXECUTING = "EXECUTING"                 # Agent performing task
    CONTEXT_UPDATE = "CONTEXT_UPDATE"       # Storing results and learnings
    HUMAN_REVIEW = "HUMAN_REVIEW"           # Awaiting human feedback

# Execution Status (simplified TDD tracking)
class ExecutionStatus(Enum):
    PLANNING = "PLANNING"       # Designing approach
    IMPLEMENTING = "IMPLEMENTING" # Writing code/docs
    VALIDATING = "VALIDATING"   # Running tests/checks
    COMPLETE = "COMPLETE"       # Task finished

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
        WorkflowState.IDLE: [WorkflowState.REQUEST_RECEIVED],
        WorkflowState.REQUEST_RECEIVED: [WorkflowState.CONTEXT_SEARCH, WorkflowState.IDLE],
        WorkflowState.CONTEXT_SEARCH: [WorkflowState.EXECUTING, WorkflowState.IDLE],
        WorkflowState.EXECUTING: [WorkflowState.CONTEXT_UPDATE, WorkflowState.IDLE],
        WorkflowState.CONTEXT_UPDATE: [WorkflowState.HUMAN_REVIEW],
        WorkflowState.HUMAN_REVIEW: [WorkflowState.IDLE, WorkflowState.REQUEST_RECEIVED]
    }
)

execution_sm = StateMachine(
    current_state=ExecutionStatus.PLANNING,
    transitions={
        ExecutionStatus.PLANNING: [ExecutionStatus.IMPLEMENTING],
        ExecutionStatus.IMPLEMENTING: [ExecutionStatus.VALIDATING],
        ExecutionStatus.VALIDATING: [ExecutionStatus.COMPLETE, ExecutionStatus.IMPLEMENTING],
        ExecutionStatus.COMPLETE: [ExecutionStatus.PLANNING]
    }
)

# Command mapping
COMMANDS = {
    # Workflow commands
    '/request': WorkflowState.REQUEST_RECEIVED,
    '/search': WorkflowState.CONTEXT_SEARCH,
    '/execute': WorkflowState.EXECUTING,
    '/update': WorkflowState.CONTEXT_UPDATE,
    '/review': WorkflowState.HUMAN_REVIEW,
    '/idle': WorkflowState.IDLE,
    # Execution status commands
    '/plan': ExecutionStatus.PLANNING,
    '/implement': ExecutionStatus.IMPLEMENTING,
    '/validate': ExecutionStatus.VALIDATING,
    '/complete': ExecutionStatus.COMPLETE
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
        'execution': {
            'current': execution_sm.current_state.value,
            'diagram': execution_sm.get_diagram(),
            'history': execution_sm.history[-5:]
        }
    })

@socketio.on('connect')
def handle_connect():
    """Handle client connection."""
    emit('state_update', {
        'workflow': workflow_sm.current_state.value,
        'execution': execution_sm.current_state.value
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
        success = execution_sm.transition(target_state)
        machine = 'execution'
    
    if success:
        # Broadcast state change to all clients
        socketio.emit('state_change', {
            'machine': machine,
            'new_state': target_state.value,
            'diagram': workflow_sm.get_diagram() if machine == 'workflow' else execution_sm.get_diagram()
        })
    else:
        current = workflow_sm.current_state.value if machine == 'workflow' else execution_sm.current_state.value
        emit('error', {
            'message': f'Cannot transition from {current} to {target_state.value}'
        })

# Initialize Context Manager
cm = ContextManager()

# Context Manager API endpoints
@app.route('/api/context', methods=['POST'])
def add_context():
    """Add a new context."""
    try:
        data = request.json
        context = Context(
            id=data.get('id', str(datetime.now().timestamp())),
            type=ContextType(data['type']),
            source=data.get('source', 'api'),
            timestamp=datetime.now(),
            data=data.get('data', {}),
            metadata=data.get('metadata', {}),
            tags=data.get('tags', [])
        )
        context_id = cm.add_context(context)
        return jsonify({"success": True, "context_id": context_id})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 400

@app.route('/api/context/<context_id>')
def get_context(context_id):
    """Get a specific context."""
    context = cm.get_context(context_id)
    if context:
        return jsonify(context.to_dict())
    return jsonify({"error": "Context not found"}), 404

@app.route('/api/context/query')
def query_contexts():
    """Query contexts with filters."""
    # Get query parameters
    query = request.args.get('q')
    context_type = request.args.get('type')
    limit = int(request.args.get('limit', 10))
    
    kwargs = {}
    if query:
        kwargs['query'] = query
    if context_type:
        try:
            kwargs['context_type'] = ContextType(context_type)
        except ValueError:
            return jsonify({"error": f"Invalid type: {context_type}"}), 400
    kwargs['limit'] = limit
    
    results = cm.query_contexts(**kwargs)
    return jsonify([c.to_dict() for c in results])

@app.route('/api/context/decision', methods=['POST'])
def log_decision():
    """Log a development decision."""
    data = request.json
    context_id = cm.log_decision(
        data['decision'],
        data['reasoning']
    )
    
    # Also trigger state transition if applicable
    if workflow_sm.current_state == WorkflowState.REQUEST_RECEIVED:
        workflow_sm.transition(WorkflowState.CONTEXT_SEARCH)
        socketio.emit('state_change', {
            'machine': 'workflow',
            'new_state': WorkflowState.CONTEXT_SEARCH.value
        })
    
    return jsonify({
        "context_id": context_id,
        "suggestions": cm.suggest_next_task()
    })

@app.route('/api/context/suggest')
def get_suggestions():
    """Get task suggestions."""
    return jsonify({"suggestions": cm.suggest_next_task()})

@app.route('/api/context/stats')
def get_stats():
    """Get Context Manager statistics."""
    return jsonify(cm.get_stats())

@app.route('/api/context/patterns')
def get_patterns():
    """Get detected patterns."""
    min_occurrences = int(request.args.get('min', 3))
    return jsonify(cm.get_patterns(min_occurrences))

if __name__ == '__main__':
    print("Starting agent workflow state machine...")
    print("Tracking execution stages: Request → Context Search → Execute → Update → Review")
    print("Context Manager API available at /api/context")
    print("Open http://localhost:5000 in your browser")
    socketio.run(app, debug=True, host='0.0.0.0', port=5000, allow_unsafe_werkzeug=True)