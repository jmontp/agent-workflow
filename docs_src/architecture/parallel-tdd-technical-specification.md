# Parallel TDD Technical Specification

## Overview

This technical specification defines the APIs, data models, protocols, and integration points for the Parallel TDD Execution system. It serves as the authoritative reference for implementation teams.

## Data Models

### Core Entities

#### ParallelTDDCycle
```python
@dataclass
class ParallelTDDCycle(TDDCycle):
    """Extended TDD cycle for parallel execution"""
    # Inherited from TDDCycle
    id: str
    story_id: str
    current_state: TDDState
    tasks: List[TDDTask]
    
    # Parallel-specific fields
    parallel_group_id: str = ""  # Group of cycles running together
    execution_priority: int = 5  # 1-10, higher = more priority
    resource_allocation: ResourceAllocation = field(default_factory=ResourceAllocation)
    conflict_status: ConflictStatus = ConflictStatus.NONE
    dependencies: List[str] = field(default_factory=list)  # Other cycle IDs
    lock_holdings: List[FileLock] = field(default_factory=list)
    context_id: str = ""  # Isolated context identifier
    transaction_id: str = ""  # Optimistic concurrency transaction
    
    # Metrics
    wait_time_seconds: float = 0.0
    execution_time_seconds: float = 0.0
    conflict_resolution_time: float = 0.0
    token_usage: int = 0
```

#### ResourceAllocation
```python
@dataclass
class ResourceAllocation:
    """Resource allocation for a parallel cycle"""
    agent_assignments: Dict[AgentType, str] = field(default_factory=dict)  # type -> agent_id
    token_budget: int = 50000
    test_environment_id: Optional[str] = None
    cpu_cores: float = 1.0
    memory_mb: int = 1024
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "agent_assignments": self.agent_assignments,
            "token_budget": self.token_budget,
            "test_environment_id": self.test_environment_id,
            "cpu_cores": self.cpu_cores,
            "memory_mb": self.memory_mb
        }
```

#### Conflict
```python
@dataclass
class Conflict:
    """Represents a conflict between parallel cycles"""
    id: str = field(default_factory=lambda: f"conflict_{uuid.uuid4().hex[:8]}")
    type: ConflictType = ConflictType.FILE_OVERLAP
    severity: ConflictSeverity = ConflictSeverity.MEDIUM
    cycle_ids: List[str] = field(default_factory=list)
    resources: List[str] = field(default_factory=list)  # Files, tests, etc.
    detected_at: datetime = field(default_factory=datetime.now)
    resolution_strategy: Optional[ResolutionStrategy] = None
    resolved_at: Optional[datetime] = None
    resolution_result: Optional[ResolutionResult] = None
    
    def can_auto_resolve(self) -> bool:
        return self.severity in [ConflictSeverity.LOW, ConflictSeverity.MEDIUM]
```

#### FileLock
```python
@dataclass
class FileLock:
    """Distributed file lock for parallel execution"""
    file_path: str
    lock_id: str = field(default_factory=lambda: uuid.uuid4().hex)
    owner_cycle_id: str = ""
    lock_type: LockType = LockType.EXCLUSIVE
    acquired_at: datetime = field(default_factory=datetime.now)
    expires_at: Optional[datetime] = None
    version: int = 0  # For optimistic concurrency
    
    def is_expired(self) -> bool:
        if not self.expires_at:
            return False
        return datetime.now() > self.expires_at
```

### Enumerations

```python
class ConflictType(Enum):
    FILE_OVERLAP = "file_overlap"           # Same file modified
    TEST_COLLISION = "test_collision"       # Same test files
    DEPENDENCY_CONFLICT = "dependency"      # Dependency not ready
    RESOURCE_CONTENTION = "resource"        # Agent/env not available
    SEMANTIC_CONFLICT = "semantic"          # Code logic conflicts

class ConflictSeverity(Enum):
    LOW = 1      # Can be auto-resolved easily
    MEDIUM = 2   # May require smart merging
    HIGH = 3     # Requires careful resolution
    CRITICAL = 4 # Blocks execution

class ResolutionStrategy(Enum):
    AUTO_MERGE = "auto_merge"
    SEQUENTIAL = "sequential"  # Run one after another
    REBASE = "rebase"         # Rebase one on top of other
    MANUAL = "manual"         # Human intervention
    ABORT = "abort"           # Cancel one cycle

class LockType(Enum):
    SHARED = "shared"       # Multiple readers
    EXCLUSIVE = "exclusive" # Single writer

class ConflictStatus(Enum):
    NONE = "none"
    POTENTIAL = "potential"   # Predicted but not occurred
    ACTIVE = "active"        # Currently in conflict
    RESOLVING = "resolving"  # Resolution in progress
    RESOLVED = "resolved"    # Successfully resolved
```

