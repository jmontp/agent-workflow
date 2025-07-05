# Context Collection System - Implementation Guide

## Overview

This guide provides concrete implementation steps to transform the current context collection system into a project-conscious system that prevents redundancy and guides agents effectively.

## Core Classes to Implement

### 1. ProjectAwareness Class

```python
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
from pathlib import Path
import ast
import re

@dataclass
class DirPurpose:
    """Represents a directory's purpose in the project."""
    path: str
    purpose: str
    typical_contents: List[str]
    modification_guidelines: str
    patterns: List[str] = field(default_factory=list)

@dataclass
class FileRole:
    """Represents a file's role and responsibilities."""
    path: str
    role: str
    modify_for: List[str]  # Types of changes this file handles
    do_not_modify_for: List[str]  # Changes that should go elsewhere
    related_files: List[str]

class ProjectAwareness:
    """Maintains semantic understanding of project structure."""
    
    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
        self.dir_purposes: Dict[str, DirPurpose] = {}
        self.file_roles: Dict[str, FileRole] = {}
        self.doc_inventory: Dict[str, DocMetadata] = {}
        self.conventions: Dict[str, str] = {}
        self._scan_project()
    
    def _scan_project(self):
        """Scan project and build semantic understanding."""
        # Key directories and their purposes
        self.dir_purposes = {
            "docs/agents/context-manager": DirPurpose(
                path="docs/agents/context-manager",
                purpose="Context Manager design and implementation docs",
                typical_contents=["specifications", "designs", "implementation guides"],
                modification_guidelines="Add new designs here, update existing specs in place",
                patterns=["*_DESIGN.md", "*_SPECIFICATION.md", "*_PLAN.md"]
            ),
            "docs/project-evolution-guide": DirPurpose(
                path="docs/project-evolution-guide",
                purpose="High-level project vision and roadmap",
                typical_contents=["vision docs", "roadmaps", "evolution guides"],
                modification_guidelines="Only update for major vision changes",
                patterns=["*.md"]
            ),
            # Add more directories...
        }
        
        # Key files and their roles
        self.file_roles = {
            "CONTEXT_MANAGER_V1.1_PLAN.md": FileRole(
                path="CONTEXT_MANAGER_V1.1_PLAN.md",
                role="Active improvement tracking for Context Manager v1.1",
                modify_for=["new improvements", "context collection enhancements", "bug fixes"],
                do_not_modify_for=["architectural changes", "new agent specs"],
                related_files=["context_manager.py", "docs/agents/context-manager/TECHNICAL_DESIGN.md"]
            ),
            # Add more files...
        }
        
        # Scan for documentation
        self._scan_documentation()
        
        # Extract conventions
        self._extract_conventions()
    
    def check_redundancy(self, proposed_file: str, content_type: str, 
                        topic: str) -> 'RedundancyCheck':
        """Check if similar content already exists."""
        check = RedundancyCheck()
        
        # Check exact path
        full_path = self.project_root / proposed_file
        if full_path.exists():
            check.add_conflict(
                conflict_type='exact_match',
                file_path=str(full_path),
                relevance=1.0,
                advice=f"File already exists. Modify {proposed_file} instead."
            )
        
        # Check similar names
        proposed_name = Path(proposed_file).stem.lower()
        for doc_path, metadata in self.doc_inventory.items():
            doc_name = Path(doc_path).stem.lower()
            similarity = self._calculate_name_similarity(proposed_name, doc_name)
            
            if similarity > 0.7:
                check.add_conflict(
                    conflict_type='similar_name',
                    file_path=doc_path,
                    relevance=similarity,
                    advice=f"Similar file exists: {doc_path}. Consider updating it."
                )
        
        # Check content overlap
        if content_type == 'plan':
            # Special handling for plans
            for plan_file in self._find_plan_files():
                if topic.lower() in plan_file.lower():
                    check.add_conflict(
                        conflict_type='topic_overlap',
                        file_path=plan_file,
                        relevance=0.8,
                        advice=f"Existing plan covers this topic: {plan_file}"
                    )
        
        return check
    
    def suggest_location(self, content_type: str, description: str) -> 'LocationSuggestion':
        """Suggest where new content should go."""
        suggestion = LocationSuggestion()
        
        # Match against directory purposes
        for dir_path, purpose in self.dir_purposes.items():
            if content_type in purpose.typical_contents:
                suggestion.add_option(
                    path=dir_path,
                    reason=purpose.purpose,
                    confidence=0.9
                )
        
        # Check for similar existing files
        similar_files = self._find_similar_files(description)
        for file_path, similarity in similar_files[:3]:
            dir_path = str(Path(file_path).parent)
            suggestion.add_option(
                path=dir_path,
                reason=f"Similar file '{Path(file_path).name}' exists here",
                confidence=similarity
            )
        
        return suggestion
```

