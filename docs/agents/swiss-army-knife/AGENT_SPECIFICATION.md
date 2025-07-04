# Swiss Army Knife Agent Specification

## Overview

The Swiss Army Knife Agent is a general-purpose execution agent designed to handle a wide variety of tasks quickly and efficiently. Like its namesake tool, it may not be the perfect specialist for any single task, but it's versatile enough to handle most common requests with reasonable quality.

**Version**: 1.0  
**Status**: In Development  
**Documentation Level**: 1 (Standard)  
**Safety Classification**: Class C (Low - general purpose executor)

## Purpose & Capabilities

### Primary Purpose
Execute diverse tasks ranging from code generation to documentation updates, bug fixes to data analysis, always leveraging the Context Manager for improved performance through pattern recognition.

### Key Capabilities
1. **Code Generation**: Create functions, classes, and modules up to 200 lines
2. **Bug Fixing**: Identify and fix simple to moderate bugs
3. **Documentation**: Write and update documentation, comments, and docstrings
4. **Refactoring**: Small-scale code improvements and cleanup
5. **Testing**: Generate unit tests for existing code
6. **Analysis**: Basic code analysis and recommendations
7. **Integration**: Work with Context Manager for pattern-based improvements

### Constraints
- Cannot handle tasks requiring deep domain expertise
- Limited to single-file modifications (multi-file coordination requires specialized agents)
- Maximum execution time: 10 minutes per task
- Code generation limited to ~200 lines for quality assurance
- Must query Context Manager before executing tasks

## API Specification

### Core Interface

```python
from dataclasses import dataclass
from typing import Dict, Any, List, Optional
from enum import Enum

class TaskType(Enum):
    """Types of tasks the Swiss Army Agent can handle."""
    CODE_GENERATION = "code_generation"
    BUG_FIX = "bug_fix"
    DOCUMENTATION = "documentation"
    REFACTORING = "refactoring"
    TESTING = "testing"
    ANALYSIS = "analysis"
    GENERAL = "general"

@dataclass
class TaskRequest:
    """Request structure for Swiss Army Agent."""
    task_description: str
    task_type: TaskType
    context: Dict[str, Any]
    constraints: Optional[Dict[str, Any]] = None
    timeout_seconds: int = 600  # 10 minutes default

@dataclass
class TaskResult:
    """Result structure from Swiss Army Agent."""
    success: bool
    output: Any
    confidence: float  # 0.0 to 1.0
    patterns_used: List[str]
    execution_time_ms: int
    suggestions: List[str]
    error: Optional[str] = None

class SwissArmyAgent:
    """General-purpose task execution agent."""
    
    def execute_task(self, request: TaskRequest) -> TaskResult:
        """
        Execute a task based on the request.
        
        Args:
            request: Task request with description and context
            
        Returns:
            TaskResult with output and metadata
            
        Raises:
            TimeoutError: If task exceeds timeout
            ValueError: If task type not supported
        """
        
    def analyze_request(self, description: str) -> TaskType:
        """Determine the type of task from description."""
        
    def estimate_complexity(self, request: TaskRequest) -> Dict[str, Any]:
        """
        Estimate task complexity and duration.
        
        Returns:
            Dict with complexity level, estimated time, confidence
        """
```

### Integration with Context Manager

```python
class ContextAwareSwissArmyAgent(SwissArmyAgent):
    """Swiss Army Agent with Context Manager integration."""
    
    def __init__(self, context_manager: ContextManager):
        self.cm = context_manager
        
    def search_relevant_patterns(self, request: TaskRequest) -> List[Context]:
        """Query Context Manager for relevant patterns."""
        queries = self.generate_search_queries(request)
        results = []
        for query in queries:
            contexts = self.cm.query_context(
                query=query,
                filters={'success_rate': '>0.7'},
                limit=5
            )
            results.extend(contexts)
        return self.rank_by_relevance(results, request)
    
    def apply_patterns(self, patterns: List[Context], task: Any) -> Any:
        """Apply learned patterns to improve task execution."""
        # Pattern application logic
        pass
    
    def update_context_with_result(self, request: TaskRequest, result: TaskResult):
        """Store execution result in Context Manager."""
        self.cm.add_context(Context(
            type=ContextType.EXECUTION,
            source='SwissArmyAgent',
            data={
                'request': request.__dict__,
                'result': result.__dict__,
                'patterns_effective': self.evaluate_pattern_effectiveness()
            }
        ))
```

## Behavioral Characteristics

### Request Processing Flow

1. **Request Analysis** (1-2s)
   - Parse natural language description
   - Identify task type and requirements
   - Estimate complexity and duration

2. **Context Search** (2-5s)
   - Generate search queries from request
   - Query Context Manager for similar tasks
   - Rank results by relevance

3. **Pattern Application** (0.5-1s)
   - Extract successful patterns from context
   - Adapt patterns to current request
   - Build execution plan

4. **Task Execution** (5s-10min)
   - Execute task with progress updates
   - Apply patterns during execution
   - Handle errors gracefully

5. **Result Packaging** (1-2s)
   - Format output appropriately
   - Calculate confidence score
   - Generate improvement suggestions

### Quality Heuristics

The agent uses these heuristics to ensure output quality:

1. **Pattern Matching**: Higher confidence when similar patterns found
2. **Complexity Check**: Lower confidence for tasks near capability limits
3. **Validation**: Basic validation of generated output
4. **Coherence**: Ensure output matches request intent

