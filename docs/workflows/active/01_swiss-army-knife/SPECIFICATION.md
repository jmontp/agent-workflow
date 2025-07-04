# Swiss Army Knife Workflow Specification

---
workflow:
  name: "Swiss Army Knife"
  version: "1.0"
  status: "active"
  complexity: "simple"
  agents_required: 
    - SwissArmyAgent
    - ContextManager
  typical_duration: "5-30 minutes"
  max_duration: "2 hours"
  success_rate_target: "80%"
  compliance_level: "basic"
  created_date: "2024-01-20"
  last_updated: "2024-01-20"
  authors:
    - "Agent Workflow Team"
---

## Overview

The Swiss Army Knife workflow is a simple, single-agent pattern designed for rapid task execution with Context Manager support. It embodies the philosophy that for many tasks, one capable general-purpose agent is more efficient than coordinating multiple specialized agents.

## Philosophy

> "A Swiss Army knife may not be the perfect tool for any single job, but it's good enough for most jobs and always available."

This workflow prioritizes:
- **Speed**: Get results quickly
- **Simplicity**: Minimal coordination overhead
- **Learning**: Every execution improves future performance
- **Flexibility**: Handle diverse task types

## When to Use

### Ideal For:
- **Prototyping**: Quick proof-of-concepts
- **Bug Fixes**: Simple code corrections
- **Documentation**: Writing or updating docs
- **Code Generation**: Functions under 200 lines
- **Research Queries**: Finding information or patterns
- **Refactoring**: Small, localized improvements
- **Testing**: Writing unit tests for existing code

### When NOT to Use:
- **Mission-Critical Code**: Use Scrum-TDD or FDA-Compliant workflows
- **Complex Architecture**: Multi-agent review needed
- **Large Refactoring**: Changes spanning many files
- **Security Features**: Requires specialized security workflow
- **Performance Optimization**: Needs profiling and benchmarking
- **Integration Work**: Complex system interactions

## Agent Roles

### 1. Swiss Army Agent
**Responsibility**: Execute all task-related activities
- Parse and understand requests
- Query Context Manager for relevant patterns
- Generate solutions based on context
- Execute implementation
- Format results for human review

**Capabilities Required**:
- Natural language understanding
- Code generation
- Pattern matching
- Basic reasoning
- Error handling

### 2. Context Manager
**Responsibility**: Provide memory and learning
- Store all requests and results
- Identify relevant patterns
- Track success/failure rates
- Suggest improvements
- Maintain audit trail

**Capabilities Required**:
- Fast search (<2 seconds)
- Pattern detection
- Context ranking
- Storage management

### 3. Human Operator
**Responsibility**: Initiate and review
- Submit clear task requests
- Review generated results
- Approve or reject outputs
- Provide feedback for learning

## Success Criteria

### Quantitative Metrics:
- **First-Attempt Success Rate**: >80%
- **Average Completion Time**: <15 minutes
- **Context Utilization**: >60% of suggestions applied
- **Human Approval Rate**: >75%

### Qualitative Metrics:
- Generated code follows project conventions
- Documentation is clear and complete
- Solutions are maintainable
- Patterns improve over time

## Workflow States

See [STATE_MACHINE.md](STATE_MACHINE.md) for detailed state definitions.

### Summary:
1. **IDLE**: Waiting for request
2. **REQUEST_RECEIVED**: Processing input
3. **CONTEXT_SEARCH**: Finding relevant patterns
4. **EXECUTING**: Performing task
5. **CONTEXT_UPDATE**: Storing results
6. **HUMAN_REVIEW**: Awaiting approval

## Context Manager Integration

### Critical Integration Points:

1. **During REQUEST_RECEIVED**:
   - Log the incoming request
   - Tag with metadata (type, estimated complexity)
   - Check for exact matches to previous requests

2. **During CONTEXT_SEARCH**:
   - Query for similar successful patterns
   - Retrieve relevant code examples
   - Get learned best practices
   - Time limit: 5 seconds

3. **During EXECUTING**:
   - Stream progress updates
   - Log decision points
   - Track resources used

4. **During CONTEXT_UPDATE**:
   - Store complete execution context
   - Update pattern confidence scores
   - Link to related contexts
   - Flag new patterns for analysis

## Error Handling

### Common Failure Modes:

1. **Ambiguous Request**
   - Detection: Low confidence parse
   - Response: Ask for clarification
   - State: Return to IDLE

2. **No Relevant Context**
   - Detection: Empty search results
   - Response: Proceed with general knowledge
   - State: Continue with warning

3. **Execution Timeout**
   - Detection: >10 minutes in EXECUTING
   - Response: Return partial results
   - State: Force to CONTEXT_UPDATE

4. **Context Manager Unavailable**
   - Detection: Connection timeout
   - Response: Proceed without context
   - State: Skip to EXECUTING

## Performance Expectations

### State Transition Times:

| Transition | Typical | Maximum | Action on Timeout |
|------------|---------|---------|-------------------|
| IDLE → REQUEST_RECEIVED | <1s | 5s | Retry once |
| REQUEST_RECEIVED → CONTEXT_SEARCH | <1s | 5s | Skip context |
| CONTEXT_SEARCH → EXECUTING | 1-5s | 30s | Proceed anyway |
| EXECUTING → CONTEXT_UPDATE | <30s | 10min | Force complete |
| CONTEXT_UPDATE → HUMAN_REVIEW | <2s | 10s | Log error |
| HUMAN_REVIEW → IDLE | User dependent | ∞ | N/A |

## Compliance Considerations

### Basic Compliance Features:
- All state transitions logged
- Request/response pairs archived
- Execution time tracked
- Resource usage monitored
- Human reviews recorded

### Data Retention:
- Active contexts: 30 days
- Archived contexts: 1 year
- Audit logs: 7 years
- Patterns: Indefinite

## Evolution Path

### Near-term Improvements (v1.1):
- Parallel context search
- Preliminary result preview
- Confidence scoring
- Request templates

### Medium-term Enhancements (v1.5):
- Multi-turn clarification
- Incremental execution
- Rollback capability
- A/B testing patterns

### Long-term Vision (v2.0):
- Multiple Swiss Army agents
- Specialized sub-workflows
- Autonomous improvement
- Pattern marketplace

## Monitoring and Alerts

### Key Metrics to Track:
- Requests per hour
- Success rate (rolling 24h)
- Average completion time
- Context cache hit rate
- Pattern effectiveness

### Alert Thresholds:
- Success rate <70%: Warning
- Success rate <60%: Critical
- Avg time >30min: Warning
- Context Manager latency >5s: Warning

---

*The Swiss Army Knife workflow represents our commitment to pragmatic, effective solutions. It may not be perfect, but it ships.*