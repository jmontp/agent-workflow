# Context Manager Technical Design v2.0

> **The Project Consciousness Model**: Context Manager acts as the cognitive system for autonomous software engineering, providing memory, pattern recognition, and coordination between agents.

## Problem Statement

During development, agents frequently create redundant documentation instead of updating existing files. This happens because:
1. Agents lack awareness of existing documentation structure
2. Keyword-based search misses semantic relationships
3. No hierarchical understanding of project information
4. Missing guidance on where information should live

## Core Design Principles

### 1. Project Consciousness Model
The Context Manager provides three levels of awareness:
- **Project Map**: High-level understanding of structure and purpose
- **Task Focus**: Current objectives and relevant context
- **Detail Access**: Specific information when needed

### 2. Semantic Understanding
Move beyond keyword matching to understand:
- Document purpose and relationships
- Code-to-documentation dependencies  
- Information hierarchy and ownership
- Update patterns and triggers

### 3. Active Guidance
Proactively guide agents to:
- Update existing files instead of creating new ones
- Find the canonical location for information
- Understand what documentation already exists
- Maintain consistency across the project

## Architecture Overview

### System Components

```
Context Manager v2.0
├── Core Engine
│   ├── Context Store (immutable events)
│   ├── Project Index (semantic understanding)
│   ├── Pattern Detector (learning system)
│   └── Task Analyzer (intent understanding)
├── Intelligence Layer  
│   ├── Document Gateway (all docs go through here)
│   ├── Semantic Search (understands relationships)
│   ├── Quality Monitor (tracks documentation health)
│   └── Update Router (decides who handles what)
├── Agent Interface
│   ├── Context Collection API
│   ├── Documentation API
│   ├── Search & Discovery API
│   └── Guidance API
└── Storage Backend
    ├── Context Storage (JSON → Redis)
    ├── Index Storage (semantic graphs)
    └── Pattern Storage (learned behaviors)
```

### Key Innovation: Semantic Project Index

```python
@dataclass
class ProjectIndex:
    """Semantic understanding of project structure."""
    
    # Project understanding
    project_purpose: str
    key_components: Dict[str, ComponentInfo]
    documentation_map: Dict[str, DocInfo]
    
    # Semantic relationships
    concept_graph: Dict[str, List[str]]  # concept -> related concepts
    doc_purposes: Dict[str, str]  # file -> purpose
    information_ownership: Dict[str, str]  # topic -> canonical file
    
    # Update patterns
    update_triggers: Dict[str, List[str]]  # code pattern -> affected docs
    common_mistakes: List[DocumentationMistake]  # learned anti-patterns
```

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

## Enhanced Intelligence Systems

### 1. Task Analysis Engine

```python
@dataclass
class EnhancedTaskAnalysis:
    """Deep understanding of task intent and context needs."""
    
    # Task understanding
    task_type: TaskType  # create, update, fix, refactor, document
    primary_intent: str  # What the user really wants
    scope: TaskScope  # file, module, system-wide
    
    # Semantic extraction
    concepts: List[Concept]  # Not just keywords, but understood concepts
    entities: List[Entity]  # Files, classes, functions mentioned
    relationships: List[Relationship]  # How concepts relate
    
    # Context requirements
    required_context: List[ContextRequirement]
    optional_context: List[ContextRequirement]
    context_depth: int  # How much detail needed
    
    # Documentation implications
    likely_updates: List[DocumentationUpdate]
    update_locations: Dict[str, str]  # info type -> file path
```

### 2. Semantic Search System