### 2. RedundancyPreventer Class

```python
@dataclass
class RedundancyCheck:
    """Results of redundancy checking."""
    conflicts: List[Dict] = field(default_factory=list)
    
    def add_conflict(self, conflict_type: str, file_path: str, 
                     relevance: float, advice: str):
        self.conflicts.append({
            'type': conflict_type,
            'file': file_path,
            'relevance': relevance,
            'advice': advice
        })
    
    @property
    def has_conflicts(self) -> bool:
        return len(self.conflicts) > 0
    
    def get_primary_conflict(self) -> Optional[Dict]:
        """Get the most relevant conflict."""
        if not self.conflicts:
            return None
        return max(self.conflicts, key=lambda x: x['relevance'])

class RedundancyPreventer:
    """Actively prevents creation of redundant content."""
    
    def __init__(self, project_awareness: ProjectAwareness):
        self.awareness = project_awareness
        self.creation_patterns = self._load_creation_patterns()
    
    def intercept_creation(self, task: str) -> Optional[CreationIntercept]:
        """Intercept potential file creation before it happens."""
        # Detect creation intent
        creation_signals = [
            r'create\s+(?:a\s+)?(?:new\s+)?(\w+)',
            r'write\s+(?:a\s+)?(?:new\s+)?(\w+)',
            r'add\s+(?:a\s+)?(?:new\s+)?(\w+)',
            r'implement\s+(?:a\s+)?(?:new\s+)?(\w+)'
        ]
        
        for pattern in creation_signals:
            match = re.search(pattern, task.lower())
            if match:
                content_type = match.group(1)
                return self._build_intercept(task, content_type)
        
        return None
    
    def _build_intercept(self, task: str, content_type: str) -> CreationIntercept:
        """Build intercept response with alternatives."""
        intercept = CreationIntercept()
        
        # Extract topic from task
        topic = self._extract_topic(task)
        
        # Check for redundancy
        redundancy = self.awareness.check_redundancy(
            proposed_file="",  # Don't know filename yet
            content_type=content_type,
            topic=topic
        )
        
        if redundancy.has_conflicts:
            intercept.should_prevent = True
            intercept.reason = "Similar content already exists"
            
            # Add alternatives
            for conflict in redundancy.conflicts:
                intercept.add_alternative(
                    action=f"Update {conflict['file']}",
                    reason=conflict['advice'],
                    confidence=conflict['relevance']
                )
        
        # Add location suggestions even if not preventing
        location = self.awareness.suggest_location(content_type, task)
        intercept.suggested_locations = location.options
        
        return intercept
```

### 3. Context Scaler Class

