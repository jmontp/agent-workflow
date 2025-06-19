#!/usr/bin/env python3
"""
Generate API documentation from source code.

This script extracts docstrings, type hints, and method signatures
to generate comprehensive API documentation in various formats.
"""

import argparse
import ast
import inspect
import json
import os
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass, field
import importlib.util

# Add the lib directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))


@dataclass
class APIMethod:
    """Represents a method/function in the API."""
    name: str
    signature: str
    docstring: Optional[str]
    parameters: List[Dict[str, Any]]
    return_type: Optional[str]
    is_async: bool
    is_abstract: bool
    decorators: List[str] = field(default_factory=list)


@dataclass
class APIClass:
    """Represents a class in the API."""
    name: str
    module: str
    docstring: Optional[str]
    base_classes: List[str]
    methods: List[APIMethod]
    attributes: List[Dict[str, Any]]
    is_abstract: bool


@dataclass
class APIModule:
    """Represents a module in the API."""
    name: str
    path: str
    docstring: Optional[str]
    classes: List[APIClass]
    functions: List[APIMethod]
    constants: List[Dict[str, Any]]


class APIDocGenerator:
    """Generate API documentation from Python source code."""
    
    def __init__(self, include_private: bool = False):
        self.include_private = include_private
        self.modules: List[APIModule] = []
    
    def extract_module_info(self, module_path: Path) -> APIModule:
        """Extract API information from a Python module."""
        with open(module_path, 'r') as f:
            source = f.read()
        
        tree = ast.parse(source)
        
        module = APIModule(
            name=module_path.stem,
            path=str(module_path),
            docstring=ast.get_docstring(tree),
            classes=[],
            functions=[],
            constants=[]
        )
        
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                if not self.include_private and node.name.startswith('_'):
                    continue
                module.classes.append(self.extract_class_info(node))
            
            elif isinstance(node, ast.FunctionDef) and node.col_offset == 0:
                if not self.include_private and node.name.startswith('_'):
                    continue
                module.functions.append(self.extract_method_info(node))
            
            elif isinstance(node, ast.Assign) and node.col_offset == 0:
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        if not self.include_private and target.id.startswith('_'):
                            continue
                        module.constants.append({
                            'name': target.id,
                            'value': ast.unparse(node.value) if hasattr(ast, 'unparse') else str(node.value)
                        })
        
        return module
    
    def extract_class_info(self, node: ast.ClassDef) -> APIClass:
        """Extract information from a class definition."""
        base_classes = []
        for base in node.bases:
            if isinstance(base, ast.Name):
                base_classes.append(base.id)
            elif isinstance(base, ast.Attribute):
                base_classes.append(ast.unparse(base) if hasattr(ast, 'unparse') else str(base))
        
        methods = []
        attributes = []
        
        for item in node.body:
            if isinstance(item, ast.FunctionDef):
                if not self.include_private and item.name.startswith('_') and item.name != '__init__':
                    continue
                methods.append(self.extract_method_info(item))
            
            elif isinstance(item, ast.AnnAssign) and isinstance(item.target, ast.Name):
                if not self.include_private and item.target.id.startswith('_'):
                    continue
                attributes.append({
                    'name': item.target.id,
                    'type': ast.unparse(item.annotation) if hasattr(ast, 'unparse') else str(item.annotation),
                    'default': ast.unparse(item.value) if item.value and hasattr(ast, 'unparse') else None
                })
        
        is_abstract = any(
            isinstance(dec, ast.Name) and dec.id == 'abstractmethod'
            for item in node.body
            if isinstance(item, ast.FunctionDef)
            for dec in item.decorator_list
        )
        
        return APIClass(
            name=node.name,
            module='',  # Will be set later
            docstring=ast.get_docstring(node),
            base_classes=base_classes,
            methods=methods,
            attributes=attributes,
            is_abstract=is_abstract
        )
    
    def extract_method_info(self, node: ast.FunctionDef) -> APIMethod:
        """Extract information from a method/function definition."""
        parameters = []
        
        for arg in node.args.args:
            param = {'name': arg.arg}
            
            # Get type annotation
            if arg.annotation:
                param['type'] = ast.unparse(arg.annotation) if hasattr(ast, 'unparse') else str(arg.annotation)
            
            parameters.append(param)
        
        # Get return type
        return_type = None
        if node.returns:
            return_type = ast.unparse(node.returns) if hasattr(ast, 'unparse') else str(node.returns)
        
        # Get decorators
        decorators = []
        is_abstract = False
        for dec in node.decorator_list:
            if isinstance(dec, ast.Name):
                decorators.append(dec.id)
                if dec.id == 'abstractmethod':
                    is_abstract = True
            elif isinstance(dec, ast.Attribute):
                decorators.append(ast.unparse(dec) if hasattr(ast, 'unparse') else str(dec))
        
        # Build signature
        params = []
        for i, arg in enumerate(node.args.args):
            param_str = arg.arg
            if arg.annotation:
                param_str += f": {ast.unparse(arg.annotation) if hasattr(ast, 'unparse') else str(arg.annotation)}"
            
            # Check for default values
            defaults_offset = len(node.args.args) - len(node.args.defaults)
            if i >= defaults_offset:
                default_idx = i - defaults_offset
                default_value = ast.unparse(node.args.defaults[default_idx]) if hasattr(ast, 'unparse') else str(node.args.defaults[default_idx])
                param_str += f" = {default_value}"
            
            params.append(param_str)
        
        signature = f"{node.name}({', '.join(params)})"
        if return_type:
            signature += f" -> {return_type}"
        
        return APIMethod(
            name=node.name,
            signature=signature,
            docstring=ast.get_docstring(node),
            parameters=parameters,
            return_type=return_type,
            is_async=isinstance(node, ast.AsyncFunctionDef),
            is_abstract=is_abstract,
            decorators=decorators
        )
    
    def scan_directory(self, directory: Path) -> List[APIModule]:
        """Scan a directory for Python modules."""
        modules = []
        
        for py_file in directory.rglob("*.py"):
            if py_file.name == '__init__.py':
                continue
            if 'test' in py_file.parts or 'tests' in py_file.parts:
                continue
            
            try:
                module = self.extract_module_info(py_file)
                modules.append(module)
            except Exception as e:
                print(f"Error processing {py_file}: {e}")
        
        return modules
    
    def generate_markdown(self, modules: List[APIModule]) -> str:
        """Generate Markdown documentation."""
        lines = ["# API Reference (Auto-Generated)\n"]
        lines.append("> Generated from source code\n")
        
        # Group modules by package
        packages: Dict[str, List[APIModule]] = {}
        for module in modules:
            parts = Path(module.path).parts
            if 'lib' in parts:
                idx = parts.index('lib')
                package = '.'.join(parts[idx+1:-1]) if len(parts) > idx + 2 else 'lib'
            else:
                package = 'scripts'
            
            if package not in packages:
                packages[package] = []
            packages[package].append(module)
        
        # Generate documentation for each package
        for package, package_modules in sorted(packages.items()):
            lines.append(f"\n## Package: {package}\n")
            
            for module in sorted(package_modules, key=lambda m: m.name):
                lines.append(f"\n### Module: {module.name}\n")
                
                if module.docstring:
                    lines.append(f"{module.docstring}\n")
                
                # Classes
                if module.classes:
                    lines.append("\n#### Classes\n")
                    
                    for cls in module.classes:
                        lines.append(f"\n##### {cls.name}\n")
                        
                        if cls.docstring:
                            lines.append(f"{cls.docstring}\n")
                        
                        if cls.base_classes:
                            lines.append(f"**Inherits from:** {', '.join(cls.base_classes)}\n")
                        
                        if cls.is_abstract:
                            lines.append("**Abstract Class**\n")
                        
                        # Attributes
                        if cls.attributes:
                            lines.append("\n**Attributes:**\n")
                            for attr in cls.attributes:
                                attr_str = f"- `{attr['name']}"
                                if 'type' in attr:
                                    attr_str += f": {attr['type']}"
                                attr_str += "`"
                                if 'default' in attr and attr['default']:
                                    attr_str += f" (default: {attr['default']})"
                                lines.append(attr_str)
                            lines.append("")
                        
                        # Methods
                        if cls.methods:
                            lines.append("\n**Methods:**\n")
                            for method in cls.methods:
                                lines.append(f"\n`{method.signature}`\n")
                                
                                if method.is_async:
                                    lines.append("*(async method)*\n")
                                
                                if method.is_abstract:
                                    lines.append("*(abstract method)*\n")
                                
                                if method.docstring:
                                    lines.append(f"{method.docstring}\n")
                
                # Module-level functions
                if module.functions:
                    lines.append("\n#### Functions\n")
                    
                    for func in module.functions:
                        lines.append(f"\n`{func.signature}`\n")
                        
                        if func.is_async:
                            lines.append("*(async function)*\n")
                        
                        if func.docstring:
                            lines.append(f"{func.docstring}\n")
                
                # Constants
                if module.constants:
                    lines.append("\n#### Constants\n")
                    
                    for const in module.constants:
                        lines.append(f"- `{const['name']}` = `{const['value']}`")
                    lines.append("")
        
        return '\n'.join(lines)
    
    def generate_openapi(self, modules: List[APIModule]) -> Dict[str, Any]:
        """Generate OpenAPI specification."""
        openapi = {
            "openapi": "3.0.0",
            "info": {
                "title": "AI Agent TDD-Scrum Workflow API",
                "version": "1.0.0",
                "description": "API for orchestrating AI agents in TDD-Scrum workflow"
            },
            "paths": {},
            "components": {
                "schemas": {}
            }
        }
        
        # Extract REST API endpoints if any
        # This is a simplified example - real implementation would need more parsing
        
        for module in modules:
            for cls in module.classes:
                if 'Agent' in cls.name:
                    # Create schema for agent
                    schema = {
                        "type": "object",
                        "properties": {
                            "name": {"type": "string"},
                            "capabilities": {
                                "type": "array",
                                "items": {"type": "string"}
                            }
                        }
                    }
                    
                    openapi["components"]["schemas"][cls.name] = schema
                    
                    # Create endpoint for agent
                    path = f"/agents/{cls.name.lower()}"
                    openapi["paths"][path] = {
                        "post": {
                            "summary": f"Execute {cls.name} task",
                            "requestBody": {
                                "content": {
                                    "application/json": {
                                        "schema": {
                                            "$ref": f"#/components/schemas/{cls.name}Task"
                                        }
                                    }
                                }
                            },
                            "responses": {
                                "200": {
                                    "description": "Task completed successfully"
                                }
                            }
                        }
                    }
        
        return openapi


