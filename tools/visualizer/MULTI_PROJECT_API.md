# Multi-Project Backend API Integration

This document describes the multi-project backend infrastructure implemented for the Discord web visualizer.

## Overview

The multi-project backend API enables the web visualizer to support multiple orchestration projects simultaneously with:

- **Project Discovery & Management**: Automatic detection and registration of projects
- **Project-Specific State**: Independent state management per project
- **WebSocket Room Management**: Project-specific real-time communication
- **Session Management**: User session tracking across projects
- **Configuration Integration**: Seamless integration with existing config systems

## API Endpoints

### Project Management

#### `GET /api/projects`
List all registered projects with their status and state information.

**Response:**
```json
{
  "multi_project_enabled": true,
  "projects": [
    {
      "name": "project-name",
      "path": "/path/to/project",
      "status": "active",
      "priority": "normal",
      "description": "Project description",
      "git_url": "https://github.com/user/repo.git",
      "owner": "user@example.com",
      "team": ["user1", "user2"],
      "discord_channel": "project-channel",
      "tags": ["web", "api"],
      "created_at": "2024-01-01T00:00:00",
      "last_activity": "2024-01-01T12:00:00",
      "resource_limits": {
        "max_parallel_agents": 3,
        "max_parallel_cycles": 2,
        "max_memory_mb": 1024,
        "max_disk_mb": 2048,
        "cpu_priority": 1.0
      },
      "ai_settings": {
        "auto_approve_low_risk": true,
        "max_auto_retry": 3,
        "require_human_review": false,
        "context_sharing_enabled": true
      },
      "work_hours": {
        "timezone": "UTC",
        "start": "09:00",
        "end": "17:00",
        "days": ["monday", "tuesday", "wednesday", "thursday", "friday"]
      },
      "dependencies": [
        {
          "target_project": "dependency-project",
          "dependency_type": "blocks",
          "description": "Dependency description",
          "criticality": "high"
        }
      ],
      "state": {
        "workflow_state": "SPRINT_ACTIVE",
        "tdd_cycles": {},
        "last_updated": "2024-01-01T12:00:00",
        "transition_history": [],
        "initialized": true,
        "project_name": "project-name"
      }
    }
  ],
  "total_count": 1,
  "active_count": 1
}
```

#### `POST /api/projects/<project_name>/switch`
Switch active project context for a user session.

**Request:**
```json
{
  "session_id": "user-session-id"
}
```

**Response:**
```json
{
  "success": true,
  "old_project": "previous-project",
  "new_project": "new-project",
  "session_id": "user-session-id",
  "project_state": {
    "workflow_state": "IDLE",
    "tdd_cycles": {},
    "last_updated": "2024-01-01T12:00:00",
    "transition_history": [],
    "initialized": true
  }
}
```

#### `GET /api/projects/<project_name>/state`
Get project-specific workflow state.

**Response:**
```json
{
  "project_name": "project-name",
  "state": {
    "workflow_state": "SPRINT_ACTIVE",
    "tdd_cycles": {
      "story-1": {
        "state": "WRITE_TEST",
        "last_updated": "2024-01-01T12:00:00"
      }
    },
    "last_updated": "2024-01-01T12:00:00",
    "transition_history": [
      {
        "from_state": "IDLE",
        "to_state": "SPRINT_ACTIVE",
        "timestamp": "2024-01-01T10:00:00"
      }
    ],
    "initialized": true
  },
  "last_updated": "2024-01-01T12:00:00"
}
```

#### `GET /api/projects/<project_name>/config`
Get project configuration details.

**Response:**
```json
{
  "name": "project-name",
  "path": "/path/to/project",
  "status": "active",
  "priority": "normal",
  "description": "Project description",
  "git_url": "https://github.com/user/repo.git",
  "owner": "user@example.com",
  "team": ["user1", "user2"],
  "discord_channel": "project-channel",
  "tags": ["web", "api"],
  "work_hours": {
    "timezone": "UTC",
    "start": "09:00",
    "end": "17:00",
    "days": ["monday", "tuesday", "wednesday", "thursday", "friday"]
  },
  "ai_settings": {
    "auto_approve_low_risk": true,
    "max_auto_retry": 3,
    "require_human_review": false,
    "context_sharing_enabled": true
  },
  "resource_limits": {
    "max_parallel_agents": 3,
    "max_parallel_cycles": 2,
    "max_memory_mb": 1024,
    "max_disk_mb": 2048,
    "cpu_priority": 1.0
  },
  "dependencies": [],
  "created_at": "2024-01-01T00:00:00",
  "last_activity": "2024-01-01T12:00:00",
  "version": "1.0"
}
```

### Project Discovery & Registration

#### `POST /api/projects/discover`
Discover potential projects in specified directories.

**Request:**
```json
{
  "search_paths": ["/path/to/search1", "/path/to/search2"]
}
```

**Response:**
```json
{
  "discovered_projects": [
    {
      "name": "discovered-project",
      "path": "/path/to/discovered-project",
      "type": "git",
      "git_url": "https://github.com/user/repo.git",
      "language": "python"
    }
  ],
  "total_count": 1
}
```

#### `POST /api/projects/register`
Register a new project in the system.

**Request:**
```json
{
  "name": "new-project",
  "path": "/path/to/project",
  "description": "New project description",
  "git_url": "https://github.com/user/repo.git",
  "owner": "user@example.com",
  "team": ["user1", "user2"],
  "priority": "normal",
  "status": "active",
  "resource_limits": {
    "max_parallel_agents": 3,
    "max_parallel_cycles": 2,
    "max_memory_mb": 1024,
    "max_disk_mb": 2048,
    "cpu_priority": 1.0
  },
  "ai_settings": {
    "auto_approve_low_risk": true,
    "max_auto_retry": 3,
    "require_human_review": false
  }
}
```

