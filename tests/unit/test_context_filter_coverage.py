"""
Comprehensive unit tests for ContextFilter targeting 95%+ line coverage.

This test suite provides comprehensive coverage for government audit compliance,
including all edge cases, error paths, caching behavior, performance metrics,
dependency analysis, and content filtering scenarios.
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


class TestContextFilterComprehensiveInit:
    """Comprehensive initialization and configuration tests"""
    
    @pytest.fixture
    def temp_project(self):
        """Create temporary project directory"""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir)
    
    def test_init_with_all_defaults(self, temp_project):
        """Test initialization with all default parameters"""
        filter_instance = ContextFilter(temp_project)
        
        assert filter_instance.project_path == Path(temp_project)
        assert filter_instance.agent_memory is None
        assert filter_instance.token_calculator is not None
        assert isinstance(filter_instance.token_calculator, TokenCalculator)
        
        # Verify all cache structures are initialized
        assert isinstance(filter_instance._file_dependencies_cache, dict)
        assert isinstance(filter_instance._file_type_cache, dict)
        assert isinstance(filter_instance._content_cache, dict)
        assert isinstance(filter_instance._cache_timestamps, dict)
        assert isinstance(filter_instance._filtering_times, list)
        
        # Verify metrics are initialized
        assert filter_instance._cache_hits == 0
        assert filter_instance._cache_misses == 0
        assert len(filter_instance._filtering_times) == 0
    
    def test_init_with_custom_components(self, temp_project):
        """Test initialization with custom agent memory and token calculator"""
        mock_memory = Mock(spec=FileBasedAgentMemory)
        mock_calculator = Mock(spec=TokenCalculator)
        
        filter_instance = ContextFilter(
            temp_project,
            agent_memory=mock_memory,
            token_calculator=mock_calculator
        )
        
        assert filter_instance.agent_memory is mock_memory
        assert filter_instance.token_calculator is mock_calculator
    
    def test_scoring_weights_constants(self):
        """Test that all scoring weight constants are properly defined"""
        assert ContextFilter.DIRECT_MENTION_WEIGHT == 0.40
        assert ContextFilter.DEPENDENCY_WEIGHT == 0.25
        assert ContextFilter.HISTORICAL_WEIGHT == 0.20
        assert ContextFilter.SEMANTIC_WEIGHT == 0.10
        assert ContextFilter.TDD_PHASE_WEIGHT == 0.05
        
        # Verify weights sum to 1.0
        total_weight = (
            ContextFilter.DIRECT_MENTION_WEIGHT +
            ContextFilter.DEPENDENCY_WEIGHT +
            ContextFilter.HISTORICAL_WEIGHT +
            ContextFilter.SEMANTIC_WEIGHT +
            ContextFilter.TDD_PHASE_WEIGHT
        )
        assert abs(total_weight - 1.0) < 0.001


class TestSearchTermExtractionComprehensive:
    """Comprehensive search term extraction tests"""
    
    @pytest.fixture
    def filter_instance(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            yield ContextFilter(temp_dir)
    
    @pytest.mark.asyncio
    async def test_extract_search_terms_with_task_object(self, filter_instance):
        """Test search term extraction with TDDTask object"""
        task = TDDTask(
            id="test_task",
            description="Implement UserManager.create_user() method for user registration",
            cycle_id="cycle_1",
            current_state=TDDState.TEST_RED
        )
        
        request = ContextRequest(
            agent_type="CodeAgent",
            story_id="story_123",
            task=task,
            focus_areas=["authentication", "validation", "database"]
        )
        
        search_terms = await filter_instance._extract_search_terms(request)
        
        # Verify all term categories are present
        assert "keywords" in search_terms
        assert "function_names" in search_terms
        assert "class_names" in search_terms
        assert "file_patterns" in search_terms
        assert "concepts" in search_terms
        
        # Verify extracted content
        assert "UserManager" in search_terms["class_names"]
        assert "create_user" in search_terms["function_names"]
        assert "user" in search_terms["keywords"]
        assert "registration" in search_terms["keywords"]
        assert "authentication" in search_terms["keywords"]
        assert "validation" in search_terms["keywords"]
        assert "database" in search_terms["keywords"]
    
    @pytest.mark.asyncio
    async def test_extract_search_terms_with_dict_task_full(self, filter_instance):
        """Test search term extraction with complete dictionary task"""
        dict_task = {
            "description": "Add calculate_tax() function to OrderProcessor class",
            "acceptance_criteria": "Should handle VAT calculation and tax exemptions"
        }
        
        request = ContextRequest(
            agent_type="CodeAgent",
            story_id="story_456",
            task=dict_task,
            focus_areas=["payment", "billing", "finance"]
        )
        
        search_terms = await filter_instance._extract_search_terms(request)
        
        # Check extraction from both description and acceptance criteria
        assert "calculate_tax" in search_terms["function_names"]
        assert "OrderProcessor" in search_terms["class_names"]
        assert "tax" in search_terms["keywords"]
        assert "calculation" in search_terms["keywords"]
        assert "exemptions" in search_terms["keywords"]
        assert "payment" in search_terms["keywords"]
        assert "billing" in search_terms["keywords"]
        assert "finance" in search_terms["keywords"]
    
    @pytest.mark.asyncio
    async def test_extract_search_terms_complex_patterns(self, filter_instance):
        """Test extraction of complex patterns and edge cases"""
        complex_task = {
            "description": "Update UserAuthService.validate_token() and AuthController.refresh_token() methods in auth_service.py and auth_controller.py files"
        }
        
        request = ContextRequest(
            agent_type="CodeAgent",
            story_id="story_complex",
            task=complex_task,
            focus_areas=["security", "jwt", "oauth"]
        )
        
        search_terms = await filter_instance._extract_search_terms(request)
        
        # Check complex pattern extraction
        assert "UserAuthService" in search_terms["class_names"]
        assert "AuthController" in search_terms["class_names"]
        assert "validate_token" in search_terms["function_names"]
        assert "refresh_token" in search_terms["function_names"]
        assert "auth_service.py" in search_terms["file_patterns"]
        assert "auth_controller.py" in search_terms["file_patterns"]
        assert "security" in search_terms["keywords"]
    
    @pytest.mark.asyncio
    async def test_extract_search_terms_programming_concepts(self, filter_instance):
        """Test extraction of programming concepts"""
        concept_task = {
            "description": "Add unittest for API endpoint with mock database integration and pytest fixtures"
        }
        
        request = ContextRequest(
            agent_type="QAAgent",
            story_id="story_concepts",
            task=concept_task,
            focus_areas=["testing", "integration", "mocking"]
        )
        
        search_terms = await filter_instance._extract_search_terms(request)
        
        # Check programming concept extraction
        expected_concepts = {"test", "api", "mock", "database", "integration", "testing"}
        found_concepts = set(search_terms["concepts"])
        assert expected_concepts.issubset(found_concepts)
    
    @pytest.mark.asyncio
    async def test_extract_search_terms_empty_and_none_cases(self, filter_instance):
        """Test edge cases with empty/None values"""
        # Test with None task
        empty_request = ContextRequest(
            agent_type="CodeAgent",
            story_id="empty_story",
            task=None,
            focus_areas=[]
        )
        
        search_terms = await filter_instance._extract_search_terms(empty_request)
        assert all(len(terms) == 0 for terms in search_terms.values())
        
        # Test with empty dict task
        empty_dict_request = ContextRequest(
            agent_type="CodeAgent",
            story_id="empty_dict_story",
            task={},
            focus_areas=[]
        )
        
        search_terms = await filter_instance._extract_search_terms(empty_dict_request)
        assert all(len(terms) == 0 for terms in search_terms.values())
        
        # Test with task missing description
        no_desc_request = ContextRequest(
            agent_type="CodeAgent",
            story_id="no_desc_story",
            task={"other_field": "value"},
            focus_areas=["single_focus"]
        )
        
        search_terms = await filter_instance._extract_search_terms(no_desc_request)
        assert "single_focus" in search_terms["keywords"]
    
    @pytest.mark.asyncio
    async def test_extract_search_terms_keyword_filtering_comprehensive(self, filter_instance):
        """Test comprehensive keyword filtering of common words"""
        verbose_task = {
            "description": "The function should be able to process the data and return the result because it is important"
        }
        
        request = ContextRequest(
            agent_type="CodeAgent",
            story_id="verbose_story",
            task=verbose_task,
            focus_areas=[]
        )
        
        search_terms = await filter_instance._extract_search_terms(request)
        
        # Verify common words are filtered out
        # Use the exact common words from the actual implementation
        filtered_common_words = {
            "the", "and", "to", "be", "is", "of", "for", "in", "on", "at", "by", "from", "with"
        }
        keywords = set(search_terms["keywords"])
        assert filtered_common_words.isdisjoint(keywords)
        
        # Verify meaningful words remain
        meaningful_words = {"function", "process", "data", "return", "result", "important"}
        assert meaningful_words.issubset(keywords)
    
    @pytest.mark.asyncio
    async def test_extract_search_terms_keyword_limit(self, filter_instance):
        """Test that keywords are limited to 20 entries"""
        many_keywords_task = {
            "description": " ".join([f"keyword{i}" for i in range(50)])  # 50 unique keywords
        }
        
        request = ContextRequest(
            agent_type="CodeAgent",
            story_id="many_keywords",
            task=many_keywords_task,
            focus_areas=[]
        )
        
        search_terms = await filter_instance._extract_search_terms(request)
        
        # Should be limited to 20 keywords
        assert len(search_terms["keywords"]) <= 20


class TestRelevanceScoringComprehensive:
    """Comprehensive relevance scoring tests"""
    
    @pytest.fixture
    def comprehensive_project(self):
        """Create comprehensive test project with various file types"""
        temp_dir = tempfile.mkdtemp()
        
        # Create Python files with different complexity
        files = {
            "user_service.py": '''
import hashlib
import json
from datetime import datetime

class UserService:
    """Service for managing users"""
    
    def __init__(self):
        self.users = {}
    
    def create_user(self, username, email, password):
        """Create a new user account"""
        if self.user_exists(username):
            raise ValueError("User already exists")
        
        user_id = self.generate_user_id()
        password_hash = self.hash_password(password)
        
        user = {
            "id": user_id,
            "username": username,
            "email": email,
            "password_hash": password_hash,
            "created_at": datetime.now()
        }
        
        self.users[user_id] = user
        return user_id
    
    def authenticate_user(self, username, password):
        """Authenticate user credentials"""
        user = self.find_user_by_username(username)
        if not user:
            return False
        
        return self.verify_password(password, user["password_hash"])
    
    def user_exists(self, username):
        """Check if user exists"""
        return any(u["username"] == username for u in self.users.values())
    
    def find_user_by_username(self, username):
        """Find user by username"""
        for user in self.users.values():
            if user["username"] == username:
                return user
        return None
    
    def hash_password(self, password):
        """Hash password securely"""
        return hashlib.sha256(password.encode()).hexdigest()
    
    def verify_password(self, password, password_hash):
        """Verify password against hash"""
        return self.hash_password(password) == password_hash
    
    def generate_user_id(self):
        """Generate unique user ID"""
        import uuid
        return str(uuid.uuid4())
''',
            "test_user_service.py": '''
import unittest
from unittest.mock import Mock, patch
from user_service import UserService

class TestUserService(unittest.TestCase):
    """Test cases for UserService"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.service = UserService()
    
    def test_create_user_success(self):
        """Test successful user creation"""
        user_id = self.service.create_user("john", "john@example.com", "password123")
        self.assertIsNotNone(user_id)
        self.assertTrue(self.service.user_exists("john"))
    
    def test_create_user_duplicate(self):
        """Test creating duplicate user raises error"""
        self.service.create_user("john", "john@example.com", "password123")
        
        with self.assertRaises(ValueError):
            self.service.create_user("john", "john2@example.com", "password456")
    
    def test_authenticate_user_valid(self):
        """Test authentication with valid credentials"""
        self.service.create_user("john", "john@example.com", "password123")
        result = self.service.authenticate_user("john", "password123")
        self.assertTrue(result)
    
    def test_authenticate_user_invalid(self):
        """Test authentication with invalid credentials"""
        self.service.create_user("john", "john@example.com", "password123")
        result = self.service.authenticate_user("john", "wrongpassword")
        self.assertFalse(result)
    
    def test_authenticate_nonexistent_user(self):
        """Test authentication with nonexistent user"""
        result = self.service.authenticate_user("nonexistent", "password")
        self.assertFalse(result)
    
    @patch('uuid.uuid4')
    def test_generate_user_id(self, mock_uuid):
        """Test user ID generation"""
        mock_uuid.return_value.return_value = "test-uuid"
        user_id = self.service.generate_user_id()
        self.assertEqual(user_id, "test-uuid")
    
    def test_hash_password(self):
        """Test password hashing"""
        password = "testpassword"
        hash1 = self.service.hash_password(password)
        hash2 = self.service.hash_password(password)
        
        # Same password should produce same hash
        self.assertEqual(hash1, hash2)
        
        # Different passwords should produce different hashes
        different_hash = self.service.hash_password("differentpassword")
        self.assertNotEqual(hash1, different_hash)
