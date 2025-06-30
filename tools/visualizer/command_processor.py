#!/usr/bin/env python3
"""
Command Processor for Discord-Style Chat Interface

Processes chat commands and integrates with the orchestrator system
to provide Discord bot functionality through the web interface.
"""

import logging
import re
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime

# Add lib and scripts directories to path for orchestrator imports
lib_path = Path(__file__).parent.parent.parent / "lib"
scripts_path = Path(__file__).parent.parent.parent / "scripts"
sys.path.insert(0, str(lib_path))
sys.path.insert(0, str(scripts_path))

logger = logging.getLogger(__name__)

# Try to import orchestrator and chat sync - graceful fallback if not available
try:
    from orchestrator import Orchestrator
    ORCHESTRATOR_AVAILABLE = True
except ImportError:
    logger.warning("Orchestrator not available - using mock responses")
    ORCHESTRATOR_AVAILABLE = False

try:
    from chat_state_sync import get_synchronizer, process_chat_command
    CHAT_SYNC_AVAILABLE = True
except ImportError:
    logger.warning("Chat synchronization not available - using basic processing")
    CHAT_SYNC_AVAILABLE = False

try:
    from collaboration_manager import get_collaboration_manager, UserPermission
    COLLABORATION_AVAILABLE = True
except ImportError:
    logger.warning("Collaboration features not available")
    COLLABORATION_AVAILABLE = False


