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
```

### Test Requirements

- **Coverage**: Aim for >90% code coverage
- **Security tests**: Required for any security-related changes
- **Integration tests**: Required for cross-component changes
- **Performance tests**: For changes affecting system performance

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