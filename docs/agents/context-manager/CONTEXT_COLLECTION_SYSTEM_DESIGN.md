# Context Collection System Design

## Executive Summary

This document presents a comprehensive redesign of the Context Manager's context collection system to address fundamental issues with how AI agents understand and interact with the codebase. The new design creates a "project consciousness" that prevents redundancy, provides clear navigation, and scales information appropriately for different tasks.

## Problem Statement

### Core Issues

1. **Project Awareness Problem**
   - Agents create redundant files because they don't know what exists
   - Example: Creating 3 new planning docs when similar ones already existed
   - Root cause: Context system dumps content without showing relationships

2. **Scope Understanding Gap**
   - Agents can't distinguish project files from external dependencies
   - No clear guidance on where different types of changes belong
   - Missing understanding of modification vs creation decisions

3. **Information Hierarchy Failure**
   - All tasks get similar context regardless of scope
   - Swiss Army Knife agent needs everything, bug fix needs specific subsystem
   - Current system lacks task-appropriate scaling

4. **Navigation vs Content Confusion**
   - System provides file contents but not file purposes
   - No understanding of relationships between files
   - Missing guidance on where to make changes

## Design Philosophy

### Project Consciousness Model

Instead of a search engine that returns files, we're building a "project consciousness" that understands:
- What exists and why
- Where things belong
- How components relate
- What patterns are established
- Where changes should go

### Key Principles

1. **Prevention Over Reaction**: Show what exists before allowing creation
2. **Understanding Over Information**: Provide mental models, not just data
3. **Guidance Over Discovery**: Actively guide agents to the right locations
4. **Relationships Over Isolation**: Show how files connect and depend on each other

## System Architecture

### Three-Layer Context Model

```
┌─────────────────────────────────────────────────────────┐
│                   NAVIGATION LAYER                      │
│  • Project structure map with purposes                  │
│  • Existing documentation inventory                     │
│  • Key file roles and responsibilities                  │
│  • Established patterns and conventions                 │
└─────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────┐
│                  RELATIONSHIP LAYER                     │
│  • Import/dependency graphs                             │
│  • Test-to-code mappings                               │
│  • Documentation-to-code links                          │
│  • Similar/related file clusters                        │
└─────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────┐
│                    CONTENT LAYER                        │
│  • Filtered file contents based on task                 │
│  • Relevant code sections highlighted                   │
│  • Historical context from similar tasks                │
│  • Pattern examples from the codebase                   │
└─────────────────────────────────────────────────────────┘
```

### Core Components

#### 1. Project Awareness Engine

```python
class ProjectAwareness:
    """Maintains understanding of project structure and contents."""
    
    def get_project_map(self) -> ProjectMap:
        """
        Returns hierarchical project structure with:
        - Directory purposes and conventions
        - File roles and responsibilities
        - Existing documentation catalog
        - Established patterns
        """
    
    def check_redundancy(self, proposed_file: str, content_type: str) -> RedundancyCheck:
        """
        Before creation, check if similar content exists:
        - Similar filenames or paths
        - Overlapping content based on type
        - Existing documentation on topic
        Returns suggestions for modification vs creation
        """
    
    def suggest_location(self, content_type: str, description: str) -> LocationSuggestion:
        """
        Suggest where new content should go based on:
        - Existing project conventions
        - Similar file locations
        - Directory purposes
        """
```

#### 2. Relationship Tracker

```python
class RelationshipTracker:
    """Tracks and exposes relationships between project components."""
    
    def get_file_relationships(self, file_path: str) -> FileRelationships:
        """
        Returns:
        - Files that import this file
        - Files this file imports
        - Test files for this code
        - Documentation referencing this file
        - Similar files in the project
        """
    
    def get_concept_map(self, concepts: List[str]) -> ConceptMap:
        """
        For given concepts, returns:
        - Primary implementation files
        - Related utility files
        - Test coverage files
        - Documentation files
        - Example usage files
        """
    
    def get_change_impact(self, file_path: str) -> ChangeImpact:
        """
        If this file changes, what else is affected:
        - Direct dependents
        - Test files that need updating
        - Documentation that might be stale
        - Related files that might need similar changes
        """
```

#### 3. Context Scaler

```python
class ContextScaler:
    """Scales context appropriately for task scope."""
    
    def analyze_task_scope(self, task: str) -> TaskScope:
        """
        Determines scope level:
        - NARROW: Single file/function (e.g., "fix typo in login.py")
        - FOCUSED: Single feature/module (e.g., "fix authentication bug")
        - BROAD: Cross-cutting concern (e.g., "add logging to all API endpoints")
        - FULL: Entire project (e.g., "create Swiss Army Knife agent")
        """
    
    def get_scaled_context(self, task_scope: TaskScope, focus_areas: List[str]) -> ScaledContext:
        """
        Returns context scaled to task:
        - NARROW: Specific file + immediate dependencies
        - FOCUSED: Module files + tests + related docs
        - BROAD: Pattern examples + all affected files
        - FULL: Complete project map + key implementations
        """
```

