#!/usr/bin/env python3
"""
Collaboration Manager for Multi-User Discord-Style Interface

Provides real-time collaborative features including user sessions,
resource locking, permission management, and conflict resolution
for the Discord-style chat interface.
"""

import asyncio
import json
import logging
import uuid
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Set, Callable
from enum import Enum
from dataclasses import dataclass, asdict
from collections import defaultdict

logger = logging.getLogger(__name__)


class UserPermission(Enum):
    """User permission levels"""
    VIEWER = "viewer"
    CONTRIBUTOR = "contributor"
    MAINTAINER = "maintainer"
    ADMIN = "admin"


@dataclass
class CollaborationSession:
    """Represents a user collaboration session"""
    session_id: str
    user_id: str
    project_name: str
    permission_level: UserPermission
    joined_at: datetime
    last_activity: datetime
    active: bool = True
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            **asdict(self),
            'permission_level': self.permission_level.value,
            'joined_at': self.joined_at.isoformat(),
            'last_activity': self.last_activity.isoformat()
        }


@dataclass
class ResourceLock:
    """Represents a resource lock for exclusive access"""
    resource_id: str
    resource_type: str  # 'epic', 'story', 'sprint', 'command'
    locked_by: str  # session_id
    locked_at: datetime
    expires_at: Optional[datetime] = None
    
    def is_expired(self) -> bool:
        """Check if lock has expired"""
        if self.expires_at is None:
            return False
        return datetime.now() > self.expires_at
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            **asdict(self),
            'locked_at': self.locked_at.isoformat(),
            'expires_at': self.expires_at.isoformat() if self.expires_at else None
        }


