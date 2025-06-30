#!/usr/bin/env python3
"""
Chat-State Synchronization System

Provides bidirectional synchronization between chat interface and state machine,
ensuring real-time consistency and visual feedback across all connected clients.
"""

import logging
import asyncio
from typing import Dict, Any, Optional, List, Callable
from datetime import datetime
from dataclasses import dataclass
from uuid import uuid4

# Import state system components
try:
    from .state_machine import State, StateMachine, CommandResult
    from .state_broadcaster import (
        broadcaster, 
        broadcast_command_execution, 
        broadcast_state_highlight,
        broadcast_error_state,
        broadcast_chat_message
    )
except ImportError:
    # Fallback for standalone usage
    from state_machine import State, StateMachine, CommandResult
    from state_broadcaster import (
        broadcaster, 
        broadcast_command_execution, 
        broadcast_state_highlight,
        broadcast_error_state,
        broadcast_chat_message
    )

logger = logging.getLogger(__name__)


@dataclass
class SyncEvent:
    """Represents a synchronization event between chat and state machine"""
    event_id: str
    event_type: str  # "command_started", "command_completed", "state_changed", "error_occurred"
    source: str  # "chat", "state_machine", "system"
    timestamp: str
    data: Dict[str, Any]
    project_name: str = "default"


