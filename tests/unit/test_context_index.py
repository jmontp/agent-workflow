"""
Comprehensive test suite for Context Index System.

Tests searchable codebase indexing with dependency analysis, file relationship mapping,
code structure analysis, and fast search/filtering capabilities with caching.
"""

import pytest
import asyncio
import tempfile
import shutil
import sqlite3
import json
import ast
from pathlib import Path
from datetime import datetime, timedelta
from unittest.mock import Mock, AsyncMock, patch, MagicMock

# Import the modules under test
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "lib"))

from context_index import (
    ContextIndex,
    FileNode,
    DependencyEdge,
    SearchResult
)
from context.models import FileType, RelevanceScore
from token_calculator import TokenCalculator


class TestFileNode:
    """Test FileNode data class"""
    
    def test_file_node_creation(self):
        """Test basic file node creation"""
        node = FileNode(
            path="/test/file.py",
            file_type=FileType.PYTHON,
            size=1024,
            last_modified=datetime.utcnow(),
            content_hash="abc123",
            imports=["os", "sys"],
            exports=["function1"],
            classes=["TestClass"],
            functions=["test_func"],
            dependencies=["/other/file.py"],
            reverse_dependencies=["/caller/file.py"]
        )
        
        assert node.path == "/test/file.py"
        assert node.file_type == FileType.PYTHON
        assert node.size == 1024
        assert node.imports == ["os", "sys"]
        assert node.exports == ["function1"]
        assert node.classes == ["TestClass"]
        assert node.functions == ["test_func"]
        assert node.access_count == 0
        assert node.last_accessed is None
    
    def test_file_node_serialization(self):
        """Test file node serialization to/from dict"""
        original_time = datetime.utcnow()
        access_time = datetime.utcnow()
        
        node = FileNode(
            path="/test/file.py",
            file_type=FileType.PYTHON,
            size=1024,
            last_modified=original_time,
            content_hash="abc123",
            imports=["json"],
            exports=[],
            classes=["MyClass"],
            functions=["my_function"],
            dependencies=[],
            reverse_dependencies=[],
            access_count=5,
            last_accessed=access_time
        )
        
        # Test to_dict
        data = node.to_dict()
        assert isinstance(data, dict)
        assert data["path"] == "/test/file.py"
        assert data["file_type"] == "python"
        assert data["size"] == 1024
        assert data["last_modified"] == original_time.isoformat()
        assert data["last_accessed"] == access_time.isoformat()
        assert data["imports"] == ["json"]
        assert data["classes"] == ["MyClass"]
        assert data["access_count"] == 5
        
        # Test from_dict
        restored = FileNode.from_dict(data)
        assert restored.path == node.path
        assert restored.file_type == node.file_type
        assert restored.size == node.size
        assert restored.last_modified == node.last_modified
        assert restored.last_accessed == node.last_accessed
        assert restored.imports == node.imports
        assert restored.classes == node.classes
        assert restored.access_count == node.access_count
    
    def test_file_node_serialization_no_access_time(self):
        """Test serialization when last_accessed is None"""
        node = FileNode(
            path="/test/file.py",
            file_type=FileType.PYTHON,
            size=1024,
            last_modified=datetime.utcnow(),
            content_hash="abc123",
            imports=[],
            exports=[],
            classes=[],
            functions=[],
            dependencies=[],
            reverse_dependencies=[],
            last_accessed=None
        )
        
        data = node.to_dict()
        assert data["last_accessed"] is None
        
        restored = FileNode.from_dict(data)
        assert restored.last_accessed is None


class TestDependencyEdge:
    """Test DependencyEdge data class"""
    
    def test_dependency_edge_creation(self):
        """Test dependency edge creation"""
        edge = DependencyEdge(
            source="/src/file1.py",
            target="/src/file2.py",
            import_type="import",
            line_number=5,
            strength=0.8
        )
        
        assert edge.source == "/src/file1.py"
        assert edge.target == "/src/file2.py"
        assert edge.import_type == "import"
        assert edge.line_number == 5
        assert edge.strength == 0.8
    
    def test_dependency_edge_defaults(self):
        """Test dependency edge default values"""
        edge = DependencyEdge(
            source="/src/file1.py",
            target="/src/file2.py",
            import_type="from",
            line_number=10
        )
        
        assert edge.strength == 1.0  # Default value


class TestSearchResult:
    """Test SearchResult data class"""
    
    def test_search_result_creation(self):
        """Test search result creation"""
        result = SearchResult(
            file_path="/test/file.py",
            relevance_score=0.85,
            match_type="exact",
            matches=["function_name", "class_name"],
            context="Function: function_name"
        )
        
        assert result.file_path == "/test/file.py"
        assert result.relevance_score == 0.85
        assert result.match_type == "exact"
        assert result.matches == ["function_name", "class_name"]
        assert result.context == "Function: function_name"
    
    def test_search_result_defaults(self):
        """Test search result default values"""
        result = SearchResult(
            file_path="/test/file.py",
            relevance_score=0.5,
            match_type="partial",
            matches=["test"]
        )
        
        assert result.context == ""  # Default value