#### 4. Redundancy Preventer

```python
class RedundancyPreventer:
    """Actively prevents creation of redundant content."""
    
    def intercept_creation(self, file_path: str, content_preview: str) -> CreationAdvice:
        """
        Before file creation:
        1. Search for similar existing files
        2. Check documentation coverage
        3. Identify potential duplicates
        4. Suggest alternatives
        
        Returns:
        - PROCEED: No conflicts found
        - MODIFY_EXISTING: Edit these files instead
        - MERGE_WITH: Combine with existing file
        - RECONSIDER: Strong duplicate exists
        """
    
    def suggest_existing_files(self, intent: str) -> List[ExistingFile]:
        """
        Based on creation intent, suggest existing files that might serve the purpose.
        Includes relevance scores and modification suggestions.
        """
```

## Implementation Details

### Context Collection Flow

```python
def collect_context_for_task(self, task: str, agent_type: str) -> ProjectContext:
    """New context collection with project consciousness."""
    
    # 1. Understand the task scope
    task_scope = self.context_scaler.analyze_task_scope(task)
    
    # 2. Build navigation layer - ALWAYS included
    navigation = self.project_awareness.get_project_map()
    
    # 3. Check for file creation intent
    if self._detects_creation_intent(task):
        redundancy_check = self.redundancy_preventer.check_redundancy(
            task, extract_content_type(task)
        )
        if redundancy_check.has_conflicts:
            navigation.highlight_conflicts(redundancy_check.existing_files)
    
    # 4. Build relationship layer based on scope
    relationships = self._build_relationships(task_scope, task)
    
    # 5. Build content layer scaled appropriately
    content = self.context_scaler.get_scaled_context(task_scope, relationships.focus_areas)
    
    # 6. Add guidance layer
    guidance = self._build_guidance(task, navigation, relationships)
    
    return ProjectContext(
        navigation=navigation,
        relationships=relationships,
        content=content,
        guidance=guidance,
        metadata={
            'task_scope': task_scope,
            'token_distribution': self._calculate_token_distribution(),
            'redundancy_warnings': redundancy_check.warnings if creation_detected else []
        }
    )
```

### Navigation Layer Structure

```python
@dataclass
class NavigationLayer:
    """Project structure with semantic understanding."""
    
    project_structure: Dict[str, DirPurpose] = field(default_factory=dict)
    documentation_inventory: Dict[str, DocMetadata] = field(default_factory=dict)
    key_files: Dict[str, FileRole] = field(default_factory=dict)
    conventions: Dict[str, Convention] = field(default_factory=dict)
    
    def to_context_string(self) -> str:
        """Convert to human-readable context."""
        return f"""
# Project Structure & Organization

## Directory Structure
{self._format_structure()}

## Documentation Inventory
Total docs: {len(self.documentation_inventory)}
{self._format_doc_inventory()}

## Key Files & Their Roles
{self._format_key_files()}

## Project Conventions
{self._format_conventions()}
"""

@dataclass
class DirPurpose:
    path: str
    purpose: str
    typical_contents: List[str]
    modification_guidelines: str

@dataclass
class FileRole:
    path: str
    role: str
    modify_for: List[str]  # Types of changes this file handles
    related_files: List[str]
```

### Relationship Layer Structure

```python
@dataclass
class RelationshipLayer:
    """File relationships and dependencies."""
    
    import_graph: Dict[str, List[str]]  # file -> imports
    reverse_imports: Dict[str, List[str]]  # file -> imported_by
    test_mappings: Dict[str, List[str]]  # code -> tests
    doc_mappings: Dict[str, List[str]]  # code -> docs
    similar_files: Dict[str, List[SimilarFile]]
    
    def get_related_cluster(self, file_path: str) -> FileCluster:
        """Get all files related to a given file."""
        return FileCluster(
            primary=file_path,
            imports=self.import_graph.get(file_path, []),
            imported_by=self.reverse_imports.get(file_path, []),
            tests=self.test_mappings.get(file_path, []),
            docs=self.doc_mappings.get(file_path, []),
            similar=self.similar_files.get(file_path, [])
        )
```

### Task Scope Detection

```python
def analyze_task_scope(self, task: str) -> TaskScope:
    """Intelligent task scope detection."""
    
    # Check for explicit scope indicators
    if any(word in task.lower() for word in ['entire', 'all', 'whole', 'project']):
        return TaskScope.FULL
    
    # Check for specific file references
    file_refs = self._extract_file_references(task)
    if file_refs and len(file_refs) == 1:
        return TaskScope.NARROW
    
    # Check for feature/module keywords
    if self._references_module(task):
        return TaskScope.FOCUSED
    
    # Check for cross-cutting concerns
    if any(word in task.lower() for word in ['logging', 'authentication', 'error handling']):
        return TaskScope.BROAD
    
    # Default based on complexity
    complexity = self._estimate_complexity(task)
    return self._scope_from_complexity(complexity)
```

