"""
Unit tests for Project Storage.

Tests the file-based persistence system for project management data
including epics, stories, sprints, TDD cycles, and configuration storage.
Comprehensive test coverage with mocked file operations for government audit compliance.
"""

import pytest
import json
import tempfile
import shutil
from pathlib import Path
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, mock_open, MagicMock, call
import stat

import sys
sys.path.append(str(Path(__file__).parent.parent.parent))

from lib.project_storage import ProjectStorage
from lib.data_models import Epic, Story, Sprint, EpicStatus, StoryStatus, SprintStatus, ProjectData


class TestProjectStorage:
    """Comprehensive test suite for the ProjectStorage class."""
    
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
            description="Build complete user authentication",
            status=EpicStatus.ACTIVE,
            tdd_requirements=["Unit tests", "Integration tests"],
            tdd_constraints={"max_complexity": 10}
        )
    
    @pytest.fixture
    def sample_story(self):
        """Create a sample story for testing."""
        return Story(
            id="STORY-1",
            title="User Login",
            description="As a user, I want to log in",
            epic_id="EPIC-1",
            priority=1,
            status=StoryStatus.BACKLOG,
            acceptance_criteria=["Must validate credentials", "Must redirect on success"],
            sprint_id="SPRINT-1",
            tdd_cycle_id="TDD-1",
            test_status="red",
            test_files=["test_login.py"],
            ci_status="pending",
            test_coverage=75.5
        )
    
    @pytest.fixture
    def sample_sprint(self):
        """Create a sample sprint for testing."""
        return Sprint(
            id="SPRINT-1",
            goal="Implement authentication features",
            status=SprintStatus.PLANNED
        )

    @pytest.fixture
    def mock_tdd_cycle(self):
        """Create a mock TDD cycle for testing."""
        mock_cycle = Mock()
        mock_cycle.id = "TDD-1"
        mock_cycle.is_complete.return_value = False
        mock_cycle.to_dict.return_value = {
            "id": "TDD-1",
            "story_id": "STORY-1",
            "status": "red",
            "created_at": datetime.now().isoformat()
        }
        return mock_cycle

    # Initialization and Setup Tests
    
    def test_project_storage_init(self, project_storage, temp_storage_dir):
        """Test ProjectStorage initialization with correct paths."""
        assert project_storage.project_path == Path(temp_storage_dir)
        assert project_storage.orch_state_dir == Path(temp_storage_dir) / ".orch-state"
        assert project_storage.backlog_file == Path(temp_storage_dir) / ".orch-state" / "backlog.json"
        assert project_storage.sprints_dir == Path(temp_storage_dir) / ".orch-state" / "sprints"
        assert project_storage.tdd_cycles_dir == Path(temp_storage_dir) / ".orch-state" / "tdd_cycles"
        assert project_storage.architecture_file == Path(temp_storage_dir) / ".orch-state" / "architecture.md"
        assert project_storage.best_practices_file == Path(temp_storage_dir) / ".orch-state" / "best-practices.md"
        assert project_storage.status_file == Path(temp_storage_dir) / ".orch-state" / "status.json"

    @patch('pathlib.Path.mkdir')
    @patch('pathlib.Path.touch')
    @patch('pathlib.Path.exists')
    def test_ensure_directories(self, mock_exists, mock_touch, mock_mkdir, project_storage):
        """Test directory creation with mocked file operations."""
        mock_exists.return_value = False
        
        project_storage.ensure_directories()
        
        # Check that directories are created
        assert mock_mkdir.call_count >= 3  # orch_state_dir, sprints_dir, tdd_cycles_dir
        assert mock_touch.call_count >= 2  # gitkeep files

    @patch('pathlib.Path.mkdir')
    @patch('pathlib.Path.touch')
    @patch('pathlib.Path.exists')
    def test_ensure_directories_existing_gitkeep(self, mock_exists, mock_touch, mock_mkdir, project_storage):
        """Test directory creation when gitkeep files already exist."""
        mock_exists.return_value = True
        
        project_storage.ensure_directories()
        
        # Should still create directories but not touch gitkeep files
        assert mock_mkdir.call_count >= 3
        mock_touch.assert_not_called()

    @patch('lib.project_storage.ProjectStorage.ensure_directories')
    @patch('lib.project_storage.ProjectStorage.save_project_data')
    @patch('pathlib.Path.exists')
    @patch('pathlib.Path.write_text')
    def test_initialize_project_success(self, mock_write_text, mock_exists, mock_save, mock_ensure, project_storage):
        """Test successful project initialization."""
        mock_exists.return_value = False
        
        result = project_storage.initialize_project()
        
        assert result is True
        mock_ensure.assert_called_once()
        mock_save.assert_called_once()
        assert mock_write_text.call_count == 2  # architecture and best practices files

    @patch('lib.project_storage.ProjectStorage.ensure_directories')
    @patch('pathlib.Path.exists')
    def test_initialize_project_existing_files(self, mock_exists, mock_ensure, project_storage):
        """Test project initialization when files already exist."""
        mock_exists.return_value = True
        
        result = project_storage.initialize_project()
        
        assert result is True
        mock_ensure.assert_called_once()

    @patch('lib.project_storage.ProjectStorage.ensure_directories')
    def test_initialize_project_exception(self, mock_ensure, project_storage):
        """Test project initialization with exception handling."""
        mock_ensure.side_effect = Exception("Directory creation failed")
        
        with patch('builtins.print') as mock_print:
            result = project_storage.initialize_project()
            assert result is False
            mock_print.assert_called_once()

    # Project Data Tests

    @patch('builtins.open', new_callable=mock_open, read_data='{"epics": [], "stories": [], "sprints": []}')
    @patch('pathlib.Path.exists')
    def test_load_project_data_success(self, mock_exists, mock_file, project_storage):
        """Test loading project data successfully."""
        mock_exists.return_value = True
        
        result = project_storage.load_project_data()
        
        assert isinstance(result, ProjectData)
        mock_file.assert_called_once()

    @patch('pathlib.Path.exists')
    def test_load_project_data_no_file(self, mock_exists, project_storage):
        """Test loading project data when file doesn't exist."""
        mock_exists.return_value = False
        
        result = project_storage.load_project_data()
        
        assert isinstance(result, ProjectData)
        assert result.epics == []
        assert result.stories == []
        assert result.sprints == []

    @patch('builtins.open', new_callable=mock_open, read_data='invalid json')
    @patch('pathlib.Path.exists')
    def test_load_project_data_json_error(self, mock_exists, mock_file, project_storage):
        """Test loading project data with JSON decode error."""
        mock_exists.return_value = True
        
        with patch('builtins.print') as mock_print:
            result = project_storage.load_project_data()
            assert isinstance(result, ProjectData)
            mock_print.assert_called_once()

    @patch('builtins.open', new_callable=mock_open)
    @patch('json.dump')
    @patch('lib.project_storage.ProjectStorage.ensure_directories')
    def test_save_project_data_success(self, mock_ensure, mock_json_dump, mock_file, project_storage, sample_epic):
        """Test saving project data successfully."""
        project_data = ProjectData(epics=[sample_epic])
        
        project_storage.save_project_data(project_data)
        
        mock_ensure.assert_called_once()
        mock_file.assert_called_once()
        mock_json_dump.assert_called_once()

    @patch('builtins.open', new_callable=mock_open)
    @patch('json.dump')
    @patch('lib.project_storage.ProjectStorage.ensure_directories')
    def test_save_project_data_exception(self, mock_ensure, mock_json_dump, mock_file, project_storage):
        """Test saving project data with exception handling."""
        mock_json_dump.side_effect = Exception("Write failed")
        project_data = ProjectData()
        
        with patch('builtins.print') as mock_print:
            project_storage.save_project_data(project_data)
            mock_print.assert_called_once()

    # Sprint Tests

    @patch('builtins.open', new_callable=mock_open)
    @patch('json.load')
    @patch('pathlib.Path.exists')
    def test_load_sprint_success(self, mock_exists, mock_json_load, mock_file, project_storage, sample_sprint):
        """Test loading sprint successfully."""
        mock_exists.return_value = True
        mock_json_load.return_value = sample_sprint.to_dict()
        
        result = project_storage.load_sprint("SPRINT-1")
        
        assert result is not None
        assert result.id == "SPRINT-1"
        mock_file.assert_called_once()

    @patch('pathlib.Path.exists')
    def test_load_sprint_no_file(self, mock_exists, project_storage):
        """Test loading sprint when file doesn't exist."""
        mock_exists.return_value = False
        
        result = project_storage.load_sprint("NONEXISTENT")
        
        assert result is None

    @patch('builtins.open', new_callable=mock_open, read_data='invalid json')
    @patch('pathlib.Path.exists')
    def test_load_sprint_json_error(self, mock_exists, mock_file, project_storage):
        """Test loading sprint with JSON decode error."""
        mock_exists.return_value = True
        
        with patch('builtins.print') as mock_print:
            result = project_storage.load_sprint("SPRINT-1")
            assert result is None
            mock_print.assert_called_once()

    @patch('builtins.open', new_callable=mock_open)
    @patch('json.dump')
    @patch('lib.project_storage.ProjectStorage.ensure_directories')
    def test_save_sprint_success(self, mock_ensure, mock_json_dump, mock_file, project_storage, sample_sprint):
        """Test saving sprint successfully."""
        project_storage.save_sprint(sample_sprint)
        
        mock_ensure.assert_called_once()
        mock_file.assert_called_once()
        mock_json_dump.assert_called_once()

    @patch('builtins.open', new_callable=mock_open)
    @patch('json.dump')
    @patch('lib.project_storage.ProjectStorage.ensure_directories')
    def test_save_sprint_exception(self, mock_ensure, mock_json_dump, mock_file, project_storage, sample_sprint):
        """Test saving sprint with exception handling."""
        mock_json_dump.side_effect = Exception("Write failed")
        
        with patch('builtins.print') as mock_print:
            project_storage.save_sprint(sample_sprint)
            mock_print.assert_called_once()

    @patch('pathlib.Path.exists')
    def test_list_sprint_files_no_directory(self, mock_exists, project_storage):
        """Test listing sprint files when directory doesn't exist."""
        mock_exists.return_value = False
        
        result = project_storage.list_sprint_files()
        
        assert result == []

    @patch('pathlib.Path.exists')
    @patch('pathlib.Path.glob')
    def test_list_sprint_files_success(self, mock_glob, mock_exists, project_storage):
        """Test listing sprint files successfully."""
        mock_exists.return_value = True
        mock_file = Mock()
        mock_file.stem = "SPRINT-1"
        mock_glob.return_value = [mock_file]
        
        result = project_storage.list_sprint_files()
        
        assert result == ["SPRINT-1"]

    # TDD Cycle Tests

    @patch('builtins.open', new_callable=mock_open)
    @patch('json.load')
    @patch('pathlib.Path.exists')
    def test_load_tdd_cycle_success(self, mock_exists, mock_json_load, mock_file, project_storage, mock_tdd_cycle):
        """Test loading TDD cycle successfully."""
        mock_exists.return_value = True
        mock_json_load.return_value = mock_tdd_cycle.to_dict()
        
        with patch('lib.tdd_models.TDDCycle') as mock_tdd_class:
            mock_tdd_class.from_dict.return_value = mock_tdd_cycle
            
            result = project_storage.load_tdd_cycle("TDD-1")
            
            assert result == mock_tdd_cycle
            mock_file.assert_called_once()

    @patch('pathlib.Path.exists')
    def test_load_tdd_cycle_no_file(self, mock_exists, project_storage):
        """Test loading TDD cycle when file doesn't exist."""
        mock_exists.return_value = False
        
        result = project_storage.load_tdd_cycle("NONEXISTENT")
        
        assert result is None

    @patch('builtins.open', new_callable=mock_open, read_data='invalid json')
    @patch('pathlib.Path.exists')
    def test_load_tdd_cycle_json_error(self, mock_exists, mock_file, project_storage):
        """Test loading TDD cycle with JSON decode error."""
        mock_exists.return_value = True
        
        with patch('builtins.print') as mock_print:
            result = project_storage.load_tdd_cycle("TDD-1")
            assert result is None
            mock_print.assert_called_once()

    @patch('builtins.open', new_callable=mock_open, read_data='{"id": "TDD-1"}')
    @patch('pathlib.Path.exists')
    def test_load_tdd_cycle_import_fallback(self, mock_exists, mock_file, project_storage, mock_tdd_cycle):
        """Test loading TDD cycle with import fallback."""
        mock_exists.return_value = True
        
        # Mock the import to simulate fallback behavior
        original_import = __builtins__['__import__']
        def mock_import(name, *args, **kwargs):
            if name == 'lib.tdd_models':
                raise ImportError("lib.tdd_models not found")
            return original_import(name, *args, **kwargs)
        
        with patch('builtins.__import__', side_effect=mock_import):
            # Mock the fallback import
            with patch('tdd_models.TDDCycle') as mock_tdd_class:
                mock_tdd_class.from_dict.return_value = mock_tdd_cycle
                with patch('json.load', return_value={"id": "TDD-1"}):
                    result = project_storage.load_tdd_cycle("TDD-1")
                    assert result == mock_tdd_cycle

    @patch('builtins.open', new_callable=mock_open)
    @patch('json.dump')
    @patch('lib.project_storage.ProjectStorage.ensure_directories')
    def test_save_tdd_cycle_success(self, mock_ensure, mock_json_dump, mock_file, project_storage, mock_tdd_cycle):
        """Test saving TDD cycle successfully."""
        project_storage.save_tdd_cycle(mock_tdd_cycle)
        
        mock_ensure.assert_called_once()
        mock_file.assert_called_once()
        mock_json_dump.assert_called_once()

    @patch('builtins.open', new_callable=mock_open)
    @patch('json.dump')
    @patch('lib.project_storage.ProjectStorage.ensure_directories')
    def test_save_tdd_cycle_exception(self, mock_ensure, mock_json_dump, mock_file, project_storage, mock_tdd_cycle):
        """Test saving TDD cycle with exception handling."""
        mock_json_dump.side_effect = Exception("Write failed")
        
        with patch('builtins.print') as mock_print:
            project_storage.save_tdd_cycle(mock_tdd_cycle)
            mock_print.assert_called_once()

    @patch('pathlib.Path.exists')
    def test_list_tdd_cycle_files_no_directory(self, mock_exists, project_storage):
        """Test listing TDD cycle files when directory doesn't exist."""
        mock_exists.return_value = False
        
        result = project_storage.list_tdd_cycle_files()
        
        assert result == []

    @patch('pathlib.Path.exists')
    @patch('pathlib.Path.glob')
    def test_list_tdd_cycle_files_success(self, mock_glob, mock_exists, project_storage):
        """Test listing TDD cycle files successfully."""
        mock_exists.return_value = True
        mock_file = Mock()
        mock_file.stem = "TDD-1"
        mock_glob.return_value = [mock_file]
        
        result = project_storage.list_tdd_cycle_files()
        
        assert result == ["TDD-1"]

    @patch('lib.project_storage.ProjectStorage.list_tdd_cycle_files')
    @patch('lib.project_storage.ProjectStorage.load_tdd_cycle')
    @patch('pathlib.Path.stat')
    @patch('pathlib.Path.exists')
    def test_get_active_tdd_cycle_success(self, mock_exists, mock_stat, mock_load, mock_list, project_storage, mock_tdd_cycle):
        """Test getting active TDD cycle successfully."""
        mock_list.return_value = ["TDD-1", "TDD-2"]
        mock_exists.return_value = True
        mock_stat_result = Mock()
        mock_stat_result.st_mtime = 1234567890
        mock_stat.return_value = mock_stat_result
        mock_load.return_value = mock_tdd_cycle
        
        result = project_storage.get_active_tdd_cycle()
        
        assert result == mock_tdd_cycle

    @patch('lib.project_storage.ProjectStorage.list_tdd_cycle_files')
    @patch('lib.project_storage.ProjectStorage.load_tdd_cycle')
    @patch('pathlib.Path.stat')
    @patch('pathlib.Path.exists')
    def test_get_active_tdd_cycle_complete_cycle(self, mock_exists, mock_stat, mock_load, mock_list, project_storage, mock_tdd_cycle):
        """Test getting active TDD cycle when cycle is complete."""
        mock_list.return_value = ["TDD-1"]
        mock_exists.return_value = True
        mock_stat_result = Mock()
        mock_stat_result.st_mtime = 1234567890
        mock_stat.return_value = mock_stat_result
        mock_tdd_cycle.is_complete.return_value = True
        mock_load.return_value = mock_tdd_cycle
        
        result = project_storage.get_active_tdd_cycle()
        
        assert result is None

    @patch('lib.project_storage.ProjectStorage.list_tdd_cycle_files')
    def test_get_active_tdd_cycle_no_files(self, mock_list, project_storage):
        """Test getting active TDD cycle when no files exist."""
        mock_list.return_value = []
        
        result = project_storage.get_active_tdd_cycle()
        
        assert result is None

    @patch('lib.project_storage.ProjectStorage.list_tdd_cycle_files')
    @patch('lib.project_storage.ProjectStorage.load_tdd_cycle')
    @patch('pathlib.Path.stat')
    @patch('pathlib.Path.exists')
    def test_get_active_tdd_cycle_import_fallback(self, mock_exists, mock_stat, mock_load, mock_list, project_storage, mock_tdd_cycle):
        """Test getting active TDD cycle with import fallback."""
        mock_list.return_value = ["TDD-1"]
        mock_exists.return_value = True
        mock_stat_result = Mock()
        mock_stat_result.st_mtime = 1234567890
        mock_stat.return_value = mock_stat_result
        mock_load.return_value = mock_tdd_cycle
        
        # Mock the import to simulate fallback behavior
        original_import = __builtins__['__import__']
        def mock_import(name, *args, **kwargs):
            if name == 'lib.tdd_models':
                raise ImportError("lib.tdd_models not found")
            return original_import(name, *args, **kwargs)
        
        with patch('builtins.__import__', side_effect=mock_import):
            result = project_storage.get_active_tdd_cycle()
            assert result == mock_tdd_cycle

    # Project Status Tests

    def test_project_exists_true(self, project_storage, temp_storage_dir):
        """Test project exists when .git directory is present."""
        git_dir = Path(temp_storage_dir) / ".git"
        git_dir.mkdir()
        
        assert project_storage.project_exists() is True

    def test_project_exists_false(self, project_storage):
        """Test project exists when .git directory is not present."""
        assert project_storage.project_exists() is False

    @patch('pathlib.Path.exists')
    def test_is_initialized_true(self, mock_exists, project_storage):
        """Test project is initialized when directories and files exist."""
        mock_exists.return_value = True
        
        assert project_storage.is_initialized() is True

    @patch('pathlib.Path.exists')
    def test_is_initialized_false(self, mock_exists, project_storage):
        """Test project is not initialized when files don't exist."""
        mock_exists.return_value = False
        
        assert project_storage.is_initialized() is False

    def test_get_project_name(self, project_storage, temp_storage_dir):
        """Test getting project name from directory."""
        expected_name = Path(temp_storage_dir).name
        assert project_storage.get_project_name() == expected_name

    @patch('builtins.open', new_callable=mock_open, read_data='{"state": "idle"}')
    @patch('pathlib.Path.exists')
    def test_load_status_success(self, mock_exists, mock_file, project_storage):
        """Test loading status successfully."""
        mock_exists.return_value = True
        
        result = project_storage.load_status()
        
        assert result == {"state": "idle"}
        mock_file.assert_called_once()

    @patch('pathlib.Path.exists')
    def test_load_status_no_file(self, mock_exists, project_storage):
        """Test loading status when file doesn't exist."""
        mock_exists.return_value = False
        
        result = project_storage.load_status()
        
        assert result == {}

    @patch('builtins.open', new_callable=mock_open, read_data='invalid json')
    @patch('pathlib.Path.exists')
    def test_load_status_json_error(self, mock_exists, mock_file, project_storage):
        """Test loading status with JSON decode error."""
        mock_exists.return_value = True
        
        result = project_storage.load_status()
        
        assert result == {}

    @patch('builtins.open', new_callable=mock_open)
    @patch('json.dump')
    @patch('lib.project_storage.ProjectStorage.ensure_directories')
    def test_save_status_success(self, mock_ensure, mock_json_dump, mock_file, project_storage):
        """Test saving status successfully."""
        status = {"state": "idle", "last_action": "test"}
        
        project_storage.save_status(status)
        
        mock_ensure.assert_called_once()
        mock_file.assert_called_once()
        mock_json_dump.assert_called_once_with(status, mock_file.return_value, indent=2)

    @patch('builtins.open', new_callable=mock_open)
    @patch('json.dump')
    @patch('lib.project_storage.ProjectStorage.ensure_directories')
    def test_save_status_exception(self, mock_ensure, mock_json_dump, mock_file, project_storage):
        """Test saving status with exception handling."""
        mock_json_dump.side_effect = Exception("Write failed")
        
        with patch('builtins.print') as mock_print:
            project_storage.save_status({"state": "idle"})
            mock_print.assert_called_once()

    # Architecture and Best Practices Tests

    @patch('pathlib.Path.read_text')
    @patch('pathlib.Path.exists')
    def test_get_architecture_content_success(self, mock_exists, mock_read_text, project_storage):
        """Test getting architecture content successfully."""
        mock_exists.return_value = True
        mock_read_text.return_value = "# Architecture\nContent here"
        
        result = project_storage.get_architecture_content()
        
        assert result == "# Architecture\nContent here"
        mock_read_text.assert_called_once()

    @patch('pathlib.Path.exists')
    def test_get_architecture_content_no_file(self, mock_exists, project_storage):
        """Test getting architecture content when file doesn't exist."""
        mock_exists.return_value = False
        
        result = project_storage.get_architecture_content()
        
        assert result == ""

    @patch('pathlib.Path.write_text')
    @patch('lib.project_storage.ProjectStorage.ensure_directories')
    def test_update_architecture(self, mock_ensure, mock_write_text, project_storage):
        """Test updating architecture content."""
        content = "# New Architecture\nUpdated content"
        
        project_storage.update_architecture(content)
        
        mock_ensure.assert_called_once()
        mock_write_text.assert_called_once_with(content)

    @patch('pathlib.Path.read_text')
    @patch('pathlib.Path.exists')
    def test_get_best_practices_content_success(self, mock_exists, mock_read_text, project_storage):
        """Test getting best practices content successfully."""
        mock_exists.return_value = True
        mock_read_text.return_value = "# Best Practices\nContent here"
        
        result = project_storage.get_best_practices_content()
        
        assert result == "# Best Practices\nContent here"
        mock_read_text.assert_called_once()

    @patch('pathlib.Path.exists')
    def test_get_best_practices_content_no_file(self, mock_exists, project_storage):
        """Test getting best practices content when file doesn't exist."""
        mock_exists.return_value = False
        
        result = project_storage.get_best_practices_content()
        
        assert result == ""

    @patch('pathlib.Path.write_text')
    @patch('lib.project_storage.ProjectStorage.ensure_directories')
    def test_update_best_practices(self, mock_ensure, mock_write_text, project_storage):
        """Test updating best practices content."""
        content = "# New Best Practices\nUpdated content"
        
        project_storage.update_best_practices(content)
        
        mock_ensure.assert_called_once()
        mock_write_text.assert_called_once_with(content)

    # TDD Metrics Tests

    @patch('builtins.open', new_callable=mock_open)
    @patch('json.dump')
    @patch('lib.project_storage.ProjectStorage.ensure_directories')
    def test_save_tdd_metrics_success(self, mock_ensure, mock_json_dump, mock_file, project_storage):
        """Test saving TDD metrics successfully."""
        metrics = {"cycles_completed": 5, "success_rate": 0.8}
        
        project_storage.save_tdd_metrics(metrics)
        
        mock_ensure.assert_called_once()
        mock_file.assert_called_once()
        mock_json_dump.assert_called_once_with(metrics, mock_file.return_value, indent=2)

    @patch('builtins.open', new_callable=mock_open)
    @patch('json.dump')
    @patch('lib.project_storage.ProjectStorage.ensure_directories')
    def test_save_tdd_metrics_exception(self, mock_ensure, mock_json_dump, mock_file, project_storage):
        """Test saving TDD metrics with exception handling."""
        mock_json_dump.side_effect = Exception("Write failed")
        
        with patch('builtins.print') as mock_print:
            project_storage.save_tdd_metrics({"test": "data"})
            mock_print.assert_called_once()

    @patch('builtins.open', new_callable=mock_open, read_data='{"cycles_completed": 5}')
    @patch('pathlib.Path.exists')
    def test_load_tdd_metrics_success(self, mock_exists, mock_file, project_storage):
        """Test loading TDD metrics successfully."""
        mock_exists.return_value = True
        
        result = project_storage.load_tdd_metrics()
        
        assert result == {"cycles_completed": 5}
        mock_file.assert_called_once()

    @patch('pathlib.Path.exists')
    def test_load_tdd_metrics_no_file(self, mock_exists, project_storage):
        """Test loading TDD metrics when file doesn't exist."""
        mock_exists.return_value = False
        
        result = project_storage.load_tdd_metrics()
        
        assert result == {}

    @patch('builtins.open', new_callable=mock_open, read_data='invalid json')
    @patch('pathlib.Path.exists')
    def test_load_tdd_metrics_json_error(self, mock_exists, mock_file, project_storage):
        """Test loading TDD metrics with JSON decode error."""
        mock_exists.return_value = True
        
        result = project_storage.load_tdd_metrics()
        
        assert result == {}

    # TDD Cycle State Tests

    @patch('builtins.open', new_callable=mock_open)
    @patch('json.dump')
    @patch('lib.project_storage.ProjectStorage.ensure_directories')
    def test_save_tdd_cycle_state_success(self, mock_ensure, mock_json_dump, mock_file, project_storage):
        """Test saving TDD cycle state successfully."""
        state_data = {"current_phase": "red", "needs_recovery": False}
        
        project_storage.save_tdd_cycle_state("TDD-1", state_data)
        
        mock_ensure.assert_called_once()
        mock_file.assert_called_once()
        mock_json_dump.assert_called_once_with(state_data, mock_file.return_value, indent=2)

    @patch('builtins.open', new_callable=mock_open)
    @patch('json.dump')
    @patch('lib.project_storage.ProjectStorage.ensure_directories')
    def test_save_tdd_cycle_state_exception(self, mock_ensure, mock_json_dump, mock_file, project_storage):
        """Test saving TDD cycle state with exception handling."""
        mock_json_dump.side_effect = Exception("Write failed")
        
        with patch('builtins.print') as mock_print:
            project_storage.save_tdd_cycle_state("TDD-1", {"test": "data"})
            mock_print.assert_called_once()

    @patch('builtins.open', new_callable=mock_open, read_data='{"current_phase": "red"}')
    @patch('pathlib.Path.exists')
    def test_load_tdd_cycle_state_success(self, mock_exists, mock_file, project_storage):
        """Test loading TDD cycle state successfully."""
        mock_exists.return_value = True
        
        result = project_storage.load_tdd_cycle_state("TDD-1")
        
        assert result == {"current_phase": "red"}
        mock_file.assert_called_once()

    @patch('pathlib.Path.exists')
    def test_load_tdd_cycle_state_no_file(self, mock_exists, project_storage):
        """Test loading TDD cycle state when file doesn't exist."""
        mock_exists.return_value = False
        
        result = project_storage.load_tdd_cycle_state("TDD-1")
        
        assert result == {}

    @patch('builtins.open', new_callable=mock_open, read_data='invalid json')
    @patch('pathlib.Path.exists')
    def test_load_tdd_cycle_state_json_error(self, mock_exists, mock_file, project_storage):
        """Test loading TDD cycle state with JSON decode error."""
        mock_exists.return_value = True
        
        result = project_storage.load_tdd_cycle_state("TDD-1")
        
        assert result == {}

    # Interrupted TDD Cycles Tests

    @patch('lib.project_storage.ProjectStorage.list_tdd_cycle_files')
    @patch('lib.project_storage.ProjectStorage.load_tdd_cycle')
    @patch('lib.project_storage.ProjectStorage.load_tdd_cycle_state')
    def test_get_interrupted_tdd_cycles_with_recovery(self, mock_load_state, mock_load_cycle, mock_list, project_storage, mock_tdd_cycle):
        """Test getting interrupted TDD cycles that need recovery."""
        mock_list.return_value = ["TDD-1", "TDD-2"]
        mock_load_cycle.return_value = mock_tdd_cycle
        mock_load_state.return_value = {"needs_recovery": True}
        
        result = project_storage.get_interrupted_tdd_cycles()
        
        assert result == ["TDD-1", "TDD-2"]

    @patch('lib.project_storage.ProjectStorage.list_tdd_cycle_files')
    @patch('lib.project_storage.ProjectStorage.load_tdd_cycle')
    @patch('lib.project_storage.ProjectStorage.load_tdd_cycle_state')
    def test_get_interrupted_tdd_cycles_no_recovery_needed(self, mock_load_state, mock_load_cycle, mock_list, project_storage, mock_tdd_cycle):
        """Test getting interrupted TDD cycles with no recovery needed."""
        mock_list.return_value = ["TDD-1"]
        mock_load_cycle.return_value = mock_tdd_cycle
        mock_load_state.return_value = {"needs_recovery": False}
        
        result = project_storage.get_interrupted_tdd_cycles()
        
        assert result == []

    @patch('lib.project_storage.ProjectStorage.list_tdd_cycle_files')
    @patch('lib.project_storage.ProjectStorage.load_tdd_cycle')
    def test_get_interrupted_tdd_cycles_complete_cycle(self, mock_load_cycle, mock_list, project_storage, mock_tdd_cycle):
        """Test getting interrupted TDD cycles when cycle is complete."""
        mock_list.return_value = ["TDD-1"]
        mock_tdd_cycle.is_complete.return_value = True
        mock_load_cycle.return_value = mock_tdd_cycle
        
        result = project_storage.get_interrupted_tdd_cycles()
        
        assert result == []

    # Test File Tracking Tests

    @patch('builtins.open', new_callable=mock_open, read_data='{"STORY-1": []}')
    @patch('pathlib.Path.exists')
    @patch('lib.project_storage.ProjectStorage.ensure_directories')
    @patch('datetime.datetime')
    def test_track_test_file_new_story(self, mock_datetime, mock_ensure, mock_exists, mock_file, project_storage):
        """Test tracking test file for new story."""
        mock_exists.return_value = True
        mock_datetime.now.return_value.isoformat.return_value = "2023-01-01T00:00:00"
        
        with patch('json.load', return_value={}), \
             patch('json.dump') as mock_json_dump:
            
            project_storage.track_test_file("STORY-1", "test_login.py", "created")
            
            mock_ensure.assert_called_once()
            mock_json_dump.assert_called_once()

    @patch('builtins.open', new_callable=mock_open)
    @patch('pathlib.Path.exists')
    @patch('lib.project_storage.ProjectStorage.ensure_directories')
    @patch('datetime.datetime')
    def test_track_test_file_update_existing(self, mock_datetime, mock_ensure, mock_exists, mock_file, project_storage):
        """Test tracking test file for existing entry."""
        mock_exists.return_value = True
        mock_datetime.now.return_value.isoformat.return_value = "2023-01-01T00:00:00"
        
        existing_data = {
            "STORY-1": [
                {
                    "file_path": "test_login.py",
                    "status": "created",
                    "created_at": "2023-01-01T00:00:00",
                    "updated_at": "2023-01-01T00:00:00"
                }
            ]
        }
        
        with patch('json.load', return_value=existing_data), \
             patch('json.dump') as mock_json_dump:
            
            project_storage.track_test_file("STORY-1", "test_login.py", "updated")
            
            mock_ensure.assert_called_once()
            mock_json_dump.assert_called_once()

    @patch('builtins.open', new_callable=mock_open)
    @patch('pathlib.Path.exists')
    @patch('lib.project_storage.ProjectStorage.ensure_directories')
    def test_track_test_file_json_error(self, mock_ensure, mock_exists, mock_file, project_storage):
        """Test tracking test file with JSON error."""
        mock_exists.return_value = True
        
        with patch('json.load', side_effect=json.JSONDecodeError("error", "doc", 0)), \
             patch('json.dump') as mock_json_dump:
            
            project_storage.track_test_file("STORY-1", "test_login.py", "created")
            
            mock_ensure.assert_called_once()
            mock_json_dump.assert_called_once()

    @patch('builtins.open', new_callable=mock_open)
    @patch('lib.project_storage.ProjectStorage.ensure_directories')
    @patch('json.dump')
    def test_track_test_file_save_exception(self, mock_json_dump, mock_ensure, mock_file, project_storage):
        """Test tracking test file with save exception."""
        mock_json_dump.side_effect = Exception("Write failed")
        
        with patch('pathlib.Path.exists', return_value=False), \
             patch('builtins.print') as mock_print:
            
            project_storage.track_test_file("STORY-1", "test_login.py", "created")
            mock_print.assert_called_once()

    @patch('builtins.open', new_callable=mock_open, read_data='{"STORY-1": ["test_data"]}')
    @patch('pathlib.Path.exists')
    def test_get_tracked_test_files_specific_story(self, mock_exists, mock_file, project_storage):
        """Test getting tracked test files for specific story."""
        mock_exists.return_value = True
        
        with patch('json.load', return_value={"STORY-1": ["test_data"]}):
            result = project_storage.get_tracked_test_files("STORY-1")
            assert result == ["test_data"]

    @patch('builtins.open', new_callable=mock_open, read_data='{"STORY-1": ["test_data"]}')
    @patch('pathlib.Path.exists')
    def test_get_tracked_test_files_all_stories(self, mock_exists, mock_file, project_storage):
        """Test getting tracked test files for all stories."""
        mock_exists.return_value = True
        
        with patch('json.load', return_value={"STORY-1": ["test_data"]}):
            result = project_storage.get_tracked_test_files()
            assert result == {"STORY-1": ["test_data"]}

    @patch('pathlib.Path.exists')
    def test_get_tracked_test_files_no_file(self, mock_exists, project_storage):
        """Test getting tracked test files when file doesn't exist."""
        mock_exists.return_value = False
        
        result = project_storage.get_tracked_test_files("STORY-1")
        assert result == {}

    @patch('builtins.open', new_callable=mock_open, read_data='invalid json')
    @patch('pathlib.Path.exists')
    def test_get_tracked_test_files_json_error(self, mock_exists, mock_file, project_storage):
        """Test getting tracked test files with JSON decode error."""
        mock_exists.return_value = True
        
        result = project_storage.get_tracked_test_files("STORY-1")
        assert result == {}

    # Backup and Restore Tests

    @patch('lib.project_storage.ProjectStorage.load_tdd_cycle')
    @patch('pathlib.Path.mkdir')
    @patch('builtins.open', new_callable=mock_open)
    @patch('json.dump')
    @patch('datetime.datetime')
    def test_backup_tdd_cycle_success(self, mock_datetime, mock_json_dump, mock_file, mock_mkdir, mock_load, project_storage, mock_tdd_cycle):
        """Test backing up TDD cycle successfully."""
        mock_load.return_value = mock_tdd_cycle
        mock_datetime.now.return_value.strftime.return_value = "20230101_120000"
        
        result = project_storage.backup_tdd_cycle("TDD-1")
        
        assert result is True
        mock_mkdir.assert_called_once()
        mock_file.assert_called_once()
        mock_json_dump.assert_called_once()

    @patch('lib.project_storage.ProjectStorage.load_tdd_cycle')
    def test_backup_tdd_cycle_no_cycle(self, mock_load, project_storage):
        """Test backing up TDD cycle when cycle doesn't exist."""
        mock_load.return_value = None
        
        result = project_storage.backup_tdd_cycle("TDD-1")
        
        assert result is False

    @patch('lib.project_storage.ProjectStorage.load_tdd_cycle')
    def test_backup_tdd_cycle_exception(self, mock_load, project_storage, mock_tdd_cycle):
        """Test backing up TDD cycle with exception handling."""
        mock_load.return_value = mock_tdd_cycle
        
        with patch('pathlib.Path.mkdir', side_effect=Exception("mkdir failed")), \
             patch('builtins.print') as mock_print:
            
            result = project_storage.backup_tdd_cycle("TDD-1")
            assert result is False
            mock_print.assert_called_once()

    @patch('pathlib.Path.exists')
    @patch('pathlib.Path.glob')
    @patch('builtins.open', new_callable=mock_open, read_data='{"id": "TDD-1"}')
    def test_restore_tdd_cycle_with_timestamp(self, mock_file, mock_glob, mock_exists, project_storage, mock_tdd_cycle):
        """Test restoring TDD cycle with specific timestamp."""
        mock_exists.return_value = True
        
        with patch('lib.tdd_models.TDDCycle') as mock_tdd_class:
            mock_tdd_class.from_dict.return_value = mock_tdd_cycle
            with patch('json.load', return_value={"id": "TDD-1"}):
                
                result = project_storage.restore_tdd_cycle_from_backup("TDD-1", "20230101_120000")
                
                assert result == mock_tdd_cycle
                mock_file.assert_called_once()

    @patch('pathlib.Path.exists')
    @patch('pathlib.Path.glob')
    @patch('builtins.open', new_callable=mock_open, read_data='{"id": "TDD-1"}')
    def test_restore_tdd_cycle_most_recent(self, mock_file, mock_glob, mock_exists, project_storage, mock_tdd_cycle):
        """Test restoring TDD cycle using most recent backup."""
        # Mock exists to return True for backup directory and backup file
        mock_exists.return_value = True
        
        mock_backup_file = Mock()
        mock_backup_file.__str__ = Mock(return_value="TDD-1_20230101_120000.json")
        mock_glob.return_value = [mock_backup_file]
        
        with patch('lib.tdd_models.TDDCycle') as mock_tdd_class:
            mock_tdd_class.from_dict.return_value = mock_tdd_cycle
            with patch('json.load', return_value={"id": "TDD-1"}):
                
                result = project_storage.restore_tdd_cycle_from_backup("TDD-1")
                
                assert result == mock_tdd_cycle

    @patch('pathlib.Path.exists')
    @patch('pathlib.Path.glob')
    @patch('builtins.open', new_callable=mock_open, read_data='{"id": "TDD-1"}')
    def test_restore_tdd_cycle_import_fallback(self, mock_file, mock_glob, mock_exists, project_storage, mock_tdd_cycle):
        """Test restoring TDD cycle with import fallback."""
        mock_exists.return_value = True
        mock_backup_file = Mock()
        mock_backup_file.__str__ = Mock(return_value="TDD-1_20230101_120000.json")
        mock_glob.return_value = [mock_backup_file]
        
        # Mock the import to simulate fallback behavior
        original_import = __builtins__['__import__']
        def mock_import(name, *args, **kwargs):
            if name == 'lib.tdd_models':
                raise ImportError("lib.tdd_models not found")
            return original_import(name, *args, **kwargs)
        
        with patch('builtins.__import__', side_effect=mock_import):
            with patch('tdd_models.TDDCycle') as mock_tdd_class:
                mock_tdd_class.from_dict.return_value = mock_tdd_cycle
                with patch('json.load', return_value={"id": "TDD-1"}):
                    result = project_storage.restore_tdd_cycle_from_backup("TDD-1")
                    assert result == mock_tdd_cycle

    @patch('pathlib.Path.glob')
    def test_restore_tdd_cycle_most_recent_file_not_found(self, mock_glob, project_storage):
        """Test restoring TDD cycle when most recent backup file doesn't exist."""
        # Mock the backup directory exists, but backup files exist
        with patch('pathlib.Path.exists') as mock_exists:
            # Directory exists but the specific backup file doesn't 
            def mock_exists_side_effect(self):
                path_str = str(self)
                if "backups/tdd_cycles" in path_str and not path_str.endswith(".json"):
                    return True  # Directory exists
                elif path_str.endswith("TDD-1_20230101_120000.json"):
                    return False  # This specific backup file doesn't exist (line 438)
                return True
            
            mock_exists.side_effect = mock_exists_side_effect
            
            # Create a mock backup file
            mock_backup_file = Mock()
            mock_backup_file.__str__ = Mock(return_value="TDD-1_20230101_120000.json")
            mock_glob.return_value = [mock_backup_file]
            
            result = project_storage.restore_tdd_cycle_from_backup("TDD-1")
            
            assert result is None

    @patch('pathlib.Path.exists')
    def test_restore_tdd_cycle_no_backup_dir(self, mock_exists, project_storage):
        """Test restoring TDD cycle when backup directory doesn't exist."""
        mock_exists.return_value = False
        
        result = project_storage.restore_tdd_cycle_from_backup("TDD-1")
        
        assert result is None

    @patch('pathlib.Path.exists')
    @patch('pathlib.Path.glob')
    def test_restore_tdd_cycle_no_backups(self, mock_glob, mock_exists, project_storage):
        """Test restoring TDD cycle when no backups exist."""
        mock_exists.return_value = True
        mock_glob.return_value = []
        
        result = project_storage.restore_tdd_cycle_from_backup("TDD-1")
        
        assert result is None

    @patch('pathlib.Path.exists')
    def test_restore_tdd_cycle_backup_file_not_found(self, mock_exists, project_storage):
        """Test restoring TDD cycle when backup file doesn't exist."""
        mock_exists.side_effect = lambda x: "backups/tdd_cycles" in str(x) and not str(x).endswith(".json")
        
        result = project_storage.restore_tdd_cycle_from_backup("TDD-1", "20230101_120000")
        
        assert result is None

    @patch('pathlib.Path.exists')
    @patch('builtins.open', new_callable=mock_open)
    def test_restore_tdd_cycle_exception(self, mock_file, mock_exists, project_storage):
        """Test restoring TDD cycle with exception handling."""
        mock_exists.return_value = True
        mock_file.side_effect = Exception("Read failed")
        
        with patch('builtins.print') as mock_print:
            result = project_storage.restore_tdd_cycle_from_backup("TDD-1", "20230101_120000")
            assert result is None
            mock_print.assert_called_once()

    # Cleanup Tests

    @patch('pathlib.Path.exists')
    @patch('pathlib.Path.glob')
    @patch('pathlib.Path.stat')
    @patch('pathlib.Path.unlink')
    @patch('datetime.datetime')
    def test_cleanup_old_tdd_backups_success(self, mock_datetime, mock_unlink, mock_stat, mock_glob, mock_exists, project_storage):
        """Test cleaning up old TDD backups successfully."""
        mock_exists.return_value = True
        mock_file = Mock()
        mock_stat_result = Mock()
        mock_stat_result.st_mtime = (datetime.now() - timedelta(days=40)).timestamp()
        mock_file.stat.return_value = mock_stat_result
        mock_glob.return_value = [mock_file]
        mock_datetime.now.return_value = datetime.now()
        
        project_storage.cleanup_old_tdd_backups(30)
        
        mock_file.unlink.assert_called_once()

    @patch('pathlib.Path.exists')
    def test_cleanup_old_tdd_backups_no_directory(self, mock_exists, project_storage):
        """Test cleaning up old TDD backups when directory doesn't exist."""
        mock_exists.return_value = False
        
        # Should not raise any exception
        project_storage.cleanup_old_tdd_backups(30)

    @patch('pathlib.Path.exists')
    @patch('pathlib.Path.glob')
    @patch('pathlib.Path.stat')
    @patch('datetime.datetime')
    def test_cleanup_old_tdd_backups_recent_files(self, mock_datetime, mock_stat, mock_glob, mock_exists, project_storage):
        """Test cleaning up old TDD backups with recent files."""
        mock_exists.return_value = True
        mock_file = Mock()
        mock_stat_result = Mock()
        mock_stat_result.st_mtime = (datetime.now() - timedelta(days=10)).timestamp()
        mock_file.stat.return_value = mock_stat_result
        mock_glob.return_value = [mock_file]
        mock_datetime.now.return_value = datetime.now()
        
        project_storage.cleanup_old_tdd_backups(30)
        
        # Should not delete recent files
        mock_file.unlink.assert_not_called()

    @patch('pathlib.Path.exists')
    @patch('pathlib.Path.glob')
    def test_cleanup_old_tdd_backups_exception(self, mock_glob, mock_exists, project_storage):
        """Test cleaning up old TDD backups with exception handling."""
        mock_exists.return_value = True
        mock_glob.side_effect = Exception("Glob failed")
        
        with patch('builtins.print') as mock_print:
            project_storage.cleanup_old_tdd_backups(30)
            mock_print.assert_called_once()

    # Integration Tests with Real File Operations

    def test_full_project_lifecycle(self, project_storage, sample_epic, sample_story, sample_sprint):
        """Test complete project lifecycle with real file operations."""
        # Initialize project
        assert project_storage.initialize_project() is True
        assert project_storage.is_initialized() is True
        
        # Create project data
        project_data = ProjectData(
            epics=[sample_epic],
            stories=[sample_story],
            sprints=[sample_sprint]
        )
        
        # Save and load project data
        project_storage.save_project_data(project_data)
        loaded_data = project_storage.load_project_data()
        
        assert len(loaded_data.epics) == 1
        assert len(loaded_data.stories) == 1
        assert len(loaded_data.sprints) == 1
        assert loaded_data.epics[0].id == sample_epic.id

    def test_multiple_sprints_persistence(self, project_storage, temp_storage_dir):
        """Test saving and loading multiple sprints."""
        sprints = [
            Sprint(id="SPRINT-1", goal="Goal 1"),
            Sprint(id="SPRINT-2", goal="Goal 2"),
            Sprint(id="SPRINT-3", goal="Goal 3")
        ]
        
        # Save all sprints
        for sprint in sprints:
            project_storage.save_sprint(sprint)
        
        # Verify all sprint files exist
        sprint_files = project_storage.list_sprint_files()
        assert len(sprint_files) == 3
        assert "SPRINT-1" in sprint_files
        assert "SPRINT-2" in sprint_files
        assert "SPRINT-3" in sprint_files
        
        # Load and verify each sprint
        for sprint in sprints:
            loaded_sprint = project_storage.load_sprint(sprint.id)
            assert loaded_sprint is not None
            assert loaded_sprint.id == sprint.id
            assert loaded_sprint.goal == sprint.goal

    def test_status_persistence_multiple_updates(self, project_storage):
        """Test multiple status updates."""
        statuses = [
            {"state": "idle", "action": "init"},
            {"state": "planning", "action": "create_sprint"},
            {"state": "active", "action": "start_development"},
            {"state": "review", "action": "complete_sprint"}
        ]
        
        for status in statuses:
            project_storage.save_status(status)
            loaded_status = project_storage.load_status()
            assert loaded_status == status

    def test_architecture_and_practices_workflow(self, project_storage):
        """Test architecture and best practices workflow."""
        # Test architecture updates
        arch_content_v1 = "# Architecture v1\nInitial design"
        project_storage.update_architecture(arch_content_v1)
        assert project_storage.get_architecture_content() == arch_content_v1
        
        arch_content_v2 = "# Architecture v2\nUpdated design with new components"
        project_storage.update_architecture(arch_content_v2)
        assert project_storage.get_architecture_content() == arch_content_v2
        
        # Test best practices updates
        practices_v1 = "# Practices v1\nInitial guidelines"
        project_storage.update_best_practices(practices_v1)
        assert project_storage.get_best_practices_content() == practices_v1
        
        practices_v2 = "# Practices v2\nUpdated guidelines with TDD focus"
        project_storage.update_best_practices(practices_v2)
        assert project_storage.get_best_practices_content() == practices_v2

    def test_error_resilience_corrupted_files(self, project_storage):
        """Test system resilience with corrupted JSON files."""
        # Initialize project first
        project_storage.initialize_project()
        
        # Corrupt the backlog file
        with open(project_storage.backlog_file, 'w') as f:
            f.write("invalid json content {{{")
        
        # Should return empty ProjectData instead of crashing
        loaded_data = project_storage.load_project_data()
        assert isinstance(loaded_data, ProjectData)
        assert loaded_data.epics == []
        
        # Should still be able to save new data
        new_data = ProjectData(epics=[Epic(title="Recovery Epic")])
        project_storage.save_project_data(new_data)
        
        # Verify recovery
        recovered_data = project_storage.load_project_data()
        assert len(recovered_data.epics) == 1
        assert recovered_data.epics[0].title == "Recovery Epic"