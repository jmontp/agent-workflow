# Context Management System API Specification

## Overview

This document defines the API interfaces for the Context Management System components, providing detailed specifications for inter-component communication and external integrations.

## Core API Interfaces

### Context Manager API

#### `IContextManager`

The primary interface for context management operations.

```python
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from enum import Enum

class ContextPriority(Enum):
    CRITICAL = "critical"
    HIGH = "high" 
    MEDIUM = "medium"
    LOW = "low"

@dataclass
class ContextRequest:
    """Request for agent context preparation"""
    agent_type: str
    task: 'TDDTask'
    story_id: str
    max_tokens: int
    priority: ContextPriority = ContextPriority.MEDIUM
    include_memory: bool = True
    compression_level: str = "moderate"  # low, moderate, high
    cache_enabled: bool = True

@dataclass
class AgentContext:
    """Prepared context for agent execution"""
    context_id: str
    agent_type: str
    story_id: str
    core_context: str
    dependencies: Optional[str] = None
    agent_memory: Optional[str] = None
    metadata: Dict[str, Any] = None
    token_usage: Dict[str, int] = None
    preparation_time: float = 0.0
    cache_hit: bool = False

class IContextManager(ABC):
    """Primary interface for context management"""
    
    @abstractmethod
    async def prepare_context(self, request: ContextRequest) -> AgentContext:
        """Prepare optimized context for agent task execution"""
        pass
    
    @abstractmethod
    async def update_context(self, context_id: str, changes: Dict[str, Any]) -> None:
        """Update existing context with incremental changes"""
        pass
    
    @abstractmethod
    async def invalidate_context(self, context_id: str) -> None:
        """Invalidate cached context"""
        pass
    
    @abstractmethod
    async def get_context_metrics(self, context_id: str) -> Dict[str, Any]:
        """Get context usage and performance metrics"""
        pass
    
    @abstractmethod
    async def cleanup_expired_contexts(self, max_age_hours: int = 24) -> int:
        """Clean up expired contexts and return count removed"""
        pass
```

### Context Filter API

#### `IContextFilter`

Interface for relevance-based context filtering.

```python
@dataclass
class FilterCriteria:
    """Criteria for context filtering"""
    task_description: str
    source_files: List[str]
    test_files: List[str]
    tdd_phase: 'TDDState'
    agent_type: str
    story_id: str
    include_patterns: List[str] = None
    exclude_patterns: List[str] = None
    max_files: int = 100

@dataclass
class FilterResult:
    """Result of context filtering"""
    relevant_files: List[str]
    relevance_scores: Dict[str, float]
    excluded_files: List[str]
    filter_reason: Dict[str, str]
    processing_time: float

class IContextFilter(ABC):
    """Interface for intelligent context filtering"""
    
    @abstractmethod
    async def filter_relevant_files(self, criteria: FilterCriteria) -> FilterResult:
        """Filter files based on relevance criteria"""
        pass
    
    @abstractmethod
    async def calculate_relevance_score(self, file_path: str, criteria: FilterCriteria) -> float:
        """Calculate relevance score for a single file"""
        pass
    
    @abstractmethod
    async def get_dependency_chain(self, file_path: str, max_depth: int = 3) -> List[str]:
        """Get dependency chain for a file"""
        pass
    
    @abstractmethod
    async def update_relevance_model(self, feedback: Dict[str, Any]) -> None:
        """Update relevance scoring based on usage feedback"""
        pass
```

### Token Calculator API

#### `ITokenCalculator`

Interface for token counting and budget management.

```python
@dataclass
class TokenBudget:
    """Token budget allocation"""
    total_budget: int
    core_context: int
    dependencies: int
    agent_memory: int
    metadata: int
    buffer: int
    
    def validate(self) -> bool:
        """Validate budget allocation doesn't exceed total"""
        allocated = self.core_context + self.dependencies + self.agent_memory + self.metadata + self.buffer
        return allocated <= self.total_budget

@dataclass
class TokenUsage:
    """Actual token usage"""
    estimated_tokens: int
    actual_tokens: int
    by_component: Dict[str, int]
    accuracy_percentage: float

class ITokenCalculator(ABC):
    """Interface for token calculation and budget management"""
    
    @abstractmethod
    def estimate_tokens(self, content: str, model: str = "claude-3") -> int:
        """Estimate token count for content"""
        pass
    
    @abstractmethod
    async def calculate_budget(self, total_tokens: int, context_components: Dict[str, Any]) -> TokenBudget:
        """Calculate optimal token budget allocation"""
        pass
    
    @abstractmethod
    async def validate_budget_usage(self, budget: TokenBudget, actual_usage: Dict[str, str]) -> TokenUsage:
        """Validate actual usage against budget"""
        pass
    
    @abstractmethod
    def get_compression_recommendation(self, content_size: int, target_size: int) -> str:
        """Recommend compression level to meet target size"""
        pass
```

