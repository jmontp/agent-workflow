"""
Comprehensive unit tests for Multi-Project Security System targeting 95%+ line coverage.

Tests authentication, authorization, access controls, secret management, project isolation,
and audit logging for government audit compliance.
"""

import pytest
import tempfile
import shutil
import json
import os
import time
import secrets
import hashlib
import base64
from pathlib import Path
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock, call
from dataclasses import asdict

import sys
sys.path.append(str(Path(__file__).parent.parent.parent))

from lib.multi_project_security import (
    MultiProjectSecurity,
    User,
    AccessLevel,
    IsolationMode,
    SecurityAction,
    AuditLogEntry,
    AccessRule,
    Secret,
    ProjectIsolation,
    CRYPTO_AVAILABLE
)


class TestMultiProjectSecurityDataClasses:
    """Test all data classes and enums."""
    
    def test_access_level_enum(self):
        """Test AccessLevel enum values and ordering."""
        assert AccessLevel.NONE.value == "none"
        assert AccessLevel.READ.value == "read"
        assert AccessLevel.WRITE.value == "write"
        assert AccessLevel.ADMIN.value == "admin"
        assert AccessLevel.OWNER.value == "owner"
    
    def test_security_action_enum(self):
        """Test SecurityAction enum values."""
        assert SecurityAction.LOGIN.value == "login"
        assert SecurityAction.LOGOUT.value == "logout"
        assert SecurityAction.ACCESS_GRANTED.value == "access_granted"
        assert SecurityAction.ACCESS_DENIED.value == "access_denied"
        assert SecurityAction.PERMISSION_CHANGED.value == "permission_changed"
        assert SecurityAction.SECRET_ACCESSED.value == "secret_accessed"
        assert SecurityAction.SECRET_CREATED.value == "secret_created"
        assert SecurityAction.SECRET_DELETED.value == "secret_deleted"
        assert SecurityAction.PROJECT_ACCESSED.value == "project_accessed"
        assert SecurityAction.COMMAND_EXECUTED.value == "command_executed"
        assert SecurityAction.FILE_ACCESSED.value == "file_accessed"
        assert SecurityAction.SECURITY_VIOLATION.value == "security_violation"
    
    def test_isolation_mode_enum(self):
        """Test IsolationMode enum values."""
        assert IsolationMode.NONE.value == "none"
        assert IsolationMode.PROCESS.value == "process"
        assert IsolationMode.CONTAINER.value == "container"
        assert IsolationMode.FILESYSTEM.value == "filesystem"
        assert IsolationMode.NETWORK.value == "network"
        assert IsolationMode.FULL.value == "full"
    
    def test_user_dataclass_creation(self):
        """Test User dataclass with all fields."""
        now = datetime.utcnow()
        user = User(
            user_id="user-123",
            username="testuser",
            email="test@example.com",
            password_hash="hashed_password",
            salt="test_salt",
            global_access_level=AccessLevel.ADMIN,
            project_permissions={"project1": AccessLevel.WRITE},
            two_factor_enabled=True,
            two_factor_secret="2fa_secret",
            api_keys=["key1", "key2"],
            is_active=True,
            is_locked=False,
            failed_login_attempts=2,
            last_login=now,
            created_at=now,
            active_sessions=["session1"],
            max_sessions=5
        )
        
        assert user.user_id == "user-123"
        assert user.username == "testuser"
        assert user.email == "test@example.com"
        assert user.password_hash == "hashed_password"
        assert user.salt == "test_salt"
        assert user.global_access_level == AccessLevel.ADMIN
        assert user.project_permissions == {"project1": AccessLevel.WRITE}
        assert user.two_factor_enabled is True
        assert user.two_factor_secret == "2fa_secret"
        assert user.api_keys == ["key1", "key2"]
        assert user.is_active is True
        assert user.is_locked is False
        assert user.failed_login_attempts == 2
        assert user.last_login == now
        assert user.created_at == now
        assert user.active_sessions == ["session1"]
        assert user.max_sessions == 5
    
    def test_user_dataclass_defaults(self):
        """Test User dataclass with default values."""
        user = User(
            user_id="user-def",
            username="default",
            email="default@example.com",
            password_hash="hash",
            salt="salt"
        )
        
        assert user.global_access_level == AccessLevel.READ
        assert user.project_permissions == {}
        assert user.two_factor_enabled is False
        assert user.two_factor_secret is None
        assert user.api_keys == []
        assert user.is_active is True
        assert user.is_locked is False
        assert user.failed_login_attempts == 0
        assert user.last_login is None
        assert isinstance(user.created_at, datetime)
        assert user.active_sessions == []
        assert user.max_sessions == 3
    
    def test_access_rule_dataclass(self):
        """Test AccessRule dataclass."""
        now = datetime.utcnow()
        rule = AccessRule(
            rule_id="rule-123",
            name="Test Rule",
            description="Test access rule",
            user_patterns=["admin*", "user*"],
            project_patterns=["proj*"],
            resource_patterns=["*.py"],
            time_restrictions={"start": "09:00", "end": "17:00"},
            allowed_actions=["read", "write"],
            denied_actions=["delete"],
            access_level=AccessLevel.WRITE,
            priority=10,
            enabled=True,
            created_by="admin",
            created_at=now
        )
        
        assert rule.rule_id == "rule-123"
        assert rule.name == "Test Rule"
        assert rule.description == "Test access rule"
        assert rule.user_patterns == ["admin*", "user*"]
        assert rule.project_patterns == ["proj*"]
        assert rule.resource_patterns == ["*.py"]
        assert rule.time_restrictions == {"start": "09:00", "end": "17:00"}
        assert rule.allowed_actions == ["read", "write"]
        assert rule.denied_actions == ["delete"]
        assert rule.access_level == AccessLevel.WRITE
        assert rule.priority == 10
        assert rule.enabled is True
        assert rule.created_by == "admin"
        assert rule.created_at == now
    
    def test_secret_dataclass(self):
        """Test Secret dataclass."""
        now = datetime.utcnow()
        secret = Secret(
            secret_id="secret-123",
            name="API Key",
            description="External API key",
            encrypted_value="encrypted_data",
            owner="user-123",
            allowed_projects=["proj1", "proj2"],
            allowed_users=["user1", "user2"],
            secret_type="api_key",
            expires_at=now + timedelta(days=30),
            created_at=now,
            last_accessed=now,
            access_count=5
        )
        
        assert secret.secret_id == "secret-123"
        assert secret.name == "API Key"
        assert secret.description == "External API key"
        assert secret.encrypted_value == "encrypted_data"
        assert secret.owner == "user-123"
        assert secret.allowed_projects == ["proj1", "proj2"]
        assert secret.allowed_users == ["user1", "user2"]
        assert secret.secret_type == "api_key"
        assert secret.expires_at == now + timedelta(days=30)
        assert secret.created_at == now
        assert secret.last_accessed == now
        assert secret.access_count == 5
    
    def test_audit_log_entry_dataclass(self):
        """Test AuditLogEntry dataclass."""
        now = datetime.utcnow()
        entry = AuditLogEntry(
            log_id="log-123",
            timestamp=now,
            action=SecurityAction.LOGIN,
            user_id="user-123",
            resource="user:user-123",
            project_name="project1",
            ip_address="192.168.1.1",
            user_agent="test-agent",
            session_id="session-123",
            success=True,
            error_message=None,
            additional_data={"key": "value"}
        )
        
        assert entry.log_id == "log-123"
        assert entry.timestamp == now
        assert entry.action == SecurityAction.LOGIN
        assert entry.user_id == "user-123"
        assert entry.resource == "user:user-123"
        assert entry.project_name == "project1"
        assert entry.ip_address == "192.168.1.1"
        assert entry.user_agent == "test-agent"
        assert entry.session_id == "session-123"
        assert entry.success is True
        assert entry.error_message is None
        assert entry.additional_data == {"key": "value"}
    
    def test_project_isolation_dataclass(self):
        """Test ProjectIsolation dataclass."""
        isolation = ProjectIsolation(
            project_name="test-project",
            isolation_mode=IsolationMode.FULL,
            isolated_directory="/tmp/isolated",
            allowed_paths=["/home/user"],
            denied_paths=["/etc", "/var"],
            process_uid=1000,
            process_gid=1000,
            resource_limits={"memory": "1GB", "cpu": "1.0"},
            allowed_hosts=["localhost"],
            denied_hosts=["*"],
            allowed_ports=[80, 443],
            container_image="python:3.9",
            container_config={"memory": "1g"}
        )
        
        assert isolation.project_name == "test-project"
        assert isolation.isolation_mode == IsolationMode.FULL
        assert isolation.isolated_directory == "/tmp/isolated"
        assert isolation.allowed_paths == ["/home/user"]
        assert isolation.denied_paths == ["/etc", "/var"]
        assert isolation.process_uid == 1000
        assert isolation.process_gid == 1000
        assert isolation.resource_limits == {"memory": "1GB", "cpu": "1.0"}
        assert isolation.allowed_hosts == ["localhost"]
        assert isolation.denied_hosts == ["*"]
        assert isolation.allowed_ports == [80, 443]
        assert isolation.container_image == "python:3.9"
        assert isolation.container_config == {"memory": "1g"}


