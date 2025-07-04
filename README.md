# Ultra-Minimal State Machine Demo

A stripped-down demonstration of state machine concepts using Flask and WebSockets in just 4 files.

## What is this?

This is a minimal implementation showing:
- Two finite state machines (Workflow and TDD)
- Real-time state visualization with Mermaid diagrams
- WebSocket communication for live updates
- Simple command interface

## Files

```
.
├── app.py                 # Flask server with state machines (~150 lines)
├── templates/
│   └── index.html        # Web interface
├── static/
│   ├── app.js           # Client-side logic
│   └── style.css        # Minimal dark theme
```

## Quick Start

```bash
# Install dependencies
pip install flask flask-socketio

# Run the demo
python app.py

# Open browser to http://localhost:5000
```

## Commands

### Workflow State Machine
- `/idle` - Return to idle state
- `/backlog` - Move to backlog ready
- `/sprint` - Start sprint

### TDD State Machine
- `/design` - Design phase
- `/test-red` - Write failing tests
- `/test-green` - Make tests pass
- `/refactor` - Improve code

## State Machines

### Workflow States
```
IDLE → BACKLOG_READY → SPRINT_ACTIVE → IDLE
```

### TDD Cycle
```
DESIGN → TEST_RED → TEST_GREEN → REFACTOR → DESIGN
```

## Features Demonstrated

1. **State Management**: Enum-based states with allowed transitions
2. **Real-time Updates**: WebSocket broadcasting to all connected clients
3. **Visual Feedback**: Live Mermaid diagrams showing current state
4. **Command Processing**: Simple slash-command interface
5. **Error Handling**: Invalid transition prevention

## Why This Exists

This demo strips away all complexity to show the core concepts of:
- Finite state machines
- State transition validation
- Real-time visualization
- Multi-client synchronization

## Full System

For the complete agent-workflow system with all features, see the `v1.0.0-complete-system` tag:

```bash
git checkout v1.0.0-complete-system
```

## License

MIT