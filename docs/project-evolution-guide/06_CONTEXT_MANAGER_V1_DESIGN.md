# Context Manager v1 Design Document

## Executive Summary

The Context Manager is a developer productivity tool that captures, organizes, and learns from development context to provide actionable insights. Built with TDD principles, it serves as both a practical tool and a learning system that improves through use. This document outlines the complete design for v1, focusing on pragmatic choices that enable quick iteration while maintaining quality standards suitable for medical device development environments.

## 1. Context Schema Design

### Core Data Structure

```python
from dataclasses import dataclass
from typing import Dict, List, Optional, Any, Union
from datetime import datetime
from enum import Enum

class ContextType(Enum):
    """Types of context entries"""
    DECISION = "decision"
    PROBLEM = "problem"
    SOLUTION = "solution"
    LEARNING = "learning"
    TODO = "todo"
    QUESTION = "question"
    ASSUMPTION = "assumption"
    CONSTRAINT = "constraint"

class Priority(Enum):
    """Priority levels for context entries"""
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4

@dataclass
class ContextEntry:
    """Individual context entry"""
    id: str  # UUID
    type: ContextType
    title: str
    content: str
    tags: List[str]
    priority: Priority
    created_at: datetime
    updated_at: datetime
    
    # Relationships
    parent_id: Optional[str] = None
    related_ids: List[str] = field(default_factory=list)
    
    # Metadata
    author: str = "system"
    source: str = "manual"  # manual, auto-detected, imported
    confidence: float = 1.0  # 0-1 confidence score
    
    # Compliance fields
    reviewed: bool = False
    review_date: Optional[datetime] = None
    reviewer: Optional[str] = None
    
    # Pattern detection
    patterns: List[str] = field(default_factory=list)
    suggestions: List[str] = field(default_factory=list)
    
    # Custom fields for flexibility
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class ContextSession:
    """Groups related context entries"""
    id: str
    name: str
    description: str
    created_at: datetime
    updated_at: datetime
    entry_ids: List[str]
    tags: List[str]
    metadata: Dict[str, Any]

@dataclass
class ContextPattern:
    """Detected patterns across contexts"""
    id: str
    name: str
    description: str
    pattern_type: str  # "recurring_decision", "common_problem", etc.
    occurrences: List[Dict[str, Any]]
    confidence: float
    suggestions: List[str]
    first_seen: datetime
    last_seen: datetime
    frequency: int
```

### Design Rationale

- **Structured but Flexible**: Core fields are strongly typed, with metadata dict for extensibility
- **Compliance-Ready**: Built-in review fields for medical device requirements
- **Relationship Tracking**: Parent/child and related entries for context graphs
- **Pattern-Aware**: Fields for detected patterns and generated suggestions
- **Versioning-Friendly**: Schema designed for easy evolution

## 2. Storage Strategy

### File Format: JSON with Schema Versioning

```python
{
    "schema_version": "1.0.0",
    "created_at": "2024-01-15T10:00:00Z",
    "updated_at": "2024-01-15T14:30:00Z",
    "entries": [...],
    "sessions": [...],
    "patterns": [...],
    "metadata": {
        "app_version": "0.1.0",
        "environment": "development"
    }
}
```

### Directory Structure

```
context_data/
├── current/
│   ├── context.json          # Active context database
│   ├── context.schema.json   # JSON Schema for validation
│   └── .lock                 # File lock for concurrent access
├── backups/
│   ├── daily/
│   │   └── context_2024-01-15.json
│   ├── weekly/
│   │   └── context_2024-W03.json
│   └── before_migration/
│       └── context_pre_v2.json
├── exports/
│   ├── markdown/
│   └── compliance/
└── logs/
    └── context_manager.log
```

### Migration Path to Redis

```python
class StorageBackend(ABC):
    """Abstract storage interface"""
    @abstractmethod
    async def save_entry(self, entry: ContextEntry) -> bool:
        pass
    
    @abstractmethod
    async def get_entry(self, id: str) -> Optional[ContextEntry]:
        pass
    
    @abstractmethod
    async def search_entries(self, query: Dict[str, Any]) -> List[ContextEntry]:
        pass

class JSONFileBackend(StorageBackend):
    """v1 JSON file implementation"""
    pass

class RedisBackend(StorageBackend):
    """Future Redis implementation"""
    pass
```

