# Error Handling Integration Guide

This guide shows how to integrate the unified error handling system into existing components across the visualizer application.

## Quick Start

### JavaScript Integration

```javascript
// Add to your HTML head
<script src="/static/js/error-manager.js"></script>
<script src="/static/js/error-notifications.js"></script>

// In your component initialization
const errorManager = window.ErrorManager;
const notificationSystem = window.ErrorNotificationSystem;

// Replace existing try-catch blocks
try {
    await this.loadProjects();
} catch (error) {
    const result = errorManager.handleError(error, {
        component: 'ProjectManager',
        operation: 'loadProjects',
        type: 'api_call'
    });
    
    // Error notification is automatically shown
    // Optional: Add custom handling
    if (!result.recoveryResult.successful) {
        console.log('Recovery failed, custom handling needed');
    }
}
```

### Python Integration

```python
# Add to your imports
from lib.error_manager import get_error_manager, handle_errors, ErrorHandler, ErrorContext

# Get error manager for your component
error_manager = get_error_manager('MyComponent')

# Option 1: Context manager
with ErrorHandler('MyComponent', 'load_data') as handler:
    data = load_data_from_api()
    
# Option 2: Decorator
@handle_errors('MyComponent', user_message='Failed to process data')
def process_data(data):
    return complex_processing(data)

# Option 3: Manual handling
try:
    result = risky_operation()
except Exception as e:
    error_record = error_manager.handle_error(e, ErrorContext(
        component='MyComponent',
        operation='risky_operation',
        additional_data={'param': 'value'}
    ))
```

## Component-Specific Integration Examples

### 1. Project Manager (JavaScript)

**Before:**
```javascript
async loadProjects() {
    try {
        const response = await fetch('/api/projects');
        if (response.ok) {
            const data = await response.json();
            this.projects.clear();
            // ... process data
        } else {
            console.error('Failed to load projects:', response.status);
        }
    } catch (error) {
        console.error('❌ Failed to initialize ProjectManager:', error);
    }
}
```

**After:**
```javascript
async loadProjects() {
    try {
        const response = await fetch('/api/projects');
        if (response.ok) {
            const data = await response.json();
            this.projects.clear();
            // ... process data
        } else {
            throw new Error(`API returned ${response.status}: ${response.statusText}`);
        }
    } catch (error) {
        const result = window.ErrorManager.handleError(error, {
            component: 'ProjectManager',
            operation: 'loadProjects',
            type: 'api_call',
            endpoint: '/api/projects'
        });
        
        // Handle recovery if needed
        if (result.recoveryResult.strategy === 'fallback') {
            this.loadFallbackProjects();
        }
    }
}

// Register recovery handlers
window.addEventListener('errorRetry', (event) => {
    if (event.detail.errorRecord.context.component === 'ProjectManager' &&
        event.detail.errorRecord.context.operation === 'loadProjects') {
        setTimeout(() => this.loadProjects(), event.detail.delay || 1000);
    }
});

window.addEventListener('errorFallback', (event) => {
    if (event.detail.errorRecord.context.component === 'ProjectManager') {
        this.loadFallbackProjects();
    }
});
```

### 2. Discord Chat (JavaScript)

**Before:**
```javascript
loadProjectData() {
    try {
        const storedChatHistory = localStorage.getItem('agent_workflow_chat_history');
        if (storedChatHistory) {
            const data = JSON.parse(storedChatHistory);
            this.projectChatHistory = new Map(Object.entries(data));
        }
    } catch (error) {
        console.warn('Failed to load project data from localStorage:', error);
    }
}
```