class CollaborationManager:
    """
    Manages multi-user collaboration for the Discord-style interface.
    
    Provides features for:
    - User session management
    - Resource locking and conflict resolution
    - Permission-based access control
    - Real-time collaboration events
    - Activity tracking and statistics
    """
    
    def __init__(self):
        self.sessions: Dict[str, CollaborationSession] = {}
        self.resource_locks: Dict[str, ResourceLock] = {}
        self.user_sessions: Dict[str, Set[str]] = defaultdict(set)  # user_id -> session_ids
        self.project_sessions: Dict[str, Set[str]] = defaultdict(set)  # project -> session_ids
        self.activity_log: List[Dict[str, Any]] = []
        self.collaboration_stats: Dict[str, Dict[str, Any]] = defaultdict(lambda: {
            'total_sessions': 0,
            'active_sessions': 0,
            'commands_executed': 0,
            'conflicts_resolved': 0,
            'last_activity': None
        })
        
        # Configuration
        self.session_timeout = timedelta(hours=2)
        self.lock_timeout = timedelta(minutes=5)
        self.max_concurrent_sessions = 10
        self.cleanup_interval = timedelta(minutes=10)
        
        # Start cleanup task
        self._cleanup_task = None
        self._start_cleanup_task()
    
    def _start_cleanup_task(self):
        """Start background cleanup task"""
        async def cleanup_loop():
            while True:
                try:
                    await self.cleanup_expired_sessions()
                    await self.cleanup_expired_locks()
                    await asyncio.sleep(self.cleanup_interval.total_seconds())
                except Exception as e:
                    logger.error(f"Error in collaboration cleanup: {e}")
                    await asyncio.sleep(60)  # Wait 1 minute on error
        
        if self._cleanup_task is None or self._cleanup_task.done():
            self._cleanup_task = asyncio.create_task(cleanup_loop())
    
    async def join_session(self, user_id: str, project_name: str, 
                          permission_level: UserPermission) -> str:
        """
        Join a collaboration session.
        
        Args:
            user_id: User identifier
            project_name: Project name
            permission_level: User's permission level
            
        Returns:
            Session ID
            
        Raises:
            ValueError: If session limit exceeded or invalid parameters
        """
        # Validate parameters
        if not user_id or not project_name:
            raise ValueError("User ID and project name are required")
        
        # Check session limits
        project_session_count = len(self.project_sessions[project_name])
        if project_session_count >= self.max_concurrent_sessions:
            raise ValueError(f"Maximum concurrent sessions ({self.max_concurrent_sessions}) exceeded for project")
        
        # Create new session
        session_id = str(uuid.uuid4())
        now = datetime.now()
        
        session = CollaborationSession(
            session_id=session_id,
            user_id=user_id,
            project_name=project_name,
            permission_level=permission_level,
            joined_at=now,
            last_activity=now
        )
        
        # Store session
        self.sessions[session_id] = session
        self.user_sessions[user_id].add(session_id)
        self.project_sessions[project_name].add(session_id)
        
        # Update statistics
        self.collaboration_stats[project_name]['total_sessions'] += 1
        self.collaboration_stats[project_name]['active_sessions'] += 1
        self.collaboration_stats[project_name]['last_activity'] = now.isoformat()
        
        # Log activity
        self._log_activity('session_joined', {
            'session_id': session_id,
            'user_id': user_id,
            'project_name': project_name,
            'permission_level': permission_level.value
        })
        
        logger.info(f"User {user_id} joined collaboration session for project {project_name}")
        return session_id
    
    async def leave_session(self, session_id: str):
        """
        Leave a collaboration session.
        
        Args:
            session_id: Session to leave
        """
        if session_id not in self.sessions:
            return
        
        session = self.sessions[session_id]
        
        # Release any locks held by this session
        await self.release_session_locks(session_id)
        
        # Remove session
        del self.sessions[session_id]
        self.user_sessions[session.user_id].discard(session_id)
        self.project_sessions[session.project_name].discard(session_id)
        
        # Update statistics
        self.collaboration_stats[session.project_name]['active_sessions'] -= 1
        
        # Log activity
        self._log_activity('session_left', {
            'session_id': session_id,
            'user_id': session.user_id,
            'project_name': session.project_name
        })
        
        logger.info(f"User {session.user_id} left collaboration session {session_id}")
    
    async def update_activity(self, session_id: str):
        """Update last activity time for a session"""
        if session_id in self.sessions:
            self.sessions[session_id].last_activity = datetime.now()
    
    async def acquire_resource_lock(self, session_id: str, resource_id: str, 
                                  resource_type: str, duration_minutes: int = 5) -> bool:
        """
        Acquire a lock on a resource.
        
        Args:
            session_id: Session requesting the lock
            resource_id: ID of the resource to lock
            resource_type: Type of resource ('epic', 'story', 'sprint', 'command')
            duration_minutes: Lock duration in minutes
            
        Returns:
            True if lock acquired, False if already locked
        """
        if session_id not in self.sessions:
            return False
        
        # Check if resource is already locked
        if resource_id in self.resource_locks:
            existing_lock = self.resource_locks[resource_id]
            if not existing_lock.is_expired() and existing_lock.locked_by != session_id:
                return False
        
        # Create new lock
        now = datetime.now()
        expires_at = now + timedelta(minutes=duration_minutes)
        
        lock = ResourceLock(
            resource_id=resource_id,
            resource_type=resource_type,
            locked_by=session_id,
            locked_at=now,
            expires_at=expires_at
        )
        
        self.resource_locks[resource_id] = lock
        
        # Log activity
        session = self.sessions[session_id]
        self._log_activity('resource_locked', {
            'session_id': session_id,
            'user_id': session.user_id,
            'project_name': session.project_name,
            'resource_id': resource_id,
            'resource_type': resource_type
        })
        
        return True
    
    async def release_resource_lock(self, session_id: str, resource_id: str) -> bool:
        """
        Release a resource lock.
        
        Args:
            session_id: Session releasing the lock
            resource_id: ID of the resource to unlock
            
        Returns:
            True if lock released, False if not locked by this session
        """
        if resource_id not in self.resource_locks:
            return False
        
        lock = self.resource_locks[resource_id]
        if lock.locked_by != session_id:
            return False
        
        del self.resource_locks[resource_id]
        
        # Log activity
        if session_id in self.sessions:
            session = self.sessions[session_id]
            self._log_activity('resource_unlocked', {
                'session_id': session_id,
                'user_id': session.user_id,
                'project_name': session.project_name,
                'resource_id': resource_id,
                'resource_type': lock.resource_type
            })
        
        return True
    
    async def release_session_locks(self, session_id: str):
        """Release all locks held by a session"""
        locks_to_release = [
            resource_id for resource_id, lock in self.resource_locks.items()
            if lock.locked_by == session_id
        ]
        
        for resource_id in locks_to_release:
            await self.release_resource_lock(session_id, resource_id)
    
    async def execute_collaborative_command(self, user_id: str, command: str, 
                                          project_name: str, session_id: str,
                                          command_processor: Callable) -> Dict[str, Any]:
        """
        Execute a command in collaborative context.
        
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
        if session_id not in self.sessions:
            return {
                "success": False,
                "error": "Invalid or expired session",
                "collaboration_error": True
            }
        
        session = self.sessions[session_id]
        
        # Update activity
        await self.update_activity(session_id)
        
        # Check permissions for command
        if not self._check_command_permission(command, session.permission_level):
            return {
                "success": False,
                "error": f"Insufficient permissions for command: {command}",
                "required_permission": self._get_required_permission(command),
                "user_permission": session.permission_level.value,
                "collaboration_error": True
            }
        
        # Acquire command lock if needed
        command_lock_id = f"command_{project_name}_{command.split()[0]}"
        lock_acquired = await self.acquire_resource_lock(
            session_id, command_lock_id, "command", duration_minutes=1
        )
        
        try:
            # Execute command
            result = await command_processor(command, user_id, project_name)
            
            # Add collaboration metadata
            result.update({
                "collaboration_session": session_id,
                "executed_by": user_id,
                "permission_level": session.permission_level.value,
                "lock_acquired": lock_acquired
            })
            
            # Update statistics
            self.collaboration_stats[project_name]['commands_executed'] += 1
            
            # Log activity
            self._log_activity('command_executed', {
                'session_id': session_id,
                'user_id': user_id,
                'project_name': project_name,
                'command': command,
                'success': result.get('success', False)
            })
            
            return result
            
        finally:
            # Release command lock
            if lock_acquired:
                await self.release_resource_lock(session_id, command_lock_id)
    
    def _check_command_permission(self, command: str, permission_level: UserPermission) -> bool:
        """Check if user has permission to execute command"""
        command_permissions = {
            "/help": UserPermission.VIEWER,
            "/state": UserPermission.VIEWER,
            "/epic": UserPermission.CONTRIBUTOR,
            "/approve": UserPermission.MAINTAINER,
            "/sprint": UserPermission.MAINTAINER,
            "/backlog": UserPermission.CONTRIBUTOR,
            "/project": UserPermission.ADMIN,
            "/request_changes": UserPermission.CONTRIBUTOR
        }
        
        base_command = command.split()[0] if command else ""
        required_permission = command_permissions.get(base_command, UserPermission.CONTRIBUTOR)
        
        # Permission hierarchy: VIEWER < CONTRIBUTOR < MAINTAINER < ADMIN
        permission_levels = {
            UserPermission.VIEWER: 1,
            UserPermission.CONTRIBUTOR: 2,
            UserPermission.MAINTAINER: 3,
            UserPermission.ADMIN: 4
        }
        
        return permission_levels[permission_level] >= permission_levels[required_permission]
    
    def _get_required_permission(self, command: str) -> str:
        """Get required permission level for a command"""
        command_permissions = {
            "/help": "viewer",
            "/state": "viewer",
            "/epic": "contributor",
            "/approve": "maintainer",
            "/sprint": "maintainer",
            "/backlog": "contributor",
            "/project": "admin",
            "/request_changes": "contributor"
        }
        
        base_command = command.split()[0] if command else ""
        return command_permissions.get(base_command, "contributor")
    
    async def get_active_users(self, project_name: str) -> List[Dict[str, Any]]:
        """Get list of active users for a project"""
        project_session_ids = self.project_sessions.get(project_name, set())
        active_users = []
        
        for session_id in project_session_ids:
            if session_id in self.sessions:
                session = self.sessions[session_id]
                active_users.append({
                    'user_id': session.user_id,
                    'session_id': session_id,
                    'permission_level': session.permission_level.value,
                    'joined_at': session.joined_at.isoformat(),
                    'last_activity': session.last_activity.isoformat()
                })
        
        # Sort by join time
        active_users.sort(key=lambda x: x['joined_at'])
        return active_users
    
    async def get_resource_locks(self, project_name: str) -> List[Dict[str, Any]]:
        """Get list of resource locks for a project"""
        project_session_ids = self.project_sessions.get(project_name, set())
        project_locks = []
        
        for resource_id, lock in self.resource_locks.items():
            if lock.locked_by in project_session_ids:
                session = self.sessions.get(lock.locked_by)
                lock_info = lock.to_dict()
                if session:
                    lock_info['locked_by_user'] = session.user_id
                project_locks.append(lock_info)
        
        return project_locks
    
    def get_collaboration_stats(self, project_name: str) -> Dict[str, Any]:
        """Get collaboration statistics for a project"""
        return dict(self.collaboration_stats[project_name])
    
    async def cleanup_expired_sessions(self):
        """Clean up expired sessions"""
        now = datetime.now()
        expired_sessions = []
        
        for session_id, session in self.sessions.items():
            if now - session.last_activity > self.session_timeout:
                expired_sessions.append(session_id)
        
        for session_id in expired_sessions:
            await self.leave_session(session_id)
            logger.info(f"Cleaned up expired session: {session_id}")
    
    async def cleanup_expired_locks(self):
        """Clean up expired resource locks"""
        expired_locks = []
        
        for resource_id, lock in self.resource_locks.items():
            if lock.is_expired():
                expired_locks.append(resource_id)
        
        for resource_id in expired_locks:
            del self.resource_locks[resource_id]
            logger.info(f"Cleaned up expired lock: {resource_id}")
    
    def _log_activity(self, activity_type: str, details: Dict[str, Any]):
        """Log collaboration activity"""
        activity = {
            'type': activity_type,
            'timestamp': datetime.now().isoformat(),
            'details': details
        }
        
        self.activity_log.append(activity)
        
        # Keep only last 1000 activities
        if len(self.activity_log) > 1000:
            self.activity_log = self.activity_log[-1000:]


# Global collaboration manager instance
_collaboration_manager = None

def get_collaboration_manager() -> CollaborationManager:
    """Get global collaboration manager instance"""
    global _collaboration_manager
    if _collaboration_manager is None:
        _collaboration_manager = CollaborationManager()
    return _collaboration_manager


if __name__ == "__main__":
    # Test the collaboration manager
    import asyncio
    
    async def test_collaboration():
        manager = CollaborationManager()
        
        print("Testing Collaboration Manager")
        print("=" * 50)
        
        # Test session management
        session1 = await manager.join_session("user1", "test_project", UserPermission.CONTRIBUTOR)
        session2 = await manager.join_session("user2", "test_project", UserPermission.MAINTAINER)
        
        print(f"Created sessions: {session1}, {session2}")
        
        # Test active users
        active_users = await manager.get_active_users("test_project")
        print(f"Active users: {len(active_users)}")
        
        # Test resource locking
        lock_acquired = await manager.acquire_resource_lock(session1, "epic1", "epic")
        print(f"Lock acquired: {lock_acquired}")
        
        # Test permission checking
        has_permission = manager._check_command_permission("/epic", UserPermission.CONTRIBUTOR)
        print(f"Has permission for /epic: {has_permission}")
        
        # Test collaboration stats
        stats = manager.get_collaboration_stats("test_project")
        print(f"Collaboration stats: {stats}")
        
        # Cleanup
        await manager.leave_session(session1)
        await manager.leave_session(session2)
        print("Sessions cleaned up")
    
    asyncio.run(test_collaboration())