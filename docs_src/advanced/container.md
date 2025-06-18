# C4 Container Diagram - AI Agent TDD-Scrum Workflow

## Container Architecture

The system implements a dual state machine architecture that coordinates workflow management with Test-Driven Development cycles through specialized containers.

```mermaid
C4Container
    title Container Diagram - AI Agent Workflow System (Dual State Machine)

    Person(user, "Product Owner", "Solo developer")
    
    System_Boundary(system, "AI Agent Workflow System") {
        Container(discord_bot, "Discord Bot", "Python, discord.py", "Command interface, dual state visualization, notifications")
        Container(orchestrator, "Orchestrator", "Python, asyncio", "Central coordination, dual state machines, project management")
        Container(workflow_sm, "Workflow State Machine", "Python", "Project lifecycle state management")
        Container(tdd_sm, "TDD State Machine", "Python", "Story-level TDD cycle management")
        Container(agent_lib, "Enhanced Agent Library", "Python, anthropic", "TDD-capable AI agents (Design, Code, Data, QA)")
        Container(state_store, "Workflow State Store", "JSON files", "Project state, task queues, approval gates")
        Container(tdd_store, "TDD State Store", "JSON files", "TDD cycles, tasks, test results, coverage")
        Container(test_artifacts, "Test Artifacts", "File system", "Test files, test results, coverage reports")
        Container(config, "Configuration", "YAML", "Project definitions, orchestration modes, TDD settings")
    }
    
    System_Ext(discord_api, "Discord API", "Real-time messaging platform")
    System_Ext(github_api, "GitHub API", "Repository and CI/CD integration")
    System_Ext(anthropic_api, "Anthropic API", "Claude AI models")
    System_Ext(ci_system, "CI/CD System", "Test execution and validation")
    
    Rel(user, discord_api, "Slash commands, TDD interactions")
    Rel(discord_api, discord_bot, "Webhook events, API calls")
    Rel(discord_bot, orchestrator, "Command dispatch, state queries")
    Rel(orchestrator, workflow_sm, "Workflow state management")
    Rel(orchestrator, tdd_sm, "TDD state management")
    Rel(orchestrator, agent_lib, "Task execution requests")
    Rel(workflow_sm, state_store, "Read/write workflow state")
    Rel(tdd_sm, tdd_store, "Read/write TDD state")
    Rel(agent_lib, test_artifacts, "Test file operations")
    Rel(orchestrator, config, "Load project definitions")
    Rel(agent_lib, anthropic_api, "AI model requests")
    Rel(agent_lib, github_api, "Code commits, test commits")
    Rel(test_artifacts, ci_system, "Test execution")
```

## Container Responsibilities

### Discord Bot
- Parse and validate workflow and TDD slash commands
- Implement dual state visualization (workflow + TDD)
- Send notifications for both workflow and TDD events
- Handle user interactions and approval buttons
- Display TDD cycle progress and test results

### Orchestrator
- Coordinate dual state machines (workflow + TDD)
- Enforce state machine transitions for both systems
- Coordinate multi-agent workflows with TDD integration
- Implement HITL approval gates for workflow and TDD decisions
- Manage project lifecycle with TDD cycle coordination

### Workflow State Machine
- Manage project-level states (IDLE → BACKLOG_READY → SPRINT_PLANNED → SPRINT_ACTIVE → SPRINT_REVIEW)
- Validate workflow command sequences
- Trigger TDD cycle creation during sprint activation
- Coordinate with TDD state machine for sprint completion

### TDD State Machine
- Manage story-level TDD cycles (DESIGN → TEST_RED → CODE_GREEN → REFACTOR → COMMIT)
- Enforce TDD command sequences and best practices
- Coordinate agent handoffs between TDD phases
- Validate TDD transition conditions (test status, code quality)

### Enhanced Agent Library
- TDD-capable agent implementations with phase specialization
- Design Agent: Creates TDD specifications and acceptance criteria
- QA Agent: Manages test creation, preservation, and validation
- Code Agent: Implements TDD discipline (minimal code, refactoring)
- Anthropic API integration with TDD context
- GitHub operations including test commits and CI integration

### Workflow State Store
- Persist workflow state across restarts
- Track task queues and approvals
- Maintain project status and sprint progress
- Coordinate with TDD state for completion tracking

### TDD State Store
- Persist TDD cycle state and progress
- Track test results and coverage metrics
- Maintain test file lifecycle information
- Store TDD task progress and agent handoff data

### Test Artifacts
- Store test files in TDD directory structure
- Maintain test results and execution history
- Preserve test coverage reports and metrics
- Support test file promotion to permanent locations

### Configuration
- Define project orchestration modes (including TDD settings)
- Configure agent behaviors for TDD phases
- Set approval thresholds for both workflow and TDD decisions
- Define TDD quality gates and coverage requirements