# 💬 HITL Commands - Discord Bot Reference

> **Complete Discord slash command reference for AI agent control, workflow management, and human-in-the-loop operations**

**Discord command guide** for controlling AI agents, managing sprints, approving tasks, and orchestrating TDD workflows. All commands work in Discord channels with slash command interface. These commands provide Human-In-The-Loop control over the dual state machine orchestration process with integrated TDD workflows.

!!! tip "Quick Command Discovery"
    Use `/state` in Discord at any time to see available commands for your current workflow state.

## ⚡ Command Quick-Reference | Discord Slash Commands

### Syntax Guide | Parameter Types | Command Format | Usage Examples

!!! info "Command Format"
    - **Required parameters:** `<parameter>`
    - **Optional parameters:** `[parameter]`
    - **Multiple values:** `ID ...` (space-separated list)

## 🎯 Core Workflow Commands | Project Management

### Epic Creation | Story Management | Sprint Control | Approval Workflow

### 📋 Project Management

=== "Epic Definition"

    **`/epic "<description>"`**
    
    Define a new high-level initiative.
    
    !!! example "Example"
        ```
        /epic "Build authentication system with OAuth2 support"
        ```
    
    **What happens next:**
    
    - System generates user stories
    - Stories await approval with `/approve`
    - Estimated effort and timeline provided

=== "Approval Process"

    **`/approve [ID ...]`**
    
    Approve proposed stories or epics so they can enter a sprint.
    
    !!! example "Example"
        ```
        /approve AUTH-1 AUTH-2
        ```
    
    **Approval triggers:**
    
    - Stories move to backlog
    - Available for sprint planning
    - Effort estimation confirmed

### 🏃 Sprint Management

=== "Planning"

    **`/sprint plan [ID ...]`**
    
    Plan next sprint with specified story IDs.
    
    !!! example "Example"
        ```
        /sprint plan AUTH-1 AUTH-2 AUTH-3
        ```
    
    **Planning includes:**
    
    - Capacity validation
    - Dependency checking
    - Sprint goal definition

=== "Execution"

    **`/sprint start`**
    
    Kick off the planned sprint.
    
    !!! warning "Prerequisites"
        - Sprint must be planned first
        - All stories must be approved
        - No active sprint in progress
    
    **Sprint start creates:**
    
    - TDD cycles for each story
    - Agent assignments
    - Progress tracking

=== "Monitoring"

    **`/sprint status`**
    
    Get a progress snapshot of the current sprint.
    
    **Status includes:**
    
    - Story completion percentage
    - Active TDD cycles
    - Blocked or failed tasks
    - Estimated completion time

=== "Control"

    **`/sprint pause`** / **`/sprint resume`**
    
    Halt or continue agent work temporarily.
    
    !!! tip "Use Cases"
        - **Pause:** Emergency maintenance, priority changes
        - **Resume:** Continue after resolving issues

### Backlog Operations

**`/backlog view product`**
List all product backlog items.

**`/backlog view sprint`**
List current sprint backlog items.

**`/backlog view <ITEM_ID>`**
Show full details for a specific item.

**`/backlog add_story "<description>" --feature <FEATURE_ID>`**
Create a new story under a feature.

**`/backlog remove <ITEM_ID>`**
Delete an item from the backlog.

**`/backlog prioritize <STORY_ID> <top|high|med|low>`**
Set priority level for a story.

### Development Control

**`/request_changes "<description>"`**
Request modifications on a pull request.

**`/suggest_fix "<description>"`**
Provide hints to the Code Agent when stuck.

**`/skip_task`**
Abandon the currently blocked task and move on.

**`/feedback "<description>"`**
Provide improvement notes after a sprint.

**`/state`**
Inspect current orchestrator state with interactive controls.

### TDD Workflow Commands

**`/tdd start <STORY_ID>`**
Manually start TDD cycle for a specific story.

**`/tdd status [STORY_ID]`**
Get current TDD phase and progress for one or all active stories.

**`/tdd overview`**
Show status of all active TDD cycles with visual progress.

**`/tdd pause <STORY_ID>`**
Temporarily halt TDD cycle for a story.

**`/tdd resume <STORY_ID>`**
Resume paused TDD cycle.

**`/tdd design_complete <STORY_ID>`**
Mark design phase complete and advance to TEST_RED.

**`/tdd tests_ready <STORY_ID>`**
Confirm tests are written and failing properly.

**`/tdd code_green <STORY_ID>`**
Confirm all tests are now passing.

**`/tdd refactor_done <STORY_ID>`**
Complete refactoring and proceed to commit.

**`/tdd review_cycle <STORY_ID>`**
Request human review of current TDD cycle.

**`/tdd skip_phase <STORY_ID>`**
Skip current TDD phase (requires approval).

**`/tdd metrics`**
Display TDD metrics: cycle time, test coverage, refactor frequency.

**`/tdd halt_all`**
Emergency stop all TDD cycles (requires confirmation).

### Multi-Project Commands

**`/global_status`**
Show status of all projects in multi-project orchestration.

**`/project_list`**
List all registered projects with their current state.

