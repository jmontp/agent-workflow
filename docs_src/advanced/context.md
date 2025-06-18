# C4 Context Diagram - AI Agent TDD-Scrum Workflow

## System Context

The system context shows how the dual state machine architecture integrates with external systems to support both workflow management and Test-Driven Development cycles.

```mermaid
C4Context
    title System Context - AI Agent TDD-Scrum Workflow (Dual State Machine)

    Person(user, "Product Owner/Engineer", "Solo developer using AI agents for TDD-enhanced software development")
    
    System_Boundary(system, "AI Agent Workflow System") {
        System(orchestrator, "Agent Orchestrator", "Coordinates AI agents through dual state machines (Workflow + TDD)")
    }
    
    System_Ext(discord, "Discord", "Primary interface for workflow and TDD command interaction")
    System_Ext(github, "GitHub", "Source code repository, test preservation, and CI/CD")
    System_Ext(anthropic, "Anthropic API", "AI agent capabilities for TDD phases")
    System_Ext(ci_system, "CI/CD System", "Test execution, coverage reporting, and quality gates")
    
    Rel(user, discord, "Issues workflow/TDD commands, approves tasks")
    Rel(discord, orchestrator, "Dual command execution, TDD notifications")
    Rel(orchestrator, github, "Code changes, test commits, PR management")
    Rel(orchestrator, anthropic, "Agent task execution with TDD context")
    Rel(orchestrator, ci_system, "Test execution, coverage validation")
    Rel(github, user, "Code review, TDD cycle feedback")
    Rel(ci_system, user, "Test results, coverage reports")
    Rel(github, ci_system, "Test file integration, CI triggers")
```

## Key Interactions

1. **User → Discord**: Issues workflow and TDD slash commands (`/epic`, `/sprint`, `/tdd test`, `/tdd code`, `/approve`)
2. **Discord → Orchestrator**: Dual command parsing and state transitions (workflow + TDD)
3. **Orchestrator → Agents**: Task dispatch with TDD phase coordination
4. **Agents → GitHub**: Code implementation, test preservation, and PR creation
5. **Agents → CI System**: Test execution, coverage validation, and quality gates
6. **GitHub → User**: CI results, TDD cycle progress, and code review
7. **CI System → User**: Test results, coverage reports, and TDD metrics
8. **User Approval Loop**: HITL gates for strategic workflow and TDD decisions
9. **Test Preservation Flow**: TDD test files committed and preserved through development cycle
10. **Dual State Coordination**: Workflow and TDD state machines synchronized for sprint completion