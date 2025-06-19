# Component Architecture

This document provides detailed technical architecture for each major component in the AI Agent TDD-Scrum Workflow system, including class diagrams, sequence diagrams, and implementation patterns.

## State Machine Components

### Workflow State Machine Architecture

The workflow state machine manages the high-level Scrum process with sophisticated state management:

```mermaid
stateDiagram-v2
    [*] --> IDLE: System Start
    
    IDLE --> BACKLOG_READY: /epic created
    BACKLOG_READY --> SPRINT_PLANNED: /sprint plan
    SPRINT_PLANNED --> SPRINT_ACTIVE: /sprint start
    SPRINT_ACTIVE --> SPRINT_REVIEW: All stories complete
    SPRINT_REVIEW --> BACKLOG_READY: /sprint complete
    
    SPRINT_ACTIVE --> SPRINT_ACTIVE: Story TDD cycles
    
    state SPRINT_ACTIVE {
        [*] --> Orchestrating
        Orchestrating --> ParallelTDD: Assign stories
        ParallelTDD --> Monitoring: Track progress
        Monitoring --> Orchestrating: Next story
        
        state ParallelTDD {
            [*] --> StoryA
            [*] --> StoryB
            [*] --> StoryC
            
            state StoryA {
                [*] --> Design_A
                Design_A --> Test_A
                Test_A --> Code_A
                Code_A --> Refactor_A
                Refactor_A --> [*]
            }
        }
    }
    
    IDLE --> IDLE: Invalid commands
    BACKLOG_READY --> BACKLOG_READY: /backlog operations
    SPRINT_PLANNED --> SPRINT_PLANNED: /sprint adjust
    SPRINT_REVIEW --> SPRINT_REVIEW: /review operations
```

### TDD State Machine Implementation

Detailed implementation of the TDD state machine with error handling:

```mermaid
classDiagram
    class TDDStateMachine {
        -story_id: str
        -current_phase: TDDPhase
        -agents: Dict[str, BaseAgent]
        -test_results: TestResults
        -retry_count: int
        -max_retries: int = 3
        
        +__init__(story_id: str, story: Story)
        +start(): void
        +transition(): bool
        +get_current_agent(): BaseAgent
        +handle_failure(): void
        +can_proceed(): bool
        +get_progress(): float
    }
    
    class TDDPhase {
        <<enumeration>>
        DESIGN
        TEST_RED
        CODE_GREEN
        REFACTOR
        COMMIT
        FAILED
        COMPLETED
    }
    
    class TestResults {
        -total_tests: int
        -passed_tests: int
        -failed_tests: int
        -coverage: float
        -error_messages: List[str]
        
        +all_passed(): bool
        +get_failure_summary(): str
        +meets_coverage_threshold(): bool
    }
    
    class PhaseTransition {
        -from_phase: TDDPhase
        -to_phase: TDDPhase
        -condition: Callable
        -on_transition: Callable
        
        +can_transition(): bool
        +execute(): void
    }
    
    class TDDCoordinator {
        -active_machines: Dict[str, TDDStateMachine]
        -story_queue: Queue[Story]
        -max_parallel: int
        -resource_monitor: ResourceMonitor
        
        +add_story(story: Story): void
        +start_next(): void
        +handle_completion(story_id: str): void
        +get_active_count(): int
        +can_start_new(): bool
    }
    
    TDDStateMachine --> TDDPhase
    TDDStateMachine --> TestResults
    TDDStateMachine --> PhaseTransition
    TDDCoordinator --> TDDStateMachine
    PhaseTransition --> TDDPhase
```

## Agent System Architecture

### Agent Hierarchy and Specialization

