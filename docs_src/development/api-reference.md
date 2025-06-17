# API Reference

Complete API reference for the AI Agent TDD-Scrum workflow system.

## Core Classes

### Orchestrator

Main coordination engine for the workflow system.

```python
from lib.orchestrator import Orchestrator

orchestrator = Orchestrator(config_path="config.yml")
```

#### Methods

**`async create_epic(description: str, priority: str = "medium") -> Epic`**

Create a new epic with the given description.

**Parameters:**
- `description` (str): Human-readable description of the epic
- `priority` (str, optional): Priority level ("low", "medium", "high"). Defaults to "medium"

**Returns:**
- `Epic`: The created epic instance

**Raises:**
- `ValueError`: If description is empty or invalid

**Example:**
```python
epic = await orchestrator.create_epic("Build authentication system", "high")
print(f"Created epic: {epic.id}")
```

**`async plan_sprint(story_ids: List[str]) -> Sprint`**

Plan a new sprint with the specified stories.

**`async start_sprint() -> bool`**

Start the currently planned sprint.

**`async get_state() -> OrchestratorState`**

Get the current orchestrator state.

### State Machine

Finite state machine managing workflow transitions.

```python
from lib.state_machine import StateMachine, OrchestratorState

state_machine = StateMachine()
```

#### States

- `IDLE`: Initial state, ready for epic creation
- `BACKLOG_READY`: Epic created, ready for sprint planning
- `SPRINT_PLANNED`: Sprint planned, ready to start
- `SPRINT_ACTIVE`: Sprint in progress
- `SPRINT_PAUSED`: Sprint temporarily paused
- `SPRINT_REVIEW`: Sprint completed, awaiting review
- `BLOCKED`: System blocked, requires intervention

#### Methods

**`transition(current_state: OrchestratorState, command: str) -> OrchestratorState`**

Execute a state transition based on the current state and command.

**`get_allowed_commands(state: OrchestratorState) -> List[str]`**

Get the list of commands allowed in the given state.

## Data Models

### Epic

High-level initiative or feature area.

```python
from lib.data_models import Epic

epic = Epic(
    id="AUTH-EPIC-001",
    description="Build comprehensive authentication system",
    priority="high",
    status="active"
)
```

#### Attributes

- `id` (str): Unique identifier
- `description` (str): Human-readable description
- `priority` (str): Priority level ("low", "medium", "high")
- `status` (str): Current status ("pending", "active", "completed")
- `created_at` (datetime): Creation timestamp
- `stories` (List[Story]): Associated stories

#### Methods

**`add_story(story: Story) -> None`**

Add a story to this epic.

**`to_dict() -> dict`**

Serialize epic to dictionary.

**`from_dict(data: dict) -> Epic`** (classmethod)

Create epic from dictionary.

### Story

Specific, actionable task within an epic.

```python
from lib.data_models import Story

story = Story(
    id="AUTH-001",
    description="Create user registration form",
    epic_id="AUTH-EPIC-001",
    priority="high"
)
```

#### Attributes

- `id` (str): Unique identifier
- `description` (str): Detailed task description
- `epic_id` (str): Parent epic identifier
- `priority` (str): Priority level
- `status` (str): Current status
- `assigned_agent` (str, optional): Agent type assigned
- `created_at` (datetime): Creation timestamp

### Sprint

Time-boxed development iteration.

```python
from lib.data_models import Sprint

sprint = Sprint(
    id="SPRINT-001",
    stories=["AUTH-001", "AUTH-002"],
    start_date=datetime.now(),
    duration_days=7
)
```

#### Attributes

- `id` (str): Unique identifier
- `stories` (List[str]): Story IDs included in sprint
- `start_date` (datetime): Sprint start date
- `duration_days` (int): Sprint length in days
- `status` (str): Current status ("planned", "active", "completed")

## Agent System

### BaseAgent

Abstract base class for all agents.

```python
from lib.agents.base_agent import BaseAgent

class CustomAgent(BaseAgent):
    async def run(self, task: str, dry_run: bool = False) -> str:
        # Implementation
        pass
```

#### Methods

**`async run(task: str, dry_run: bool = False) -> str`** (abstract)

Execute the given task.

**`get_capabilities() -> List[str]`**

Return list of agent capabilities.

### DesignAgent

Specialized agent for architecture and design tasks.

```python
from lib.agents.design_agent import DesignAgent

agent = DesignAgent()
result = await agent.run("Create API specification for user authentication")
```

#### Capabilities

- System architecture design
- API specification creation
- Component interface design
- Technical documentation
- Design review and validation

### CodeAgent

Specialized agent for code implementation tasks.

```python
from lib.agents.code_agent import CodeAgent

agent = CodeAgent()
result = await agent.run("Implement user registration endpoint")
```

#### Capabilities

- Feature implementation
- Bug fixing and debugging
- Code refactoring
- Performance optimization
- Integration development

### QAAgent

Specialized agent for testing and quality assurance.

```python
from lib.agents.qa_agent import QAAgent

agent = QAAgent()
result = await agent.run("Create unit tests for authentication module")
```

