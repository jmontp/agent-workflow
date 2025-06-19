#!/usr/bin/env python3
"""
Dependency Tracker - Automatic File Dependency Mapping

Scans the codebase to build a comprehensive dependency map between:
- Code files (Python modules)
- Test files (unit, integration, coverage tests)
- Documentation files (markdown, CLAUDE.md)
- Configuration files

Supports both explicit imports and convention-based mappings.
"""

import ast
import re
import yaml
import json
from pathlib import Path
from typing import Dict, List, Set, Optional, Tuple, Any
from dataclasses import dataclass, field, asdict
from collections import defaultdict
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class FileDependency:
    """Represents a dependency relationship between files"""
    source_file: str
    target_file: str
    dependency_type: str  # 'import', 'test', 'doc_reference', 'example', 'config'
    line_number: Optional[int] = None
    context: Optional[str] = None
    
    def to_dict(self):
        return {k: v for k, v in asdict(self).items() if v is not None}


@dataclass
class FileNode:
    """Represents a file in the dependency graph"""
    path: str
    file_type: str  # 'code', 'test', 'doc', 'config'
    module_name: Optional[str] = None
    classes: List[str] = field(default_factory=list)
    functions: List[str] = field(default_factory=list)
    imports: List[str] = field(default_factory=list)
    dependencies: Set[str] = field(default_factory=set)
    dependents: Set[str] = field(default_factory=set)
    
    def to_dict(self):
        data = asdict(self)
        data['dependencies'] = list(self.dependencies)
        data['dependents'] = list(self.dependents)
        return data


