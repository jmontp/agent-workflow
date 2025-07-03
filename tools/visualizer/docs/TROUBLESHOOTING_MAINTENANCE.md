# Troubleshooting & Maintenance Guide
## AI Agent Workflow Visualizer

This guide provides practical troubleshooting steps, maintenance procedures, and diagnostic tools for engineers maintaining the AI Agent Workflow Visualizer.

---

## Table of Contents

1. [Common Issues & Solutions](#common-issues--solutions)
2. [Diagnostic Tools](#diagnostic-tools)
3. [Performance Troubleshooting](#performance-troubleshooting)
4. [WebSocket Issues](#websocket-issues)
5. [Multi-Project Issues](#multi-project-issues)
6. [Browser-Specific Issues](#browser-specific-issues)
7. [Maintenance Procedures](#maintenance-procedures)
8. [Log Analysis](#log-analysis)
9. [Recovery Procedures](#recovery-procedures)
10. [Health Monitoring](#health-monitoring)

---

## Common Issues & Solutions

### 1. Changes Not Reflecting After Code Update

**Symptoms**: 
- Code changes don't appear when running `aw web`
- Old JavaScript/CSS still loading
- Python changes not taking effect

**Root Causes**:
1. Python package cached in site-packages
2. Browser cache serving old files
3. Service worker caching
4. Development server not reloading

**Solutions**:

```bash
# Solution 1: Reinstall package in editable mode
pip uninstall -y agent-workflow --break-system-packages
pip install -e . --user --break-system-packages

# Solution 2: Clear all caches and restart
aw web-stop
rm -rf ~/.cache/pip
rm -rf __pycache__
find . -name "*.pyc" -delete
lsof -ti:5000 | xargs kill -9 2>/dev/null || true
aw web

# Solution 3: Force browser refresh
# Chrome/Firefox: Ctrl+Shift+R or Ctrl+F5
# Safari: Cmd+Opt+R
# Or open in incognito/private window
```

**Prevention**:
```python
# Add to app.py for development
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0
app.config['TEMPLATES_AUTO_RELOAD'] = True

# Add cache busting to static files
@app.url_defaults
def add_cache_buster(endpoint, values):
    if endpoint == 'static':
        values['v'] = int(time.time())
```

### 2. WebSocket Connection Failures

**Symptoms**:
- "WebSocket connection failed" errors
- Real-time updates not working
- Chat messages not sending

**Diagnostics**:
```javascript
// Browser console diagnostics
console.log('Socket.IO loaded:', typeof io !== 'undefined');
console.log('WebSocket available:', 'WebSocket' in window);
console.log('Current connection:', window.wsManager?.isConnected());

// Check WebSocket frames
// Chrome DevTools > Network > WS > Frames
```

**Solutions**:

```javascript
// Solution 1: Force WebSocket transport
const socket = io({
    transports: ['websocket'],  // Skip polling fallback
    reconnection: true,
    reconnectionAttempts: 5,
    reconnectionDelay: 1000
});

// Solution 2: Add connection retry logic
class RobustWebSocketManager {
    connect() {
        const maxRetries = 5;
        let retries = 0;
        
        const attemptConnection = () => {
            try {
                this.socket = io();
                this.socket.on('connect_error', (error) => {
                    console.error('Connection error:', error);
                    if (retries < maxRetries) {
                        retries++;
                        setTimeout(attemptConnection, 1000 * retries);
                    }
                });
            } catch (error) {
                console.error('Socket.IO initialization failed:', error);
            }
        };
        
        attemptConnection();
    }
}
```

### 3. UI Elements Not Visible

**Symptoms**:
- State diagrams hidden
- Chat interface not showing
- Buttons not clickable

**Root Cause**: CSS conflicts or nuclear CSS not applied

**Solutions**:

```css
/* Emergency CSS fix - add to page */
.nuclear-force-show {
    display: block !important;
    visibility: visible !important;
    opacity: 1 !important;
    position: relative !important;
    z-index: 2147483647 !important;
    pointer-events: auto !important;
}

/* Apply to affected elements */
.main-content,
.diagram-container,
.chat-interface {
    @extend .nuclear-force-show;
}
```

```javascript
// JavaScript recovery
function forceUIVisibility() {
    const criticalElements = [
        '.main-content',
        '.diagram-container',
        '.chat-interface'
    ];
    
    criticalElements.forEach(selector => {
        const element = document.querySelector(selector);
        if (element) {
            element.style.cssText = `
                display: block !important;
                visibility: visible !important;
                opacity: 1 !important;
                position: relative !important;
                z-index: 9999 !important;
            `;
        }
    });
}

// Run on load and after dynamic updates
document.addEventListener('DOMContentLoaded', forceUIVisibility);
```

### 4. Session/Authentication Issues

**Symptoms**:
- Logged out unexpectedly
- Project context lost
- Permission errors

**Solutions**:

```python
# Solution 1: Extend session lifetime
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=24)
app.config['SESSION_REFRESH_EACH_REQUEST'] = True

# Solution 2: Add session recovery
@app.before_request
def check_session_validity():
    if 'user_id' in session:
        # Validate session is still valid
        last_activity = session.get('last_activity')
        if last_activity:
            time_since = datetime.now() - last_activity
            if time_since > timedelta(hours=1):
                # Attempt to recover session
                if recover_session(session['user_id']):
                    session['last_activity'] = datetime.now()
                else:
                    session.clear()
                    return redirect('/login')

# Solution 3: Client-side session management
class SessionManager {
    constructor() {
        this.heartbeatInterval = 30000; // 30 seconds
        this.startHeartbeat();
    }
    
    startHeartbeat() {
        setInterval(async () => {
            try {
                const response = await fetch('/api/heartbeat', {
                    method: 'POST',
                    credentials: 'include'
                });
                
                if (!response.ok) {
                    this.handleSessionExpired();
                }
            } catch (error) {
                console.error('Heartbeat failed:', error);
            }
        }, this.heartbeatInterval);
    }
}
```

---

## Diagnostic Tools

### 1. Built-in Diagnostics Page

Create a diagnostics endpoint for troubleshooting:

```python
# diagnostics.py
@app.route('/diagnostics')
@require_admin
def diagnostics():
    """System diagnostics page"""
    diagnostics_data = {
        'system': {
            'python_version': sys.version,
            'flask_version': flask.__version__,
            'platform': platform.platform(),
            'memory_usage': get_memory_usage(),
            'cpu_percent': psutil.cpu_percent()
        },
        'integrations': {
            'orchestrator': ORCHESTRATOR_AVAILABLE,
            'state_broadcaster': STATE_BROADCASTER_AVAILABLE,
            'multi_project': MULTI_PROJECT_AVAILABLE,
            'collaboration': COLLABORATION_AVAILABLE
        },
        'websocket': {
            'connected_clients': len(socketio.server.manager.rooms),
            'rooms': list(socketio.server.manager.rooms.keys())
        },
        'configuration': {
            'debug_mode': app.debug,
            'projects_loaded': len(projects),
            'active_interfaces': interface_manager.get_status() if interface_manager else None
        }
    }
    
    return render_template('diagnostics.html', data=diagnostics_data)
```

### 2. JavaScript Debug Console

```javascript
// debug-console.js - Add to page for troubleshooting
window.VisualizerDebug = {
    // Check all components
    checkComponents() {
        const components = {
            wsManager: typeof window.wsManager !== 'undefined',
            discordChat: typeof window.discordChat !== 'undefined',
            projectManager: typeof window.projectManager !== 'undefined',
            visualizer: typeof window.visualizer !== 'undefined',
            errorManager: typeof window.ErrorManager !== 'undefined'
        };
        
        console.table(components);
        return components;
    },
    
    // Check WebSocket status
    checkWebSocket() {
        if (!window.wsManager) {
            console.error('WebSocket manager not initialized');
            return;
        }
        
        console.log('Connected:', window.wsManager.connected);
        console.log('Socket ID:', window.wsManager.socket?.id);
        console.log('Current rooms:', Array.from(window.wsManager.currentRooms));
        console.log('Project context:', window.wsManager.projectContext);
    },
    
    // Check current state
    checkState() {
        console.log('Current workflow state:', window.currentState);
        console.log('Active project:', window.projectManager?.activeProject);
        console.log('Chat history size:', window.discordChat?.messages?.length);
    },
    
    // Force reconnect
    forceReconnect() {
        if (window.wsManager) {
            window.wsManager.disconnect();
            setTimeout(() => {
                window.wsManager.connect();
            }, 1000);
        }
    },
    
    // Clear all caches
    clearCaches() {
        // Clear localStorage
        localStorage.clear();
        
        // Clear sessionStorage
        sessionStorage.clear();
        
        // Clear service worker caches
        if ('caches' in window) {
            caches.keys().then(names => {
                names.forEach(name => caches.delete(name));
            });
        }
        
        console.log('All caches cleared');
    },
    
    // Export debug data
    exportDebugData() {
        const debugData = {
            timestamp: new Date().toISOString(),
            components: this.checkComponents(),
            state: window.currentState,
            errors: window.errorLog || [],
            performance: performance.getEntriesByType('navigation')[0],
            userAgent: navigator.userAgent
        };
        
        const blob = new Blob([JSON.stringify(debugData, null, 2)], {
            type: 'application/json'
        });
        
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `visualizer-debug-${Date.now()}.json`;
        a.click();
    }
};

// Auto-attach to window for console access
console.log('Debug console available: window.VisualizerDebug');
```

### 3. Network Diagnostics

```python
# network_diagnostics.py
import requests
import socket
import time

def diagnose_network():
    """Comprehensive network diagnostics"""
    results = {
        'timestamp': datetime.now().isoformat(),
        'checks': {}
    }
    
    # Check localhost connectivity
    try:
        socket.create_connection(('localhost', 5000), timeout=5)
        results['checks']['localhost'] = 'OK'
    except Exception as e:
        results['checks']['localhost'] = f'FAIL: {e}'
    
    # Check WebSocket port
    try:
        socket.create_connection(('localhost', 5001), timeout=5)
        results['checks']['websocket_port'] = 'OK'
    except Exception as e:
        results['checks']['websocket_port'] = f'FAIL: {e}'
    
    # Check external connectivity
    try:
        response = requests.get('https://api.github.com', timeout=5)
        results['checks']['external_api'] = f'OK: {response.status_code}'
    except Exception as e:
        results['checks']['external_api'] = f'FAIL: {e}'
    
    # Check DNS resolution
    try:
        socket.gethostbyname('github.com')
        results['checks']['dns'] = 'OK'
    except Exception as e:
        results['checks']['dns'] = f'FAIL: {e}'
    
    return results
```

---

## Performance Troubleshooting

### 1. Slow Page Load

**Diagnostics**:
```javascript
// Measure page load performance
window.addEventListener('load', () => {
    const perfData = performance.getEntriesByType('navigation')[0];
    console.log('Page Load Metrics:');
    console.log('DNS Lookup:', perfData.domainLookupEnd - perfData.domainLookupStart, 'ms');
    console.log('TCP Connection:', perfData.connectEnd - perfData.connectStart, 'ms');
    console.log('Request Time:', perfData.responseStart - perfData.requestStart, 'ms');
    console.log('Response Time:', perfData.responseEnd - perfData.responseStart, 'ms');
    console.log('DOM Processing:', perfData.domComplete - perfData.domLoading, 'ms');
    console.log('Total Load Time:', perfData.loadEventEnd - perfData.fetchStart, 'ms');
});
```

**Solutions**:
```python
# Enable compression
from flask_compress import Compress
Compress(app)

# Add caching headers
@app.after_request
def add_cache_headers(response):
    if request.path.startswith('/static/'):
        response.cache_control.max_age = 31536000  # 1 year
        response.cache_control.public = True
    return response

# Minify JSON responses
import json
from flask import Response

def jsonify_compact(*args, **kwargs):
    response = json.dumps(dict(*args, **kwargs), separators=(',', ':'))
    return Response(response, mimetype='application/json')
```

### 2. Memory Leaks

**Detection**:
```javascript
// Memory leak detector
class MemoryMonitor {
    constructor() {
        this.measurements = [];
        this.interval = null;
    }
    
    start() {
        this.interval = setInterval(() => {
            if (performance.memory) {
                this.measurements.push({
                    timestamp: Date.now(),
                    usedJSHeapSize: performance.memory.usedJSHeapSize,
                    totalJSHeapSize: performance.memory.totalJSHeapSize
                });
                
                // Keep only last 100 measurements
                if (this.measurements.length > 100) {
                    this.measurements.shift();
                }
                
                // Check for continuous growth
                if (this.measurements.length > 10) {
                    const growth = this.calculateGrowthRate();
                    if (growth > 0.1) { // 10% growth
                        console.warn('Potential memory leak detected:', growth);
                    }
                }
            }
        }, 10000); // Check every 10 seconds
    }
    
    calculateGrowthRate() {
        const recent = this.measurements.slice(-10);
        const first = recent[0].usedJSHeapSize;
        const last = recent[recent.length - 1].usedJSHeapSize;
        return (last - first) / first;
    }
    
    stop() {
        clearInterval(this.interval);
    }
    
    getReport() {
        return {
            measurements: this.measurements,
            currentMemory: performance.memory,
            growthRate: this.calculateGrowthRate()
        };
    }
}
```

**Common Leak Sources & Fixes**:
```javascript
// 1. Event listener leaks
class Component {
    constructor() {
        this.handlers = new Map();
    }
    
    addEventListener(element, event, handler) {
        // Store reference for cleanup
        if (!this.handlers.has(element)) {
            this.handlers.set(element, new Map());
        }
        this.handlers.get(element).set(event, handler);
        element.addEventListener(event, handler);
    }
    
    destroy() {
        // Clean up all listeners
        this.handlers.forEach((events, element) => {
            events.forEach((handler, event) => {
                element.removeEventListener(event, handler);
            });
        });
        this.handlers.clear();
    }
}

// 2. Timer leaks
class SafeTimers {
    constructor() {
        this.timers = new Set();
    }
    
    setTimeout(callback, delay) {
        const id = setTimeout(() => {
            this.timers.delete(id);
            callback();
        }, delay);
        this.timers.add(id);
        return id;
    }
    
    clearAll() {
        this.timers.forEach(id => clearTimeout(id));
        this.timers.clear();
    }
}

// 3. WebSocket subscription leaks
class SafeWebSocket {
    constructor() {
        this.subscriptions = new Map();
    }
    
    on(event, handler) {
        const wrappedHandler = (...args) => {
            try {
                handler(...args);
            } catch (error) {
                console.error(`Error in ${event} handler:`, error);
            }
        };
        
        this.subscriptions.set(handler, wrappedHandler);
        this.socket.on(event, wrappedHandler);
        
        // Return unsubscribe function
        return () => this.off(event, handler);
    }
    
    off(event, handler) {
        const wrappedHandler = this.subscriptions.get(handler);
        if (wrappedHandler) {
            this.socket.off(event, wrappedHandler);
            this.subscriptions.delete(handler);
        }
    }
    
    destroy() {
        // Remove all subscriptions
        this.subscriptions.forEach((wrapped, original) => {
            this.socket.off(wrapped);
        });
        this.subscriptions.clear();
    }
}
```

---

## WebSocket Issues

### 1. Connection Drops

**Monitoring**:
```javascript
// Connection stability monitor
class ConnectionMonitor {
    constructor(wsManager) {
        this.wsManager = wsManager;
        this.disconnects = [];
        this.reconnects = [];
        
        this.setupMonitoring();
    }
    
    setupMonitoring() {
        this.wsManager.on('disconnect', (reason) => {
            this.disconnects.push({
                timestamp: Date.now(),
                reason: reason
            });
            
            // Alert if too many disconnects
            const recentDisconnects = this.disconnects.filter(
                d => Date.now() - d.timestamp < 300000 // Last 5 minutes
            );
            
            if (recentDisconnects.length > 5) {
                this.alertUnstableConnection();
            }
        });
        
        this.wsManager.on('reconnect', (attemptNumber) => {
            this.reconnects.push({
                timestamp: Date.now(),
                attempt: attemptNumber
            });
        });
    }
    
    getStabilityReport() {
        const now = Date.now();
        const hour = 3600000;
        
        return {
            disconnectsLastHour: this.disconnects.filter(
                d => now - d.timestamp < hour
            ).length,
            reconnectsLastHour: this.reconnects.filter(
                r => now - r.timestamp < hour
            ).length,
            averageUptime: this.calculateAverageUptime()
        };
    }
}
```

### 2. Message Ordering Issues

**Solution**:
```javascript
// Message sequencing
class SequencedMessageHandler {
    constructor() {
        this.expectedSequence = 0;
        this.messageBuffer = new Map();
        this.maxBufferSize = 100;
    }
    
    handleMessage(message) {
        const sequence = message.sequence;
        
        if (sequence === this.expectedSequence) {
            // Process message
            this.processMessage(message);
            this.expectedSequence++;
            
            // Check buffer for next messages
            this.processBufferedMessages();
        } else if (sequence > this.expectedSequence) {
            // Buffer out-of-order message
            this.bufferMessage(message);
        }
        // Ignore old messages (sequence < expected)
    }
    
    processBufferedMessages() {
        while (this.messageBuffer.has(this.expectedSequence)) {
            const message = this.messageBuffer.get(this.expectedSequence);
            this.messageBuffer.delete(this.expectedSequence);
            this.processMessage(message);
            this.expectedSequence++;
        }
    }
    
    bufferMessage(message) {
        if (this.messageBuffer.size >= this.maxBufferSize) {
            // Buffer full, drop oldest
            const oldestKey = Math.min(...this.messageBuffer.keys());
            this.messageBuffer.delete(oldestKey);
        }
        this.messageBuffer.set(message.sequence, message);
    }
}
```

---

## Multi-Project Issues

### 1. Project Context Confusion

**Symptoms**:
- Commands executing in wrong project
- Chat history mixed between projects
- State updates in wrong project

**Diagnostics**:
```python
# Add project context logging
@app.before_request
def log_project_context():
    logger.info(f"Request: {request.path}, Project: {session.get('project_name')}, User: {session.get('user_id')}")

@socketio.on('chat_command')
def handle_chat_command_with_logging(data):
    logger.info(f"Command: {data.get('command')}, Project: {data.get('project_name')}, User: {session.get('user_id')}")
```

**Solutions**:
```javascript
// Ensure project context in all operations
class ProjectAwareComponent {
    constructor() {
        this.currentProject = null;
    }
    
    setProject(projectName) {
        this.currentProject = projectName;
        this.onProjectChange(projectName);
    }
    
    wrapWithProjectContext(operation) {
        return async (...args) => {
            if (!this.currentProject) {
                throw new Error('No project context set');
            }
            
            // Add project context to operation
            const context = {
                project_name: this.currentProject,
                ...args[0]
            };
            
            return operation(context, ...args.slice(1));
        };
    }
    
    // Wrap all operations
    sendCommand = this.wrapWithProjectContext(async (context, command) => {
        return await wsManager.emit('chat_command', {
            ...context,
            command
        });
    });
}
```

### 2. Project Switching Failures

**Solutions**:
```python
# Robust project switching
@socketio.on('switch_project')
def handle_project_switch(data):
    old_project = session.get('project_name')
    new_project = data['project_name']
    
    try:
        # Validate new project exists
        if not project_exists(new_project):
            emit('error', {'message': f'Project {new_project} not found'})
            return
        
        # Save old project state
        if old_project:
            save_project_state(old_project, get_current_state())
            leave_room(f'project_{old_project}')
        
        # Switch to new project
        session['project_name'] = new_project
        join_room(f'project_{new_project}')
        
        # Load new project state
        new_state = load_project_state(new_project)
        
        emit('project_switched', {
            'success': True,
            'old_project': old_project,
            'new_project': new_project,
            'state': new_state
        })
        
    except Exception as e:
        logger.error(f"Project switch failed: {e}")
        emit('error', {
            'message': 'Failed to switch project',
            'details': str(e)
        })
        
        # Attempt recovery
        if old_project:
            session['project_name'] = old_project
            join_room(f'project_{old_project}')
```

---

## Browser-Specific Issues

### 1. Safari WebSocket Issues

**Problem**: Safari has stricter WebSocket security

**Solution**:
```javascript
// Safari-specific WebSocket configuration
if (/^((?!chrome|android).)*safari/i.test(navigator.userAgent)) {
    window.SAFARI_MODE = true;
    
    // Use specific transport order for Safari
    const socket = io({
        transports: ['polling', 'websocket'], // Polling first for Safari
        upgrade: true,
        rememberUpgrade: true
    });
}
```

### 2. Firefox Mixed Content

**Problem**: Firefox blocks mixed HTTP/HTTPS content

**Solution**:
```python
# Force HTTPS in production
@app.before_request
def force_https():
    if not request.is_secure and app.env == 'production':
        return redirect(request.url.replace('http://', 'https://'))

# Content Security Policy
@app.after_request
def set_security_headers(response):
    response.headers['Content-Security-Policy'] = "upgrade-insecure-requests"
    return response
```

### 3. Edge/IE Compatibility

**Solution**:
```javascript
// Polyfills for older browsers
if (!String.prototype.includes) {
    String.prototype.includes = function(search, start) {
        return this.indexOf(search, start) !== -1;
    };
}

if (!Array.prototype.find) {
    Array.prototype.find = function(predicate) {
        for (let i = 0; i < this.length; i++) {
            if (predicate(this[i], i, this)) {
                return this[i];
            }
        }
        return undefined;
    };
}
```

---

## Maintenance Procedures

### 1. Regular Health Checks

```python
# health_check.py
import asyncio
from datetime import datetime, timedelta

class HealthChecker:
    def __init__(self, app, socketio):
        self.app = app
        self.socketio = socketio
        self.checks = []
        
    async def run_health_checks(self):
        """Run all health checks"""
        results = {
            'timestamp': datetime.now().isoformat(),
            'checks': {}
        }
        
        # Database connectivity
        results['checks']['database'] = await self.check_database()
        
        # WebSocket health
        results['checks']['websocket'] = await self.check_websocket()
        
        # Integration health
        results['checks']['integrations'] = await self.check_integrations()
        
        # Resource usage
        results['checks']['resources'] = await self.check_resources()
        
        return results
    
    async def check_database(self):
        try:
            # Test database query
            projects = project_storage.list_projects()
            return {
                'status': 'healthy',
                'project_count': len(projects)
            }
        except Exception as e:
            return {
                'status': 'unhealthy',
                'error': str(e)
            }
    
    async def check_websocket(self):
        return {
            'status': 'healthy',
            'connected_clients': len(self.socketio.server.manager.rooms),
            'rooms': list(self.socketio.server.manager.rooms.keys())
        }
    
    async def check_resources(self):
        import psutil
        
        return {
            'cpu_percent': psutil.cpu_percent(),
            'memory_percent': psutil.virtual_memory().percent,
            'disk_percent': psutil.disk_usage('/').percent
        }
```

### 2. Log Rotation

```python
# log_config.py
import logging.handlers

def setup_logging(app):
    # Rotating file handler
    file_handler = logging.handlers.RotatingFileHandler(
        'visualizer.log',
        maxBytes=10485760,  # 10MB
        backupCount=10
    )
    
    file_handler.setFormatter(logging.Formatter(
        '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
    ))
    
    app.logger.addHandler(file_handler)
    app.logger.setLevel(logging.INFO)
    
    # Also add syslog handler for production
    if app.env == 'production':
        syslog_handler = logging.handlers.SysLogHandler(address='/dev/log')
        syslog_handler.setFormatter(logging.Formatter(
            'visualizer[%(process)d]: %(message)s'
        ))
        app.logger.addHandler(syslog_handler)
```

### 3. Database Maintenance

```python
# db_maintenance.py
def cleanup_old_data(days=30):
    """Clean up old data"""
    cutoff = datetime.now() - timedelta(days=days)
    
    # Clean old chat messages
    for project in projects:
        chat_history = project_chat_history.get(project, [])
        project_chat_history[project] = [
            msg for msg in chat_history
            if datetime.fromisoformat(msg['timestamp']) > cutoff
        ]
    
    # Clean old state history
    for project in projects:
        if hasattr(project_storage, 'cleanup_old_states'):
            project_storage.cleanup_old_states(project, cutoff)
    
    logger.info(f"Cleaned up data older than {days} days")

# Schedule regular cleanup
from apscheduler.schedulers.background import BackgroundScheduler

scheduler = BackgroundScheduler()
scheduler.add_job(
    func=cleanup_old_data,
    trigger="interval",
    days=1,
    id='cleanup_job',
    name='Clean up old data',
    replace_existing=True
)
scheduler.start()
```

---

## Log Analysis

### 1. Log Parsing Tools

```python
# log_analyzer.py
import re
from collections import defaultdict, Counter
from datetime import datetime

class LogAnalyzer:
    def __init__(self, log_file):
        self.log_file = log_file
        self.patterns = {
            'error': re.compile(r'ERROR.*'),
            'warning': re.compile(r'WARNING.*'),
            'websocket': re.compile(r'websocket|WebSocket|socket\.io'),
            'project': re.compile(r'project[_-]?\w+'),
            'user': re.compile(r'user[_-]?\w+'),
            'timestamp': re.compile(r'\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}')
        }
    
    def analyze(self):
        stats = {
            'errors': [],
            'warnings': [],
            'websocket_events': [],
            'project_activity': defaultdict(int),
            'user_activity': defaultdict(int),
            'hourly_distribution': defaultdict(int)
        }
        
        with open(self.log_file, 'r') as f:
            for line in f:
                self.process_line(line, stats)
        
        return self.generate_report(stats)
    
    def process_line(self, line, stats):
        # Extract timestamp
        timestamp_match = self.patterns['timestamp'].search(line)
        if timestamp_match:
            timestamp = datetime.strptime(
                timestamp_match.group(), 
                '%Y-%m-%d %H:%M:%S'
            )
            stats['hourly_distribution'][timestamp.hour] += 1
        
        # Check for errors
        if self.patterns['error'].search(line):
            stats['errors'].append(line.strip())
        
        # Check for warnings
        if self.patterns['warning'].search(line):
            stats['warnings'].append(line.strip())
        
        # WebSocket events
        if self.patterns['websocket'].search(line):
            stats['websocket_events'].append(line.strip())
        
        # Project activity
        project_match = self.patterns['project'].search(line)
        if project_match:
            stats['project_activity'][project_match.group()] += 1
        
        # User activity
        user_match = self.patterns['user'].search(line)
        if user_match:
            stats['user_activity'][user_match.group()] += 1
    
    def generate_report(self, stats):
        return {
            'error_count': len(stats['errors']),
            'warning_count': len(stats['warnings']),
            'websocket_event_count': len(stats['websocket_events']),
            'most_active_projects': Counter(stats['project_activity']).most_common(5),
            'most_active_users': Counter(stats['user_activity']).most_common(5),
            'peak_hours': sorted(
                stats['hourly_distribution'].items(), 
                key=lambda x: x[1], 
                reverse=True
            )[:3],
            'recent_errors': stats['errors'][-10:]  # Last 10 errors
        }

# Usage
analyzer = LogAnalyzer('visualizer.log')
report = analyzer.analyze()
print(json.dumps(report, indent=2))
```

### 2. Real-time Log Monitoring

```python
# log_monitor.py
import time
import os

class LogMonitor:
    def __init__(self, log_file, patterns):
        self.log_file = log_file
        self.patterns = patterns
        self.file = None
        self.position = 0
    
    def start(self):
        """Start monitoring log file"""
        # Open file and seek to end
        self.file = open(self.log_file, 'r')
        self.file.seek(0, os.SEEK_END)
        self.position = self.file.tell()
        
        print(f"Monitoring {self.log_file} for patterns: {list(self.patterns.keys())}")
        
        try:
            while True:
                line = self.file.readline()
                if line:
                    self.check_patterns(line)
                else:
                    time.sleep(0.1)  # No new data, wait
                    
        except KeyboardInterrupt:
            print("\nStopping log monitor")
        finally:
            self.file.close()
    
    def check_patterns(self, line):
        """Check line against patterns"""
        for name, pattern in self.patterns.items():
            if pattern.search(line):
                self.alert(name, line)
    
    def alert(self, pattern_name, line):
        """Alert when pattern found"""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        print(f"\n[{timestamp}] ALERT: {pattern_name}")
        print(f"  {line.strip()}")
        
        # Could also send notifications, emails, etc.
        if pattern_name == 'critical_error':
            self.send_alert_notification(line)

# Usage
monitor = LogMonitor('visualizer.log', {
    'critical_error': re.compile(r'CRITICAL|FATAL'),
    'websocket_error': re.compile(r'websocket.*error', re.I),
    'memory_warning': re.compile(r'memory.*high|out of memory', re.I)
})
monitor.start()
```

---

## Recovery Procedures

### 1. Emergency Recovery Script

```bash
#!/bin/bash
# emergency_recovery.sh

echo "Starting emergency recovery..."

# 1. Stop all services
echo "Stopping services..."
systemctl stop visualizer || true
systemctl stop redis || true

# 2. Clear problematic state
echo "Clearing state..."
rm -f /tmp/visualizer.lock
rm -rf /var/cache/visualizer/*
redis-cli FLUSHDB

# 3. Check disk space
echo "Checking disk space..."
df -h
if [ $(df / | awk 'NR==2 {print $5}' | sed 's/%//') -gt 90 ]; then
    echo "WARNING: Disk space critical!"
    # Clear old logs
    find /var/log/visualizer -name "*.log.*" -mtime +7 -delete
fi

# 4. Repair permissions
echo "Fixing permissions..."
chown -R visualizer:visualizer /opt/visualizer
chmod -R 755 /opt/visualizer

# 5. Validate configuration
echo "Validating configuration..."
python3 -c "
import yaml
with open('/opt/visualizer/orch-config.yaml') as f:
    config = yaml.safe_load(f)
print('Configuration valid')
"

# 6. Start services
echo "Starting services..."
systemctl start redis
sleep 2
systemctl start visualizer

# 7. Health check
echo "Running health check..."
sleep 5
curl -f http://localhost:5000/health || {
    echo "Health check failed!"
    journalctl -u visualizer -n 50
    exit 1
}

echo "Recovery complete!"
```

### 2. State Recovery

```python
# state_recovery.py
import json
import os
from datetime import datetime
import shutil

class StateRecovery:
    def __init__(self, backup_dir='/var/backups/visualizer'):
        self.backup_dir = backup_dir
    
    def create_backup(self, project_name):
        """Create state backup"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_path = os.path.join(
            self.backup_dir, 
            f'{project_name}_{timestamp}.json'
        )
        
        state = {
            'project_name': project_name,
            'timestamp': timestamp,
            'chat_history': project_chat_history.get(project_name, []),
            'workflow_state': get_project_state(project_name),
            'configuration': get_project_config(project_name)
        }
        
        with open(backup_path, 'w') as f:
            json.dump(state, f, indent=2)
        
        logger.info(f"Created backup: {backup_path}")
        return backup_path
    
    def restore_backup(self, backup_path):
        """Restore from backup"""
        with open(backup_path, 'r') as f:
            state = json.load(f)
        
        project_name = state['project_name']
        
        # Restore chat history
        project_chat_history[project_name] = state['chat_history']
        
        # Restore workflow state
        set_project_state(project_name, state['workflow_state'])
        
        # Restore configuration
        set_project_config(project_name, state['configuration'])
        
        logger.info(f"Restored backup for {project_name} from {state['timestamp']}")
        
        return True
    
    def list_backups(self, project_name=None):
        """List available backups"""
        backups = []
        
        for filename in os.listdir(self.backup_dir):
            if filename.endswith('.json'):
                if project_name and not filename.startswith(project_name):
                    continue
                    
                filepath = os.path.join(self.backup_dir, filename)
                stat = os.stat(filepath)
                
                backups.append({
                    'filename': filename,
                    'filepath': filepath,
                    'size': stat.st_size,
                    'modified': datetime.fromtimestamp(stat.st_mtime)
                })
        
        return sorted(backups, key=lambda x: x['modified'], reverse=True)
```

### 3. Disaster Recovery

```python
# disaster_recovery.py
class DisasterRecovery:
    def __init__(self):
        self.recovery_steps = []
    
    def assess_damage(self):
        """Assess system damage"""
        report = {
            'timestamp': datetime.now().isoformat(),
            'services': {},
            'data': {},
            'connectivity': {}
        }
        
        # Check services
        report['services']['flask'] = self.check_service('visualizer')
        report['services']['redis'] = self.check_service('redis')
        report['services']['nginx'] = self.check_service('nginx')
        
        # Check data integrity
        report['data']['projects'] = self.check_project_data()
        report['data']['configuration'] = self.check_configuration()
        
        # Check connectivity
        report['connectivity']['database'] = self.check_database()
        report['connectivity']['websocket'] = self.check_websocket()
        
        return report
    
    def execute_recovery(self, report):
        """Execute recovery based on assessment"""
        recovery_plan = []
        
        # Service recovery
        for service, status in report['services'].items():
            if not status['healthy']:
                recovery_plan.append({
                    'action': 'restart_service',
                    'target': service,
                    'priority': 'high'
                })
        
        # Data recovery
        if not report['data']['projects']['healthy']:
            recovery_plan.append({
                'action': 'restore_project_data',
                'target': 'all_projects',
                'priority': 'critical'
            })
        
        # Execute plan
        for step in sorted(recovery_plan, key=lambda x: x['priority']):
            self.execute_step(step)
    
    def execute_step(self, step):
        """Execute a recovery step"""
        logger.info(f"Executing: {step['action']} on {step['target']}")
        
        if step['action'] == 'restart_service':
            os.system(f"systemctl restart {step['target']}")
        
        elif step['action'] == 'restore_project_data':
            recovery = StateRecovery()
            for project in get_all_projects():
                backups = recovery.list_backups(project)
                if backups:
                    recovery.restore_backup(backups[0]['filepath'])
```

---

## Health Monitoring

### 1. Prometheus Metrics

```python
# metrics.py
from prometheus_client import Counter, Histogram, Gauge, Info

# Define metrics
request_count = Counter(
    'visualizer_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status']
)

request_duration = Histogram(
    'visualizer_request_duration_seconds',
    'HTTP request duration',
    ['method', 'endpoint']
)

websocket_connections = Gauge(
    'visualizer_websocket_connections',
    'Active WebSocket connections'
)

project_count = Gauge(
    'visualizer_projects_total',
    'Total number of projects'
)

system_info = Info(
    'visualizer_system',
    'System information'
)

# Instrument application
@app.before_request
def before_request():
    request.start_time = time.time()

@app.after_request
def after_request(response):
    if hasattr(request, 'start_time'):
        duration = time.time() - request.start_time
        
        request_duration.labels(
            method=request.method,
            endpoint=request.endpoint or 'unknown'
        ).observe(duration)
        
        request_count.labels(
            method=request.method,
            endpoint=request.endpoint or 'unknown',
            status=response.status_code
        ).inc()
    
    return response

# Update WebSocket metrics
@socketio.on('connect')
def handle_connect():
    websocket_connections.inc()

@socketio.on('disconnect')
def handle_disconnect():
    websocket_connections.dec()
```

### 2. Health Dashboard

```python
# health_dashboard.py
@app.route('/health/dashboard')
def health_dashboard():
    """Health monitoring dashboard"""
    health_data = {
        'system': {
            'uptime': get_uptime(),
            'version': app.config.get('VERSION'),
            'environment': app.env
        },
        'resources': {
            'cpu_percent': psutil.cpu_percent(interval=1),
            'memory': psutil.virtual_memory()._asdict(),
            'disk': psutil.disk_usage('/')._asdict()
        },
        'services': {
            'flask': {'status': 'running', 'pid': os.getpid()},
            'websocket': {
                'status': 'running',
                'connections': websocket_connections._value.get()
            },
            'redis': check_redis_health()
        },
        'application': {
            'projects': project_count._value.get(),
            'active_users': get_active_user_count(),
            'request_rate': calculate_request_rate()
        }
    }
    
    return render_template('health_dashboard.html', data=health_data)
```

### 3. Alerting Rules

```yaml
# prometheus_alerts.yml
groups:
  - name: visualizer_alerts
    rules:
      - alert: HighErrorRate
        expr: rate(visualizer_requests_total{status=~"5.."}[5m]) > 0.05
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: High error rate detected
          description: "Error rate is {{ $value }} errors per second"
      
      - alert: HighMemoryUsage
        expr: process_resident_memory_bytes / 1024 / 1024 > 2048
        for: 10m
        labels:
          severity: warning
        annotations:
          summary: High memory usage
          description: "Memory usage is {{ $value }}MB"
      
      - alert: WebSocketConnectionDrop
        expr: rate(visualizer_websocket_connections[1m]) < -10
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: Mass WebSocket disconnection
          description: "{{ $value }} connections dropped per second"
```

---

This comprehensive troubleshooting and maintenance guide provides the tools and procedures needed to keep the AI Agent Workflow Visualizer running smoothly. Regular maintenance and proactive monitoring will prevent most issues before they impact users.