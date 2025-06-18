# Project Repository Architecture

Project repositories contain the actual code being developed with AI assistance using Test-Driven Development workflows. Each project repository maintains its own project management data, workflow state, and TDD state while being coordinated by the orchestration system's dual state machine architecture.

## Repository Structure

```
project-repository/
├── src/                     # Project source code
├── tests/                   # Project tests
│   ├── unit/                # Permanent unit tests
│   ├── integration/         # Permanent integration tests
│   └── tdd/                 # TDD working directory
│       ├── AUTH-1/          # Story-specific TDD tests
│       │   ├── test_login.py
│       │   └── test_auth.py
│       └── AUTH-2/          # Another story's TDD tests
├── .git/                    # Git repository
├── .orch-state/            # AI workflow state (managed by orchestration)
│   ├── backlog.json        # Epics, stories, and priorities
│   ├── sprints/            # Sprint data and retrospectives
│   │   ├── sprint-abc123.json
│   │   └── sprint-def456.json
│   ├── tdd/                # TDD state storage
│   │   ├── cycles/         # TDD cycle data per story
│   │   │   ├── AUTH-1-cycle.json
│   │   │   └── AUTH-2-cycle.json
│   │   └── test-results/   # Test execution results
│   │       ├── AUTH-1-results.json
│   │       └── coverage-reports/
│   ├── architecture.md     # Project-specific architecture decisions
│   ├── best-practices.md   # Project conventions and patterns
│   └── status.json         # Current workflow state
└── README.md               # Project documentation
```

## `.orch-state/` Directory

### Purpose
The `.orch-state/` directory stores all AI workflow-related data and TDD state within the project repository, ensuring that project management information and TDD cycle data are version-controlled alongside the code. This includes both high-level workflow state and detailed TDD cycle progression.

### Enhanced Contents (with TDD Support)

#### New TDD-Specific Storage

**`.orch-state/tdd/` Directory Structure:**
- `cycles/`: TDD cycle data per story
- `test-results/`: Test execution results and metrics
- `coverage-reports/`: Test coverage data and trends
- `metrics/`: TDD performance and quality metrics

**`tests/tdd/` Directory Structure:**
- `{story-id}/`: Story-specific test files during TDD development
- Test files preserved through TDD phases
- Eventually promoted to permanent test locations

### Traditional Contents (Enhanced)

#### `backlog.json`
Contains all project management data:
```json
{
  "epics": [
    {
      "id": "epic-001",
      "title": "User Authentication System",
      "description": "Complete user auth with login, registration, and session management",
      "created_at": "2024-01-15T10:30:00Z",
      "status": "active"
    }
  ],
  "stories": [
    {
      "id": "story-001",
      "epic_id": "epic-001",
      "title": "User login functionality",
      "description": "As a user, I want to log in with email/password",
      "acceptance_criteria": ["Login form validation", "Error handling", "Session creation"],
      "priority": 1,
      "status": "backlog",
      "sprint_id": null,
      "created_at": "2024-01-15T10:35:00Z"
    }
  ],
  "sprints": [
    {
      "id": "sprint-001",
      "goal": "Implement basic user authentication",
      "start_date": "2024-01-16",
      "end_date": "2024-01-30",
      "story_ids": ["story-001", "story-002"],
      "status": "active",
      "created_at": "2024-01-16T09:00:00Z"
    }
  ]
}
```

#### `sprints/` Directory
Individual sprint files with detailed information:
```json
{
  "id": "sprint-001",
  "goal": "Implement basic user authentication",
  "start_date": "2024-01-16",
  "end_date": "2024-01-30",
  "story_ids": ["story-001", "story-002"],
  "status": "completed",
  "retrospective": {
    "what_went_well": [
      "Good test coverage achieved",
      "Clear user stories helped focus development"
    ],
    "what_could_improve": [
      "Better estimation needed",
      "More frequent code reviews"
    ],
    "action_items": [
      "Implement automated testing pipeline",
      "Schedule daily standup meetings"
    ]
  }
}
```

