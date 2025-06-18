"""
Context Index - Searchable Codebase Indexing System

Builds and maintains a searchable index of codebase structure, dependencies,
and relationships for fast context retrieval. Provides:
- File relationship mapping and import tracking
- Code structure analysis for relevance scoring
- Historical access pattern tracking
- Fast search and filtering capabilities with caching
"""

import ast
import json
import pickle
import hashlib
import logging
import sqlite3
from typing import Dict, List, Optional, Set, Any, Tuple, Union
from pathlib import Path
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from collections import defaultdict, Counter

try:
    from .context.models import FileType, RelevanceScore
    from .token_calculator import TokenCalculator
except ImportError:
    from context.models import FileType, RelevanceScore
    from token_calculator import TokenCalculator

logger = logging.getLogger(__name__)


@dataclass
class FileNode:
    """Represents a file in the codebase index"""
    path: str
    file_type: FileType
    size: int
    last_modified: datetime
    content_hash: str
    imports: List[str]
    exports: List[str]
    classes: List[str]
    functions: List[str]
    dependencies: List[str]
    reverse_dependencies: List[str]
    access_count: int = 0
    last_accessed: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        result = asdict(self)
        result['last_modified'] = self.last_modified.isoformat()
        if self.last_accessed:
            result['last_accessed'] = self.last_accessed.isoformat()
        result['file_type'] = self.file_type.value
        return result
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'FileNode':
        """Create from dictionary"""
        data = data.copy()
        data['last_modified'] = datetime.fromisoformat(data['last_modified'])
        if data.get('last_accessed'):
            data['last_accessed'] = datetime.fromisoformat(data['last_accessed'])
        data['file_type'] = FileType(data['file_type'])
        return cls(**data)


@dataclass
class DependencyEdge:
    """Represents a dependency relationship between files"""
    source: str
    target: str
    import_type: str  # 'import', 'from', 'relative'
    line_number: int
    strength: float = 1.0  # Dependency strength (0.0 to 1.0)


@dataclass
class SearchResult:
    """Search result with relevance scoring"""
    file_path: str
    relevance_score: float
    match_type: str  # 'exact', 'partial', 'semantic'
    matches: List[str]
    context: str = ""