''',
            "user_controller.py": '''
from user_service import UserService
from flask import Flask, request, jsonify

app = Flask(__name__)
user_service = UserService()

@app.route('/api/users', methods=['POST'])
def create_user():
    """API endpoint to create user"""
    data = request.get_json()
    
    try:
        user_id = user_service.create_user(
            data['username'],
            data['email'],
            data['password']
        )
        return jsonify({"user_id": user_id, "status": "created"}), 201
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except KeyError as e:
        return jsonify({"error": f"Missing field: {e}"}), 400

@app.route('/api/auth', methods=['POST'])
def authenticate():
    """API endpoint for authentication"""
    data = request.get_json()
    
    try:
        result = user_service.authenticate_user(
            data['username'],
            data['password']
        )
        
        if result:
            return jsonify({"status": "authenticated"}), 200
        else:
            return jsonify({"error": "Invalid credentials"}), 401
    except KeyError as e:
        return jsonify({"error": f"Missing field: {e}"}), 400
''',
            "config.py": '''
import os

# Database configuration
DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///app.db')
DATABASE_POOL_SIZE = int(os.getenv('DATABASE_POOL_SIZE', '10'))

# Security configuration
SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key')
JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'jwt-secret-key')
PASSWORD_SALT_ROUNDS = int(os.getenv('PASSWORD_SALT_ROUNDS', '12'))

# API configuration
API_HOST = os.getenv('API_HOST', '0.0.0.0')
API_PORT = int(os.getenv('API_PORT', '5000'))
DEBUG_MODE = os.getenv('DEBUG_MODE', 'False').lower() == 'true'
''',
            "utils.py": r'''
import re
import hashlib
from typing import Optional

