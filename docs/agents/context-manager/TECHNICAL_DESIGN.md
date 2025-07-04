# Context Manager Technical Design

> **Note**: This document consolidates the technical design details from the project evolution phase. For the journey and decisions that led here, see the [project evolution guide](../../project-evolution-guide/).

## Overview

This document contains the complete technical design for Context Manager v1, including schema, storage, API, and implementation details.

## Quick Links

- **Week 1 Implementation Plan**: See [IMPLEMENTATION_PLAN.md](IMPLEMENTATION_PLAN.md)
- **API Reference**: See [AGENT_SPECIFICATION.md](AGENT_SPECIFICATION.md)
- **Bootstrap Approach**: See [BOOTSTRAP_GUIDE.md](BOOTSTRAP_GUIDE.md)

## Context Schema Design

### Core Data Structure

```python
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from datetime import datetime
from enum import Enum

class ContextType(Enum):
    """Types of context entries"""
    DEVELOPMENT = "development"
    PLANNING = "planning"
    EXECUTION = "execution"
    DOCUMENTATION = "documentation"

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
    metadata: Dict[str, Any] = field(default_factory=dict)
    relationships: List[str] = field(default_factory=list)  # Related context IDs
    tags: List[str] = field(default_factory=list)          # Searchable tags
    ttl: Optional[int] = None                               # Time-to-live in seconds
    
    # Compliance fields
    requires_audit: bool = True
    sensitivity_level: str = "internal"  # internal|confidential|public
    
    def validate(self) -> bool:
        """Validate context against schema rules."""
        # Implementation in schema.py
```

### Documentation Intelligence System

```python
@dataclass
class DocMetadata:
    """Lightweight metadata for existing documentation files."""
    
    # File reference
    path: str                       # Path to actual .md file
    doc_type: str                   # Inferred type (readme, api_spec, etc.)
    last_analyzed: datetime         # When we last analyzed this doc
    
    # Intelligence data
    patterns_detected: 'DocPattern' # Learned patterns from this doc
    quality_scores: Dict[str, float] = field(default_factory=dict)
    staleness_indicators: List[str] = field(default_factory=list)
    
    # Relationships
    linked_contexts: List[str] = field(default_factory=list)    # Related events
    linked_docs: List[str] = field(default_factory=list)        # Related docs
    dependencies: Dict[str, List[str]] = field(default_factory=dict)  # Code dependencies
    
    # Update tracking
    update_history: List['DocUpdate'] = field(default_factory=list)
    pending_updates: List['SuggestedUpdate'] = field(default_factory=list)
    
    def needs_update(self) -> bool:
        """Check if document likely needs updating."""
        return len(self.staleness_indicators) > 0 or len(self.pending_updates) > 0

@dataclass
class DocPattern:
    """Learned patterns from existing documentation."""
    
    # Structure patterns
    file_naming: Dict[str, str]         # Pattern mappings
    section_headers: List[str]          # Common sections in order
    section_patterns: Dict[str, str]    # Section name -> content pattern
    
    # Style patterns
    markdown_style: Dict[str, str]      # Style preferences
    code_block_style: str               # Language tags used
    list_style: str                     # Bullet point style
    
    # Content patterns
    common_phrases: Dict[str, int]      # Phrase -> frequency
    terminology: Dict[str, str]         # Project-specific terms
    update_triggers: Dict[str, List[str]]  # Code pattern -> doc sections
    
    # Quality patterns
    avg_section_length: Dict[str, int]  # Expected section sizes
    required_sections: List[str]        # Sections that should exist
    optional_sections: List[str]        # Sections that might exist

@dataclass
class DocUpdate:
    """Record of a documentation update."""
    timestamp: datetime
    trigger_context: str                # Context ID that triggered update
    update_type: str                    # 'manual', 'automated', 'suggested'
    sections_affected: List[str]
    change_summary: str
    performed_by: str                   # Agent or human ID

@dataclass 
class SuggestedUpdate:
    """Pending documentation update suggestion."""
    suggested_at: datetime
    trigger_contexts: List[str]         # Contexts suggesting this update
    section: str                        # Section to update
    update_type: str                    # 'addition', 'modification', 'deletion'
    confidence: float                   # 0.0-1.0
    suggested_content: Optional[str]    # For simple updates
    complexity: str                     # 'simple', 'medium', 'complex'
    suggested_handler: str              # 'context_manager', 'swiss_army', 'human'
```

