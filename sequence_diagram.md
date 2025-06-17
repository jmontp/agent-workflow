# AI Agent Scrum Workflows

This document contains a set of sequence diagrams illustrating the various workflows within the AI Agent TDD-Scrum system.

---

## 1. Main Workflow: AI Agent TDD-Scrum (v2)

This diagram shows the primary "happy path" for a full sprint cycle, from planning to review.

```mermaid
%%{init: {'theme': 'dark', 'themeVariables': { 'primaryColor': '#42a5f5', 'mainBkg': '#1e1e1e', 'textColor': '#ffffff'}}}%%
sequenceDiagram
    title "AI Agent TDD-Scrum Workflow (v2)"

    participant U as "User (Product Owner)"
    participant BOT as "Orchestrator (Scrum Master)"
    box "Specialist Agent Team"
        participant QA_Agent as "QA Agent (Test Writer)"
        participant Code_Agent as "Code Agent (Implementation)"
        participant Tech_Doc_Agent as "Tech Doc Agent"
        participant User_Doc_Agent as "User Doc Agent"
    end
    participant GH as "GitHub Repo"
    participant CI as "CI/CD Pipeline"

    %% == 1. Backlog Refinement (Epic -> Feature -> Story) ==
    U->>BOT: /define_epic "Build a complete auth system"
    BOT->>BOT: Decompose epic into features (e.g., Registration, Login, SSO)
    BOT-->>U: "Features for 'Auth System' are drafted. Please approve."
    U->>BOT: /approve_features [REG, SSO]
    BOT->>BOT: Decompose approved features into user stories
    BOT-->>U: "Product Backlog updated with stories. Ready for sprint planning."

    %% == 2. Sprint Planning ==
    U->>BOT: /plan_sprint stories: [REG-1, REG-2, SSO-1]
    BOT-->>U: "Sprint for 'User Registration & Google SSO' is planned."
    U->>BOT: ✅ Start Sprint

    %% == 3. Sprint Execution (TDD Task Loop) ==
    loop For each task in Sprint Backlog
        BOT->>QA_Agent: Task: "Write tests for user registration endpoint"
        QA_Agent-->>BOT: Returns `test_registration.py`
        
        note right of BOT: The Code Agent only receives the<br/>task description and the test file.
        BOT->>Code_Agent: Task: "Implement user registration endpoint to pass these tests."<br/>File: `test_registration.py`
        Code_Agent-->>BOT: Returns `registration.py`
        
        BOT->>GH: Commit `registration.py` and `test_registration.py` to 'feat/auth-sprint-1'
        GH->>CI: Trigger build & execute pytest
        CI-->>BOT: Report test results (✔/✖)
        
        alt Tests Passed
            BOT->>Tech_Doc_Agent: "Document the registration endpoint API."
            Tech_Doc_Agent-->>BOT: Returns updated `api_spec.md`
            
            BOT->>User_Doc_Agent: "Explain how a new user signs up.<br/>Include data validation rules."
            User_Doc_Agent-->>BOT: Returns updated `user_guide.md`
            
            BOT->>GH: Commit documentation changes
        else Tests Failed
            BOT->>Code_Agent: "Tests failed. Here is the output, please fix."<br/>File: `test_output.log`
            note over BOT: Debug loop continues until tests pass.
        end
    end

    %% == 4. Sprint Review ==
    Note over U, BOT: End of Sprint Cycle
    BOT->>GH: Create Pull Request for 'feat/auth-sprint-1'
    BOT-->>U: "Sprint Review: 'User Registration & Google SSO' is ready. 🎉<br/>**PR #125 is ready for your review and approval.**"
    U->>GH: Review Pull Request, leave comments if needed
    alt PR Approved
        U->>GH: Approve & Merge Pull Request
        GH-->>BOT: Webhook: PR Merged
        BOT-->>U: "Sprint Goal achieved and merged!"
    else PR Needs Changes
        U->>BOT: /request_changes "Please add more robust error handling for duplicate emails."
        note over BOT: New tasks are added to the backlog for the next sprint.
    end

    %% == 5. Sprint Retrospective ==
    U->>BOT: /feedback "The User Doc Agent should use LaTeX for math formulas."
    BOT-->>U: "Feedback noted. Agent prompts will be updated."
```

