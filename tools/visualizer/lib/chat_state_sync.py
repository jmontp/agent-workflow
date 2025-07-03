#!/usr/bin/env python3
"""
Chat State Synchronization Module

Provides bidirectional synchronization between Discord-style chat commands
and the underlying workflow state machine, enabling real-time coordination
and collaborative features.
"""

import asyncio
import json
import logging
import sys
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime

# Add lib directory to path for imports
lib_path = Path(__file__).parent.parent.parent / "lib"
sys.path.insert(0, str(lib_path))

logger = logging.getLogger(__name__)

# Try to import state broadcaster and state machine with prioritized pattern: agent_workflow → lib → fallback
try:
    # Primary: Try agent_workflow package first
    from agent_workflow.core.state_broadcaster import broadcaster
    STATE_BROADCASTER_AVAILABLE = True
except ImportError:
    try:
        # Secondary: Try lib directory for backward compatibility
        from state_broadcaster import broadcaster
        STATE_BROADCASTER_AVAILABLE = True
    except ImportError:
        logger.warning("State broadcaster not available - using mock implementation")
        STATE_BROADCASTER_AVAILABLE = False

try:
    # Primary: Try agent_workflow package first
    from agent_workflow.core.state_machine import StateMachine
    STATE_MACHINE_AVAILABLE = True
except ImportError:
    try:
        # Secondary: Try lib directory for backward compatibility
        from state_machine import StateMachine
        STATE_MACHINE_AVAILABLE = True
    except ImportError:
        logger.warning("State machine not available - using mock implementation")
        STATE_MACHINE_AVAILABLE = False