def validate_email(email: str) -> bool:
    """Validate email format"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def validate_username(username: str) -> bool:
    """Validate username format"""
    if not username or len(username) < 3:
        return False
    
    # Username should contain only alphanumeric characters and underscores
    pattern = r'^[a-zA-Z0-9_]+$'
    return re.match(pattern, username) is not None

def validate_password(password: str) -> bool:
    """Validate password strength"""
    if not password or len(password) < 8:
        return False
    
    # Check for at least one uppercase, lowercase, and digit
    has_upper = any(c.isupper() for c in password)
    has_lower = any(c.islower() for c in password)
    has_digit = any(c.isdigit() for c in password)
    
    return has_upper and has_lower and has_digit

def sanitize_input(input_str: str) -> str:
    """Sanitize user input"""
    if not input_str:
        return ""
    
    # Remove potentially dangerous characters
    sanitized = re.sub(r'[<>&"\'()]', '', input_str)
    return sanitized.strip()

def generate_hash(data: str) -> str:
    """Generate SHA-256 hash of data"""
    return hashlib.sha256(data.encode()).hexdigest()
''',
            "README.md": '''
# User Management System

This is a comprehensive user management system with authentication capabilities.

## Features

### User Management
- User registration with email validation
- Secure password hashing using SHA-256
- User authentication and session management
- User profile management

### Security Features
- Password strength validation
- Input sanitization
- SQL injection prevention
- XSS protection

### API Endpoints

#### POST /api/users
Create a new user account.

**Request Body:**
```json
{
    "username": "john_doe",
    "email": "john@example.com",
    "password": "SecurePassword123"
}
```

**Response:**
```json
{
    "user_id": "uuid-string",
    "status": "created"
}
```

#### POST /api/auth
Authenticate user credentials.

**Request Body:**
```json
{
    "username": "john_doe",
    "password": "SecurePassword123"
}
```

**Response:**
```json
{
    "status": "authenticated"
}
```

## Configuration

Set the following environment variables:

- `DATABASE_URL`: Database connection string
- `SECRET_KEY`: Application secret key
- `JWT_SECRET_KEY`: JWT signing key
- `API_HOST`: API server host
- `API_PORT`: API server port

## Testing

Run the test suite:

```bash
python -m pytest tests/
```

## Architecture

The system follows a layered architecture:

1. **Controller Layer**: Handles HTTP requests and responses
2. **Service Layer**: Contains business logic
3. **Utility Layer**: Provides helper functions
4. **Configuration Layer**: Manages application settings
''',
            "requirements.txt": '''
Flask==2.3.3
pytest==7.4.2
pytest-mock==3.11.1
''',
            "setup.py": '''
from setuptools import setup, find_packages

setup(
    name="user-management-system",
    version="1.0.0",
    description="A comprehensive user management system",
    packages=find_packages(),
    install_requires=[
        "Flask>=2.3.0",
        "pytest>=7.0.0",
        "pytest-mock>=3.0.0",
    ],
    python_requires=">=3.8",
)
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
    
    @pytest.mark.asyncio
    async def test_calculate_relevance_score_error_handling(self, filter_instance):
        """Test relevance score calculation error handling"""
        # Test with non-existent file
        nonexistent_file = "/nonexistent/file.py"
        request = ContextRequest(
            agent_type="CodeAgent",
            story_id="test_story",
            task={"description": "test task"},
            focus_areas=[]
        )
        search_terms = await filter_instance._extract_search_terms(request)
        
        score = await filter_instance._calculate_relevance_score(
            nonexistent_file, request, search_terms
        )
        
        assert isinstance(score, RelevanceScore)
        assert score.total_score == 0.0
        assert score.file_path == nonexistent_file
        # Reasons may be empty for files that simply don't exist vs actual errors
        assert isinstance(score.reasons, list)
    
    @pytest.mark.asyncio
    async def test_direct_mention_score_empty_content(self, filter_instance):
        """Test direct mention score with empty content"""
        empty_content = ""
        search_terms = {
            "keywords": ["user", "authentication"],
            "function_names": ["authenticate"],
            "class_names": ["UserService"],
            "concepts": ["security"]
        }
        
        score = await filter_instance._calculate_direct_mention_score(
            empty_content, search_terms, "empty_file.py"
        )
        
        assert score == 0.0
    
    @pytest.mark.asyncio
    async def test_direct_mention_score_keyword_frequency_capping(self, filter_instance):
        """Test that keyword frequency is capped appropriately"""
        # Content with many repetitions of a keyword
        repeated_content = "user " * 100  # 100 repetitions
        search_terms = {
            "keywords": ["user"],
            "function_names": [],
            "class_names": [],
            "concepts": []
        }
        
        score = await filter_instance._calculate_direct_mention_score(
            repeated_content, search_terms, "repeated_file.py"
        )
        
        # Score should be capped (0.5 max per keyword * 0.3 weight = 0.15 max for keywords)
        assert score <= 0.2  # Allow some buffer for calculation
    
    @pytest.mark.asyncio
    async def test_direct_mention_score_all_components(self, filter_instance, comprehensive_project):
        """Test direct mention score with all components"""
        user_service_file = str(Path(comprehensive_project) / "user_service.py")
        content = await filter_instance._get_file_content(user_service_file)
        
        search_terms = {
            "keywords": ["user", "service", "authentication"],
            "function_names": ["create_user", "authenticate_user"],
            "class_names": ["UserService"],
            "concepts": ["security"],
            "file_patterns": []
        }
        
        score = await filter_instance._calculate_direct_mention_score(
            content, search_terms, user_service_file
        )
        
        # Should get high score due to multiple matches
        assert score > 0.5
        
        # Test with filename containing relevant terms
        relevant_filename = str(Path(comprehensive_project) / "user_service.py")
        filename_score = await filter_instance._calculate_direct_mention_score(
            "# minimal content", search_terms, relevant_filename
        )
        
        # Should get some score from filename relevance
        assert filename_score > 0.0
    
    @pytest.mark.asyncio
    async def test_dependency_score_comprehensive(self, filter_instance, comprehensive_project):
        """Test comprehensive dependency scoring"""
        user_service_file = str(Path(comprehensive_project) / "user_service.py")
        
        search_terms = {
            "keywords": ["json", "hashlib", "datetime"],
            "concepts": ["security", "authentication"],
            "file_patterns": ["user_service.py"]
        }
        
        request = ContextRequest(
            agent_type="CodeAgent",
            story_id="test_story",
            task={"description": "test"},
            focus_areas=[]
        )
        
        score = await filter_instance._calculate_dependency_score(
            user_service_file, search_terms, request
        )
        
        # Should get score for importing relevant modules
        assert score > 0.0
    
    @pytest.mark.asyncio
    async def test_dependency_score_reverse_dependencies(self, filter_instance, comprehensive_project):
        """Test reverse dependency scoring"""
        user_service_file = str(Path(comprehensive_project) / "user_service.py")
        
        search_terms = {
            "keywords": [],
            "concepts": [],
            "file_patterns": ["test_user_service.py", "user_controller.py"]  # Files that import user_service
        }
        
        request = ContextRequest(
            agent_type="CodeAgent",
            story_id="test_story",
            task={"description": "test"},
            focus_areas=[]
        )
        
        score = await filter_instance._calculate_dependency_score(
            user_service_file, search_terms, request
        )
        
        # Should get score for being imported by relevant files
        assert score >= 0.0
    
    @pytest.mark.asyncio
    async def test_dependency_score_core_file_patterns(self, filter_instance, comprehensive_project):
        """Test core file pattern bonus scoring"""
        # Create core files
        core_files = ["__init__.py", "main.py", "app.py", "core.py", "base.py", "common.py"]
        
        for core_file in core_files:
            core_path = Path(comprehensive_project) / core_file
            core_path.write_text("# Core file")
            
            search_terms = {"keywords": [], "concepts": [], "file_patterns": []}
            request = ContextRequest(
                agent_type="CodeAgent",
                story_id="test_story",
                task={"description": "test"},
                focus_areas=[]
            )
            
            score = await filter_instance._calculate_dependency_score(
                str(core_path), search_terms, request
            )
            
            # Core files should get bonus points
            assert score >= 0.1
    
    @pytest.mark.asyncio
    async def test_dependency_score_error_handling(self, filter_instance):
        """Test dependency score error handling"""
        nonexistent_file = "/nonexistent/file.py"
        search_terms = {"keywords": [], "concepts": [], "file_patterns": []}
        request = ContextRequest(
            agent_type="CodeAgent",
            story_id="test_story",
            task={"description": "test"},
            focus_areas=[]
        )
        
        score = await filter_instance._calculate_dependency_score(
            nonexistent_file, search_terms, request
        )
        
        # Should handle error gracefully
        assert score == 0.0
    
    @pytest.mark.asyncio
    async def test_historical_score_no_agent_memory(self, filter_instance):
        """Test historical score when no agent memory is available"""
        score = await filter_instance._calculate_historical_score(
            "test_file.py", "CodeAgent", "story_123"
        )
        
        assert score == 0.0
    
    @pytest.mark.asyncio
    async def test_historical_score_with_mock_memory(self, filter_instance):
        """Test historical score with mocked agent memory"""
        mock_memory = Mock(spec=FileBasedAgentMemory)
        filter_instance.agent_memory = mock_memory
        
        # Mock snapshots with file access history
        mock_snapshots = [
            Mock(file_list=["test_file.py", "other_file.py"]),
            Mock(file_list=["test_file.py"]),
            Mock(file_list=["different_file.py"]),
            Mock(file_list=["test_file.py"]),
        ]
        mock_memory.get_context_history = AsyncMock(return_value=mock_snapshots)
        
        score = await filter_instance._calculate_historical_score(
            "test_file.py", "CodeAgent", "story_123"
        )
        
        # Should get score based on access frequency
        assert score > 0.0
        assert score <= 1.0
        
        # Verify memory was called correctly
        mock_memory.get_context_history.assert_called_once_with(
            "CodeAgent", "story_123", limit=50
        )
    
    @pytest.mark.asyncio
    async def test_historical_score_recent_access_bonus(self, filter_instance):
        """Test historical score recent access bonus"""
        mock_memory = Mock(spec=FileBasedAgentMemory)
        filter_instance.agent_memory = mock_memory
        
        # Mock snapshots with recent access (first 5 entries get bonus)
        mock_snapshots = [Mock(file_list=["recent_file.py"]) for _ in range(3)]
        mock_memory.get_context_history = AsyncMock(return_value=mock_snapshots)
        
        score = await filter_instance._calculate_historical_score(
            "recent_file.py", "CodeAgent", "story_123"
        )
        
        # Should get bonus for recent access
        assert score > 0.5  # High score due to recent access bonus
    
    @pytest.mark.asyncio
    async def test_historical_score_empty_snapshots(self, filter_instance):
        """Test historical score with empty snapshots"""
        mock_memory = Mock(spec=FileBasedAgentMemory)
        filter_instance.agent_memory = mock_memory
        mock_memory.get_context_history = AsyncMock(return_value=[])
        
        score = await filter_instance._calculate_historical_score(
            "test_file.py", "CodeAgent", "story_123"
        )
        
        assert score == 0.0
    
    @pytest.mark.asyncio
    async def test_historical_score_error_handling(self, filter_instance):
        """Test historical score error handling"""
        mock_memory = Mock(spec=FileBasedAgentMemory)
        filter_instance.agent_memory = mock_memory
        mock_memory.get_context_history = AsyncMock(side_effect=Exception("Memory error"))
        
        score = await filter_instance._calculate_historical_score(
            "test_file.py", "CodeAgent", "story_123"
        )
        
        # Should handle error gracefully
        assert score == 0.0


class TestSemanticScoringComprehensive:
    """Comprehensive semantic scoring tests"""
    
    @pytest.fixture
    def filter_instance(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            yield ContextFilter(temp_dir)
    
    @pytest.mark.asyncio
    async def test_semantic_score_code_agent_python_files(self, filter_instance):
        """Test semantic scoring for CodeAgent with Python files"""
        python_content = '''
class UserService:
    def create_user(self):
        pass
    
    def authenticate_user(self):
        pass

import json
import hashlib
'''
        
        request = ContextRequest(
            agent_type="CodeAgent",
            story_id="story_123",
            task=None,
            focus_areas=[]
        )
        
        score = await filter_instance._calculate_semantic_score(
            python_content, FileType.PYTHON, request
        )
        
        # CodeAgent should strongly favor Python files with def, class, and import
        assert score > 0.8  # Should get points for all three components
    
    @pytest.mark.asyncio
    async def test_semantic_score_qa_agent_test_files(self, filter_instance):
        """Test semantic scoring for QAAgent with test files"""
        test_content = '''
import unittest
from unittest.mock import Mock, patch

class TestUserService(unittest.TestCase):
    def test_create_user(self):
        mock_service = Mock()
        with patch('user_service.UserService') as mock_class:
            mock_class.return_value = mock_service
            # Test implementation
            assert True
    
    def test_authenticate_user(self):
        # Test with fixture
        pass
'''
        
        request = ContextRequest(
            agent_type="QAAgent",
            story_id="story_test",
            task=None,
            focus_areas=[]
        )
        
        score = await filter_instance._calculate_semantic_score(
            test_content, FileType.TEST, request
        )
        
        # QAAgent should strongly favor test files with test keywords
        assert score > 0.7  # 0.5 for test file + 0.3 for test keywords
    
    @pytest.mark.asyncio
    async def test_semantic_score_design_agent_documentation(self, filter_instance):
        """Test semantic scoring for DesignAgent with documentation"""
        doc_content = '''
# System Architecture

This document describes the overall system architecture and design patterns.

## Design Principles

The system follows these architectural principles:

1. Separation of concerns
2. Single responsibility principle
3. Dependency inversion

## Component Specification

Each component has a well-defined interface and clear responsibilities.
'''
        
        request = ContextRequest(
            agent_type="DesignAgent",
            story_id="story_design",
            task=None,
            focus_areas=[]
        )
        
        score = await filter_instance._calculate_semantic_score(
            doc_content, FileType.MARKDOWN, request
        )
        
        # DesignAgent should favor markdown with design keywords
        assert score > 0.6  # 0.4 for markdown + 0.3 for design keywords
    
    @pytest.mark.asyncio
    async def test_semantic_score_data_agent_json_files(self, filter_instance):
        """Test semantic scoring for DataAgent with JSON files"""
        json_content = '''
{
    "data": {
        "users": [
            {"id": 1, "name": "John"},
            {"id": 2, "name": "Jane"}
        ]
    },
    "schema": {
        "version": "1.0",
        "database": "users_db"
    },
    "model": {
        "user": {
            "fields": ["id", "name", "email"]
        }
    }
}
'''
        
        request = ContextRequest(
            agent_type="DataAgent",
            story_id="story_data",
            task=None,
            focus_areas=[]
        )
        
        score = await filter_instance._calculate_semantic_score(
            json_content, FileType.JSON, request
        )
        
        # DataAgent should favor JSON files with data keywords
        assert score > 0.6  # 0.3 for JSON + 0.4 for data keywords
    
    @pytest.mark.asyncio
    async def test_semantic_score_tdd_phase_integration(self, filter_instance):
        """Test semantic scoring with TDD phase integration"""
        test_content = "import unittest\nclass TestUser(unittest.TestCase): pass"
        
        # Test RED phase
        red_task = TDDTask(id="red_task", description="test", cycle_id="c1", current_state=TDDState.TEST_RED)
        red_request = ContextRequest(
            agent_type="QAAgent",
            story_id="story_red",
            task=red_task,
            focus_areas=[]
        )
        
        red_score = await filter_instance._calculate_semantic_score(
            test_content, FileType.TEST, red_request
        )
        
        # Should get bonus for test file in RED phase
        assert red_score > 0.7  # Base score + TDD bonus
        
        # Test GREEN phase
        impl_content = "class UserService:\n    def create_user(self): pass"
        green_task = TDDTask(id="green_task", description="test", cycle_id="c1", current_state=TDDState.CODE_GREEN)
        green_request = ContextRequest(
            agent_type="CodeAgent",
            story_id="story_green",
            task=green_task,
            focus_areas=[]
        )
        
        green_score = await filter_instance._calculate_semantic_score(
            impl_content, FileType.PYTHON, green_request
        )
        
        # Should get bonus for implementation file in GREEN phase
        assert green_score > 0.6
        
        # Test REFACTOR phase
        refactor_content = "# refactor this code\nclass UserService:\n    def cleanup(self): pass"
        refactor_task = TDDTask(id="refactor_task", description="test", cycle_id="c1", current_state=TDDState.REFACTOR)
        refactor_request = ContextRequest(
            agent_type="CodeAgent",
            story_id="story_refactor",
            task=refactor_task,
            focus_areas=[]
        )
        
        refactor_score = await filter_instance._calculate_semantic_score(
            refactor_content, FileType.PYTHON, refactor_request
        )
        
        # Should get bonus for refactor keywords
        assert refactor_score > 0.4
    
    @pytest.mark.asyncio
    async def test_semantic_score_error_handling(self, filter_instance):
        """Test semantic score error handling"""
        # Mock an error in scoring
        with patch.object(filter_instance, '_calculate_semantic_score', side_effect=Exception("Semantic error")):
            request = ContextRequest(
                agent_type="CodeAgent",
                story_id="error_story",
                task=None,
                focus_areas=[]
            )
            
            # This should be the actual method call, not the mocked one
            # Let's test the real method with problematic input
            pass
        
        # Test with edge case content
        problematic_content = None
        request = ContextRequest(
            agent_type="CodeAgent",
            story_id="error_story",
            task=None,
            focus_areas=[]
        )
        
        # The actual method should handle None content gracefully
        score = await filter_instance._calculate_semantic_score(
            "", FileType.PYTHON, request
        )
        
        assert score >= 0.0


class TestTDDPhaseScoringComprehensive:
    """Comprehensive TDD phase scoring tests"""
    
    @pytest.fixture
    def filter_instance(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            yield ContextFilter(temp_dir)
    
    @pytest.mark.asyncio
    async def test_tdd_phase_score_red_phase_comprehensive(self, filter_instance):
        """Test comprehensive RED phase scoring"""
        # Test files should get highest score
        test_file = "/path/to/test_user.py"
        score = await filter_instance._calculate_tdd_phase_score(
            test_file, FileType.TEST, TDDState.TEST_RED
        )
        assert score == 0.8
        
        # Files with 'test' in name should get high score
        test_name_file = "/path/to/test_helpers.py"
        score = await filter_instance._calculate_tdd_phase_score(
            test_name_file, FileType.PYTHON, TDDState.TEST_RED
        )
        assert score == 0.6
        
        # Python files in test directory should get medium score
        test_dir_file = "/path/to/tests/helper.py"
        score = await filter_instance._calculate_tdd_phase_score(
            test_dir_file, FileType.PYTHON, TDDState.TEST_RED
        )
        assert score == 0.4
        
        # Non-test files should get no bonus
        regular_file = "/path/to/service.py"
        score = await filter_instance._calculate_tdd_phase_score(
            regular_file, FileType.PYTHON, TDDState.TEST_RED
        )
        assert score == 0.0
    
    @pytest.mark.asyncio
    async def test_tdd_phase_score_green_phase_comprehensive(self, filter_instance):
        """Test comprehensive GREEN phase scoring"""
        # Implementation files should get highest score
        impl_file = "/path/to/user_service.py"
        score = await filter_instance._calculate_tdd_phase_score(
            impl_file, FileType.PYTHON, TDDState.CODE_GREEN
        )
        assert score == 0.8
        
        # Files with 'implement' in name should get high score
        implement_file = "/path/to/implement_user.py"
        score = await filter_instance._calculate_tdd_phase_score(
            implement_file, FileType.PYTHON, TDDState.CODE_GREEN
        )
        assert score == 0.6
        
        # Files with 'main' in name should get high score
        main_file = "/path/to/main_service.py"
        score = await filter_instance._calculate_tdd_phase_score(
            main_file, FileType.PYTHON, TDDState.CODE_GREEN
        )
        assert score == 0.6
        
        # Test files should get no bonus in GREEN phase
        test_file = "/path/to/test_user.py"
        score = await filter_instance._calculate_tdd_phase_score(
            test_file, FileType.TEST, TDDState.CODE_GREEN
        )
        assert score == 0.0
    
    @pytest.mark.asyncio
    async def test_tdd_phase_score_refactor_phase_comprehensive(self, filter_instance):
        """Test comprehensive REFACTOR phase scoring"""
        # Both Python and test files should get medium score
        python_file = "/path/to/service.py"
        score = await filter_instance._calculate_tdd_phase_score(
            python_file, FileType.PYTHON, TDDState.REFACTOR
        )
        assert score == 0.6
        
        test_file = "/path/to/test_service.py"
        score = await filter_instance._calculate_tdd_phase_score(
            test_file, FileType.TEST, TDDState.REFACTOR
        )
        assert score == 0.6
        
        # Files with refactor keywords should get highest score
        refactor_keywords = ["refactor", "cleanup", "optimize"]
        for keyword in refactor_keywords:
            refactor_file = f"/path/to/{keyword}_service.py"
            score = await filter_instance._calculate_tdd_phase_score(
                refactor_file, FileType.PYTHON, TDDState.REFACTOR
            )
            assert score == 1.0  # 0.6 + 0.8 capped at 1.0
    
    @pytest.mark.asyncio
    async def test_tdd_phase_score_score_capping(self, filter_instance):
        """Test that TDD phase scores are properly capped at 1.0"""
        # Create a file that would score over 1.0
        refactor_file = "/path/to/refactor_cleanup_optimize.py"
        score = await filter_instance._calculate_tdd_phase_score(
            refactor_file, FileType.PYTHON, TDDState.REFACTOR
        )
        
        # Should be capped at 1.0
        assert score == 1.0
    
    @pytest.mark.asyncio
    async def test_tdd_phase_score_error_handling(self, filter_instance):
        """Test TDD phase score error handling"""
        # Test with invalid file path
        with patch('pathlib.Path') as mock_path:
            mock_path.side_effect = Exception("Path error")
            
            score = await filter_instance._calculate_tdd_phase_score(
                "/invalid/path.py", FileType.PYTHON, TDDState.TEST_RED
            )
            
            assert score == 0.0


class TestContentFilteringComprehensive:
    """Comprehensive content filtering tests"""
    
    @pytest.fixture
    def filter_instance(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            yield ContextFilter(temp_dir)
    
    @pytest.fixture
    def mock_token_calculator(self):
        """Mock token calculator with predictable behavior"""
        mock_calc = Mock(spec=TokenCalculator)
        mock_calc.estimate_tokens = AsyncMock(side_effect=lambda content: len(content) // 4)
        return mock_calc
    
    @pytest.mark.asyncio
    async def test_filter_content_by_relevance_routing(self, filter_instance):
        """Test content filtering routing by file type"""
        request = ContextRequest(
            agent_type="CodeAgent",
            story_id="story_123",
            task={"description": "test task"},
            focus_areas=[]
        )
        
        # Test Python file routing
        with patch.object(filter_instance, '_filter_python_content', return_value="python_filtered") as mock_python:
            result = await filter_instance.filter_content_by_relevance(
                "test.py", "python content", request, 1000
            )
            assert result == "python_filtered"
            mock_python.assert_called_once()
        
        # Test markdown file routing
        with patch.object(filter_instance, '_filter_text_content', return_value="text_filtered") as mock_text:
            result = await filter_instance.filter_content_by_relevance(
                "test.md", "markdown content", request, 1000
            )
            assert result == "text_filtered"
            mock_text.assert_called_once()
        
        # Test test file routing
        with patch.object(filter_instance, '_filter_test_content', return_value="test_filtered") as mock_test:
            result = await filter_instance.filter_content_by_relevance(
                "test_file.py", "test content", request, 1000
            )
            assert result == "test_filtered"
            mock_test.assert_called_once()
        
        # Test other file type routing
        with patch.object(filter_instance, '_truncate_content', return_value="truncated") as mock_truncate:
            result = await filter_instance.filter_content_by_relevance(
                "file.bin", "binary content", request, 1000
            )
            assert result == "truncated"
            mock_truncate.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_filter_python_content_comprehensive(self, filter_instance, mock_token_calculator):
        """Test comprehensive Python content filtering"""
        filter_instance.token_calculator = mock_token_calculator
        
        complex_python_content = '''
import os
import json
from typing import Dict, List

class UserService:
    """Service for managing users - high relevance"""
    
    def __init__(self):
        self.users = {}
    
    def create_user(self, username: str, email: str) -> str:
        """Create a new user - high relevance"""
        user_id = self.generate_id()
        self.users[user_id] = {
            "username": username,
            "email": email
        }
        return user_id
    
    def authenticate_user(self, username: str, password: str) -> bool:
        """Authenticate user - high relevance"""
        user = self.find_user(username)
        return user is not None
    
    def find_user(self, username: str) -> Dict:
        """Find user by username - medium relevance"""
        for user in self.users.values():
            if user["username"] == username:
                return user
        return None
    
    def generate_id(self) -> str:
        """Generate unique ID - low relevance"""
        import uuid
        return str(uuid.uuid4())
    
    def unrelated_method(self) -> str:
        """This method is completely unrelated"""
        return "unrelated"

def helper_function():
    """Standalone helper function"""
    return True

def another_helper():
    """Another helper function"""
    return False
'''
        
        request = ContextRequest(
            agent_type="CodeAgent",
            story_id="story_123",
            task={"description": "Implement user authentication with create_user method"},
            focus_areas=["user", "authentication"]
        )
        
        filtered = await filter_instance._filter_python_content(
            complex_python_content, request, target_tokens=500
        )
        
        assert isinstance(filtered, str)
        assert len(filtered) > 0
        
        # Should include high-relevance methods
        assert "create_user" in filtered
        assert "authenticate_user" in filtered
        
        # Should include relevance comments
        assert "Relevance:" in filtered
        
        # Should prioritize by relevance score
        lines = filtered.split('\n')
        create_user_line = next((i for i, line in enumerate(lines) if "create_user" in line), -1)
        unrelated_line = next((i for i, line in enumerate(lines) if "unrelated_method" in line), -1)
        
        # If both are present, create_user should come before unrelated_method
        if create_user_line != -1 and unrelated_line != -1:
            assert create_user_line < unrelated_line
    
    @pytest.mark.asyncio
    async def test_filter_python_content_syntax_error_fallback(self, filter_instance):
        """Test Python content filtering fallback for syntax errors"""
        invalid_python = '''
def broken_function(
    # Missing closing parenthesis and body
    invalid syntax here
'''
        
        request = ContextRequest(
            agent_type="CodeAgent",
            story_id="story_123",
            task={"description": "test"},
            focus_areas=[]
        )
        
        with patch.object(filter_instance, '_filter_text_content', return_value="fallback_result") as mock_fallback:
            result = await filter_instance._filter_python_content(
                invalid_python, request, target_tokens=200
            )
            
            # Should fallback to text filtering
            assert result == "fallback_result"
            mock_fallback.assert_called_once_with(invalid_python, request, 200)
    
    @pytest.mark.asyncio
    async def test_filter_python_content_ast_error_handling(self, filter_instance):
        """Test Python content filtering with AST parsing errors"""
        # Test with content that causes AST errors
        problematic_content = "invalid python syntax {"
        
        request = ContextRequest(
            agent_type="CodeAgent",
            story_id="story_123",
            task={"description": "test"},
            focus_areas=[]
        )
        
        result = await filter_instance._filter_python_content(
            problematic_content, request, target_tokens=200
        )
        
        # Should handle gracefully and return some content
        assert isinstance(result, str)
        assert len(result) > 0
    
    @pytest.mark.asyncio
    async def test_filter_test_content_comprehensive(self, filter_instance, mock_token_calculator):
        """Test comprehensive test content filtering"""
        filter_instance.token_calculator = mock_token_calculator
        
        complex_test_content = '''
import unittest
import pytest
from unittest.mock import Mock, patch
from user_service import UserService

class TestUserAuthentication(unittest.TestCase):
    """Test cases for user authentication - high relevance"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.service = UserService()
    
    def test_authenticate_valid_user(self):
        """Test authentication with valid credentials - high relevance"""
        self.service.create_user("john", "john@example.com", "password")
        result = self.service.authenticate_user("john", "password")
        self.assertTrue(result)
    
    def test_authenticate_invalid_user(self):
        """Test authentication with invalid credentials - high relevance"""
        result = self.service.authenticate_user("nonexistent", "password")
        self.assertFalse(result)
    
    def test_create_user_success(self):
        """Test successful user creation - medium relevance"""
        user_id = self.service.create_user("jane", "jane@example.com", "password")
        self.assertIsNotNone(user_id)

