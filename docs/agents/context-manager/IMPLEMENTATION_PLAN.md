# Context Manager Implementation Plan

> **Note**: This document contains the week-by-week implementation details extracted from the project evolution phase. For the complete journey, see the [project evolution guide](../../project-evolution-guide/).

## Overview

This plan outlines the practical implementation of Context Manager v1 over 4 weeks, using TDD principles and bootstrap methodology. Updated to include documentation gateway capabilities as the sole manager of all documentation operations.

## Week 1: Core Foundation

### Day 1-2: Schema & Core Tests
```python
# test_context_schema.py
def test_context_creation():
    """Test basic context creation with required fields"""
    context = Context(
        id="test-123",
        type=ContextType.DEVELOPMENT,
        source="human",
        timestamp=datetime.now(),
        data={"decision": "Use JSON storage"}
    )
    assert context.validate()

def test_context_validation():
    """Test schema validation catches missing fields"""
    with pytest.raises(ValidationError):
        Context(type="invalid_type")  # Should fail

# test_doc_metadata.py
def test_metadata_creation():
    """Test metadata tracking for existing docs"""
    metadata = DocMetadata(
        path="docs/README.md",
        doc_type="readme",
        last_analyzed=datetime.now(),
        patterns_detected=DocPattern(),
        quality_scores={"completeness": 0.8}
    )
    assert metadata.path == "docs/README.md"

def test_pattern_extraction():
    """Test extracting patterns from doc"""
    patterns = cm.learn_doc_patterns("docs/README.md")
    assert patterns.section_headers is not None
    # Verify learned markdown style
```

### Day 2-3: Storage Implementation
```python
# context_manager.py (~150 lines max)
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List, Optional, Any
import json
import uuid

class ContextManager:
    def __init__(self):
        self.contexts: Dict[str, Context] = {}
        self.history: List[Context] = []
        self.patterns: Dict[str, int] = {}
        self.audit_log: List[Dict] = []
        
    # Core Features for Bootstrap
    def log_decision(self, decision: str, reasoning: str) -> str:
        """Track development decisions for self-improvement"""
        context = Context(
            id=str(uuid.uuid4()),
            type="development",
            source="human",
            timestamp=datetime.now(),
            data={
                "decision": decision,
                "reasoning": reasoning
            },
            metadata={
                "tokens": len(decision + reasoning) // 4
            }
        )
        return self.add_context(context)
```

### Day 3-4: Pattern Detection
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

### Day 4-5: API Integration
```python
# Enhanced app.py integration
from context_manager import ContextManager

cm = ContextManager()

@app.route('/api/context/decision', methods=['POST'])
def log_decision():
    """Log development decision"""
    data = request.json
    context_id = cm.log_decision(
        data['decision'],
        data['reasoning']
    )
    return jsonify({"context_id": context_id})

@app.route('/api/context/suggest')
def suggest_tasks():
    """Get task suggestions"""
    suggestions = cm.suggest_next_task()
    return jsonify({"suggestions": suggestions})
```

### Day 5: Bootstrap Features
```python
# Usage During Development
# Day 1
cm.log_decision(
    "Starting with simple dict storage",
    "Need quick iteration, will add Redis later"
)

# Day 2
cm.log_decision(
    "Adding audit trail early",
    "Medical device compliance requires full traceability"
)

# Day 3
suggestions = cm.suggest_next_task()
# Returns: ["Add persistence - many decisions to track"]

# Day 4
cm.log_decision(
    "Implementing file-based persistence",
    "Based on suggestion, need to maintain state between sessions"
)
```

## Week 1 Deliverables

### Bootstrap Features ✓
- [x] Log development decisions
- [x] Track patterns in usage
- [x] Suggest next tasks
- [x] Basic persistence
- [x] Audit trail (compliance foundation)

### Integration ✓
- [x] REST API endpoints
- [x] WebSocket integration
- [x] State machine context tracking

### Documentation Focus ✓
- [x] Every decision logged with reasoning
- [x] Audit trail for all context operations
- [x] Pattern detection for self-improvement