## API Specifications

### Parallel Coordinator API

```python
class ParallelCoordinatorAPI:
    """Main API for parallel TDD coordination"""
    
    async def start_parallel_execution(
        self,
        stories: List[Story],
        config: ParallelConfig
    ) -> ParallelExecutionHandle:
        """
        Start parallel execution of multiple stories
        
        Args:
            stories: List of stories to execute
            config: Parallel execution configuration
            
        Returns:
            Handle for monitoring and controlling execution
            
        Raises:
            ResourceExhausted: If insufficient resources
            InvalidConfiguration: If config is invalid
        """
        
    async def schedule_cycle(
        self,
        story: Story,
        priority: int = 5,
        dependencies: List[str] = None
    ) -> ParallelTDDCycle:
        """
        Schedule a single cycle for execution
        
        Args:
            story: Story to execute
            priority: Execution priority (1-10)
            dependencies: List of cycle IDs this depends on
            
        Returns:
            Scheduled cycle object
            
        Raises:
            SchedulingConflict: If cycle cannot be scheduled
            DependencyError: If dependencies cannot be satisfied
        """
        
    async def detect_conflicts(
        self,
        cycle1_id: str,
        cycle2_id: str
    ) -> List[Conflict]:
        """
        Detect conflicts between two cycles
        
        Args:
            cycle1_id: First cycle ID
            cycle2_id: Second cycle ID
            
        Returns:
            List of detected conflicts
        """
        
    async def resolve_conflict(
        self,
        conflict: Conflict,
        strategy: ResolutionStrategy = ResolutionStrategy.AUTO_MERGE
    ) -> ResolutionResult:
        """
        Resolve a conflict between cycles
        
        Args:
            conflict: Conflict to resolve
            strategy: Resolution strategy to use
            
        Returns:
            Resolution result with success status
            
        Raises:
            ResolutionFailed: If conflict cannot be resolved
        """
        
    async def get_execution_status(
        self,
        handle: ParallelExecutionHandle
    ) -> ParallelExecutionStatus:
        """
        Get current status of parallel execution
        
        Args:
            handle: Execution handle from start_parallel_execution
            
        Returns:
            Current execution status with metrics
        """
        
    async def abort_cycle(
        self,
        cycle_id: str,
        reason: str
    ) -> None:
        """
        Abort a running cycle
        
        Args:
            cycle_id: Cycle to abort
            reason: Reason for abortion
            
        Raises:
            CycleNotFound: If cycle doesn't exist
        """
```

### Agent Pool API

```python
class AgentPoolAPI:
    """API for managing agent pools"""
    
    async def acquire_agent(
        self,
        agent_type: AgentType,
        cycle_id: str,
        timeout: int = 30
    ) -> Agent:
        """
        Acquire an agent from the pool
        
        Args:
            agent_type: Type of agent needed
            cycle_id: Cycle requesting the agent
            timeout: Max seconds to wait
            
        Returns:
            Acquired agent instance
            
        Raises:
            AgentPoolExhausted: If no agents available
            TimeoutError: If timeout exceeded
        """
        
    async def release_agent(
        self,
        agent: Agent,
        cycle_id: str
    ) -> None:
        """
        Release agent back to pool
        
        Args:
            agent: Agent to release
            cycle_id: Cycle releasing the agent
        """
        
    async def scale_pool(
        self,
        agent_type: AgentType,
        target_size: int
    ) -> None:
        """
        Scale agent pool to target size
        
        Args:
            agent_type: Type of agent pool
            target_size: Desired pool size
            
        Raises:
            ScalingError: If scaling fails
            InvalidSize: If size outside allowed range
        """
        
    async def get_pool_metrics(
        self,
        agent_type: AgentType
    ) -> PoolMetrics:
        """
        Get metrics for an agent pool
        
        Args:
            agent_type: Type of agent pool
            
        Returns:
            Pool metrics including utilization
        """
```

### Lock Manager API