```python
class SemanticSearch:
    """Understands meaning, not just keywords."""
    
    def search(self, query: str, intent: SearchIntent) -> SearchResults:
        # Parse query intent
        intent_analysis = self._analyze_intent(query)
        
        # Expand concepts semantically
        expanded_concepts = self._expand_concepts(intent_analysis.concepts)
        
        # Search with relationship awareness
        results = self._relationship_aware_search(expanded_concepts)
        
        # Rank by semantic relevance
        return self._rank_by_meaning(results, intent_analysis)
    
    def _expand_concepts(self, concepts: List[str]) -> List[str]:
        """Expand concepts using learned relationships."""
        expanded = set(concepts)
        for concept in concepts:
            # Add related concepts from graph
            expanded.update(self.concept_graph.get(concept, []))
            # Add synonyms and variations
            expanded.update(self._get_variations(concept))
        return list(expanded)
```

### 3. Documentation Gateway

```python
class DocumentationGateway:
    """All documentation operations go through here."""
    
    def before_file_operation(self, operation: FileOp) -> Guidance:
        """Called before any file operation by agents."""
        
        if operation.type == 'create':
            # Check if info belongs elsewhere
            existing = self._find_existing_location(operation.content_type)
            if existing:
                return Guidance(
                    action='update_instead',
                    target_file=existing,
                    reason=f"This information belongs in {existing}"
                )
        
        elif operation.type == 'update':
            # Ensure consistency
            conflicts = self._check_conflicts(operation)
            if conflicts:
                return Guidance(
                    action='resolve_first',
                    conflicts=conflicts
                )
        
        return Guidance(action='proceed')
    
    def _find_existing_location(self, content_type: str) -> Optional[str]:
        """Find where this type of information should live."""
        return self.project_index.information_ownership.get(content_type)
```

## Storage Strategy

### Hierarchical Storage (v2)

```python
# Directory structure
aw_context/                    # All Context Manager data
├── contexts/                  # Immutable event records
│   ├── active/               # Hot contexts
│   │   └── {date}/
│   │       └── {id}.json
│   └── archive/              # Cold storage
│       └── {year-month}/
├── project_index/            # Semantic project understanding
│   ├── structure.json        # Project map and components
│   ├── concepts.json         # Concept graph and relationships
│   ├── ownership.json        # Information → File mappings
│   └── patterns.json         # Learned patterns and anti-patterns
├── doc_intelligence/         # Documentation awareness
│   ├── metadata/            # Per-document intelligence
│   ├── quality/             # Quality tracking
│   ├── relationships/       # Doc-to-doc relationships
│   └── update_queue/        # Pending updates
├── search_index/            # Semantic search data
│   ├── embeddings/          # Future: vector embeddings
│   ├── concepts/            # Concept mappings
│   └── relationships/       # Relationship graphs
└── agent_memory/            # Agent-specific context
    ├── mistakes/            # Common errors to avoid
    ├── successes/           # Successful patterns
    └── preferences/         # Learned preferences
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

## Context Collection Enhancement

### Intelligent Context Collection

```python
class ContextCollector:
    """Provides hierarchical, relevant context to agents."""
    
    def collect_context_for_task(self, task: str) -> CollectedContext:
        """Collect context with semantic understanding."""
        
        # Deep task analysis
        analysis = self.task_analyzer.analyze(task)
        
        # Three-tier context collection
        context = CollectedContext()
        
        # Tier 1: Project Overview (always included)
        context.project_overview = self._get_project_overview(analysis)
        
        # Tier 2: Task-Specific Focus
        context.task_focus = self._collect_task_focus(analysis)
        
        # Tier 3: Detailed Information (on demand)
        context.details = self._collect_details(analysis)
        
        # Add guidance
        context.guidance = self._generate_guidance(analysis)
        
        return context
    
    def _generate_guidance(self, analysis: TaskAnalysis) -> Guidance:
        """Proactive guidance to prevent common mistakes."""
        guidance = []
        
        # Check for potential documentation creation
        if 'document' in analysis.keywords or 'create' in analysis.actions:
            existing_docs = self._find_related_docs(analysis.concepts)
            if existing_docs:
                guidance.append(
                    f"Before creating new documentation, consider updating: "
                    f"{', '.join(existing_docs)}"
                )
        
        # Warn about common mistakes
        for mistake in self.project_index.common_mistakes:
            if self._might_repeat_mistake(analysis, mistake):
                guidance.append(f"Warning: {mistake.description}")
        
        return guidance