```mermaid
classDiagram
    class BaseAgent {
        <<abstract>>
        -agent_id: str
        -agent_type: str
        -context_manager: ContextManager
        -security_profile: SecurityProfile
        -metrics: AgentMetrics
        
        +run(task: Task, dry_run: bool): Result
        +validate_access(operation: str): bool
        +get_context(): Context
        +report_metrics(): Dict
        #execute_task(task: Task): Result
        #prepare_context(task: Task): Context
    }
    
    class OrchestatorAgent {
        -workflow_state: WorkflowStateMachine
        -tdd_coordinator: TDDCoordinator
        -approval_queue: Queue[Approval]
        
        +coordinate_sprint(sprint: Sprint): void
        +assign_stories(stories: List[Story]): void
        +handle_approval(approval: Approval): void
        +monitor_progress(): Dict
    }
    
    class DesignAgent {
        -design_patterns: Dict[str, Pattern]
        -architecture_knowledge: KnowledgeBase
        
        +create_design(story: Story): Design
        +review_architecture(): ArchReview
        +suggest_patterns(): List[Pattern]
        +generate_specs(): TechnicalSpec
    }
    
    class CodeAgent {
        -language_models: Dict[str, LanguageModel]
        -code_analyzer: CodeAnalyzer
        
        +implement_feature(spec: TechnicalSpec): Code
        +fix_test_failures(failures: List[TestFailure]): Code
        +refactor_code(code: Code, metrics: CodeMetrics): Code
        +commit_changes(message: str): CommitResult
    }
    
    class QAAgent {
        -test_frameworks: Dict[str, TestFramework]
        -coverage_analyzer: CoverageAnalyzer
        
        +write_tests(spec: TechnicalSpec): TestSuite
        +run_tests(test_suite: TestSuite): TestResults
        +analyze_coverage(): CoverageReport
        +suggest_edge_cases(): List[TestCase]
    }
    
    class DataAgent {
        -analysis_tools: Dict[str, AnalysisTool]
        -visualization: VisualizationEngine
        
        +analyze_metrics(data: MetricsData): Analysis
        +generate_reports(): List[Report]
        +create_dashboards(): Dashboard
        +predict_trends(): Predictions
    }
    
    BaseAgent <|-- OrchestatorAgent
    BaseAgent <|-- DesignAgent
    BaseAgent <|-- CodeAgent
    BaseAgent <|-- QAAgent
    BaseAgent <|-- DataAgent
    
    BaseAgent --> ContextManager
    BaseAgent --> SecurityProfile
    BaseAgent --> AgentMetrics
```

### Agent Lifecycle Sequence

```mermaid
sequenceDiagram
    participant Orchestrator
    participant AgentFactory
    participant SecurityController
    participant Agent
    participant ContextManager
    participant Task
    
    Orchestrator->>AgentFactory: create_agent(type, task)
    AgentFactory->>SecurityController: get_security_profile(type)
    SecurityController-->>AgentFactory: SecurityProfile
    
    AgentFactory->>Agent: new Agent(profile)
    AgentFactory-->>Orchestrator: Agent instance
    
    Orchestrator->>Agent: run(task)
    Agent->>ContextManager: prepare_context(task)
    ContextManager->>ContextManager: load relevant files
    ContextManager->>ContextManager: compress context
    ContextManager-->>Agent: Context
    
    Agent->>Agent: validate_access(task.operations)
    Agent->>Task: execute()
    Task-->>Agent: Result
    
    Agent->>ContextManager: update_context(result)
    Agent-->>Orchestrator: TaskResult
    
    Orchestrator->>Agent: shutdown()
    Agent->>ContextManager: persist_memory()
    Agent->>Agent: cleanup_resources()
```

## Context Management System

### Context Architecture

```mermaid
graph TB
    subgraph "Context Management System"
        subgraph "Input Processing"
            CI[Context Indexer<br/>File analysis]
            CF[Context Filter<br/>Relevance scoring]
            TC[Token Calculator<br/>Size optimization]
        end
        
        subgraph "Storage Layer"
            CC[Context Cache<br/>LRU Cache]
            CM[Context Memory<br/>Persistent store]
            CDB[Context Database<br/>Relationships]
        end
        
        subgraph "Optimization"
            Comp[Context Compressor<br/>Semantic compression]
            Chunk[Context Chunker<br/>Smart splitting]
            Prio[Priority Manager<br/>Importance ranking]
        end
        
        subgraph "Output"
            Builder[Context Builder<br/>Agent-specific views]
            Validator[Context Validator<br/>Completeness check]
        end
    end
    
    CI --> CF
    CF --> TC
    TC --> Comp
    
    Comp --> CC
    CC --> CM
    CM --> CDB
    
    CC --> Chunk
    Chunk --> Prio
    Prio --> Builder
    Builder --> Validator
    
    style CI fill:#4dabf7,stroke:#1971c2,stroke-width:2px
    style CC fill:#51cf66,stroke:#37b24d,stroke-width:2px
    style Builder fill:#ff6b6b,stroke:#c92a2a,stroke-width:2px
```

### Context Flow Implementation

