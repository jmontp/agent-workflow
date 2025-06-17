# HITL Commands

Command reference for the AI Agent TDD-Scrum workflow system. These commands provide Human-In-The-Loop control over the multi-agent orchestration process.

## Command Quick-Reference

## Core Commands

### Project Management

**`/epic "<description>"`**
Define a new high-level initiative.

**`/approve [ID ...]`**
Approve proposed stories or epics so they can enter a sprint.

### Sprint Management

**`/sprint plan [ID ...]`**
Plan next sprint with specified story IDs.

**`/sprint start`**
Kick off the planned sprint.

**`/sprint status`**
Get a progress snapshot of the current sprint.

**`/sprint pause`**
Halt agent work temporarily.

**`/sprint resume`**
Continue paused sprint work.

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
/skip_task   # after three failed CI attempts
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