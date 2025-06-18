"""
Unit tests for Multi-Project Configuration Manager.

Tests the configuration management system for multi-project orchestration,
including project registration, discovery, validation, and configuration persistence.
"""

import pytest
import tempfile
import shutil
import json
import yaml
from pathlib import Path
from datetime import datetime
from unittest.mock import Mock, patch

import sys
sys.path.append(str(Path(__file__).parent.parent.parent))

from lib.multi_project_config import (
    MultiProjectConfigManager, ProjectConfig, GlobalOrchestratorConfig,
    ProjectPriority, ProjectStatus, ResourceLimits
)


class TestMultiProjectConfigManager:
    """Test the MultiProjectConfigManager class."""
    
    @pytest.fixture
    def temp_config_dir(self):
        """Create temporary directory for configuration testing."""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def config_manager(self, temp_config_dir):
        """Create a config manager with temporary storage."""
        config_path = Path(temp_config_dir) / "test-config.yaml"
        return MultiProjectConfigManager(str(config_path))
    
    @pytest.fixture
    def sample_project_dir(self, temp_config_dir):
        """Create a sample project directory."""
        project_dir = Path(temp_config_dir) / "sample_project"
        project_dir.mkdir(parents=True)
        
        # Create some project files
        (project_dir / "README.md").write_text("# Sample Project")
        (project_dir / "src").mkdir()
        (project_dir / "src" / "main.py").write_text("print('hello')")
        
        return str(project_dir)

    def test_init_creates_default_config(self, config_manager):
        """Test that initialization creates default configuration."""
        assert config_manager.global_config is not None
        assert config_manager.global_config.max_total_agents > 0
        assert config_manager.global_config.max_concurrent_projects > 0
        assert len(config_manager.projects) == 0

    def test_init_loads_existing_config(self, temp_config_dir):
        """Test loading existing configuration file."""
        config_path = Path(temp_config_dir) / "existing-config.yaml"
        
        # Create existing config
        config_data = {
            "global": {
                "max_total_agents": 15,
                "max_concurrent_projects": 8,
                "resource_allocation_strategy": "priority_based"
            },
            "projects": {}
        }
        
        with open(config_path, 'w') as f:
            yaml.dump(config_data, f)
        
        manager = MultiProjectConfigManager(str(config_path))
        
        assert manager.global_config.max_total_agents == 15
        assert manager.global_config.max_concurrent_projects == 8
        assert manager.global_config.resource_allocation_strategy == "priority_based"

    def test_register_project_basic(self, config_manager, sample_project_dir):
        """Test basic project registration."""
        project_config = config_manager.register_project(
            name="test-project",
            path=sample_project_dir,
            description="Test project for unit testing"
        )
        
        assert project_config.name == "test-project"
        assert project_config.path == sample_project_dir
        assert project_config.description == "Test project for unit testing"
        assert project_config.status == ProjectStatus.ACTIVE
        assert project_config.priority == ProjectPriority.NORMAL
        
        # Check project is in manager
        assert "test-project" in config_manager.projects
        assert config_manager.projects["test-project"] == project_config

    def test_register_project_with_custom_settings(self, config_manager, sample_project_dir):
        """Test project registration with custom settings."""
        project_config = config_manager.register_project(
            name="custom-project",
            path=sample_project_dir,
            priority=ProjectPriority.HIGH,
            status=ProjectStatus.MAINTENANCE,
            description="High priority project",
            discord_channel="#custom-channel",
            team=["developer1", "developer2"]
        )
        
        assert project_config.priority == ProjectPriority.HIGH
        assert project_config.status == ProjectStatus.MAINTENANCE
        assert project_config.discord_channel == "#custom-channel"
        assert project_config.team == ["developer1", "developer2"]

    def test_register_project_creates_state_directory(self, config_manager, sample_project_dir):
        """Test that project registration creates .orch-state directory."""
        config_manager.register_project("state-test", sample_project_dir)
        
        state_dir = Path(sample_project_dir) / ".orch-state"
        assert state_dir.exists()
        assert state_dir.is_dir()
        
        # Check project config file is created
        project_config_file = state_dir / "project-config.json"
        assert project_config_file.exists()
        
        # Verify config content
        with open(project_config_file) as f:
            config_data = json.load(f)
        
        assert config_data["name"] == "state-test"
        assert config_data["status"] == "active"

    def test_register_project_duplicate_name(self, config_manager, sample_project_dir):
        """Test that registering duplicate project names raises error."""
        config_manager.register_project("duplicate", sample_project_dir)
        
        with pytest.raises(ValueError, match="Project 'duplicate' already exists"):
            config_manager.register_project("duplicate", sample_project_dir)

    def test_register_project_invalid_path(self, config_manager):
        """Test that registering with invalid path raises error."""
        with pytest.raises(ValueError, match="Project path .* does not exist"):
            config_manager.register_project("invalid", "/nonexistent/path")

    def test_get_project_existing(self, config_manager, sample_project_dir):
        """Test getting an existing project."""
        original_config = config_manager.register_project("existing", sample_project_dir)
        retrieved_config = config_manager.get_project("existing")
        
        assert retrieved_config == original_config
        assert retrieved_config.name == "existing"

    def test_get_project_nonexistent(self, config_manager):
        """Test getting a nonexistent project returns None."""
        result = config_manager.get_project("nonexistent")
        assert result is None

    def test_list_projects_empty(self, config_manager):
        """Test listing projects when none are registered."""
        projects = config_manager.list_projects()
        assert projects == []

    def test_list_projects_with_data(self, config_manager, sample_project_dir):
        """Test listing projects with registered projects."""
        config_manager.register_project("project1", sample_project_dir)
        config_manager.register_project("project2", sample_project_dir, priority=ProjectPriority.HIGH)
        
        projects = config_manager.list_projects()
        
        assert len(projects) == 2
        project_names = [p.name for p in projects]
        assert "project1" in project_names
        assert "project2" in project_names

    def test_get_active_projects(self, config_manager, sample_project_dir):
        """Test getting only active projects."""
        config_manager.register_project("active1", sample_project_dir)
        config_manager.register_project("active2", sample_project_dir)
        config_manager.register_project("paused", sample_project_dir, status=ProjectStatus.PAUSED)
        config_manager.register_project("archived", sample_project_dir, status=ProjectStatus.ARCHIVED)
        
        active_projects = config_manager.get_active_projects()
        
        assert len(active_projects) == 2
        active_names = [p.name for p in active_projects]
        assert "active1" in active_names
        assert "active2" in active_names
        assert "paused" not in active_names
        assert "archived" not in active_names

    def test_update_project_status(self, config_manager, sample_project_dir):
        """Test updating project status."""
        config_manager.register_project("status-test", sample_project_dir)
        
        # Update status
        success = config_manager.update_project_status("status-test", ProjectStatus.PAUSED)
        assert success
        
        # Verify update
        project = config_manager.get_project("status-test")
        assert project.status == ProjectStatus.PAUSED

    def test_update_project_status_nonexistent(self, config_manager):
        """Test updating status of nonexistent project."""
        success = config_manager.update_project_status("nonexistent", ProjectStatus.PAUSED)
        assert not success

    def test_remove_project(self, config_manager, sample_project_dir):
        """Test removing a project."""
        config_manager.register_project("to-remove", sample_project_dir)
        assert "to-remove" in config_manager.projects
        
        success = config_manager.remove_project("to-remove")
        assert success
        assert "to-remove" not in config_manager.projects

    def test_remove_project_nonexistent(self, config_manager):
        """Test removing nonexistent project."""
        success = config_manager.remove_project("nonexistent")
        assert not success

    def test_discover_projects_no_projects(self, temp_config_dir, config_manager):
        """Test project discovery with no discoverable projects."""
        # Create empty directory
        empty_dir = Path(temp_config_dir) / "empty"
        empty_dir.mkdir()
        
        discovered = config_manager.discover_projects([str(empty_dir)])
        assert discovered == []

    def test_discover_projects_with_git_repos(self, temp_config_dir, config_manager):
        """Test discovering Git repositories."""
        # Create mock Git repository
        git_project = Path(temp_config_dir) / "git_project"
        git_project.mkdir()
        git_dir = git_project / ".git"
        git_dir.mkdir()
        (git_project / "README.md").write_text("# Git Project")
        
        discovered = config_manager.discover_projects([temp_config_dir])
        
        assert len(discovered) >= 1
        git_discoveries = [d for d in discovered if d["name"] == "git_project"]
        assert len(git_discoveries) == 1
        assert git_discoveries[0]["type"] == "git_repo"

    def test_discover_projects_with_orch_state(self, temp_config_dir, config_manager):
        """Test discovering existing orchestrated projects."""
        # Create project with .orch-state
        orch_project = Path(temp_config_dir) / "orch_project"
        orch_project.mkdir()
        orch_state = orch_project / ".orch-state"
        orch_state.mkdir()
        (orch_state / "status.json").write_text('{"state": "IDLE"}')
        
        discovered = config_manager.discover_projects([temp_config_dir])
        
        orch_discoveries = [d for d in discovered if d["name"] == "orch_project"]
        assert len(orch_discoveries) == 1
        assert orch_discoveries[0]["type"] == "orch_existing"

    def test_validate_configuration_valid(self, config_manager):
        """Test configuration validation with valid config."""
        issues = config_manager.validate_configuration()
        assert issues == []

    def test_validate_configuration_with_issues(self, config_manager):
        """Test configuration validation with issues."""
        # Create invalid configuration
        config_manager.global_config.max_total_agents = -1
        config_manager.global_config.max_concurrent_projects = 0
        
        issues = config_manager.validate_configuration()
        
        assert len(issues) >= 2
        assert any("max_total_agents must be positive" in issue for issue in issues)
        assert any("max_concurrent_projects must be positive" in issue for issue in issues)

    def test_save_configuration(self, config_manager, sample_project_dir):
        """Test saving configuration to file."""
        # Add some projects
        config_manager.register_project("save-test1", sample_project_dir)
        config_manager.register_project("save-test2", sample_project_dir, priority=ProjectPriority.HIGH)
        
        # Save configuration
        config_manager.save_configuration()
        
        # Verify file exists and contains data
        assert config_manager.config_path.exists()
        
        with open(config_manager.config_path) as f:
            saved_data = yaml.safe_load(f)
        
        assert "global" in saved_data
        assert "projects" in saved_data
        assert "save-test1" in saved_data["projects"]
        assert "save-test2" in saved_data["projects"]
        assert saved_data["projects"]["save-test2"]["priority"] == "high"

    def test_load_configuration_after_save(self, temp_config_dir, sample_project_dir):
        """Test loading configuration after saving."""
        config_path = Path(temp_config_dir) / "save-load-test.yaml"
        
        # Create manager and add projects
        manager1 = MultiProjectConfigManager(str(config_path))
        manager1.register_project("persistent-test", sample_project_dir, priority=ProjectPriority.CRITICAL)
        manager1.save_configuration()
        
        # Create new manager from saved config
        manager2 = MultiProjectConfigManager(str(config_path))
        
        # Verify data is loaded
        assert "persistent-test" in manager2.projects
        project = manager2.get_project("persistent-test")
        assert project.priority == ProjectPriority.CRITICAL


