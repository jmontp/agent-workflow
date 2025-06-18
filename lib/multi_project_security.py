"""
Multi-Project Security and Isolation System

Comprehensive security framework for multi-project orchestration including
access controls, project isolation, secret management, and audit logging.
"""

import os
import hashlib
import secrets
import logging
import asyncio
import json
import base64
import time
from typing import Dict, List, Optional, Any, Set, Tuple, Union
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
import subprocess
import tempfile
import shutil

# Import cryptography for encryption (if available)
try:
    from cryptography.fernet import Fernet
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
    CRYPTO_AVAILABLE = True
except ImportError:
    CRYPTO_AVAILABLE = False

logger = logging.getLogger(__name__)


class AccessLevel(Enum):
    """Access levels for projects and resources"""
    NONE = "none"           # No access
    READ = "read"           # Read-only access
    WRITE = "write"         # Read and write access
    ADMIN = "admin"         # Full administrative access
    OWNER = "owner"         # Ownership level access


class SecurityAction(Enum):
    """Types of security actions for audit logging"""
    LOGIN = "login"
    LOGOUT = "logout"
    ACCESS_GRANTED = "access_granted"
    ACCESS_DENIED = "access_denied"
    PERMISSION_CHANGED = "permission_changed"
    SECRET_ACCESSED = "secret_accessed"
    SECRET_CREATED = "secret_created"
    SECRET_DELETED = "secret_deleted"
    PROJECT_ACCESSED = "project_accessed"
    COMMAND_EXECUTED = "command_executed"
    FILE_ACCESSED = "file_accessed"
    SECURITY_VIOLATION = "security_violation"


class IsolationMode(Enum):
    """Project isolation modes"""
    NONE = "none"                   # No isolation
    PROCESS = "process"             # Process-level isolation
    CONTAINER = "container"         # Container isolation
    FILESYSTEM = "filesystem"       # Filesystem isolation
    NETWORK = "network"            # Network isolation
    FULL = "full"                  # Full isolation (all methods)


@dataclass
class User:
    """User account information"""
    user_id: str
    username: str
    email: str
    password_hash: str
    salt: str
    
    # Access and permissions
    global_access_level: AccessLevel = AccessLevel.READ
    project_permissions: Dict[str, AccessLevel] = field(default_factory=dict)
    
    # Security settings
    two_factor_enabled: bool = False
    two_factor_secret: Optional[str] = None
    api_keys: List[str] = field(default_factory=list)
    
    # Account status
    is_active: bool = True
    is_locked: bool = False
    failed_login_attempts: int = 0
    last_login: Optional[datetime] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    
    # Session management
    active_sessions: List[str] = field(default_factory=list)
    max_sessions: int = 3


@dataclass
class AccessRule:
    """Access control rule"""
    rule_id: str
    name: str
    description: str
    
    # Rule criteria
    user_patterns: List[str] = field(default_factory=list)  # Username patterns
    project_patterns: List[str] = field(default_factory=list)  # Project name patterns
    resource_patterns: List[str] = field(default_factory=list)  # Resource patterns
    time_restrictions: Dict[str, Any] = field(default_factory=dict)  # Time-based restrictions
    
    # Access control
    allowed_actions: List[str] = field(default_factory=list)
    denied_actions: List[str] = field(default_factory=list)
    access_level: AccessLevel = AccessLevel.READ
    
    # Rule metadata
    priority: int = 0  # Higher priority rules are evaluated first
    enabled: bool = True
    created_by: str = ""
    created_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class Secret:
    """Encrypted secret storage"""
    secret_id: str
    name: str
    description: str
    encrypted_value: str
    
    # Access control
    owner: str
    allowed_projects: List[str] = field(default_factory=list)
    allowed_users: List[str] = field(default_factory=list)
    
    # Metadata
    secret_type: str = "generic"  # generic, api_key, database, ssh_key, etc.
    expires_at: Optional[datetime] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    last_accessed: Optional[datetime] = None
    access_count: int = 0