```mermaid
classDiagram
    class ContextManager {
        -indexer: ContextIndexer
        -filter: ContextFilter
        -cache: ContextCache
        -compressor: ContextCompressor
        -token_calc: TokenCalculator
        
        +prepare_context(task: Task, agent_type: str): Context
        +update_context(result: Result): void
        +get_relevant_files(query: str): List[File]
        +estimate_tokens(context: Context): int
        +optimize_for_window(context: Context, limit: int): Context
    }
    
    class ContextIndexer {
        -file_index: Dict[str, FileMetadata]
        -symbol_index: Dict[str, List[Reference]]
        -dependency_graph: Graph
        
        +index_file(path: str): void
        +find_references(symbol: str): List[Reference]
        +get_dependencies(file: str): List[str]
        +search(query: str): List[Match]
    }
    
    class ContextFilter {
        -relevance_model: RelevanceModel
        -importance_scores: Dict[str, float]
        
        +filter_files(files: List[File], task: Task): List[File]
        +score_relevance(file: File, task: Task): float
        +apply_thresholds(scores: Dict): List[File]
    }
    
    class ContextCache {
        -cache: LRUCache
        -hit_rate: float
        -miss_handler: Callable
        
        +get(key: str): Optional[Context]
        +put(key: str, context: Context): void
        +invalidate(pattern: str): void
        +get_stats(): CacheStats
    }
    
    class ContextCompressor {
        -compression_strategies: List[Strategy]
        -quality_threshold: float
        
        +compress(context: Context): CompressedContext
        +decompress(compressed: CompressedContext): Context
        +estimate_quality_loss(context: Context): float
    }
    
    class TokenCalculator {
        -encoding: tiktoken.Encoding
        -model_limits: Dict[str, int]
        
        +count_tokens(text: str): int
        +estimate_context_size(context: Context): int
        +fits_in_window(context: Context, model: str): bool
        +suggest_truncation(context: Context, limit: int): Context
    }
    
    ContextManager --> ContextIndexer
    ContextManager --> ContextFilter
    ContextManager --> ContextCache
    ContextManager --> ContextCompressor
    ContextManager --> TokenCalculator
```

## Resource Management Architecture

### Resource Scheduler Design

```mermaid
graph TB
    subgraph "Resource Scheduler"
        subgraph "Resource Monitoring"
            CPU[CPU Monitor<br/>Usage tracking]
            Memory[Memory Monitor<br/>Allocation tracking]
            Agents[Agent Monitor<br/>Active count]
        end
        
        subgraph "Scheduling Algorithm"
            Queue[Priority Queue<br/>Task ordering]
            Allocator[Resource Allocator<br/>Agent assignment]
            Balancer[Load Balancer<br/>Distribution logic]
        end
        
        subgraph "Constraints"
            Limits[Resource Limits<br/>Max thresholds]
            Priorities[Task Priorities<br/>Importance weights]
            Fairness[Fairness Policy<br/>Project balance]
        end
        
        subgraph "Optimization"
            Predictor[Load Predictor<br/>ML-based forecast]
            Optimizer[Schedule Optimizer<br/>Efficiency tuning]
        end
    end
    
    CPU --> Queue
    Memory --> Queue
    Agents --> Queue
    
    Queue --> Allocator
    Allocator --> Balancer
    
    Limits --> Allocator
    Priorities --> Queue
    Fairness --> Balancer
    
    Balancer --> Predictor
    Predictor --> Optimizer
    Optimizer --> Queue
    
    style Queue fill:#ff6b6b,stroke:#c92a2a,stroke-width:2px
    style Allocator fill:#4dabf7,stroke:#1971c2,stroke-width:2px
    style Optimizer fill:#51cf66,stroke:#37b24d,stroke-width:2px
```

### Resource Allocation Algorithm

```python
class ResourceScheduler:
    def __init__(self):
        self.resource_pool = ResourcePool()
        self.task_queue = PriorityQueue()
        self.allocation_policy = AllocationPolicy()
        
    def schedule_task(self, task: Task) -> Optional[Allocation]:
        """Main scheduling algorithm"""
        # 1. Check resource availability
        available = self.resource_pool.get_available_resources()
        required = self.estimate_resources(task)
        
        if not self.can_allocate(available, required):
            # 2. Try to preempt lower priority tasks
            if self.allocation_policy.allows_preemption:
                freed = self.preempt_tasks(required, task.priority)
                if freed >= required:
                    return self.allocate(task, required)
            
            # 3. Queue the task
            self.task_queue.put(task, priority=task.priority)
            return None
            
        # 4. Direct allocation
        return self.allocate(task, required)
        
    def allocate(self, task: Task, resources: Resources) -> Allocation:
        """Allocate resources to task"""
        allocation = Allocation(
            task_id=task.id,
            cpu_cores=resources.cpu,
            memory_mb=resources.memory,
            agent_slots=resources.agents
        )
        
        self.resource_pool.reserve(allocation)
        self.start_monitoring(allocation)
        
        return allocation
```