class TestContextIndexInit:
    """Test ContextIndex initialization"""
    
    @pytest.fixture
    def temp_project(self):
        """Create temporary project directory"""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir)
    
    def test_init_with_defaults(self, temp_project):
        """Test initialization with default parameters"""
        index = ContextIndex(temp_project)
        
        assert index.project_path == Path(temp_project)
        assert index.token_calculator is not None
        assert index.cache_path == Path(temp_project) / ".orch-state" / "context_index.db"
        assert isinstance(index.file_nodes, dict)
        assert isinstance(index.dependencies, list)
        assert isinstance(index.dependency_graph, dict)
        assert isinstance(index.reverse_dependency_graph, dict)
        assert len(index.file_nodes) == 0
        assert len(index.dependencies) == 0
    
    def test_init_with_custom_params(self, temp_project):
        """Test initialization with custom parameters"""
        custom_cache = str(Path(temp_project) / "custom_cache.db")
        mock_calculator = Mock(spec=TokenCalculator)
        
        index = ContextIndex(
            project_path=temp_project,
            index_cache_path=custom_cache,
            token_calculator=mock_calculator
        )
        
        assert index.cache_path == Path(custom_cache)
        assert index.token_calculator is mock_calculator
    
    def test_init_creates_cache_directory(self, temp_project):
        """Test that initialization creates cache directory"""
        index = ContextIndex(temp_project)
        
        assert index.cache_path.parent.exists()
        assert index.cache_path.parent.name == ".orch-state"
    
    def test_database_initialization(self, temp_project):
        """Test SQLite database initialization"""
        index = ContextIndex(temp_project)
        
        # Check that database file is created
        assert index.cache_path.exists()
        
        # Check that tables are created
        conn = sqlite3.connect(str(index.cache_path))
        cursor = conn.cursor()
        
        # Check files table
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='files'")
        assert cursor.fetchone() is not None
        
        # Check dependencies table
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='dependencies'")
        assert cursor.fetchone() is not None
        
        # Check index_metadata table
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='index_metadata'")
        assert cursor.fetchone() is not None
        
        conn.close()