### Backup Strategy

- **Automatic Daily Backups**: Triggered on first write each day
- **Weekly Archives**: Compressed weekly snapshots
- **Pre-Migration Snapshots**: Before any schema changes
- **Export Formats**: Markdown for readability, JSON for data transfer

## 3. Pattern Detection Algorithm

### v1 Simple Pattern Detection

```python
class PatternDetector:
    """Simple pattern detection for v1"""
    
    def detect_patterns(self, entries: List[ContextEntry]) -> List[ContextPattern]:
        patterns = []
        
        # 1. Recurring Keywords
        keyword_freq = self._analyze_keywords(entries)
        patterns.extend(self._keyword_patterns(keyword_freq))
        
        # 2. Time-based Patterns
        time_patterns = self._analyze_temporal_patterns(entries)
        patterns.extend(time_patterns)
        
        # 3. Type Sequences
        sequence_patterns = self._analyze_type_sequences(entries)
        patterns.extend(sequence_patterns)
        
        # 4. Solution Effectiveness
        solution_patterns = self._analyze_solutions(entries)
        patterns.extend(solution_patterns)
        
        return patterns
    
    def generate_suggestions(self, 
                           context: ContextEntry, 
                           patterns: List[ContextPattern]) -> List[str]:
        """Generate actionable suggestions"""
        suggestions = []
        
        # Based on context type
        if context.type == ContextType.PROBLEM:
            suggestions.extend(self._suggest_solutions(context, patterns))
        elif context.type == ContextType.DECISION:
            suggestions.extend(self._suggest_considerations(context, patterns))
        
        # Based on patterns
        for pattern in patterns:
            if self._pattern_applies(pattern, context):
                suggestions.extend(pattern.suggestions)
        
        return suggestions
```

### Patterns to Track

1. **Recurring Decisions**: Similar decisions made multiple times
2. **Problem-Solution Pairs**: Problems that led to effective solutions
3. **Time-based Patterns**: Issues that occur at specific times/intervals
4. **Workflow Patterns**: Common sequences of actions
5. **Knowledge Gaps**: Repeated questions or uncertainties
6. **Technical Debt Indicators**: Temporary solutions that persist

### Learning Approach

- **Explicit Feedback**: Users can mark suggestions as helpful/not helpful
- **Implicit Signals**: Track which suggestions lead to actions
- **Pattern Confidence**: Adjust based on occurrence frequency and feedback
- **Continuous Refinement**: Patterns evolve as more data is collected

## 4. API Design

### RESTful Endpoints

```python
# Base URL: /api/context/v1

# Context Entries
POST   /entries              # Create new entry
GET    /entries              # List entries (with filters)
GET    /entries/{id}         # Get specific entry
PUT    /entries/{id}         # Update entry
DELETE /entries/{id}         # Delete entry
GET    /entries/{id}/related # Get related entries

# Sessions
POST   /sessions             # Create session
GET    /sessions             # List sessions
GET    /sessions/{id}        # Get session with entries
PUT    /sessions/{id}        # Update session
DELETE /sessions/{id}        # Delete session

# Patterns & Suggestions
GET    /patterns             # Get detected patterns
GET    /suggestions          # Get suggestions for current context
POST   /feedback             # Submit feedback on suggestions

# Search & Analytics
POST   /search               # Advanced search
GET    /analytics/summary    # Context analytics
GET    /analytics/trends     # Pattern trends

# Import/Export
POST   /import               # Import context data
GET    /export/{format}      # Export (json, markdown, csv)
```

### WebSocket Events

```python
# WebSocket endpoint: /ws/context

# Events from server
{
    "event": "entry_created",
    "data": { "entry": {...} }
}

{
    "event": "pattern_detected",
    "data": { "pattern": {...}, "confidence": 0.85 }
}

{
    "event": "suggestion_generated",
    "data": { "suggestions": [...] }
}

# Events from client
{
    "event": "subscribe",
    "data": { "types": ["entries", "patterns"] }
}

{
    "event": "feedback",
    "data": { "suggestion_id": "...", "helpful": true }
}
```