**After:**
```javascript
loadProjectData() {
    try {
        const storedChatHistory = localStorage.getItem('agent_workflow_chat_history');
        if (storedChatHistory) {
            const data = JSON.parse(storedChatHistory);
            this.projectChatHistory = new Map(Object.entries(data));
        }
    } catch (error) {
        const result = window.ErrorManager.handleError(error, {
            component: 'DiscordChat',
            operation: 'loadProjectData',
            type: 'storage'
        });
        
        // Use fallback storage if localStorage fails
        if (result.recoveryResult.strategy === 'fallback') {
            this.useMemoryStorage();
        }
    }
}

// Register storage fallback handler
window.addEventListener('errorFallback', (event) => {
    if (event.detail.errorRecord.context.component === 'DiscordChat' &&
        event.detail.errorRecord.context.type === 'storage') {
        this.useMemoryStorage();
    }
});

useMemoryStorage() {
    console.log('🔄 Using memory storage as fallback');
    this.projectChatHistory = new Map();
    this.usingMemoryStorage = true;
    
    // Show user notification about degraded functionality
    window.dispatchEvent(new CustomEvent('errorNotification', {
        detail: {
            displayInfo: {
                title: 'Storage Unavailable',
                message: 'Chat history will not persist across sessions.',
                severity: 'warning',
                actions: [
                    {
                        label: 'Dismiss',
                        action: () => {},
                        primary: false
                    }
                ]
            }
        }
    }));
}
```

### 3. State Visualizer (JavaScript)

**Before:**
```javascript
initializeSocketIO() {
    try {
        if (typeof io === 'undefined') {
            throw new Error('Socket.IO library not loaded - check CDN connectivity');
        }
        
        this.socket = io({
            transports: ['websocket', 'polling'],
            upgrade: true,
            rememberUpgrade: true,
            timeout: 10000
        });
        
        this.socket.on('connect_error', (error) => {
            console.error('Connection error:', error);
            this.connected = false;
            this.updateConnectionStatus(false);
            this.addActivityLog('System', `Connection error: ${error.message}`, 'error');
        });
    } catch (e) {
        console.warn('Socket.IO initialization failed:', e);
    }
}
```

**After:**
```javascript
initializeSocketIO() {
    try {
        if (typeof io === 'undefined') {
            throw new Error('Socket.IO library not loaded - check CDN connectivity');
        }
        
        this.socket = io({
            transports: ['websocket', 'polling'],
            upgrade: true,
            rememberUpgrade: true,
            timeout: 10000
        });
        
        this.socket.on('connect_error', (error) => {
            window.ErrorManager.handleError(error, {
                component: 'StateVisualizer',
                operation: 'websocket_connection',
                type: 'websocket'
            });
        });
        
        this.socket.on('disconnect', (reason) => {
            window.ErrorManager.handleError(new Error(`Disconnected: ${reason}`), {
                component: 'StateVisualizer',
                operation: 'websocket_connection',
                type: 'websocket'
            });
        });
        
    } catch (error) {
        const result = window.ErrorManager.handleError(error, {
            component: 'StateVisualizer',
            operation: 'initializeSocketIO',
            type: 'initialization'
        });
        
        if (result.recoveryResult.strategy === 'fallback') {
            this.useFallbackMode();
        }
    }
}

// Register WebSocket recovery handlers
window.addEventListener('errorRetry', (event) => {
    if (event.detail.errorRecord.context.type === 'websocket') {
        setTimeout(() => this.attemptReconnection(), event.detail.delay || 1000);
    }
});

useFallbackMode() {
    console.log('🔄 Using fallback mode without real-time updates');
    this.fallbackMode = true;
    this.startPollingMode();
}
```

### 4. Flask App (Python)

**Before:**
```python
@app.route('/api/projects')
def get_projects():
    try:
        projects = []
        for project in multi_project_manager.list_projects():
            project_state = load_project_state(project.name, project.path)
            # ... process project data
        return jsonify({"projects": projects})
    except Exception as e:
        logger.error(f"Get projects error: {e}")
        return jsonify({"error": "Failed to load projects"}), 500
```