```python
from enum import Enum

class TaskScope(Enum):
    NARROW = "narrow"      # Single file/function
    FOCUSED = "focused"    # Single module/feature  
    BROAD = "broad"        # Cross-cutting concern
    FULL = "full"          # Entire project

class ContextScaler:
    """Scales context appropriately for task scope."""
    
    def __init__(self, project_index: ProjectIndex):
        self.project_index = project_index
        self.scope_indicators = self._load_scope_indicators()
    
    def analyze_task_scope(self, task: str) -> TaskScope:
        """Determine appropriate scope for task."""
        task_lower = task.lower()
        
        # Check explicit indicators
        if any(word in task_lower for word in ['entire', 'all', 'whole', 'project', 'codebase']):
            return TaskScope.FULL
        
        if any(word in task_lower for word in ['specific', 'single', 'one', 'particular']):
            return TaskScope.NARROW
        
        # Check for file references
        file_refs = self._extract_file_references(task)
        if file_refs:
            if len(file_refs) == 1:
                return TaskScope.NARROW
            elif len(file_refs) <= 3:
                return TaskScope.FOCUSED
        
        # Check for cross-cutting keywords
        cross_cutting = ['logging', 'error handling', 'authentication', 'caching', 'monitoring']
        if any(keyword in task_lower for keyword in cross_cutting):
            return TaskScope.BROAD
        
        # Default to focused
        return TaskScope.FOCUSED
    
    def get_scaled_context(self, scope: TaskScope, task_analysis: TaskAnalysis,
                          max_tokens: int) -> ScaledContext:
        """Get context scaled to task scope."""
        context = ScaledContext(scope=scope)
        
        if scope == TaskScope.NARROW:
            # Very focused context
            context.set_token_budget({
                'navigation': 0.1,    # 10% - Just immediate area
                'relationships': 0.2, # 20% - Direct dependencies
                'content': 0.6,       # 60% - Full file content
                'guidance': 0.1      # 10% - Specific guidance
            })
            
        elif scope == TaskScope.FOCUSED:
            # Module-level context
            context.set_token_budget({
                'navigation': 0.2,    # 20% - Module structure
                'relationships': 0.3, # 30% - Module dependencies
                'content': 0.4,       # 40% - Key files
                'guidance': 0.1      # 10% - Patterns
            })
            
        elif scope == TaskScope.BROAD:
            # Cross-cutting context
            context.set_token_budget({
                'navigation': 0.3,    # 30% - Project structure
                'relationships': 0.2, # 20% - Pattern locations
                'content': 0.3,       # 30% - Examples
                'guidance': 0.2      # 20% - Best practices
            })
            
        else:  # FULL
            # Complete project context
            context.set_token_budget({
                'navigation': 0.4,    # 40% - Full structure
                'relationships': 0.2, # 20% - Key relationships
                'content': 0.2,       # 20% - Critical files
                'guidance': 0.2      # 20% - Conventions
            })
        
        return context
```

### 4. Enhanced Context Collection