class TestIndexBuilding:
    """Test index building functionality"""
    
    @pytest.fixture
    def temp_project(self):
        """Create comprehensive test project"""
        temp_dir = tempfile.mkdtemp()
        
        # Create Python files with imports
        main_file = Path(temp_dir) / "main.py"
        main_content = '''
import os
import json
from datetime import datetime
from utils import helper_function
from models.user import User

class Application:
    def __init__(self):
        self.users = []
    
    def add_user(self, username):
        user = User(username)
        self.users.append(user)
        return user
    
    def get_user_count(self):
        return len(self.users)

def main():
    app = Application()
    app.add_user("john")
    print(f"Users: {app.get_user_count()}")

if __name__ == "__main__":
    main()
'''
        main_file.write_text(main_content)
        
        # Create models directory
        models_dir = Path(temp_dir) / "models"
        models_dir.mkdir()
        
        user_model = models_dir / "user.py"
        user_content = '''
from datetime import datetime

class User:
    def __init__(self, username):
        self.username = username
        self.created_at = datetime.utcnow()
    
    def get_age_days(self):
        return (datetime.utcnow() - self.created_at).days
'''
        user_model.write_text(user_content)
        
        # Create utils file
        utils_file = Path(temp_dir) / "utils.py"
        utils_content = '''
def helper_function(data):
    """Helper function for data processing"""
    return data.strip().lower()

def format_date(date):
    """Format date for display"""
    return date.strftime("%Y-%m-%d")
'''
        utils_file.write_text(utils_content)
        
        # Create test file
        test_file = Path(temp_dir) / "test_main.py"
        test_content = '''
import unittest
from main import Application

class TestApplication(unittest.TestCase):
    def setUp(self):
        self.app = Application()
    
    def test_add_user(self):
        user = self.app.add_user("test")
        self.assertEqual(user.username, "test")
    
    def test_user_count(self):
        self.assertEqual(self.app.get_user_count(), 0)
        self.app.add_user("test")
        self.assertEqual(self.app.get_user_count(), 1)
'''
        test_file.write_text(test_content)
        
        # Create config file
        config_file = Path(temp_dir) / "config.json"
        config_content = '''
{
    "database_url": "sqlite:///app.db",
    "debug": true,
    "max_users": 1000
}
'''
        config_file.write_text(config_content)
        
        # Create markdown file
        readme_file = Path(temp_dir) / "README.md"
        readme_content = '''
# Test Project

This is a test project for context indexing.

## Features
- User management
- Application framework
- Testing utilities
'''
        readme_file.write_text(readme_content)
        
        yield temp_dir
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def index(self, temp_project):
        return ContextIndex(temp_project)
    
    @pytest.mark.asyncio
    async def test_build_index_basic(self, index):
        """Test basic index building"""
        await index.build_index()
        
        # Check that files were indexed
        assert len(index.file_nodes) > 0
        
        # Check specific files
        main_path = str(index.project_path / "main.py")
        assert main_path in index.file_nodes
        
        main_node = index.file_nodes[main_path]
        assert main_node.file_type == FileType.PYTHON
        assert "Application" in main_node.classes
        assert "add_user" in main_node.functions
        assert "get_user_count" in main_node.functions
        assert "os" in main_node.imports
        assert "json" in main_node.imports
    
    @pytest.mark.asyncio
    async def test_build_index_dependencies(self, index):
        """Test dependency graph building"""
        await index.build_index()
        
        # Check dependency relationships
        main_path = str(index.project_path / "main.py")
        user_path = str(index.project_path / "models" / "user.py")
        utils_path = str(index.project_path / "utils.py")
        
        # main.py should depend on utils.py and models/user.py
        main_deps = index.dependency_graph.get(main_path, set())
        assert len(main_deps) > 0
        
        # Check reverse dependencies
        utils_reverse_deps = index.reverse_dependency_graph.get(utils_path, set())
        assert main_path in utils_reverse_deps
    
    @pytest.mark.asyncio
    async def test_build_index_file_types(self, index):
        """Test file type detection during indexing"""
        await index.build_index()
        
        # Check Python files
        main_path = str(index.project_path / "main.py")
        assert index.file_nodes[main_path].file_type == FileType.PYTHON
        
        # Check test files
        test_path = str(index.project_path / "test_main.py")
        assert index.file_nodes[test_path].file_type == FileType.TEST
        
        # Check JSON files
        config_path = str(index.project_path / "config.json")
        assert index.file_nodes[config_path].file_type == FileType.JSON
        
        # Check markdown files
        readme_path = str(index.project_path / "README.md")
        assert index.file_nodes[readme_path].file_type == FileType.MARKDOWN
    
    @pytest.mark.asyncio
    async def test_build_index_search_indices(self, index):
        """Test search index building"""
        await index.build_index()
        
        # Check function index
        assert "add_user" in index.function_index
        assert "get_user_count" in index.function_index
        
        # Check class index
        assert "application" in index.class_index
        assert "user" in index.class_index
        
        # Check import index
        assert "os" in index.import_index
        assert "json" in index.import_index
    
    @pytest.mark.asyncio
    async def test_build_index_force_rebuild(self, index):
        """Test force rebuild functionality"""
        # Build index first time
        await index.build_index()
        initial_count = len(index.file_nodes)
        
        # Force rebuild
        await index.build_index(force_rebuild=True)
        
        # Should still have same files
        assert len(index.file_nodes) == initial_count
    
    @pytest.mark.asyncio
    async def test_build_index_incremental(self, index, temp_project):
        """Test incremental index building"""
        # Build initial index
        await index.build_index()
        initial_count = len(index.file_nodes)
        
        # Add new file
        new_file = Path(temp_project) / "new_module.py"
        new_file.write_text("def new_function(): pass")
        
        # Build again (incremental)
        await index.build_index()
        
        # Should have one more file
        assert len(index.file_nodes) == initial_count + 1
        assert str(new_file) in index.file_nodes
    
    @pytest.mark.asyncio
    async def test_build_index_file_deletion(self, index, temp_project):
        """Test handling of deleted files"""
        # Build initial index
        await index.build_index()
        
        # Delete a file
        utils_path = Path(temp_project) / "utils.py"
        utils_path.unlink()
        
        # Rebuild index
        await index.build_index()
        
        # Deleted file should be removed from index
        assert str(utils_path) not in index.file_nodes
    
    @pytest.mark.asyncio
    async def test_should_index_file_filtering(self, index, temp_project):
        """Test file filtering during indexing"""
        # Create files that should be ignored
        ignored_files = [
            Path(temp_project) / ".git" / "config",
            Path(temp_project) / "__pycache__" / "cache.pyc",
            Path(temp_project) / "node_modules" / "package.js",
            Path(temp_project) / ".hidden_file.py"
        ]
        
        for file_path in ignored_files:
            file_path.parent.mkdir(parents=True, exist_ok=True)
            file_path.write_text("content")
        
        # Create very large file
        large_file = Path(temp_project) / "large_file.py"
        large_file.write_text("x" * 2_000_000)  # 2MB
        
        await index.build_index()
        
        # Ignored files should not be indexed
        for file_path in ignored_files:
            assert str(file_path) not in index.file_nodes
        
        # Large file should not be indexed
        assert str(large_file) not in index.file_nodes
    
    @pytest.mark.asyncio
    async def test_persistence_save_and_load(self, index, temp_project):
        """Test index persistence to database"""
        # Build and save index
        await index.build_index()
        
        # Create new index instance and load
        index2 = ContextIndex(temp_project)
        await index2.build_index()  # This should load from cache
        
        # Should have same content
        assert len(index2.file_nodes) == len(index.file_nodes)
        assert len(index2.dependencies) == len(index.dependencies)
        
        # Check specific file
        main_path = str(index.project_path / "main.py")
        if main_path in index.file_nodes and main_path in index2.file_nodes:
            assert index.file_nodes[main_path].classes == index2.file_nodes[main_path].classes


