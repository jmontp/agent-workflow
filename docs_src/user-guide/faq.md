# Frequently Asked Questions

Common questions about the AI Agent TDD-Scrum workflow system.

## General Questions

### What is the AI Agent TDD-Scrum workflow system?

It's a Human-In-The-Loop (HITL) orchestration framework that coordinates multiple specialized AI agents through Discord. The system follows a research-mode Scrum methodology optimized for solo engineers working with AI assistance.

### Do I need AI integration to use the system?

No, the system works without AI integration for testing and learning the workflow. However, you'll need AI capabilities (like Claude Code) for the agents to actually perform development tasks.

### Can I use this with multiple projects?

Yes, the orchestrator supports multi-project management. Each project gets its own Discord channel and independent state machine.

## Setup and Installation

### What are the minimum requirements?

- Python 3.8 or higher
- Discord bot token
- Git for cloning the repository
- Optional: Claude Code or other AI integration for full functionality

### How do I get a Discord bot token?

1. Go to the [Discord Developer Portal](https://discord.com/developers/applications)
2. Create a new application
3. Go to the "Bot" section
4. Click "Reset Token" and copy the token
5. Invite the bot to your server with appropriate permissions

### Can I run this on Windows/Mac/Linux?

Yes, the system is cross-platform and works on all major operating systems. It's been tested on Windows (including WSL), macOS, and various Linux distributions.

## Workflow and Commands

### What's the difference between an epic and a story?

- **Epic**: A high-level initiative or feature area (e.g., "Build authentication system")
- **Story**: A specific, actionable task within an epic (e.g., "Create user login form")

### Why can't I run certain commands?

The system uses a finite state machine that enforces proper workflow sequences. Use the `/state` command to see which commands are currently available.

### How do I know what state I'm in?

Use the `/state` command anytime to see:
- Current state (e.g., SPRINT_ACTIVE)
- Allowed commands for that state
- Visual state diagram
- Command matrix

### Can I pause a sprint mid-execution?

Yes, use `/sprint pause` to halt agent work. Resume with `/sprint resume` when ready to continue.

## Agents and AI Integration

### What do the different agents do?

- **DesignAgent**: Creates architecture, designs components, writes specifications
- **CodeAgent**: Implements features, fixes bugs, refactors code
- **QAAgent**: Creates tests, validates quality, analyzes coverage
- **DataAgent**: Analyzes data, creates reports, generates visualizations

### How do agents know what to work on?

Agents receive tasks from the orchestrator based on:
- Stories in the current sprint
- Their specialized capabilities
- Human-provided context and requirements

### Can I give direct instructions to agents?

Yes, use commands like:
- `/suggest_fix "description"` to guide a stuck agent
- `/request_changes "description"` to modify agent output
- `/feedback "description"` to provide general improvement notes

### What happens if an agent gets stuck?

The system has escalation policies:
- After 3 failed attempts, tasks escalate to human review
- You can use `/suggest_fix` to provide guidance
- Use `/skip_task` to abandon problematic tasks

## Security and Permissions

### Are there security restrictions on agents?

Yes, each agent type has specific tool access controls:
- **DesignAgent**: Read-only access, can create documentation
- **CodeAgent**: Can edit code and commit changes
- **QAAgent**: Can run tests and quality tools only
- **DataAgent**: Can access data files and create visualizations

### Can agents modify any file in my project?

Agents respect security boundaries and can only access files within their permitted scope. The system uses principle of least privilege.

### Is my code sent to external AI services?

This depends on your AI integration choice. The framework itself doesn't send code externally, but integrated AI services (like Claude Code) may process code according to their terms of service.

## Troubleshooting

### The bot doesn't respond to my commands

Check these common issues:
1. Verify the Discord bot token is set correctly
2. Ensure the bot has proper permissions in your server
3. Make sure you're using slash commands (type `/` to see available commands)

### My tests are failing

Try these solutions:
1. Run unit tests only: `pytest tests/unit/`
2. Ensure all dependencies are installed: `pip install -r requirements.txt`
3. Check that environment variables are set properly

### The system seems slow

Performance can be affected by:
- Network connectivity to Discord and AI services
- Size and complexity of tasks
- System resources (CPU, memory)
- Number of concurrent projects

## Advanced Usage

### Can I customize the workflow states?

The state machine is designed to be extensible, but modifications require code changes. The current states cover most common development workflows.

### How do I integrate with other tools?

The system is designed to be modular. You can:
- Add new agent types
- Integrate additional AI services
- Connect to different project management tools
- Extend the Discord bot with custom commands

### Can I run this in production?

The system is suitable for development workflows. For production use, consider:
- Proper error handling and monitoring
- Backup and recovery procedures
- Security review of AI integrations
- Performance optimization for your scale

### How do I contribute to the project?

1. Fork the repository
2. Create a feature branch
3. Implement changes with tests
4. Submit a pull request
5. Follow the contributing guidelines in the repository

## Best Practices

### How should I structure my epics and stories?

- Keep epics focused on specific feature areas
- Write stories as user-focused requirements
- Break large stories into smaller, manageable tasks
- Prioritize stories based on business value

### What's the optimal sprint length?

For solo development with AI assistance:
- Start with 1-2 week sprints
- Adjust based on task complexity and AI performance
- Consider shorter sprints for learning and experimentation

### How do I get the best results from AI agents?

- Provide clear, specific requirements
- Include context about existing code and patterns
- Use descriptive names for features and stories
- Give feedback regularly to improve agent performance

## TDD Workflow Questions

### What is the TDD workflow in the AI Agent system?

The system implements a parallel TDD state machine that runs alongside the main Scrum workflow. Each story in an active sprint follows a strict Test-Driven Development cycle: DESIGN → TEST_RED → CODE_GREEN → REFACTOR → COMMIT.

### How does TDD work with multiple stories?

Multiple stories can run TDD cycles simultaneously. Each story has its own independent TDD state machine, allowing parallel development while maintaining TDD discipline for each feature.

### What are the TDD states and what happens in each?

- **DESIGN**: Design Agent creates technical specifications and acceptance criteria
- **TEST_RED**: QA Agent writes comprehensive failing tests based on specifications  
- **CODE_GREEN**: Code Agent implements minimal code to make tests pass
- **REFACTOR**: Code Agent improves code quality while keeping tests green
- **COMMIT**: Final commit with complete feature and clean code

### How do I monitor TDD progress?

Use these commands:
- `/tdd overview` - See status of all active TDD cycles
- `/tdd status <STORY_ID>` - Get detailed information for a specific story
- `/tdd metrics` - View cycle times, success rates, and quality metrics

### Can I control the TDD cycle manually?

Yes, you have several control options:
- `/tdd pause <STORY_ID>` - Temporarily halt a TDD cycle
- `/tdd resume <STORY_ID>` - Resume a paused cycle
- `/tdd skip_phase <STORY_ID>` - Skip current phase (requires approval)
- `/tdd review_cycle <STORY_ID>` - Request human review at any phase

### What happens if a TDD cycle gets stuck?

The system has several recovery mechanisms:
- After failed attempts, tasks escalate to human review
- Use `/suggest_fix "description"` to provide guidance to agents
- Use `/tdd skip_phase` to move past problematic phases
- Human approval gates allow intervention at any point

### How do I ensure test quality in TDD cycles?

The system enforces several quality gates:
- Tests must fail initially (RED state) before implementation
- All tests must pass before refactoring (GREEN requirement)
- Code coverage thresholds are maintained
- CI integration validates all changes

### Can I run traditional sprints without TDD?

Yes, TDD is optional. Stories without TDD requirements follow the traditional agent workflow. You can mix TDD and non-TDD stories within the same sprint.

### How does TDD integrate with CI/CD?

TDD cycles integrate with CI/CD pipelines:
- Tests are committed in RED state for continuous validation
- Implementation commits trigger CI builds
- Quality gates can include external tools (SonarQube, security scans)
- Failed CI runs pause TDD cycles for human intervention

### What metrics does the TDD system track?

Key metrics include:
- Cycle time per TDD phase
- Success rates for each state transition
- Test coverage percentages
- Refactor frequency and impact
- CI success rates and failure patterns

### How do I troubleshoot stuck TDD cycles?

Common issues and solutions:

**Cycle stuck in CODE_GREEN:**
- Check test failures in CI logs
- Provide guidance with `/suggest_fix`
- Consider `/tdd skip_phase` if persistently blocked

**Tests failing after refactor:**
- System automatically rolls back to last green state
- Use `/tdd review_cycle` for manual intervention
- Adjust refactor scope and retry

**Design phase taking too long:**
- Check story complexity and requirements clarity
- Use `/tdd design_complete` to manually advance
- Consider splitting complex stories

### Are there different TDD profiles for different story types?

Yes, you can configure TDD parameters:
- Coverage thresholds per story type
- Complexity limits for different components
- Custom phase timeouts for API vs UI development
- Different quality gates for critical vs non-critical features

### How do TDD cycles handle dependencies between stories?

TDD supports story dependencies:
- Stories can wait for other stories to complete specific phases
- Use `/tdd depends <STORY_A> <STORY_B>` to define dependencies
- Dependency chains are visualized in `/tdd overview`
- Circular dependencies are detected and prevented

### Can I integrate external quality tools with TDD?

Yes, TDD cycles support external tool integration:
- Security scanning during CODE_GREEN phase
- Performance benchmarking during REFACTOR
- Custom quality gates with `/tdd gate` commands
- Manual overrides with justification tracking

### What's the difference between TDD commit types?

TDD uses incremental commits to preserve test development:
- `/tdd commit-tests` - Commits failing tests (TEST_RED → CODE_GREEN)
- `/tdd commit-code` - Commits working implementation (CODE_GREEN → REFACTOR)  
- `/tdd commit-refactor` - Commits refactored code (REFACTOR → COMMIT)
- `/tdd commit` - Final commit when satisfied with quality

This approach ensures tests are preserved in the repository even if implementation fails, maintaining TDD audit trail.