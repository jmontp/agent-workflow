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
import time


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


@dataclass
class TaskAnalysis:
    """Analysis of a task to determine what context is needed."""
    
    keywords: List[str]          # Key terms extracted from the task
    actions: List[str]           # Verbs/actions to be performed
    concepts: List[str]          # Domain concepts mentioned
    file_patterns: List[str]     # File types/patterns likely needed
    estimated_scope: str         # 'small', 'medium', 'large', 'unknown'


@dataclass
class ContextItem:
    """Individual item of context for an agent task."""
    
    type: str                    # 'file', 'function', 'class', 'context', 'doc_section', 'folder_desc'
    path: str                    # File path or identifier
    content: str                 # Actual content
    relevance_score: float       # How relevant to the task (0-1)
    tokens: int                  # Token count for context management
    metadata: Dict[str, Any]     # Additional item-specific metadata


@dataclass
class ContextCollection:
    """Complete context collection for a specific task."""
    
    task_description: str        # Original task description
    task_analysis: TaskAnalysis  # Analysis of the task
    items: List[ContextItem]     # All context items
    total_tokens: int            # Total token count
    summary: str                 # Executive summary of context
    suggestions: List[str]       # Suggestions for agent
    truncated: bool              # Whether context was truncated
    collection_time_ms: int      # Time taken to collect context
    
    def format_for_agent(self) -> str:
        """Format all collected context into the exact format an agent would receive."""
        lines = []
        
        # Header
        lines.append(f"# Task: {self.task_description}")
        lines.append("")
        
        # Task Analysis
        lines.append("## Task Analysis")
        lines.append(f"Keywords: {', '.join(self.task_analysis.keywords)}")
        lines.append(f"Actions: {', '.join(self.task_analysis.actions)}")
        lines.append(f"Concepts: {', '.join(self.task_analysis.concepts[:10])}")  # Limit concepts shown
        lines.append(f"Estimated Scope: {self.task_analysis.estimated_scope}")
        lines.append("")
        
        # Group items by type
        items_by_type = {
            'context': [],
            'file': [],
            'function': [],
            'class': [],
            'doc_section': [],
            'folder_desc': []
        }
        
        for item in self.items:
            items_by_type[item.type].append(item)
        
        # Add code files
        code_items = items_by_type['file'] + items_by_type['function'] + items_by_type['class']
        if code_items:
            lines.append(f"## Code Files ({len(code_items)} items, {sum(i.tokens for i in code_items)} tokens)")
            for item in code_items:
                lines.append(f"\n### {item.path}")
                lines.append(item.content[:500] + "..." if len(item.content) > 500 else item.content)
            lines.append("")
        
        # Add summary
        lines.append("---")
        lines.append(f"Total tokens: {self.total_tokens}")
        lines.append(f"Collection time: {self.collection_time_ms}ms")
        
        if self.truncated:
            lines.append("\n⚠️ CONTEXT WAS TRUNCATED - Some relevant items may have been excluded")
        
        return "\n".join(lines)


@dataclass 
class ContextManagerConfig:
    """Configuration for Context Manager behavior."""
    
    use_claude_analysis: bool = True          # Enable Claude-based task analysis
    claude_timeout_seconds: int = 5           # Timeout for Claude API calls
    claude_cache_ttl_hours: int = 24          # Cache TTL for Claude responses
    max_claude_cost_per_task: float = 0.05    # Max cost per task in USD
    fallback_to_heuristic: bool = True        # Fallback if Claude fails
    enable_claude_reranking: bool = True      # Use Claude to re-rank results
    claude_rerank_top_n: int = 20             # Number of items to re-rank
    
    # Cache settings
    cache_claude_responses: bool = True       # Enable caching
    cache_dir: Optional[Path] = None          # Cache directory (auto-set if None)