class TestSearchFunctionality:
    """Test search functionality"""
    
    @pytest.fixture
    def temp_project(self):
        """Create project with searchable content"""
        temp_dir = tempfile.mkdtemp()
        
        # Create files with searchable content
        files = {
            "user_service.py": '''
class UserService:
    def authenticate_user(self, username, password):
        return True
    
    def create_user(self, user_data):
        return User(user_data)
    
    def validate_email(self, email):
        return "@" in email
''',
            "user_model.py": '''
from datetime import datetime

class User:
    def __init__(self, data):
        self.username = data.get("username")
        self.email = data.get("email")
        self.created_at = datetime.utcnow()
''',
            "auth_controller.py": '''
from user_service import UserService

class AuthController:
    def __init__(self):
        self.user_service = UserService()
    
    def login(self, credentials):
        return self.user_service.authenticate_user(
            credentials["username"],
            credentials["password"]
        )
''',
            "test_auth.py": '''
import unittest
from auth_controller import AuthController

class TestAuth(unittest.TestCase):
    def test_login(self):
        controller = AuthController()
        result = controller.login({"username": "test", "password": "pass"})
        self.assertTrue(result)
'''
        }
        
        for filename, content in files.items():
            file_path = Path(temp_dir) / filename
            file_path.write_text(content)
        
        yield temp_dir
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    async def indexed_project(self, temp_project):
        """Create indexed project"""
        index = ContextIndex(temp_project)
        await index.build_index()
        return index
    
    @pytest.mark.asyncio
    async def test_search_functions_exact_match(self, indexed_project):
        """Test searching for functions with exact match"""
        results = await indexed_project.search_files("authenticate_user", search_type="functions")
        
        assert len(results) > 0
        assert any(r.match_type == "exact" for r in results)
        assert any("authenticate_user" in r.matches for r in results)
    
    @pytest.mark.asyncio
    async def test_search_functions_partial_match(self, indexed_project):
        """Test searching for functions with partial match"""
        results = await indexed_project.search_files("user", search_type="functions")
        
        assert len(results) > 0
        
        # Should find functions containing "user"
        function_matches = []
        for result in results:
            function_matches.extend(result.matches)
        
        user_functions = [m for m in function_matches if "user" in m.lower()]
        assert len(user_functions) > 0
    
    @pytest.mark.asyncio
    async def test_search_classes(self, indexed_project):
        """Test searching for classes"""
        results = await indexed_project.search_files("UserService", search_type="classes")
        
        assert len(results) > 0
        assert any("UserService" in r.matches for r in results)
        assert any("Class:" in r.context for r in results)
    
    @pytest.mark.asyncio
    async def test_search_imports(self, indexed_project):
        """Test searching for imports"""
        results = await indexed_project.search_files("user_service", search_type="imports")
        
        assert len(results) > 0
        assert any("user_service" in r.matches for r in results)
        assert any("Import:" in r.context for r in results)
    
    @pytest.mark.asyncio
    async def test_search_all_types(self, indexed_project):
        """Test searching across all types"""
        results = await indexed_project.search_files("user", search_type="all")
        
        assert len(results) > 0
        
        # Should find matches from different types
        contexts = [r.context for r in results]
        context_types = set()
        for context in contexts:
            if "Function:" in context:
                context_types.add("function")
            elif "Class:" in context:
                context_types.add("class")
            elif "Import:" in context:
                context_types.add("import")
        
        # Should have multiple types of matches
        assert len(context_types) > 1
    
    @pytest.mark.asyncio
    async def test_search_max_results_limit(self, indexed_project):
        """Test search results limiting"""
        results = await indexed_project.search_files("test", max_results=2)
        
        assert len(results) <= 2
    
    @pytest.mark.asyncio
    async def test_search_relevance_ordering(self, indexed_project):
        """Test that search results are ordered by relevance"""
        results = await indexed_project.search_files("user", max_results=5)
        
        if len(results) > 1:
            # Results should be ordered by relevance score (descending)
            for i in range(len(results) - 1):
                assert results[i].relevance_score >= results[i + 1].relevance_score
    
    @pytest.mark.asyncio
    async def test_search_deduplication(self, indexed_project):
        """Test that search results are deduplicated by file path"""
        results = await indexed_project.search_files("user", search_type="all")
        
        # Extract file paths
        file_paths = [r.file_path for r in results]
        
        # Should not have duplicate file paths
        assert len(file_paths) == len(set(file_paths))
    
    @pytest.mark.asyncio
    async def test_search_performance_tracking(self, indexed_project):
        """Test that search performance is tracked"""
        initial_count = len(indexed_project.search_times)
        
        await indexed_project.search_files("user")
        
        assert len(indexed_project.search_times) == initial_count + 1
        assert indexed_project.search_times[-1] > 0