## Security Architecture Components

### Security Layer Implementation

```mermaid
classDiagram
    class SecurityController {
        -profiles: Dict[str, SecurityProfile]
        -audit_log: AuditLogger
        -policy_engine: PolicyEngine
        
        +check_access(agent: Agent, operation: Operation): bool
        +get_profile(agent_type: str): SecurityProfile
        +log_access(agent: Agent, operation: Operation, result: bool): void
        +update_policies(policies: List[Policy]): void
    }
    
    class SecurityProfile {
        -agent_type: str
        -allowed_tools: List[str]
        -blocked_tools: List[str]
        -file_permissions: FilePermissions
        -network_access: NetworkPolicy
        
        +can_use_tool(tool: str): bool
        +can_access_file(path: str, mode: str): bool
        +can_make_request(url: str): bool
        +to_cli_flags(): Dict[str, List[str]]
    }
    
    class AuditLogger {
        -log_store: LogStore
        -encryption: Encryption
        -retention_policy: RetentionPolicy
        
        +log_action(entry: AuditEntry): void
        +query_logs(filter: LogFilter): List[AuditEntry]
        +export_compliance_report(): Report
        +rotate_logs(): void
    }
    
    class PolicyEngine {
        -rules: List[SecurityRule]
        -evaluator: RuleEvaluator
        
        +evaluate(context: SecurityContext): Decision
        +add_rule(rule: SecurityRule): void
        +validate_policies(): List[Violation]
    }
    
    class ToolAccessControl {
        -tool_registry: Dict[str, ToolDefinition]
        -access_matrix: AccessMatrix
        
        +check_tool_access(agent_type: str, tool: str): bool
        +get_allowed_tools(agent_type: str): List[str]
        +register_tool(tool: ToolDefinition): void
    }
    
    SecurityController --> SecurityProfile
    SecurityController --> AuditLogger
    SecurityController --> PolicyEngine
    SecurityProfile --> ToolAccessControl
    PolicyEngine --> SecurityRule
    AuditLogger --> AuditEntry
```

### Security Enforcement Flow

```mermaid
sequenceDiagram
    participant Agent
    participant SecurityController
    participant PolicyEngine
    participant ToolAccessControl
    participant AuditLogger
    participant ClaudeCLI
    
    Agent->>SecurityController: request_operation(op)
    SecurityController->>PolicyEngine: evaluate(agent, op)
    PolicyEngine->>PolicyEngine: check_rules()
    PolicyEngine-->>SecurityController: Decision
    
    alt Access Granted
        SecurityController->>ToolAccessControl: get_restrictions(agent.type)
        ToolAccessControl-->>SecurityController: tool_list
        SecurityController->>ClaudeCLI: execute_with_restrictions(op, tool_list)
        ClaudeCLI-->>SecurityController: result
        SecurityController->>AuditLogger: log_success(agent, op)
    else Access Denied
        SecurityController->>AuditLogger: log_denial(agent, op, reason)
        SecurityController-->>Agent: AccessDeniedError
    end
    
    AuditLogger->>AuditLogger: encrypt_and_store()
```

## Data Flow Architecture

### Complete System Data Flow

```mermaid
graph TB
    subgraph "User Input"
        Discord[Discord Commands]
        API[REST API]
    end
    
    subgraph "Command Processing"
        CmdParser[Command Parser<br/>Validation]
        Router[Request Router<br/>Project routing]
        Queue[Command Queue<br/>Priority handling]
    end
    
    subgraph "State Management"
        WSM[Workflow State Machine]
        TSM[TDD State Machines]
        StateStore[State Storage]
    end
    
    subgraph "Agent Orchestration"
        Orchestrator[Main Orchestrator]
        AgentFactory[Agent Factory]
        AgentPool[Agent Pool]
    end
    
    subgraph "Execution"
        Agents[Specialized Agents]
        Context[Context System]
        Security[Security Layer]
    end
    
    subgraph "Results"
        Results[Task Results]
        Metrics[Metrics Collection]
        Notifications[User Notifications]
    end
    
    subgraph "Storage"
        ProjectFiles[Project Files]
        StateFiles[State Files]
        Logs[Audit Logs]
    end
    
    Discord --> CmdParser
    API --> CmdParser
    CmdParser --> Router
    Router --> Queue
    
    Queue --> WSM
    WSM --> TSM
    WSM --> StateStore
    TSM --> StateStore
    
    WSM --> Orchestrator
    Orchestrator --> AgentFactory
    AgentFactory --> AgentPool
    AgentPool --> Agents
    
    Agents --> Context
    Agents --> Security
    Security --> Agents
    
    Agents --> Results
    Results --> Metrics
    Results --> Notifications
    
    Results --> ProjectFiles
    StateStore --> StateFiles
    Security --> Logs
    
    Notifications --> Discord
    
    style Discord fill:#7b68ee,stroke:#483d8b,stroke-width:2px
    style WSM fill:#ff6b6b,stroke:#c92a2a,stroke-width:2px
    style Agents fill:#4dabf7,stroke:#1971c2,stroke-width:2px
    style Results fill:#51cf66,stroke:#37b24d,stroke-width:2px
```

