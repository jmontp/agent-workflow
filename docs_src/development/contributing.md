# Contributing

Welcome to the AI Agent TDD-Scrum Workflow project! We appreciate your interest in contributing.

## Getting Started

### Prerequisites

- Python 3.8 or higher
- Git for version control
- Discord account for testing bot functionality
- Basic understanding of async Python programming

### Development Setup

1. **Fork and clone the repository:**
   ```bash
   git clone https://github.com/jmontp/agent-workflow.git
   cd agent-workflow
   ```

2. **Create a virtual environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # Linux/Mac
   # or
   venv\Scripts\activate     # Windows
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   pip install -r requirements-dev.txt  # Development dependencies
   ```

4. **Set up environment variables:**
   ```bash
   cp .env.example .env
   # Edit .env with your Discord bot token and other settings
   ```

## Development Workflow

### Branch Strategy

- `main`: Production-ready code
- `develop`: Integration branch for features
- `feature/*`: Individual feature development
- `hotfix/*`: Critical bug fixes

### Making Changes

1. **Create a feature branch:**
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make your changes:**
   - Follow existing code style and patterns
   - Add tests for new functionality
   - Update documentation as needed

3. **Test your changes:**
   ```bash
   # Run the full test suite
   pytest

   # Run specific test categories
   pytest tests/unit/
   pytest tests/integration/
   pytest -m "not slow"
   ```

4. **Commit your changes:**
   ```bash
   git add .
   git commit -m "Add feature: description of your changes"
   ```

5. **Push and create a pull request:**
   ```bash
   git push origin feature/your-feature-name
   ```

## Code Style Guidelines

### Python Code Style

We follow PEP 8 with some modifications:

- **Line length**: 88 characters (Black formatter default)
- **Import ordering**: Use `isort` for consistent import organization
- **Type hints**: Required for public methods and complex functions
- **Docstrings**: Use Google-style docstrings

### Example Code Style

```python
from typing import List, Optional
import asyncio

from lib.data_models import Epic, Story


class EpicManager:
    """Manages epic creation and lifecycle.
    
    This class handles the creation, modification, and deletion of epics
    within the workflow system.
    """
    
    def __init__(self, storage_path: str) -> None:
        """Initialize the epic manager.
        
        Args:
            storage_path: Path to the storage directory for epics.
        """
        self.storage_path = storage_path
        
    async def create_epic(
        self, 
        description: str, 
        priority: str = "medium"
    ) -> Epic:
        """Create a new epic with the given description.
        
        Args:
            description: Human-readable description of the epic.
            priority: Priority level (low, medium, high).
            
        Returns:
            The created Epic instance.
            
        Raises:
            ValueError: If description is empty or invalid.
        """
        if not description.strip():
            raise ValueError("Epic description cannot be empty")
            
        # Implementation here...
```

### Testing Guidelines

#### Test Organization

- **Unit tests**: `tests/unit/` - Test individual components in isolation
- **Integration tests**: `tests/integration/` - Test component interactions
- **End-to-end tests**: `tests/e2e/` - Test complete user workflows

#### Test Patterns

```python
import pytest
from unittest.mock import AsyncMock, patch

from lib.orchestrator import Orchestrator


class TestOrchestrator:
    """Test suite for the Orchestrator class."""
    
    @pytest.fixture
    def orchestrator(self):
        """Create a test orchestrator instance."""
        return Orchestrator(config_path="test_config.yml")
    
    @pytest.mark.asyncio
    async def test_create_epic_success(self, orchestrator):
        """Test successful epic creation."""
        # Given
        description = "Build authentication system"
        
        # When
        epic = await orchestrator.create_epic(description)
        
        # Then
        assert epic.description == description
        assert epic.status == "pending"
        
    @pytest.mark.asyncio
    async def test_create_epic_with_empty_description_raises_error(self, orchestrator):
        """Test that empty description raises ValueError."""
        # Given
        description = ""
        
        # When/Then
        with pytest.raises(ValueError, match="Epic description cannot be empty"):
            await orchestrator.create_epic(description)
```

## Architecture Guidelines

### Adding New Agents

When adding a new agent type:

1. **Inherit from BaseAgent:**
   ```python
   from lib.agents.base_agent import BaseAgent
   
   class NewAgent(BaseAgent):
       async def run(self, task: str, dry_run: bool = False) -> str:
           # Implementation
   ```

2. **Define security profile:**
   Add to `lib/agent_tool_config.py`:
   ```python
   "NewAgent": {
       "allowed_tools": ["read", "specific_tool"],
       "blocked_tools": ["edit", "system"]
   }
   ```

3. **Add comprehensive tests:**
   - Unit tests for agent logic
   - Security boundary tests
   - Integration tests with orchestrator

### State Machine Extensions

When modifying the state machine:

1. **Update state definitions** in `lib/state_machine.py`
2. **Add transition logic** with proper validation
3. **Update command mappings** in the Discord bot
4. **Add comprehensive tests** for all new transitions

## Documentation

### Documentation Requirements

- **API documentation**: Update docstrings for any public methods
- **User documentation**: Update relevant user guides
- **Architecture documentation**: Update design docs for significant changes

### Building Documentation

```bash
# Install documentation dependencies
pip install mkdocs-material

# Serve locally for development
mkdocs serve

# Build static site
mkdocs build
```

## Testing

### Running Tests

```bash
# Full test suite
pytest

# With coverage report
pytest --cov=lib --cov-report=html

# Specific test categories
pytest tests/unit/
pytest tests/integration/
pytest -m "not slow"

# Security tests
pytest tests/unit/test_agent_tool_config.py

# TDD-specific tests
pytest tests/unit/test_tdd_models.py
pytest tests/unit/test_tdd_state_machine.py
pytest test_tdd_e2e.py
```

### Test Requirements

- **Coverage**: Aim for >90% code coverage
- **Security tests**: Required for any security-related changes
- **Integration tests**: Required for cross-component changes
- **Performance tests**: For changes affecting system performance
- **TDD tests**: Required for all TDD state machine and model changes

## TDD Development Practices

### Working with TDD Features

The AI Agent TDD-Scrum system includes a comprehensive TDD workflow system. When contributing to TDD-related functionality, follow these practices:

#### TDD State Machine Development

**State Transition Testing:**
```python
def test_tdd_state_transition():
    """Test TDD state transitions follow RED-GREEN-REFACTOR cycle"""
    machine = TDDStateMachine(TDDState.DESIGN)
    
    # Test valid transition
    result = machine.transition("/tdd test")
    assert result.success
    assert result.new_state == TDDState.TEST_RED
    
    # Test invalid transition
    result = machine.transition("/tdd refactor") 
    assert not result.success
    assert "Write failing tests first" in result.hint
```

**Condition Validation:**
```python
def test_transition_conditions():
    """Test that transition conditions are properly validated"""
    task = TDDTask(description="Test login API")
    task.test_results = [TestResult(status=TestStatus.RED)]
    
    machine = TDDStateMachine()
    cycle = TDDCycle(current_task_id=task.id)
    cycle.add_task(task)
    
    # Should allow transition when conditions are met
    result = machine.validate_command("/tdd code", cycle)
    assert result.success
```

#### TDD Model Development

**Data Model Changes:**
- All TDD models must include `to_dict()` and `from_dict()` methods
- Ensure serialization compatibility for persistence
- Add proper type hints and documentation

```python
@dataclass
class TDDTask:
    """Individual task within a TDD cycle"""
    id: str = field(default_factory=lambda: f"tdd-task-{uuid.uuid4().hex[:8]}")
    # ... other fields
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary for persistence"""
        return {
            "id": self.id,
            # ... serialize all fields including nested objects
        }
```

#### Test Preservation Workflow

When working on test preservation features:

**File Management:**
```python
def test_test_file_lifecycle():
    """Test the complete test file lifecycle"""
    test_file = TestFile(
        file_path="/tests/tdd/story-123/test_login.py",
        story_id="story-123",
        status=TestFileStatus.DRAFT
    )
    
    # Test commit transition
    test_file.committed_at = datetime.now().isoformat()
    assert test_file.is_committed()
    
    # Test integration
    permanent_path = test_file.get_permanent_location()
    assert "tests/unit/" in permanent_path
```

**CI Integration:**
```python
def test_ci_status_updates():
    """Test CI status tracking for TDD cycles"""
    cycle = TDDCycle(story_id="story-123")
    cycle.update_ci_status(CIStatus.RUNNING)
    
    assert cycle.ci_status == CIStatus.RUNNING
    # Test status propagation to tasks
```

### TDD Code Style Guidelines

#### Command Validation
```python
# Good: Clear error messages with helpful hints
if command not in self.TRANSITIONS:
    return TDDCommandResult(
        success=False,
        error_message=f"Unknown TDD command: {command}",
        hint="Use /tdd status to see available commands"
    )

# Bad: Generic error without guidance
if command not in self.TRANSITIONS:
    return TDDCommandResult(success=False)
```

#### State Management
```python
# Good: Atomic state updates with logging
def transition(self, command: str) -> TDDCommandResult:
    result = self.validate_command(command)
    if result.success:
        old_state = self.current_state
        self.current_state = result.new_state
        logger.info(f"TDD transition: {old_state} → {self.current_state}")
    return result

# Bad: State changes without validation or logging
def transition(self, command: str):
    self.current_state = new_state  # No validation
```

#### Error Handling
```python
# Good: Specific error handling with context
try:
    test_results = self.run_tests(test_files)
except TestExecutionError as e:
    return TDDCommandResult(
        success=False,
        error_message=f"Test execution failed: {e}",
        hint="Check test file syntax and dependencies"
    )

# Bad: Silent failures or generic exceptions
try:
    self.run_tests(test_files)
except:
    pass  # Silent failure
```

### TDD Testing Requirements

#### State Machine Tests
- **Transition Matrix**: Test all valid and invalid state transitions
- **Command Validation**: Verify command parsing and validation logic
- **Condition Checking**: Test all transition conditions and hints
- **Error Scenarios**: Test malformed commands and edge cases

#### Model Tests
- **Serialization**: Test `to_dict()` and `from_dict()` for all models
- **Lifecycle**: Test complete object lifecycles (create → update → complete)
- **Relationships**: Test task-cycle-story relationships
- **Business Logic**: Test domain-specific methods and calculations

#### Integration Tests
- **E2E Workflows**: Test complete TDD cycles from start to finish
- **Persistence**: Test data persistence and recovery
- **Agent Coordination**: Test TDD workflow with multiple agents
- **Error Recovery**: Test recovery from failed states

#### Example Test Structure
```python
class TestTDDStateMachine:
    """Comprehensive test suite for TDD state machine"""
    
    @pytest.fixture
    def machine(self):
        return TDDStateMachine(TDDState.DESIGN)
    
    @pytest.fixture
    def sample_cycle(self):
        cycle = TDDCycle(story_id="test-story")
        task = TDDTask(description="Test task")
        cycle.add_task(task)
        cycle.start_task(task.id)
        return cycle
    
    def test_valid_transitions(self, machine):
        """Test all valid state transitions"""
        # Test each transition in TRANSITIONS matrix
    
    def test_invalid_transitions(self, machine):
        """Test invalid transitions return helpful errors"""
        # Test transitions not in matrix
    
    def test_condition_validation(self, machine, sample_cycle):
        """Test transition conditions are properly checked"""
        # Test each condition in TRANSITION_CONDITIONS
    
    @pytest.mark.parametrize("command,state,expected_hint", [
        ("/tdd code", TDDState.DESIGN, "Write failing tests first"),
        # ... more test cases
    ])
    def test_error_hints(self, machine, command, state, expected_hint):
        """Test that error hints are helpful and accurate"""
        machine.current_state = state
        result = machine.validate_command(command)
        assert not result.success
        assert expected_hint in result.hint
```

### Performance Considerations

- **State Transitions**: Should complete in <1ms for local operations
- **Model Serialization**: Should handle cycles with 100+ tasks efficiently
- **Test File Management**: Should support 1000+ test files per cycle
- **Memory Usage**: Avoid memory leaks in long-running TDD cycles

## Review Process

### Pull Request Guidelines

1. **Clear description**: Explain what and why
2. **Link issues**: Reference related GitHub issues
3. **Include tests**: All changes must include appropriate tests
4. **Update documentation**: Keep docs in sync with code changes
5. **Security review**: Highlight any security implications

### Review Checklist

- [ ] Code follows style guidelines
- [ ] Tests pass and coverage is maintained
- [ ] Documentation is updated
- [ ] Security implications are considered
- [ ] Breaking changes are documented
- [ ] Performance impact is assessed

## Getting Help

### Resources

- **GitHub Issues**: Report bugs and request features
- **GitHub Discussions**: Ask questions and share ideas
- **Discord**: Join our development Discord server (link in README)

### Common Issues

**Tests failing locally:**
- Ensure all dependencies are installed
- Check environment variable configuration
- Run `pytest -v` for detailed error output

**Import errors:**
- Verify virtual environment is activated
- Run `pip install -e .` to install in development mode

**Discord bot not responding:**
- Check bot token configuration
- Verify bot permissions in test server
- Review Discord API rate limits

## Release Process

### Version Management

We use semantic versioning (SemVer):
- **Major**: Breaking changes
- **Minor**: New features, backward compatible
- **Patch**: Bug fixes, backward compatible

### Release Checklist

1. Update version numbers
2. Update CHANGELOG.md
3. Run full test suite
4. Update documentation
5. Create release PR
6. Tag release after merge
7. Deploy to production

Thank you for contributing to the AI Agent TDD-Scrum Workflow project!