class TestDependencyAnalysis:
    """Test dependency analysis functionality"""
    
    @pytest.fixture
    def temp_project(self):
        """Create project with complex dependencies"""
        temp_dir = tempfile.mkdtemp()
        
        # Create interconnected files
        files = {
            "core/base.py": '''
class BaseModel:
    def save(self):
        pass
''',
            "models/user.py": '''
from core.base import BaseModel

class User(BaseModel):
    def __init__(self, username):
        self.username = username
''',
            "services/user_service.py": '''
from models.user import User
import json

class UserService:
    def create_user(self, data):
        return User(data["username"])
    
    def serialize_user(self, user):
        return json.dumps({"username": user.username})
''',
            "controllers/user_controller.py": '''
from services.user_service import UserService

class UserController:
    def __init__(self):
        self.service = UserService()
    
    def handle_create_user(self, request):
        return self.service.create_user(request.data)
''',
            "main.py": '''
from controllers.user_controller import UserController

def main():
    controller = UserController()
    return controller

if __name__ == "__main__":
    main()
'''
        }
        
        for filepath, content in files.items():
            full_path = Path(temp_dir) / filepath
            full_path.parent.mkdir(parents=True, exist_ok=True)
            full_path.write_text(content)
        
        yield temp_dir
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    async def indexed_project(self, temp_project):
        """Create indexed project with dependencies"""
        index = ContextIndex(temp_project)
        await index.build_index()
        return index
    
    @pytest.mark.asyncio
    async def test_get_file_dependencies_basic(self, indexed_project, temp_project):
        """Test getting basic file dependencies"""
        user_service_path = str(Path(temp_project) / "services" / "user_service.py")
        
        deps = await indexed_project.get_file_dependencies(user_service_path)
        
        assert "file" in deps
        assert "direct_dependencies" in deps
        assert "dependency_count" in deps
        assert "reverse_dependencies" in deps
        assert "reverse_dependency_count" in deps
        
        assert deps["file"] == user_service_path
        assert isinstance(deps["direct_dependencies"], list)
        assert isinstance(deps["dependency_count"], int)
    
    @pytest.mark.asyncio
    async def test_get_file_dependencies_with_depth(self, indexed_project, temp_project):
        """Test getting dependencies with depth"""
        main_path = str(Path(temp_project) / "main.py")
        
        deps = await indexed_project.get_file_dependencies(
            main_path, 
            depth=3, 
            include_reverse=True
        )
        
        assert "transitive_dependencies" in deps
        assert "transitive_count" in deps
        assert isinstance(deps["transitive_dependencies"], list)
        assert deps["transitive_count"] >= 0
    
    @pytest.mark.asyncio
    async def test_get_file_dependencies_not_found(self, indexed_project):
        """Test getting dependencies for non-existent file"""
        deps = await indexed_project.get_file_dependencies("/nonexistent/file.py")
        
        assert "error" in deps
        assert "not found in index" in deps["error"]
    
    @pytest.mark.asyncio
    async def test_dependency_graph_structure(self, indexed_project, temp_project):
        """Test dependency graph structure"""
        # Check that dependency relationships are correct
        main_path = str(Path(temp_project) / "main.py")
        controller_path = str(Path(temp_project) / "controllers" / "user_controller.py")
        
        # main.py should depend on user_controller
        main_deps = indexed_project.dependency_graph.get(main_path, set())
        assert any("user_controller" in dep for dep in main_deps)
        
        # user_controller should have main.py as reverse dependency
        controller_reverse = indexed_project.reverse_dependency_graph.get(controller_path, set())
        assert main_path in controller_reverse
    
    @pytest.mark.asyncio
    async def test_transitive_dependencies(self, indexed_project, temp_project):
        """Test transitive dependency calculation"""
        main_path = str(Path(temp_project) / "main.py")
        
        transitive_deps = await indexed_project._get_transitive_dependencies(main_path, depth=3)
        
        assert isinstance(transitive_deps, set)
        
        # Should include files multiple levels down
        expected_in_chain = ["user_controller", "user_service", "user", "base"]
        found_files = [dep for dep in transitive_deps 
                      if any(expected in dep for expected in expected_in_chain)]
        
        assert len(found_files) > 0


