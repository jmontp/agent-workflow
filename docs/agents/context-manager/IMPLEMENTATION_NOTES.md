# Context Manager Implementation Notes

## Development Journal

This document captures real-time learnings, decisions, and patterns discovered while building the Context Manager.

## Pre-Implementation Decisions

### Architecture Choice: Separate Module
**Decision**: Create `context_manager.py` as a standalone module  
**Reasoning**: 
- Separation of concerns from Flask app
- Easier testing in isolation
- Can be imported by future agents
- Aligns with "Context Manager as first agent" philosophy

### Storage Choice: JSON over SQLite
**Decision**: Start with JSON file storage  
**Reasoning**:
- Human-readable for debugging
- No schema migrations during rapid iteration
- Easy to inspect context flow
- Simple backup (just copy files)
- Can transition to SQLite/Redis when patterns stabilize

### Testing Strategy: TDD
**Decision**: Write tests first, implement after  
**Reasoning**:
- Context Manager is foundational - must be reliable
- Tests document expected behavior
- Catches integration issues early
- Bootstrap principle: tests are documentation

## Implementation Patterns

### Pattern: Context as Immutable Record
```python
# DON'T: Modify context after creation
context.data['new_field'] = value  # Bad!

# DO: Create new context with relationships
new_context = Context(
    type=ContextType.DERIVED,
    data={'new_field': value},
    relationships=[original_context.id]
)
```
**Why**: Audit trail integrity, easier debugging, prevents race conditions

### Pattern: Explicit Error Context
```python
# DON'T: Raise generic exceptions
raise Exception("Storage failed")

# DO: Include context in errors
raise StorageError(
    f"Failed to store context {context.id}",
    context=context,
    original_error=e
)
```
**Why**: Better debugging, can log error patterns, helps bootstrap learning

### Pattern: Fail Fast with Validation
```python
# DO: Validate early
def add_context(self, context: Context) -> str:
    # Validate immediately
    if not context.validate():
        raise ValidationError(f"Invalid context: {context.validation_errors()}")
    
    # Then proceed with storage
    return self._store(context)
```
**Why**: Clear error messages, prevents corrupt data, easier testing

## Code Smells to Avoid

### 1. Context Explosion
**Smell**: Every tiny operation creates a context
```python
# BAD: Too granular
cm.add_context(Context(data={"action": "opened_file", "file": "test.py"}))
cm.add_context(Context(data={"action": "read_line", "line": 1}))
```

**Fix**: Batch related operations
```python
# GOOD: Meaningful context units
cm.add_context(Context(
    type=ContextType.DEVELOPMENT,
    data={
        "action": "file_analysis",
        "file": "test.py",
        "operations": ["opened", "read", "parsed"],
        "summary": "Extracted 3 functions"
    }
))
```

### 2. Circular Dependencies
**Smell**: Context Manager depends on what it manages
```python
# BAD: Context Manager calls agents directly
class ContextManager:
    def route_context(self, context, agent):
        agent.process(context)  # Direct coupling!
```

**Fix**: Use events or queues
```python
# GOOD: Loose coupling through events
class ContextManager:
    def route_context(self, context, agent_id):
        self.emit('context_available', {
            'agent_id': agent_id,
            'context_id': context.id
        })
```

### 3. Pattern Over-Fitting
**Smell**: Creating too-specific patterns
```python
# BAD: Too specific
pattern = "user_clicked_button_save_on_tuesday_afternoon"
```

**Fix**: Generalize appropriately
```python
# GOOD: Useful abstraction
pattern = "save_action"
time_pattern = "peak_hours"  # Separate time patterns
```

## Performance Considerations

### Memory Management
```python
class ContextManager:
    def __init__(self):
        self.active_contexts = {}  # Hot cache
        self.max_active = 1000     # Prevent memory explosion
        
    def _manage_memory(self):
        if len(self.active_contexts) > self.max_active:
            # Move oldest to disk
            oldest = self._get_oldest_contexts(100)
            self._archive_contexts(oldest)
```

### Batch Operations
```python
# DON'T: Individual operations in loops
for ctx in contexts:
    cm.add_context(ctx)  # N disk writes!

# DO: Batch operations
cm.add_contexts(contexts)  # Single disk write
```

### Index Maintenance
```python
# Maintain indices for common queries
self.indices = {
    'by_type': defaultdict(list),      # O(1) type lookup
    'by_source': defaultdict(list),     # O(1) source lookup  
    'by_date': SortedList(),           # O(log n) date range
}
```

## Integration Gotchas

### Flask Context Issues
```python
# Problem: Flask app context not available in threads
def background_pattern_detection():
    with app.app_context():  # Required!
        patterns = cm.detect_patterns()
```

### Async Considerations
```python
# If using Flask-SocketIO
@socketio.on('context_update')
def handle_context_update(data):
    # SocketIO runs in separate context
    context_id = cm.add_context(...)
    # Emit to all clients
    emit('context_added', {'id': context_id}, broadcast=True)
```

### Testing Isolation
```python
# Ensure tests don't pollute each other
class TestContextManager:
    def setup_method(self):
        self.temp_dir = tempfile.mkdtemp()
        self.cm = ContextManager(storage_path=self.temp_dir)
    
    def teardown_method(self):
        shutil.rmtree(self.temp_dir)
```

## Bootstrap Insights

### Week 1 Learnings

**Day 1-2**: Schema Design Insights
- Dataclasses provide good IDE support
- Optional fields essential for flexibility
- Validation should be method, not property

