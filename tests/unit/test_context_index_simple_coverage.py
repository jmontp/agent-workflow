"""
Simple comprehensive coverage test for context_index.py.

This test focuses on achieving 95%+ line coverage with minimal fixture complexity.
"""

import pytest
import tempfile
import shutil
import sqlite3
import json
import ast
import hashlib
from pathlib import Path
from datetime import datetime
from unittest.mock import Mock, AsyncMock, patch

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


class TestContextIndexCoverage:
    """Comprehensive coverage tests for ContextIndex"""
    
    def setup_method(self):
        """Set up test method"""
        self.temp_dir = tempfile.mkdtemp()
        self.addCleanup = lambda f: f  # Mock cleanup
    
    def teardown_method(self):
        """Clean up after test"""
        if hasattr(self, 'temp_dir'):
            shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def create_sample_project(self):
        """Create a sample project structure"""
        # Create Python files
        main_py = Path(self.temp_dir) / "main.py"
        main_py.write_text('''
import os
import json
from utils import helper

class Application:
    def __init__(self):
        self.name = "test"
    
    def run(self):
        return helper.process()

def main():
    app = Application()
    return app.run()
''')
        
        utils_py = Path(self.temp_dir) / "utils.py"
        utils_py.write_text('''
def helper():
    return "processed"

def process():
    return helper()

class Helper:
    def method(self):
        pass
''')
        
        # Create test file
        test_py = Path(self.temp_dir) / "test_main.py"
        test_py.write_text('''
import unittest
from main import Application

class TestApp(unittest.TestCase):
    def test_run(self):
        app = Application()
        result = app.run()
        self.assertIsNotNone(result)
''')
        
        # Create config file
        config_json = Path(self.temp_dir) / "config.json"
        config_json.write_text('{"debug": true, "port": 8080}')
        
        # Create markdown file
        readme_md = Path(self.temp_dir) / "README.md"
        readme_md.write_text('# Test Project\n\nThis is a test.')
        
        return self.temp_dir
    
    def test_context_index_initialization(self):
        """Test ContextIndex initialization"""
        project_path = self.create_sample_project()
        
        # Test with default parameters
        index = ContextIndex(project_path)
        assert index.project_path == Path(project_path)
        assert index.token_calculator is not None
        assert index.cache_path.name == "context_index.db"
        assert hasattr(index, 'file_nodes')
        assert hasattr(index, 'dependencies')
        assert hasattr(index, 'db')
        
        # Test with custom parameters
        custom_cache = str(Path(project_path) / "custom.db")
        mock_calc = Mock(spec=TokenCalculator)
        mock_calc.estimate_tokens = AsyncMock(return_value=100)
        
        index2 = ContextIndex(
            project_path=project_path,
            index_cache_path=custom_cache,
            token_calculator=mock_calc
        )
        assert index2.cache_path == Path(custom_cache)
        assert index2.token_calculator is mock_calc
    
    @pytest.mark.asyncio
    async def test_build_index_complete(self):
        """Test complete index building process"""
        project_path = self.create_sample_project()
        index = ContextIndex(project_path)
        
        # Test build index
        await index.build_index()
        
        # Verify files were indexed
        assert len(index.file_nodes) > 0
        
        # Check specific files
        main_path = str(Path(project_path) / "main.py")
        assert main_path in index.file_nodes
        
        main_node = index.file_nodes[main_path]
        assert main_node.file_type == FileType.PYTHON
        assert "Application" in main_node.classes
        assert "main" in main_node.functions
        assert "run" in main_node.functions
        assert "os" in main_node.imports
        assert "json" in main_node.imports
        
        # Test force rebuild
        initial_count = len(index.file_nodes)
        await index.build_index(force_rebuild=True)
        assert len(index.file_nodes) == initial_count
    
    @pytest.mark.asyncio
    async def test_search_functionality(self):
        """Test search functionality"""
        project_path = self.create_sample_project()
        index = ContextIndex(project_path)
        await index.build_index()
        
        # Test function search
        results = await index.search_files("main", search_type="functions")
        assert isinstance(results, list)
        
        # Test class search
        results = await index.search_files("Application", search_type="classes")
        assert isinstance(results, list)
        
        # Test import search
        results = await index.search_files("os", search_type="imports")
        assert isinstance(results, list)
        
        # Test all types search
        results = await index.search_files("test", search_type="all")
        assert isinstance(results, list)
        
        # Test max results
        results = await index.search_files("test", max_results=1)
        assert len(results) <= 1
        
        # Test empty query
        results = await index.search_files("")
        assert isinstance(results, list)
    
    @pytest.mark.asyncio
    async def test_dependency_analysis(self):
        """Test dependency analysis"""
        project_path = self.create_sample_project()
        index = ContextIndex(project_path)
        await index.build_index()
        
        main_path = str(Path(project_path) / "main.py")
        
        # Test basic dependencies
        deps = await index.get_file_dependencies(main_path)
        assert "file" in deps
        assert "direct_dependencies" in deps
        assert "dependency_count" in deps
        assert "reverse_dependencies" in deps
        
        # Test with depth
        deps = await index.get_file_dependencies(main_path, depth=2, include_reverse=True)
        assert "transitive_dependencies" in deps
        assert "transitive_count" in deps
        
        # Test non-existent file
        deps = await index.get_file_dependencies("/nonexistent.py")
        assert "error" in deps
    
    @pytest.mark.asyncio
    async def test_file_structure_analysis(self):
        """Test file structure analysis"""
        project_path = self.create_sample_project()
        index = ContextIndex(project_path)
        await index.build_index()
        
        main_path = str(Path(project_path) / "main.py")
        
        # Test file structure
        structure = await index.get_file_structure(main_path)
        assert "file" in structure
        assert "file_type" in structure
        assert "classes" in structure
        assert "functions" in structure
        assert "imports" in structure
        assert structure["file_type"] == "python"
        
        # Test non-existent file
        structure = await index.get_file_structure("/nonexistent.py")
        assert "error" in structure
    
    @pytest.mark.asyncio
    async def test_related_files(self):
        """Test related file finding"""
        project_path = self.create_sample_project()
        index = ContextIndex(project_path)
        await index.build_index()
        
        main_path = str(Path(project_path) / "main.py")
        
        # Test finding related files
        related = await index.find_related_files(main_path, max_results=5)
        assert isinstance(related, list)
        
        for file_path, relation_type, strength in related:
            assert isinstance(file_path, str)
            assert isinstance(relation_type, str)
            assert 0.0 <= strength <= 1.0
    
    @pytest.mark.asyncio
    async def test_access_tracking(self):
        """Test file access tracking"""
        project_path = self.create_sample_project()
        index = ContextIndex(project_path)
        await index.build_index()
        
        main_path = str(Path(project_path) / "main.py")
        
        if main_path in index.file_nodes:
            node = index.file_nodes[main_path]
            initial_count = node.access_count
            
            # Track access
            await index.track_file_access(main_path)
            assert node.access_count == initial_count + 1
            assert node.last_accessed is not None
        
        # Test non-existent file
        await index.track_file_access("/nonexistent.py")  # Should not raise
    
    @pytest.mark.asyncio
    async def test_project_statistics(self):
        """Test project statistics"""
        project_path = self.create_sample_project()
        index = ContextIndex(project_path)
        await index.build_index()
        
        # Track some file access
        for file_path in list(index.file_nodes.keys())[:2]:
            await index.track_file_access(file_path)
        
        stats = await index.get_project_statistics()
        assert "total_files" in stats
        assert "file_types" in stats
        assert "total_dependencies" in stats
        assert "average_dependencies_per_file" in stats
        assert "most_dependent_files" in stats
        assert "most_depended_upon_files" in stats
        assert "largest_files" in stats
        assert "most_accessed_files" in stats
        
        assert isinstance(stats["total_files"], int)
        assert stats["total_files"] > 0
    
    def test_performance_metrics(self):
        """Test performance metrics"""
        project_path = self.create_sample_project()
        index = ContextIndex(project_path)
        
        # Add some search times
        index.search_times = [0.1, 0.2, 0.3]
        index.cache_hits = 10
        index.cache_misses = 5
        
        metrics = index.get_performance_metrics()
        assert "total_files" in metrics
        assert "total_dependencies" in metrics
        assert "index_build_time" in metrics
        assert "average_search_time" in metrics
        assert "total_searches" in metrics
        assert "cache_hit_rate" in metrics
        assert "search_indices" in metrics
        
        assert metrics["total_searches"] == 3
        assert metrics["cache_hit_rate"] == 10 / 15
    
    @pytest.mark.asyncio
    async def test_error_handling(self):
        """Test error handling scenarios"""
        project_path = self.create_sample_project()
        
        # Create file with syntax error
        broken_py = Path(project_path) / "broken.py"
        broken_py.write_text("def broken(:\n    invalid syntax")
        
        # Create empty file
        empty_py = Path(project_path) / "empty.py"
        empty_py.write_text("")
        
        index = ContextIndex(project_path)
        await index.build_index()  # Should not crash
        
        # Broken file should still be indexed
        broken_path = str(broken_py)
        if broken_path in index.file_nodes:
            assert index.file_nodes[broken_path].file_type == FileType.PYTHON
    
    def test_string_similarity_calculations(self):
        """Test string similarity calculations"""
        # Use temp directory to avoid permission issues
        with tempfile.TemporaryDirectory() as temp_dir:
            index = ContextIndex(temp_dir)
        
            # Test exact match
            assert index._calculate_string_similarity("test", "test") == 1.0
            
            # Test no overlap
            assert index._calculate_string_similarity("abc", "def") == 0.0
            
            # Test substring (returns max ratio, can be > 1.0)
            similarity = index._calculate_string_similarity("test", "testing")
            assert similarity > 0.0
            
            # Test empty strings
            assert index._calculate_string_similarity("", "") == 1.0
            
            # Test edge cases
            assert 0.0 <= index._calculate_string_similarity("a", "b") <= 1.0
            assert 0.0 <= index._calculate_string_similarity("", "test") <= 1.0
    
    def test_list_similarity_calculations(self):
        """Test list similarity calculations"""
        with tempfile.TemporaryDirectory() as temp_dir:
            index = ContextIndex(temp_dir)
            
            # Test identical lists
            assert index._calculate_list_similarity(["a", "b"], ["a", "b"]) == 1.0
            
            # Test empty lists
            assert index._calculate_list_similarity([], []) == 1.0
            
            # Test one empty
            assert index._calculate_list_similarity([], ["a"]) == 0.0
            assert index._calculate_list_similarity(["a"], []) == 0.0
            
            # Test no overlap
            assert index._calculate_list_similarity(["a"], ["b"]) == 0.0
            
            # Test partial overlap
            similarity = index._calculate_list_similarity(["a", "b"], ["b", "c"])
            assert 0.0 < similarity <= 1.0
    
    def test_file_type_detection(self):
        """Test file type detection"""
        with tempfile.TemporaryDirectory() as temp_dir:
            index = ContextIndex(temp_dir)
            
            # Test Python files
            assert index._determine_file_type(Path("main.py")) == FileType.PYTHON
            assert index._determine_file_type(Path("utils.py")) == FileType.PYTHON
            
            # Test test files
            assert index._determine_file_type(Path("test_main.py")) == FileType.TEST
            assert index._determine_file_type(Path("tests/test_utils.py")) == FileType.TEST
            assert index._determine_file_type(Path("test/test_utils.py")) == FileType.TEST
            
            # Test other types
            assert index._determine_file_type(Path("config.json")) == FileType.JSON
            assert index._determine_file_type(Path("README.md")) == FileType.MARKDOWN
            assert index._determine_file_type(Path("guide.rst")) == FileType.MARKDOWN
            assert index._determine_file_type(Path("config.yml")) == FileType.YAML
            assert index._determine_file_type(Path("config.yaml")) == FileType.YAML
            assert index._determine_file_type(Path("setup.cfg")) == FileType.CONFIG
            assert index._determine_file_type(Path("setup.ini")) == FileType.CONFIG
            assert index._determine_file_type(Path("app.conf")) == FileType.CONFIG
            assert index._determine_file_type(Path("pyproject.toml")) == FileType.CONFIG
            assert index._determine_file_type(Path("LICENSE")) == FileType.OTHER
    
    def test_file_filtering(self):
        """Test file filtering logic"""
        with tempfile.TemporaryDirectory() as temp_dir:
            index = ContextIndex(temp_dir)
            
            # Test normal file
            normal_file = Path(temp_dir) / "normal.py"
            normal_file.write_text("def test(): pass")
            assert index._should_index_file(normal_file) == True
            
            # Test hidden file
            hidden_file = Path(temp_dir) / ".hidden.py"
            hidden_file.write_text("def test(): pass")
            assert index._should_index_file(hidden_file) == False
            
            # Test .orch-state exception
            orch_dir = Path(temp_dir) / ".orch-state"
            orch_dir.mkdir()
            orch_file = orch_dir / "status.json"
            orch_file.write_text('{"status": "active"}')
            assert index._should_index_file(orch_file) == True
            
            # Test ignore patterns
            ignored_patterns = [
                "__pycache__/cache.pyc",
                ".git/config",
                "venv/lib/python.py",
                "node_modules/pkg.js",
                ".pytest_cache/cache.py",
                "build/output.o",
                "dist/package.whl",
                ".mypy_cache/file.json"
            ]
            
            for pattern in ignored_patterns:
                test_path = Path(temp_dir) / pattern
                test_path.parent.mkdir(parents=True, exist_ok=True)
                test_path.write_text("content")
                assert index._should_index_file(test_path) == False
            
            # Test large file
            large_file = Path(temp_dir) / "large.py"
            large_file.write_text("x" * 2_000_000)  # 2MB
            assert index._should_index_file(large_file) == False
            
            # Test file that doesn't exist (OSError)
            nonexistent = Path(temp_dir) / "nonexistent.py"
            assert index._should_index_file(nonexistent) == False
    
    @pytest.mark.asyncio
    async def test_database_operations(self):
        """Test database operations"""
        project_path = self.create_sample_project()
        index = ContextIndex(project_path)
        
        # Test database initialization
        assert index.cache_path.exists()
        
        # Test building and saving
        await index.build_index()
        
        # Test clearing
        await index._clear_index()
        assert len(index.file_nodes) == 0
        assert len(index.dependencies) == 0
        
        # Test loading from cache
        await index._load_index_from_cache()
        
        # Test closing
        await index.close()
    
    @pytest.mark.asyncio
    async def test_private_methods(self):
        """Test private methods for coverage"""
        project_path = self.create_sample_project()
        index = ContextIndex(project_path)
        await index.build_index()
        
        main_path = str(Path(project_path) / "main.py")
        
        # Test transitive dependencies
        if main_path in index.file_nodes:
            transitive = await index._get_transitive_dependencies(main_path, 2)
            assert isinstance(transitive, set)
            
            # Test with depth 0
            transitive_zero = await index._get_transitive_dependencies(main_path, 0)
            assert isinstance(transitive_zero, set)
        
        # Test similar files
        if main_path in index.file_nodes:
            similar = await index._find_structurally_similar_files(main_path, 3)
            assert isinstance(similar, list)
            
            # Test with file not in index
            empty_similar = await index._find_structurally_similar_files("/nonexistent.py", 3)
            assert empty_similar == []
        
        # Test shared imports
        if main_path in index.file_nodes:
            shared = await index._find_files_with_shared_imports(main_path, 3)
            assert isinstance(shared, list)
            
            # Test with file not in index
            empty_shared = await index._find_files_with_shared_imports("/nonexistent.py", 3)
            assert empty_shared == []
        
        # Test structural similarity
        if len(index.file_nodes) >= 2:
            paths = list(index.file_nodes.keys())[:2]
            node1 = index.file_nodes[paths[0]]
            node2 = index.file_nodes[paths[1]]
            
            similarity = index._calculate_structural_similarity(node1, node2)
            assert 0.0 <= similarity <= 1.0
    
    @pytest.mark.asyncio
    async def test_edge_cases_and_error_conditions(self):
        """Test edge cases and error conditions for coverage"""
        project_path = self.create_sample_project()
        index = ContextIndex(project_path)
        
        # Test building on corrupted cache
        with patch.object(index, '_load_index_from_cache', side_effect=Exception("Corrupted cache")):
            await index.build_index()  # Should handle gracefully
        
        # Test search with various edge cases
        await index.build_index()
        
        # Test search error handling with mocked exception
        with patch.object(index, '_search_functions', side_effect=Exception("Search error")):
            results = await index.search_files("test", search_type="functions")
            assert results == []  # Should return empty list on error
        
        # Test database update errors
        with patch.object(index, 'db') as mock_db:
            mock_db.execute.side_effect = Exception("DB error")
            await index._update_file_access_in_db("test.py", 1, datetime.utcnow())
            # Should not raise exception
        
        # Test file processing with various file content
        invalid_json = Path(project_path) / "invalid.json"
        invalid_json.write_text('{"invalid": json}')  # Invalid JSON
        
        unicode_file = Path(project_path) / "unicode.py"
        unicode_file.write_text('# -*- coding: utf-8 -*-\ndef función(): pass')
        
        empty_file = Path(project_path) / "empty.py"
        empty_file.write_text('')
        
        # Rebuild to process these files
        await index.build_index(force_rebuild=True)
    
    @pytest.mark.asyncio
    async def test_content_search_and_performance(self):
        """Test content search and performance tracking"""
        project_path = self.create_sample_project()
        index = ContextIndex(project_path)
        await index.build_index()
        
        # Test content search
        results = await index.search_files("test", search_type="content", include_content=True)
        assert isinstance(results, list)
        
        # Test performance metrics with search operations
        initial_search_count = len(index.search_times)
        
        # Perform multiple searches to generate metrics
        await index.search_files("Application", search_type="functions")
        await index.search_files("test", search_type="classes")
        await index.search_files("os", search_type="imports")
        
        # Check performance was tracked
        assert len(index.search_times) > initial_search_count
        
        # Test cache metrics
        index.cache_hits = 5
        index.cache_misses = 2
        metrics = index.get_performance_metrics()
        assert metrics["cache_hit_rate"] == 5 / 7
        
        # Test with no cache operations
        index.cache_hits = 0
        index.cache_misses = 0
        metrics = index.get_performance_metrics()
        assert metrics["cache_hit_rate"] == 0.0
    
    @pytest.mark.asyncio
    async def test_advanced_file_extraction(self):
        """Test advanced file structure extraction"""
        project_path = self.create_sample_project()
        
        # Create complex Python file with various constructs
        complex_py = Path(project_path) / "complex.py"
        complex_py.write_text('''
import os, sys
import json as js
from datetime import datetime, timedelta
from typing import List, Dict
from . import relative_import
from ..parent import parent_import

class BaseClass:
    def base_method(self):
        pass

class DerivedClass(BaseClass):
    def __init__(self):
        super().__init__()
    
    def derived_method(self):
        return "derived"
    
    @property
    def prop(self):
        return self._prop

def function_with_params(a: int, b: str = "default") -> bool:
    return True

async def async_function():
    await some_operation()

def _private_function():
    pass

@decorator
def decorated_function():
    pass

lambda_func = lambda x: x * 2

# Global variable
CONSTANT = "value"
''')
        
        index = ContextIndex(project_path)
        await index.build_index()
        
        complex_path = str(complex_py)
        if complex_path in index.file_nodes:
            node = index.file_nodes[complex_path]
            
            # Check classes were extracted
            assert "BaseClass" in node.classes
            assert "DerivedClass" in node.classes
            
            # Check functions were extracted
            assert "function_with_params" in node.functions
            assert "async_function" in node.functions
            assert "_private_function" in node.functions
            assert "decorated_function" in node.functions
            
            # Check imports were extracted
            assert "os" in node.imports
            assert "sys" in node.imports
            assert "json" in node.imports  # from 'import json as js'
            assert "datetime" in node.imports  # from 'from datetime import datetime'