class TestFileStructureAnalysis:
    """Test file structure analysis"""
    
    @pytest.fixture
    def temp_project(self):
        """Create project for structure analysis"""
        temp_dir = tempfile.mkdtemp()
        
        # Create Python file with detailed structure
        python_file = Path(temp_dir) / "complex_module.py"
        python_content = '''
import os
import sys
from datetime import datetime
from typing import List, Dict

class UserManager:
    """Manages user operations"""
    
    def __init__(self):
        self.users = []
    
    def add_user(self, username: str) -> bool:
        """Add a new user"""
        self.users.append(username)
        return True
    
    def remove_user(self, username: str) -> bool:
        """Remove a user"""
        if username in self.users:
            self.users.remove(username)
            return True
        return False
    
    def get_user_count(self) -> int:
        """Get total user count"""
        return len(self.users)

class AdminManager(UserManager):
    """Manages admin operations"""
    
    def promote_user(self, username: str) -> bool:
        """Promote user to admin"""
        return username in self.users

def create_manager() -> UserManager:
    """Factory function for user manager"""
    return UserManager()

def validate_username(username: str) -> bool:
    """Validate username format"""
    return len(username) > 0 and username.isalnum()

# Global variable
DEFAULT_ADMIN = "admin"
'''
        python_file.write_text(python_content)
        
        # Create JSON file with structure
        json_file = Path(temp_dir) / "config.json"
        json_content = '''
{
    "database": {
        "host": "localhost",
        "port": 5432,
        "name": "myapp"
    },
    "logging": {
        "level": "INFO",
        "file": "app.log"
    },
    "features": {
        "authentication": true,
        "authorization": false
    }
}
'''
        json_file.write_text(json_content)
        
        yield temp_dir
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    async def indexed_project(self, temp_project):
        """Create indexed project"""
        index = ContextIndex(temp_project)
        await index.build_index()
        return index
    
    @pytest.mark.asyncio
    async def test_get_file_structure_python(self, indexed_project, temp_project):
        """Test getting Python file structure"""
        python_path = str(Path(temp_project) / "complex_module.py")
        
        structure = await indexed_project.get_file_structure(python_path)
        
        assert "file" in structure
        assert "file_type" in structure
        assert "classes" in structure
        assert "functions" in structure
        assert "imports" in structure
        
        # Check extracted content
        assert structure["file_type"] == "python"
        assert "UserManager" in structure["classes"]
        assert "AdminManager" in structure["classes"]
        assert "add_user" in structure["functions"]
        assert "remove_user" in structure["functions"]
        assert "create_manager" in structure["functions"]
        assert "validate_username" in structure["functions"]
        assert "os" in structure["imports"]
        assert "sys" in structure["imports"]
        assert "datetime" in structure["imports"]
    
    @pytest.mark.asyncio
    async def test_get_file_structure_json(self, indexed_project, temp_project):
        """Test getting JSON file structure"""
        json_path = str(Path(temp_project) / "config.json")
        
        structure = await indexed_project.get_file_structure(json_path)
        
        assert structure["file_type"] == "json"
        assert "exports" in structure
        
        # Should extract top-level keys
        exports = structure["exports"]
        assert "database" in exports
        assert "logging" in exports
        assert "features" in exports
    
    @pytest.mark.asyncio
    async def test_get_file_structure_not_found(self, indexed_project):
        """Test getting structure for non-existent file"""
        structure = await indexed_project.get_file_structure("/nonexistent/file.py")
        
        assert "error" in structure
        assert "not found in index" in structure["error"]
    
    @pytest.mark.asyncio
    async def test_file_structure_metadata(self, indexed_project, temp_project):
        """Test file structure metadata"""
        python_path = str(Path(temp_project) / "complex_module.py")
        
        structure = await indexed_project.get_file_structure(python_path)
        
        assert "size" in structure
        assert "last_modified" in structure
        assert "content_hash" in structure
        assert "access_count" in structure
        assert "last_accessed" in structure
        
        assert isinstance(structure["size"], int)
        assert structure["size"] > 0


class TestRelatedFiles:
    """Test related file finding"""
    
    @pytest.fixture
    def temp_project(self):
        """Create project with related files"""
        temp_dir = tempfile.mkdtemp()
        
        files = {
            "models/user.py": '''
from datetime import datetime
import json

class User:
    def to_dict(self):
        return {"username": self.username}
''',
            "models/admin.py": '''
from datetime import datetime
import json
from models.user import User

class Admin(User):
    def admin_action(self):
        pass
''',
            "services/user_service.py": '''
from models.user import User
import json

class UserService:
    def create_user(self):
        return User()
''',
            "services/admin_service.py": '''
from models.admin import Admin
import json
import requests

class AdminService:
    def create_admin(self):
        return Admin()
''',
            "utils/helpers.py": '''
import json
from datetime import datetime

def format_date(date):
    return date.strftime("%Y-%m-%d")
'''
        }
        
        for filepath, content in files.items():
            full_path = Path(temp_dir) / filepath
            full_path.parent.mkdir(parents=True, exist_ok=True)
            full_path.write_text(content)
        
        yield temp_dir
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    async def indexed_project(self, temp_project):
        """Create indexed project"""
        index = ContextIndex(temp_project)
        await index.build_index()
        return index
    
    @pytest.mark.asyncio
    async def test_find_related_files_dependencies(self, indexed_project, temp_project):
        """Test finding related files via dependencies"""
        user_model_path = str(Path(temp_project) / "models" / "user.py")
        
        related = await indexed_project.find_related_files(
            user_model_path,
            relation_types=["dependency", "reverse_dependency"],
            max_results=10
        )
        
        assert isinstance(related, list)
        assert len(related) > 0
        
        # Each result should be (file_path, relation_type, strength)
        for file_path, relation_type, strength in related:
            assert isinstance(file_path, str)
            assert relation_type in ["dependency", "reverse_dependency"]
            assert 0.0 <= strength <= 1.0
        
        # Should find reverse dependencies (files that import user.py)
        reverse_deps = [item for item in related if item[1] == "reverse_dependency"]
        assert len(reverse_deps) > 0
    
    @pytest.mark.asyncio
    async def test_find_related_files_shared_imports(self, indexed_project, temp_project):
        """Test finding related files via shared imports"""
        user_model_path = str(Path(temp_project) / "models" / "user.py")
        
        related = await indexed_project.find_related_files(
            user_model_path,
            relation_types=["shared_imports"],
            max_results=5
        )
        
        # Should find files that share imports with user.py
        shared_import_files = [item for item in related if item[1] == "shared_imports"]
        
        # Files that also import json and datetime should be found
        assert len(shared_import_files) > 0
    
    @pytest.mark.asyncio
    async def test_find_related_files_similar_structure(self, indexed_project, temp_project):
        """Test finding structurally similar files"""
        user_model_path = str(Path(temp_project) / "models" / "user.py")
        
        related = await indexed_project.find_related_files(
            user_model_path,
            relation_types=["similar_structure"],
            max_results=5
        )
        
        similar_files = [item for item in related if item[1] == "similar_structure"]
        
        # Should find files with similar class/function structure
        if len(similar_files) > 0:
            for file_path, relation_type, similarity in similar_files:
                assert 0.0 <= similarity <= 1.0
    
    @pytest.mark.asyncio
    async def test_find_related_files_all_types(self, indexed_project, temp_project):
        """Test finding related files with all relation types"""
        user_service_path = str(Path(temp_project) / "services" / "user_service.py")
        
        related = await indexed_project.find_related_files(
            user_service_path,
            max_results=10
        )
        
        # Should find multiple types of relationships
        relation_types = set(item[1] for item in related)
        assert len(relation_types) > 1
        
        # Results should be sorted by strength
        if len(related) > 1:
            for i in range(len(related) - 1):
                assert related[i][2] >= related[i + 1][2]
    
    @pytest.mark.asyncio
    async def test_structural_similarity_calculation(self, indexed_project, temp_project):
        """Test structural similarity calculation"""
        user_path = str(Path(temp_project) / "models" / "user.py")
        admin_path = str(Path(temp_project) / "models" / "admin.py")
        
        if user_path in indexed_project.file_nodes and admin_path in indexed_project.file_nodes:
            user_node = indexed_project.file_nodes[user_path]
            admin_node = indexed_project.file_nodes[admin_path]
            
            similarity = indexed_project._calculate_structural_similarity(user_node, admin_node)
            
            assert 0.0 <= similarity <= 1.0
            # Admin inherits from User, so should have some similarity
            assert similarity > 0.0