### Documentation Intelligence (New) ✓
- [ ] DocMetadata schema implementation
- [ ] Pattern learning system
- [ ] Update detection from contexts
- [ ] Routing by complexity
- [ ] Quality metrics calculation
- [ ] Learn from manual updates

## Week 2: Advanced Features

### Monday: Advanced Patterns
- Temporal pattern tests
- Implement time-based patterns
- Multiple pattern types working

### Tuesday: Suggestion Engine & Document Validation
- Suggestion generation tests
- Implement suggestion logic
- Basic suggestions working
- Document standards validation
- Validation rules per doc type
- Documentation quality scoring
- Auto-suggestion for doc improvements

```python
def test_learn_from_mistakes():
    """Test system learns from documentation mistakes."""
    cm = ContextManager()
    
    # Record a mistake
    cm.record_mistake(
        action="created CONTEXT_IMPROVEMENTS.md",
        should_have="updated TECHNICAL_DESIGN.md",
        pattern="creating new files for improvements"
    )
    
    # System should prevent similar mistake
    operation = FileOperation(
        type='create',
        path='SEARCH_IMPROVEMENTS.md'
    )
    
    guidance = cm.check_file_operation(operation)
    assert guidance.action == 'warning'
    assert 'similar to previous mistake' in guidance.reason

def test_learn_from_success():
    """Test system reinforces successful patterns."""
    cm = ContextManager()
    
    # Record successful documentation update
    cm.record_success(
        action="updated docs/API.md with new endpoint",
        impact="kept docs in sync with code",
        pattern="updating existing docs for API changes"
    )
    
    # System should suggest this pattern
    suggestions = cm.suggest_documentation_action("added new API endpoint")
    assert "update docs/API.md" in suggestions[0].action
```

## Phase 3: Advanced Features (Week 3-4)

### Predictive Guidance

```python
def test_predictive_documentation_needs():
    """Test system anticipates documentation needs."""
    cm = ContextManager()
    
    # After several API additions
    cm.add_context(Context(
        type=ContextType.CODE_CHANGE,
        data={"files": ["api/endpoints.py"], "change": "new endpoint"}
    ))
    
    # System should predict need for API doc update
    predictions = cm.predict_documentation_needs()
    
    assert predictions[0].file == "docs/API.md"
    assert predictions[0].urgency == "high"
    assert "new endpoint" in predictions[0].reason
```

### Multi-Agent Coordination

```python
def test_shared_context_optimization():
    """Test context sharing between agents."""
    cm = ContextManager()
    
    # Two agents working on related tasks
    context1 = cm.collect_context_for_task("implement user authentication")
    context2 = cm.collect_context_for_task("write authentication tests")
    
    # Should identify shared context
    shared = cm.identify_shared_context([context1, context2])
    assert len(shared.files) > 0
    
    # Should optimize to avoid duplication
    optimized = cm.optimize_multi_agent_context([context1, context2])
    assert optimized.total_tokens < (context1.tokens + context2.tokens)
```

## Success Metrics

### Redundancy Prevention
- **Before**: 3 redundant files created for context improvements
- **After**: 0 redundant files (all updates to existing docs)
- **Target**: 95% reduction in redundant documentation

### Context Quality
- **Relevance**: >90% of collected items used by agents
- **Guidance**: >80% of suggestions followed
- **Efficiency**: <5% wasted tokens on irrelevant content

### Performance
- **Task analysis**: <100ms
- **Context collection**: <500ms  
- **File operation check**: <50ms
- **Semantic search**: <200ms

### Learning Effectiveness
- **Mistake prevention**: 90% of repeated mistakes caught
- **Success patterns**: 80% of successful patterns reinforced
- **Prediction accuracy**: 70% of documentation needs predicted

## Implementation Strategy

### Incremental Rollout

1. **Phase 1 (Week 1)**: Core v2 engine with anti-redundancy
   - Deploy alongside v1
   - Start with warnings only
   - Measure effectiveness

2. **Phase 2 (Week 2)**: Intelligence layer
   - Enable semantic search
   - Activate quality monitoring
   - Begin learning from usage

