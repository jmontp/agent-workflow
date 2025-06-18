"""
Comprehensive test suite for Context Compressor System.

Tests intelligent content compression with AST-based Python compression,
test file compression, documentation summarization, and performance tracking.
"""

import pytest
import asyncio
import ast
import json
from unittest.mock import Mock, AsyncMock, patch
from typing import Dict, Any

# Import the modules under test
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "lib"))

from context_compressor import ContextCompressor
from context.models import CompressionLevel, FileType, TokenUsage, ContextRequest
from token_calculator import TokenCalculator


class TestContextCompressorInit:
    """Test ContextCompressor initialization"""
    
    def test_init_with_defaults(self):
        """Test initialization with default parameters"""
        compressor = ContextCompressor()
        
        assert compressor.token_calculator is not None
        assert compressor._compression_operations == 0
        assert compressor._total_compression_time == 0.0
        assert len(compressor._compression_ratios) == 0
        assert len(compressor._compression_stats) == 4  # One for each compression level
    
    def test_init_with_custom_token_calculator(self):
        """Test initialization with custom token calculator"""
        mock_calculator = Mock(spec=TokenCalculator)
        compressor = ContextCompressor(token_calculator=mock_calculator)
        
        assert compressor.token_calculator == mock_calculator
    
    def test_compression_stats_initialization(self):
        """Test that compression stats are properly initialized"""
        compressor = ContextCompressor()
        
        for level in CompressionLevel:
            assert level in compressor._compression_stats
            stats = compressor._compression_stats[level]
            assert stats["count"] == 0
            assert stats["avg_ratio"] == 0.0


