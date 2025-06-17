# AI Agent Scrum Workflows – Research Mode (v3)

This file documents the core interaction patterns between the Product Owner (single user) and the AI-powered Orchestrator + specialist agents.

---

## 1. Main Workflow: Lightweight Scrum Cycle

```mermaid
%%{init: {'theme': 'dark'}}%%
sequenceDiagram
    title "AI Agent Research Scrum Workflow"

    participant U as "User (Product Owner)"
    participant BOT as "Orchestrator (Scrum Master)"
    box "Specialist Agents"
        participant QA as "QA Agent"
        participant DEV as "Code Agent"
        participant DOC as "Doc Agent"
    end
    participant GH as "GitHub Repo"
    participant CI as "CI Runner"

    %% == 1. Vision & Backlog ==
    U->>BOT: /epic "Build auth system"
    BOT->>BOT: Decompose into candidate stories (AUTH-1, AUTH-2)
    BOT-->>U: "Proposed stories ready: [AUTH-1, AUTH-2]"

    U->>BOT: /approve AUTH-1 AUTH-2
    BOT->>BOT: Add stories to product backlog

    %% == 2. Sprint Planning ==
    U->>BOT: /sprint plan AUTH-1 AUTH-2
    BOT-->>U: "Sprint drafted: Auth ‑ Basic"
    U->>BOT: /sprint start

    %% == 3. Sprint Execution ==
    loop each task in Sprint
        BOT->>QA: "Write failing tests for TASK"
        QA-->>BOT: test_task.py

        BOT->>DEV: "Implement code to pass tests" + test_task.py
        DEV-->>BOT: patch.diff

        BOT->>GH: Push branch feat/TASK
        GH->>CI: run pytest & lint
        CI-->>BOT: report ✔ / ✖

        alt Tests pass
            BOT->>DOC: "Add docs for TASK"
            DOC-->>BOT: docs_update.md
            BOT->>GH: Commit docs_update.md
        else Tests fail & attempt < 3
            BOT->>DEV: "CI failed – please fix"
        else Tests fail after 3 attempts
            BOT-->>U: "TASK blocked"  \nOptions: /suggest_fix, /skip_task
        end
    end

    %% == 4. Sprint Review ==
    BOT->>GH: Open PR "auth-sprint"
    BOT-->>U: "Sprint ready – please review PR #123"
    U->>BOT: /request_changes "Guard against duplicate emails"
    note over BOT: Changes become new backlog item.
```

---

## 2. Backlog Management Flow

```mermaid
%%{init: {'theme': 'dark'}}%%
sequenceDiagram
    title "Backlog Commands"

    participant U as "User"
    participant BOT as "Orchestrator"

    U->>BOT: /backlog view product
    BOT-->>U: List stories [AUTH-1, AUTH-2]

    U->>BOT: /backlog view AUTH-1
    BOT-->>U: Full details AUTH-1

    U->>BOT: /backlog add_story "As a user I can reset my password" --feature AUTH
    BOT-->>U: "Story AUTH-3 created"

    U->>BOT: /backlog prioritize AUTH-3 high
    BOT-->>U: "AUTH-3 priority set to high"
```


---

## 3. Sprint Control Commands

```mermaid
%%{init: {'theme': 'dark'}}%%
sequenceDiagram
    title "Sprint Control"

    participant U as "User"
    participant BOT as "Orchestrator"

    Note over U,BOT: During an active sprint...

    U->>BOT: /sprint status
    BOT-->>U: "Sprint 'Auth-Basic': 2/4 tasks complete"

    U->>BOT: /sprint pause
    BOT->>BOT: Freeze agent tasks
    BOT-->>U: "Sprint paused"

    U->>BOT: /sprint resume
    BOT->>BOT: Resume tasks
    BOT-->>U: "Sprint resumed"
```


---

## 4. Debug & Rework Loop (Condensed)

```mermaid
%%{init: {'theme': 'dark'}}%%
sequenceDiagram
    title "Debug Loop"

    participant BOT as "Orchestrator"
    participant DEV as "Code Agent"
    participant GH as "GitHub"
    participant CI as "CI Runner"
    participant U as "User"

    BOT->>DEV: "Fix CI failure (attempt 1)"
    loop Up to 3 attempts
        DEV-->>BOT: patch.diff
        BOT->>GH: push
        GH->>CI: test
        CI-->>BOT: ✖
        BOT->>DEV: "Fix again"
    end

    BOT-->>U: "Task blocked after 3 attempts"\nChoose: /suggest_fix or /skip_task
```