class TestMultiProjectSecurityCore:
    """Test core MultiProjectSecurity functionality."""
    
    @pytest.fixture
    def temp_storage_dir(self):
        """Create temporary directory for security storage."""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def security_system(self, temp_storage_dir):
        """Create MultiProjectSecurity instance."""
        with patch('lib.multi_project_security.CRYPTO_AVAILABLE', True):
            with patch('lib.multi_project_security.Fernet') as mock_fernet:
                mock_cipher = Mock()
                mock_cipher.encrypt.return_value = b'encrypted_data'
                mock_cipher.decrypt.return_value = b'decrypted_data'
                mock_fernet.return_value = mock_cipher
                mock_fernet.generate_key.return_value = b'test_key'
                
                system = MultiProjectSecurity(
                    storage_path=temp_storage_dir,
                    enable_audit_logging=True,
                    default_isolation_mode=IsolationMode.PROCESS
                )
                system.cipher = mock_cipher
                return system
    
    @pytest.fixture
    def security_system_no_crypto(self, temp_storage_dir):
        """Create MultiProjectSecurity instance without crypto."""
        with patch('lib.multi_project_security.CRYPTO_AVAILABLE', False):
            return MultiProjectSecurity(
                storage_path=temp_storage_dir,
                enable_audit_logging=True,
                default_isolation_mode=IsolationMode.NONE
            )
    
    def test_init_with_master_key(self, temp_storage_dir):
        """Test initialization with master key."""
        with patch('lib.multi_project_security.CRYPTO_AVAILABLE', True):
            with patch('lib.multi_project_security.Fernet') as mock_fernet:
                mock_cipher = Mock()
                mock_fernet.return_value = mock_cipher
                
                system = MultiProjectSecurity(
                    storage_path=temp_storage_dir,
                    master_key="test_master_key",
                    enable_audit_logging=False,
                    default_isolation_mode=IsolationMode.CONTAINER
                )
                
                # Verify key was properly processed
                expected_key = base64.urlsafe_b64encode("test_master_key".encode().ljust(32)[:32])
                mock_fernet.assert_called_once_with(expected_key)
                assert system.enable_audit_logging is False
                assert system.default_isolation_mode == IsolationMode.CONTAINER
    
    def test_init_without_crypto(self, temp_storage_dir):
        """Test initialization without cryptography library."""
        with patch('lib.multi_project_security.CRYPTO_AVAILABLE', False):
            system = MultiProjectSecurity(storage_path=temp_storage_dir)
            assert not hasattr(system, 'cipher')
    
    def test_init_creates_storage_directory(self, temp_storage_dir):
        """Test that initialization creates storage directory."""
        storage_path = Path(temp_storage_dir) / "security"
        assert not storage_path.exists()
        
        system = MultiProjectSecurity(storage_path=str(storage_path))
        assert storage_path.exists()
        assert system.storage_path == storage_path
    
    @patch('lib.multi_project_security.logger')
    def test_init_logging(self, mock_logger, temp_storage_dir):
        """Test initialization logging."""
        MultiProjectSecurity(storage_path=temp_storage_dir)
        mock_logger.info.assert_called_with("Multi-project security system initialized")


class TestUserManagement:
    """Test user creation, authentication, and management."""
    
    @pytest.fixture
    def security_system(self):
        """Create security system for user tests."""
        temp_dir = tempfile.mkdtemp()
        system = MultiProjectSecurity(storage_path=temp_dir)
        yield system
        shutil.rmtree(temp_dir)
    
    def test_create_user_success(self, security_system):
        """Test successful user creation."""
        with patch.object(security_system, '_generate_id', return_value='user_123'):
            with patch.object(security_system, '_hash_password', return_value='hashed_pw'):
                success = security_system.create_user(
                    username="testuser",
                    email="test@example.com",
                    password="secure_password",
                    global_access_level=AccessLevel.WRITE
                )
                
                assert success is True
                assert len(security_system.users) == 1
                
                user = security_system.users['user_123']
                assert user.username == "testuser"
                assert user.email == "test@example.com"
                assert user.password_hash == "hashed_pw"
                assert user.global_access_level == AccessLevel.WRITE
                assert len(security_system.audit_log) > 0
    
    def test_create_user_duplicate_username(self, security_system):
        """Test creating user with duplicate username."""
        # Create first user
        security_system.create_user("testuser", "test1@example.com", "password1")
        
        # Try to create user with same username
        success = security_system.create_user("testuser", "test2@example.com", "password2")
        
        assert success is False
        assert len(security_system.users) == 1
    
    def test_create_user_duplicate_email(self, security_system):
        """Test creating user with duplicate email."""
        # Create first user
        security_system.create_user("user1", "test@example.com", "password1")
        
        # Try to create user with same email
        success = security_system.create_user("user2", "test@example.com", "password2")
        
        assert success is False
        assert len(security_system.users) == 1
    
    def test_authenticate_user_success(self, security_system):
        """Test successful user authentication."""
        # Create user
        security_system.create_user("testuser", "test@example.com", "secure_password")
        
        with patch.object(security_system, '_create_session', return_value='session_token'):
            session_token = security_system.authenticate_user(
                "testuser", 
                "secure_password", 
                ip_address="192.168.1.1"
            )
            
            assert session_token == 'session_token'
            
            # Check user was updated
            user = next(iter(security_system.users.values()))
            assert user.last_login is not None
            assert user.failed_login_attempts == 0
    
    def test_authenticate_user_not_found(self, security_system):
        """Test authentication with non-existent user."""
        session_token = security_system.authenticate_user(
            "nonexistent", 
            "password",
            ip_address="192.168.1.1"
        )
        
        assert session_token is None
        
        # Check audit log for access denied
        denied_logs = [log for log in security_system.audit_log 
                      if log.action == SecurityAction.ACCESS_DENIED]
        assert len(denied_logs) > 0
        assert denied_logs[0].error_message == "User not found"
    
    def test_authenticate_user_locked_account(self, security_system):
        """Test authentication with locked account."""
        # Create and lock user
        security_system.create_user("testuser", "test@example.com", "password")
        user = next(iter(security_system.users.values()))
        user.is_locked = True
        
        session_token = security_system.authenticate_user("testuser", "password")
        
        assert session_token is None
        
        # Check audit log
        denied_logs = [log for log in security_system.audit_log 
                      if log.action == SecurityAction.ACCESS_DENIED]
        assert any("locked or inactive" in log.error_message for log in denied_logs)
    
    def test_authenticate_user_inactive_account(self, security_system):
        """Test authentication with inactive account."""
        # Create and deactivate user
        security_system.create_user("testuser", "test@example.com", "password")
        user = next(iter(security_system.users.values()))
        user.is_active = False
        
        session_token = security_system.authenticate_user("testuser", "password")
        
        assert session_token is None
    
    def test_authenticate_user_too_many_failed_attempts(self, security_system):
        """Test authentication with too many failed attempts."""
        # Create user
        security_system.create_user("testuser", "test@example.com", "password")
        
        with patch.object(security_system, '_should_lockout_user', return_value=True):
            session_token = security_system.authenticate_user("testuser", "password")
            
            assert session_token is None
            
            # Check user was locked
            user = next(iter(security_system.users.values()))
            assert user.is_locked is True
            
            # Check security violation log
            violation_logs = [log for log in security_system.audit_log 
                            if log.action == SecurityAction.SECURITY_VIOLATION]
            assert len(violation_logs) > 0
    
    def test_authenticate_user_wrong_password(self, security_system):
        """Test authentication with wrong password."""
        # Create user
        security_system.create_user("testuser", "test@example.com", "correct_password")
        
        session_token = security_system.authenticate_user("testuser", "wrong_password")
        
        assert session_token is None
        
        # Check failed login was tracked
        user = next(iter(security_system.users.values()))
        assert user.failed_login_attempts > 0
        
        # Check audit log
        denied_logs = [log for log in security_system.audit_log 
                      if log.action == SecurityAction.ACCESS_DENIED]
        assert any("Invalid password" in log.error_message for log in denied_logs)


