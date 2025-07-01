# Multi-Project Visualizer API Documentation

## Overview

This document provides comprehensive API documentation for the Multi-Project Visualizer backend, including REST endpoints, WebSocket events, and integration specifications.

## Table of Contents

1. [API Overview](#api-overview)
2. [Authentication & Security](#authentication--security)
3. [REST API Endpoints](#rest-api-endpoints)
4. [WebSocket Events](#websocket-events)
5. [Data Models](#data-models)
6. [Error Handling](#error-handling)
7. [Rate Limiting](#rate-limiting)
8. [SDK Examples](#sdk-examples)
9. [Testing Guide](#testing-guide)

## API Overview

### Base Configuration

**Base URL**: `http://localhost:5000` (default)
**Protocol**: HTTP/1.1 with WebSocket upgrade support
**Content-Type**: `application/json`
**WebSocket Protocol**: `socket.io`

### API Versioning

The API uses URL-based versioning:
- Current version: `v1`
- All endpoints prefixed with `/api/v1/`
- Future versions will be accessible via `/api/v2/`, etc.

### Feature Detection

The API includes feature detection to gracefully handle missing dependencies:

```python
# Multi-project support detection
GET /api/v1/features
{
    "multi_project_enabled": true,
    "collaboration_enabled": true,
    "context_management_enabled": true,
    "command_processor_enabled": true
}
```

## Authentication & Security

### Session Management

The API uses session-based authentication with automatic session management:

```javascript
// Sessions are automatically created on WebSocket connection
// Session ID is maintained in browser localStorage
const sessionId = localStorage.getItem('visualizer_session_id');
```

### Security Headers

All responses include security headers:
- `X-Content-Type-Options: nosniff`
- `X-Frame-Options: DENY`
- `X-XSS-Protection: 1; mode=block`
- `Content-Security-Policy: default-src 'self'`

### Input Validation

All inputs are validated and sanitized:
- **Project names**: Alphanumeric and hyphens only
- **Message content**: HTML escaped, length limited
- **File paths**: Normalized and validated against whitelist
- **Commands**: Validated against allowed command set

## REST API Endpoints

### Project Management

#### GET /api/v1/projects

List all registered projects with their status and configuration.

**Parameters**: None

**Response**:
```json
{
    "multi_project_enabled": true,
    "projects": [
        {
            "name": "example-project",
            "path": "/path/to/project",
            "status": "active",
            "priority": "normal",
            "description": "Example project description",
            "git_url": "https://github.com/user/repo.git",
            "owner": "user@example.com",
            "team": ["user1@example.com", "user2@example.com"],
            "discord_channel": "project-example",
            "tags": ["web", "api", "python"],
            "created_at": "2024-01-01T00:00:00Z",
            "last_activity": "2024-01-01T12:00:00Z",
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
                    "description": "Requires completion of dependency-project",
                    "criticality": "high"
                }
            ],
            "state": {
                "workflow_state": "SPRINT_ACTIVE",
                "tdd_cycles": {
                    "story-1": {
                        "state": "WRITE_TEST",
                        "last_updated": "2024-01-01T12:00:00Z",
                        "progress": 0.3
                    }
                },
                "last_updated": "2024-01-01T12:00:00Z",
                "transition_history": [
                    {
                        "from_state": "IDLE",
                        "to_state": "SPRINT_ACTIVE",
                        "timestamp": "2024-01-01T10:00:00Z",
                        "trigger": "sprint_start_command"
                    }
                ],
                "initialized": true,
                "project_name": "example-project"
            }
        }
    ],
    "total_count": 1,
    "active_count": 1,
    "last_updated": "2024-01-01T12:00:00Z"
}
```

**Status Codes**:
- `200`: Success
- `503`: Multi-project support not available

#### GET /api/v1/projects/{project_name}

Get detailed information for a specific project.

**Parameters**:
- `project_name` (path): Name of the project

**Response**:
```json
{
    "name": "example-project",
    "path": "/path/to/project",
    "status": "active",
    "priority": "normal",
    "description": "Example project description",
    "git_url": "https://github.com/user/repo.git",
    "owner": "user@example.com",
    "team": ["user1@example.com"],
    "discord_channel": "project-example",
    "tags": ["web", "api"],
    "created_at": "2024-01-01T00:00:00Z",
    "last_activity": "2024-01-01T12:00:00Z",
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
    "dependencies": [],
    "version": "1.0",
    "metrics": {
        "total_messages": 150,
        "active_users": 3,
        "workflow_transitions": 25,
        "uptime_hours": 72.5
    }
}
```

**Status Codes**:
- `200`: Success
- `404`: Project not found
- `503`: Multi-project support not available

#### POST /api/v1/projects/{project_name}/switch

Switch the active project context for a user session.

**Parameters**:
- `project_name` (path): Name of the project to switch to

**Request Body**:
```json
{
    "session_id": "user-session-uuid",
    "force": false,
    "preserve_context": true
}
```

**Response**:
```json
{
    "success": true,
    "old_project": "previous-project",
    "new_project": "example-project",
    "session_id": "user-session-uuid",
    "switch_timestamp": "2024-01-01T12:00:00Z",
    "project_state": {
        "workflow_state": "IDLE",
        "tdd_cycles": {},
        "last_updated": "2024-01-01T12:00:00Z",
        "transition_history": [],
        "initialized": true
    },
    "preserved_context": {
        "chat_position": 150,
        "active_commands": ["epic", "story"],
        "user_preferences": {}
    }
}
```

**Status Codes**:
- `200`: Success
- `400`: Invalid session or project name
- `404`: Project not found
- `409`: Cannot switch (project busy)
- `503`: Multi-project support not available

#### GET /api/v1/projects/{project_name}/state

Get the current workflow state for a specific project.

**Parameters**:
- `project_name` (path): Name of the project

**Response**:
```json
{
    "project_name": "example-project",
    "state": {
        "workflow_state": "SPRINT_ACTIVE",
        "tdd_cycles": {
            "story-1": {
                "state": "WRITE_TEST",
                "last_updated": "2024-01-01T12:00:00Z",
                "progress": 0.3,
                "agent_assignments": {
                    "test_agent": "agent-uuid-1",
                    "code_agent": "agent-uuid-2"
                }
            },
            "story-2": {
                "state": "REFACTOR",
                "last_updated": "2024-01-01T11:30:00Z",
                "progress": 0.8,
                "agent_assignments": {
                    "code_agent": "agent-uuid-3"
                }
            }
        },
        "last_updated": "2024-01-01T12:00:00Z",
        "transition_history": [
            {
                "from_state": "IDLE",
                "to_state": "SPRINT_ACTIVE",
                "timestamp": "2024-01-01T10:00:00Z",
                "trigger": "sprint_start_command",
                "user": "user@example.com"
            }
        ],
        "initialized": true,
        "pending_approvals": [
            {
                "id": "approval-uuid",
                "type": "epic_approval",
                "description": "Approve new user authentication epic",
                "created_at": "2024-01-01T11:45:00Z",
                "priority": "high"
            }
        ]
    },
    "last_updated": "2024-01-01T12:00:00Z",
    "state_hash": "sha256-hash-of-state"
}
```

**Status Codes**:
- `200`: Success
- `404`: Project not found
- `503`: Multi-project support not available

#### GET /api/v1/projects/{project_name}/config

Get project configuration details.

**Parameters**:
- `project_name` (path): Name of the project

**Response**: Same as GET /api/v1/projects/{project_name} but with additional configuration details.

#### POST /api/v1/projects/discover

Discover potential projects in specified directories.

**Request Body**:
```json
{
    "search_paths": ["/path/to/search1", "/path/to/search2"],
    "recursive": true,
    "include_hidden": false,
    "filters": {
        "file_patterns": ["*.py", "package.json", "Cargo.toml"],
        "exclude_patterns": ["node_modules", ".git", "__pycache__"]
    }
}
```

**Response**:
```json
{
    "discovered_projects": [
        {
            "name": "discovered-project",
            "path": "/path/to/discovered-project",
            "type": "git",
            "git_url": "https://github.com/user/repo.git",
            "language": "python",
            "framework": "flask",
            "confidence": 0.95,
            "recommended_config": {
                "description": "Auto-detected Flask web application",
                "tags": ["web", "python", "flask"],
                "ai_settings": {
                    "auto_approve_low_risk": true
                }
            }
        }
    ],
    "total_count": 1,
    "scan_duration_ms": 1250,
    "search_paths_scanned": 2
}
```

**Status Codes**:
- `200`: Success
- `400`: Invalid search paths
- `403`: Access denied to search paths
- `503`: Multi-project support not available

#### POST /api/v1/projects/register

Register a new project in the system.

**Request Body**:
```json
{
    "name": "new-project",
    "path": "/path/to/project",
    "description": "New project description",
    "git_url": "https://github.com/user/repo.git",
    "owner": "user@example.com",
    "team": ["user1@example.com", "user2@example.com"],
    "priority": "normal",
    "status": "active",
    "tags": ["web", "api"],
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
    }
}
```

**Response**:
```json
{
    "success": true,
    "message": "Project 'new-project' registered successfully",
    "project": {
        "name": "new-project",
        "path": "/path/to/project",
        "status": "active",
        "priority": "normal",
        "created_at": "2024-01-01T12:00:00Z",
        "id": "project-uuid"
    },
    "next_steps": [
        "Initialize project state",
        "Configure team permissions",
        "Set up Discord channel"
    ]
}
```

**Status Codes**:
- `201`: Project created successfully
- `400`: Invalid project configuration
- `409`: Project already exists
- `503`: Multi-project support not available

### Chat Management

#### GET /api/v1/projects/{project_name}/chat/history

Get chat history for a specific project.

**Parameters**:
- `project_name` (path): Name of the project
- `limit` (query): Maximum number of messages (default: 100, max: 500)
- `offset` (query): Number of messages to skip (default: 0)
- `since` (query): ISO timestamp to get messages since
- `message_types` (query): Comma-separated list of message types to include

**Response**:
```json
{
    "messages": [
        {
            "id": "message-uuid",
            "user_id": "user-uuid",
            "username": "user@example.com",
            "message": "Hello, team!",
            "timestamp": "2024-01-01T12:00:00Z",
            "type": "user",
            "project_name": "example-project",
            "edited": false,
            "reactions": [
                {
                    "emoji": "👍",
                    "users": ["user1@example.com"],
                    "count": 1
                }
            ],
            "thread_id": null,
            "reply_to": null
        }
    ],
    "total_count": 150,
    "has_more": true,
    "next_offset": 100
}
```

#### POST /api/v1/projects/{project_name}/chat/send

Send a message to a project's chat.

**Request Body**:
```json
{
    "message": "Hello, team!",
    "type": "user",
    "session_id": "user-session-uuid",
    "reply_to": "message-uuid",
    "thread_id": "thread-uuid"
}
```

**Response**:
```json
{
    "success": true,
    "message_id": "message-uuid",
    "timestamp": "2024-01-01T12:00:00Z",
    "broadcast": true
}
```

#### DELETE /api/v1/projects/{project_name}/chat/messages/{message_id}

Delete a specific message (if user has permission).

**Parameters**:
- `project_name` (path): Name of the project
- `message_id` (path): ID of the message to delete

**Response**:
```json
{
    "success": true,
    "deleted_at": "2024-01-01T12:00:00Z"
}
```

### System Information

#### GET /api/v1/status

Get overall system status and health information.

**Response**:
```json
{
    "status": "healthy",
    "version": "1.0.0",
    "uptime_seconds": 86400,
    "features": {
        "multi_project_enabled": true,
        "collaboration_enabled": true,
        "context_management_enabled": true,
        "command_processor_enabled": true
    },
    "statistics": {
        "total_projects": 5,
        "active_projects": 3,
        "connected_users": 12,
        "messages_today": 450,
        "workflow_transitions_today": 25
    },
    "resource_usage": {
        "memory_mb": 256,
        "cpu_percent": 15.3,
        "disk_usage_mb": 1024
    }
}
```

#### GET /api/v1/debug

Get detailed debugging information (requires debug mode).

**Response**:
```json
{
    "websocket_connections": 5,
    "active_rooms": ["project_example", "project_test"],
    "session_count": 3,
    "message_queue_size": 0,
    "error_count_last_hour": 2,
    "performance_metrics": {
        "avg_response_time_ms": 45,
        "memory_usage_trend": "stable",
        "connection_stability": 0.99
    }
}
```

## WebSocket Events

### Connection Management

#### Client → Server Events

##### `connect`
Emitted automatically when client connects.

**Data**: None (automatic)

**Server Response**: `connected` event with session information

##### `disconnect`
Emitted automatically when client disconnects.

**Data**: None (automatic)

**Server Action**: Cleans up user session and project rooms

### Project Management Events

#### Client → Server Events

##### `join_project`
Join a project-specific room for real-time updates.

**Data**:
```javascript
{
    project_name: 'example-project',
    session_id: 'user-session-uuid'
}
```

**Server Response**: `project_joined` event

##### `leave_project`
Leave a project room.

**Data**:
```javascript
{
    project_name: 'example-project',
    session_id: 'user-session-uuid'
}
```

**Server Response**: `project_left` event

##### `switch_project`
Switch to a different project via WebSocket.

**Data**:
```javascript
{
    project_name: 'new-project',
    session_id: 'user-session-uuid',
    preserve_context: true
}
```

**Server Response**: `project_switched` event

##### `request_project_list`
Request list of available projects.

**Data**: None

**Server Response**: `project_list` event

#### Server → Client Events

##### `project_joined`
Emitted when user successfully joins a project room.

**Data**:
```javascript
{
    project_name: 'example-project',
    session_id: 'user-session-uuid',
    timestamp: '2024-01-01T12:00:00Z',
    project_state: {
        workflow_state: 'IDLE',
        tdd_cycles: {},
        last_updated: '2024-01-01T12:00:00Z'
    },
    room_members: ['user1@example.com', 'user2@example.com'],
    welcome_message: 'Welcome to example-project!'
}
```

##### `project_left`
Emitted when user leaves a project room.

**Data**:
```javascript
{
    project_name: 'example-project',
    session_id: 'user-session-uuid',
    timestamp: '2024-01-01T12:00:00Z'
}
```

##### `project_switched`
Emitted when user successfully switches projects.

**Data**:
```javascript
{
    old_project: 'previous-project',
    new_project: 'example-project',
    session_id: 'user-session-uuid',
    timestamp: '2024-01-01T12:00:00Z',
    project_state: {
        workflow_state: 'SPRINT_ACTIVE',
        tdd_cycles: {},
        last_updated: '2024-01-01T12:00:00Z'
    }
}
```

##### `project_list`
Emitted in response to `request_project_list`.

**Data**:
```javascript
{
    enabled: true,
    projects: [
        {
            name: 'example-project',
            status: 'active',
            description: 'Example project',
            member_count: 3,
            last_activity: '2024-01-01T12:00:00Z'
        }
    ],
    total_count: 1,
    active_count: 1
}
```

### Chat Events

#### Client → Server Events

##### `chat_command`
Send a chat message or command.

**Data**:
```javascript
{
    message: 'Hello, team!',
    project_name: 'example-project',
    session_id: 'user-session-uuid',
    type: 'user',
    reply_to: 'message-uuid'
}
```

**Server Response**: `command_response` event

##### `start_typing`
Indicate user is typing.

**Data**:
```javascript
{
    project_name: 'example-project',
    session_id: 'user-session-uuid'
}
```

**Server Response**: Broadcasts `typing_indicator` to project room

##### `stop_typing`
Indicate user stopped typing.

**Data**:
```javascript
{
    project_name: 'example-project',
    session_id: 'user-session-uuid'
}
```

**Server Response**: Broadcasts typing stop to project room

#### Server → Client Events

##### `new_chat_message`
Broadcast new chat message to project room.

**Data**:
```javascript
{
    id: 'message-uuid',
    user_id: 'user-uuid',
    username: 'user@example.com',
    message: 'Hello, team!',
    timestamp: '2024-01-01T12:00:00Z',
    type: 'user',
    project_name: 'example-project',
    reply_to: null
}
```

##### `command_response`
Response to a chat command.

**Data**:
```javascript
{
    success: true,
    response: 'Epic created successfully',
    command: 'epic',
    timestamp: '2024-01-01T12:00:00Z',
    data: {
        epic_id: 'epic-uuid',
        description: 'New user authentication'
    }
}
```

##### `typing_indicator`
Indicates someone is typing in the project.

**Data**:
```javascript
{
    user_id: 'user-uuid',
    username: 'user@example.com',
    project_name: 'example-project',
    is_typing: true
}
```

### State Management Events

#### Server → Client Events

##### `state_update`
Workflow state has changed.

**Data**:
```javascript
{
    project_name: 'example-project',
    old_state: 'IDLE',
    new_state: 'SPRINT_ACTIVE',
    transition_data: {
        trigger: 'sprint_start_command',
        user: 'user@example.com',
        timestamp: '2024-01-01T12:00:00Z'
    },
    tdd_cycles: {
        'story-1': {
            state: 'WRITE_TEST',
            progress: 0.1
        }
    }
}
```

##### `workflow_transition`
Detailed workflow transition information.

**Data**:
```javascript
{
    project_name: 'example-project',
    transition: {
        from_state: 'IDLE',
        to_state: 'SPRINT_ACTIVE',
        timestamp: '2024-01-01T12:00:00Z',
        trigger: 'sprint_start_command',
        user: 'user@example.com',
        metadata: {
            sprint_name: 'Sprint 1',
            story_count: 5
        }
    }
}
```

##### `tdd_cycle_update`
TDD cycle state has changed.

**Data**:
```javascript
{
    project_name: 'example-project',
    story_id: 'story-1',
    cycle_data: {
        state: 'WRITE_TEST',
        progress: 0.3,
        last_updated: '2024-01-01T12:00:00Z',
        agent_assignments: {
            test_agent: 'agent-uuid-1'
        }
    }
}
```

### Error Events

#### Server → Client Events

##### `error`
General error information.

**Data**:
```javascript
{
    error: 'Project not found',
    code: 'PROJECT_NOT_FOUND',
    timestamp: '2024-01-01T12:00:00Z',
    request_id: 'req-uuid'
}
```

##### `project_error`
Project-specific error.

**Data**:
```javascript
{
    project_name: 'example-project',
    error: 'Failed to load project state',
    code: 'STATE_LOAD_ERROR',
    timestamp: '2024-01-01T12:00:00Z',
    details: {
        file_path: '/path/to/.orch-state/status.json',
        reason: 'File not found'
    }
}
```

## Data Models

### Project Model

```typescript
interface Project {
    name: string;
    path: string;
    status: ProjectStatus;
    priority: ProjectPriority;
    description?: string;
    git_url?: string;
    owner: string;
    team: string[];
    discord_channel?: string;
    tags: string[];
    created_at: string; // ISO 8601
    last_activity: string; // ISO 8601
    resource_limits: ResourceLimits;
    ai_settings: AISettings;
    work_hours: WorkHours;
    dependencies: ProjectDependency[];
    state: ProjectState;
    version: string;
}

type ProjectStatus = 'active' | 'idle' | 'paused' | 'error' | 'offline';
type ProjectPriority = 'low' | 'normal' | 'high' | 'critical';
```

### Resource Limits Model

```typescript
interface ResourceLimits {
    max_parallel_agents: number;
    max_parallel_cycles: number;
    max_memory_mb: number;
    max_disk_mb: number;
    cpu_priority: number; // 0.0 to 2.0
}
```

### AI Settings Model

```typescript
interface AISettings {
    auto_approve_low_risk: boolean;
    max_auto_retry: number;
    require_human_review: boolean;
    context_sharing_enabled: boolean;
}
```

### Work Hours Model

```typescript
interface WorkHours {
    timezone: string;
    start: string; // HH:MM format
    end: string; // HH:MM format
    days: WeekDay[];
}

type WeekDay = 'monday' | 'tuesday' | 'wednesday' | 'thursday' | 'friday' | 'saturday' | 'sunday';
```

### Project State Model

```typescript
interface ProjectState {
    workflow_state: WorkflowState;
    tdd_cycles: Record<string, TDDCycle>;
    last_updated: string; // ISO 8601
    transition_history: StateTransition[];
    initialized: boolean;
    project_name: string;
    pending_approvals: Approval[];
}

type WorkflowState = 'IDLE' | 'EPIC_DEFINITION' | 'BACKLOG_MANAGEMENT' | 'SPRING_PLANNING' | 'SPRINT_ACTIVE' | 'REVIEW_PENDING';
```

### TDD Cycle Model

```typescript
interface TDDCycle {
    state: TDDState;
    last_updated: string; // ISO 8601
    progress: number; // 0.0 to 1.0
    agent_assignments: Record<string, string>;
}

type TDDState = 'WRITE_TEST' | 'RUN_TEST' | 'IMPLEMENT' | 'REFACTOR' | 'COMPLETE';
```

### Message Model

```typescript
interface Message {
    id: string;
    user_id: string;
    username: string;
    message: string;
    timestamp: string; // ISO 8601
    type: MessageType;
    project_name: string;
    edited: boolean;
    reactions: Reaction[];
    thread_id?: string;
    reply_to?: string;
}

type MessageType = 'user' | 'bot' | 'system' | 'command' | 'error';
```

## Error Handling

### Error Response Format

All API errors follow a consistent format:

```json
{
    "error": "Human-readable error message",
    "code": "MACHINE_READABLE_ERROR_CODE",
    "timestamp": "2024-01-01T12:00:00Z",
    "request_id": "req-uuid",
    "details": {
        "field": "Additional context information"
    }
}
```

### Common Error Codes

| Code | Description | HTTP Status |
|------|-------------|-------------|
| `PROJECT_NOT_FOUND` | Requested project does not exist | 404 |
| `INVALID_PROJECT_NAME` | Project name contains invalid characters | 400 |
| `PROJECT_ALREADY_EXISTS` | Project with same name already registered | 409 |
| `MULTI_PROJECT_UNAVAILABLE` | Multi-project features not enabled | 503 |
| `INVALID_SESSION` | Session ID is invalid or expired | 401 |
| `PERMISSION_DENIED` | User lacks required permissions | 403 |
| `RATE_LIMIT_EXCEEDED` | Too many requests in time window | 429 |
| `INTERNAL_ERROR` | Unexpected server error | 500 |
| `VALIDATION_ERROR` | Request data validation failed | 400 |
| `STATE_CONFLICT` | Operation conflicts with current state | 409 |

### Error Recovery

The API includes automatic error recovery mechanisms:

1. **Retry Logic**: Transient errors are automatically retried with exponential backoff
2. **Graceful Degradation**: Features gracefully disable when dependencies unavailable
3. **Circuit Breaker**: Prevents cascade failures by temporarily disabling failing components
4. **Fallback Responses**: Provides cached or default data when primary sources fail

## Rate Limiting

### Rate Limits

| Endpoint Type | Requests per Minute | Burst Limit |
|---------------|-------------------|-------------|
| Project Management | 60 | 10 |
| Chat Messages | 300 | 50 |
| State Queries | 120 | 20 |
| WebSocket Events | 600 | 100 |

### Rate Limit Headers

Responses include rate limiting information:

```http
X-RateLimit-Limit: 60
X-RateLimit-Remaining: 45
X-RateLimit-Reset: 1640995200
X-RateLimit-Window: 60
```

### Rate Limit Exceeded Response

```json
{
    "error": "Rate limit exceeded",
    "code": "RATE_LIMIT_EXCEEDED",
    "retry_after": 15,
    "limit": 60,
    "window": 60
}
```

## SDK Examples

### JavaScript/TypeScript SDK

```typescript
class VisualizerAPI {
    private baseUrl: string;
    private socket: SocketIOClient.Socket;

    constructor(baseUrl: string = 'http://localhost:5000') {
        this.baseUrl = baseUrl;
        this.socket = io(baseUrl);
    }

    // REST API methods
    async getProjects(): Promise<Project[]> {
        const response = await fetch(`${this.baseUrl}/api/v1/projects`);
        const data = await response.json();
        return data.projects;
    }

    async switchProject(projectName: string, sessionId: string): Promise<SwitchResponse> {
        const response = await fetch(`${this.baseUrl}/api/v1/projects/${projectName}/switch`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ session_id: sessionId })
        });
        return response.json();
    }

    // WebSocket methods
    joinProject(projectName: string, sessionId: string): void {
        this.socket.emit('join_project', { project_name: projectName, session_id: sessionId });
    }

    sendMessage(message: string, projectName: string, sessionId: string): void {
        this.socket.emit('chat_command', {
            message,
            project_name: projectName,
            session_id: sessionId,
            type: 'user'
        });
    }

    // Event listeners
    onProjectSwitched(callback: (data: ProjectSwitchedEvent) => void): void {
        this.socket.on('project_switched', callback);
    }

    onNewMessage(callback: (data: Message) => void): void {
        this.socket.on('new_chat_message', callback);
    }

    onStateUpdate(callback: (data: StateUpdateEvent) => void): void {
        this.socket.on('state_update', callback);
    }
}

// Usage example
const api = new VisualizerAPI();

// Get projects
const projects = await api.getProjects();
console.log('Available projects:', projects);

// Join a project
api.joinProject('example-project', 'my-session-id');

// Listen for messages
api.onNewMessage((message) => {
    console.log(`New message from ${message.username}: ${message.message}`);
});

// Send a message
api.sendMessage('Hello, team!', 'example-project', 'my-session-id');
```

### Python SDK

```python
import requests
import socketio
from typing import List, Dict, Any, Optional

class VisualizerAPI:
    def __init__(self, base_url: str = 'http://localhost:5000'):
        self.base_url = base_url
        self.sio = socketio.Client()
        
    def connect(self):
        """Connect to the WebSocket server"""
        self.sio.connect(self.base_url)
    
    def disconnect(self):
        """Disconnect from the WebSocket server"""
        self.sio.disconnect()
    
    # REST API methods
    def get_projects(self) -> List[Dict[str, Any]]:
        """Get list of all projects"""
        response = requests.get(f'{self.base_url}/api/v1/projects')
        response.raise_for_status()
        return response.json()['projects']
    
    def get_project(self, project_name: str) -> Dict[str, Any]:
        """Get detailed information for a specific project"""
        response = requests.get(f'{self.base_url}/api/v1/projects/{project_name}')
        response.raise_for_status()
        return response.json()
    
    def switch_project(self, project_name: str, session_id: str) -> Dict[str, Any]:
        """Switch to a different project"""
        response = requests.post(
            f'{self.base_url}/api/v1/projects/{project_name}/switch',
            json={'session_id': session_id}
        )
        response.raise_for_status()
        return response.json()
    
    def get_project_state(self, project_name: str) -> Dict[str, Any]:
        """Get current workflow state for a project"""
        response = requests.get(f'{self.base_url}/api/v1/projects/{project_name}/state')
        response.raise_for_status()
        return response.json()
    
    # WebSocket methods
    def join_project(self, project_name: str, session_id: str):
        """Join a project room"""
        self.sio.emit('join_project', {
            'project_name': project_name,
            'session_id': session_id
        })
    
    def send_message(self, message: str, project_name: str, session_id: str):
        """Send a chat message"""
        self.sio.emit('chat_command', {
            'message': message,
            'project_name': project_name,
            'session_id': session_id,
            'type': 'user'
        })
    
    # Event handlers
    def on_project_joined(self, handler):
        """Register handler for project_joined events"""
        self.sio.on('project_joined', handler)
    
    def on_new_message(self, handler):
        """Register handler for new_chat_message events"""
        self.sio.on('new_chat_message', handler)
    
    def on_state_update(self, handler):
        """Register handler for state_update events"""
        self.sio.on('state_update', handler)

# Usage example
api = VisualizerAPI()
api.connect()

# Get projects
projects = api.get_projects()
print(f"Available projects: {[p['name'] for p in projects]}")

# Join a project
api.join_project('example-project', 'my-session-id')

# Register event handlers
@api.on_new_message
def handle_message(data):
    print(f"New message from {data['username']}: {data['message']}")

@api.on_state_update
def handle_state_update(data):
    print(f"State changed in {data['project_name']}: {data['old_state']} -> {data['new_state']}")

# Send a message
api.send_message('Hello from Python!', 'example-project', 'my-session-id')
```

## Testing Guide

### Unit Testing

Test individual API endpoints:

```python
import pytest
import requests

class TestProjectAPI:
    @pytest.fixture
    def api_base(self):
        return 'http://localhost:5000/api/v1'
    
    def test_get_projects(self, api_base):
        response = requests.get(f'{api_base}/projects')
        assert response.status_code == 200
        data = response.json()
        assert 'projects' in data
        assert 'total_count' in data
    
    def test_get_nonexistent_project(self, api_base):
        response = requests.get(f'{api_base}/projects/nonexistent')
        assert response.status_code == 404
        data = response.json()
        assert data['code'] == 'PROJECT_NOT_FOUND'
    
    def test_project_switch(self, api_base):
        # Assuming 'test-project' exists
        response = requests.post(
            f'{api_base}/projects/test-project/switch',
            json={'session_id': 'test-session'}
        )
        assert response.status_code == 200
        data = response.json()
        assert data['success'] is True
        assert data['new_project'] == 'test-project'
```

### Integration Testing

Test WebSocket functionality:

```python
import socketio
import asyncio
import pytest

class TestWebSocketIntegration:
    @pytest.fixture
    async def socket_client(self):
        sio = socketio.AsyncClient()
        await sio.connect('http://localhost:5000')
        yield sio
        await sio.disconnect()
    
    @pytest.mark.asyncio
    async def test_project_join_leave(self, socket_client):
        # Join project
        await socket_client.emit('join_project', {
            'project_name': 'test-project',
            'session_id': 'test-session'
        })
        
        # Wait for confirmation
        event = await socket_client.receive()
        assert event[0] == 'project_joined'
        assert event[1]['project_name'] == 'test-project'
        
        # Leave project
        await socket_client.emit('leave_project', {
            'project_name': 'test-project',
            'session_id': 'test-session'
        })
    
    @pytest.mark.asyncio
    async def test_chat_message(self, socket_client):
        # Join project first
        await socket_client.emit('join_project', {
            'project_name': 'test-project',
            'session_id': 'test-session'
        })
        
        # Send chat message
        await socket_client.emit('chat_command', {
            'message': 'Test message',
            'project_name': 'test-project',
            'session_id': 'test-session',
            'type': 'user'
        })
        
        # Wait for broadcast
        event = await socket_client.receive()
        assert event[0] == 'new_chat_message'
        assert event[1]['message'] == 'Test message'
```

### Load Testing

Test API performance:

```python
import concurrent.futures
import requests
import time

def load_test_projects_endpoint(base_url, num_requests=100, concurrency=10):
    """Load test the projects endpoint"""
    
    def make_request():
        start_time = time.time()
        response = requests.get(f'{base_url}/api/v1/projects')
        end_time = time.time()
        return {
            'status_code': response.status_code,
            'response_time': end_time - start_time,
            'success': response.status_code == 200
        }
    
    results = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=concurrency) as executor:
        futures = [executor.submit(make_request) for _ in range(num_requests)]
        results = [future.result() for future in concurrent.futures.as_completed(futures)]
    
    # Analyze results
    success_count = sum(1 for r in results if r['success'])
    avg_response_time = sum(r['response_time'] for r in results) / len(results)
    
    print(f"Load test results:")
    print(f"  Success rate: {success_count}/{num_requests} ({100*success_count/num_requests:.1f}%)")
    print(f"  Average response time: {avg_response_time:.3f}s")
    print(f"  Requests per second: {num_requests/sum(r['response_time'] for r in results):.1f}")

# Run load test
load_test_projects_endpoint('http://localhost:5000')
```

### API Testing Script

Complete API validation:

```bash
#!/bin/bash
# api_test.sh - Comprehensive API testing script

API_BASE="http://localhost:5000/api/v1"
SESSION_ID="test-session-$(date +%s)"

echo "Starting API tests..."

# Test 1: Get projects
echo "Test 1: Getting projects..."
curl -s "$API_BASE/projects" | jq .

# Test 2: Get system status
echo "Test 2: Getting system status..."
curl -s "$API_BASE/status" | jq .

# Test 3: Test project switching (if test-project exists)
echo "Test 3: Testing project switch..."
curl -s -X POST "$API_BASE/projects/test-project/switch" \
  -H "Content-Type: application/json" \
  -d "{\"session_id\": \"$SESSION_ID\"}" | jq .

# Test 4: Get project state
echo "Test 4: Getting project state..."
curl -s "$API_BASE/projects/test-project/state" | jq .

# Test 5: Test error handling
echo "Test 5: Testing error handling..."
curl -s "$API_BASE/projects/nonexistent" | jq .

echo "API tests completed."
```

This comprehensive API documentation provides all the information needed to integrate with and extend the Multi-Project Visualizer system. For additional support or to report issues, please refer to the troubleshooting section or contact the development team.