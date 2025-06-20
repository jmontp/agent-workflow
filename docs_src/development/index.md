# 👨‍💻 Development

Development guides for contributors and system maintainers.

## Contributing to the Project

Welcome to the development documentation for the AI Agent TDD-Scrum Workflow system. This section provides comprehensive guides for contributors and system maintainers.

<div class="grid cards" markdown>

-   :material-git:{ .lg .middle } **Contributing**

    ---
    
    Guidelines for contributing code, documentation, and features
    
    [:octicons-arrow-right-24: Contributing](contributing.md)

-   :material-api:{ .lg .middle } **API Reference**

    ---
    
    Complete API documentation for system components
    
    [:octicons-arrow-right-24: API Docs](api-reference.md)

-   :material-tools:{ .lg .middle } **Development Tools**

    ---
    
    Suite of utilities for testing, monitoring, and documentation
    
    [:octicons-arrow-right-24: Dev Tools](development-tools.md)

</div>

## Development Environment

### Prerequisites

- **Python 3.8+** with virtual environment support
- **Git** for version control
- **Discord Bot Token** for testing
- **pytest** for running tests
- **mkdocs-material** for documentation

### Setup

```bash
# Clone the repository
git clone https://github.com/jmontp/agent-workflow.git
cd agent-workflow

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Install in development mode
pip install -e .
```

### Development Commands

```bash
# Run tests
pytest tests/                    # Full test suite
pytest tests/unit/              # Unit tests only
pytest tests/integration/       # Integration tests only
pytest -m "not slow"           # Skip slow tests

# Code quality
black lib/ tests/               # Format code
flake8 lib/ tests/              # Lint code
mypy lib/                       # Type checking

# Documentation
mkdocs serve                    # Local development server
mkdocs build                    # Build static site
```

## Architecture for Developers

### Code Organization

```
lib/
├── agents/                     # AI agent implementations
├── state_machine.py           # Workflow state management
├── discord_bot.py             # HITL interface
├── data_models.py             # Data structures
├── project_storage.py         # Persistence layer
└── security/                  # Security controls

scripts/
├── orchestrator.py            # Main entry point
└── utilities/                 # Helper scripts

tests/
├── unit/                      # Unit tests
├── integration/               # Integration tests
└── fixtures/                  # Test data
```

### Key Patterns

- **Agent Base Class**: All agents inherit from `BaseAgent`
- **State Machine**: Finite state machine with strict validation
- **Security Boundaries**: Tool access control per agent type
- **Async/Await**: Asynchronous agent execution
- **Type Hints**: Full type annotation coverage

## Testing Strategy

### Test Categories

1. **Unit Tests**: Individual component testing
2. **Integration Tests**: Component interaction testing
3. **E2E Tests**: Complete workflow testing
4. **Security Tests**: Access control validation

### Test Structure

```python
# Unit test example
class TestStateTransitions:
    def test_idle_to_backlog_ready(self):
        sm = StateMachine()
        result = sm.handle_command("/epic", "test epic")
        assert result.new_state == State.BACKLOG_READY

# Integration test example
class TestAgentCoordination:
    async def test_design_to_qa_handoff(self):
        design_agent = DesignAgent()
        qa_agent = QAAgent()
        
        design_result = await design_agent.run(task)
        qa_result = await qa_agent.run(design_result.output)
        
        assert qa_result.tests_created > 0
```

### Test Coverage

Target: >90% code coverage

```bash
# Generate coverage report
pytest --cov=lib --cov-report=html tests/
open htmlcov/index.html
```

## Security Development

### Agent Security Model

Each agent type has specific tool restrictions:

```python
# Example security configuration
AGENT_TOOL_CONFIG = {
    'CodeAgent': {
        'allowed': ['file_edit', 'git_commit', 'pytest'],
        'blocked': ['rm', 'git_push', 'sudo']
    },
    'DesignAgent': {
        'allowed': ['file_read', 'web_search'],
        'blocked': ['file_edit', 'git_commit', 'rm']
    }
}
```

### Security Testing

All security boundaries must be tested:

```python
def test_design_agent_cannot_edit_files():
    agent = DesignAgent()
    with pytest.raises(SecurityError):
        agent.edit_file("test.py", "malicious code")
```

## API Development

### Adding New Commands

1. **Define Command**: Add to Discord bot command handlers
2. **State Validation**: Ensure command is valid for current state
3. **Agent Integration**: Connect to appropriate agent type
4. **Security Check**: Validate access permissions
5. **Tests**: Add comprehensive test coverage

### Example Command Implementation

```python
@bot.slash_command(name="new_command")
async def new_command(ctx, parameter: str):
    # Validate current state
    if not state_machine.can_execute_command("new_command"):
        await ctx.respond("Command not available in current state")
        return
    
    # Execute with appropriate agent
    agent = AgentFactory.create_agent("CommandAgent")
    result = await agent.run(parameter)
    
    # Update state if needed
    state_machine.transition_to_new_state(result)
    
    await ctx.respond(f"Command completed: {result.summary}")
```

## Release Process

### Version Management

- **Semantic Versioning**: MAJOR.MINOR.PATCH
- **Release Branches**: `release/vX.Y.Z`
- **Hotfix Branches**: `hotfix/vX.Y.Z`

### Release Checklist

1. **Update Version**: Bump version in `__init__.py`
2. **Update Changelog**: Document all changes
3. **Run Full Tests**: Ensure all tests pass
4. **Security Audit**: Validate security controls
5. **Documentation**: Update docs if needed
6. **Create Release**: Tag and create GitHub release

## Troubleshooting Development Issues

### Common Issues

1. **Import Errors**: Check Python path and virtual environment
2. **Test Failures**: Ensure test database is clean
3. **Discord Bot**: Verify token and permissions
4. **Agent Errors**: Check security configuration

### Debugging

```python
# Enable debug logging
import logging
logging.basicConfig(level=logging.DEBUG)

# Use debugger
import pdb; pdb.set_trace()

# Agent debugging
agent = DesignAgent(debug=True)
```

## Getting Help

- **GitHub Issues**: Report bugs and feature requests
- **Discussions**: Ask questions and share ideas
- **Discord**: Join the development community
- **Documentation**: Check existing docs first

## Next Steps

- **[Contributing Guidelines](contributing.md)** - Detailed contribution process
- **[API Reference](api-reference.md)** - Complete API documentation
- **[Testing Strategy](../advanced/testing.md)** - Comprehensive testing approach