```python
class LockManagerAPI:
    """API for distributed lock management"""
    
    async def acquire_locks(
        self,
        cycle_id: str,
        file_paths: List[str],
        lock_type: LockType = LockType.EXCLUSIVE,
        timeout: int = 10
    ) -> List[FileLock]:
        """
        Acquire locks for multiple files atomically
        
        Args:
            cycle_id: Cycle requesting locks
            file_paths: Files to lock
            lock_type: Type of lock needed
            timeout: Max seconds to wait
            
        Returns:
            List of acquired locks
            
        Raises:
            LockTimeout: If locks cannot be acquired
            DeadlockDetected: If deadlock detected
        """
        
    async def release_locks(
        self,
        locks: List[FileLock]
    ) -> None:
        """
        Release multiple locks
        
        Args:
            locks: Locks to release
        """
        
    async def extend_lock(
        self,
        lock: FileLock,
        duration: timedelta
    ) -> FileLock:
        """
        Extend lock duration
        
        Args:
            lock: Lock to extend
            duration: Additional duration
            
        Returns:
            Updated lock with new expiry
            
        Raises:
            LockExpired: If lock already expired
            LockNotOwned: If cycle doesn't own lock
        """
        
    async def get_lock_info(
        self,
        file_path: str
    ) -> Optional[FileLock]:
        """
        Get current lock info for a file
        
        Args:
            file_path: File to check
            
        Returns:
            Lock info if locked, None otherwise
        """
```

### Context Manager API

```python
class ParallelContextAPI:
    """API for parallel context management"""
    
    async def create_isolated_context(
        self,
        cycle_id: str,
        story: Story,
        token_budget: int
    ) -> IsolatedContext:
        """
        Create isolated context for a cycle
        
        Args:
            cycle_id: Cycle needing context
            story: Story being executed
            token_budget: Token allocation
            
        Returns:
            Isolated context object
            
        Raises:
            InsufficientTokens: If budget too low
        """
        
    async def share_context(
        self,
        from_cycle: str,
        to_cycle: str,
        context_keys: List[str]
    ) -> None:
        """
        Share specific context between cycles
        
        Args:
            from_cycle: Source cycle ID
            to_cycle: Destination cycle ID
            context_keys: Keys to share
            
        Raises:
            ContextNotFound: If context doesn't exist
            SharingViolation: If sharing not allowed
        """
        
    async def optimize_contexts(
        self,
        cycle_ids: List[str]
    ) -> ContextOptimizationResult:
        """
        Optimize context distribution across cycles
        
        Args:
            cycle_ids: Cycles to optimize
            
        Returns:
            Optimization results with metrics
        """
```

## Integration Protocols

### Agent Communication Protocol

```yaml
# Agent request format
agent_request:
  version: "1.0"
  cycle_id: "cycle_123"
  agent_type: "code"
  task:
    id: "task_456"
    command: "implement_minimal_solution"
    context:
      story_id: "story_789"
      test_files: ["test_feature.py"]
      token_budget: 50000
  metadata:
    priority: 7
    timeout: 300
    
# Agent response format
agent_response:
  version: "1.0"
  cycle_id: "cycle_123"
  task_id: "task_456"
  result:
    success: true
    output: "Implementation complete"
    artifacts:
      "src/feature.py": "..."
    metrics:
      execution_time: 45.2
      tokens_used: 35000
```

### Conflict Detection Protocol

```yaml
# Conflict check request
conflict_check:
  version: "1.0"
  requester: "cycle_123"
  target_resources:
    files: ["user.py", "auth.py"]
    tests: ["test_user.py"]
  operation: "write"
  
# Conflict check response  
conflict_response:
  version: "1.0"
  conflicts:
    - type: "file_overlap"
      severity: "medium"
      conflicting_cycle: "cycle_456"
      resources: ["auth.py"]
      suggestion: "auto_merge"
```

### Lock Acquisition Protocol

```yaml
# Lock request
lock_request:
  version: "1.0"
  cycle_id: "cycle_123"
  requests:
    - file_path: "src/user.py"
      lock_type: "exclusive"
      duration: 300
    - file_path: "src/auth.py"
      lock_type: "exclusive"
      duration: 300
  atomic: true
  
# Lock response
lock_response:
  version: "1.0"
  success: true
  locks:
    - lock_id: "lock_abc"
      file_path: "src/user.py"
      expires_at: "2024-01-01T12:30:00Z"
    - lock_id: "lock_def"
      file_path: "src/auth.py"
      expires_at: "2024-01-01T12:30:00Z"
```

## Event Bus Specifications

### Event Types

