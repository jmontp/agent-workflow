# Discord-Style Chat Interface Foundation

## Overview

This document describes the foundational backend implementation for the Discord-style chat interface in the AI Agent TDD-Scrum Workflow visualizer. The foundation provides the core Flask routes, WebSocket handlers, and command processing infrastructure that enables real-time chat communication with the orchestrator system.

## Architecture

### Components Created

1. **Flask API Endpoints** (`app.py` extensions)
   - `/api/chat/send` (POST) - Process incoming chat messages and commands
   - `/api/chat/history` (GET) - Retrieve chat message history
   - `/api/chat/autocomplete` (GET) - Provide command autocomplete suggestions

2. **WebSocket Event Handlers** (`app.py` extensions)
   - `chat_command` - Handle incoming commands from clients
   - `command_response` - Send bot responses to clients
   - `typing_indicator` - Real-time typing indicators
   - `request_chat_history` - Request message history
   - `start_typing`/`stop_typing` - User typing events
   - `join_chat`/`leave_chat` - User presence management

3. **Command Processor** (`command_processor.py`)
   - Standalone command parsing and processing engine
   - Integration with orchestrator system
   - Comprehensive command support with pattern matching
   - Graceful fallback when orchestrator is unavailable

### Design Principles

- **Separation of Concerns**: Chat functionality is modular and doesn't interfere with existing visualizer features
- **Real-time Communication**: WebSocket-based for instant message delivery and typing indicators
- **Graceful Degradation**: Works with mock responses when orchestrator is unavailable
- **Security**: Input validation and error handling for all user inputs
- **Scalability**: Message history management with automatic pruning

## API Endpoints

### POST `/api/chat/send`

Processes incoming chat messages and commands.

**Request Body:**
```json
{
  "message": "/epic \"Create user authentication\"",
  "user_id": "user123",
  "username": "Developer"
}
```

**Response:**
```json
{
  "success": true,
  "message_id": "uuid-here"
}
```

**Features:**
- Validates message format
- Stores messages in chat history
- Automatically detects and processes commands (starting with `/`)
- Shows typing indicators for bot responses
- Broadcasts messages to all connected clients

### GET `/api/chat/history`

Retrieves chat message history with optional limit.

**Parameters:**
- `limit` (optional): Number of messages to retrieve (max 100, default 50)

**Response:**
```json
{
  "messages": [
    {
      "id": "uuid",
      "user_id": "user123",
      "username": "Developer",
      "message": "/sprint status",
      "timestamp": "2024-01-01T12:00:00Z",
      "type": "user"
    },
    {
      "id": "uuid",
      "user_id": "bot",
      "username": "Agent Bot",
      "message": "📊 Sprint Status...",
      "timestamp": "2024-01-01T12:00:01Z",
      "type": "bot",
      "command_result": {...}
    }
  ],
  "total_count": 15
}
```

### GET `/api/chat/autocomplete`

Provides command autocomplete suggestions.

**Parameters:**
- `query` (optional): Partial command to match against

**Response:**
```json
{
  "suggestions": [
    {
      "command": "/sprint plan",
      "description": "Plan a new sprint"
    },
    {
      "command": "/sprint start", 
      "description": "Start the current sprint"
    }
  ]
}
```

## WebSocket Events

### Client → Server Events

- `chat_command` - Send a command message
- `request_chat_history` - Request message history
- `start_typing` - User starts typing
- `stop_typing` - User stops typing
- `join_chat` - User joins chat
- `leave_chat` - User leaves chat

### Server → Client Events

- `new_chat_message` - New message from any user
- `command_response` - Bot response to a command
- `typing_indicator` - Typing status updates
- `chat_history` - Message history response
- `user_joined` - User joined notification
- `user_left` - User left notification
- `active_users` - List of active users
- `command_error` - Command processing error
- `chat_error` - General chat error

## Command Processor

### Supported Commands

The command processor supports all Discord bot commands:

- `/epic "description"` - Define high-level initiatives
- `/approve [item_ids]` - Approve stories or tasks
- `/sprint <action> [params]` - Sprint lifecycle management
- `/backlog <action> [params]` - Backlog management
- `/state` - Show current workflow state
- `/project register <path>` - Register new projects
- `/request_changes "description"` - Request PR changes
- `/help [command]` - Show help information