### Error Handling

```python
class SwissArmyError(Exception):
    """Base exception for Swiss Army Agent errors."""
    pass

class TaskTooComplexError(SwissArmyError):
    """Task exceeds agent capabilities."""
    pass

class PatternApplicationError(SwissArmyError):
    """Failed to apply pattern effectively."""
    pass

class TimeoutError(SwissArmyError):
    """Task execution exceeded timeout."""
    pass
```

### Confidence Scoring

Confidence is calculated based on:
- **Pattern Match Score** (40%): How well context matches request
- **Complexity Score** (30%): Inverse of task complexity
- **Execution Success** (20%): Clean execution without errors
- **Validation Score** (10%): Output passes basic checks

## Task Examples

### Code Generation
```python
request = TaskRequest(
    task_description="Create a function to validate email addresses",
    task_type=TaskType.CODE_GENERATION,
    context={"language": "python", "style": "defensive"},
    constraints={"max_lines": 50}
)

# Result includes generated code with patterns from Context Manager
```

### Bug Fix
```python
request = TaskRequest(
    task_description="Fix the SQL injection vulnerability in this query",
    task_type=TaskType.BUG_FIX,
    context={"code": vulnerable_code, "language": "python"},
    timeout_seconds=300
)

# Result includes fixed code with security best practices applied
```

### Documentation
```python
request = TaskRequest(
    task_description="Add comprehensive docstrings to this class",
    task_type=TaskType.DOCUMENTATION,
    context={"code": undocumented_class, "style": "google"},
)

# Result includes documented code following style guide
```

## Performance Requirements

### Response Times (Realistic for v1)

| Operation | Target | Maximum | Notes |
|-----------|--------|---------|-------|
| Request Analysis | 2s | 5s | Parse and classify |
| Context Search | 3s | 10s | May timeout gracefully |
| Simple Tasks | 10s | 60s | <50 lines of code |
| Complex Tasks | 1min | 10min | Full timeout allowed |
| Result Packaging | 1s | 5s | Format and validate |

### Resource Limits

- **Memory Usage**: <500MB per task
- **Token Usage**: <5000 tokens per request
- **Context Search**: <10 queries per task
- **Output Size**: <10KB for code, <50KB for docs

### Throughput

- **Concurrent Tasks**: 1 (sequential execution in v1)
- **Tasks per Hour**: ~20-50 depending on complexity
- **Queue Depth**: 100 tasks maximum

## Testing Strategy

### Unit Tests

```python
class TestSwissArmyAgent:
    def test_task_classification(self):
        """Test correct identification of task types."""
        
    def test_simple_code_generation(self):
        """Test generation of simple functions."""
        
    def test_pattern_application(self):
        """Test that patterns improve output."""
        
    def test_timeout_handling(self):
        """Test graceful timeout after 10 minutes."""
        
    def test_error_recovery(self):
        """Test error handling and partial results."""
```

### Integration Tests

```python
class TestSwissArmyIntegration:
    def test_context_manager_flow(self):
        """Test full flow with Context Manager."""
        
    def test_pattern_learning(self):
        """Test that agent learns from successes."""
        
    def test_workflow_integration(self):
        """Test integration with Swiss Army Knife workflow."""
```

## Monitoring & Metrics

### Key Metrics

```python
@dataclass
class SwissArmyMetrics:
    # Performance
    tasks_completed: int
    success_rate: float
    avg_execution_time: float
    timeout_rate: float
    
    # Quality
    avg_confidence_score: float
    pattern_usage_rate: float
    user_approval_rate: float
    
    # Patterns
    patterns_applied: int
    pattern_effectiveness: float
    new_patterns_discovered: int
    
    # Errors
    error_rate: float
    common_errors: Dict[str, int]
```

### Health Checks

```python
def health_check() -> Dict[str, Any]:
    return {
        'status': 'healthy',
        'uptime': uptime_seconds,
        'tasks_in_queue': queue_depth,
        'avg_response_time': avg_time_ms,
        'context_manager_connected': cm_healthy,
        'last_error': last_error_time
    }
```

## Evolution Path

### v1.0 (Current)
- Basic task execution
- Context Manager integration
- Single-task processing
- Simple pattern application

### v1.5 (Planned)
- Concurrent task processing
- Improved pattern matching
- Multi-language support
- Better error recovery

### v2.0 (Future)
- Multi-file coordination
- Complex refactoring
- Learning from failures
- Autonomous improvement

## Limitations & Considerations

### What Swiss Army Agent is NOT good at:
1. **Deep expertise tasks**: Use specialized agents
2. **Multi-file refactoring**: Requires coordination agent
3. **Performance optimization**: Needs profiling tools
4. **Security audits**: Requires security agent
5. **Architecture design**: Needs design agent

### When to use specialized agents instead:
- **Critical code**: Use Code Agent with QA Agent
- **Medical device features**: Use FDA-compliant workflow
- **System design**: Use Design Agent
- **Complex testing**: Use dedicated QA Agent

## Safety & Security

### Sandboxing
- Code execution in isolated environment
- No direct file system access (only through APIs)
- Limited network access
- Resource quotas enforced

### Validation
- Output syntax validation
- Basic security checks (no obvious vulnerabilities)
- Size and complexity limits
- Pattern source verification

---

*The Swiss Army Knife Agent: Good enough for most tasks, fast enough to be useful, smart enough to learn from experience.*