```

### Smart Relevance Scoring

```python
def calculate_relevance(self, item: Any, task_analysis: TaskAnalysis) -> float:
    """Multi-factor relevance scoring."""
    
    score = 0.0
    
    # Semantic relevance (not just keyword match)
    semantic_score = self._semantic_similarity(item, task_analysis)
    score += semantic_score * 0.4
    
    # Relationship relevance (connected items)
    relationship_score = self._relationship_relevance(item, task_analysis)
    score += relationship_score * 0.3
    
    # Recency and modification patterns
    temporal_score = self._temporal_relevance(item, task_analysis)
    score += temporal_score * 0.2
    
    # Task-specific boosts
    task_boost = self._task_specific_boost(item, task_analysis)
    score += task_boost * 0.1
    
    return min(1.0, score)
```

## Pattern Detection

### Enhanced Pattern Recognition

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

## Implementation Phases

### Phase 1: Core v2 Engine (Current)

1. **Enhanced Task Analysis**
   - Implement semantic task understanding
   - Build concept extraction beyond keywords
   - Create relationship detection

2. **Project Index System**
   - Build semantic project map
   - Create information ownership mappings
   - Implement concept graph

3. **Documentation Gateway**
   - Intercept file operations
   - Guide to existing files
   - Prevent redundant creation

### Phase 2: Intelligence Layer (Next)

1. **Semantic Search**
   - Concept expansion
   - Relationship-aware search
   - Intent understanding

2. **Quality Monitoring**
   - Documentation health metrics
   - Staleness detection
   - Consistency checking

3. **Learning System**
   - Pattern extraction from usage
   - Mistake detection and prevention
   - Success pattern reinforcement

### Phase 3: Advanced Features (Future)

1. **Neural Embeddings**
   - Vector representations of concepts
   - Semantic similarity search
   - Cross-language understanding

2. **Predictive Guidance**
   - Anticipate documentation needs
   - Suggest updates proactively
   - Learn from agent behaviors

3. **Multi-Agent Coordination**
   - Shared context optimization
   - Conflict resolution
   - Collaborative documentation

## Documentation Intelligence

### Anti-Redundancy System

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

### Core APIs

```python
# Context Collection API
POST /api/context/collect
{
    "task": "Fix authentication in user login",
    "max_tokens": 4000,
    "include_guidance": true
}

# Returns hierarchical context:
{
    "project_overview": {
        "purpose": "Autonomous software engineering system",
        "key_components": ["Context Manager", "Agents", "Documentation"],
        "current_focus": "Authentication system"
    },
    "task_focus": {
        "relevant_files": [
            {"path": "auth/login.py", "relevance": 0.95},
            {"path": "docs/AUTH.md", "relevance": 0.85}
        ],
        "concepts": ["authentication", "JWT", "user sessions"],
        "recent_changes": [...]
    },
    "guidance": [
        "Authentication logic is in auth/login.py",
        "Update docs/AUTH.md after changes",
        "Related test files: tests/test_auth.py"
    ]
}

# Documentation Gateway API  
POST /api/docs/check-operation
{
    "operation": "create",
    "path": "AUTH_FIX.md",
    "content_type": "authentication_documentation"
}

# Returns guidance:
{
    "action": "update_instead",
    "target_file": "docs/AUTH.md",
    "reason": "Authentication documentation belongs in docs/AUTH.md",
    "existing_sections": ["Overview", "JWT Implementation", "Troubleshooting"]
}
```

### Search & Discovery API

```python
# Semantic search
GET /api/search?q=authentication+problems&intent=debug

# Returns semantically relevant results:
{
    "direct_matches": [...],
    "related_concepts": ["JWT", "sessions", "login"],
    "expanded_results": [...],
    "suggested_files": ["auth/login.py", "docs/AUTH.md", "tests/test_auth.py"]
}