def main():
    parser = argparse.ArgumentParser(description='Generate API documentation from source code')
    parser.add_argument(
        '--include-private',
        action='store_true',
        help='Include private methods and attributes'
    )
    parser.add_argument(
        '--format',
        choices=['markdown', 'openapi'],
        default='markdown',
        help='Output format'
    )
    parser.add_argument(
        '--output',
        type=str,
        help='Output file (default: stdout)'
    )
    parser.add_argument(
        '--directory',
        type=str,
        default='lib',
        help='Directory to scan (default: lib)'
    )
    
    args = parser.parse_args()
    
    # Get the project root
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    target_dir = project_root / args.directory
    
    if not target_dir.exists():
        print(f"Error: Directory {target_dir} does not exist")
        sys.exit(1)
    
    # Generate documentation
    generator = APIDocGenerator(include_private=args.include_private)
    modules = generator.scan_directory(target_dir)
    
    if args.format == 'markdown':
        output = generator.generate_markdown(modules)
    else:  # openapi
        output_dict = generator.generate_openapi(modules)
        output = json.dumps(output_dict, indent=2)
    
    # Write output
    if args.output:
        with open(args.output, 'w') as f:
            f.write(output)
        print(f"Documentation written to {args.output}")
    else:
        print(output)


if __name__ == '__main__':
    main()