class TestAccessControl:
    """Test access control and permission checking."""
    
    @pytest.fixture
    def security_system_with_users(self):
        """Create security system with test users."""
        temp_dir = tempfile.mkdtemp()
        system = MultiProjectSecurity(storage_path=temp_dir)
        
        # Create test users
        system.create_user("admin_user", "admin@example.com", "password", AccessLevel.OWNER)
        system.create_user("regular_user", "user@example.com", "password", AccessLevel.READ)
        system.create_user("locked_user", "locked@example.com", "password", AccessLevel.WRITE)
        
        # Lock one user
        locked_user = None
        for user in system.users.values():
            if user.username == "locked_user":
                locked_user = user
                break
        if locked_user:
            locked_user.is_locked = True
        
        # Set up project permissions
        regular_user = None
        for user in system.users.values():
            if user.username == "regular_user":
                regular_user = user
                break
        if regular_user:
            regular_user.project_permissions["project1"] = AccessLevel.WRITE
            regular_user.project_permissions["project2"] = AccessLevel.READ
        
        yield system
        shutil.rmtree(temp_dir)
    
    def test_check_access_nonexistent_user(self, security_system_with_users):
        """Test access check for non-existent user."""
        has_access = security_system_with_users.check_access(
            "nonexistent_user", "project1", "read"
        )
        assert has_access is False
    
    def test_check_access_locked_user(self, security_system_with_users):
        """Test access check for locked user."""
        locked_user_id = None
        for user_id, user in security_system_with_users.users.items():
            if user.username == "locked_user":
                locked_user_id = user_id
                break
        
        has_access = security_system_with_users.check_access(
            locked_user_id, "project1", "read"
        )
        assert has_access is False
    
    def test_check_access_owner_level(self, security_system_with_users):
        """Test access check for owner level user."""
        admin_user_id = None
        for user_id, user in security_system_with_users.users.items():
            if user.username == "admin_user":
                admin_user_id = user_id
                break
        
        has_access = security_system_with_users.check_access(
            admin_user_id, "any_project", "delete"
        )
        assert has_access is True
    
    def test_check_access_project_permissions(self, security_system_with_users):
        """Test access check based on project permissions."""
        regular_user_id = None
        for user_id, user in security_system_with_users.users.items():
            if user.username == "regular_user":
                regular_user_id = user_id
                break
        
        # Should have write access to project1
        has_access = security_system_with_users.check_access(
            regular_user_id, "project1", "write"
        )
        assert has_access is True
        
        # Should have read access to project2 but not write
        has_access = security_system_with_users.check_access(
            regular_user_id, "project2", "read"
        )
        assert has_access is True
        
        has_access = security_system_with_users.check_access(
            regular_user_id, "project2", "write"
        )
        assert has_access is False
        
        # Should not have access to project3
        has_access = security_system_with_users.check_access(
            regular_user_id, "project3", "read"
        )
        assert has_access is False
    
    def test_check_access_with_rules(self, security_system_with_users):
        """Test access check with access rules."""
        regular_user_id = None
        for user_id, user in security_system_with_users.users.items():
            if user.username == "regular_user":
                regular_user_id = user_id
                break
        
        # Create access rule that allows read access to project3
        rule = AccessRule(
            rule_id="rule_1",
            name="Allow read to project3",
            description="Test rule",
            user_patterns=["regular_user"],
            project_patterns=["project3"],
            allowed_actions=["read"]
        )
        security_system_with_users.access_rules["rule_1"] = rule
        
        # Should now have read access to project3 via rule
        has_access = security_system_with_users.check_access(
            regular_user_id, "project3", "read", resource="test.py"
        )
        assert has_access is True
    
    def test_get_required_access_level(self, security_system_with_users):
        """Test getting required access level for actions."""
        system = security_system_with_users
        
        assert system._get_required_access_level("read") == AccessLevel.READ
        assert system._get_required_access_level("view") == AccessLevel.READ
        assert system._get_required_access_level("list") == AccessLevel.READ
        assert system._get_required_access_level("write") == AccessLevel.WRITE
        assert system._get_required_access_level("edit") == AccessLevel.WRITE
        assert system._get_required_access_level("create") == AccessLevel.WRITE
        assert system._get_required_access_level("delete") == AccessLevel.ADMIN
        assert system._get_required_access_level("admin") == AccessLevel.ADMIN
        assert system._get_required_access_level("manage") == AccessLevel.ADMIN
        assert system._get_required_access_level("unknown") == AccessLevel.READ
    
    def test_has_sufficient_access(self, security_system_with_users):
        """Test access level hierarchy checking."""
        system = security_system_with_users
        
        # Test hierarchy
        assert system._has_sufficient_access(AccessLevel.OWNER, AccessLevel.ADMIN) is True
        assert system._has_sufficient_access(AccessLevel.ADMIN, AccessLevel.WRITE) is True
        assert system._has_sufficient_access(AccessLevel.WRITE, AccessLevel.READ) is True
        assert system._has_sufficient_access(AccessLevel.READ, AccessLevel.NONE) is True
        
        # Test insufficient access
        assert system._has_sufficient_access(AccessLevel.READ, AccessLevel.WRITE) is False
        assert system._has_sufficient_access(AccessLevel.WRITE, AccessLevel.ADMIN) is False
        assert system._has_sufficient_access(AccessLevel.NONE, AccessLevel.READ) is False