class TestContentCompression:
    """Test main content compression functionality"""
    
    @pytest.fixture
    def compressor(self):
        """Create compressor with mock token calculator"""
        mock_calculator = AsyncMock(spec=TokenCalculator)
        return ContextCompressor(token_calculator=mock_calculator)
    
    @pytest.mark.asyncio
    async def test_compress_python_content(self, compressor):
        """Test Python content compression"""
        python_code = '''
import os
import sys

class TestClass:
    """This is a test class."""
    
    def __init__(self):
        self.value = 42
    
    def test_method(self):
        """Test method with docstring."""
        return self.value * 2

def standalone_function():
    """A standalone function."""
    return "Hello, World!"

# Some comments
CONSTANT_VALUE = 100
'''
        
        # Mock token estimation
        compressor.token_calculator.estimate_tokens.side_effect = [1000, 600]  # before, after
        
        compressed, ratio = await compressor.compress_content(
            content=python_code,
            file_path="test_file.py",
            file_type=FileType.PYTHON,
            compression_level=CompressionLevel.MODERATE
        )
        
        assert isinstance(compressed, str)
        assert ratio == 0.6  # 600/1000
        assert "import os" in compressed  # Should preserve imports
        assert "class TestClass" in compressed  # Should preserve class structure
        assert compressor._compression_operations == 1
    
    @pytest.mark.asyncio
    async def test_compress_test_content(self, compressor):
        """Test test file compression"""
        test_code = '''
import pytest
from unittest.mock import Mock

@pytest.fixture
def sample_fixture():
    return Mock()

class TestSampleClass:
    def test_basic_functionality(self):
        """Test basic functionality."""
        assert True
        assert 1 + 1 == 2
        assert "hello" in "hello world"
    
    def test_with_fixture(self, sample_fixture):
        """Test using fixture."""
        sample_fixture.return_value = 42
        assert sample_fixture.return_value == 42

def test_standalone_function():
    """Standalone test function."""
    result = some_function()
    assert result is not None
    assert isinstance(result, str)
'''
        
        compressor.token_calculator.estimate_tokens.side_effect = [800, 400]
        
        compressed, ratio = await compressor.compress_content(
            content=test_code,
            file_path="test_sample.py", 
            file_type=FileType.TEST,
            compression_level=CompressionLevel.MODERATE
        )
        
        assert isinstance(compressed, str)
        assert ratio == 0.5  # 400/800
        assert "import pytest" in compressed  # Should preserve imports
        assert "fixture" in compressed.lower()  # Should preserve fixtures
        assert "assert" in compressed  # Should preserve assertions
    
    @pytest.mark.asyncio
    async def test_compress_markdown_content(self, compressor):
        """Test markdown content compression"""
        markdown_content = '''
# Main Title

This is an introduction paragraph with important information.

## Section 1

This section contains detailed explanations about the topic.
Multiple sentences provide comprehensive coverage.

## Section 2

Another section with different content.
This has multiple paragraphs as well.

Some additional content here.

### Subsection

Even more detailed information in subsections.
'''
        
        compressor.token_calculator.estimate_tokens.side_effect = [500, 250]
        
        compressed, ratio = await compressor.compress_content(
            content=markdown_content,
            file_path="test.md",
            file_type=FileType.MARKDOWN,
            compression_level=CompressionLevel.MODERATE
        )
        
        assert isinstance(compressed, str)
        assert ratio == 0.5
        assert "# Main Title" in compressed  # Should preserve headers
        assert len(compressed) < len(markdown_content)
    
    @pytest.mark.asyncio
    async def test_compress_json_content(self, compressor):
        """Test JSON content compression"""
        json_content = '''
{
    "name": "test_project",
    "version": "1.0.0",
    "description": "A test project for compression",
    "dependencies": {
        "package1": "^1.0.0",
        "package2": "^2.1.0",
        "package3": "^0.5.0"
    },
    "scripts": {
        "test": "pytest",
        "build": "python setup.py build",
        "install": "pip install ."
    },
    "author": "Test Author",
    "license": "MIT"
}
'''
        
        compressor.token_calculator.estimate_tokens.side_effect = [300, 150]
        
        compressed, ratio = await compressor.compress_content(
            content=json_content,
            file_path="package.json",
            file_type=FileType.JSON,
            compression_level=CompressionLevel.MODERATE
        )
        
        assert isinstance(compressed, str)
        assert ratio == 0.5
        # Should be valid JSON or schema representation
        assert "name" in compressed
    
    @pytest.mark.asyncio
    async def test_compression_with_target_tokens(self, compressor):
        """Test compression with specific token target"""
        content = "This is a test content that needs to be compressed to fit within token limits."
        
        compressor.token_calculator.estimate_tokens.side_effect = [100, 50]
        
        compressed, ratio = await compressor.compress_content(
            content=content,
            file_path="test.txt",
            file_type=FileType.OTHER,
            compression_level=CompressionLevel.MODERATE,
            target_tokens=50
        )
        
        assert isinstance(compressed, str)
        assert ratio == 0.5
    
    @pytest.mark.asyncio
    async def test_compression_error_handling(self, compressor):
        """Test error handling during compression"""
        # Mock token calculator to raise exception
        compressor.token_calculator.estimate_tokens.side_effect = Exception("Token estimation failed")
        
        compressed, ratio = await compressor.compress_content(
            content="test content",
            file_path="test.py",
            file_type=FileType.PYTHON,
            compression_level=CompressionLevel.MODERATE
        )
        
        # Should return original content and ratio 1.0 on error
        assert compressed == "test content"
        assert ratio == 1.0


