# 🧠 Core Concepts

Understanding the fundamental concepts behind the AI Agent TDD-Scrum Workflow system.

## System Overview

The AI Agent TDD-Scrum Workflow system implements a sophisticated Human-In-The-Loop orchestration framework that coordinates multiple specialized AI agents through a Discord interface.

<div class="grid cards" markdown>

-   :material-sitemap:{ .lg .middle } **System Overview**

    ---
    
    High-level architecture and component interaction
    
    [:octicons-arrow-right-24: Overview](overview.md)

-   :material-security:{ .lg .middle } **Security Model**

    ---
    
    Agent access control and security boundaries
    
    [:octicons-arrow-right-24: Security](security.md)

</div>

## Key Concepts

### Dual State Machine Architecture

The system operates on two coordinated state machines:

1. **Primary Workflow State Machine**: Manages Scrum workflow (IDLE → BACKLOG → SPRINT → REVIEW)
2. **TDD State Machines**: One per story (DESIGN → TEST → CODE → REFACTOR)

### Ephemeral Agent System

Agents are created on-demand for optimal resource utilization:

- **Orchestrator Agent**: Temporary sprint coordination
- **Design Agents**: Per-story technical specifications
- **QA Agents**: Per-cycle test creation
- **Code Agents**: Per-cycle implementation
- **Analytics Agent**: Persistent cross-story metrics

### Human-In-The-Loop (HITL)

Strategic decision points require human approval:

- Epic definition and story prioritization
- Architecture decisions from Design agents
- Sprint planning and task assignment
- Quality gates and deployment decisions

### Context Management

Intelligent agent communication system:

- Memory-efficient context compression
- Cross-agent knowledge sharing
- Token optimization for large codebases
- Intelligent context switching

## Design Principles

### Test-Driven Development (TDD)

Strict enforcement of RED-GREEN-REFACTOR cycles:

1. **RED**: Write failing tests first
2. **GREEN**: Implement minimal code to pass tests
3. **REFACTOR**: Improve code while maintaining green tests

### Security by Design

Multi-layered security approach:

- Agent access control per tool type
- Project-level data isolation
- Audit logging for all actions
- Principle of least privilege

### Scalability

System designed for growth:

- Multi-project orchestration
- Resource scheduling and optimization
- Cross-project intelligence sharing
- Performance monitoring and tuning

## Understanding the System

To effectively use this system, it's helpful to understand:

1. **Workflow States**: How the system transitions between different phases
2. **Agent Capabilities**: What each agent type can and cannot do
3. **Security Boundaries**: How access control protects your projects
4. **TDD Integration**: How Test-Driven Development is enforced

## Next Steps

- **[System Overview](overview.md)** - Detailed architecture and components
- **[Security Model](security.md)** - Understanding access control and boundaries
- **[Architecture](../architecture/system-overview.md)** - Technical implementation details