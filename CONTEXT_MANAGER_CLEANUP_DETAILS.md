# Context Manager Cleanup - Detailed Line Analysis

## Immediate Action Items with Line Numbers

### 1. Unused Imports to Remove
```python
Line 8: from datetime import datetime, timedelta  # Remove timedelta
Line 9: from typing import Dict, List, Optional, Any, Set, Tuple  # Remove Set
Line 18: import sys  # Remove entirely
```

### 2. Print Statements to Convert to Logging

```python
Line 377: print(f"Error loading context {context_file}: {e}")
Line 655: print(f"Error analyzing {doc_path}: {e}")
Line 743: print(f"Error calculating quality for {doc_path}: {e}")
Line 960: print(f"Error scanning {md_file}: {e}")
Line 969: print(f"Generating descriptions for folder {idx+1}/{total_folders}: {Path(folder_path).name}")
Line 981: print(f"Batch generation failed for {folder_path}, falling back to individual: {e}")
Line 1003: print("Skipping Claude descriptions for faster indexing...")
Line 1055: print(f"Error scanning {code_file}: {e}")
Line 1064: print(f"Generating code descriptions for folder {idx+1}/{total_folders}: {Path(folder_path).name}")
Line 1076: print(f"Batch generation failed for {folder_path}, falling back to individual: {e}")
Line 1343: print("Skipping folder descriptions...")
Line 1405: print(f"Generating simple folder descriptions: {e}")
Line 2252: print(f"Error reading doc file {item.path}: {e}")
Line 2277: print(f"Error reading code file {item.path}: {e}")
Line 2293: print(f"Unknown item type: {type(item)}")
Line 2297: print(f"Error converting item to ContextItem: {e}")
```

### 3. Methods to Inline (Only Called Once)

```python
Lines 558-565: _audit_operation() - Only called once, inline it
Lines 567-569: _has_persistence() - One-liner, inline it
```

### 4. Duplicate Save Methods to Consolidate

These three methods follow identical patterns:
```python
Lines 822-840: _save_doc_metadata()
Lines 842-864: _save_patterns()
Lines 1409-1481: _save_project_index()
```

Can be replaced with:
```python
def _save_json(self, data: Any, filename: str, subdir: str = ""):
    """Generic JSON save method."""
    save_path = self.metadata_dir / subdir / filename
    save_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Convert to dict if has to_dict method
    if hasattr(data, 'to_dict'):
        data = data.to_dict()
    
    with open(save_path, 'w') as f:
        json.dump(data, f, indent=2, default=str)
```

### 5. Overly Verbose Docstrings to Simplify

Many docstrings add no value beyond the method name:

```python
Line 28: def load_config():
    """Load CLI configuration."""  # Redundant

Line 36: def save_config(config):
    """Save CLI configuration."""  # Redundant

Line 42: def get_current_project():
    """Get current project ID."""  # Redundant
```

### 6. Complex Methods to Break Down

#### Method: _optimize_for_tokens (Lines 2300-2442)
Break into:
- `_calculate_initial_budgets()`
- `_add_items_by_priority()`
- `_redistribute_remaining_tokens()`
- `_finalize_token_optimization()`

#### Method: collect_context_for_task (Lines 1859-1991)
Break into:
- `_validate_collection_parameters()`
- `_analyze_and_collect_task_context()`
- `_format_task_context_response()`

### 7. Redundant Error Handling Pattern

This pattern appears 20+ times:
```python
try:
    # some operation
except Exception as e:
    print(f"Error doing something: {e}")
    return None  # or empty list/dict
```

Replace with decorator:
```python
def safe_operation(default_return=None, log_errors=True):
    def decorator(func):
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                if log_errors:
                    logger.error(f"Error in {func.__name__}: {e}")
                return default_return
        return wrapper
    return decorator
```

### 8. Magic Numbers to Extract

```python
Line 1860: max_tokens: int = 4000  # Default token limit
Line 2305: TOKEN_CHAR_RATIO = 0.25  # Token estimation ratio
Line 2380: 'contexts': 0.3,  # Token allocation percentages
Line 2381: 'code': 0.4,
Line 2382: 'docs': 0.2,
Line 2383: 'folders': 0.1
```

Create configuration class:
```python
@dataclass
class ContextManagerConfig:
    max_tokens: int = 4000
    token_char_ratio: float = 0.25
    token_allocation: Dict[str, float] = field(default_factory=lambda: {
        'contexts': 0.3,
        'code': 0.4,
        'docs': 0.2,
        'folders': 0.1
    })
```

### 9. Deeply Nested Code to Flatten

Example from _scan_documentation (Lines 924-1008):
```python
# Current: 4 levels of nesting
for root, dirs, files in os.walk(root_path):
    for file in files:
        if file.endswith('.md'):
            try:
                # process
                if condition:
                    if another_condition:
                        # more processing
```

Flatten using early returns and helper methods.

### 10. Schema Classes to Move

Move all these to schemas.py:
- Lines 23-33: ContextType enum
- Lines 36-80: Context dataclass
- Lines 82-131: DocMetadata dataclass
- Lines 133-187: DocPattern dataclass
- Lines 189-218: ProjectIndex dataclass
- Lines 220-235: CodeMetadata dataclass
- Lines 1742-1745: TaskAnalysis dataclass
- Lines 1855-1857: ContextItem dataclass
- Lines 1850-1853: TaskContext dataclass

## Quick Start Commands

```bash
# Step 1: Create module structure
mkdir context_manager
touch context_manager/__init__.py
touch context_manager/{schemas,storage,analyzers,patterns,project_index,task_context,utils}.py

# Step 2: Move schemas (automated)
# Extract lines 23-235 and 1742-1857 to schemas.py

# Step 3: Run simple replacements
# Replace print statements with logger.error()
# Remove unused imports
# Inline single-use methods

# Step 4: Test that cm.py still works
python cm.py stats
```

## Estimated Line Savings by Section

1. **Schemas extraction**: 250 lines moved (not saved, but organized)
2. **Duplicate save methods**: 80 lines saved
3. **Inline single-use methods**: 50 lines saved
4. **Simplify verbose docstrings**: 100 lines saved
5. **Extract error handling**: 100 lines saved
6. **Break down complex methods**: 200 lines saved (better organization)
7. **Remove debug prints**: 0 lines (convert to logging)
8. **Consolidate scan methods**: 150 lines saved

**Total lines saved**: ~730 lines
**Total lines better organized**: ~520 lines
**Net reduction**: ~1,250 lines worth of improvement