### Command Processing Flow

1. **Pattern Matching**: Uses regex patterns to parse commands and extract parameters
2. **Orchestrator Integration**: Calls orchestrator.handle_command() for actual processing
3. **Response Formatting**: Converts orchestrator responses to user-friendly chat messages
4. **Error Handling**: Provides helpful error messages and suggestions
5. **Mock Responses**: Falls back to simulated responses when orchestrator is unavailable

### Message Types

- `user` - Messages from users
- `bot` - Responses from the Agent Bot
- `system` - System notifications (join/leave)
- `typing` - Typing indicator placeholders

## Data Management

### Chat History

- **Storage**: In-memory array (chat_history)
- **Limit**: Automatically prunes to last 100 messages
- **Format**: Structured JSON objects with metadata
- **Persistence**: Currently ephemeral (resets on server restart)

### User Presence

- **Active Users**: Set of currently connected user IDs
- **Typing Users**: Set of users currently typing
- **Session Management**: Cleaned up on disconnect

## Integration Points

### Existing System Compatibility

The chat foundation integrates cleanly with the existing visualizer:

- **No Breaking Changes**: All existing endpoints and functionality preserved
- **Shared State**: Can access existing state broadcaster and interface manager
- **Common Dependencies**: Uses same Flask app, SocketIO instance, and logging
- **Color Scheme**: Ready to use existing CSS variables from color-schemes.css

### Orchestrator Integration

```python
# Command processing with orchestrator
result = self.orchestrator.handle_command("/epic", "default", description=description)
```

The command processor directly calls orchestrator methods, ensuring consistency with Discord bot behavior.

## Error Handling

### Graceful Fallbacks

- **Import Errors**: Falls back to mock responses if orchestrator unavailable
- **Command Errors**: Returns helpful error messages with suggestions
- **Validation Errors**: Client-side and server-side input validation
- **WebSocket Errors**: Proper error event emission

### Logging

Comprehensive logging for debugging and monitoring:

```python
logger.info(f"Processing command: {command} from user: {user_id}")
logger.error(f"Error processing command: {e}")
```

## Next Steps for Other Agents

This foundation enables other agents to work in parallel:

### Frontend Agent (Agent 2)
- Can use the existing WebSocket events
- Message rendering components
- Chat UI components with Discord-style design
- Integration with existing visualizer interface

### JavaScript Agent (Agent 3)
- Real-time WebSocket client implementation
- Typing indicator management
- Autocomplete functionality
- Message history management

### Documentation Agent (Agent 4)
- User guides for chat interface
- Command reference documentation
- Integration examples
- API documentation

## Testing

### Manual Testing

The command processor includes a test script:

```bash
cd tools/visualizer
python3 command_processor.py
```

### API Testing

Basic endpoint testing can be performed with curl:

```bash
# Test autocomplete
curl "http://localhost:5000/api/chat/autocomplete?query=sprint"

# Test chat history
curl "http://localhost:5000/api/chat/history"

# Test send message
curl -X POST "http://localhost:5000/api/chat/send" \
  -H "Content-Type: application/json" \
  -d '{"message": "/help", "user_id": "test", "username": "Test User"}'
```

## Configuration

### Environment Variables

No additional environment variables required - uses existing visualizer configuration.

### Dependencies

Uses existing visualizer dependencies:
- Flask
- Flask-SocketIO
- Standard Python libraries (re, json, logging, threading)

## Security Considerations

- **Input Validation**: All user inputs validated and sanitized
- **Command Injection**: No direct system command execution
- **Rate Limiting**: Could be added for production use
- **Authentication**: Currently anonymous - can be extended with user auth

## Performance

- **Memory Management**: Automatic message history pruning
- **Async Processing**: Commands processed in background threads
- **WebSocket Efficiency**: Event-based communication
- **Response Time**: Real-time typing indicators and instant messaging

This foundation provides a robust, scalable base for the Discord-style chat interface while maintaining compatibility with the existing system and following established patterns.