#### `architecture.md`
Project-specific architectural decisions and design documentation:
```markdown
# Project Architecture

## Overview
This project implements a modern web application with React frontend and Node.js backend.

## Components
- Frontend: React 18 with TypeScript
- Backend: Node.js with Express
- Database: PostgreSQL with Prisma ORM
- Authentication: JWT with refresh tokens

## Design Decisions
- **Microservices**: Monolithic architecture chosen for simplicity
- **State Management**: Redux Toolkit for complex state scenarios
- **Testing**: Jest + React Testing Library for unit tests

## Dependencies
- External APIs: Stripe for payments, SendGrid for emails
- Third-party libraries: Material-UI for components

## Future Considerations
- Migration to microservices when scaling becomes necessary
- Implementation of GraphQL for more efficient data fetching
```

#### `best-practices.md`
Project-specific coding standards and AI agent guidelines:
```markdown
# Project Best Practices

## Code Standards
- Use TypeScript for all new code
- Follow ESLint and Prettier configurations
- Minimum 80% test coverage required

## Testing Strategy
- Unit tests for all business logic
- Integration tests for API endpoints
- E2E tests for critical user workflows

## Git Workflow
- Feature branches from main
- Pull request required for all changes
- Squash and merge strategy

## AI Agent Guidelines
- CodeAgent should follow existing patterns in src/utils/
- Use established error handling patterns
- Maintain consistency with existing component structure

## Review Process
- Automated tests must pass
- Code review by at least one team member
- Security review for authentication changes
```

#### `status.json`
Current workflow state and metadata with TDD integration:
```json
{
  "current_state": "SPRINT_ACTIVE",
  "orchestration_mode": "blocking",
  "last_updated": "2024-01-20T14:30:00Z",
  "active_tasks": [
    {
      "id": "task-001",
      "agent_type": "CodeAgent",
      "command": "Implement user login form",
      "status": "in_progress",
      "tdd_context": {
        "story_id": "AUTH-1",
        "current_tdd_state": "CODE_GREEN",
        "cycle_id": "cycle-abc123"
      }
    }
  ],
  "pending_approvals": ["story-003", "story-004"],
  "active_tdd_cycles": {
    "AUTH-1": "CODE_GREEN",
    "AUTH-2": "TEST_RED",
    "AUTH-3": "DESIGN"
  },
  "tdd_summary": {
    "total_cycles": 3,
    "completed_cycles": 0,
    "average_cycle_time": "0h 00m",
    "overall_test_coverage": 0.0
  }
}
```

#### TDD Cycle Data (`.orch-state/tdd/cycles/AUTH-1-cycle.json`)
Detailed TDD cycle state and progress:
```json
{
  "id": "cycle-abc123",
  "story_id": "AUTH-1",
  "current_state": "CODE_GREEN",
  "current_task_id": "task-def456",
  "tasks": [
    {
      "id": "task-def456",
      "description": "Implement user login validation",
      "current_state": "CODE_GREEN",
      "test_files": ["tests/tdd/AUTH-1/test_login.py"],
      "test_file_objects": [
        {
          "id": "testfile-ghi789",
          "file_path": "/project/tests/tdd/AUTH-1/test_login.py",
          "relative_path": "tests/tdd/AUTH-1/test_login.py",
          "status": "committed",
          "test_count": 5,
          "passing_tests": 5,
          "failing_tests": 0,
          "coverage_percentage": 92.5
        }
      ],
      "design_notes": "Login form with email/password validation",
      "implementation_notes": "Minimal implementation to pass tests"
    }
  ],
  "started_at": "2024-01-20T10:00:00Z",
  "total_test_runs": 12,
  "total_commits": 3,
  "ci_status": "passed",
  "overall_test_coverage": 92.5
}
```

