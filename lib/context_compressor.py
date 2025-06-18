"""
Context Compressor - Intelligent Content Compression System

Intelligent compression of code and documentation while preserving semantic meaning.
Implements specialized compression strategies for different content types:
- AST-based Python code compression with dependency preservation
- Test file compression maintaining assertions and fixture relationships  
- Documentation summarization with key information retention
- JSON/YAML structure simplification with schema preservation
"""

import ast
import json
import re
import logging
from typing import Dict, List, Optional, Set, Any, Tuple, Union
from pathlib import Path
from datetime import datetime

try:
    from .context.models import (
        CompressionLevel,
        FileType,
        TokenUsage,
        ContextRequest
    )
    from .token_calculator import TokenCalculator
except ImportError:
    from context.models import (
        CompressionLevel,
        FileType,
        TokenUsage,
        ContextRequest
    )
    from token_calculator import TokenCalculator

logger = logging.getLogger(__name__)


class ContextCompressor:
    """
    Intelligent content compression preserving semantic meaning.
    
    Provides specialized compression strategies:
    - Python: AST-based compression preserving structure and dependencies
    - Test: Assertion-focused compression maintaining test logic
    - Documentation: Summary-based compression retaining key concepts
    - Data: Structure-preserving compression for JSON/YAML/Config files
    """
    
    def __init__(self, token_calculator: Optional[TokenCalculator] = None):
        """
        Initialize ContextCompressor.
        
        Args:
            token_calculator: Token calculator for measuring compression effectiveness
        """
        self.token_calculator = token_calculator or TokenCalculator()
        
        # Performance tracking
        self._compression_operations = 0
        self._total_compression_time = 0.0
        self._compression_ratios = []
        
        # Compression statistics by level
        self._compression_stats = {
            CompressionLevel.LOW: {"count": 0, "avg_ratio": 0.0},
            CompressionLevel.MODERATE: {"count": 0, "avg_ratio": 0.0},
            CompressionLevel.HIGH: {"count": 0, "avg_ratio": 0.0},
            CompressionLevel.EXTREME: {"count": 0, "avg_ratio": 0.0}
        }
        
        logger.info("ContextCompressor initialized")
    
    async def compress_content(
        self,
        content: str,
        file_path: str,
        file_type: FileType,
        compression_level: CompressionLevel,
        target_tokens: Optional[int] = None,
        preserve_structure: bool = True
    ) -> Tuple[str, float]:
        """
        Compress content intelligently based on file type and compression level.
        
        Args:
            content: Original content to compress
            file_path: Path to the file for context
            file_type: Type of file for specialized compression
            compression_level: Level of compression to apply
            target_tokens: Target token count (optional)
            preserve_structure: Whether to preserve logical structure
            
        Returns:
            Tuple of (compressed_content, compression_ratio)
        """
        start_time = datetime.now()
        
        try:
            original_tokens = await self.token_calculator.estimate_tokens(content)
            
            if original_tokens == 0:
                return content, 1.0
            
            # Apply compression based on file type
            if file_type == FileType.PYTHON:
                compressed = await self._compress_python_content(
                    content, compression_level, target_tokens, preserve_structure
                )
            elif file_type == FileType.TEST:
                compressed = await self._compress_test_content(
                    content, compression_level, target_tokens, preserve_structure
                )
            elif file_type == FileType.MARKDOWN:
                compressed = await self._compress_markdown_content(
                    content, compression_level, target_tokens
                )
            elif file_type == FileType.JSON:
                compressed = await self._compress_json_content(
                    content, compression_level, target_tokens
                )
            elif file_type in [FileType.YAML, FileType.CONFIG]:
                compressed = await self._compress_config_content(
                    content, compression_level, target_tokens
                )
            else:
                # Fallback to text compression
                compressed = await self._compress_text_content(
                    content, compression_level, target_tokens
                )
            
            # Calculate compression ratio
            compressed_tokens = await self.token_calculator.estimate_tokens(compressed)
            compression_ratio = compressed_tokens / original_tokens if original_tokens > 0 else 1.0
            
            # Track performance
            elapsed = (datetime.now() - start_time).total_seconds()
            self._total_compression_time += elapsed
            self._compression_operations += 1
            self._compression_ratios.append(compression_ratio)
            
            # Update compression level statistics
            self._update_compression_stats(compression_level, compression_ratio)
            
            logger.debug(
                f"Compressed {file_type.value} content: {original_tokens} -> {compressed_tokens} tokens "
                f"(ratio: {compression_ratio:.3f}, level: {compression_level.value})"
            )
            
            return compressed, compression_ratio
            
        except Exception as e:
            logger.error(f"Error compressing content for {file_path}: {str(e)}")
            return content, 1.0
    
    async def compress_code_block(
        self,
        code: str,
        language: str,
        compression_level: CompressionLevel,
        preserve_imports: bool = True,
        preserve_docstrings: bool = False
    ) -> str:
        """
        Compress a specific code block with fine-grained control.
        
        Args:
            code: Code to compress
            language: Programming language
            compression_level: Level of compression
            preserve_imports: Whether to preserve import statements
            preserve_docstrings: Whether to preserve docstrings
            
        Returns:
            Compressed code
        """
        if language.lower() == 'python':
            return await self._compress_python_block(
                code, compression_level, preserve_imports, preserve_docstrings
            )
        else:
            # Generic code compression
            return await self._compress_generic_code(code, compression_level)
    
    async def estimate_compression_potential(
        self,
        content: str,
        file_type: FileType,
        compression_level: CompressionLevel
    ) -> Dict[str, Any]:
        """
        Estimate compression potential without actually compressing.
        
        Args:
            content: Content to analyze
            file_type: Type of file
            compression_level: Target compression level
            
        Returns:
            Dictionary with compression analysis
        """
        original_tokens = await self.token_calculator.estimate_tokens(content)
        
        # Estimate compression ratios based on content characteristics
        analysis = {
            "original_tokens": original_tokens,
            "file_type": file_type.value,
            "compression_level": compression_level.value,
            "estimated_compression_ratio": 1.0,
            "compressible_elements": [],
            "preservation_notes": []
        }
        
        if file_type == FileType.PYTHON:
            analysis.update(await self._analyze_python_compression_potential(content, compression_level))
        elif file_type == FileType.TEST:
            analysis.update(await self._analyze_test_compression_potential(content, compression_level))
        elif file_type == FileType.MARKDOWN:
            analysis.update(await self._analyze_markdown_compression_potential(content, compression_level))
        elif file_type == FileType.JSON:
            analysis.update(await self._analyze_json_compression_potential(content, compression_level))
        
        analysis["estimated_final_tokens"] = int(original_tokens * analysis["estimated_compression_ratio"])
        
        return analysis
    
    # Python-specific compression methods
    
    async def _compress_python_content(
        self,
        content: str,
        compression_level: CompressionLevel,
        target_tokens: Optional[int] = None,
        preserve_structure: bool = True
    ) -> str:
        """Compress Python content using AST analysis"""
        try:
            tree = ast.parse(content)
            
            # Extract components for selective compression
            imports = await self._extract_imports(tree, content)
            classes = await self._extract_classes(tree, content)
            functions = await self._extract_functions(tree, content)
            constants = await self._extract_constants(tree, content)
            
            compressed_parts = []
            
            # Always preserve imports (they're usually essential)
            if imports:
                compressed_parts.append("# Imports")
                compressed_parts.append(imports)
                compressed_parts.append("")
            
            # Add constants if present
            if constants and compression_level != CompressionLevel.EXTREME:
                compressed_parts.append("# Constants")
                compressed_parts.append(constants)
                compressed_parts.append("")
            
            # Compress classes based on level
            for class_info in classes:
                compressed_class = await self._compress_python_class(
                    class_info, compression_level, preserve_structure
                )
                if compressed_class:
                    compressed_parts.append(compressed_class)
                    compressed_parts.append("")
            
            # Compress functions based on level
            for func_info in functions:
                compressed_func = await self._compress_python_function(
                    func_info, compression_level, preserve_structure
                )
                if compressed_func:
                    compressed_parts.append(compressed_func)
                    compressed_parts.append("")
            
            result = "\n".join(compressed_parts).strip()
            
            # Apply target token limit if specified
            if target_tokens:
                result = await self._truncate_to_tokens(result, target_tokens)
            
            return result
            
        except SyntaxError:
            # Fallback to text compression for invalid Python
            return await self._compress_text_content(content, compression_level, target_tokens)
        except Exception as e:
            logger.warning(f"Error in Python compression: {str(e)}")
            return await self._compress_text_content(content, compression_level, target_tokens)
    
    async def _compress_python_class(
        self,
        class_info: Dict[str, Any],
        compression_level: CompressionLevel,
        preserve_structure: bool
    ) -> str:
        """Compress a Python class definition"""
        name = class_info['name']
        content = class_info['content']
        methods = class_info.get('methods', [])
        
        if compression_level == CompressionLevel.LOW:
            # Light compression: remove empty lines and comments
            return self._remove_empty_lines_and_comments(content)
        
        elif compression_level == CompressionLevel.MODERATE:
            # Moderate compression: compress method bodies but preserve signatures
            compressed_methods = []
            for method in methods:
                signature = method.get('signature', '')
                if signature:
                    compressed_methods.append(signature + ":")
                    compressed_methods.append("    pass  # [compressed]")
                    compressed_methods.append("")
            
            if compressed_methods:
                return f"class {name}:\n    " + "\n    ".join(compressed_methods)
            else:
                return f"class {name}:\n    pass  # [compressed]"
        
        elif compression_level in [CompressionLevel.HIGH, CompressionLevel.EXTREME]:
            # High compression: class signature only
            return f"class {name}:\n    pass  # [compressed - {len(methods)} methods]"
        
        return content
    
    async def _compress_python_function(
        self,
        func_info: Dict[str, Any],
        compression_level: CompressionLevel,
        preserve_structure: bool
    ) -> str:
        """Compress a Python function definition"""
        name = func_info['name']
        signature = func_info.get('signature', f"def {name}()")
        content = func_info['content']
        docstring = func_info.get('docstring', '')
        
        if compression_level == CompressionLevel.LOW:
            # Light compression: preserve signature and docstring, compress body
            parts = [signature + ":"]
            if docstring and len(docstring) < 200:
                parts.append(f'    """{docstring}"""')
            parts.append("    pass  # [body compressed]")
            return "\n".join(parts)
        
        elif compression_level == CompressionLevel.MODERATE:
            # Moderate compression: signature and brief docstring
            parts = [signature + ":"]
            if docstring:
                brief_doc = docstring.split('\n')[0][:100]
                parts.append(f'    """{brief_doc}"""')
            parts.append("    pass  # [compressed]")
            return "\n".join(parts)
        
        elif compression_level in [CompressionLevel.HIGH, CompressionLevel.EXTREME]:
            # High compression: signature only
            return f"{signature}:\n    pass  # [compressed]"
        
        return content
    
    async def _compress_test_content(
        self,
        content: str,
        compression_level: CompressionLevel,
        target_tokens: Optional[int] = None,
        preserve_structure: bool = True
    ) -> str:
        """Compress test content preserving test logic and assertions"""
        try:
            tree = ast.parse(content)
            
            imports = await self._extract_imports(tree, content)
            test_classes = []
            test_functions = []
            fixtures = []
            
            # Identify test components
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    if node.name.startswith('test_'):
                        test_functions.append(await self._extract_test_function(node, content))
                    elif any(decorator.id == 'fixture' for decorator in node.decorator_list 
                           if isinstance(decorator, ast.Name)):
                        fixtures.append(await self._extract_fixture(node, content))
                elif isinstance(node, ast.ClassDef) and 'test' in node.name.lower():
                    test_classes.append(await self._extract_test_class(node, content))
            
            compressed_parts = []
            
            # Always preserve imports and fixtures
            if imports:
                compressed_parts.append("# Imports")
                compressed_parts.append(imports)
                compressed_parts.append("")
            
            if fixtures:
                compressed_parts.append("# Fixtures")
                for fixture in fixtures:
                    compressed_parts.append(await self._compress_test_fixture(fixture, compression_level))
                    compressed_parts.append("")
            
            # Compress test classes
            for test_class in test_classes:
                compressed_class = await self._compress_test_class(test_class, compression_level)
                if compressed_class:
                    compressed_parts.append(compressed_class)
                    compressed_parts.append("")
            
            # Compress test functions
            for test_func in test_functions:
                compressed_func = await self._compress_test_function(test_func, compression_level)
                if compressed_func:
                    compressed_parts.append(compressed_func)
                    compressed_parts.append("")
            
            result = "\n".join(compressed_parts).strip()
            
            if target_tokens:
                result = await self._truncate_to_tokens(result, target_tokens)
            
            return result
            
        except Exception as e:
            logger.warning(f"Error in test compression: {str(e)}")
            return await self._compress_text_content(content, compression_level, target_tokens)
    
    async def _compress_test_function(
        self,
        func_info: Dict[str, Any],
        compression_level: CompressionLevel
    ) -> str:
        """Compress test function preserving test logic"""
        name = func_info['name']
        signature = func_info.get('signature', f"def {name}()")
        assertions = func_info.get('assertions', [])
        
        if compression_level == CompressionLevel.LOW:
            # Preserve test structure with simplified body
            parts = [signature + ":"]
            parts.append("    # Test setup")
            parts.append("    # [setup code compressed]")
            parts.append("")
            for assertion in assertions[:3]:  # Keep first 3 assertions
                parts.append(f"    {assertion}")
            if len(assertions) > 3:
                parts.append(f"    # ... {len(assertions) - 3} more assertions")
            return "\n".join(parts)
        
        elif compression_level == CompressionLevel.MODERATE:
            # Keep signature and key assertions
            parts = [signature + ":"]
            if assertions:
                parts.append(f"    # {len(assertions)} assertions")
                for assertion in assertions[:2]:  # Keep first 2 assertions
                    parts.append(f"    {assertion}")
                if len(assertions) > 2:
                    parts.append(f"    # ... {len(assertions) - 2} more assertions")
            else:
                parts.append("    pass  # [test compressed]")
            return "\n".join(parts)
        
        else:  # HIGH or EXTREME
            # Signature only with assertion count
            assertion_count = len(assertions)
            return f"{signature}:\n    pass  # [test with {assertion_count} assertions]"
    
    async def _compress_markdown_content(
        self,
        content: str,
        compression_level: CompressionLevel,
        target_tokens: Optional[int] = None
    ) -> str:
        """Compress markdown content preserving structure and key information"""
        lines = content.split('\n')
        compressed_lines = []
        
        current_section = ""
        section_content = []
        
        for line in lines:
            if line.startswith('#'):
                # Process previous section
                if current_section and section_content:
                    compressed_section = await self._compress_markdown_section(
                        current_section, section_content, compression_level
                    )
                    compressed_lines.extend(compressed_section)
                
                # Start new section
                current_section = line
                section_content = []
            else:
                section_content.append(line)
        
        # Process final section
        if current_section and section_content:
            compressed_section = await self._compress_markdown_section(
                current_section, section_content, compression_level
            )
            compressed_lines.extend(compressed_section)
        
        result = '\n'.join(compressed_lines)
        
        if target_tokens:
            result = await self._truncate_to_tokens(result, target_tokens)
        
        return result
    
    async def _compress_markdown_section(
        self,
        header: str,
        content: List[str],
        compression_level: CompressionLevel
    ) -> List[str]:
        """Compress a markdown section"""
        result = [header]
        
        if compression_level == CompressionLevel.LOW:
            # Light compression: remove empty lines
            result.extend([line for line in content if line.strip()])
        
        elif compression_level == CompressionLevel.MODERATE:
            # Moderate compression: summarize paragraphs
            paragraphs = []
            current_paragraph = []
            
            for line in content:
                if line.strip():
                    current_paragraph.append(line)
                else:
                    if current_paragraph:
                        paragraphs.append(' '.join(current_paragraph))
                        current_paragraph = []
            
            if current_paragraph:
                paragraphs.append(' '.join(current_paragraph))
            
            # Keep first sentence of each paragraph
            for paragraph in paragraphs:
                sentences = paragraph.split('.')
                if sentences:
                    result.append(sentences[0] + '.')
        
        else:  # HIGH or EXTREME
            # High compression: header only with content summary
            content_text = ' '.join(content)
            word_count = len(content_text.split())
            result.append(f"[{word_count} words of content compressed]")
        
        result.append("")  # Add spacing
        return result
    
    async def _compress_json_content(
        self,
        content: str,
        compression_level: CompressionLevel,
        target_tokens: Optional[int] = None
    ) -> str:
        """Compress JSON content preserving structure"""
        try:
            data = json.loads(content)
            
            if compression_level == CompressionLevel.LOW:
                # Compact formatting
                return json.dumps(data, separators=(',', ':'))
            
            elif compression_level == CompressionLevel.MODERATE:
                # Structure with type hints
                return self._json_to_schema(data, max_depth=3)
            
            else:  # HIGH or EXTREME
                # Schema only
                return self._json_to_schema(data, max_depth=1)
                
        except json.JSONDecodeError:
            # Fallback to text compression
            return await self._compress_text_content(content, compression_level, target_tokens)
    
    async def _compress_config_content(
        self,
        content: str,
        compression_level: CompressionLevel,
        target_tokens: Optional[int] = None
    ) -> str:
        """Compress configuration file content"""
        lines = content.split('\n')
        compressed_lines = []
        
        for line in lines:
            stripped = line.strip()
            
            # Always keep non-comment, non-empty lines
            if stripped and not stripped.startswith('#'):
                if compression_level == CompressionLevel.LOW:
                    compressed_lines.append(line)
                elif compression_level == CompressionLevel.MODERATE:
                    # Keep setting name and type
                    if '=' in stripped:
                        key, value = stripped.split('=', 1)
                        compressed_lines.append(f"{key.strip()} = {type(value.strip()).__name__}")
                    else:
                        compressed_lines.append(stripped)
                else:  # HIGH or EXTREME
                    # Keep only setting names
                    if '=' in stripped:
                        key = stripped.split('=', 1)[0]
                        compressed_lines.append(f"{key.strip()} = ...")
                    else:
                        compressed_lines.append(stripped)
            
            # Preserve section headers in comments
            elif stripped.startswith('#') and len(stripped) > 10:
                if compression_level != CompressionLevel.EXTREME:
                    compressed_lines.append(line)
        
        result = '\n'.join(compressed_lines)
        
        if target_tokens:
            result = await self._truncate_to_tokens(result, target_tokens)
        
        return result
    
    async def _compress_text_content(
        self,
        content: str,
        compression_level: CompressionLevel,
        target_tokens: Optional[int] = None
    ) -> str:
        """Generic text compression"""
        if compression_level == CompressionLevel.LOW:
            # Remove extra whitespace and empty lines
            lines = [line.strip() for line in content.split('\n') if line.strip()]
            return '\n'.join(lines)
        
        elif compression_level == CompressionLevel.MODERATE:
            # Keep first sentence of each paragraph
            paragraphs = content.split('\n\n')
            compressed_paragraphs = []
            
            for paragraph in paragraphs:
                sentences = paragraph.split('.')
                if sentences:
                    compressed_paragraphs.append(sentences[0] + '.')
            
            return '\n\n'.join(compressed_paragraphs)
        
        else:  # HIGH or EXTREME
            # First paragraph only
            first_paragraph = content.split('\n\n')[0] if content else ""
            if compression_level == CompressionLevel.EXTREME:
                # First sentence of first paragraph
                sentences = first_paragraph.split('.')
                return sentences[0] + '.' if sentences else ""
            return first_paragraph
    
    # Helper methods for AST analysis
    
    async def _extract_imports(self, tree: ast.AST, content: str) -> str:
        """Extract import statements"""
        imports = []
        for node in ast.walk(tree):
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                import_line = ast.get_source_segment(content, node)
                if import_line:
                    imports.append(import_line)
        return '\n'.join(imports)
    
    async def _extract_classes(self, tree: ast.AST, content: str) -> List[Dict[str, Any]]:
        """Extract class definitions with metadata"""
        classes = []
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                class_content = ast.get_source_segment(content, node)
                methods = []
                
                for method_node in node.body:
                    if isinstance(method_node, ast.FunctionDef):
                        method_sig = f"def {method_node.name}({', '.join(arg.arg for arg in method_node.args.args)})"
                        methods.append({
                            'name': method_node.name,
                            'signature': method_sig
                        })
                
                classes.append({
                    'name': node.name,
                    'content': class_content,
                    'methods': methods
                })
        
        return classes
    
    async def _extract_functions(self, tree: ast.AST, content: str) -> List[Dict[str, Any]]:
        """Extract function definitions with metadata"""
        functions = []
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and not self._is_method(node, tree):
                func_content = ast.get_source_segment(content, node)
                signature = f"def {node.name}({', '.join(arg.arg for arg in node.args.args)})"
                
                # Extract docstring
                docstring = ""
                if (node.body and isinstance(node.body[0], ast.Expr) and
                    isinstance(node.body[0].value, ast.Constant) and
                    isinstance(node.body[0].value.value, str)):
                    docstring = node.body[0].value.value
                
                functions.append({
                    'name': node.name,
                    'content': func_content,
                    'signature': signature,
                    'docstring': docstring
                })
        
        return functions
    
    async def _extract_constants(self, tree: ast.AST, content: str) -> str:
        """Extract module-level constants"""
        constants = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Assign):
                assign_content = ast.get_source_segment(content, node)
                if assign_content and self._is_constant_assignment(node):
                    constants.append(assign_content)
        
        return '\n'.join(constants)
    
    def _is_method(self, node: ast.FunctionDef, tree: ast.AST) -> bool:
        """Check if function is a method inside a class"""
        for parent in ast.walk(tree):
            if isinstance(parent, ast.ClassDef) and node in parent.body:
                return True
        return False
    
    def _is_constant_assignment(self, node: ast.Assign) -> bool:
        """Check if assignment is a constant (uppercase variable)"""
        if len(node.targets) == 1 and isinstance(node.targets[0], ast.Name):
            return node.targets[0].id.isupper()
        return False
    
    async def _extract_test_function(self, node: ast.FunctionDef, content: str) -> Dict[str, Any]:
        """Extract test function with assertions"""
        func_content = ast.get_source_segment(content, node)
        signature = f"def {node.name}({', '.join(arg.arg for arg in node.args.args)})"
        
        # Extract assertions
        assertions = []
        for stmt in ast.walk(node):
            if isinstance(stmt, ast.Assert):
                assert_content = ast.get_source_segment(content, stmt)
                if assert_content:
                    assertions.append(assert_content)
            elif isinstance(stmt, ast.Expr) and isinstance(stmt.value, ast.Call):
                # Look for assert method calls
                if (isinstance(stmt.value.func, ast.Attribute) and 
                    stmt.value.func.attr.startswith('assert')):
                    assert_content = ast.get_source_segment(content, stmt)
                    if assert_content:
                        assertions.append(assert_content)
        
        return {
            'name': node.name,
            'content': func_content,
            'signature': signature,
            'assertions': assertions
        }
    
    async def _extract_fixture(self, node: ast.FunctionDef, content: str) -> Dict[str, Any]:
        """Extract pytest fixture"""
        func_content = ast.get_source_segment(content, node)
        signature = f"def {node.name}({', '.join(arg.arg for arg in node.args.args)})"
        
        return {
            'name': node.name,
            'content': func_content,
            'signature': signature,
            'type': 'fixture'
        }
    
    async def _extract_test_class(self, node: ast.ClassDef, content: str) -> Dict[str, Any]:
        """Extract test class with test methods"""
        class_content = ast.get_source_segment(content, node)
        test_methods = []
        
        for method_node in node.body:
            if isinstance(method_node, ast.FunctionDef) and method_node.name.startswith('test_'):
                test_methods.append(await self._extract_test_function(method_node, content))
        
        return {
            'name': node.name,
            'content': class_content,
            'test_methods': test_methods
        }
    
    async def _compress_test_fixture(
        self,
        fixture_info: Dict[str, Any],
        compression_level: CompressionLevel
    ) -> str:
        """Compress test fixture"""
        name = fixture_info['name']
        signature = fixture_info['signature']
        
        if compression_level == CompressionLevel.LOW:
            return f"@pytest.fixture\n{signature}:\n    pass  # [fixture compressed]"
        else:
            return f"@pytest.fixture\n{signature}:\n    pass  # [fixture]"
    
    async def _compress_test_class(
        self,
        class_info: Dict[str, Any],
        compression_level: CompressionLevel
    ) -> str:
        """Compress test class"""
        name = class_info['name']
        test_methods = class_info.get('test_methods', [])
        
        if compression_level == CompressionLevel.LOW:
            # Preserve class structure with compressed methods
            parts = [f"class {name}:"]
            for method in test_methods:
                compressed_method = await self._compress_test_function(method, compression_level)
                parts.append("    " + compressed_method.replace('\n', '\n    '))
            return '\n'.join(parts)
        else:
            # Class signature with method count
            method_count = len(test_methods)
            return f"class {name}:\n    pass  # [test class with {method_count} methods]"
    
    def _json_to_schema(self, data: Any, max_depth: int, current_depth: int = 0) -> str:
        """Convert JSON data to schema representation"""
        if current_depth >= max_depth:
            return f"<{type(data).__name__}>"
        
        if isinstance(data, dict):
            if not data:
                return "{}"
            
            items = []
            for key, value in list(data.items())[:5]:  # Limit to first 5 items
                value_schema = self._json_to_schema(value, max_depth, current_depth + 1)
                items.append(f'"{key}": {value_schema}')
            
            if len(data) > 5:
                items.append(f'"...": "<{len(data) - 5} more items>"')
            
            return "{\n" + ",\n".join(f"  {item}" for item in items) + "\n}"
        
        elif isinstance(data, list):
            if not data:
                return "[]"
            
            if len(data) == 1:
                item_schema = self._json_to_schema(data[0], max_depth, current_depth + 1)
                return f"[{item_schema}]"
            else:
                item_schema = self._json_to_schema(data[0], max_depth, current_depth + 1)
                return f"[{item_schema}, ... ({len(data)} items)]"
        
        else:
            return f"<{type(data).__name__}>"
    
    def _remove_empty_lines_and_comments(self, content: str) -> str:
        """Remove empty lines and comments from code"""
        lines = []
        for line in content.split('\n'):
            stripped = line.strip()
            if stripped and not stripped.startswith('#'):
                lines.append(line)
        return '\n'.join(lines)
    
    async def _truncate_to_tokens(self, content: str, target_tokens: int) -> str:
        """Truncate content to fit within token limit"""
        current_tokens = await self.token_calculator.estimate_tokens(content)
        
        if current_tokens <= target_tokens:
            return content
        
        # Estimate characters per token
        chars_per_token = len(content) / current_tokens if current_tokens > 0 else 4
        target_chars = int(target_tokens * chars_per_token)
        
        if target_chars >= len(content):
            return content
        
        truncated = content[:target_chars]
        
        # Try to break at line boundary
        last_newline = truncated.rfind('\n')
        if last_newline > target_chars * 0.8:
            truncated = truncated[:last_newline]
        
        return truncated + "\n# ... [content truncated to fit token budget]"
    
    # Compression analysis methods
    
    async def _analyze_python_compression_potential(
        self,
        content: str,
        compression_level: CompressionLevel
    ) -> Dict[str, Any]:
        """Analyze Python code compression potential"""
        try:
            tree = ast.parse(content)
            
            # Count different elements
            imports = sum(1 for node in ast.walk(tree) if isinstance(node, (ast.Import, ast.ImportFrom)))
            classes = sum(1 for node in ast.walk(tree) if isinstance(node, ast.ClassDef))
            functions = sum(1 for node in ast.walk(tree) if isinstance(node, ast.FunctionDef))
            docstrings = sum(1 for node in ast.walk(tree) 
                           if isinstance(node, ast.Expr) and isinstance(node.value, ast.Constant))
            
            # Estimate compression ratios based on level
            if compression_level == CompressionLevel.LOW:
                ratio = 0.8  # Remove comments and empty lines
            elif compression_level == CompressionLevel.MODERATE:
                ratio = 0.6  # Compress function bodies
            elif compression_level == CompressionLevel.HIGH:
                ratio = 0.4  # Signatures only
            else:  # EXTREME
                ratio = 0.2  # Minimal structure
            
            return {
                "estimated_compression_ratio": ratio,
                "compressible_elements": [
                    f"{imports} import statements",
                    f"{classes} classes",
                    f"{functions} functions",
                    f"{docstrings} docstrings"
                ],
                "preservation_notes": [
                    "Import statements will be preserved",
                    "Class and function signatures will be preserved",
                    "Docstrings may be summarized or removed"
                ]
            }
            
        except SyntaxError:
            return {
                "estimated_compression_ratio": 0.7,
                "compressible_elements": ["Invalid Python syntax - text compression only"],
                "preservation_notes": ["Fallback to text compression"]
            }
    
    async def _analyze_test_compression_potential(
        self,
        content: str,
        compression_level: CompressionLevel
    ) -> Dict[str, Any]:
        """Analyze test code compression potential"""
        try:
            tree = ast.parse(content)
            
            test_functions = sum(1 for node in ast.walk(tree) 
                               if isinstance(node, ast.FunctionDef) and node.name.startswith('test_'))
            fixtures = sum(1 for node in ast.walk(tree)
                          if isinstance(node, ast.FunctionDef) and 
                          any(getattr(d, 'id', '') == 'fixture' for d in node.decorator_list))
            assertions = sum(1 for node in ast.walk(tree) if isinstance(node, ast.Assert))
            
            # Test compression is more conservative
            if compression_level == CompressionLevel.LOW:
                ratio = 0.7
            elif compression_level == CompressionLevel.MODERATE:
                ratio = 0.5
            else:
                ratio = 0.3
            
            return {
                "estimated_compression_ratio": ratio,
                "compressible_elements": [
                    f"{test_functions} test functions",
                    f"{fixtures} fixtures",
                    f"{assertions} assertions"
                ],
                "preservation_notes": [
                    "Test signatures will be preserved",
                    "Key assertions will be preserved",
                    "Fixtures will be preserved"
                ]
            }
            
        except SyntaxError:
            return {
                "estimated_compression_ratio": 0.6,
                "compressible_elements": ["Invalid Python syntax in test file"],
                "preservation_notes": ["Fallback to text compression"]
            }
    
    async def _analyze_markdown_compression_potential(
        self,
        content: str,
        compression_level: CompressionLevel
    ) -> Dict[str, Any]:
        """Analyze markdown compression potential"""
        lines = content.split('\n')
        headers = sum(1 for line in lines if line.strip().startswith('#'))
        paragraphs = len([p for p in content.split('\n\n') if p.strip()])
        
        if compression_level == CompressionLevel.LOW:
            ratio = 0.8
        elif compression_level == CompressionLevel.MODERATE:
            ratio = 0.5
        else:
            ratio = 0.3
        
        return {
            "estimated_compression_ratio": ratio,
            "compressible_elements": [
                f"{headers} headers",
                f"{paragraphs} paragraphs"
            ],
            "preservation_notes": [
                "Headers will be preserved",
                "Key sentences will be preserved",
                "Structure will be maintained"
            ]
        }
    
    async def _analyze_json_compression_potential(
        self,
        content: str,
        compression_level: CompressionLevel
    ) -> Dict[str, Any]:
        """Analyze JSON compression potential"""
        try:
            data = json.loads(content)
            
            def count_elements(obj, depth=0):
                if isinstance(obj, dict):
                    return 1 + sum(count_elements(v, depth+1) for v in obj.values())
                elif isinstance(obj, list):
                    return 1 + sum(count_elements(item, depth+1) for item in obj)
                else:
                    return 1
            
            total_elements = count_elements(data)
            
            if compression_level == CompressionLevel.LOW:
                ratio = 0.7  # Compact formatting
            elif compression_level == CompressionLevel.MODERATE:
                ratio = 0.4  # Schema with some values
            else:
                ratio = 0.2  # Schema only
            
            return {
                "estimated_compression_ratio": ratio,
                "compressible_elements": [
                    f"{total_elements} JSON elements",
                    "Nested structure" if isinstance(data, (dict, list)) else "Simple value"
                ],
                "preservation_notes": [
                    "Structure will be preserved",
                    "Data types will be indicated",
                    "Schema will be maintained"
                ]
            }
            
        except json.JSONDecodeError:
            return {
                "estimated_compression_ratio": 0.8,
                "compressible_elements": ["Invalid JSON - text compression"],
                "preservation_notes": ["Fallback to text compression"]
            }
    
    def _update_compression_stats(self, level: CompressionLevel, ratio: float) -> None:
        """Update compression statistics"""
        stats = self._compression_stats[level]
        stats["count"] += 1
        stats["avg_ratio"] = (stats["avg_ratio"] * (stats["count"] - 1) + ratio) / stats["count"]
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get compression performance metrics"""
        avg_compression_time = (
            self._total_compression_time / self._compression_operations
            if self._compression_operations > 0 else 0.0
        )
        
        avg_compression_ratio = (
            sum(self._compression_ratios) / len(self._compression_ratios)
            if self._compression_ratios else 1.0
        )
        
        return {
            "total_operations": self._compression_operations,
            "average_compression_time": avg_compression_time,
            "total_compression_time": self._total_compression_time,
            "average_compression_ratio": avg_compression_ratio,
            "min_compression_ratio": min(self._compression_ratios) if self._compression_ratios else 1.0,
            "max_compression_ratio": max(self._compression_ratios) if self._compression_ratios else 1.0,
            "compression_stats_by_level": self._compression_stats
        }