#!/usr/bin/env python3
"""
Collaboration Management System

Provides real-time collaboration features for multi-user workflow management,
including command execution tracking, conflict resolution, and user presence.
"""

import logging
import asyncio
from typing import Dict, List, Optional, Any, Set, Callable
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from uuid import uuid4
from enum import Enum

# Import state system components
try:
    from .state_broadcaster import (
        broadcaster, 
        broadcast_user_presence, 
        broadcast_command_execution,
        broadcast_error_state,
        broadcast_chat_message
    )
except ImportError:
    # Fallback for standalone usage
    from state_broadcaster import (
        broadcaster, 
        broadcast_user_presence, 
        broadcast_command_execution,
        broadcast_error_state,
        broadcast_chat_message
    )

logger = logging.getLogger(__name__)


class ConflictResolution(Enum):
    """Conflict resolution strategies"""
    FIRST_WINS = "first_wins"
    LAST_WINS = "last_wins"
    MERGE = "merge"
    MANUAL = "manual"
    ABORT = "abort"


class UserPermission(Enum):
    """User permission levels"""
    VIEWER = "viewer"
    CONTRIBUTOR = "contributor"
    MAINTAINER = "maintainer"
    ADMIN = "admin"


@dataclass
class UserSession:
    """Represents an active user session"""
    user_id: str
    session_id: str
    join_time: datetime
    last_activity: datetime
    project_name: str
    permission_level: UserPermission
    current_command: Optional[str] = None
    status: str = "active"  # "active", "idle", "typing", "away"
    client_info: Dict[str, Any] = None


@dataclass
class CommandLock:
    """Represents a command execution lock"""
    lock_id: str
    user_id: str
    command: str
    resource: str  # Resource being locked (e.g., "sprint", "backlog", "epic:123")
    lock_time: datetime
    expires_at: datetime
    project_name: str


@dataclass
class CollaborationConflict:
    """Represents a collaboration conflict"""
    conflict_id: str
    conflict_type: str  # "concurrent_command", "resource_lock", "state_change"
    users_involved: List[str]
    commands_involved: List[str]
    resource: str
    detected_at: datetime
    resolution_strategy: ConflictResolution
    resolved: bool = False
    resolution_data: Optional[Dict[str, Any]] = None