class ContextIndex:
    """
    Searchable codebase indexing with dependency analysis.
    
    Maintains an in-memory index of codebase structure with SQLite persistence
    for fast searching and relationship analysis. Tracks file dependencies,
    code structure, and access patterns for intelligent context selection.
    """
    
    def __init__(
        self,
        project_path: str,
        index_cache_path: Optional[str] = None,
        token_calculator: Optional[TokenCalculator] = None
    ):
        """
        Initialize ContextIndex.
        
        Args:
            project_path: Path to project root
            index_cache_path: Path to index cache file (optional)
            token_calculator: Token calculator for content analysis
        """
        self.project_path = Path(project_path)
        self.token_calculator = token_calculator or TokenCalculator()
        
        # Index storage
        self.cache_path = Path(index_cache_path) if index_cache_path else self.project_path / ".orch-state" / "context_index.db"
        self.cache_path.parent.mkdir(parents=True, exist_ok=True)
        
        # In-memory index
        self.file_nodes: Dict[str, FileNode] = {}
        self.dependencies: List[DependencyEdge] = []
        self.dependency_graph: Dict[str, Set[str]] = defaultdict(set)
        self.reverse_dependency_graph: Dict[str, Set[str]] = defaultdict(set)
        
        # Search indices
        self.function_index: Dict[str, List[str]] = defaultdict(list)
        self.class_index: Dict[str, List[str]] = defaultdict(list)
        self.import_index: Dict[str, List[str]] = defaultdict(list)
        self.content_index: Dict[str, List[str]] = defaultdict(list)
        
        # Performance tracking
        self.last_full_scan: Optional[datetime] = None
        self.index_build_time = 0.0
        self.search_times: List[float] = []
        self.cache_hits = 0
        self.cache_misses = 0
        
        # Initialize database
        self._init_database()
        
        logger.info(f"ContextIndex initialized for project: {self.project_path}")
    
    async def build_index(self, force_rebuild: bool = False) -> None:
        """
        Build or update the codebase index.
        
        Args:
            force_rebuild: Whether to force a complete rebuild
        """
        start_time = datetime.now()
        
        try:
            if force_rebuild:
                await self._clear_index()
            
            # Load existing index from cache
            if not force_rebuild:
                await self._load_index_from_cache()
            
            # Scan for changes and update index
            await self._scan_and_update_files()
            
            # Build dependency graph
            await self._build_dependency_graph()
            
            # Build search indices
            await self._build_search_indices()
            
            # Save to cache
            await self._save_index_to_cache()
            
            self.last_full_scan = datetime.now()
            self.index_build_time = (self.last_full_scan - start_time).total_seconds()
            
            logger.info(
                f"Index built successfully: {len(self.file_nodes)} files, "
                f"{len(self.dependencies)} dependencies in {self.index_build_time:.2f}s"
            )
            
        except Exception as e:
            logger.error(f"Error building index: {str(e)}")
            raise
    
    async def search_files(
        self,
        query: str,
        search_type: str = "all",
        max_results: int = 50,
        include_content: bool = False
    ) -> List[SearchResult]:
        """
        Search for files matching the query.
        
        Args:
            query: Search query
            search_type: Type of search ('all', 'functions', 'classes', 'imports', 'content')
            max_results: Maximum number of results
            include_content: Whether to include content context
            
        Returns:
            List of SearchResult objects
        """
        start_time = datetime.now()
        
        try:
            results = []
            
            if search_type in ["all", "functions"]:
                results.extend(await self._search_functions(query, max_results // 4))
            
            if search_type in ["all", "classes"]:
                results.extend(await self._search_classes(query, max_results // 4))
            
            if search_type in ["all", "imports"]:
                results.extend(await self._search_imports(query, max_results // 4))
            
            if search_type in ["all", "content"] and include_content:
                results.extend(await self._search_content(query, max_results // 4))
            
            # Deduplicate and sort by relevance
            seen_files = set()
            unique_results = []
            
            for result in sorted(results, key=lambda r: r.relevance_score, reverse=True):
                if result.file_path not in seen_files:
                    seen_files.add(result.file_path)
                    unique_results.append(result)
                    if len(unique_results) >= max_results:
                        break
            
            # Track performance
            elapsed = (datetime.now() - start_time).total_seconds()
            self.search_times.append(elapsed)
            
            logger.debug(f"Search completed: {len(unique_results)} results in {elapsed:.3f}s")
            
            return unique_results
            
        except Exception as e:
            logger.error(f"Error searching files: {str(e)}")
            return []
    
    async def get_file_dependencies(
        self,
        file_path: str,
        depth: int = 1,
        include_reverse: bool = False
    ) -> Dict[str, Any]:
        """
        Get dependencies for a specific file.
        
        Args:
            file_path: Path to the file
            depth: Depth of dependency traversal
            include_reverse: Whether to include reverse dependencies
            
        Returns:
            Dictionary with dependency information
        """
        if file_path not in self.file_nodes:
            return {"error": f"File {file_path} not found in index"}
        
        result = {
            "file": file_path,
            "direct_dependencies": list(self.dependency_graph.get(file_path, set())),
            "dependency_count": len(self.dependency_graph.get(file_path, set())),
            "reverse_dependencies": list(self.reverse_dependency_graph.get(file_path, set())) if include_reverse else [],
            "reverse_dependency_count": len(self.reverse_dependency_graph.get(file_path, set()))
        }
        
        if depth > 1:
            # Get transitive dependencies
            transitive_deps = await self._get_transitive_dependencies(file_path, depth)
            result["transitive_dependencies"] = list(transitive_deps)
            result["transitive_count"] = len(transitive_deps)
        
        return result
    
    async def get_file_structure(self, file_path: str) -> Dict[str, Any]:
        """
        Get structural information about a file.
        
        Args:
            file_path: Path to the file
            
        Returns:
            Dictionary with file structure information
        """
        if file_path not in self.file_nodes:
            return {"error": f"File {file_path} not found in index"}
        
        node = self.file_nodes[file_path]
        
        return {
            "file": file_path,
            "file_type": node.file_type.value,
            "size": node.size,
            "last_modified": node.last_modified.isoformat(),
            "content_hash": node.content_hash,
            "classes": node.classes,
            "functions": node.functions,
            "imports": node.imports,
            "exports": node.exports,
            "access_count": node.access_count,
            "last_accessed": node.last_accessed.isoformat() if node.last_accessed else None
        }
    
    async def find_related_files(
        self,
        file_path: str,
        relation_types: List[str] = None,
        max_results: int = 20
    ) -> List[Tuple[str, str, float]]:
        """
        Find files related to the given file.
        
        Args:
            file_path: Path to the source file
            relation_types: Types of relations to consider
            max_results: Maximum number of results
            
        Returns:
            List of (related_file, relation_type, strength) tuples
        """
        if relation_types is None:
            relation_types = ["dependency", "reverse_dependency", "similar_structure", "shared_imports"]
        
        related_files = []
        
        if "dependency" in relation_types:
            for dep_file in self.dependency_graph.get(file_path, set()):
                related_files.append((dep_file, "dependency", 1.0))
        
        if "reverse_dependency" in relation_types:
            for rev_dep in self.reverse_dependency_graph.get(file_path, set()):
                related_files.append((rev_dep, "reverse_dependency", 0.8))
        
        if "similar_structure" in relation_types:
            similar_files = await self._find_structurally_similar_files(file_path)
            for similar_file, similarity in similar_files:
                related_files.append((similar_file, "similar_structure", similarity))
        
        if "shared_imports" in relation_types:
            shared_import_files = await self._find_files_with_shared_imports(file_path)
            for shared_file, shared_count in shared_import_files:
                strength = min(shared_count / 5.0, 1.0)  # Normalize to max 5 shared imports
                related_files.append((shared_file, "shared_imports", strength))
        
        # Sort by strength and limit results
        related_files.sort(key=lambda x: x[2], reverse=True)
        return related_files[:max_results]
    
    async def track_file_access(self, file_path: str) -> None:
        """
        Track access to a file for usage analytics.
        
        Args:
            file_path: Path to the accessed file
        """
        if file_path in self.file_nodes:
            node = self.file_nodes[file_path]
            node.access_count += 1
            node.last_accessed = datetime.now()
            
            # Update database
            await self._update_file_access_in_db(file_path, node.access_count, node.last_accessed)
    
    async def get_project_statistics(self) -> Dict[str, Any]:
        """Get comprehensive project statistics"""
        stats = {
            "total_files": len(self.file_nodes),
            "file_types": Counter(node.file_type.value for node in self.file_nodes.values()),
            "total_dependencies": len(self.dependencies),
            "average_dependencies_per_file": len(self.dependencies) / len(self.file_nodes) if self.file_nodes else 0,
            "most_dependent_files": [],
            "most_depended_upon_files": [],
            "largest_files": [],
            "most_accessed_files": []
        }
        
        # Most dependent files (files that import many others)
        dependency_counts = [(path, len(deps)) for path, deps in self.dependency_graph.items()]
        dependency_counts.sort(key=lambda x: x[1], reverse=True)
        stats["most_dependent_files"] = dependency_counts[:10]
        
        # Most depended upon files (files imported by many others)
        reverse_dependency_counts = [(path, len(deps)) for path, deps in self.reverse_dependency_graph.items()]
        reverse_dependency_counts.sort(key=lambda x: x[1], reverse=True)
        stats["most_depended_upon_files"] = reverse_dependency_counts[:10]
        
        # Largest files
        file_sizes = [(path, node.size) for path, node in self.file_nodes.items()]
        file_sizes.sort(key=lambda x: x[1], reverse=True)
        stats["largest_files"] = file_sizes[:10]
        
        # Most accessed files
        access_counts = [(path, node.access_count) for path, node in self.file_nodes.items()]
        access_counts.sort(key=lambda x: x[1], reverse=True)
        stats["most_accessed_files"] = access_counts[:10]
        
        return stats
    
    # Private implementation methods
    
    def _init_database(self) -> None:
        """Initialize SQLite database for persistent storage"""
        try:
            self.db = sqlite3.connect(str(self.cache_path))
            self.db.execute('''
                CREATE TABLE IF NOT EXISTS files (
                    path TEXT PRIMARY KEY,
                    file_type TEXT,
                    size INTEGER,
                    last_modified TEXT,
                    content_hash TEXT,
                    imports TEXT,
                    exports TEXT,
                    classes TEXT,
                    functions TEXT,
                    access_count INTEGER DEFAULT 0,
                    last_accessed TEXT
                )
            ''')
            
            self.db.execute('''
                CREATE TABLE IF NOT EXISTS dependencies (
                    source TEXT,
                    target TEXT,
                    import_type TEXT,
                    line_number INTEGER,
                    strength REAL,
                    PRIMARY KEY (source, target)
                )
            ''')
            
            self.db.execute('''
                CREATE TABLE IF NOT EXISTS index_metadata (
                    key TEXT PRIMARY KEY,
                    value TEXT
                )
            ''')
            
            # Create indices for better performance
            self.db.execute('CREATE INDEX IF NOT EXISTS idx_files_type ON files(file_type)')
            self.db.execute('CREATE INDEX IF NOT EXISTS idx_files_modified ON files(last_modified)')
            self.db.execute('CREATE INDEX IF NOT EXISTS idx_deps_source ON dependencies(source)')
            self.db.execute('CREATE INDEX IF NOT EXISTS idx_deps_target ON dependencies(target)')
            
            self.db.commit()
            
        except Exception as e:
            logger.error(f"Error initializing database: {str(e)}")
            raise
    
    async def _clear_index(self) -> None:
        """Clear all index data"""
        self.file_nodes.clear()
        self.dependencies.clear()
        self.dependency_graph.clear()
        self.reverse_dependency_graph.clear()
        self.function_index.clear()
        self.class_index.clear()
        self.import_index.clear()
        self.content_index.clear()
        
        # Clear database
        self.db.execute('DELETE FROM files')
        self.db.execute('DELETE FROM dependencies')
        self.db.commit()
    
    async def _load_index_from_cache(self) -> None:
        """Load index from database cache"""
        try:
            # Load files
            cursor = self.db.execute('''
                SELECT path, file_type, size, last_modified, content_hash, 
                       imports, exports, classes, functions, access_count, last_accessed
                FROM files
            ''')
            
            for row in cursor:
                path, file_type, size, last_modified, content_hash, imports_str, exports_str, classes_str, functions_str, access_count, last_accessed_str = row
                
                node = FileNode(
                    path=path,
                    file_type=FileType(file_type),
                    size=size,
                    last_modified=datetime.fromisoformat(last_modified),
                    content_hash=content_hash,
                    imports=json.loads(imports_str) if imports_str else [],
                    exports=json.loads(exports_str) if exports_str else [],
                    classes=json.loads(classes_str) if classes_str else [],
                    functions=json.loads(functions_str) if functions_str else [],
                    dependencies=[],  # Will be populated from dependencies table
                    reverse_dependencies=[],  # Will be populated from dependencies table
                    access_count=access_count or 0,
                    last_accessed=datetime.fromisoformat(last_accessed_str) if last_accessed_str else None
                )
                
                self.file_nodes[path] = node
            
            # Load dependencies
            cursor = self.db.execute('''
                SELECT source, target, import_type, line_number, strength
                FROM dependencies
            ''')
            
            for row in cursor:
                source, target, import_type, line_number, strength = row
                
                dependency = DependencyEdge(
                    source=source,
                    target=target,
                    import_type=import_type,
                    line_number=line_number,
                    strength=strength
                )
                
                self.dependencies.append(dependency)
            
            logger.debug(f"Loaded index from cache: {len(self.file_nodes)} files, {len(self.dependencies)} dependencies")
            
        except Exception as e:
            logger.warning(f"Error loading index from cache: {str(e)}")
            # Continue with empty index
    
    async def _save_index_to_cache(self) -> None:
        """Save index to database cache"""
        try:
            # Save files
            self.db.execute('DELETE FROM files')
            
            for path, node in self.file_nodes.items():
                self.db.execute('''
                    INSERT INTO files (
                        path, file_type, size, last_modified, content_hash,
                        imports, exports, classes, functions, access_count, last_accessed
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    path,
                    node.file_type.value,
                    node.size,
                    node.last_modified.isoformat(),
                    node.content_hash,
                    json.dumps(node.imports),
                    json.dumps(node.exports),
                    json.dumps(node.classes),
                    json.dumps(node.functions),
                    node.access_count,
                    node.last_accessed.isoformat() if node.last_accessed else None
                ))
            
            # Save dependencies
            self.db.execute('DELETE FROM dependencies')
            
            for dep in self.dependencies:
                self.db.execute('''
                    INSERT INTO dependencies (source, target, import_type, line_number, strength)
                    VALUES (?, ?, ?, ?, ?)
                ''', (
                    dep.source,
                    dep.target,
                    dep.import_type,
                    dep.line_number,
                    dep.strength
                ))
            
            # Save metadata
            self.db.execute('DELETE FROM index_metadata')
            self.db.execute('''
                INSERT INTO index_metadata (key, value) VALUES (?, ?)
            ''', ('last_full_scan', self.last_full_scan.isoformat() if self.last_full_scan else ''))
            
            self.db.commit()
            
            logger.debug("Index saved to cache successfully")
            
        except Exception as e:
            logger.error(f"Error saving index to cache: {str(e)}")
    
    async def _scan_and_update_files(self) -> None:
        """Scan project directory and update file index"""
        processed_files = set()
        
        # Scan for Python files
        for py_file in self.project_path.rglob("*.py"):
            if self._should_index_file(py_file):
                await self._process_file(str(py_file))
                processed_files.add(str(py_file))
        
        # Scan for other relevant files
        for pattern in ["*.md", "*.json", "*.yaml", "*.yml", "*.toml", "*.cfg", "*.ini"]:
            for file_path in self.project_path.rglob(pattern):
                if self._should_index_file(file_path):
                    await self._process_file(str(file_path))
                    processed_files.add(str(file_path))
        
        # Remove deleted files from index
        deleted_files = set(self.file_nodes.keys()) - processed_files
        for deleted_file in deleted_files:
            del self.file_nodes[deleted_file]
            logger.debug(f"Removed deleted file from index: {deleted_file}")
    
    def _should_index_file(self, file_path: Path) -> bool:
        """Determine if file should be indexed"""
        # Skip hidden files and directories
        if any(part.startswith('.') for part in file_path.parts):
            # Allow .orch-state for project files
            if '.orch-state' not in str(file_path):
                return False
        
        # Skip common ignore patterns
        ignore_patterns = [
            '__pycache__', '.git', '.venv', 'venv', 'node_modules',
            '.pytest_cache', '.coverage', 'build', 'dist', '.mypy_cache'
        ]
        
        if any(pattern in str(file_path) for pattern in ignore_patterns):
            return False
        
        # Check file size (skip very large files)
        try:
            if file_path.stat().st_size > 1_000_000:  # 1MB limit
                return False
        except OSError:
            return False
        
        return True
    
    async def _process_file(self, file_path: str) -> None:
        """Process a single file and update its index entry"""
        try:
            path = Path(file_path)
            stat = path.stat()
            
            # Calculate content hash for change detection
            with open(path, 'rb') as f:
                content_hash = hashlib.md5(f.read()).hexdigest()
            
            # Check if file needs updating
            if file_path in self.file_nodes:
                existing_node = self.file_nodes[file_path]
                if (existing_node.content_hash == content_hash and 
                    existing_node.last_modified == datetime.fromtimestamp(stat.st_mtime)):
                    return  # File hasn't changed
            
            # Determine file type
            file_type = self._determine_file_type(path)
            
            # Extract structure information
            structure_info = await self._extract_file_structure(file_path, file_type)
            
            # Create or update file node
            node = FileNode(
                path=file_path,
                file_type=file_type,
                size=stat.st_size,
                last_modified=datetime.fromtimestamp(stat.st_mtime),
                content_hash=content_hash,
                imports=structure_info.get('imports', []),
                exports=structure_info.get('exports', []),
                classes=structure_info.get('classes', []),
                functions=structure_info.get('functions', []),
                dependencies=[],  # Will be populated in build_dependency_graph
                reverse_dependencies=[],
                access_count=self.file_nodes[file_path].access_count if file_path in self.file_nodes else 0,
                last_accessed=self.file_nodes[file_path].last_accessed if file_path in self.file_nodes else None
            )
            
            self.file_nodes[file_path] = node
            
        except Exception as e:
            logger.warning(f"Error processing file {file_path}: {str(e)}")
    
    def _determine_file_type(self, path: Path) -> FileType:
        """Determine file type from path"""
        suffix = path.suffix.lower()
        name = path.name.lower()
        
        if suffix == '.py':
            if 'test' in name or name.startswith('test_') or path.parent.name in ['tests', 'test']:
                return FileType.TEST
            else:
                return FileType.PYTHON
        elif suffix in ['.md', '.rst']:
            return FileType.MARKDOWN
        elif suffix == '.json':
            return FileType.JSON
        elif suffix in ['.yml', '.yaml']:
            return FileType.YAML
        elif suffix in ['.cfg', '.ini', '.conf', '.toml']:
            return FileType.CONFIG
        else:
            return FileType.OTHER
    
    async def _extract_file_structure(self, file_path: str, file_type: FileType) -> Dict[str, List[str]]:
        """Extract structural information from file"""
        structure = {
            'imports': [],
            'exports': [],
            'classes': [],
            'functions': []
        }
        
        try:
            if file_type in [FileType.PYTHON, FileType.TEST]:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                
                try:
                    tree = ast.parse(content)
                    
                    for node in ast.walk(tree):
                        if isinstance(node, ast.Import):
                            for alias in node.names:
                                structure['imports'].append(alias.name)
                        
                        elif isinstance(node, ast.ImportFrom):
                            if node.module:
                                structure['imports'].append(node.module)
                        
                        elif isinstance(node, ast.ClassDef):
                            structure['classes'].append(node.name)
                        
                        elif isinstance(node, ast.FunctionDef):
                            structure['functions'].append(node.name)
                
                except SyntaxError:
                    # Handle invalid Python files gracefully
                    logger.debug(f"Syntax error in file {file_path}, skipping AST analysis")
                    
            elif file_type == FileType.JSON:
                # For JSON files, we might want to index top-level keys
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    
                    if isinstance(data, dict):
                        structure['exports'] = list(data.keys())[:20]  # Limit to first 20 keys
                        
                except (json.JSONDecodeError, UnicodeDecodeError):
                    pass
                    
        except Exception as e:
            logger.debug(f"Error extracting structure from {file_path}: {str(e)}")
        
        return structure
    
    async def _build_dependency_graph(self) -> None:
        """Build dependency graph from file imports"""
        self.dependencies.clear()
        self.dependency_graph.clear()
        self.reverse_dependency_graph.clear()
        
        # Create mapping from module names to file paths
        module_to_file = {}
        for file_path, node in self.file_nodes.items():
            if node.file_type in [FileType.PYTHON, FileType.TEST]:
                # Extract module name from file path
                rel_path = Path(file_path).relative_to(self.project_path)
                module_parts = list(rel_path.parts[:-1])  # Exclude filename
                if rel_path.name != '__init__.py':
                    module_parts.append(rel_path.stem)
                
                if module_parts:
                    module_name = '.'.join(module_parts)
                    module_to_file[module_name] = file_path
                
                # Also map direct filename without extension
                module_to_file[rel_path.stem] = file_path
        
        # Build dependencies
        for file_path, node in self.file_nodes.items():
            if node.file_type in [FileType.PYTHON, FileType.TEST]:
                for import_name in node.imports:
                    # Find corresponding file
                    target_file = None
                    
                    # Try exact match first
                    if import_name in module_to_file:
                        target_file = module_to_file[import_name]
                    else:
                        # Try partial matches
                        for module_name, module_file in module_to_file.items():
                            if import_name.startswith(module_name) or module_name.startswith(import_name):
                                target_file = module_file
                                break
                    
                    if target_file and target_file != file_path:
                        # Create dependency edge
                        dependency = DependencyEdge(
                            source=file_path,
                            target=target_file,
                            import_type='import',
                            line_number=0,  # Would need more sophisticated parsing for line numbers
                            strength=1.0
                        )
                        
                        self.dependencies.append(dependency)
                        self.dependency_graph[file_path].add(target_file)
                        self.reverse_dependency_graph[target_file].add(file_path)
        
        # Update file nodes with dependency information
        for file_path, node in self.file_nodes.items():
            node.dependencies = list(self.dependency_graph.get(file_path, set()))
            node.reverse_dependencies = list(self.reverse_dependency_graph.get(file_path, set()))
    
    async def _build_search_indices(self) -> None:
        """Build search indices for fast lookup"""
        self.function_index.clear()
        self.class_index.clear()
        self.import_index.clear()
        self.content_index.clear()
        
        for file_path, node in self.file_nodes.items():
            # Index functions
            for function in node.functions:
                self.function_index[function.lower()].append(file_path)
            
            # Index classes
            for class_name in node.classes:
                self.class_index[class_name.lower()].append(file_path)
            
            # Index imports
            for import_name in node.imports:
                self.import_index[import_name.lower()].append(file_path)
            
            # Index file path components
            path_parts = Path(file_path).parts
            for part in path_parts:
                if len(part) > 2:  # Skip very short parts
                    self.content_index[part.lower()].append(file_path)
    
    async def _search_functions(self, query: str, max_results: int) -> List[SearchResult]:
        """Search for functions matching query"""
        results = []
        query_lower = query.lower()
        
        for function_name, file_paths in self.function_index.items():
            if query_lower in function_name:
                relevance = self._calculate_string_similarity(query_lower, function_name)
                match_type = "exact" if query_lower == function_name else "partial"
                
                for file_path in file_paths:
                    results.append(SearchResult(
                        file_path=file_path,
                        relevance_score=relevance,
                        match_type=match_type,
                        matches=[function_name],
                        context=f"Function: {function_name}"
                    ))
        
        return sorted(results, key=lambda r: r.relevance_score, reverse=True)[:max_results]
    
    async def _search_classes(self, query: str, max_results: int) -> List[SearchResult]:
        """Search for classes matching query"""
        results = []
        query_lower = query.lower()
        
        for class_name, file_paths in self.class_index.items():
            if query_lower in class_name:
                relevance = self._calculate_string_similarity(query_lower, class_name)
                match_type = "exact" if query_lower == class_name else "partial"
                
                for file_path in file_paths:
                    results.append(SearchResult(
                        file_path=file_path,
                        relevance_score=relevance,
                        match_type=match_type,
                        matches=[class_name],
                        context=f"Class: {class_name}"
                    ))
        
        return sorted(results, key=lambda r: r.relevance_score, reverse=True)[:max_results]
    
    async def _search_imports(self, query: str, max_results: int) -> List[SearchResult]:
        """Search for imports matching query"""
        results = []
        query_lower = query.lower()
        
        for import_name, file_paths in self.import_index.items():
            if query_lower in import_name:
                relevance = self._calculate_string_similarity(query_lower, import_name)
                match_type = "exact" if query_lower == import_name else "partial"
                
                for file_path in file_paths:
                    results.append(SearchResult(
                        file_path=file_path,
                        relevance_score=relevance * 0.7,  # Lower weight for imports
                        match_type=match_type,
                        matches=[import_name],
                        context=f"Import: {import_name}"
                    ))
        
        return sorted(results, key=lambda r: r.relevance_score, reverse=True)[:max_results]
    
    async def _search_content(self, query: str, max_results: int) -> List[SearchResult]:
        """Search file content (simplified - would need full-text search for production)"""
        results = []
        query_lower = query.lower()
        
        for content_term, file_paths in self.content_index.items():
            if query_lower in content_term:
                relevance = self._calculate_string_similarity(query_lower, content_term) * 0.5
                
                for file_path in file_paths:
                    results.append(SearchResult(
                        file_path=file_path,
                        relevance_score=relevance,
                        match_type="partial",
                        matches=[content_term],
                        context=f"Path component: {content_term}"
                    ))
        
        return sorted(results, key=lambda r: r.relevance_score, reverse=True)[:max_results]
    
    def _calculate_string_similarity(self, s1: str, s2: str) -> float:
        """Calculate simple string similarity (would use more sophisticated algorithm in production)"""
        if s1 == s2:
            return 1.0
        
        if s1 in s2 or s2 in s1:
            return max(len(s1) / len(s2), len(s2) / len(s1))
        
        # Simple character overlap similarity
        s1_chars = set(s1)
        s2_chars = set(s2)
        overlap = len(s1_chars & s2_chars)
        total = len(s1_chars | s2_chars)
        
        return overlap / total if total > 0 else 0.0
    
    async def _get_transitive_dependencies(self, file_path: str, depth: int) -> Set[str]:
        """Get transitive dependencies up to specified depth"""
        visited = set()
        queue = [(file_path, 0)]
        
        while queue:
            current_file, current_depth = queue.pop(0)
            
            if current_file in visited or current_depth >= depth:
                continue
            
            visited.add(current_file)
            
            # Add direct dependencies to queue
            for dep_file in self.dependency_graph.get(current_file, set()):
                if dep_file not in visited:
                    queue.append((dep_file, current_depth + 1))
        
        visited.discard(file_path)  # Remove the original file
        return visited
    
    async def _find_structurally_similar_files(self, file_path: str, max_results: int = 5) -> List[Tuple[str, float]]:
        """Find files with similar structure"""
        if file_path not in self.file_nodes:
            return []
        
        source_node = self.file_nodes[file_path]
        similar_files = []
        
        for other_path, other_node in self.file_nodes.items():
            if other_path == file_path or other_node.file_type != source_node.file_type:
                continue
            
            # Calculate structural similarity
            similarity = self._calculate_structural_similarity(source_node, other_node)
            
            if similarity > 0.1:  # Minimum similarity threshold
                similar_files.append((other_path, similarity))
        
        similar_files.sort(key=lambda x: x[1], reverse=True)
        return similar_files[:max_results]
    
    def _calculate_structural_similarity(self, node1: FileNode, node2: FileNode) -> float:
        """Calculate structural similarity between two file nodes"""
        # Compare function names
        func_similarity = self._calculate_list_similarity(node1.functions, node2.functions)
        
        # Compare class names
        class_similarity = self._calculate_list_similarity(node1.classes, node2.classes)
        
        # Compare imports
        import_similarity = self._calculate_list_similarity(node1.imports, node2.imports)
        
        # Weighted combination
        return (func_similarity * 0.4 + class_similarity * 0.4 + import_similarity * 0.2)
    
    def _calculate_list_similarity(self, list1: List[str], list2: List[str]) -> float:
        """Calculate similarity between two lists of strings"""
        if not list1 and not list2:
            return 1.0
        
        if not list1 or not list2:
            return 0.0
        
        set1 = set(list1)
        set2 = set(list2)
        
        intersection = len(set1 & set2)
        union = len(set1 | set2)
        
        return intersection / union if union > 0 else 0.0
    
    async def _find_files_with_shared_imports(self, file_path: str, max_results: int = 5) -> List[Tuple[str, int]]:
        """Find files that share imports with the given file"""
        if file_path not in self.file_nodes:
            return []
        
        source_imports = set(self.file_nodes[file_path].imports)
        shared_files = []
        
        for other_path, other_node in self.file_nodes.items():
            if other_path == file_path:
                continue
            
            other_imports = set(other_node.imports)
            shared_count = len(source_imports & other_imports)
            
            if shared_count > 0:
                shared_files.append((other_path, shared_count))
        
        shared_files.sort(key=lambda x: x[1], reverse=True)
        return shared_files[:max_results]
    
    async def _update_file_access_in_db(self, file_path: str, access_count: int, last_accessed: datetime) -> None:
        """Update file access information in database"""
        try:
            self.db.execute('''
                UPDATE files SET access_count = ?, last_accessed = ? WHERE path = ?
            ''', (access_count, last_accessed.isoformat(), file_path))
            self.db.commit()
        except Exception as e:
            logger.warning(f"Error updating file access in database: {str(e)}")
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get performance metrics for the index"""
        avg_search_time = (
            sum(self.search_times) / len(self.search_times)
            if self.search_times else 0.0
        )
        
        cache_hit_rate = (
            self.cache_hits / (self.cache_hits + self.cache_misses)
            if (self.cache_hits + self.cache_misses) > 0 else 0.0
        )
        
        return {
            "total_files": len(self.file_nodes),
            "total_dependencies": len(self.dependencies),
            "index_build_time": self.index_build_time,
            "last_full_scan": self.last_full_scan.isoformat() if self.last_full_scan else None,
            "average_search_time": avg_search_time,
            "total_searches": len(self.search_times),
            "cache_hit_rate": cache_hit_rate,
            "cache_hits": self.cache_hits,
            "cache_misses": self.cache_misses,
            "search_indices": {
                "functions": len(self.function_index),
                "classes": len(self.class_index),
                "imports": len(self.import_index),
                "content_terms": len(self.content_index)
            }
        }
    
    async def close(self) -> None:
        """Close database connection"""
        if hasattr(self, 'db'):
            self.db.close()