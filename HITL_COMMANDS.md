# HITL Commands for AI Agent Scrum

This document outlines the commands the Human-in-the-Loop (HITL) User, acting as the Product Owner, can use to interact with and guide the Orchestrator (Scrum Master) agent.

---

## 1. Planning & Refinement

These commands are used to define the project's direction and scope.

### `/define_epic <description>`
**Description:** Initializes a new high-level epic. The orchestrator will break this down into smaller, manageable features.
**Example:** 
```
/define_epic "Build a user-facing analytics dashboard"
```

### `/approve_features <feature_ids>`
**Description:** Approves one or more features that the orchestrator has proposed. The orchestrator will then decompose these features into user stories for the product backlog.
**Example:**
```
/approve_features [DASH-1, DASH-3]
```

### `/plan_sprint <story_ids>`
**Description:** Selects specific user stories from the product backlog to be included in the next sprint.
**Example:**
```
/plan_sprint stories: [DASH-1.1, DASH-1.2, DASH-3.1]
```

---

## 2. Sprint Control & Monitoring

These commands are used to manage the active sprint and monitor its progress.

### `/sprint_status`
**Description:** Requests a real-time progress report for the current sprint.
**Example:**
```
/sprint_status
```
**Expected Output:** 
> "Sprint 'Analytics-UI': 4/7 tasks complete. 1 task blocked (awaiting API key). Estimated completion: 2 days."

### `/pause_sprint`
**Description:** Immediately pauses all agent activity in the current sprint. Useful for urgent interventions.
**Example:**
```
/pause_sprint
```

### `/resume_sprint`
**Description:** Resumes activity in a paused sprint.
**Example:**
```
/resume_sprint
```

---

## 3. Review & Feedback

These commands are used during the Sprint Review and for providing continuous feedback.

### `/request_changes <description>`
**Description:** Used during a Pull Request review to specify required changes before approval. These changes will be added to the backlog.
**Example:**
```
/request_changes "The login button needs to be re-styled to match the new design spec."
```

### `/feedback <description>`
**Description:** Provides general feedback to the orchestrator, typically after a sprint, to improve the performance of specialist agents in the future.
**Example:**
```
/feedback "The QA Agent's tests are good, but they should also include performance regression tests."
```

---

## 4. Backlog Management

These commands allow for manual management of the product and sprint backlogs.

### `/view_backlog [product|sprint]`
**Description:** Displays the contents of the specified backlog.
**Example:**
```
/view_backlog product
```

### `/add_story <description>`
**Description:** Manually adds a new user story to the product backlog.
**Example:**
```
/add_story "As a user, I want to be able to export my dashboard data to a CSV file."
``` 