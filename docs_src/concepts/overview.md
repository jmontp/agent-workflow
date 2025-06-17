# System Overview

The AI Agent TDD-Scrum Workflow system is a Human-In-The-Loop orchestration framework that coordinates specialized AI agents through a sophisticated dual state machine architecture for Test-Driven Development and Scrum workflow management.

## Core Concepts

### Dual State Machine Architecture
The system operates two coordinated state machines:

**Primary Workflow State Machine:**
- Manages high-level Scrum development lifecycle
- States: `IDLE` → `BACKLOG_READY` → `SPRINT_PLANNED` → `SPRINT_ACTIVE` → `SPRINT_REVIEW`
- Handles epic creation, sprint planning, and project coordination
- Enforces human approval gates for strategic decisions

**Secondary TDD State Machines:**
- Manages individual story implementation through proper TDD cycles
- States: `DESIGN` → `TEST_RED` → `CODE_GREEN` → `REFACTOR` → `COMMIT`
- Multiple instances run in parallel during active sprints
- Ensures proper RED-GREEN-REFACTOR methodology for each story

### Ephemeral Multi-Agent Coordination
The system creates agents on-demand based on workload:
- **Orchestrator Agent**: Spun up for sprint coordination and multi-task management
- **Design Agents**: Architecture and technical specifications per story
- **QA Agents**: Test creation and quality validation per TDD cycle
- **Code Agents**: Feature implementation and refactoring per story
- **Analytics Agent**: Cross-story metrics and progress reporting

### Human-In-The-Loop Control
Strategic decisions require human approval while TDD cycles can run autonomously:
- Epic and story creation (workflow level)
- Sprint planning and execution (workflow level)
- TDD phase reviews and error handling (story level)
- Code review and deployment (workflow level)
- Multi-story coordination and dependencies

### Parallel Processing
Multiple TDD cycles execute simultaneously:
- Independent story development with isolated state machines
- Parallel RED-GREEN-REFACTOR cycles for different features
- Shared coordination layer for progress tracking and resource management
- Cross-story analytics and dependency management

## Two-Repository Architecture

### Orchestration Repository
**Purpose**: Central coordination framework
- Agent definitions and capabilities
- Workflow engine and state machine
- Discord bot and user interface
- Security policies and tool restrictions

### Project Repositories  
**Purpose**: Individual development projects
- Project source code
- Embedded workflow data (`.orch-state/` directory)
- Sprint plans, backlogs, and progress tracking
- Architecture decisions and documentation

**Benefits:**
- Project data stays with project code
- Version control for management artifacts
- Easy project migration between orchestrator instances
- Clear security boundaries

## Key Components

### Discord Interface
Primary user interaction through comprehensive slash commands:
- **Workflow Commands**: `/epic`, `/sprint plan|start|status|pause|resume` - Manage development cycles
- **TDD Commands**: `/tdd start|status|overview|pause|resume` - Control individual TDD cycles
- **Phase Commands**: `/tdd design_complete|tests_ready|code_green|refactor_done` - Advance TDD phases
- **Review Commands**: `/tdd review_cycle`, `/approve`, `/request_changes` - Human oversight
- **System Commands**: `/state`, `/tdd metrics` - Interactive system inspection

### Dual State Machine Coordination
Enforces proper workflow and TDD sequences:
- **Workflow Level**: Prevents invalid sprint operations, guides Scrum sequences
- **TDD Level**: Enforces RED-GREEN-REFACTOR methodology per story
- **Cross-State Validation**: Sprint commands affect all active TDD cycles
- **State Recovery**: System can resume from any state after interruption
- **Visual Feedback**: Interactive state diagrams for both state machines

### Enhanced Agent Security
Tool access control with ephemeral agent patterns:
- **Orchestrator Agent**: Full system access for coordination (temporary)
- **Design Agents**: Read-only access per story for architecture (temporary)
- **QA Agents**: Test execution tools per TDD cycle (temporary)
- **Code Agents**: Code editing and version control per story (temporary)
- **Analytics Agent**: Cross-story data analysis and reporting (persistent)

### Integrated TDD-Scrum Management
Complete development lifecycle with proper TDD methodology:
- **Epic and Story Hierarchies**: Traditional Scrum backlog management
- **Sprint Planning**: Automatic TDD cycle estimation and resource allocation
- **Parallel TDD Execution**: Multiple stories developed simultaneously with proper TDD
- **Progress Tracking**: Real-time visibility into both workflow and TDD states
- **Quality Gates**: Automated TDD phase validation with human oversight options
- **Error Escalation**: Multi-level escalation from TDD cycles to sprint coordination

## Workflow Philosophy

The system follows **TDD-enhanced research-mode Scrum** principles:

### Core Principles
- **Test-First Development**: Every story follows proper RED-GREEN-REFACTOR methodology
- **Parallel Processing**: Multiple TDD cycles execute simultaneously for velocity
- **Minimal Ceremony**: Streamlined Scrum adapted for solo engineers with AI assistance
- **Maximum Momentum**: Automated TDD cycles with human oversight only when needed
- **Quality by Design**: Built-in quality gates through TDD methodology
- **Continuous Learning**: Both workflow and TDD metrics inform process improvements

### TDD Integration Benefits
- **Enforced Quality**: RED-GREEN-REFACTOR ensures proper test coverage and design
- **Parallel Development**: Multiple stories can be developed simultaneously without conflicts
- **Automated Validation**: TDD cycles validate implementation against requirements automatically
- **Human Oversight**: Strategic decisions escalated while technical implementation automated
- **Rapid Feedback**: Real-time TDD progress visibility with immediate error detection

### Balanced Automation
This approach balances automation benefits with human control:
- **Strategic Control**: Humans manage epics, sprint planning, and story prioritization
- **Technical Automation**: AI agents handle TDD implementation with proper methodology
- **Quality Assurance**: Automated TDD cycles ensure high-quality output
- **Error Recovery**: Multi-level escalation from TDD phase issues to human intervention
- **Continuous Improvement**: TDD metrics drive both technical and process improvements

The dual state machine architecture ensures both proper Scrum methodology at the project level and rigorous TDD practices at the story level, maximizing both velocity and quality.