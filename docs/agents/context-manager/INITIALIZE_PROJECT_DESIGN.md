# Initialize Project Design

## Overview

The `initialize_project` function creates a comprehensive metadata layer by scanning all project documentation and code, building an understanding of where information lives. This enables the Context Manager to act as an intelligent router for agent requests.

## Purpose

When agents ask questions like:
- "Where is the error handling implemented?"
- "What's the architecture for the state machine?"
- "Where are the API docs?"

The Context Manager can immediately point to the right files and sections without scanning everything each time.

## Design

### Core Functionality

```python
def initialize_project(self, project_root: str = ".") -> Dict[str, Any]:
    """
    Initialize project by scanning all documentation and code.
    Builds comprehensive metadata layer for intelligent routing.
    
    Returns:
        Summary of initialization including:
        - Files scanned
        - Patterns learned
        - Knowledge graph built
        - Suggested next steps
    """
```

### Scanning Process

1. **Documentation Scan**
   - Find all .md files
   - Extract structure (headers, sections)
   - Learn terminology and patterns
   - Map concepts to locations

2. **Code Scan**
   - Identify all source files
   - Extract classes, functions, modules
   - Map functionality to files
   - Detect architectural patterns

3. **Dependency Analysis**
   - Track which docs reference which code
   - Build relationships between components
   - Create navigation shortcuts

4. **Knowledge Graph Construction**
   - Build semantic index of concepts
   - Create file-to-topic mappings
   - Generate quick lookup tables

### Data Structures

#### ProjectIndex
```python
@dataclass
class ProjectIndex:
    """Complete project understanding."""
    
    # File mappings
    doc_files: Dict[str, DocMetadata]
    code_files: Dict[str, CodeMetadata]
    
    # Concept mappings
    concepts: Dict[str, List[str]]  # concept -> file paths
    functions: Dict[str, str]       # function -> file path
    classes: Dict[str, str]         # class -> file path
    
    # Relationships
    dependencies: Dict[str, List[str]]  # file -> dependent files
    references: Dict[str, List[str]]    # doc -> code references
    
    # Learned patterns
    naming_conventions: Dict[str, str]
    architectural_patterns: List[str]
    
    # Quick lookups
    faq_mappings: Dict[str, str]  # common questions -> answers
    index_timestamp: datetime
```

#### CodeMetadata
```python
@dataclass
class CodeMetadata:
    """Metadata for source code files."""
    
    path: str
    language: str
    last_modified: datetime
    
    # Extracted elements
    classes: List[str]
    functions: List[str]
    imports: List[str]
    exports: List[str]
    
    # Documentation
    docstrings: Dict[str, str]  # element -> docstring
    comments: List[str]
    
    # Complexity metrics
    lines_of_code: int
    complexity_score: float
```

### Intelligence Features

1. **Smart Routing**
   ```python
   def find_information(query: str) -> List[LocationResult]:
       """Find where specific information lives."""
       # Uses NLP to understand query
       # Returns ranked list of locations
   ```

2. **Concept Mapping**
   ```python
   def get_concept_locations(concept: str) -> Dict[str, List[str]]:
       """Find all locations discussing a concept."""
       # Returns docs and code mentioning concept
   ```

3. **Architecture Understanding**
   ```python
   def get_architecture_summary() -> ArchitectureSummary:
       """Generate high-level architecture understanding."""
       # Returns key components and relationships
   ```

### Storage

Project indices stored in:
```
context_store/{project_id}/
    indices/
        project_index.json      # Main index
        concept_map.json        # Concept mappings
        quick_lookups.json      # FAQ mappings
        code_index/            # Per-file code metadata
        doc_index/             # Per-file doc metadata
```

### Usage Examples

```python
# Initialize project
cm = ContextManager()
result = cm.initialize_project(".")

print(f"Scanned {result['files_scanned']} files")
print(f"Found {result['concepts_mapped']} concepts")
print(f"Built {result['relationships']} relationships")

# Later, when agent asks a question
locations = cm.find_information("Where is error handling implemented?")
for loc in locations:
    print(f"{loc.file}:{loc.line} - {loc.confidence}%")

# Get all info about a concept
auth_info = cm.get_concept_locations("authentication")
print(f"Authentication mentioned in:")
for doc in auth_info['docs']:
    print(f"  Doc: {doc}")
for code in auth_info['code']:
    print(f"  Code: {code}")
```

### CLI Integration

```bash
# Initialize current project
cm init

# Initialize specific project
cm init --project my-project

# Re-scan project
cm init --rescan

# Show initialization status
cm status
```

### Web UI Integration

Add "Initialize Project" button to Context Manager UI that:
1. Shows progress bar during scanning
2. Displays summary of findings
3. Highlights any issues found
4. Suggests documentation improvements

### Benefits

1. **Fast Information Retrieval**: No need to scan files repeatedly
2. **Cross-Reference Navigation**: Jump between related docs and code
3. **Pattern Recognition**: Understand project conventions
4. **Agent Efficiency**: Agents get instant answers about project structure
5. **Documentation Health**: Identify gaps and inconsistencies

### Implementation Priority

1. Basic file scanning and indexing
2. Documentation structure extraction
3. Code element extraction
4. Concept mapping
5. Smart routing
6. Advanced NLP features

This creates a "nervous system" that understands the entire project structure and can guide agents to the right information instantly.