3. **Phase 3 (Week 3-4)**: Advanced features
   - Predictive guidance
   - Multi-agent optimization
   - Full enforcement mode

### Backward Compatibility

```python
# All v1 APIs continue to work
@app.route('/api/context/', methods=['POST'])  # v1
@app.route('/api/v2/context/', methods=['POST'])  # v2

# CLI supports both versions
cm query  # v1 behavior
cm query --semantic  # v2 behavior
```

## Next Steps

### Immediate (This Week)

1. **Clean up redundant files**
   ```bash
   mkdir -p archived/context_plans
   mv CONTEXT_*.md archived/context_plans/
   git add -A
   git commit -m "Consolidate Context Manager design into canonical location"
   ```

2. **Implement semantic task analysis**
   - Start with test cases
   - Build task type classifier
   - Add entity extraction

3. **Create project index**
   - Scan existing structure
   - Build ownership mappings
   - Extract relationships

4. **Add documentation gateway**
   - Hook into file operations
   - Implement guidance system
   - Add CLI commands

### This Month

1. **Deploy v2 with measurements**
   - Track redundancy prevention
   - Measure context quality
   - Monitor performance

2. **Iterate based on usage**
   - Refine task analysis
   - Improve guidance
   - Enhance search

3. **Share learnings**
   - Document what worked
   - Record patterns
   - Plan v3 features

## Conclusion

Context Manager v2 transforms from a passive store to an active project consciousness that:
- **Prevents** redundant documentation by understanding where information belongs
- **Guides** agents with hierarchical, relevant context
- **Learns** from patterns to continuously improve
- **Coordinates** all documentation through a central gateway

This directly solves the problem we experienced: agents creating redundant files because they lack awareness of existing project structure. With these improvements, Context Manager becomes the cognitive system that maintains project coherence and prevents documentation sprawl.
8. Update suggestions based on code changes
9. Simple updates handled by CM

### Ready for Agents When:
1. Stable context flow established
2. Pattern detection improving suggestions
3. No context explosion (staying under limits)
4. Clean API for agent integration
5. Documentation patterns captured
6. Documentation intelligence routing updates
7. Agents requesting doc updates through CM
8. Documentation suggestions improving
9. Cross-references maintained automatically

## Key Implementation Notes

### Start Ultra-Simple
- <200 lines initial implementation
- Basic dict storage
- Focus on working features over optimization

### Documentation First
- Audit trail from day one
- Every decision tracked
- Patterns emerge from usage
- All docs go through Context Manager
- Intelligent documentation updates

### Self-Bootstrapping
- Use it to build itself
- Log all design decisions
- Learn from development patterns

### Compliance Ready
- FDA traceability built-in
- Audit logs for all operations
- Data integrity checks

## Testing Strategy

### TDD Test Structure
```
tests/
├── unit/
│   ├── test_context_schema.py      # Schema validation
│   ├── test_doc_metadata.py        # DocMetadata schema
│   ├── test_storage.py             # Storage operations
│   ├── test_pattern_learning.py    # Doc pattern extraction
│   ├── test_patterns.py            # Pattern detection
│   ├── test_update_routing.py      # Update complexity routing
│   └── test_api.py                 # API endpoints
├── integration/
│   ├── test_flask_integration.py   # Flask app integration
│   ├── test_websocket.py           # Real-time events
│   ├── test_bootstrap.py           # Self-documentation
│   └── test_doc_intelligence.py    # End-to-end doc intelligence
└── performance/
    ├── test_throughput.py          # 10 contexts/sec
    ├── test_search.py              # <2s searches
    └── test_pattern_analysis.py     # Pattern learning performance
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

## Next Steps After V1

1. Use patterns learned to design Documentation Agent
2. Enhance storage with Redis/PostgreSQL  
3. Add context scoring and pruning
4. Implement control loop from Context Engineering
5. Build agent communication protocols
6. Expand documentation intelligence
7. Cross-project documentation learning
8. Automated documentation quality improvement

This plan gives us a working Context Manager in one week that genuinely helps its own development while laying the foundation for a compliant, scalable system.