**After:**
```python
from lib.error_manager import get_error_manager, ErrorContext

error_manager = get_error_manager('FlaskApp')

@app.route('/api/projects')
def get_projects():
    try:
        projects = []
        for project in multi_project_manager.list_projects():
            project_state = load_project_state(project.name, project.path)
            # ... process project data
        return jsonify({"projects": projects})
    except Exception as e:
        error_record = error_manager.handle_error(e, ErrorContext(
            component='FlaskApp',
            operation='get_projects',
            user_id=session.get('user_id'),
            session_id=session.get('session_id'),
            additional_data={'endpoint': '/api/projects'}
        ))
        
        # Return structured error response
        return jsonify({
            "error": error_record.user_message,
            "error_code": error_record.error_code.value,
            "error_id": error_record.id,
            "recovery_available": error_record.recovery_result.successful if error_record.recovery_result else False
        }), 500

# Register recovery handlers
def handle_api_retry(error_record, attempt_number, delay):
    """Handle API endpoint retry logic"""
    if error_record.context.operation == 'get_projects':
        # Log retry attempt
        logger.info(f"Retrying get_projects API call (attempt {attempt_number})")

error_manager.register_recovery_handler(RecoveryStrategy.RETRY, handle_api_retry)
```

### 5. Command Processor (Python)

**Before:**
```python
def __init__(self):
    if ORCHESTRATOR_AVAILABLE:
        try:
            self.orchestrator = Orchestrator()
            logger.info("Command processor initialized with orchestrator")
        except Exception as e:
            logger.error(f"Failed to initialize orchestrator: {e}")
            self.orchestrator = None
```

**After:**
```python
from lib.error_manager import get_error_manager, ErrorHandler, ErrorContext

def __init__(self):
    self.error_manager = get_error_manager('CommandProcessor')
    
    if ORCHESTRATOR_AVAILABLE:
        with ErrorHandler('CommandProcessor', 'initialize_orchestrator') as handler:
            self.orchestrator = Orchestrator()
            logger.info("Command processor initialized with orchestrator")
        
        if handler.get_error_record():
            # Handle initialization failure
            error_record = handler.get_error_record()
            if error_record.recovery_result.strategy == RecoveryStrategy.FALLBACK:
                self.orchestrator = MockOrchestrator()
                logger.info("Using mock orchestrator as fallback")
            else:
                self.orchestrator = None

# Register recovery handlers
def handle_orchestrator_fallback(error_record):
    """Provide mock orchestrator when real one fails"""
    if error_record.context.operation == 'initialize_orchestrator':
        return True  # Indicates fallback handled
    return False

self.error_manager.register_recovery_handler(RecoveryStrategy.FALLBACK, handle_orchestrator_fallback)
```

## Error Handling Best Practices

### 1. **Always Provide Context**
```javascript
// Good
window.ErrorManager.handleError(error, {
    component: 'ProjectManager',
    operation: 'loadProjects',
    type: 'api_call',
    endpoint: '/api/projects',
    userId: this.userId
});

// Bad
window.ErrorManager.handleError(error);
```

### 2. **Use Appropriate User Messages**
```python
# Good
error_manager.handle_error(e, context, user_message="Unable to save your changes. Please try again.")

# Bad
error_manager.handle_error(e, context, user_message="Database connection failed with error 1042")
```

### 3. **Register Recovery Handlers**
```javascript
// Register component-specific recovery logic
window.addEventListener('errorRetry', (event) => {
    const { errorRecord, attemptNumber } = event.detail;
    if (errorRecord.context.component === 'MyComponent') {
        this.handleRetry(errorRecord, attemptNumber);
    }
});

window.addEventListener('errorFallback', (event) => {
    const { errorRecord } = event.detail;
    if (errorRecord.context.component === 'MyComponent') {
        this.activateFallbackMode();
    }
});
```

### 4. **Implement Graceful Degradation**
```javascript
activateFallbackMode() {
    this.fallbackMode = true;
    this.disableAdvancedFeatures();
    this.showDegradedModeNotification();
}

showDegradedModeNotification() {
    window.dispatchEvent(new CustomEvent('errorNotification', {
        detail: {
            displayInfo: {
                title: 'Limited Functionality',
                message: 'Some features are temporarily unavailable. Core functionality remains active.',
                severity: 'warning',
                actions: [
                    {
                        label: 'Refresh to Restore',
                        action: () => window.location.reload(),
                        primary: true
                    },
                    {
                        label: 'Continue',
                        action: () => {},
                        primary: false
                    }
                ]
            }
        }
    }));
}
```