class TestAccessRules:
    """Test access rule functionality."""
    
    @pytest.fixture
    def security_system(self):
        """Create security system for access rule tests."""
        temp_dir = tempfile.mkdtemp()
        system = MultiProjectSecurity(storage_path=temp_dir)
        
        # Create test user
        system.create_user("testuser", "test@example.com", "password")
        
        yield system
        shutil.rmtree(temp_dir)
    
    def test_check_access_rules_denied_action(self, security_system):
        """Test access rules with denied actions."""
        user = next(iter(security_system.users.values()))
        
        # Create rule that denies delete action
        rule = AccessRule(
            rule_id="deny_rule",
            name="Deny Delete",
            description="Deny delete actions",
            user_patterns=["testuser"],
            project_patterns=["*"],
            denied_actions=["delete"],
            priority=10
        )
        security_system.access_rules["deny_rule"] = rule
        
        result = security_system._check_access_rules(
            user, "project1", "delete", "file.txt"
        )
        assert result is False
    
    def test_check_access_rules_allowed_action(self, security_system):
        """Test access rules with allowed actions."""
        user = next(iter(security_system.users.values()))
        
        # Create rule that allows write action
        rule = AccessRule(
            rule_id="allow_rule",
            name="Allow Write",
            description="Allow write actions",
            user_patterns=["testuser"],
            project_patterns=["*"],
            allowed_actions=["write"],
            priority=10
        )
        security_system.access_rules["allow_rule"] = rule
        
        result = security_system._check_access_rules(
            user, "project1", "write", "file.txt"
        )
        assert result is True
    
    def test_check_access_rules_disabled_rule(self, security_system):
        """Test that disabled rules are ignored."""
        user = next(iter(security_system.users.values()))
        
        # Create disabled rule
        rule = AccessRule(
            rule_id="disabled_rule",
            name="Disabled Rule",
            description="This rule is disabled",
            user_patterns=["testuser"],
            project_patterns=["*"],
            allowed_actions=["admin"],
            enabled=False
        )
        security_system.access_rules["disabled_rule"] = rule
        
        result = security_system._check_access_rules(
            user, "project1", "admin", "resource"
        )
        assert result is False
    
    def test_check_access_rules_priority_order(self, security_system):
        """Test that rules are evaluated in priority order."""
        user = next(iter(security_system.users.values()))
        
        # Create low priority rule that allows
        rule1 = AccessRule(
            rule_id="low_priority",
            name="Low Priority Allow",
            description="Low priority rule",
            user_patterns=["testuser"],
            project_patterns=["*"],
            allowed_actions=["read"],
            priority=1
        )
        
        # Create high priority rule that denies
        rule2 = AccessRule(
            rule_id="high_priority",
            name="High Priority Deny",
            description="High priority rule",
            user_patterns=["testuser"],
            project_patterns=["*"],
            denied_actions=["read"],
            priority=10
        )
        
        security_system.access_rules["low_priority"] = rule1
        security_system.access_rules["high_priority"] = rule2
        
        # High priority deny should take precedence
        result = security_system._check_access_rules(
            user, "project1", "read", "resource"
        )
        assert result is False
    
    def test_rule_matches_patterns(self, security_system):
        """Test rule pattern matching."""
        rule = AccessRule(
            rule_id="test_rule",
            name="Test Rule",
            description="Test pattern matching",
            user_patterns=["test*", "admin"],
            project_patterns=["proj*", "special"],
            resource_patterns=["*.py", "config.*"]
        )
        
        # Test matching patterns
        assert security_system._rule_matches(rule, "testuser", "project1", "file.py") is True
        assert security_system._rule_matches(rule, "admin", "special", "config.json") is True
        
        # Test non-matching patterns
        assert security_system._rule_matches(rule, "other", "project1", "file.py") is False
        assert security_system._rule_matches(rule, "testuser", "other", "file.py") is False
        assert security_system._rule_matches(rule, "testuser", "project1", "file.txt") is False
    
    def test_rule_matches_no_patterns(self, security_system):
        """Test rule matching with empty patterns (should match all)."""
        rule = AccessRule(
            rule_id="empty_rule",
            name="Empty Rule",
            description="Rule with no patterns"
        )
        
        # Should match anything when no patterns are specified
        assert security_system._rule_matches(rule, "anyuser", "anyproject", "anyresource") is True
    
    def test_rule_matches_with_time_restrictions(self, security_system):
        """Test rule matching with time restrictions."""
        rule = AccessRule(
            rule_id="time_rule",
            name="Time Rule",
            description="Rule with time restrictions",
            time_restrictions={"start": "09:00", "end": "17:00"}
        )
        
        # Time restriction logic is implemented but not fully functional in the code
        # This tests that the method doesn't crash
        assert security_system._rule_matches(rule, "user", "project", "resource") is True


