# Code Patterns & Best Practices
## AI Agent Workflow Visualizer

This document describes common code patterns, implementation strategies, and best practices used throughout the AI Agent Workflow Visualizer. These patterns ensure consistency, maintainability, and reliability.

---

## Table of Contents

1. [JavaScript Patterns](#javascript-patterns)
2. [Python Patterns](#python-patterns)
3. [CSS Patterns](#css-patterns)
4. [WebSocket Patterns](#websocket-patterns)
5. [Error Handling Patterns](#error-handling-patterns)
6. [State Management Patterns](#state-management-patterns)
7. [Security Patterns](#security-patterns)
8. [Testing Patterns](#testing-patterns)
9. [Performance Patterns](#performance-patterns)
10. [Anti-Patterns to Avoid](#anti-patterns-to-avoid)

---

## JavaScript Patterns

### 1. Module Pattern with Singleton

Used for global managers that should have only one instance.

```javascript
// WebSocket Manager Singleton
const WebSocketManager = (function() {
    let instance;
    
    function createInstance() {
        const manager = {
            socket: null,
            connected: false,
            
            connect() {
                if (!this.socket) {
                    this.socket = io();
                    this.setupEventHandlers();
                }
                return this.socket;
            },
            
            setupEventHandlers() {
                this.socket.on('connect', () => {
                    this.connected = true;
                    this.onConnect();
                });
            }
        };
        
        return manager;
    }
    
    return {
        getInstance() {
            if (!instance) {
                instance = createInstance();
            }
            return instance;
        }
    };
})();

// Usage
const wsManager = WebSocketManager.getInstance();
```

### 2. Event Emitter Pattern

For decoupled component communication.

```javascript
class EventEmitter {
    constructor() {
        this.events = {};
    }
    
    on(event, listener) {
        if (!this.events[event]) {
            this.events[event] = [];
        }
        this.events[event].push(listener);
        
        // Return unsubscribe function
        return () => this.off(event, listener);
    }
    
    off(event, listener) {
        if (!this.events[event]) return;
        
        this.events[event] = this.events[event].filter(l => l !== listener);
    }
    
    emit(event, ...args) {
        if (!this.events[event]) return;
        
        this.events[event].forEach(listener => {
            try {
                listener(...args);
            } catch (error) {
                console.error(`Error in event listener for ${event}:`, error);
            }
        });
    }
}

// Usage in components
class ProjectManager extends EventEmitter {
    switchProject(newProject) {
        const oldProject = this.currentProject;
        this.currentProject = newProject;
        
        this.emit('projectSwitched', { oldProject, newProject });
    }
}
```

### 3. Promise-based Async Pattern

Consistent async operation handling.

```javascript
class APIClient {
    async request(endpoint, options = {}) {
        const defaultOptions = {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json'
            }
        };
        
        const finalOptions = { ...defaultOptions, ...options };
        
        try {
            const response = await fetch(endpoint, finalOptions);
            
            if (!response.ok) {
                throw new APIError(response.status, await response.text());
            }
            
            return await response.json();
        } catch (error) {
            if (error instanceof APIError) {
                throw error;
            }
            throw new NetworkError('Network request failed', error);
        }
    }
    
    // Convenience methods
    get(endpoint) {
        return this.request(endpoint);
    }
    
    post(endpoint, data) {
        return this.request(endpoint, {
            method: 'POST',
            body: JSON.stringify(data)
        });
    }
}

// Usage with error handling
async function loadProjects() {
    const api = new APIClient();
    
    try {
        const projects = await api.get('/api/projects');
        updateUI(projects);
    } catch (error) {
        if (error instanceof APIError && error.status === 404) {
            showMessage('No projects found');
        } else {
            showError('Failed to load projects');
        }
    }
}
```

### 4. Component Lifecycle Pattern

Standard lifecycle for UI components.

```javascript
class UIComponent {
    constructor(container, options = {}) {
        this.container = container;
        this.options = options;
        this.state = {};
        this.subscriptions = [];
        
        this.initialize();
    }
    
    async initialize() {
        try {
            await this.loadData();
            this.render();
            this.attachEventHandlers();
            this.subscribeToUpdates();
            this.onReady();
        } catch (error) {
            this.handleInitError(error);
        }
    }
    
    async loadData() {
        // Override in subclass
    }
    
    render() {
        // Override in subclass
    }
    
    attachEventHandlers() {
        // Store references for cleanup
        this.handlers = {
            onClick: this.handleClick.bind(this),
            onKeyDown: this.handleKeyDown.bind(this)
        };
        
        this.container.addEventListener('click', this.handlers.onClick);
        this.container.addEventListener('keydown', this.handlers.onKeyDown);
    }
    
    subscribeToUpdates() {
        // Store subscriptions for cleanup
        const unsubscribe = wsManager.on('update', this.handleUpdate.bind(this));
        this.subscriptions.push(unsubscribe);
    }
    
    destroy() {
        // Clean up event handlers
        if (this.handlers) {
            this.container.removeEventListener('click', this.handlers.onClick);
            this.container.removeEventListener('keydown', this.handlers.onKeyDown);
        }
        
        // Clean up subscriptions
        this.subscriptions.forEach(unsubscribe => unsubscribe());
        
        // Clear container
        this.container.innerHTML = '';
        
        this.onDestroy();
    }
    
    // Lifecycle hooks
    onReady() {}
    onDestroy() {}
    handleInitError(error) {
        console.error('Component initialization failed:', error);
    }
}
```

### 5. Factory Pattern

For creating similar objects with different configurations.

```javascript
class MessageFactory {
    static createMessage(type, content, metadata = {}) {
        const baseMessage = {
            id: generateUUID(),
            timestamp: new Date().toISOString(),
            content,
            metadata
        };
        
        switch (type) {
            case 'user':
                return {
                    ...baseMessage,
                    type: 'user',
                    username: metadata.username || 'Anonymous',
                    user_id: metadata.user_id
                };
                
            case 'bot':
                return {
                    ...baseMessage,
                    type: 'bot',
                    username: 'System Bot',
                    status: metadata.status || 'success'
                };
                
            case 'system':
                return {
                    ...baseMessage,
                    type: 'system',
                    severity: metadata.severity || 'info'
                };
                
            default:
                throw new Error(`Unknown message type: ${type}`);
        }
    }
    
    static createErrorMessage(error, context) {
        return this.createMessage('system', error.message, {
            severity: 'error',
            error_code: error.code,
            context
        });
    }
    
    static createCommandResponse(command, result) {
        return this.createMessage('bot', result.message, {
            command,
            status: result.success ? 'success' : 'error',
            data: result.data
        });
    }
}

// Usage
const userMessage = MessageFactory.createMessage('user', 'Hello', {
    username: 'John',
    user_id: 'user_123'
});

const errorMessage = MessageFactory.createErrorMessage(
    new Error('Connection failed'),
    { component: 'WebSocket' }
);
```

---

## Python Patterns

### 1. Context Manager Pattern

For resource management and cleanup.

```python
from contextlib import contextmanager
import threading

@contextmanager
def project_context(project_name):
    """Temporarily switch project context"""
    old_project = get_current_project()
    
    try:
        set_current_project(project_name)
        yield project_name
    finally:
        set_current_project(old_project)

# Usage
with project_context('project-alpha'):
    # Operations run in project-alpha context
    process_command(command)

# Or as a class
class DatabaseTransaction:
    def __init__(self, connection):
        self.connection = connection
        self.transaction = None
    
    def __enter__(self):
        self.transaction = self.connection.begin()
        return self.transaction
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is None:
            self.transaction.commit()
        else:
            self.transaction.rollback()
        return False  # Propagate exception

# Usage
with DatabaseTransaction(db_connection) as tx:
    tx.execute("INSERT INTO ...")
```

### 2. Decorator Pattern

For cross-cutting concerns like validation, caching, logging.

```python
from functools import wraps
import time
import logging

def validate_project_access(f):
    """Validate user has access to project"""
    @wraps(f)
    def decorated(*args, **kwargs):
        # Extract project_name from various sources
        project_name = (
            kwargs.get('project_name') or
            request.form.get('project_name') or
            request.json.get('project_name')
        )
        
        if not project_name:
            abort(400, 'Project name required')
        
        if not user_has_project_access(session['user_id'], project_name):
            abort(403, 'Access denied to project')
        
        return f(*args, **kwargs)
    return decorated

def rate_limit(max_calls, period):
    """Rate limit decorator with configurable limits"""
    def decorator(f):
        calls = []
        
        @wraps(f)
        def wrapper(*args, **kwargs):
            now = time.time()
            # Remove old calls
            calls[:] = [call for call in calls if call > now - period]
            
            if len(calls) >= max_calls:
                raise RateLimitError(f"Rate limit exceeded: {max_calls}/{period}s")
            
            calls.append(now)
            return f(*args, **kwargs)
        
        return wrapper
    return decorator

def retry_on_failure(max_retries=3, delay=1.0, backoff=2.0):
    """Retry failed operations with exponential backoff"""
    def decorator(f):
        @wraps(f)
        async def wrapper(*args, **kwargs):
            last_exception = None
            current_delay = delay
            
            for attempt in range(max_retries + 1):
                try:
                    return await f(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    if attempt < max_retries:
                        logger.warning(f"Attempt {attempt + 1} failed: {e}")
                        await asyncio.sleep(current_delay)
                        current_delay *= backoff
                    else:
                        logger.error(f"All {max_retries} retries failed")
                        raise
            
            raise last_exception
        
        return wrapper
    return decorator

# Usage
@validate_project_access
@rate_limit(10, 60)  # 10 calls per minute
@retry_on_failure(max_retries=3)
async def process_command(command, project_name):
    # Function implementation
    pass
```

### 3. Strategy Pattern

For interchangeable algorithms or behaviors.

```python
from abc import ABC, abstractmethod

class RecoveryStrategy(ABC):
    @abstractmethod
    async def recover(self, error, context):
        """Attempt to recover from error"""
        pass

class RetryStrategy(RecoveryStrategy):
    def __init__(self, max_retries=3, delay=1.0):
        self.max_retries = max_retries
        self.delay = delay
    
    async def recover(self, error, context):
        for attempt in range(self.max_retries):
            try:
                return await context['operation']()
            except Exception as e:
                if attempt == self.max_retries - 1:
                    raise
                await asyncio.sleep(self.delay)

class FallbackStrategy(RecoveryStrategy):
    def __init__(self, fallback_value):
        self.fallback_value = fallback_value
    
    async def recover(self, error, context):
        logger.warning(f"Using fallback for {context['operation_name']}")
        return self.fallback_value

class CircuitBreakerStrategy(RecoveryStrategy):
    def __init__(self, failure_threshold=5, timeout=60):
        self.failure_threshold = failure_threshold
        self.timeout = timeout
        self.failures = 0
        self.last_failure_time = None
        self.is_open = False
    
    async def recover(self, error, context):
        if self.is_open:
            if time.time() - self.last_failure_time > self.timeout:
                self.is_open = False
                self.failures = 0
            else:
                raise CircuitOpenError("Circuit breaker is open")
        
        try:
            result = await context['operation']()
            self.failures = 0
            return result
        except Exception as e:
            self.failures += 1
            self.last_failure_time = time.time()
            
            if self.failures >= self.failure_threshold:
                self.is_open = True
                logger.error(f"Circuit breaker opened after {self.failures} failures")
            
            raise

# Usage
class ErrorHandler:
    def __init__(self):
        self.strategies = {
            'network': RetryStrategy(max_retries=3),
            'validation': FallbackStrategy(None),
            'overload': CircuitBreakerStrategy()
        }
    
    async def handle_error(self, error, error_type, context):
        strategy = self.strategies.get(error_type)
        if strategy:
            return await strategy.recover(error, context)
        raise error
```

### 4. Repository Pattern

For data access abstraction.

```python
from typing import List, Optional, Dict, Any
import json
import os

class Repository(ABC):
    @abstractmethod
    async def get(self, id: str) -> Optional[Dict[str, Any]]:
        pass
    
    @abstractmethod
    async def create(self, data: Dict[str, Any]) -> str:
        pass
    
    @abstractmethod
    async def update(self, id: str, data: Dict[str, Any]) -> bool:
        pass
    
    @abstractmethod
    async def delete(self, id: str) -> bool:
        pass
    
    @abstractmethod
    async def list(self, filters: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        pass

class FileRepository(Repository):
    """File-based repository implementation"""
    
    def __init__(self, base_path: str):
        self.base_path = base_path
        os.makedirs(base_path, exist_ok=True)
    
    async def get(self, id: str) -> Optional[Dict[str, Any]]:
        file_path = os.path.join(self.base_path, f"{id}.json")
        if not os.path.exists(file_path):
            return None
        
        with open(file_path, 'r') as f:
            return json.load(f)
    
    async def create(self, data: Dict[str, Any]) -> str:
        id = data.get('id') or generate_uuid()
        data['id'] = id
        
        file_path = os.path.join(self.base_path, f"{id}.json")
        with open(file_path, 'w') as f:
            json.dump(data, f, indent=2)
        
        return id
    
    async def update(self, id: str, data: Dict[str, Any]) -> bool:
        existing = await self.get(id)
        if not existing:
            return False
        
        updated = {**existing, **data}
        file_path = os.path.join(self.base_path, f"{id}.json")
        
        with open(file_path, 'w') as f:
            json.dump(updated, f, indent=2)
        
        return True
    
    async def delete(self, id: str) -> bool:
        file_path = os.path.join(self.base_path, f"{id}.json")
        if os.path.exists(file_path):
            os.remove(file_path)
            return True
        return False
    
    async def list(self, filters: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        results = []
        
        for filename in os.listdir(self.base_path):
            if filename.endswith('.json'):
                with open(os.path.join(self.base_path, filename), 'r') as f:
                    data = json.load(f)
                    
                    if filters:
                        if all(data.get(k) == v for k, v in filters.items()):
                            results.append(data)
                    else:
                        results.append(data)
        
        return results

# Usage
class ProjectService:
    def __init__(self, repository: Repository):
        self.repository = repository
    
    async def create_project(self, name: str, config: dict) -> str:
        project_data = {
            'name': name,
            'config': config,
            'created_at': datetime.now().isoformat(),
            'status': 'active'
        }
        
        return await self.repository.create(project_data)
    
    async def get_active_projects(self) -> List[Dict[str, Any]]:
        return await self.repository.list({'status': 'active'})

# Dependency injection
project_repo = FileRepository('/var/projects')
project_service = ProjectService(project_repo)
```

### 5. Observer Pattern

For event-driven updates.

```python
from typing import Callable, List, Dict, Any
import asyncio
from dataclasses import dataclass

@dataclass
class Event:
    type: str
    data: Dict[str, Any]
    timestamp: float

class Observable:
    def __init__(self):
        self._observers: Dict[str, List[Callable]] = {}
    
    def attach(self, event_type: str, observer: Callable) -> Callable:
        """Attach an observer to an event type"""
        if event_type not in self._observers:
            self._observers[event_type] = []
        
        self._observers[event_type].append(observer)
        
        # Return detach function
        def detach():
            self._observers[event_type].remove(observer)
        
        return detach
    
    async def notify(self, event: Event):
        """Notify all observers of an event"""
        observers = self._observers.get(event.type, [])
        
        # Run observers concurrently
        tasks = [
            self._run_observer(observer, event)
            for observer in observers
        ]
        
        await asyncio.gather(*tasks, return_exceptions=True)
    
    async def _run_observer(self, observer: Callable, event: Event):
        """Run a single observer with error handling"""
        try:
            if asyncio.iscoroutinefunction(observer):
                await observer(event)
            else:
                observer(event)
        except Exception as e:
            logger.error(f"Observer error for {event.type}: {e}")

class WorkflowStateMachine(Observable):
    def __init__(self):
        super().__init__()
        self.state = 'IDLE'
    
    async def transition(self, new_state: str, metadata: dict = None):
        old_state = self.state
        self.state = new_state
        
        event = Event(
            type='state_changed',
            data={
                'old_state': old_state,
                'new_state': new_state,
                'metadata': metadata or {}
            },
            timestamp=time.time()
        )
        
        await self.notify(event)
        
        # Notify specific state events
        state_event = Event(
            type=f'entered_{new_state.lower()}',
            data={'metadata': metadata or {}},
            timestamp=time.time()
        )
        
        await self.notify(state_event)

# Usage
state_machine = WorkflowStateMachine()

# Attach observers
async def log_state_change(event: Event):
    logger.info(f"State changed: {event.data['old_state']} -> {event.data['new_state']}")

async def update_ui(event: Event):
    await broadcast_to_clients({
        'type': 'state_update',
        'state': event.data['new_state']
    })

state_machine.attach('state_changed', log_state_change)
state_machine.attach('state_changed', update_ui)

# Trigger state change
await state_machine.transition('SPRINT_ACTIVE', {'sprint_id': 'sprint-123'})
```

---

## CSS Patterns

### 1. CSS Variable System

Centralized design tokens for consistency.

```css
/* variables.css - Central design system */
:root {
    /* Color Palette */
    --color-primary: #5865F2;
    --color-primary-hover: #4752C4;
    --color-secondary: #57F287;
    --color-danger: #ED4245;
    --color-warning: #FEE75C;
    
    /* Background Colors */
    --bg-primary: #36393F;
    --bg-secondary: #2F3136;
    --bg-tertiary: #202225;
    
    /* Text Colors */
    --text-primary: #FFFFFF;
    --text-secondary: #B9BBBE;
    --text-muted: #72767D;
    
    /* Spacing Scale */
    --spacing-xs: 4px;
    --spacing-sm: 8px;
    --spacing-md: 16px;
    --spacing-lg: 24px;
    --spacing-xl: 32px;
    
    /* Typography */
    --font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto;
    --font-size-sm: 12px;
    --font-size-base: 14px;
    --font-size-lg: 16px;
    --font-size-xl: 20px;
    
    /* Borders */
    --border-radius-sm: 4px;
    --border-radius-md: 8px;
    --border-radius-lg: 12px;
    --border-width: 1px;
    --border-color: rgba(255, 255, 255, 0.1);
    
    /* Transitions */
    --transition-fast: 150ms ease;
    --transition-medium: 250ms ease;
    --transition-slow: 350ms ease;
    
    /* Z-index Scale */
    --z-dropdown: 1000;
    --z-modal: 2000;
    --z-tooltip: 3000;
    --z-notification: 4000;
}

/* Dark theme overrides */
[data-theme="dark"] {
    --bg-primary: #1E1F22;
    --bg-secondary: #2B2D31;
    --bg-tertiary: #313338;
}

/* Usage in components */
.button {
    background: var(--color-primary);
    color: var(--text-primary);
    padding: var(--spacing-sm) var(--spacing-md);
    border-radius: var(--border-radius-sm);
    transition: background var(--transition-fast);
}

.button:hover {
    background: var(--color-primary-hover);
}
```

### 2. Component Isolation Pattern

BEM-like naming with scoped styles.

```css
/* Component root */
.chat-interface {
    display: flex;
    flex-direction: column;
    height: 100%;
    background: var(--bg-primary);
}

/* Component elements */
.chat-interface__header {
    display: flex;
    align-items: center;
    padding: var(--spacing-md);
    border-bottom: var(--border-width) solid var(--border-color);
}

.chat-interface__messages {
    flex: 1;
    overflow-y: auto;
    padding: var(--spacing-md);
}

.chat-interface__input {
    display: flex;
    padding: var(--spacing-md);
    border-top: var(--border-width) solid var(--border-color);
}

/* Component modifiers */
.chat-interface--loading {
    opacity: 0.5;
    pointer-events: none;
}

.chat-interface__message {
    margin-bottom: var(--spacing-sm);
}

.chat-interface__message--user {
    background: var(--color-primary);
    align-self: flex-end;
}

.chat-interface__message--bot {
    background: var(--bg-secondary);
    align-self: flex-start;
}

/* Component states */
.chat-interface__message:hover {
    transform: translateX(2px);
}

.chat-interface__input:focus-within {
    box-shadow: 0 0 0 2px var(--color-primary);
}
```

### 3. Responsive Design Pattern

Mobile-first with progressive enhancement.

```css
/* Base mobile styles */
.container {
    width: 100%;
    padding: var(--spacing-md);
}

.grid {
    display: grid;
    grid-template-columns: 1fr;
    gap: var(--spacing-md);
}

/* Tablet and up */
@media (min-width: 768px) {
    .container {
        max-width: 750px;
        margin: 0 auto;
    }
    
    .grid {
        grid-template-columns: repeat(2, 1fr);
    }
}

/* Desktop and up */
@media (min-width: 1024px) {
    .container {
        max-width: 960px;
    }
    
    .grid {
        grid-template-columns: repeat(3, 1fr);
        gap: var(--spacing-lg);
    }
}

/* Large screens */
@media (min-width: 1440px) {
    .container {
        max-width: 1200px;
    }
}

/* Responsive utilities */
.hide-mobile {
    display: none;
}

@media (min-width: 768px) {
    .hide-mobile {
        display: initial;
    }
    
    .hide-tablet-up {
        display: none;
    }
}
```

### 4. Animation Pattern

Consistent animation system.

```css
/* Keyframe definitions */
@keyframes fadeIn {
    from {
        opacity: 0;
        transform: translateY(10px);
    }
    to {
        opacity: 1;
        transform: translateY(0);
    }
}

@keyframes slideIn {
    from {
        transform: translateX(-100%);
    }
    to {
        transform: translateX(0);
    }
}

@keyframes pulse {
    0%, 100% {
        opacity: 1;
    }
    50% {
        opacity: 0.5;
    }
}

/* Animation utilities */
.animate-fadeIn {
    animation: fadeIn var(--transition-medium) ease-out;
}

.animate-slideIn {
    animation: slideIn var(--transition-slow) ease-out;
}

.animate-pulse {
    animation: pulse 2s ease-in-out infinite;
}

/* Reduce motion support */
@media (prefers-reduced-motion: reduce) {
    *,
    *::before,
    *::after {
        animation-duration: 0.01ms !important;
        animation-iteration-count: 1 !important;
        transition-duration: 0.01ms !important;
    }
}
```

### 5. Nuclear CSS Pattern

Last-resort style enforcement.

```css
/* Nuclear layout enforcement */
.nuclear-layout {
    /* Phase 1: Reset cascade */
    all: initial !important;
    
    /* Phase 2: Force display */
    display: block !important;
    visibility: visible !important;
    opacity: 1 !important;
    
    /* Phase 3: Ensure positioning */
    position: relative !important;
    z-index: 2147483647 !important; /* Maximum z-index */
    
    /* Phase 4: Force dimensions */
    width: 100% !important;
    height: auto !important;
    min-height: 400px !important;
    
    /* Phase 5: Ensure visibility */
    background: var(--bg-primary) !important;
    color: var(--text-primary) !important;
    overflow: visible !important;
}

/* Nuclear fixes for specific issues */
.nuclear-show-diagrams {
    /* Force diagram visibility */
    .diagram-container {
        display: block !important;
        opacity: 1 !important;
        transform: none !important;
        filter: none !important;
    }
    
    /* Remove any overlays */
    &::before,
    &::after {
        display: none !important;
    }
    
    /* Ensure parent visibility */
    * {
        pointer-events: auto !important;
        user-select: auto !important;
    }
}
```

---

## WebSocket Patterns

### 1. Connection Management

Robust connection handling with automatic recovery.

```javascript
class WebSocketConnection {
    constructor(url) {
        this.url = url;
        this.socket = null;
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 5;
        this.reconnectDelay = 1000;
        this.messageQueue = [];
        this.eventHandlers = new Map();
        
        this.connect();
    }
    
    connect() {
        try {
            this.socket = new WebSocket(this.url);
            this.setupEventHandlers();
        } catch (error) {
            this.handleConnectionError(error);
        }
    }
    
    setupEventHandlers() {
        this.socket.onopen = () => {
            console.log('WebSocket connected');
            this.reconnectAttempts = 0;
            this.flushMessageQueue();
            this.emit('connected');
        };
        
        this.socket.onclose = (event) => {
            console.log('WebSocket disconnected', event);
            this.emit('disconnected', event);
            
            if (!event.wasClean) {
                this.attemptReconnect();
            }
        };
        
        this.socket.onerror = (error) => {
            console.error('WebSocket error', error);
            this.emit('error', error);
        };
        
        this.socket.onmessage = (event) => {
            try {
                const data = JSON.parse(event.data);
                this.handleMessage(data);
            } catch (error) {
                console.error('Failed to parse message', error);
            }
        };
    }
    
    attemptReconnect() {
        if (this.reconnectAttempts >= this.maxReconnectAttempts) {
            console.error('Max reconnection attempts reached');
            this.emit('reconnectFailed');
            return;
        }
        
        this.reconnectAttempts++;
        const delay = this.reconnectDelay * Math.pow(2, this.reconnectAttempts - 1);
        
        console.log(`Reconnecting in ${delay}ms (attempt ${this.reconnectAttempts})`);
        
        setTimeout(() => {
            this.connect();
        }, delay);
    }
    
    send(message) {
        if (this.socket && this.socket.readyState === WebSocket.OPEN) {
            this.socket.send(JSON.stringify(message));
        } else {
            // Queue message for sending when connected
            this.messageQueue.push(message);
        }
    }
    
    flushMessageQueue() {
        while (this.messageQueue.length > 0) {
            const message = this.messageQueue.shift();
            this.send(message);
        }
    }
    
    on(event, handler) {
        if (!this.eventHandlers.has(event)) {
            this.eventHandlers.set(event, []);
        }
        this.eventHandlers.get(event).push(handler);
    }
    
    emit(event, data) {
        const handlers = this.eventHandlers.get(event) || [];
        handlers.forEach(handler => {
            try {
                handler(data);
            } catch (error) {
                console.error(`Error in ${event} handler:`, error);
            }
        });
    }
}
```

### 2. Message Protocol

Structured message format with versioning.

```javascript
class MessageProtocol {
    static VERSION = '1.0';
    
    static createMessage(type, payload, metadata = {}) {
        return {
            version: this.VERSION,
            id: generateUUID(),
            type,
            payload,
            metadata: {
                timestamp: Date.now(),
                ...metadata
            }
        };
    }
    
    static createRequest(method, params = {}) {
        return this.createMessage('request', {
            method,
            params
        }, {
            requiresResponse: true
        });
    }
    
    static createResponse(requestId, result, error = null) {
        return this.createMessage('response', {
            result,
            error
        }, {
            requestId
        });
    }
    
    static createEvent(event, data) {
        return this.createMessage('event', {
            event,
            data
        });
    }
    
    static validateMessage(message) {
        if (!message.version || !message.id || !message.type) {
            throw new Error('Invalid message format');
        }
        
        if (message.version !== this.VERSION) {
            console.warn(`Message version mismatch: ${message.version}`);
        }
        
        return true;
    }
}

// Usage
const request = MessageProtocol.createRequest('getProjectState', {
    projectName: 'project-alpha'
});

ws.send(request);

// Handle response
ws.on('message', (message) => {
    if (MessageProtocol.validateMessage(message)) {
        if (message.type === 'response' && message.metadata.requestId === request.id) {
            handleProjectState(message.payload.result);
        }
    }
});
```

---

## Error Handling Patterns

### 1. Layered Error Handling

Multiple levels of error handling for robustness.

```javascript
// Application-level error boundary
window.addEventListener('error', (event) => {
    console.error('Uncaught error:', event.error);
    
    // Log to error tracking service
    if (window.errorTracker) {
        window.errorTracker.logError(event.error, {
            source: 'window.error',
            url: event.filename,
            line: event.lineno,
            column: event.colno
        });
    }
    
    // Show user-friendly error message
    showErrorNotification('An unexpected error occurred');
    
    // Prevent default error handling
    event.preventDefault();
});

window.addEventListener('unhandledrejection', (event) => {
    console.error('Unhandled promise rejection:', event.reason);
    
    if (window.errorTracker) {
        window.errorTracker.logError(event.reason, {
            source: 'unhandledrejection',
            promise: event.promise
        });
    }
    
    showErrorNotification('An operation failed to complete');
    
    event.preventDefault();
});

// Component-level error handling
class ErrorBoundary {
    constructor(component, fallback) {
        this.component = component;
        this.fallback = fallback;
        this.hasError = false;
    }
    
    async execute(operation) {
        try {
            this.hasError = false;
            return await operation();
        } catch (error) {
            this.hasError = true;
            this.handleError(error);
            return this.fallback(error);
        }
    }
    
    handleError(error) {
        console.error(`Error in ${this.component}:`, error);
        
        // Categorize error
        const category = this.categorizeError(error);
        
        // Apply recovery strategy
        switch (category) {
            case 'network':
                this.handleNetworkError(error);
                break;
            case 'validation':
                this.handleValidationError(error);
                break;
            case 'permission':
                this.handlePermissionError(error);
                break;
            default:
                this.handleGenericError(error);
        }
    }
    
    categorizeError(error) {
        if (error instanceof NetworkError || error.code === 'NETWORK_ERROR') {
            return 'network';
        }
        if (error instanceof ValidationError || error.code === 'VALIDATION_ERROR') {
            return 'validation';
        }
        if (error.status === 403 || error.code === 'PERMISSION_DENIED') {
            return 'permission';
        }
        return 'generic';
    }
}
```

### 2. Error Recovery Strategies

```javascript
class ErrorRecovery {
    static strategies = {
        retry: async (operation, options = {}) => {
            const { maxAttempts = 3, delay = 1000, backoff = 2 } = options;
            let lastError;
            
            for (let attempt = 1; attempt <= maxAttempts; attempt++) {
                try {
                    return await operation();
                } catch (error) {
                    lastError = error;
                    
                    if (attempt < maxAttempts) {
                        const waitTime = delay * Math.pow(backoff, attempt - 1);
                        console.log(`Retry attempt ${attempt} in ${waitTime}ms`);
                        await new Promise(resolve => setTimeout(resolve, waitTime));
                    }
                }
            }
            
            throw lastError;
        },
        
        fallback: async (operation, fallbackValue) => {
            try {
                return await operation();
            } catch (error) {
                console.warn('Using fallback value due to error:', error);
                return fallbackValue;
            }
        },
        
        cache: async (operation, cacheKey) => {
            try {
                const result = await operation();
                localStorage.setItem(cacheKey, JSON.stringify(result));
                return result;
            } catch (error) {
                const cached = localStorage.getItem(cacheKey);
                if (cached) {
                    console.warn('Using cached value due to error:', error);
                    return JSON.parse(cached);
                }
                throw error;
            }
        },
        
        queue: async (operation, queueName = 'default') => {
            try {
                return await operation();
            } catch (error) {
                console.warn('Queueing operation for retry:', error);
                
                const queue = JSON.parse(localStorage.getItem(`queue_${queueName}`) || '[]');
                queue.push({
                    operation: operation.toString(),
                    timestamp: Date.now(),
                    error: error.message
                });
                localStorage.setItem(`queue_${queueName}`, JSON.stringify(queue));
                
                throw error;
            }
        }
    };
    
    static async withRecovery(operation, strategy = 'retry', options = {}) {
        const recoveryFn = this.strategies[strategy];
        if (!recoveryFn) {
            throw new Error(`Unknown recovery strategy: ${strategy}`);
        }
        
        return recoveryFn(operation, options);
    }
}

// Usage
const data = await ErrorRecovery.withRecovery(
    () => fetchDataFromAPI(),
    'retry',
    { maxAttempts: 5, delay: 2000 }
);

const config = await ErrorRecovery.withRecovery(
    () => loadConfiguration(),
    'cache',
    'app_config'
);
```

---

## State Management Patterns

### 1. Centralized State Store

Single source of truth for application state.

```javascript
class StateStore {
    constructor(initialState = {}) {
        this.state = initialState;
        this.listeners = new Map();
        this.middleware = [];
    }
    
    getState() {
        // Return immutable copy
        return JSON.parse(JSON.stringify(this.state));
    }
    
    setState(updates) {
        const oldState = this.getState();
        
        // Apply middleware
        let finalUpdates = updates;
        for (const mw of this.middleware) {
            finalUpdates = mw(oldState, finalUpdates);
        }
        
        // Update state
        this.state = { ...this.state, ...finalUpdates };
        
        // Notify listeners
        this.notifyListeners(oldState, this.state);
    }
    
    subscribe(path, listener) {
        if (!this.listeners.has(path)) {
            this.listeners.set(path, new Set());
        }
        
        this.listeners.get(path).add(listener);
        
        // Return unsubscribe function
        return () => {
            this.listeners.get(path).delete(listener);
        };
    }
    
    notifyListeners(oldState, newState) {
        // Check each path for changes
        this.listeners.forEach((listeners, path) => {
            const oldValue = this.getValueAtPath(oldState, path);
            const newValue = this.getValueAtPath(newState, path);
            
            if (oldValue !== newValue) {
                listeners.forEach(listener => {
                    try {
                        listener(newValue, oldValue);
                    } catch (error) {
                        console.error('Listener error:', error);
                    }
                });
            }
        });
    }
    
    getValueAtPath(obj, path) {
        return path.split('.').reduce((curr, key) => curr?.[key], obj);
    }
    
    use(middleware) {
        this.middleware.push(middleware);
    }
}

// Middleware example
const loggingMiddleware = (oldState, updates) => {
    console.log('State update:', updates);
    return updates;
};

const validationMiddleware = (oldState, updates) => {
    if (updates.user && !updates.user.id) {
        throw new Error('User must have an ID');
    }
    return updates;
};

// Usage
const store = new StateStore({
    user: null,
    projects: [],
    currentProject: null
});

store.use(loggingMiddleware);
store.use(validationMiddleware);

// Subscribe to changes
const unsubscribe = store.subscribe('currentProject', (newProject, oldProject) => {
    console.log(`Project changed from ${oldProject} to ${newProject}`);
    updateUIForProject(newProject);
});

// Update state
store.setState({
    currentProject: 'project-alpha'
});
```

### 2. Action-Based Updates

Predictable state updates through actions.

```javascript
class ActionTypes {
    static PROJECT_SELECTED = 'PROJECT_SELECTED';
    static PROJECT_CREATED = 'PROJECT_CREATED';
    static PROJECT_DELETED = 'PROJECT_DELETED';
    static USER_LOGGED_IN = 'USER_LOGGED_IN';
    static USER_LOGGED_OUT = 'USER_LOGGED_OUT';
}

class Actions {
    static selectProject(projectId) {
        return {
            type: ActionTypes.PROJECT_SELECTED,
            payload: { projectId }
        };
    }
    
    static createProject(project) {
        return {
            type: ActionTypes.PROJECT_CREATED,
            payload: { project }
        };
    }
    
    static loginUser(user) {
        return {
            type: ActionTypes.USER_LOGGED_IN,
            payload: { user }
        };
    }
}

class StateManager {
    constructor(initialState, reducer) {
        this.state = initialState;
        this.reducer = reducer;
        this.listeners = [];
    }
    
    dispatch(action) {
        console.log('Dispatching:', action);
        
        const oldState = this.state;
        this.state = this.reducer(oldState, action);
        
        if (oldState !== this.state) {
            this.notifyListeners();
        }
    }
    
    subscribe(listener) {
        this.listeners.push(listener);
        return () => {
            this.listeners = this.listeners.filter(l => l !== listener);
        };
    }
    
    notifyListeners() {
        this.listeners.forEach(listener => listener(this.state));
    }
    
    getState() {
        return this.state;
    }
}

// Reducer
function appReducer(state, action) {
    switch (action.type) {
        case ActionTypes.PROJECT_SELECTED:
            return {
                ...state,
                currentProject: action.payload.projectId
            };
            
        case ActionTypes.PROJECT_CREATED:
            return {
                ...state,
                projects: [...state.projects, action.payload.project]
            };
            
        case ActionTypes.USER_LOGGED_IN:
            return {
                ...state,
                user: action.payload.user,
                isAuthenticated: true
            };
            
        case ActionTypes.USER_LOGGED_OUT:
            return {
                ...state,
                user: null,
                isAuthenticated: false
            };
            
        default:
            return state;
    }
}

// Usage
const stateManager = new StateManager(
    {
        user: null,
        isAuthenticated: false,
        projects: [],
        currentProject: null
    },
    appReducer
);

// Subscribe to state changes
stateManager.subscribe((state) => {
    console.log('State updated:', state);
    updateUI(state);
});

// Dispatch actions
stateManager.dispatch(Actions.loginUser({ id: 'user123', name: 'John' }));
stateManager.dispatch(Actions.selectProject('project-alpha'));
```

---

## Security Patterns

### 1. Input Sanitization

Comprehensive input validation and sanitization.

```javascript
class InputSanitizer {
    static sanitizeHTML(input) {
        const div = document.createElement('div');
        div.textContent = input;
        return div.innerHTML;
    }
    
    static sanitizeCommand(command) {
        // Remove potentially dangerous characters
        return command
            .replace(/[<>]/g, '')  // Remove HTML brackets
            .replace(/[&]/g, '')   // Remove ampersands
            .replace(/[;|]/g, '')  // Remove command separators
            .trim();
    }
    
    static validateEmail(email) {
        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        return emailRegex.test(email);
    }
    
    static validateProjectName(name) {
        // Alphanumeric, hyphens, underscores only
        const projectRegex = /^[a-zA-Z0-9-_]+$/;
        return projectRegex.test(name) && name.length >= 3 && name.length <= 50;
    }
    
    static sanitizeJSON(jsonString) {
        try {
            const parsed = JSON.parse(jsonString);
            // Remove any functions or undefined values
            return JSON.parse(JSON.stringify(parsed));
        } catch {
            throw new Error('Invalid JSON input');
        }
    }
    
    static createSafeURL(url) {
        try {
            const parsed = new URL(url);
            
            // Only allow safe protocols
            if (!['http:', 'https:'].includes(parsed.protocol)) {
                throw new Error('Unsafe protocol');
            }
            
            return parsed.href;
        } catch {
            throw new Error('Invalid URL');
        }
    }
}

// Usage
const sanitizedCommand = InputSanitizer.sanitizeCommand(userInput);
const safeHTML = InputSanitizer.sanitizeHTML(userContent);

if (!InputSanitizer.validateProjectName(projectName)) {
    throw new ValidationError('Invalid project name');
}
```

### 2. CSRF Protection

```python
from flask_wtf.csrf import CSRFProtect, generate_csrf
from functools import wraps

csrf = CSRFProtect(app)

# Custom CSRF validation for AJAX
def validate_csrf_ajax(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        token = request.headers.get('X-CSRF-Token')
        
        if not token:
            abort(403, 'CSRF token missing')
        
        try:
            csrf.protect()
        except:
            abort(403, 'Invalid CSRF token')
        
        return f(*args, **kwargs)
    return decorated_function

# In templates
@app.context_processor
def inject_csrf_token():
    return dict(csrf_token=generate_csrf)

# Client-side
class SecurityHeaders {
    static getCSRFToken() {
        return document.querySelector('meta[name="csrf-token"]')?.content;
    }
    
    static getSecureHeaders() {
        return {
            'Content-Type': 'application/json',
            'X-CSRF-Token': this.getCSRFToken(),
            'X-Requested-With': 'XMLHttpRequest'
        };
    }
}

// Usage in fetch
fetch('/api/command', {
    method: 'POST',
    headers: SecurityHeaders.getSecureHeaders(),
    body: JSON.stringify(data)
});
```

---

## Testing Patterns

### 1. Unit Testing Pattern

```javascript
// Test structure
describe('ProjectManager', () => {
    let projectManager;
    let mockAPI;
    
    beforeEach(() => {
        // Setup
        mockAPI = {
            getProjects: jest.fn(),
            createProject: jest.fn(),
            updateProject: jest.fn()
        };
        
        projectManager = new ProjectManager(mockAPI);
    });
    
    afterEach(() => {
        // Cleanup
        jest.clearAllMocks();
    });
    
    describe('loadProjects', () => {
        it('should load projects from API', async () => {
            // Arrange
            const mockProjects = [
                { id: '1', name: 'Project 1' },
                { id: '2', name: 'Project 2' }
            ];
            mockAPI.getProjects.mockResolvedValue(mockProjects);
            
            // Act
            await projectManager.loadProjects();
            
            // Assert
            expect(mockAPI.getProjects).toHaveBeenCalledTimes(1);
            expect(projectManager.projects.size).toBe(2);
            expect(projectManager.projects.get('1')).toEqual(mockProjects[0]);
        });
        
        it('should handle API errors gracefully', async () => {
            // Arrange
            const error = new Error('API Error');
            mockAPI.getProjects.mockRejectedValue(error);
            
            // Act
            await projectManager.loadProjects();
            
            // Assert
            expect(projectManager.projects.size).toBe(0);
            expect(projectManager.error).toBe(error.message);
        });
    });
    
    describe('createProject', () => {
        it('should validate project data before creation', async () => {
            // Arrange
            const invalidProject = { name: '' }; // Missing required fields
            
            // Act & Assert
            await expect(projectManager.createProject(invalidProject))
                .rejects.toThrow('Invalid project data');
            
            expect(mockAPI.createProject).not.toHaveBeenCalled();
        });
    });
});
```

### 2. Integration Testing Pattern

```python
import pytest
from unittest.mock import patch, MagicMock
import asyncio

class TestChatIntegration:
    @pytest.fixture
    def app(self):
        """Create test app instance"""
        from app import create_app
        app = create_app(testing=True)
        return app
    
    @pytest.fixture
    def client(self, app):
        """Create test client"""
        return app.test_client()
    
    @pytest.fixture
    def authenticated_client(self, client):
        """Create authenticated test client"""
        with client.session_transaction() as sess:
            sess['user_id'] = 'test_user'
            sess['project'] = 'test_project'
        return client
    
    @pytest.mark.asyncio
    async def test_chat_command_flow(self, authenticated_client):
        """Test complete chat command flow"""
        # Send command
        response = authenticated_client.post('/api/chat/send', json={
            'message': '/epic "Test epic"',
            'project_name': 'test_project'
        })
        
        assert response.status_code == 200
        data = response.get_json()
        
        assert data['success'] is True
        assert data['message']['type'] == 'bot'
        assert 'created' in data['message']['content'].lower()
    
    @pytest.mark.asyncio
    @patch('app.orchestrator')
    async def test_command_processing_with_orchestrator(self, mock_orchestrator, authenticated_client):
        """Test command processing with mocked orchestrator"""
        # Setup mock
        mock_orchestrator.process_command.return_value = {
            'success': True,
            'result': 'Epic created successfully'
        }
        
        # Send command
        response = authenticated_client.post('/api/chat/send', json={
            'message': '/epic "Test epic"',
            'project_name': 'test_project'
        })
        
        # Verify orchestrator was called correctly
        mock_orchestrator.process_command.assert_called_once_with(
            '/epic "Test epic"',
            project_name='test_project',
            user_id='test_user'
        )
        
        assert response.status_code == 200
```

---

## Performance Patterns

### 1. Debouncing and Throttling

```javascript
// Debounce - delays execution until after wait period of inactivity
function debounce(func, wait) {
    let timeoutId;
    
    return function debounced(...args) {
        clearTimeout(timeoutId);
        
        timeoutId = setTimeout(() => {
            func.apply(this, args);
        }, wait);
    };
}

// Throttle - ensures function is called at most once per wait period
function throttle(func, wait) {
    let lastCallTime = 0;
    let timeoutId;
    
    return function throttled(...args) {
        const now = Date.now();
        const timeSinceLastCall = now - lastCallTime;
        
        if (timeSinceLastCall >= wait) {
            lastCallTime = now;
            func.apply(this, args);
        } else {
            clearTimeout(timeoutId);
            timeoutId = setTimeout(() => {
                lastCallTime = Date.now();
                func.apply(this, args);
            }, wait - timeSinceLastCall);
        }
    };
}

// Advanced debounce with immediate option
function advancedDebounce(func, wait, immediate = false) {
    let timeoutId;
    
    return function debounced(...args) {
        const callNow = immediate && !timeoutId;
        
        clearTimeout(timeoutId);
        
        timeoutId = setTimeout(() => {
            timeoutId = null;
            if (!immediate) {
                func.apply(this, args);
            }
        }, wait);
        
        if (callNow) {
            func.apply(this, args);
        }
    };
}

// Usage
const debouncedSearch = debounce((query) => {
    performSearch(query);
}, 300);

const throttledScroll = throttle(() => {
    updateScrollPosition();
}, 100);

searchInput.addEventListener('input', (e) => {
    debouncedSearch(e.target.value);
});

window.addEventListener('scroll', throttledScroll);
```

### 2. Lazy Loading

```javascript
// Lazy load components
class LazyLoader {
    static components = new Map();
    
    static register(name, loader) {
        this.components.set(name, {
            loader,
            loaded: false,
            component: null
        });
    }
    
    static async load(name) {
        const entry = this.components.get(name);
        
        if (!entry) {
            throw new Error(`Unknown component: ${name}`);
        }
        
        if (!entry.loaded) {
            console.log(`Lazy loading ${name}...`);
            entry.component = await entry.loader();
            entry.loaded = true;
        }
        
        return entry.component;
    }
}

// Register components
LazyLoader.register('Analytics', () => import('./analytics.js'));
LazyLoader.register('RichEditor', () => import('./rich-editor.js'));
LazyLoader.register('Charts', () => import('./charts.js'));

// Usage
async function showAnalytics() {
    const { Analytics } = await LazyLoader.load('Analytics');
    const analytics = new Analytics();
    analytics.show();
}

// Intersection Observer for lazy loading
class LazyImageLoader {
    constructor() {
        this.imageObserver = new IntersectionObserver(
            this.handleIntersection.bind(this),
            {
                rootMargin: '50px 0px',
                threshold: 0.01
            }
        );
    }
    
    observe(element) {
        this.imageObserver.observe(element);
    }
    
    handleIntersection(entries) {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                const img = entry.target;
                const src = img.dataset.src;
                
                if (src) {
                    img.src = src;
                    img.removeAttribute('data-src');
                    this.imageObserver.unobserve(img);
                }
            }
        });
    }
}

// Usage
const imageLoader = new LazyImageLoader();
document.querySelectorAll('img[data-src]').forEach(img => {
    imageLoader.observe(img);
});
```

### 3. Memory Management

```javascript
// Object pooling for frequent allocations
class ObjectPool {
    constructor(factory, reset, maxSize = 100) {
        this.factory = factory;
        this.reset = reset;
        this.maxSize = maxSize;
        this.pool = [];
    }
    
    acquire() {
        if (this.pool.length > 0) {
            return this.pool.pop();
        }
        return this.factory();
    }
    
    release(obj) {
        if (this.pool.length < this.maxSize) {
            this.reset(obj);
            this.pool.push(obj);
        }
    }
    
    clear() {
        this.pool = [];
    }
}

// Usage
const messagePool = new ObjectPool(
    () => ({ id: '', content: '', timestamp: 0 }),
    (msg) => {
        msg.id = '';
        msg.content = '';
        msg.timestamp = 0;
    }
);

// Memory-efficient data structures
class CircularBuffer {
    constructor(size) {
        this.size = size;
        this.buffer = new Array(size);
        this.head = 0;
        this.tail = 0;
        this.count = 0;
    }
    
    push(item) {
        this.buffer[this.head] = item;
        this.head = (this.head + 1) % this.size;
        
        if (this.count < this.size) {
            this.count++;
        } else {
            this.tail = (this.tail + 1) % this.size;
        }
    }
    
    toArray() {
        const result = [];
        let index = this.tail;
        
        for (let i = 0; i < this.count; i++) {
            result.push(this.buffer[index]);
            index = (index + 1) % this.size;
        }
        
        return result;
    }
}

// Weak references for caching
class WeakCache {
    constructor() {
        this.cache = new WeakMap();
    }
    
    get(key) {
        return this.cache.get(key);
    }
    
    set(key, value) {
        this.cache.set(key, value);
    }
    
    has(key) {
        return this.cache.has(key);
    }
}
```

---

## Anti-Patterns to Avoid

### 1. Callback Hell

**Bad:**
```javascript
getData(function(a) {
    getMoreData(a, function(b) {
        getMoreData(b, function(c) {
            getMoreData(c, function(d) {
                console.log(d);
            });
        });
    });
});
```

**Good:**
```javascript
async function processData() {
    try {
        const a = await getData();
        const b = await getMoreData(a);
        const c = await getMoreData(b);
        const d = await getMoreData(c);
        console.log(d);
    } catch (error) {
        handleError(error);
    }
}
```

### 2. God Objects

**Bad:**
```javascript
class AppManager {
    constructor() {
        this.users = [];
        this.projects = [];
        this.database = null;
        this.api = null;
        this.ui = null;
        this.websocket = null;
        // ... 100 more properties
    }
    
    loginUser() { /* ... */ }
    createProject() { /* ... */ }
    updateDatabase() { /* ... */ }
    renderUI() { /* ... */ }
    handleWebSocket() { /* ... */ }
    // ... 200 more methods
}
```

**Good:**
```javascript
// Separate concerns
class UserManager {
    constructor(api) {
        this.api = api;
        this.users = [];
    }
    
    async login(credentials) { /* ... */ }
    async logout() { /* ... */ }
}

class ProjectManager {
    constructor(api) {
        this.api = api;
        this.projects = [];
    }
    
    async create(data) { /* ... */ }
    async update(id, data) { /* ... */ }
}

// Compose in main app
class App {
    constructor() {
        this.userManager = new UserManager(api);
        this.projectManager = new ProjectManager(api);
    }
}
```

### 3. Premature Optimization

**Bad:**
```javascript
// Over-optimized for a simple case
const cache = new Map();
const weakCache = new WeakMap();
const memoizedResults = {};

function calculateSimpleSum(a, b) {
    const key = `${a}_${b}`;
    
    // Check multiple caches
    if (cache.has(key)) return cache.get(key);
    if (key in memoizedResults) return memoizedResults[key];
    
    // Bitwise optimization for simple addition
    const result = (a ^ b) + ((a & b) << 1);
    
    // Store in multiple caches
    cache.set(key, result);
    memoizedResults[key] = result;
    
    return result;
}
```

**Good:**
```javascript
// Simple and clear
function calculateSimpleSum(a, b) {
    return a + b;
}

// Add caching only when profiling shows it's needed
const memoize = (fn) => {
    const cache = new Map();
    
    return (...args) => {
        const key = JSON.stringify(args);
        if (cache.has(key)) {
            return cache.get(key);
        }
        
        const result = fn(...args);
        cache.set(key, result);
        return result;
    };
};
```

### 4. Ignoring Error Cases

**Bad:**
```javascript
async function fetchUserData(userId) {
    const response = await fetch(`/api/users/${userId}`);
    const data = await response.json();
    return data.user;  // Assumes success
}
```

**Good:**
```javascript
async function fetchUserData(userId) {
    try {
        const response = await fetch(`/api/users/${userId}`);
        
        if (!response.ok) {
            throw new APIError(
                `Failed to fetch user: ${response.status}`,
                response.status
            );
        }
        
        const data = await response.json();
        
        if (!data.user) {
            throw new DataError('User data missing in response');
        }
        
        return data.user;
    } catch (error) {
        if (error instanceof APIError) {
            // Handle API errors
            logger.error('API Error:', error);
            throw error;
        } else if (error instanceof TypeError) {
            // Network error
            throw new NetworkError('Network request failed', error);
        } else {
            // Unknown error
            throw new Error('Unexpected error fetching user data', { cause: error });
        }
    }
}
```

---

This comprehensive guide to code patterns and best practices should help maintain consistency and quality across the AI Agent Workflow Visualizer codebase. Remember:

1. **Consistency** is more important than perfection
2. **Readability** trumps cleverness
3. **Test** your patterns thoroughly
4. **Document** why, not just what
5. **Refactor** when patterns no longer fit

Use these patterns as guidelines, not rigid rules. Adapt them to fit the specific needs of each situation.