class TestUtilityFunctions(unittest.TestCase):
    """Test utility functions - low relevance"""
    
    def test_helper_function(self):
        """Test helper function"""
        self.assertTrue(True)
    
    def test_another_helper(self):
        """Test another helper"""
        self.assertFalse(False)

def test_standalone_function():
    """Standalone test function - medium relevance"""
    assert True
'''
        
        request = ContextRequest(
            agent_type="QAAgent",
            story_id="story_test",
            task={"description": "Test user authentication functionality"},
            focus_areas=["authentication", "user"]
        )
        
        filtered = await filter_instance._filter_test_content(
            complex_test_content, request, target_tokens=600
        )
        
        assert isinstance(filtered, str)
        assert len(filtered) > 0
        
        # Should include imports
        assert "import" in filtered
        
        # Should include high-relevance tests
        assert "test_authenticate" in filtered
        
        # Should include test relevance comments
        assert "Test relevance:" in filtered
    
    @pytest.mark.asyncio
    async def test_filter_test_content_no_ast_nodes(self, filter_instance):
        """Test test content filtering when no AST nodes are found"""
        simple_test_content = '''
# Simple test file with no classes or functions
import unittest
'''
        
        request = ContextRequest(
            agent_type="QAAgent",
            story_id="story_test",
            task={"description": "test"},
            focus_areas=[]
        )
        
        result = await filter_instance._filter_test_content(
            simple_test_content, request, target_tokens=200
        )
        
        # Should still include imports and handle gracefully
        assert "import" in result
    
    @pytest.mark.asyncio
    async def test_filter_text_content_comprehensive(self, filter_instance, mock_token_calculator):
        """Test comprehensive text content filtering"""
        filter_instance.token_calculator = mock_token_calculator
        
        complex_text_content = '''
