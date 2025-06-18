"""
Final coverage test for project_storage.py line 438.

This test specifically targets the uncovered line 438 in the restore_tdd_cycle_from_backup method.
"""

import pytest
import tempfile
import shutil
from pathlib import Path
from unittest.mock import Mock, patch

import sys
sys.path.append(str(Path(__file__).parent.parent.parent))

from lib.project_storage import ProjectStorage


class TestProjectStorageFinalCoverage:
    """Test to achieve 100% coverage by hitting line 438."""
    
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

    def test_restore_tdd_cycle_backup_file_exists_false_line_438(self, project_storage):
        """Test restore TDD cycle when backup_file.exists() returns False - targets line 438."""
        # Create real directory structure first
        backup_dir = project_storage.orch_state_dir / "backups" / "tdd_cycles"
        backup_dir.mkdir(parents=True, exist_ok=True)
        
        # Create a file, then mock pathlib to make it appear to glob but not exist
        backup_file = backup_dir / "TDD-1_20230101_120000.json"
        backup_file.write_text('{"id": "TDD-1"}')
        
        # Use monkeypatch to override the exists method specifically for our file
        original_exists = backup_file.exists
        
        def fake_exists():
            return False
            
        # Monkey patch the exists method on this specific file object
        # This is a hack but necessary since Path methods are read-only in normal circumstances
        import types
        backup_file.exists = types.MethodType(lambda self: False, backup_file)
        
        try:
            # Now call the method - glob will find the file but exists() will return False
            result = project_storage.restore_tdd_cycle_from_backup("TDD-1")
            assert result is None
        finally:
            # Restore original method
            backup_file.exists = original_exists

    def test_restore_tdd_cycle_no_timestamp_backup_file_not_exists(self, project_storage):
        """Test restore without timestamp when most recent backup file doesn't exist."""
        with patch('pathlib.Path.exists') as mock_exists, \
             patch('pathlib.Path.glob') as mock_glob:
            
            # Setup: backup directory exists
            def exists_side_effect(path_obj):
                if "backups/tdd_cycles" in str(path_obj) and not str(path_obj).endswith(".json"):
                    return True  # Directory exists
                elif str(path_obj).endswith(".json"):
                    return False  # Backup file doesn't exist
                return False
            
            mock_exists.side_effect = exists_side_effect
            
            # Create a mock Path object for the backup file
            mock_backup_file = Mock(spec=Path)
            mock_backup_file.__lt__ = Mock(return_value=False)
            mock_backup_file.__gt__ = Mock(return_value=True) 
            mock_backup_file.__str__ = Mock(return_value="TDD-1_20230101_120000.json")
            mock_backup_file.exists.return_value = False  # This will trigger line 438
            
            mock_glob.return_value = [mock_backup_file]
            
            result = project_storage.restore_tdd_cycle_from_backup("TDD-1")
            
            assert result is None

    def test_restore_tdd_cycle_with_specific_timestamp_not_exists(self, project_storage):
        """Test restore with specific timestamp when file doesn't exist."""
        with patch('pathlib.Path.exists') as mock_exists:
            
            def exists_side_effect(path_obj):
                path_str = str(path_obj)
                if "backups/tdd_cycles" in path_str and path_str.endswith("backups/tdd_cycles"):
                    return True  # Directory exists
                elif path_str.endswith("TDD-1_20230101_120000.json"):
                    return False  # Specific backup file doesn't exist - triggers line 438
                return False
            
            mock_exists.side_effect = exists_side_effect
            
            result = project_storage.restore_tdd_cycle_from_backup("TDD-1", "20230101_120000")
            
            assert result is None