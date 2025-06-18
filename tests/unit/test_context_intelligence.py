"""
Test suite for Context Intelligence Layer

Comprehensive tests for ContextFilter, ContextCompressor, ContextIndex,
and their integration with ContextManager.
"""

import pytest
import asyncio
import tempfile
import shutil
from pathlib import Path
from datetime import datetime
from typing import Dict, List

# Import the components to test
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "lib"))

from context_filter import ContextFilter
from context_compressor import ContextCompressor
from context_index import ContextIndex
from context_manager import ContextManager
from context.models import (
    ContextRequest, FileType, CompressionLevel, 
    RelevanceScore, TokenBudget
)
from token_calculator import TokenCalculator
from agent_memory import FileBasedAgentMemory


class TestContextFilter:
    """Test ContextFilter functionality"""
    
    @pytest.fixture
    async def temp_project(self):
        """Create a temporary project directory with sample files"""
        temp_dir = Path(tempfile.mkdtemp())
        
        try:
            # Create project structure
            (temp_dir / "src").mkdir()
            (temp_dir / "tests").mkdir()
            (temp_dir / "docs").mkdir()
            
            # Create sample Python files
            (temp_dir / "src" / "main.py").write_text("""
import json
import logging

class UserManager:
    def __init__(self):
        self.users = {}
    
    def create_user(self, username, email):
        if username in self.users:
            raise ValueError("User already exists")
        self.users[username] = {"email": email}
        return True
    
    def get_user(self, username):
        return self.users.get(username)
""")
            
            (temp_dir / "src" / "auth.py").write_text("""
import hashlib
from main import UserManager

class AuthManager:
    def __init__(self, user_manager):
        self.user_manager = user_manager
        self.sessions = {}
    
    def authenticate(self, username, password):
        user = self.user_manager.get_user(username)
        if user and self._verify_password(password, user.get('password_hash')):
            return self._create_session(username)
        return None
    
    def _verify_password(self, password, hash_value):
        return hashlib.sha256(password.encode()).hexdigest() == hash_value
    
    def _create_session(self, username):
        session_id = hashlib.sha256(f"{username}{datetime.now()}".encode()).hexdigest()
        self.sessions[session_id] = username
        return session_id
""")
            
            (temp_dir / "tests" / "test_main.py").write_text("""
import pytest
from src.main import UserManager

def test_create_user():
    manager = UserManager()
    result = manager.create_user("john", "john@example.com")
    assert result is True

def test_get_user():
    manager = UserManager()
    manager.create_user("jane", "jane@example.com")
    user = manager.get_user("jane")
    assert user["email"] == "jane@example.com"

def test_duplicate_user():
    manager = UserManager()
    manager.create_user("bob", "bob@example.com")
    with pytest.raises(ValueError):
        manager.create_user("bob", "bob2@example.com")
""")
            
            (temp_dir / "docs" / "README.md").write_text("""
# User Management System

This system provides user authentication and management functionality.

## Features

- User creation and retrieval
- Password hashing and authentication
- Session management

## Usage

```python
from src.main import UserManager
from src.auth import AuthManager

user_manager = UserManager()
auth_manager = AuthManager(user_manager)
```
""")
            
            yield temp_dir
            
        finally:
            shutil.rmtree(temp_dir)
    
    @pytest.fixture
    async def context_filter(self, temp_project):
        """Create ContextFilter instance"""
        return ContextFilter(
            project_path=str(temp_project),
            token_calculator=TokenCalculator()
        )
    
    @pytest.mark.asyncio
    async def test_filter_relevant_files(self, context_filter, temp_project):
        """Test file filtering with relevance scoring"""
        # Create a context request for user management functionality
        request = ContextRequest(
            agent_type="CodeAgent",
            story_id="user-management",
            task={
                "description": "Implement user authentication with password validation",
                "acceptance_criteria": "Users should be able to authenticate with username and password"
            },
            max_tokens=50000
        )
        
        # Get all Python files as candidates
        candidate_files = list(str(f) for f in temp_project.rglob("*.py"))
        
        # Filter files
        relevance_scores = await context_filter.filter_relevant_files(
            request=request,
            candidate_files=candidate_files,
            max_files=10,
            min_score_threshold=0.05
        )
        
        # Verify results
        assert len(relevance_scores) > 0
        assert all(isinstance(score, RelevanceScore) for score in relevance_scores)
        
        # Verify scoring components are present
        for score in relevance_scores:
            assert 0.0 <= score.total_score <= 1.0
            assert 0.0 <= score.direct_mention <= 1.0
            assert 0.0 <= score.dependency_score <= 1.0
            assert isinstance(score.reasons, list)
        
        # Files with "auth" or "user" should score higher
        auth_files = [s for s in relevance_scores if "auth" in s.file_path.lower()]
        if auth_files:
            assert auth_files[0].total_score > 0.1
    
    @pytest.mark.asyncio
    async def test_content_filtering(self, context_filter, temp_project):
        """Test content filtering within files"""
        request = ContextRequest(
            agent_type="CodeAgent",
            task={"description": "Fix user authentication password verification"},
            max_tokens=50000
        )
        
        # Read a file
        auth_file = temp_project / "src" / "auth.py"
        content = auth_file.read_text()
        
        # Filter content
        filtered_content = await context_filter.filter_content_by_relevance(
            file_path=str(auth_file),
            content=content,
            request=request,
            target_tokens=1000
        )
        
        # Verify filtering
        assert len(filtered_content) <= len(content)
        assert "authenticate" in filtered_content  # Should preserve relevant methods
        assert "def " in filtered_content  # Should preserve function definitions
    
    @pytest.mark.asyncio
    async def test_relevance_explanation(self, context_filter, temp_project):
        """Test detailed relevance explanation"""
        request = ContextRequest(
            agent_type="CodeAgent",
            task={"description": "Implement user authentication system"},
            max_tokens=50000
        )
        
        auth_file = str(temp_project / "src" / "auth.py")
        
        explanation = await context_filter.get_file_relevance_explanation(
            file_path=auth_file,
            request=request
        )
        
        # Verify explanation structure
        assert "file_path" in explanation
        assert "total_score" in explanation
        assert "scoring_breakdown" in explanation
        assert "reasons" in explanation
        assert "search_terms" in explanation
        
        # Verify breakdown has all components
        breakdown = explanation["scoring_breakdown"]
        assert "direct_mention" in breakdown
        assert "dependency" in breakdown
        assert "historical" in breakdown
        assert "semantic" in breakdown
        assert "tdd_phase" in breakdown