```python
class EnhancedContextCollector:
    """New context collector with project consciousness."""
    
    def __init__(self, context_manager: ContextManager):
        self.cm = context_manager
        self.project_awareness = ProjectAwareness(context_manager.project_root)
        self.redundancy_preventer = RedundancyPreventer(self.project_awareness)
        self.context_scaler = ContextScaler(context_manager.project_index)
        self.relationship_tracker = RelationshipTracker(context_manager.project_index)
    
    def collect_context_for_task(self, task: str, agent_type: str = None,
                                max_tokens: int = 50000) -> ProjectContext:
        """Collect context with project consciousness."""
        
        # 1. Intercept potential file creation
        creation_intercept = self.redundancy_preventer.intercept_creation(task)
        if creation_intercept and creation_intercept.should_prevent:
            return self._build_anti_redundancy_context(creation_intercept, task)
        
        # 2. Analyze task scope
        scope = self.context_scaler.analyze_task_scope(task)
        
        # 3. Regular task analysis (existing method)
        task_analysis = self.cm._analyze_task(task)
        
        # 4. Build three-layer context
        navigation = self._build_navigation_layer(scope, task_analysis)
        relationships = self._build_relationship_layer(scope, task_analysis, navigation)
        content = self._build_content_layer(scope, task_analysis, relationships, max_tokens)
        
        # 5. Add guidance
        guidance = self._build_guidance_layer(task, scope, navigation, relationships)
        
        # 6. Package as ProjectContext
        return ProjectContext(
            task=task,
            scope=scope,
            navigation=navigation,
            relationships=relationships,
            content=content,
            guidance=guidance,
            warnings=creation_intercept.warnings if creation_intercept else [],
            metadata={
                'collection_time': time.time(),
                'token_distribution': content.get_token_distribution(),
                'agent_type': agent_type
            }
        )
    
    def _build_navigation_layer(self, scope: TaskScope, 
                               task_analysis: TaskAnalysis) -> NavigationLayer:
        """Build project structure understanding."""
        nav = NavigationLayer()
        
        # Always include key structure
        nav.project_structure = self.project_awareness.get_structure_map()
        
        # Add documentation inventory if relevant
        if scope in [TaskScope.BROAD, TaskScope.FULL] or 'document' in task_analysis.keywords:
            nav.documentation_inventory = self.project_awareness.doc_inventory
        
        # Add file roles
        nav.key_files = self.project_awareness.get_key_files_for_task(task_analysis)
        
        # Add conventions
        nav.conventions = self.project_awareness.conventions
        
        return nav
    
    def _build_anti_redundancy_context(self, intercept: CreationIntercept, 
                                      task: str) -> ProjectContext:
        """Special context to prevent redundant creation."""
        context = ProjectContext(
            task=task,
            scope=TaskScope.FOCUSED,
            warnings=[
                "⚠️ REDUNDANCY DETECTED: Similar content already exists.",
                f"Reason: {intercept.reason}"
            ]
        )
        
        # Build special navigation showing existing files
        nav = NavigationLayer()
        nav.existing_alternatives = intercept.alternatives
        nav.documentation_inventory = {
            alt['file']: self.project_awareness.get_doc_metadata(alt['file'])
            for alt in intercept.alternatives
            if alt['file'] in self.project_awareness.doc_inventory
        }
        
        context.navigation = nav
        
        # Add specific content from conflicting files
        content_items = []
        for alt in intercept.alternatives[:3]:  # Top 3 alternatives
            if Path(alt['file']).exists():
                content_items.append(ContextItem(
                    type='existing_alternative',
                    path=alt['file'],
                    content=self._get_file_preview(alt['file']),
                    relevance_score=alt['confidence'],
                    metadata={'reason': alt['reason']}
                ))
        
        context.content = ContentLayer(items=content_items)
        
        # Add clear guidance
        context.guidance = GuidanceLayer(
            primary_action=f"Update existing file: {intercept.alternatives[0]['file']}",
            steps=[
                f"Open {intercept.alternatives[0]['file']}",
                "Find the appropriate section to update",
                "Add your improvements there",
                "Update the table of contents if needed"
            ],
            rationale="Maintaining a single source of truth prevents confusion and fragmentation."
        )
        
        return context
```

## Integration with Existing System

### Modify context_manager.py

```python
class ContextManager:
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Add new enhanced collector
        self.enhanced_collector = None
        if self.project_root:
            self.enhanced_collector = EnhancedContextCollector(self)
    
    def collect_context_for_task(self, task_description: str, agent_type: str = None,
                                max_tokens: int = 50000, **kwargs):
        """Updated to use enhanced collector when available."""
        
        # Use enhanced collector if initialized
        if self.enhanced_collector and self.config.use_enhanced_collection:
            return self.enhanced_collector.collect_context_for_task(
                task_description, agent_type, max_tokens
            )
        
        # Fall back to original implementation
        return self._original_collect_context_for_task(
            task_description, agent_type, max_tokens, **kwargs
        )
```

## Configuration Updates

```python
@dataclass
class ContextManagerConfig:
    """Extended configuration."""
    # Existing fields...
    
    # New fields for enhanced collection
    use_enhanced_collection: bool = True
    prevent_redundancy: bool = True
    show_relationships: bool = True
    scale_context_by_scope: bool = True
    
    # Thresholds
    redundancy_threshold: float = 0.7
    min_relevance_narrow: float = 0.5
    min_relevance_broad: float = 0.3
```

