# Project Setup Guide

This guide explains how to set up and register new project repositories with the AI Agent TDD-Scrum workflow system.

## Prerequisites

1. **Git Repository**: Your project must be a valid git repository
2. **Discord Access**: Access to the Discord server with the workflow bot
3. **Project Permissions**: Write access to the project repository

## Registration Process

### Step 1: Prepare Your Project Repository

Ensure your project is a valid git repository:

```bash
# Navigate to your project
cd /path/to/your/project

# Verify git repository
git status

# Ensure you have at least one commit
git log --oneline -1
```

### Step 2: Register with Discord Bot

Use the `/project register` command in Discord:

```
/project register path:/path/to/your/project
```

Optional: Specify a custom project name:
```
/project register path:/path/to/your/project name:my-custom-name
```

### Step 3: Verify Registration

The bot will:
1. ✅ Validate the path exists and is a git repository
2. ✅ Check for naming conflicts
3. ✅ Create a Discord channel `{hostname}-{projectname}`
4. ✅ Initialize the `.orch-state/` directory structure
5. ✅ Add the project to the orchestration system

## Project Structure After Registration

After successful registration, your project will have:

```
your-project/
├── .git/                   # Existing git repository
├── src/                    # Your existing code
├── .orch-state/           # New: AI workflow state
│   ├── backlog.json       # Empty project management data
│   ├── sprints/           # Directory for sprint history
│   │   └── .gitkeep       # Placeholder file
│   ├── architecture.md    # Template architecture decisions
│   ├── best-practices.md  # Template project conventions
│   └── status.json        # Current workflow state
└── [your existing files]
```

## Initial Configuration

### Architecture Documentation

Edit `.orch-state/architecture.md` to document your project's architecture:

```markdown
# Project Architecture

## Overview
Brief description of your project's architecture and purpose.

## Components
- Component 1: Description
- Component 2: Description

## Design Decisions
- Decision 1: Rationale
- Decision 2: Rationale

## Dependencies
- External APIs and services
- Key libraries and frameworks

## Future Considerations
- Planned improvements
- Technical debt items
```

### Best Practices

Update `.orch-state/best-practices.md` with project-specific guidelines:

```markdown
# Project Best Practices

## Code Standards
- Coding conventions specific to your project
- Style guidelines and formatting rules

## Testing Strategy
- Testing frameworks and approaches
- Coverage requirements

## Git Workflow
- Branching strategy
- Commit message conventions

## AI Agent Guidelines
- Project-specific instructions for AI agents
- Patterns and conventions to follow

## Review Process
- Code review requirements
- Approval workflows
```

## Discord Channel Usage

### Channel Naming Convention

Channels are automatically created with the pattern:
```
{hostname}-{projectname}
```

For example:
- `devbox-myproject`
- `laptop-ecommerce-site`
- `server-api-gateway`

### Available Commands

Once registered, use these commands in your project channel:

#### Epic Management
```
/epic "Implement user authentication system"
```

#### Backlog Management
```
/backlog view
/backlog add_story title:"User login" description:"Login functionality"
/backlog prioritize story_id:story-123 priority:1
```

#### Sprint Management
```
/sprint plan
/sprint start
/sprint status
/sprint pause
/sprint resume
```

#### Workflow Control
```
/approve
/request_changes "Need better error handling"
/state
```

## Common Setup Scenarios

### New Project Setup

For a brand new project:

1. Create and initialize git repository:
   ```bash
   mkdir my-new-project
   cd my-new-project
   git init
   git commit --allow-empty -m "Initial commit"
   ```

2. Register with Discord bot:
   ```
   /project register path:/path/to/my-new-project
   ```

3. Start with epic definition:
   ```
   /epic "Build MVP for user management system"
   ```

### Existing Project Integration

For an existing project with code:

1. Ensure git repository is current:
   ```bash
   cd /path/to/existing/project
   git status
   git add .
   git commit -m "Prepare for AI workflow integration"
   ```

2. Register project:
   ```
   /project register path:/path/to/existing/project
   ```

3. Document current architecture:
   - Edit `.orch-state/architecture.md`
   - Update `.orch-state/best-practices.md`

