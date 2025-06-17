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