```python
@dataclass
class ParallelEvent:
    """Base class for parallel execution events"""
    event_id: str = field(default_factory=lambda: uuid.uuid4().hex)
    event_type: str = ""
    cycle_id: str = ""
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)

# Cycle lifecycle events
class CycleStartedEvent(ParallelEvent):
    event_type: str = "cycle.started"
    story_id: str = ""
    priority: int = 5

class CycleCompletedEvent(ParallelEvent):
    event_type: str = "cycle.completed"
    duration_seconds: float = 0.0
    success: bool = True

# Conflict events
class ConflictDetectedEvent(ParallelEvent):
    event_type: str = "conflict.detected"
    conflict: Conflict = None
    affected_cycles: List[str] = field(default_factory=list)

class ConflictResolvedEvent(ParallelEvent):
    event_type: str = "conflict.resolved"
    conflict_id: str = ""
    resolution_strategy: ResolutionStrategy = None
    
# Resource events
class AgentAcquiredEvent(ParallelEvent):
    event_type: str = "agent.acquired"
    agent_type: AgentType = None
    agent_id: str = ""
    
class ResourceExhaustedEvent(ParallelEvent):
    event_type: str = "resource.exhausted"
    resource_type: str = ""
    waiting_cycles: List[str] = field(default_factory=list)
```

### Event Subscriptions

```python
class EventSubscription:
    """Event subscription configuration"""
    
    def __init__(
        self,
        event_patterns: List[str],
        handler: Callable[[ParallelEvent], Awaitable[None]],
        filter_predicate: Optional[Callable[[ParallelEvent], bool]] = None
    ):
        self.event_patterns = event_patterns  # e.g., ["cycle.*", "conflict.detected"]
        self.handler = handler
        self.filter_predicate = filter_predicate
```

## Storage Specifications

### Parallel State Storage

```python
class ParallelStateStorage:
    """Storage interface for parallel execution state"""
    
    async def save_parallel_state(
        self,
        state: ParallelExecutionState
    ) -> None:
        """Save complete parallel execution state"""
        
    async def load_parallel_state(
        self,
        execution_id: str
    ) -> Optional[ParallelExecutionState]:
        """Load parallel execution state"""
        
    async def save_cycle_checkpoint(
        self,
        cycle_id: str,
        checkpoint: CycleCheckpoint
    ) -> None:
        """Save cycle checkpoint for recovery"""
        
    async def list_active_executions(
        self
    ) -> List[ParallelExecutionSummary]:
        """List all active parallel executions"""
```

### File Structure

```
.orch-state/
├── parallel/
│   ├── executions/
│   │   ├── {execution_id}/
│   │   │   ├── metadata.json
│   │   │   ├── cycles/
│   │   │   │   ├── {cycle_id}.json
│   │   │   │   └── ...
│   │   │   ├── conflicts/
│   │   │   │   ├── {conflict_id}.json
│   │   │   │   └── ...
│   │   │   └── metrics/
│   │   │       ├── throughput.json
│   │   │       ├── resource_usage.json
│   │   │       └── conflicts.json
│   │   └── ...
│   ├── locks/
│   │   ├── {file_path_hash}.lock
│   │   └── ...
│   ├── agent_pools/
│   │   ├── design_pool.json
│   │   ├── qa_pool.json
│   │   ├── code_pool.json
│   │   └── ...
│   └── checkpoints/
│       ├── {cycle_id}/
│       │   ├── {timestamp}.json
│       │   └── ...
│       └── ...
```

## Performance Requirements

### Latency SLAs

| Operation | P50 | P95 | P99 | Max |
|-----------|-----|-----|-----|-----|
| Acquire Agent | 100ms | 500ms | 1s | 30s |
| Acquire Lock | 50ms | 200ms | 500ms | 10s |
| Conflict Detection | 200ms | 1s | 2s | 5s |
| Context Creation | 500ms | 2s | 5s | 10s |
| State Checkpoint | 100ms | 500ms | 1s | 5s |

### Throughput Requirements

| Metric | Target | Peak |
|--------|--------|------|
| Concurrent Cycles | 5 | 10 |
| Cycles/Hour | 20 | 50 |
| Conflicts/Hour (resolved) | 10 | 25 |
| Agent Requests/Minute | 100 | 250 |

### Resource Limits

| Resource | Per Cycle | Total System |
|----------|-----------|--------------|
| Memory | 2GB | 20GB |
| CPU Cores | 1.0 | 10.0 |
| Token Budget | 50k | 200k |
| File Locks | 20 | 200 |
| Test Environments | 1 | 5 |

## Error Handling

### Error Codes