**Day 3**: Storage Layer Discoveries
- File locking necessary even for single-user
- JSON datetime serialization needs custom encoder
- Backup-on-write pattern prevents data loss

**Day 4**: Pattern Detection Revelations
- Simple frequency counting surprisingly effective
- Time windows matter (24h too long, 1h too short)
- Negative patterns (what NOT to do) equally valuable

**Day 5**: Integration Surprises
- Flask blueprint integration cleaner than expected
- WebSocket events perfect for real-time patterns
- CLI integration helps manual testing

### Patterns That Emerged

1. **Test-First Saves Time**
   - Found schema issues before implementation
   - API design flaws caught early
   - Integration points clearer

2. **Simple Algorithms Win**
   - Keyword frequency > complex NLP
   - Time-based patterns > statistical correlation
   - File storage > database (for now)

3. **Bootstrap Momentum**
   - Day 3: First useful suggestion
   - Day 4: Suggestions driving development
   - Day 5: Patterns preventing mistakes

## Future Considerations

### When to Upgrade Storage
Monitor these metrics:
- Query time > 200ms consistently
- Storage size > 1GB
- Concurrent user issues
- Need for complex queries

### When to Add ML
Wait for these conditions:
- 10,000+ contexts collected
- Patterns stabilizing
- Simple patterns insufficient
- Clear performance benefit

### When to Distribute
Consider distribution when:
- Multiple projects need isolation
- Geographic distribution required
- Single instance bottleneck
- High availability needed

## Debugging Tips

### Enable Debug Logging
```python
# Set in environment
export CONTEXT_MANAGER_DEBUG=true

# Or in code
cm = ContextManager(debug=True)
```

### Useful Debug Commands
```python
# Inspect recent contexts
cm.debug_recent_contexts(10)

# Check pattern detection
cm.debug_patterns()

# Verify storage integrity
cm.debug_storage_check()

# Memory usage
cm.debug_memory_stats()
```

### Common Issues

1. **"Context not found"**
   - Check if context was archived
   - Verify ID format
   - Check permissions

2. **"Pattern detection slow"**
   - Reduce time window
   - Check context volume
   - Profile detection algorithm

3. **"Storage errors"**
   - Check disk space
   - Verify file permissions
   - Check for file locks

## Code Cleanup Insights (From v1 Analysis)

### Current State Analysis
The Context Manager grew to 2,704 lines in a single file. Analysis revealed:

**Dead Code**: 
- Unused imports (timedelta, sys, Set)
- Single-use methods that should be inlined
- 17 print statements that should use logging

**Duplication**:
- Similar save methods repeated 3 times
- Same error handling pattern 20+ times
- Code analysis methods with 80% similar logic

**Complexity**:
- Monster methods >100 lines each:
  - `_optimize_for_tokens` (142 lines)
  - `_collect_relevant_items` (134 lines)
  - `collect_context_for_task` (133 lines)
  - `needs_update` (131 lines)
  - `get_project_status` (126 lines)

### Refactoring Lessons

1. **Modularization Strategy**
   ```
   context_manager/
   ├── __init__.py          # Main class
   ├── schemas.py           # Dataclasses
   ├── storage.py           # File I/O
   ├── analyzers.py         # Code/doc analysis  
   ├── patterns.py          # Pattern detection
   ├── project_index.py     # Project understanding
   ├── task_context.py      # Context collection
   └── utils.py            # Shared utilities
   ```

2. **Common Patterns to Extract**
   - Error handling decorator
   - Generic JSON save/load
   - File analysis strategy pattern
   - Token optimization algorithm

3. **Performance Optimizations Needed**
   - Cache computed relevance scores
   - Limit import analysis depth
   - Batch file operations
   - Use indices for common queries

## Context Collection Improvements (v2 Design)

### Problems with v1 Approach

1. **Simplistic Keyword Matching**
   - No stemming/lemmatization
   - Ignores compound terms
   - Misses technical acronyms

2. **Static Relevance Scoring**
   - Fixed scores don't adapt
   - No relationship awareness
   - Linear scoring without context

3. **Missing Semantic Understanding**
   - No concept expansion
   - No import relationships
   - No directory proximity

### v2 Enhancements

**Enhanced Keyword Extraction**:
```python
def _extract_keywords(self, text: str) -> List[str]:
    # Extract compounds (snake_case, CamelCase, ACRONYMS)
    # Apply simple stemming
    # Keep short technical terms
    # Return both original and stemmed versions
```

**Dynamic Relevance Scoring**:
```python
def calculate_relevance(self, item, task_analysis, context_so_far):
    # Semantic similarity (not just keywords)
    # Relationship relevance (imports, proximity)
    # Recency and modification patterns
    # Task-specific boosts
```

**Learning from History**:
```python
def learn_from_usage(self, task, context_used, success):
    # Track which context was actually useful
    # Adjust scoring weights
    # Learn common patterns
    # Prevent repeated mistakes
```

## Conclusion

The Context Manager implementation validates the bootstrap approach. By using it to track its own development, we've discovered patterns that would have been lost otherwise. The simple solutions (JSON, keyword patterns, basic routing) have proven more valuable than complex alternatives.

The v2 design addresses the core issue we experienced: agents creating redundant documentation because they lack semantic understanding of the project structure. By evolving from a passive store to an active project consciousness, Context Manager v2 will guide agents to maintain coherence and prevent documentation sprawl.

Key takeaway: **Start simple, track everything, let patterns guide complexity, then evolve based on real usage.**