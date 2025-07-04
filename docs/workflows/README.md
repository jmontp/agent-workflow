# Workflow Documentation

This directory contains specifications for different execution workflows in the agent-workflow system. Each workflow defines a specific pattern for how agents, humans, and the Context Manager collaborate to complete tasks.

## What is a Workflow?

A workflow is a documented pattern that defines:
- **State Machine**: The states and transitions for task execution
- **Agent Roles**: Which agents participate and their responsibilities
- **Context Flow**: How information moves through the system
- **Use Cases**: When to use this workflow pattern
- **Performance Expectations**: Realistic timings and success criteria

## Workflow Selection Guide

Choose the appropriate workflow based on your task:

| Task Type | Complexity | Time Budget | Recommended Workflow | Success Rate |
|-----------|------------|-------------|---------------------|--------------|
| Quick fixes, queries | Simple | <30 min | [Swiss Army Knife](active/01_swiss-army-knife/) | 80%+ |
| Feature development | Medium | 1-4 hours | Scrum-TDD (coming soon) | 85%+ |
| System design | Complex | Days | Multi-Agent Review (planned) | 90%+ |
| Medical device features | Critical | Weeks | FDA-Compliant (future) | 95%+ |

## Currently Available Workflows

### 1. Swiss Army Knife (Active)
- **Purpose**: Rapid task execution with a single general-purpose agent
- **Best For**: Prototypes, bug fixes, documentation, simple features
- **States**: IDLE → REQUEST → SEARCH → EXECUTE → UPDATE → REVIEW
- **Duration**: 5-30 minutes typically
- [Full Documentation](active/01_swiss-army-knife/)

### 2. Scrum-TDD (Coming Soon)
- **Purpose**: Structured development with test-driven approach
- **Best For**: Production features, complex logic, team development
- **States**: BACKLOG → SPRINT → TDD cycle → REVIEW
- **Duration**: 1-4 hours typically

## How Workflows Evolve

1. **Experimental**: New patterns tested in isolation
2. **Active**: Proven patterns in production use
3. **Archived**: Historical versions kept for reference

## Workflow Principles

1. **Start Simple**: Use the simplest workflow that meets your needs
2. **Learn and Adapt**: Context Manager tracks success rates
3. **Document Everything**: Every state change is logged
4. **Fail Gracefully**: All workflows include error recovery
5. **Human in the Loop**: Final approval always with humans

## Creating New Workflows

See [WORKFLOW_STANDARD.md](WORKFLOW_STANDARD.md) for documentation guidelines.

## Integration with Context Manager

The Context Manager plays a crucial role in all workflows:
- **Pattern Recognition**: Suggests optimal workflows based on request
- **Knowledge Base**: Provides relevant context during execution
- **Learning**: Improves workflow selection over time
- **Audit Trail**: Maintains compliance records

## Quick Start

1. **Identify Your Task**: What are you trying to accomplish?
2. **Check Time Budget**: How long can this take?
3. **Select Workflow**: Use the table above
4. **Follow the Guide**: Each workflow has detailed instructions
5. **Review Results**: Approve or iterate

## Future Workflows

We're planning these advanced patterns:
- **Parallel Execution**: Multiple agents working simultaneously
- **Hierarchical Review**: Multi-level approval chains
- **Autonomous Chains**: Self-directing agent sequences
- **Hybrid Patterns**: Combining multiple workflows

## Metrics and Success

Each workflow tracks:
- **Completion Rate**: How often tasks finish successfully
- **Time to Complete**: Average duration
- **Human Satisfaction**: Approval/rejection rates
- **Context Utilization**: How well previous learnings are applied

---

*Remember: The best workflow is the one that gets the job done reliably. Start simple, measure results, and evolve based on data.*