### Redundancy Detection Algorithm

```python
def check_redundancy(self, proposed_path: str, content_type: str) -> RedundancyCheck:
    """Sophisticated redundancy detection."""
    
    results = RedundancyCheck()
    
    # 1. Exact path matching
    if os.path.exists(proposed_path):
        results.add_conflict('exact_match', proposed_path, 1.0)
    
    # 2. Similar name detection
    similar_names = self._find_similar_filenames(proposed_path)
    for name, similarity in similar_names:
        if similarity > 0.8:
            results.add_conflict('similar_name', name, similarity)
    
    # 3. Content type matching
    if content_type == 'documentation':
        existing_docs = self._find_docs_on_topic(proposed_path)
        for doc, relevance in existing_docs:
            if relevance > 0.7:
                results.add_conflict('existing_documentation', doc, relevance)
    
    # 4. Pattern matching
    if content_type in ['plan', 'design', 'spec']:
        pattern_matches = self._find_by_pattern(content_type)
        for match, confidence in pattern_matches:
            results.add_conflict('pattern_match', match, confidence)
    
    # 5. Generate advice
    if results.has_conflicts:
        results.advice = self._generate_advice(results.conflicts)
    
    return results
```

## Context Templates

### Bug Fix Task Template
```
## Task Understanding
Fixing: [specific issue]
Scope: FOCUSED on [module/feature]

## Existing Related Files
[Show test files that might catch this bug]
[Show implementation files in the affected area]
[Show recent changes to these files]

## Where to Make Changes
Based on the issue, you should modify:
- [specific file]: [reason]
- Tests to add: [test file]: [what to test]

## Similar Past Fixes
[Show similar bugs fixed before with diffs]
```

### New Feature Template
```
## Task Understanding
Implementing: [feature description]
Scope: [FOCUSED/BROAD]

## DO NOT CREATE NEW FILES FOR
✗ Documentation - exists in: [list existing docs]
✗ Similar features - see: [list similar implementations]
✗ Utilities - available in: [list utility files]

## Recommended Approach
1. Extend existing [file] for [functionality]
2. Add tests to [test file]
3. Update documentation in [doc file]

## Existing Patterns to Follow
[Show similar feature implementations]
[Show test patterns]
[Show documentation patterns]
```

### Documentation Update Template
```
## Documentation Landscape
Total documentation files: [count]
Related to your task: [count]

## Existing Documentation
[List all related docs with brief descriptions]
[Highlight docs that might need updates]
[Show last modified dates]

## Before Creating New Documentation
⚠️ These files already cover similar topics:
[List with similarity scores]

Consider updating these instead of creating new files.

## Documentation Patterns
[Show structure patterns from existing docs]
[Show naming conventions]
[Show typical sections]
```

## Benefits

### 1. Prevents Redundancy
- Pre-creation checks catch duplicates
- Suggests existing files to modify
- Shows similar content before creation

### 2. Provides Mental Model
- Clear project structure understanding
- File purpose and responsibility mapping
- Established pattern recognition

### 3. Scales Appropriately
- Narrow tasks get focused context
- Broad tasks get patterns and examples
- Full tasks get complete navigation

### 4. Guides Changes
- Shows where changes belong
- Suggests files to modify vs create
- Provides examples from codebase

## Success Metrics

### Quantitative
- **Redundant File Creation**: <5% (from current ~30%)
- **Context Relevance**: >95% of provided files used
- **Task Success Rate**: >90% without additional context requests
- **Token Efficiency**: <10% wasted on irrelevant content

### Qualitative
- Agents understand where to make changes
- No more "I'll create a new file for this" when one exists
- Clear understanding of project structure
- Confident navigation of codebase

## Implementation Plan

### Phase 1: Navigation Layer (Week 1)
- Build project structure mapper
- Create documentation inventory
- Implement file role detection
- Add convention extractor

### Phase 2: Relationship Layer (Week 2)
- Build import graph analyzer
- Create test-to-code mapper
- Implement similarity detection
- Add documentation linker

### Phase 3: Intelligence Layer (Week 3)
- Implement redundancy detector
- Build scope analyzer
- Create context scaler
- Add guidance generator

### Phase 4: Integration (Week 4)
- Wire components together
- Create context templates
- Build agent interfaces
- Add monitoring/metrics

## Conclusion

This design transforms the Context Manager from a passive information retriever into an active project consciousness that understands the codebase structure, prevents redundancy, and guides agents to make changes in the right places. By providing navigation, relationships, and scaled content, we ensure agents have the understanding they need to work effectively within the existing project structure.