@dataclass
class AuditLogEntry:
    """Audit log entry"""
    log_id: str
    timestamp: datetime
    action: SecurityAction
    user_id: str
    resource: str
    
    # Context information
    project_name: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    session_id: Optional[str] = None
    
    # Action details
    success: bool = True
    error_message: Optional[str] = None
    additional_data: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ProjectIsolation:
    """Project isolation configuration"""
    project_name: str
    isolation_mode: IsolationMode
    
    # Filesystem isolation
    isolated_directory: Optional[str] = None
    allowed_paths: List[str] = field(default_factory=list)
    denied_paths: List[str] = field(default_factory=list)
    
    # Process isolation
    process_uid: Optional[int] = None
    process_gid: Optional[int] = None
    resource_limits: Dict[str, Any] = field(default_factory=dict)
    
    # Network isolation
    allowed_hosts: List[str] = field(default_factory=list)
    denied_hosts: List[str] = field(default_factory=list)
    allowed_ports: List[int] = field(default_factory=list)
    
    # Container settings (if using container isolation)
    container_image: Optional[str] = None
    container_config: Dict[str, Any] = field(default_factory=dict)


class MultiProjectSecurity:
    """
    Comprehensive security system for multi-project orchestration.
    
    Provides user authentication, authorization, project isolation,
    secret management, and comprehensive audit logging.
    """
    
    def __init__(
        self,
        storage_path: str = ".orch-global/security",
        master_key: Optional[str] = None,
        enable_audit_logging: bool = True,
        default_isolation_mode: IsolationMode = IsolationMode.PROCESS
    ):
        """
        Initialize multi-project security system.
        
        Args:
            storage_path: Path to store security data
            master_key: Master encryption key for secrets
            enable_audit_logging: Whether to enable audit logging
            default_isolation_mode: Default isolation mode for projects
        """
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        self.enable_audit_logging = enable_audit_logging
        self.default_isolation_mode = default_isolation_mode
        
        # Security state
        self.users: Dict[str, User] = {}
        self.access_rules: Dict[str, AccessRule] = {}
        self.secrets: Dict[str, Secret] = {}
        self.project_isolations: Dict[str, ProjectIsolation] = {}
        self.audit_log: List[AuditLogEntry] = []
        
        # Session management
        self.active_sessions: Dict[str, Dict[str, Any]] = {}
        self.session_timeout: int = 3600  # 1 hour
        
        # Encryption setup
        self._setup_encryption(master_key)
        
        # Security monitoring
        self.security_events: List[Dict[str, Any]] = []
        self.failed_login_tracker: Dict[str, List[datetime]] = {}
        
        # Load existing data
        self._load_security_data()
        
        logger.info("Multi-project security system initialized")
    
    def create_user(
        self,
        username: str,
        email: str,
        password: str,
        global_access_level: AccessLevel = AccessLevel.READ
    ) -> bool:
        """
        Create a new user account.
        
        Args:
            username: Username for the account
            email: Email address
            password: Plain text password (will be hashed)
            global_access_level: Default global access level
            
        Returns:
            True if created successfully, False otherwise
        """
        if any(user.username == username for user in self.users.values()):
            logger.warning(f"Username '{username}' already exists")
            return False
        
        if any(user.email == email for user in self.users.values()):
            logger.warning(f"Email '{email}' already registered")
            return False
        
        # Generate user ID
        user_id = self._generate_id("user")
        
        # Hash password
        salt = secrets.token_hex(16)
        password_hash = self._hash_password(password, salt)
        
        # Create user
        user = User(
            user_id=user_id,
            username=username,
            email=email,
            password_hash=password_hash,
            salt=salt,
            global_access_level=global_access_level
        )
        
        self.users[user_id] = user
        
        # Log user creation
        self._log_security_event(
            SecurityAction.ACCESS_GRANTED,
            "system",
            f"user:{user_id}",
            additional_data={"action": "user_created", "username": username}
        )
        
        logger.info(f"Created user account: {username}")
        return True
    
    def authenticate_user(self, username: str, password: str, ip_address: Optional[str] = None) -> Optional[str]:
        """
        Authenticate a user and create a session.
        
        Args:
            username: Username to authenticate
            password: Password to verify
            ip_address: IP address of the client
            
        Returns:
            Session token if authentication successful, None otherwise
        """
        # Find user by username
        user = None
        for u in self.users.values():
            if u.username == username:
                user = u
                break
        
        if not user:
            self._log_security_event(
                SecurityAction.ACCESS_DENIED,
                "unknown",
                f"user:{username}",
                success=False,
                error_message="User not found",
                ip_address=ip_address
            )
            return None
        
        # Check if account is locked
        if user.is_locked or not user.is_active:
            self._log_security_event(
                SecurityAction.ACCESS_DENIED,
                user.user_id,
                f"user:{user.user_id}",
                success=False,
                error_message="Account locked or inactive",
                ip_address=ip_address
            )
            return None
        
        # Check failed login attempts
        if self._should_lockout_user(user.user_id, ip_address):
            user.is_locked = True
            self._log_security_event(
                SecurityAction.SECURITY_VIOLATION,
                user.user_id,
                f"user:{user.user_id}",
                success=False,
                error_message="Account locked due to failed login attempts",
                ip_address=ip_address
            )
            return None
        
        # Verify password
        if not self._verify_password(password, user.password_hash, user.salt):
            user.failed_login_attempts += 1
            self._track_failed_login(user.user_id, ip_address)
            
            self._log_security_event(
                SecurityAction.ACCESS_DENIED,
                user.user_id,
                f"user:{user.user_id}",
                success=False,
                error_message="Invalid password",
                ip_address=ip_address
            )
            return None
        
        # Create session
        session_token = self._create_session(user, ip_address)
        
        # Update user login info
        user.last_login = datetime.utcnow()
        user.failed_login_attempts = 0
        
        self._log_security_event(
            SecurityAction.LOGIN,
            user.user_id,
            f"user:{user.user_id}",
            session_id=session_token,
            ip_address=ip_address
        )
        
        logger.info(f"User authenticated: {username}")
        return session_token
    
    def check_access(
        self,
        user_id: str,
        project_name: str,
        action: str,
        resource: Optional[str] = None
    ) -> bool:
        """
        Check if a user has access to perform an action.
        
        Args:
            user_id: ID of the user
            project_name: Name of the project
            action: Action to perform
            resource: Specific resource (optional)
            
        Returns:
            True if access is granted, False otherwise
        """
        if user_id not in self.users:
            return False
        
        user = self.users[user_id]
        
        # Check if user is active
        if not user.is_active or user.is_locked:
            return False
        
        # Check global access level
        if user.global_access_level == AccessLevel.OWNER:
            return True
        
        # Check project-specific permissions
        project_access = user.project_permissions.get(project_name, AccessLevel.NONE)
        
        # Determine required access level for action
        required_level = self._get_required_access_level(action)
        
        # Check if user has sufficient access
        has_access = self._has_sufficient_access(project_access, required_level)
        
        # Check access rules
        if not has_access:
            has_access = self._check_access_rules(user, project_name, action, resource)
        
        # Log access attempt
        self._log_security_event(
            SecurityAction.ACCESS_GRANTED if has_access else SecurityAction.ACCESS_DENIED,
            user_id,
            f"project:{project_name}",
            project_name=project_name,
            success=has_access,
            additional_data={"action": action, "resource": resource}
        )
        
        return has_access
    
    def create_secret(
        self,
        name: str,
        value: str,
        secret_type: str = "generic",
        owner: str = "",
        allowed_projects: Optional[List[str]] = None,
        description: str = ""
    ) -> str:
        """
        Create and encrypt a secret.
        
        Args:
            name: Name of the secret
            value: Secret value to encrypt
            secret_type: Type of secret
            owner: Owner user ID
            allowed_projects: Projects that can access this secret
            description: Description of the secret
            
        Returns:
            Secret ID
        """
        if not CRYPTO_AVAILABLE:
            raise RuntimeError("Cryptography library not available for secret management")
        
        secret_id = self._generate_id("secret")
        encrypted_value = self.cipher.encrypt(value.encode()).decode()
        
        secret = Secret(
            secret_id=secret_id,
            name=name,
            description=description,
            encrypted_value=encrypted_value,
            owner=owner,
            allowed_projects=allowed_projects or [],
            secret_type=secret_type
        )
        
        self.secrets[secret_id] = secret
        
        self._log_security_event(
            SecurityAction.SECRET_CREATED,
            owner,
            f"secret:{secret_id}",
            additional_data={"secret_name": name, "secret_type": secret_type}
        )
        
        logger.info(f"Created secret: {name}")
        return secret_id
    
    def get_secret(self, secret_id: str, user_id: str, project_name: Optional[str] = None) -> Optional[str]:
        """
        Retrieve and decrypt a secret.
        
        Args:
            secret_id: ID of the secret
            user_id: ID of the requesting user
            project_name: Project context (optional)
            
        Returns:
            Decrypted secret value if authorized, None otherwise
        """
        if secret_id not in self.secrets:
            return None
        
        secret = self.secrets[secret_id]
        
        # Check access permissions
        if not self._can_access_secret(secret, user_id, project_name):
            self._log_security_event(
                SecurityAction.ACCESS_DENIED,
                user_id,
                f"secret:{secret_id}",
                project_name=project_name,
                success=False,
                error_message="Insufficient permissions"
            )
            return None
        
        # Decrypt secret
        try:
            decrypted_value = self.cipher.decrypt(secret.encrypted_value.encode()).decode()
            
            # Update access tracking
            secret.last_accessed = datetime.utcnow()
            secret.access_count += 1
            
            self._log_security_event(
                SecurityAction.SECRET_ACCESSED,
                user_id,
                f"secret:{secret_id}",
                project_name=project_name,
                additional_data={"secret_name": secret.name}
            )
            
            return decrypted_value
            
        except Exception as e:
            logger.error(f"Failed to decrypt secret {secret_id}: {str(e)}")
            return None
    
    def setup_project_isolation(
        self,
        project_name: str,
        isolation_mode: Optional[IsolationMode] = None
    ) -> bool:
        """
        Setup isolation for a project.
        
        Args:
            project_name: Name of the project
            isolation_mode: Isolation mode to use
            
        Returns:
            True if setup successful, False otherwise
        """
        isolation_mode = isolation_mode or self.default_isolation_mode
        
        isolation = ProjectIsolation(
            project_name=project_name,
            isolation_mode=isolation_mode
        )
        
        # Setup isolation based on mode
        if isolation_mode == IsolationMode.FILESYSTEM:
            success = self._setup_filesystem_isolation(isolation)
        elif isolation_mode == IsolationMode.PROCESS:
            success = self._setup_process_isolation(isolation)
        elif isolation_mode == IsolationMode.CONTAINER:
            success = self._setup_container_isolation(isolation)
        elif isolation_mode == IsolationMode.NETWORK:
            success = self._setup_network_isolation(isolation)
        elif isolation_mode == IsolationMode.FULL:
            success = (
                self._setup_filesystem_isolation(isolation) and
                self._setup_process_isolation(isolation) and
                self._setup_network_isolation(isolation)
            )
        else:
            success = True  # No isolation
        
        if success:
            self.project_isolations[project_name] = isolation
            logger.info(f"Setup {isolation_mode.value} isolation for project: {project_name}")
        
        return success
    
    def get_audit_log(
        self,
        user_id: Optional[str] = None,
        project_name: Optional[str] = None,
        action: Optional[SecurityAction] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: int = 100
    ) -> List[AuditLogEntry]:
        """
        Get filtered audit log entries.
        
        Args:
            user_id: Filter by user ID
            project_name: Filter by project name
            action: Filter by action type
            start_time: Filter by start time
            end_time: Filter by end time
            limit: Maximum number of entries to return
            
        Returns:
            List of matching audit log entries
        """
        filtered_entries = []
        
        for entry in self.audit_log:
            # Apply filters
            if user_id and entry.user_id != user_id:
                continue
            if project_name and entry.project_name != project_name:
                continue
            if action and entry.action != action:
                continue
            if start_time and entry.timestamp < start_time:
                continue
            if end_time and entry.timestamp > end_time:
                continue
            
            filtered_entries.append(entry)
        
        # Sort by timestamp (newest first) and limit
        filtered_entries.sort(key=lambda e: e.timestamp, reverse=True)
        return filtered_entries[:limit]
    
    def get_security_status(self) -> Dict[str, Any]:
        """Get comprehensive security status"""
        active_sessions_count = len(self.active_sessions)
        failed_logins_24h = len([
            entry for entry in self.audit_log
            if entry.action == SecurityAction.ACCESS_DENIED and
            entry.timestamp > datetime.utcnow() - timedelta(hours=24)
        ])
        
        return {
            "security_system": {
                "encryption_enabled": CRYPTO_AVAILABLE,
                "audit_logging_enabled": self.enable_audit_logging,
                "default_isolation_mode": self.default_isolation_mode.value
            },
            "users": {
                "total_users": len(self.users),
                "active_users": len([u for u in self.users.values() if u.is_active]),
                "locked_users": len([u for u in self.users.values() if u.is_locked]),
                "users_with_2fa": len([u for u in self.users.values() if u.two_factor_enabled])
            },
            "sessions": {
                "active_sessions": active_sessions_count,
                "session_timeout": self.session_timeout
            },
            "secrets": {
                "total_secrets": len(self.secrets),
                "secrets_by_type": self._get_secrets_by_type()
            },
            "isolation": {
                "projects_with_isolation": len(self.project_isolations),
                "isolation_modes": self._get_isolation_modes_summary()
            },
            "audit": {
                "total_log_entries": len(self.audit_log),
                "failed_logins_24h": failed_logins_24h,
                "recent_security_events": len(self.security_events)
            },
            "access_rules": {
                "total_rules": len(self.access_rules),
                "enabled_rules": len([r for r in self.access_rules.values() if r.enabled])
            }
        }
    
    # Private methods
    
    def _setup_encryption(self, master_key: Optional[str]):
        """Setup encryption for secrets"""
        if not CRYPTO_AVAILABLE:
            logger.warning("Cryptography library not available - secret management disabled")
            return
        
        if master_key:
            key = base64.urlsafe_b64encode(master_key.encode().ljust(32)[:32])
        else:
            # Generate or load key
            key_file = self.storage_path / "master.key"
            if key_file.exists():
                with open(key_file, 'rb') as f:
                    key = f.read()
            else:
                key = Fernet.generate_key()
                with open(key_file, 'wb') as f:
                    f.write(key)
                os.chmod(key_file, 0o600)  # Restrict permissions
        
        self.cipher = Fernet(key)
    
    def _generate_id(self, prefix: str) -> str:
        """Generate unique ID with prefix"""
        timestamp = str(int(time.time()))
        random_part = secrets.token_hex(8)
        return f"{prefix}_{timestamp}_{random_part}"
    
    def _hash_password(self, password: str, salt: str) -> str:
        """Hash password with salt"""
        return hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 100000).hex()
    
    def _verify_password(self, password: str, password_hash: str, salt: str) -> bool:
        """Verify password against hash"""
        return self._hash_password(password, salt) == password_hash
    
    def _create_session(self, user: User, ip_address: Optional[str] = None) -> str:
        """Create a new session for user"""
        session_token = secrets.token_urlsafe(32)
        
        # Check session limits
        if len(user.active_sessions) >= user.max_sessions:
            # Remove oldest session
            oldest_session = user.active_sessions.pop(0)
            if oldest_session in self.active_sessions:
                del self.active_sessions[oldest_session]
        
        # Create session
        session_data = {
            "user_id": user.user_id,
            "username": user.username,
            "created_at": datetime.utcnow(),
            "last_activity": datetime.utcnow(),
            "ip_address": ip_address
        }
        
        self.active_sessions[session_token] = session_data
        user.active_sessions.append(session_token)
        
        return session_token
    
    def _should_lockout_user(self, user_id: str, ip_address: Optional[str] = None) -> bool:
        """Check if user should be locked out due to failed attempts"""
        # Check failed attempts in last 15 minutes
        cutoff_time = datetime.utcnow() - timedelta(minutes=15)
        
        if user_id in self.failed_login_tracker:
            recent_failures = [
                attempt for attempt in self.failed_login_tracker[user_id]
                if attempt > cutoff_time
            ]
            
            if len(recent_failures) >= 5:  # 5 failed attempts in 15 minutes
                return True
        
        return False
    
    def _track_failed_login(self, user_id: str, ip_address: Optional[str] = None):
        """Track failed login attempt"""
        if user_id not in self.failed_login_tracker:
            self.failed_login_tracker[user_id] = []
        
        self.failed_login_tracker[user_id].append(datetime.utcnow())
        
        # Keep only recent attempts
        cutoff_time = datetime.utcnow() - timedelta(hours=1)
        self.failed_login_tracker[user_id] = [
            attempt for attempt in self.failed_login_tracker[user_id]
            if attempt > cutoff_time
        ]
    
    def _get_required_access_level(self, action: str) -> AccessLevel:
        """Get required access level for an action"""
        # Define action requirements
        action_levels = {
            "read": AccessLevel.READ,
            "view": AccessLevel.READ,
            "list": AccessLevel.READ,
            "write": AccessLevel.WRITE,
            "edit": AccessLevel.WRITE,
            "create": AccessLevel.WRITE,
            "delete": AccessLevel.ADMIN,
            "admin": AccessLevel.ADMIN,
            "manage": AccessLevel.ADMIN
        }
        
        return action_levels.get(action.lower(), AccessLevel.READ)
    
    def _has_sufficient_access(self, user_level: AccessLevel, required_level: AccessLevel) -> bool:
        """Check if user access level is sufficient for required level"""
        level_hierarchy = {
            AccessLevel.NONE: 0,
            AccessLevel.READ: 1,
            AccessLevel.WRITE: 2,
            AccessLevel.ADMIN: 3,
            AccessLevel.OWNER: 4
        }
        
        return level_hierarchy.get(user_level, 0) >= level_hierarchy.get(required_level, 0)
    
    def _check_access_rules(self, user: User, project_name: str, action: str, resource: Optional[str]) -> bool:
        """Check access rules for additional permissions"""
        # Sort rules by priority (higher first)
        sorted_rules = sorted(self.access_rules.values(), key=lambda r: r.priority, reverse=True)
        
        for rule in sorted_rules:
            if not rule.enabled:
                continue
            
            # Check if rule applies to this user/project/resource
            if not self._rule_matches(rule, user.username, project_name, resource):
                continue
            
            # Check if action is explicitly denied
            if action in rule.denied_actions:
                return False
            
            # Check if action is explicitly allowed
            if action in rule.allowed_actions:
                return True
        
        return False
    
    def _rule_matches(self, rule: AccessRule, username: str, project_name: str, resource: Optional[str]) -> bool:
        """Check if a rule matches the given context"""
        import fnmatch
        
        # Check user patterns
        if rule.user_patterns:
            if not any(fnmatch.fnmatch(username, pattern) for pattern in rule.user_patterns):
                return False
        
        # Check project patterns
        if rule.project_patterns:
            if not any(fnmatch.fnmatch(project_name, pattern) for pattern in rule.project_patterns):
                return False
        
        # Check resource patterns
        if rule.resource_patterns and resource:
            if not any(fnmatch.fnmatch(resource, pattern) for pattern in rule.resource_patterns):
                return False
        
        # Check time restrictions
        if rule.time_restrictions:
            current_time = datetime.utcnow()
            # Time restriction logic would go here
            pass
        
        return True
    
    def _can_access_secret(self, secret: Secret, user_id: str, project_name: Optional[str]) -> bool:
        """Check if user can access a secret"""
        # Owner can always access
        if secret.owner == user_id:
            return True
        
        # Check if user is in allowed users list
        if user_id in secret.allowed_users:
            return True
        
        # Check if project is in allowed projects list
        if project_name and project_name in secret.allowed_projects:
            return True
        
        # Check if user has admin access to any allowed project
        user = self.users.get(user_id)
        if user:
            for project in secret.allowed_projects:
                if user.project_permissions.get(project) == AccessLevel.ADMIN:
                    return True
        
        return False
    
    def _setup_filesystem_isolation(self, isolation: ProjectIsolation) -> bool:
        """Setup filesystem isolation for project"""
        try:
            # Create isolated directory
            isolation_dir = self.storage_path / "isolated" / isolation.project_name
            isolation_dir.mkdir(parents=True, exist_ok=True)
            
            isolation.isolated_directory = str(isolation_dir)
            
            # Setup allowed/denied paths
            isolation.allowed_paths = [str(isolation_dir)]
            isolation.denied_paths = ["/etc", "/usr", "/var", "/bin", "/sbin"]
            
            logger.debug(f"Setup filesystem isolation for {isolation.project_name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to setup filesystem isolation: {str(e)}")
            return False
    
    def _setup_process_isolation(self, isolation: ProjectIsolation) -> bool:
        """Setup process isolation for project"""
        try:
            # Set resource limits
            isolation.resource_limits = {
                "max_memory": 1024 * 1024 * 1024,  # 1GB
                "max_cpu_time": 3600,  # 1 hour
                "max_processes": 10,
                "max_open_files": 100
            }
            
            logger.debug(f"Setup process isolation for {isolation.project_name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to setup process isolation: {str(e)}")
            return False
    
    def _setup_container_isolation(self, isolation: ProjectIsolation) -> bool:
        """Setup container isolation for project"""
        try:
            # Configure container settings
            isolation.container_image = "python:3.9-slim"
            isolation.container_config = {
                "memory_limit": "1g",
                "cpu_limit": "1.0",
                "network_mode": "none",
                "read_only": True
            }
            
            logger.debug(f"Setup container isolation for {isolation.project_name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to setup container isolation: {str(e)}")
            return False
    
    def _setup_network_isolation(self, isolation: ProjectIsolation) -> bool:
        """Setup network isolation for project"""
        try:
            # Configure network restrictions
            isolation.allowed_hosts = ["127.0.0.1", "localhost"]
            isolation.denied_hosts = ["*"]  # Block all by default
            isolation.allowed_ports = [80, 443, 8080, 8443]
            
            logger.debug(f"Setup network isolation for {isolation.project_name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to setup network isolation: {str(e)}")
            return False
    
    def _log_security_event(
        self,
        action: SecurityAction,
        user_id: str,
        resource: str,
        project_name: Optional[str] = None,
        session_id: Optional[str] = None,
        ip_address: Optional[str] = None,
        success: bool = True,
        error_message: Optional[str] = None,
        additional_data: Optional[Dict[str, Any]] = None
    ):
        """Log a security event"""
        if not self.enable_audit_logging:
            return
        
        log_entry = AuditLogEntry(
            log_id=self._generate_id("log"),
            timestamp=datetime.utcnow(),
            action=action,
            user_id=user_id,
            resource=resource,
            project_name=project_name,
            session_id=session_id,
            ip_address=ip_address,
            success=success,
            error_message=error_message,
            additional_data=additional_data or {}
        )
        
        self.audit_log.append(log_entry)
        
        # Keep audit log size manageable
        if len(self.audit_log) > 10000:
            self.audit_log = self.audit_log[-5000:]  # Keep last 5000 entries
    
    def _get_secrets_by_type(self) -> Dict[str, int]:
        """Get count of secrets by type"""
        type_counts = {}
        for secret in self.secrets.values():
            type_counts[secret.secret_type] = type_counts.get(secret.secret_type, 0) + 1
        return type_counts
    
    def _get_isolation_modes_summary(self) -> Dict[str, int]:
        """Get summary of isolation modes in use"""
        mode_counts = {}
        for isolation in self.project_isolations.values():
            mode = isolation.isolation_mode.value
            mode_counts[mode] = mode_counts.get(mode, 0) + 1
        return mode_counts
    
    def _load_security_data(self):
        """Load security data from storage"""
        try:
            # Load users
            users_file = self.storage_path / "users.json"
            if users_file.exists():
                with open(users_file, 'r') as f:
                    users_data = json.load(f)
                    for user_id, user_dict in users_data.items():
                        # Convert datetime strings
                        for date_field in ['last_login', 'created_at']:
                            if user_dict.get(date_field):
                                user_dict[date_field] = datetime.fromisoformat(user_dict[date_field])
                        # Convert enums
                        user_dict['global_access_level'] = AccessLevel(user_dict['global_access_level'])
                        project_perms = {}
                        for proj, level in user_dict.get('project_permissions', {}).items():
                            project_perms[proj] = AccessLevel(level)
                        user_dict['project_permissions'] = project_perms
                        
                        self.users[user_id] = User(**user_dict)
            
            # Load access rules
            rules_file = self.storage_path / "access_rules.json"
            if rules_file.exists():
                with open(rules_file, 'r') as f:
                    rules_data = json.load(f)
                    for rule_id, rule_dict in rules_data.items():
                        if 'created_at' in rule_dict:
                            rule_dict['created_at'] = datetime.fromisoformat(rule_dict['created_at'])
                        rule_dict['access_level'] = AccessLevel(rule_dict['access_level'])
                        self.access_rules[rule_id] = AccessRule(**rule_dict)
            
            # Load secrets metadata (encrypted values stay encrypted)
            secrets_file = self.storage_path / "secrets.json"
            if secrets_file.exists():
                with open(secrets_file, 'r') as f:
                    secrets_data = json.load(f)
                    for secret_id, secret_dict in secrets_data.items():
                        for date_field in ['created_at', 'last_accessed', 'expires_at']:
                            if secret_dict.get(date_field):
                                secret_dict[date_field] = datetime.fromisoformat(secret_dict[date_field])
                        self.secrets[secret_id] = Secret(**secret_dict)
            
            logger.info(f"Loaded security data: {len(self.users)} users, {len(self.access_rules)} rules, {len(self.secrets)} secrets")
            
        except Exception as e:
            logger.error(f"Failed to load security data: {str(e)}")
    
    def _save_security_data(self):
        """Save security data to storage"""
        try:
            # Save users
            users_data = {}
            for user_id, user in self.users.items():
                user_dict = asdict(user)
                # Convert datetime objects
                for date_field in ['last_login', 'created_at']:
                    if user_dict.get(date_field):
                        user_dict[date_field] = getattr(user, date_field).isoformat()
                # Convert enums
                user_dict['global_access_level'] = user.global_access_level.value
                project_perms = {}
                for proj, level in user.project_permissions.items():
                    project_perms[proj] = level.value
                user_dict['project_permissions'] = project_perms
                
                users_data[user_id] = user_dict
            
            with open(self.storage_path / "users.json", 'w') as f:
                json.dump(users_data, f, indent=2)
            
            # Save access rules
            rules_data = {}
            for rule_id, rule in self.access_rules.items():
                rule_dict = asdict(rule)
                if rule_dict.get('created_at'):
                    rule_dict['created_at'] = rule.created_at.isoformat()
                rule_dict['access_level'] = rule.access_level.value
                rules_data[rule_id] = rule_dict
            
            with open(self.storage_path / "access_rules.json", 'w') as f:
                json.dump(rules_data, f, indent=2)
            
            # Save secrets metadata
            secrets_data = {}
            for secret_id, secret in self.secrets.items():
                secret_dict = asdict(secret)
                for date_field in ['created_at', 'last_accessed', 'expires_at']:
                    if secret_dict.get(date_field) and getattr(secret, date_field):
                        secret_dict[date_field] = getattr(secret, date_field).isoformat()
                secrets_data[secret_id] = secret_dict
            
            with open(self.storage_path / "secrets.json", 'w') as f:
                json.dump(secrets_data, f, indent=2)
            
            logger.debug("Saved security data")
            
        except Exception as e:
            logger.error(f"Failed to save security data: {str(e)}")
    
    async def cleanup_sessions(self):
        """Clean up expired sessions"""
        current_time = datetime.utcnow()
        expired_sessions = []
        
        for session_token, session_data in self.active_sessions.items():
            last_activity = session_data.get("last_activity", session_data["created_at"])
            if current_time - last_activity > timedelta(seconds=self.session_timeout):
                expired_sessions.append(session_token)
        
        for session_token in expired_sessions:
            session_data = self.active_sessions[session_token]
            user_id = session_data["user_id"]
            
            # Remove from user's active sessions
            if user_id in self.users:
                user = self.users[user_id]
                if session_token in user.active_sessions:
                    user.active_sessions.remove(session_token)
            
            # Remove from active sessions
            del self.active_sessions[session_token]
            
            self._log_security_event(
                SecurityAction.LOGOUT,
                user_id,
                f"session:{session_token}",
                session_id=session_token,
                additional_data={"reason": "session_timeout"}
            )
        
        if expired_sessions:
            logger.info(f"Cleaned up {len(expired_sessions)} expired sessions")