class ContextManager:
    """Central context orchestration for agent-workflow system."""
    
    STOPWORDS = {
        'the', 'is', 'at', 'which', 'on', 'a', 'an', 'as', 'are', 'was', 'were', 
        'been', 'be', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 
        'should', 'could', 'may', 'might', 'must', 'can', 'this', 'that', 'these', 
        'those', 'i', 'you', 'he', 'she', 'it', 'we', 'they', 'them', 'their', 
        'what', 'which', 'who', 'when', 'where', 'why', 'how', 'all', 'each', 
        'every', 'some', 'any', 'few', 'more', 'most', 'other', 'into', 'through', 
        'during', 'before', 'after', 'above', 'below', 'to', 'from', 'up', 'down', 
        'in', 'out', 'on', 'off', 'over', 'under', 'again', 'further', 'then', 
        'once', 'and', 'or', 'but', 'if', 'because', 'as', 'until', 'while', 'of', 
        'at', 'by', 'for', 'with', 'about', 'against', 'between', 'into', 'through', 
        'during', 'before', 'after', 'above', 'below', 'to', 'from', 'up', 'down', 
        'in', 'out', 'on', 'off', 'over', 'under', 'again', 'further', 'then', 'once'
    }
    
    def __init__(self, base_dir: str = None, config: Optional[ContextManagerConfig] = None):
        """Initialize Context Manager with storage directory."""
        # Default to ./aw_docs in current project
        if base_dir is None:
            base_dir = Path.cwd() / "aw_docs"
        
        self.base_dir = Path(base_dir)
        self.storage_dir = self.base_dir / "context_store"
        
        # Configuration
        self.config = config or ContextManagerConfig()
        if self.config.cache_dir is None:
            self.config.cache_dir = self.storage_dir / "claude_cache"
        
        # In-memory caches
        self.contexts: Dict[str, Context] = {}
        self.doc_metadata: Dict[str, DocMetadata] = {}
        self.patterns: Dict[str, int] = {}
        self.audit_log: List[Dict[str, Any]] = []
        self.project_index: Optional[ProjectIndex] = None
        
        # Claude response cache
        self._claude_cache: Dict[str, Any] = {}
        
        # Initialize storage
        self._init_storage()
        self._load_existing_data()
        self._load_project_index()
        
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
                    # Extract concepts from function names
                    self._extract_concepts_from_identifier(func, str(code_file))
                for cls in metadata.classes:
                    self.project_index.classes[cls] = str(code_file)
                    # Extract concepts from class names
                    self._extract_concepts_from_identifier(cls, str(code_file))
                
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
        # Extract code-like terms in backticks
        code_terms = re.findall(r'`([^`]+)`', text)
        
        # Extract capitalized phrases but limit to 5 words max
        # This prevents capturing entire markdown sections
        capitalized_phrases = re.findall(r'[A-Z][a-z]+(?:\s+[A-Z][a-z]+){0,4}', text)
        
        # Extract technical terms that are commonly used
        technical_patterns = [
            r'\b([A-Z]+[a-z]*[A-Z]+[a-zA-Z]*)\b',  # CamelCase like "ContextManager"
            r'\b([a-z]+_[a-z]+(?:_[a-z]+)*)\b',     # snake_case like "context_manager"
            r'\b([A-Z]+(?:_[A-Z]+)+)\b',            # CONSTANTS like "MAX_TOKENS"
        ]
        
        technical_terms = []
        for pattern in technical_patterns:
            technical_terms.extend(re.findall(pattern, text))
        
        # Combine all potential concepts
        all_concepts = set()
        
        # Add code terms (limit length)
        for term in code_terms:
            if 2 < len(term) <= 50 and ' ' not in term.strip():
                all_concepts.add(term.strip())
        
        # Add capitalized phrases (filter out common non-technical phrases)
        common_phrases = {'The', 'This', 'These', 'Those', 'That', 'When', 'Where', 'What', 'How', 'Why'}
        for phrase in capitalized_phrases:
            words = phrase.split()
            if (len(phrase) > 2 and 
                len(phrase) <= 50 and 
                len(words) <= 5 and
                words[0] not in common_phrases):
                all_concepts.add(phrase)
        
        # Add technical terms
        for term in technical_terms:
            if 2 < len(term) <= 50:
                all_concepts.add(term)
        
        # Store concepts
        for concept in all_concepts:
            if concept not in self.project_index.concepts:
                self.project_index.concepts[concept] = []
            if file_path not in self.project_index.concepts[concept]:
                self.project_index.concepts[concept].append(file_path)
    
    def _extract_concepts_from_identifier(self, identifier: str, file_path: str):
        """Extract concepts from code identifiers (function/class names)."""
        # The identifier itself is a concept if it's meaningful
        if len(identifier) > 2:
            if identifier not in self.project_index.concepts:
                self.project_index.concepts[identifier] = []
            if file_path not in self.project_index.concepts[identifier]:
                self.project_index.concepts[identifier].append(file_path)
        
        # Split camelCase and PascalCase
        parts = re.findall(r'[A-Z]?[a-z]+|[A-Z]+(?=[A-Z][a-z]|\b)', identifier)
        
        # Split snake_case
        if '_' in identifier:
            parts.extend(identifier.split('_'))
        
        # Add meaningful parts as concepts (filter out common words)
        common_words = {'get', 'set', 'is', 'has', 'add', 'remove', 'update', 'delete', 
                       'init', 'main', 'test', 'handle', 'process', 'to', 'from', 'of', 
                       'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'for'}
        
        for part in parts:
            part_lower = part.lower()
            if len(part) > 2 and part_lower not in common_words:
                # Store the part in its original case if it's meaningful
                concept = part if part[0].isupper() else part_lower
                if concept not in self.project_index.concepts:
                    self.project_index.concepts[concept] = []
                if file_path not in self.project_index.concepts[concept]:
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
    
    async def _analyze_task_with_claude(self, task_description: str) -> Optional[TaskAnalysis]:
        """Use Claude to analyze task and extract meaningful information."""
        if not self.config.use_claude_analysis:
            return None
            
        # Check cache first
        cache_key = f"task_analysis:{task_description}"
        if self.config.cache_claude_responses and cache_key in self._claude_cache:
            cached = self._claude_cache[cache_key]
            # Check if cache is still valid
            if (datetime.now() - cached['timestamp']).total_seconds() < self.config.claude_cache_ttl_hours * 3600:
                return cached['result']
        
        try:
            # Get Claude tools
            tools = self.get_claude_tools()
            if not tools:
                return None
                
            # Create prompt for Claude
            prompt = f'''Analyze this software development task and extract key information.

Task: "{task_description}"

Extract and return as JSON:
1. primary_intent: What is the user trying to accomplish? (one sentence)
2. keywords: List of important technical terms (max 10)
3. actions: What actions need to be taken? (e.g., "fix", "implement", "refactor")
4. concepts: Technical concepts and entities involved (e.g., "authentication", "database", "UI")
5. file_patterns: Likely file types/patterns needed (e.g., "*test*.py", "*.config.js", "*controller*")
6. estimated_scope: "narrow" (single file), "medium" (few files), or "broad" (many files)
7. success_criteria: How would we know the task is complete?

Return ONLY valid JSON, no additional text.'''

            # Use claude CLI directly via bash
            import subprocess
            import json
            import tempfile
            
            # Write prompt to a temporary file to avoid shell escaping issues
            with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
                f.write(prompt)
                prompt_file = f.name
            
            # Call claude with -p flag for non-interactive mode
            cmd = f'claude -p < {prompt_file}'
            
            try:
                result = subprocess.run(
                    cmd,
                    shell=True,
                    capture_output=True,
                    text=True,
                    timeout=self.config.claude_timeout_seconds
                )
                
                if result.returncode != 0:
                    raise Exception(f"Claude CLI failed: {result.stderr}")
            finally:
                # Clean up temp file
                import os
                os.unlink(prompt_file)
            
            # Parse JSON response
            response_text = result.stdout.strip()
            
            # Try to extract JSON from the response
            # Claude might return markdown code blocks, so handle that
            json_match = re.search(r'```json\s*(.*?)\s*```', response_text, re.DOTALL)
            if json_match:
                json_str = json_match.group(1)
            else:
                # Try to find raw JSON
                json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
                if json_match:
                    json_str = json_match.group(0)
                else:
                    raise ValueError("No JSON found in Claude response")
            
            data = json.loads(json_str)
            
            # Create TaskAnalysis from Claude's response
            analysis = TaskAnalysis(
                keywords=data.get('keywords', [])[:10],
                actions=data.get('actions', []),
                concepts=data.get('concepts', []),
                file_patterns=data.get('file_patterns', []),
                estimated_scope=data.get('estimated_scope', 'medium')
            )
            
            # Cache the result
            if self.config.cache_claude_responses:
                self._claude_cache[cache_key] = {
                    'result': analysis,
                    'timestamp': datetime.now()
                }
            
            return analysis
            
        except Exception as e:
            # Log error but don't fail
            self.log_error(f"Claude task analysis failed: {str(e)}")
            return None
    
    def _analyze_task(self, task_description: str) -> TaskAnalysis:
        """Analyze a task description to extract key information."""
        # Convert to lowercase for analysis
        task_lower = task_description.lower()
        words = task_lower.split()
        
        # Extract keywords (non-stopwords > 3 chars)
        keywords = []
        for word in words:
            # Remove common punctuation
            clean_word = word.strip('.,!?;:"\'()')
            if len(clean_word) > 3 and clean_word not in self.STOPWORDS:
                keywords.append(clean_word)
        
        # Identify action verbs
        action_indicators = {
            'fix': ['fix', 'repair', 'resolve', 'debug', 'patch'],
            'implement': ['implement', 'add', 'create', 'build', 'develop'],
            'refactor': ['refactor', 'restructure', 'reorganize', 'optimize', 'clean'],
            'test': ['test', 'verify', 'check', 'validate', 'ensure'],
            'document': ['document', 'write', 'update', 'describe', 'explain']
        }
        
        actions = []
        for action_type, indicators in action_indicators.items():
            if any(indicator in task_lower for indicator in indicators):
                actions.append(action_type)
        
        # Map keywords to existing concepts if project is initialized
        concepts = []
        if self.project_index and self.project_index.concepts:
            for keyword in keywords:
                # Check if keyword matches any concept (case-insensitive)
                for concept in self.project_index.concepts:
                    if keyword in concept.lower() or concept.lower() in keyword:
                        concepts.append(concept)
                        break
        
        # Infer file patterns based on task
        file_patterns = self._infer_file_patterns(keywords, actions, concepts)
        
        # Estimate scope based on concept count and actions
        if len(concepts) == 0:
            estimated_scope = 'narrow'  # No concepts found, probably specific
        elif len(concepts) <= 2:
            estimated_scope = 'narrow'
        elif len(concepts) <= 5:
            estimated_scope = 'medium'
        else:
            estimated_scope = 'broad'
        
        # If multiple actions or refactoring, increase scope
        if len(actions) > 2 or 'refactor' in actions:
            if estimated_scope == 'narrow':
                estimated_scope = 'medium'
            elif estimated_scope == 'medium':
                estimated_scope = 'broad'
        
        return TaskAnalysis(
            keywords=keywords,
            actions=actions,
            concepts=concepts,
            file_patterns=file_patterns,
            estimated_scope=estimated_scope
        )
    
    def _infer_file_patterns(self, keywords: List[str], actions: List[str], concepts: List[str]) -> List[str]:
        """Infer likely file patterns based on task analysis."""
        patterns = []
        
        # Add patterns based on actions
        if 'test' in actions:
            patterns.extend(['*test*.py', '*_test.py', 'test_*.py', '*spec.js'])
        
        if 'document' in actions:
            patterns.extend(['*.md', 'README*', 'CHANGELOG*', 'docs/*'])
        
        # Add patterns based on keywords
        keyword_patterns = {
            'api': ['*api*.py', '*endpoint*.py', '*route*.py', '*controller*.js'],
            'ui': ['*.html', '*.css', '*.jsx', '*.tsx', '*component*.js'],
            'database': ['*model*.py', '*schema*.py', '*migration*.sql', '*.sql'],
            'config': ['*config*.py', '*.json', '*.yaml', '*.yml', '.env*'],
            'script': ['*.sh', '*.bash', '*script*.py'],
            'build': ['*build*.py', 'Makefile', '*.gradle', 'package.json'],
            'deploy': ['*deploy*.py', 'Dockerfile', '*.yaml', '*.yml', '.github/*']
        }
        
        for keyword in keywords:
            for pattern_key, pattern_list in keyword_patterns.items():
                if pattern_key in keyword:
                    patterns.extend(pattern_list)
        
        # Add patterns based on specific file mentions
        for keyword in keywords:
            # Check if keyword looks like a filename
            if '.' in keyword or keyword.endswith('.py') or keyword.endswith('.js'):
                patterns.append(f'*{keyword}*')
            elif keyword.endswith('er') or keyword.endswith('or'):  # likely a module name
                patterns.append(f'*{keyword}*.py')
                patterns.append(f'*{keyword}*.js')
        
        # Remove duplicates while preserving order
        seen = set()
        unique_patterns = []
        for pattern in patterns:
            if pattern not in seen:
                seen.add(pattern)
                unique_patterns.append(pattern)
        
        return unique_patterns
    
    def collect_context_for_task(self, task_description: str, agent_type: str = None, 
                                max_tokens: int = 50000, include_types: List[str] = None, 
                                exclude_patterns: List[str] = None, agent_template: Dict[str, Any] = None, 
                                explain_selection: bool = False, min_relevance: float = 0.3,
                                use_claude_analysis: Optional[bool] = None) -> ContextCollection:
        """
        Intelligent context collection based on task description.
        
        This method analyzes a task description and collects all relevant context 
        from the project, including documentation, code files, and previous contexts.
        It uses pattern matching and relevance scoring to prioritize the most useful
        information while staying within token limits.
        
        Args:
            task_description: Description of the task to collect context for
            agent_type: Type of agent requesting context (affects prioritization)
            max_tokens: Maximum tokens to include in context (default: 50000)
            include_types: List of context types to include (default: ['all'])
            exclude_patterns: List of file patterns to exclude (e.g., ['*.test.js'])
            agent_template: Custom template for context organization
            explain_selection: If True, include explanations for why items were selected
            min_relevance: Minimum relevance score to include an item (0-1, default: 0.3)
            use_claude_analysis: Override config to enable/disable Claude analysis (None = use config)
        
        Returns:
            ContextCollection: Complete context collection with items, analysis, and suggestions
        
        Raises:
            ValueError: If task_description is empty or project not initialized
            
        Example:
            >>> cm = ContextManager()
            >>> context = cm.collect_context_for_task(
            ...     "Fix the authentication bug in the login endpoint",
            ...     agent_type="code",
            ...     max_tokens=30000
            ... )
            >>> print(f"Collected {len(context.items)} items totaling {context.total_tokens} tokens")
        """
        # Record start time for performance tracking
        start_time = time.time()
        
        # Validate inputs
        if not task_description or not task_description.strip():
            raise ValueError("Task description cannot be empty")
        
        if self.project_index is None:
            raise ValueError("Project not initialized. Run 'cm init' first.")
        
        # Analyze the task - try Claude first, fallback to heuristic
        task_analysis = None
        
        # Determine whether to use Claude (parameter overrides config)
        should_use_claude = use_claude_analysis if use_claude_analysis is not None else self.config.use_claude_analysis
        
        # Try Claude analysis if enabled
        if should_use_claude:
            try:
                # Run async Claude analysis in sync context
                import asyncio
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                task_analysis = loop.run_until_complete(
                    self._analyze_task_with_claude(task_description)
                )
                loop.close()
                
                if task_analysis:
                    # Log that we used Claude
                    context = Context(
                        id=str(uuid.uuid4()),
                        type=ContextType.DEVELOPMENT,
                        source="claude_analysis",
                        timestamp=datetime.now(),
                        data={"task": task_description, "analysis": "claude"},
                        tags=["ai_enhanced"]
                    )
                    self.add_context(context)
            except Exception as e:
                # Log error but continue
                self.log_error(f"Claude analysis failed: {str(e)}")
        
        # Fallback to heuristic analysis if Claude failed or is disabled
        if task_analysis is None:
            task_analysis = self._analyze_task(task_description)
        
        # Set default include_types if not provided
        if include_types is None:
            include_types = ['all']
        
        # Collect relevant items based on task analysis
        raw_items = self._collect_relevant_items(
            task_analysis=task_analysis,
            include_types=include_types,
            exclude_patterns=exclude_patterns or [],
            min_relevance=min_relevance,
            explain_selection=explain_selection
        )
        
        # Convert raw items to ContextItem objects
        context_items = []
        for item, relevance_score in raw_items:
            context_item = self._convert_to_context_item(item, relevance_score)
            if context_item:
                context_items.append(context_item)
        
        # Optimize for token limit
        items, truncated = self._optimize_for_tokens(context_items, max_tokens)
        
        # Generate summary (simple version for now)
        summary = task_description[:200] + "..." if len(task_description) > 200 else task_description
        
        # Generate suggestions (empty for now, will be enhanced later)
        suggestions = []
        
        # Calculate total tokens
        total_tokens = sum(item.tokens for item in items)
        
        # Calculate collection time
        collection_time_ms = int((time.time() - start_time) * 1000)
        
        # Create and return the context collection
        return ContextCollection(
            task_description=task_description,
            task_analysis=task_analysis,
            items=items,
            total_tokens=total_tokens,
            summary=summary,
            suggestions=suggestions,
            truncated=truncated,
            collection_time_ms=collection_time_ms
        )
    
    def _collect_relevant_items(self, task_analysis: TaskAnalysis, include_types: List[str], 
                               exclude_patterns: List[str], min_relevance: float, 
                               explain_selection: bool) -> List[Tuple[Any, float]]:
        """
        Collect relevant context items based on task analysis.
        
        Returns:
            List of tuples (item, relevance_score) where item can be:
            - Context object
            - DocMetadata object
            - CodeMetadata object
            - Tuple of (folder_path, description) for folders
        """
        items = []
        
        # Handle 'all' type
        if 'all' in include_types:
            include_types = ['contexts', 'docs', 'code', 'folders']
        
        # Stage 1: Recent contexts (last 48 hours)
        if 'contexts' in include_types:
            cutoff_time = datetime.now() - timedelta(hours=48)
            for context_id, context in self.contexts.items():
                if context.timestamp >= cutoff_time:
                    if self._should_include_item(context, include_types, exclude_patterns):
                        relevance = self._calculate_context_relevance(context, task_analysis)
                        if relevance >= min_relevance:
                            items.append((context, relevance))
        
        # Check if project index exists
        if not self.project_index:
            return items
        
        # Prepare keyword sets for matching
        all_keywords = set(k.lower() for k in task_analysis.keywords)
        all_concepts = set(c.lower() for c in task_analysis.concepts)
        all_terms = all_keywords | all_concepts
        
        # Stage 2: Direct concept matches from project index
        if 'docs' in include_types or 'code' in include_types:
            for concept in task_analysis.concepts:
                concept_lower = concept.lower()
                if concept_lower in self.project_index.concepts:
                    file_paths = self.project_index.concepts[concept_lower]
                    for file_path in file_paths:
                        # Check if it's a doc or code file
                        if file_path in self.project_index.doc_files and 'docs' in include_types:
                            doc_meta = self.project_index.doc_files[file_path]
                            if self._should_include_item(doc_meta, include_types, exclude_patterns):
                                items.append((doc_meta, 0.9))  # High relevance for direct concept match
                        elif file_path in self.project_index.code_files and 'code' in include_types:
                            code_meta = self.project_index.code_files[file_path]
                            if self._should_include_item(code_meta, include_types, exclude_patterns):
                                items.append((code_meta, 0.9))  # High relevance for direct concept match
        
        # Stage 3: Function/class name matches based on keywords
        if 'code' in include_types:
            # Check function names
            for func_name, file_path in self.project_index.functions.items():
                if any(keyword.lower() in func_name.lower() for keyword in task_analysis.keywords):
                    if file_path in self.project_index.code_files:
                        code_meta = self.project_index.code_files[file_path]
                        if self._should_include_item(code_meta, include_types, exclude_patterns):
                            # Calculate relevance based on keyword match strength
                            relevance = self._calculate_name_match_relevance(func_name, task_analysis.keywords)
                            if relevance >= min_relevance:
                                items.append((code_meta, relevance))
            
            # Check class names
            for class_name, file_path in self.project_index.classes.items():
                if any(keyword.lower() in class_name.lower() for keyword in task_analysis.keywords):
                    if file_path in self.project_index.code_files:
                        code_meta = self.project_index.code_files[file_path]
                        if self._should_include_item(code_meta, include_types, exclude_patterns):
                            relevance = self._calculate_name_match_relevance(class_name, task_analysis.keywords)
                            if relevance >= min_relevance:
                                items.append((code_meta, relevance))
        
        # Stage 4: Description-based matches
        if 'docs' in include_types:
            for file_path, doc_meta in self.project_index.doc_files.items():
                if doc_meta.description and self._should_include_item(doc_meta, include_types, exclude_patterns):
                    desc_lower = doc_meta.description.lower()
                    matching_terms = sum(1 for term in all_terms if term in desc_lower)
                    if matching_terms > 0:
                        relevance = min(0.7, matching_terms * 0.2)  # Cap at 0.7 for description matches
                        if relevance >= min_relevance:
                            items.append((doc_meta, relevance))
        
        if 'code' in include_types:
            for file_path, code_meta in self.project_index.code_files.items():
                if code_meta.description and self._should_include_item(code_meta, include_types, exclude_patterns):
                    desc_lower = code_meta.description.lower()
                    matching_terms = sum(1 for term in all_terms if term in desc_lower)
                    if matching_terms > 0:
                        relevance = min(0.7, matching_terms * 0.2)
                        if relevance >= min_relevance:
                            items.append((code_meta, relevance))
        
        # Stage 5: Include relevant folder descriptions
        if 'folders' in include_types:
            for folder_path, description in self.project_index.folder_descriptions.items():
                if description:
                    desc_lower = description.lower()
                    matching_terms = sum(1 for term in all_terms if term in desc_lower)
                    if matching_terms > 0:
                        folder_item = (folder_path, description)
                        if self._should_include_item(folder_item, include_types, exclude_patterns):
                            relevance = min(0.5, matching_terms * 0.15)  # Lower relevance for folders
                            if relevance >= min_relevance:
                                items.append((folder_item, relevance))
        
        # Remove duplicates based on path (for files) or id (for contexts)
        seen_paths = set()
        unique_items = []
        for item, score in items:
            if isinstance(item, Context):
                if item.id not in seen_paths:
                    seen_paths.add(item.id)
                    unique_items.append((item, score))
            elif isinstance(item, (DocMetadata, CodeMetadata)):
                if item.path not in seen_paths:
                    seen_paths.add(item.path)
                    unique_items.append((item, score))
            elif isinstance(item, tuple):  # Folder items
                if item[0] not in seen_paths:
                    seen_paths.add(item[0])
                    unique_items.append((item, score))
        
        # Sort by relevance score (highest first)
        unique_items.sort(key=lambda x: x[1], reverse=True)
        
        return unique_items
    
    def _calculate_context_relevance(self, context: Context, task_analysis: TaskAnalysis) -> float:
        """Calculate relevance score for a context based on task analysis."""
        relevance = 0.0
        
        # Check context data for keyword matches
        context_str = json.dumps(context.data).lower()
        
        # Keyword matches (0.3 weight)
        keyword_matches = sum(1 for keyword in task_analysis.keywords 
                            if keyword.lower() in context_str)
        if task_analysis.keywords:
            relevance += 0.3 * (keyword_matches / len(task_analysis.keywords))
        
        # Concept matches (0.4 weight)
        concept_matches = sum(1 for concept in task_analysis.concepts 
                            if concept.lower() in context_str)
        if task_analysis.concepts:
            relevance += 0.4 * (concept_matches / len(task_analysis.concepts))
        
        # Action matches (0.2 weight)
        action_matches = sum(1 for action in task_analysis.actions 
                           if action.lower() in context_str)
        if task_analysis.actions:
            relevance += 0.2 * (action_matches / len(task_analysis.actions))
        
        # Tag matches (0.1 weight)
        tag_matches = sum(1 for tag in context.tags 
                        if any(keyword.lower() in tag.lower() 
                              for keyword in task_analysis.keywords))
        if context.tags and task_analysis.keywords:
            relevance += 0.1 * (tag_matches / len(context.tags))
        
        # Boost for specific context types
        if context.type == ContextType.DECISION and 'decision' in task_analysis.actions:
            relevance += 0.1
        elif context.type == ContextType.ERROR and 'debug' in task_analysis.actions:
            relevance += 0.1
        
        return min(1.0, relevance)
    
    def _calculate_name_match_relevance(self, name: str, keywords: List[str]) -> float:
        """Calculate relevance score for function/class name matches."""
        name_lower = name.lower()
        relevance = 0.0
        
        # Exact match gets highest score
        for keyword in keywords:
            keyword_lower = keyword.lower()
            if keyword_lower == name_lower:
                return 0.85
            elif keyword_lower in name_lower:
                # Partial match - score based on match quality
                match_ratio = len(keyword_lower) / len(name_lower)
                relevance = max(relevance, 0.5 + (match_ratio * 0.3))
        
        return relevance
    
    def _should_include_item(self, item: Any, include_types: List[str], 
                           exclude_patterns: List[str]) -> bool:
        """Check if an item should be included based on filters."""
        # If no exclude patterns, include everything
        if not exclude_patterns:
            return True
        
        # Get the path or identifier to check
        path = None
        if isinstance(item, (DocMetadata, CodeMetadata)):
            path = item.path
        elif isinstance(item, Context):
            # Check context source and tags
            for pattern in exclude_patterns:
                if pattern in item.source or any(pattern in tag for tag in item.tags):
                    return False
            return True
        elif isinstance(item, tuple):  # Folder item
            path = item[0]
        
        # Check path against exclude patterns
        if path:
            for pattern in exclude_patterns:
                if pattern in path:
                    return False
        
        return True
    
    def _convert_to_context_item(self, item: Any, relevance_score: float) -> Optional[ContextItem]:
        """Convert various item types to ContextItem format."""
        try:
            if isinstance(item, Context):
                # Convert Context to ContextItem
                content = json.dumps(item.data, indent=2)
                return ContextItem(
                    type='context',
                    path=f"context/{item.id}",
                    content=content,
                    relevance_score=relevance_score,
                    tokens=len(content.split()),  # Simple token estimate
                    metadata={
                        'context_type': item.type.value,
                        'source': item.source,
                        'timestamp': item.timestamp.isoformat(),
                        'tags': item.tags
                    }
                )
            
            elif isinstance(item, DocMetadata):
                # Read doc file content
                try:
                    content = Path(item.path).read_text()
                    # Truncate if too long
                    if len(content) > 10000:
                        content = content[:10000] + "\n... [truncated]"
                    
                    return ContextItem(
                        type='doc_section',
                        path=item.path,
                        content=content,
                        relevance_score=relevance_score,
                        tokens=len(content.split()),
                        metadata={
                            'doc_type': item.doc_type,
                            'description': item.description,
                            'needs_update': item.needs_update()
                        }
                    )
                except Exception as e:
                    print(f"Error reading doc file {item.path}: {e}")
                    return None
            
            elif isinstance(item, CodeMetadata):
                # Read code file content
                try:
                    content = Path(item.path).read_text()
                    # Truncate if too long
                    if len(content) > 10000:
                        content = content[:10000] + "\n... [truncated]"
                    
                    return ContextItem(
                        type='file',
                        path=item.path,
                        content=content,
                        relevance_score=relevance_score,
                        tokens=len(content.split()),
                        metadata={
                            'language': item.language,
                            'description': item.description,
                            'functions': item.functions[:10],  # Limit functions listed
                            'classes': item.classes[:10]       # Limit classes listed
                        }
                    )
                except Exception as e:
                    print(f"Error reading code file {item.path}: {e}")
                    return None
            
            elif isinstance(item, tuple) and len(item) == 2:
                # Folder description tuple
                folder_path, description = item
                return ContextItem(
                    type='folder_desc',
                    path=folder_path,
                    content=f"Folder: {folder_path}\nDescription: {description}",
                    relevance_score=relevance_score,
                    tokens=len(description.split()) + 10,  # Add some for formatting
                    metadata={'folder_path': folder_path}
                )
            
            else:
                print(f"Unknown item type: {type(item)}")
                return None
                
        except Exception as e:
            print(f"Error converting item to ContextItem: {e}")
            return None
    
    def _optimize_for_tokens(self, items: List[ContextItem], max_tokens: int) -> Tuple[List[ContextItem], bool]:
        """
        Sophisticated token optimization with balanced representation across types.
        
        Groups items by type and allocates proportional token budgets:
        - 30% for contexts (recent decisions, errors, patterns)
        - 40% for code (implementation details)
        - 20% for docs (specifications, guides)
        - 10% for folders (structural overview)
        
        Supports smart truncation for large high-relevance items and redistribution
        of unused budget between categories.
        
        Args:
            items: List of context items sorted by relevance
            max_tokens: Maximum allowed tokens
            
        Returns:
            Tuple of (optimized items, whether truncation occurred)
        """
        # Edge case: very small token limit
        if max_tokens < 100:
            # Just include the most relevant item if possible
            if items and items[0].tokens <= max_tokens:
                return [items[0]], True
            return [], True
        
        # Group items by type
        contexts = []
        code_files = []
        doc_files = []
        folder_descs = []
        
        for item in items:
            if item.type == 'context':
                contexts.append(item)
            elif item.type == 'file':
                code_files.append(item)
            elif item.type == 'doc_section':
                doc_files.append(item)
            elif item.type == 'folder_desc':
                folder_descs.append(item)
        
        # Calculate initial budgets (with some buffer for overhead)
        overhead = min(500, int(max_tokens * 0.02))  # 2% overhead, max 500 tokens
        available_tokens = max_tokens - overhead
        
        budget_contexts = int(available_tokens * 0.30)
        budget_code = int(available_tokens * 0.40)
        budget_docs = int(available_tokens * 0.20)
        budget_folders = int(available_tokens * 0.10)
        
        # Process each category
        selected_contexts, used_contexts, trunc_contexts = self._add_items_within_budget(
            contexts, budget_contexts, "contexts"
        )
        selected_code, used_code, trunc_code = self._add_items_within_budget(
            code_files, budget_code, "code"
        )
        selected_docs, used_docs, trunc_docs = self._add_items_within_budget(
            doc_files, budget_docs, "docs"
        )
        selected_folders, used_folders, trunc_folders = self._add_items_within_budget(
            folder_descs, budget_folders, "folders"
        )
        
        # Calculate unused tokens
        unused_contexts = budget_contexts - used_contexts
        unused_code = budget_code - used_code
        unused_docs = budget_docs - used_docs
        unused_folders = budget_folders - used_folders
        total_unused = unused_contexts + unused_code + unused_docs + unused_folders
        
        # Redistribute unused budget proportionally to categories that need more
        redistribution_items = []
        
        # Check which categories have items left
        remaining_contexts = contexts[len(selected_contexts):]
        remaining_code = code_files[len(selected_code):]
        remaining_docs = doc_files[len(selected_docs):]
        remaining_folders = folder_descs[len(selected_folders):]
        
        # Prioritize redistribution to code and docs
        if total_unused > 100:  # Only redistribute if significant unused budget
            # Try to add more code files first (highest priority)
            if remaining_code and unused_contexts + unused_docs + unused_folders > 0:
                extra_budget = int(total_unused * 0.5)  # Use 50% of unused for code
                extra_code, extra_used, _ = self._add_items_within_budget(
                    remaining_code, extra_budget, "code"
                )
                redistribution_items.extend(extra_code)
                total_unused -= extra_used
            
            # Then try docs
            if remaining_docs and total_unused > 100:
                extra_budget = int(total_unused * 0.6)  # Use 60% of remaining for docs
                extra_docs, extra_used, _ = self._add_items_within_budget(
                    remaining_docs, extra_budget, "docs"
                )
                redistribution_items.extend(extra_docs)
                total_unused -= extra_used
            
            # Then contexts
            if remaining_contexts and total_unused > 100:
                extra_budget = int(total_unused * 0.8)  # Use 80% of remaining for contexts
                extra_contexts, extra_used, _ = self._add_items_within_budget(
                    remaining_contexts, extra_budget, "contexts"
                )
                redistribution_items.extend(extra_contexts)
        
        # Combine all selected items
        all_selected = (
            selected_contexts + selected_code + selected_docs + 
            selected_folders + redistribution_items
        )
        
        # Sort by relevance to maintain quality
        all_selected.sort(key=lambda x: x.relevance_score, reverse=True)
        
        # Determine if truncation occurred
        truncated = (
            trunc_contexts or trunc_code or trunc_docs or trunc_folders or
            len(contexts) > len(selected_contexts) or
            len(code_files) > len(selected_code) or
            len(doc_files) > len(selected_docs) or
            len(folder_descs) > len(selected_folders)
        )
        
        # Ensure at least one item is included if possible
        if not all_selected and items:
            # Try to include at least the most relevant item
            most_relevant = max(items, key=lambda x: x.relevance_score)
            if most_relevant.tokens <= max_tokens:
                return [most_relevant], True
            else:
                # Try to truncate it
                truncated_item = self._truncate_item(most_relevant, max_tokens)
                if truncated_item:
                    return [truncated_item], True
        
        return all_selected, truncated
    
    def _add_items_within_budget(self, items: List[ContextItem], budget: int, 
                                 category: str) -> Tuple[List[ContextItem], int, bool]:
        """
        Add items from a category while staying within budget.
        
        Supports smart truncation for large items with high relevance.
        
        Args:
            items: List of items in this category (already sorted by relevance)
            budget: Token budget for this category
            category: Category name for logging
            
        Returns:
            Tuple of (selected items, tokens used, whether any items were truncated)
        """
        selected = []
        used_tokens = 0
        any_truncated = False
        
        for item in items:
            if used_tokens >= budget:
                break
            
            # Check if item fits
            if used_tokens + item.tokens <= budget:
                selected.append(item)
                used_tokens += item.tokens
            else:
                # Item doesn't fit - check if it's worth truncating
                remaining_budget = budget - used_tokens
                
                # Only truncate if:
                # 1. Item has high relevance (>0.6)
                # 2. We can include at least 20% of the item
                # 3. Remaining budget is substantial (>500 tokens)
                if (item.relevance_score > 0.6 and 
                    remaining_budget > 500 and 
                    remaining_budget >= item.tokens * 0.2):
                    
                    # Try to truncate the item
                    truncated_item = self._truncate_item(item, remaining_budget)
                    if truncated_item:
                        selected.append(truncated_item)
                        used_tokens += truncated_item.tokens
                        any_truncated = True
        
        return selected, used_tokens, any_truncated
    
    def _truncate_item(self, item: ContextItem, max_tokens: int) -> Optional[ContextItem]:
        """
        Intelligently truncate a context item to fit within token limit.
        
        Args:
            item: The item to truncate
            max_tokens: Maximum tokens allowed
            
        Returns:
            Truncated ContextItem or None if truncation not possible
        """
        if max_tokens < 100:  # Too small to truncate meaningfully
            return None
        
        # Estimate how much content we can keep
        original_tokens = self._estimate_tokens(item.content)
        if original_tokens <= max_tokens:
            return item  # No truncation needed
        
        # Calculate truncation ratio
        keep_ratio = max_tokens / original_tokens
        
        # Different truncation strategies based on item type
        if item.type == 'file' or item.type == 'doc_section':
            # For files, try to keep the beginning (imports, class definitions)
            # and some from the middle
            lines = item.content.split('\n')
            total_lines = len(lines)
            
            if total_lines < 10:
                # Very short file, just truncate by character count
                char_limit = int(len(item.content) * keep_ratio * 0.9)  # 90% to be safe
                truncated_content = item.content[:char_limit] + "\n\n... [truncated]"
            else:
                # Keep first 30% and last 10% of lines
                keep_start = int(total_lines * keep_ratio * 0.7)
                keep_end = int(total_lines * keep_ratio * 0.1)
                
                truncated_lines = (
                    lines[:keep_start] + 
                    ["\n... [truncated middle section] ...\n"] + 
                    lines[-keep_end:] if keep_end > 0 else []
                )
                truncated_content = '\n'.join(truncated_lines)
        
        elif item.type == 'context':
            # For contexts, truncate the data portion
            try:
                # Parse the JSON content
                context_data = json.loads(item.content)
                
                # Truncate string values in the data
                for key, value in context_data.items():
                    if isinstance(value, str) and len(value) > 200:
                        max_len = int(200 * keep_ratio)
                        context_data[key] = value[:max_len] + "... [truncated]"
                
                truncated_content = json.dumps(context_data, indent=2)
            except:
                # Fallback to simple truncation
                char_limit = int(len(item.content) * keep_ratio * 0.9)
                truncated_content = item.content[:char_limit] + "\n... [truncated]"
        
        else:
            # Default truncation for other types
            char_limit = int(len(item.content) * keep_ratio * 0.9)
            truncated_content = item.content[:char_limit] + "\n... [truncated]"
        
        # Create new truncated item
        truncated_item = ContextItem(
            type=item.type,
            path=item.path,
            content=truncated_content,
            relevance_score=item.relevance_score,
            tokens=self._estimate_tokens(truncated_content),
            metadata={**item.metadata, 'truncated': True, 'original_tokens': item.tokens}
        )
        
        # Verify it actually fits
        if truncated_item.tokens <= max_tokens:
            return truncated_item
        
        # If still too big, do a more aggressive truncation
        final_char_limit = int(max_tokens * 3.5)  # Rough estimate: 3.5 chars per token
        final_content = item.content[:final_char_limit] + "\n... [heavily truncated]"
        
        return ContextItem(
            type=item.type,
            path=item.path,
            content=final_content,
            relevance_score=item.relevance_score,
            tokens=self._estimate_tokens(final_content),
            metadata={**item.metadata, 'truncated': True, 'heavily_truncated': True, 
                     'original_tokens': item.tokens}
        )
    
    def _estimate_tokens(self, content: str) -> int:
        """
        Estimate token count for a piece of content.
        
        Uses a simple heuristic of ~4 characters per token, which is
        reasonable for English text and code.
        
        Args:
            content: The content to estimate tokens for
            
        Returns:
            Estimated token count
        """
        if not content:
            return 0
        
        # Simple estimation: ~4 characters per token
        # This is a reasonable approximation for English text and code
        char_count = len(content)
        
        # Adjust based on content type heuristics
        # Code tends to have more tokens due to symbols
        if '{' in content or ';' in content or 'def ' in content or 'function ' in content:
            # Likely code - slightly more tokens per character
            return int(char_count / 3.5)
        else:
            # Likely text - standard ratio
            return int(char_count / 4)
    
    def _get_item_content(self, item: Any, item_type: str) -> str:
        """
        Extract content from different item types.
        
        Args:
            item: The item to extract content from
            item_type: Type hint for the item
            
        Returns:
            String content or empty string if extraction fails
        """
        try:
            if isinstance(item, ContextItem):
                return item.content
            elif isinstance(item, Context):
                return json.dumps(item.data, indent=2)
            elif isinstance(item, (DocMetadata, CodeMetadata)):
                # Try to read file content
                try:
                    return Path(item.path).read_text()
                except:
                    return f"[Unable to read {item.path}]"
            elif isinstance(item, tuple) and len(item) == 2:
                # Folder description
                return f"Folder: {item[0]}\nDescription: {item[1]}"
            elif isinstance(item, dict):
                return json.dumps(item, indent=2)
            elif isinstance(item, str):
                return item
            else:
                return str(item)
        except Exception as e:
            return f"[Error extracting content: {e}]"
    
    def _get_item_path(self, item: Any, item_type: str) -> str:
        """
        Extract path or identifier from different item types.
        
        Args:
            item: The item to extract path from
            item_type: Type hint for the item
            
        Returns:
            Path string or identifier
        """
        try:
            if isinstance(item, ContextItem):
                return item.path
            elif isinstance(item, Context):
                return f"context/{item.id}"
            elif isinstance(item, (DocMetadata, CodeMetadata)):
                return item.path
            elif isinstance(item, tuple) and len(item) == 2:
                # Folder description
                return item[0]
            elif isinstance(item, dict) and 'path' in item:
                return item['path']
            elif isinstance(item, dict) and 'id' in item:
                return f"item/{item['id']}"
            else:
                return f"unknown/{hash(str(item))}"
        except Exception:
            return "unknown/error"
    
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