### Context Compressor API

#### `IContextCompressor`

Interface for intelligent content compression.

```python
@dataclass
class CompressionRequest:
    """Request for content compression"""
    content: str
    content_type: str  # python, test, markdown, json, etc.
    target_tokens: int
    preserve_structure: bool = True
    preserve_semantics: bool = True
    compression_strategy: str = "adaptive"  # aggressive, moderate, conservative, adaptive

@dataclass
class CompressionResult:
    """Result of content compression"""
    compressed_content: str
    original_tokens: int
    compressed_tokens: int
    compression_ratio: float
    semantic_preservation_score: float
    processing_time: float
    strategy_used: str

class IContextCompressor(ABC):
    """Interface for intelligent context compression"""
    
    @abstractmethod
    async def compress_content(self, request: CompressionRequest) -> CompressionResult:
        """Compress content according to specifications"""
        pass
    
    @abstractmethod
    async def compress_file_collection(self, files: Dict[str, str], target_tokens: int) -> Dict[str, CompressionResult]:
        """Compress multiple files with coordinated token budget"""
        pass
    
    @abstractmethod
    def estimate_compression_ratio(self, content: str, content_type: str) -> float:
        """Estimate achievable compression ratio"""
        pass
    
    @abstractmethod
    async def decompress_content(self, compressed_content: str, metadata: Dict[str, Any]) -> str:
        """Decompress content if reversible compression was used"""
        pass
```

### Agent Memory API

#### `IAgentMemory`

Interface for persistent agent memory management.

```python
@dataclass
class Decision:
    """Agent decision record"""
    id: str
    agent_type: str
    task_id: str
    decision_type: str
    context: Dict[str, Any]
    rationale: str
    outcome: str
    timestamp: str
    confidence: float

@dataclass
class PhaseHandoff:
    """TDD phase handoff record"""
    from_phase: 'TDDState'
    to_phase: 'TDDState'
    artifacts: Dict[str, str]
    context_summary: str
    handoff_notes: str
    timestamp: str

@dataclass
class AgentMemory:
    """Complete agent memory"""
    agent_type: str
    story_id: str
    decisions: List[Decision]
    artifacts: Dict[str, str]
    learned_patterns: List[str]
    phase_handoffs: List[PhaseHandoff]
    context_preferences: Dict[str, Any]
    performance_metrics: Dict[str, float]

class IAgentMemory(ABC):
    """Interface for agent memory management"""
    
    @abstractmethod
    async def store_decision(self, decision: Decision) -> None:
        """Store agent decision"""
        pass
    
    @abstractmethod
    async def store_artifacts(self, agent_type: str, story_id: str, artifacts: Dict[str, str]) -> None:
        """Store agent artifacts"""
        pass
    
    @abstractmethod
    async def store_phase_handoff(self, handoff: PhaseHandoff) -> None:
        """Store TDD phase handoff"""
        pass
    
    @abstractmethod
    async def get_agent_memory(self, agent_type: str, story_id: str) -> AgentMemory:
        """Retrieve complete agent memory"""
        pass
    
    @abstractmethod
    async def get_relevant_decisions(self, agent_type: str, task_context: Dict[str, Any], limit: int = 10) -> List[Decision]:
        """Get relevant past decisions for current task"""
        pass
    
    @abstractmethod
    async def update_performance_metrics(self, agent_type: str, story_id: str, metrics: Dict[str, float]) -> None:
        """Update agent performance metrics"""
        pass
```

### Context Index API

#### `IContextIndex`

Interface for searchable context indexing.

