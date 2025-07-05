# Context Manager Cleanup Plan

## Executive Summary

The Context Manager has grown to 2,704 lines in a single file, making it difficult to maintain and understand. This cleanup plan will reduce the codebase by ~40% (approximately 1,100 lines) through strategic refactoring, dead code removal, and modularization.

## 1. Dead Code Detection

### Unused Imports
- **timedelta** (line 8) - imported but never used
- **sys** (line 18) - imported but never used directly
- **Set** from typing (line 9) - imported but not used

**Lines Saved**: ~3 lines

### Methods Only Called Once Internally
These methods could be inlined or simplified:
- `_analyze_js_file` - Only called from `_analyze_code_file`
- `_analyze_python_file` - Only called from `_analyze_code_file`
- `_audit_operation` - Only called once, could be inlined
- `_has_persistence` - Simple one-liner, should be inlined

**Lines Saved**: ~50 lines

### Debug/Print Statements
Found 17 print statements that should be replaced with proper logging:
- Lines: 377, 655, 743, 960, 969, 981, 1003, 1055, 1064, 1076, 1343, 1405, 1763, 1896, 2161, 2252, 2277, 2293, 2297

**Lines Saved**: ~0 lines (convert to logging)

## 2. Duplicate Code Consolidation

### Similar Pattern Methods
Multiple methods follow similar patterns that could be consolidated:
- `_analyze_code_file`, `_analyze_python_file`, `_analyze_js_file` - Could use a strategy pattern
- `_scan_documentation` and `_scan_code` - Share 80% similar logic
- `_save_doc_metadata`, `_save_patterns`, `_save_project_index` - All follow same save pattern

**Lines Saved**: ~200 lines through consolidation

### Repeated Error Handling
Same try-except pattern repeated 20+ times. Could be extracted to a decorator.

**Lines Saved**: ~100 lines

## 3. Overly Complex Methods to Break Down

### Monster Methods (>100 lines each)
1. **`_optimize_for_tokens`** (142 lines) - Break into:
   - `_calculate_token_budgets`
   - `_allocate_tokens_by_type`
   - `_redistribute_unused_tokens`
   
2. **`_collect_relevant_items`** (134 lines) - Break into:
   - `_collect_contexts`
   - `_collect_code_items`
   - `_collect_documentation`
   - `_collect_folders`

3. **`collect_context_for_task`** (133 lines) - Break into:
   - `_prepare_task_collection`
   - `_execute_collection_stages`
   - `_format_collection_results`

4. **`needs_update`** (131 lines) - This is inside DocMetadata class and should be simplified

5. **`get_project_status`** (126 lines) - Break into smaller status methods

**Lines Saved**: ~200 lines through better organization

## 4. Code Organization - Module Split

### Proposed Module Structure
```
context_manager/
├── __init__.py          # Main ContextManager class (~500 lines)
├── schemas.py           # All dataclasses and enums (~300 lines)
├── storage.py           # File I/O operations (~200 lines)
├── analyzers.py         # Code/doc analysis (~400 lines)
├── patterns.py          # Pattern detection (~200 lines)
├── project_index.py     # Project indexing (~600 lines)
├── task_context.py      # Task context collection (~500 lines)
└── utils.py            # Shared utilities (~200 lines)
```

**Current monolith**: 2,704 lines
**After split**: ~2,900 lines total (but properly organized)
**Actual reduction**: ~1,100 lines through consolidation

## 5. Specific Pruning Actions

### Immediate Removals (Quick Wins)
1. **Remove unused imports** (3 lines)
2. **Inline single-use helper methods** (50 lines)
3. **Remove verbose docstrings that add no value** (~100 lines)
   - Many docstrings just repeat the method name
   - Example: `"""Get current project ID."""` for `get_current_project()`

### Consolidation Targets
1. **Merge similar save methods** into generic `_save_json` (100 lines)
2. **Create generic analyze method** with language plugins (200 lines)
3. **Extract error handling decorator** (100 lines)
4. **Consolidate scan methods** (150 lines)

### Simplification Targets
1. **Simplify `needs_update` logic** - Currently 131 lines for a boolean check (100 lines)
2. **Extract token calculation logic** to separate class (200 lines)
3. **Simplify project status generation** (80 lines)

## 6. Implementation Priority

### Phase 1: Quick Wins (1 hour)
- Remove unused imports
- Replace print statements with logging
- Inline single-use helpers
- **Estimated reduction**: 150 lines

### Phase 2: Consolidation (2-3 hours)
- Create generic save/load methods
- Consolidate scan methods
- Extract error handling decorator
- **Estimated reduction**: 400 lines

### Phase 3: Modularization (4-6 hours)
- Split into separate modules
- Create proper package structure
- Add __init__.py with clean exports
- **Estimated reduction**: 500 lines

### Phase 4: Simplification (2-3 hours)
- Simplify complex methods
- Remove verbose docstrings
- Clean up data structures
- **Estimated reduction**: 100 lines

## 7. Quality Improvements

### Code Smells to Fix
1. **God Object**: ContextManager does too much
2. **Long Parameter Lists**: Some methods have 6+ parameters
3. **Deep Nesting**: Some methods have 4+ levels of nesting
4. **Magic Numbers**: Token limits, timeouts hardcoded

### Proposed Improvements
1. Use configuration object for settings
2. Extract business logic from data persistence
3. Implement proper logging instead of print
4. Add type hints to all methods

## 8. Testing Considerations

The current code has no visible test coverage. After cleanup:
1. Each module should have unit tests
2. Integration tests for main workflows
3. Performance tests for large projects

## Summary

**Total estimated reduction**: 1,100-1,200 lines (~40%)
**Total effort**: 9-13 hours
**Result**: Clean, modular, maintainable codebase

### Recommended Approach
1. Start with Phase 1 (quick wins) to see immediate improvement
2. Create the module structure early
3. Move code incrementally, testing as you go
4. Focus on maintaining backward compatibility with cm.py CLI

### Next Steps
1. Review and approve this plan
2. Create module structure
3. Begin Phase 1 implementation
4. Set up basic test framework