class TestContextCompressor:
    """Test ContextCompressor functionality"""
    
    @pytest.fixture
    def context_compressor(self):
        """Create ContextCompressor instance"""
        return ContextCompressor(token_calculator=TokenCalculator())
    
    @pytest.mark.asyncio
    async def test_python_compression(self, context_compressor):
        """Test Python code compression"""
        python_code = '''
import json
import logging

class DataProcessor:
    """Process data from various sources."""
    
    def __init__(self, config):
        self.config = config
        self.logger = logging.getLogger(__name__)
    
    def process_file(self, filename):
        """Process a single file."""
        try:
            with open(filename, 'r') as f:
                data = json.load(f)
            
            # Complex processing logic here
            result = self._transform_data(data)
            self._validate_result(result)
            
            return result
        except Exception as e:
            self.logger.error(f"Error processing {filename}: {e}")
            raise
    
    def _transform_data(self, data):
        """Transform the data according to rules."""
        # Many lines of transformation logic
        transformed = {}
        for key, value in data.items():
            if isinstance(value, str):
                transformed[key] = value.upper()
            elif isinstance(value, (int, float)):
                transformed[key] = value * 2
            else:
                transformed[key] = str(value)
        return transformed
    
    def _validate_result(self, result):
        """Validate the processed result."""
        if not result:
            raise ValueError("Empty result")
        # Additional validation logic here
        pass
'''
        
        # Test different compression levels
        for level in [CompressionLevel.LOW, CompressionLevel.MODERATE, CompressionLevel.HIGH]:
            compressed, ratio = await context_compressor.compress_content(
                content=python_code,
                file_path="test.py",
                file_type=FileType.PYTHON,
                compression_level=level,
                preserve_structure=True
            )
            
            # Verify compression occurred
            assert len(compressed) <= len(python_code)
            assert 0.0 < ratio <= 1.0
            
            # Verify structure preservation
            if level != CompressionLevel.EXTREME:
                assert "class DataProcessor" in compressed
                assert "def " in compressed  # Function definitions should be preserved
    
    @pytest.mark.asyncio
    async def test_test_compression(self, context_compressor):
        """Test test file compression"""
        test_code = '''
import pytest
from mymodule import Calculator

class TestCalculator:
    def test_addition(self):
        calc = Calculator()
        result = calc.add(2, 3)
        assert result == 5
    
    def test_subtraction(self):
        calc = Calculator()
        result = calc.subtract(5, 3)
        assert result == 2
    
    def test_division_by_zero(self):
        calc = Calculator()
        with pytest.raises(ZeroDivisionError):
            calc.divide(10, 0)

def test_multiplication():
    calc = Calculator()
    assert calc.multiply(4, 5) == 20

@pytest.fixture
def calculator():
    return Calculator()
'''
        
        compressed, ratio = await context_compressor.compress_content(
            content=test_code,
            file_path="test_calc.py",
            file_type=FileType.TEST,
            compression_level=CompressionLevel.MODERATE,
            preserve_structure=True
        )
        
        # Verify test-specific preservation
        assert "assert" in compressed  # Assertions should be preserved
        assert "test_" in compressed   # Test function names should be preserved
        assert "@pytest.fixture" in compressed  # Fixtures should be preserved
    
    @pytest.mark.asyncio
    async def test_markdown_compression(self, context_compressor):
        """Test markdown content compression"""
        markdown_content = '''
# Project Documentation

This is a comprehensive documentation for our project.

## Overview

The project consists of multiple components that work together to provide
a complete solution for data processing and analysis.

### Key Features

- Data ingestion from multiple sources
- Real-time processing capabilities
- Advanced analytics and reporting
- User-friendly dashboard interface

## Architecture

The system follows a microservices architecture with the following components:

### Data Layer
Handles all data storage and retrieval operations.

### Processing Layer
Implements the core business logic and data transformations.

### Presentation Layer
Provides user interfaces and API endpoints.

## Installation

Follow these steps to install the system:

1. Clone the repository
2. Install dependencies
3. Configure the environment
4. Run the setup script

## Usage

Basic usage examples are provided below.
'''
        
        compressed, ratio = await context_compressor.compress_content(
            content=markdown_content,
            file_path="README.md",
            file_type=FileType.MARKDOWN,
            compression_level=CompressionLevel.MODERATE
        )
        
        # Verify structure preservation
        assert "# Project Documentation" in compressed  # Main heading preserved
        assert "##" in compressed  # Section headings preserved
        assert ratio < 1.0  # Some compression occurred
    
    @pytest.mark.asyncio
    async def test_compression_estimation(self, context_compressor):
        """Test compression potential estimation"""
        python_code = "def hello():\n    return 'Hello, world!'\n\nclass Test:\n    pass"
        
        analysis = await context_compressor.estimate_compression_potential(
            content=python_code,
            file_type=FileType.PYTHON,
            compression_level=CompressionLevel.MODERATE
        )
        
        # Verify analysis structure
        assert "original_tokens" in analysis
        assert "estimated_compression_ratio" in analysis
        assert "compressible_elements" in analysis
        assert "preservation_notes" in analysis
        assert "estimated_final_tokens" in analysis
        
        # Verify reasonable estimates
        assert analysis["original_tokens"] > 0
        assert 0.0 < analysis["estimated_compression_ratio"] <= 1.0