4. Create initial epic for next phase:
   ```
   /epic "Modernize authentication system"
   ```

### Multiple Environment Setup

For projects with different environments:

1. Register each environment separately:
   ```
   /project register path:/path/to/project-dev name:myproject-dev
   /project register path:/path/to/project-staging name:myproject-staging
   /project register path:/path/to/project-prod name:myproject-prod
   ```

2. Each gets its own Discord channel:
   - `#hostname-myproject-dev`
   - `#hostname-myproject-staging`
   - `#hostname-myproject-prod`

## Troubleshooting

### Registration Failures

**Error: "Path does not exist"**
- Verify the path is correct and accessible
- Use absolute paths, not relative paths

**Error: "Path is not a git repository"**
- Run `git init` in the directory
- Ensure `.git` directory exists

**Error: "Project already registered"**
- Use a different project name
- Check existing projects with `/state`

**Error: "Channel already exists"**
- Another project may be using the same name
- This could indicate a naming conflict or duplicate registration

### Post-Registration Issues

**Cannot find project channel**
- Check channel naming: `{hostname}-{projectname}`
- Verify you have permission to see the channel
- Bot may need time to create the channel

**Commands not working**
- Ensure you're in the correct project channel
- Check bot permissions
- Verify project is in correct state with `/state`

## Best Practices

### Project Organization

1. **Clear Naming**: Use descriptive project names
2. **Consistent Structure**: Follow established patterns
3. **Documentation**: Keep architecture and practices current
4. **Git Hygiene**: Regular commits and clean history

### Workflow Integration

1. **Start Small**: Begin with simple epics and stories
2. **Iterative Approach**: Use short sprints initially
3. **Regular Reviews**: Conduct sprint retrospectives
4. **Continuous Improvement**: Update practices based on experience

### Team Coordination

1. **Channel Discipline**: Use project-specific channels
2. **Clear Communication**: Document decisions in architecture.md
3. **Approval Process**: Establish clear approval workflows
4. **Regular Standups**: Coordinate with team members

## Security Considerations

### Repository Access

- Workflow bot requires read/write access to `.orch-state/` directory
- Bot cannot access other project files without explicit permissions
- Standard git permissions model applies

### Data Privacy

- Project management data stored in project repository
- No external data storage or transmission
- Audit trail maintained in git history

### Discord Permissions

- Project channels provide access control
- Bot permissions scoped to workflow operations
- Team members need appropriate Discord roles

## TDD Workflow Setup

### Prerequisites for TDD Integration

Before enabling TDD workflows, ensure your project meets these requirements:

1. **Testing Framework**: Your project must have a test framework configured (pytest, unittest, jest, etc.)
2. **CI/CD Pipeline**: Basic CI integration for automated test execution
3. **Project Structure**: Clear separation between source and test directories
4. **Coverage Tools**: Code coverage measurement tools installed

### Enabling TDD Mode

#### Step 1: Configure TDD Settings

Create or update `.orch-state/tdd-config.json`:

```json
{
  "tdd_enabled": true,
  "test_framework": "pytest",
  "test_directory": "tests",
  "tdd_test_directory": "tests/tdd",
  "coverage_threshold": 90.0,
  "quality_gates": {
    "complexity_limit": 10,
    "duplication_threshold": 5.0,
    "security_scan": true
  },
  "ci_integration": {
    "enabled": true,
    "provider": "github_actions",
    "trigger_on_commit": true
  },
  "auto_progression": {
    "enabled": false,
    "require_human_approval": true,
    "stuck_cycle_timeout": 30
  }
}
```

#### Step 2: Test Framework Setup

**For Python projects (pytest):**

```bash
# Install dependencies
pip install pytest pytest-cov pytest-xdist

# Create pytest.ini
cat > pytest.ini << EOF
[tool:pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = --cov=src --cov-report=html --cov-report=term-missing
EOF
```

**For JavaScript projects (jest):**

```bash
# Install dependencies
npm install --save-dev jest @jest/globals

# Create jest.config.js
cat > jest.config.js << EOF
module.exports = {
  testEnvironment: 'node',
  coverageDirectory: 'coverage',
  collectCoverageFrom: [
    'src/**/*.js',
    '!src/**/*.test.js'
  ],
  testMatch: ['**/tests/**/*.test.js']
};
EOF
```

