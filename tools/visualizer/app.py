#!/usr/bin/env python3
"""
Real-Time State Visualizer Web Application

Flask application with WebSocket support for real-time visualization
of workflow and TDD state machine transitions.
"""

import asyncio
import json
import logging
import os
import sys
import time
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List

from flask import Flask, render_template, jsonify, request, session, make_response
from flask_socketio import SocketIO, emit, join_room, leave_room
import websockets
import re
import uuid

# Add lib directory to path  
lib_path = Path(__file__).parent.parent.parent / "lib"
sys.path.insert(0, str(lib_path))

from state_broadcaster import broadcaster
from agent_interfaces import interface_manager, InterfaceType, AgentType
from security import (
    validate_configuration, sanitize_prompt, sanitize_code,
    audit_operation, SecurityLevel, mask_api_key
)

# Configure logging first
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Try to import additional components with graceful fallback
try:
    from context_manager_factory import get_context_manager_factory, ContextMode
    from context_config import ContextConfig
    CONTEXT_MANAGEMENT_AVAILABLE = True
except ImportError:
    logger.warning("Context management not available - some features disabled")
    CONTEXT_MANAGEMENT_AVAILABLE = False

# Import chat and collaboration components
try:
    from command_processor import CommandProcessor
    COMMAND_PROCESSOR_AVAILABLE = True
except ImportError:
    logger.warning("Command processor not available - basic chat only")
    COMMAND_PROCESSOR_AVAILABLE = False

try:
    from lib.chat_state_sync import get_synchronizer, process_chat_command
    CHAT_SYNC_AVAILABLE = True
except ImportError:
    logger.warning("Chat synchronization not available - using basic chat")
    CHAT_SYNC_AVAILABLE = False

try:
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
active_users = set()


@app.after_request
def add_header(response):
    """Add headers to prevent caching and ensure correct MIME types"""
    if 'static' in request.path:
        # Set appropriate MIME types for JavaScript files
        if request.path.endswith('.js'):
            response.headers['Content-Type'] = 'application/javascript; charset=utf-8'
        elif request.path.endswith('.css'):
            response.headers['Content-Type'] = 'text/css; charset=utf-8'
        
        # Prevent caching for development
        response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, post-check=0, pre-check=0, max-age=0'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '-1'
    
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


@app.route('/debug')
def debug_info():
    """Debug information endpoint"""
    return jsonify({
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
    })


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
    
    import asyncio
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
    
    import asyncio
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
    
    import asyncio
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
    import asyncio
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
    
    import asyncio
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
    
    import asyncio
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
    
    import asyncio
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
    
    import asyncio
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
            "id": str(uuid.uuid4()),
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
                            import asyncio
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
                        "id": str(uuid.uuid4()),
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
                        "id": str(uuid.uuid4()),
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
        
        import asyncio
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
        
        import asyncio
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
        
        import asyncio
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