### Error Handling

```python
class ContextError(Exception):
    """Base exception for Context Manager"""
    pass

class ValidationError(ContextError):
    """Schema validation failed"""
    pass

class StorageError(ContextError):
    """Storage operation failed"""
    pass

class PatternError(ContextError):
    """Pattern detection error"""
    pass

# Standard error response
{
    "error": {
        "code": "VALIDATION_ERROR",
        "message": "Invalid context entry",
        "details": {
            "field": "priority",
            "reason": "Must be between 1 and 4"
        }
    },
    "request_id": "uuid",
    "timestamp": "2024-01-15T10:00:00Z"
}
```

### Integration with Flask App

```python
# context_manager_routes.py
from flask import Blueprint, jsonify, request
from context_manager import ContextManager

context_bp = Blueprint('context', __name__, url_prefix='/api/context/v1')
cm = ContextManager()

@context_bp.route('/entries', methods=['POST'])
async def create_entry():
    """Create context entry"""
    try:
        data = request.get_json()
        entry = await cm.create_entry(**data)
        return jsonify(entry.to_dict()), 201
    except ValidationError as e:
        return jsonify({"error": str(e)}), 400

# In main app.py
app.register_blueprint(context_bp)
```

## 5. TDD Test Plan

### Core Test Cases

```python
# test_context_manager.py

class TestContextEntry:
    """Test context entry operations"""
    
    def test_create_minimal_entry(self):
        """Test creating entry with minimum required fields"""
        
    def test_create_full_entry(self):
        """Test creating entry with all fields"""
        
    def test_invalid_entry_validation(self):
        """Test schema validation catches errors"""
        
    def test_entry_relationships(self):
        """Test parent/child and related entries"""
        
    def test_entry_serialization(self):
        """Test JSON serialization/deserialization"""

class TestPatternDetection:
    """Test pattern detection algorithms"""
    
    def test_keyword_pattern_detection(self):
        """Test recurring keyword detection"""
        
    def test_temporal_pattern_detection(self):
        """Test time-based pattern detection"""
        
    def test_sequence_pattern_detection(self):
        """Test action sequence patterns"""
        
    def test_suggestion_generation(self):
        """Test generating relevant suggestions"""
        
    def test_pattern_confidence_scoring(self):
        """Test confidence calculation"""

class TestStorage:
    """Test storage operations"""
    
    def test_save_and_retrieve_entry(self):
        """Test basic CRUD operations"""
        
    def test_concurrent_access(self):
        """Test file locking works correctly"""
        
    def test_backup_creation(self):
        """Test automatic backup triggers"""
        
    def test_data_migration(self):
        """Test schema migration process"""
        
    def test_search_functionality(self):
        """Test search with various filters"""

class TestAPI:
    """Test REST API endpoints"""
    
    def test_create_entry_endpoint(self):
        """Test POST /entries"""
        
    def test_search_endpoint(self):
        """Test POST /search with queries"""
        
    def test_websocket_events(self):
        """Test real-time event delivery"""
        
    def test_error_responses(self):
        """Test proper error formatting"""
```

### Bootstrap Feature Tests

```python
class TestBootstrapFeatures:
    """Test self-documentation features"""
    
    def test_capture_own_decisions(self):
        """Test Context Manager documents its own development"""
        
    def test_pattern_learning_from_self(self):
        """Test learning from own development patterns"""
        
    def test_suggestion_effectiveness(self):
        """Test suggestions improve over time"""
```

### Performance Benchmarks

```python
class TestPerformance:
    """Performance benchmarks"""
    
    def test_large_dataset_search(self):
        """Test search with 10,000+ entries completes < 100ms"""
        
    def test_pattern_detection_speed(self):
        """Test pattern detection on 1,000 entries < 500ms"""
        
    def test_concurrent_write_performance(self):
        """Test 10 concurrent writes complete < 1s"""
```

## 6. Bootstrap Implementation Plan

### Self-Documentation Approach

1. **Capture Design Decisions**: Every design choice becomes a context entry
2. **Track Problems & Solutions**: Development challenges and resolutions
3. **Document Assumptions**: Explicit capture of assumptions made
4. **Learning Patterns**: Identify what patterns emerge during development