class ChatStateSynchronizer:
    """
    Manages bidirectional synchronization between chat interface and state machine.
    
    Features:
    - Real-time command execution tracking
    - State change notifications to chat
    - Visual state highlighting
    - Progress indicators for long-running commands
    - Error handling and recovery suggestions
    """
    
    def __init__(self, state_machine: Optional[StateMachine] = None):
        self.state_machine = state_machine or StateMachine()
        self.active_synchronizations: Dict[str, SyncEvent] = {}
        self.command_handlers: Dict[str, Callable] = {}
        self.state_change_listeners: List[Callable] = []
        self.error_handlers: List[Callable] = []
        
        # Initialize command handlers
        self._initialize_command_handlers()
        
        # Set up state machine listener
        self._setup_state_machine_listener()
        
        logger.info("ChatStateSynchronizer initialized")
    
    def _initialize_command_handlers(self):
        """Initialize command-specific handlers for chat integration"""
        self.command_handlers = {
            "/epic": self._handle_epic_sync,
            "/approve": self._handle_approve_sync,
            "/sprint": self._handle_sprint_sync,
            "/backlog": self._handle_backlog_sync,
            "/state": self._handle_state_sync,
            "/project": self._handle_project_sync,
            "/request_changes": self._handle_request_changes_sync,
            "/help": self._handle_help_sync
        }
    
    def _setup_state_machine_listener(self):
        """Set up listener for state machine changes"""
        # Store original transition method
        original_transition = self.state_machine.transition
        
        def synced_transition(command: str, project_name: str = "default") -> CommandResult:
            """Wrapped transition method that triggers sync events"""
            old_state = self.state_machine.current_state
            
            try:
                # Execute the transition
                result = original_transition(command, project_name)
                
                # If successful, trigger sync events
                if result.success and result.new_state:
                    self._on_state_changed(old_state, result.new_state, command, project_name)
                else:
                    self._on_command_failed(command, result.error_message or "Unknown error", project_name)
                
                return result
                
            except Exception as e:
                logger.error(f"Error in state transition: {e}")
                self._on_command_failed(command, str(e), project_name)
                raise
        
        # Replace the transition method
        self.state_machine.transition = synced_transition
    
    async def process_chat_command(self, command: str, user_id: str, project_name: str = "default") -> Dict[str, Any]:
        """
        Process a command from chat interface with full synchronization.
        
        Args:
            command: The command string (e.g., "/epic 'description'")
            user_id: User identifier
            project_name: Project name for context
            
        Returns:
            Dictionary with command result and sync information
        """
        command_id = str(uuid4())
        
        # Start command execution tracking
        self._start_command_tracking(command_id, command, user_id, project_name)
        
        try:
            # Validate command with state machine
            base_command = command.split()[0]
            validation_result = self.state_machine.validate_command(base_command)
            
            if not validation_result.success:
                # Command validation failed
                await self._handle_command_validation_failure(
                    command_id, command, validation_result, user_id, project_name
                )
                return {
                    "success": False,
                    "command_id": command_id,
                    "error": validation_result.error_message,
                    "hint": validation_result.hint,
                    "current_state": self.state_machine.current_state.value
                }
            
            # Highlight current state before transition
            await self._highlight_state_transition(
                self.state_machine.current_state.value, 
                validation_result.new_state.value if validation_result.new_state else None,
                project_name
            )
            
            # Execute command through appropriate handler
            handler = self.command_handlers.get(base_command, self._handle_generic_command)
            result = await handler(command, user_id, project_name, command_id)
            
            # Complete command tracking
            self._complete_command_tracking(command_id, "completed", result)
            
            return {
                "success": True,
                "command_id": command_id,
                "result": result,
                "new_state": self.state_machine.current_state.value
            }
            
        except Exception as e:
            logger.error(f"Error processing chat command: {e}")
            
            # Handle command failure
            await self._handle_command_failure(command_id, command, str(e), user_id, project_name)
            
            return {
                "success": False,
                "command_id": command_id,
                "error": str(e),
                "current_state": self.state_machine.current_state.value
            }
    
    def _start_command_tracking(self, command_id: str, command: str, user_id: str, project_name: str):
        """Start tracking a command execution"""
        sync_event = SyncEvent(
            event_id=command_id,
            event_type="command_started",
            source="chat",
            timestamp=datetime.now().isoformat(),
            data={
                "command": command,
                "user_id": user_id,
                "state_before": self.state_machine.current_state.value
            },
            project_name=project_name
        )
        
        self.active_synchronizations[command_id] = sync_event
        
        # Broadcast command execution start
        broadcast_command_execution(
            command=command,
            user_id=user_id,
            status="started",
            command_id=command_id,
            project_name=project_name
        )
        
        logger.info(f"Started tracking command: {command_id}")
    
    def _complete_command_tracking(self, command_id: str, status: str, result: Dict[str, Any]):
        """Complete command tracking with result"""
        if command_id in self.active_synchronizations:
            sync_event = self.active_synchronizations[command_id]
            sync_event.event_type = "command_completed"
            sync_event.data.update({
                "status": status,
                "result": result,
                "state_after": self.state_machine.current_state.value,
                "completion_time": datetime.now().isoformat()
            })
            
            # Broadcast command completion
            broadcast_command_execution(
                command=sync_event.data["command"],
                user_id=sync_event.data["user_id"],
                status=status,
                command_id=command_id,
                result=result,
                project_name=sync_event.project_name
            )
            
            # Clean up after delay
            asyncio.create_task(self._cleanup_sync_event(command_id, delay=10))
        
        logger.info(f"Completed tracking command: {command_id} with status: {status}")
    
    async def _cleanup_sync_event(self, command_id: str, delay: float = 10):
        """Clean up synchronization event after delay"""
        await asyncio.sleep(delay)
        if command_id in self.active_synchronizations:
            del self.active_synchronizations[command_id]
    
    def _on_state_changed(self, old_state: State, new_state: State, command: str, project_name: str):
        """Handle state machine state changes"""
        # Broadcast state change notification
        broadcast_chat_message(
            user_id="system",
            message=f"🔄 State changed: {old_state.value} → {new_state.value}",
            message_type="system",
            project_name=project_name
        )
        
        # Highlight new state
        broadcast_state_highlight(
            state_name=new_state.value,
            action="highlight",
            duration=2.0,
            project_name=project_name,
            highlight_type="current"
        )
        
        # Notify listeners
        for listener in self.state_change_listeners:
            try:
                listener(old_state, new_state, command, project_name)
            except Exception as e:
                logger.error(f"Error in state change listener: {e}")
        
        logger.info(f"State synchronization: {old_state.value} → {new_state.value}")
    
    def _on_command_failed(self, command: str, error_message: str, project_name: str):
        """Handle command failures"""
        broadcast_error_state(
            error_type="command_error",
            error_message=error_message,
            context={"command": command},
            project_name=project_name
        )
        
        # Provide helpful suggestions
        suggestions = self._get_error_recovery_suggestions(command, error_message)
        if suggestions:
            broadcast_chat_message(
                user_id="system",
                message=f"💡 Suggestions: {', '.join(suggestions)}",
                message_type="system",
                project_name=project_name
            )
    
    async def _handle_command_validation_failure(self, command_id: str, command: str, 
                                               validation_result: CommandResult, user_id: str, project_name: str):
        """Handle command validation failures with helpful feedback"""
        # Broadcast validation error
        broadcast_error_state(
            error_type="validation_error",
            error_message=validation_result.error_message or "Command validation failed",
            context={
                "command": command,
                "current_state": self.state_machine.current_state.value,
                "hint": validation_result.hint
            },
            user_id=user_id,
            project_name=project_name
        )
        
        # Highlight current state to show where user is
        broadcast_state_highlight(
            state_name=self.state_machine.current_state.value,
            action="error",
            duration=2.0,
            project_name=project_name,
            highlight_type="error"
        )
        
        # Complete command tracking as failed
        self._complete_command_tracking(command_id, "failed", {
            "error": validation_result.error_message,
            "hint": validation_result.hint
        })
    
    async def _handle_command_failure(self, command_id: str, command: str, error: str, user_id: str, project_name: str):
        """Handle general command execution failures"""
        broadcast_error_state(
            error_type="system_error",
            error_message=error,
            context={"command": command},
            user_id=user_id,
            project_name=project_name
        )
        
        # Complete command tracking as failed
        self._complete_command_tracking(command_id, "failed", {"error": error})
    
    async def _highlight_state_transition(self, current_state: str, target_state: Optional[str], project_name: str):
        """Highlight state transition visually"""
        # Highlight current state
        broadcast_state_highlight(
            state_name=current_state,
            action="pulse",
            duration=1.0,
            project_name=project_name,
            highlight_type="transition"
        )
        
        # If transitioning to new state, show target
        if target_state and target_state != current_state:
            await asyncio.sleep(0.5)  # Small delay for visual effect
            broadcast_state_highlight(
                state_name=target_state,
                action="highlight",
                duration=2.0,
                project_name=project_name,
                highlight_type="target"
            )
    
    def _get_error_recovery_suggestions(self, command: str, error_message: str) -> List[str]:
        """Get recovery suggestions for command errors"""
        base_command = command.split()[0]
        current_state = self.state_machine.current_state.value
        
        suggestions = []
        
        # State-specific suggestions
        if "not allowed" in error_message.lower():
            allowed_commands = self.state_machine.get_allowed_commands()
            if allowed_commands:
                suggestions.append(f"Try: {', '.join(allowed_commands[:3])}")
        
        # Command-specific suggestions
        if base_command == "/sprint" and current_state == "IDLE":
            suggestions.append("Create an epic first with /epic")
        elif base_command == "/epic" and current_state == "SPRINT_ACTIVE":
            suggestions.append("Pause the sprint first with /sprint pause")
        
        # Generic suggestions
        suggestions.append("Use /state to see current workflow state")
        suggestions.append("Use /help for available commands")
        
        return suggestions[:3]  # Return top 3 suggestions
    
    # =====================================================
    # Command-Specific Handlers
    # =====================================================
    
    async def _handle_epic_sync(self, command: str, user_id: str, project_name: str, command_id: str) -> Dict[str, Any]:
        """Handle /epic command with synchronization"""
        # Extract epic description
        parts = command.split('"')
        if len(parts) < 2:
            raise ValueError("Epic description is required")
        
        description = parts[1]
        
        # Execute state transition
        result = self.state_machine.transition("/epic", project_name)
        
        # Broadcast epic creation
        broadcast_chat_message(
            user_id="system",
            message=f"📋 Epic created: {description}",
            message_type="system",
            project_name=project_name
        )
        
        return {
            "epic_description": description,
            "state_transition": result.success,
            "new_state": self.state_machine.current_state.value
        }
    
    async def _handle_approve_sync(self, command: str, user_id: str, project_name: str, command_id: str) -> Dict[str, Any]:
        """Handle /approve command with synchronization"""
        # Execute state transition
        result = self.state_machine.transition("/approve", project_name)
        
        # Broadcast approval
        broadcast_chat_message(
            user_id="system",
            message="✅ Items approved",
            message_type="system",
            project_name=project_name
        )
        
        return {
            "approved": True,
            "state_transition": result.success,
            "new_state": self.state_machine.current_state.value
        }
    
    async def _handle_sprint_sync(self, command: str, user_id: str, project_name: str, command_id: str) -> Dict[str, Any]:
        """Handle /sprint commands with synchronization"""
        parts = command.split()
        if len(parts) < 2:
            raise ValueError("Sprint action is required")
        
        action = parts[1]
        full_command = f"/sprint {action}"
        
        # Execute state transition
        result = self.state_machine.transition(full_command, project_name)
        
        # Broadcast sprint action
        action_messages = {
            "plan": "📋 Sprint planned",
            "start": "🚀 Sprint started",
            "pause": "⏸️ Sprint paused",
            "resume": "▶️ Sprint resumed",
            "status": "📊 Sprint status requested"
        }
        
        message = action_messages.get(action, f"🏃 Sprint {action}")
        broadcast_chat_message(
            user_id="system",
            message=message,
            message_type="system",
            project_name=project_name
        )
        
        return {
            "sprint_action": action,
            "state_transition": result.success,
            "new_state": self.state_machine.current_state.value
        }
    
    async def _handle_backlog_sync(self, command: str, user_id: str, project_name: str, command_id: str) -> Dict[str, Any]:
        """Handle /backlog commands with synchronization"""
        parts = command.split()
        if len(parts) < 2:
            raise ValueError("Backlog action is required")
        
        action = parts[1]
        
        # Backlog commands don't change state, but we still track them
        broadcast_chat_message(
            user_id="system",
            message=f"📋 Backlog {action} executed",
            message_type="system",
            project_name=project_name
        )
        
        return {
            "backlog_action": action,
            "state_unchanged": True,
            "current_state": self.state_machine.current_state.value
        }
    
    async def _handle_state_sync(self, command: str, user_id: str, project_name: str, command_id: str) -> Dict[str, Any]:
        """Handle /state command with synchronization"""
        # Get current state info
        state_info = self.state_machine.get_state_info()
        
        # Highlight current state
        broadcast_state_highlight(
            state_name=self.state_machine.current_state.value,
            action="pulse",
            duration=3.0,
            project_name=project_name,
            highlight_type="info"
        )
        
        # Broadcast state information
        broadcast_chat_message(
            user_id="system",
            message=f"🔄 Current state: {self.state_machine.current_state.value}",
            message_type="system",
            project_name=project_name
        )
        
        return {
            "state_info": state_info,
            "current_state": self.state_machine.current_state.value
        }
    
    async def _handle_project_sync(self, command: str, user_id: str, project_name: str, command_id: str) -> Dict[str, Any]:
        """Handle /project commands with synchronization"""
        broadcast_chat_message(
            user_id="system",
            message="🏗️ Project command executed",
            message_type="system",
            project_name=project_name
        )
        
        return {
            "project_command": True,
            "current_state": self.state_machine.current_state.value
        }
    
    async def _handle_request_changes_sync(self, command: str, user_id: str, project_name: str, command_id: str) -> Dict[str, Any]:
        """Handle /request_changes command with synchronization"""
        # Execute state transition
        result = self.state_machine.transition("/request_changes", project_name)
        
        broadcast_chat_message(
            user_id="system",
            message="📝 Changes requested",
            message_type="system",
            project_name=project_name
        )
        
        return {
            "changes_requested": True,
            "state_transition": result.success,
            "new_state": self.state_machine.current_state.value
        }
    
    async def _handle_help_sync(self, command: str, user_id: str, project_name: str, command_id: str) -> Dict[str, Any]:
        """Handle /help command with synchronization"""
        # Get contextual commands
        contextual_commands = broadcaster.get_contextual_commands(
            self.state_machine.current_state.value, 
            user_id, 
            project_name
        )
        
        broadcast_chat_message(
            user_id="system",
            message="❓ Help information provided",
            message_type="system",
            project_name=project_name
        )
        
        return {
            "help_requested": True,
            "contextual_commands": contextual_commands,
            "current_state": self.state_machine.current_state.value
        }
    
    async def _handle_generic_command(self, command: str, user_id: str, project_name: str, command_id: str) -> Dict[str, Any]:
        """Handle generic commands with basic synchronization"""
        broadcast_chat_message(
            user_id="system",
            message=f"⚙️ Command executed: {command}",
            message_type="system",
            project_name=project_name
        )
        
        return {
            "command": command,
            "current_state": self.state_machine.current_state.value
        }
    
    # =====================================================
    # Listener Management
    # =====================================================
    
    def add_state_change_listener(self, listener: Callable):
        """Add a listener for state changes"""
        self.state_change_listeners.append(listener)
    
    def remove_state_change_listener(self, listener: Callable):
        """Remove a state change listener"""
        if listener in self.state_change_listeners:
            self.state_change_listeners.remove(listener)
    
    def add_error_handler(self, handler: Callable):
        """Add an error handler"""
        self.error_handlers.append(handler)
    
    def remove_error_handler(self, handler: Callable):
        """Remove an error handler"""
        if handler in self.error_handlers:
            self.error_handlers.remove(handler)
    
    # =====================================================
    # Status and Debugging
    # =====================================================
    
    def get_sync_status(self) -> Dict[str, Any]:
        """Get current synchronization status"""
        return {
            "active_synchronizations": len(self.active_synchronizations),
            "current_state": self.state_machine.current_state.value,
            "state_change_listeners": len(self.state_change_listeners),
            "error_handlers": len(self.error_handlers),
            "command_handlers": list(self.command_handlers.keys())
        }
    
    def get_active_sync_events(self) -> List[Dict[str, Any]]:
        """Get list of active synchronization events"""
        return [
            {
                "event_id": event.event_id,
                "event_type": event.event_type,
                "source": event.source,
                "timestamp": event.timestamp,
                "command": event.data.get("command"),
                "user_id": event.data.get("user_id"),
                "project_name": event.project_name
            }
            for event in self.active_synchronizations.values()
        ]


# Global synchronizer instance
_synchronizer = None

def get_synchronizer(state_machine: Optional[StateMachine] = None) -> ChatStateSynchronizer:
    """Get global synchronizer instance"""
    global _synchronizer
    if _synchronizer is None:
        _synchronizer = ChatStateSynchronizer(state_machine)
    return _synchronizer


# Convenience function for external usage
async def process_chat_command(command: str, user_id: str, project_name: str = "default", 
                             state_machine: Optional[StateMachine] = None) -> Dict[str, Any]:
    """
    Convenience function to process a chat command with synchronization.
    
    Args:
        command: The command string
        user_id: User identifier  
        project_name: Project name
        state_machine: Optional state machine instance
        
    Returns:
        Dictionary with command result and sync information
    """
    synchronizer = get_synchronizer(state_machine)
    return await synchronizer.process_chat_command(command, user_id, project_name)