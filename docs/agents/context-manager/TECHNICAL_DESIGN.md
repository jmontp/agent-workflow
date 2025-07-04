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

### Document Data Structure

```python
class DocumentType(Enum):
    """Types of documentation managed by Context Manager."""
    README = "readme"
    API_SPEC = "api_spec"
    ARCHITECTURE = "architecture"
    DECISION_RECORD = "decision_record"
    WORKFLOW = "workflow"
    AGENT_SPEC = "agent_spec"
    USER_GUIDE = "user_guide"
    CHANGELOG = "changelog"
    MEETING_NOTES = "meeting_notes"
    TEST_PLAN = "test_plan"

@dataclass
class Document:
    """Mutable documentation artifact managed by Context Manager."""
    
    # Required fields
    path: str                    # File path (e.g., "docs/README.md")
    doc_type: DocumentType       # Type of documentation
    content: str                 # Current content
    version: int                 # Version number
    last_modified: datetime      # Last update timestamp
    modified_by: str             # Agent/human identifier
    
    # Relationships
    linked_contexts: List[str] = field(default_factory=list)   # Related context IDs
    linked_docs: List[str] = field(default_factory=list)       # Related document paths
    
    # Metadata
    metadata: Dict[str, Any] = field(default_factory=dict)
    sections: Dict[str, str] = field(default_factory=dict)     # Section mapping
    tags: List[str] = field(default_factory=list)
    
    # Quality metrics
    completeness_score: float = 0.0  # 0-1 score
    consistency_score: float = 0.0    # 0-1 score
    last_validated: Optional[datetime] = None
    
    def validate_standards(self) -> ValidationResult:
        """Validate document against type-specific standards."""
        # Implementation in document_validator.py
```

### Context vs Document Design Rationale

- **Context = Immutable Events**: Once created, contexts never change (audit trail)
- **Documents = Mutable Knowledge**: Documents evolve through versions
- **Bidirectional Linking**: Contexts can reference docs that existed at that time
- **Separation of Concerns**: Different storage, different lifecycles

- **Dataclasses over Pydantic**: Native Python, good IDE support, no external dependencies
- **Flexible Metadata**: Core fields are typed, metadata dict for extensibility
- **Compliance Built-in**: Audit and sensitivity fields for medical device requirements

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

documents/                  # Mutable documentation
├── current/                # Current versions
│   ├── README.md.json
│   ├── CHANGELOG.md.json
│   ├── api/
│   │   └── openapi.json
│   └── guides/
│       └── user-guide.json
├── versions/               # Version history
│   └── {doc_path}/
│       └── v{version}.json
└── indices/                # Document search indices
    ├── by_type.json
    ├── by_tag.json
    └── relationships.json
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

class DocumentBackend(ABC):
    """Abstract document storage interface"""
    
    @abstractmethod
    def save_document(self, doc: Document) -> bool:
        pass
    
    @abstractmethod
    def get_document(self, path: str, version: Optional[int] = None) -> Optional[Document]:
        pass
    
    @abstractmethod
    def search_documents(self, query: Dict[str, Any]) -> List[Document]:
        pass
    
    @abstractmethod
    def get_versions(self, path: str) -> List[int]:
        pass

class JSONFileBackend(StorageBackend):
    """v1 implementation using JSON files"""
    pass

class JSONDocumentBackend(DocumentBackend):
    """v1 document storage using JSON"""
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

# Documentation Gateway
POST   /api/docs/                       # Create document
GET    /api/docs/{path}                 # Get document (latest version)
GET    /api/docs/{path}/v/{version}    # Get specific version
PUT    /api/docs/{path}                 # Update document
GET    /api/docs/{path}/versions        # List all versions
POST   /api/docs/search                 # Search documents
POST   /api/docs/validate               # Validate against standards
GET    /api/docs/{path}/suggestions     # Get update suggestions
POST   /api/docs/link                   # Link documents
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

// Documentation events
socket.on('doc_updated', (data) => {
    notifyDocChange(data.path, data.version);
});

socket.on('doc_suggestion', (data) => {
    showDocSuggestion(data.suggestion);
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

class TestDocumentManager:
    def test_document_versioning(self):
        """Document updates create new versions"""
        cm = ContextManager()
        doc_id = cm.create_doc(
            DocumentType.README,
            "# Initial Content",
            {"author": "test"}
        )
        
        cm.update_doc(doc_id, {"content": "# Updated Content"})
        versions = cm.get_versions(doc_id)
        assert len(versions) == 2
        
    def test_document_standards_validation(self):
        """Documents validated against standards"""
        # Create doc missing required sections
        # Verify validation fails with specific errors
        
    def test_context_document_linking(self):
        """Contexts and documents can be linked"""
        # Create context referencing doc
        # Update doc
        # Verify context still references correct version
```

## Performance Targets

| Operation | Target | Max | Notes |
|-----------|--------|-----|-------|
| add_context | 100ms | 2s | Include validation |
| get_context | 50ms | 1s | From cache/storage |
| search_contexts | 500ms | 2s | Full-text search |
| pattern_detection | 5s | 10min | Run async in background |
| create_doc | 200ms | 3s | Include validation |
| update_doc | 300ms | 3s | Version + validation |
| search_docs | 500ms | 2s | Full-text search |
| validate_standards | 100ms | 1s | Per document |

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