### Documentation Intelligence Design Rationale

- **Metadata Only**: No content duplication - work with existing .md files directly
- **Pattern Learning**: Extract and adapt to project's documentation style
- **Intelligence Layer**: Context Manager coordinates but doesn't own all writing
- **Progressive Enhancement**: Start with metadata, add intelligence over time
- **Flexible Routing**: Simple updates handled directly, complex ones routed to appropriate agents/humans

### Context vs Documentation Relationship

- **Context = Immutable Events**: Track all changes and decisions
- **DocMetadata = Learned Intelligence**: Understanding of documentation structure and needs
- **Bidirectional Linking**: Contexts trigger doc updates, docs reference relevant contexts
- **No Lock-in**: Documentation remains in standard markdown, CM adds intelligence layer

## Storage Strategy

### JSON Storage (v1)

```python
# Directory structure
contexts/                   # Immutable event records
├── active/                 # Hot contexts
│   └── {date}/
│       └── {context_id}.json
├── archive/                # Cold storage
│   └── {year-month}/
└── indices/                # Search indices
    ├── by_type.json
    ├── by_source.json
    └── patterns.json

doc_metadata/               # Documentation intelligence
├── metadata/               # Metadata for each doc
│   └── {path_hash}.json   # Hash of file path -> metadata
├── patterns/               # Learned patterns
│   ├── global_patterns.json    # Project-wide patterns
│   └── by_type/               # Type-specific patterns
│       ├── readme_patterns.json
│       └── api_patterns.json
├── indices/                # Search and relationships
│   ├── doc_index.json     # Path -> metadata mapping
│   ├── dependency_graph.json  # Code -> doc dependencies
│   └── update_queue.json  # Pending updates
└── learning/              # Pattern learning data
    ├── style_samples.json
    └── update_history.json
```

### Storage Interface (Future-proof)

```python
from abc import ABC, abstractmethod

class StorageBackend(ABC):
    """Abstract storage interface for easy migration"""
    
    @abstractmethod
    def save_context(self, context: Context) -> bool:
        pass
    
    @abstractmethod
    def get_context(self, context_id: str) -> Optional[Context]:
        pass
    
    @abstractmethod
    def search_contexts(self, query: Dict[str, Any]) -> List[Context]:
        pass

class DocMetadataBackend(ABC):
    """Abstract documentation metadata interface"""
    
    @abstractmethod
    def save_metadata(self, metadata: DocMetadata) -> bool:
        pass
    
    @abstractmethod
    def get_metadata(self, path: str) -> Optional[DocMetadata]:
        pass
    
    @abstractmethod
    def search_metadata(self, query: Dict[str, Any]) -> List[DocMetadata]:
        pass
    
    @abstractmethod
    def save_patterns(self, patterns: DocPattern, scope: str = 'global') -> bool:
        pass
    
    @abstractmethod
    def get_patterns(self, scope: str = 'global') -> Optional[DocPattern]:
        pass

class JSONFileBackend(StorageBackend):
    """v1 implementation using JSON files"""
    pass

class JSONMetadataBackend(DocMetadataBackend):
    """v1 metadata storage using JSON"""
    pass

class RedisBackend(StorageBackend):
    """Future Redis implementation"""
    pass
```

## Pattern Detection

### Simple v1 Algorithm

```python
def detect_patterns(self, time_window: timedelta = timedelta(hours=24)):
    """Simple pattern detection for v1."""
    recent_contexts = self.get_contexts_since(datetime.now() - time_window)
    
    # Extract features
    features = self.extract_features(recent_contexts)
    
    # Count frequencies
    pattern_counts = Counter(features)
    
    # Identify significant patterns (>3 occurrences)
    significant_patterns = {
        pattern: count 
        for pattern, count in pattern_counts.items() 
        if count >= 3
    }
    
    # Generate suggestions
    return self.patterns_to_suggestions(significant_patterns)
```

### Patterns Tracked