**Response:**
```json
{
  "success": true,
  "message": "Project 'new-project' registered successfully",
  "project": {
    "name": "new-project",
    "path": "/path/to/project",
    "status": "active",
    "priority": "normal",
    "created_at": "2024-01-01T12:00:00"
  }
}
```

## WebSocket Events

### Project Room Management

#### `join_project`
Join a project-specific room for real-time updates.

**Emit:**
```javascript
socket.emit('join_project', {
  project_name: 'project-name',
  session_id: 'user-session-id'
});
```

**Response:**
```javascript
socket.on('project_joined', (data) => {
  // data contains project_name, session_id, timestamp, project_state, room_members
});
```

#### `leave_project`
Leave a project room.

**Emit:**
```javascript
socket.emit('leave_project', {
  project_name: 'project-name',
  session_id: 'user-session-id'
});
```

#### `switch_project`
Switch to a different project via WebSocket.

**Emit:**
```javascript
socket.emit('switch_project', {
  project_name: 'new-project',
  session_id: 'user-session-id'
});
```

**Response:**
```javascript
socket.on('project_switched', (data) => {
  // data contains old_project, new_project, session_id, timestamp, project_state
});
```

#### `request_project_list`
Request list of available projects.

**Emit:**
```javascript
socket.emit('request_project_list');
```

**Response:**
```javascript
socket.on('project_list', (data) => {
  // data contains enabled, projects array, total_count, active_count
});
```

#### `broadcast_to_project`
Send a message to all members of a project room.

**Emit:**
```javascript
socket.emit('broadcast_to_project', {
  project_name: 'project-name',
  message: 'Hello project team!',
  type: 'announcement',
  session_id: 'user-session-id'
});
```

### Event Notifications

#### `project_switched`
Emitted when a user switches projects.

#### `project_member_joined`
Emitted when a new member joins a project room.

#### `project_member_left`
Emitted when a member leaves a project room.

#### `project_registered`
Emitted when a new project is registered.

#### `project_broadcast`
Emitted when a message is broadcast to a project room.

#### `project_error`
Emitted when a project-related error occurs.

#### `multi_project_status`
Emitted on connection with multi-project availability status.

## Error Handling

All endpoints implement comprehensive error handling:

### Common Error Responses

```json
{
  "error": "Error message describing what went wrong"
}
```

### HTTP Status Codes

- **200**: Success
- **400**: Bad Request (invalid parameters)
- **404**: Not Found (project doesn't exist)
- **500**: Internal Server Error
- **503**: Service Unavailable (multi-project not available)

## Configuration Integration

The system integrates with the existing configuration infrastructure:

### MultiProjectConfigManager Integration

- Automatically loads projects from `orch-config.yaml`
- Supports graceful fallback when multi-project features are unavailable
- Maintains project state in `.orch-state/status.json` files

### Environment Detection

The system automatically detects whether multi-project support is available:

```python
try:
    from multi_project_config import MultiProjectConfigManager, ProjectStatus
    MULTI_PROJECT_AVAILABLE = True
except ImportError:
    MULTI_PROJECT_AVAILABLE = False
```

### Project State Loading

Project state is loaded from the project's `.orch-state/status.json` file:

```python
def load_project_state(project_name: str, project_path: str) -> Dict[str, Any]:
    """Load project state from .orch-state directory"""
    # Implementation handles missing files gracefully
    # Returns default state structure if file doesn't exist
```

## Session Management

The system tracks user sessions across projects:

- **project_rooms**: Maps project names to sets of session IDs
- **active_project_sessions**: Maps session IDs to current project names
- **Automatic cleanup**: Removes sessions on disconnect

## Testing

Use the provided test script to validate the API:

```bash
python tools/visualizer/test_multi_project_api.py
```

The test script validates:
- All API endpoints respond correctly
- Error handling for non-existent projects
- Project discovery functionality
- Debug endpoint includes multi-project information

## Integration Points

### Frontend Integration

The backend provides all necessary endpoints for frontend components to:

1. **Display project list**: Use `GET /api/projects`
2. **Switch projects**: Use `POST /api/projects/<name>/switch`
3. **Show project state**: Use `GET /api/projects/<name>/state`
4. **Real-time updates**: Subscribe to WebSocket events

### Command Processor Integration

The chat command processor can be enhanced to work with project contexts:

```python
# In send_chat_message endpoint
project_name = data.get('project_name', 'default')
# Pass project_name to command processor
```

### State Broadcasting Integration

The state broadcaster can emit project-specific events:

```python
# Broadcast to specific project room
socketio.emit('workflow_transition', data, room=project_name)
```

## Production Considerations

### Security

- Project path validation to prevent directory traversal
- Session ID validation and tracking
- Input sanitization for all user-provided data

### Performance

- Efficient session and room management
- Lazy loading of project states
- Minimal memory footprint for inactive projects

### Reliability

- Graceful fallback when multi-project features unavailable
- Comprehensive error handling and logging
- Automatic cleanup of disconnected sessions

### Scalability

- Room-based broadcasting reduces unnecessary network traffic
- Project-specific state isolation
- Configurable resource limits per project

## Future Enhancements

1. **Project Templates**: Pre-configured project setups
2. **Cross-Project Dependencies**: Visual dependency graphs
3. **Resource Monitoring**: Real-time resource usage per project
4. **Project Analytics**: Usage statistics and metrics
5. **Project Permissions**: Fine-grained access control
6. **Project Archiving**: Automated project lifecycle management