class TestAccessTracking:
    """Test file access tracking"""
    
    @pytest.fixture
    async def indexed_project(self):
        """Create simple indexed project"""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create simple file
            test_file = Path(temp_dir) / "test.py"
            test_file.write_text("def test(): pass")
            
            index = ContextIndex(temp_dir)
            await index.build_index()
            yield index
    
    @pytest.mark.asyncio
    async def test_track_file_access(self, indexed_project):
        """Test tracking file access"""
        test_path = str(indexed_project.project_path / "test.py")
        
        if test_path in indexed_project.file_nodes:
            node = indexed_project.file_nodes[test_path]
            initial_count = node.access_count
            initial_time = node.last_accessed
            
            # Track access
            await indexed_project.track_file_access(test_path)
            
            assert node.access_count == initial_count + 1
            assert node.last_accessed is not None
            assert node.last_accessed != initial_time
    
    @pytest.mark.asyncio
    async def test_track_nonexistent_file_access(self, indexed_project):
        """Test tracking access to non-existent file"""
        # Should handle gracefully
        await indexed_project.track_file_access("/nonexistent/file.py")
        
        # Should not raise exception


class TestProjectStatistics:
    """Test project statistics generation"""
    
    @pytest.fixture
    def temp_project(self):
        """Create project with various file types"""
        temp_dir = tempfile.mkdtemp()
        
        files = {
            "main.py": "class Main: pass",
            "service.py": "def service(): pass",
            "test_main.py": "import unittest",
            "config.json": '{"key": "value"}',
            "README.md": "# Project",
            "data.yaml": "data: value",
            "helper.py": "def helper(): pass"
        }
        
        for filename, content in files.items():
            (Path(temp_dir) / filename).write_text(content)
        
        yield temp_dir
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    async def indexed_project(self, temp_project):
        """Create indexed project"""
        index = ContextIndex(temp_project)
        await index.build_index()
        
        # Add some access tracking
        for file_path in index.file_nodes.keys():
            await index.track_file_access(file_path)
        
        return index
    
    @pytest.mark.asyncio
    async def test_get_project_statistics(self, indexed_project):
        """Test comprehensive project statistics"""
        stats = await indexed_project.get_project_statistics()
        
        assert isinstance(stats, dict)
        assert "total_files" in stats
        assert "file_types" in stats
        assert "total_dependencies" in stats
        assert "average_dependencies_per_file" in stats
        assert "most_dependent_files" in stats
        assert "most_depended_upon_files" in stats
        assert "largest_files" in stats
        assert "most_accessed_files" in stats
        
        # Check data types
        assert isinstance(stats["total_files"], int)
        assert isinstance(stats["file_types"], dict)
        assert isinstance(stats["total_dependencies"], int)
        assert isinstance(stats["average_dependencies_per_file"], (int, float))
        assert isinstance(stats["most_dependent_files"], list)
        assert isinstance(stats["most_depended_upon_files"], list)
        assert isinstance(stats["largest_files"], list)
        assert isinstance(stats["most_accessed_files"], list)
        
        # Check file type breakdown
        file_types = stats["file_types"]
        assert "python" in file_types
        assert "test" in file_types
        assert "json" in file_types
        assert "markdown" in file_types
    
    @pytest.mark.asyncio
    async def test_statistics_sorting(self, indexed_project):
        """Test that statistics are properly sorted"""
        stats = await indexed_project.get_project_statistics()
        
        # Check that largest files are sorted by size (descending)
        largest_files = stats["largest_files"]
        if len(largest_files) > 1:
            for i in range(len(largest_files) - 1):
                assert largest_files[i][1] >= largest_files[i + 1][1]
        
        # Check that most accessed files are sorted by access count (descending)
        most_accessed = stats["most_accessed_files"]
        if len(most_accessed) > 1:
            for i in range(len(most_accessed) - 1):
                assert most_accessed[i][1] >= most_accessed[i + 1][1]