1. **Decision Patterns**: Recurring decisions and their outcomes
2. **Error Patterns**: Common errors and resolutions
3. **Workflow Patterns**: State transition sequences
4. **Development Patterns**: Feature implementation success/failure
5. **Documentation Patterns**: Update triggers and style consistency

## Documentation Intelligence

### Pattern Learning System

```python
def learn_doc_patterns(self, doc_path: str) -> DocPattern:
    """Extract patterns from existing documentation."""
    content = self.read_file(doc_path)
    
    # Structure analysis
    patterns = DocPattern()
    patterns.section_headers = self.extract_headers(content)
    patterns.markdown_style = self.analyze_markdown_style(content)
    
    # Content analysis
    patterns.common_phrases = self.extract_common_phrases(content)
    patterns.terminology = self.extract_project_terms(content)
    
    # Learn from multiple docs of same type
    if doc_type := self.infer_doc_type(doc_path):
        similar_docs = self.find_similar_docs(doc_type)
        patterns = self.merge_patterns(patterns, similar_docs)
    
    return patterns
```

### Update Detection and Routing

```python
def analyze_update_impact(self, context: Context) -> List[SuggestedUpdate]:
    """Determine which docs need updating based on context."""
    suggestions = []
    
    # Check if context represents code change
    if context.type == ContextType.CODE_CHANGE:
        affected_files = context.data.get('files', [])
        
        # Find documentation dependencies
        for file in affected_files:
            dependent_docs = self.find_dependent_docs(file)
            
            for doc_path in dependent_docs:
                metadata = self.get_metadata(doc_path)
                update_type = self.classify_update_need(context, metadata)
                
                suggestion = SuggestedUpdate(
                    suggested_at=datetime.now(),
                    trigger_contexts=[context.id],
                    section=self.identify_section(doc_path, context),
                    update_type=update_type,
                    complexity=self.assess_complexity(update_type),
                    confidence=self.calculate_confidence(context, metadata),
                    suggested_handler=self.route_to_handler(update_type)
                )
                suggestions.append(suggestion)
    
    return suggestions

def route_to_handler(self, update_type: str) -> str:
    """Determine who should handle the documentation update."""
    routing_rules = {
        # Simple updates - Context Manager handles directly
        'version_bump': 'context_manager',
        'timestamp_update': 'context_manager',
        'list_addition': 'context_manager',
        
        # Medium complexity - Swiss Army Knife agent
        'new_section': 'swiss_army_agent',
        'example_update': 'swiss_army_agent',
        'api_addition': 'swiss_army_agent',
        
        # Complex updates - Future Documentation Agent or Human
        'major_refactor': 'documentation_agent',
        'architecture_change': 'human',
        'breaking_change': 'human'
    }
    return routing_rules.get(update_type, 'human')
```

### Documentation Quality Metrics

```python
def calculate_doc_quality(self, doc_path: str) -> Dict[str, float]:
    """Assess documentation quality across multiple dimensions."""
    metadata = self.get_metadata(doc_path)
    content = self.read_file(doc_path)
    patterns = metadata.patterns_detected
    
    scores = {
        'completeness': self.check_required_sections(content, patterns),
        'consistency': self.check_style_consistency(content, patterns),
        'staleness': self.calculate_staleness(metadata),
        'clarity': self.assess_readability(content),
        'accuracy': self.check_code_doc_sync(doc_path, metadata)
    }
    
    return scores
```

### Learning from Updates

```python
def record_update_outcome(self, update: DocUpdate, success: bool, feedback: str = None):
    """Learn from documentation update outcomes."""
    # Record what worked or didn't
    self.update_history.append({
        'update': update,
        'success': success,
        'feedback': feedback,
        'patterns_used': update.patterns_applied
    })
    
    # Adjust confidence for similar future updates
    if not success:
        self.adjust_pattern_confidence(update.update_type, -0.1)
    else:
        self.adjust_pattern_confidence(update.update_type, 0.05)
    
    # Learn new patterns from successful manual updates
    if update.update_type == 'manual' and success:
        new_patterns = self.extract_patterns_from_diff(update)
        self.merge_learned_patterns(new_patterns)
```