---

## 2. Ancillary Workflow: Backlog Management

This diagram illustrates how the User (Product Owner) grooms the product backlog.

```mermaid
%%{init: {'theme': 'dark', 'themeVariables': { 'primaryColor': '#42a5f5', 'mainBkg': '#1e1e1e', 'textColor': '#ffffff'}}}%%
sequenceDiagram
    title "Backlog Management Workflow"

    participant U as "User (Product Owner)"
    participant BOT as "Orchestrator (Scrum Master)"

    U->>BOT: /view_backlog product
    BOT-->>U: Displays list of stories [STORY-1, STORY-2, ...]

    U->>BOT: /view_item STORY-2
    BOT-->>U: Shows full details for STORY-2

    U->>BOT: /prioritize_story STORY-2 top
    BOT-->>U: "STORY-2 is now top priority."

    U->>BOT: /add_story "As a user, I can reset my password via email."
    BOT-->>U: "New story STORY-3 added to backlog."

    U->>BOT: /remove_item STORY-1
    BOT-->>U: "STORY-1 has been removed from the backlog."
```

---

## 3. Ancillary Workflow: Debug & Rework Loop

This diagram details the process when a task fails CI tests.

```mermaid
%%{init: {'theme': 'dark', 'themeVariables': { 'primaryColor': '#42a5f5', 'mainBkg': '#1e1e1e', 'textColor': '#ffffff'}}}%%
sequenceDiagram
    title "Debug & Rework Loop Workflow"
    
    participant BOT as "Orchestrator"
    participant Code_Agent as "Code Agent"
    participant GH as "GitHub Repo"
    participant CI as "CI/CD Pipeline"
    participant U as "User (HITL)"

    note over BOT, CI: A task has been implemented and pushed to GitHub.
    GH->>CI: Trigger build & execute tests
    CI-->>BOT: ✖ Tests Failed. Provides `test_output.log`

    loop 3 Times (or as configured)
        BOT->>Code_Agent: "Tests failed. Please fix the code based on this log."<br/>File: `test_output.log`
        Code_Agent-->>BOT: Returns updated code file.
        BOT->>GH: Commit the fix attempt
        GH->>CI: Re-trigger build & tests
        CI-->>BOT: ✖ Tests Failed. Provides new `test_output.log`
    end
    
    Note over BOT, U: Agent has failed to fix the issue after 3 attempts.
    BOT-->>U: "Task 'Implement Registration' is blocked. I failed to fix the tests after 3 attempts. Please advise."<br/>[View Logs] [Suggest Fix] [Skip Task]
    
    alt User Provides a Fix
        U->>BOT: /suggest_fix "The database connection string is wrong in `config.py`."
        BOT->>Code_Agent: "The user suggested a fix: 'The database connection string is wrong in `config.py`'. Please apply this fix."
        Code_Agent-->>BOT: Returns corrected code.
        note over BOT: The loop continues with the user's fix.
    else User Skips Task
        U->>BOT: /skip_task
        BOT->>BOT: Marks task as 'skipped' and moves on.
        BOT-->>U: "Task skipped. Moving to the next task."
    end
```

---

## 4. Ancillary Workflow: Sprint Control & Monitoring

This diagram illustrates how the User can check on and manage an active sprint.

```mermaid
%%{init: {'theme': 'dark', 'themeVariables': { 'primaryColor': '#42a5f5', 'mainBkg': '#1e1e1e', 'textColor': '#ffffff'}}}%%
sequenceDiagram
    title "Sprint Control & Monitoring Workflow"

    participant U as "User (Product Owner)"
    participant BOT as "Orchestrator (Scrum Master)"
    
    Note over U, BOT: During an active sprint...

    U->>BOT: /sprint_status
    BOT-->>U: "Sprint 'Analytics-UI': 4/7 tasks complete.<br/>1 task blocked (awaiting API key)."
    
    U->>BOT: /pause_sprint
    BOT->>BOT: Halts all agent activities.
    BOT-->>U: "Sprint Paused. All agent work has been stopped."

    Note over U, BOT: Some time passes...

    U->>BOT: /resume_sprint
    BOT->>BOT: Resumes agent activities.
    BOT-->>U: "Sprint Resumed."
```