class TestContextIndex:
    """Test ContextIndex functionality"""
    
    @pytest.fixture
    async def temp_project(self):
        """Create a temporary project directory"""
        temp_dir = Path(tempfile.mkdtemp())
        
        try:
            # Create project structure with interdependent files
            (temp_dir / "src").mkdir()
            
            (temp_dir / "src" / "models.py").write_text("""
class User:
    def __init__(self, username, email):
        self.username = username
        self.email = email

class Post:
    def __init__(self, title, content, author):
        self.title = title
        self.content = content
        self.author = author
""")
            
            (temp_dir / "src" / "services.py").write_text("""
from models import User, Post

class UserService:
    def __init__(self):
        self.users = {}
    
    def create_user(self, username, email):
        user = User(username, email)
        self.users[username] = user
        return user

class PostService:
    def __init__(self, user_service):
        self.user_service = user_service
        self.posts = []
    
    def create_post(self, title, content, username):
        author = self.user_service.users.get(username)
        if author:
            post = Post(title, content, author)
            self.posts.append(post)
            return post
        return None
""")
            
            yield temp_dir
            
        finally:
            shutil.rmtree(temp_dir)
    
    @pytest.fixture
    async def context_index(self, temp_project):
        """Create and initialize ContextIndex"""
        index = ContextIndex(
            project_path=str(temp_project),
            token_calculator=TokenCalculator()
        )
        await index.build_index()
        return index
    
    @pytest.mark.asyncio
    async def test_index_building(self, context_index, temp_project):
        """Test index building functionality"""
        # Verify index was built
        assert len(context_index.file_nodes) > 0
        
        # Check that Python files were indexed
        python_files = [path for path in context_index.file_nodes.keys() if path.endswith('.py')]
        assert len(python_files) >= 2
        
        # Verify file structure was extracted
        for file_path, node in context_index.file_nodes.items():
            if file_path.endswith('models.py'):
                assert 'User' in node.classes
                assert 'Post' in node.classes
            elif file_path.endswith('services.py'):
                assert 'UserService' in node.classes
                assert 'PostService' in node.classes
                assert 'models' in node.imports
    
    @pytest.mark.asyncio
    async def test_dependency_analysis(self, context_index, temp_project):
        """Test dependency graph construction"""
        # Find the services file
        services_file = None
        for file_path in context_index.file_nodes.keys():
            if file_path.endswith('services.py'):
                services_file = file_path
                break
        
        assert services_file is not None
        
        # Get dependencies
        deps = await context_index.get_file_dependencies(
            file_path=services_file,
            include_reverse=True
        )
        
        # Verify dependency structure
        assert "dependency_count" in deps
        assert "reverse_dependency_count" in deps
        assert "direct_dependencies" in deps
        
        # Services should depend on models
        assert deps["dependency_count"] > 0
    
    @pytest.mark.asyncio
    async def test_search_functionality(self, context_index):
        """Test file search capabilities"""
        # Search for classes
        results = await context_index.search_files(
            query="User",
            search_type="classes",
            max_results=10
        )
        
        assert len(results) > 0
        
        # Verify search result structure
        for result in results:
            assert hasattr(result, 'file_path')
            assert hasattr(result, 'relevance_score')
            assert hasattr(result, 'match_type')
            assert 0.0 <= result.relevance_score <= 1.0
        
        # Search for functions
        function_results = await context_index.search_files(
            query="create",
            search_type="functions",
            max_results=10
        )
        
        # Should find create_user and create_post functions
        assert len(function_results) > 0
    
    @pytest.mark.asyncio
    async def test_file_relationships(self, context_index, temp_project):
        """Test file relationship analysis"""
        # Find models file
        models_file = None
        for file_path in context_index.file_nodes.keys():
            if file_path.endswith('models.py'):
                models_file = file_path
                break
        
        assert models_file is not None
        
        # Get related files
        related = await context_index.find_related_files(
            file_path=models_file,
            relation_types=["reverse_dependency", "similar_structure"],
            max_results=10
        )
        
        # Should find services.py as a reverse dependency
        assert len(related) > 0
        related_files = [rel[0] for rel in related]
        services_files = [f for f in related_files if f.endswith('services.py')]
        assert len(services_files) > 0
    
    @pytest.mark.asyncio
    async def test_project_statistics(self, context_index):
        """Test project statistics generation"""
        stats = await context_index.get_project_statistics()
        
        # Verify statistics structure
        assert "total_files" in stats
        assert "file_types" in stats
        assert "total_dependencies" in stats
        assert "most_dependent_files" in stats
        assert "most_depended_upon_files" in stats
        
        # Verify reasonable values
        assert stats["total_files"] > 0
        assert isinstance(stats["file_types"], dict)


