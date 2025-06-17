# C4 Container Diagram - AI Agent TDD-Scrum Workflow

## Container Architecture

```mermaid
C4Container
    title Container Diagram - AI Agent Workflow System

    Person(user, "Product Owner", "Solo developer")
    
    System_Boundary(system, "AI Agent Workflow System") {
        Container(discord_bot, "Discord Bot", "Python, discord.py", "Command interface, state visualization, notifications")
        Container(orchestrator, "Orchestrator", "Python, asyncio", "Central coordination, state machine, project management")
        Container(agent_lib, "Agent Library", "Python, anthropic", "Specialized AI agents (Design, Code, Data, QA)")
        Container(state_store, "State Store", "JSON files", "Project state, task queues, approval gates")
        Container(config, "Configuration", "YAML", "Project definitions, orchestration modes")
    }
    
    System_Ext(discord_api, "Discord API", "Real-time messaging platform")
    System_Ext(github_api, "GitHub API", "Repository and CI/CD integration")
    System_Ext(anthropic_api, "Anthropic API", "Claude AI models")
    
    Rel(user, discord_api, "Slash commands, interactions")
    Rel(discord_api, discord_bot, "Webhook events, API calls")
    Rel(discord_bot, orchestrator, "Command dispatch, state queries")
    Rel(orchestrator, agent_lib, "Task execution requests")
    Rel(orchestrator, state_store, "Read/write project state")
    Rel(orchestrator, config, "Load project definitions")
    Rel(agent_lib, anthropic_api, "AI model requests")
    Rel(agent_lib, github_api, "Code commits, PR creation")
```

## Container Responsibilities

### Discord Bot
- Parse and validate slash commands
- Implement interactive state visualization
- Send notifications and approval requests
- Handle user interactions and buttons

### Orchestrator
- Enforce state machine transitions
- Coordinate multi-agent workflows
- Implement HITL approval gates
- Manage project lifecycle

### Agent Library
- Specialized agent implementations
- Anthropic API integration
- Code generation and testing
- GitHub operations

### State Store
- Persist workflow state across restarts
- Track task queues and approvals
- Maintain project status

### Configuration
- Define project orchestration modes
- Configure agent behaviors
- Set approval thresholds