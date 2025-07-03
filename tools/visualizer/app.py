#!/usr/bin/env python3
"""
Real-Time State Visualizer Web Application

Flask application with WebSocket support for real-time visualization
of workflow and TDD state machine transitions.
"""

# Standard library imports
import asyncio
import hashlib
import logging
import os
import sys
import time
from datetime import datetime
from pathlib import Path

# Third-party imports
from flask import Flask, render_template, jsonify, request, session
from flask_socketio import SocketIO, emit, join_room, leave_room
import websockets

# Local utility imports
from utils import generate_uuid, serialize_json, ConfigDict, StateDict, Dict, Any

# Add lib directory to path  
lib_path = Path(__file__).parent.parent.parent / "lib"
sys.path.insert(0, str(lib_path))

# Also add agent_workflow to path for new package structure
agent_workflow_path = Path(__file__).parent.parent.parent / "agent_workflow"
sys.path.insert(0, str(agent_workflow_path))

# State broadcaster import with prioritized pattern: agent_workflow → lib → fallback
try:
    # Primary: Try agent_workflow package first
    from agent_workflow.core.state_broadcaster import broadcaster
except ImportError:
    try:
        # Secondary: Try lib directory for backward compatibility
        from state_broadcaster import broadcaster
    except ImportError:
        try:
            # Fallback - try direct import with lib prefix
            sys.path.insert(0, str(Path(__file__).parent.parent.parent))
            from lib.state_broadcaster import broadcaster
        except ImportError:
            import logging
            logging.warning("state_broadcaster not available - using mock")
            # Create a mock broadcaster
            class MockBroadcaster:
                def broadcast_state(self, state): pass
                def start(self): pass
                def stop(self): pass
            broadcaster = MockBroadcaster()
# Agent interfaces import with prioritized pattern: agent_workflow → lib/local → fallback
try:
    # Primary: Try agent_workflow package structure
    from agent_workflow.integrations.agent_interfaces import interface_manager, InterfaceType, AgentType
except ImportError:
    try:
        # Secondary: Try local visualizer agent_interfaces
        from agent_interfaces import interface_manager, InterfaceType, AgentType
    except ImportError:
        try:
            # Tertiary: Try lib directory for backward compatibility
            from lib.agent_interfaces import interface_manager, InterfaceType, AgentType
        except ImportError:
            # Fallback if agent_interfaces doesn't exist
            import logging
            temp_logger = logging.getLogger(__name__)
            temp_logger.warning("agent_interfaces not available - some features disabled")
            interface_manager = None
            InterfaceType = None
            AgentType = None

# Configure logging first - do this before any logger usage
import logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Import security from agent_workflow package if available, otherwise provide fallbacks
security_available = False
validate_configuration = None
sanitize_prompt = None
sanitize_code = None
audit_operation = None
SecurityLevel = None
mask_api_key = None

try:
    from agent_workflow.security.tool_config import validate_agent_access, get_security_summary, AgentType
    # Create compatible wrapper functions using available security functions
    def validate_configuration(config): 
        """Validate configuration using available security functions"""
        return isinstance(config, dict)
    
    def sanitize_prompt(prompt): 
        """Sanitize prompt for security"""
        if not isinstance(prompt, str):
            return ""
        # Basic sanitization - remove potential command injection
        import re
        sanitized = re.sub(r'[;&|`$(){}[\]<>]', '', prompt)
        return sanitized[:1000]  # Limit length
    
    def sanitize_code(code): 
        """Sanitize code for security"""
        if not isinstance(code, str):
            return ""
        # Basic sanitization for display
        import re
        sanitized = re.sub(r'(\w+)\s*=\s*["\'][^"\']*password[^"\']*["\']', r'\1 = "***"', code, flags=re.IGNORECASE)
        return sanitized
    
    def audit_operation(operation): 
        """Audit security operation"""
        logger.info(f"Security audit: {operation}")
    
    # Use AgentType as SecurityLevel equivalent
    SecurityLevel = AgentType
    
    def mask_api_key(key): 
        """Mask API key for security"""
        if not key or not isinstance(key, str):
            return "***"
        if len(key) <= 8:
            return "***"
        return key[:4] + "***" + key[-2:]
    
    security_available = True
    logger.info("Security module loaded with agent tool config")
    
except ImportError:
    try:
        # Secondary: Try agent_workflow security structure
        from agent_workflow.security.multi_project_security import AccessLevel
        # Create wrapper functions using multi-project security
        def validate_configuration(config): 
            return isinstance(config, dict)
        
        def sanitize_prompt(prompt): 
            if not isinstance(prompt, str):
                return ""
            import re
            sanitized = re.sub(r'[;&|`$(){}[\]<>]', '', prompt)
            return sanitized[:1000]
        
        def sanitize_code(code): 
            if not isinstance(code, str):
                return ""
            import re
            sanitized = re.sub(r'(\w+)\s*=\s*["\'][^"\']*password[^"\']*["\']', r'\1 = "***"', code, flags=re.IGNORECASE)
            return sanitized
        
        def audit_operation(operation): 
            logger.info(f"Security audit: {operation}")
        
        SecurityLevel = AccessLevel
        
        def mask_api_key(key): 
            if not key or not isinstance(key, str):
                return "***"
            if len(key) <= 8:
                return "***"
            return key[:4] + "***" + key[-2:]
        
        security_available = True
        logger.info("Security module loaded with agent_workflow security")
        
    except ImportError:
        try:
            # Tertiary: Try lib directory for backward compatibility
            from lib.multi_project_security import AccessLevel
            # Create wrapper functions using multi-project security
            def validate_configuration(config): 
                return isinstance(config, dict)
            
            def sanitize_prompt(prompt): 
                if not isinstance(prompt, str):
                    return ""
                import re
                sanitized = re.sub(r'[;&|`$(){}[\]<>]', '', prompt)
                return sanitized[:1000]
            
            def sanitize_code(code): 
                if not isinstance(code, str):
                    return ""
                import re
                sanitized = re.sub(r'(\w+)\s*=\s*["\'][^"\']*password[^"\']*["\']', r'\1 = "***"', code, flags=re.IGNORECASE)
                return sanitized
            
            def audit_operation(operation): 
                logger.info(f"Security audit: {operation}")
            
            SecurityLevel = AccessLevel
            
            def mask_api_key(key): 
                if not key or not isinstance(key, str):
                    return "***"
                if len(key) <= 8:
                    return "***"
                return key[:4] + "***" + key[-2:]
        
            security_available = True
            logger.info("Security module loaded with multi-project security")
            
        except ImportError:
            # Fallback implementations
            logger.warning("Security module not available - using fallback implementations")
            
            # Fallback implementations
            def validate_configuration(config): 
                """Fallback configuration validation"""
                return isinstance(config, dict)
            
            def sanitize_prompt(prompt): 
                """Fallback prompt sanitization"""
                if not isinstance(prompt, str):
                    return ""
                # Basic sanitization - remove potential command injection
                import re
                sanitized = re.sub(r'[;&|`$(){}[\]<>]', '', prompt)
                return sanitized[:1000]  # Limit length
            
            def sanitize_code(code): 
                """Fallback code sanitization"""
                if not isinstance(code, str):
                    return ""
                # Basic sanitization for display - mask sensitive patterns
                import re
                sanitized = re.sub(r'(\w+)\s*=\s*["\'][^"\']*password[^"\']*["\']', r'\1 = "***"', code, flags=re.IGNORECASE)
                return sanitized
            
            def audit_operation(operation): 
                """Fallback audit operation"""
                logger.info(f"Security audit (fallback): {operation}")
            
            class SecurityLevel:
                """Fallback security level enum"""
                LOW = "low"
                MEDIUM = "medium"
                HIGH = "high"
            
            def mask_api_key(key): 
                """Fallback API key masking"""
                if not key or not isinstance(key, str):
                    return "***"
                if len(key) <= 8:
                    return "***"
                return key[:4] + "***" + key[-2:]
            
            security_available = False

# Try to import context management components (prefer agent_workflow, fallback to lib)
try:
    from agent_workflow.context.manager_factory import get_context_manager_factory, ContextMode
    CONTEXT_MANAGEMENT_AVAILABLE = True
except ImportError:
    try:
        from context_manager_factory import get_context_manager_factory, ContextMode
        CONTEXT_MANAGEMENT_AVAILABLE = True
    except ImportError:
        try:
            from lib.context_manager_factory import get_context_manager_factory, ContextMode
            CONTEXT_MANAGEMENT_AVAILABLE = True
        except ImportError:
            logger.warning("Context management not available - some features disabled")
            CONTEXT_MANAGEMENT_AVAILABLE = False

# Try to import multi-project components with prioritized pattern: agent_workflow → lib → fallback
try:
    # Primary: Try agent_workflow package structure
    from agent_workflow.config.multi_project_config import MultiProjectConfigManager
    MULTI_PROJECT_AVAILABLE = True
except ImportError:
    try:
        # Secondary: Try local import
        from multi_project_config import MultiProjectConfigManager
        MULTI_PROJECT_AVAILABLE = True
    except ImportError:
        try:
            # Tertiary: Try lib directory for backward compatibility
            from lib.multi_project_config import MultiProjectConfigManager
            MULTI_PROJECT_AVAILABLE = True
        except ImportError:
            logger.warning("Multi-project management not available - using single project mode")
            MULTI_PROJECT_AVAILABLE = False

# Import chat and collaboration components with prioritized pattern: agent_workflow → local → lib → fallback
try:
    # Primary: Try agent_workflow package structure
    from agent_workflow.integrations.command_processor import CommandProcessor
    COMMAND_PROCESSOR_AVAILABLE = True
except ImportError:
    try:
        # Secondary: Try local import
        from command_processor import CommandProcessor
        COMMAND_PROCESSOR_AVAILABLE = True
    except ImportError:
        try:
            # Tertiary: Try lib directory for backward compatibility
            from lib.command_processor import CommandProcessor
            COMMAND_PROCESSOR_AVAILABLE = True
        except ImportError:
            logger.warning("Command processor not available - basic chat only")
            COMMAND_PROCESSOR_AVAILABLE = False

try:
    # Primary: Try agent_workflow package structure
    from agent_workflow.integrations.collaboration_manager import get_collaboration_manager, UserPermission
    COLLABORATION_AVAILABLE = True
except ImportError:
    try:
        # Secondary: Try local import
        from collaboration_manager import get_collaboration_manager, UserPermission
        COLLABORATION_AVAILABLE = True
    except ImportError:
        try:
            # Tertiary: Try lib directory for backward compatibility
            from lib.collaboration_manager import get_collaboration_manager, UserPermission
            COLLABORATION_AVAILABLE = True
        except ImportError:
            logger.warning("Collaboration features not available")
            COLLABORATION_AVAILABLE = False

# Flask app setup
app = Flask(__name__)
app.config['SECRET_KEY'] = 'state-visualizer-dev-key'
# Disable caching for development
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0
# Configure SocketIO with more robust settings
socketio = SocketIO(
    app, 
    cors_allowed_origins="*", 
    async_mode='threading',
    logger=True,
    engineio_logger=False,
    ping_timeout=60,
    ping_interval=25
)

# Global state for tracking
current_state = {
    "workflow_state": "IDLE",
    "tdd_cycles": {},
    "last_updated": datetime.now().isoformat(),
    "transition_history": []
}

# Chat history for the Discord-style interface
chat_history = []
typing_users = set()

# Project-specific chat data structures
project_chat_history = {}  # project_name -> list of messages
project_user_sessions = {}  # user_id -> {'project': project_name, 'session_id': session_id}
project_typing_users = {}  # project_name -> set of user_ids
user_project_rooms = {}  # user_id -> project_name (current room)
active_users = set()

# Multi-project support
multi_project_manager = None
project_rooms = {}  # project_name -> set of session_ids
active_project_sessions = {}  # session_id -> project_name

# Initialize multi-project manager
if MULTI_PROJECT_AVAILABLE:
    try:
        multi_project_manager = MultiProjectConfigManager()
        logger.info(f"Multi-project manager initialized with {len(multi_project_manager.projects)} projects")
    except Exception as e:
        logger.warning(f"Failed to initialize multi-project manager: {e}")
        multi_project_manager = None
        MULTI_PROJECT_AVAILABLE = False


