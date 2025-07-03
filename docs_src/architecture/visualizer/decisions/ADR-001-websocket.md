# ADR-001: WebSocket Communication Architecture

## Status
Accepted

## Context
The visualizer needs real-time communication between the web interface and the backend orchestrator to provide immediate feedback on workflow state changes, command execution, and multi-project coordination.

## Decision
We will use Socket.IO for WebSocket communication with project-specific rooms for isolation.

## Rationale

### Technology Choice: Socket.IO over native WebSockets
- **Fallback Support**: Automatic fallback to polling for older browsers
- **Room Management**: Built-in support for project-specific communication channels
- **Reconnection**: Automatic reconnection handling with exponential backoff
- **Event-based**: Clean event-driven architecture matches our use case

### Room-based Project Isolation
```python
# Each project gets a dedicated room
room_name = f"project_{project_id}"
join_room(room_name)
emit('state_update', data, room=room_name)
```

**Benefits**:
- **Security**: Projects cannot see each other's data
- **Scalability**: Independent scaling per project
- **Performance**: Targeted updates only to interested clients

### Event Types
- `join_project`: Client joins project room
- `leave_project`: Client leaves project room  
- `command`: Execute orchestrator command
- `state_update`: Broadcast state changes
- `chat_message`: Send/receive chat messages

## Consequences

### Positive
- **Real-time Updates**: Immediate state synchronization
- **Project Isolation**: Secure multi-tenant architecture
- **Reliable Communication**: Built-in error handling and reconnection
- **Scalable**: Room-based architecture supports growth

### Negative
- **Complexity**: Additional layer compared to simple HTTP polling
- **Resource Usage**: Persistent connections consume server resources
- **Debugging**: WebSocket debugging more complex than HTTP

## Implementation Details

### Server Side (Flask-SocketIO)
```python
@socketio.on('join_project')
def handle_join_project(data):
    project_id = data['project_id']
    room = f"project_{project_id}"
    join_room(room)
    emit('joined', {'room': room})

@socketio.on('command')
def handle_command(data):
    project_id = session.get('project_id')
    result = orchestrator.execute_command(data['command'])
    emit('command_response', result, room=f"project_{project_id}")
```

### Client Side (JavaScript)
```javascript
const socket = io();

socket.on('connect', () => {
    socket.emit('join_project', {project_id: currentProjectId});
});

socket.on('state_update', (data) => {
    updateStateDiagram(data.state);
});
```

## Alternatives Considered

### 1. HTTP Polling
- **Pros**: Simpler, better caching, easier debugging
- **Cons**: Higher latency, more server load, poor user experience

### 2. Server-Sent Events (SSE)
- **Pros**: Simpler than WebSockets, good browser support
- **Cons**: One-way communication, requires separate endpoint for commands

### 3. Native WebSockets
- **Pros**: Lower overhead, direct browser support
- **Cons**: No fallback, manual reconnection logic, no room management

## Monitoring and Metrics

### Key Metrics
- Connection count per project
- Message throughput
- Reconnection frequency
- Average response time

### Alerting
- Connection failures > 5%
- Message queue backlog > 1000
- Average response time > 2 seconds

## Future Considerations

### Scaling
- **Redis Adapter**: For multi-instance deployments
- **Message Queue**: For high-throughput scenarios
- **Connection Pooling**: For resource optimization

### Security Enhancements
- **Authentication**: Project-based access tokens
- **Rate Limiting**: Per-connection message limits
- **Input Validation**: Strict message schema validation