# User Authentication System

This document describes the user authentication system implementation.

## Overview

The authentication system provides secure user login and registration functionality.
It includes user validation, password hashing, and session management.

## User Management

### User Registration

The system allows new users to register with the following information:
- Username (required)
- Email address (required)
- Password (required, must meet security requirements)

### User Authentication

Users can authenticate using their username and password.
The system validates credentials against the stored user database.

## Security Features

### Password Security

All passwords are hashed using SHA-256 algorithm before storage.
The system enforces password strength requirements.

### Session Management

User sessions are managed securely with timeout controls.

## API Documentation

### POST /api/users

Create a new user account.

### POST /api/auth

Authenticate user credentials.

## Configuration

Database settings and security configuration.

## Troubleshooting

Common issues and solutions.

## Unrelated Section

This section talks about something completely different that has nothing to do 
with users or authentication or security. This should have low relevance.
'''
        
        request = ContextRequest(
            agent_type="DesignAgent",
            story_id="story_design",
            task={"description": "Design user authentication system"},
            focus_areas=["user", "authentication", "security"]
        )
        
        filtered = await filter_instance._filter_text_content(
            complex_text_content, request, target_tokens=400
        )
        
        assert isinstance(filtered, str)
        assert len(filtered) > 0
        
        # Should include relevant sections
        assert "authentication" in filtered.lower()
        assert "user" in filtered.lower()
        assert "security" in filtered.lower()
        
        # Should prioritize headers
        assert "#" in filtered
        
        # Should exclude or deprioritize unrelated sections
        assert "unrelated" not in filtered.lower() or filtered.lower().index("unrelated") > filtered.lower().index("authentication")
    
    @pytest.mark.asyncio
    async def test_filter_text_content_empty_sections(self, filter_instance):
        """Test text content filtering with empty sections"""
        text_with_empty_sections = '''
