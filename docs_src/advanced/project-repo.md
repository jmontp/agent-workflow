# Project Repository Architecture

Project repositories contain the actual code being developed with AI assistance. Each project repository maintains its own project management data and state while being coordinated by the orchestration system.

## Repository Structure

```
project-repository/
├── src/                     # Project source code
├── tests/                   # Project tests
├── .git/                    # Git repository
├── .orch-state/            # AI workflow state (managed by orchestration)
│   ├── backlog.json        # Epics, stories, and priorities
│   ├── sprints/            # Sprint data and retrospectives
│   │   ├── sprint-abc123.json
│   │   └── sprint-def456.json
│   ├── architecture.md     # Project-specific architecture decisions
│   ├── best-practices.md   # Project conventions and patterns
│   └── status.json         # Current workflow state
└── README.md               # Project documentation
```

## `.orch-state/` Directory

### Purpose
The `.orch-state/` directory stores all AI workflow-related data within the project repository, ensuring that project management information is version-controlled alongside the code.

### Contents

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
Current workflow state and metadata:
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
      "status": "in_progress"
    }
  ],
  "pending_approvals": ["story-003", "story-004"]
}
```

## Version Control Integration

### Git Integration
- All `.orch-state/` files are version controlled
- Changes tracked alongside code modifications
- Sprint data preserved in project history
- Architecture decisions documented over time

### Branching Strategy
- `.orch-state/` changes typically made on main branch
- Sprint planning updates committed as project milestones
- Feature branches may update story status

### Conflict Resolution
- Merge conflicts in `.orch-state/` resolved like any code
- Orchestrator detects and reports state inconsistencies
- Manual intervention required for complex conflicts

## Data Ownership

### Project Data
- **Belongs to Project**: Stories, epics, sprints, architecture decisions
- **Versioned with Code**: All management data tracked in git
- **Project-Specific**: No shared data between projects

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

### Read Access
- Orchestrator reads project state and data
- Discord Bot displays current status and history
- Agents access project context for decision making

### Write Access
- Only orchestrator writes to `.orch-state/`
- Changes made through Discord commands
- Agent results persisted automatically

### Security
- Repository access controls apply to workflow data
- No cross-project data leakage
- Standard git permissions model used