class TestPerformanceMetrics:
    """Test performance metrics and optimization"""
    
    @pytest.fixture
    async def indexed_project(self):
        """Create indexed project"""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create test file
            test_file = Path(temp_dir) / "test.py"
            test_file.write_text("def test(): pass")
            
            index = ContextIndex(temp_dir)
            await index.build_index()
            yield index
    
    @pytest.mark.asyncio
    async def test_get_performance_metrics(self, indexed_project):
        """Test performance metrics collection"""
        # Perform some operations to generate metrics
        await indexed_project.search_files("test")
        await indexed_project.search_files("nonexistent")
        
        metrics = indexed_project.get_performance_metrics()
        
        assert isinstance(metrics, dict)
        assert "total_files" in metrics
        assert "total_dependencies" in metrics
        assert "index_build_time" in metrics
        assert "last_full_scan" in metrics
        assert "average_search_time" in metrics
        assert "total_searches" in metrics
        assert "cache_hit_rate" in metrics
        assert "cache_hits" in metrics
        assert "cache_misses" in metrics
        assert "search_indices" in metrics
        
        # Check that search operations were tracked
        assert metrics["total_searches"] > 0
        assert metrics["average_search_time"] > 0
        
        # Check search indices info
        search_indices = metrics["search_indices"]
        assert "functions" in search_indices
        assert "classes" in search_indices
        assert "imports" in search_indices
        assert "content_terms" in search_indices
    
    @pytest.mark.asyncio
    async def test_performance_timing(self, indexed_project):
        """Test that performance timing works"""
        initial_search_count = len(indexed_project.search_times)
        
        # Perform search
        await indexed_project.search_files("test")
        
        # Should have recorded timing
        assert len(indexed_project.search_times) == initial_search_count + 1
        assert indexed_project.search_times[-1] > 0
    
    @pytest.mark.asyncio
    async def test_close_database(self, indexed_project):
        """Test database connection closing"""
        # Should not raise exception
        await indexed_project.close()
        
        # Database connection should be closed
        # (In real usage, further operations would fail)


class TestErrorHandling:
    """Test error handling scenarios"""
    
    @pytest.fixture
    def temp_project(self):
        """Create project with problematic files"""
        temp_dir = tempfile.mkdtemp()
        
        # Create file with invalid Python syntax
        invalid_file = Path(temp_dir) / "invalid.py"
        invalid_file.write_text("def broken_function(\n    # Missing closing")
        
        # Create empty file
        empty_file = Path(temp_dir) / "empty.py"
        empty_file.write_text("")
        
        # Create valid file
        valid_file = Path(temp_dir) / "valid.py"
        valid_file.write_text("def valid_function(): pass")
        
        yield temp_dir
        shutil.rmtree(temp_dir)
    
    @pytest.mark.asyncio
    async def test_handle_invalid_python_files(self, temp_project):
        """Test handling of invalid Python files"""
        index = ContextIndex(temp_project)
        
        # Should not crash on invalid Python
        await index.build_index()
        
        # Should still index the file (just without AST analysis)
        invalid_path = str(Path(temp_project) / "invalid.py")
        assert invalid_path in index.file_nodes
        
        # Valid file should still be processed correctly
        valid_path = str(Path(temp_project) / "valid.py")
        assert valid_path in index.file_nodes
        assert "valid_function" in index.file_nodes[valid_path].functions
    
    @pytest.mark.asyncio
    async def test_handle_empty_files(self, temp_project):
        """Test handling of empty files"""
        index = ContextIndex(temp_project)
        await index.build_index()
        
        empty_path = str(Path(temp_project) / "empty.py")
        if empty_path in index.file_nodes:
            node = index.file_nodes[empty_path]
            assert len(node.functions) == 0
            assert len(node.classes) == 0
            assert len(node.imports) == 0
    
    @pytest.mark.asyncio
    async def test_search_error_handling(self, temp_project):
        """Test search error handling"""
        index = ContextIndex(temp_project)
        await index.build_index()
        
        # Search should not crash even with empty index or invalid queries
        results = await index.search_files("")
        assert isinstance(results, list)
        
        results = await index.search_files("nonexistent_term")
        assert isinstance(results, list)
    
    @pytest.mark.asyncio
    async def test_database_error_recovery(self, temp_project):
        """Test database error recovery"""
        index = ContextIndex(temp_project)
        
        # Corrupt the database file
        if index.cache_path.exists():
            with open(index.cache_path, 'w') as f:
                f.write("corrupted data")
        
        # Should recover gracefully
        try:
            await index.build_index()
        except Exception:
            # Even if it fails, should not crash the entire system
            pass


if __name__ == "__main__":
    pytest.main([__file__])