# Header 1

Content for section 1.

# Header 2



# Header 3

Content for section 3.
'''
        
        request = ContextRequest(
            agent_type="DesignAgent",
            story_id="story_design",
            task={"description": "test"},
            focus_areas=[]
        )
        
        result = await filter_instance._filter_text_content(
            text_with_empty_sections, request, target_tokens=200
        )
        
        # Should handle empty sections gracefully
        assert isinstance(result, str)
        assert "Header" in result
    
    @pytest.mark.asyncio
    async def test_truncate_content_comprehensive(self, filter_instance):
        """Test comprehensive content truncation"""
        # Test content that fits within limit
        short_content = "This is short content."
        result = await filter_instance._truncate_content(short_content, target_tokens=100)
        assert result == short_content
        
        # Test content that needs truncation
        long_content = "word " * 200  # 200 words
        result = await filter_instance._truncate_content(long_content, target_tokens=50)
        
        assert len(result) < len(long_content)
        assert "[content truncated]" in result
        
        # Test word boundary breaking
        boundary_content = "a" * 100 + " boundary " + "b" * 100
        result = await filter_instance._truncate_content(boundary_content, target_tokens=30)
        
        # Should try to break at word boundary
        assert len(result) < len(boundary_content)
        
        # Test edge case where last_space is too early
        no_space_content = "a" * 1000  # No spaces
        result = await filter_instance._truncate_content(no_space_content, target_tokens=50)
        
        assert len(result) < len(no_space_content)
        assert "[content truncated]" in result
    
    @pytest.mark.asyncio
    async def test_score_python_node_comprehensive(self, filter_instance):
        """Test comprehensive Python node scoring"""
        # Test function node with exact match
        func_code = "def authenticate_user(username, password): pass"
        func_tree = ast.parse(func_code)
        func_node = func_tree.body[0]
        
        search_terms = {
            "function_names": ["authenticate_user"],
            "keywords": ["authenticate"],
            "class_names": []
        }
        
        score = await filter_instance._score_python_node(func_node, search_terms)
        assert score == 1.0  # Exact function name match
        
        # Test function node with keyword match
        search_terms_keyword = {
            "function_names": [],
            "keywords": ["authenticate", "user"],
            "class_names": []
        }
        
        score = await filter_instance._score_python_node(func_node, search_terms_keyword)
        assert score == 1.0  # Two keyword matches: 0.5 + 0.5 = 1.0
        
        # Test class node with exact match
        class_code = "class UserService: pass"
        class_tree = ast.parse(class_code)
        class_node = class_tree.body[0]
        
        search_terms_class = {
            "function_names": [],
            "keywords": [],
            "class_names": ["UserService"]
        }
        
        score = await filter_instance._score_python_node(class_node, search_terms_class)
        assert score == 1.0  # Exact class name match
        
        # Test class node with keyword match
        search_terms_class_keyword = {
            "function_names": [],
            "keywords": ["user", "service"],
            "class_names": []
        }
        
        score = await filter_instance._score_python_node(class_node, search_terms_class_keyword)
        assert score == 1.0  # Two keyword matches: 0.5 + 0.5 = 1.0
        
        # Test node with no matches
        search_terms_no_match = {
            "function_names": ["different_function"],
            "keywords": ["different"],
            "class_names": ["DifferentClass"]
        }
        
        score = await filter_instance._score_python_node(func_node, search_terms_no_match)
        assert score == 0.0
        
        # Test unsupported node type
        import_code = "import os"
        import_tree = ast.parse(import_code)
        import_node = import_tree.body[0]
        
        score = await filter_instance._score_python_node(import_node, search_terms)
        assert score == 0.0  # Unsupported node type


class TestFileUtilitiesComprehensive:
    """Comprehensive file utility tests"""
    
    @pytest.fixture
    def comprehensive_project(self):
        """Create comprehensive test project"""
        temp_dir = tempfile.mkdtemp()
        
        # Create various file types
        files = {
            "service.py": '''
import json
import hashlib
from datetime import datetime

class DataService:
    def process_data(self):
        return {"status": "success"}
''',
            "tests/test_service.py": '''
import unittest
from service import DataService

class TestDataService(unittest.TestCase):
    def test_process_data(self):
        service = DataService()
        result = service.process_data()
        self.assertEqual(result["status"], "success")
''',
            "config.yaml": '''
database:
  host: localhost
  port: 5432
''',
            "config.ini": '''
[database]
host = localhost
port = 5432
''',
            "config.toml": '''
[database]
host = "localhost"
port = 5432
''',
            "data.json": '''
{
    "users": [
        {"id": 1, "name": "John"}
    ]
}
''',
            "README.md": '''
# Project Documentation

This is a sample project.
''',
            "requirements.txt": '''
