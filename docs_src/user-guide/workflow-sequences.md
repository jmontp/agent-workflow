# AI Agent TDD-Scrum Workflows – Dual State Machine (v4)

This file documents the core interaction patterns between the Product Owner (single user) and the AI-powered dual state machine system with integrated TDD workflows.

---

## 1. Enhanced TDD-Scrum Workflow

```mermaid
%%{init: {'theme': 'dark'}}%%
sequenceDiagram
    title "Enhanced TDD-Scrum Workflow with Dual State Machines"

    participant U as "User (Product Owner)"
    participant WSM as "Workflow State Machine"
    participant Coord as "Multi-Task Coordinator"
    box "TDD Cycle AUTH-1"
        participant TDD1 as "TDD State Machine"
        participant DESIGN1 as "Design Agent"
        participant QA1 as "QA Agent"
        participant DEV1 as "Code Agent"
    end
    box "TDD Cycle AUTH-2"
        participant TDD2 as "TDD State Machine"
        participant DESIGN2 as "Design Agent"
        participant QA2 as "QA Agent"
        participant DEV2 as "Code Agent"
    end
    participant GH as "GitHub Repo"
    participant CI as "CI Runner"

    %% == 1. Vision & Backlog ==
    U->>WSM: /epic "Build auth system"
    WSM->>WSM: Decompose into candidate stories (AUTH-1, AUTH-2)
    WSM-->>U: "Proposed stories ready: [AUTH-1, AUTH-2]"

    U->>WSM: /approve AUTH-1 AUTH-2
    WSM->>WSM: Add stories to product backlog (BACKLOG_READY)

    %% == 2. Sprint Planning ==
    U->>WSM: /sprint plan AUTH-1 AUTH-2
    WSM-->>U: "Sprint drafted: Auth System"
    U->>WSM: /sprint start
    WSM->>WSM: SPRINT_PLANNED → SPRINT_ACTIVE

    %% == 3. Parallel TDD Execution ==
    WSM->>Coord: Create TDD cycles for AUTH-1, AUTH-2
    Coord->>TDD1: Initialize TDD cycle for AUTH-1
    Coord->>TDD2: Initialize TDD cycle for AUTH-2

    par AUTH-1 TDD Cycle
        TDD1->>TDD1: DESIGN phase
        TDD1->>DESIGN1: Create auth API specs
        DESIGN1-->>TDD1: Technical specifications
        
        TDD1->>TDD1: TEST_RED phase
        TDD1->>QA1: Write failing tests
        QA1-->>TDD1: test_auth_api.py (failing)
        
        TDD1->>TDD1: CODE_GREEN phase
        TDD1->>DEV1: Implement to pass tests
        DEV1-->>TDD1: auth_api.py
        DEV1->>GH: Push AUTH-1 implementation
        GH->>CI: Run tests for AUTH-1
        CI-->>TDD1: ✔ All tests pass
        
        TDD1->>TDD1: REFACTOR phase
        TDD1->>DEV1: Improve code quality
        DEV1-->>TDD1: Refactored auth_api.py
        
        TDD1->>TDD1: COMMIT phase
        TDD1->>DEV1: Final commit for AUTH-1
        DEV1->>GH: Commit AUTH-1 complete
        TDD1-->>Coord: AUTH-1 complete
        
    and AUTH-2 TDD Cycle
        TDD2->>TDD2: DESIGN phase
        TDD2->>DESIGN2: Create user model specs
        DESIGN2-->>TDD2: User model specifications
        
        TDD2->>TDD2: TEST_RED phase
        TDD2->>QA2: Write failing tests
        QA2-->>TDD2: test_user_model.py (failing)
        
        TDD2->>TDD2: CODE_GREEN phase
        TDD2->>DEV2: Implement user model
        DEV2-->>TDD2: user_model.py
        DEV2->>GH: Push AUTH-2 implementation
        GH->>CI: Run tests for AUTH-2
        CI-->>TDD2: ✔ All tests pass
        
        TDD2->>TDD2: REFACTOR phase
        TDD2->>DEV2: Optimize user model
        DEV2-->>TDD2: Optimized user_model.py
        
        TDD2->>TDD2: COMMIT phase
        TDD2->>DEV2: Final commit for AUTH-2
        DEV2->>GH: Commit AUTH-2 complete
        TDD2-->>Coord: AUTH-2 complete
    end

    %% == 4. Sprint Completion ==
    Coord-->>WSM: All TDD cycles complete
    WSM->>WSM: SPRINT_ACTIVE → SPRINT_REVIEW
    WSM->>GH: Create Sprint PR
    WSM-->>U: "Sprint complete - Review PR #123"
    
    U->>WSM: /feedback "Great TDD implementation!"
    WSM->>WSM: SPRINT_REVIEW → IDLE
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

## 4. TDD Cycle Management

```mermaid
%%{init: {'theme': 'dark'}}%%
sequenceDiagram
    title "Individual TDD Cycle Control"

    participant U as "User"
    participant TDD as "TDD State Machine"
    participant DESIGN as "Design Agent"
    participant QA as "QA Agent"
    participant CODE as "Code Agent"

    U->>TDD: /tdd status AUTH-1
    TDD-->>U: "AUTH-1 in DESIGN phase"

    TDD->>DESIGN: Create specifications
    DESIGN-->>TDD: Technical specs complete
    TDD->>TDD: DESIGN → TEST_RED

    TDD->>QA: Write failing tests
    QA-->>TDD: 12 failing tests written
    
    U->>TDD: /tdd review_cycle AUTH-1
    TDD-->>U: "Review request: 12 tests ready for implementation"
    U->>TDD: /approve
    
    TDD->>TDD: TEST_RED → CODE_GREEN
    TDD->>CODE: Implement to pass tests
    CODE-->>TDD: Implementation complete
    
    U->>TDD: /tdd status AUTH-1
    TDD-->>U: "AUTH-1 in REFACTOR phase - quality gates met"
    
    TDD->>TDD: REFACTOR → COMMIT
    TDD->>CODE: Final commit
    CODE-->>TDD: Story complete