```python
@dataclass
class IndexEntry:
    """Context index entry"""
    file_path: str
    content_type: str
    symbols: List[str]  # classes, functions, variables
    dependencies: List[str]
    reverse_dependencies: List[str]
    last_modified: str
    content_hash: str
    metadata: Dict[str, Any]

@dataclass
class SearchQuery:
    """Context search query"""
    query_text: str
    file_types: List[str] = None
    symbols: List[str] = None
    max_results: int = 50
    include_dependencies: bool = False
    similarity_threshold: float = 0.7

@dataclass
class SearchResult:
    """Context search result"""
    entries: List[IndexEntry]
    relevance_scores: Dict[str, float]
    query_time: float
    total_matches: int

class IContextIndex(ABC):
    """Interface for context indexing and search"""
    
    @abstractmethod
    async def index_file(self, file_path: str) -> IndexEntry:
        """Index a single file"""
        pass
    
    @abstractmethod
    async def index_directory(self, directory_path: str, patterns: List[str] = None) -> List[IndexEntry]:
        """Index all files in directory matching patterns"""
        pass
    
    @abstractmethod
    async def search(self, query: SearchQuery) -> SearchResult:
        """Search indexed content"""
        pass
    
    @abstractmethod
    async def get_dependencies(self, file_path: str, include_reverse: bool = False) -> List[str]:
        """Get file dependencies"""
        pass
    
    @abstractmethod
    async def invalidate_file(self, file_path: str) -> None:
        """Remove file from index"""
        pass
    
    @abstractmethod
    async def rebuild_index(self, project_path: str) -> int:
        """Rebuild complete index and return entry count"""
        pass
```

## Configuration APIs

### Context Configuration

```python
@dataclass
class ContextConfig:
    """Context management configuration"""
    max_context_tokens: int = 200000
    default_compression_level: str = "moderate"
    cache_ttl_hours: int = 24
    max_cache_size_mb: int = 1000
    enable_predictive_caching: bool = True
    relevance_threshold: float = 0.5
    max_dependency_depth: int = 3
    token_buffer_percentage: float = 0.05

@dataclass
class AgentConfig:
    """Agent-specific context configuration"""
    agent_type: str
    preferred_context_size: int
    compression_tolerance: str = "moderate"
    memory_retention_days: int = 30
    context_priorities: Dict[str, float] = None
    
class IContextConfig(ABC):
    """Interface for context configuration management"""
    
    @abstractmethod
    def get_context_config(self) -> ContextConfig:
        """Get current context configuration"""
        pass
    
    @abstractmethod
    def get_agent_config(self, agent_type: str) -> AgentConfig:
        """Get agent-specific configuration"""
        pass
    
    @abstractmethod
    async def update_config(self, config: ContextConfig) -> None:
        """Update context configuration"""
        pass
    
    @abstractmethod
    async def update_agent_config(self, agent_type: str, config: AgentConfig) -> None:
        """Update agent-specific configuration"""
        pass
```

## External Integration APIs

### Claude Code Integration

```python
class IClaudeCodeIntegration(ABC):
    """Interface for Claude Code CLI integration"""
    
    @abstractmethod
    async def prepare_claude_prompt(self, context: AgentContext, task: 'TDDTask') -> str:
        """Prepare optimized prompt for Claude Code CLI"""
        pass
    
    @abstractmethod
    async def estimate_claude_tokens(self, prompt: str) -> int:
        """Estimate token usage for Claude Code prompt"""
        pass
    
    @abstractmethod
    async def execute_with_context(self, agent_type: str, prompt: str, context: AgentContext) -> Dict[str, Any]:
        """Execute Claude Code with prepared context"""
        pass
```

### TDD State Machine Integration

```python
class ITDDContextIntegration(ABC):
    """Interface for TDD state machine integration"""
    
    @abstractmethod
    def get_phase_context_requirements(self, phase: 'TDDState') -> Dict[str, Any]:
        """Get context requirements for TDD phase"""
        pass
    
    @abstractmethod
    async def prepare_phase_handoff(self, from_phase: 'TDDState', to_phase: 'TDDState', context: AgentContext) -> PhaseHandoff:
        """Prepare context for TDD phase transition"""
        pass
    
    @abstractmethod
    async def validate_phase_context(self, phase: 'TDDState', context: AgentContext) -> bool:
        """Validate context completeness for TDD phase"""
        pass
```

## Error Handling APIs

### Context Exceptions

