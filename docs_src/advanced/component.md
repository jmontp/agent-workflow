# C4 Component Diagram - AI Agent TDD-Scrum Workflow

## Component Architecture

The system implements a dual state machine architecture with TDD-enhanced agents that coordinate workflow management and Test-Driven Development cycles.

### Discord Bot Components

```mermaid
C4Component
    title Discord Bot Components

    Container_Boundary(discord_bot, "Discord Bot") {
        Component(command_parser, "Command Parser", "Parse and validate slash commands")
        Component(state_visualizer, "State Visualizer", "Generate interactive state diagrams")
        Component(notification_manager, "Notification Manager", "Send alerts and status updates")
        Component(button_handler, "Button Handler", "Handle interactive UI elements")
    }
    
    Container(orchestrator, "Orchestrator", "Core coordination logic")
    System_Ext(discord_api, "Discord API")
    
    Rel(discord_api, command_parser, "Slash command events")
    Rel(command_parser, orchestrator, "Validated commands")
    Rel(orchestrator, state_visualizer, "State data")
    Rel(state_visualizer, discord_api, "Interactive messages")
    Rel(orchestrator, notification_manager, "Status updates")
    Rel(notification_manager, discord_api, "Notifications")
    Rel(button_handler, orchestrator, "User interactions")
```

### Orchestrator Components

```mermaid
C4Component
    title Orchestrator Components (Dual State Machine Architecture)

    Container_Boundary(orchestrator, "Orchestrator") {
        Component(workflow_sm, "Workflow State Machine", "Enforce workflow command transitions")
        Component(tdd_sm, "TDD State Machine", "Enforce TDD command transitions")
        Component(state_coordinator, "State Coordinator", "Coordinate dual state machines")
        Component(project_manager, "Project Manager", "Multi-project coordination")
        Component(task_dispatcher, "Task Dispatcher", "Agent task coordination")
        Component(tdd_coordinator, "TDD Coordinator", "Manage TDD cycles and tasks")
        Component(approval_gate, "Approval Gate", "HITL workflow management")
        Component(retry_logic, "Retry Logic", "3-attempt failure handling")
    }
    
    Container(agent_lib, "Enhanced Agent Library")
    Container(state_store, "State Store")
    Container(tdd_store, "TDD State Store")
    Container(discord_bot, "Discord Bot")
    
    Rel(discord_bot, workflow_sm, "Workflow command validation")
    Rel(discord_bot, tdd_sm, "TDD command validation")
    Rel(workflow_sm, state_coordinator, "Workflow state changes")
    Rel(tdd_sm, state_coordinator, "TDD state changes")
    Rel(state_coordinator, project_manager, "Coordinated state transitions")
    Rel(project_manager, task_dispatcher, "Workflow task assignment")
    Rel(project_manager, tdd_coordinator, "TDD cycle management")
    Rel(task_dispatcher, agent_lib, "Agent execution")
    Rel(tdd_coordinator, agent_lib, "TDD phase execution")
    Rel(approval_gate, discord_bot, "Approval requests")
    Rel(retry_logic, approval_gate, "Escalation after 3 failures")
    Rel(project_manager, state_store, "Persist workflow state")
    Rel(tdd_coordinator, tdd_store, "Persist TDD state")
```

### Enhanced Agent Library Components