### 5. **Monitor Error Patterns**
```python
# Periodically check error statistics
def monitor_error_health():
    stats = error_manager.get_error_stats()
    
    if stats['total_errors'] > 100:  # Too many errors
        logger.warning("High error rate detected")
        
    if stats['recovery_success_rate'] < 50:  # Low recovery rate
        logger.error("Low recovery success rate")
        
    # Check for recurring error patterns
    for error_code, count in stats['error_code_breakdown'].items():
        if count > 10:  # Recurring error
            logger.warning(f"Recurring error pattern: {error_code} ({count} times)")

# Schedule periodic monitoring
import threading
threading.Timer(300, monitor_error_health).start()  # Every 5 minutes
```

## Testing Error Handling

### 1. **Error Injection Testing**
```javascript
// Test error handling by injecting errors
function testErrorHandling() {
    // Test network errors
    window.ErrorManager.handleError(new Error('Network failed'), {
        component: 'TestComponent',
        operation: 'test_network',
        type: 'network'
    });
    
    // Test storage errors
    window.ErrorManager.handleError(new DOMException('Quota exceeded', 'QuotaExceededError'), {
        component: 'TestComponent',
        operation: 'test_storage',
        type: 'storage'
    });
    
    // Check error statistics
    const stats = window.ErrorManager.getErrorStats();
    console.log('Error stats:', stats);
}
```

### 2. **Recovery Testing**
```python
def test_recovery_mechanisms():
    error_manager = get_error_manager('TestComponent')
    
    # Test retry mechanism
    test_error = ConnectionError("Test connection failure")
    error_record = error_manager.handle_error(test_error, ErrorContext(
        component='TestComponent',
        operation='test_retry'
    ))
    
    assert error_record.recovery_result.strategy == RecoveryStrategy.RETRY
    assert error_record.recovery_result.attempted == True
    
    # Test fallback mechanism
    test_error = ImportError("Test import failure")
    error_record = error_manager.handle_error(test_error, ErrorContext(
        component='TestComponent',
        operation='test_fallback'
    ))
    
    assert error_record.recovery_result.strategy == RecoveryStrategy.FALLBACK
```

## Deployment Checklist

### 1. **JavaScript Files**
- [ ] Add error-manager.js to HTML templates
- [ ] Add error-notifications.js to HTML templates
- [ ] Update existing try-catch blocks
- [ ] Register component-specific recovery handlers
- [ ] Test error notifications in different browsers

### 2. **Python Files**
- [ ] Import error_manager in affected modules
- [ ] Replace existing exception handling
- [ ] Register recovery handlers for critical operations
- [ ] Add error handling to API endpoints
- [ ] Test recovery mechanisms

### 3. **Configuration**
- [ ] Configure external logging services
- [ ] Set up error monitoring dashboards
- [ ] Configure alerting thresholds
- [ ] Set up error history export scheduled tasks

### 4. **Documentation**
- [ ] Update component documentation with error handling
- [ ] Document recovery strategies for each component
- [ ] Create error troubleshooting guides
- [ ] Document monitoring and alerting procedures

## Troubleshooting Common Issues

### 1. **Error Manager Not Loaded**
```javascript
// Check if error manager is available
if (typeof window.ErrorManager === 'undefined') {
    console.error('ErrorManager not loaded - check script inclusion');
    // Fallback to basic error handling
}
```

### 2. **Recovery Handlers Not Firing**
```javascript
// Ensure handlers are registered after ErrorManager is loaded
document.addEventListener('DOMContentLoaded', () => {
    // Register recovery handlers here
    window.addEventListener('errorRetry', handleRetry);
    window.addEventListener('errorFallback', handleFallback);
});
```

### 3. **Python Import Issues**
```python
# Handle missing error manager gracefully
try:
    from lib.error_manager import get_error_manager
    error_manager = get_error_manager('MyComponent')
except ImportError:
    # Fallback to basic logging
    import logging
    logger = logging.getLogger(__name__)
    
    def handle_error_fallback(error, context=None):
        logger.error(f"Error in {context or 'unknown'}: {error}")
```

This integration guide provides a comprehensive approach to implementing the unified error handling system across the visualizer application, ensuring consistent error management and improved user experience.