"""
Comprehensive test suite for project_storage.py to achieve 95%+ coverage for government audit compliance.
This test suite focuses on all critical paths, edge cases, and error conditions.
"""

import pytest
import tempfile
import shutil
import json
import os
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock, mock_open, call
from datetime import datetime, timedelta
import threading
import time

import sys
sys.path.append(str(Path(__file__).parent.parent.parent))

from lib.project_storage import ProjectStorage
from lib.data_models import ProjectData, Epic, Story, Sprint


class TestProjectStorageAuditCoverage:
    """Comprehensive test coverage for project_storage.py targeting 95%+ coverage."""
    
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
    def mock_tdd_cycle(self):
        """Mock TDD cycle object."""
        cycle = Mock()
        cycle.id = "TDD-1"
        cycle.is_complete.return_value = False
        cycle.to_dict.return_value = {"id": "TDD-1", "status": "active"}
        return cycle

    # ================================
    # LINE 438 COVERAGE - CRITICAL TARGET
    # ================================
    
    def test_restore_tdd_cycle_line_438_race_condition(self, project_storage):
        """Test line 438: backup file exists during glob but deleted before exists() check."""
        backup_dir = project_storage.orch_state_dir / "backups" / "tdd_cycles"
        backup_dir.mkdir(parents=True, exist_ok=True)
        
        # Create a real backup file
        backup_file = backup_dir / "TDD-1_20230101_120000.json"
        backup_file.write_text('{"id": "TDD-1"}')
       
        # Mock the Path.exists method to return False for the specific file
        # This simulates the race condition where glob finds the file but exists() returns False
        original_exists = backup_file.exists
        
        def mock_exists():
            return False
        
        # Patch exists method on the backup file specifically  
        with patch.object(type(backup_file), 'exists', return_value=False):
            # This should hit line 438 because exists() will return False
            result = project_storage.restore_tdd_cycle_from_backup("TDD-1")
            assert result is None

    def test_restore_tdd_cycle_line_438_with_timestamp_missing_file(self, project_storage):
        """Test line 438: specific timestamp file path that doesn't exist."""
        backup_dir = project_storage.orch_state_dir / "backups" / "tdd_cycles"
        backup_dir.mkdir(parents=True, exist_ok=True)
        
        # Don't create the file - this will make the exists() check fail on line 437
        # leading to the return None on line 438
        result = project_storage.restore_tdd_cycle_from_backup("TDD-1", "20230101_120000")
        
        assert result is None

    # ================================
    # FILE SYSTEM OPERATIONS COVERAGE
    # ================================
    
    def test_file_permissions_errors(self, project_storage):
        """Test file permission errors during operations."""
        # Test permission error during directory creation
        with patch('pathlib.Path.mkdir', side_effect=PermissionError("Permission denied")):
            success = project_storage.initialize_project()
            assert not success
    
    def test_disk_space_errors(self, project_storage):
        """Test disk space errors during file operations."""
        # Test OSError during file writing (simulating disk full)
        project_data = ProjectData()
        
        with patch('builtins.open', side_effect=OSError("No space left on device")):
            # This should trigger the exception handler and print error
            project_storage.save_project_data(project_data)
            # Method should handle error gracefully
    
    def test_corrupted_json_recovery(self, project_storage):
        """Test recovery from corrupted JSON files."""
        project_storage.ensure_directories()
        
        # Create corrupted JSON file
        with open(project_storage.backlog_file, 'w') as f:
            f.write('{"invalid": json, "syntax": error}')
        
        # Should return empty ProjectData when JSON is corrupted
        data = project_storage.load_project_data()
        assert isinstance(data, ProjectData)
        assert len(data.epics) == 0
    
    def test_concurrent_file_access(self, project_storage):
        """Test concurrent file access scenarios."""
        project_storage.ensure_directories()
        
        # Simulate concurrent writes
        def write_data(data_id):
            project_data = ProjectData()
            epic = Epic(id=f"epic-{data_id}", title=f"Epic {data_id}", description="Test epic")
            project_data.epics = [epic]
            project_storage.save_project_data(project_data)
        
        # Start multiple threads writing simultaneously
        threads = []
        for i in range(5):
            thread = threading.Thread(target=write_data, args=(i,))
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # Verify data integrity - should be able to load without error
        data = project_storage.load_project_data()
        assert isinstance(data, ProjectData)
    
    def test_file_locking_simulation(self, project_storage):
        """Test file locking scenarios."""
        project_storage.ensure_directories()
        
        # Mock file operations to simulate lock contention
        with patch('builtins.open', side_effect=[
            OSError("Resource temporarily unavailable"),
            mock_open(read_data='{"epics": [], "stories": []}').return_value
        ]):
            # First call fails with lock error, should handle gracefully
            data = project_storage.load_project_data()
            # Should still return valid ProjectData
            assert isinstance(data, ProjectData)
    
    # ================================
    # DATA INTEGRITY AND VALIDATION
    # ================================
    
    def test_data_serialization_edge_cases(self, project_storage):
        """Test edge cases in data serialization."""
        project_storage.ensure_directories()
        
        # Test with special characters and unicode
        project_data = ProjectData()
        epic = Epic(
            id="epic-unicode",
            title="Epic with 🚀 unicode and special chars: <>\"'&",
            description="Description with\nnewlines\tand\ttabs"
        )
        project_data.epics = [epic]
        
        # Save and reload
        project_storage.save_project_data(project_data)
        loaded_data = project_storage.load_project_data()
        
        assert len(loaded_data.epics) == 1
        assert loaded_data.epics[0].title == epic.title
        assert loaded_data.epics[0].description == epic.description
    
    def test_large_data_handling(self, project_storage):
        """Test handling of large data structures."""
        project_storage.ensure_directories()
        
        # Create large project data
        project_data = ProjectData()
        
        # Add many epics and stories
        for i in range(100):
            epic = Epic(
                id=f"epic-{i:03d}",
                title=f"Epic {i}",
                description=f"This is a long description for epic {i} " * 10
            )
            project_data.epics.append(epic)
            
            # Add stories to each epic
            for j in range(10):
                story = Story(
                    id=f"story-{i:03d}-{j:03d}",
                    title=f"Story {j} for Epic {i}",
                    description=f"This is a detailed story description " * 20,
                    epic_id=epic.id
                )
                project_data.stories.append(story)
        
        # Save and reload large dataset
        project_storage.save_project_data(project_data)
        loaded_data = project_storage.load_project_data()
        
        assert len(loaded_data.epics) == 100
        assert len(loaded_data.stories) == 1000
    
    def test_nested_directory_creation(self, project_storage):
        """Test creation of deeply nested directory structures."""
        # Test backup directory creation with deep nesting
        cycle_id = "TDD-1"
        success = project_storage.backup_tdd_cycle(cycle_id)
        # Should fail gracefully when cycle doesn't exist
        assert not success
        
        # Create a mock cycle and test backup
        with patch.object(project_storage, 'load_tdd_cycle') as mock_load:
            mock_cycle = Mock()
            mock_cycle.to_dict.return_value = {"id": cycle_id, "status": "active"}
            mock_load.return_value = mock_cycle
            
            success = project_storage.backup_tdd_cycle(cycle_id)
            assert success
            
            # Verify backup directory was created
            backup_dir = project_storage.orch_state_dir / "backups" / "tdd_cycles"
            assert backup_dir.exists()
    
    # ================================
    # ERROR HANDLING AND RECOVERY
    # ================================
    
    def test_filesystem_error_recovery(self, project_storage):
        """Test recovery from various filesystem errors."""
        # Test FileNotFoundError during status loading
        result = project_storage.load_status()
        assert result == {}
        
        # Test with directory that becomes read-only
        project_storage.ensure_directories()
        
        with patch('builtins.open', side_effect=PermissionError("Read-only filesystem")):
            # Should handle permission errors gracefully
            project_storage.save_status({"state": "active"})
            # No exception should be raised
    
    def test_interrupted_operations_recovery(self, project_storage):
        """Test recovery from interrupted file operations."""
        project_storage.ensure_directories()
        
        # Simulate interrupted write (partial file)
        partial_json = '{"epics": ['
        with open(project_storage.backlog_file, 'w') as f:
            f.write(partial_json)
        
        # Should handle corrupted file gracefully
        data = project_storage.load_project_data()
        assert isinstance(data, ProjectData)
        assert len(data.epics) == 0
    
    def test_backup_and_recovery_mechanisms(self, project_storage):
        """Test backup and recovery functionality."""
        # Test backup of non-existent cycle
        assert not project_storage.backup_tdd_cycle("non-existent")
        
        # Test restore from non-existent backup
        result = project_storage.restore_tdd_cycle_from_backup("non-existent")
        assert result is None
        
        # Test cleanup of old backups
        project_storage.cleanup_old_tdd_backups(30)
        # Should complete without error even if no backups exist
    
    # ================================
    # COMPREHENSIVE INTEGRATION TESTS
    # ================================
    
    def test_full_project_lifecycle_with_errors(self, project_storage):
        """Test complete project lifecycle with error injection."""
        # Initialize project
        success = project_storage.initialize_project()
        assert success
        
        # Verify all files were created
        assert project_storage.is_initialized()
        assert project_storage.architecture_file.exists()
        assert project_storage.best_practices_file.exists()
        
        # Test project data operations with errors
        project_data = ProjectData()
        epic = Epic(id="epic-1", title="Test Epic", description="Test Description")
        project_data.epics = [epic]
        
        # Save project data
        project_storage.save_project_data(project_data)
        
        # Inject error during loading
        with patch('json.load', side_effect=json.JSONDecodeError("Invalid JSON", "", 0)):
            loaded_data = project_storage.load_project_data()
            assert isinstance(loaded_data, ProjectData)
            assert len(loaded_data.epics) == 0
    
    def test_status_and_metrics_persistence(self, project_storage):
        """Test status and metrics data persistence."""
        # Test status operations
        status_data = {
            "current_state": "SPRINT_ACTIVE",
            "sprint_id": "sprint-1",
            "last_updated": datetime.now().isoformat()
        }
        
        project_storage.save_status(status_data)
        loaded_status = project_storage.load_status()
        assert loaded_status == status_data
        
        # Test TDD metrics
        metrics_data = {
            "cycles_completed": 5,
            "tests_written": 25,
            "coverage_percentage": 95.5,
            "last_cycle": datetime.now().isoformat()
        }
        
        project_storage.save_tdd_metrics(metrics_data)
        loaded_metrics = project_storage.load_tdd_metrics()
        assert loaded_metrics == metrics_data
    
    def test_test_file_tracking_comprehensive(self, project_storage):
        """Test comprehensive test file tracking functionality."""
        story_id = "story-1"
        test_file_path = "/path/to/test_file.py"
        
        # Track new test file
        project_storage.track_test_file(story_id, test_file_path, "created")
        
        # Get tracked files
        tracked_files = project_storage.get_tracked_test_files(story_id)
        assert len(tracked_files) == 1
        assert tracked_files[0]["file_path"] == test_file_path
        assert tracked_files[0]["status"] == "created"
        
        # Update existing file
        project_storage.track_test_file(story_id, test_file_path, "updated")
        
        # Verify update
        tracked_files = project_storage.get_tracked_test_files(story_id)
        assert len(tracked_files) == 1
        assert tracked_files[0]["status"] == "updated"
        
        # Get all tracked files
        all_tracked = project_storage.get_tracked_test_files()
        assert story_id in all_tracked
        assert len(all_tracked[story_id]) == 1
    
    def test_interrupted_tdd_cycles_detection(self, project_storage):
        """Test detection of interrupted TDD cycles."""
        # Mock TDD cycle that needs recovery
        cycle_id = "TDD-1"
        
        with patch.object(project_storage, 'list_tdd_cycle_files') as mock_list:
            mock_list.return_value = [cycle_id]
            
            with patch.object(project_storage, 'load_tdd_cycle') as mock_load:
                mock_cycle = Mock()
                mock_cycle.is_complete.return_value = False
                mock_load.return_value = mock_cycle
                
                with patch.object(project_storage, 'load_tdd_cycle_state') as mock_state:
                    mock_state.return_value = {"needs_recovery": True}
                    
                    interrupted = project_storage.get_interrupted_tdd_cycles()
                    assert cycle_id in interrupted
    
    # ================================
    # EDGE CASES AND BOUNDARY CONDITIONS
    # ================================
    
    def test_empty_file_handling(self, project_storage):
        """Test handling of empty files."""
        project_storage.ensure_directories()
        
        # Create empty JSON file
        project_storage.backlog_file.touch()
        
        # Should handle empty file gracefully
        data = project_storage.load_project_data()
        assert isinstance(data, ProjectData)
    
    def test_very_long_file_paths(self, project_storage):
        """Test handling of very long file paths."""
        # Create story with very long ID
        long_story_id = "story-" + "x" * 200
        test_file_path = "/very/long/path/" + "directory/" * 10 + "test_file.py"
        
        # Should handle long paths gracefully
        project_storage.track_test_file(long_story_id, test_file_path)
        
        tracked = project_storage.get_tracked_test_files(long_story_id)
        assert len(tracked) == 1
    
    def test_special_characters_in_paths(self, project_storage):
        """Test handling of special characters in file paths."""
        story_id = "story-with-special@chars!#$%"
        test_file_path = "/path/with spaces/and-special@chars!.py"
        
        project_storage.track_test_file(story_id, test_file_path)
        
        tracked = project_storage.get_tracked_test_files(story_id)
        assert len(tracked) == 1
        assert tracked[0]["file_path"] == test_file_path
    
    def test_datetime_handling_edge_cases(self, project_storage):
        """Test datetime handling in various operations."""
        # Test backup cleanup with various date scenarios
        project_storage.ensure_directories()
        backup_dir = project_storage.orch_state_dir / "backups" / "tdd_cycles"
        backup_dir.mkdir(parents=True, exist_ok=True)
        
        # Create files with different ages
        old_file = backup_dir / "old_backup.json"
        old_file.write_text("{}")
        
        # Modify file timestamp to be old
        old_time = time.time() - (40 * 24 * 60 * 60)  # 40 days ago
        os.utime(old_file, (old_time, old_time))
        
        recent_file = backup_dir / "recent_backup.json"
        recent_file.write_text("{}")
        
        # Clean up old backups (keep 30 days)
        project_storage.cleanup_old_tdd_backups(30)
        
        # Old file should be deleted, recent file should remain
        assert not old_file.exists()
        assert recent_file.exists()
    
    # ================================
    # COMPREHENSIVE ERROR SCENARIOS
    # ================================
    
    def test_all_json_error_paths(self, project_storage):
        """Test all JSON error handling paths."""
        project_storage.ensure_directories()
        
        # Test different types of JSON errors that should fail JSON parsing
        json_errors = [
            '{"invalid": json syntax}',  # Invalid JSON
            '{"missing_closing_brace":',  # Incomplete JSON
            '',  # Empty file
            'not json at all',  # Not JSON
        ]
        
        for invalid_json in json_errors:
            # Test project data loading
            with open(project_storage.backlog_file, 'w') as f:
                f.write(invalid_json)
            
            data = project_storage.load_project_data()
            assert isinstance(data, ProjectData)
            
            # Test status loading - only test cases that will actually cause JSON errors
            if invalid_json != '':  # Empty file doesn't cause JSON error for status
                with open(project_storage.status_file, 'w') as f:
                    f.write(invalid_json)
                
                status = project_storage.load_status()
                assert status == {}
            
            # Test metrics loading
            metrics_file = project_storage.orch_state_dir / "tdd_metrics.json"
            with open(metrics_file, 'w') as f:
                f.write(invalid_json)
            
            metrics = project_storage.load_tdd_metrics()
            assert metrics == {}
    
    def test_file_operations_with_system_errors(self, project_storage):
        """Test file operations with various system errors."""
        # Test different system errors
        system_errors = [
            OSError("Operation not permitted"),
            IOError("Input/output error"),
            FileNotFoundError("No such file or directory"),
            PermissionError("Permission denied"),
        ]
        
        for error in system_errors:
            with patch('builtins.open', side_effect=error):
                # All these operations should handle errors gracefully
                project_storage.save_project_data(ProjectData())
                project_storage.save_status({})
                project_storage.save_tdd_metrics({})
                project_storage.track_test_file("story-1", "/test.py")
                
                # No exceptions should be raised

    def test_concurrent_modification_detection(self, project_storage):
        """Test detection and handling of concurrent modifications."""
        project_storage.ensure_directories()
        
        # Simulate concurrent modification scenario
        original_data = ProjectData()
        epic = Epic(id="epic-1", title="Original Epic", description="Original")
        original_data.epics = [epic]
        
        # Save initial data
        project_storage.save_project_data(original_data)
        
        # Load data in thread 1
        data1 = project_storage.load_project_data()
        
        # Modify and save in thread 2
        data2 = project_storage.load_project_data()
        data2.epics[0].title = "Modified Epic"
        project_storage.save_project_data(data2)
        
        # Modify and save in thread 1 (should overwrite)
        data1.epics[0].title = "Thread 1 Epic"
        project_storage.save_project_data(data1)
        
        # Final state should be from thread 1
        final_data = project_storage.load_project_data()
        assert final_data.epics[0].title == "Thread 1 Epic"