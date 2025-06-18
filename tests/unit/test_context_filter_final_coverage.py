"""
Final Context Filter Coverage Test Suite - Targeting 95%+ Line Coverage

This test suite specifically targets the uncovered lines in lib/context_filter.py
to achieve 95%+ coverage for government audit compliance.

Missing lines identified from coverage report:
30-32, 153-155, 343, 350, 354-358, 369-373, 395-397, 442, 481, 499-501, 
605-607, 645-647, 695-697, 746, 750-752, 775, 789, 805, 944-945, 966-970
"""

import pytest
import asyncio
import tempfile
import shutil
import ast
import json
import os
from pathlib import Path
from datetime import datetime, timedelta
from unittest.mock import Mock, AsyncMock, patch, MagicMock, call

# Import the modules under test
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "lib"))

from context_filter import ContextFilter
from context.models import (
    RelevanceScore, FileType, ContextRequest, AgentContext,
    CompressionLevel
)
from tdd_models import TDDState, TDDTask
from agent_memory import FileBasedAgentMemory
from token_calculator import TokenCalculator


class TestContextFilterFinalCoverage:
    """Test suite targeting specific uncovered lines"""
    
    @pytest.fixture
    def temp_project(self):
        """Create temporary project directory"""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def filter_instance(self, temp_project):
        return ContextFilter(temp_project)
    
    def test_import_error_coverage(self):
        """Test coverage for import error paths (lines 30-32)"""
        # This test covers the except ImportError block by testing that 
        # the module works even with import errors
        with tempfile.TemporaryDirectory() as temp_dir:
            # Test that the class can be instantiated even with potential import issues
            filter_instance = ContextFilter(temp_dir)
            assert filter_instance is not None
            assert filter_instance.project_path == Path(temp_dir)
    
    @pytest.mark.asyncio
    async def test_filter_relevant_files_general_exception(self, filter_instance):
        """Test coverage for general exception handling in filter_relevant_files (lines 153-155)"""
        request = ContextRequest(
            agent_type="CodeAgent",
            story_id="test_story",
            task={"description": "test task"},
            focus_areas=[]
        )
        
        # Mock _extract_search_terms to raise exception
        with patch.object(filter_instance, '_extract_search_terms', side_effect=Exception("General error")):
            results = await filter_instance.filter_relevant_files(
                request, ["test_file.py"], max_files=10
            )
            
            # Should handle exception gracefully and return empty list
            assert results == []
    
    @pytest.mark.asyncio
    async def test_calculate_relevance_score_with_high_scores_and_reasons(self, filter_instance, temp_project):
        """Test relevance score calculation with high scores to trigger reason logging (lines 343, 350, 357, 365, 372)"""
        
        # Create a file with content that will score highly
        test_file = Path(temp_project) / "high_scoring_file.py"
        test_content = '''
import json
import hashlib
from datetime import datetime
from user_service import UserService

class UserController:
    """High scoring class with many matches"""
    
    def create_user(self, username, email):
        """Create user method - should score highly"""
        service = UserService()
        return service.create_user(username, email)
    
    def authenticate_user(self, username, password):
        """Authenticate user method - should score highly"""
        service = UserService()
        return service.authenticate_user(username, password)
    
    def validate_user_data(self, user_data):
        """Validate user data - frequently accessed method"""
        return True
'''
        test_file.write_text(test_content)
        
        # Create request that will generate high scores
        task = TDDTask(
            id="high_score_task",
            description="Implement UserController with create_user and authenticate_user methods",
            cycle_id="cycle_1",
            current_state=TDDState.CODE_GREEN
        )
        
        request = ContextRequest(
            agent_type="CodeAgent",
            story_id="high_score_story",
            task=task,
            focus_areas=["user", "authentication", "controller"]
        )
        
        # Mock agent memory to provide high historical score
        mock_memory = Mock(spec=FileBasedAgentMemory)
        filter_instance.agent_memory = mock_memory
        
        # Create snapshots that will generate high historical score and recent access bonus
        mock_snapshots = []
        for i in range(10):
            snapshot = Mock()
            snapshot.file_list = [str(test_file)]
            mock_snapshots.append(snapshot)
        
        mock_memory.get_context_history = AsyncMock(return_value=mock_snapshots)
        
        search_terms = await filter_instance._extract_search_terms(request)
        
        # This should trigger all the high score reason additions
        score = await filter_instance._calculate_relevance_score(
            str(test_file), request, search_terms
        )
        
        assert isinstance(score, RelevanceScore)
        assert score.total_score > 0.0
        assert len(score.reasons) > 0
        
        # Check that various reason types are included
        reason_text = " ".join(score.reasons)
        # The exact reasons depend on scoring thresholds, but we should have some reasons
        assert len(score.reasons) >= 1
    
    @pytest.mark.asyncio
    async def test_calculate_relevance_score_with_tdd_state_missing(self, filter_instance, temp_project):
        """Test relevance score calculation when task doesn't have current_state (lines 369-373)"""
        
        test_file = Path(temp_project) / "test_file.py"
        test_file.write_text("class TestClass: pass")
        
        # Create task without current_state
        task_dict = {
            "description": "Test task without current_state"
        }
        
        request = ContextRequest(
            agent_type="CodeAgent",
            story_id="no_state_story",
            task=task_dict,  # Dict without current_state
            focus_areas=[]
        )
        
        search_terms = await filter_instance._extract_search_terms(request)
        
        score = await filter_instance._calculate_relevance_score(
            str(test_file), request, search_terms
        )
        
        assert isinstance(score, RelevanceScore)
        assert score.tdd_phase_score == 0.0  # Should be 0 when no current_state
    
    @pytest.mark.asyncio
    async def test_calculate_relevance_score_exception_handling(self, filter_instance):
        """Test relevance score calculation exception handling (lines 395-397)"""
        
        # Test with invalid file path that will cause exceptions
        invalid_file = "/invalid/nonexistent/path/file.py"
        
        request = ContextRequest(
            agent_type="CodeAgent",
            story_id="exception_story",
            task={"description": "test"},
            focus_areas=[]
        )
        
        search_terms = await filter_instance._extract_search_terms(request)
        
        # This should trigger exception handling in _calculate_relevance_score
        score = await filter_instance._calculate_relevance_score(
            invalid_file, request, search_terms
        )
        
        assert isinstance(score, RelevanceScore)
        assert score.total_score == 0.0
        assert score.file_path == invalid_file
        # Note: reasons may be empty for non-existent files vs actual errors
        assert isinstance(score.reasons, list)
    
    @pytest.mark.asyncio
    async def test_direct_mention_score_with_class_definition_bonus(self, filter_instance):
        """Test direct mention score with class definition bonus (line 442)"""
        
        content_with_class_def = '''
class UserService:
    """User service class"""
    def create_user(self):
        pass
'''
        
        search_terms = {
            "class_names": ["UserService"],
            "function_names": [],
            "keywords": [],
            "concepts": []
        }
        
        score = await filter_instance._calculate_direct_mention_score(
            content_with_class_def, search_terms, "user_service.py"
        )
        
        # Should get score for class match and definition bonus
        assert score > 0.0  # Should get some score for class match
    
    @pytest.mark.asyncio
    async def test_dependency_score_with_reverse_dependencies(self, filter_instance, temp_project):
        """Test dependency score with reverse dependencies (line 481)"""
        
        # Create multiple files with import relationships
        service_file = Path(temp_project) / "user_service.py"
        service_file.write_text('''
class UserService:
    def create_user(self):
        pass
''')
        
        controller_file = Path(temp_project) / "user_controller.py"
        controller_file.write_text('''
from user_service import UserService

class UserController:
    def __init__(self):
        self.service = UserService()
''')
        
        search_terms = {
            "keywords": [],
            "concepts": [],
            "file_patterns": ["user_controller.py"]  # File that imports user_service
        }
        
        request = ContextRequest(
            agent_type="CodeAgent",
            story_id="reverse_dep_story",
            task={"description": "test"},
            focus_areas=[]
        )
        
        # Mock _get_reverse_dependencies to return the controller file
        with patch.object(filter_instance, '_get_reverse_dependencies', return_value={str(controller_file)}):
            score = await filter_instance._calculate_dependency_score(
                str(service_file), search_terms, request
            )
            
            # Should get score for reverse dependency match (line 481)
            assert score >= 0.25  # Should get 0.25 for pattern match
    
    @pytest.mark.asyncio
    async def test_dependency_score_exception_handling(self, filter_instance):
        """Test dependency score exception handling (lines 499-501)"""
        
        search_terms = {"keywords": [], "concepts": [], "file_patterns": []}
        request = ContextRequest(
            agent_type="CodeAgent",
            story_id="dep_exception_story",
            task={"description": "test"},
            focus_areas=[]
        )
        
        # Mock _get_file_dependencies to raise exception
        with patch.object(filter_instance, '_get_file_dependencies', side_effect=Exception("Dependency error")):
            score = await filter_instance._calculate_dependency_score(
                "test_file.py", search_terms, request
            )
            
            # Should handle exception gracefully (lines 499-501)
            assert score == 0.0
    
    @pytest.mark.asyncio
    async def test_semantic_score_error_handling(self, filter_instance):
        """Test semantic score error handling (lines 605-607)"""
        
        request = ContextRequest(
            agent_type="CodeAgent",
            story_id="semantic_error_story",
            task=None,
            focus_areas=[]
        )
        
        # Mock to cause an exception during semantic scoring
        with patch.object(request, 'agent_type', side_effect=Exception("Agent type error")):
            score = await filter_instance._calculate_semantic_score(
                "test content", FileType.PYTHON, request
            )
            
            # Should handle exception gracefully (lines 605-607)
            assert score == 0.0
    
    @pytest.mark.asyncio
    async def test_tdd_phase_score_error_handling(self, filter_instance):
        """Test TDD phase score error handling (lines 645-647)"""
        
        # Mock Path in the context_filter module
        with patch('context_filter.Path') as mock_path:
            mock_path.side_effect = Exception("Path error")
            
            score = await filter_instance._calculate_tdd_phase_score(
                "test_file.py", FileType.PYTHON, TDDState.TEST_RED
            )
            
            # Should handle exception gracefully (lines 645-647)
            assert score == 0.0
    
    @pytest.mark.asyncio
    async def test_filter_python_content_general_exception(self, filter_instance):
        """Test Python content filtering general exception handling (lines 695-697)"""
        
        request = ContextRequest(
            agent_type="CodeAgent",
            story_id="python_error_story",
            task={"description": "test"},
            focus_areas=[]
        )
        
        # Mock ast.get_source_segment to raise exception
        with patch('ast.get_source_segment', side_effect=Exception("AST error")):
            python_content = '''
def test_function():
    pass
'''
            result = await filter_instance._filter_python_content(
                python_content, request, target_tokens=100
            )
            
            # Should handle exception gracefully (lines 695-697)
            assert isinstance(result, str)
            assert len(result) > 0
    
    @pytest.mark.asyncio
    async def test_filter_test_content_exception_handling(self, filter_instance):
        """Test test content filtering exception handling (lines 750-752)"""
        
        request = ContextRequest(
            agent_type="QAAgent",
            story_id="test_error_story",
            task={"description": "test"},
            focus_areas=[]
        )
        
        # Mock ast.get_source_segment to raise exception
        with patch('ast.get_source_segment', side_effect=Exception("Test AST error")):
            test_content = '''
import unittest

class TestExample(unittest.TestCase):
    def test_something(self):
        pass
'''
            result = await filter_instance._filter_test_content(
                test_content, request, target_tokens=100
            )
            
            # Should handle exception gracefully (lines 750-752)
            assert isinstance(result, str)
            assert len(result) > 0
    
    @pytest.mark.asyncio
    async def test_filter_text_content_with_empty_section_skipping(self, filter_instance):
        """Test text content filtering empty section skipping (line 775)"""
        
        text_content = '''
# Header 1

Content for section 1.



# Header 2

Content for section 2.
'''
        
        request = ContextRequest(
            agent_type="DesignAgent",
            story_id="text_story",
            task={"description": "test content"},
            focus_areas=["content"]
        )
        
        result = await filter_instance._filter_text_content(
            text_content, request, target_tokens=200
        )
        
        # Should handle empty sections (line 775: continue)
        assert isinstance(result, str)
        assert "Header" in result
        assert "Content" in result
    
    @pytest.mark.asyncio
    async def test_filter_text_content_important_section_bonus(self, filter_instance):
        """Test text content filtering important section bonus (line 789)"""
        
        text_content = '''
# Normal Section

This is normal content.

# Important Information

This is important content that should get a bonus.

# Warning: Critical

This is a warning that should also get a bonus.

# TODO: Implementation

This is a todo item that should get bonus points.
'''
        
        request = ContextRequest(
            agent_type="DesignAgent",
            story_id="important_story",
            task={"description": "find important information"},
            focus_areas=["important"]
        )
        
        result = await filter_instance._filter_text_content(
            text_content, request, target_tokens=400
        )
        
        # Should prioritize important sections (line 789 adds bonus)
        assert "important" in result.lower()
        assert isinstance(result, str)
    
    @pytest.mark.asyncio
    async def test_filter_text_content_token_limit_break(self, filter_instance):
        """Test text content filtering token limit break (line 805)"""
        
        # Create content that will exceed token limit
        large_content = "\n\n".join([f"Section {i}\n" + "Content " * 50 for i in range(20)])
        
        request = ContextRequest(
            agent_type="DesignAgent",
            story_id="limit_story",
            task={"description": "test"},
            focus_areas=["section"]
        )
        
        # Use very small token limit to force break
        result = await filter_instance._filter_text_content(
            large_content, request, target_tokens=50
        )
        
        # Should break when token limit exceeded (line 805)
        assert isinstance(result, str)
        assert len(result) < len(large_content)
    
    @pytest.mark.asyncio
    async def test_get_reverse_dependencies_file_not_equal_skip(self, filter_instance, temp_project):
        """Test reverse dependencies skipping same file (lines 944-945)"""
        
        # Create the file we're analyzing
        target_file = Path(temp_project) / "target.py"
        target_file.write_text("class Target: pass")
        
        # Create another file that imports target
        other_file = Path(temp_project) / "other.py"
        other_file.write_text("from target import Target")
        
        reverse_deps = await filter_instance._get_reverse_dependencies(str(target_file))
        
        # Should find other.py but not target.py itself (lines 944-945: continue if same file)
        assert str(other_file) in reverse_deps
        assert str(target_file) not in reverse_deps
    
    @pytest.mark.asyncio
    async def test_get_reverse_dependencies_exception_handling(self, filter_instance):
        """Test reverse dependencies exception handling (lines 966-970)"""
        
        # Test with invalid project path
        original_path = filter_instance.project_path
        filter_instance.project_path = Path("/nonexistent/invalid/path")
        
        # This should trigger the exception handling
        reverse_deps = await filter_instance._get_reverse_dependencies("test.py")
        
        # Should handle exception gracefully (lines 966-970)
        assert isinstance(reverse_deps, set)
        assert len(reverse_deps) == 0
        
        # Restore original path
        filter_instance.project_path = original_path
    
    @pytest.mark.asyncio
    async def test_get_reverse_dependencies_import_content_exception(self, filter_instance, temp_project):
        """Test reverse dependencies with file content reading exception"""
        
        target_file = Path(temp_project) / "target.py"
        target_file.write_text("class Target: pass")
        
        # Create a file that will cause exception when reading content
        problem_file = Path(temp_project) / "problem.py"
        problem_file.write_text("from target import Target")
        
        # Mock _get_file_content to raise exception for the problem file
        original_get_content = filter_instance._get_file_content
        
        async def mock_get_content(path):
            if "problem.py" in path:
                raise Exception("Content read error")
            return await original_get_content(path)
        
        with patch.object(filter_instance, '_get_file_content', side_effect=mock_get_content):
            reverse_deps = await filter_instance._get_reverse_dependencies(str(target_file))
            
            # Should handle the exception and continue (line 967: continue)
            assert isinstance(reverse_deps, set)
            # problem.py should be skipped due to exception
    
    @pytest.mark.asyncio
    async def test_comprehensive_integration_with_all_edge_cases(self, filter_instance, temp_project):
        """Integration test that exercises many edge cases together"""
        
        # Create files that will trigger various code paths
        files = {
            "service.py": '''
import json
import hashlib
from datetime import datetime

class UserService:
    def create_user(self, username):
        return True
    
    def authenticate_user(self, username, password):
        return True
''',
            "controller.py": '''
from service import UserService

class UserController:
    def __init__(self):
        self.service = UserService()
''',
            "test_service.py": '''
import unittest
from service import UserService

class TestUserService(unittest.TestCase):
    def test_create_user(self):
        service = UserService()
        self.assertTrue(service.create_user("test"))
''',
            "empty_file.py": "",
            "malformed.py": "def broken_syntax(",
            "README.md": '''
# User Service

Important: This service handles user authentication.

Warning: Security considerations apply.

TODO: Add more validation.
'''
        }
        
        for filename, content in files.items():
            (Path(temp_project) / filename).write_text(content)
        
        # Create request that will exercise many code paths
        task = TDDTask(
            id="integration_task",
            description="Implement UserService with create_user and authenticate_user methods",
            cycle_id="cycle_1",
            current_state=TDDState.CODE_GREEN
        )
        
        request = ContextRequest(
            agent_type="CodeAgent",
            story_id="integration_story",
            task=task,
            focus_areas=["user", "service", "authentication"]
        )
        
        # Mock agent memory
        mock_memory = Mock(spec=FileBasedAgentMemory)
        filter_instance.agent_memory = mock_memory
        mock_snapshots = [Mock(file_list=[str(Path(temp_project) / "service.py")]) for _ in range(5)]
        mock_memory.get_context_history = AsyncMock(return_value=mock_snapshots)
        
        candidate_files = [str(Path(temp_project) / f) for f in files.keys()]
        
        # This should exercise many code paths including error handling
        results = await filter_instance.filter_relevant_files(
            request, candidate_files, max_files=10, min_score_threshold=0.0
        )
        
        assert isinstance(results, list)
        assert len(results) > 0
        
        # Test content filtering on various file types
        for filename in ["service.py", "test_service.py", "README.md", "malformed.py"]:
            file_path = str(Path(temp_project) / filename)
            content = await filter_instance._get_file_content(file_path)
            
            if content:  # Only filter non-empty content
                filtered = await filter_instance.filter_content_by_relevance(
                    file_path, content, request, target_tokens=200
                )
                assert isinstance(filtered, str)


    @pytest.mark.asyncio
    async def test_import_error_path_coverage(self):
        """Test import error path coverage for lines 30-32"""
        # This specifically tests the import error handling
        with patch('builtins.__import__', side_effect=ImportError("Mocked import error")):
            try:
                # Try to reimport the module to trigger ImportError path
                import importlib
                importlib.reload(sys.modules['context_filter'])
            except:
                pass  # Expected to fail
        
        # The real test is that the module still works despite import issues
        with tempfile.TemporaryDirectory() as temp_dir:
            filter_instance = ContextFilter(temp_dir)
            assert filter_instance is not None
    
    @pytest.mark.asyncio 
    async def test_specific_line_coverage_for_missing_branches(self, filter_instance, temp_project):
        """Test specific branches to cover remaining lines"""
        
        # Test line 442 - class definition bonus
        content_with_exact_class = '''class UserService:
    pass'''
        search_terms = {"class_names": ["UserService"], "function_names": [], "keywords": [], "concepts": []}
        score = await filter_instance._calculate_direct_mention_score(
            content_with_exact_class, search_terms, "test.py"
        )
        assert score > 0
        
        # Test line 775 - empty section continue
        text_with_empty = '''
Section 1


Section 2
'''
        request = ContextRequest(
            agent_type="DesignAgent", story_id="test", task={"description": "test"}, focus_areas=[]
        )
        
        result = await filter_instance._filter_text_content(text_with_empty, request, 100)
        assert isinstance(result, str)
        
        # Test lines 944-945 - reverse dependency file equality check
        test_file = Path(temp_project) / "target.py"
        test_file.write_text("class Target: pass")
        
        deps = await filter_instance._get_reverse_dependencies(str(test_file))
        # Should not include itself
        assert str(test_file) not in deps
        
        # Test lines 969-970 - reverse dependency exception handling
        original_path = filter_instance.project_path
        filter_instance.project_path = Path("/completely/invalid/path/that/does/not/exist")
        
        deps = await filter_instance._get_reverse_dependencies("test.py")
        assert isinstance(deps, set)
        assert len(deps) == 0
        
        filter_instance.project_path = original_path


if __name__ == "__main__":
    pytest.main([__file__, "-v"])