#### Step 3: Directory Structure Setup

The TDD workflow requires specific directory organization:

```
your-project/
├── src/                      # Source code
├── tests/
│   ├── unit/                # Permanent unit tests
│   ├── integration/         # Permanent integration tests
│   └── tdd/                 # TDD workspace (managed by system)
│       ├── AUTH-001/        # Story-specific tests
│       │   ├── test_login.py
│       │   └── test_auth.py
│       └── USER-002/
│           └── test_profile.py
├── .orch-state/
│   ├── tdd-config.json      # TDD configuration
│   ├── tdd-cycles/          # Active TDD cycle data
│   │   ├── AUTH-001.json    # TDD cycle state
│   │   └── USER-002.json
│   └── tdd-metrics.json     # Performance metrics
└── [existing project files]
```

#### Step 4: CI/CD Integration

**GitHub Actions (`.github/workflows/tdd.yml`):**

```yaml
name: TDD Workflow

on:
  push:
    paths:
      - 'tests/tdd/**'
      - 'src/**'
  pull_request:
    paths:
      - 'tests/tdd/**'
      - 'src/**'

jobs:
  tdd-validation:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.9'
      
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install pytest pytest-cov
      
      - name: Run TDD tests
        run: |
          pytest tests/tdd/ --cov=src --cov-fail-under=90
      
      - name: Validate RED state
        if: contains(github.ref, 'tdd-red')
        run: |
          # Expect tests to fail in RED state
          pytest tests/tdd/ || true
      
      - name: Validate GREEN state
        if: contains(github.ref, 'tdd-green')
        run: |
          # Expect all tests to pass in GREEN state
          pytest tests/tdd/ --cov=src --cov-fail-under=90
      
      - name: Upload coverage
        uses: codecov/codecov-action@v3
```

### TDD Workflow Configuration Options

#### Coverage Requirements

Configure different coverage thresholds for different story types:

```json
{
  "coverage_profiles": {
    "critical": {
      "threshold": 95.0,
      "branch_coverage": 90.0,
      "exclude_patterns": []
    },
    "standard": {
      "threshold": 90.0,
      "branch_coverage": 80.0,
      "exclude_patterns": ["**/migrations/**"]
    },
    "experimental": {
      "threshold": 75.0,
      "branch_coverage": 70.0,
      "exclude_patterns": ["**/prototypes/**"]
    }
  }
}
```

#### Quality Gates

Define automated quality checks:

```json
{
  "quality_gates": {
    "static_analysis": {
      "enabled": true,
      "tools": ["pylint", "mypy", "black"],
      "fail_threshold": "error"
    },
    "security_scan": {
      "enabled": true,
      "tools": ["bandit", "safety"],
      "fail_on_high": true
    },
    "performance": {
      "enabled": true,
      "max_execution_time": 5.0,
      "memory_threshold": "100MB"
    },
    "complexity": {
      "enabled": true,
      "cyclomatic_complexity": 10,
      "cognitive_complexity": 15
    }
  }
}
```

#### Agent Behavior Configuration

Customize how TDD agents operate:

```json
{
  "agent_config": {
    "design_agent": {
      "design_template": "api_specification",
      "include_acceptance_criteria": true,
      "generate_test_scenarios": true
    },
    "qa_agent": {
      "test_types": ["unit", "integration", "edge_cases"],
      "mock_external_dependencies": true,
      "generate_test_data": true,
      "ensure_red_state": true
    },
    "code_agent": {
      "minimal_implementation": true,
      "avoid_premature_optimization": true,
      "follow_design_patterns": ["SOLID", "DRY"]
    }
  }
}
```

### TDD-Specific Project Templates

#### API Development Template