## API Design

### RESTful Endpoints

```python
# Flask Blueprint integration
from flask import Blueprint

context_bp = Blueprint('context', __name__, url_prefix='/api/context')

# Core CRUD
POST   /api/context/                    # Create context
GET    /api/context/{id}                # Get context
PUT    /api/context/{id}                # Update context
DELETE /api/context/{id}                # Delete context

# Patterns & Suggestions  
GET    /api/context/patterns            # Get detected patterns
GET    /api/context/suggestions         # Get current suggestions
POST   /api/context/feedback            # Feedback on suggestions

# Bootstrap Features
POST   /api/context/decision            # Log decision
POST   /api/context/problem             # Log problem
GET    /api/context/next                # Get next task suggestions

# Documentation Intelligence
POST   /api/docs/analyze                # Analyze doc and extract patterns
GET    /api/docs/{path}/metadata        # Get doc metadata and quality scores
GET    /api/docs/{path}/suggestions     # Get update suggestions
POST   /api/docs/{path}/update          # Apply simple update (CM handles)
GET    /api/docs/patterns               # Get learned documentation patterns
POST   /api/docs/learn                  # Force pattern learning from docs
GET    /api/docs/quality                # Get quality metrics for all docs
POST   /api/docs/link                   # Link documents and contexts
GET    /api/docs/stale                  # List potentially stale documentation
```

### WebSocket Events

```javascript
// Real-time updates
socket.on('context_added', (data) => {
    updateContextPanel(data.context);
});

socket.on('pattern_detected', (data) => {
    showNotification(`Pattern: ${data.pattern.name}`);
});

socket.on('suggestion_available', (data) => {
    displaySuggestion(data.suggestion);
});

// Documentation intelligence events
socket.on('doc_stale', (data) => {
    notifyStaleDoc(data.path, data.reasons);
});

socket.on('doc_update_suggested', (data) => {
    showUpdateSuggestion(data.path, data.suggestion);
});

socket.on('pattern_learned', (data) => {
    console.log(`Learned new pattern: ${data.pattern_type}`);
});
```

## Testing Strategy

### TDD Test Structure

```
tests/
├── unit/
│   ├── test_context_schema.py      # Schema validation
│   ├── test_storage.py             # Storage operations
│   ├── test_patterns.py            # Pattern detection
│   └── test_api.py                 # API endpoints
├── integration/
│   ├── test_flask_integration.py   # Flask app integration
│   ├── test_websocket.py           # Real-time events
│   └── test_bootstrap.py           # Self-documentation
└── performance/
    ├── test_throughput.py          # 1000 contexts/sec
    └── test_search.py              # <200ms searches
```

### Key Test Cases

```python
class TestContextManager:
    def test_bootstrap_decision_logging(self):
        """Context Manager can log its own decisions"""
        cm = ContextManager()
        context_id = cm.log_decision(
            "Use JSON storage",
            "Simple and debuggable"
        )
        assert context_id is not None
        
    def test_pattern_detection_threshold(self):
        """Patterns require minimum occurrences"""
        # Add 2 similar contexts - no pattern
        # Add 3rd similar context - pattern detected
        
    def test_suggestion_generation(self):
        """Relevant suggestions from patterns"""
        # Create pattern
        # Verify suggestions match pattern

class TestDocumentIntelligence:
    def test_pattern_extraction(self):
        """Extract patterns from existing documentation"""
        cm = ContextManager()
        patterns = cm.learn_doc_patterns("docs/README.md")
        assert patterns.section_headers is not None
        assert patterns.markdown_style is not None
        
    def test_update_detection(self):
        """Detect when docs need updating"""
        cm = ContextManager()
        # Add code change context
        context = Context(
            type=ContextType.CODE_CHANGE,
            data={"files": ["api/endpoints.py"], "changes": "new endpoint"}
        )
        suggestions = cm.analyze_update_impact(context)
        assert any(s.path == "docs/API.md" for s in suggestions)
        
    def test_update_routing(self):
        """Route updates to appropriate handlers"""
        cm = ContextManager()
        assert cm.route_to_handler('version_bump') == 'context_manager'
        assert cm.route_to_handler('new_section') == 'swiss_army_agent'
        assert cm.route_to_handler('breaking_change') == 'human'
        
    def test_quality_metrics(self):
        """Calculate documentation quality scores"""
        cm = ContextManager()
        scores = cm.calculate_doc_quality("docs/README.md")
        assert 'completeness' in scores
        assert 'staleness' in scores
        assert all(0 <= score <= 1 for score in scores.values())
```

