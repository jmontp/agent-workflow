#!/usr/bin/env python3
"""
Context Manager v1 - The nervous system of the agent-workflow.
Tracks all context, learns patterns, and coordinates documentation.
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Set, Tuple
from enum import Enum
from pathlib import Path
import json
import uuid
import os
import re
from collections import Counter
import ast
import sys


# Schema definitions
class ContextType(Enum):
    """Types of context entries."""
    DEVELOPMENT = "development"
    PLANNING = "planning"
    EXECUTION = "execution"
    DOCUMENTATION = "documentation"
    CODE_CHANGE = "code_change"
    ERROR = "error"
    DECISION = "decision"


@dataclass
class Context:
    """Core context structure for all system interactions."""
    
    # Required fields
    id: str                    # UUID
    type: ContextType          # Enum
    source: str                # Agent or human identifier
    timestamp: datetime        # Creation time
    data: Dict[str, Any]      # Actual content
    
    # Optional metadata
    project_id: str = "default"  # For future multi-project support
    metadata: Dict[str, Any] = field(default_factory=dict)
    relationships: List[str] = field(default_factory=list)  # Related context IDs
    tags: List[str] = field(default_factory=list)          # Searchable tags
    ttl: Optional[int] = None                               # Time-to-live in seconds
    
    # Compliance fields
    requires_audit: bool = True
    sensitivity_level: str = "internal"  # internal|confidential|public
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            'id': self.id,
            'type': self.type.value,
            'source': self.source,
            'timestamp': self.timestamp.isoformat(),
            'data': self.data,
            'project_id': self.project_id,
            'metadata': self.metadata,
            'relationships': self.relationships,
            'tags': self.tags,
            'ttl': self.ttl,
            'requires_audit': self.requires_audit,
            'sensitivity_level': self.sensitivity_level
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Context':
        """Create Context from dictionary."""
        data['type'] = ContextType(data['type'])
        data['timestamp'] = datetime.fromisoformat(data['timestamp'])
        return cls(**data)


@dataclass
class DocMetadata:
    """Lightweight metadata for existing documentation files."""
    
    # File reference
    path: str                       # Path to actual .md file
    doc_type: str                   # Inferred type (readme, api_spec, etc.)
    last_analyzed: datetime         # When we last analyzed this doc
    
    # Intelligence data
    quality_scores: Dict[str, float] = field(default_factory=dict)
    staleness_indicators: List[str] = field(default_factory=list)
    
    # Claude-generated description
    description: Optional[str] = None  # 1-2 sentence summary of file purpose
    
    # Relationships
    linked_contexts: List[str] = field(default_factory=list)    # Related events
    linked_docs: List[str] = field(default_factory=list)        # Related docs
    dependencies: Dict[str, List[str]] = field(default_factory=dict)  # Code dependencies
    
    # Update tracking
    pending_updates: List[Dict[str, Any]] = field(default_factory=list)
    
    def needs_update(self) -> bool:
        """Check if document likely needs updating."""
        return len(self.staleness_indicators) > 0 or len(self.pending_updates) > 0


@dataclass
class CodeMetadata:
    """Metadata for source code files."""
    
    path: str
    language: str
    last_modified: datetime
    
    # Claude-generated description
    description: Optional[str] = None  # 1-2 sentence summary of file purpose
    
    # Extracted elements
    classes: List[str] = field(default_factory=list)
    functions: List[str] = field(default_factory=list)
    imports: List[str] = field(default_factory=list)
    exports: List[str] = field(default_factory=list)
    
    # Documentation
    docstrings: Dict[str, str] = field(default_factory=dict)
    comments: List[str] = field(default_factory=list)
    
    # Metrics
    lines_of_code: int = 0
    complexity_score: float = 0.0


@dataclass
class ProjectIndex:
    """Complete project understanding."""
    
    # File mappings
    doc_files: Dict[str, DocMetadata] = field(default_factory=dict)
    code_files: Dict[str, CodeMetadata] = field(default_factory=dict)
    
    # Claude-generated folder descriptions
    folder_descriptions: Dict[str, str] = field(default_factory=dict)  # folder path -> description
    
    # Concept mappings
    concepts: Dict[str, List[str]] = field(default_factory=dict)  # concept -> file paths
    functions: Dict[str, str] = field(default_factory=dict)       # function -> file path
    classes: Dict[str, str] = field(default_factory=dict)         # class -> file path
    
    # Relationships
    dependencies: Dict[str, List[str]] = field(default_factory=dict)  # file -> dependent files
    references: Dict[str, List[str]] = field(default_factory=dict)    # doc -> code references
    
    # Learned patterns
    naming_conventions: Dict[str, str] = field(default_factory=dict)
    architectural_patterns: List[str] = field(default_factory=list)
    
    # Quick lookups
    faq_mappings: Dict[str, str] = field(default_factory=dict)  # common questions -> answers
    index_timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class LocationResult:
    """Result of finding information in the project."""
    file: str
    line: int
    content: str
    confidence: float
    context: str  # surrounding context


@dataclass
class DocPattern:
    """Learned patterns from existing documentation."""
    
    # Structure patterns
    file_naming: Dict[str, str] = field(default_factory=dict)        # Pattern mappings
    section_headers: List[str] = field(default_factory=list)         # Common sections in order
    section_patterns: Dict[str, str] = field(default_factory=dict)   # Section name -> content pattern
    
    # Style patterns
    markdown_style: Dict[str, str] = field(default_factory=dict)     # Style preferences
    code_block_style: str = "```"                                    # Language tags used
    list_style: str = "-"                                            # Bullet point style
    
    # Content patterns
    common_phrases: Dict[str, int] = field(default_factory=dict)     # Phrase -> frequency
    terminology: Dict[str, str] = field(default_factory=dict)        # Project-specific terms
    update_triggers: Dict[str, List[str]] = field(default_factory=dict)  # Code pattern -> doc sections
    
    # Quality patterns
    avg_section_length: Dict[str, int] = field(default_factory=dict) # Expected section sizes
    required_sections: List[str] = field(default_factory=list)       # Sections that should exist
    optional_sections: List[str] = field(default_factory=list)       # Sections that might exist


class ContextManager:
    """Central context orchestration for agent-workflow system."""
    
    def __init__(self, base_dir: str = None):
        """Initialize Context Manager with storage directory."""
        # Default to ./aw_docs in current project
        if base_dir is None:
            base_dir = Path.cwd() / "aw_docs"
        
        self.base_dir = Path(base_dir)
        self.storage_dir = self.base_dir / "context_store"
        
        # In-memory caches
        self.contexts: Dict[str, Context] = {}
        self.doc_metadata: Dict[str, DocMetadata] = {}
        self.patterns: Dict[str, int] = {}
        self.audit_log: List[Dict[str, Any]] = []
        self.project_index: Optional[ProjectIndex] = None
        
        # Initialize storage
        self._init_storage()
        self._load_existing_data()
        
        # Optional AI tools
        self._claude_tools = None
    
    def _init_storage(self):
        """Initialize directory structure."""
        # Context storage
        (self.storage_dir / "contexts" / "active").mkdir(parents=True, exist_ok=True)
        (self.storage_dir / "contexts" / "archive").mkdir(parents=True, exist_ok=True)
        (self.storage_dir / "indices").mkdir(parents=True, exist_ok=True)
        
        # Doc metadata storage
        (self.storage_dir / "doc_metadata" / "metadata").mkdir(parents=True, exist_ok=True)
        (self.storage_dir / "doc_metadata" / "patterns").mkdir(parents=True, exist_ok=True)
    
    def _load_existing_data(self):
        """Load existing contexts and metadata from storage."""
        # For v1, just load active contexts
        active_dir = self.storage_dir / "contexts" / "active"
        for date_dir in active_dir.glob("*"):
            if date_dir.is_dir():
                for context_file in date_dir.glob("*.json"):
                    try:
                        with open(context_file, 'r') as f:
                            data = json.load(f)
                            context = Context.from_dict(data)
                            self.contexts[context.id] = context
                    except Exception as e:
                        print(f"Error loading context {context_file}: {e}")
    
    # Core context operations
    def add_context(self, context: Context) -> str:
        """Add new context to the system."""
        # Add to memory
        self.contexts[context.id] = context
        
        # Persist to disk
        date_str = context.timestamp.strftime("%Y-%m-%d")
        context_dir = self.storage_dir / "contexts" / "active" / date_str
        context_dir.mkdir(parents=True, exist_ok=True)
        
        context_file = context_dir / f"{context.id}.json"
        with open(context_file, 'w') as f:
            json.dump(context.to_dict(), f, indent=2)
        
        # Add audit entry
        self._audit_operation("add_context", context.id, True)
        
        # Trigger pattern detection (async in production)
        self._detect_patterns([context])
        
        return context.id
    
    def get_context(self, context_id: str) -> Optional[Context]:
        """Retrieve context by ID."""
        return self.contexts.get(context_id)
    
    def query_contexts(self, 
                      query: str = None,
                      context_type: ContextType = None,
                      source: str = None,
                      since: datetime = None,
                      limit: int = 10) -> List[Context]:
        """Search contexts with filters."""
        results = list(self.contexts.values())
        
        # Apply filters
        if context_type:
            results = [c for c in results if c.type == context_type]
        if source:
            results = [c for c in results if c.source == source]
        if since:
            results = [c for c in results if c.timestamp >= since]
        if query:
            # Simple text search in data
            query_lower = query.lower()
            results = [c for c in results if 
                      query_lower in str(c.data).lower() or
                      query_lower in ' '.join(c.tags).lower()]
        
        # Sort by timestamp (newest first) and limit
        results.sort(key=lambda c: c.timestamp, reverse=True)
        return results[:limit]
    
    # Bootstrap features
    def log_decision(self, decision: str, reasoning: str) -> str:
        """Track development decisions for self-improvement."""
        context = Context(
            id=str(uuid.uuid4()),
            type=ContextType.DECISION,
            source="human",
            timestamp=datetime.now(),
            data={
                "decision": decision,
                "reasoning": reasoning
            },
            tags=["bootstrap", "decision"],
            metadata={
                "tokens": len(decision + reasoning) // 4  # Rough estimate
            }
        )
        return self.add_context(context)
    
    def log_error(self, error: str, context_info: Dict[str, Any] = None) -> str:
        """Log errors for pattern analysis."""
        context = Context(
            id=str(uuid.uuid4()),
            type=ContextType.ERROR,
            source="system",
            timestamp=datetime.now(),
            data={
                "error": error,
                "context": context_info or {}
            },
            tags=["error", "pattern-source"]
        )
        return self.add_context(context)
    
    def suggest_next_task(self) -> List[Dict[str, Any]]:
        """Generate task suggestions based on patterns."""
        suggestions = []
        
        # Analyze recent contexts
        recent = self.query_contexts(
            since=datetime.now() - timedelta(hours=24),
            limit=50
        )
        
        # Count context types
        type_counts = Counter(c.type for c in recent)
        
        # Simple heuristics for v1
        if type_counts[ContextType.ERROR] > 3:
            suggestions.append({
                "task": "Add error handling",
                "reason": f"Detected {type_counts[ContextType.ERROR]} errors in last 24h",
                "confidence": 0.8
            })
        
        if type_counts[ContextType.DECISION] > 5:
            suggestions.append({
                "task": "Document decisions in CLAUDE.md",
                "reason": "Multiple decisions made, should be documented",
                "confidence": 0.7
            })
        
        # Check for missing persistence
        if len(self.contexts) > 20 and not self._has_persistence():
            suggestions.append({
                "task": "Implement persistence",
                "reason": "Growing context count needs reliable storage",
                "confidence": 0.9
            })
        
        return suggestions
    
    # Pattern detection
    def _detect_patterns(self, contexts: List[Context]):
        """Simple pattern detection for v1."""
        for context in contexts:
            # Extract features
            if context.type == ContextType.DECISION:
                # Track decision keywords
                decision = context.data.get('decision', '').lower()
                for word in decision.split():
                    if len(word) > 4:  # Skip short words
                        self.patterns[f"decision_word:{word}"] = \
                            self.patterns.get(f"decision_word:{word}", 0) + 1
            
            elif context.type == ContextType.ERROR:
                # Track error patterns
                error = context.data.get('error', '')
                error_type = type(error).__name__ if not isinstance(error, str) else 'string'
                self.patterns[f"error_type:{error_type}"] = \
                    self.patterns.get(f"error_type:{error_type}", 0) + 1
    
    def get_patterns(self, min_occurrences: int = 3) -> Dict[str, int]:
        """Get significant patterns."""
        return {k: v for k, v in self.patterns.items() if v >= min_occurrences}
    
    # Utility methods
    def _audit_operation(self, operation: str, target: str, success: bool):
        """Add audit log entry."""
        self.audit_log.append({
            "timestamp": datetime.now().isoformat(),
            "operation": operation,
            "target": target,
            "success": success
        })
    
    def _has_persistence(self) -> bool:
        """Check if persistence is properly configured."""
        return (self.storage_dir / "contexts" / "active").exists()
    
    def get_stats(self) -> Dict[str, Any]:
        """Get current statistics."""
        type_counts = Counter(c.type for c in self.contexts.values())
        return {
            "total_contexts": len(self.contexts),
            "by_type": {t.value: type_counts[t] for t in ContextType},
            "patterns_detected": len(self.patterns),
            "significant_patterns": len(self.get_patterns()),
            "audit_entries": len(self.audit_log),
            "docs_analyzed": len(self.doc_metadata)
        }
    
    # Documentation Intelligence Features
    def analyze_doc(self, doc_path: str) -> DocMetadata:
        """Analyze a documentation file and extract patterns."""
        path = Path(doc_path)
        if not path.exists() or not path.suffix == '.md':
            raise ValueError(f"Invalid markdown file: {doc_path}")
        
        # Read content
        content = path.read_text()
        
        # Create or update metadata
        metadata = self.doc_metadata.get(doc_path, DocMetadata(
            path=doc_path,
            doc_type=self._infer_doc_type(doc_path),
            last_analyzed=datetime.now()
        ))
        
        # Calculate quality scores
        metadata.quality_scores = self._calculate_quality_scores(content)
        
        # Check for staleness indicators
        metadata.staleness_indicators = self._check_staleness(content, metadata)
        
        # Store metadata
        self.doc_metadata[doc_path] = metadata
        self._save_doc_metadata(metadata)
        
        return metadata
    
    def learn_doc_patterns(self, doc_paths: List[str] = None) -> DocPattern:
        """Learn documentation patterns from existing files."""
        patterns = DocPattern()
        
        # If no paths specified, find all markdown files
        if doc_paths is None:
            doc_paths = []
            for root, _, files in os.walk("docs"):
                for file in files:
                    if file.endswith('.md'):
                        doc_paths.append(os.path.join(root, file))
        
        # Analyze each document
        for doc_path in doc_paths:
            try:
                content = Path(doc_path).read_text()
                
                # Extract section headers
                headers = re.findall(r'^#{1,6}\s+(.+)$', content, re.MULTILINE)
                for header in headers:
                    if header not in patterns.section_headers:
                        patterns.section_headers.append(header)
                
                # Detect markdown style
                if '**' in content:
                    patterns.markdown_style['bold'] = '**'
                elif '__' in content:
                    patterns.markdown_style['bold'] = '__'
                
                # Detect list style
                if re.search(r'^\s*-\s+', content, re.MULTILINE):
                    patterns.list_style = '-'
                elif re.search(r'^\s*\*\s+', content, re.MULTILINE):
                    patterns.list_style = '*'
                
                # Extract common phrases (3+ words appearing multiple times)
                words = re.findall(r'\b\w+\b', content.lower())
                for i in range(len(words) - 2):
                    phrase = ' '.join(words[i:i+3])
                    if len(phrase) > 10:  # Skip very short phrases
                        patterns.common_phrases[phrase] = patterns.common_phrases.get(phrase, 0) + 1
                
            except Exception as e:
                print(f"Error analyzing {doc_path}: {e}")
        
        # Filter common phrases to significant ones
        patterns.common_phrases = {k: v for k, v in patterns.common_phrases.items() if v >= 3}
        
        # Save patterns
        self._save_patterns(patterns)
        
        # Log the learning
        self.log_decision(
            f"Learned documentation patterns from {len(doc_paths)} files",
            f"Found {len(patterns.section_headers)} unique headers, {len(patterns.common_phrases)} common phrases"
        )
        
        return patterns
    
    def suggest_doc_updates(self, context: Context) -> List[Dict[str, Any]]:
        """Suggest documentation updates based on context."""
        suggestions = []
        
        # Check if this is a code change
        if context.type == ContextType.CODE_CHANGE:
            affected_files = context.data.get('files', [])
            
            for file in affected_files:
                # Find related documentation
                related_docs = self._find_related_docs(file)
                
                for doc_path in related_docs:
                    metadata = self.doc_metadata.get(doc_path)
                    if metadata:
                        suggestion = {
                            'doc_path': doc_path,
                            'reason': f"Code change in {file}",
                            'update_type': 'review_needed',
                            'confidence': 0.7,
                            'sections': self._identify_affected_sections(file, doc_path)
                        }
                        suggestions.append(suggestion)
        
        # Check if this is a decision that should be documented
        elif context.type == ContextType.DECISION:
            if 'architecture' in context.data.get('decision', '').lower():
                suggestions.append({
                    'doc_path': 'docs/architecture/README.md',
                    'reason': 'Architecture decision should be documented',
                    'update_type': 'add_decision',
                    'confidence': 0.8,
                    'content': context.data
                })
        
        return suggestions
    
    def calculate_doc_quality(self, doc_path: str) -> Dict[str, float]:
        """Calculate documentation quality metrics."""
        try:
            content = Path(doc_path).read_text()
            
            scores = {
                'completeness': 0.0,
                'clarity': 0.0,
                'consistency': 0.0,
                'staleness': 0.0
            }
            
            # Completeness - check for standard sections
            expected_sections = ['Overview', 'Usage', 'API', 'Examples']
            found_sections = len([s for s in expected_sections if s.lower() in content.lower()])
            scores['completeness'] = found_sections / len(expected_sections)
            
            # Clarity - check for code examples and clear structure
            code_blocks = len(re.findall(r'```', content))
            headers = len(re.findall(r'^#{1,6}\s+', content, re.MULTILINE))
            scores['clarity'] = min(1.0, (code_blocks + headers) / 10.0)
            
            # Consistency - compare with learned patterns
            # For now, simple check
            scores['consistency'] = 0.7 if self.doc_metadata.get(doc_path) else 0.5
            
            # Staleness - check last modified vs related code changes
            metadata = self.doc_metadata.get(doc_path)
            if metadata and metadata.last_analyzed:
                days_old = (datetime.now() - metadata.last_analyzed).days
                scores['staleness'] = max(0.0, 1.0 - (days_old / 30.0))
            
            return scores
            
        except Exception as e:
            print(f"Error calculating quality for {doc_path}: {e}")
            return {'error': 1.0}
    
    # Helper methods for documentation intelligence
    def _infer_doc_type(self, doc_path: str) -> str:
        """Infer document type from path and name."""
        path_lower = doc_path.lower()
        if 'readme' in path_lower:
            return 'readme'
        elif 'api' in path_lower or 'specification' in path_lower:
            return 'api_spec'
        elif 'guide' in path_lower or 'tutorial' in path_lower:
            return 'guide'
        elif 'changelog' in path_lower:
            return 'changelog'
        else:
            return 'general'
    
    def _calculate_quality_scores(self, content: str) -> Dict[str, float]:
        """Calculate quality scores for document content."""
        scores = {
            'completeness': 0.0,
            'clarity': 0.0,
            'consistency': 0.0,
            'staleness': 0.0
        }
        
        # Completeness - check for standard sections
        expected_sections = ['Overview', 'Usage', 'API', 'Examples']
        found_sections = len([s for s in expected_sections if s.lower() in content.lower()])
        scores['completeness'] = found_sections / len(expected_sections)
        
        # Clarity - check for code examples and clear structure
        code_blocks = len(re.findall(r'```', content))
        headers = len(re.findall(r'^#{1,6}\s+', content, re.MULTILINE))
        scores['clarity'] = min(1.0, (code_blocks + headers) / 10.0)
        
        # Consistency - simple check for now
        scores['consistency'] = 0.7
        
        # Staleness - default to fresh for now
        scores['staleness'] = 1.0
        
        return scores
    
    def _check_staleness(self, content: str, metadata: DocMetadata) -> List[str]:
        """Check for staleness indicators."""
        indicators = []
        
        # Check for TODOs
        if 'TODO' in content or 'FIXME' in content:
            indicators.append('contains_todos')
        
        # Check for outdated version numbers
        if re.search(r'v\d+\.\d+', content):
            indicators.append('version_numbers_found')
        
        return indicators
    
    def _find_related_docs(self, code_file: str) -> List[str]:
        """Find documentation related to a code file."""
        related = []
        
        # Simple heuristic: look for docs with similar names
        base_name = Path(code_file).stem
        for doc_path in self.doc_metadata.keys():
            if base_name.lower() in doc_path.lower():
                related.append(doc_path)
        
        return related
    
    def _identify_affected_sections(self, code_file: str, doc_path: str) -> List[str]:
        """Identify which sections of a doc might need updating."""
        # Simple heuristic for now
        if 'api' in code_file.lower():
            return ['API', 'Usage', 'Examples']
        else:
            return ['Overview', 'Implementation']
    
    def _save_doc_metadata(self, metadata: DocMetadata):
        """Save document metadata to disk."""
        metadata_file = self.storage_dir / "doc_metadata" / "metadata" / f"{Path(metadata.path).stem}.json"
        metadata_file.parent.mkdir(parents=True, exist_ok=True)
        
        data = {
            'path': metadata.path,
            'doc_type': metadata.doc_type,
            'last_analyzed': metadata.last_analyzed.isoformat(),
            'quality_scores': metadata.quality_scores,
            'staleness_indicators': metadata.staleness_indicators,
            'linked_contexts': metadata.linked_contexts,
            'linked_docs': metadata.linked_docs,
            'dependencies': metadata.dependencies,
            'pending_updates': metadata.pending_updates
        }
        
        with open(metadata_file, 'w') as f:
            json.dump(data, f, indent=2)
    
    def _save_patterns(self, patterns: DocPattern):
        """Save learned patterns to disk."""
        patterns_file = self.storage_dir / "doc_metadata" / "patterns" / "global_patterns.json"
        patterns_file.parent.mkdir(parents=True, exist_ok=True)
        
        data = {
            'file_naming': patterns.file_naming,
            'section_headers': patterns.section_headers,
            'section_patterns': patterns.section_patterns,
            'markdown_style': patterns.markdown_style,
            'code_block_style': patterns.code_block_style,
            'list_style': patterns.list_style,
            'common_phrases': patterns.common_phrases,
            'terminology': patterns.terminology,
            'update_triggers': patterns.update_triggers,
            'avg_section_length': patterns.avg_section_length,
            'required_sections': patterns.required_sections,
            'optional_sections': patterns.optional_sections
        }
        
        with open(patterns_file, 'w') as f:
            json.dump(data, f, indent=2)
    
    # Project Initialization Features
    def initialize_project(self, project_root: str = ".", skip_descriptions: bool = False) -> Dict[str, Any]:
        """
        Initialize project by scanning all documentation and code.
        Builds comprehensive metadata layer for intelligent routing.
        
        Args:
            project_root: Root directory of project to scan
            skip_descriptions: Skip generating Claude descriptions for faster indexing
            
        Returns:
            Summary of initialization results
        """
        start_time = datetime.now()
        root_path = Path(project_root).resolve()
        self.skip_descriptions = skip_descriptions
        
        # Create new project index
        self.project_index = ProjectIndex()
        
        # Scan documentation
        doc_count = self._scan_documentation(root_path)
        
        # Scan code
        code_count = self._scan_code(root_path)
        
        # Build concept mappings
        concepts_count = self._build_concept_mappings()
        
        # Extract relationships
        relationships_count = self._extract_relationships()
        
        # Generate folder descriptions
        self._generate_folder_descriptions(root_path)
        
        # Save index
        self._save_project_index()
        
        # Log the initialization
        self.log_decision(
            f"Initialized project at {root_path}",
            f"Scanned {doc_count} docs, {code_count} code files, found {concepts_count} concepts"
        )
        
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        return {
            "success": True,
            "project_root": str(root_path),
            "files_scanned": doc_count + code_count,
            "docs_scanned": doc_count,
            "code_scanned": code_count,
            "concepts_mapped": concepts_count,
            "relationships": relationships_count,
            "duration_seconds": duration,
            "index_timestamp": self.project_index.index_timestamp.isoformat()
        }
    
    def _scan_documentation(self, root_path: Path) -> int:
        """Scan all documentation files."""
        doc_count = 0
        files_by_folder = {}
        
        # First pass: collect all doc files and analyze metadata
        for md_file in root_path.rglob("*.md"):
            # Skip hidden and build directories
            if any(part.startswith('.') for part in md_file.parts):
                continue
            if any(part in ['node_modules', 'build', 'dist', 'venv'] for part in md_file.parts):
                continue
            
            try:
                # Analyze the document
                metadata = self.analyze_doc(str(md_file))
                self.project_index.doc_files[str(md_file)] = metadata
                
                # Read content for concept extraction and batch processing
                content = md_file.read_text()
                
                # Extract concepts from content
                self._extract_concepts_from_text(content, str(md_file))
                
                # Group by folder for batch description generation
                folder = str(md_file.parent)
                if folder not in files_by_folder:
                    files_by_folder[folder] = []
                files_by_folder[folder].append({
                    'path': str(md_file),
                    'content': content,
                    'type': 'doc'
                })
                
                doc_count += 1
            except Exception as e:
                print(f"Error scanning {md_file}: {e}")
        
        # Second pass: batch generate descriptions by folder
        if not getattr(self, 'skip_descriptions', False):
            try:
                tools = self.get_claude_tools()
                total_folders = len(files_by_folder)
                
                for idx, (folder_path, files) in enumerate(files_by_folder.items()):
                    print(f"Generating descriptions for folder {idx+1}/{total_folders}: {Path(folder_path).name}")
                    
                    try:
                        # Batch generate descriptions for all files in folder
                        descriptions = tools.generate_folder_descriptions_batch(folder_path, files)
                        
                        # Update metadata with generated descriptions
                        for file_path, description in descriptions.items():
                            if file_path in self.project_index.doc_files:
                                self.project_index.doc_files[file_path].description = description
                    
                    except Exception as e:
                        print(f"Batch generation failed for {folder_path}, falling back to individual: {e}")
                        # Fallback to individual generation
                        for file_info in files:
                            try:
                                desc = tools.generate_file_description(
                                    file_info['path'],
                                    file_info['content'][:5000],
                                    file_type="doc"
                                )
                                if file_info['path'] in self.project_index.doc_files:
                                    self.project_index.doc_files[file_info['path']].description = desc
                            except:
                                # Final fallback
                                if file_info['path'] in self.project_index.doc_files:
                                    self.project_index.doc_files[file_info['path']].description = f"Documentation file: {Path(file_info['path']).name}"
            except:
                # If Claude tools not available, use simple descriptions
                for file_path, metadata in self.project_index.doc_files.items():
                    if not metadata.description:
                        metadata.description = f"Documentation file: {Path(file_path).name}"
        else:
            # Skip descriptions - use simple ones
            print("Skipping Claude descriptions for faster indexing...")
            for file_path, metadata in self.project_index.doc_files.items():
                metadata.description = f"Documentation file: {Path(file_path).name}"
        
        return doc_count
    
    def _scan_code(self, root_path: Path) -> int:
        """Scan all code files."""
        code_count = 0
        code_extensions = {'.py', '.js', '.ts', '.jsx', '.tsx', '.java', '.cpp', '.c', '.h', '.go', '.rs'}
        files_by_folder = {}
        
        # First pass: collect all code files and analyze metadata
        for code_file in root_path.rglob("*"):
            if not code_file.is_file() or code_file.suffix not in code_extensions:
                continue
            
            # Skip hidden and build directories
            if any(part.startswith('.') for part in code_file.parts):
                continue
            if any(part in ['node_modules', 'build', 'dist', 'venv', '__pycache__'] for part in code_file.parts):
                continue
            
            try:
                metadata = self._analyze_code_file(code_file)
                self.project_index.code_files[str(code_file)] = metadata
                
                # Map functions and classes
                for func in metadata.functions:
                    self.project_index.functions[func] = str(code_file)
                for cls in metadata.classes:
                    self.project_index.classes[cls] = str(code_file)
                
                # Read content for batch processing
                content = code_file.read_text()
                
                # Group by folder for batch description generation
                folder = str(code_file.parent)
                if folder not in files_by_folder:
                    files_by_folder[folder] = []
                files_by_folder[folder].append({
                    'path': str(code_file),
                    'content': content,
                    'type': 'code'
                })
                
                code_count += 1
            except Exception as e:
                print(f"Error scanning {code_file}: {e}")
        
        # Second pass: batch generate descriptions by folder
        if not getattr(self, 'skip_descriptions', False):
            try:
                tools = self.get_claude_tools()
                total_folders = len(files_by_folder)
                
                for idx, (folder_path, files) in enumerate(files_by_folder.items()):
                    print(f"Generating code descriptions for folder {idx+1}/{total_folders}: {Path(folder_path).name}")
                    
                    try:
                        # Batch generate descriptions for all files in folder
                        descriptions = tools.generate_folder_descriptions_batch(folder_path, files)
                        
                        # Update metadata with generated descriptions
                        for file_path, description in descriptions.items():
                            if file_path in self.project_index.code_files:
                                self.project_index.code_files[file_path].description = description
                    
                    except Exception as e:
                        print(f"Batch generation failed for {folder_path}, falling back to individual: {e}")
                        # Fallback to individual generation
                        for file_info in files:
                            try:
                                desc = tools.generate_file_description(
                                    file_info['path'],
                                    file_info['content'][:5000],
                                    file_type="code"
                                )
                                if file_info['path'] in self.project_index.code_files:
                                    self.project_index.code_files[file_info['path']].description = desc
                            except:
                                # Final fallback
                                if file_info['path'] in self.project_index.code_files:
                                    metadata = self.project_index.code_files[file_info['path']]
                                    self.project_index.code_files[file_info['path']].description = f"{metadata.language} source file with {len(metadata.functions)} functions."
            except:
                # If Claude tools not available, use simple descriptions
                for file_path, metadata in self.project_index.code_files.items():
                    if not metadata.description:
                        metadata.description = f"{metadata.language} source file with {len(metadata.functions)} functions."
        else:
            # Skip descriptions - use simple ones
            for file_path, metadata in self.project_index.code_files.items():
                metadata.description = f"{metadata.language} source file with {len(metadata.functions)} functions."
        
        return code_count
    
    def _analyze_code_file(self, file_path: Path) -> CodeMetadata:
        """Analyze a single code file."""
        metadata = CodeMetadata(
            path=str(file_path),
            language=self._detect_language(file_path.suffix),
            last_modified=datetime.fromtimestamp(file_path.stat().st_mtime)
        )
        
        content = file_path.read_text()
        lines = content.splitlines()
        metadata.lines_of_code = len(lines)
        
        if metadata.language == "python":
            self._analyze_python_file(content, metadata)
        elif metadata.language in ["javascript", "typescript"]:
            self._analyze_js_file(content, metadata)
        
        return metadata
    
    def _analyze_python_file(self, content: str, metadata: CodeMetadata):
        """Extract Python-specific metadata."""
        try:
            tree = ast.parse(content)
            
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    metadata.functions.append(node.name)
                    if ast.get_docstring(node):
                        metadata.docstrings[node.name] = ast.get_docstring(node)
                elif isinstance(node, ast.ClassDef):
                    metadata.classes.append(node.name)
                    if ast.get_docstring(node):
                        metadata.docstrings[node.name] = ast.get_docstring(node)
                elif isinstance(node, ast.Import):
                    for alias in node.names:
                        metadata.imports.append(alias.name)
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        metadata.imports.append(node.module)
        except:
            # If AST parsing fails, fall back to regex
            functions = re.findall(r'def\s+(\w+)\s*\(', content)
            classes = re.findall(r'class\s+(\w+)\s*[\(:]', content)
            metadata.functions.extend(functions)
            metadata.classes.extend(classes)
    
    def _analyze_js_file(self, content: str, metadata: CodeMetadata):
        """Extract JavaScript/TypeScript metadata."""
        # Simple regex-based extraction
        functions = re.findall(r'function\s+(\w+)\s*\(|const\s+(\w+)\s*=\s*(?:async\s*)?\(|(\w+)\s*:\s*(?:async\s*)?\(', content)
        classes = re.findall(r'class\s+(\w+)', content)
        imports = re.findall(r'import\s+.*?\s+from\s+[\'"](.+?)[\'"]', content)
        
        metadata.functions.extend([f for group in functions for f in group if f])
        metadata.classes.extend(classes)
        metadata.imports.extend(imports)
    
    def _detect_language(self, suffix: str) -> str:
        """Detect programming language from file extension."""
        language_map = {
            '.py': 'python',
            '.js': 'javascript',
            '.ts': 'typescript',
            '.jsx': 'javascript',
            '.tsx': 'typescript',
            '.java': 'java',
            '.cpp': 'cpp',
            '.c': 'c',
            '.h': 'c',
            '.go': 'go',
            '.rs': 'rust'
        }
        return language_map.get(suffix, 'unknown')
    
    def _extract_concepts_from_text(self, text: str, file_path: str):
        """Extract concepts from text content."""
        # Extract capitalized multi-word phrases as potential concepts
        concepts = re.findall(r'[A-Z][a-z]+(?:\s+[A-Z][a-z]+)+', text)
        
        # Also extract code-like terms
        code_terms = re.findall(r'`([^`]+)`', text)
        
        # Common technical concepts
        for concept in concepts + code_terms:
            if len(concept) > 2:  # Skip very short concepts
                if concept not in self.project_index.concepts:
                    self.project_index.concepts[concept] = []
                self.project_index.concepts[concept].append(file_path)
    
    def _build_concept_mappings(self) -> int:
        """Build concept-to-location mappings."""
        # Deduplicate concept locations
        for concept, locations in self.project_index.concepts.items():
            self.project_index.concepts[concept] = list(set(locations))
        
        # Build FAQ mappings for common questions
        self.project_index.faq_mappings.update({
            "error handling": self._find_files_containing(["error", "exception", "try", "catch"]),
            "authentication": self._find_files_containing(["auth", "login", "token", "jwt"]),
            "database": self._find_files_containing(["database", "sql", "query", "model"]),
            "api": self._find_files_containing(["api", "endpoint", "route", "rest"]),
            "testing": self._find_files_containing(["test", "spec", "jest", "pytest"]),
            "configuration": self._find_files_containing(["config", "settings", "env"]),
            "state management": self._find_files_containing(["state", "redux", "store", "context"]),
        })
        
        return len(self.project_index.concepts)
    
    def _find_files_containing(self, keywords: List[str]) -> str:
        """Find files containing any of the keywords."""
        files = set()
        
        # Search in doc files
        for path, metadata in self.project_index.doc_files.items():
            try:
                content = Path(path).read_text().lower()
                if any(keyword.lower() in content for keyword in keywords):
                    files.add(path)
            except:
                pass
        
        # Search in code files
        for path, metadata in self.project_index.code_files.items():
            path_lower = path.lower()
            if any(keyword.lower() in path_lower for keyword in keywords):
                files.add(path)
            
            # Check function and class names
            for func in metadata.functions:
                if any(keyword.lower() in func.lower() for keyword in keywords):
                    files.add(path)
                    break
        
        return ", ".join(sorted(files)[:5])  # Return top 5 files
    
    def _extract_relationships(self) -> int:
        """Extract relationships between files."""
        relationship_count = 0
        
        # Find code references in documentation
        for doc_path, doc_meta in self.project_index.doc_files.items():
            try:
                content = Path(doc_path).read_text()
                
                # Look for code file references
                for code_path in self.project_index.code_files.keys():
                    code_file = Path(code_path).name
                    if code_file in content:
                        if doc_path not in self.project_index.references:
                            self.project_index.references[doc_path] = []
                        self.project_index.references[doc_path].append(code_path)
                        relationship_count += 1
            except:
                pass
        
        # Find import dependencies
        for code_path, code_meta in self.project_index.code_files.items():
            dependencies = []
            for imp in code_meta.imports:
                # Try to resolve local imports
                for other_path in self.project_index.code_files.keys():
                    if imp in other_path:
                        dependencies.append(other_path)
            
            if dependencies:
                self.project_index.dependencies[code_path] = list(set(dependencies))
                relationship_count += len(dependencies)
        
        return relationship_count
    
    def _generate_folder_descriptions(self, root_path: Path):
        """Generate descriptions for all directories in the project."""
        if getattr(self, 'skip_descriptions', False):
            print("Skipping folder descriptions...")
            return
            
        try:
            tools = self.get_claude_tools()
            
            # Get all unique directories
            all_dirs = set()
            
            # Add root
            all_dirs.add(root_path)
            
            # Add all parent directories of files
            for file_path in self.project_index.doc_files.keys():
                path = Path(file_path)
                for parent in path.parents:
                    if parent >= root_path:  # Only include dirs within project
                        all_dirs.add(parent)
            
            for file_path in self.project_index.code_files.keys():
                path = Path(file_path)
                for parent in path.parents:
                    if parent >= root_path:  # Only include dirs within project
                        all_dirs.add(parent)
            
            # Generate descriptions for each directory
            for dir_path in sorted(all_dirs):
                # Get contents of this directory
                contents = []
                
                # Add files
                for file_path, metadata in self.project_index.doc_files.items():
                    if Path(file_path).parent == dir_path:
                        contents.append({
                            'name': Path(file_path).name,
                            'type': 'file',
                            'description': metadata.description or ''
                        })
                
                for file_path, metadata in self.project_index.code_files.items():
                    if Path(file_path).parent == dir_path:
                        contents.append({
                            'name': Path(file_path).name,
                            'type': 'file',
                            'description': metadata.description or ''
                        })
                
                # Add subdirectories
                for other_dir in all_dirs:
                    if other_dir.parent == dir_path and other_dir != dir_path:
                        contents.append({
                            'name': other_dir.name,
                            'type': 'directory',
                            'description': self.project_index.folder_descriptions.get(str(other_dir), '')
                        })
                
                # Generate description
                description = tools.generate_folder_description(str(dir_path), contents)
                self.project_index.folder_descriptions[str(dir_path)] = description
                
        except Exception as e:
            # If Claude tools not available, generate simple descriptions
            print(f"Generating simple folder descriptions: {e}")
            for dir_path in [root_path]:
                self.project_index.folder_descriptions[str(dir_path)] = "Project root directory."
    
    def _save_project_index(self):
        """Save project index to disk."""
        index_dir = self.storage_dir / "indices"
        index_dir.mkdir(parents=True, exist_ok=True)
        
        # Save main index
        index_file = index_dir / "project_index.json"
        index_data = {
            "index_timestamp": self.project_index.index_timestamp.isoformat(),
            "concepts": self.project_index.concepts,
            "functions": self.project_index.functions,
            "classes": self.project_index.classes,
            "dependencies": self.project_index.dependencies,
            "references": self.project_index.references,
            "naming_conventions": self.project_index.naming_conventions,
            "architectural_patterns": self.project_index.architectural_patterns,
            "faq_mappings": self.project_index.faq_mappings,
            "folder_descriptions": self.project_index.folder_descriptions
        }
        
        with open(index_file, 'w') as f:
            json.dump(index_data, f, indent=2)
        
        # Save concept map
        concept_file = index_dir / "concept_map.json"
        with open(concept_file, 'w') as f:
            json.dump(self.project_index.concepts, f, indent=2)
        
        # Save quick lookups
        lookup_file = index_dir / "quick_lookups.json"
        with open(lookup_file, 'w') as f:
            json.dump(self.project_index.faq_mappings, f, indent=2)
        
        # Save doc metadata
        doc_metadata_file = index_dir / "doc_metadata.json"
        doc_data = {}
        for path, meta in self.project_index.doc_files.items():
            doc_data[path] = {
                'path': meta.path,
                'doc_type': meta.doc_type,
                'last_analyzed': meta.last_analyzed.isoformat(),
                'description': meta.description,
                'quality_scores': meta.quality_scores,
                'staleness_indicators': meta.staleness_indicators,
                'linked_contexts': meta.linked_contexts,
                'linked_docs': meta.linked_docs,
                'dependencies': meta.dependencies,
                'pending_updates': meta.pending_updates,
                'needs_update': meta.needs_update()
            }
        with open(doc_metadata_file, 'w') as f:
            json.dump(doc_data, f, indent=2)
        
        # Save code metadata
        code_metadata_file = index_dir / "code_metadata.json"
        code_data = {}
        for path, meta in self.project_index.code_files.items():
            code_data[path] = {
                'path': meta.path,
                'language': meta.language,
                'last_modified': meta.last_modified.isoformat(),
                'description': meta.description,
                'classes': meta.classes,
                'functions': meta.functions,
                'imports': meta.imports,
                'exports': meta.exports,
                'docstrings': meta.docstrings,
                'comments': meta.comments,
                'lines_of_code': meta.lines_of_code,
                'complexity_score': meta.complexity_score
            }
        with open(code_metadata_file, 'w') as f:
            json.dump(code_data, f, indent=2)
    
    def find_information(self, query: str) -> List[LocationResult]:
        """
        Find where specific information lives in the project.
        Uses initialized metadata for fast lookups.
        
        Args:
            query: Natural language query
            
        Returns:
            Ranked list of file locations with confidence scores
        """
        if not self.project_index:
            # Try to load existing index
            self._load_project_index()
            if not self.project_index:
                raise ValueError("Project not initialized. Run initialize_project first.")
        
        results = []
        query_lower = query.lower()
        
        # Check FAQ mappings first
        for faq, locations in self.project_index.faq_mappings.items():
            if faq in query_lower:
                # Parse locations string back into list
                for loc in locations.split(", "):
                    if loc:
                        results.append(LocationResult(
                            file=loc,
                            line=0,
                            content=f"FAQ match: {faq}",
                            confidence=0.9,
                            context=f"Common question about {faq}"
                        ))
        
        # Search in concepts
        for concept, locations in self.project_index.concepts.items():
            if concept.lower() in query_lower or query_lower in concept.lower():
                for loc in locations:
                    results.append(LocationResult(
                        file=loc,
                        line=0,
                        content=f"Concept: {concept}",
                        confidence=0.8,
                        context=f"Contains information about {concept}"
                    ))
        
        # Search in function names
        for func, location in self.project_index.functions.items():
            if func.lower() in query_lower or any(word in func.lower() for word in query_lower.split()):
                results.append(LocationResult(
                    file=location,
                    line=0,
                    content=f"Function: {func}",
                    confidence=0.7,
                    context=f"Function {func} implementation"
                ))
        
        # Search in class names
        for cls, location in self.project_index.classes.items():
            if cls.lower() in query_lower or any(word in cls.lower() for word in query_lower.split()):
                results.append(LocationResult(
                    file=location,
                    line=0,
                    content=f"Class: {cls}",
                    confidence=0.7,
                    context=f"Class {cls} definition"
                ))
        
        # Sort by confidence and deduplicate
        seen = set()
        unique_results = []
        for result in sorted(results, key=lambda x: x.confidence, reverse=True):
            if result.file not in seen:
                seen.add(result.file)
                unique_results.append(result)
        
        return unique_results[:10]  # Return top 10 results
    
    def _load_project_index(self):
        """Load existing project index from disk."""
        index_file = self.storage_dir / "indices" / "project_index.json"
        if index_file.exists():
            with open(index_file, 'r') as f:
                data = json.load(f)
            
            self.project_index = ProjectIndex(
                concepts=data.get("concepts", {}),
                functions=data.get("functions", {}),
                classes=data.get("classes", {}),
                dependencies=data.get("dependencies", {}),
                references=data.get("references", {}),
                naming_conventions=data.get("naming_conventions", {}),
                architectural_patterns=data.get("architectural_patterns", []),
                faq_mappings=data.get("faq_mappings", {}),
                folder_descriptions=data.get("folder_descriptions", {}),
                index_timestamp=datetime.fromisoformat(data.get("index_timestamp", datetime.now().isoformat()))
            )
            
            # Load doc metadata
            doc_metadata_file = self.storage_dir / "indices" / "doc_metadata.json"
            if doc_metadata_file.exists():
                with open(doc_metadata_file, 'r') as f:
                    doc_data = json.load(f)
                    for path, data in doc_data.items():
                        self.project_index.doc_files[path] = DocMetadata(
                            path=data['path'],
                            doc_type=data['doc_type'],
                            last_analyzed=datetime.fromisoformat(data['last_analyzed']),
                            description=data.get('description'),
                            quality_scores=data.get('quality_scores', {}),
                            staleness_indicators=data.get('staleness_indicators', []),
                            linked_contexts=data.get('linked_contexts', []),
                            linked_docs=data.get('linked_docs', []),
                            dependencies=data.get('dependencies', {}),
                            pending_updates=data.get('pending_updates', [])
                        )
            
            # Load code metadata
            code_metadata_file = self.storage_dir / "indices" / "code_metadata.json"
            if code_metadata_file.exists():
                with open(code_metadata_file, 'r') as f:
                    code_data = json.load(f)
                    for path, data in code_data.items():
                        self.project_index.code_files[path] = CodeMetadata(
                            path=data['path'],
                            language=data['language'],
                            last_modified=datetime.fromisoformat(data['last_modified']),
                            description=data.get('description'),
                            classes=data.get('classes', []),
                            functions=data.get('functions', []),
                            imports=data.get('imports', []),
                            exports=data.get('exports', []),
                            docstrings=data.get('docstrings', {}),
                            comments=data.get('comments', []),
                            lines_of_code=data.get('lines_of_code', 0),
                            complexity_score=data.get('complexity_score', 0.0)
                        )
    
    def get_project_status(self) -> Dict[str, Any]:
        """Get current project initialization status."""
        if not self.project_index:
            self._load_project_index()
        
        if self.project_index:
            return {
                "initialized": True,
                "index_timestamp": self.project_index.index_timestamp.isoformat(),
                "total_concepts": len(self.project_index.concepts),
                "total_functions": len(self.project_index.functions),
                "total_classes": len(self.project_index.classes),
                "total_docs": len(self.project_index.doc_files),
                "total_code_files": len(self.project_index.code_files)
            }
        else:
            return {
                "initialized": False,
                "message": "Project not initialized. Run 'cm init' to scan project."
            }
    
    # AI-Enhanced Methods (optional)
    def get_claude_tools(self):
        """Get or initialize Claude tools for AI enhancements."""
        if self._claude_tools is None:
            # Try to import claude_tools from aw_docs
            sys.path.insert(0, str(self.base_dir))
            try:
                from claude_tools import ClaudeTools
                self._claude_tools = ClaudeTools(self)
            except ImportError:
                raise ImportError("claude_tools.py not found in aw_docs/")
        return self._claude_tools
    
    def explain_with_ai(self, query: str) -> str:
        """Use AI to explain a concept or answer a question."""
        tools = self.get_claude_tools()
        return tools.explain_with_context(query)
    
    def generate_doc_with_ai(self, file_path: str) -> str:
        """Generate documentation for a file using AI."""
        tools = self.get_claude_tools()
        return tools.generate_documentation(file_path)
    
    def analyze_patterns_with_ai(self) -> Dict[str, Any]:
        """Deep pattern analysis using AI."""
        tools = self.get_claude_tools()
        return tools.analyze_patterns_deep()