```python
class ParallelErrorCode(Enum):
    # Resource errors (1xxx)
    RESOURCE_EXHAUSTED = 1001
    AGENT_POOL_EMPTY = 1002
    TOKEN_BUDGET_EXCEEDED = 1003
    
    # Lock errors (2xxx)
    LOCK_TIMEOUT = 2001
    DEADLOCK_DETECTED = 2002
    LOCK_EXPIRED = 2003
    
    # Conflict errors (3xxx)
    CONFLICT_UNRESOLVABLE = 3001
    MERGE_FAILED = 3002
    DEPENDENCY_CYCLE = 3003
    
    # System errors (4xxx)
    CHECKPOINT_FAILED = 4001
    STATE_CORRUPTED = 4002
    COMMUNICATION_ERROR = 4003
```

### Error Recovery

```python
@dataclass
class ErrorRecovery:
    """Error recovery configuration"""
    error_code: ParallelErrorCode
    max_retries: int = 3
    backoff_strategy: BackoffStrategy = BackoffStrategy.EXPONENTIAL
    fallback_action: FallbackAction = FallbackAction.ABORT_CYCLE
    alert_threshold: int = 2  # Alert after N occurrences
```

## Monitoring Metrics

### Key Performance Indicators

```python
@dataclass
class ParallelKPIs:
    """Key performance indicators for parallel execution"""
    
    # Throughput metrics
    cycles_started_per_hour: float
    cycles_completed_per_hour: float
    stories_completed_per_hour: float
    
    # Efficiency metrics
    average_parallelism: float  # Avg concurrent cycles
    resource_utilization: float  # 0-1
    conflict_rate: float  # Conflicts per cycle
    
    # Quality metrics
    auto_resolve_rate: float  # Auto-resolved conflicts
    test_pass_rate: float
    rollback_rate: float  # Cycles rolled back
    
    # Performance metrics
    average_cycle_time: timedelta
    average_wait_time: timedelta
    average_conflict_resolution_time: timedelta
```

### Alerting Rules

```yaml
alerts:
  - name: "High Conflict Rate"
    condition: "conflict_rate > 0.3"
    severity: "warning"
    action: "reduce_parallelism"
    
  - name: "Resource Exhaustion"
    condition: "resource_utilization > 0.95"
    severity: "critical"
    action: "scale_resources"
    
  - name: "Lock Timeout Storm"
    condition: "lock_timeouts_per_minute > 10"
    severity: "critical"
    action: "investigate_deadlock"
```

## Security Considerations

### Access Control

```python
class ParallelAccessControl:
    """Access control for parallel operations"""
    
    async def can_start_cycle(
        self,
        user_id: str,
        story: Story
    ) -> bool:
        """Check if user can start parallel cycle"""
        
    async def can_resolve_conflict(
        self,
        user_id: str,
        conflict: Conflict
    ) -> bool:
        """Check if user can resolve conflict"""
        
    async def can_abort_cycle(
        self,
        user_id: str,
        cycle_id: str
    ) -> bool:
        """Check if user can abort cycle"""
```

### Audit Trail

```python
@dataclass
class ParallelAuditEntry:
    """Audit entry for parallel operations"""
    timestamp: datetime
    user_id: str
    action: str  # "start_cycle", "resolve_conflict", etc.
    cycle_id: Optional[str]
    details: Dict[str, Any]
    ip_address: str
    success: bool
```

## Migration Guide

### From Sequential to Parallel

1. **Enable Feature Flag**
   ```python
   config.features.parallel_tdd_enabled = True
   config.parallel.max_cycles = 2  # Start conservative
   ```

2. **Configure Resource Pools**
   ```python
   config.agent_pools = {
       AgentType.DESIGN: {"min": 1, "max": 3},
       AgentType.QA: {"min": 1, "max": 3},
       AgentType.CODE: {"min": 2, "max": 5}
   }
   ```

3. **Set Conflict Policies**
   ```python
   config.conflict_resolution = {
       ConflictType.FILE_OVERLAP: ResolutionStrategy.AUTO_MERGE,
       ConflictType.TEST_COLLISION: ResolutionStrategy.SEQUENTIAL,
       ConflictType.DEPENDENCY_CONFLICT: ResolutionStrategy.MANUAL
   }
   ```

4. **Monitor and Tune**
   - Monitor conflict rates
   - Adjust parallelism level
   - Tune resource allocation
   - Enable advanced features gradually

This technical specification provides the complete blueprint for implementing the Parallel TDD Execution system with all necessary APIs, protocols, and integration points defined.