class DependencyTracker:
    """Tracks dependencies between files in the codebase"""
    
    def __init__(self, project_root: Path):
        self.project_root = Path(project_root).resolve()
        self.file_nodes: Dict[str, FileNode] = {}
        self.dependencies: List[FileDependency] = []
        self.naming_conventions = self._load_naming_conventions()
        
    def _load_naming_conventions(self) -> Dict[str, List[Dict[str, Any]]]:
        """Load naming convention patterns"""
        return {
            'test_to_code': [
                {
                    'pattern': r'tests?/unit/test_(.+?)(_coverage|_final|_critical|_audit)?\.py$',
                    'target': r'lib/\1.py',
                    'type': 'test'
                },
                {
                    'pattern': r'tests?/integration/test_(.+?)\.py$',
                    'target': r'lib/\1.py',
                    'type': 'integration_test'
                },
                {
                    'pattern': r'tests?/unit/test_agents_(.+?)\.py$',
                    'target': r'lib/agents/\1.py',
                    'type': 'test'
                },
            ],
            'doc_to_code': [
                {
                    'pattern': r'docs_src/.*/(.+?)\.md$',
                    'target': r'lib/\1.py',
                    'type': 'documentation'
                },
                {
                    'pattern': r'(.+?)/CLAUDE\.md$',
                    'target': r'\1',
                    'type': 'directory_doc'
                }
            ]
        }
    
    def scan_project(self) -> None:
        """Scan the entire project and build dependency map"""
        logger.info(f"Scanning project: {self.project_root}")
        
        # First pass: collect all files
        self._collect_files()
        
        # Second pass: analyze dependencies
        self._analyze_python_files()
        self._analyze_markdown_files()
        self._apply_naming_conventions()
        
        # Third pass: build dependency graph
        self._build_dependency_graph()
        
        logger.info(f"Scan complete: {len(self.file_nodes)} files, {len(self.dependencies)} dependencies")
    
    def _collect_files(self) -> None:
        """Collect all relevant files in the project"""
        patterns = {
            '**/*.py': 'code',
            '**/test_*.py': 'test',
            '**/*.md': 'doc',
            '**/*.yaml': 'config',
            '**/*.yml': 'config',
            '**/*.toml': 'config',
            '**/*.json': 'config'
        }
        
        for pattern, file_type in patterns.items():
            for file_path in self.project_root.glob(pattern):
                if self._should_include_file(file_path):
                    rel_path = self._get_relative_path(file_path)
                    
                    # Determine more specific file type
                    if rel_path.startswith('tests/'):
                        file_type = 'test'
                    elif rel_path.startswith('docs_src/'):
                        file_type = 'doc'
                    elif file_path.name == 'CLAUDE.md':
                        file_type = 'doc'
                    
                    node = FileNode(path=rel_path, file_type=file_type)
                    self.file_nodes[rel_path] = node
    
    def _should_include_file(self, file_path: Path) -> bool:
        """Check if file should be included in dependency tracking"""
        exclude_patterns = [
            '__pycache__', '.git', '.pytest_cache', 'venv', 
            'env', 'build', 'dist', '*.egg-info', 'htmlcov',
            'site', '.tox', 'node_modules'
        ]
        
        path_str = str(file_path)
        return not any(pattern in path_str for pattern in exclude_patterns)
    
    def _get_relative_path(self, file_path: Path) -> str:
        """Get relative path from project root"""
        try:
            return str(file_path.relative_to(self.project_root))
        except ValueError:
            return str(file_path)
    
    def _analyze_python_files(self) -> None:
        """Analyze Python files for imports and structure"""
        for rel_path, node in self.file_nodes.items():
            if node.file_type in ['code', 'test'] and rel_path.endswith('.py'):
                file_path = self.project_root / rel_path
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    # Parse AST
                    tree = ast.parse(content, filename=str(file_path))
                    
                    # Extract imports
                    imports = self._extract_imports(tree, rel_path)
                    node.imports = imports
                    
                    # Extract classes and functions
                    node.classes = self._extract_classes(tree)
                    node.functions = self._extract_functions(tree)
                    
                    # Extract module name
                    node.module_name = self._path_to_module(rel_path)
                    
                except Exception as e:
                    logger.debug(f"Error analyzing {rel_path}: {e}")
    
    def _extract_imports(self, tree: ast.AST, source_file: str) -> List[str]:
        """Extract imports from Python AST"""
        imports = []
        
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.append(alias.name)
                    self._add_import_dependency(source_file, alias.name, node.lineno)
                    
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    imports.append(node.module)
                    self._add_import_dependency(source_file, node.module, node.lineno)
                    
                    # Handle relative imports
                    if node.level > 0:
                        # Convert relative import to absolute
                        base_module = self._path_to_module(source_file)
                        if base_module:
                            parts = base_module.split('.')
                            if len(parts) > node.level:
                                parent = '.'.join(parts[:-node.level])
                                full_module = f"{parent}.{node.module}" if node.module else parent
                                imports.append(full_module)
        
        return list(set(imports))
    
    def _add_import_dependency(self, source_file: str, module_name: str, line_number: int) -> None:
        """Add import dependency"""
        # Try to resolve module to file
        target_file = self._resolve_module_to_file(module_name)
        if target_file and target_file in self.file_nodes:
            dep = FileDependency(
                source_file=source_file,
                target_file=target_file,
                dependency_type='import',
                line_number=line_number,
                context=f"import {module_name}"
            )
            self.dependencies.append(dep)
    
    def _resolve_module_to_file(self, module_name: str) -> Optional[str]:
        """Resolve a module name to a file path"""
        # Handle local imports
        if module_name.startswith('lib.'):
            return module_name.replace('.', '/') + '.py'
        elif module_name.startswith('agent_workflow.'):
            return module_name.replace('.', '/') + '.py'
        
        # Check if it's a direct file reference
        for suffix in ['.py', '/__init__.py']:
            potential_path = module_name.replace('.', '/') + suffix
            if potential_path in self.file_nodes:
                return potential_path
        
        return None
    
    def _path_to_module(self, file_path: str) -> Optional[str]:
        """Convert file path to module name"""
        if file_path.endswith('.py'):
            # Remove .py extension
            module_path = file_path[:-3]
            
            # Handle __init__.py
            if module_path.endswith('/__init__'):
                module_path = module_path[:-9]
            
            # Convert to module name
            return module_path.replace('/', '.')
        
        return None
    
    def _extract_classes(self, tree: ast.AST) -> List[str]:
        """Extract class names from AST"""
        return [node.name for node in ast.walk(tree) if isinstance(node, ast.ClassDef)]
    
    def _extract_functions(self, tree: ast.AST) -> List[str]:
        """Extract function names from AST"""
        return [node.name for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)]
    
    def _analyze_markdown_files(self) -> None:
        """Analyze markdown files for code references"""
        code_ref_patterns = [
            # Code blocks with file references
            r'```python\s*\n#\s*(?:from\s+)?([a-zA-Z0-9_./]+\.py)',
            # Direct file references
            r'`([a-zA-Z0-9_./]+\.py)`',
            # Import statements in code blocks
            r'```python\s*\n.*?(?:from|import)\s+([a-zA-Z0-9_.]+)',
            # File path references
            r'(?:file:|File:)\s*`?([a-zA-Z0-9_./]+\.py)`?',
        ]
        
        for rel_path, node in self.file_nodes.items():
            if node.file_type == 'doc' and rel_path.endswith('.md'):
                file_path = self.project_root / rel_path
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    # Extract code references
                    for pattern in code_ref_patterns:
                        matches = re.findall(pattern, content, re.MULTILINE | re.DOTALL)
                        for match in matches:
                            # Try to resolve to actual file
                            if match.endswith('.py'):
                                if match in self.file_nodes:
                                    dep = FileDependency(
                                        source_file=rel_path,
                                        target_file=match,
                                        dependency_type='doc_reference',
                                        context=f"References {match}"
                                    )
                                    self.dependencies.append(dep)
                            else:
                                # Try to resolve module reference
                                resolved = self._resolve_module_to_file(match)
                                if resolved:
                                    dep = FileDependency(
                                        source_file=rel_path,
                                        target_file=resolved,
                                        dependency_type='doc_reference',
                                        context=f"References {match}"
                                    )
                                    self.dependencies.append(dep)
                    
                except Exception as e:
                    logger.debug(f"Error analyzing markdown {rel_path}: {e}")
    
    def _apply_naming_conventions(self) -> None:
        """Apply naming conventions to find implicit dependencies"""
        for rel_path, node in self.file_nodes.items():
            # Apply test-to-code conventions
            if node.file_type == 'test':
                for convention in self.naming_conventions['test_to_code']:
                    match = re.match(convention['pattern'], rel_path)
                    if match:
                        target = re.sub(convention['pattern'], convention['target'], rel_path)
                        if target in self.file_nodes:
                            dep = FileDependency(
                                source_file=rel_path,
                                target_file=target,
                                dependency_type=convention['type'],
                                context="Naming convention"
                            )
                            self.dependencies.append(dep)
            
            # Apply doc-to-code conventions
            elif node.file_type == 'doc':
                for convention in self.naming_conventions['doc_to_code']:
                    match = re.match(convention['pattern'], rel_path)
                    if match:
                        if convention['type'] == 'directory_doc':
                            # Special handling for CLAUDE.md files
                            dir_path = match.group(1)
                            # Find all code files in that directory
                            for other_path, other_node in self.file_nodes.items():
                                if other_path.startswith(dir_path) and other_node.file_type == 'code':
                                    dep = FileDependency(
                                        source_file=rel_path,
                                        target_file=other_path,
                                        dependency_type='directory_doc',
                                        context="Directory documentation"
                                    )
                                    self.dependencies.append(dep)
                        else:
                            target = re.sub(convention['pattern'], convention['target'], rel_path)
                            if target in self.file_nodes:
                                dep = FileDependency(
                                    source_file=rel_path,
                                    target_file=target,
                                    dependency_type=convention['type'],
                                    context="Naming convention"
                                )
                                self.dependencies.append(dep)
    
    def _build_dependency_graph(self) -> None:
        """Build bidirectional dependency graph"""
        for dep in self.dependencies:
            if dep.source_file in self.file_nodes and dep.target_file in self.file_nodes:
                self.file_nodes[dep.source_file].dependencies.add(dep.target_file)
                self.file_nodes[dep.target_file].dependents.add(dep.source_file)
    
    def get_file_dependencies(self, file_path: str) -> Dict[str, Any]:
        """Get all dependencies for a specific file"""
        rel_path = self._get_relative_path(Path(file_path))
        
        if rel_path not in self.file_nodes:
            return {}
        
        node = self.file_nodes[rel_path]
        
        # Categorize dependencies
        deps_by_type = defaultdict(list)
        for dep in self.dependencies:
            if dep.source_file == rel_path:
                deps_by_type[dep.dependency_type].append(dep.target_file)
            elif dep.target_file == rel_path:
                deps_by_type[f"dependent_{dep.dependency_type}"].append(dep.source_file)
        
        return {
            'file': rel_path,
            'type': node.file_type,
            'dependencies': dict(deps_by_type),
            'all_dependencies': list(node.dependencies),
            'all_dependents': list(node.dependents)
        }
    
    def find_related_files(self, file_path: str) -> Dict[str, List[str]]:
        """Find all files related to the given file"""
        deps = self.get_file_dependencies(file_path)
        if not deps:
            return {}
        
        related = {
            'tests': [],
            'docs': [],
            'code': [],
            'config': []
        }
        
        # Direct dependencies
        for dep_file in deps.get('all_dependencies', []):
            if dep_file in self.file_nodes:
                node = self.file_nodes[dep_file]
                if node.file_type == 'test':
                    related['tests'].append(dep_file)
                elif node.file_type == 'doc':
                    related['docs'].append(dep_file)
                elif node.file_type == 'code':
                    related['code'].append(dep_file)
                elif node.file_type == 'config':
                    related['config'].append(dep_file)
        
        # Dependents
        for dep_file in deps.get('all_dependents', []):
            if dep_file in self.file_nodes:
                node = self.file_nodes[dep_file]
                if node.file_type == 'test' and dep_file not in related['tests']:
                    related['tests'].append(dep_file)
                elif node.file_type == 'doc' and dep_file not in related['docs']:
                    related['docs'].append(dep_file)
        
        return {k: v for k, v in related.items() if v}
    
    def export_dependencies(self, output_path: Optional[Path] = None) -> None:
        """Export dependencies to YAML file"""
        if output_path is None:
            output_path = self.project_root / 'dependencies.yaml'
        
        # Build export structure
        export_data = {
            'version': '1.0',
            'generated': str(Path(__file__).name),
            'mappings': {}
        }
        
        # Group by file
        for rel_path, node in sorted(self.file_nodes.items()):
            if node.dependencies or node.dependents:
                file_data = {
                    'type': node.file_type,
                    'dependencies': sorted(list(node.dependencies)),
                    'dependents': sorted(list(node.dependents))
                }
                
                # Add related files by category
                related = self.find_related_files(rel_path)
                if related:
                    file_data['related'] = related
                
                export_data['mappings'][rel_path] = file_data
        
        # Write YAML
        with open(output_path, 'w') as f:
            yaml.dump(export_data, f, default_flow_style=False, sort_keys=False)
        
        logger.info(f"Exported dependencies to {output_path}")
    
    def generate_update_rules(self) -> Dict[str, Any]:
        """Generate rules for automatic updates"""
        rules = {
            'update_rules': [],
            'validation_rules': []
        }
        
        # Code change rules
        rules['update_rules'].append({
            'when': {'file_pattern': 'lib/**/*.py', 'change_type': 'modified'},
            'update': [
                {'pattern': 'tests/unit/test_{module}*.py', 'action': 'update_tests'},
                {'pattern': 'docs_src/**/{module}.md', 'action': 'update_docs'},
                {'pattern': '{dir}/CLAUDE.md', 'action': 'update_directory_docs'}
            ]
        })
        
        # Documentation change rules
        rules['validation_rules'].append({
            'when': {'file_pattern': 'docs_src/**/*.md', 'change_type': 'modified'},
            'validate': [
                {'check': 'code_references_exist'},
                {'check': 'examples_are_valid'}
            ]
        })
        
        # New feature rules
        rules['update_rules'].append({
            'when': {'file_pattern': 'lib/**/*.py', 'change_type': 'created'},
            'create': [
                {'template': 'test_template.py', 'path': 'tests/unit/test_{module}.py'},
                {'template': 'doc_template.md', 'path': 'docs_src/api/{module}.md'}
            ]
        })
        
        return rules


def main():
    """Main entry point for dependency tracker"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Track file dependencies in the project')
    parser.add_argument('--project-root', type=Path, default=Path.cwd(),
                        help='Project root directory')
    parser.add_argument('--output', type=Path, help='Output file for dependencies')
    parser.add_argument('--file', type=str, help='Get dependencies for specific file')
    parser.add_argument('--related', type=str, help='Find related files')
    parser.add_argument('--export-rules', action='store_true', 
                        help='Export update rules')
    
    args = parser.parse_args()
    
    tracker = DependencyTracker(args.project_root)
    tracker.scan_project()
    
    if args.file:
        deps = tracker.get_file_dependencies(args.file)
        print(yaml.dump(deps, default_flow_style=False))
    elif args.related:
        related = tracker.find_related_files(args.related)
        print(yaml.dump(related, default_flow_style=False))
    elif args.export_rules:
        rules = tracker.generate_update_rules()
        print(yaml.dump(rules, default_flow_style=False))
    else:
        tracker.export_dependencies(args.output)


if __name__ == '__main__':
    main()