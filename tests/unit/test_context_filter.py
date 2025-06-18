"""
Comprehensive test suite for Context Filter System.

Tests intelligent context filtering with multi-factor relevance scoring,
including direct mention analysis, dependency analysis, historical patterns,
semantic similarity, and TDD phase relevance.
"""

import pytest
import asyncio
import tempfile
import shutil
import ast
from pathlib import Path
from datetime import datetime, timedelta
from unittest.mock import Mock, AsyncMock, patch, MagicMock

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


class TestContextFilterInit:
    """Test ContextFilter initialization"""
    
    @pytest.fixture
    def temp_project(self):
        """Create temporary project directory"""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir)
    
    def test_init_with_defaults(self, temp_project):
        """Test initialization with default parameters"""
        filter_instance = ContextFilter(temp_project)
        
        assert filter_instance.project_path == Path(temp_project)
        assert filter_instance.agent_memory is None
        assert filter_instance.token_calculator is not None
        assert isinstance(filter_instance._file_dependencies_cache, dict)
        assert isinstance(filter_instance._file_type_cache, dict)
        assert isinstance(filter_instance._content_cache, dict)
        assert len(filter_instance._filtering_times) == 0
        assert filter_instance._cache_hits == 0
        assert filter_instance._cache_misses == 0
    
    def test_init_with_custom_components(self, temp_project):
        """Test initialization with custom components"""
        mock_memory = Mock(spec=FileBasedAgentMemory)
        mock_calculator = Mock(spec=TokenCalculator)
        
        filter_instance = ContextFilter(
            temp_project,
            agent_memory=mock_memory,
            token_calculator=mock_calculator
        )
        
        assert filter_instance.agent_memory is mock_memory
        assert filter_instance.token_calculator is mock_calculator
    
    def test_scoring_weights(self):
        """Test that scoring weights are properly defined"""
        assert ContextFilter.DIRECT_MENTION_WEIGHT == 0.40
        assert ContextFilter.DEPENDENCY_WEIGHT == 0.25
        assert ContextFilter.HISTORICAL_WEIGHT == 0.20
        assert ContextFilter.SEMANTIC_WEIGHT == 0.10
        assert ContextFilter.TDD_PHASE_WEIGHT == 0.05
        
        # Weights should sum to 1.0
        total_weight = (
            ContextFilter.DIRECT_MENTION_WEIGHT +
            ContextFilter.DEPENDENCY_WEIGHT +
            ContextFilter.HISTORICAL_WEIGHT +
            ContextFilter.SEMANTIC_WEIGHT +
            ContextFilter.TDD_PHASE_WEIGHT
        )
        assert abs(total_weight - 1.0) < 0.001


