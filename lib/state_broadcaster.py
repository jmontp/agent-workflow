"""
State Broadcasting System for Real-Time Visualization

Provides WebSocket broadcasting of state machine changes for real-time
visualization and monitoring of workflow and TDD state transitions.
"""

import asyncio
import json
import logging
import weakref
from typing import Dict, List, Optional, Any, Set, Union
from datetime import datetime
from dataclasses import asdict
import websockets
from websockets.server import WebSocketServerProtocol
from uuid import uuid4

# Import state types
try:
    from .state_machine import State
    from .tdd_models import TDDState
except ImportError:
    from state_machine import State
    from tdd_models import TDDState

logger = logging.getLogger(__name__)


class StatebroadCaster:
    """
    Singleton class for broadcasting state changes to connected clients.
    
    Provides WebSocket server for real-time state updates and JSON API
    for current state queries.
    """
    
    _instance = None
    _initialized = False
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
            
        self.clients: Set[WebSocketServerProtocol] = set()
        self.current_workflow_state = State.IDLE
        self.tdd_cycles: Dict[str, Dict[str, Any]] = {}
        self.transition_history: List[Dict[str, Any]] = []
        self.server = None
        self.port = 8080
        
        # Chat integration features
        self.active_commands: Dict[str, Dict[str, Any]] = {}  # command_id -> command_data
        self.user_sessions: Dict[str, Dict[str, Any]] = {}  # user_id -> session_data
        self.chat_history: List[Dict[str, Any]] = []
        self.state_highlights: Dict[str, Dict[str, Any]] = {}  # state_name -> highlight_data
        
        self._initialized = True
        
    async def start_server(self, port: int = 8080):
        """Start the WebSocket server for state broadcasting"""
        self.port = port
        try:
            self.server = await websockets.serve(
                self.handle_client,
                "localhost", 
                port,
                ping_interval=20,
                ping_timeout=10
            )
            logger.info(f"State broadcaster started on ws://localhost:{port}")
        except Exception as e:
            logger.error(f"Failed to start state broadcaster: {e}")
            
    async def stop_server(self):
        """Stop the WebSocket server"""
        if self.server:
            self.server.close()
            await self.server.wait_closed()
            logger.info("State broadcaster stopped")
            
    async def handle_client(self, websocket: WebSocketServerProtocol, path: str):
        """Handle new WebSocket client connections"""
        self.clients.add(websocket)
        logger.info(f"Client connected: {websocket.remote_address}")
        
        try:
            # Send current state to new client
            await self.send_current_state(websocket)
            
            # Keep connection alive and handle messages
            async for message in websocket:
                try:
                    data = json.loads(message)
                    await self.handle_client_message(websocket, data)
                except json.JSONDecodeError:
                    await websocket.send(json.dumps({
                        "type": "error",
                        "message": "Invalid JSON message"
                    }))
                    
        except websockets.exceptions.ConnectionClosed:
            logger.info(f"Client disconnected: {websocket.remote_address}")
        except Exception as e:
            logger.error(f"Error handling client {websocket.remote_address}: {e}")
        finally:
            self.clients.discard(websocket)
            
    async def handle_client_message(self, websocket: WebSocketServerProtocol, data: Dict[str, Any]):
        """Handle messages from WebSocket clients"""
        message_type = data.get("type")
        
        if message_type == "get_current_state":
            await self.send_current_state(websocket)
        elif message_type == "get_history":
            await websocket.send(json.dumps({
                "type": "transition_history",
                "history": self.transition_history[-50:]  # Last 50 transitions
            }))
        else:
            await websocket.send(json.dumps({
                "type": "error", 
                "message": f"Unknown message type: {message_type}"
            }))
            
    async def send_current_state(self, websocket: WebSocketServerProtocol):
        """Send current state to a specific client"""
        state_data = {
            "type": "current_state",
            "timestamp": datetime.now().isoformat(),
            "workflow_state": self.current_workflow_state.value if hasattr(self.current_workflow_state, 'value') else str(self.current_workflow_state),
            "tdd_cycles": self.tdd_cycles,
            "active_cycles": len(self.tdd_cycles)
        }
        
        try:
            await websocket.send(json.dumps(state_data))
        except Exception as e:
            logger.error(f"Failed to send current state: {e}")
            
    async def broadcast_to_all(self, message: Dict[str, Any]):
        """Broadcast message to all connected clients"""
        if not self.clients:
            return
            
        message_json = json.dumps(message)
        disconnected_clients = set()
        
        for client in self.clients:
            try:
                await client.send(message_json)
            except websockets.exceptions.ConnectionClosed:
                disconnected_clients.add(client)
            except Exception as e:
                logger.error(f"Failed to send to client: {e}")
                disconnected_clients.add(client)
                
        # Remove disconnected clients
        self.clients -= disconnected_clients
        
    def emit_workflow_transition(self, old_state: State, new_state: State, project_name: str = "default"):
        """Emit workflow state transition"""
        self.current_workflow_state = new_state
        
        transition = {
            "type": "workflow_transition",
            "timestamp": datetime.now().isoformat(),
            "project": project_name,
            "old_state": old_state.value if hasattr(old_state, 'value') else str(old_state),
            "new_state": new_state.value if hasattr(new_state, 'value') else str(new_state)
        }
        
        self.transition_history.append(transition)
        
        # Broadcast asynchronously
        try:
            loop = asyncio.get_running_loop()
            asyncio.create_task(self.broadcast_to_all(transition))
        except RuntimeError:
            # No event loop running, skip broadcasting
            pass
        logger.info(f"Workflow transition: {old_state} → {new_state}")
        
    def emit_tdd_transition(self, story_id: str, old_state: Optional[TDDState], new_state: TDDState, project_name: str = "default"):
        """Emit TDD state transition"""
        # Update TDD cycle tracking
        if story_id not in self.tdd_cycles:
            self.tdd_cycles[story_id] = {}
            
        self.tdd_cycles[story_id].update({
            "current_state": new_state.value if hasattr(new_state, 'value') else str(new_state),
            "last_updated": datetime.now().isoformat(),
            "project": project_name
        })
        
        transition = {
            "type": "tdd_transition", 
            "timestamp": datetime.now().isoformat(),
            "project": project_name,
            "story_id": story_id,
            "old_state": old_state.value if old_state and hasattr(old_state, 'value') else str(old_state) if old_state else None,
            "new_state": new_state.value if hasattr(new_state, 'value') else str(new_state)
        }
        
        self.transition_history.append(transition)
        
        # Broadcast asynchronously
        try:
            loop = asyncio.get_running_loop()
            asyncio.create_task(self.broadcast_to_all(transition))
        except RuntimeError:
            # No event loop running, skip broadcasting
            pass
        logger.info(f"TDD transition [{story_id}]: {old_state} → {new_state}")
        
    def emit_agent_activity(self, agent_type: str, story_id: str, action: str, status: str, project_name: str = "default"):
        """Emit agent activity for visualization"""
        activity = {
            "type": "agent_activity",
            "timestamp": datetime.now().isoformat(),
            "project": project_name,
            "story_id": story_id,
            "agent_type": agent_type,
            "action": action,
            "status": status  # "started", "completed", "failed"
        }
        
        # Broadcast asynchronously
        try:
            loop = asyncio.get_running_loop()
            asyncio.create_task(self.broadcast_to_all(activity))
        except RuntimeError:
            # No event loop running, skip broadcasting
            pass
        logger.info(f"Agent activity [{story_id}]: {agent_type} {action} - {status}")
        
    def emit_parallel_status(self, status_data: Dict[str, Any], project_name: str = "default"):
        """Emit parallel execution status for visualization"""
        parallel_status = {
            "type": "parallel_status",
            "timestamp": datetime.now().isoformat(),
            "project": project_name,
            "status_data": status_data
        }
        
        # Broadcast asynchronously
        try:
            loop = asyncio.get_running_loop()
            asyncio.create_task(self.broadcast_to_all(parallel_status))
        except RuntimeError:
            # No event loop running, skip broadcasting
            pass
        logger.info(f"Parallel status update [{project_name}]: {status_data}")
    
    # =====================================================
    # Chat Integration Methods
    # =====================================================
    
    def broadcast_chat_message(self, user_id: str, message: str, message_type: str = "user", project_name: str = "default"):
        """Broadcast chat message to all connected clients"""
        chat_data = {
            "type": "chat_message",
            "timestamp": datetime.now().isoformat(),
            "project": project_name,
            "user_id": user_id,
            "message": message,
            "message_type": message_type,  # "user", "system", "bot", "error"
            "message_id": str(uuid4())
        }
        
        # Add to chat history
        self.chat_history.append(chat_data)
        # Keep only last 100 messages
        if len(self.chat_history) > 100:
            self.chat_history.pop(0)
        
        # Broadcast asynchronously
        self._async_broadcast(chat_data)
        logger.info(f"Chat message from {user_id}: {message[:50]}...")
    
    def broadcast_command_execution(self, command: str, user_id: str, status: str, 
                                  command_id: Optional[str] = None, result: Optional[Dict[str, Any]] = None,
                                  project_name: str = "default"):
        """Broadcast command execution status with progress tracking"""
        if command_id is None:
            command_id = str(uuid4())
        
        command_data = {
            "type": "command_execution",
            "timestamp": datetime.now().isoformat(),
            "project": project_name,
            "command_id": command_id,
            "command": command,
            "user_id": user_id,
            "status": status,  # "started", "progress", "completed", "failed", "cancelled"
            "result": result or {}
        }
        
        # Track active commands
        if status == "started":
            self.active_commands[command_id] = {
                "command": command,
                "user_id": user_id,
                "start_time": datetime.now().isoformat(),
                "project": project_name,
                "status": "running"
            }
        elif status in ["completed", "failed", "cancelled"]:
            if command_id in self.active_commands:
                self.active_commands[command_id]["end_time"] = datetime.now().isoformat()
                self.active_commands[command_id]["status"] = status
                # Remove from active after a delay to show completion
                asyncio.create_task(self._cleanup_command(command_id, delay=5))
        
        # Broadcast asynchronously
        self._async_broadcast(command_data)
        logger.info(f"Command execution [{command_id}]: {command} - {status}")
    
    def broadcast_state_highlight(self, state_name: str, action: str, duration: float = 3.0,
                                project_name: str = "default", highlight_type: str = "current"):
        """Broadcast state highlighting for visual feedback in diagram"""
        highlight_id = str(uuid4())
        
        highlight_data = {
            "type": "state_highlight",
            "timestamp": datetime.now().isoformat(),
            "project": project_name,
            "highlight_id": highlight_id,
            "state_name": state_name,
            "action": action,  # "highlight", "pulse", "error", "success"
            "highlight_type": highlight_type,  # "current", "transition", "error", "success"
            "duration": duration
        }
        
        # Track active highlights
        self.state_highlights[highlight_id] = {
            "state_name": state_name,
            "start_time": datetime.now(),
            "duration": duration,
            "type": highlight_type
        }
        
        # Schedule highlight cleanup
        asyncio.create_task(self._cleanup_highlight(highlight_id, duration))
        
        # Broadcast asynchronously
        self._async_broadcast(highlight_data)
        logger.info(f"State highlight: {state_name} - {action}")
    
    def get_contextual_commands(self, current_state: str, user_id: str = "default", 
                              project_name: str = "default") -> List[Dict[str, Any]]:
        """Get context-aware command suggestions based on current workflow state"""
        # Try to use advanced suggestions engine first
        try:
            from .command_suggestions import get_command_suggestions
            return get_command_suggestions("", current_state, user_id, project_name, 8)
        except ImportError:
            logger.info("Advanced command suggestions not available, using fallback")
        
        # Fallback to basic suggestions
        try:
            from .state_machine import State, StateMachine
            state_enum = State(current_state)
            temp_sm = StateMachine(state_enum)
            allowed_commands = temp_sm.get_allowed_commands()
        except (ImportError, ValueError):
            # Fallback to basic command list if state machine not available
            allowed_commands = ["/help", "/state", "/epic", "/approve", "/sprint", "/backlog"]
        
        suggestions = []
        for cmd in allowed_commands:
            suggestion = {
                "command": cmd,
                "description": self._get_command_description(cmd),
                "usage": self._get_command_usage(cmd),
                "available": True,
                "priority": self._get_command_priority(cmd, current_state),
                "examples": [],
                "reason": "Available command",
                "shortcuts": []
            }
            suggestions.append(suggestion)
        
        # Sort by priority and relevance
        suggestions.sort(key=lambda x: x["priority"], reverse=True)
        
        return suggestions[:8]  # Return top 8 suggestions
    
    def broadcast_user_presence(self, user_id: str, action: str, project_name: str = "default"):
        """Broadcast user presence updates for collaboration"""
        presence_data = {
            "type": "user_presence",
            "timestamp": datetime.now().isoformat(),
            "project": project_name,
            "user_id": user_id,
            "action": action,  # "joined", "left", "typing", "idle", "active"
        }
        
        # Update user session tracking
        if action == "joined":
            self.user_sessions[user_id] = {
                "join_time": datetime.now().isoformat(),
                "project": project_name,
                "last_activity": datetime.now().isoformat(),
                "status": "active"
            }
        elif action == "left":
            if user_id in self.user_sessions:
                del self.user_sessions[user_id]
        elif action in ["typing", "active"]:
            if user_id in self.user_sessions:
                self.user_sessions[user_id]["last_activity"] = datetime.now().isoformat()
                self.user_sessions[user_id]["status"] = action
        
        # Broadcast asynchronously
        self._async_broadcast(presence_data)
        logger.info(f"User presence: {user_id} - {action}")
    
    def broadcast_error_state(self, error_type: str, error_message: str, context: Dict[str, Any] = None,
                            user_id: str = "system", project_name: str = "default"):
        """Broadcast error states with context for debugging"""
        error_data = {
            "type": "error_state",
            "timestamp": datetime.now().isoformat(),
            "project": project_name,
            "error_id": str(uuid4()),
            "error_type": error_type,  # "command_error", "validation_error", "system_error"
            "error_message": error_message,
            "user_id": user_id,
            "context": context or {},
            "severity": self._classify_error_severity(error_type, error_message)
        }
        
        # Broadcast asynchronously
        self._async_broadcast(error_data)
        logger.error(f"Error state: {error_type} - {error_message}")
    
    def get_chat_history(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get recent chat history"""
        return self.chat_history[-limit:] if limit > 0 else self.chat_history
    
    def get_active_commands(self) -> Dict[str, Dict[str, Any]]:
        """Get currently active commands"""
        return self.active_commands.copy()
    
    def get_user_sessions(self) -> Dict[str, Dict[str, Any]]:
        """Get active user sessions"""
        return self.user_sessions.copy()
    
    # =====================================================
    # Helper Methods
    # =====================================================
    
    async def _cleanup_command(self, command_id: str, delay: float = 5.0):
        """Clean up completed command after delay"""
        await asyncio.sleep(delay)
        if command_id in self.active_commands:
            del self.active_commands[command_id]
    
    async def _cleanup_highlight(self, highlight_id: str, duration: float):
        """Clean up state highlight after duration"""
        await asyncio.sleep(duration)
        if highlight_id in self.state_highlights:
            del self.state_highlights[highlight_id]
    
    def _async_broadcast(self, data: Dict[str, Any]):
        """Helper to broadcast data asynchronously"""
        try:
            loop = asyncio.get_running_loop()
            asyncio.create_task(self.broadcast_to_all(data))
        except RuntimeError:
            # No event loop running, skip broadcasting
            pass
    
    def _get_command_description(self, command: str) -> str:
        """Get description for a command"""
        descriptions = {
            "/epic": "Define a new high-level initiative",
            "/approve": "Approve proposed stories or tasks",
            "/sprint": "Sprint lifecycle management",
            "/backlog": "Manage product and sprint backlog",
            "/state": "Show current workflow state",
            "/project": "Project management commands",
            "/request_changes": "Request changes to a PR",
            "/help": "Show available commands and usage"
        }
        return descriptions.get(command, "No description available")
    
    def _get_command_usage(self, command: str) -> str:
        """Get usage information for a command"""
        usage = {
            "/epic": '/epic "description"',
            "/approve": "/approve [item_ids]",
            "/sprint": "/sprint <action> [parameters]",
            "/backlog": "/backlog <action> [parameters]",
            "/state": "/state",
            "/project": "/project <action> [parameters]",
            "/request_changes": '/request_changes "description"',
            "/help": "/help [command]"
        }
        return usage.get(command, command)
    
    def _get_command_priority(self, command: str, current_state: str) -> int:
        """Get priority for command suggestions based on current state"""
        # Base priorities
        base_priority = {
            "/help": 1,
            "/state": 2,
            "/epic": 5,
            "/approve": 4,
            "/sprint": 6,
            "/backlog": 3,
            "/project": 2,
            "/request_changes": 4
        }
        
        # State-specific boosts
        state_boosts = {
            "IDLE": {"/epic": 3, "/project": 2},
            "BACKLOG_READY": {"/approve": 3, "/sprint": 2},
            "SPRINT_PLANNED": {"/sprint": 3},
            "SPRINT_ACTIVE": {"/sprint": 2, "/state": 1},
            "SPRINT_PAUSED": {"/sprint": 3},
            "SPRINT_REVIEW": {"/request_changes": 3}
        }
        
        priority = base_priority.get(command, 1)
        if current_state in state_boosts:
            priority += state_boosts[current_state].get(command, 0)
        
        return priority
    
    def _classify_error_severity(self, error_type: str, error_message: str) -> str:
        """Classify error severity for proper handling"""
        if "validation" in error_type.lower():
            return "warning"
        elif "system" in error_type.lower() or "failed" in error_message.lower():
            return "error"
        elif "command" in error_type.lower():
            return "info"
        else:
            return "warning"
        
    def get_current_state(self) -> Dict[str, Any]:
        """Get current state as dictionary"""
        return {
            "workflow_state": self.current_workflow_state.value if hasattr(self.current_workflow_state, 'value') else str(self.current_workflow_state),
            "tdd_cycles": self.tdd_cycles,
            "active_cycles": len(self.tdd_cycles),
            "last_updated": datetime.now().isoformat(),
            # Chat integration data
            "active_commands": len(self.active_commands),
            "active_users": len(self.user_sessions),
            "chat_messages": len(self.chat_history),
            "state_highlights": len(self.state_highlights)
        }


# Global instance
broadcaster = StatebroadCaster()


def emit_workflow_transition(old_state: State, new_state: State, project_name: str = "default"):
    """Convenience function for workflow transitions"""
    broadcaster.emit_workflow_transition(old_state, new_state, project_name)


def emit_tdd_transition(story_id: str, old_state: Optional[TDDState], new_state: TDDState, project_name: str = "default"):
    """Convenience function for TDD transitions"""
    broadcaster.emit_tdd_transition(story_id, old_state, new_state, project_name)


def emit_agent_activity(agent_type: str, story_id: str, action: str, status: str, project_name: str = "default"):
    """Convenience function for agent activity"""
    broadcaster.emit_agent_activity(agent_type, story_id, action, status, project_name)


def emit_parallel_status(status_data: Dict[str, Any], project_name: str = "default"):
    """Convenience function for parallel status"""
    broadcaster.emit_parallel_status(status_data, project_name)


# =====================================================
# Chat Integration Convenience Functions
# =====================================================

def broadcast_chat_message(user_id: str, message: str, message_type: str = "user", project_name: str = "default"):
    """Convenience function for broadcasting chat messages"""
    broadcaster.broadcast_chat_message(user_id, message, message_type, project_name)


def broadcast_command_execution(command: str, user_id: str, status: str, 
                              command_id: Optional[str] = None, result: Optional[Dict[str, Any]] = None,
                              project_name: str = "default"):
    """Convenience function for broadcasting command execution status"""
    broadcaster.broadcast_command_execution(command, user_id, status, command_id, result, project_name)


def broadcast_state_highlight(state_name: str, action: str, duration: float = 3.0,
                            project_name: str = "default", highlight_type: str = "current"):
    """Convenience function for broadcasting state highlights"""
    broadcaster.broadcast_state_highlight(state_name, action, duration, project_name, highlight_type)


def get_contextual_commands(current_state: str, user_id: str = "default", 
                          project_name: str = "default") -> List[Dict[str, Any]]:
    """Convenience function for getting contextual command suggestions"""
    return broadcaster.get_contextual_commands(current_state, user_id, project_name)


def broadcast_user_presence(user_id: str, action: str, project_name: str = "default"):
    """Convenience function for broadcasting user presence"""
    broadcaster.broadcast_user_presence(user_id, action, project_name)


def broadcast_error_state(error_type: str, error_message: str, context: Dict[str, Any] = None,
                        user_id: str = "system", project_name: str = "default"):
    """Convenience function for broadcasting error states"""
    broadcaster.broadcast_error_state(error_type, error_message, context, user_id, project_name)


def get_chat_history(limit: int = 50) -> List[Dict[str, Any]]:
    """Convenience function for getting chat history"""
    return broadcaster.get_chat_history(limit)


def get_active_commands() -> Dict[str, Dict[str, Any]]:
    """Convenience function for getting active commands"""
    return broadcaster.get_active_commands()


def get_user_sessions() -> Dict[str, Dict[str, Any]]:
    """Convenience function for getting user sessions"""
    return broadcaster.get_user_sessions()


async def start_broadcaster(port: int = 8080):
    """Start the state broadcaster server"""
    await broadcaster.start_server(port)


async def stop_broadcaster():
    """Stop the state broadcaster server"""
    await broadcaster.stop_server()