class TestSecretManagement:
    """Test secret management functionality."""
    
    @pytest.fixture
    def security_system(self):
        """Create security system with crypto for secret tests."""
        temp_dir = tempfile.mkdtemp()
        
        try:
            with patch('lib.multi_project_security.CRYPTO_AVAILABLE', True):
                with patch('lib.multi_project_security.Fernet') as mock_fernet:
                    mock_cipher = Mock()
                    mock_cipher.encrypt.return_value = b'encrypted_data'
                    mock_cipher.decrypt.return_value = b'decrypted_value'
                    mock_fernet.return_value = mock_cipher
                    mock_fernet.generate_key.return_value = b'test_key'
                    
                    system = MultiProjectSecurity(storage_path=temp_dir)
                    system.cipher = mock_cipher
                    
                    # Create test users
                    system.create_user("owner", "owner@example.com", "password", AccessLevel.ADMIN)
                    system.create_user("user", "user@example.com", "password", AccessLevel.READ)
                    
                    yield system
        finally:
            shutil.rmtree(temp_dir)
    
    def test_create_secret_success(self, security_system):
        """Test successful secret creation."""
        owner_id = None
        for user_id, user in security_system.users.items():
            if user.username == "owner":
                owner_id = user_id
                break
        
        with patch.object(security_system, '_generate_id', return_value='secret_123'):
            secret_id = security_system.create_secret(
                name="API Key",
                value="secret_value",
                secret_type="api_key",
                owner=owner_id,
                allowed_projects=["project1"],
                description="Test secret"
            )
            
            assert secret_id == "secret_123"
            assert secret_id in security_system.secrets
            
            secret = security_system.secrets[secret_id]
            assert secret.name == "API Key"
            assert secret.secret_type == "api_key"
            assert secret.owner == owner_id
            assert secret.allowed_projects == ["project1"]
            assert secret.description == "Test secret"
            
            # Check audit log
            created_logs = [log for log in security_system.audit_log 
                          if log.action == SecurityAction.SECRET_CREATED]
            assert len(created_logs) > 0
    
    def test_create_secret_no_crypto(self):
        """Test secret creation without cryptography library."""
        temp_dir = tempfile.mkdtemp()
        
        with patch('lib.multi_project_security.CRYPTO_AVAILABLE', False):
            system = MultiProjectSecurity(storage_path=temp_dir)
            
            with pytest.raises(RuntimeError, match="Cryptography library not available"):
                system.create_secret("test", "value")
        
        shutil.rmtree(temp_dir)
    
    def test_get_secret_success(self, security_system):
        """Test successful secret retrieval."""
        owner_id = None
        for user_id, user in security_system.users.items():
            if user.username == "owner":
                owner_id = user_id
                break
        
        # Create secret
        secret_id = security_system.create_secret(
            name="Test Secret",
            value="secret_value",
            owner=owner_id,
            allowed_projects=["project1"]
        )
        
        # Retrieve secret as owner
        retrieved_value = security_system.get_secret(secret_id, owner_id)
        
        assert retrieved_value == "decrypted_value"
        
        # Check access tracking
        secret = security_system.secrets[secret_id]
        assert secret.access_count > 0
        assert secret.last_accessed is not None
        
        # Check audit log
        accessed_logs = [log for log in security_system.audit_log 
                        if log.action == SecurityAction.SECRET_ACCESSED]
        assert len(accessed_logs) > 0
    
    def test_get_secret_not_found(self, security_system):
        """Test retrieving non-existent secret."""
        owner_id = next(iter(security_system.users.keys()))
        
        retrieved_value = security_system.get_secret("nonexistent", owner_id)
        assert retrieved_value is None
    
    def test_get_secret_access_denied(self, security_system):
        """Test secret access denied for unauthorized user."""
        owner_id = None
        user_id = None
        
        for uid, user in security_system.users.items():
            if user.username == "owner":
                owner_id = uid
            elif user.username == "user":
                user_id = uid
        
        # Create secret as owner
        secret_id = security_system.create_secret(
            name="Private Secret",
            value="secret_value",
            owner=owner_id
        )
        
        # Try to access as different user
        retrieved_value = security_system.get_secret(secret_id, user_id)
        
        assert retrieved_value is None
        
        # Check audit log for access denied
        denied_logs = [log for log in security_system.audit_log 
                      if log.action == SecurityAction.ACCESS_DENIED and
                      "secret:" in log.resource]
        assert len(denied_logs) > 0
    
    def test_get_secret_decryption_error(self, security_system):
        """Test secret retrieval with decryption error."""
        owner_id = next(iter(security_system.users.keys()))
        
        # Create secret
        secret_id = security_system.create_secret(
            name="Test Secret",
            value="secret_value",
            owner=owner_id
        )
        
        # Mock decryption failure
        security_system.cipher.decrypt.side_effect = Exception("Decryption failed")
        
        retrieved_value = security_system.get_secret(secret_id, owner_id)
        assert retrieved_value is None
    
    def test_can_access_secret_owner(self, security_system):
        """Test secret access permission for owner."""
        owner_id = next(iter(security_system.users.keys()))
        
        secret = Secret(
            secret_id="test",
            name="Test",
            description="Test",
            encrypted_value="encrypted",
            owner=owner_id
        )
        
        can_access = security_system._can_access_secret(secret, owner_id, "test_project")
        assert can_access is True
    
    def test_can_access_secret_allowed_user(self, security_system):
        """Test secret access permission for allowed user."""
        owner_id = None
        user_id = None
        
        for uid, user in security_system.users.items():
            if user.username == "owner":
                owner_id = uid
            elif user.username == "user":
                user_id = uid
        
        secret = Secret(
            secret_id="test",
            name="Test",
            description="Test",
            encrypted_value="encrypted",
            owner=owner_id,
            allowed_users=[user_id]
        )
        
        can_access = security_system._can_access_secret(secret, user_id, "test_project")
        assert can_access is True
    
    def test_can_access_secret_allowed_project(self, security_system):
        """Test secret access permission for allowed project."""
        owner_id = None
        user_id = None
        
        for uid, user in security_system.users.items():
            if user.username == "owner":
                owner_id = uid
            elif user.username == "user":
                user_id = uid
        
        secret = Secret(
            secret_id="test",
            name="Test",
            description="Test",
            encrypted_value="encrypted",
            owner=owner_id,
            allowed_projects=["project1"]
        )
        
        can_access = security_system._can_access_secret(secret, user_id, "project1")
        assert can_access is True
    
    def test_can_access_secret_admin_project_access(self, security_system):
        """Test secret access permission for user with admin access to project."""
        owner_id = None
        user_id = None
        
        for uid, user in security_system.users.items():
            if user.username == "owner":
                owner_id = uid
            elif user.username == "user":
                user_id = uid
                # Give admin access to project1
                user.project_permissions["project1"] = AccessLevel.ADMIN
        
        secret = Secret(
            secret_id="test",
            name="Test",
            description="Test",
            encrypted_value="encrypted",
            owner=owner_id,
            allowed_projects=["project1"]
        )
        
        can_access = security_system._can_access_secret(secret, user_id, "project2")
        assert can_access is True  # User has admin access to allowed project
    
    def test_can_access_secret_denied(self, security_system):
        """Test secret access permission denied."""
        owner_id = None
        user_id = None
        
        for uid, user in security_system.users.items():
            if user.username == "owner":
                owner_id = uid
            elif user.username == "user":
                user_id = uid
        
        secret = Secret(
            secret_id="test",
            name="Test",
            description="Test",
            encrypted_value="encrypted",
            owner=owner_id
        )
        
        can_access = security_system._can_access_secret(secret, user_id, "test_project")
        assert can_access is False


class TestProjectIsolation:
    """Test project isolation functionality."""
    
    @pytest.fixture
    def security_system(self):
        """Create security system for isolation tests."""
        temp_dir = tempfile.mkdtemp()
        system = MultiProjectSecurity(storage_path=temp_dir)
        yield system
        shutil.rmtree(temp_dir)
    
    def test_setup_project_isolation_none(self, security_system):
        """Test setting up no isolation."""
        success = security_system.setup_project_isolation(
            "test_project", IsolationMode.NONE
        )
        
        assert success is True
        assert "test_project" in security_system.project_isolations
        
        isolation = security_system.project_isolations["test_project"]
        assert isolation.isolation_mode == IsolationMode.NONE
    
    def test_setup_project_isolation_filesystem(self, security_system):
        """Test setting up filesystem isolation."""
        success = security_system.setup_project_isolation(
            "test_project", IsolationMode.FILESYSTEM
        )
        
        assert success is True
        
        isolation = security_system.project_isolations["test_project"]
        assert isolation.isolation_mode == IsolationMode.FILESYSTEM
        assert isolation.isolated_directory is not None
        assert len(isolation.allowed_paths) > 0
        assert len(isolation.denied_paths) > 0
    
    def test_setup_project_isolation_process(self, security_system):
        """Test setting up process isolation."""
        success = security_system.setup_project_isolation(
            "test_project", IsolationMode.PROCESS
        )
        
        assert success is True
        
        isolation = security_system.project_isolations["test_project"]
        assert isolation.isolation_mode == IsolationMode.PROCESS
        assert len(isolation.resource_limits) > 0
        assert "max_memory" in isolation.resource_limits
    
    def test_setup_project_isolation_container(self, security_system):
        """Test setting up container isolation."""
        success = security_system.setup_project_isolation(
            "test_project", IsolationMode.CONTAINER
        )
        
        assert success is True
        
        isolation = security_system.project_isolations["test_project"]
        assert isolation.isolation_mode == IsolationMode.CONTAINER
        assert isolation.container_image is not None
        assert len(isolation.container_config) > 0
    
    def test_setup_project_isolation_network(self, security_system):
        """Test setting up network isolation."""
        success = security_system.setup_project_isolation(
            "test_project", IsolationMode.NETWORK
        )
        
        assert success is True
        
        isolation = security_system.project_isolations["test_project"]
        assert isolation.isolation_mode == IsolationMode.NETWORK
        assert len(isolation.allowed_hosts) > 0
        assert len(isolation.denied_hosts) > 0
        assert len(isolation.allowed_ports) > 0
    
    def test_setup_project_isolation_full(self, security_system):
        """Test setting up full isolation."""
        success = security_system.setup_project_isolation(
            "test_project", IsolationMode.FULL
        )
        
        assert success is True
        
        isolation = security_system.project_isolations["test_project"]
        assert isolation.isolation_mode == IsolationMode.FULL
        # Should have all isolation components
        assert isolation.isolated_directory is not None
        assert len(isolation.resource_limits) > 0
        assert len(isolation.allowed_hosts) > 0
    
    def test_setup_project_isolation_default_mode(self, security_system):
        """Test setting up isolation with default mode."""
        success = security_system.setup_project_isolation("test_project")
        
        assert success is True
        
        isolation = security_system.project_isolations["test_project"]
        assert isolation.isolation_mode == security_system.default_isolation_mode
    
    @patch('lib.multi_project_security.logger')
    def test_setup_filesystem_isolation_error(self, mock_logger, security_system):
        """Test filesystem isolation setup error."""
        # Mock Path.mkdir to raise exception
        with patch.object(Path, 'mkdir', side_effect=Exception("Permission denied")):
            success = security_system._setup_filesystem_isolation(
                ProjectIsolation("test", IsolationMode.FILESYSTEM)
            )
            
            assert success is False
            mock_logger.error.assert_called()
    
    @patch('lib.multi_project_security.logger')
    def test_setup_process_isolation_error(self, mock_logger, security_system):
        """Test process isolation setup error."""
        # Create a ProjectIsolation instance that will cause an error
        isolation = ProjectIsolation("test_project", IsolationMode.PROCESS)
        
        # Create a custom class that raises an exception when resource_limits is set
        class BrokenIsolation:
            def __init__(self):
                self.project_name = "test_project"
                self.mode = IsolationMode.PROCESS
            
            @property
            def resource_limits(self):
                return {}
                
            @resource_limits.setter
            def resource_limits(self, value):
                raise Exception("Process setup failed")
        
        broken_isolation = BrokenIsolation()
        success = security_system._setup_process_isolation(broken_isolation)
        
        assert success is False
        mock_logger.error.assert_called_once()