# Find information location
GET /api/docs/where-does-this-belong?info=api_endpoints

# Returns:
{
    "canonical_location": "docs/API.md",
    "reason": "API documentation is centralized in docs/API.md",
    "existing_structure": ["Endpoints", "Authentication", "Examples"]
}
```

## RESTful Endpoints (Complete List)

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

## Key Innovations

### 1. Project Consciousness Model

The Context Manager acts as the "consciousness" of the project:
- **Memory**: Stores all events and decisions
- **Understanding**: Semantic grasp of project structure
- **Awareness**: Knows what exists and where
- **Guidance**: Actively prevents mistakes

### 2. Hierarchical Context Delivery

Instead of dumping all context, provide it in tiers:
1. **Overview**: Project purpose and structure (always)
2. **Focus**: Task-specific relevant information
3. **Details**: Deep information when needed

This prevents context overflow while ensuring agents have what they need.

### 3. Anti-Redundancy Mechanisms

- **Pre-operation checks**: Catch file creation before it happens
- **Semantic understanding**: Know that "AUTH_FIX.md" content belongs in "docs/AUTH.md"
- **Learning system**: Remember and prevent repeated mistakes
- **Active guidance**: Tell agents where information should go

### 4. Semantic vs Keyword Search

**Old (Keyword)**:
- Search: "authentication"
- Results: Any file containing "authentication"

**New (Semantic)**:
- Search: "authentication problems"
- Understanding: User wants to debug auth issues
- Results: auth/login.py, error logs, AUTH.md troubleshooting section, recent auth-related contexts

## Testing Strategy

### Test Coverage for v2 Features

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

## Migration Strategy

### From v1 to v2

1. **Preserve existing functionality**
   - All v1 APIs remain functional
   - Add v2 endpoints alongside
   - Gradual migration path

2. **Build semantic index**
   - Scan existing project
   - Extract relationships
   - Learn patterns

3. **Enable gateway features**
   - Start with warnings
   - Move to active guidance
   - Finally enforce best practices

### Removing Redundant Documentation

Based on this unified design, the following files should be removed:

**Root directory files to remove**:
- `CONTEXT_COLLECTION_IMPROVEMENT_PLAN.md` - Merged into this design
- `CONTEXT_MANAGER_CLEANUP_PLAN.md` - Implementation detail, not design
- `CONTEXT_MANAGER_CLEANUP_DETAILS.md` - Implementation detail, not design

**Consolidation actions**:
- Move cleanup plans to `IMPLEMENTATION_NOTES.md` as lessons learned
- Extract improvement ideas into GitHub issues
- Keep only canonical documentation in docs/agents/context-manager/

## Summary

### The Context Manager v2 Vision

Context Manager v2 evolves from a passive context store to an active project consciousness that:

1. **Understands** project structure semantically, not just through keywords
2. **Guides** agents to update existing files instead of creating new ones  
3. **Learns** from patterns to prevent repeated mistakes
4. **Coordinates** all documentation through a central gateway
5. **Provides** hierarchical context that matches task needs

### Key Architectural Decisions

1. **Semantic Project Index**: Deep understanding of project structure and relationships
2. **Documentation Gateway**: All file operations go through Context Manager
3. **Hierarchical Context**: Overview → Focus → Details approach
4. **Active Guidance**: Proactively prevent redundancy and maintain consistency
5. **Learning System**: Continuously improve from usage patterns

### Next Steps

1. Update `IMPLEMENTATION_PLAN.md` with v2 features
2. Remove redundant documentation files
3. Begin implementing semantic project index
4. Add documentation gateway hooks
5. Enhance context collection with guidance

This design directly addresses the problem we experienced: agents creating redundant files because they lack awareness of existing documentation structure. With v2, the Context Manager will actively guide agents to the right places, preventing documentation sprawl and maintaining project coherence.