**`/project_start <PROJECT_NAME>`**
Start orchestration for a specific project.

**`/project_stop <PROJECT_NAME>`**
Stop orchestration for a specific project.

**`/project_register <NAME> <PATH>`**
Register a new project for orchestration.

**`/resource_status`**
Display resource allocation across all projects.

**`/resource_optimize`**
Trigger resource optimization across projects.

### Context Management Commands

**`/context status`**
Show context management system status.

**`/context optimize`**
Trigger context optimization across all agents.

**`/context memory [AGENT_ID]`**
Display agent memory usage and cache statistics.

**`/context clear_cache`**
Clear context cache (use when memory issues occur).

### Cross-Project Intelligence Commands

**`/insights global`**
Show cross-project insights and pattern analysis.

**`/patterns list`**
Display detected patterns across projects.

**`/knowledge_transfer`**
Show recommended knowledge transfers between projects.

---

## Examples

### 1. Strategic Planning
```bash
/epic "Build a modular authentication system"
```
> Orchestrator returns proposed stories `AUTH-1`, `AUTH-2`.

```bash
/approve AUTH-1 AUTH-2
```

### 2. Sprint Lifecycle
```bash
/sprint plan AUTH-1 AUTH-2
/sprint start
```

At any time:
```bash
/sprint status
/sprint pause   # emergency halt
/sprint resume  # continue work
```

### 3. Backlog Grooming
```bash
/backlog view product
/backlog add_story "As a user I can reset my password" --feature AUTH
/backlog prioritize AUTH-3 high
```

### 4. Review & Debug
```bash
/request_changes "Add duplicate-email guard in registration API"
/suggest_fix "Database URL is wrong in config.py"
```

### 5. Multi-Project Management
```bash
# Register and start multiple projects
/project_register frontend-app /path/to/frontend
/project_register backend-api /path/to/backend

# Check global status
/global_status
# Shows: 2 projects registered, 1 active, 3 total agents

# Start specific projects
/project_start frontend-app
/project_start backend-api

# Monitor resource allocation
/resource_status
# Shows: CPU: 65%, Memory: 4.2GB/8GB, Agents: 5/10
```

### 6. Context Management
```bash
# Check context system status
/context status
# Shows: Cache hit rate: 87%, Memory usage: 1.2GB

# Optimize context when performance degrades
/context optimize

# Check specific agent memory
/context memory DesignAgent-AUTH-1
# Shows: Context size: 12K tokens, Cache: 3 items

# Clear cache if needed
/context clear_cache
```

### 7. Cross-Project Intelligence
```bash
# View insights across projects
/insights global
# Shows: 5 patterns detected, 3 transfer opportunities

# List detected patterns
/patterns list
# Shows: API design patterns, testing strategies, etc.

# Get knowledge transfer recommendations
/knowledge_transfer
# Shows: Transfer logging strategy from backend-api to frontend-app
/skip_task   # after three failed CI attempts
```

### 5. TDD Workflow Management
```bash
# Monitor TDD progress during active sprint
/tdd overview

# Check specific story TDD status
/tdd status AUTH-1

# Manually advance TDD phases when needed
/tdd design_complete AUTH-1
/tdd tests_ready AUTH-1
/tdd code_green AUTH-1
/tdd refactor_done AUTH-1

# Review TDD cycle before proceeding
/tdd review_cycle AUTH-1

# Handle stuck TDD cycles
/tdd pause AUTH-1
/suggest_fix "Need to handle async authentication flow"
/tdd resume AUTH-1

# Skip problematic phase with justification
/tdd skip_phase AUTH-1   # Requires approval
```

### 6. Parallel TDD Monitoring
```bash
# Start sprint with multiple stories
/sprint start
# Automatically creates TDD cycles for all stories

# Monitor all TDD cycles
/tdd overview
```
> Output shows parallel progress:
> ```
> AUTH-1: CODE_GREEN (14/15 tests passing)
> AUTH-2: REFACTOR (applying clean patterns)  
> AUTH-3: TEST_RED (8 failing tests written)
> ```

```bash
# Get TDD performance metrics
/tdd metrics

# Emergency halt all TDD cycles
/tdd halt_all
```

---

## Escalation Policy (Research Mode)
1. The Orchestrator escalates after **three consecutive CI failures**.
2. Security-critical code requires explicit human approval.
3. Agents time-box tasks to **30 min**; longer tasks trigger a status ping.

_This lightweight command set keeps you focused on big-picture direction while agents handle the details._

## State Awareness & Invalid Commands
The orchestrator enforces a finite-state machine (see `command_state_machine.md`).

* Use `/state` at any time to:
  1. View the **current state** (e.g., `SPRINT_ACTIVE`).
  2. Click **Allowed Commands** – shows only the verbs valid right now.
  3. Click **Diagram** – in-chat SVG of the full state chart.
  4. Click **Matrix** – raw command→state table.

If you issue a command that is **not legal** for the current state, the bot replies with an error message:

**Warning:** Command `/sprint plan` is not allowed now (state: **SPRINT_ACTIVE**). Try `/sprint status`.

No action is taken until a valid command is sent. 