class TestContextManagerIntegration:
    """Test integration of intelligence layer with ContextManager"""
    
    @pytest.fixture
    async def temp_project(self):
        """Create a temporary project with comprehensive structure"""
        temp_dir = Path(tempfile.mkdtemp())
        
        try:
            # Create project structure
            (temp_dir / "src").mkdir()
            (temp_dir / "tests").mkdir()
            (temp_dir / ".orch-state").mkdir()
            
            # Create sample files for testing
            (temp_dir / "src" / "calculator.py").write_text("""
class Calculator:
    def add(self, a, b):
        return a + b
    
    def subtract(self, a, b):
        return a - b
    
    def multiply(self, a, b):
        return a * b
    
    def divide(self, a, b):
        if b == 0:
            raise ZeroDivisionError("Cannot divide by zero")
        return a / b
""")
            
            (temp_dir / "tests" / "test_calculator.py").write_text("""
import pytest
from src.calculator import Calculator

def test_addition():
    calc = Calculator()
    assert calc.add(2, 3) == 5

def test_division_by_zero():
    calc = Calculator()
    with pytest.raises(ZeroDivisionError):
        calc.divide(10, 0)
""")
            
            yield temp_dir
            
        finally:
            shutil.rmtree(temp_dir)
    
    @pytest.fixture
    async def context_manager(self, temp_project):
        """Create ContextManager with intelligence enabled"""
        manager = ContextManager(
            project_path=str(temp_project),
            enable_intelligence=True,
            max_tokens=50000
        )
        
        # Build the context index
        await manager.build_context_index()
        
        return manager
    
    @pytest.mark.asyncio
    async def test_intelligent_context_preparation(self, context_manager):
        """Test context preparation with intelligence layer"""
        # Create a context request
        context = await context_manager.prepare_context(
            agent_type="CodeAgent",
            task={
                "description": "Fix calculator division method to handle edge cases",
                "current_state": "RED"
            },
            story_id="calculator-fixes",
            max_tokens=10000
        )
        
        # Verify context was prepared
        assert context is not None
        assert context.agent_type == "CodeAgent"
        assert context.story_id == "calculator-fixes"
        
        # Verify content was included
        assert len(context.file_contents) > 0
        assert context.core_context != ""
        
        # Verify token budget was respected
        assert context.token_usage.total_used <= 10000
        
        # Verify relevance scores were calculated (if intelligence is enabled)
        if context.relevance_scores:
            assert all(isinstance(score, RelevanceScore) for score in context.relevance_scores)
    
    @pytest.mark.asyncio
    async def test_codebase_search(self, context_manager):
        """Test codebase search functionality"""
        results = await context_manager.search_codebase(
            query="Calculator",
            search_type="classes",
            max_results=10
        )
        
        # Should find the Calculator class
        assert len(results) > 0
        
        # Verify result structure
        for result in results:
            assert "file_path" in result
            assert "relevance_score" in result
            assert "match_type" in result
            assert "matches" in result
            assert "context" in result
    
    @pytest.mark.asyncio
    async def test_file_dependencies(self, context_manager, temp_project):
        """Test file dependency analysis"""
        calc_file = str(temp_project / "src" / "calculator.py")
        
        deps = await context_manager.get_file_dependencies(
            file_path=calc_file,
            depth=1,
            include_reverse=True
        )
        
        # Verify dependency information
        assert "file" in deps
        assert "dependency_count" in deps
        assert "reverse_dependency_count" in deps
    
    @pytest.mark.asyncio
    async def test_compression_estimation(self, context_manager):
        """Test compression potential estimation"""
        python_code = """
def complex_function():
    # This is a complex function with many lines
    result = []
    for i in range(100):
        if i % 2 == 0:
            result.append(i * 2)
        else:
            result.append(i * 3)
    return result
"""
        
        analysis = await context_manager.estimate_compression_potential(
            content=python_code,
            file_type=FileType.PYTHON,
            compression_level=CompressionLevel.MODERATE
        )
        
        # Verify analysis was performed
        assert "original_tokens" in analysis
        assert "estimated_compression_ratio" in analysis
        assert analysis["original_tokens"] > 0
    
    @pytest.mark.asyncio
    async def test_performance_metrics(self, context_manager):
        """Test performance metrics collection"""
        # Prepare some context to generate metrics
        await context_manager.prepare_context(
            agent_type="CodeAgent",
            task={"description": "Test task"},
            story_id="test",
            max_tokens=5000
        )
        
        # Get metrics
        metrics = context_manager.get_performance_metrics()
        
        # Verify comprehensive metrics
        assert "context_manager" in metrics
        assert "token_calculator" in metrics
        
        # Verify context manager metrics
        cm_metrics = metrics["context_manager"]
        assert "total_requests" in cm_metrics
        assert "cache_hit_rate" in cm_metrics
        assert "average_preparation_time" in cm_metrics
        
        # Verify metrics have reasonable values
        assert cm_metrics["total_requests"] > 0
        assert 0.0 <= cm_metrics["cache_hit_rate"] <= 1.0


# Run tests if executed directly
if __name__ == "__main__":
    pytest.main([__file__, "-v"])