class TestProjectConfig:
    """Test the ProjectConfig dataclass."""
    
    def test_project_config_creation(self):
        """Test creating a ProjectConfig with all fields."""
        now = datetime.utcnow()
        
        config = ProjectConfig(
            name="test-project",
            path="/path/to/project",
            description="Test project",
            priority=ProjectPriority.HIGH,
            status=ProjectStatus.ACTIVE,
            created_at=now,
            version="1.0"
        )
        
        assert config.name == "test-project"
        assert config.path == "/path/to/project"
        assert config.description == "Test project"
        assert config.priority == ProjectPriority.HIGH
        assert config.status == ProjectStatus.ACTIVE
        assert config.created_at == now
        assert config.version == "1.0"

    def test_project_config_defaults(self):
        """Test ProjectConfig with default values."""
        config = ProjectConfig(
            name="default-test",
            path="/path/to/project"
        )
        
        assert config.name == "default-test"
        assert config.path == "/path/to/project"
        assert config.priority == ProjectPriority.NORMAL
        assert config.status == ProjectStatus.ACTIVE
        assert config.description == ""
        assert isinstance(config.created_at, datetime)


class TestGlobalOrchestratorConfig:
    """Test the GlobalOrchestratorConfig dataclass."""
    
    def test_global_config_creation(self):
        """Test creating GlobalOrchestratorConfig with custom values."""
        config = GlobalOrchestratorConfig(
            max_total_agents=25,
            max_concurrent_projects=15,
            resource_allocation_strategy="dynamic",
            global_cpu_cores=8,
            global_memory_limit_gb=16
        )
        
        assert config.max_total_agents == 25
        assert config.max_concurrent_projects == 15
        assert config.resource_allocation_strategy == "dynamic"
        assert config.global_cpu_cores == 8
        assert config.global_memory_limit_gb == 16

    def test_global_config_defaults(self):
        """Test GlobalOrchestratorConfig with default values."""
        config = GlobalOrchestratorConfig()
        
        assert config.max_total_agents == 20
        assert config.max_concurrent_projects == 10
        assert config.resource_allocation_strategy == "fair_share"
        assert config.global_cpu_cores == 4
        assert config.global_memory_limit_gb == 8