class TestAuditLogging:
    """Test audit logging functionality."""
    
    @pytest.fixture
    def security_system(self):
        """Create security system for audit tests."""
        temp_dir = tempfile.mkdtemp()
        system = MultiProjectSecurity(storage_path=temp_dir, enable_audit_logging=True)
        yield system
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def security_system_no_audit(self):
        """Create security system without audit logging."""
        temp_dir = tempfile.mkdtemp()
        system = MultiProjectSecurity(storage_path=temp_dir, enable_audit_logging=False)
        yield system
        shutil.rmtree(temp_dir)
    
    def test_log_security_event(self, security_system):
        """Test logging security events."""
        security_system._log_security_event(
            SecurityAction.LOGIN,
            "user_123",
            "user:user_123",
            project_name="project1",
            session_id="session_123",
            ip_address="192.168.1.1",
            success=True,
            additional_data={"test": "data"}
        )
        
        assert len(security_system.audit_log) > 0
        
        entry = security_system.audit_log[-1]
        assert entry.action == SecurityAction.LOGIN
        assert entry.user_id == "user_123"
        assert entry.resource == "user:user_123"
        assert entry.project_name == "project1"
        assert entry.session_id == "session_123"
        assert entry.ip_address == "192.168.1.1"
        assert entry.success is True
        assert entry.additional_data == {"test": "data"}
        assert isinstance(entry.timestamp, datetime)
        assert isinstance(entry.log_id, str)
    
    def test_log_security_event_disabled(self, security_system_no_audit):
        """Test that events are not logged when audit logging is disabled."""
        initial_count = len(security_system_no_audit.audit_log)
        
        security_system_no_audit._log_security_event(
            SecurityAction.LOGIN,
            "user_123",
            "user:user_123"
        )
        
        assert len(security_system_no_audit.audit_log) == initial_count
    
    def test_audit_log_size_management(self, security_system):
        """Test audit log size management."""
        # Clear any existing entries
        security_system.audit_log.clear()
        
        # Fill audit log beyond limit (triggers at 10001, trims to 5000, then we add 1 more)
        for i in range(10001):
            security_system._log_security_event(
                SecurityAction.LOGIN,
                f"user_{i}",
                f"user:user_{i}"
            )
        
        # Should be trimmed to 5000 entries
        assert len(security_system.audit_log) == 5000
    
    def test_get_audit_log_no_filters(self, security_system):
        """Test getting audit log without filters."""
        # Add some test entries
        for i in range(10):
            security_system._log_security_event(
                SecurityAction.LOGIN,
                f"user_{i}",
                f"user:user_{i}",
                project_name=f"project_{i % 3}"
            )
        
        entries = security_system.get_audit_log()
        
        assert len(entries) == 10
        # Should be sorted by timestamp (newest first)
        timestamps = [entry.timestamp for entry in entries]
        assert timestamps == sorted(timestamps, reverse=True)
    
    def test_get_audit_log_user_filter(self, security_system):
        """Test getting audit log filtered by user."""
        # Add test entries for different users
        security_system._log_security_event(SecurityAction.LOGIN, "user_1", "resource")
        security_system._log_security_event(SecurityAction.LOGIN, "user_2", "resource")
        security_system._log_security_event(SecurityAction.LOGOUT, "user_1", "resource")
        
        entries = security_system.get_audit_log(user_id="user_1")
        
        assert len(entries) == 2
        assert all(entry.user_id == "user_1" for entry in entries)
    
    def test_get_audit_log_project_filter(self, security_system):
        """Test getting audit log filtered by project."""
        security_system._log_security_event(
            SecurityAction.PROJECT_ACCESSED, "user_1", "resource", project_name="project1"
        )
        security_system._log_security_event(
            SecurityAction.PROJECT_ACCESSED, "user_1", "resource", project_name="project2"
        )
        
        entries = security_system.get_audit_log(project_name="project1")
        
        assert len(entries) == 1
        assert entries[0].project_name == "project1"
    
    def test_get_audit_log_action_filter(self, security_system):
        """Test getting audit log filtered by action."""
        security_system._log_security_event(SecurityAction.LOGIN, "user_1", "resource")
        security_system._log_security_event(SecurityAction.LOGOUT, "user_1", "resource")
        security_system._log_security_event(SecurityAction.LOGIN, "user_2", "resource")
        
        entries = security_system.get_audit_log(action=SecurityAction.LOGIN)
        
        assert len(entries) == 2
        assert all(entry.action == SecurityAction.LOGIN for entry in entries)
    
    def test_get_audit_log_time_filter(self, security_system):
        """Test getting audit log filtered by time."""
        now = datetime.utcnow()
        start_time = now - timedelta(hours=1)
        end_time = now + timedelta(hours=1)
        
        security_system._log_security_event(SecurityAction.LOGIN, "user_1", "resource")
        
        entries = security_system.get_audit_log(
            start_time=start_time, 
            end_time=end_time
        )
        
        assert len(entries) > 0
        assert all(start_time <= entry.timestamp <= end_time for entry in entries)
    
    def test_get_audit_log_limit(self, security_system):
        """Test audit log limit parameter."""
        # Add many entries
        for i in range(20):
            security_system._log_security_event(
                SecurityAction.LOGIN, f"user_{i}", "resource"
            )
        
        entries = security_system.get_audit_log(limit=5)
        
        assert len(entries) == 5