@app.after_request
def add_enhanced_cache_headers(response):
    """Add enhanced headers to completely disable caching and ensure correct content types"""
    # Determine if this is a static file request
    is_static = (request.path.startswith('/static/') or 
                request.path.endswith('.js') or 
                request.path.endswith('.css') or
                request.path.endswith('.html'))
    
    if is_static:
        # Ultra-aggressive cache busting for static files
        response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, post-check=0, pre-check=0, max-age=0'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '0'
        response.headers['Last-Modified'] = datetime.now().strftime('%a, %d %b %Y %H:%M:%S GMT')
        response.headers['ETag'] = f'"{int(time.time())}"'
        
        # Add development timestamp to identify cache issues
        response.headers['X-Dev-Timestamp'] = str(int(time.time() * 1000))
        response.headers['X-Cache-Buster'] = hashlib.md5(str(time.time()).encode()).hexdigest()[:8]
        
    # Ensure correct content types for JavaScript and CSS
    if request.path.endswith('.js'):
        response.headers['Content-Type'] = 'application/javascript; charset=utf-8'
    elif request.path.endswith('.css'):
        response.headers['Content-Type'] = 'text/css; charset=utf-8'
    elif request.path.endswith('.html'):
        response.headers['Content-Type'] = 'text/html; charset=utf-8'
    
    return response


@app.route('/')
def index():
    """Main visualizer page"""
    return render_template('index.html')


@app.route('/api/state')
def get_current_state():
    """JSON API endpoint for current state"""
    return jsonify(broadcaster.get_current_state())


@app.route('/api/history')
def get_transition_history():
    """JSON API endpoint for transition history"""
    return jsonify({
        "history": broadcaster.transition_history[-50:],  # Last 50 transitions
        "count": len(broadcaster.transition_history)
    })


@app.route('/health')
def health_check():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "connected_clients": len(broadcaster.clients),
        "active_tdd_cycles": len(broadcaster.tdd_cycles)
    })


@app.route('/test/scripts')
def test_scripts():
    """Test endpoint to verify script loading"""
    import os
    static_path = os.path.join(app.root_path, 'static')
    js_path = os.path.join(static_path, 'js')
    
    scripts = {
        'chat-components.js': os.path.exists(os.path.join(js_path, 'chat-components.js')),
        'discord-chat.js': os.path.exists(os.path.join(js_path, 'discord-chat.js')),
        'ui-enhancements.js': os.path.exists(os.path.join(js_path, 'ui-enhancements.js')),
        'visualizer.js': os.path.exists(os.path.join(static_path, 'visualizer.js'))
    }
    
    return jsonify({
        "static_path": static_path,
        "scripts_exist": scripts,
        "flask_static_folder": app.static_folder,
        "flask_static_url_path": app.static_url_path
    })


@app.route('/metrics')
def metrics_endpoint():
    """Prometheus-compatible metrics endpoint"""
    try:
        current_state = broadcaster.get_current_state()
        
        # Generate Prometheus-style metrics
        metrics_output = []
        metrics_output.append("# HELP workflow_current_state Current workflow state")
        metrics_output.append("# TYPE workflow_current_state gauge")
        
        # Map states to numeric values for Prometheus
        state_values = {
            "IDLE": 0, "BACKLOG_READY": 1, "SPRINT_PLANNED": 2,
            "SPRINT_ACTIVE": 3, "SPRINT_PAUSED": 4, "SPRINT_REVIEW": 5,
            "BLOCKED": 6, "EXPLORING": 7, "QUICK_FIX": 8
        }
        
        state_value = state_values.get(current_state.get("workflow_state", "IDLE"), 0)
        metrics_output.append(f'workflow_current_state {state_value}')
        
        metrics_output.append("# HELP tdd_active_cycles Number of active TDD cycles")
        metrics_output.append("# TYPE tdd_active_cycles gauge")
        metrics_output.append(f'tdd_active_cycles {len(current_state.get("tdd_cycles", {}))}')
        
        metrics_output.append("# HELP visualizer_connected_clients Number of connected WebSocket clients")
        metrics_output.append("# TYPE visualizer_connected_clients gauge")
        metrics_output.append(f'visualizer_connected_clients {len(broadcaster.clients)}')
        
        return "\n".join(metrics_output), 200, {'Content-Type': 'text/plain; charset=utf-8'}
        
    except Exception as e:
        logger.error(f"Metrics endpoint error: {e}")
        return jsonify({"error": "metrics collection failed"}), 500


# =====================================================
# Multi-Project API Endpoints
# =====================================================

@app.route('/api/projects')
def get_projects():
    """Get all registered projects with their status"""
    if not MULTI_PROJECT_AVAILABLE or not multi_project_manager:
        return jsonify({
            "multi_project_enabled": False,
            "projects": [],
            "reason": "Multi-project management not available"
        }), 200
    
    try:
        projects = []
        for project in multi_project_manager.list_projects():
            # Load project state if available
            project_state = load_project_state(project.name, project.path)
            
            project_info = {
                "name": project.name,
                "path": project.path,
                "status": project.status.value,
                "priority": project.priority.value,
                "description": project.description,
                "git_url": project.git_url,
                "owner": project.owner,
                "team": project.team,
                "discord_channel": project.discord_channel,
                "tags": project.tags,
                "created_at": project.created_at.isoformat(),
                "last_activity": project.last_activity.isoformat() if project.last_activity else None,
                "resource_limits": {
                    "max_parallel_agents": project.resource_limits.max_parallel_agents,
                    "max_parallel_cycles": project.resource_limits.max_parallel_cycles,
                    "max_memory_mb": project.resource_limits.max_memory_mb,
                    "max_disk_mb": project.resource_limits.max_disk_mb,
                    "cpu_priority": project.resource_limits.cpu_priority
                },
                "ai_settings": project.ai_settings,
                "work_hours": project.work_hours,
                "dependencies": [
                    {
                        "target_project": dep.target_project,
                        "dependency_type": dep.dependency_type,
                        "description": dep.description,
                        "criticality": dep.criticality
                    }
                    for dep in project.dependencies
                ],
                "state": project_state
            }
            projects.append(project_info)
        
        return jsonify({
            "multi_project_enabled": True,
            "projects": projects,
            "total_count": len(projects),
            "active_count": len([p for p in projects if p["status"] == "active"])
        })
        
    except Exception as e:
        logger.error(f"Error getting projects: {e}")
        return jsonify({"error": "Failed to get projects"}), 500


@app.route('/api/projects/<project_name>/switch', methods=['POST'])
def switch_project(project_name):
    """Switch active project context"""
    if not MULTI_PROJECT_AVAILABLE or not multi_project_manager:
        return jsonify({"error": "Multi-project management not available"}), 503
    
    try:
        # Validate project exists
        project = multi_project_manager.get_project(project_name)
        if not project:
            return jsonify({"error": f"Project '{project_name}' not found"}), 404
        
        # Get session ID from request
        data = request.get_json() or {}
        session_id = data.get('session_id', request.headers.get('X-Session-ID', 'default'))
        
        # Update active project for this session
        old_project = active_project_sessions.get(session_id)
        active_project_sessions[session_id] = project_name
        
        # Join/leave project rooms
        if old_project and old_project != project_name:
            if old_project in project_rooms:
                project_rooms[old_project].discard(session_id)
        
        if project_name not in project_rooms:
            project_rooms[project_name] = set()
        project_rooms[project_name].add(session_id)
        
        # Load project state
        project_state = load_project_state(project_name, project.path)
        
        # Emit project switched event
        socketio.emit('project_switched', {
            'old_project': old_project,
            'new_project': project_name,
            'session_id': session_id,
            'timestamp': datetime.now().isoformat(),
            'project_state': project_state
        }, room=session_id)
        
        return jsonify({
            "success": True,
            "old_project": old_project,
            "new_project": project_name,
            "session_id": session_id,
            "project_state": project_state
        })
        
    except Exception as e:
        logger.error(f"Error switching to project {project_name}: {e}")
        return jsonify({"error": f"Failed to switch to project: {str(e)}"}), 500