```

---

## 5. Parallel TDD Monitoring

```mermaid
%%{init: {'theme': 'dark'}}%%
sequenceDiagram
    title "Multi-Story TDD Coordination"

    participant U as "User"
    participant Coord as "Coordinator"
    participant TDD_A as "TDD AUTH-1"
    participant TDD_B as "TDD AUTH-2"
    participant TDD_C as "TDD AUTH-3"

    U->>Coord: /tdd overview
    Coord->>TDD_A: Get status
    Coord->>TDD_B: Get status
    Coord->>TDD_C: Get status
    
    TDD_A-->>Coord: "CODE_GREEN - 14/15 tests"
    TDD_B-->>Coord: "REFACTOR - applying patterns"
    TDD_C-->>Coord: "DESIGN - creating specs"
    
    Coord-->>U: Display parallel progress table
    
    Note over U,Coord: User sees all TDD cycles at once
    
    U->>Coord: /tdd pause AUTH-2
    Coord->>TDD_B: Pause cycle
    TDD_B-->>Coord: "AUTH-2 paused in REFACTOR"
    
    U->>Coord: /suggest_fix "AUTH-2 needs error handling for async flows"
    Coord->>TDD_B: Apply suggestion
    
    U->>Coord: /tdd resume AUTH-2
    Coord->>TDD_B: Resume with guidance
    TDD_B-->>Coord: "AUTH-2 resumed in REFACTOR"
```

---

## 6. TDD Error Handling and Recovery

```mermaid
%%{init: {'theme': 'dark'}}%%
sequenceDiagram
    title "TDD Cycle Error Recovery"

    participant U as "User"
    participant TDD as "TDD State Machine"
    participant CODE as "Code Agent"
    participant CI as "CI System"

    TDD->>CODE: Implement feature (attempt 1)
    CODE->>CI: Push implementation
    CI-->>TDD: ❌ Tests fail

    TDD->>CODE: Fix tests (attempt 2)
    CODE->>CI: Push fix
    CI-->>TDD: ❌ Tests fail

    TDD->>CODE: Fix tests (attempt 3)
    CODE->>CI: Push fix
    CI-->>TDD: ❌ Tests fail

    TDD-->>U: "AUTH-1 blocked in CODE_GREEN after 3 attempts"
    
    alt User provides guidance
        U->>TDD: /suggest_fix "Database connection timeout in tests"
        TDD->>CODE: Apply suggestion
        CODE->>CI: Push with fix
        CI-->>TDD: ✅ Tests pass
        TDD->>TDD: CODE_GREEN → REFACTOR
    else User skips phase
        U->>TDD: /tdd skip_phase AUTH-1
        TDD->>TDD: CODE_GREEN → REFACTOR (manual override)
    else User requests review
        U->>TDD: /tdd review_cycle AUTH-1
        TDD-->>U: "Manual review requested for AUTH-1"
        Note over U,TDD: Human review and intervention
    end
```

---

## 7. Debug & Rework Loop (Condensed)

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