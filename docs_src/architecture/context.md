# C4 Context Diagram - AI Agent TDD-Scrum Workflow

## System Context

```mermaid
C4Context
    title System Context - AI Agent TDD-Scrum Workflow

    Person(user, "Product Owner/Engineer", "Solo developer using AI agents for software development")
    
    System_Boundary(system, "AI Agent Workflow System") {
        System(orchestrator, "Agent Orchestrator", "Coordinates multiple AI agents through HITL workflow")
    }
    
    System_Ext(discord, "Discord", "Primary interface for human interaction and approval")
    System_Ext(github, "GitHub", "Source code repository and CI/CD")
    System_Ext(anthropic, "Anthropic API", "AI agent capabilities")
    
    Rel(user, discord, "Issues commands, approves tasks")
    Rel(discord, orchestrator, "Command execution, notifications")
    Rel(orchestrator, github, "Code changes, PR management")
    Rel(orchestrator, anthropic, "Agent task execution")
    Rel(github, user, "Code review, CI feedback")
```

## Key Interactions

1. **User → Discord**: Issues slash commands (`/epic`, `/sprint`, `/approve`)
2. **Discord → Orchestrator**: Command parsing and state transitions
3. **Orchestrator → Agents**: Task dispatch and coordination
4. **Agents → GitHub**: Code implementation and PR creation
5. **GitHub → User**: CI results and code review
6. **User Approval Loop**: HITL gates for strategic decisions