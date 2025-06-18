"""
Unit tests for Project Storage.

Tests the file-based persistence system for project management data
including epics, stories, sprints, and configuration storage.
"""

import pytest
import tempfile
import shutil
import json
from pathlib import Path
from datetime import datetime
from unittest.mock import Mock, patch

import sys
sys.path.append(str(Path(__file__).parent.parent.parent))

from lib.project_storage import ProjectStorage
from lib.data_models import Epic, Story, Sprint, EpicStatus, StoryStatus, SprintStatus, ProjectData


class TestProjectStorage:
    """Test the ProjectStorage class."""
    
    @pytest.fixture
    def temp_storage_dir(self):
        """Create temporary directory for storage testing."""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def project_storage(self, temp_storage_dir):
        """Create a ProjectStorage instance with temporary storage."""
        return ProjectStorage(project_path=temp_storage_dir)
    
    @pytest.fixture
    def sample_epic(self):
        """Create a sample epic for testing."""
        return Epic(
            id="EPIC-1",
            title="Authentication System",
            description="Build complete user authentication"
        )
    
    @pytest.fixture
    def sample_story(self):
        """Create a sample story for testing."""
        return Story(
            id="STORY-1",
            title="User Login",
            description="As a user, I want to log in",
            epic_id="EPIC-1"
        )
    
    @pytest.fixture
    def sample_sprint(self):
        """Create a sample sprint for testing."""
        return Sprint(
            id="SPRINT-1",
            goal="Implement authentication features"
        )

    def test_project_storage_init(self, project_storage, temp_storage_dir):
        """Test ProjectStorage initialization."""
        assert project_storage.project_path == Path(temp_storage_dir)
        assert project_storage.orch_state_dir == Path(temp_storage_dir) / ".orch-state"
        
        # Ensure directories exist
        project_storage.ensure_directories()
        assert project_storage.orch_state_dir.exists()
        assert project_storage.sprints_dir.exists()
        assert project_storage.tdd_cycles_dir.exists()

    def test_save_and_load_project_data(self, project_storage, sample_epic, sample_story, sample_sprint):
        """Test saving and loading project data."""
        # Create project data with epic, story, and sprint
        project_data = ProjectData(
            epics=[sample_epic],
            stories=[sample_story],
            sprints=[sample_sprint]
        )
        
        # Save project data
        project_storage.save_project_data(project_data)
        
        # Check that file was created
        assert project_storage.backlog_file.exists()
        
        # Load project data back
        loaded_data = project_storage.load_project_data()
        
        assert len(loaded_data.epics) == 1
        assert len(loaded_data.stories) == 1
        assert len(loaded_data.sprints) == 1
        assert loaded_data.epics[0].id == sample_epic.id
        assert loaded_data.stories[0].id == sample_story.id
        assert loaded_data.sprints[0].id == sample_sprint.id

    def test_load_empty_project_data(self, project_storage):
        """Test loading project data when no file exists."""
        loaded_data = project_storage.load_project_data()
        
        assert isinstance(loaded_data, ProjectData)
        assert loaded_data.epics == []
        assert loaded_data.stories == []
        assert loaded_data.sprints == []

    def test_save_and_load_sprint(self, project_storage, sample_sprint):
        """Test saving and loading individual sprint."""
        project_storage.save_sprint(sample_sprint)
        
        # Check that file was created
        sprint_file = project_storage.sprints_dir / f"{sample_sprint.id}.json"
        assert sprint_file.exists()
        
        # Load sprint back
        loaded_sprint = project_storage.load_sprint(sample_sprint.id)
        
        assert loaded_sprint is not None
        assert loaded_sprint.id == sample_sprint.id
        assert loaded_sprint.goal == sample_sprint.goal

    def test_load_nonexistent_sprint(self, project_storage):
        """Test loading a nonexistent sprint."""
        loaded_sprint = project_storage.load_sprint("NONEXISTENT-SPRINT")
        assert loaded_sprint is None

    def test_list_sprint_files(self, project_storage, sample_sprint):
        """Test listing sprint files."""
        # Initially empty
        sprint_files = project_storage.list_sprint_files()
        assert sprint_files == []
        
        # Save a sprint
        project_storage.save_sprint(sample_sprint)
        
        # Should now have one file
        sprint_files = project_storage.list_sprint_files()
        assert len(sprint_files) == 1
        assert sample_sprint.id in sprint_files

    def test_initialize_project(self, project_storage):
        """Test project initialization."""
        success = project_storage.initialize_project()
        
        assert success
        assert project_storage.orch_state_dir.exists()
        assert project_storage.backlog_file.exists()
        assert project_storage.architecture_file.exists()
        assert project_storage.best_practices_file.exists()

    def test_project_exists(self, project_storage, temp_storage_dir):
        """Test checking if project exists."""
        # Initially no .git directory
        assert not project_storage.project_exists()
        
        # Create .git directory
        git_dir = Path(temp_storage_dir) / ".git"
        git_dir.mkdir()
        
        # Now should exist
        assert project_storage.project_exists()

    def test_is_initialized(self, project_storage):
        """Test checking if project is initialized."""
        # Initially not initialized
        assert not project_storage.is_initialized()
        
        # Initialize project
        project_storage.initialize_project()
        
        # Now should be initialized
        assert project_storage.is_initialized()

    def test_get_project_name(self, project_storage, temp_storage_dir):
        """Test getting project name."""
        expected_name = Path(temp_storage_dir).name
        assert project_storage.get_project_name() == expected_name

    def test_save_and_load_status(self, project_storage):
        """Test saving and loading status."""
        status = {"state": "idle", "last_action": "test"}
        
        project_storage.save_status(status)
        loaded_status = project_storage.load_status()
        
        assert loaded_status == status

    def test_load_empty_status(self, project_storage):
        """Test loading status when no file exists."""
        status = project_storage.load_status()
        assert status == {}

    def test_architecture_content(self, project_storage):
        """Test architecture file operations."""
        # Initially empty
        content = project_storage.get_architecture_content()
        assert content == ""
        
        # Update architecture
        new_content = "# Test Architecture\nThis is a test."
        project_storage.update_architecture(new_content)
        
        # Should now have content
        content = project_storage.get_architecture_content()
        assert content == new_content

    def test_best_practices_content(self, project_storage):
        """Test best practices file operations."""
        # Initially empty
        content = project_storage.get_best_practices_content()
        assert content == ""
        
        # Update best practices
        new_content = "# Test Practices\nThese are test practices."
        project_storage.update_best_practices(new_content)
        
        # Should now have content
        content = project_storage.get_best_practices_content()
        assert content == new_content