class ChatStateSynchronizer:
    """
    Synchronizes chat commands with the workflow state machine.
    
    Provides bidirectional synchronization between Discord-style chat interface
    and the underlying state machine, enabling real-time collaboration and
    ensuring consistent state across all interfaces.
    """
    
    def __init__(self):
        self.state_machine = None
        self.broadcaster = None
        self.command_queue = []
        self.sync_active = False
        self.sync_status = {
            "synchronized": False,
            "last_sync": None,
            "pending_commands": 0,
            "errors": []
        }
        
        # Initialize components
        self._initialize_state_machine()
        self._initialize_broadcaster()
        
    def _initialize_state_machine(self):
        """Initialize state machine integration"""
        if STATE_MACHINE_AVAILABLE:
            try:
                self.state_machine = StateMachine()
                logger.info("Chat state synchronizer initialized with state machine")
            except Exception as e:
                logger.error(f"Failed to initialize state machine: {e}")
                self.state_machine = None
        else:
            logger.warning("State machine not available - using mock implementation")
            self.state_machine = None
            
    def _initialize_broadcaster(self):
        """Initialize state broadcaster integration"""
        if STATE_BROADCASTER_AVAILABLE:
            try:
                self.broadcaster = broadcaster
                logger.info("Chat state synchronizer initialized with broadcaster")
            except Exception as e:
                logger.error(f"Failed to initialize broadcaster: {e}")
                self.broadcaster = None
        else:
            logger.warning("State broadcaster not available - using mock implementation")
            self.broadcaster = None
    
    async def process_chat_command(self, command: str, user_id: str, 
                                 project_name: str = "default") -> Dict[str, Any]:
        """
        Process a chat command with full state synchronization.
        
        Args:
            command: The command string from chat
            user_id: User identifier
            project_name: Project context
            
        Returns:
            Dictionary containing command result with sync information
        """
        try:
            command_id = f"cmd_{datetime.now().timestamp()}"
            
            # Validate command format
            if not command.startswith('/'):
                return {
                    "success": False,
                    "command_id": command_id,
                    "error": "Commands must start with '/'",
                    "hint": "Type '/help' for available commands",
                    "current_state": self._get_current_state()
                }
            
            # Get current state
            current_state = self._get_current_state()
            
            # Parse command
            command_parts = command.strip().split()
            base_command = command_parts[0] if command_parts else ""
            
            # Validate command against current state
            validation = self._validate_command_for_state(base_command, current_state)
            if not validation["valid"]:
                return {
                    "success": False,
                    "command_id": command_id,
                    "error": validation["error"],
                    "hint": validation.get("hint"),
                    "current_state": current_state,
                    "allowed_commands": validation.get("allowed_commands", [])
                }
            
            # Execute command
            result = await self._execute_command(command, user_id, project_name)
            result["command_id"] = command_id
            
            # Synchronize state if command succeeded
            if result.get("success"):
                await self._synchronize_state_change(result, user_id, project_name)
            
            return result
            
        except Exception as e:
            logger.error(f"Error processing chat command: {e}")
            return {
                "success": False,
                "command_id": command_id,
                "error": f"Internal error: {str(e)}",
                "current_state": self._get_current_state()
            }
    
    def _get_current_state(self) -> str:
        """Get current workflow state"""
        if self.broadcaster and STATE_BROADCASTER_AVAILABLE:
            try:
                state_data = self.broadcaster.get_current_state()
                return state_data.get("workflow_state", "IDLE")
            except Exception as e:
                logger.error(f"Error getting current state: {e}")
        
        return "IDLE"  # Default fallback
    
    def _validate_command_for_state(self, command: str, current_state: str) -> Dict[str, Any]:
        """
        Validate if a command is allowed in the current state.
        
        Args:
            command: The command to validate
            current_state: Current workflow state
            
        Returns:
            Dictionary with validation result
        """
        # State transition rules (simplified version)
        state_commands = {
            "IDLE": ["/epic", "/project", "/help", "/state"],
            "BACKLOG_READY": ["/approve", "/sprint", "/backlog", "/help", "/state"],
            "SPRINT_PLANNED": ["/sprint", "/help", "/state"],
            "SPRINT_ACTIVE": ["/sprint", "/help", "/state"],
            "SPRINT_PAUSED": ["/sprint", "/help", "/state"],
            "SPRINT_REVIEW": ["/request_changes", "/feedback", "/help", "/state"],
            "BLOCKED": ["/suggest_fix", "/skip_task", "/help", "/state"]
        }
        
        # Commands that are always allowed
        always_allowed = ["/help", "/state"]
        
        if command in always_allowed:
            return {"valid": True}
        
        allowed_commands = state_commands.get(current_state, [])
        
        if command in allowed_commands:
            return {"valid": True}
        
        # Provide helpful error message
        hint = None
        if current_state == "IDLE":
            hint = "Start by creating an epic with '/epic \"description\"'"
        elif current_state == "BACKLOG_READY":
            hint = "Approve stories with '/approve' or plan a sprint with '/sprint plan'"
        elif current_state == "SPRINT_PLANNED":
            hint = "Start the sprint with '/sprint start'"
        elif current_state == "SPRINT_ACTIVE":
            hint = "Check sprint status with '/sprint status' or pause with '/sprint pause'"
        
        return {
            "valid": False,
            "error": f"Command '{command}' not allowed in state '{current_state}'",
            "hint": hint,
            "allowed_commands": allowed_commands
        }
    
    async def _execute_command(self, command: str, user_id: str, 
                             project_name: str) -> Dict[str, Any]:
        """
        Execute the command using the state machine.
        
        Args:
            command: Command to execute
            user_id: User identifier
            project_name: Project context
            
        Returns:
            Command execution result
        """
        if self.state_machine and STATE_MACHINE_AVAILABLE:
            try:
                # Use state machine to execute command
                result = await self._execute_via_state_machine(command, user_id, project_name)
                return result
            except Exception as e:
                logger.error(f"Error executing command via state machine: {e}")
                return {
                    "success": False,
                    "error": f"Execution failed: {str(e)}"
                }
        else:
            # Mock execution for testing
            return await self._mock_command_execution(command, user_id, project_name)
    
    async def _execute_via_state_machine(self, command: str, user_id: str, 
                                       project_name: str) -> Dict[str, Any]:
        """Execute command using the actual state machine"""
        try:
            # Parse command
            command_parts = command.strip().split()
            base_command = command_parts[0] if command_parts else ""
            
            # Map chat commands to state machine transitions
            command_mapping = {
                "/epic": "epic_created",
                "/approve": "stories_approved", 
                "/sprint plan": "sprint_planned",
                "/sprint start": "sprint_started",
                "/sprint pause": "sprint_paused",
                "/sprint resume": "sprint_resumed",
                "/sprint status": None,  # Query command, no state change
                "/backlog view": None,
                "/backlog add_story": None,
                "/backlog prioritize": None,
                "/request_changes": "changes_requested",
                "/feedback": "feedback_provided",
                "/help": None,
                "/state": None
            }
            
            transition = command_mapping.get(base_command)
            
            if transition:
                # Execute state transition
                old_state = self.state_machine.current_state
                self.state_machine.trigger(transition)
                new_state = self.state_machine.current_state
                
                return {
                    "success": True,
                    "command": command,
                    "old_state": old_state,
                    "new_state": new_state,
                    "transition": transition,
                    "message": f"State changed from {old_state} to {new_state}"
                }
            else:
                # Query command - no state change
                return {
                    "success": True,
                    "command": command,
                    "current_state": self.state_machine.current_state,
                    "message": f"Command executed successfully"
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": f"State machine execution failed: {str(e)}"
            }
    
    async def _mock_command_execution(self, command: str, user_id: str, 
                                    project_name: str) -> Dict[str, Any]:
        """Mock command execution for testing"""
        command_parts = command.strip().split()
        base_command = command_parts[0] if command_parts else ""
        
        # Simulate successful execution
        mock_results = {
            "/epic": {
                "success": True,
                "message": "Epic created successfully (mock)",
                "new_state": "BACKLOG_READY"
            },
            "/approve": {
                "success": True,
                "message": "Stories approved successfully (mock)",
                "approved_count": 2
            },
            "/sprint plan": {
                "success": True,
                "message": "Sprint planned successfully (mock)",
                "new_state": "SPRINT_PLANNED"
            },
            "/sprint start": {
                "success": True,
                "message": "Sprint started successfully (mock)",
                "new_state": "SPRINT_ACTIVE"
            },
            "/sprint status": {
                "success": True,
                "message": "Sprint status retrieved (mock)",
                "total_tasks": 5,
                "completed_tasks": 2,
                "failed_tasks": 0
            },
            "/state": {
                "success": True,
                "message": "Current state retrieved (mock)",
                "current_state": self._get_current_state()
            }
        }
        
        result = mock_results.get(base_command, {
            "success": True,
            "message": f"Command {base_command} executed (mock)"
        })
        
        result["command"] = command
        result["mock"] = True
        return result
    
    async def _synchronize_state_change(self, result: Dict[str, Any], 
                                      user_id: str, project_name: str):
        """
        Synchronize state changes to the broadcaster.
        
        Args:
            result: Command execution result
            user_id: User who executed the command
            project_name: Project context
        """
        try:
            if not self.broadcaster or not STATE_BROADCASTER_AVAILABLE:
                return
            
            # Create state change event
            if result.get("new_state"):
                sync_event = {
                    "type": "workflow_transition",
                    "old_state": result.get("old_state"),
                    "new_state": result.get("new_state"),
                    "trigger": result.get("transition"),
                    "user_id": user_id,
                    "project_name": project_name,
                    "timestamp": datetime.now().isoformat(),
                    "source": "chat_command",
                    "command": result.get("command")
                }
                
                # Broadcast the state change
                await self.broadcaster.broadcast_state_change(sync_event)
                logger.info(f"Synchronized state change: {result.get('old_state')} -> {result.get('new_state')}")
            
            # Update sync status
            self.sync_status.update({
                "synchronized": True,
                "last_sync": datetime.now().isoformat(),
                "pending_commands": len(self.command_queue)
            })
            
        except Exception as e:
            logger.error(f"Error synchronizing state change: {e}")
            self.sync_status["errors"].append({
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            })
    
    def get_sync_status(self) -> Dict[str, Any]:
        """Get current synchronization status"""
        return {
            **self.sync_status,
            "state_machine_available": STATE_MACHINE_AVAILABLE and self.state_machine is not None,
            "broadcaster_available": STATE_BROADCASTER_AVAILABLE and self.broadcaster is not None,
            "current_state": self._get_current_state()
        }
    
    def get_contextual_commands(self, current_state: str = None, 
                              user_id: str = "default", 
                              project_name: str = "default") -> List[Dict[str, Any]]:
        """
        Get contextual command suggestions based on current state.
        
        Args:
            current_state: Current workflow state (if known)
            user_id: User identifier
            project_name: Project name
            
        Returns:
            List of suggested commands with context
        """
        if current_state is None:
            current_state = self._get_current_state()
        
        # State-specific command suggestions
        suggestions = {
            "IDLE": [
                {
                    "command": "/epic",
                    "description": "Create a new epic to start the workflow",
                    "usage": '/epic "Epic description"',
                    "priority": 10,
                    "category": "workflow"
                }
            ],
            "BACKLOG_READY": [
                {
                    "command": "/approve",
                    "description": "Approve proposed stories",
                    "usage": "/approve [story-ids]",
                    "priority": 9,
                    "category": "approval"
                },
                {
                    "command": "/sprint plan",
                    "description": "Plan a new sprint with selected stories",
                    "usage": "/sprint plan story-1,story-2",
                    "priority": 8,
                    "category": "planning"
                }
            ],
            "SPRINT_PLANNED": [
                {
                    "command": "/sprint start",
                    "description": "Start the planned sprint",
                    "usage": "/sprint start",
                    "priority": 10,
                    "category": "execution"
                }
            ],
            "SPRINT_ACTIVE": [
                {
                    "command": "/sprint status",
                    "description": "Check current sprint progress",
                    "usage": "/sprint status",
                    "priority": 9,
                    "category": "monitoring"
                },
                {
                    "command": "/sprint pause",
                    "description": "Pause the current sprint",
                    "usage": "/sprint pause",
                    "priority": 5,
                    "category": "control"
                }
            ]
        }
        
        # Add universal commands
        universal_commands = [
            {
                "command": "/help",
                "description": "Show available commands and help",
                "usage": "/help [command]",
                "priority": 7,
                "category": "help"
            },
            {
                "command": "/state",
                "description": "Show current workflow state",
                "usage": "/state",
                "priority": 6,
                "category": "information"
            }
        ]
        
        # Combine suggestions
        contextual_commands = suggestions.get(current_state, [])
        all_commands = contextual_commands + universal_commands
        
        # Sort by priority
        all_commands.sort(key=lambda x: x.get("priority", 0), reverse=True)
        
        return all_commands