@socketio.on('disconnect')
def handle_disconnect():
    """Handle SocketIO client disconnection"""
    logger.info(f"SocketIO client disconnected: {request.sid}")


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
    
    import asyncio
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
    
    import asyncio
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
    
    import asyncio
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
    """Handle incoming chat command from WebSocket"""
    try:
        message = data.get('message', '').strip()
        user_id = data.get('user_id', 'anonymous')
        username = data.get('username', 'User')
        
        if not message:
            emit('command_error', {"error": "Message cannot be empty"})
            return
        
        # Create message object
        chat_message = {
            "id": str(uuid.uuid4()),
            "user_id": user_id,
            "username": username,
            "message": message,
            "timestamp": datetime.now().isoformat(),
            "type": "user"
        }
        
        # Add to chat history
        chat_history.append(chat_message)
        
        # Keep only last 100 messages
        if len(chat_history) > 100:
            chat_history.pop(0)
        
        # Broadcast message to all clients
        socketio.emit('new_chat_message', chat_message)
        
        # If it's a command, process it
        if message.startswith('/'):
            # Show typing indicator
            socketio.emit('typing_indicator', {
                "user_id": "bot",
                "username": "Agent Bot",
                "typing": True
            })
            
            # Process command asynchronously
            def process_command_async():
                try:
                    from command_processor import process_command
                    result = process_command(message, user_id)
                    
                    # Create bot response
                    bot_response = {
                        "id": str(uuid.uuid4()),
                        "user_id": "bot",
                        "username": "Agent Bot",
                        "message": result.get('response', 'Command processed'),
                        "timestamp": datetime.now().isoformat(),
                        "type": "bot",
                        "command_result": result
                    }
                    
                    # Add to chat history
                    chat_history.append(bot_response)
                    
                    # Stop typing and send response
                    socketio.emit('typing_indicator', {
                        "user_id": "bot",
                        "username": "Agent Bot", 
                        "typing": False
                    })
                    socketio.emit('command_response', bot_response)
                    
                except Exception as e:
                    logger.error(f"Error processing command via WebSocket: {e}")
                    error_response = {
                        "id": str(uuid.uuid4()),
                        "user_id": "bot",
                        "username": "Agent Bot",
                        "message": f"Error processing command: {str(e)}",
                        "timestamp": datetime.now().isoformat(),
                        "type": "bot",
                        "error": True
                    }
                    chat_history.append(error_response)
                    socketio.emit('typing_indicator', {
                        "user_id": "bot",
                        "username": "Agent Bot",
                        "typing": False
                    })
                    socketio.emit('command_response', error_response)
            
            # Run in background thread
            import threading
            threading.Thread(target=process_command_async, daemon=True).start()
        
    except Exception as e:
        logger.error(f"Error handling chat command: {e}")
        emit('command_error', {"error": str(e)})


@socketio.on('request_chat_history')
def handle_chat_history_request(data):
    """Handle request for chat history"""
    try:
        limit = data.get('limit', 50) if data else 50
        limit = min(limit, 100)  # Max 100 messages
        
        # Return most recent messages
        recent_messages = chat_history[-limit:] if chat_history else []
        
        emit('chat_history', {
            "messages": recent_messages,
            "total_count": len(chat_history)
        })
        
    except Exception as e:
        logger.error(f"Error getting chat history via WebSocket: {e}")
        emit('chat_error', {"error": "Failed to get chat history"})


@socketio.on('start_typing')
def handle_start_typing(data):
    """Handle user start typing event"""
    try:
        user_id = data.get('user_id', 'anonymous')
        username = data.get('username', 'User')
        
        typing_users.add(user_id)
        
        # Broadcast typing indicator to other clients
        socketio.emit('typing_indicator', {
            "user_id": user_id,
            "username": username,
            "typing": True
        }, broadcast=True, include_self=False)
        
    except Exception as e:
        logger.error(f"Error handling start typing: {e}")


@socketio.on('stop_typing')
def handle_stop_typing(data):
    """Handle user stop typing event"""
    try:
        user_id = data.get('user_id', 'anonymous')
        username = data.get('username', 'User')
        
        typing_users.discard(user_id)
        
        # Broadcast stop typing indicator to other clients
        socketio.emit('typing_indicator', {
            "user_id": user_id,
            "username": username,
            "typing": False
        }, broadcast=True, include_self=False)
        
    except Exception as e:
        logger.error(f"Error handling stop typing: {e}")


@socketio.on('join_chat')
def handle_join_chat(data):
    """Handle user joining chat"""
    try:
        user_id = data.get('user_id', 'anonymous')
        username = data.get('username', 'User')
        
        active_users.add(user_id)
        
        # Send welcome message
        welcome_message = {
            "id": str(uuid.uuid4()),
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
            "id": str(uuid.uuid4()),
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
    import asyncio
    
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


@app.after_request
def add_header(response):
    """Add headers to disable caching and ensure correct content types"""
    if response.mimetype == 'application/javascript' or response.mimetype == 'text/javascript':
        response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '0'
    return response


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='TDD State Visualizer')
    parser.add_argument('--host', default='localhost', help='Host to bind to')
    parser.add_argument('--port', type=int, default=5000, help='Port to bind to')
    parser.add_argument('--debug', action='store_true', help='Enable debug mode')
    
    args = parser.parse_args()
    
    run_visualizer(args.host, args.port, args.debug)