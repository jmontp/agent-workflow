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

### Design Rationale

- **Dataclasses over Pydantic**: Native Python, good IDE support, no external dependencies
- **Flexible Metadata**: Core fields are typed, metadata dict for extensibility
- **Compliance Built-in**: Audit and sensitivity fields for medical device requirements

## Storage Strategy

### JSON Storage (v1)

```python
# Directory structure
contexts/
├── active/              # Hot contexts
│   └── {date}/
│       └── {context_id}.json
├── archive/             # Cold storage
│   └── {year-month}/
└── indices/             # Search indices
    ├── by_type.json
    ├── by_source.json
    └── patterns.json
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

class JSONFileBackend(StorageBackend):
    """v1 implementation using JSON files"""
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
```

## Performance Targets

| Operation | Target | Max | Notes |
|-----------|--------|-----|-------|
| add_context | 10ms | 50ms | Include validation |
| get_context | 5ms | 20ms | From cache |
| search | 50ms | 200ms | Full-text search |
| pattern_detection | 100ms | 500ms | Run async |

## Security Considerations

### Context Boundaries

```python
AGENT_PERMISSIONS = {
    'DesignAgent': ['read_all', 'write_design'],
    'CodeAgent': ['read_design', 'read_test', 'write_code'],
    'QAAgent': ['read_all', 'write_test'],
    'DocumentationAgent': ['read_all', 'write_docs'],
    'DataAgent': ['read_all']  # No write
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
        'path': './contexts',
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
    }
}
```

## Summary

This technical design provides a complete blueprint for implementing Context Manager v1. The focus is on:

1. **Simplicity**: JSON storage, basic patterns, clean API
2. **Quality**: TDD approach, comprehensive testing
3. **Future-proof**: Interfaces for migration, extensible schema
4. **Bootstrap**: Self-documenting from day one

For implementation details and daily plan, see [IMPLEMENTATION_PLAN.md](IMPLEMENTATION_PLAN.md).