```json
{
  "project_type": "api",
  "tdd_config": {
    "test_patterns": {
      "unit": "test_unit_*.py",
      "integration": "test_api_*.py",
      "contract": "test_contract_*.py"
    },
    "phases": {
      "design": {
        "artifacts": ["openapi_spec", "data_models", "error_schemas"],
        "validation": "schema_validation"
      },
      "test_red": {
        "test_types": ["unit", "integration", "contract"],
        "mock_strategy": "external_services"
      },
      "code_green": {
        "implementation_style": "minimal_viable",
        "database_strategy": "in_memory"
      },
      "refactor": {
        "focus_areas": ["performance", "security", "maintainability"]
      }
    }
  }
}
```

#### Frontend Component Template

```json
{
  "project_type": "frontend",
  "tdd_config": {
    "test_patterns": {
      "unit": "*.test.js",
      "integration": "*.integration.test.js",
      "e2e": "*.e2e.test.js"
    },
    "testing_library": "react-testing-library",
    "phases": {
      "design": {
        "artifacts": ["component_interface", "props_schema", "state_diagram"],
        "validation": "typescript_compilation"
      },
      "test_red": {
        "test_types": ["unit", "integration"],
        "mock_strategy": "api_calls"
      },
      "code_green": {
        "implementation_style": "component_first",
        "styling_approach": "css_modules"
      }
    }
  }
}
```

### TDD Project Initialization

#### New Project with TDD

For new projects starting with TDD:

```bash
# Create project structure
mkdir my-tdd-project
cd my-tdd-project
git init

# Initialize TDD-ready structure
mkdir -p src tests/{unit,integration,tdd} .orch-state

# Register with TDD enabled
/project register path:/path/to/my-tdd-project
# System detects TDD configuration and enables TDD mode

# Create first epic with TDD
/epic "Build user authentication system with TDD"
/tdd configure AUTH coverage_profile:critical
```

#### Existing Project TDD Migration

For existing projects adopting TDD:

```bash
# Backup existing tests
cp -r tests tests_backup

# Create TDD structure
mkdir -p tests/tdd .orch-state/tdd-cycles

# Move existing tests to permanent locations
mv tests/test_*.py tests/unit/
mv tests/integration_*.py tests/integration/

# Enable TDD mode
echo '{"tdd_enabled": true}' > .orch-state/tdd-config.json

# Re-register project to detect TDD
/project register path:/path/to/existing/project
```

### TDD Troubleshooting Setup

#### Common Setup Issues

**TDD directory not created:**
- Verify `.orch-state/tdd-config.json` exists
- Check project registration detected TDD configuration
- Ensure bot has write permissions to project directory

**Tests not running in CI:**
- Verify test framework is properly configured
- Check CI workflow includes TDD test paths
- Ensure coverage tools are installed in CI environment

**Agent access errors:**
- Verify agent security profiles allow TDD operations
- Check file permissions in tests/tdd/ directory
- Ensure git repository allows automated commits

#### Validation Commands

Verify TDD setup is working:

```bash
# Check TDD configuration
/tdd status

# Validate test framework
pytest tests/tdd/ --collect-only

# Verify CI integration
git add .orch-state/tdd-config.json
git commit -m "Enable TDD workflow"
git push  # Should trigger CI validation

# Test agent permissions
/tdd start TEST-001  # Should create TDD cycle
```

### TDD Best Practices for Setup

#### Project Organization

1. **Separate TDD Workspace**: Keep TDD tests separate from permanent test suite
2. **Story-Based Organization**: Organize TDD tests by story ID for clarity
3. **Clear Naming Conventions**: Use consistent naming for TDD test files
4. **Version Control Integration**: Ensure TDD artifacts are properly tracked

#### CI/CD Configuration

1. **Separate TDD Pipelines**: Different CI behavior for RED vs GREEN states
2. **Quality Gate Integration**: Automated quality checks at each TDD phase
3. **Artifact Preservation**: Maintain TDD test history for audit trails
4. **Performance Monitoring**: Track TDD cycle times and success rates

#### Team Coordination

1. **Shared TDD Standards**: Document TDD practices for the team
2. **Review Processes**: Define review requirements for TDD phases
3. **Escalation Procedures**: Clear processes when TDD cycles get stuck
4. **Metrics Tracking**: Regular review of TDD performance metrics

With this setup, your project will be fully configured for TDD workflows with proper tooling, CI integration, and team processes.