### Data Model Relationships

```mermaid
erDiagram
    PROJECT ||--o{ EPIC : contains
    EPIC ||--o{ STORY : contains
    PROJECT ||--o{ SPRINT : has
    SPRINT ||--o{ STORY : includes
    STORY ||--|| TDD_CYCLE : triggers
    TDD_CYCLE ||--o{ TDD_PHASE : contains
    TDD_PHASE ||--|| AGENT_TASK : creates
    AGENT_TASK ||--|| AGENT : assigned_to
    AGENT ||--o{ TOOL_ACCESS : has
    AGENT_TASK ||--|| RESULT : produces
    RESULT ||--o{ METRIC : generates
    
    PROJECT {
        string id PK
        string name
        string path
        json config
        timestamp created_at
    }
    
    EPIC {
        string id PK
        string project_id FK
        string description
        string status
        int priority
    }
    
    STORY {
        string id PK
        string epic_id FK
        string sprint_id FK
        string title
        string description
        int story_points
        string status
    }
    
    SPRINT {
        string id PK
        string project_id FK
        string name
        date start_date
        date end_date
        string status
    }
    
    TDD_CYCLE {
        string id PK
        string story_id FK
        string current_phase
        json phase_results
        timestamp started_at
    }
    
    AGENT {
        string id PK
        string type
        string status
        json metrics
    }
```

## Performance Optimization Architecture

### Caching Strategy

```mermaid
graph TB
    subgraph "Multi-Level Cache"
        subgraph "L1 - Memory Cache"
            HotData[Hot Data<br/>Frequent access]
            ActiveContext[Active Contexts<br/>Current tasks]
        end
        
        subgraph "L2 - Redis Cache"
            WarmData[Warm Data<br/>Recent access]
            SharedContext[Shared Contexts<br/>Cross-agent]
        end
        
        subgraph "L3 - File Cache"
            ColdData[Cold Data<br/>Historical]
            ArchivedContext[Archived Contexts<br/>Completed tasks]
        end
    end
    
    subgraph "Cache Management"
        CacheManager[Cache Manager<br/>Coordination]
        Eviction[Eviction Policy<br/>LRU/LFU]
        Preloader[Preloader<br/>Predictive loading]
    end
    
    Request[Cache Request] --> CacheManager
    CacheManager --> HotData
    HotData -.miss.-> WarmData
    WarmData -.miss.-> ColdData
    
    CacheManager --> Eviction
    CacheManager --> Preloader
    
    style HotData fill:#ff6b6b,stroke:#c92a2a,stroke-width:2px
    style WarmData fill:#ffd43b,stroke:#fab005,stroke-width:2px
    style ColdData fill:#4dabf7,stroke:#1971c2,stroke-width:2px
```

### Performance Monitoring