## Testing Strategy

### Unit Tests

```python
def test_redundancy_detection():
    """Test that redundancy is detected correctly."""
    awareness = ProjectAwareness("/test/project")
    awareness.doc_inventory = {
        "CONTEXT_MANAGER_V1.1_PLAN.md": DocMetadata(
            path="CONTEXT_MANAGER_V1.1_PLAN.md",
            title="Context Manager V1.1 Plan",
            topics=["context", "improvements", "collection"]
        )
    }
    
    check = awareness.check_redundancy(
        proposed_file="CONTEXT_COLLECTION_PLAN.md",
        content_type="plan",
        topic="context collection"
    )
    
    assert check.has_conflicts
    assert check.conflicts[0]['type'] == 'topic_overlap'

def test_scope_detection():
    """Test task scope analysis."""
    scaler = ContextScaler(mock_project_index())
    
    assert scaler.analyze_task_scope("Fix typo in login.py") == TaskScope.NARROW
    assert scaler.analyze_task_scope("Refactor authentication module") == TaskScope.FOCUSED
    assert scaler.analyze_task_scope("Add logging to all endpoints") == TaskScope.BROAD
    assert scaler.analyze_task_scope("Create Swiss Army Knife agent") == TaskScope.FULL

def test_anti_redundancy_context():
    """Test that anti-redundancy context is built correctly."""
    collector = EnhancedContextCollector(mock_context_manager())
    
    context = collector.collect_context_for_task(
        "Create a new plan for improving context collection"
    )
    
    assert "REDUNDANCY DETECTED" in context.warnings[0]
    assert "Update existing file" in context.guidance.primary_action
    assert len(context.content.items) > 0
```

## Migration Plan

### Phase 1: Add Classes (No Breaking Changes)
1. Add new classes to context_manager.py
2. Keep existing functionality intact
3. Add feature flag for enhanced collection

### Phase 2: Gradual Rollout
1. Enable for specific agent types first
2. Monitor redundancy prevention metrics
3. Collect feedback on context quality

### Phase 3: Full Migration
1. Make enhanced collection the default
2. Deprecate old collection method
3. Remove feature flags

## Performance Considerations

### Caching Strategy
```python
class ProjectAwarenessCache:
    """Cache project understanding to avoid repeated scanning."""
    
    def __init__(self, ttl_seconds: int = 300):
        self.cache = {}
        self.ttl = ttl_seconds
        self.last_scan = {}
    
    def get_or_compute(self, key: str, compute_func: Callable):
        if key in self.cache:
            if time.time() - self.last_scan[key] < self.ttl:
                return self.cache[key]
        
        result = compute_func()
        self.cache[key] = result
        self.last_scan[key] = time.time()
        return result
```

### Async Operations
```python
async def collect_context_async(self, task: str) -> ProjectContext:
    """Async version for better performance."""
    # Run independent operations in parallel
    navigation_task = asyncio.create_task(self._build_navigation_async())
    scope_task = asyncio.create_task(self._analyze_scope_async(task))
    
    navigation = await navigation_task
    scope = await scope_task
    
    # Build remaining layers
    relationships = await self._build_relationships_async(scope, navigation)
    content = await self._build_content_async(scope, relationships)
    
    return ProjectContext(
        navigation=navigation,
        relationships=relationships,
        content=content
    )
```

## Success Metrics

### Implementation Metrics
- **Code Coverage**: >90% for new classes
- **Performance**: <2s for typical context collection
- **Cache Hit Rate**: >80% for project awareness

### Business Metrics
- **Redundant Files Created**: Track reduction from baseline
- **Agent Success Rate**: Measure task completion improvement
- **Context Quality Score**: Agent feedback on usefulness

## Conclusion

This implementation guide provides concrete steps to build a context collection system that acts as a true "project consciousness." By implementing these classes and following the migration plan, the Context Manager will actively prevent redundancy and guide agents to work effectively within the existing project structure.