#### Test Results Data (`.orch-state/tdd/test-results/AUTH-1-results.json`)
Test execution history and metrics:
```json
{
  "story_id": "AUTH-1",
  "cycle_id": "cycle-abc123",
  "latest_results": [
    {
      "id": "result-jkl012",
      "test_file": "tests/tdd/AUTH-1/test_login.py",
      "test_name": "test_valid_login",
      "status": "green",
      "execution_time": 0.045,
      "timestamp": "2024-01-20T14:25:00Z"
    }
  ],
  "test_run_history": [
    {
      "timestamp": "2024-01-20T14:25:00Z",
      "total_tests": 5,
      "passing": 5,
      "failing": 0,
      "coverage": 92.5,
      "phase": "CODE_GREEN"
    }
  ],
  "coverage_trend": {
    "baseline": 0.0,
    "current": 92.5,
    "target": 90.0,
    "trend": "increasing"
  }
}
```

## Version Control Integration

### Enhanced Git Integration (with TDD Support)
- All `.orch-state/` files are version controlled (workflow + TDD data)
- TDD cycle changes tracked alongside code modifications
- Test file preservation through git commits during TDD phases
- Sprint data and TDD metrics preserved in project history
- Architecture decisions and TDD insights documented over time
- Complete TDD audit trail from design through commit phases

### Enhanced Branching Strategy (with TDD Support)
- `.orch-state/` changes typically made on main branch (workflow + TDD data)
- Sprint planning updates committed as project milestones with TDD cycle initialization
- Feature branches may update story status and TDD cycle progress
- TDD test files committed during RED phase to preserve failing tests
- Code implementation committed during GREEN phase with passing tests
- Refactored code committed during REFACTOR phase with continued test success

### Enhanced Conflict Resolution (with TDD Support)
- Merge conflicts in `.orch-state/` resolved like any code (workflow + TDD data)
- Orchestrator detects and reports dual state inconsistencies
- TDD cycle conflicts resolved with test preservation priority
- Manual intervention required for complex workflow and TDD conflicts
- Test file conflicts resolved with latest working test version

## Data Ownership

### Enhanced Project Data (with TDD Support)
- **Belongs to Project**: Stories, epics, sprints, architecture decisions, TDD cycles, test results
- **Versioned with Code**: All management and TDD data tracked in git
- **Project-Specific**: No shared data between projects or TDD cycles
- **Story-Level TDD Isolation**: TDD cycles and test files isolated per story

### Orchestration Data
- **Belongs to Orchestrator**: Agent definitions, security policies
- **Global Configuration**: Shared across all projects
- **Runtime State**: Project registration and channel mappings

## Benefits of Repository Co-location

### Consistency
- Project management data evolves with code
- Architecture decisions documented alongside implementation
- Sprint retrospectives linked to specific code versions

### Auditability
- Complete history of project decisions
- Correlation between features and planning data
- Compliance and tracking for regulated environments

### Portability
- Projects can be moved between orchestration instances
- Self-contained project data travels with repository
- No external dependencies for project management data

## Access Patterns

### Enhanced Read Access (with TDD Support)
- Orchestrator reads project workflow and TDD state
- Discord Bot displays current workflow and TDD status with progress
- Agents access project and TDD context for decision making
- TDD agents read test files and execution results for phase coordination

### Enhanced Write Access (with TDD Support)
- Only orchestrator writes to `.orch-state/` (workflow + TDD data)
- TDD agents write to `tests/tdd/` directory during appropriate phases
- Changes made through Discord workflow and TDD commands
- Agent results persisted automatically in appropriate storage locations
- Test files preserved through TDD phase transitions

### Enhanced Security (with TDD Support)
- Repository access controls apply to workflow and TDD data
- No cross-project or cross-story TDD data leakage
- TDD phase-specific access controls for test file modifications
- Standard git permissions model used for both code and test artifacts
- Story-level TDD isolation enforced through directory structure and access controls