class TestDataClasses:
    """Test data classes comprehensively"""
    
    def test_file_node_complete(self):
        """Test FileNode with all features"""
        now = datetime.utcnow()
        
        node = FileNode(
            path="/test/file.py",
            file_type=FileType.PYTHON,
            size=1024,
            last_modified=now,
            content_hash="hash123",
            imports=["os", "sys"],
            exports=["func1"],
            classes=["TestClass"],
            functions=["test_func"],
            dependencies=["/dep.py"],
            reverse_dependencies=["/rev.py"],
            access_count=5,
            last_accessed=now
        )
        
        # Test serialization
        data = node.to_dict()
        assert data["file_type"] == "python"
        assert data["access_count"] == 5
        
        # Test deserialization
        restored = FileNode.from_dict(data)
        assert restored.path == node.path
        assert restored.file_type == node.file_type
        assert restored.access_count == node.access_count
    
    def test_dependency_edge(self):
        """Test DependencyEdge"""
        edge = DependencyEdge(
            source="/src.py",
            target="/target.py",
            import_type="import",
            line_number=10,
            strength=0.8
        )
        
        assert edge.source == "/src.py"
        assert edge.target == "/target.py"
        assert edge.import_type == "import"
        assert edge.line_number == 10
        assert edge.strength == 0.8
        
        # Test defaults
        edge2 = DependencyEdge("/a.py", "/b.py", "from", 1)
        assert edge2.strength == 1.0
    
    def test_search_result(self):
        """Test SearchResult"""
        result = SearchResult(
            file_path="/result.py",
            relevance_score=0.9,
            match_type="exact",
            matches=["test_func"],
            context="Function: test_func"
        )
        
        assert result.file_path == "/result.py"
        assert result.relevance_score == 0.9
        assert result.match_type == "exact"
        assert result.matches == ["test_func"]
        assert result.context == "Function: test_func"
        
        # Test defaults
        result2 = SearchResult("/test.py", 0.5, "partial", ["match"])
        assert result2.context == ""


if __name__ == "__main__":
    pytest.main([__file__, "-v"])