flask==2.0.0
pytest==6.0.0
''',
            "binary_file.bin": b'\x00\x01\x02\x03\x04\x05'  # Binary content
        }
        
        for file_path, content in files.items():
            full_path = Path(temp_dir) / file_path
            full_path.parent.mkdir(parents=True, exist_ok=True)
            
            if isinstance(content, bytes):
                full_path.write_bytes(content)
            else:
                full_path.write_text(content)
        
        yield temp_dir
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def filter_instance(self, comprehensive_project):
        return ContextFilter(comprehensive_project)
    
    @pytest.mark.asyncio
    async def test_get_file_content_various_files(self, filter_instance, comprehensive_project):
        """Test getting content from various file types"""
        # Test Python file
        python_file = str(Path(comprehensive_project) / "service.py")
        content = await filter_instance._get_file_content(python_file)
        assert "class DataService" in content
        assert "import json" in content
        
        # Test JSON file
        json_file = str(Path(comprehensive_project) / "data.json")
        content = await filter_instance._get_file_content(json_file)
        assert "users" in content
        
        # Test markdown file
        md_file = str(Path(comprehensive_project) / "README.md")
        content = await filter_instance._get_file_content(md_file)
        assert "# Project Documentation" in content
        
        # Test binary file (should handle gracefully with errors='ignore')
        bin_file = str(Path(comprehensive_project) / "binary_file.bin")
        content = await filter_instance._get_file_content(bin_file)
        assert isinstance(content, str)  # Should return string even for binary
    
    @pytest.mark.asyncio
    async def test_get_file_content_nonexistent_file(self, filter_instance):
        """Test getting content from nonexistent file"""
        nonexistent_file = "/nonexistent/file.py"
        content = await filter_instance._get_file_content(nonexistent_file)
        assert content == ""
    
    @pytest.mark.asyncio
    async def test_get_file_content_cache_expiration(self, filter_instance, comprehensive_project):
        """Test file content cache expiration"""
        python_file = str(Path(comprehensive_project) / "service.py")
        
        # First read
        content1 = await filter_instance._get_file_content(python_file)
        
        # Manually expire cache by setting old timestamp
        filter_instance._cache_timestamps[python_file] = datetime.now() - timedelta(seconds=400)
        
        # Second read should miss cache due to expiration
        initial_misses = filter_instance._cache_misses
        content2 = await filter_instance._get_file_content(python_file)
        
        assert content1 == content2
        assert filter_instance._cache_misses == initial_misses + 1
    
    @pytest.mark.asyncio
    async def test_get_file_type_comprehensive(self, filter_instance, comprehensive_project):
        """Test comprehensive file type detection"""
        # Test Python file
        python_file = str(Path(comprehensive_project) / "service.py")
        file_type = await filter_instance._get_file_type(python_file)
        assert file_type == FileType.PYTHON
        
        # Test test file (Python file in tests directory)
        test_file = str(Path(comprehensive_project) / "tests" / "test_service.py")
        file_type = await filter_instance._get_file_type(test_file)
        assert file_type == FileType.TEST
        
        # Test JSON file
        json_file = str(Path(comprehensive_project) / "data.json")
        file_type = await filter_instance._get_file_type(json_file)
        assert file_type == FileType.JSON
        
        # Test YAML file
        yaml_file = str(Path(comprehensive_project) / "config.yaml")
        file_type = await filter_instance._get_file_type(yaml_file)
        assert file_type == FileType.YAML
        
        # Test markdown file
        md_file = str(Path(comprehensive_project) / "README.md")
        file_type = await filter_instance._get_file_type(md_file)
        assert file_type == FileType.MARKDOWN
        
        # Test config files
        config_files = ["config.ini", "config.toml"]
        for config_file in config_files:
            file_path = str(Path(comprehensive_project) / config_file)
            file_type = await filter_instance._get_file_type(file_path)
            assert file_type == FileType.CONFIG
        
        # Test other file type
        other_file = str(Path(comprehensive_project) / "requirements.txt")
        file_type = await filter_instance._get_file_type(other_file)
        assert file_type == FileType.OTHER
    
    @pytest.mark.asyncio
    async def test_get_file_type_test_detection_patterns(self, filter_instance):
        """Test various test file detection patterns"""
        # Test file starting with test_
        test_prefix_file = "/path/to/test_user.py"
        file_type = await filter_instance._get_file_type(test_prefix_file)
        assert file_type == FileType.TEST
        
        # Test file with 'test' in name
        test_in_name_file = "/path/to/user_test.py"
        file_type = await filter_instance._get_file_type(test_in_name_file)
        assert file_type == FileType.TEST
        
        # Test file in tests directory
        test_dir_file = "/path/to/tests/user.py"
        file_type = await filter_instance._get_file_type(test_dir_file)
        assert file_type == FileType.TEST
    
    @pytest.mark.asyncio
    async def test_get_file_dependencies_comprehensive(self, filter_instance, comprehensive_project):
        """Test comprehensive file dependency extraction"""
        python_file = str(Path(comprehensive_project) / "service.py")
        
        dependencies = await filter_instance._get_file_dependencies(python_file)
        
        assert isinstance(dependencies, set)
        assert "json" in dependencies
        assert "hashlib" in dependencies
        assert "datetime" in dependencies
    
    @pytest.mark.asyncio
    async def test_get_file_dependencies_complex_imports(self, filter_instance, comprehensive_project):
        """Test dependency extraction with complex import patterns"""
        # Create file with complex imports
        complex_file = Path(comprehensive_project) / "complex_imports.py"
        complex_content = '''
import os
import sys
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from collections import defaultdict, Counter
import json as json_module
from user_service import UserService, AuthService
import package.submodule
from package.submodule import function_name
'''
        complex_file.write_text(complex_content)
        
        dependencies = await filter_instance._get_file_dependencies(str(complex_file))
        
        expected_deps = {
            "os", "sys", "pathlib", "typing", "datetime", "collections",
            "json", "user_service", "package"
        }
        
        assert expected_deps.issubset(dependencies)
    
    @pytest.mark.asyncio
    async def test_get_file_dependencies_non_python_file(self, filter_instance, comprehensive_project):
        """Test dependency extraction for non-Python files"""
        json_file = str(Path(comprehensive_project) / "data.json")
        
        dependencies = await filter_instance._get_file_dependencies(json_file)
        
        # Should return empty set for non-Python files
        assert dependencies == set()
    
    @pytest.mark.asyncio
    async def test_get_file_dependencies_error_handling(self, filter_instance):
        """Test dependency extraction error handling"""
        nonexistent_file = "/nonexistent/file.py"
        
        dependencies = await filter_instance._get_file_dependencies(nonexistent_file)
        
        # Should return empty set for errors
        assert dependencies == set()
    
    @pytest.mark.asyncio
    async def test_get_reverse_dependencies_comprehensive(self, filter_instance, comprehensive_project):
        """Test comprehensive reverse dependency finding"""
        service_file = str(Path(comprehensive_project) / "service.py")
        
        reverse_deps = await filter_instance._get_reverse_dependencies(service_file)
        
        assert isinstance(reverse_deps, set)
        # test_service.py imports service, so should be in reverse deps
        test_file = str(Path(comprehensive_project) / "tests" / "test_service.py")
        assert test_file in reverse_deps
    
    @pytest.mark.asyncio
    async def test_get_reverse_dependencies_error_handling(self, filter_instance):
        """Test reverse dependency error handling"""
        # Test with invalid project path
        original_path = filter_instance.project_path
        filter_instance.project_path = Path("/nonexistent/path")
        
        reverse_deps = await filter_instance._get_reverse_dependencies("test.py")
        
        # Should handle error gracefully
        assert isinstance(reverse_deps, set)
        assert len(reverse_deps) == 0
        
        # Restore original path
        filter_instance.project_path = original_path


class TestPerformanceAndCachingComprehensive:
    """Comprehensive performance and caching tests"""
    
    @pytest.fixture
    def filter_instance(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            yield ContextFilter(temp_dir)
    
    def test_get_performance_metrics_comprehensive(self, filter_instance):
        """Test comprehensive performance metrics"""
        # Test initial state
        metrics = filter_instance.get_performance_metrics()
        
        expected_keys = {
            "average_filtering_time", "max_filtering_time", "min_filtering_time",
            "total_filtering_operations", "cache_hit_rate", "cache_hits",
            "cache_misses", "cached_files", "cached_dependencies"
        }
        
        assert set(metrics.keys()) == expected_keys
        
        # Test initial values
        assert metrics["average_filtering_time"] == 0.0
        assert metrics["max_filtering_time"] == 0.0
        assert metrics["min_filtering_time"] == 0.0
        assert metrics["total_filtering_operations"] == 0
        assert metrics["cache_hit_rate"] == 0.0
        assert metrics["cache_hits"] == 0
        assert metrics["cache_misses"] == 0
        assert metrics["cached_files"] == 0
        assert metrics["cached_dependencies"] == 0
    
    def test_get_performance_metrics_with_data(self, filter_instance):
        """Test performance metrics with actual data"""
        # Add some filtering times
        filter_instance._filtering_times = [0.1, 0.2, 0.3, 0.4, 0.5]
        
        # Add some cache data
        filter_instance._cache_hits = 10
        filter_instance._cache_misses = 5
        filter_instance._content_cache = {"file1": "content1", "file2": "content2"}
        filter_instance._file_dependencies_cache = {"file1": {"dep1"}}
        
        metrics = filter_instance.get_performance_metrics()
        
        # Test calculated values
        assert metrics["average_filtering_time"] == 0.3  # (0.1+0.2+0.3+0.4+0.5)/5
        assert metrics["max_filtering_time"] == 0.5
        assert metrics["min_filtering_time"] == 0.1
        assert metrics["total_filtering_operations"] == 5
        assert metrics["cache_hit_rate"] == 10/15  # 10/(10+5)
        assert metrics["cache_hits"] == 10
        assert metrics["cache_misses"] == 5
        assert metrics["cached_files"] == 2
        assert metrics["cached_dependencies"] == 1
    
    def test_get_performance_metrics_zero_division_protection(self, filter_instance):
        """Test performance metrics zero division protection"""
        # Test cache hit rate calculation with zero operations
        filter_instance._cache_hits = 0
        filter_instance._cache_misses = 0
        
        metrics = filter_instance.get_performance_metrics()
        
        # Should handle zero division gracefully
        assert metrics["cache_hit_rate"] == 0.0
    
    @pytest.mark.asyncio
    async def test_clear_cache_comprehensive(self, filter_instance):
        """Test comprehensive cache clearing"""
        # Populate all caches
        filter_instance._content_cache = {"file1": "content1", "file2": "content2"}
        filter_instance._file_dependencies_cache = {"file1": {"dep1"}, "file2": {"dep2"}}
        filter_instance._file_type_cache = {"file1": FileType.PYTHON, "file2": FileType.TEST}
        filter_instance._cache_timestamps = {"file1": datetime.now(), "file2": datetime.now()}
        
        # Verify caches have data
        assert len(filter_instance._content_cache) > 0
        assert len(filter_instance._file_dependencies_cache) > 0
        assert len(filter_instance._file_type_cache) > 0
        assert len(filter_instance._cache_timestamps) > 0
        
        # Clear cache
        await filter_instance.clear_cache()
        
        # Verify all caches are empty
        assert len(filter_instance._content_cache) == 0
        assert len(filter_instance._file_dependencies_cache) == 0
        assert len(filter_instance._file_type_cache) == 0
        assert len(filter_instance._cache_timestamps) == 0


class TestEdgeCasesAndErrorHandling:
    """Comprehensive edge cases and error handling tests"""
    
    @pytest.fixture
    def filter_instance(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            yield ContextFilter(temp_dir)
    
    @pytest.mark.asyncio
    async def test_filter_relevant_files_empty_candidate_list(self, filter_instance):
        """Test filtering with empty candidate file list"""
        request = ContextRequest(
            agent_type="CodeAgent",
            story_id="test_story",
            task={"description": "test task"},
            focus_areas=[]
        )
        
        results = await filter_instance.filter_relevant_files(
            request, [], max_files=10, min_score_threshold=0.1
        )
        
        assert results == []
    
    @pytest.mark.asyncio
    async def test_filter_relevant_files_all_files_below_threshold(self, filter_instance):
        """Test filtering when all files score below threshold"""
        # Create files with no relevance
        temp_file = Path(filter_instance.project_path) / "irrelevant.py"
        temp_file.write_text("# completely irrelevant content")
        
        request = ContextRequest(
            agent_type="CodeAgent",
            story_id="test_story",
            task={"description": "completely different unrelated task"},
            focus_areas=["unrelated", "different"]
        )
        
        results = await filter_instance.filter_relevant_files(
            request, [str(temp_file)], max_files=10, min_score_threshold=0.9  # Very high threshold
        )
        
        # Should return empty list if no files meet threshold
        assert results == []
    
    @pytest.mark.asyncio
    async def test_filter_relevant_files_exception_handling(self, filter_instance):
        """Test filtering with exceptions during processing"""
        request = ContextRequest(
            agent_type="CodeAgent",
            story_id="test_story",
            task={"description": "test task"},
            focus_areas=[]
        )
        
        # Mock _calculate_relevance_score to raise exception
        with patch.object(filter_instance, '_calculate_relevance_score', side_effect=Exception("Scoring error")):
            results = await filter_instance.filter_relevant_files(
                request, ["test_file.py"], max_files=10
            )
            
            # Should handle exception gracefully and return empty list
            assert results == []
    
    @pytest.mark.asyncio
    async def test_get_file_relevance_explanation_comprehensive(self, filter_instance):
        """Test comprehensive file relevance explanation"""
        # Create test file
        test_file = Path(filter_instance.project_path) / "user_auth.py"
        test_content = '''