class TestPythonSpecificCompression:
    """Test Python-specific compression methods"""
    
    @pytest.fixture
    def compressor(self):
        """Create compressor for testing"""
        return ContextCompressor()
    
    @pytest.mark.asyncio
    async def test_compress_python_class(self, compressor):
        """Test Python class compression"""
        class_info = {
            'name': 'TestClass',
            'content': '''class TestClass:
    def method1(self):
        pass
    def method2(self):
        pass''',
            'methods': [
                {'name': 'method1', 'signature': 'def method1(self)'},
                {'name': 'method2', 'signature': 'def method2(self)'}
            ]
        }
        
        # Test moderate compression
        compressed = await compressor._compress_python_class(
            class_info, CompressionLevel.MODERATE, preserve_structure=True
        )
        
        assert "class TestClass:" in compressed
        assert "def method1(self):" in compressed
        assert "pass  # [compressed]" in compressed
    
    @pytest.mark.asyncio
    async def test_compress_python_function(self, compressor):
        """Test Python function compression"""
        func_info = {
            'name': 'test_function',
            'signature': 'def test_function(param1, param2)',
            'content': '''def test_function(param1, param2):
    """Function docstring."""
    result = param1 + param2
    return result''',
            'docstring': 'Function docstring.'
        }
        
        # Test low compression (preserve docstring)
        compressed = await compressor._compress_python_function(
            func_info, CompressionLevel.LOW, preserve_structure=True
        )
        
        assert "def test_function(param1, param2):" in compressed
        assert "Function docstring." in compressed
        assert "pass  # [body compressed]" in compressed
        
        # Test high compression (signature only)
        compressed = await compressor._compress_python_function(
            func_info, CompressionLevel.HIGH, preserve_structure=True
        )
        
        assert "def test_function(param1, param2):" in compressed
        assert "pass  # [compressed]" in compressed
        assert "Function docstring." not in compressed
    
    @pytest.mark.asyncio
    async def test_extract_imports(self, compressor):
        """Test import extraction from AST"""
        code = '''
import os
import sys
from pathlib import Path
from typing import Dict, List
'''
        tree = ast.parse(code)
        imports = await compressor._extract_imports(tree, code)
        
        assert "import os" in imports
        assert "import sys" in imports
        assert "from pathlib import Path" in imports
        assert "from typing import Dict, List" in imports
    
    @pytest.mark.asyncio
    async def test_extract_classes(self, compressor):
        """Test class extraction from AST"""
        code = '''
class FirstClass:
    def method1(self):
        pass

class SecondClass:
    def method2(self, param):
        pass
    def method3(self):
        pass
'''
        tree = ast.parse(code)
        classes = await compressor._extract_classes(tree, code)
        
        assert len(classes) == 2
        assert classes[0]['name'] == 'FirstClass'
        assert classes[1]['name'] == 'SecondClass'
        assert len(classes[0]['methods']) == 1
        assert len(classes[1]['methods']) == 2
    
    @pytest.mark.asyncio
    async def test_extract_functions(self, compressor):
        """Test function extraction from AST"""
        code = '''
def function1():
    """First function."""
    pass

def function2(param1, param2):
    """Second function."""
    return param1 + param2
'''
        tree = ast.parse(code)
        functions = await compressor._extract_functions(tree, code)
        
        assert len(functions) == 2
        assert functions[0]['name'] == 'function1'
        assert functions[1]['name'] == 'function2'
        assert functions[0]['docstring'] == 'First function.'
        assert functions[1]['docstring'] == 'Second function.'


class TestTestFileCompression:
    """Test test file specific compression"""
    
    @pytest.fixture
    def compressor(self):
        """Create compressor for testing"""
        mock_calculator = AsyncMock(spec=TokenCalculator)
        return ContextCompressor(token_calculator=mock_calculator)
    
    @pytest.mark.asyncio
    async def test_compress_test_function(self, compressor):
        """Test test function compression"""
        func_info = {
            'name': 'test_example',
            'signature': 'def test_example(self)',
            'assertions': [
                'assert result is not None',
                'assert result == expected',
                'assert len(result) > 0'
            ]
        }
        
        # Test moderate compression
        compressed = await compressor._compress_test_function(
            func_info, CompressionLevel.MODERATE
        )
        
        assert "def test_example(self):" in compressed
        assert "3 assertions" in compressed
        assert "assert result is not None" in compressed
        assert "assert result == expected" in compressed
    
    @pytest.mark.asyncio
    async def test_compress_test_fixture(self, compressor):
        """Test fixture compression"""
        fixture_info = {
            'name': 'sample_fixture',
            'signature': 'def sample_fixture()',
            'type': 'fixture'
        }
        
        compressed = await compressor._compress_test_fixture(
            fixture_info, CompressionLevel.MODERATE
        )
        
        assert "@pytest.fixture" in compressed
        assert "def sample_fixture():" in compressed
        assert "pass  # [fixture]" in compressed
    
    @pytest.mark.asyncio
    async def test_extract_test_function(self, compressor):
        """Test test function extraction"""
        code = '''
def test_example():
    """Test function."""
    result = some_function()
    assert result is not None
    assert result == "expected"
    self.assertEqual(result, "expected")
'''
        tree = ast.parse(code)
        func_node = tree.body[0]  # First function
        
        func_info = await compressor._extract_test_function(func_node, code)
        
        assert func_info['name'] == 'test_example'
        assert 'assert result is not None' in func_info['assertions']
        assert 'assert result == "expected"' in func_info['assertions']
        assert 'self.assertEqual(result, "expected")' in func_info['assertions']