## Performance Targets

| Operation | Target | Max | Notes |
|-----------|--------|-----|-------|
| add_context | 100ms | 2s | Include validation |
| get_context | 50ms | 1s | From cache/storage |
| search_contexts | 500ms | 2s | Full-text search |
| pattern_detection | 5s | 10min | Run async in background |
| analyze_doc | 200ms | 3s | Extract patterns from doc |
| learn_patterns | 2s | 30s | Learn from multiple docs |
| suggest_updates | 500ms | 5s | Analyze impact and route |
| apply_simple_update | 300ms | 2s | Version bump, list add |
| calculate_quality | 100ms | 1s | Per document metrics |

## Security Considerations

### Context Boundaries

```python
AGENT_PERMISSIONS = {
    'DesignAgent': ['read_all', 'write_design', 'read_docs'],
    'CodeAgent': ['read_design', 'read_test', 'write_code', 'read_docs'],
    'QAAgent': ['read_all', 'write_test', 'read_docs'],
    'DocumentationAgent': ['read_all', 'write_docs', 'manage_docs'],
    'DataAgent': ['read_all', 'read_docs'],  # No write
    'SwissArmyAgent': ['read_all', 'write_code', 'request_doc_update']
}

# Documentation permissions (only through Context Manager)
DOC_PERMISSIONS = {
    'create': ['DocumentationAgent', 'ContextManager'],
    'update': ['DocumentationAgent', 'ContextManager'],
    'delete': ['ContextManager'],  # Only CM can delete
    'version': ['ContextManager'],  # Only CM manages versions
}
```

### Audit Requirements

Every operation generates an audit entry:
```json
{
    "timestamp": "2024-01-20T10:30:00Z",
    "operation": "add_context",
    "user": "developer",
    "context_id": "uuid",
    "success": true
}
```

## Migration Path

### To Redis (Week 2+)
1. Implement RedisBackend matching StorageBackend interface
2. Add connection pooling and retry logic
3. Migrate hot contexts first, keep JSON for archive
4. Update configuration to use Redis

### To PostgreSQL (Future)
1. Design relational schema
2. Add full-text search indices
3. Implement PostgreSQLBackend
4. Migrate with zero downtime

## Configuration

```python
# config.py
CONTEXT_MANAGER_CONFIG = {
    'storage': {
        'backend': 'json',  # 'redis' in future
        'contexts_path': './contexts',
        'documents_path': './documents',
        'backup_interval': 3600,  # seconds
    },
    'patterns': {
        'min_occurrences': 3,
        'time_window': 86400,  # 24 hours
        'confidence_threshold': 0.7,
    },
    'api': {
        'rate_limit': 100,  # requests per minute
        'max_context_size': 10240,  # bytes
        'max_doc_size': 1048576,  # 1MB
    },
    'documents': {
        'version_limit': 100,  # Max versions per doc
        'validation_enabled': True,
        'auto_suggest': True,  # Auto-suggest doc updates
        'link_depth': 3,  # Max link traversal depth
    }
}
```

## Summary

This technical design provides a complete blueprint for implementing Context Manager v1 with documentation gateway capabilities. The focus is on:

1. **Dual Purpose**: Context management + Documentation gateway
2. **Clear Separation**: Immutable contexts vs versioned documents
3. **Quality**: TDD approach, comprehensive testing
4. **Future-proof**: Interfaces for migration, extensible schema
5. **Bootstrap**: Self-documenting from day one
6. **Consistency**: All docs go through Context Manager

Key architectural decision: Context Manager is the sole gateway for all documentation operations, ensuring consistency, versioning, and intelligent suggestions across the entire documentation ecosystem.

For implementation details and daily plan, see [IMPLEMENTATION_PLAN.md](IMPLEMENTATION_PLAN.md).