```python
class ContextException(Exception):
    """Base exception for context management errors"""
    pass

class TokenLimitExceededException(ContextException):
    """Raised when context exceeds token limits"""
    def __init__(self, required_tokens: int, max_tokens: int):
        self.required_tokens = required_tokens
        self.max_tokens = max_tokens
        super().__init__(f"Context requires {required_tokens} tokens, but limit is {max_tokens}")

class ContextNotFoundError(ContextException):
    """Raised when requested context is not available"""
    pass

class CompressionFailedException(ContextException):
    """Raised when content compression fails"""
    pass

class IndexCorruptedException(ContextException):
    """Raised when context index is corrupted"""
    pass
```

### Error Recovery Interface

```python
class IContextErrorRecovery(ABC):
    """Interface for context error recovery"""
    
    @abstractmethod
    async def handle_token_limit_exceeded(self, request: ContextRequest, current_size: int) -> AgentContext:
        """Handle token limit exceeded by applying aggressive compression"""
        pass
    
    @abstractmethod
    async def recover_from_index_corruption(self, project_path: str) -> bool:
        """Recover from index corruption by rebuilding"""
        pass
    
    @abstractmethod
    async def fallback_to_basic_context(self, request: ContextRequest) -> AgentContext:
        """Provide basic context when advanced features fail"""
        pass
```

## Monitoring and Metrics APIs

### Context Metrics

```python
@dataclass
class ContextMetrics:
    """Context management metrics"""
    total_requests: int
    cache_hit_rate: float
    average_preparation_time: float
    token_utilization_rate: float
    compression_effectiveness: float
    context_relevance_score: float

@dataclass
class PerformanceMetrics:
    """Performance metrics"""
    cpu_usage_percentage: float
    memory_usage_mb: float
    disk_io_rate: float
    network_io_rate: float
    cache_size_mb: float
    index_size_mb: float

class IContextMetrics(ABC):
    """Interface for context metrics collection"""
    
    @abstractmethod
    async def collect_context_metrics(self, time_range_hours: int = 24) -> ContextMetrics:
        """Collect context management metrics"""
        pass
    
    @abstractmethod
    async def collect_performance_metrics(self) -> PerformanceMetrics:
        """Collect system performance metrics"""
        pass
    
    @abstractmethod
    async def export_metrics(self, format: str = "json") -> str:
        """Export metrics in specified format"""
        pass
```

## Usage Examples

### Basic Context Preparation

```python
# Example: Prepare context for QA Agent in TEST_RED phase
async def prepare_qa_context_example():
    context_manager = get_context_manager()
    
    request = ContextRequest(
        agent_type="QAAgent",
        task=current_tdd_task,
        story_id="story-123",
        max_tokens=80000,
        priority=ContextPriority.HIGH,
        compression_level="moderate"
    )
    
    context = await context_manager.prepare_context(request)
    
    # Use context with QA Agent
    qa_agent = QAAgent()
    result = await qa_agent.execute_task(context)
    
    return result
```

### Advanced Context Filtering

```python
# Example: Filter files for Code Agent implementation
async def filter_implementation_context():
    context_filter = get_context_filter()
    
    criteria = FilterCriteria(
        task_description="Implement user authentication service",
        source_files=["src/auth/", "src/user/"],
        test_files=["tests/tdd/auth_test.py"],
        tdd_phase=TDDState.CODE_GREEN,
        agent_type="CodeAgent",
        story_id="story-123",
        include_patterns=["*.py", "*.md"],
        exclude_patterns=["*__pycache__*", "*.pyc"],
        max_files=50
    )
    
    result = await context_filter.filter_relevant_files(criteria)
    
    print(f"Found {len(result.relevant_files)} relevant files")
    for file_path, score in result.relevance_scores.items():
        print(f"  {file_path}: {score:.2f}")
    
    return result
```

### Context Compression

```python
# Example: Compress large implementation files
async def compress_implementation_files():
    compressor = get_context_compressor()
    
    files = {
        "src/auth/service.py": read_file("src/auth/service.py"),
        "src/auth/models.py": read_file("src/auth/models.py"),
        "src/auth/repository.py": read_file("src/auth/repository.py")
    }
    
    compressed_files = await compressor.compress_file_collection(
        files=files,
        target_tokens=30000
    )
    
    for file_path, result in compressed_files.items():
        print(f"{file_path}: {result.original_tokens} -> {result.compressed_tokens} tokens "
              f"({result.compression_ratio:.2f}x compression)")
    
    return compressed_files
```

This API specification provides a comprehensive interface for all Context Management System components, enabling clean separation of concerns and easy testing and integration.