class TestMarkdownCompression:
    """Test markdown-specific compression"""
    
    @pytest.fixture
    def compressor(self):
        """Create compressor for testing"""
        mock_calculator = AsyncMock(spec=TokenCalculator)
        return ContextCompressor(token_calculator=mock_calculator)
    
    @pytest.mark.asyncio
    async def test_compress_markdown_section(self, compressor):
        """Test markdown section compression"""
        header = "## Test Section"
        content = [
            "This is the first paragraph with multiple sentences.",
            "This contains important information.",
            "",
            "This is the second paragraph.",
            "It also has multiple sentences for testing."
        ]
        
        # Test moderate compression
        compressed = await compressor._compress_markdown_section(
            header, content, CompressionLevel.MODERATE
        )
        
        assert header in compressed
        assert len(compressed) > 1  # Should have header + content
        
        # Test high compression
        compressed = await compressor._compress_markdown_section(
            header, content, CompressionLevel.HIGH
        )
        
        assert header in compressed
        assert "[" in compressed[1]  # Should have compressed content indicator


class TestJSONCompression:
    """Test JSON-specific compression"""
    
    @pytest.fixture
    def compressor(self):
        """Create compressor for testing"""
        return ContextCompressor()
    
    def test_json_to_schema_simple(self, compressor):
        """Test JSON to schema conversion for simple objects"""
        data = {
            "name": "test",
            "version": "1.0.0",
            "enabled": True,
            "count": 42
        }
        
        schema = compressor._json_to_schema(data, max_depth=2)
        
        assert '"name": <str>' in schema
        assert '"version": <str>' in schema
        assert '"enabled": <bool>' in schema
        assert '"count": <int>' in schema
    
    def test_json_to_schema_nested(self, compressor):
        """Test JSON to schema conversion for nested objects"""
        data = {
            "config": {
                "database": {
                    "host": "localhost",
                    "port": 5432
                },
                "cache": {
                    "enabled": True,
                    "ttl": 3600
                }
            },
            "items": [1, 2, 3, 4, 5]
        }
        
        schema = compressor._json_to_schema(data, max_depth=3)
        
        assert '"config":' in schema
        assert '"items":' in schema
        assert '"database":' in schema
        assert '"host":' in schema
    
    def test_json_to_schema_array(self, compressor):
        """Test JSON to schema conversion for arrays"""
        data = [
            {"id": 1, "name": "item1"},
            {"id": 2, "name": "item2"}
        ]
        
        schema = compressor._json_to_schema(data, max_depth=2)
        
        assert "[" in schema
        assert '"id": <int>' in schema
        assert "2 items" in schema
    
    def test_json_to_schema_depth_limiting(self, compressor):
        """Test that schema conversion respects depth limits"""
        data = {
            "level1": {
                "level2": {
                    "level3": {
                        "level4": "deep_value"
                    }
                }
            }
        }
        
        # Test with max_depth=2
        schema = compressor._json_to_schema(data, max_depth=2)
        assert "level1" in schema
        assert "level2" in schema
        assert "<dict>" in schema  # level3 should be truncated