class TestResourceLimits:
    """Test the ResourceLimits dataclass."""
    
    def test_resource_limits_creation(self):
        """Test creating ResourceLimits with custom values."""
        limits = ResourceLimits(
            max_parallel_agents=5,
            max_parallel_cycles=3,
            max_memory_mb=2048,
            max_disk_mb=4096,
            cpu_priority=2.0
        )
        
        assert limits.max_parallel_agents == 5
        assert limits.max_parallel_cycles == 3
        assert limits.max_memory_mb == 2048
        assert limits.max_disk_mb == 4096
        assert limits.cpu_priority == 2.0

    def test_resource_limits_defaults(self):
        """Test ResourceLimits with default values."""
        limits = ResourceLimits()
        
        assert limits.max_parallel_agents == 3
        assert limits.max_parallel_cycles == 2
        assert limits.max_memory_mb == 1024
        assert limits.max_disk_mb == 2048
        assert limits.cpu_priority == 1.0


class TestEnums:
    """Test enum classes."""
    
    def test_project_priority_values(self):
        """Test ProjectPriority enum values."""
        assert ProjectPriority.CRITICAL.value == "critical"
        assert ProjectPriority.HIGH.value == "high"
        assert ProjectPriority.NORMAL.value == "normal"
        assert ProjectPriority.LOW.value == "low"

    def test_project_status_values(self):
        """Test ProjectStatus enum values."""
        assert ProjectStatus.ACTIVE.value == "active"
        assert ProjectStatus.PAUSED.value == "paused"
        assert ProjectStatus.MAINTENANCE.value == "maintenance"
        assert ProjectStatus.ARCHIVED.value == "archived"
        assert ProjectStatus.INITIALIZING.value == "initializing"