# Global synchronizer instance
_synchronizer = None

def get_synchronizer() -> ChatStateSynchronizer:
    """Get global chat state synchronizer instance"""
    global _synchronizer
    if _synchronizer is None:
        _synchronizer = ChatStateSynchronizer()
    return _synchronizer

async def process_chat_command(command: str, user_id: str = "anonymous", 
                             project_name: str = "default") -> Dict[str, Any]:
    """
    Convenience function to process a chat command with synchronization.
    
    Args:
        command: The command string from chat
        user_id: User identifier
        project_name: Project context
        
    Returns:
        Dictionary containing command result with sync information
    """
    synchronizer = get_synchronizer()
    return await synchronizer.process_chat_command(command, user_id, project_name)

def get_contextual_commands(current_state: str = None, user_id: str = "default", 
                          project_name: str = "default") -> List[Dict[str, Any]]:
    """
    Get contextual command suggestions.
    
    Args:
        current_state: Current workflow state (if known)
        user_id: User identifier
        project_name: Project name
        
    Returns:
        List of suggested commands with context
    """
    synchronizer = get_synchronizer()
    return synchronizer.get_contextual_commands(current_state, user_id, project_name)


if __name__ == "__main__":
    # Test the synchronizer
    import asyncio
    
    async def test_synchronizer():
        synchronizer = ChatStateSynchronizer()
        
        print("Testing Chat State Synchronizer")
        print("=" * 50)
        
        # Test sync status
        status = synchronizer.get_sync_status()
        print(f"Sync Status: {status}")
        
        # Test contextual commands
        commands = synchronizer.get_contextual_commands("IDLE")
        print(f"Commands for IDLE state: {len(commands)}")
        for cmd in commands[:3]:
            print(f"  {cmd['command']}: {cmd['description']}")
        
        # Test command processing
        test_commands = ["/help", "/epic \"Test epic\"", "/unknown"]
        
        for command in test_commands:
            print(f"\nTesting command: {command}")
            result = await synchronizer.process_chat_command(command, "test_user")
            print(f"Success: {result.get('success')}")
            print(f"Message: {result.get('message', 'No message')}")
            if result.get('error'):
                print(f"Error: {result['error']}")
    
    asyncio.run(test_synchronizer())