class TestConfigFileCompression:
    """Test configuration file compression"""
    
    @pytest.fixture
    def compressor(self):
        """Create compressor for testing"""
        mock_calculator = AsyncMock(spec=TokenCalculator)
        return ContextCompressor(token_calculator=mock_calculator)
    
    @pytest.mark.asyncio
    async def test_compress_config_content(self, compressor):
        """Test configuration file compression"""
        config_content = '''
# Database Configuration
database.host = localhost
database.port = 5432
database.name = testdb

# Cache Configuration  
cache.enabled = true
cache.ttl = 3600
cache.size = 1000

# Logging Configuration
logging.level = INFO
logging.file = app.log
'''
        
        # Test moderate compression
        compressed = await compressor._compress_config_content(
            config_content, CompressionLevel.MODERATE, target_tokens=100
        )
        
        assert "database.host = str" in compressed  # Type substitution
        assert "cache.enabled = bool" in compressed
        assert "# Database Configuration" in compressed  # Preserve section headers
        
        # Test high compression
        compressed = await compressor._compress_config_content(
            config_content, CompressionLevel.HIGH, target_tokens=50
        )
        
        assert "database.host = ..." in compressed
        assert "cache.enabled = ..." in compressed


class TestCompressionAnalysis:
    """Test compression analysis and estimation"""
    
    @pytest.fixture
    def compressor(self):
        """Create compressor for testing"""
        mock_calculator = AsyncMock(spec=TokenCalculator)
        return ContextCompressor(token_calculator=mock_calculator)
    
    @pytest.mark.asyncio
    async def test_estimate_compression_potential(self, compressor):
        """Test compression potential estimation"""
        python_code = '''
import os
class TestClass:
    def method(self):
        pass
'''
        
        compressor.token_calculator.estimate_tokens.return_value = 100
        
        analysis = await compressor.estimate_compression_potential(
            content=python_code,
            file_type=FileType.PYTHON,
            compression_level=CompressionLevel.MODERATE
        )
        
        assert "original_tokens" in analysis
        assert "estimated_compression_ratio" in analysis
        assert "compressible_elements" in analysis
        assert "preservation_notes" in analysis
        assert "estimated_final_tokens" in analysis
        
        assert analysis["file_type"] == "python"
        assert analysis["compression_level"] == "moderate"
        assert analysis["original_tokens"] == 100
    
    @pytest.mark.asyncio
    async def test_analyze_python_compression_potential(self, compressor):
        """Test Python-specific compression analysis"""
        python_code = '''
import os
import sys

class TestClass:
    """Class docstring."""
    def method1(self):
        pass
    def method2(self):
        pass

def function1():
    """Function docstring."""
    pass

def function2():
    pass
'''
        
        analysis = await compressor._analyze_python_compression_potential(
            python_code, CompressionLevel.MODERATE
        )
        
        assert "estimated_compression_ratio" in analysis
        assert "compressible_elements" in analysis
        assert "preservation_notes" in analysis
        
        elements = analysis["compressible_elements"]
        assert any("import" in elem for elem in elements)
        assert any("class" in elem for elem in elements)
        assert any("function" in elem for elem in elements)
    
    @pytest.mark.asyncio
    async def test_analyze_test_compression_potential(self, compressor):
        """Test test file compression analysis"""
        test_code = '''
import pytest

@pytest.fixture
def sample_fixture():
    pass

def test_function1():
    assert True

def test_function2():
    assert False
'''
        
        analysis = await compressor._analyze_test_compression_potential(
            test_code, CompressionLevel.MODERATE
        )
        
        assert "estimated_compression_ratio" in analysis
        assert analysis["estimated_compression_ratio"] <= 1.0
        
        elements = analysis["compressible_elements"]
        assert any("test function" in elem for elem in elements)
        assert any("fixture" in elem for elem in elements)


