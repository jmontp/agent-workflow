# Technical Reference Guide
## AI Agent Workflow Visualizer

This technical reference provides detailed implementation guidance for developers working with the AI Agent Workflow Visualizer. It covers code patterns, API specifications, configuration options, and extension points.

---

## Table of Contents

1. [System Requirements](#system-requirements)
2. [Architecture Overview](#architecture-overview)
3. [Core Components Reference](#core-components-reference)
4. [API Reference](#api-reference)
5. [WebSocket Events](#websocket-events)
6. [Configuration Reference](#configuration-reference)
7. [Code Patterns](#code-patterns)
8. [Extension Guide](#extension-guide)
9. [Performance Tuning](#performance-tuning)
10. [Security Implementation](#security-implementation)

---

## System Requirements

### Runtime Requirements
- **Python**: 3.8+ (tested up to 3.12)
- **Node.js**: 14+ (for build tools)
- **Redis**: 6.0+ (for multi-instance scaling)
- **Browser**: Chrome 90+, Firefox 88+, Safari 14+, Edge 90+

### Python Dependencies
```python
# Core dependencies
flask>=2.3.0
flask-socketio>=5.3.0
python-socketio>=5.9.0
websockets>=11.0
pyyaml>=6.0

# Optional integrations
redis>=4.5.0           # For scaling
anthropic>=0.3.0       # For AI integration
prometheus-client>=0.16.0  # For metrics
```

### Development Dependencies
```python
# Testing
pytest>=7.4.0
pytest-asyncio>=0.21.0
pytest-cov>=4.1.0

# Code quality
black>=23.3.0
flake8>=6.0.0
mypy>=1.4.0
```

---

## Architecture Overview

### Component Hierarchy
```
┌─────────────────────────────────────────────────────────┐
│                    Browser Client                        │
├─────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌──────────────┐  ┌───────────────┐  │
│  │   Discord    │  │    State     │  │   Project     │  │
│  │    Chat      │  │  Visualizer  │  │   Manager     │  │
│  └──────┬──────┘  └──────┬───────┘  └───────┬───────┘  │
│         │                 │                   │          │
│         └─────────────────┼───────────────────┘          │
│                           │                              │
│                    ┌──────▼───────┐                      │
│                    │  WebSocket   │                      │
│                    │   Manager    │                      │
│                    └──────┬───────┘                      │
└───────────────────────────┼─────────────────────────────┘
                            │
                    ┌───────▼────────┐
                    │   Socket.IO    │
                    │     Server      │
                    └───────┬────────┘
                            │
        ┌───────────────────┼───────────────────┐
        │                   │                   │
┌───────▼────────┐  ┌───────▼────────┐  ┌──────▼───────┐
│     Flask      │  │    Command     │  │   Security   │
│   Application  │  │   Processor    │  │   Manager    │
└───────┬────────┘  └───────┬────────┘  └──────┬───────┘
        │                   │                   │
        └───────────────────┼───────────────────┘
                            │
                    ┌───────▼────────┐
                    │  Integration   │
                    │     Layer      │
                    └────────────────┘
```

### Data Flow Patterns

#### Command Execution Flow
```mermaid
sequenceDiagram
    participant U as User
    participant C as Chat UI
    participant W as WebSocket
    participant F as Flask
    participant P as Processor
    participant O as Orchestrator
    participant S as State
    
    U->>C: Type /epic "..."
    C->>W: Send command
    W->>F: Route message
    F->>P: Process command
    P->>O: Execute
    O->>S: Update state
    S-->>W: Broadcast
    W-->>C: Update UI
    C-->>U: Show result
```

---

## Core Components Reference

### 1. WebSocket Manager

**File**: `static/js/websocket-manager.js`

#### Public API
```javascript
class WebSocketManager {
    // Connection management
    connect(): Promise<void>
    disconnect(): void
    isConnected(): boolean
    
    // Event handling
    on(event: string, handler: Function): void
    off(event: string, handler: Function): void
    emit(event: string, data: any): void
    
    // Room management
    joinRoom(room: string): Promise<void>
    leaveRoom(room: string): Promise<void>
    getCurrentRooms(): Set<string>
    
    // Project context
    setProjectContext(projectName: string): void
    getProjectContext(): string
}

// Global instance
window.wsManager = new WebSocketManager();
```

#### Usage Examples
```javascript
// Listen for state updates
wsManager.on('state_update', (data) => {
    console.log('New state:', data);
    updateVisualization(data);
});

// Send a command
wsManager.emit('chat_command', {
    command: '/epic "Implement user auth"',
    project: 'my-project'
});

// Switch project context
await wsManager.setProjectContext('new-project');
```

### 2. Discord Chat Component

**File**: `static/js/discord-chat.js`

#### Public API
```javascript
class DiscordChat {
    // Lifecycle
    constructor(socketIO, visualizer)
    initialize(): Promise<void>
    destroy(): void
    
    // Project management
    setProject(projectName: string): void
    getProject(): string
    getProjectHistory(projectName: string): Array<Message>
    clearProjectHistory(projectName: string): void
    
    // Message handling
    sendMessage(text: string): Promise<void>
    addMessage(message: Message): void
    clearMessages(): void
    
    // UI state
    showTypingIndicator(userId: string): void
    hideTypingIndicator(userId: string): void
    updateAutocomplete(suggestions: Array<string>): void
}
```

#### Message Format
```typescript
interface Message {
    id: string;
    user_id: string;
    username: string;
    message: string;
    timestamp: string;
    type: 'user' | 'bot' | 'system';
    project_name: string;
    metadata?: {
        command?: string;
        status?: 'success' | 'error' | 'pending';
        embed?: EmbedData;
    };
}
```

### 3. State Visualizer

**File**: `static/js/visualizer.js`

#### Public API
```javascript
class StateVisualizer {
    // Initialization
    constructor(containerId: string)
    initialize(): Promise<void>
    
    // State updates
    updateWorkflowState(state: WorkflowState): void
    updateTDDCycles(cycles: Map<string, TDDCycle>): void
    highlightTransition(from: string, to: string): void
    
    // Layout control
    refreshLayout(): void
    setVerticalLayout(): void
    setHorizontalLayout(): void
    
    // Zoom control
    zoomIn(): void
    zoomOut(): void
    resetZoom(): void
    fitToScreen(): void
}
```

#### State Formats
```typescript
interface WorkflowState {
    current: string;
    available_transitions: string[];
    blocked_reason?: string;
    metadata: {
        sprint_id?: string;
        epic_id?: string;
        story_count?: number;
    };
}

interface TDDCycle {
    story_id: string;
    current_phase: 'design' | 'test_red' | 'code_green' | 'refactor' | 'commit';
    iteration: number;
    start_time: string;
    phases_completed: string[];
}
```

### 4. Project Manager

**File**: `static/js/project-manager.js`

#### Public API
```javascript
class ProjectManager {
    // Project operations
    loadProjects(): Promise<void>
    createProject(config: ProjectConfig): Promise<Project>
    switchProject(projectId: string): Promise<void>
    deleteProject(projectId: string): Promise<boolean>
    
    // Project queries
    getActiveProject(): Project
    getProject(projectId: string): Project
    getAllProjects(): Map<string, Project>
    
    // UI updates
    updateProjectStatus(projectId: string, status: string): void
    showProjectMenu(projectId: string, event: MouseEvent): void
}
```

---

## API Reference

### REST Endpoints

#### Project Management

##### `GET /api/projects`
List all registered projects.

**Response**:
```json
{
    "multi_project_enabled": true,
    "projects": [
        {
            "name": "project-alpha",
            "path": "/path/to/project",
            "status": "active",
            "priority": "high",
            "state": {
                "workflow_state": "SPRINT_ACTIVE",
                "last_updated": "2024-01-01T12:00:00Z"
            }
        }
    ],
    "total_count": 1,
    "active_count": 1
}
```

##### `POST /api/projects`
Create a new project.

**Request**:
```json
{
    "name": "new-project",
    "path": "/path/to/new-project",
    "git_url": "https://github.com/user/repo.git",
    "description": "New project description"
}
```

##### `PUT /api/projects/{project_name}`
Update project configuration.

##### `DELETE /api/projects/{project_name}`
Delete a project (requires confirmation).

#### State Management

##### `GET /api/state`
Get current system state.

**Response**:
```json
{
    "workflow_state": "IDLE",
    "tdd_cycles": {},
    "last_updated": "2024-01-01T12:00:00Z",
    "projects": {
        "project-alpha": {
            "state": "SPRINT_ACTIVE",
            "active_stories": 3
        }
    }
}
```

##### `GET /api/projects/{project_name}/state`
Get project-specific state.

#### Chat & Commands

##### `POST /api/chat/send`
Send a chat message/command.

**Request**:
```json
{
    "message": "/epic \"Implement authentication\"",
    "project_name": "project-alpha",
    "user_id": "user_123"
}
```

##### `GET /api/chat/history`
Get chat history for a project.

**Query Parameters**:
- `project_name` (required)
- `limit` (optional, default: 100)
- `before` (optional, timestamp)

##### `GET /api/chat/autocomplete`
Get command autocomplete suggestions.

**Query Parameters**:
- `partial` - Partial command text
- `project_name` - Current project context

---

## WebSocket Events

### Client → Server Events

#### `connect`
Establish WebSocket connection.

#### `join_project_room`
Join a project-specific room.
```javascript
socket.emit('join_project_room', {
    project_name: 'project-alpha',
    user_id: 'user_123'
});
```

#### `leave_project_room`
Leave a project room.

#### `chat_command`
Send a chat command.
```javascript
socket.emit('chat_command', {
    command: '/epic "New feature"',
    project_name: 'project-alpha'
});
```

#### `start_typing` / `stop_typing`
Typing indicators.

### Server → Client Events

#### `state_update`
Workflow state change notification.
```javascript
socket.on('state_update', (data) => {
    // data.workflow_state
    // data.project_name
    // data.timestamp
});
```

#### `chat_message`
New chat message.
```javascript
socket.on('chat_message', (message) => {
    // message.id
    // message.user_id
    // message.message
    // message.type
});
```

#### `typing_update`
Typing indicator update.

#### `error`
Error notification.
```javascript
socket.on('error', (error) => {
    // error.code
    // error.message
    // error.details
});
```

---

## Configuration Reference

### Application Configuration

**File**: `orch-config.yaml`

```yaml
# Project definitions
projects:
  project-alpha:
    path: "/path/to/project-alpha"
    status: "active"
    priority: "high"
    git_url: "https://github.com/org/project-alpha.git"
    
    # Resource limits
    resource_limits:
      max_parallel_agents: 3
      max_memory_mb: 2048
      max_disk_mb: 10240
      cpu_priority: 1.0
    
    # AI settings
    ai_settings:
      auto_approve_low_risk: true
      max_auto_retry: 3
      require_human_review: false
      
    # Work schedule
    work_hours:
      timezone: "America/New_York"
      start: "09:00"
      end: "17:00"
      days: ["monday", "tuesday", "wednesday", "thursday", "friday"]

# Global settings
global_settings:
  max_parallel_projects: 5
  default_timeout: 300
  session_timeout: 3600
  
# Web interface settings
web_interface:
  host: "0.0.0.0"
  port: 5000
  debug: false
  cors_origins: ["https://app.example.com"]
  
# Security settings
security:
  require_auth: true
  api_key_header: "X-API-Key"
  session_encryption: true
  audit_logging: true
```

### Interface Configuration

**File**: `interface_configs.json`

```json
{
  "configs": {
    "claude_code": {
      "interface_type": "claude_code",
      "enabled": true,
      "api_key": "${CLAUDE_API_KEY}",
      "endpoint_url": null,
      "timeout": 300,
      "max_tokens": 4000,
      "model": "claude-3-sonnet-20240229",
      "temperature": 0.7,
      "custom_settings": {
        "use_system_prompt": true,
        "retry_on_rate_limit": true
      }
    }
  },
  "active_interface": "claude_code"
}
```

### Environment Variables

```bash
# Flask settings
FLASK_ENV=production
FLASK_DEBUG=false
SECRET_KEY=your-secret-key

# Database (optional)
DATABASE_URL=postgresql://user:pass@localhost/visualizer

# Redis (for scaling)
REDIS_URL=redis://localhost:6379/0

# Security
FORCE_HTTPS=true
SESSION_COOKIE_SECURE=true
ALLOWED_ORIGINS=https://app.example.com

# AI Integration
ANTHROPIC_API_KEY=sk-ant-...
OPENAI_API_KEY=sk-...

# Monitoring
SENTRY_DSN=https://...@sentry.io/...
PROMETHEUS_ENABLED=true

# Logging
LOG_LEVEL=INFO
LOG_FORMAT=json
LOG_FILE=/var/log/visualizer/app.log
```

---

## Code Patterns

### Error Handling Pattern

```javascript
// JavaScript error handling
async function riskyOperation() {
    try {
        const result = await someAsyncOperation();
        return result;
    } catch (error) {
        const handled = window.ErrorManager.handleError(error, {
            component: 'MyComponent',
            operation: 'riskyOperation',
            context: { /* additional data */ },
            recovery: 'retry' // or 'fallback', 'ignore', 'escalate'
        });
        
        if (handled.successful) {
            return handled.result;
        } else {
            // Manual recovery or propagate
            throw handled.error;
        }
    }
}
```

```python
# Python error handling
from lib.error_manager import handle_errors, ErrorContext

@handle_errors('MyComponent', recovery='retry')
async def risky_operation(self, data):
    # Automatic error handling via decorator
    result = await external_api_call(data)
    return result

# Or manual handling
try:
    result = await risky_operation()
except Exception as e:
    error_context = ErrorContext(
        component='MyComponent',
        operation='risky_operation',
        user_id=session.get('user_id'),
        additional_data={'input': data}
    )
    error_record = error_manager.handle_error(e, error_context)
    
    if error_record.recovery_attempted:
        result = error_record.recovery_result
    else:
        raise
```

### State Update Pattern

```javascript
// Client-side state update
class ComponentWithState {
    constructor() {
        this.state = {};
        this.setupStateSync();
    }
    
    setupStateSync() {
        wsManager.on('state_update', (data) => {
            if (data.project_name === this.currentProject) {
                this.handleStateUpdate(data);
            }
        });
    }
    
    handleStateUpdate(data) {
        const oldState = { ...this.state };
        this.state = data.state;
        
        // Notify UI of changes
        this.notifyStateChange(oldState, this.state);
        
        // Update DOM
        this.render();
    }
    
    updateState(changes) {
        // Optimistic update
        this.state = { ...this.state, ...changes };
        this.render();
        
        // Send to server
        wsManager.emit('update_state', {
            project: this.currentProject,
            changes: changes
        });
    }
}
```

### Component Communication Pattern

```javascript
// Event-based loose coupling
class ProjectManager {
    switchProject(newProject) {
        const oldProject = this.currentProject;
        this.currentProject = newProject;
        
        // Notify other components
        document.dispatchEvent(new CustomEvent('project-switched', {
            detail: {
                oldProject,
                newProject,
                timestamp: Date.now()
            }
        }));
    }
}

// In other components
document.addEventListener('project-switched', (event) => {
    const { oldProject, newProject } = event.detail;
    // React to project change
    this.handleProjectSwitch(newProject);
});
```

### Progressive Enhancement Pattern

```python
# Python progressive enhancement
class VisualizerApp:
    def __init__(self):
        self.orchestrator = self._init_orchestrator()
        self.chat_sync = self._init_chat_sync()
        self.features = self._detect_features()
    
    def _init_orchestrator(self):
        try:
            from orchestrator import Orchestrator
            return Orchestrator()
        except ImportError:
            logger.warning("Orchestrator not available")
            return MockOrchestrator()
    
    def _detect_features(self):
        return {
            'orchestrator': not isinstance(self.orchestrator, MockOrchestrator),
            'chat_sync': self.chat_sync is not None,
            'ai_enabled': os.getenv('ANTHROPIC_API_KEY') is not None,
            'multi_project': self._check_multi_project_support()
        }
    
    def process_command(self, command):
        if self.features['orchestrator']:
            return self.orchestrator.process_command(command)
        else:
            return self._mock_command_response(command)
```

---

## Extension Guide

### Adding a New Command

1. **Define command pattern** in `command_processor.py`:
```python
self.command_patterns['/analyze'] = {
    'pattern': r'^/analyze\s+(\w+)\s+"([^"]+)"$',
    'handler': self._handle_analyze_command,
    'description': 'Analyze code or data',
    'usage': '/analyze <type> "<target>"',
    'examples': [
        '/analyze code "src/main.py"',
        '/analyze data "metrics.json"'
    ],
    'min_permission': UserPermission.CONTRIBUTOR
}
```

2. **Implement handler**:
```python
async def _handle_analyze_command(self, args, user_id, project_name):
    analysis_type = args[0]
    target = args[1]
    
    # Validate inputs
    if analysis_type not in ['code', 'data']:
        return self._error_response("Invalid analysis type")
    
    # Execute analysis
    try:
        result = await self.analyzer.analyze(analysis_type, target)
        return {
            'type': 'bot',
            'message': f'Analysis complete for {target}',
            'metadata': {
                'embed': self._format_analysis_embed(result)
            }
        }
    except Exception as e:
        return self._error_response(str(e))
```

3. **Add autocomplete** in `discord-chat.js`:
```javascript
// In getAutocompleteCommands()
if (partial.startsWith('/analyze')) {
    const types = ['code', 'data'];
    return types
        .filter(t => t.startsWith(partial.slice(9)))
        .map(t => `/analyze ${t} "`);
}
```

### Adding a New UI Component

1. **Create component file**:
```javascript
// static/js/components/my-component.js
class MyComponent {
    constructor(container) {
        this.container = container;
        this.state = {};
        this.initialize();
    }
    
    initialize() {
        this.render();
        this.attachEventHandlers();
        this.subscribeToUpdates();
    }
    
    render() {
        this.container.innerHTML = `
            <div class="my-component">
                <!-- Component HTML -->
            </div>
        `;
    }
    
    attachEventHandlers() {
        // DOM event handlers
    }
    
    subscribeToUpdates() {
        wsManager.on('relevant_event', (data) => {
            this.handleUpdate(data);
        });
    }
}

// Export for use
window.MyComponent = MyComponent;
```

2. **Add styles**:
```css
/* static/css/my-component.css */
.my-component {
    /* Component styles */
}
```

3. **Initialize in main app**:
```javascript
// In app-core.js
document.addEventListener('DOMContentLoaded', () => {
    const container = document.getElementById('my-component-container');
    if (container) {
        new MyComponent(container);
    }
});
```

### Adding a New WebSocket Event

1. **Define server handler** in `app.py`:
```python
@socketio.on('my_custom_event')
@validate_project_access
def handle_custom_event(data):
    project_name = data.get('project_name')
    user_id = session.get('user_id')
    
    # Process event
    result = process_custom_event(data)
    
    # Emit response
    emit('custom_event_response', result)
    
    # Broadcast if needed
    emit('custom_event_update', result, 
         room=f'project_{project_name}', 
         broadcast=True)
```

2. **Add client handler**:
```javascript
// Subscribe to event
wsManager.on('custom_event_response', (data) => {
    console.log('Received response:', data);
    updateUI(data);
});

// Send event
wsManager.emit('my_custom_event', {
    project_name: currentProject,
    data: customData
});
```

---

## Performance Tuning

### Frontend Optimization

#### 1. Lazy Loading
```javascript
// Lazy load non-critical components
const loadAnalytics = () => import('./analytics.js');

// Load when needed
button.addEventListener('click', async () => {
    const { Analytics } = await loadAnalytics();
    const analytics = new Analytics();
    analytics.track('button_clicked');
});
```

#### 2. Debouncing
```javascript
// Debounce expensive operations
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

// Use for search, resize, etc.
const debouncedSearch = debounce(performSearch, 300);
input.addEventListener('input', debouncedSearch);
```

#### 3. Virtual Scrolling
```javascript
// For large message lists
class VirtualScroller {
    constructor(container, items, itemHeight) {
        this.container = container;
        this.items = items;
        this.itemHeight = itemHeight;
        this.visibleRange = { start: 0, end: 50 };
    }
    
    render() {
        const visibleItems = this.items.slice(
            this.visibleRange.start,
            this.visibleRange.end
        );
        // Render only visible items
    }
}
```

### Backend Optimization

#### 1. Caching
```python
from functools import lru_cache
from flask_caching import Cache

cache = Cache(app, config={'CACHE_TYPE': 'redis'})

@cache.memoize(timeout=300)
def get_project_state(project_name):
    # Expensive operation cached for 5 minutes
    return load_project_state(project_name)

@lru_cache(maxsize=128)
def parse_command(command_text):
    # In-memory cache for command parsing
    return command_parser.parse(command_text)
```

#### 2. Connection Pooling
```python
# Redis connection pool
redis_pool = redis.ConnectionPool(
    host='localhost',
    port=6379,
    max_connections=50
)
redis_client = redis.Redis(connection_pool=redis_pool)

# Database connection pool
engine = create_engine(
    DATABASE_URL,
    pool_size=20,
    max_overflow=30,
    pool_pre_ping=True
)
```

#### 3. Async Operations
```python
import asyncio
from concurrent.futures import ThreadPoolExecutor

executor = ThreadPoolExecutor(max_workers=10)

async def process_commands_async(commands):
    loop = asyncio.get_event_loop()
    tasks = []
    
    for command in commands:
        task = loop.run_in_executor(
            executor,
            process_command_sync,
            command
        )
        tasks.append(task)
    
    results = await asyncio.gather(*tasks)
    return results
```

### Monitoring & Profiling

#### Frontend Profiling
```javascript
// Performance marks
performance.mark('myOperation-start');
// ... operation ...
performance.mark('myOperation-end');
performance.measure('myOperation', 'myOperation-start', 'myOperation-end');

// Get measurements
const measures = performance.getEntriesByType('measure');
console.log(measures);
```

#### Backend Profiling
```python
import time
from functools import wraps

def profile_time(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        start = time.time()
        result = func(*args, **kwargs)
        duration = time.time() - start
        logger.info(f"{func.__name__} took {duration:.3f}s")
        return result
    return wrapper

@profile_time
def expensive_operation():
    # Operation to profile
    pass
```

---

## Security Implementation

### Input Validation

```python
from security import validate_input, sanitize_html

def validate_command(command_text):
    # Length check
    if len(command_text) > 1000:
        raise ValueError("Command too long")
    
    # Format check
    if not command_text.startswith('/'):
        raise ValueError("Commands must start with /")
    
    # Injection prevention
    if any(char in command_text for char in ['<', '>', '&', ';']):
        command_text = sanitize_html(command_text)
    
    return command_text
```

### API Authentication

```python
from functools import wraps
from flask import request, abort

def require_api_key(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        api_key = request.headers.get('X-API-Key')
        
        if not api_key:
            abort(401, 'API key required')
        
        if not validate_api_key(api_key):
            abort(403, 'Invalid API key')
        
        return f(*args, **kwargs)
    return decorated_function

@app.route('/api/sensitive')
@require_api_key
def sensitive_endpoint():
    return jsonify({'data': 'sensitive'})
```

### Session Security

```python
# Secure session configuration
app.config.update(
    SESSION_COOKIE_SECURE=True,
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE='Strict',
    PERMANENT_SESSION_LIFETIME=timedelta(hours=1)
)

# Session validation
@app.before_request
def validate_session():
    if 'user_id' in session:
        # Check session validity
        last_activity = session.get('last_activity')
        if last_activity:
            if datetime.now() - last_activity > timedelta(hours=1):
                session.clear()
                return redirect('/login')
        
        session['last_activity'] = datetime.now()
```

### Rate Limiting

```python
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

limiter = Limiter(
    app,
    key_func=get_remote_address,
    default_limits=["1000 per hour"],
    storage_uri="redis://localhost:6379"
)

# Apply rate limits
@app.route('/api/commands', methods=['POST'])
@limiter.limit("10 per minute")
def send_command():
    # Process command
    pass

# Custom rate limit by user
@limiter.request_filter
def user_rate_limit():
    # Premium users get higher limits
    user = get_current_user()
    if user and user.is_premium:
        return "100 per minute"
    return "10 per minute"
```

---

This technical reference provides comprehensive implementation details for the AI Agent Workflow Visualizer. Use it as a guide for understanding the system's internals and extending its functionality.