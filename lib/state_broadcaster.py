"""
State Broadcasting System for Real-Time Visualization

Provides WebSocket broadcasting of state machine changes for real-time
visualization and monitoring of workflow and TDD state transitions.
"""

import asyncio
import json
import logging
import weakref
from typing import Dict, List, Optional, Any, Set
from datetime import datetime
from dataclasses import asdict
import websockets
from websockets.server import WebSocketServerProtocol

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
        asyncio.create_task(self.broadcast_to_all(transition))
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
        asyncio.create_task(self.broadcast_to_all(transition))
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
        asyncio.create_task(self.broadcast_to_all(activity))
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
        asyncio.create_task(self.broadcast_to_all(parallel_status))
        logger.info(f"Parallel status update [{project_name}]: {status_data}")
        
    def get_current_state(self) -> Dict[str, Any]:
        """Get current state as dictionary"""
        return {
            "workflow_state": self.current_workflow_state.value if hasattr(self.current_workflow_state, 'value') else str(self.current_workflow_state),
            "tdd_cycles": self.tdd_cycles,
            "active_cycles": len(self.tdd_cycles),
            "last_updated": datetime.now().isoformat()
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


async def start_broadcaster(port: int = 8080):
    """Start the state broadcaster server"""
    await broadcaster.start_server(port)


async def stop_broadcaster():
    """Stop the state broadcaster server"""
    await broadcaster.stop_server()