class TestCodeBlockCompression:
    """Test code block compression functionality"""
    
    @pytest.fixture
    def compressor(self):
        """Create compressor for testing"""
        return ContextCompressor()
    
    @pytest.mark.asyncio
    async def test_compress_python_block(self, compressor):
        """Test Python code block compression"""
        python_code = '''
def example_function():
    """Example function."""
    return "Hello, World!"
'''
        
        compressed = await compressor.compress_code_block(
            code=python_code,
            language="python",
            compression_level=CompressionLevel.MODERATE,
            preserve_imports=True,
            preserve_docstrings=False
        )
        
        assert isinstance(compressed, str)
        assert "def example_function" in compressed
    
    @pytest.mark.asyncio
    async def test_compress_generic_code(self, compressor):
        """Test generic code compression"""
        javascript_code = '''
function exampleFunction() {
    console.log("Hello, World!");
    return true;
}
'''
        
        compressed = await compressor._compress_generic_code(
            javascript_code, CompressionLevel.MODERATE
        )
        
        assert isinstance(compressed, str)
        assert len(compressed) <= len(javascript_code)


class TestPerformanceTracking:
    """Test compression performance tracking"""
    
    @pytest.fixture
    def compressor(self):
        """Create compressor for testing"""
        mock_calculator = AsyncMock(spec=TokenCalculator)
        return ContextCompressor(token_calculator=mock_calculator)
    
    @pytest.mark.asyncio
    async def test_performance_metrics_tracking(self, compressor):
        """Test that performance metrics are tracked"""
        compressor.token_calculator.estimate_tokens.side_effect = [1000, 600]
        
        # Perform compression
        await compressor.compress_content(
            content="test content",
            file_path="test.py",
            file_type=FileType.PYTHON,
            compression_level=CompressionLevel.MODERATE
        )
        
        # Check that metrics were recorded
        assert compressor._compression_operations == 1
        assert compressor._total_compression_time > 0
        assert len(compressor._compression_ratios) == 1
        assert compressor._compression_ratios[0] == 0.6
        
        # Check compression stats
        stats = compressor._compression_stats[CompressionLevel.MODERATE]
        assert stats["count"] == 1
        assert stats["avg_ratio"] == 0.6
    
    def test_get_performance_metrics(self, compressor):
        """Test getting performance metrics"""
        # Simulate some operations
        compressor._compression_operations = 5
        compressor._total_compression_time = 2.5
        compressor._compression_ratios = [0.6, 0.7, 0.5, 0.8, 0.6]
        
        # Update stats for different levels
        compressor._compression_stats[CompressionLevel.LOW]["count"] = 2
        compressor._compression_stats[CompressionLevel.LOW]["avg_ratio"] = 0.75
        compressor._compression_stats[CompressionLevel.MODERATE]["count"] = 3
        compressor._compression_stats[CompressionLevel.MODERATE]["avg_ratio"] = 0.6
        
        metrics = compressor.get_performance_metrics()
        
        assert metrics["total_operations"] == 5
        assert metrics["average_compression_time"] == 0.5  # 2.5/5
        assert metrics["total_compression_time"] == 2.5
        assert metrics["average_compression_ratio"] == 0.64  # Mean of ratios
        assert metrics["min_compression_ratio"] == 0.5
        assert metrics["max_compression_ratio"] == 0.8
        assert "compression_stats_by_level" in metrics
    
    def test_update_compression_stats(self, compressor):
        """Test compression statistics update"""
        # Test first update
        compressor._update_compression_stats(CompressionLevel.LOW, 0.8)
        
        stats = compressor._compression_stats[CompressionLevel.LOW]
        assert stats["count"] == 1
        assert stats["avg_ratio"] == 0.8
        
        # Test second update (should average)
        compressor._update_compression_stats(CompressionLevel.LOW, 0.6)
        
        stats = compressor._compression_stats[CompressionLevel.LOW]
        assert stats["count"] == 2
        assert stats["avg_ratio"] == 0.7  # (0.8 + 0.6) / 2