@app.route('/api/projects/<project_name>/state')
def get_project_state(project_name):
    """Get project-specific state"""
    if not MULTI_PROJECT_AVAILABLE or not multi_project_manager:
        return jsonify({"error": "Multi-project management not available"}), 503
    
    try:
        # Validate project exists
        project = multi_project_manager.get_project(project_name)
        if not project:
            return jsonify({"error": f"Project '{project_name}' not found"}), 404
        
        # Load project state
        project_state = load_project_state(project_name, project.path)
        
        return jsonify({
            "project_name": project_name,
            "state": project_state,
            "last_updated": datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error getting state for project {project_name}: {e}")
        return jsonify({"error": f"Failed to get project state: {str(e)}"}), 500


@app.route('/api/projects/<project_name>/config')
def get_project_config(project_name):
    """Get project configuration"""
    if not MULTI_PROJECT_AVAILABLE or not multi_project_manager:
        return jsonify({"error": "Multi-project management not available"}), 503
    
    try:
        # Validate project exists
        project = multi_project_manager.get_project(project_name)
        if not project:
            return jsonify({"error": f"Project '{project_name}' not found"}), 404
        
        # Return sanitized project configuration
        config = {
            "name": project.name,
            "path": project.path,
            "status": project.status.value,
            "priority": project.priority.value,
            "description": project.description,
            "git_url": project.git_url,
            "owner": project.owner,
            "team": project.team,
            "discord_channel": project.discord_channel,
            "tags": project.tags,
            "work_hours": project.work_hours,
            "ai_settings": project.ai_settings,
            "resource_limits": {
                "max_parallel_agents": project.resource_limits.max_parallel_agents,
                "max_parallel_cycles": project.resource_limits.max_parallel_cycles,
                "max_memory_mb": project.resource_limits.max_memory_mb,
                "max_disk_mb": project.resource_limits.max_disk_mb,
                "cpu_priority": project.resource_limits.cpu_priority
            },
            "dependencies": [
                {
                    "target_project": dep.target_project,
                    "dependency_type": dep.dependency_type,
                    "description": dep.description,
                    "criticality": dep.criticality
                }
                for dep in project.dependencies
            ],
            "created_at": project.created_at.isoformat(),
            "last_activity": project.last_activity.isoformat() if project.last_activity else None,
            "version": project.version
        }
        
        return jsonify(config)
        
    except Exception as e:
        logger.error(f"Error getting config for project {project_name}: {e}")
        return jsonify({"error": f"Failed to get project config: {str(e)}"}), 500


@app.route('/api/projects/discover', methods=['POST'])
def discover_projects():
    """Discover potential projects in specified paths"""
    if not MULTI_PROJECT_AVAILABLE or not multi_project_manager:
        return jsonify({"error": "Multi-project management not available"}), 503
    
    try:
        data = request.get_json()
        if not data or 'search_paths' not in data:
            return jsonify({"error": "search_paths is required"}), 400
        
        search_paths = data['search_paths']
        if not isinstance(search_paths, list):
            return jsonify({"error": "search_paths must be a list"}), 400
        
        discovered = multi_project_manager.discover_projects(search_paths)
        
        return jsonify({
            "discovered_projects": discovered,
            "total_count": len(discovered)
        })
        
    except Exception as e:
        logger.error(f"Error discovering projects: {e}")
        return jsonify({"error": f"Failed to discover projects: {str(e)}"}), 500


@app.route('/api/projects/register', methods=['POST'])
def register_project():
    """Register a new project"""
    if not MULTI_PROJECT_AVAILABLE or not multi_project_manager:
        return jsonify({"error": "Multi-project management not available"}), 503
    
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No data provided"}), 400
        
        name = data.get('name')
        path = data.get('path')
        
        if not name or not path:
            return jsonify({"error": "name and path are required"}), 400
        
        # Extract additional project configuration
        project_kwargs = {}
        optional_fields = [
            'description', 'git_url', 'owner', 'team', 'discord_channel', 
            'tags', 'priority', 'status'
        ]
        
        for field in optional_fields:
            if field in data:
                project_kwargs[field] = data[field]
        
        # Handle nested objects
        if 'resource_limits' in data:
            from multi_project_config import ResourceLimits
            project_kwargs['resource_limits'] = ResourceLimits(**data['resource_limits'])
        
        if 'ai_settings' in data:
            project_kwargs['ai_settings'] = data['ai_settings']
        
        if 'work_hours' in data:
            project_kwargs['work_hours'] = data['work_hours']
        
        # Register project
        project = multi_project_manager.register_project(name, path, **project_kwargs)
        
        # Initialize project room
        if name not in project_rooms:
            project_rooms[name] = set()
        
        # Emit project registered event
        socketio.emit('project_registered', {
            'project_name': name,
            'project_path': path,
            'timestamp': datetime.now().isoformat()
        })
        
        return jsonify({
            "success": True,
            "message": f"Project '{name}' registered successfully",
            "project": {
                "name": project.name,
                "path": project.path,
                "status": project.status.value,
                "priority": project.priority.value,
                "created_at": project.created_at.isoformat()
            }
        })
        
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        logger.error(f"Error registering project: {e}")
        return jsonify({"error": f"Failed to register project: {str(e)}"}), 500


def load_project_state(project_name: str, project_path: str) -> Dict[str, Any]:
    """Load project state from .orch-state directory"""
    try:
        from pathlib import Path
        
        state_dir = Path(project_path) / ".orch-state"
        status_file = state_dir / "status.json"
        
        if not status_file.exists():
            return {
                "workflow_state": "IDLE",
                "tdd_cycles": {},
                "last_updated": None,
                "transition_history": [],
                "initialized": False
            }
        
        with open(status_file, 'r') as f:
            import json
            state_data = json.load(f)
        
        return {
            "workflow_state": state_data.get("workflow_state", "IDLE"),
            "tdd_cycles": state_data.get("tdd_cycles", {}),
            "last_updated": state_data.get("last_updated"),
            "transition_history": state_data.get("transition_history", [])[-10:],  # Last 10 transitions
            "initialized": True,
            "project_name": project_name
        }
        
    except Exception as e:
        logger.error(f"Error loading state for project {project_name}: {e}")
        return {
            "workflow_state": "IDLE",
            "tdd_cycles": {},
            "last_updated": None,
            "transition_history": [],
            "initialized": False,
            "error": str(e)
        }


@app.route('/debug')
def debug_info():
    """Debug information endpoint"""
    debug_data = {
        "broadcaster_clients": len(broadcaster.clients),
        "socketio_clients": len(socketio.server.manager.rooms.get("/", {})),
        "transition_history_count": len(broadcaster.transition_history),
        "memory_usage": {
            "transition_history": len(str(broadcaster.transition_history)),
            "tdd_cycles": len(str(broadcaster.tdd_cycles))
        },
        "performance": {
            "uptime_seconds": (datetime.now() - datetime.fromisoformat("2024-01-01T00:00:00")).total_seconds()
        }
    }
    
    # Add multi-project debug information
    if MULTI_PROJECT_AVAILABLE and multi_project_manager:
        debug_data["multi_project"] = {
            "enabled": True,
            "total_projects": len(multi_project_manager.projects),
            "active_projects": len(multi_project_manager.get_active_projects()),
            "project_rooms": {
                project_name: len(sessions)
                for project_name, sessions in project_rooms.items()
            },
            "active_sessions": len(active_project_sessions),
            "room_count": len(project_rooms)
        }
    else:
        debug_data["multi_project"] = {
            "enabled": False,
            "reason": "Multi-project management not available"
        }
    
    return jsonify(debug_data)


# =====================================================
# Context Management Endpoints
# =====================================================

@app.route('/api/context/status')
def get_context_status():
    """Get current context management status"""
    if not CONTEXT_MANAGEMENT_AVAILABLE:
        return jsonify({"context_management_available": False, "reason": "Context management not available"}), 200
    
    try:
        factory = get_context_manager_factory()
        current_mode = factory.get_current_mode()
        current_manager = factory.get_current_manager()
        
        status = {
            "context_management_available": True,
            "current_mode": current_mode.value if current_mode else None,
            "factory_status": factory.get_detection_status(),
            "mode_info": factory.get_mode_info(),
            "manager_active": current_manager is not None
        }
        
        # Add performance metrics if manager is active
        if current_manager:
            status["performance_metrics"] = current_manager.get_performance_metrics()
        
        return jsonify(status)
        
    except Exception as e:
        logger.error(f"Error getting context status: {e}")
        return jsonify({"error": "Failed to get context status"}), 500


@app.route('/api/context/modes')
def get_context_modes():
    """Get available context modes and their information"""
    if not CONTEXT_MANAGEMENT_AVAILABLE:
        return jsonify({"context_management_available": False, "modes": {}}), 200
    
    try:
        factory = get_context_manager_factory()
        
        modes_info = {}
        for mode in ContextMode:
            modes_info[mode.value] = factory.get_mode_info(mode)
        
        return jsonify({
            "context_management_available": True,
            "modes": modes_info,
            "current_mode": factory.get_current_mode().value if factory.get_current_mode() else None
        })
        
    except Exception as e:
        logger.error(f"Error getting context modes: {e}")
        return jsonify({"error": "Failed to get context modes"}), 500


@app.route('/api/context/switch', methods=['POST'])
def switch_context_mode():
    """Switch context management mode"""
    async def _switch():
        try:
            data = request.get_json()
            if not data or 'mode' not in data:
                return {"success": False, "error": "Mode is required"}
            
            mode_str = data['mode']
            try:
                new_mode = ContextMode(mode_str)
            except ValueError:
                return {"success": False, "error": f"Invalid mode: {mode_str}"}
            
            factory = get_context_manager_factory()
            old_mode = factory.get_current_mode()
            
            # Switch mode
            manager = await factory.switch_mode(new_mode)
            
            return {
                "success": True,
                "message": f"Successfully switched to {new_mode.value} mode",
                "old_mode": old_mode.value if old_mode else None,
                "new_mode": new_mode.value,
                "manager_type": type(manager).__name__
            }
            
        except Exception as e:
            logger.error(f"Error switching context mode: {e}")
            return {"success": False, "error": str(e)}
    
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(_switch())
        loop.close()
        
        if result.get("success"):
            # Emit context mode change event
            socketio.emit('context_mode_changed', {
                "type": "context_mode_switch",
                "old_mode": result.get("old_mode"),
                "new_mode": result.get("new_mode"),
                "timestamp": datetime.now().isoformat()
            })
            
            return jsonify(result)
        else:
            return jsonify(result), 400
            
    except Exception as e:
        logger.error(f"Error in switch_context_mode endpoint: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/api/context/config', methods=['GET', 'PUT'])
def manage_context_config():
    """Get or update context configuration"""
    if request.method == 'GET':
        try:
            factory = get_context_manager_factory()
            config_summary = factory.config.get_summary()
            validation = factory.config.validate()
            
            return jsonify({
                "config": config_summary,
                "validation": validation,
                "config_path": factory.config_path
            })
            
        except Exception as e:
            logger.error(f"Error getting context config: {e}")
            return jsonify({"error": "Failed to get configuration"}), 500
    
    elif request.method == 'PUT':
        try:
            config_updates = request.get_json()
            if not config_updates:
                return jsonify({"error": "No configuration data provided"}), 400
            
            factory = get_context_manager_factory()
            
            # Update configuration
            new_config = factory.config.update_from_dict(config_updates)
            
            # Validate new configuration
            validation = new_config.validate()
            if validation["errors"]:
                return jsonify({
                    "error": "Configuration validation failed",
                    "details": validation["errors"],
                    "warnings": validation["warnings"]
                }), 400
            
            # Save new configuration
            factory.config = new_config
            factory.save_config()
            
            # Emit config change event
            socketio.emit('context_config_changed', {
                "type": "context_config_update",
                "timestamp": datetime.now().isoformat()
            })
            
            return jsonify({
                "success": True,
                "message": "Configuration updated successfully",
                "config": new_config.get_summary(),
                "warnings": validation["warnings"]
            })
            
        except Exception as e:
            logger.error(f"Error updating context config: {e}")
            return jsonify({"error": "Failed to update configuration"}), 500


@app.route('/api/context/performance')
def get_context_performance():
    """Get context management performance comparison"""
    async def _get_performance():
        try:
            factory = get_context_manager_factory()
            return await factory.get_performance_comparison()
        except Exception as e:
            logger.error(f"Error getting context performance: {e}")
            return {"error": str(e)}
    
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(_get_performance())
        loop.close()
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error in get_context_performance endpoint: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/api/context/test', methods=['POST'])
def test_context_preparation():
    """Test context preparation with current mode"""
    async def _test():
        try:
            data = request.get_json() or {}
            agent_type = data.get('agent_type', 'CodeAgent')
            task_description = data.get('task', 'Test task for context preparation')
            
            factory = get_context_manager_factory()
            manager = await factory.create_context_manager()
            
            if not manager:
                return {"success": False, "error": "No context manager available"}
            
            # Create test task
            test_task = {
                "description": task_description,
                "story_id": "test-story",
                "current_state": "WRITE_TEST"
            }
            
            # Measure preparation time
            start_time = time.time()
            context = await manager.prepare_context(agent_type, test_task)
            preparation_time = time.time() - start_time
            
            return {
                "success": True,
                "mode": factory.get_current_mode().value,
                "preparation_time": preparation_time,
                "token_usage": {
                    "total_used": context.token_usage.total_used,
                    "core_task_used": context.token_usage.core_task_used
                },
                "file_count": len(context.file_contents) if context.file_contents else 0,
                "compression_applied": getattr(context, 'compression_applied', False),
                "cache_hit": getattr(context, 'cache_hit', False)
            }
            
        except Exception as e:
            logger.error(f"Error testing context preparation: {e}")
            return {"success": False, "error": str(e)}
    
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(_test())
        loop.close()
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error in test_context_preparation endpoint: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


# =====================================================
# Agent Interface Management Endpoints
# =====================================================

@app.route('/api/interfaces')
def get_interfaces():
    """Get status of all agent interfaces"""
    try:
        status = interface_manager.get_interface_status()
        return jsonify(status)
    except Exception as e:
        logger.error(f"Error getting interface status: {e}")
        return jsonify({"error": "Failed to get interface status"}), 500


@app.route('/api/interfaces/<interface_type>/switch', methods=['POST'])
def switch_interface(interface_type):
    """Switch to a different agent interface"""
    async def _switch():
        try:
            result = await interface_manager.switch_interface(interface_type)
            return result
        except Exception as e:
            logger.error(f"Error switching interface: {e}")
            return {"success": False, "error": str(e)}
    
    # Run async function in event loop
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(_switch())
        loop.close()
        
        if result.get("success"):
            # Emit interface change event via WebSocket
            socketio.emit('interface_changed', {
                "type": "interface_switch",
                "old_interface": result.get("old_interface"),
                "new_interface": result.get("active_interface"),
                "timestamp": datetime.now().isoformat()
            })
            
            return jsonify(result)
        else:
            return jsonify(result), 400
            
    except Exception as e:
        logger.error(f"Error in switch_interface endpoint: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/api/interfaces/<interface_type>/test', methods=['POST'])
def test_interface(interface_type):
    """Test a specific agent interface"""
    async def _test():
        try:
            # Initialize interface if needed
            if interface_type not in interface_manager.interfaces:
                await interface_manager.initialize_interface(interface_type)
            
            # Get interface and test it
            interface = interface_manager.interfaces.get(interface_type)
            if not interface:
                return {"success": False, "error": "Interface not available"}
            
            return await interface.test_connection()
        except Exception as e:
            logger.error(f"Error testing interface: {e}")
            return {"success": False, "error": str(e)}
    
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(_test())
        loop.close()
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error in test_interface endpoint: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/api/interfaces/<interface_type>/config', methods=['GET', 'PUT'])
def manage_interface_config(interface_type):
    """Get or update interface configuration"""
    if request.method == 'GET':
        try:
            if interface_type not in interface_manager.configs:
                return jsonify({"error": "Interface not found"}), 404
            
            config = interface_manager.configs[interface_type]
            return jsonify(config.mask_sensitive_data())
            
        except Exception as e:
            logger.error(f"Error getting interface config: {e}")
            return jsonify({"error": "Failed to get configuration"}), 500
    
    elif request.method == 'PUT':
        try:
            config_updates = request.get_json()
            if not config_updates:
                return jsonify({"error": "No configuration data provided"}), 400
            
            # Security validation
            security_audit = audit_operation('configure', interface_type, config_updates)
            if not security_audit.valid:
                logger.warning(f"Configuration validation failed for {interface_type}: {security_audit.errors}")
                return jsonify({
                    "error": "Configuration validation failed",
                    "details": security_audit.errors,
                    "warnings": security_audit.warnings
                }), 400
            
            # Additional configuration validation
            config_validation = validate_configuration(config_updates, interface_type)
            if not config_validation.valid:
                logger.warning(f"Configuration security check failed for {interface_type}: {config_validation.errors}")
                return jsonify({
                    "error": "Configuration security check failed",
                    "details": config_validation.errors,
                    "warnings": config_validation.warnings
                }), 400
            
            # Use sanitized data if available
            sanitized_config = config_validation.sanitized_data or config_updates
            
            # Mask sensitive data in logs
            log_config = {k: mask_api_key(v) if k == 'api_key' else v for k, v in sanitized_config.items()}
            logger.info(f"Updating configuration for {interface_type}: {log_config}")
            
            result = interface_manager.update_interface_config(interface_type, sanitized_config)
            
            if result.get("success"):
                # Emit config change event
                socketio.emit('interface_config_changed', {
                    "type": "config_update",
                    "interface_type": interface_type,
                    "needs_reinitialization": result.get("needs_reinitialization", False),
                    "timestamp": datetime.now().isoformat()
                })
                
                return jsonify(result)
            else:
                return jsonify(result), 400
                
        except Exception as e:
            logger.error(f"Error updating interface config: {e}")
            return jsonify({"error": "Failed to update configuration"}), 500


@app.route('/api/interfaces/<interface_type>/initialize', methods=['POST'])
def initialize_interface(interface_type):
    """Initialize a specific interface"""
    async def _initialize():
        try:
            return await interface_manager.initialize_interface(interface_type)
        except Exception as e:
            logger.error(f"Error initializing interface: {e}")
            return False
    
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        success = loop.run_until_complete(_initialize())
        loop.close()
        
        if success:
            socketio.emit('interface_initialized', {
                "type": "interface_init",
                "interface_type": interface_type,
                "timestamp": datetime.now().isoformat()
            })
            
            return jsonify({"success": True, "message": f"Interface {interface_type} initialized"})
        else:
            return jsonify({"success": False, "error": "Initialization failed"}), 500
            
    except Exception as e:
        logger.error(f"Error in initialize_interface endpoint: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/api/interfaces/generate', methods=['POST'])
def generate_with_interface():
    """Generate content using the active agent interface"""
    async def _generate():
        try:
            data = request.get_json()
            if not data:
                return {"success": False, "error": "No data provided"}
            
            prompt = data.get("prompt")
            agent_type_str = data.get("agent_type", "CODE")
            context = data.get("context", {})
            
            if not prompt:
                return {"success": False, "error": "Prompt is required"}
            
            # Security validation for prompt
            prompt_validation = sanitize_prompt(prompt)
            if not prompt_validation.valid:
                logger.warning(f"Prompt validation failed: {prompt_validation.errors}")
                return {
                    "success": False, 
                    "error": "Prompt validation failed",
                    "details": prompt_validation.errors
                }
            
            # Use sanitized prompt
            sanitized_prompt = prompt_validation.sanitized_data.get('prompt', prompt)
            
            # Security audit
            security_audit = audit_operation('generate', interface_manager.active_interface or 'unknown', {
                'prompt': sanitized_prompt,
                'agent_type': agent_type_str
            })
            
            # Log security warnings but allow operation to continue
            if security_audit.warnings:
                logger.warning(f"Generation security warnings: {security_audit.warnings}")
            
            if security_audit.security_level == SecurityLevel.CRITICAL:
                logger.error(f"Critical security issue in generation request: {security_audit.errors}")
                return {
                    "success": False,
                    "error": "Request blocked due to security concerns",
                    "details": security_audit.errors
                }
            
            # Convert agent type string to enum
            try:
                agent_type = AgentType(agent_type_str)
            except ValueError:
                return {"success": False, "error": f"Invalid agent type: {agent_type_str}"}
            
            # Get active interface
            interface = await interface_manager.get_active_interface()
            if not interface:
                return {"success": False, "error": "No active interface available"}
            
            # Generate response
            response = await interface.generate_response(sanitized_prompt, agent_type, context)
            
            return {
                "success": True,
                "response": response,
                "interface_type": interface_manager.active_interface,
                "agent_type": agent_type_str,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error generating response: {e}")
            return {"success": False, "error": str(e)}
    
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(_generate())
        loop.close()
        
        if result.get("success"):
            return jsonify(result)
        else:
            return jsonify(result), 400
            
    except Exception as e:
        logger.error(f"Error in generate_with_interface endpoint: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/api/interfaces/analyze', methods=['POST'])
def analyze_with_interface():
    """Analyze code using the active agent interface"""
    async def _analyze():
        try:
            data = request.get_json()
            if not data:
                return {"success": False, "error": "No data provided"}
            
            code = data.get("code")
            analysis_type = data.get("analysis_type", "review")
            agent_type_str = data.get("agent_type", "CODE")
            
            if not code:
                return {"success": False, "error": "Code is required"}
            
            # Security validation for code
            code_validation = sanitize_code(code)
            if not code_validation.valid:
                logger.warning(f"Code validation failed: {code_validation.errors}")
                return {
                    "success": False,
                    "error": "Code validation failed",
                    "details": code_validation.errors
                }
            
            # Use sanitized code
            sanitized_code = code_validation.sanitized_data.get('code', code)
            
            # Security audit
            security_audit = audit_operation('analyze', interface_manager.active_interface or 'unknown', {
                'code': sanitized_code,
                'analysis_type': analysis_type,
                'agent_type': agent_type_str
            })
            
            # Log security warnings but allow operation to continue
            if security_audit.warnings:
                logger.warning(f"Analysis security warnings: {security_audit.warnings}")
            
            if security_audit.security_level == SecurityLevel.CRITICAL:
                logger.error(f"Critical security issue in analysis request: {security_audit.errors}")
                return {
                    "success": False,
                    "error": "Request blocked due to security concerns",
                    "details": security_audit.errors
                }
            
            # Convert agent type string to enum
            try:
                agent_type = AgentType(agent_type_str)
            except ValueError:
                return {"success": False, "error": f"Invalid agent type: {agent_type_str}"}
            
            # Get active interface
            interface = await interface_manager.get_active_interface()
            if not interface:
                return {"success": False, "error": "No active interface available"}
            
            # Analyze code
            analysis = await interface.analyze_code(sanitized_code, analysis_type, agent_type)
            
            return {
                "success": True,
                "analysis": analysis,
                "interface_type": interface_manager.active_interface,
                "agent_type": agent_type_str,
                "analysis_type": analysis_type,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error analyzing code: {e}")
            return {"success": False, "error": str(e)}
    
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(_analyze())
        loop.close()
        
        if result.get("success"):
            return jsonify(result)
        else:
            return jsonify(result), 400
            
    except Exception as e:
        logger.error(f"Error in analyze_with_interface endpoint: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


# =====================================================
# TDD Cycle REST API Endpoints
# =====================================================

@app.route('/api/tdd/cycles')
def get_all_tdd_cycles():
    """Get all active TDD cycles"""
    try:
        from state_broadcaster import get_all_tdd_cycles, get_tdd_metrics
        
        cycles = get_all_tdd_cycles()
        metrics = get_tdd_metrics()
        
        return jsonify({
            "success": True,
            "cycles": cycles,
            "metrics": metrics,
            "timestamp": datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error getting TDD cycles: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/api/tdd/cycles/<story_id>')
def get_tdd_cycle(story_id):
    """Get TDD cycle for specific story"""
    try:
        from state_broadcaster import get_tdd_cycle_status
        
        cycle = get_tdd_cycle_status(story_id)
        if cycle:
            return jsonify({
                "success": True,
                "cycle": cycle,
                "timestamp": datetime.now().isoformat()
            })
        else:
            return jsonify({
                "success": False,
                "error": f"No TDD cycle found for story {story_id}"
            }), 404
        
    except Exception as e:
        logger.error(f"Error getting TDD cycle for story {story_id}: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/api/tdd/cycles', methods=['POST'])
def create_tdd_cycle():
    """Create a new TDD cycle"""
    try:
        data = request.get_json()
        story_id = data.get('story_id')
        project = data.get('project', 'default')
        
        if not story_id:
            return jsonify({"success": False, "error": "Story ID is required"}), 400
        
        # Import here to avoid circular imports
        from state_machine import StateMachine
        
        # Create state machine instance
        state_machine = StateMachine()
        
        # Start TDD cycle
        cycle_id = state_machine.start_tdd_cycle(story_id, project_name=project)
        
        return jsonify({
            "success": True,
            "cycle_id": cycle_id,
            "story_id": story_id,
            "project": project,
            "timestamp": datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error creating TDD cycle: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/api/tdd/cycles/<cycle_id>/transition', methods=['POST'])
def transition_tdd_cycle(cycle_id):
    """Transition TDD cycle to new state"""
    try:
        data = request.get_json()
        new_state = data.get('new_state')
        project = data.get('project', 'default')
        
        if not new_state:
            return jsonify({"success": False, "error": "New state is required"}), 400
        
        # Import here to avoid circular imports
        from state_machine import StateMachine
        
        # Create state machine instance
        state_machine = StateMachine()
        
        # Transition TDD cycle
        success = state_machine.transition_tdd_cycle(cycle_id, new_state, project)
        
        if success:
            return jsonify({
                "success": True,
                "cycle_id": cycle_id,
                "new_state": new_state,
                "timestamp": datetime.now().isoformat()
            })
        else:
            return jsonify({
                "success": False,
                "error": f"Failed to transition cycle {cycle_id} to {new_state}"
            }), 400
        
    except Exception as e:
        logger.error(f"Error transitioning TDD cycle {cycle_id}: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/api/tdd/cycles/<cycle_id>/complete', methods=['POST'])
def complete_tdd_cycle(cycle_id):
    """Complete a TDD cycle"""
    try:
        data = request.get_json() or {}
        project = data.get('project', 'default')
        
        # Import here to avoid circular imports
        from state_machine import StateMachine
        
        # Create state machine instance
        state_machine = StateMachine()
        
        # Complete TDD cycle
        success = state_machine.complete_tdd_cycle(cycle_id, project)
        
        if success:
            return jsonify({
                "success": True,
                "cycle_id": cycle_id,
                "completed_at": datetime.now().isoformat()
            })
        else:
            return jsonify({
                "success": False,
                "error": f"Failed to complete cycle {cycle_id}"
            }), 400
        
    except Exception as e:
        logger.error(f"Error completing TDD cycle {cycle_id}: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/api/tdd/cycles/<cycle_id>/progress', methods=['POST'])
def update_tdd_progress(cycle_id):
    """Update TDD cycle progress"""
    try:
        data = request.get_json()
        progress_data = data.get('progress', {})
        story_id = data.get('story_id')
        project = data.get('project', 'default')
        
        if not story_id:
            return jsonify({"success": False, "error": "Story ID is required"}), 400
        
        # Import here to avoid circular imports
        from state_broadcaster import emit_tdd_progress_update
        
        # Emit progress update
        emit_tdd_progress_update(story_id, cycle_id, progress_data, project)
        
        return jsonify({
            "success": True,
            "cycle_id": cycle_id,
            "story_id": story_id,
            "progress": progress_data,
            "timestamp": datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error updating TDD progress for cycle {cycle_id}: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/api/tdd/metrics')
def get_tdd_metrics():
    """Get TDD cycle metrics and statistics"""
    try:
        from state_broadcaster import get_tdd_metrics
        
        metrics = get_tdd_metrics()
        
        return jsonify({
            "success": True,
            "metrics": metrics,
            "timestamp": datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error getting TDD metrics: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/api/interfaces/types')
def get_interface_types():
    """Get available interface types"""
    return jsonify({
        "interface_types": [
            {
                "type": InterfaceType.CLAUDE_CODE.value,
                "name": "Claude Code",
                "description": "Uses Claude Code CLI with tool restrictions",
                "requires_api_key": False,
                "features": ["Tool restrictions", "Agent-specific security", "Local execution"]
            },
            {
                "type": InterfaceType.ANTHROPIC_API.value,
                "name": "Anthropic API",
                "description": "Direct Anthropic API integration",
                "requires_api_key": True,
                "features": ["Direct API access", "High performance", "Latest models"]
            },
            {
                "type": InterfaceType.MOCK.value,
                "name": "Mock Interface",
                "description": "Mock interface for testing and demonstrations",
                "requires_api_key": False,
                "features": ["Testing", "Demo mode", "No external dependencies"]
            }
        ],
        "agent_types": [
            {
                "type": AgentType.ORCHESTRATOR.value,
                "name": "Orchestrator",
                "description": "Coordinates workflow and manages other agents"
            },
            {
                "type": AgentType.DESIGN.value,
                "name": "Design Agent",
                "description": "Creates architecture and technical specifications"
            },
            {
                "type": AgentType.CODE.value,
                "name": "Code Agent",
                "description": "Implements features and writes code"
            },
            {
                "type": AgentType.QA.value,
                "name": "QA Agent",
                "description": "Creates and runs tests for quality assurance"
            },
            {
                "type": AgentType.DATA.value,
                "name": "Data Agent",
                "description": "Analyzes data and generates insights"
            }
        ]
    })


# =====================================================
# Discord-Style Chat API Endpoints
# =====================================================

@app.route('/api/chat/send', methods=['POST'])
def send_chat_message():
    """Handle incoming chat commands with collaboration support"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No data provided"}), 400
        
        message = data.get('message', '').strip()
        user_id = data.get('user_id', 'anonymous')
        username = data.get('username', 'User')
        session_id = data.get('session_id')
        project_name = data.get('project_name', 'default')
        
        if not message:
            return jsonify({"error": "Message cannot be empty"}), 400
        
        # Create message object
        chat_message = {
            "id": generate_uuid(),
            "user_id": user_id,
            "username": username,
            "message": message,
            "timestamp": datetime.now().isoformat(),
            "type": "user",
            "session_id": session_id,
            "project_name": project_name
        }
        
        # Add to chat history
        chat_history.append(chat_message)
        
        # Keep only last 100 messages
        if len(chat_history) > 100:
            chat_history.pop(0)
        
        # Emit to all connected clients
        socketio.emit('new_chat_message', chat_message)
        
        # Check if this is a command (starts with /)
        if message.startswith('/'):
            # Show typing indicator
            socketio.emit('bot_typing', {"typing": True})
            
            # Process command asynchronously with collaboration support
            def process_async():
                try:
                    # Try collaborative processing first
                    if COLLABORATION_AVAILABLE and session_id:
                        try:
                            collaboration_manager = get_collaboration_manager()
                            
                            async def async_wrapper():
                                from command_processor import get_processor
                                processor = get_processor()
                                return await processor.process_collaborative_command(
                                    message, user_id, project_name, session_id
                                )
                            
                            # Run async in event loop
                            try:
                                loop = asyncio.new_event_loop()
                                asyncio.set_event_loop(loop)
                                result = loop.run_until_complete(async_wrapper())
                                loop.close()
                            except Exception as e:
                                logger.error(f"Error in collaborative processing: {e}")
                                # Fall back to regular processing
                                from command_processor import process_command
                                result = process_command(message, user_id)
                                result["collaboration_fallback"] = True
                                
                        except Exception as e:
                            logger.error(f"Collaboration manager error: {e}")
                            # Fall back to regular processing
                            from command_processor import process_command
                            result = process_command(message, user_id)
                            result["collaboration_error"] = str(e)
                    else:
                        # Regular command processing
                        from command_processor import process_command
                        result = process_command(message, user_id)
                    
                    # Create bot response
                    bot_response = {
                        "id": generate_uuid(),
                        "user_id": "bot",
                        "username": "Agent Bot",
                        "message": result.get('response', 'Command processed'),
                        "timestamp": datetime.now().isoformat(),
                        "type": "bot",
                        "command_result": result,
                        "collaboration_enabled": COLLABORATION_AVAILABLE and session_id is not None
                    }
                    
                    # Add to chat history
                    chat_history.append(bot_response)
                    
                    # Stop typing and send response
                    socketio.emit('bot_typing', {"typing": False})
                    socketio.emit('command_response', bot_response)
                    
                    # Emit state change if applicable
                    if result.get('new_state'):
                        socketio.emit('workflow_state_change', {
                            'old_state': result.get('old_state'),
                            'new_state': result.get('new_state'),
                            'user_id': user_id,
                            'command': message,
                            'timestamp': datetime.now().isoformat()
                        })
                    
                except Exception as e:
                    logger.error(f"Error processing command: {e}")
                    error_response = {
                        "id": generate_uuid(),
                        "user_id": "bot",
                        "username": "Agent Bot",
                        "message": f"Error processing command: {str(e)}",
                        "timestamp": datetime.now().isoformat(),
                        "type": "bot",
                        "error": True
                    }
                    chat_history.append(error_response)
                    socketio.emit('bot_typing', {"typing": False})
                    socketio.emit('command_response', error_response)
            
            # Run in background thread
            import threading
            threading.Thread(target=process_async, daemon=True).start()
        
        return jsonify({
            "success": True,
            "message_id": chat_message["id"],
            "collaboration_enabled": COLLABORATION_AVAILABLE and session_id is not None
        })
        
    except Exception as e:
        logger.error(f"Error sending chat message: {e}")
        return jsonify({"error": "Failed to send message"}), 500


@app.route('/api/chat/history')
def get_chat_history():
    """Retrieve chat message history"""
    try:
        limit = request.args.get('limit', 50, type=int)
        limit = min(limit, 100)  # Max 100 messages
        
        # Return most recent messages
        recent_messages = chat_history[-limit:] if chat_history else []
        
        return jsonify({
            "messages": recent_messages,
            "total_count": len(chat_history)
        })
        
    except Exception as e:
        logger.error(f"Error getting chat history: {e}")
        return jsonify({"error": "Failed to get chat history"}), 500


@app.route('/api/chat/autocomplete')
def get_command_autocomplete():
    """Provide command autocomplete suggestions with contextual awareness"""
    try:
        query = request.args.get('query', '').strip().lower()
        current_state = request.args.get('state', 'IDLE')
        user_id = request.args.get('user_id', 'default')
        project_name = request.args.get('project_name', 'default')
        
        # Try to get contextual suggestions
        if CHAT_SYNC_AVAILABLE:
            try:
                # Try agent_workflow first, then lib for backward compatibility
                try:
                    from agent_workflow.context.chat_state_sync import get_contextual_commands
                except ImportError:
                    from lib.chat_state_sync import get_contextual_commands
                contextual_commands = get_contextual_commands(current_state, user_id, project_name)
                
                # Convert to autocomplete format
                suggestions = [
                    {
                        "command": cmd["command"],
                        "description": cmd["description"],
                        "usage": cmd.get("usage", cmd["command"]),
                        "priority": cmd.get("priority", 0),
                        "category": cmd.get("category", "general")
                    }
                    for cmd in contextual_commands
                ]
            except Exception as e:
                logger.error(f"Error getting contextual commands: {e}")
                suggestions = []
        else:
            suggestions = []
        
        # Fallback to basic commands if contextual not available
        if not suggestions:
            suggestions = [
                {"command": "/epic", "description": "Define a new high-level initiative", "category": "workflow"},
                {"command": "/approve", "description": "Approve proposed stories or tasks", "category": "approval"},
                {"command": "/sprint plan", "description": "Plan a new sprint", "category": "planning"},
                {"command": "/sprint start", "description": "Start the current sprint", "category": "execution"},
                {"command": "/sprint status", "description": "Show sprint status", "category": "monitoring"},
                {"command": "/sprint pause", "description": "Pause the current sprint", "category": "control"},
                {"command": "/sprint resume", "description": "Resume a paused sprint", "category": "control"},
                {"command": "/backlog view", "description": "View the product backlog", "category": "management"},
                {"command": "/backlog add_story", "description": "Add a new story to backlog", "category": "management"},
                {"command": "/backlog prioritize", "description": "Prioritize backlog items", "category": "management"},
                {"command": "/state", "description": "Show current workflow state", "category": "information"},
                {"command": "/project register", "description": "Register a new project", "category": "setup"},
                {"command": "/request_changes", "description": "Request changes to a PR", "category": "review"},
                {"command": "/help", "description": "Show available commands", "category": "help"}
            ]
        
        # Filter based on query
        if query:
            filtered_commands = [
                cmd for cmd in suggestions 
                if query in cmd["command"].lower() or query in cmd["description"].lower()
            ]
        else:
            filtered_commands = suggestions[:10]  # Show first 10 if no query
        
        return jsonify({
            "suggestions": filtered_commands[:10],  # Limit to 10 suggestions
            "contextual": CHAT_SYNC_AVAILABLE,
            "current_state": current_state
        })
        
    except Exception as e:
        logger.error(f"Error getting autocomplete suggestions: {e}")
        return jsonify({"error": "Failed to get suggestions"}), 500


# =====================================================
# Collaboration API Endpoints
# =====================================================

@app.route('/api/collaboration/join', methods=['POST'])
def join_collaboration():
    """Join a collaboration session"""
    if not COLLABORATION_AVAILABLE:
        return jsonify({"error": "Collaboration features not available"}), 503
    
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No data provided"}), 400
        
        user_id = data.get('user_id')
        project_name = data.get('project_name', 'default')
        permission_level = data.get('permission_level', 'contributor')
        
        if not user_id:
            return jsonify({"error": "User ID is required"}), 400
        
        # Convert permission level string to enum
        try:
            if permission_level == "admin":
                perm_enum = UserPermission.ADMIN
            elif permission_level == "maintainer":
                perm_enum = UserPermission.MAINTAINER
            elif permission_level == "viewer":
                perm_enum = UserPermission.VIEWER
            else:
                perm_enum = UserPermission.CONTRIBUTOR
        except Exception:
            perm_enum = UserPermission.CONTRIBUTOR
        
        # Join session
        async def join_async():
            collaboration_manager = get_collaboration_manager()
            return await collaboration_manager.join_session(user_id, project_name, perm_enum)
        
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            session_id = loop.run_until_complete(join_async())
            loop.close()
        except Exception as e:
            return jsonify({"error": f"Failed to join session: {str(e)}"}), 500
        
        # Emit collaboration event
        socketio.emit('collaboration_user_joined', {
            'user_id': user_id,
            'project_name': project_name,
            'session_id': session_id,
            'permission_level': permission_level,
            'timestamp': datetime.now().isoformat()
        })
        
        return jsonify({
            "success": True,
            "session_id": session_id,
            "user_id": user_id,
            "project_name": project_name,
            "permission_level": permission_level
        })
        
    except Exception as e:
        logger.error(f"Error joining collaboration: {e}")
        return jsonify({"error": "Failed to join collaboration"}), 500


@app.route('/api/collaboration/leave', methods=['POST'])
def leave_collaboration():
    """Leave a collaboration session"""
    if not COLLABORATION_AVAILABLE:
        return jsonify({"error": "Collaboration features not available"}), 503
    
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No data provided"}), 400
        
        session_id = data.get('session_id')
        if not session_id:
            return jsonify({"error": "Session ID is required"}), 400
        
        # Leave session
        async def leave_async():
            collaboration_manager = get_collaboration_manager()
            await collaboration_manager.leave_session(session_id)
        
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(leave_async())
            loop.close()
        except Exception as e:
            logger.error(f"Error leaving session: {e}")
        
        # Emit collaboration event
        socketio.emit('collaboration_user_left', {
            'session_id': session_id,
            'timestamp': datetime.now().isoformat()
        })
        
        return jsonify({"success": True})
        
    except Exception as e:
        logger.error(f"Error leaving collaboration: {e}")
        return jsonify({"error": "Failed to leave collaboration"}), 500


@app.route('/api/collaboration/status/<project_name>')
def get_collaboration_status(project_name):
    """Get collaboration status for a project"""
    if not COLLABORATION_AVAILABLE:
        return jsonify({"collaboration_enabled": False, "reason": "Not available"}), 200
    
    try:
        async def get_status_async():
            collaboration_manager = get_collaboration_manager()
            return await collaboration_manager.get_collaboration_status(project_name)
        
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            status = loop.run_until_complete(get_status_async())
            loop.close()
            return jsonify(status)
        except Exception as e:
            logger.error(f"Error getting collaboration status: {e}")
            return jsonify({"collaboration_enabled": False, "error": str(e)}), 500
        
    except Exception as e:
        logger.error(f"Error in collaboration status endpoint: {e}")
        return jsonify({"collaboration_enabled": False, "error": str(e)}), 500


@socketio.on('connect')
def handle_connect():
    """Handle new SocketIO client connection"""
    logger.info(f"SocketIO client connected: {request.sid}")
    
    # Send current state to new client
    current_state = broadcaster.get_current_state()
    emit('state_update', current_state)
    
    # Send multi-project status if available
    if MULTI_PROJECT_AVAILABLE and multi_project_manager:
        emit('multi_project_status', {
            'enabled': True,
            'project_count': len(multi_project_manager.projects),
            'projects': [
                {
                    'name': p.name,
                    'status': p.status.value,
                    'priority': p.priority.value
                }
                for p in multi_project_manager.list_projects()
            ]
        })
    else:
        emit('multi_project_status', {
            'enabled': False,
            'reason': 'Multi-project management not available'
        })


# =====================================================
# Multi-Project WebSocket Room Management
# =====================================================

@socketio.on('join_project')
def handle_join_project(data):
    """Handle client joining a project room"""
    if not MULTI_PROJECT_AVAILABLE or not multi_project_manager:
        emit('project_error', {"error": "Multi-project management not available"})
        return
    
    try:
        project_name = data.get('project_name')
        session_id = data.get('session_id', request.sid)
        
        if not project_name:
            emit('project_error', {"error": "project_name is required"})
            return
        
        # Validate project exists
        project = multi_project_manager.get_project(project_name)
        if not project:
            emit('project_error', {"error": f"Project '{project_name}' not found"})
            return
        
        # Leave current project room if any
        current_project = active_project_sessions.get(session_id)
        if current_project and current_project != project_name:
            if current_project in project_rooms:
                project_rooms[current_project].discard(session_id)
            leave_room(current_project)
        
        # Join new project room
        join_room(project_name)
        active_project_sessions[session_id] = project_name
        
        if project_name not in project_rooms:
            project_rooms[project_name] = set()
        project_rooms[project_name].add(session_id)
        
        # Load and send project state
        project_state = load_project_state(project_name, project.path)
        
        emit('project_joined', {
            'project_name': project_name,
            'session_id': session_id,
            'timestamp': datetime.now().isoformat(),
            'project_state': project_state,
            'room_members': len(project_rooms[project_name])
        })
        
        # Broadcast to project room that a new member joined
        emit('project_member_joined', {
            'session_id': session_id,
            'project_name': project_name,
            'timestamp': datetime.now().isoformat(),
            'room_members': len(project_rooms[project_name])
        }, room=project_name, include_self=False)
        
        logger.info(f"Session {session_id} joined project {project_name}")
        
    except Exception as e:
        logger.error(f"Error joining project: {e}")
        emit('project_error', {"error": f"Failed to join project: {str(e)}"})


@socketio.on('leave_project')
def handle_leave_project(data):
    """Handle client leaving a project room"""
    try:
        project_name = data.get('project_name') if data else None
        session_id = data.get('session_id', request.sid) if data else request.sid
        
        # If no project specified, leave current project
        if not project_name:
            project_name = active_project_sessions.get(session_id)
        
        if not project_name:
            emit('project_error', {"error": "No active project to leave"})
            return
        
        # Leave project room
        leave_room(project_name)
        
        if project_name in project_rooms:
            project_rooms[project_name].discard(session_id)
        
        if session_id in active_project_sessions:
            del active_project_sessions[session_id]
        
        emit('project_left', {
            'project_name': project_name,
            'session_id': session_id,
            'timestamp': datetime.now().isoformat()
        })
        
        # Broadcast to project room that a member left
        if project_name in project_rooms and project_rooms[project_name]:
            emit('project_member_left', {
                'session_id': session_id,
                'project_name': project_name,
                'timestamp': datetime.now().isoformat(),
                'room_members': len(project_rooms[project_name])
            }, room=project_name)
        
        logger.info(f"Session {session_id} left project {project_name}")
        
    except Exception as e:
        logger.error(f"Error leaving project: {e}")
        emit('project_error', {"error": f"Failed to leave project: {str(e)}"})


@socketio.on('request_project_list')
def handle_project_list_request():
    """Handle request for project list"""
    if not MULTI_PROJECT_AVAILABLE or not multi_project_manager:
        emit('project_list', {
            'enabled': False,
            'projects': [],
            'reason': 'Multi-project management not available'
        })
        return
    
    try:
        projects = []
        for project in multi_project_manager.list_projects():
            project_state = load_project_state(project.name, project.path)
            
            projects.append({
                'name': project.name,
                'path': project.path,
                'status': project.status.value,
                'priority': project.priority.value,
                'description': project.description,
                'owner': project.owner,
                'team': project.team,
                'tags': project.tags,
                'state': project_state,
                'room_members': len(project_rooms.get(project.name, set()))
            })
        
        emit('project_list', {
            'enabled': True,
            'projects': projects,
            'total_count': len(projects),
            'active_count': len([p for p in projects if p['status'] == 'active'])
        })
        
    except Exception as e:
        logger.error(f"Error getting project list: {e}")
        emit('project_error', {"error": f"Failed to get project list: {str(e)}"})


@socketio.on('switch_project')
def handle_switch_project(data):
    """Handle project switch via WebSocket"""
    if not MULTI_PROJECT_AVAILABLE or not multi_project_manager:
        emit('project_error', {"error": "Multi-project management not available"})
        return
    
    try:
        project_name = data.get('project_name')
        session_id = data.get('session_id', request.sid)
        
        if not project_name:
            emit('project_error', {"error": "project_name is required"})
            return
        
        # Validate project exists
        project = multi_project_manager.get_project(project_name)
        if not project:
            emit('project_error', {"error": f"Project '{project_name}' not found"})
            return
        
        # Leave current project and join new one
        current_project = active_project_sessions.get(session_id)
        
        # Leave current project room
        if current_project and current_project != project_name:
            if current_project in project_rooms:
                project_rooms[current_project].discard(session_id)
            leave_room(current_project)
        
        # Join new project room
        join_room(project_name)
        active_project_sessions[session_id] = project_name
        
        if project_name not in project_rooms:
            project_rooms[project_name] = set()
        project_rooms[project_name].add(session_id)
        
        # Load project state
        project_state = load_project_state(project_name, project.path)
        
        emit('project_switched', {
            'old_project': current_project,
            'new_project': project_name,
            'session_id': session_id,
            'timestamp': datetime.now().isoformat(),
            'project_state': project_state
        })
        
        logger.info(f"Session {session_id} switched from {current_project} to {project_name}")
        
    except Exception as e:
        logger.error(f"Error switching project: {e}")
        emit('project_error', {"error": f"Failed to switch project: {str(e)}"})


@socketio.on('broadcast_to_project')
def handle_project_broadcast(data):
    """Handle broadcasting a message to a specific project room"""
    try:
        project_name = data.get('project_name')
        message = data.get('message')
        message_type = data.get('type', 'general')
        session_id = data.get('session_id', request.sid)
        
        if not project_name or not message:
            emit('project_error', {"error": "project_name and message are required"})
            return
        
        # Verify session is in the project room
        if session_id not in project_rooms.get(project_name, set()):
            emit('project_error', {"error": "Not a member of the specified project room"})
            return
        
        # Broadcast to project room
        emit('project_broadcast', {
            'project_name': project_name,
            'message': message,
            'type': message_type,
            'sender_session': session_id,
            'timestamp': datetime.now().isoformat()
        }, room=project_name)
        
    except Exception as e:
        logger.error(f"Error broadcasting to project: {e}")
        emit('project_error', {"error": f"Failed to broadcast message: {str(e)}"})


@socketio.on('disconnect')
def handle_disconnect():
    """Handle SocketIO client disconnection"""
    logger.info(f"SocketIO client disconnected: {request.sid}")
    
    # Clean up project room memberships
    session_id = request.sid
    project_name = active_project_sessions.get(session_id)
    
    if project_name:
        if project_name in project_rooms:
            project_rooms[project_name].discard(session_id)
        
        if session_id in active_project_sessions:
            del active_project_sessions[session_id]
        
        # Notify project room of member leaving
        if project_name in project_rooms and project_rooms[project_name]:
            socketio.emit('project_member_left', {
                'session_id': session_id,
                'project_name': project_name,
                'timestamp': datetime.now().isoformat(),
                'room_members': len(project_rooms[project_name])
            }, room=project_name)


@socketio.on('request_state')
def handle_state_request():
    """Handle client request for current state"""
    current_state = broadcaster.get_current_state()
    emit('state_update', current_state)


@socketio.on('request_history')
def handle_history_request():
    """Handle client request for transition history"""
    emit('history_update', {
        "history": broadcaster.transition_history[-50:],
        "count": len(broadcaster.transition_history)
    })


@socketio.on('request_interface_status')
def handle_interface_status_request():
    """Handle client request for interface status"""
    try:
        status = interface_manager.get_interface_status()
        emit('interface_status', status)
    except Exception as e:
        logger.error(f"Error getting interface status: {e}")
        emit('interface_error', {"error": "Failed to get interface status"})


@socketio.on('switch_interface')
def handle_interface_switch(data):
    """Handle WebSocket interface switch request"""
    async def _switch():
        try:
            interface_type = data.get('interface_type')
            if not interface_type:
                return {"success": False, "error": "Interface type required"}
            
            result = await interface_manager.switch_interface(interface_type)
            return result
        except Exception as e:
            logger.error(f"Error switching interface via WebSocket: {e}")
            return {"success": False, "error": str(e)}
    
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(_switch())
        loop.close()
        
        # Emit result to the requesting client
        emit('interface_switch_result', result)
        
        # If successful, broadcast to all clients
        if result.get("success"):
            socketio.emit('interface_changed', {
                "type": "interface_switch",
                "old_interface": result.get("old_interface"),
                "new_interface": result.get("active_interface"),
                "timestamp": datetime.now().isoformat()
            })
            
    except Exception as e:
        logger.error(f"Error in WebSocket interface switch: {e}")
        emit('interface_error', {"error": str(e)})


@socketio.on('request_context_status')
def handle_context_status_request():
    """Handle client request for context status"""
    try:
        factory = get_context_manager_factory()
        current_mode = factory.get_current_mode()
        current_manager = factory.get_current_manager()
        
        status = {
            "current_mode": current_mode.value if current_mode else None,
            "factory_status": factory.get_detection_status(),
            "mode_info": factory.get_mode_info(),
            "manager_active": current_manager is not None
        }
        
        emit('context_status', status)
    except Exception as e:
        logger.error(f"Error getting context status: {e}")
        emit('context_error', {"error": "Failed to get context status"})


@socketio.on('switch_context_mode')
def handle_context_mode_switch(data):
    """Handle WebSocket context mode switch request"""
    async def _switch():
        try:
            mode_str = data.get('mode')
            if not mode_str:
                return {"success": False, "error": "Mode is required"}
            
            try:
                new_mode = ContextMode(mode_str)
            except ValueError:
                return {"success": False, "error": f"Invalid mode: {mode_str}"}
            
            factory = get_context_manager_factory()
            old_mode = factory.get_current_mode()
            
            # Switch mode
            manager = await factory.switch_mode(new_mode)
            
            return {
                "success": True,
                "message": f"Successfully switched to {new_mode.value} mode",
                "old_mode": old_mode.value if old_mode else None,
                "new_mode": new_mode.value,
                "manager_type": type(manager).__name__
            }
            
        except Exception as e:
            logger.error(f"Error switching context mode via WebSocket: {e}")
            return {"success": False, "error": str(e)}
    
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(_switch())
        loop.close()
        
        # Emit result to the requesting client
        emit('context_switch_result', result)
        
        # If successful, broadcast to all clients
        if result.get("success"):
            socketio.emit('context_mode_changed', {
                "type": "context_mode_switch",
                "old_mode": result.get("old_mode"),
                "new_mode": result.get("new_mode"),
                "timestamp": datetime.now().isoformat()
            })
            
    except Exception as e:
        logger.error(f"Error in WebSocket context mode switch: {e}")
        emit('context_error', {"error": str(e)})


@socketio.on('test_context_preparation')
def handle_context_test(data):
    """Handle WebSocket context preparation test"""
    async def _test():
        try:
            agent_type = data.get('agent_type', 'CodeAgent')
            task_description = data.get('task', 'Test task for context preparation')
            
            factory = get_context_manager_factory()
            manager = await factory.create_context_manager()
            
            if not manager:
                return {"success": False, "error": "No context manager available"}
            
            # Create test task
            test_task = {
                "description": task_description,
                "story_id": "test-story",
                "current_state": "WRITE_TEST"
            }
            
            # Measure preparation time
            start_time = time.time()
            context = await manager.prepare_context(agent_type, test_task)
            preparation_time = time.time() - start_time
            
            return {
                "success": True,
                "mode": factory.get_current_mode().value,
                "preparation_time": preparation_time,
                "token_usage": {
                    "total_used": context.token_usage.total_used,
                    "core_task_used": context.token_usage.core_task_used
                },
                "file_count": len(context.file_contents) if context.file_contents else 0,
                "compression_applied": getattr(context, 'compression_applied', False),
                "cache_hit": getattr(context, 'cache_hit', False)
            }
            
        except Exception as e:
            logger.error(f"Error testing context preparation: {e}")
            return {"success": False, "error": str(e)}
    
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(_test())
        loop.close()
        
        emit('context_test_result', result)
        
    except Exception as e:
        logger.error(f"Error in WebSocket context test: {e}")
        emit('context_error', {"error": str(e)})


# =====================================================
# Discord-Style Chat WebSocket Handlers
# =====================================================

@socketio.on('chat_command')
def handle_chat_command(data):
    """Handle incoming chat command from WebSocket - project-aware"""
    try:
        message = data.get('message', '').strip()
        user_id = data.get('user_id', 'anonymous')
        username = data.get('username', 'User')
        project_name = data.get('project_name', 'default')
        room = data.get('room')
        
        if not message:
            emit('command_error', {"error": "Message cannot be empty", "project_name": project_name})
            return
        
        # Create message object with project context
        chat_message = {
            "id": generate_uuid(),
            "user_id": user_id,
            "username": username,
            "message": message,
            "timestamp": datetime.now().isoformat(),
            "type": "user",
            "project_name": project_name
        }
        
        # Add to project-specific chat history
        if project_name not in project_chat_history:
            project_chat_history[project_name] = []
        
        project_chat_history[project_name].append(chat_message)
        
        # Keep only last 100 messages per project
        if len(project_chat_history[project_name]) > 100:
            project_chat_history[project_name].pop(0)
        
        # Also add to global history for backwards compatibility
        chat_history.append(chat_message)
        if len(chat_history) > 100:
            chat_history.pop(0)
        
        # Broadcast message to project room
        room_name = f"project_{project_name}"
        socketio.emit('new_chat_message', chat_message, room=room_name)
        
        # If it's a command, process it
        if message.startswith('/'):
            # Show typing indicator for project room
            socketio.emit('bot_typing', {
                "user_id": "bot",
                "username": "Agent Bot",
                "typing": True,
                "project_name": project_name
            }, room=room_name)
            
            # Process command asynchronously
            def process_command_async():
                try:
                    from command_processor import process_command
                    result = process_command(message, user_id, project_name=project_name)
                    
                    # Create bot response with project context
                    bot_response = {
                        "id": generate_uuid(),
                        "user_id": "bot",
                        "username": "Agent Bot",
                        "message": result.get('response', 'Command processed'),
                        "timestamp": datetime.now().isoformat(),
                        "type": "bot",
                        "command_result": result,
                        "project_name": project_name
                    }
                    
                    # Add to project-specific chat history
                    project_chat_history[project_name].append(bot_response)
                    
                    # Also add to global history
                    chat_history.append(bot_response)
                    
                    # Stop typing and send response to project room
                    socketio.emit('bot_typing', {
                        "user_id": "bot",
                        "username": "Agent Bot", 
                        "typing": False,
                        "project_name": project_name
                    }, room=room_name)
                    socketio.emit('command_response', bot_response, room=room_name)
                    
                except Exception as e:
                    logger.error(f"Error processing command via WebSocket: {e}")
                    error_response = {
                        "id": generate_uuid(),
                        "user_id": "bot",
                        "username": "Agent Bot",
                        "message": f"Error processing command: {str(e)}",
                        "timestamp": datetime.now().isoformat(),
                        "type": "bot",
                        "error": True,
                        "project_name": project_name
                    }
                    
                    # Add to project-specific history
                    project_chat_history[project_name].append(error_response)
                    chat_history.append(error_response)
                    
                    # Stop typing and send error to project room
                    socketio.emit('bot_typing', {
                        "user_id": "bot",
                        "username": "Agent Bot",
                        "typing": False,
                        "project_name": project_name
                    }, room=room_name)
                    socketio.emit('command_response', error_response, room=room_name)
            
            # Run in background thread
            import threading
            threading.Thread(target=process_command_async, daemon=True).start()
        
    except Exception as e:
        logger.error(f"Error handling chat command: {e}")
        emit('command_error', {"error": str(e)})


@socketio.on('request_chat_history')
def handle_chat_history_request(data):
    """Handle request for project-specific chat history"""
    try:
        limit = data.get('limit', 50) if data else 50
        limit = min(limit, 100)  # Max 100 messages
        project_name = data.get('project_name', 'default') if data else 'default'
        
        # Get project-specific messages
        project_messages = project_chat_history.get(project_name, [])
        recent_messages = project_messages[-limit:] if project_messages else []
        
        emit('chat_history', {
            "messages": recent_messages,
            "total_count": len(project_messages),
            "project_name": project_name
        })
        
    except Exception as e:
        logger.error(f"Error getting chat history via WebSocket: {e}")
        emit('chat_error', {"error": "Failed to get chat history", "project_name": data.get('project_name', 'default') if data else 'default'})


@socketio.on('start_typing')
def handle_start_typing(data):
    """Handle user start typing event - project-aware"""
    try:
        user_id = data.get('user_id', 'anonymous')
        username = data.get('username', 'User')
        project_name = data.get('project_name', 'default')
        
        # Add to global and project-specific typing users
        typing_users.add(user_id)
        if project_name not in project_typing_users:
            project_typing_users[project_name] = set()
        project_typing_users[project_name].add(user_id)
        
        # Broadcast typing indicator to project room only
        room_name = f"project_{project_name}"
        socketio.emit('typing_indicator', {
            "user_id": user_id,
            "username": username,
            "typing": True,
            "project_name": project_name
        }, room=room_name, include_self=False)
        
    except Exception as e:
        logger.error(f"Error handling start typing: {e}")


@socketio.on('stop_typing')
def handle_stop_typing(data):
    """Handle user stop typing event - project-aware"""
    try:
        user_id = data.get('user_id', 'anonymous')
        username = data.get('username', 'User')
        project_name = data.get('project_name', 'default')
        
        # Remove from global and project-specific typing users
        typing_users.discard(user_id)
        if project_name in project_typing_users:
            project_typing_users[project_name].discard(user_id)
        
        # Broadcast stop typing indicator to project room only
        room_name = f"project_{project_name}"
        socketio.emit('typing_indicator', {
            "user_id": user_id,
            "username": username,
            "typing": False,
            "project_name": project_name
        }, room=room_name, include_self=False)
        
    except Exception as e:
        logger.error(f"Error handling stop typing: {e}")


# =====================================================
# Project-Specific Room Management
# =====================================================

@socketio.on('join_project_room')
def handle_join_project_room(data):
    """Handle user joining a project-specific chat room"""
    try:
        user_id = data.get('user_id', 'anonymous')
        username = data.get('username', 'User')
        project_name = data.get('project_name', 'default')
        session_id = data.get('session_id')
        
        # Create room name
        room_name = f"project_{project_name}"
        
        # Join the room
        join_room(room_name)
        
        # Track user's current project room
        user_project_rooms[user_id] = project_name
        
        # Track project session
        project_user_sessions[user_id] = {
            'project': project_name,
            'session_id': session_id,
            'joined_at': datetime.now().isoformat()
        }
        
        # Emit confirmation
        emit('room_joined', {
            "room": room_name,
            "project_name": project_name,
            "user_id": user_id
        })
        
        # Notify other users in the project room
        socketio.emit('user_joined', {
            "user_id": user_id,
            "username": username,
            "project_name": project_name,
            "timestamp": datetime.now().isoformat()
        }, room=room_name, include_self=False)
        
        logger.info(f"User {username} ({user_id}) joined project room: {project_name}")
        
    except Exception as e:
        logger.error(f"Error joining project room: {e}")
        emit('chat_error', {"error": "Failed to join project room", "project_name": data.get('project_name', 'default')})


@socketio.on('leave_project_room')
def handle_leave_project_room(data):
    """Handle user leaving a project-specific chat room"""
    try:
        user_id = data.get('user_id', 'anonymous')
        project_name = data.get('project_name', 'default')
        
        # Create room name
        room_name = f"project_{project_name}"
        
        # Leave the room
        leave_room(room_name)
        
        # Clean up tracking
        if user_id in user_project_rooms:
            del user_project_rooms[user_id]
        
        if user_id in project_user_sessions:
            del project_user_sessions[user_id]
        
        # Clean up typing indicators
        if project_name in project_typing_users:
            project_typing_users[project_name].discard(user_id)
        
        # Emit confirmation
        emit('room_left', {
            "room": room_name,
            "project_name": project_name,
            "user_id": user_id
        })
        
        # Notify other users in the project room
        socketio.emit('user_left', {
            "user_id": user_id,
            "project_name": project_name,
            "timestamp": datetime.now().isoformat()
        }, room=room_name)
        
        logger.info(f"User {user_id} left project room: {project_name}")
        
    except Exception as e:
        logger.error(f"Error leaving project room: {e}")
        emit('chat_error', {"error": "Failed to leave project room", "project_name": project_name})


@socketio.on('switch_project')
def handle_switch_project(data):
    """Handle user switching between projects"""
    try:
        user_id = data.get('user_id', 'anonymous')
        new_project = data.get('new_project', 'default')
        old_project = data.get('old_project')
        
        # Leave old project room if specified
        if old_project and old_project != new_project:
            old_room_name = f"project_{old_project}"
            leave_room(old_room_name)
            
            # Clean up old project typing indicators
            if old_project in project_typing_users:
                project_typing_users[old_project].discard(user_id)
            
            # Notify users in old room
            socketio.emit('user_left', {
                "user_id": user_id,
                "project_name": old_project,
                "timestamp": datetime.now().isoformat()
            }, room=old_room_name)
        
        # Join new project room
        new_room_name = f"project_{new_project}"
        join_room(new_room_name)
        
        # Update tracking
        user_project_rooms[user_id] = new_project
        project_user_sessions[user_id] = project_user_sessions.get(user_id, {})
        project_user_sessions[user_id].update({
            'project': new_project,
            'switched_at': datetime.now().isoformat()
        })
        
        # Emit confirmations
        emit('room_left', {"room": f"project_{old_project}", "project_name": old_project})
        emit('room_joined', {"room": new_room_name, "project_name": new_project})
        emit('project_switched', {
            "project_name": new_project,
            "previous_project": old_project
        })
        
        # Notify users in new room
        socketio.emit('user_joined', {
            "user_id": user_id,
            "project_name": new_project,
            "timestamp": datetime.now().isoformat()
        }, room=new_room_name, include_self=False)
        
        logger.info(f"User {user_id} switched from {old_project} to {new_project}")
        
    except Exception as e:
        logger.error(f"Error switching project: {e}")
        emit('chat_error', {"error": "Failed to switch project"})


@socketio.on('join_chat')
def handle_join_chat(data):
    """Handle user joining chat"""
    try:
        user_id = data.get('user_id', 'anonymous')
        username = data.get('username', 'User')
        
        active_users.add(user_id)
        
        # Send welcome message
        welcome_message = {
            "id": generate_uuid(),
            "user_id": "system",
            "username": "System",
            "message": f"{username} joined the chat",
            "timestamp": datetime.now().isoformat(),
            "type": "system"
        }
        
        socketio.emit('user_joined', {
            "user_id": user_id,
            "username": username,
            "message": welcome_message
        }, broadcast=True)
        
        # Send current active users to the new user
        emit('active_users', {
            "users": list(active_users),
            "count": len(active_users)
        })
        
    except Exception as e:
        logger.error(f"Error handling join chat: {e}")


@socketio.on('leave_chat')
def handle_leave_chat(data):
    """Handle user leaving chat"""
    try:
        user_id = data.get('user_id', 'anonymous')
        username = data.get('username', 'User')
        
        active_users.discard(user_id)
        typing_users.discard(user_id)
        
        # Send goodbye message
        goodbye_message = {
            "id": generate_uuid(),
            "user_id": "system",
            "username": "System",
            "message": f"{username} left the chat",
            "timestamp": datetime.now().isoformat(),
            "type": "system"
        }
        
        socketio.emit('user_left', {
            "user_id": user_id,
            "username": username,
            "message": goodbye_message
        }, broadcast=True)
        
    except Exception as e:
        logger.error(f"Error handling leave chat: {e}")


# =====================================================
# TDD Cycle WebSocket Handlers
# =====================================================

@socketio.on('start_tdd_cycle')
def handle_start_tdd_cycle(data):
    """Handle TDD cycle start request"""
    try:
        story_id = data.get('story_id')
        project = data.get('project', 'default')
        
        if not story_id:
            emit('error', {'message': 'Story ID is required'})
            return
        
        # Import here to avoid circular imports
        from state_machine import StateMachine
        
        # Get or create state machine instance
        if not hasattr(handle_start_tdd_cycle, '_state_machine'):
            handle_start_tdd_cycle._state_machine = StateMachine()
        
        state_machine = handle_start_tdd_cycle._state_machine
        
        # Start TDD cycle
        cycle_id = state_machine.start_tdd_cycle(story_id, project_name=project)
        
        # Emit success event
        emit('tdd_cycle_started', {
            'story_id': story_id,
            'cycle_id': cycle_id,
            'project': project,
            'timestamp': datetime.now().isoformat()
        })
        
        logger.info(f"Started TDD cycle {cycle_id} for story {story_id}")
        
    except Exception as e:
        logger.error(f"Error starting TDD cycle: {e}")
        emit('error', {'message': f'Failed to start TDD cycle: {str(e)}'})


@socketio.on('tdd_transition')
def handle_tdd_transition(data):
    """Handle TDD state transition request"""
    try:
        cycle_id = data.get('cycle_id')
        new_state = data.get('new_state')
        project = data.get('project', 'default')
        
        if not cycle_id or not new_state:
            emit('error', {'message': 'Cycle ID and new state are required'})
            return
        
        # Import here to avoid circular imports
        from state_machine import StateMachine
        
        # Get or create state machine instance
        if not hasattr(handle_tdd_transition, '_state_machine'):
            handle_tdd_transition._state_machine = StateMachine()
        
        state_machine = handle_tdd_transition._state_machine
        
        # Transition TDD cycle
        success = state_machine.transition_tdd_cycle(cycle_id, new_state, project)
        
        if success:
            # The state machine will emit the transition event
            logger.info(f"TDD cycle {cycle_id} transitioned to {new_state}")
        else:
            emit('error', {'message': f'Failed to transition TDD cycle {cycle_id} to {new_state}'})
        
    except Exception as e:
        logger.error(f"Error transitioning TDD cycle: {e}")
        emit('error', {'message': f'Failed to transition TDD cycle: {str(e)}'})


@socketio.on('complete_tdd_cycle')
def handle_complete_tdd_cycle(data):
    """Handle TDD cycle completion request"""
    try:
        cycle_id = data.get('cycle_id')
        project = data.get('project', 'default')
        
        if not cycle_id:
            emit('error', {'message': 'Cycle ID is required'})
            return
        
        # Import here to avoid circular imports
        from state_machine import StateMachine
        
        # Get or create state machine instance
        if not hasattr(handle_complete_tdd_cycle, '_state_machine'):
            handle_complete_tdd_cycle._state_machine = StateMachine()
        
        state_machine = handle_complete_tdd_cycle._state_machine
        
        # Complete TDD cycle
        success = state_machine.complete_tdd_cycle(cycle_id, project)
        
        if success:
            # The state machine will emit the completion event
            logger.info(f"Completed TDD cycle {cycle_id}")
        else:
            emit('error', {'message': f'Failed to complete TDD cycle {cycle_id}'})
        
    except Exception as e:
        logger.error(f"Error completing TDD cycle: {e}")
        emit('error', {'message': f'Failed to complete TDD cycle: {str(e)}'})


@socketio.on('request_tdd_status')
def handle_request_tdd_status():
    """Handle request for TDD cycle status"""
    try:
        from state_broadcaster import get_all_tdd_cycles, get_tdd_metrics
        
        # Get TDD cycle data
        all_cycles = get_all_tdd_cycles()
        metrics = get_tdd_metrics()
        
        emit('tdd_status_update', {
            'cycles': all_cycles,
            'metrics': metrics,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error getting TDD status: {e}")
        emit('error', {'message': f'Failed to get TDD status: {str(e)}'})


@socketio.on('update_tdd_progress')
def handle_update_tdd_progress(data):
    """Handle TDD cycle progress update"""
    try:
        story_id = data.get('story_id')
        cycle_id = data.get('cycle_id')
        progress_data = data.get('progress', {})
        project = data.get('project', 'default')
        
        if not story_id or not cycle_id:
            emit('error', {'message': 'Story ID and cycle ID are required'})
            return
        
        # Import here to avoid circular imports
        from state_broadcaster import emit_tdd_progress_update
        
        # Emit progress update
        emit_tdd_progress_update(story_id, cycle_id, progress_data, project)
        
        logger.info(f"Updated TDD progress for cycle {cycle_id}: {progress_data}")
        
    except Exception as e:
        logger.error(f"Error updating TDD progress: {e}")
        emit('error', {'message': f'Failed to update TDD progress: {str(e)}'})


@socketio.on('disconnect')
def handle_disconnect():
    """Handle client disconnection - updated to include chat cleanup"""
    logger.info(f"SocketIO client disconnected: {request.sid}")
    
    # Clean up any typing indicators for this session
    # Note: In a real implementation, you'd want to track user_id by session_id
    # For now, we'll just clear typing indicators periodically


class StateMonitor:
    """Monitor state broadcaster and relay to SocketIO clients"""
    
    def __init__(self, socketio_app):
        self.socketio = socketio_app
        self.running = False
        self.websocket_client = None
        
    async def start_monitoring(self):
        """Start monitoring the state broadcaster WebSocket"""
        self.running = True
        broadcaster_uri = "ws://localhost:8080"
        
        logger.info("Starting state monitor...")
        
        while self.running:
            try:
                # Connect to state broadcaster
                async with websockets.connect(broadcaster_uri) as websocket:
                    self.websocket_client = websocket
                    logger.info("Connected to state broadcaster")
                    
                    # Listen for state updates
                    async for message in websocket:
                        try:
                            import json
                            data = json.loads(message)
                            self.handle_state_update(data)
                        except json.JSONDecodeError as e:
                            logger.error(f"Invalid JSON from broadcaster: {e}")
                        except Exception as e:
                            logger.error(f"Error processing state update: {e}")
                            
            except ConnectionRefusedError:
                logger.warning("State broadcaster not available, retrying in 5 seconds...")
                await asyncio.sleep(5)
            except Exception as e:
                logger.error(f"State monitor error: {e}")
                await asyncio.sleep(5)
                
    def handle_state_update(self, data: Dict[str, Any]):
        """Handle state update from broadcaster and relay to SocketIO clients"""
        update_type = data.get("type")
        
        if update_type == "workflow_transition":
            logger.info(f"Workflow transition: {data.get('old_state')} → {data.get('new_state')}")
            self.socketio.emit('workflow_transition', data)
            
        elif update_type == "tdd_transition":
            logger.info(f"TDD transition [{data.get('story_id')}]: {data.get('old_state')} → {data.get('new_state')}")
            self.socketio.emit('tdd_transition', data)
            
        elif update_type == "agent_activity":
            logger.info(f"Agent activity [{data.get('story_id')}]: {data.get('agent_type')} {data.get('action')} - {data.get('status')}")
            self.socketio.emit('agent_activity', data)
            
        elif update_type == "current_state":
            self.socketio.emit('state_update', data)
            
        # Always emit generic update for debugging
        self.socketio.emit('raw_update', data)
        
    def stop_monitoring(self):
        """Stop the state monitoring"""
        self.running = False
        if self.websocket_client:
            asyncio.create_task(self.websocket_client.close())


# Global state monitor
state_monitor = StateMonitor(socketio)


def run_visualizer(host='localhost', port=5000, debug=False):
    """Run the visualizer web application"""
    logger.info(f"Starting State Visualizer on http://{host}:{port}")
    
    # Start state monitoring in background
    import threading
    
    def monitor_thread():
        """Thread function for state monitoring"""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(state_monitor.start_monitoring())
        except Exception as e:
            logger.error(f"State monitoring error: {e}")
        finally:
            loop.close()
    
    monitor_thread = threading.Thread(target=monitor_thread, daemon=True)
    monitor_thread.start()
    
    # Run Flask-SocketIO app
    try:
        socketio.run(
            app,
            host=host,
            port=port,
            debug=debug,
            allow_unsafe_werkzeug=True
        )
    finally:
        state_monitor.stop_monitoring()


# =====================================================
# Enhanced Project Management API Endpoints
# =====================================================

@app.route('/api/project-templates')
def get_project_templates():
    """Get available project templates"""
    try:
        # Return default templates for now
        templates = [
            {
                "id": "web-app",
                "name": "Web Application",
                "icon": "🌐",
                "description": "Modern web application with frontend and backend",
                "category": "web",
                "files": ["package.json", "src/", "public/", "tests/"],
                "settings": {
                    "workflowMode": "partial",
                    "tddEnabled": True,
                    "agents": {
                        "design": {"enabled": True, "creativity": 7},
                        "code": {"enabled": True, "style": "standard"},
                        "qa": {"enabled": True, "rigor": "thorough"}
                    }
                }
            },
            {
                "id": "api-service",
                "name": "API Service",
                "icon": "🔌",
                "description": "RESTful API service with database integration",
                "category": "api",
                "files": ["requirements.txt", "src/", "tests/", "docs/"],
                "settings": {
                    "workflowMode": "autonomous",
                    "tddEnabled": True,
                    "agents": {
                        "code": {"enabled": True, "style": "minimal"},
                        "qa": {"enabled": True, "rigor": "exhaustive"},
                        "data": {"enabled": True, "depth": "detailed"}
                    }
                }
            }
        ]
        
        return jsonify(templates)
        
    except Exception as e:
        logger.error(f"Error getting project templates: {e}")
        return jsonify({"error": "Failed to get project templates"}), 500




@app.route('/api/projects/<project_id>/health')
def get_project_health(project_id):
    """Get health status for a specific project"""
    try:
        # Mock health data
        health_data = {
            "status": "healthy" if project_id != "error-project" else "error",
            "score": 85,
            "lastCheck": datetime.now().isoformat(),
            "metrics": {
                "gitStatus": "clean",
                "testCoverage": 78,
                "buildStatus": "passing",
                "dependencies": "up-to-date",
                "lastActivity": "2 hours ago"
            },
            "issues": [],
            "suggestions": [
                "Consider increasing test coverage to 80%+",
                "Update outdated dependencies"
            ]
        }
        
        if project_id == "error-project":
            health_data["issues"] = ["Build failing", "Security vulnerabilities found"]
            health_data["score"] = 45
        
        return jsonify(health_data)
        
    except Exception as e:
        logger.error(f"Error getting project health for {project_id}: {e}")
        return jsonify({"error": "Failed to get project health"}), 500


@app.route('/api/projects/<project_id>/analytics')
def get_project_analytics(project_id):
    """Get analytics data for a specific project"""
    try:
        timeframe = request.args.get('timeframe', '30d')
        
        # Mock analytics data
        analytics_data = {
            "timeframe": timeframe,
            "summary": {
                "totalCommits": 127,
                "testCoverage": 78.5,
                "buildSuccess": 94.2,
                "deploymentCount": 15
            },
            "activity": {
                "commits": [
                    {"date": "2024-01-15", "count": 5},
                    {"date": "2024-01-14", "count": 3},
                    {"date": "2024-01-13", "count": 8},
                    {"date": "2024-01-12", "count": 2},
                    {"date": "2024-01-11", "count": 4}
                ],
                "issues": [
                    {"date": "2024-01-15", "opened": 2, "closed": 3},
                    {"date": "2024-01-14", "opened": 1, "closed": 1},
                    {"date": "2024-01-13", "opened": 0, "closed": 2}
                ]
            },
            "performance": {
                "buildTime": "2m 34s",
                "testTime": "1m 12s",
                "deploymentTime": "4m 56s"
            },
            "dependencies": {
                "total": 45,
                "outdated": 3,
                "vulnerable": 1
            }
        }
        
        return jsonify(analytics_data)
        
    except Exception as e:
        logger.error(f"Error getting analytics for {project_id}: {e}")
        return jsonify({"error": "Failed to get project analytics"}), 500


@app.route('/api/projects/<project_id>/collaboration')
def get_project_collaboration(project_id):
    """Get collaboration data for a specific project"""
    try:
        collaboration_data = {
            "teamMembers": [
                {
                    "id": "user1",
                    "name": "John Doe",
                    "email": "john@example.com",
                    "role": "maintainer",
                    "status": "online",
                    "avatar": "JD",
                    "lastActive": "5 minutes ago"
                },
                {
                    "id": "user2",
                    "name": "Jane Smith",
                    "email": "jane@example.com",
                    "role": "contributor",
                    "status": "away",
                    "avatar": "JS",
                    "lastActive": "2 hours ago"
                }
            ],
            "recentActivity": [
                {
                    "type": "commit",
                    "user": "John Doe",
                    "action": "committed changes to feature branch",
                    "timestamp": "2024-01-15T10:30:00Z",
                    "icon": "💾"
                },
                {
                    "type": "review",
                    "user": "Jane Smith",
                    "action": "reviewed pull request #123",
                    "timestamp": "2024-01-15T09:15:00Z",
                    "icon": "👀"
                },
                {
                    "type": "issue",
                    "user": "John Doe",
                    "action": "closed issue #456",
                    "timestamp": "2024-01-15T08:45:00Z",
                    "icon": "✅"
                }
            ],
            "permissions": {
                "viewProject": True,
                "editFiles": True,
                "createBranches": True,
                "mergePRs": False,
                "startWorkflows": True,
                "approveTasks": False,
                "configureAgents": False,
                "manageSettings": False
            }
        }
        
        return jsonify(collaboration_data)
        
    except Exception as e:
        logger.error(f"Error getting collaboration data for {project_id}: {e}")
        return jsonify({"error": "Failed to get collaboration data"}), 500


@app.route('/api/projects/<project_id>/invite', methods=['POST'])
def invite_team_member(project_id):
    """Invite a new team member to the project"""
    try:
        data = request.get_json()
        email = data.get('email')
        role = data.get('role', 'viewer')
        
        if not email:
            return jsonify({"success": False, "error": "Email is required"}), 400
        
        # Mock invitation logic
        invitation_data = {
            "success": True,
            "invitationId": f"inv_{project_id}_{int(time.time())}",
            "email": email,
            "role": role,
            "status": "sent",
            "expiresAt": (datetime.now() + timedelta(days=7)).isoformat()
        }
        
        return jsonify(invitation_data)
        
    except Exception as e:
        logger.error(f"Error inviting team member to {project_id}: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='TDD State Visualizer')
    parser.add_argument('--host', default='localhost', help='Host to bind to')
    parser.add_argument('--port', type=int, default=5000, help='Port to bind to')
    parser.add_argument('--debug', action='store_true', help='Enable debug mode')
    
    args = parser.parse_args()
    
    run_visualizer(args.host, args.port, args.debug)