### Bootstrap Entries

```python
# Initial context entries for Context Manager development
bootstrap_entries = [
    {
        "type": "DECISION",
        "title": "Choose JSON for v1 storage",
        "content": "Selected JSON over SQLite for simplicity and human readability",
        "tags": ["storage", "architecture", "v1"],
        "related": ["Consider Redis migration path"]
    },
    {
        "type": "CONSTRAINT", 
        "title": "Medical device compliance requirement",
        "content": "Must support audit trails and data integrity checks",
        "tags": ["compliance", "requirements"],
        "priority": "CRITICAL"
    },
    {
        "type": "LEARNING",
        "title": "TDD helps with API design",
        "content": "Writing tests first clarified the API interface needs",
        "tags": ["methodology", "testing", "api"]
    }
]
```

### Pattern Learning Process

1. **Week 1**: Manually tag patterns noticed during development
2. **Week 2**: Implement basic pattern detection on bootstrap data
3. **Week 3**: Refine patterns based on actual usage
4. **Week 4**: Generate first automated suggestions

## 7. UI Integration Ideas

### Minimal UI Changes

```javascript
// Add context capture to existing workflow
class ContextCapture {
    constructor() {
        this.quickCapture = new QuickCaptureWidget();
        this.contextPanel = new ContextPanel();
    }
    
    // Keyboard shortcut: Ctrl+Shift+C
    openQuickCapture() {
        this.quickCapture.show({
            types: ['DECISION', 'PROBLEM', 'LEARNING'],
            onSave: (entry) => this.saveContext(entry)
        });
    }
}
```

### Context Visualization

```html
<!-- Sidebar Context Panel -->
<div class="context-panel">
    <div class="context-current">
        <h3>Current Context</h3>
        <div class="context-tags">
            <span class="tag">authentication</span>
            <span class="tag">api-design</span>
        </div>
    </div>
    
    <div class="context-suggestions">
        <h3>Suggestions</h3>
        <ul>
            <li>Consider rate limiting (similar: 3 decisions)</li>
            <li>Review error handling pattern</li>
        </ul>
    </div>
    
    <div class="context-related">
        <h3>Related Contexts</h3>
        <ul>
            <li>JWT implementation decision</li>
            <li>Session management approach</li>
        </ul>
    </div>
</div>
```

### Developer-Focused Features

1. **Quick Capture**: Keyboard shortcut for instant context capture
2. **Auto-Detection**: Detect context from code comments and commits
3. **IDE Integration**: VS Code extension for seamless capture
4. **CLI Tools**: Command-line context management
5. **Export Options**: Generate documentation from context

### Real-time Updates

```javascript
// WebSocket integration for live updates
const contextSocket = new WebSocket('/ws/context');

contextSocket.on('pattern_detected', (data) => {
    showNotification(`New pattern: ${data.pattern.name}`);
    updateSuggestionsPanel(data.pattern.suggestions);
});

contextSocket.on('suggestion_generated', (data) => {
    if (data.confidence > 0.8) {
        showInlineHint(data.suggestion);
    }
});
```

## 8. Day-by-Day Schedule

### Week 1: Foundation (Mon-Fri)

**Monday: Schema & Storage Design**
- Morning: Write schema tests (test_schema.py)
- Afternoon: Implement ContextEntry, validation
- End of day: Basic JSON storage working

**Tuesday: Storage Implementation**
- Morning: Write storage tests (test_storage.py)
- Afternoon: Implement JSONFileBackend
- End of day: CRUD operations complete

**Wednesday: Pattern Detection Core**
- Morning: Write pattern detection tests
- Afternoon: Implement basic PatternDetector
- End of day: Keyword patterns working

**Thursday: API Foundation**
- Morning: Write API tests
- Afternoon: Implement Flask blueprints
- End of day: Basic REST endpoints working

**Friday: Integration & Bootstrap**
- Morning: Integration tests
- Afternoon: Create bootstrap entries
- End of day: Self-documentation started

### Week 2: Advanced Features (Mon-Fri)

**Monday: Advanced Patterns**
- Morning: Temporal pattern tests
- Afternoon: Implement time-based patterns
- End of day: Multiple pattern types working