class TestContentTruncation:
    """Test content truncation functionality"""
    
    @pytest.fixture
    def compressor(self):
        """Create compressor for testing"""
        mock_calculator = AsyncMock(spec=TokenCalculator)
        return ContextCompressor(token_calculator=mock_calculator)
    
    @pytest.mark.asyncio
    async def test_truncate_to_tokens(self, compressor):
        """Test content truncation to token limit"""
        long_content = "This is a very long piece of content. " * 100
        
        compressor.token_calculator.estimate_tokens.return_value = 200  # Exceeds target
        
        truncated = await compressor._truncate_to_tokens(long_content, target_tokens=50)
        
        assert len(truncated) < len(long_content)
        assert "[content truncated to fit token budget]" in truncated
    
    @pytest.mark.asyncio
    async def test_truncate_at_line_boundary(self, compressor):
        """Test that truncation prefers line boundaries"""
        content = "Line 1\nLine 2\nLine 3\nLine 4\nLine 5\n" * 10
        
        compressor.token_calculator.estimate_tokens.return_value = 200
        
        truncated = await compressor._truncate_to_tokens(content, target_tokens=50)
        
        # Should break at newline if possible
        assert truncated.count('\n') >= 1
        assert "[content truncated to fit token budget]" in truncated


class TestErrorHandling:
    """Test error handling in compression"""
    
    @pytest.fixture
    def compressor(self):
        """Create compressor for testing"""
        return ContextCompressor()
    
    @pytest.mark.asyncio
    async def test_invalid_python_syntax(self, compressor):
        """Test handling of invalid Python syntax"""
        invalid_python = '''
def invalid_function(
    # Missing closing parenthesis and colon
    pass
'''
        
        # Should fall back to text compression
        compressed, ratio = await compressor.compress_content(
            content=invalid_python,
            file_path="invalid.py",
            file_type=FileType.PYTHON,
            compression_level=CompressionLevel.MODERATE
        )
        
        # Should not raise exception, should return some form of compressed content
        assert isinstance(compressed, str)
        assert isinstance(ratio, float)
    
    @pytest.mark.asyncio
    async def test_invalid_json_content(self, compressor):
        """Test handling of invalid JSON"""
        invalid_json = '''
{
    "key1": "value1",
    "key2": value2,  // Invalid: unquoted value
    "key3": 
}
'''
        
        # Should fall back to text compression
        compressed, ratio = await compressor.compress_content(
            content=invalid_json,
            file_path="invalid.json",
            file_type=FileType.JSON,
            compression_level=CompressionLevel.MODERATE
        )
        
        assert isinstance(compressed, str)
        assert isinstance(ratio, float)
    
    @pytest.mark.asyncio
    async def test_empty_content_handling(self, compressor):
        """Test handling of empty content"""
        compressed, ratio = await compressor.compress_content(
            content="",
            file_path="empty.py",
            file_type=FileType.PYTHON,
            compression_level=CompressionLevel.MODERATE
        )
        
        assert compressed == ""
        assert ratio == 1.0  # No compression possible/needed


@pytest.mark.asyncio
async def test_compression_levels_consistency():
    """Test that all compression levels work consistently"""
    compressor = ContextCompressor()
    
    sample_code = '''
import os
import sys

class SampleClass:
    """Sample class for testing."""
    
    def __init__(self):
        self.value = 0
    
    def method1(self):
        """First method."""
        return self.value
    
    def method2(self, param):
        """Second method."""
        self.value = param
        return param * 2

def standalone_function():
    """Standalone function."""
    return "result"
'''
    
    # Test all compression levels
    ratios = {}
    for level in CompressionLevel:
        compressed, ratio = await compressor.compress_content(
            content=sample_code,
            file_path="test.py",
            file_type=FileType.PYTHON,
            compression_level=level
        )
        ratios[level] = ratio
        
        # Ensure all return valid results
        assert isinstance(compressed, str)
        assert isinstance(ratio, float)
        assert 0.0 <= ratio <= 1.0
    
    # Generally, higher compression levels should yield better ratios
    # (though this isn't strictly guaranteed for all content types)
    assert ratios[CompressionLevel.LOW] >= ratios[CompressionLevel.MODERATE] or abs(ratios[CompressionLevel.LOW] - ratios[CompressionLevel.MODERATE]) < 0.1