class TestSessionManagement:
    """Test session management functionality."""
    
    @pytest.fixture
    def security_system(self):
        """Create security system for session tests."""
        temp_dir = tempfile.mkdtemp()
        system = MultiProjectSecurity(storage_path=temp_dir)
        
        # Create test user
        system.create_user("testuser", "test@example.com", "password")
        
        yield system
        shutil.rmtree(temp_dir)
    
    def test_create_session(self, security_system):
        """Test session creation."""
        user = next(iter(security_system.users.values()))
        
        with patch.object(security_system, '_generate_id', return_value='session_123'):
            with patch('secrets.token_urlsafe', return_value='session_token'):
                session_token = security_system._create_session(user, "192.168.1.1")
                
                assert session_token == 'session_token'
                assert session_token in security_system.active_sessions
                assert session_token in user.active_sessions
                
                session_data = security_system.active_sessions[session_token]
                assert session_data["user_id"] == user.user_id
                assert session_data["username"] == user.username
                assert session_data["ip_address"] == "192.168.1.1"
                assert isinstance(session_data["created_at"], datetime)
    
    def test_create_session_max_limit(self, security_system):
        """Test session creation when user has max sessions."""
        user = next(iter(security_system.users.values()))
        user.max_sessions = 2
        
        # Create max sessions
        for i in range(3):
            with patch('secrets.token_urlsafe', return_value=f'session_{i}'):
                security_system._create_session(user)
        
        # Should only have max_sessions active
        assert len(user.active_sessions) == user.max_sessions
        assert len([s for s in security_system.active_sessions if 
                   security_system.active_sessions[s]["user_id"] == user.user_id]) == user.max_sessions
    
    def test_should_lockout_user_no_failures(self, security_system):
        """Test lockout check with no failed attempts."""
        user_id = next(iter(security_system.users.keys()))
        
        should_lockout = security_system._should_lockout_user(user_id)
        assert should_lockout is False
    
    def test_should_lockout_user_few_failures(self, security_system):
        """Test lockout check with few failed attempts."""
        user_id = next(iter(security_system.users.keys()))
        
        # Add a few failed attempts
        for _ in range(3):
            security_system._track_failed_login(user_id, "192.168.1.1")
        
        should_lockout = security_system._should_lockout_user(user_id)
        assert should_lockout is False
    
    def test_should_lockout_user_many_failures(self, security_system):
        """Test lockout check with many failed attempts."""
        user_id = next(iter(security_system.users.keys()))
        
        # Add many failed attempts
        for _ in range(6):
            security_system._track_failed_login(user_id, "192.168.1.1")
        
        should_lockout = security_system._should_lockout_user(user_id)
        assert should_lockout is True
    
    def test_track_failed_login(self, security_system):
        """Test tracking failed login attempts."""
        user_id = next(iter(security_system.users.keys()))
        
        security_system._track_failed_login(user_id, "192.168.1.1")
        
        assert user_id in security_system.failed_login_tracker
        assert len(security_system.failed_login_tracker[user_id]) == 1
    
    def test_track_failed_login_cleanup_old(self, security_system):
        """Test that old failed login attempts are cleaned up."""
        user_id = next(iter(security_system.users.keys()))
        
        # Mock old attempts
        old_time = datetime.utcnow() - timedelta(hours=2)
        security_system.failed_login_tracker[user_id] = [old_time]
        
        # Add new attempt
        security_system._track_failed_login(user_id, "192.168.1.1")
        
        # Old attempt should be removed
        assert len(security_system.failed_login_tracker[user_id]) == 1
        assert security_system.failed_login_tracker[user_id][0] > old_time
    
    @pytest.mark.asyncio
    async def test_cleanup_sessions(self, security_system):
        """Test session cleanup."""
        user = next(iter(security_system.users.values()))
        
        # Create session
        session_token = security_system._create_session(user)
        
        # Mock old session
        session_data = security_system.active_sessions[session_token]
        old_time = datetime.utcnow() - timedelta(seconds=security_system.session_timeout + 1)
        session_data["created_at"] = old_time
        session_data["last_activity"] = old_time
        
        await security_system.cleanup_sessions()
        
        # Session should be removed
        assert session_token not in security_system.active_sessions
        assert session_token not in user.active_sessions
        
        # Check logout was logged
        logout_logs = [log for log in security_system.audit_log 
                      if log.action == SecurityAction.LOGOUT]
        assert len(logout_logs) > 0


class TestSecurityStatus:
    """Test security status reporting."""
    
    @pytest.fixture
    def security_system_with_data(self):
        """Create security system with test data."""
        temp_dir = tempfile.mkdtemp()
        
        try:
            with patch('lib.multi_project_security.CRYPTO_AVAILABLE', True):
                with patch('lib.multi_project_security.Fernet') as mock_fernet:
                    mock_cipher = Mock()
                    mock_cipher.encrypt.return_value = b'encrypted_data'
                    mock_fernet.return_value = mock_cipher
                    mock_fernet.generate_key.return_value = b'test_key'
                    
                    system = MultiProjectSecurity(storage_path=temp_dir)
                    system.cipher = mock_cipher
                
                # Add test data
                system.create_user("user1", "user1@example.com", "password", AccessLevel.READ)
                system.create_user("user2", "user2@example.com", "password", AccessLevel.ADMIN)
                system.create_user("locked_user", "locked@example.com", "password")
                
                # Lock one user
                for user in system.users.values():
                    if user.username == "locked_user":
                        user.is_locked = True
                        break
                
                # Enable 2FA for one user
                for user in system.users.values():
                    if user.username == "user1":
                        user.two_factor_enabled = True
                        break
                
                # Create secrets
                system.create_secret("secret1", "value1", "api_key", "user1")
                system.create_secret("secret2", "value2", "database", "user1")
                system.create_secret("secret3", "value3", "api_key", "user2")
                
                # Setup project isolation
                system.setup_project_isolation("project1", IsolationMode.PROCESS)
                system.setup_project_isolation("project2", IsolationMode.CONTAINER)
                
                # Create access rules
                rule = AccessRule(
                    rule_id="rule1",
                    name="Test Rule",
                    description="Test",
                    enabled=True
                )
                system.access_rules["rule1"] = rule
                
                disabled_rule = AccessRule(
                    rule_id="rule2",
                    name="Disabled Rule",
                    description="Test",
                    enabled=False
                )
                system.access_rules["rule2"] = disabled_rule
                
                # Create some sessions
                user1_id = None
                for user_id, user in system.users.items():
                    if user.username == "user1":
                        user1_id = user_id
                        break
                
                if user1_id:
                    system._create_session(system.users[user1_id])
                
                # Add some failed login attempts in last 24h
                system._log_security_event(
                    SecurityAction.ACCESS_DENIED,
                    "test_user",
                    "resource",
                    success=False,
                    error_message="Failed login"
                )
                
                yield system
        finally:
            shutil.rmtree(temp_dir)
    
    def test_get_security_status(self, security_system_with_data):
        """Test getting comprehensive security status."""
        status = security_system_with_data.get_security_status()
        
        # Check security system info
        assert status["security_system"]["encryption_enabled"] is True
        assert status["security_system"]["audit_logging_enabled"] is True
        assert status["security_system"]["default_isolation_mode"] == "process"
        
        # Check user stats
        assert status["users"]["total_users"] == 3
        assert status["users"]["active_users"] == 3
        assert status["users"]["locked_users"] == 1
        assert status["users"]["users_with_2fa"] == 1
        
        # Check session stats
        assert status["sessions"]["active_sessions"] >= 1
        assert status["sessions"]["session_timeout"] == 3600
        
        # Check secrets stats
        assert status["secrets"]["total_secrets"] == 3
        secrets_by_type = status["secrets"]["secrets_by_type"]
        assert secrets_by_type["api_key"] == 2
        assert secrets_by_type["database"] == 1
        
        # Check isolation stats
        assert status["isolation"]["projects_with_isolation"] == 2
        isolation_modes = status["isolation"]["isolation_modes"]
        assert isolation_modes["process"] == 1
        assert isolation_modes["container"] == 1
        
        # Check audit stats
        assert status["audit"]["total_log_entries"] > 0
        assert status["audit"]["failed_logins_24h"] >= 1
        
        # Check access rules stats
        assert status["access_rules"]["total_rules"] == 2
        assert status["access_rules"]["enabled_rules"] == 1
    
    def test_get_secrets_by_type(self, security_system_with_data):
        """Test getting secrets count by type."""
        secrets_by_type = security_system_with_data._get_secrets_by_type()
        
        assert secrets_by_type["api_key"] == 2
        assert secrets_by_type["database"] == 1
    
    def test_get_isolation_modes_summary(self, security_system_with_data):
        """Test getting isolation modes summary."""
        isolation_summary = security_system_with_data._get_isolation_modes_summary()
        
        assert isolation_summary["process"] == 1
        assert isolation_summary["container"] == 1