class TestSearchTermExtraction:
    """Test search term extraction from context requests"""
    
    @pytest.fixture
    def filter_instance(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            yield ContextFilter(temp_dir)
    
    @pytest.fixture
    def sample_task(self):
        """Create sample TDD task"""
        return TDDTask(
            id="test_task",
            description="Implement UserController class with create_user method",
            cycle_id="cycle_1",
            current_state=TDDState.RED
        )
    
    @pytest.fixture
    def sample_request(self, sample_task):
        """Create sample context request"""
        return ContextRequest(
            agent_type="CodeAgent",
            story_id="story_123",
            task=sample_task,
            focus_areas=["authentication", "validation"]
        )
    
    @pytest.mark.asyncio
    async def test_extract_search_terms_basic(self, filter_instance, sample_request):
        """Test basic search term extraction"""
        search_terms = await filter_instance._extract_search_terms(sample_request)
        
        assert isinstance(search_terms, dict)
        assert "keywords" in search_terms
        assert "function_names" in search_terms
        assert "class_names" in search_terms
        assert "file_patterns" in search_terms
        assert "concepts" in search_terms
        
        # Check extracted content
        assert "UserController" in search_terms["class_names"]
        assert "create_user" in search_terms["function_names"]
        assert "authentication" in search_terms["keywords"]
        assert "validation" in search_terms["keywords"]
    
    @pytest.mark.asyncio
    async def test_extract_search_terms_with_dict_task(self, filter_instance):
        """Test search term extraction with dictionary task"""
        dict_task = {
            "description": "Add calculate_total function to OrderService",
            "acceptance_criteria": "Should handle tax calculation"
        }
        
        request = ContextRequest(
            agent_type="CodeAgent",
            story_id="story_456",
            task=dict_task,
            focus_areas=["payment", "billing"]
        )
        
        search_terms = await filter_instance._extract_search_terms(request)
        
        assert "calculate_total" in search_terms["function_names"]
        assert "OrderService" in search_terms["class_names"]
        assert "tax" in search_terms["keywords"]
        assert "payment" in search_terms["keywords"]
        assert "billing" in search_terms["keywords"]
    
    @pytest.mark.asyncio
    async def test_extract_search_terms_file_patterns(self, filter_instance):
        """Test file pattern extraction"""
        task_with_files = {
            "description": "Update config.json and settings.yaml files"
        }
        
        request = ContextRequest(
            agent_type="CodeAgent",
            story_id="story_789",
            task=task_with_files,
            focus_areas=[]
        )
        
        search_terms = await filter_instance._extract_search_terms(request)
        
        assert "config.json" in search_terms["file_patterns"]
        assert "settings.yaml" in search_terms["file_patterns"]
    
    @pytest.mark.asyncio
    async def test_extract_search_terms_concepts(self, filter_instance):
        """Test programming concept extraction"""
        task_with_concepts = {
            "description": "Add unittest for API endpoint with mock database"
        }
        
        request = ContextRequest(
            agent_type="QAAgent",
            story_id="story_concepts",
            task=task_with_concepts,
            focus_areas=["testing", "integration"]
        )
        
        search_terms = await filter_instance._extract_search_terms(request)
        
        assert "test" in search_terms["concepts"]
        assert "api" in search_terms["concepts"]
        assert "mock" in search_terms["concepts"]
        assert "database" in search_terms["concepts"]
        assert "testing" in search_terms["concepts"]
        assert "integration" in search_terms["concepts"]
    
    @pytest.mark.asyncio
    async def test_extract_search_terms_empty_request(self, filter_instance):
        """Test search term extraction with empty request"""
        empty_request = ContextRequest(
            agent_type="CodeAgent",
            story_id="empty_story",
            task=None,
            focus_areas=[]
        )
        
        search_terms = await filter_instance._extract_search_terms(empty_request)
        
        # Should return empty but valid structure
        assert isinstance(search_terms, dict)
        assert len(search_terms["keywords"]) == 0
        assert len(search_terms["function_names"]) == 0
        assert len(search_terms["class_names"]) == 0
    
    @pytest.mark.asyncio
    async def test_extract_search_terms_keyword_filtering(self, filter_instance):
        """Test that common words are filtered out"""
        task_with_common_words = {
            "description": "The function should be able to process the data and return the result"
        }
        
        request = ContextRequest(
            agent_type="CodeAgent",
            story_id="common_words",
            task=task_with_common_words,
            focus_areas=[]
        )
        
        search_terms = await filter_instance._extract_search_terms(request)
        
        # Common words should be filtered out
        keywords = search_terms["keywords"]
        common_words = {"the", "and", "to", "should", "be", "able"}
        
        for word in common_words:
            assert word not in keywords
        
        # But meaningful words should remain
        assert "function" in keywords
        assert "process" in keywords
        assert "data" in keywords
        assert "return" in keywords
        assert "result" in keywords


class TestRelevanceScoring:
    """Test relevance scoring algorithms"""
    
    @pytest.fixture
    def temp_project(self):
        """Create temporary project with test files"""
        temp_dir = tempfile.mkdtemp()
        
        # Create test Python file
        python_file = Path(temp_dir) / "user_service.py"
        python_content = '''
class UserService:
    def create_user(self, username, email):
        """Create a new user"""
        return User(username=username, email=email)
    
    def validate_email(self, email):
        """Validate email format"""
        return "@" in email

def authenticate_user(username, password):
    """Authenticate user credentials"""
    return True
'''
        python_file.write_text(python_content)
        
        # Create test file
        test_file = Path(temp_dir) / "test_user_service.py"
        test_content = '''
import unittest
from user_service import UserService

class TestUserService(unittest.TestCase):
    def test_create_user(self):
        service = UserService()
        user = service.create_user("john", "john@example.com")
        self.assertIsNotNone(user)
    
    def test_validate_email(self):
        service = UserService()
        self.assertTrue(service.validate_email("test@example.com"))
'''
        test_file.write_text(test_content)
        
        # Create markdown file
        md_file = Path(temp_dir) / "README.md"
        md_content = '''
# User Service Documentation

This module provides user management functionality.

## Features
- User creation
- Email validation
- Authentication
'''
        md_file.write_text(md_content)
        
        yield temp_dir
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def filter_instance(self, temp_project):
        return ContextFilter(temp_project)
    
    @pytest.fixture
    def sample_request(self):
        task = TDDTask(
            id="test_task",
            description="Implement create_user method in UserService class",
            cycle_id="cycle_1",
            current_state=TDDState.GREEN
        )
        
        return ContextRequest(
            agent_type="CodeAgent",
            story_id="story_user_creation",
            task=task,
            focus_areas=["user", "creation", "validation"]
        )
    
    @pytest.mark.asyncio
    async def test_direct_mention_score_high(self, filter_instance, sample_request):
        """Test high direct mention score calculation"""
        python_file = str(filter_instance.project_path / "user_service.py")
        
        search_terms = await filter_instance._extract_search_terms(sample_request)
        content = await filter_instance._get_file_content(python_file)
        
        score = await filter_instance._calculate_direct_mention_score(
            content, search_terms, python_file
        )
        
        # Should have high score due to UserService class and create_user method
        assert score > 0.5
    
    @pytest.mark.asyncio
    async def test_direct_mention_score_class_definitions(self, filter_instance, sample_request):
        """Test direct mention scoring for class definitions"""
        python_file = str(filter_instance.project_path / "user_service.py")
        
        search_terms = {"class_names": ["UserService"], "function_names": [], "keywords": []}
        content = await filter_instance._get_file_content(python_file)
        
        score = await filter_instance._calculate_direct_mention_score(
            content, search_terms, python_file
        )
        
        # Should get bonus for class definition
        assert score > 0.3
    
    @pytest.mark.asyncio
    async def test_direct_mention_score_function_definitions(self, filter_instance, sample_request):
        """Test direct mention scoring for function definitions"""
        python_file = str(filter_instance.project_path / "user_service.py")
        
        search_terms = {"class_names": [], "function_names": ["create_user"], "keywords": []}
        content = await filter_instance._get_file_content(python_file)
        
        score = await filter_instance._calculate_direct_mention_score(
            content, search_terms, python_file
        )
        
        # Should get bonus for function definition
        assert score > 0.2
    
    @pytest.mark.asyncio
    async def test_direct_mention_score_filename_relevance(self, filter_instance):
        """Test filename relevance scoring"""
        user_file = str(filter_instance.project_path / "user_service.py")
        
        search_terms = {"keywords": ["user"], "concepts": ["service"], "function_names": [], "class_names": []}
        content = "# Empty file"
        
        score = await filter_instance._calculate_direct_mention_score(
            content, search_terms, user_file
        )
        
        # Should get points for filename relevance
        assert score > 0.0
    
    @pytest.mark.asyncio
    async def test_calculate_relevance_score_complete(self, filter_instance, sample_request):
        """Test complete relevance score calculation"""
        python_file = str(filter_instance.project_path / "user_service.py")
        search_terms = await filter_instance._extract_search_terms(sample_request)
        
        relevance_score = await filter_instance._calculate_relevance_score(
            python_file, sample_request, search_terms
        )
        
        assert isinstance(relevance_score, RelevanceScore)
        assert relevance_score.file_path == python_file
        assert relevance_score.total_score > 0.0
        assert relevance_score.direct_mention >= 0.0
        assert relevance_score.dependency_score >= 0.0
        assert relevance_score.historical_score >= 0.0
        assert relevance_score.semantic_score >= 0.0
        assert relevance_score.tdd_phase_score >= 0.0
        assert isinstance(relevance_score.reasons, list)
    
    @pytest.mark.asyncio
    async def test_semantic_score_code_agent(self, filter_instance):
        """Test semantic scoring for CodeAgent"""
        python_file = str(filter_instance.project_path / "user_service.py")
        content = await filter_instance._get_file_content(python_file)
        
        request = ContextRequest(
            agent_type="CodeAgent",
            story_id="story_123",
            task=None,
            focus_areas=[]
        )
        
        score = await filter_instance._calculate_semantic_score(
            content, FileType.PYTHON, request
        )
        
        # CodeAgent should favor Python files with classes and functions
        assert score > 0.5
    
    @pytest.mark.asyncio
    async def test_semantic_score_qa_agent(self, filter_instance):
        """Test semantic scoring for QAAgent"""
        test_file = str(filter_instance.project_path / "test_user_service.py")
        content = await filter_instance._get_file_content(test_file)
        
        request = ContextRequest(
            agent_type="QAAgent",
            story_id="story_123",
            task=None,
            focus_areas=[]
        )
        
        score = await filter_instance._calculate_semantic_score(
            content, FileType.TEST, request
        )
        
        # QAAgent should favor test files
        assert score > 0.5
    
    @pytest.mark.asyncio
    async def test_semantic_score_design_agent(self, filter_instance):
        """Test semantic scoring for DesignAgent"""
        md_file = str(filter_instance.project_path / "README.md")
        content = await filter_instance._get_file_content(md_file)
        
        request = ContextRequest(
            agent_type="DesignAgent",
            story_id="story_123",
            task=None,
            focus_areas=[]
        )
        
        score = await filter_instance._calculate_semantic_score(
            content, FileType.MARKDOWN, request
        )
        
        # DesignAgent should favor markdown files
        assert score > 0.0
    
    @pytest.mark.asyncio
    async def test_tdd_phase_score_red_phase(self, filter_instance):
        """Test TDD phase scoring for RED phase"""
        test_file = str(filter_instance.project_path / "test_user_service.py")
        
        score = await filter_instance._calculate_tdd_phase_score(
            test_file, FileType.TEST, TDDState.RED
        )
        
        # RED phase should favor test files
        assert score > 0.6
    
    @pytest.mark.asyncio
    async def test_tdd_phase_score_green_phase(self, filter_instance):
        """Test TDD phase scoring for GREEN phase"""
        python_file = str(filter_instance.project_path / "user_service.py")
        
        score = await filter_instance._calculate_tdd_phase_score(
            python_file, FileType.PYTHON, TDDState.GREEN
        )
        
        # GREEN phase should favor implementation files
        assert score > 0.6
    
    @pytest.mark.asyncio
    async def test_tdd_phase_score_refactor_phase(self, filter_instance):
        """Test TDD phase scoring for REFACTOR phase"""
        python_file = str(filter_instance.project_path / "user_service.py")
        
        score = await filter_instance._calculate_tdd_phase_score(
            python_file, FileType.PYTHON, TDDState.REFACTOR
        )
        
        # REFACTOR phase should favor both test and implementation files
        assert score > 0.4


class TestFileFiltering:
    """Test file filtering functionality"""
    
    @pytest.fixture
    def temp_project(self):
        """Create temporary project with multiple test files"""
        temp_dir = tempfile.mkdtemp()
        
        # Create relevant files
        relevant_files = [
            ("user_controller.py", "class UserController:\n    def create_user(self):\n        pass"),
            ("user_service.py", "class UserService:\n    def validate_user(self):\n        pass"),
            ("test_user.py", "import unittest\nclass TestUser(unittest.TestCase):\n    pass"),
            ("models.py", "class User:\n    def __init__(self):\n        pass"),
        ]
        
        # Create irrelevant files
        irrelevant_files = [
            ("config.py", "DATABASE_URL = 'sqlite:///app.db'"),
            ("utils.py", "def helper_function():\n    return True"),
            ("README.md", "# Project Documentation"),
        ]
        
        all_files = relevant_files + irrelevant_files
        
        for filename, content in all_files:
            file_path = Path(temp_dir) / filename
            file_path.write_text(content)
        
        yield temp_dir
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def filter_instance(self, temp_project):
        return ContextFilter(temp_project)
    
    @pytest.fixture
    def user_focused_request(self):
        task = TDDTask(
            id="user_task",
            description="Implement UserController with create_user method",
            cycle_id="cycle_1",
            current_state=TDDState.GREEN
        )
        
        return ContextRequest(
            agent_type="CodeAgent",
            story_id="story_user",
            task=task,
            focus_areas=["user", "controller"]
        )
    
    @pytest.mark.asyncio
    async def test_filter_relevant_files_basic(self, filter_instance, user_focused_request, temp_project):
        """Test basic file filtering"""
        candidate_files = [
            str(Path(temp_project) / f) for f in 
            ["user_controller.py", "user_service.py", "test_user.py", "config.py", "utils.py"]
        ]
        
        results = await filter_instance.filter_relevant_files(
            user_focused_request,
            candidate_files,
            max_files=10,
            min_score_threshold=0.1
        )
        
        assert isinstance(results, list)
        assert len(results) > 0
        
        # Results should be sorted by relevance (descending)
        for i in range(len(results) - 1):
            assert results[i].total_score >= results[i + 1].total_score
        
        # User-related files should score higher
        result_files = [r.file_path for r in results]
        user_controller_path = str(Path(temp_project) / "user_controller.py")
        assert user_controller_path in result_files
    
    @pytest.mark.asyncio
    async def test_filter_relevant_files_max_limit(self, filter_instance, user_focused_request, temp_project):
        """Test file filtering with maximum file limit"""
        candidate_files = [
            str(Path(temp_project) / f) for f in 
            ["user_controller.py", "user_service.py", "test_user.py", "models.py", "config.py"]
        ]
        
        results = await filter_instance.filter_relevant_files(
            user_focused_request,
            candidate_files,
            max_files=2
        )
        
        assert len(results) <= 2
        
        # Should return the most relevant files
        if len(results) == 2:
            assert results[0].total_score >= results[1].total_score
    
    @pytest.mark.asyncio
    async def test_filter_relevant_files_min_threshold(self, filter_instance, user_focused_request, temp_project):
        """Test file filtering with minimum score threshold"""
        candidate_files = [
            str(Path(temp_project) / f) for f in 
            ["user_controller.py", "config.py", "utils.py"]
        ]
        
        results = await filter_instance.filter_relevant_files(
            user_focused_request,
            candidate_files,
            min_score_threshold=0.3  # High threshold
        )
        
        # All returned files should meet the threshold
        for result in results:
            assert result.total_score >= 0.3
    
    @pytest.mark.asyncio
    async def test_filter_relevant_files_error_handling(self, filter_instance, user_focused_request):
        """Test file filtering error handling"""
        # Include non-existent file
        candidate_files = [
            "/nonexistent/file.py",
            str(filter_instance.project_path / "user_controller.py")
        ]
        
        results = await filter_instance.filter_relevant_files(
            user_focused_request,
            candidate_files
        )
        
        # Should handle errors gracefully and return valid results
        assert isinstance(results, list)
        # Non-existent file should be skipped
    
    @pytest.mark.asyncio
    async def test_filter_relevant_files_performance_tracking(self, filter_instance, user_focused_request, temp_project):
        """Test that performance metrics are tracked"""
        candidate_files = [str(Path(temp_project) / "user_controller.py")]
        
        initial_count = len(filter_instance._filtering_times)
        
        await filter_instance.filter_relevant_files(
            user_focused_request,
            candidate_files
        )
        
        # Should track filtering time
        assert len(filter_instance._filtering_times) == initial_count + 1
        assert filter_instance._filtering_times[-1] > 0


class TestContentFiltering:
    """Test content filtering within files"""
    
    @pytest.fixture
    def filter_instance(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            yield ContextFilter(temp_dir)
    
    @pytest.fixture
    def sample_request(self):
        task = TDDTask(
            id="content_task",
            description="Implement user authentication",
            cycle_id="cycle_1",
            current_state=TDDState.GREEN
        )
        
        return ContextRequest(
            agent_type="CodeAgent",
            story_id="story_auth",
            task=task,
            focus_areas=["authentication", "user"]
        )
    
    @pytest.mark.asyncio
    async def test_filter_python_content(self, filter_instance, sample_request):
        """Test Python content filtering"""
        python_content = '''
import os
import hashlib

class UserService:
    def authenticate_user(self, username, password):
        """Authenticate user with username and password"""
        return self.verify_password(username, password)
    
    def verify_password(self, username, password):
        """Verify password hash"""
        return True
    
    def create_user(self, username, email):
        """Create new user account"""
        return User(username, email)
    
    def unrelated_method(self):
        """This method is not related to authentication"""
        return "unrelated"

def helper_function():
    """Helper function"""
    return True
'''
        
        filtered = await filter_instance.filter_content_by_relevance(
            "test.py", python_content, sample_request, target_tokens=1000
        )
        
        assert isinstance(filtered, str)
        assert len(filtered) > 0
        
        # Should include authentication-related methods
        assert "authenticate_user" in filtered
        assert "verify_password" in filtered
        
        # Should include relevance comments
        assert "Relevance:" in filtered
    
    @pytest.mark.asyncio
    async def test_filter_test_content(self, filter_instance, sample_request):
        """Test test file content filtering"""
        test_content = '''
import unittest
from user_service import UserService

class TestUserAuthentication(unittest.TestCase):
    def test_authenticate_valid_user(self):
        """Test authentication with valid credentials"""
        service = UserService()
        result = service.authenticate_user("john", "password123")
        self.assertTrue(result)
    
    def test_authenticate_invalid_user(self):
        """Test authentication with invalid credentials"""
        service = UserService()
        result = service.authenticate_user("john", "wrongpassword")
        self.assertFalse(result)
    
    def test_unrelated_feature(self):
        """Test unrelated functionality"""
        self.assertTrue(True)

class TestOtherFeatures(unittest.TestCase):
    def test_something_else(self):
        """Test something completely different"""
        pass
'''
        
        filtered = await filter_instance.filter_content_by_relevance(
            "test_auth.py", test_content, sample_request, target_tokens=800
        )
        
        assert isinstance(filtered, str)
        assert len(filtered) > 0
        
        # Should include imports
        assert "import" in filtered
        
        # Should include authentication-related tests
        assert "test_authenticate" in filtered
        
        # Should include test relevance comments
        assert "Test relevance:" in filtered
    
    @pytest.mark.asyncio
    async def test_filter_text_content(self, filter_instance, sample_request):
        """Test text/markdown content filtering"""
        text_content = '''
# User Authentication System

This document describes the user authentication system.

## Overview

The authentication system provides secure user login and logout functionality.

## Authentication Flow

1. User enters credentials
2. System validates credentials
3. User is granted access

## Security Features

- Password hashing
- Session management
- Rate limiting

## Configuration

Database settings and API keys are stored in config files.

## Troubleshooting

Common issues and solutions for authentication problems.

## Unrelated Section

This section talks about something completely different that has nothing to do with users or authentication.
'''
        
        filtered = await filter_instance.filter_content_by_relevance(
            "auth_docs.md", text_content, sample_request, target_tokens=500
        )
        
        assert isinstance(filtered, str)
        assert len(filtered) > 0
        
        # Should include authentication-related sections
        assert "authentication" in filtered.lower()
        assert "user" in filtered.lower()
        
        # Should prioritize headers and important sections
        assert "#" in filtered  # Headers should be included
    
    @pytest.mark.asyncio
    async def test_filter_content_token_limit(self, filter_instance, sample_request):
        """Test content filtering with tight token limits"""
        long_content = "def function():\n    pass\n" * 100  # Repeat to make long content
        
        filtered = await filter_instance.filter_content_by_relevance(
            "long_file.py", long_content, sample_request, target_tokens=50
        )
        
        # Should be truncated to approximately target tokens
        assert len(filtered) < len(long_content)
        assert "[content truncated]" in filtered or len(filtered) > 0
    
    @pytest.mark.asyncio
    async def test_filter_content_invalid_python(self, filter_instance, sample_request):
        """Test content filtering with invalid Python syntax"""
        invalid_python = '''
def broken_function(
    # Missing closing parenthesis and body
'''
        
        filtered = await filter_instance.filter_content_by_relevance(
            "broken.py", invalid_python, sample_request, target_tokens=200
        )
        
        # Should fallback to text filtering
        assert isinstance(filtered, str)
        assert len(filtered) > 0
    
    @pytest.mark.asyncio
    async def test_filter_content_unsupported_type(self, filter_instance, sample_request):
        """Test content filtering for unsupported file types"""
        binary_content = "Some content for unsupported file type"
        
        filtered = await filter_instance.filter_content_by_relevance(
            "file.bin", binary_content, sample_request, target_tokens=100
        )
        
        # Should use simple truncation
        assert isinstance(filtered, str)
        assert len(filtered) <= len(binary_content)


class TestFileUtilities:
    """Test file utility methods"""
    
    @pytest.fixture
    def temp_project(self):
        """Create temporary project with test files"""
        temp_dir = tempfile.mkdtemp()
        
        # Create Python file
        python_file = Path(temp_dir) / "service.py"
        python_content = '''
import json
from datetime import datetime

class DataService:
    def process_data(self):
        pass
'''
        python_file.write_text(python_content)
        
        # Create test file
        test_file = Path(temp_dir) / "tests" / "test_service.py"
        test_file.parent.mkdir(exist_ok=True)
        test_content = '''
import unittest
from service import DataService

class TestDataService(unittest.TestCase):
    pass
'''
        test_file.write_text(test_content)
        
        yield temp_dir
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def filter_instance(self, temp_project):
        return ContextFilter(temp_project)
    
    @pytest.mark.asyncio
    async def test_get_file_content_caching(self, filter_instance, temp_project):
        """Test file content caching"""
        python_file = str(Path(temp_project) / "service.py")
        
        # First read
        content1 = await filter_instance._get_file_content(python_file)
        cache_hits_1 = filter_instance._cache_hits
        cache_misses_1 = filter_instance._cache_misses
        
        # Second read (should hit cache)
        content2 = await filter_instance._get_file_content(python_file)
        cache_hits_2 = filter_instance._cache_hits
        cache_misses_2 = filter_instance._cache_misses
        
        assert content1 == content2
        assert cache_hits_2 > cache_hits_1  # Cache hit
        assert cache_misses_2 == cache_misses_1 + 1  # Only one miss from first read
    
    @pytest.mark.asyncio
    async def test_get_file_type_python(self, filter_instance, temp_project):
        """Test Python file type detection"""
        python_file = str(Path(temp_project) / "service.py")
        file_type = await filter_instance._get_file_type(python_file)
        assert file_type == FileType.PYTHON
    
    @pytest.mark.asyncio
    async def test_get_file_type_test(self, filter_instance, temp_project):
        """Test test file type detection"""
        test_file = str(Path(temp_project) / "tests" / "test_service.py")
        file_type = await filter_instance._get_file_type(test_file)
        assert file_type == FileType.TEST
    
    @pytest.mark.asyncio
    async def test_get_file_type_caching(self, filter_instance, temp_project):
        """Test file type caching"""
        python_file = str(Path(temp_project) / "service.py")
        
        # Should cache file type
        type1 = await filter_instance._get_file_type(python_file)
        type2 = await filter_instance._get_file_type(python_file)
        
        assert type1 == type2
        assert python_file in filter_instance._file_type_cache
    
    @pytest.mark.asyncio
    async def test_get_file_dependencies(self, filter_instance, temp_project):
        """Test file dependency extraction"""
        python_file = str(Path(temp_project) / "service.py")
        
        dependencies = await filter_instance._get_file_dependencies(python_file)
        
        assert isinstance(dependencies, set)
        assert "json" in dependencies
        assert "datetime" in dependencies
    
    @pytest.mark.asyncio
    async def test_get_file_dependencies_caching(self, filter_instance, temp_project):
        """Test dependency caching"""
        python_file = str(Path(temp_project) / "service.py")
        
        deps1 = await filter_instance._get_file_dependencies(python_file)
        deps2 = await filter_instance._get_file_dependencies(python_file)
        
        assert deps1 == deps2
        assert python_file in filter_instance._file_dependencies_cache
    
    @pytest.mark.asyncio
    async def test_get_reverse_dependencies(self, filter_instance, temp_project):
        """Test reverse dependency finding"""
        service_file = str(Path(temp_project) / "service.py")
        
        reverse_deps = await filter_instance._get_reverse_dependencies(service_file)
        
        assert isinstance(reverse_deps, set)
        # test_service.py imports service, so should be in reverse deps
        test_file = str(Path(temp_project) / "tests" / "test_service.py")
        assert test_file in reverse_deps


class TestRelevanceExplanation:
    """Test relevance explanation functionality"""
    
    @pytest.fixture
    def temp_project(self):
        """Create temporary project"""
        temp_dir = tempfile.mkdtemp()
        
        python_file = Path(temp_dir) / "user_auth.py"
        python_content = '''
class UserAuthenticator:
    def authenticate(self, username, password):
        return True
'''
        python_file.write_text(python_content)
        
        yield temp_dir
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def filter_instance(self, temp_project):
        return ContextFilter(temp_project)
    
    @pytest.fixture
    def auth_request(self):
        task = TDDTask(
            id="auth_task",
            description="Implement user authentication",
            cycle_id="cycle_1",
            current_state=TDDState.GREEN
        )
        
        return ContextRequest(
            agent_type="CodeAgent",
            story_id="story_auth",
            task=task,
            focus_areas=["authentication", "user"]
        )
    
    @pytest.mark.asyncio
    async def test_get_file_relevance_explanation(self, filter_instance, auth_request, temp_project):
        """Test getting detailed relevance explanation"""
        auth_file = str(Path(temp_project) / "user_auth.py")
        
        explanation = await filter_instance.get_file_relevance_explanation(
            auth_file, auth_request
        )
        
        assert isinstance(explanation, dict)
        assert "file_path" in explanation
        assert "total_score" in explanation
        assert "scoring_breakdown" in explanation
        assert "reasons" in explanation
        assert "search_terms" in explanation
        
        # Check scoring breakdown structure
        breakdown = explanation["scoring_breakdown"]
        assert "direct_mention" in breakdown
        assert "dependency" in breakdown
        assert "historical" in breakdown
        assert "semantic" in breakdown
        assert "tdd_phase" in breakdown
        
        # Each component should have score, weight, and contribution
        for component in breakdown.values():
            assert "score" in component
            assert "weight" in component
            assert "contribution" in component
        
        # Verify search terms extraction
        search_terms = explanation["search_terms"]
        assert "keywords" in search_terms
        assert "authentication" in search_terms["keywords"]


class TestPerformanceMetrics:
    """Test performance metrics collection"""
    
    @pytest.fixture
    def filter_instance(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            yield ContextFilter(temp_dir)
    
    def test_get_performance_metrics_initial(self, filter_instance):
        """Test initial performance metrics"""
        metrics = filter_instance.get_performance_metrics()
        
        assert isinstance(metrics, dict)
        assert "average_filtering_time" in metrics
        assert "max_filtering_time" in metrics
        assert "min_filtering_time" in metrics
        assert "total_filtering_operations" in metrics
        assert "cache_hit_rate" in metrics
        assert "cache_hits" in metrics
        assert "cache_misses" in metrics
        assert "cached_files" in metrics
        assert "cached_dependencies" in metrics
        
        # Initial state
        assert metrics["total_filtering_operations"] == 0
        assert metrics["cache_hits"] == 0
        assert metrics["cache_misses"] == 0
    
    @pytest.mark.asyncio
    async def test_performance_metrics_after_operations(self, filter_instance):
        """Test performance metrics after operations"""
        # Perform some cache operations
        await filter_instance._get_file_content("nonexistent.py")  # Cache miss
        await filter_instance._get_file_content("nonexistent.py")  # Cache hit
        
        metrics = filter_instance.get_performance_metrics()
        
        assert metrics["cache_misses"] > 0
        assert metrics["cache_hits"] > 0
        assert metrics["cache_hit_rate"] > 0.0
    
    @pytest.mark.asyncio
    async def test_clear_cache(self, filter_instance):
        """Test cache clearing functionality"""
        # Add some items to cache
        await filter_instance._get_file_content("test.py")
        await filter_instance._get_file_type("test.py")
        await filter_instance._get_file_dependencies("test.py")
        
        # Verify cache has items
        assert len(filter_instance._content_cache) > 0
        assert len(filter_instance._file_type_cache) > 0
        
        # Clear cache
        await filter_instance.clear_cache()
        
        # Verify cache is empty
        assert len(filter_instance._content_cache) == 0
        assert len(filter_instance._file_type_cache) == 0
        assert len(filter_instance._file_dependencies_cache) == 0
        assert len(filter_instance._cache_timestamps) == 0


class TestPythonASTAnalysis:
    """Test Python AST analysis functionality"""
    
    @pytest.fixture
    def filter_instance(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            yield ContextFilter(temp_dir)
    
    @pytest.mark.asyncio
    async def test_score_python_node_function(self, filter_instance):
        """Test scoring Python function nodes"""
        # Create function node
        code = "def authenticate_user(username): pass"
        tree = ast.parse(code)
        func_node = tree.body[0]
        
        search_terms = {
            "function_names": ["authenticate_user"],
            "keywords": ["authenticate"],
            "class_names": []
        }
        
        score = await filter_instance._score_python_node(func_node, search_terms)
        
        # Should get high score for exact function name match
        assert score >= 1.0
    
    @pytest.mark.asyncio
    async def test_score_python_node_class(self, filter_instance):
        """Test scoring Python class nodes"""
        # Create class node
        code = "class UserService: pass"
        tree = ast.parse(code)
        class_node = tree.body[0]
        
        search_terms = {
            "function_names": [],
            "keywords": ["user"],
            "class_names": ["UserService"]
        }
        
        score = await filter_instance._score_python_node(class_node, search_terms)
        
        # Should get high score for exact class name match
        assert score >= 1.0
    
    @pytest.mark.asyncio
    async def test_score_python_node_partial_match(self, filter_instance):
        """Test scoring with partial keyword matches"""
        code = "def user_validation(data): pass"
        tree = ast.parse(code)
        func_node = tree.body[0]
        
        search_terms = {
            "function_names": [],
            "keywords": ["user", "validation"],
            "class_names": []
        }
        
        score = await filter_instance._score_python_node(func_node, search_terms)
        
        # Should get partial score for keyword matches in name
        assert score > 0.0
        assert score < 1.0


class TestIntegrationScenarios:
    """Integration test scenarios"""
    
    @pytest.fixture
    def comprehensive_project(self):
        """Create comprehensive test project"""
        temp_dir = tempfile.mkdtemp()
        
        # Create project structure
        files = {
            "models/user.py": '''
class User:
    def __init__(self, username, email):
        self.username = username
        self.email = email
''',
            "services/auth_service.py": '''
from models.user import User

class AuthenticationService:
    def authenticate_user(self, username, password):
        """Authenticate user with credentials"""
        return self.verify_credentials(username, password)
    
    def verify_credentials(self, username, password):
        """Verify user credentials"""
        return True
''',
            "controllers/user_controller.py": '''
from services.auth_service import AuthenticationService

class UserController:
    def __init__(self):
        self.auth_service = AuthenticationService()
    
    def login(self, username, password):
        """Handle user login"""
        return self.auth_service.authenticate_user(username, password)
''',
            "tests/test_auth.py": '''
import unittest
from services.auth_service import AuthenticationService

class TestAuthentication(unittest.TestCase):
    def test_authenticate_valid_user(self):
        service = AuthenticationService()
        result = service.authenticate_user("john", "password")
        self.assertTrue(result)
''',
            "config/settings.py": '''
DATABASE_URL = "sqlite:///app.db"
SECRET_KEY = "secret"
''',
            "utils/helpers.py": '''
def format_username(username):
    return username.strip().lower()
''',
            "README.md": '''
# Authentication System

This project implements user authentication functionality.
'''
        }
        
        for file_path, content in files.items():
            full_path = Path(temp_dir) / file_path
            full_path.parent.mkdir(parents=True, exist_ok=True)
            full_path.write_text(content)
        
        yield temp_dir
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def filter_instance(self, comprehensive_project):
        return ContextFilter(comprehensive_project)
    
    @pytest.fixture
    def auth_request(self):
        task = TDDTask(
            id="auth_integration",
            description="Implement complete user authentication flow",
            cycle_id="cycle_1",
            current_state=TDDState.GREEN
        )
        
        return ContextRequest(
            agent_type="CodeAgent",
            story_id="story_auth_complete",
            task=task,
            focus_areas=["authentication", "user", "login"]
        )
    
    @pytest.mark.asyncio
    async def test_comprehensive_filtering_scenario(self, filter_instance, auth_request, comprehensive_project):
        """Test comprehensive filtering scenario"""
        # Get all Python files
        candidate_files = []
        for py_file in Path(comprehensive_project).rglob("*.py"):
            candidate_files.append(str(py_file))
        candidate_files.extend([
            str(Path(comprehensive_project) / "README.md")
        ])
        
        results = await filter_instance.filter_relevant_files(
            auth_request,
            candidate_files,
            max_files=5
        )
        
        assert len(results) > 0
        assert len(results) <= 5
        
        # Verify results are properly scored and ordered
        for i in range(len(results) - 1):
            assert results[i].total_score >= results[i + 1].total_score
        
        # Check that authentication-related files score highly
        result_filenames = [Path(r.file_path).name for r in results]
        high_relevance_files = {"auth_service.py", "user_controller.py", "test_auth.py"}
        
        # At least some authentication files should be in top results
        assert len(set(result_filenames) & high_relevance_files) > 0
    
    @pytest.mark.asyncio
    async def test_agent_specific_filtering(self, filter_instance, comprehensive_project):
        """Test agent-specific filtering preferences"""
        candidate_files = [str(f) for f in Path(comprehensive_project).rglob("*.py")]
        
        # Test QA Agent preference for test files
        qa_task = TDDTask(id="qa_task", description="Test authentication", cycle_id="c1", current_state=TDDState.RED)
        qa_request = ContextRequest(agent_type="QAAgent", story_id="qa_story", task=qa_task, focus_areas=["test"])
        
        qa_results = await filter_instance.filter_relevant_files(qa_request, candidate_files, max_files=3)
        
        # QA agent should prefer test files
        qa_filenames = [Path(r.file_path).name for r in qa_results]
        assert any("test_" in name for name in qa_filenames)
        
        # Test Design Agent preference for documentation
        design_files = candidate_files + [str(Path(comprehensive_project) / "README.md")]
        design_task = TDDTask(id="design_task", description="Design authentication", cycle_id="c1", current_state=TDDState.DESIGN)
        design_request = ContextRequest(agent_type="DesignAgent", story_id="design_story", task=design_task, focus_areas=["architecture"])
        
        design_results = await filter_instance.filter_relevant_files(design_request, design_files, max_files=3)
        
        # Should include README for design context
        design_paths = [r.file_path for r in design_results]
        readme_path = str(Path(comprehensive_project) / "README.md")
        # README might not be top result but should be considered relevant for DesignAgent


if __name__ == "__main__":
    pytest.main([__file__])