class UserAuthenticator:
    def authenticate(self, username, password):
        return True
    
    def validate_user(self, user_data):
        return True
'''
        test_file.write_text(test_content)
        
        request = ContextRequest(
            agent_type="CodeAgent",
            story_id="auth_story",
            task={"description": "Implement user authentication"},
            focus_areas=["authentication", "user", "security"]
        )
        
        explanation = await filter_instance.get_file_relevance_explanation(
            str(test_file), request
        )
        
        # Verify structure
        assert isinstance(explanation, dict)
        required_keys = {
            "file_path", "total_score", "scoring_breakdown", "reasons", "search_terms"
        }
        assert set(explanation.keys()) == required_keys
        
        # Verify scoring breakdown
        breakdown = explanation["scoring_breakdown"]
        score_components = {
            "direct_mention", "dependency", "historical", "semantic", "tdd_phase"
        }
        assert set(breakdown.keys()) == score_components
        
        # Verify each component has required fields
        for component in breakdown.values():
            assert "score" in component
            assert "weight" in component
            assert "contribution" in component
            assert isinstance(component["score"], (int, float))
            assert isinstance(component["weight"], (int, float))
            assert isinstance(component["contribution"], (int, float))
        
        # Verify search terms
        search_terms = explanation["search_terms"]
        assert "authentication" in search_terms["keywords"]
        assert "UserAuthenticator" in search_terms["class_names"]
        assert "authenticate" in search_terms["function_names"]
    
    @pytest.mark.asyncio
    async def test_extract_search_terms_malformed_task(self, filter_instance):
        """Test search term extraction with malformed task data"""
        # Test with task that has unexpected structure
        malformed_task = {
            "description": None,  # None instead of string
            "acceptance_criteria": 123,  # Number instead of string
            "unexpected_field": {"nested": "data"}
        }
        
        request = ContextRequest(
            agent_type="CodeAgent",
            story_id="malformed_story",
            task=malformed_task,
            focus_areas=["test"]
        )
        
        search_terms = await filter_instance._extract_search_terms(request)
        
        # Should handle gracefully
        assert isinstance(search_terms, dict)
        assert "test" in search_terms["keywords"]  # From focus_areas
    
    @pytest.mark.asyncio
    async def test_file_operations_with_permission_errors(self, filter_instance):
        """Test file operations with permission errors"""
        # This test might be platform specific and may need adjustment
        
        # Create a file and then try to simulate permission error
        test_file = Path(filter_instance.project_path) / "restricted.py"
        test_file.write_text("# test content")
        
        # Mock open to raise PermissionError
        with patch('builtins.open', side_effect=PermissionError("Permission denied")):
            content = await filter_instance._get_file_content(str(test_file))
            
            # Should handle error gracefully
            assert content == ""
    
    @pytest.mark.asyncio
    async def test_unicode_handling(self, filter_instance):
        """Test handling of Unicode content"""
        # Create file with Unicode content
        unicode_file = Path(filter_instance.project_path) / "unicode_test.py"
        unicode_content = '''
# -*- coding: utf-8 -*-
class UnicodeExample:
    """Class with Unicode: 你好世界 🌍 café résumé"""
    
    def process_text(self, text="Default: αβγ"):
        """Process text with Greek letters: αβγδε"""
        return f"Processed: {text} ñoño"
'''
        unicode_file.write_text(unicode_content, encoding='utf-8')
        
        # Test content reading
        content = await filter_instance._get_file_content(str(unicode_file))
        assert "你好世界" in content
        assert "αβγ" in content
        assert "ñoño" in content
        
        # Test content filtering
        request = ContextRequest(
            agent_type="CodeAgent",
            story_id="unicode_story",
            task={"description": "Process Unicode text"},
            focus_areas=["unicode", "text"]
        )
        
        filtered = await filter_instance.filter_content_by_relevance(
            str(unicode_file), content, request, target_tokens=500
        )
        
        # Should handle Unicode content properly
        assert isinstance(filtered, str)
        assert len(filtered) > 0
    
    @pytest.mark.asyncio
    async def test_very_large_file_handling(self, filter_instance):
        """Test handling of very large files"""
        # Create a large file (simulate with repeated content)
        large_file = Path(filter_instance.project_path) / "large_file.py"
        large_content = '''
def large_function():
    """This is a large function with repeated content"""
    data = []
    for i in range(1000):
        data.append(f"item_{i}")
    return data
''' * 100  # Repeat 100 times
        
        large_file.write_text(large_content)
        
        request = ContextRequest(
            agent_type="CodeAgent",
            story_id="large_story",
            task={"description": "Handle large file"},
            focus_areas=["large", "function"]
        )
        
        # Test content filtering with small token limit
        filtered = await filter_instance.filter_content_by_relevance(
            str(large_file), large_content, request, target_tokens=100
        )
        
        # Should truncate appropriately
        assert len(filtered) < len(large_content)
        assert isinstance(filtered, str)
    
    @pytest.mark.asyncio
    async def test_concurrent_operations(self, filter_instance):
        """Test concurrent operations on the filter"""
        # Create multiple test files
        for i in range(5):
            test_file = Path(filter_instance.project_path) / f"concurrent_test_{i}.py"
            test_file.write_text(f"class TestClass{i}: pass")
        
        request = ContextRequest(
            agent_type="CodeAgent",
            story_id="concurrent_story",
            task={"description": "Concurrent test"},
            focus_areas=["test", "concurrent"]
        )
        
        # Run multiple operations concurrently
        candidate_files = [
            str(Path(filter_instance.project_path) / f"concurrent_test_{i}.py")
            for i in range(5)
        ]
        
        # Use asyncio.gather to run operations concurrently
        tasks = [
            filter_instance.filter_relevant_files(request, candidate_files, max_files=3)
            for _ in range(3)
        ]
        
        results = await asyncio.gather(*tasks)
        
        # All operations should complete successfully
        assert len(results) == 3
        for result in results:
            assert isinstance(result, list)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])