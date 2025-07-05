# Context Collection System - Practical Example

## Real-World Scenario: Preventing Documentation Redundancy

This example demonstrates how the new context collection system would have prevented the creation of redundant planning documents.

### What Actually Happened

An agent was asked to create a context collection improvement plan and created:
- `CONTEXT_COLLECTION_IMPROVEMENT_PLAN.md`
- `CONTEXT_MANAGER_CLEANUP_PLAN.md` 
- `CONTEXT_MANAGER_CLEANUP_DETAILS.md`

However, similar documentation already existed:
- `docs/agents/context-manager/TECHNICAL_DESIGN.md`
- `docs/agents/context-manager/IMPLEMENTATION_PLAN.md`
- `CONTEXT_MANAGER_V1.1_PLAN.md`

### How the New System Would Handle This

#### 1. Task Analysis Phase

```python
task = "Create a plan to improve context collection quality"

# System analyzes task
task_analysis = {
    'intent': 'create_documentation',
    'type': 'plan',
    'topic': 'context_collection',
    'action': 'improve',
    'scope': 'FOCUSED'
}
```

#### 2. Navigation Layer Response

```
## ⚠️ BEFORE YOU CREATE NEW DOCUMENTATION

### Existing Documentation Inventory

📁 Context Manager Documentation (12 files)
├── docs/agents/context-manager/
│   ├── TECHNICAL_DESIGN.md - Complete technical design including context collection
│   ├── IMPLEMENTATION_PLAN.md - Week-by-week implementation guide
│   └── AGENT_SPECIFICATION.md - Full API and behavior specification
├── Root Level Planning Docs
│   ├── CONTEXT_MANAGER_V1.1_PLAN.md - Current improvement plan (created 2 days ago)
│   └── CONTEXT_COLLECTION_ROADMAP.md - Existing collection improvements

### Similar Documents Detected (Relevance Score)
1. CONTEXT_MANAGER_V1.1_PLAN.md (0.89) - Already contains context improvements
2. TECHNICAL_DESIGN.md:context-collection (0.82) - Has context collection design
3. IMPLEMENTATION_PLAN.md:week-3 (0.75) - Covers context optimization

### Recommendation
❌ DO NOT create a new plan document
✅ UPDATE CONTEXT_MANAGER_V1.1_PLAN.md - Section 3: Context Collection Improvements
```

#### 3. Relationship Layer Shows Connections

```
## Related Files Map

CONTEXT_MANAGER_V1.1_PLAN.md
├── References → context_manager.py (implementation)
├── References → TECHNICAL_DESIGN.md (design details)
├── Referenced by → IMPLEMENTATION_NOTES.md
└── Similar to → Your proposed plan (89% overlap)

context_manager.py::collect_context_for_task()
├── Documented in → TECHNICAL_DESIGN.md
├── Tests in → tests/test_context_collection.py
├── Used by → All agent implementations
└── Last modified → 2 days ago (actively being improved)
```

#### 4. Content Layer Provides Specific Sections

```python
# Instead of dumping entire files, show relevant sections

relevant_sections = [
    {
        'file': 'CONTEXT_MANAGER_V1.1_PLAN.md',
        'section': '## 3. Enhanced Context Collection',
        'line_range': (145, 289),
        'summary': 'Existing plan for context improvements including relevance scoring'
    },
    {
        'file': 'docs/agents/context-manager/TECHNICAL_DESIGN.md',
        'section': '### Context Collection Algorithm',
        'line_range': (567, 812),
        'summary': 'Current algorithm design with identified weaknesses'
    }
]
```

#### 5. Guidance Layer Provides Clear Direction

```
## How to Add Your Improvements

Since context collection improvements are already being tracked, add your enhancements to the existing plan:

1. **Open**: CONTEXT_MANAGER_V1.1_PLAN.md
2. **Navigate to**: Section 3 - Enhanced Context Collection
3. **Add subsection**: "3.4 Quality Improvements"
4. **Include**:
   - Your specific algorithm improvements
   - New relevance scoring approach
   - Implementation priority

This maintains document organization and prevents fragmentation.

## Alternative: Create Detailed Design Doc

If your improvements are substantial enough to warrant a separate document:

1. **Create**: docs/agents/context-manager/CONTEXT_COLLECTION_ALGORITHM_DESIGN.md
2. **Link from**: CONTEXT_MANAGER_V1.1_PLAN.md
3. **Follow pattern**: Similar to TECHNICAL_DESIGN.md structure
```

### The Result

Instead of creating 3 new files with overlapping content, the agent would:

1. **Understand** existing documentation landscape
2. **Recognize** the V1.1 plan already tracks improvements  
3. **Update** the appropriate section of the existing plan
4. **Maintain** document coherence and organization

### Code Example: How It Works

```python
class ContextCollector:
    def collect_context_for_task(self, task: str) -> ProjectContext:
        # Detect creation intent
        if self._detects_creation_intent(task):
            # Check for redundancy BEFORE showing any context
            proposed_type = self._extract_content_type(task)  # 'plan'
            proposed_topic = self._extract_topic(task)  # 'context_collection'
            
            # Find existing related documents
            existing = self.redundancy_preventer.find_existing(
                content_type=proposed_type,
                topic=proposed_topic
            )
            
            if existing.has_matches:
                # Build special context highlighting existing docs
                context = self._build_anti_redundancy_context(existing)
                context.add_warning(
                    "Similar documentation exists. Consider updating instead of creating."
                )
                return context
        
        # Normal context collection for non-creation tasks
        return self._standard_context_collection(task)
```

### Measuring Success

**Before** (Current System):
- Agent sees: Generic file dumps
- Agent thinks: "I should create a comprehensive plan"
- Result: 3 new redundant files

**After** (New System):
- Agent sees: Structured documentation inventory with relationships
- Agent thinks: "There's already a V1.1 plan tracking this"
- Result: Updates 1 existing file appropriately

### Key Insights

1. **Timing Matters**: Check for redundancy BEFORE providing context
2. **Structure Helps**: Showing document organization prevents duplication
3. **Guidance Works**: Explicit directions channel efforts appropriately
4. **Relationships Clarify**: Seeing how files connect reveals overlap

This example demonstrates how the new context collection system acts as a "project consciousness" that actively prevents redundancy and guides agents to work within the existing structure.