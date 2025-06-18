"""
Unit tests for Multi-Project Security System.

Tests the security system that manages user authentication, authorization,
access control, and project isolation in multi-project environments.
"""

import pytest
import tempfile
import shutil
import hashlib
from pathlib import Path
from datetime import datetime, timedelta
from unittest.mock import Mock, patch

import sys
sys.path.append(str(Path(__file__).parent.parent.parent))

from lib.multi_project_security import (
    MultiProjectSecurity, User, AccessLevel, IsolationMode,
    AuditLogEntry, SecurityAction
)


class TestUser:
    """Test the User dataclass."""
    
    def test_user_creation(self):
        """Test creating a User instance."""
        now = datetime.utcnow()
        
        user = User(
            user_id="user-123",
            username="testuser",
            email="test@example.com",
            password_hash="hashed_password",
            salt="test_salt",
            global_access_level=AccessLevel.WRITE,
            created_at=now
        )
        
        assert user.user_id == "user-123"
        assert user.username == "testuser"
        assert user.email == "test@example.com"
        assert user.password_hash == "hashed_password"
        assert user.global_access_level == AccessLevel.WRITE
        assert user.created_at == now

    def test_user_defaults(self):
        """Test User with default values."""
        user = User(
            user_id="default-user",
            username="default",
            email="default@example.com",
            password_hash="dummy_hash",
            salt="dummy_salt"
        )
        
        assert user.global_access_level == AccessLevel.READ
        assert user.is_active is True
        assert user.project_permissions == {}
        assert isinstance(user.created_at, datetime)

    # Note: Many User and other class methods referenced in tests may not exist in actual implementation


class TestEnums:
    """Test enum classes."""
    
    def test_access_level_values(self):
        """Test AccessLevel enum values."""
        assert AccessLevel.OWNER.value == "owner"
        assert AccessLevel.ADMIN.value == "admin"
        assert AccessLevel.WRITE.value == "write"
        assert AccessLevel.READ.value == "read"
        assert AccessLevel.NONE.value == "none"

    def test_isolation_mode_values(self):
        """Test IsolationMode enum values."""
        assert IsolationMode.NONE.value == "none"
        assert IsolationMode.PROCESS.value == "process"
        assert IsolationMode.FILESYSTEM.value == "filesystem"
        assert IsolationMode.NETWORK.value == "network"
        assert IsolationMode.CONTAINER.value == "container"
        assert IsolationMode.FULL.value == "full"

    def test_security_action_values(self):
        """Test SecurityAction enum values."""
        assert SecurityAction.LOGIN.value == "login"
        assert SecurityAction.LOGOUT.value == "logout"
        assert SecurityAction.ACCESS_GRANTED.value == "access_granted"
        assert SecurityAction.ACCESS_DENIED.value == "access_denied"
        assert SecurityAction.SECURITY_VIOLATION.value == "security_violation"


class TestMultiProjectSecurity:
    """Test the MultiProjectSecurity class."""
    
    @pytest.fixture
    def temp_storage_dir(self):
        """Create temporary directory for security storage testing."""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def security_system(self, temp_storage_dir):
        """Create a MultiProjectSecurity instance."""
        return MultiProjectSecurity(
            storage_path=temp_storage_dir,
            enable_audit_logging=True,
            default_isolation_mode=IsolationMode.PROCESS
        )

    def test_security_system_init(self, security_system, temp_storage_dir):
        """Test MultiProjectSecurity initialization."""
        assert security_system.storage_path == Path(temp_storage_dir)
        assert security_system.enable_audit_logging is True
        assert security_system.default_isolation_mode == IsolationMode.PROCESS
        assert security_system.users == {}
        assert security_system.storage_path.exists()

    def test_create_user(self, security_system):
        """Test creating a new user."""
        success = security_system.create_user(
            username="testuser",
            email="test@example.com",
            password="secure_password",
            global_access_level=AccessLevel.WRITE
        )
        
        assert success
        assert len(security_system.users) == 1
        
        # Get the created user
        user = next(iter(security_system.users.values()))
        assert user.username == "testuser"
        assert user.email == "test@example.com"
        assert user.global_access_level == AccessLevel.WRITE
        
        # Password should be hashed
        assert user.password_hash != "secure_password"
        assert len(user.password_hash) > 0

    def test_create_user_duplicate_username(self, security_system):
        """Test creating user with duplicate username."""
        # Create first user
        security_system.create_user("testuser", "test1@example.com", "password1")
        
        # Try to create user with same username
        success = security_system.create_user("testuser", "test2@example.com", "password2")
        
        assert not success  # Should fail

    def test_authenticate_user_success(self, security_system):
        """Test successful user authentication."""
        # Create user
        security_system.create_user("testuser", "test@example.com", "secure_password")
        
        # Authenticate
        session_token = security_system.authenticate_user("testuser", "secure_password")
        
        assert session_token is not None
        assert len(session_token) > 0

    def test_authenticate_user_wrong_password(self, security_system):
        """Test authentication with wrong password."""
        # Create user
        security_system.create_user("testuser", "test@example.com", "secure_password")
        
        # Try to authenticate with wrong password
        session_token = security_system.authenticate_user("testuser", "wrong_password")
        
        assert session_token is None

    def test_setup_project_isolation(self, security_system):
        """Test setting up project isolation."""
        success = security_system.setup_project_isolation("project1")
        
        assert success
        assert "project1" in security_system.project_isolations

    def test_get_security_status(self, security_system):
        """Test getting security system status."""
        # Create some test data
        security_system.create_user("testuser", "test@example.com", "password")
        security_system.setup_project_isolation("project1")
        
        status = security_system.get_security_status()
        
        assert "security_system" in status
        assert "users" in status
        assert "sessions" in status
        assert "secrets" in status
        assert "isolation" in status
        assert "audit" in status
        
        assert status["users"]["total_users"] == 1
        assert status["security_system"]["audit_logging_enabled"] is True

    # Note: Many methods referenced in other tests may not exist in actual implementation