class CollaborationManager:
    """
    Manages real-time collaboration features for multi-user workflow management.
    
    Features:
    - User session tracking and presence
    - Command execution locking and coordination
    - Conflict detection and resolution
    - Shared state synchronization
    - Permission-based access control
    """
    
    def __init__(self):
        self.active_sessions: Dict[str, UserSession] = {}
        self.command_locks: Dict[str, CommandLock] = {}
        self.conflicts: Dict[str, CollaborationConflict] = {}
        self.conflict_handlers: Dict[str, Callable] = {}
        self.session_listeners: List[Callable] = []
        self.default_permissions: Dict[str, UserPermission] = {}
        
        # Resource lock timeouts (in seconds)
        self.lock_timeouts = {
            "sprint": 300,  # 5 minutes
            "epic": 180,    # 3 minutes
            "backlog": 120, # 2 minutes
            "project": 600, # 10 minutes
            "default": 180  # 3 minutes
        }
        
        # Initialize conflict resolution handlers
        self._initialize_conflict_handlers()
        
        # Start cleanup task
        self._cleanup_task = asyncio.create_task(self._periodic_cleanup())
        
        logger.info("Collaboration manager initialized")
    
    def _initialize_conflict_handlers(self):
        """Initialize conflict resolution handlers"""
        self.conflict_handlers = {
            "concurrent_command": self._handle_concurrent_command_conflict,
            "resource_lock": self._handle_resource_lock_conflict,
            "state_change": self._handle_state_change_conflict
        }
    
    async def join_session(self, user_id: str, project_name: str, 
                          permission_level: UserPermission = UserPermission.CONTRIBUTOR,
                          client_info: Dict[str, Any] = None) -> str:
        """
        Join a collaboration session.
        
        Args:
            user_id: User identifier
            project_name: Project name
            permission_level: User's permission level
            client_info: Optional client information
            
        Returns:
            Session ID
        """
        session_id = str(uuid4())
        now = datetime.now()
        
        # Create user session
        session = UserSession(
            user_id=user_id,
            session_id=session_id,
            join_time=now,
            last_activity=now,
            project_name=project_name,
            permission_level=permission_level,
            client_info=client_info or {}
        )
        
        self.active_sessions[session_id] = session
        
        # Broadcast user joined
        broadcast_user_presence(user_id, "joined", project_name)
        
        # Notify session listeners
        for listener in self.session_listeners:
            try:
                await listener("user_joined", session)
            except Exception as e:
                logger.error(f"Error in session listener: {e}")
        
        logger.info(f"User {user_id} joined session {session_id} for project {project_name}")
        
        return session_id
    
    async def leave_session(self, session_id: str):
        """Leave a collaboration session"""
        if session_id not in self.active_sessions:
            return
        
        session = self.active_sessions[session_id]
        
        # Release any command locks held by this user
        await self._release_user_locks(session.user_id, session.project_name)
        
        # Remove session
        del self.active_sessions[session_id]
        
        # Broadcast user left
        broadcast_user_presence(session.user_id, "left", session.project_name)
        
        # Notify session listeners
        for listener in self.session_listeners:
            try:
                await listener("user_left", session)
            except Exception as e:
                logger.error(f"Error in session listener: {e}")
        
        logger.info(f"User {session.user_id} left session {session_id}")
    
    async def update_user_activity(self, session_id: str, activity: str = "active"):
        """Update user activity status"""
        if session_id not in self.active_sessions:
            return
        
        session = self.active_sessions[session_id]
        session.last_activity = datetime.now()
        session.status = activity
        
        # Broadcast activity update
        broadcast_user_presence(session.user_id, activity, session.project_name)
    
    async def acquire_command_lock(self, user_id: str, command: str, resource: str, 
                                 project_name: str, timeout: Optional[int] = None) -> Optional[str]:
        """
        Acquire a lock for command execution.
        
        Args:
            user_id: User requesting the lock
            command: Command being executed
            resource: Resource being locked
            project_name: Project context
            timeout: Lock timeout in seconds
            
        Returns:
            Lock ID if acquired, None if failed
        """
        # Check if resource is already locked
        existing_lock = self._find_resource_lock(resource, project_name)
        if existing_lock and not self._is_lock_expired(existing_lock):
            # Resource is locked by another user
            if existing_lock.user_id != user_id:
                await self._handle_lock_conflict(user_id, command, existing_lock)
                return None
        
        # Determine timeout
        if timeout is None:
            resource_type = resource.split(':')[0] if ':' in resource else resource
            timeout = self.lock_timeouts.get(resource_type, self.lock_timeouts["default"])
        
        # Create lock
        lock_id = str(uuid4())
        now = datetime.now()
        expires_at = now + timedelta(seconds=timeout)
        
        lock = CommandLock(
            lock_id=lock_id,
            user_id=user_id,
            command=command,
            resource=resource,
            lock_time=now,
            expires_at=expires_at,
            project_name=project_name
        )
        
        self.command_locks[lock_id] = lock
        
        # Broadcast lock acquisition
        broadcast_command_execution(
            command=f"LOCK:{command}",
            user_id=user_id,
            status="started",
            command_id=lock_id,
            project_name=project_name
        )
        
        logger.info(f"User {user_id} acquired lock {lock_id} for resource {resource}")
        
        return lock_id
    
    async def release_command_lock(self, lock_id: str):
        """Release a command lock"""
        if lock_id not in self.command_locks:
            return
        
        lock = self.command_locks[lock_id]
        del self.command_locks[lock_id]
        
        # Broadcast lock release
        broadcast_command_execution(
            command=f"UNLOCK:{lock.command}",
            user_id=lock.user_id,
            status="completed",
            command_id=lock_id,
            project_name=lock.project_name
        )
        
        logger.info(f"Released lock {lock_id} for resource {lock.resource}")
    
    async def execute_collaborative_command(self, user_id: str, command: str, 
                                          project_name: str, session_id: str,
                                          command_processor: Callable = None) -> Dict[str, Any]:
        """
        Execute a command with collaboration awareness.
        
        Args:
            user_id: User executing the command
            command: Command to execute
            project_name: Project context
            session_id: User's session ID
            command_processor: Function to process the command
            
        Returns:
            Command execution result with collaboration metadata
        """
        # Validate session
        if session_id not in self.active_sessions:
            return {
                "success": False,
                "error": "Invalid session",
                "collaboration_error": True
            }
        
        session = self.active_sessions[session_id]
        
        # Check permissions
        if not self._check_command_permission(session, command):
            return {
                "success": False,
                "error": "Insufficient permissions",
                "collaboration_error": True,
                "required_permission": self._get_required_permission(command)
            }
        
        # Determine resource being affected
        resource = self._determine_command_resource(command)
        
        # Try to acquire lock if needed
        lock_id = None
        if self._command_requires_lock(command):
            lock_id = await self.acquire_command_lock(user_id, command, resource, project_name)
            if lock_id is None:
                return {
                    "success": False,
                    "error": "Resource is locked by another user",
                    "collaboration_error": True,
                    "resource": resource
                }
        
        try:
            # Update user activity
            await self.update_user_activity(session_id, "executing")
            
            # Check for conflicts with other users
            conflict = await self._detect_command_conflicts(user_id, command, project_name)
            if conflict:
                result = await self._resolve_conflict(conflict)
                if not result["proceed"]:
                    return {
                        "success": False,
                        "error": "Command conflicts with other users",
                        "collaboration_error": True,
                        "conflict": conflict
                    }
            
            # Execute the command
            if command_processor:
                result = await command_processor(command, user_id, project_name)
            else:
                result = {"success": True, "message": "Command executed"}
            
            # Add collaboration metadata
            result["collaboration"] = {
                "user_id": user_id,
                "session_id": session_id,
                "lock_id": lock_id,
                "resource": resource,
                "timestamp": datetime.now().isoformat()
            }
            
            # Broadcast successful execution
            broadcast_command_execution(
                command=command,
                user_id=user_id,
                status="completed",
                result=result,
                project_name=project_name
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Error executing collaborative command: {e}")
            
            # Broadcast execution failure
            broadcast_error_state(
                error_type="collaboration_error",
                error_message=str(e),
                context={"command": command, "user_id": user_id},
                project_name=project_name
            )
            
            return {
                "success": False,
                "error": str(e),
                "collaboration_error": True
            }
            
        finally:
            # Release lock if acquired
            if lock_id:
                await self.release_command_lock(lock_id)
            
            # Update user activity back to active
            await self.update_user_activity(session_id, "active")
    
    async def get_active_users(self, project_name: str) -> List[Dict[str, Any]]:
        """Get list of active users in a project"""
        users = []
        
        for session in self.active_sessions.values():
            if session.project_name == project_name:
                users.append({
                    "user_id": session.user_id,
                    "session_id": session.session_id,
                    "status": session.status,
                    "permission_level": session.permission_level.value,
                    "current_command": session.current_command,
                    "join_time": session.join_time.isoformat(),
                    "last_activity": session.last_activity.isoformat()
                })
        
        return users
    
    async def get_resource_locks(self, project_name: str) -> List[Dict[str, Any]]:
        """Get list of active resource locks for a project"""
        locks = []
        
        for lock in self.command_locks.values():
            if lock.project_name == project_name and not self._is_lock_expired(lock):
                locks.append({
                    "lock_id": lock.lock_id,
                    "user_id": lock.user_id,
                    "command": lock.command,
                    "resource": lock.resource,
                    "lock_time": lock.lock_time.isoformat(),
                    "expires_at": lock.expires_at.isoformat()
                })
        
        return locks
    
    async def force_release_lock(self, lock_id: str, admin_user_id: str) -> bool:
        """Force release a lock (admin only)"""
        if lock_id not in self.command_locks:
            return False
        
        lock = self.command_locks[lock_id]
        
        # Broadcast forced release
        broadcast_chat_message(
            user_id="system",
            message=f"🔓 Lock forcibly released by admin {admin_user_id}",
            message_type="system",
            project_name=lock.project_name
        )
        
        await self.release_command_lock(lock_id)
        return True
    
    # =====================================================
    # Conflict Detection and Resolution
    # =====================================================
    
    async def _detect_command_conflicts(self, user_id: str, command: str, project_name: str) -> Optional[CollaborationConflict]:
        """Detect potential conflicts with other users' commands"""
        # Check for concurrent commands affecting the same resource
        resource = self._determine_command_resource(command)
        
        # Find other active commands on the same resource
        conflicting_users = []
        conflicting_commands = []
        
        for session in self.active_sessions.values():
            if (session.project_name == project_name and 
                session.user_id != user_id and 
                session.current_command and
                self._commands_conflict(command, session.current_command)):
                
                conflicting_users.append(session.user_id)
                conflicting_commands.append(session.current_command)
        
        if conflicting_users:
            conflict_id = str(uuid4())
            conflict = CollaborationConflict(
                conflict_id=conflict_id,
                conflict_type="concurrent_command",
                users_involved=[user_id] + conflicting_users,
                commands_involved=[command] + conflicting_commands,
                resource=resource,
                detected_at=datetime.now(),
                resolution_strategy=ConflictResolution.FIRST_WINS
            )
            
            self.conflicts[conflict_id] = conflict
            return conflict
        
        return None
    
    async def _resolve_conflict(self, conflict: CollaborationConflict) -> Dict[str, Any]:
        """Resolve a collaboration conflict"""
        handler = self.conflict_handlers.get(conflict.conflict_type)
        if handler:
            return await handler(conflict)
        
        # Default resolution: first wins
        return {"proceed": True, "reason": "Default resolution"}
    
    async def _handle_concurrent_command_conflict(self, conflict: CollaborationConflict) -> Dict[str, Any]:
        """Handle concurrent command conflicts"""
        if conflict.resolution_strategy == ConflictResolution.FIRST_WINS:
            # First user wins, others are notified
            primary_user = conflict.users_involved[0]
            other_users = conflict.users_involved[1:]
            
            for user_id in other_users:
                # Find user's session
                session = self._find_user_session(user_id, conflict.resource)
                if session:
                    broadcast_chat_message(
                        user_id="system",
                        message=f"⚠️ {primary_user} is already executing a similar command. Please wait.",
                        message_type="system",
                        project_name=session.project_name
                    )
            
            return {"proceed": len(conflict.users_involved) == 1}
        
        return {"proceed": True}
    
    async def _handle_resource_lock_conflict(self, conflict: CollaborationConflict) -> Dict[str, Any]:
        """Handle resource lock conflicts"""
        return {"proceed": False, "reason": "Resource is locked"}
    
    async def _handle_state_change_conflict(self, conflict: CollaborationConflict) -> Dict[str, Any]:
        """Handle state change conflicts"""
        return {"proceed": True, "reason": "State changes are coordinated"}
    
    async def _handle_lock_conflict(self, user_id: str, command: str, existing_lock: CommandLock):
        """Handle lock acquisition conflicts"""
        # Notify user about the lock
        session = self._find_user_session(user_id)
        if session:
            time_remaining = (existing_lock.expires_at - datetime.now()).total_seconds()
            broadcast_chat_message(
                user_id="system",
                message=f"🔒 Resource locked by {existing_lock.user_id}. Try again in {int(time_remaining)}s.",
                message_type="system",
                project_name=session.project_name
            )
    
    # =====================================================
    # Helper Methods
    # =====================================================
    
    def _find_resource_lock(self, resource: str, project_name: str) -> Optional[CommandLock]:
        """Find existing lock for a resource"""
        for lock in self.command_locks.values():
            if lock.resource == resource and lock.project_name == project_name:
                return lock
        return None
    
    def _find_user_session(self, user_id: str, project_name: str = None) -> Optional[UserSession]:
        """Find user's active session"""
        for session in self.active_sessions.values():
            if session.user_id == user_id and (project_name is None or session.project_name == project_name):
                return session
        return None
    
    def _is_lock_expired(self, lock: CommandLock) -> bool:
        """Check if a lock has expired"""
        return datetime.now() > lock.expires_at
    
    def _check_command_permission(self, session: UserSession, command: str) -> bool:
        """Check if user has permission to execute command"""
        required_permission = self._get_required_permission(command)
        
        # Permission hierarchy: ADMIN > MAINTAINER > CONTRIBUTOR > VIEWER
        permission_levels = {
            UserPermission.VIEWER: 0,
            UserPermission.CONTRIBUTOR: 1,
            UserPermission.MAINTAINER: 2,
            UserPermission.ADMIN: 3
        }
        
        user_level = permission_levels.get(session.permission_level, 0)
        required_level = permission_levels.get(required_permission, 1)
        
        return user_level >= required_level
    
    def _get_required_permission(self, command: str) -> UserPermission:
        """Get required permission level for a command"""
        command_permissions = {
            "/epic": UserPermission.CONTRIBUTOR,
            "/approve": UserPermission.MAINTAINER,
            "/sprint": UserPermission.MAINTAINER,
            "/backlog": UserPermission.CONTRIBUTOR,
            "/state": UserPermission.VIEWER,
            "/project": UserPermission.ADMIN,
            "/request_changes": UserPermission.CONTRIBUTOR,
            "/help": UserPermission.VIEWER
        }
        
        base_command = command.split()[0]
        return command_permissions.get(base_command, UserPermission.CONTRIBUTOR)
    
    def _determine_command_resource(self, command: str) -> str:
        """Determine what resource a command affects"""
        base_command = command.split()[0]
        
        resource_map = {
            "/epic": "epic",
            "/approve": "backlog",
            "/sprint": "sprint",
            "/backlog": "backlog",
            "/project": "project",
            "/request_changes": "review"
        }
        
        return resource_map.get(base_command, "general")
    
    def _command_requires_lock(self, command: str) -> bool:
        """Check if command requires a resource lock"""
        locking_commands = {"/epic", "/approve", "/sprint", "/project"}
        base_command = command.split()[0]
        return base_command in locking_commands
    
    def _commands_conflict(self, command1: str, command2: str) -> bool:
        """Check if two commands conflict with each other"""
        resource1 = self._determine_command_resource(command1)
        resource2 = self._determine_command_resource(command2)
        
        # Commands conflict if they affect the same resource
        return resource1 == resource2 and resource1 != "general"
    
    async def _release_user_locks(self, user_id: str, project_name: str):
        """Release all locks held by a user in a project"""
        to_release = []
        
        for lock_id, lock in self.command_locks.items():
            if lock.user_id == user_id and lock.project_name == project_name:
                to_release.append(lock_id)
        
        for lock_id in to_release:
            await self.release_command_lock(lock_id)
    
    async def _periodic_cleanup(self):
        """Periodic cleanup of expired locks and inactive sessions"""
        while True:
            try:
                await asyncio.sleep(60)  # Run every minute
                
                # Clean up expired locks
                expired_locks = []
                for lock_id, lock in self.command_locks.items():
                    if self._is_lock_expired(lock):
                        expired_locks.append(lock_id)
                
                for lock_id in expired_locks:
                    await self.release_command_lock(lock_id)
                
                # Clean up inactive sessions (inactive for > 30 minutes)
                inactive_sessions = []
                cutoff = datetime.now() - timedelta(minutes=30)
                
                for session_id, session in self.active_sessions.items():
                    if session.last_activity < cutoff:
                        inactive_sessions.append(session_id)
                
                for session_id in inactive_sessions:
                    await self.leave_session(session_id)
                
            except Exception as e:
                logger.error(f"Error in periodic cleanup: {e}")
    
    def add_session_listener(self, listener: Callable):
        """Add a session event listener"""
        self.session_listeners.append(listener)
    
    def remove_session_listener(self, listener: Callable):
        """Remove a session event listener"""
        if listener in self.session_listeners:
            self.session_listeners.remove(listener)
    
    def get_collaboration_stats(self, project_name: str) -> Dict[str, Any]:
        """Get collaboration statistics for a project"""
        project_sessions = [s for s in self.active_sessions.values() if s.project_name == project_name]
        project_locks = [l for l in self.command_locks.values() if l.project_name == project_name]
        project_conflicts = [c for c in self.conflicts.values() if any(
            s.project_name == project_name for s in self.active_sessions.values() 
            if s.user_id in c.users_involved
        )]
        
        return {
            "active_users": len(project_sessions),
            "active_locks": len(project_locks),
            "unresolved_conflicts": len([c for c in project_conflicts if not c.resolved]),
            "user_breakdown": {
                perm.value: len([s for s in project_sessions if s.permission_level == perm])
                for perm in UserPermission
            },
            "lock_breakdown": {
                resource: len([l for l in project_locks if l.resource == resource])
                for resource in set(l.resource for l in project_locks)
            }
        }


# Global collaboration manager instance
_collaboration_manager = None

def get_collaboration_manager() -> CollaborationManager:
    """Get global collaboration manager instance"""
    global _collaboration_manager
    if _collaboration_manager is None:
        _collaboration_manager = CollaborationManager()
    return _collaboration_manager


# Convenience functions
async def join_collaboration_session(user_id: str, project_name: str, 
                                   permission_level: UserPermission = UserPermission.CONTRIBUTOR,
                                   client_info: Dict[str, Any] = None) -> str:
    """Convenience function to join a collaboration session"""
    manager = get_collaboration_manager()
    return await manager.join_session(user_id, project_name, permission_level, client_info)


async def leave_collaboration_session(session_id: str):
    """Convenience function to leave a collaboration session"""
    manager = get_collaboration_manager()
    await manager.leave_session(session_id)


async def execute_collaborative_command(user_id: str, command: str, project_name: str, 
                                      session_id: str, command_processor: Callable = None) -> Dict[str, Any]:
    """Convenience function to execute a collaborative command"""
    manager = get_collaboration_manager()
    return await manager.execute_collaborative_command(user_id, command, project_name, session_id, command_processor)