class CommandProcessor:
    """
    Processes chat commands and integrates with the orchestrator system.
    
    Provides a bridge between the Discord-style chat interface and
    the underlying workflow orchestration system.
    """
    
    def __init__(self):
        self.orchestrator = None
        self.synchronizer = None
        self.command_patterns = self._initialize_command_patterns()
        self.help_text = self._generate_help_text()
        
        if ORCHESTRATOR_AVAILABLE:
            try:
                # Initialize orchestrator with default configuration
                self.orchestrator = Orchestrator()
                logger.info("Command processor initialized with orchestrator")
            except Exception as e:
                logger.error(f"Failed to initialize orchestrator: {e}")
                self.orchestrator = None
        
        if CHAT_SYNC_AVAILABLE:
            try:
                # Initialize chat synchronizer
                self.synchronizer = get_synchronizer()
                logger.info("Command processor initialized with chat synchronization")
            except Exception as e:
                logger.error(f"Failed to initialize chat synchronizer: {e}")
                self.synchronizer = None
        
        if COLLABORATION_AVAILABLE:
            try:
                # Initialize collaboration manager
                self.collaboration_manager = get_collaboration_manager()
                logger.info("Command processor initialized with collaboration features")
            except Exception as e:
                logger.error(f"Failed to initialize collaboration manager: {e}")
                self.collaboration_manager = None
        else:
            self.collaboration_manager = None
        
    def _initialize_command_patterns(self) -> Dict[str, Dict[str, Any]]:
        """Initialize command parsing patterns"""
        return {
            '/epic': {
                'pattern': r'^/epic\s+"?([^"]+)"?$',
                'handler': self._handle_epic_command,
                'description': 'Define a new high-level initiative',
                'usage': '/epic "description"',
                'examples': ['/epic "Implement user authentication system"']
            },
            '/approve': {
                'pattern': r'^/approve(?:\s+(.+))?$',
                'handler': self._handle_approve_command,
                'description': 'Approve proposed stories or tasks',
                'usage': '/approve [item_ids]',
                'examples': ['/approve', '/approve story-1,story-2']
            },
            '/sprint': {
                'pattern': r'^/sprint\s+(plan|start|status|pause|resume)(?:\s+(.+))?$',
                'handler': self._handle_sprint_command,
                'description': 'Sprint lifecycle management',
                'usage': '/sprint <action> [parameters]',
                'examples': [
                    '/sprint plan story-1,story-2',
                    '/sprint start',
                    '/sprint status',
                    '/sprint pause',
                    '/sprint resume'
                ]
            },
            '/backlog': {
                'pattern': r'^/backlog\s+(view|add_story|prioritize)(?:\s+(.+))?$',
                'handler': self._handle_backlog_command,
                'description': 'Manage product and sprint backlog',
                'usage': '/backlog <action> [parameters]',
                'examples': [
                    '/backlog view',
                    '/backlog add_story "New feature description"',
                    '/backlog prioritize story-1,story-2'
                ]
            },
            '/state': {
                'pattern': r'^/state$',
                'handler': self._handle_state_command,
                'description': 'Show current workflow state',
                'usage': '/state',
                'examples': ['/state']
            },
            '/project': {
                'pattern': r'^/project\s+(register)(?:\s+(.+))?$',
                'handler': self._handle_project_command,
                'description': 'Project management',
                'usage': '/project <action> [parameters]',
                'examples': ['/project register /path/to/project']
            },
            '/request_changes': {
                'pattern': r'^/request_changes\s+"?([^"]+)"?$',
                'handler': self._handle_request_changes_command,
                'description': 'Request changes to a PR',
                'usage': '/request_changes "description"',
                'examples': ['/request_changes "Please add unit tests"']
            },
            '/help': {
                'pattern': r'^/help(?:\s+(.+))?$',
                'handler': self._handle_help_command,
                'description': 'Show available commands and usage',
                'usage': '/help [command]',
                'examples': ['/help', '/help epic']
            }
        }
    
    def _generate_help_text(self) -> str:
        """Generate comprehensive help text"""
        help_lines = [
            "🤖 **Agent Workflow Commands**",
            "",
            "**Available Commands:**"
        ]
        
        for cmd, info in self.command_patterns.items():
            help_lines.append(f"• `{cmd}` - {info['description']}")
            help_lines.append(f"  Usage: `{info['usage']}`")
            if info.get('examples'):
                help_lines.append(f"  Examples: {', '.join(f'`{ex}`' for ex in info['examples'])}")
            help_lines.append("")
        
        help_lines.extend([
            "**Tips:**",
            "• Commands are case-sensitive and must start with `/`",
            "• Use quotes for multi-word descriptions",
            "• Type `/help <command>` for detailed help on a specific command",
            "",
            "**Project States:**",
            "• IDLE - No active work",
            "• BACKLOG_READY - Stories ready for sprint planning",
            "• SPRINT_PLANNED - Sprint planned but not started",
            "• SPRINT_ACTIVE - Sprint in progress",
            "• SPRINT_PAUSED - Sprint temporarily paused",
            "• SPRINT_REVIEW - Sprint completed, under review"
        ])
        
        return "\n".join(help_lines)
    
    def process_command(self, message: str, user_id: str = "anonymous") -> Dict[str, Any]:
        """
        Process a chat command and return the result.
        
        Args:
            message: The command message from the user
            user_id: Identifier for the user sending the command
            
        Returns:
            Dictionary containing command result with response and metadata
        """
        try:
            message = message.strip()
            
            if not message.startswith('/'):
                return {
                    "success": False,
                    "response": "❌ Commands must start with `/`. Type `/help` for available commands.",
                    "error": "Invalid command format"
                }
            
            # Find matching command pattern
            for command, config in self.command_patterns.items():
                pattern = config['pattern']
                match = re.match(pattern, message, re.IGNORECASE)
                
                if match:
                    logger.info(f"Processing command: {command} from user: {user_id}")
                    
                    # Call the appropriate handler
                    handler = config['handler']
                    try:
                        result = handler(match, user_id)
                        result['command'] = command
                        result['user_id'] = user_id
                        result['timestamp'] = datetime.now().isoformat()
                        return result
                    except Exception as e:
                        logger.error(f"Error in command handler for {command}: {e}")
                        return {
                            "success": False,
                            "response": f"❌ Error processing command: {str(e)}",
                            "error": str(e),
                            "command": command
                        }
            
            # No matching command found
            return {
                "success": False,
                "response": f"❌ Unknown command: `{message.split()[0]}`. Type `/help` for available commands.",
                "error": "Unknown command",
                "suggestions": self._get_command_suggestions(message)
            }
            
        except Exception as e:
            logger.error(f"Error processing command: {e}")
            return {
                "success": False,
                "response": f"❌ Unexpected error: {str(e)}",
                "error": str(e)
            }
    
    def _get_command_suggestions(self, message: str) -> List[str]:
        """Get command suggestions based on partial input"""
        command_part = message.split()[0].lower()
        suggestions = []
        
        for cmd in self.command_patterns.keys():
            if cmd.lower().startswith(command_part.lower()):
                suggestions.append(cmd)
        
        return suggestions[:5]  # Return top 5 suggestions
    
    async def process_command_with_sync(self, message: str, user_id: str = "anonymous", project_name: str = "default") -> Dict[str, Any]:
        """
        Process a chat command with full synchronization support.
        
        Args:
            message: The command message from the user
            user_id: Identifier for the user sending the command
            project_name: Project name for context
            
        Returns:
            Dictionary containing command result with sync information
        """
        try:
            message = message.strip()
            
            if not message.startswith('/'):
                return {
                    "success": False,
                    "response": "❌ Commands must start with `/`. Type `/help` for available commands.",
                    "error": "Invalid command format",
                    "sync_available": CHAT_SYNC_AVAILABLE
                }
            
            # Use chat synchronization if available
            if self.synchronizer and CHAT_SYNC_AVAILABLE:
                try:
                    sync_result = await process_chat_command(message, user_id, project_name)
                    
                    if sync_result["success"]:
                        return {
                            "success": True,
                            "response": f"✅ Command executed successfully",
                            "command_id": sync_result["command_id"],
                            "sync_data": sync_result,
                            "new_state": sync_result.get("new_state"),
                            "synchronized": True
                        }
                    else:
                        return {
                            "success": False,
                            "response": f"❌ {sync_result.get('error', 'Unknown error')}",
                            "error": sync_result.get("error"),
                            "hint": sync_result.get("hint"),
                            "current_state": sync_result.get("current_state"),
                            "synchronized": True
                        }
                        
                except Exception as e:
                    logger.error(f"Error in synchronized command processing: {e}")
                    # Fall back to regular processing
                    return await self._fallback_to_regular_processing(message, user_id)
            
            # Fall back to regular processing if sync not available
            return await self._fallback_to_regular_processing(message, user_id)
            
        except Exception as e:
            logger.error(f"Error processing command with sync: {e}")
            return {
                "success": False,
                "response": f"❌ Unexpected error: {str(e)}",
                "error": str(e),
                "synchronized": False
            }
    
    async def _fallback_to_regular_processing(self, message: str, user_id: str) -> Dict[str, Any]:
        """Fallback to regular command processing when sync is not available"""
        result = self.process_command(message, user_id)
        result["synchronized"] = False
        result["fallback"] = True
        return result
    
    def get_contextual_suggestions(self, current_state: str = None, user_id: str = "default", project_name: str = "default") -> List[Dict[str, Any]]:
        """
        Get contextual command suggestions based on current workflow state.
        
        Args:
            current_state: Current workflow state (if known)
            user_id: User identifier
            project_name: Project name
            
        Returns:
            List of command suggestions with context
        """
        if self.synchronizer and CHAT_SYNC_AVAILABLE:
            try:
                # Get state from synchronizer if not provided
                if current_state is None:
                    sync_status = self.synchronizer.get_sync_status()
                    current_state = sync_status.get("current_state", "IDLE")
                
                # Get contextual commands from broadcaster
                from state_broadcaster import get_contextual_commands
                return get_contextual_commands(current_state, user_id, project_name)
                
            except Exception as e:
                logger.error(f"Error getting contextual suggestions: {e}")
        
        # Fallback to basic suggestions
        return self._get_basic_command_suggestions()
    
    def _get_basic_command_suggestions(self) -> List[Dict[str, Any]]:
        """Get basic command suggestions when sync is not available"""
        basic_commands = [
            {
                "command": "/help",
                "description": "Show available commands and usage",
                "usage": "/help [command]",
                "available": True,
                "priority": 8
            },
            {
                "command": "/state",
                "description": "Show current workflow state",
                "usage": "/state",
                "available": True,
                "priority": 7
            },
            {
                "command": "/epic",
                "description": "Define a new high-level initiative",
                "usage": '/epic "description"',
                "available": True,
                "priority": 6
            },
            {
                "command": "/approve",
                "description": "Approve proposed stories or tasks",
                "usage": "/approve [item_ids]",
                "available": True,
                "priority": 5
            }
        ]
        
        return basic_commands
    
    def get_sync_status(self) -> Dict[str, Any]:
        """Get synchronization system status"""
        status = {
            "chat_sync_available": CHAT_SYNC_AVAILABLE,
            "orchestrator_available": ORCHESTRATOR_AVAILABLE,
            "synchronizer_initialized": self.synchronizer is not None,
            "orchestrator_initialized": self.orchestrator is not None
        }
        
        if self.synchronizer:
            try:
                status.update(self.synchronizer.get_sync_status())
            except Exception as e:
                status["sync_status_error"] = str(e)
        
        return status
    
    async def process_collaborative_command(self, message: str, user_id: str = "anonymous", 
                                          project_name: str = "default", session_id: str = None,
                                          permission_level: str = "contributor") -> Dict[str, Any]:
        """
        Process a command with full collaboration support.
        
        Args:
            message: The command message from the user
            user_id: User identifier
            project_name: Project name
            session_id: User's collaboration session ID
            permission_level: User's permission level
            
        Returns:
            Dictionary containing command result with collaboration metadata
        """
        try:
            # Validate collaboration session if available
            if self.collaboration_manager and COLLABORATION_AVAILABLE:
                if session_id is None:
                    # Try to join a new session
                    try:
                        perm_enum = UserPermission.CONTRIBUTOR
                        if permission_level == "admin":
                            perm_enum = UserPermission.ADMIN
                        elif permission_level == "maintainer":
                            perm_enum = UserPermission.MAINTAINER
                        elif permission_level == "viewer":
                            perm_enum = UserPermission.VIEWER
                        
                        session_id = await self.collaboration_manager.join_session(
                            user_id, project_name, perm_enum
                        )
                    except Exception as e:
                        logger.error(f"Failed to join collaboration session: {e}")
                        session_id = None
                
                if session_id:
                    # Execute with collaboration awareness
                    try:
                        result = await self.collaboration_manager.execute_collaborative_command(
                            user_id=user_id,
                            command=message,
                            project_name=project_name,
                            session_id=session_id,
                            command_processor=self._async_command_wrapper
                        )
                        
                        result["collaboration_enabled"] = True
                        result["session_id"] = session_id
                        return result
                        
                    except Exception as e:
                        logger.error(f"Error in collaborative command execution: {e}")
                        # Fall through to regular processing
            
            # Fall back to synchronized processing if collaboration fails
            if self.synchronizer and CHAT_SYNC_AVAILABLE:
                result = await self.process_command_with_sync(message, user_id, project_name)
                result["collaboration_enabled"] = False
                result["fallback_reason"] = "Collaboration not available"
                return result
            
            # Final fallback to basic processing
            result = self.process_command(message, user_id)
            result["collaboration_enabled"] = False
            result["synchronized"] = False
            result["fallback_reason"] = "Advanced features not available"
            return result
            
        except Exception as e:
            logger.error(f"Error processing collaborative command: {e}")
            return {
                "success": False,
                "response": f"❌ Error processing command: {str(e)}",
                "error": str(e),
                "collaboration_enabled": False
            }
    
    async def _async_command_wrapper(self, command: str, user_id: str, project_name: str) -> Dict[str, Any]:
        """Async wrapper for command processing in collaboration context"""
        try:
            if self.synchronizer and CHAT_SYNC_AVAILABLE:
                return await self.process_command_with_sync(command, user_id, project_name)
            else:
                return self.process_command(command, user_id)
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "response": f"❌ Command execution failed: {str(e)}"
            }
    
    async def join_collaboration_session(self, user_id: str, project_name: str, 
                                       permission_level: str = "contributor") -> Optional[str]:
        """Join a collaboration session"""
        if not self.collaboration_manager or not COLLABORATION_AVAILABLE:
            return None
        
        try:
            # Convert permission level string to enum
            perm_enum = UserPermission.CONTRIBUTOR
            if permission_level == "admin":
                perm_enum = UserPermission.ADMIN
            elif permission_level == "maintainer":
                perm_enum = UserPermission.MAINTAINER
            elif permission_level == "viewer":
                perm_enum = UserPermission.VIEWER
            
            session_id = await self.collaboration_manager.join_session(
                user_id, project_name, perm_enum
            )
            
            return session_id
            
        except Exception as e:
            logger.error(f"Failed to join collaboration session: {e}")
            return None
    
    async def leave_collaboration_session(self, session_id: str) -> bool:
        """Leave a collaboration session"""
        if not self.collaboration_manager or not COLLABORATION_AVAILABLE:
            return False
        
        try:
            await self.collaboration_manager.leave_session(session_id)
            return True
        except Exception as e:
            logger.error(f"Failed to leave collaboration session: {e}")
            return False
    
    async def get_collaboration_status(self, project_name: str) -> Dict[str, Any]:
        """Get collaboration status for a project"""
        if not self.collaboration_manager or not COLLABORATION_AVAILABLE:
            return {
                "collaboration_enabled": False,
                "reason": "Collaboration features not available"
            }
        
        try:
            active_users = await self.collaboration_manager.get_active_users(project_name)
            resource_locks = await self.collaboration_manager.get_resource_locks(project_name)
            stats = self.collaboration_manager.get_collaboration_stats(project_name)
            
            return {
                "collaboration_enabled": True,
                "active_users": active_users,
                "resource_locks": resource_locks,
                "stats": stats,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting collaboration status: {e}")
            return {
                "collaboration_enabled": False,
                "error": str(e)
            }
    
    def get_advanced_status(self) -> Dict[str, Any]:
        """Get comprehensive status of all advanced features"""
        status = self.get_sync_status()
        
        status.update({
            "collaboration_available": COLLABORATION_AVAILABLE,
            "collaboration_manager_initialized": self.collaboration_manager is not None,
            "features": {
                "basic_processing": True,
                "chat_synchronization": CHAT_SYNC_AVAILABLE and self.synchronizer is not None,
                "collaboration": COLLABORATION_AVAILABLE and self.collaboration_manager is not None,
                "orchestrator_integration": ORCHESTRATOR_AVAILABLE and self.orchestrator is not None
            }
        })
        
        return status
    
    # =====================================================
    # Command Handlers
    # =====================================================
    
    def _handle_epic_command(self, match: re.Match, user_id: str) -> Dict[str, Any]:
        """Handle /epic command"""
        description = match.group(1).strip() if match.group(1) else ""
        
        if not description:
            return {
                "success": False,
                "response": "❌ Epic description is required. Usage: `/epic \"description\"`",
                "error": "Missing description"
            }
        
        if self.orchestrator:
            try:
                # Call orchestrator handle_command method
                result = self.orchestrator.handle_command("/epic", "default", description=description)
                
                if result.get("success"):
                    response_lines = [
                        f"✅ **Epic Created**: {description}",
                        ""
                    ]
                    
                    if result.get("stories"):
                        response_lines.append("**Proposed Stories:**")
                        for story in result["stories"]:
                            response_lines.append(f"• {story}")
                        response_lines.append("")
                    
                    if result.get("next_step"):
                        response_lines.append(f"**Next Step:** {result['next_step']}")
                    
                    return {
                        "success": True,
                        "response": "\n".join(response_lines),
                        "epic_data": result
                    }
                else:
                    return {
                        "success": False,
                        "response": f"❌ {result.get('error', 'Failed to create epic')}",
                        "error": result.get('error')
                    }
            except Exception as e:
                logger.error(f"Error calling orchestrator for epic: {e}")
                return {
                    "success": False,
                    "response": f"❌ Error creating epic: {str(e)}",
                    "error": str(e)
                }
        else:
            # Mock response when orchestrator is not available
            return {
                "success": True,
                "response": f"✅ **Epic Created** (Mock): {description}\n\n**Note:** Orchestrator not available - this is a simulated response.",
                "mock": True
            }
    
    def _handle_approve_command(self, match: re.Match, user_id: str) -> Dict[str, Any]:
        """Handle /approve command"""
        items_str = match.group(1) if match.group(1) else ""
        item_ids = [item.strip() for item in items_str.split(",") if item.strip()] if items_str else []
        
        if self.orchestrator:
            try:
                result = self.orchestrator.handle_command("/approve", "default", item_ids=item_ids)
                
                if result.get("success"):
                    approved_count = len(result.get("approved_items", []))
                    response_lines = [
                        f"✅ **Approved {approved_count} items**",
                        ""
                    ]
                    
                    if result.get("approved_items"):
                        response_lines.append("**Approved Items:**")
                        for item in result["approved_items"]:
                            response_lines.append(f"• {item}")
                        response_lines.append("")
                    
                    if result.get("next_step"):
                        response_lines.append(f"**Next Step:** {result['next_step']}")
                    
                    return {
                        "success": True,
                        "response": "\n".join(response_lines),
                        "approval_data": result
                    }
                else:
                    return {
                        "success": False,
                        "response": f"❌ {result.get('error', 'Failed to approve items')}",
                        "error": result.get('error')
                    }
            except Exception as e:
                return {
                    "success": False,
                    "response": f"❌ Error processing approval: {str(e)}",
                    "error": str(e)
                }
        else:
            return {
                "success": True,
                "response": f"✅ **Approved** (Mock): {len(item_ids)} items\n\n**Note:** Orchestrator not available.",
                "mock": True
            }
    
    def _handle_sprint_command(self, match: re.Match, user_id: str) -> Dict[str, Any]:
        """Handle /sprint command"""
        action = match.group(1).lower()
        params = match.group(2) if match.group(2) else ""
        
        if self.orchestrator:
            try:
                command = f"/sprint {action}"
                kwargs = {}
                
                if params and action == "plan":
                    kwargs["story_ids"] = [item.strip() for item in params.split(",") if item.strip()]
                
                result = self.orchestrator.handle_command(command, "default", **kwargs)
                
                if result.get("success"):
                    if action == "status":
                        response_lines = [
                            "📊 **Sprint Status**",
                            "",
                            f"• Total Tasks: {result.get('total_tasks', 0)}",
                            f"• Completed: {result.get('completed_tasks', 0)}",
                            f"• Failed: {result.get('failed_tasks', 0)}",
                            f"• Current State: {result.get('current_state', 'Unknown')}",
                            f"• Pending Approvals: {result.get('pending_approvals', 0)}"
                        ]
                    else:
                        response_lines = [
                            f"🏃 **Sprint {action.title()}**",
                            "",
                            result.get("message", "")
                        ]
                        
                        if result.get("next_step"):
                            response_lines.extend(["", f"**Next Step:** {result['next_step']}"])
                    
                    return {
                        "success": True,
                        "response": "\n".join(response_lines),
                        "sprint_data": result
                    }
                else:
                    error_msg = result.get("error", "Unknown error")
                    hint = result.get("hint", "")
                    current_state = result.get("current_state", "")
                    
                    response_lines = [f"❌ **Command Failed**: {error_msg}"]
                    if hint:
                        response_lines.extend(["", f"**Suggestion:** {hint}"])
                    if current_state:
                        response_lines.extend(["", f"**Current State:** {current_state}"])
                    
                    return {
                        "success": False,
                        "response": "\n".join(response_lines),
                        "error": error_msg
                    }
            except Exception as e:
                return {
                    "success": False,
                    "response": f"❌ Error processing sprint command: {str(e)}",
                    "error": str(e)
                }
        else:
            return {
                "success": True,
                "response": f"🏃 **Sprint {action.title()}** (Mock)\n\n**Note:** Orchestrator not available.",
                "mock": True
            }
    
    def _handle_backlog_command(self, match: re.Match, user_id: str) -> Dict[str, Any]:
        """Handle /backlog command"""
        action = match.group(1).lower()
        params = match.group(2) if match.group(2) else ""
        
        if self.orchestrator:
            try:
                command = f"/backlog {action}"
                kwargs = {}
                
                if params:
                    if action == "add_story":
                        kwargs["description"] = params.strip('"')
                    elif action == "prioritize":
                        kwargs["story_ids"] = [item.strip() for item in params.split(",") if item.strip()]
                
                result = self.orchestrator.handle_command(command, "default", **kwargs)
                
                if result.get("success"):
                    return {
                        "success": True,
                        "response": f"📋 **Backlog {action.title()}** completed successfully",
                        "backlog_data": result
                    }
                else:
                    return {
                        "success": False,
                        "response": f"❌ {result.get('error', 'Failed to process backlog command')}",
                        "error": result.get('error')
                    }
            except Exception as e:
                return {
                    "success": False,
                    "response": f"❌ Error processing backlog command: {str(e)}",
                    "error": str(e)
                }
        else:
            return {
                "success": True,
                "response": f"📋 **Backlog {action.title()}** (Mock)\n\n**Note:** Orchestrator not available.",
                "mock": True
            }
    
    def _handle_state_command(self, match: re.Match, user_id: str) -> Dict[str, Any]:
        """Handle /state command"""
        if self.orchestrator:
            try:
                result = self.orchestrator.handle_command("/state", "default")
                
                if result.get("success"):
                    state_info = result.get("state_info", {})
                    
                    response_lines = [
                        "🔄 **Current Workflow State**",
                        "",
                        f"**State:** {state_info.get('current_state', 'Unknown')}",
                        f"**Description:** {state_info.get('description', 'No description')}",
                        ""
                    ]
                    
                    if state_info.get("allowed_commands"):
                        response_lines.append("**Allowed Commands:**")
                        for cmd in state_info["allowed_commands"]:
                            response_lines.append(f"• `{cmd}`")
                        response_lines.append("")
                    
                    if result.get("mermaid_diagram"):
                        response_lines.extend([
                            "**State Diagram:**",
                            f"```mermaid\n{result['mermaid_diagram']}\n```"
                        ])
                    
                    return {
                        "success": True,
                        "response": "\n".join(response_lines),
                        "state_data": result
                    }
                else:
                    return {
                        "success": False,
                        "response": f"❌ {result.get('error', 'Failed to get state')}",
                        "error": result.get('error')
                    }
            except Exception as e:
                return {
                    "success": False,
                    "response": f"❌ Error getting state: {str(e)}",
                    "error": str(e)
                }
        else:
            return {
                "success": True,
                "response": "🔄 **Current Workflow State** (Mock)\n\n**State:** IDLE\n\n**Note:** Orchestrator not available.",
                "mock": True
            }
    
    def _handle_project_command(self, match: re.Match, user_id: str) -> Dict[str, Any]:
        """Handle /project command"""
        action = match.group(1).lower()
        params = match.group(2) if match.group(2) else ""
        
        if action == "register":
            if not params:
                return {
                    "success": False,
                    "response": "❌ Project path is required. Usage: `/project register /path/to/project`",
                    "error": "Missing project path"
                }
            
            if self.orchestrator:
                try:
                    result = self.orchestrator.handle_command("/project register", "default", path=params.strip())
                    
                    if result.get("success"):
                        return {
                            "success": True,
                            "response": f"✅ **Project Registered**: {params.strip()}",
                            "project_data": result
                        }
                    else:
                        return {
                            "success": False,
                            "response": f"❌ {result.get('error', 'Failed to register project')}",
                            "error": result.get('error')
                        }
                except Exception as e:
                    return {
                        "success": False,
                        "response": f"❌ Error registering project: {str(e)}",
                        "error": str(e)
                    }
            else:
                return {
                    "success": True,
                    "response": f"✅ **Project Registered** (Mock): {params.strip()}\n\n**Note:** Orchestrator not available.",
                    "mock": True
                }
        
        return {
            "success": False,
            "response": f"❌ Unknown project action: {action}",
            "error": "Unknown action"
        }
    
    def _handle_request_changes_command(self, match: re.Match, user_id: str) -> Dict[str, Any]:
        """Handle /request_changes command"""
        description = match.group(1).strip() if match.group(1) else ""
        
        if not description:
            return {
                "success": False,
                "response": "❌ Change description is required. Usage: `/request_changes \"description\"`",
                "error": "Missing description"
            }
        
        if self.orchestrator:
            try:
                result = self.orchestrator.handle_command("/request_changes", "default", description=description)
                
                if result.get("success"):
                    return {
                        "success": True,
                        "response": f"📝 **Changes Requested**: {description}",
                        "changes_data": result
                    }
                else:
                    return {
                        "success": False,
                        "response": f"❌ {result.get('error', 'Failed to request changes')}",
                        "error": result.get('error')
                    }
            except Exception as e:
                return {
                    "success": False,
                    "response": f"❌ Error requesting changes: {str(e)}",
                    "error": str(e)
                }
        else:
            return {
                "success": True,
                "response": f"📝 **Changes Requested** (Mock): {description}\n\n**Note:** Orchestrator not available.",
                "mock": True
            }
    
    def _handle_help_command(self, match: re.Match, user_id: str) -> Dict[str, Any]:
        """Handle /help command"""
        command = match.group(1).strip() if match.group(1) else ""
        
        if command:
            # Help for specific command
            if command.startswith('/'):
                command = command
            else:
                command = f"/{command}"
            
            if command in self.command_patterns:
                info = self.command_patterns[command]
                response_lines = [
                    f"ℹ️ **Help: {command}**",
                    "",
                    f"**Description:** {info['description']}",
                    f"**Usage:** `{info['usage']}`",
                    ""
                ]
                
                if info.get('examples'):
                    response_lines.append("**Examples:**")
                    for example in info['examples']:
                        response_lines.append(f"• `{example}`")
                
                return {
                    "success": True,
                    "response": "\n".join(response_lines)
                }
            else:
                return {
                    "success": False,
                    "response": f"❌ Unknown command: `{command}`. Type `/help` for all commands.",
                    "error": "Unknown command"
                }
        else:
            # General help
            return {
                "success": True,
                "response": self.help_text
            }


# Global instance for easy import
_processor = None

def get_processor() -> CommandProcessor:
    """Get global command processor instance"""
    global _processor
    if _processor is None:
        _processor = CommandProcessor()
    return _processor

def process_command(message: str, user_id: str = "anonymous") -> Dict[str, Any]:
    """
    Convenience function to process a command.
    
    Args:
        message: The command message from the user
        user_id: Identifier for the user sending the command
        
    Returns:
        Dictionary containing command result
    """
    processor = get_processor()
    return processor.process_command(message, user_id)


if __name__ == "__main__":
    # Test the command processor
    processor = CommandProcessor()
    
    test_commands = [
        "/help",
        "/epic \"Test epic description\"",
        "/sprint status",
        "/state",
        "/unknown_command"
    ]
    
    print("Testing Command Processor")
    print("=" * 50)
    
    for cmd in test_commands:
        print(f"\nCommand: {cmd}")
        result = processor.process_command(cmd, "test_user")
        print(f"Success: {result['success']}")
        print(f"Response: {result['response']}")
        if result.get('error'):
            print(f"Error: {result['error']}")
        print("-" * 30)

# =====================================================
# Module Interface Functions  
# =====================================================

# Global processor instance
_processor_instance = None

def get_processor():
    """Get or create the global command processor instance"""
    global _processor_instance
    if _processor_instance is None:
        _processor_instance = CommandProcessor()
    return _processor_instance

def process_command(message: str, user_id: str = "anonymous") -> Dict[str, Any]:
    """Process a command using the global processor instance"""
    processor = get_processor()
    return processor.process_command(message, user_id)

async def process_collaborative_command(message: str, user_id: str = "anonymous", 
                                      project_name: str = "default", session_id: str = None,
                                      permission_level: str = "contributor") -> Dict[str, Any]:
    """Process a command with collaboration support using the global processor instance"""
    processor = get_processor()
    return await processor.process_collaborative_command(
        message, user_id, project_name, session_id, permission_level
    )