```mermaid
C4Component
    title Enhanced Agent Library Components (TDD-Capable)

    Container_Boundary(agent_lib, "Enhanced Agent Library") {
        Component(base_agent, "Base Agent", "Common agent interface")
        Component(design_agent_tdd, "Design Agent (TDD)", "TDD specifications & design")
        Component(code_agent_tdd, "Code Agent (TDD)", "TDD implementation & refactoring")
        Component(qa_agent_tdd, "QA Agent (TDD)", "Test creation & preservation")
        Component(data_agent, "Data Agent", "Data processing")
        Component(tdd_phase_manager, "TDD Phase Manager", "Coordinate TDD agent handoffs")
        Component(test_preservation, "Test Preservation", "Manage test file lifecycle")
        Component(anthropic_client, "Anthropic Client", "AI model integration")
        Component(github_client, "GitHub Client", "Repository operations")
    }
    
    System_Ext(anthropic_api, "Anthropic API")
    System_Ext(github_api, "GitHub API")
    
    Rel(base_agent, design_agent_tdd, "Inheritance")
    Rel(base_agent, code_agent_tdd, "Inheritance")
    Rel(base_agent, qa_agent_tdd, "Inheritance")
    Rel(base_agent, data_agent, "Inheritance")
    Rel(tdd_phase_manager, design_agent_tdd, "Design phase coordination")
    Rel(tdd_phase_manager, qa_agent_tdd, "Test phase coordination")
    Rel(tdd_phase_manager, code_agent_tdd, "Code phase coordination")
    Rel(qa_agent_tdd, test_preservation, "Test file management")
    Rel(code_agent_tdd, test_preservation, "Test validation")
    Rel(design_agent_tdd, anthropic_client, "AI requests")
    Rel(code_agent_tdd, anthropic_client, "AI requests")
    Rel(qa_agent_tdd, anthropic_client, "AI requests")
    Rel(code_agent_tdd, github_client, "Code commits")
    Rel(qa_agent_tdd, github_client, "Test commits")
    Rel(anthropic_client, anthropic_api, "API calls")
    Rel(github_client, github_api, "Repository operations")
```

### TDD State Management Components

```mermaid
C4Component
    title TDD State Management Components

    Container_Boundary(tdd_system, "TDD Management System") {
        Component(tdd_state_machine, "TDD State Machine", "Enforce TDD transitions")
        Component(tdd_cycle_manager, "TDD Cycle Manager", "Manage TDD cycles per story")
        Component(tdd_task_manager, "TDD Task Manager", "Handle TDD tasks within cycles")
        Component(test_file_manager, "Test File Manager", "Manage test file lifecycle")
        Component(test_result_tracker, "Test Result Tracker", "Track test execution results")
        Component(ci_integration, "CI Integration", "Interface with CI/CD pipelines")
    }
    
    Container(tdd_storage, "TDD Storage")
    Container(test_artifacts, "Test Artifacts")
    
    Rel(tdd_state_machine, tdd_cycle_manager, "State transitions")
    Rel(tdd_cycle_manager, tdd_task_manager, "Task lifecycle")
    Rel(tdd_task_manager, test_file_manager, "Test file operations")
    Rel(test_file_manager, test_result_tracker, "Test execution")
    Rel(test_result_tracker, ci_integration, "CI validation")
    Rel(tdd_cycle_manager, tdd_storage, "Persist TDD state")
    Rel(test_file_manager, test_artifacts, "Store test files")
```

### Test Preservation Workflow Components

```mermaid
C4Component
    title Test Preservation Workflow Components

    Container_Boundary(test_preservation, "Test Preservation System") {
        Component(test_creator, "Test Creator", "Create failing tests (RED phase)")
        Component(test_committer, "Test Committer", "Commit tests to repository")
        Component(test_validator, "Test Validator", "Validate tests during code phases")
        Component(test_promoter, "Test Promoter", "Promote tests to permanent location")
        Component(coverage_tracker, "Coverage Tracker", "Track test coverage metrics")
    }
    
    Container(tdd_test_dir, "TDD Test Directory")
    Container(permanent_tests, "Permanent Test Location")
    Container(coverage_reports, "Coverage Reports")
    
    Rel(test_creator, tdd_test_dir, "Create test files")
    Rel(test_committer, tdd_test_dir, "Commit failing tests")
    Rel(test_validator, tdd_test_dir, "Validate during development")
    Rel(test_promoter, permanent_tests, "Integrate into test suite")
    Rel(coverage_tracker, coverage_reports, "Generate coverage data")
    Rel(test_promoter, tdd_test_dir, "Source test files")
```