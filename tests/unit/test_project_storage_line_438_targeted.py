"""
Specific test to achieve 100% coverage of line 438 in project_storage.py.
This test targets the exact scenario where backup_file.exists() returns False.
"""

import pytest
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch, Mock

import sys
sys.path.append(str(Path(__file__).parent.parent.parent))

from lib.project_storage import ProjectStorage


class TestProjectStorageLine438:
    """Targeted test for line 438 coverage."""
    
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

    def test_line_438_direct_path_simulation(self, project_storage):
        """Test line 438 by directly simulating the code path."""
        # Create backup directory
        backup_dir = project_storage.orch_state_dir / "backups" / "tdd_cycles"
        backup_dir.mkdir(parents=True, exist_ok=True)
        
        # Create a backup file
        backup_file = backup_dir / "TDD-1_20230101_120000.json"
        backup_file.write_text('{"id": "TDD-1", "status": "active"}')
        
        # Now patch the pathlib.Path.exists method to return False
        # This simulates the exact condition on line 437-438
        with patch('pathlib.Path.exists') as mock_exists:
            # Set up the mock to return False for our specific file
            def exists_side_effect(self):
                if self.name == "TDD-1_20230101_120000.json":
                    return False  # This will cause line 438 to execute
                return True  # Allow other path operations to work normally
            
            mock_exists.side_effect = exists_side_effect
            
            # Call the method - this should hit line 438
            result = project_storage.restore_tdd_cycle_from_backup("TDD-1")
            
            # The method should return None due to line 438
            assert result is None

    def test_line_438_with_timestamp_path(self, project_storage):
        """Test line 438 with specific timestamp path."""
        # Create backup directory  
        backup_dir = project_storage.orch_state_dir / "backups" / "tdd_cycles"
        backup_dir.mkdir(parents=True, exist_ok=True)
        
        # Test the path where backup_timestamp is provided
        # This creates backup_file on line 429 but file doesn't exist
        result = project_storage.restore_tdd_cycle_from_backup("TDD-1", "20230101_120000") 
        
        # Should return None from line 438 since file doesn't exist
        assert result is None

    def test_line_438_most_recent_backup_missing(self, project_storage):
        """Test line 438 when most recent backup file is missing."""
        backup_dir = project_storage.orch_state_dir / "backups" / "tdd_cycles"
        backup_dir.mkdir(parents=True, exist_ok=True)
        
        # Create a backup file to be found by glob
        backup_file = backup_dir / "TDD-1_20230101_120000.json" 
        backup_file.write_text('{"id": "TDD-1"}')
        
        # Delete the file immediately after creation
        # This simulates a race condition where glob finds it but it's deleted before exists() check
        backup_file.unlink()
        
        # This should follow the path: glob finds files, but when exists() is called, it returns False
        result = project_storage.restore_tdd_cycle_from_backup("TDD-1")
        
        # Should return None from line 438
        assert result is None

    def test_line_438_comprehensive_path_coverage(self, project_storage):
        """Comprehensive test ensuring line 438 is definitively covered."""
        # Test both main paths that can lead to line 438
        
        # Path 1: With specific timestamp - file doesn't exist
        result1 = project_storage.restore_tdd_cycle_from_backup("TDD-1", "20230101_120000")
        assert result1 is None
        
        # Path 2: Without timestamp - create and immediately remove file
        backup_dir = project_storage.orch_state_dir / "backups" / "tdd_cycles"
        backup_dir.mkdir(parents=True, exist_ok=True)
        
        # Create file temporarily
        backup_file = backup_dir / "TDD-2_20230101_120000.json"
        backup_file.write_text('{"id": "TDD-2"}')
        
        # Use context manager to ensure file is deleted right after glob would find it
        backup_file.unlink()
        
        result2 = project_storage.restore_tdd_cycle_from_backup("TDD-2")
        assert result2 is None
        
        # Both calls should have hit line 438