**Tuesday: Suggestion Engine**
- Morning: Suggestion generation tests
- Afternoon: Implement suggestion logic
- End of day: Basic suggestions working

**Wednesday: Search & Query**
- Morning: Search functionality tests
- Afternoon: Implement search filters
- End of day: Advanced search working

**Thursday: WebSocket Integration**
- Morning: WebSocket tests
- Afternoon: Real-time events implementation
- End of day: Live updates working

**Friday: UI Integration**
- Morning: UI component tests
- Afternoon: Implement minimal UI
- End of day: Quick capture working

### Week 3: Polish & Performance (Mon-Fri)

**Monday: Performance Optimization**
- Morning: Performance benchmarks
- Afternoon: Optimize slow operations
- End of day: Meet performance targets

**Tuesday: Error Handling**
- Morning: Error case tests
- Afternoon: Comprehensive error handling
- End of day: Robust error responses

**Wednesday: Import/Export**
- Morning: Import/export tests
- Afternoon: Multiple format support
- End of day: Data portability complete

**Thursday: Documentation**
- Morning: API documentation
- Afternoon: User guide
- End of day: Complete docs

**Friday: Release Prep**
- Morning: Final integration tests
- Afternoon: Deployment preparation
- End of day: v1.0 ready

### Week 4: Learning & Iteration (Mon-Fri)

**Monday: Pattern Analysis**
- Analyze bootstrap patterns
- Refine detection algorithms
- Document learnings

**Tuesday: Suggestion Tuning**
- Review suggestion effectiveness
- Implement feedback loop
- Adjust confidence scores

**Wednesday: Performance Monitoring**
- Deploy monitoring
- Analyze usage patterns
- Plan optimizations

**Thursday: User Feedback**
- Gather developer feedback
- Prioritize improvements
- Plan v1.1 features

**Friday: Retrospective**
- Team retrospective
- Document lessons learned
- Create v2 roadmap

## 9. Key Design Decisions

### Decision: JSON Storage for v1
**Rationale**: Human-readable, simple implementation, easy debugging
**Trade-off**: Performance vs simplicity (accepted for v1)
**Migration Path**: Storage interface allows Redis swap

### Decision: Dataclasses for Schema
**Rationale**: Type safety, IDE support, serialization support
**Trade-off**: Python 3.7+ requirement (acceptable)
**Alternative**: Pydantic (considered for v2)

### Decision: Simple Pattern Detection
**Rationale**: Start with proven algorithms, iterate based on data
**Trade-off**: Accuracy vs complexity (favor simplicity)
**Evolution**: ML-based detection in future versions

### Decision: Flask Integration
**Rationale**: Leverage existing app infrastructure
**Trade-off**: Coupling vs convenience (minimal coupling)
**Future**: Could extract to standalone service

## 10. Success Metrics

### Quantitative Metrics
- Response time < 100ms for searches
- Pattern detection accuracy > 70%
- Zero data loss in 1000 operations
- 90% test coverage

### Qualitative Metrics
- Developers find suggestions helpful
- Reduced context switching time
- Improved decision documentation
- Natural workflow integration

## 11. Risk Mitigation

### Technical Risks
- **Data Loss**: Automatic backups, atomic writes
- **Performance**: Pagination, caching, indices
- **Concurrency**: File locking, operation queuing

### Process Risks
- **Scope Creep**: Strict v1 feature set
- **Over-Engineering**: YAGNI principle
- **Integration Issues**: Incremental integration

## 12. Future Considerations

### v1.1 Enhancements
- Basic ML pattern detection
- Team collaboration features
- Extended export formats
- Plugin architecture

### v2.0 Vision
- Redis backend
- Distributed architecture
- Advanced AI suggestions
- Full IDE integration

## Conclusion

The Context Manager v1 represents a pragmatic approach to developer productivity through context awareness. By starting simple, using TDD, and focusing on real value delivery, we create a foundation for continuous improvement. The bootstrap approach ensures the tool helps build itself, providing immediate validation of its concepts.

The key to success is maintaining balance: simple enough to build quickly, robust enough for medical device environments, and flexible enough to evolve based on real usage patterns.