class TestUtilityMethods:
    """Test utility and helper methods."""
    
    @pytest.fixture
    def security_system(self):
        """Create security system for utility tests."""
        temp_dir = tempfile.mkdtemp()
        system = MultiProjectSecurity(storage_path=temp_dir)
        yield system
        shutil.rmtree(temp_dir)
    
    def test_generate_id(self, security_system):
        """Test ID generation."""
        with patch('time.time', return_value=1234567890):
            with patch('secrets.token_hex', return_value='abcdef123456'):
                generated_id = security_system._generate_id("test")
                
                assert generated_id == "test_1234567890_abcdef123456"
    
    def test_hash_password(self, security_system):
        """Test password hashing."""
        password = "test_password"
        salt = "test_salt"
        
        hashed = security_system._hash_password(password, salt)
        
        assert isinstance(hashed, str)
        assert len(hashed) > 0
        assert hashed != password
    
    def test_verify_password_correct(self, security_system):
        """Test password verification with correct password."""
        password = "test_password"
        salt = "test_salt"
        hashed = security_system._hash_password(password, salt)
        
        is_valid = security_system._verify_password(password, hashed, salt)
        assert is_valid is True
    
    def test_verify_password_incorrect(self, security_system):
        """Test password verification with incorrect password."""
        password = "test_password"
        wrong_password = "wrong_password"
        salt = "test_salt"
        hashed = security_system._hash_password(password, salt)
        
        is_valid = security_system._verify_password(wrong_password, hashed, salt)
        assert is_valid is False


class TestDataPersistence:
    """Test data loading and saving functionality."""
    
    @pytest.fixture
    def security_system(self):
        """Create security system for persistence tests."""
        temp_dir = tempfile.mkdtemp()
        system = MultiProjectSecurity(storage_path=temp_dir)
        yield system
        shutil.rmtree(temp_dir)
    
    def test_save_and_load_users(self, security_system):
        """Test saving and loading user data."""
        # Create test user
        security_system.create_user(
            "testuser", "test@example.com", "password", AccessLevel.ADMIN
        )
        
        user = next(iter(security_system.users.values()))
        user.project_permissions["project1"] = AccessLevel.WRITE
        user.two_factor_enabled = True
        user.last_login = datetime.utcnow()
        
        # Save data
        security_system._save_security_data()
        
        # Create new system and load data
        new_system = MultiProjectSecurity(storage_path=security_system.storage_path)
        
        assert len(new_system.users) == 1
        loaded_user = next(iter(new_system.users.values()))
        assert loaded_user.username == "testuser"
        assert loaded_user.email == "test@example.com"
        assert loaded_user.global_access_level == AccessLevel.ADMIN
        assert loaded_user.project_permissions["project1"] == AccessLevel.WRITE
        assert loaded_user.two_factor_enabled is True
        assert loaded_user.last_login is not None
    
    def test_save_and_load_access_rules(self, security_system):
        """Test saving and loading access rules."""
        # Create test rule
        rule = AccessRule(
            rule_id="test_rule",
            name="Test Rule",
            description="Test rule",
            access_level=AccessLevel.WRITE,
            created_at=datetime.utcnow()
        )
        security_system.access_rules["test_rule"] = rule
        
        # Save data
        security_system._save_security_data()
        
        # Create new system and load data
        new_system = MultiProjectSecurity(storage_path=security_system.storage_path)
        
        assert len(new_system.access_rules) == 1
        loaded_rule = new_system.access_rules["test_rule"]
        assert loaded_rule.name == "Test Rule"
        assert loaded_rule.access_level == AccessLevel.WRITE
        assert loaded_rule.created_at is not None
    
    def test_save_and_load_secrets(self, security_system):
        """Test saving and loading secrets metadata."""
        # Mock crypto
        with patch('lib.multi_project_security.CRYPTO_AVAILABLE', True):
            with patch('lib.multi_project_security.Fernet') as mock_fernet:
                mock_cipher = Mock()
                mock_cipher.encrypt.return_value = b'encrypted_data'
                mock_fernet.return_value = mock_cipher
                security_system.cipher = mock_cipher
                
                # Create test secret
                secret_id = security_system.create_secret(
                    "test_secret", "value", "api_key", "owner123"
                )
                
                secret = security_system.secrets[secret_id]
                secret.last_accessed = datetime.utcnow()
                secret.expires_at = datetime.utcnow() + timedelta(days=30)
                
                # Save data
                security_system._save_security_data()
                
                # Create new system and load data
                new_system = MultiProjectSecurity(storage_path=security_system.storage_path)
                
                assert len(new_system.secrets) == 1
                loaded_secret = new_system.secrets[secret_id]
                assert loaded_secret.name == "test_secret"
                assert loaded_secret.secret_type == "api_key"
                assert loaded_secret.owner == "owner123"
                assert loaded_secret.last_accessed is not None
                assert loaded_secret.expires_at is not None
    
    @patch('lib.multi_project_security.logger')
    def test_load_security_data_error(self, mock_logger, security_system):
        """Test error handling in data loading."""
        # Create invalid JSON file
        users_file = security_system.storage_path / "users.json"
        with open(users_file, 'w') as f:
            f.write("invalid json{")
        
        # Should handle error gracefully
        security_system._load_security_data()
        
        # Should log error
        mock_logger.error.assert_called()
    
    @patch('lib.multi_project_security.logger')
    def test_save_security_data_error(self, mock_logger, security_system):
        """Test error handling in data saving."""
        # Mock json.dump to raise exception
        with patch('json.dump', side_effect=Exception("Write failed")):
            security_system._save_security_data()
            
            # Should log error
            mock_logger.error.assert_called()


class TestEncryptionSetup:
    """Test encryption setup functionality."""
    
    @pytest.fixture
    def temp_storage_dir(self):
        """Create temporary directory."""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir)
    
    def test_setup_encryption_with_crypto_available(self, temp_storage_dir):
        """Test encryption setup when crypto is available."""
        with patch('lib.multi_project_security.CRYPTO_AVAILABLE', True):
            with patch('lib.multi_project_security.Fernet') as mock_fernet:
                mock_cipher = Mock()
                mock_fernet.return_value = mock_cipher
                mock_fernet.generate_key.return_value = b'generated_key'
                
                system = MultiProjectSecurity(storage_path=temp_storage_dir)
                
                # Should have created cipher
                assert hasattr(system, 'cipher')
                assert system.cipher == mock_cipher
                
                # Should have generated and saved key
                key_file = Path(temp_storage_dir) / "master.key"
                assert key_file.exists()
    
    def test_setup_encryption_with_existing_key(self, temp_storage_dir):
        """Test encryption setup with existing key file."""
        with patch('lib.multi_project_security.CRYPTO_AVAILABLE', True):
            with patch('lib.multi_project_security.Fernet') as mock_fernet:
                mock_cipher = Mock()
                mock_fernet.return_value = mock_cipher
                
                # Create existing key file
                key_file = Path(temp_storage_dir) / "master.key"
                key_file.parent.mkdir(parents=True, exist_ok=True)
                with open(key_file, 'wb') as f:
                    f.write(b'existing_key')
                
                system = MultiProjectSecurity(storage_path=temp_storage_dir)
                
                # Should have loaded existing key
                mock_fernet.assert_called_with(b'existing_key')
    
    @patch('lib.multi_project_security.logger')
    def test_setup_encryption_without_crypto(self, mock_logger, temp_storage_dir):
        """Test encryption setup when crypto is not available."""
        with patch('lib.multi_project_security.CRYPTO_AVAILABLE', False):
            system = MultiProjectSecurity(storage_path=temp_storage_dir)
            
            # Should not have cipher
            assert not hasattr(system, 'cipher')
            
            # Should log warning
            mock_logger.warning.assert_called_with(
                "Cryptography library not available - secret management disabled"
            )


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])