```mermaid
classDiagram
    class PerformanceMonitor {
        -metrics_collector: MetricsCollector
        -analyzers: List[PerformanceAnalyzer]
        -alert_manager: AlertManager
        
        +collect_metrics(): void
        +analyze_performance(): PerformanceReport
        +detect_anomalies(): List[Anomaly]
        +optimize_automatically(): void
    }
    
    class MetricsCollector {
        -counters: Dict[str, Counter]
        -gauges: Dict[str, Gauge]
        -histograms: Dict[str, Histogram]
        
        +increment(metric: str, value: float): void
        +record_duration(operation: str, duration: float): void
        +get_snapshot(): MetricsSnapshot
    }
    
    class PerformanceAnalyzer {
        <<interface>>
        +analyze(metrics: MetricsSnapshot): Analysis
        +suggest_optimizations(): List[Optimization]
    }
    
    class ResourceAnalyzer {
        +analyze_cpu_usage(): CPUAnalysis
        +analyze_memory_usage(): MemoryAnalysis
        +detect_leaks(): List[MemoryLeak]
    }
    
    class LatencyAnalyzer {
        +analyze_response_times(): LatencyAnalysis
        +identify_bottlenecks(): List[Bottleneck]
        +suggest_caching(): List[CacheCandidate]
    }
    
    class ThroughputAnalyzer {
        +analyze_task_completion(): ThroughputAnalysis
        +calculate_efficiency(): float
        +recommend_parallelism(): int
    }
    
    PerformanceMonitor --> MetricsCollector
    PerformanceMonitor --> PerformanceAnalyzer
    PerformanceAnalyzer <|-- ResourceAnalyzer
    PerformanceAnalyzer <|-- LatencyAnalyzer
    PerformanceAnalyzer <|-- ThroughputAnalyzer
```

## Error Handling and Recovery

### Error Handling Architecture

```mermaid
graph TB
    subgraph "Error Detection"
        Monitor[Error Monitor<br/>Detection]
        Classifier[Error Classifier<br/>Categorization]
        Severity[Severity Analyzer<br/>Impact assessment]
    end
    
    subgraph "Error Handling"
        Handler[Error Handler<br/>Routing]
        Retry[Retry Manager<br/>Automatic retry]
        Fallback[Fallback Strategy<br/>Alternative paths]
        Escalation[Escalation Manager<br/>Human intervention]
    end
    
    subgraph "Recovery"
        StateRecovery[State Recovery<br/>Rollback]
        DataRecovery[Data Recovery<br/>Consistency]
        AgentRecovery[Agent Recovery<br/>Restart]
    end
    
    subgraph "Learning"
        ErrorDB[Error Database<br/>Historical data]
        Pattern[Pattern Recognition<br/>Common failures]
        Prevention[Prevention Rules<br/>Proactive fixes]
    end
    
    Monitor --> Classifier
    Classifier --> Severity
    Severity --> Handler
    
    Handler --> Retry
    Handler --> Fallback
    Handler --> Escalation
    
    Retry --> StateRecovery
    Fallback --> DataRecovery
    Escalation --> AgentRecovery
    
    Handler --> ErrorDB
    ErrorDB --> Pattern
    Pattern --> Prevention
    Prevention --> Monitor
    
    style Monitor fill:#ff6b6b,stroke:#c92a2a,stroke-width:2px
    style Handler fill:#4dabf7,stroke:#1971c2,stroke-width:2px
    style StateRecovery fill:#51cf66,stroke:#37b24d,stroke-width:2px
```

### Recovery Sequence

```mermaid
sequenceDiagram
    participant System
    participant ErrorHandler
    participant StateManager
    participant RecoveryEngine
    participant HumanOperator
    
    System->>ErrorHandler: error_occurred(error)
    ErrorHandler->>ErrorHandler: classify_error()
    
    alt Transient Error
        ErrorHandler->>RecoveryEngine: attempt_retry(error)
        RecoveryEngine->>System: retry_operation()
        System-->>ErrorHandler: success
    else State Corruption
        ErrorHandler->>StateManager: get_last_valid_state()
        StateManager-->>ErrorHandler: checkpoint
        ErrorHandler->>RecoveryEngine: rollback_to(checkpoint)
        RecoveryEngine->>System: restore_state()
    else Critical Error
        ErrorHandler->>HumanOperator: escalate(error)
        HumanOperator->>RecoveryEngine: manual_intervention()
        RecoveryEngine->>System: apply_fix()
    end
    
    RecoveryEngine->>ErrorHandler: log_resolution()
```

## Summary

This component architecture document details:

1. **State Machines**: Dual state machine implementation with comprehensive state management
2. **Agent System**: Hierarchical agent architecture with specialized capabilities
3. **Context Management**: Sophisticated context optimization and caching
4. **Resource Scheduling**: Intelligent resource allocation and optimization
5. **Security Layers**: Multi-level security enforcement and audit
6. **Data Flow**: Complete system data flow and relationships
7. **Performance**: Caching strategies and monitoring systems
8. **Error Handling**: Comprehensive error detection and recovery

Each component is designed for:
- **Modularity**: Clear interfaces and separation of concerns
- **Scalability**: Horizontal and vertical scaling capabilities
- **Reliability**: Error handling and recovery mechanisms
- **Security**: Defense in depth with audit trails
- **Performance**: Optimization at every layer