#### Capabilities

- Test suite creation
- Quality validation
- Coverage analysis
- Performance testing
- Security testing

### DataAgent

Specialized agent for data analysis and visualization.

```python
from lib.agents.data_agent import DataAgent

agent = DataAgent()
result = await agent.run("Analyze user registration patterns")
```

#### Capabilities

- Data analysis and insights
- Pipeline creation
- Metrics reporting
- Visualization generation
- Statistical analysis

## Discord Bot

Discord interface for Human-In-The-Loop control.

```python
from lib.discord_bot import DiscordBot

bot = DiscordBot(orchestrator=orchestrator)
```

### Commands

All Discord commands are implemented as slash commands:

- `/epic "description"` - Create new epic
- `/approve [ID...]` - Approve pending items
- `/sprint plan|start|status|pause|resume` - Sprint management
- `/backlog view|add_story|prioritize` - Backlog operations
- `/state` - Interactive state inspection

## Storage System

### ProjectStorage

File-based persistence for project data.

```python
from lib.project_storage import ProjectStorage

storage = ProjectStorage(project_path="/path/to/project")
```

#### Methods

**`save_epic(epic: Epic) -> None`**

Persist epic to storage.

**`load_epic(epic_id: str) -> Epic`**

Load epic from storage.

**`save_sprint(sprint: Sprint) -> None`**

Persist sprint to storage.

**`get_project_state() -> dict`**

Get complete project state.

## Security System

### Agent Tool Configuration

Security controls for agent capabilities.

```python
from lib.agent_tool_config import get_agent_security_profile

profile = get_agent_security_profile("CodeAgent")
allowed_tools = profile["allowed_tools"]
blocked_tools = profile["blocked_tools"]
```

#### Security Profiles

Each agent type has specific tool restrictions:

- **DesignAgent**: Read-only access, documentation creation
- **CodeAgent**: Code editing, version control (limited)
- **QAAgent**: Testing tools only
- **DataAgent**: Data processing and visualization

## Error Handling

### Custom Exceptions

```python
from lib.exceptions import (
    InvalidStateTransitionError,
    AgentExecutionError,
    ConfigurationError
)

try:
    await orchestrator.start_sprint()
except InvalidStateTransitionError as e:
    print(f"Invalid state transition: {e}")
```

#### Exception Types

- `InvalidStateTransitionError`: Illegal state machine transition
- `AgentExecutionError`: Agent task execution failure
- `ConfigurationError`: Invalid configuration settings
- `StorageError`: File system or data persistence error

## Configuration

### Config Schema

```python
from lib.config import Config

config = Config.from_file("config.yml")
```

#### Configuration Structure

```yaml
orchestrator:
  mode: "blocking"  # blocking, partial, autonomous
  max_concurrent_projects: 3
  state_save_interval: 60

discord:
  bot_token: "your_token_here"
  command_prefix: "/"
  max_commands_per_minute: 20

agents:
  timeout_minutes: 30
  max_retries: 3
  
projects:
  - name: "web-app"
    path: "/path/to/project"
    mode: "partial"
```

## Utilities

### Logging

```python
from lib.utils.logging import get_logger

logger = get_logger(__name__)
logger.info("Orchestrator started")
```

### Async Helpers

```python
from lib.utils.async_helpers import run_with_timeout

result = await run_with_timeout(agent.run(task), timeout=300)
```

## Examples

### Complete Workflow Example

```python
import asyncio
from lib.orchestrator import Orchestrator

async def main():
    # Initialize orchestrator
    orchestrator = Orchestrator("config.yml")
    
    # Create epic
    epic = await orchestrator.create_epic(
        "Build user authentication system", 
        priority="high"
    )
    
    # Plan sprint
    sprint = await orchestrator.plan_sprint([
        "AUTH-001", "AUTH-002", "AUTH-003"
    ])
    
    # Start sprint
    success = await orchestrator.start_sprint()
    
    if success:
        print("Sprint started successfully!")
    
    # Monitor progress
    while True:
        state = await orchestrator.get_state()
        if state == "SPRINT_REVIEW":
            break
        await asyncio.sleep(30)  # Check every 30 seconds

if __name__ == "__main__":
    asyncio.run(main())
```

### Custom Agent Example

```python
from lib.agents.base_agent import BaseAgent

class DocumentationAgent(BaseAgent):
    """Agent specialized in creating and maintaining documentation."""
    
    def get_capabilities(self) -> List[str]:
        return [
            "markdown_generation",
            "api_documentation", 
            "user_guide_creation",
            "code_commenting"
        ]
    
    async def run(self, task: str, dry_run: bool = False) -> str:
        if "api documentation" in task.lower():
            return await self._generate_api_docs(task)
        elif "user guide" in task.lower():
            return await self._create_user_guide(task)
        else:
            return await self._general_documentation(task)
    
    async def _generate_api_docs(self, task: str) -> str:
        # Implementation for API documentation
        return "Generated API documentation"
```

This API reference provides comprehensive coverage of the system's public interfaces and usage patterns.