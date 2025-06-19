# 🚀 Interactive API Reference

<div class="api-header">
  <div class="api-info">
    <span class="api-version">v1.0.0</span>
    <span class="api-status">✅ Stable</span>
    <span class="api-updated">Updated: 2025-01-19</span>
  </div>
  <div class="api-tools">
    <a href="#quick-start" class="btn btn-primary">🏃‍♂️ Quick Start</a>
    <a href="#interactive-explorer" class="btn btn-secondary">🔍 API Explorer</a>
    <a href="#postman-collection" class="btn btn-outline">📮 Postman</a>
  </div>
</div>

> **Complete API reference** for the AI Agent TDD-Scrum workflow system with interactive examples, multi-language support, and live testing capabilities.

## 🎯 Interactive API Explorer {#interactive-explorer}

<div class="api-explorer">
  <div class="explorer-tabs">
    <button class="tab-btn active" data-tab="playground">🛝 Playground</button>
    <button class="tab-btn" data-tab="examples">💡 Examples</button>
    <button class="tab-btn" data-tab="testing">🧪 Testing</button>
  </div>
  
  <div class="tab-content active" id="playground">
    <p>🚧 <strong>Coming Soon:</strong> Interactive playground for testing API calls directly in the browser</p>
    <pre><code class="language-bash"># For now, use the CLI
python -m lib.orchestrator --help</code></pre>
  </div>
  
  <div class="tab-content" id="examples">
    <p>📖 Jump to real-world examples in each section below</p>
  </div>
  
  <div class="tab-content" id="testing">
    <p>🧪 See <a href="#testing-guide">Testing Guide</a> for endpoint validation</p>
  </div>
</div>

## 🏃‍♂️ Quick Start Guide {#quick-start}

<div class="quick-start-grid">
  <div class="quick-start-card">
    <h3>🐍 Python</h3>
    <pre><code class="language-python">from lib.orchestrator import Orchestrator
from lib.agents import create_agent

# Initialize
orchestrator = Orchestrator()

# Create epic
epic = await orchestrator.create_epic(
    "Build authentication system",
    priority="high"
)</code></pre>
  </div>
  
  <div class="quick-start-card">
    <h3>🔧 CLI</h3>
    <pre><code class="language-bash"># Start orchestrator
python scripts/orchestrator.py

# Via Discord (recommended)
python lib/discord_bot.py</code></pre>
  </div>
  
  <div class="quick-start-card">
    <h3>🤖 Discord Bot</h3>
    <pre><code class="language-bash"># Register project
/project register /path/to/project

# Create epic
/epic "Build user authentication"

# Plan sprint
/sprint plan</code></pre>
  </div>
</div>

## 📮 Postman Collection {#postman-collection}

<div class="postman-section">
  <div class="postman-info">
    <h3>🚀 Get Started with Postman</h3>
    <p>Import our collection to test all endpoints interactively:</p>
  </div>
  
  <div class="postman-buttons">
    <button class="btn btn-primary" onclick="downloadPostmanCollection()">
      📥 Download Collection
    </button>
    <button class="btn btn-secondary" onclick="openPostmanDocs()">
      📚 Postman Docs
    </button>
  </div>
  
  <div class="postman-preview">
    <details>
      <summary>👀 Preview Collection Structure</summary>
      <pre><code class="language-json">{
  "info": {
    "name": "AI Agent TDD-Scrum API",
    "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json"
  },
  "item": [
    {
      "name": "Orchestrator",
      "item": [
        {"name": "Create Epic", "request": {...}},
        {"name": "Plan Sprint", "request": {...}},
        {"name": "Get Metrics", "request": {...}}
      ]
    },
    {
      "name": "Agents",
      "item": [
        {"name": "Execute Code Agent", "request": {...}},
        {"name": "Execute Design Agent", "request": {...}}
      ]
    }
  ]
}</code></pre>
    </details>
  </div>
</div>

## 📚 Navigation & Reference

<div class="nav-grid">
  <div class="nav-section">
    <h3>🏗️ Core Components</h3>
    <ul>
      <li><a href="#orchestrator">🎭 Orchestrator</a></li>
      <li><a href="#state-machine">🔀 State Machine</a></li>
      <li><a href="#data-models">📋 Data Models</a></li>
    </ul>
  </div>
  
  <div class="nav-section">
    <h3>🤖 Agent System</h3>
    <ul>
      <li><a href="#baseagent">🧱 BaseAgent</a></li>
      <li><a href="#design-agent">🎨 DesignAgent</a></li>
      <li><a href="#code-agent">💻 CodeAgent</a></li>
      <li><a href="#qa-agent">🧪 QAAgent</a></li>
      <li><a href="#data-agent">📊 DataAgent</a></li>
    </ul>
  </div>
  
  <div class="nav-section">
    <h3>🧠 Intelligence Layer</h3>
    <ul>
      <li><a href="#context-manager">🔄 Context Manager</a></li>
      <li><a href="#tdd-system">🔴🟢🔄 TDD System</a></li>
      <li><a href="#security">🔒 Security</a></li>
    </ul>
  </div>
  
  <div class="nav-section">
    <h3>🚀 Integration</h3>
    <ul>
      <li><a href="#discord-integration">💬 Discord Bot</a></li>
      <li><a href="#storage">💾 Storage</a></li>
      <li><a href="#testing-guide">🧪 Testing</a></li>
    </ul>
  </div>
</div>

<div class="search-section">
  <input type="text" id="api-search" placeholder="🔍 Search API methods, classes, or concepts..." />
  <div class="search-results" id="search-results"></div>
</div>

---

## 🏗️ Core Components

### 🎭 Orchestrator {#orchestrator}

<div class="component-header">
  <div class="component-info">
    <span class="component-type">🏗️ Core Engine</span>
    <span class="component-stability">✅ Stable</span>
    <span class="component-async">⚡ Async</span>
  </div>
  <div class="component-actions">
    <button class="btn btn-sm" onclick="copyToClipboard('orchestrator-import')">📋 Copy Import</button>
    <button class="btn btn-sm" onclick="runExample('orchestrator-basic')">▶️ Try Example</button>
  </div>
</div>

**Main coordination engine** for the AI Agent TDD-Scrum workflow system. Manages the lifecycle of epics, stories, and sprints while coordinating agent activities across multiple projects.

#### 🚀 Quick Examples

<div class="example-tabs">
  <button class="tab-btn active" data-tab="basic">🎯 Basic Usage</button>
  <button class="tab-btn" data-tab="advanced">🚀 Advanced</button>
  <button class="tab-btn" data-tab="async">⚡ Async Patterns</button>
</div>

<div class="tab-content active" id="basic">

```python title="🎯 Basic Orchestrator Usage" id="orchestrator-import"
from lib.orchestrator import Orchestrator
from lib.data_models import Epic, Story, Sprint

# 🔧 Initialize with configuration
orchestrator = Orchestrator(config_path="config.yml")

# 🎯 Or use defaults  
orchestrator = Orchestrator()

# 📝 Create your first epic
epic = await orchestrator.create_epic(
    "Build authentication system",
    priority="high"
)
print(f"✅ Created epic: {epic.id}")
```

</div>

<div class="tab-content" id="advanced">

```python title="🚀 Advanced Multi-Project Setup"
from lib.orchestrator import Orchestrator
from lib.context_manager import ContextManager

# 🧠 Initialize with context management
context_manager = ContextManager(
    project_path="./",
    enable_caching=True,
    enable_monitoring=True
)

orchestrator = Orchestrator(
    config_path="config.yml",
    context_manager=context_manager
)

# 🎯 Multi-project coordination
projects = ["backend-api", "frontend-app", "mobile-app"]
for project in projects:
    await orchestrator.register_project(project)
```

</div>

<div class="tab-content" id="async">

```python title="⚡ Async Workflow Patterns"
import asyncio
from lib.orchestrator import Orchestrator

async def run_full_workflow():
    orchestrator = Orchestrator()
    
    # 🔄 Concurrent epic creation
    epics = await asyncio.gather(
        orchestrator.create_epic("Authentication", priority="high"),
        orchestrator.create_epic("Payment System", priority="medium"), 
        orchestrator.create_epic("User Dashboard", priority="low")
    )
    
    # 📊 Get real-time metrics
    metrics = await orchestrator.get_metrics()
    print(f"📈 Sprint velocity: {metrics['velocity']}")
    
# 🚀 Run the workflow
asyncio.run(run_full_workflow())
```

</div>
</div>

#### 🛠️ Constructor & Configuration

<div class="method-signature">
  <code class="signature">__init__(config_path=None, project_path=".", context_manager=None)</code>
  <span class="method-type">constructor</span>
</div>

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `config_path` | `Optional[str]` | `None` | 📄 Path to YAML configuration file |
| `project_path` | `str` | `"."` | 📂 Root directory of the project |
| `context_manager` | `Optional[ContextManager]` | `None` | 🧠 Context manager for advanced features |

<div class="parameter-examples">
  <details>
    <summary>📋 Configuration Examples</summary>
    
```yaml title="config.yml"
orchestrator:
  mode: "blocking"              # blocking|partial|autonomous
  max_concurrent_projects: 3
  state_save_interval: 60       # seconds
  
agents:
  timeout_minutes: 30
  max_retries: 3
  context_window_size: 8000
```

```python title="Dynamic Configuration"
# 🔧 Runtime configuration updates
orchestrator.config.update_agent_timeout(45)
orchestrator.config.enable_tdd_auto_progression()

# 📂 Project-specific overrides
orchestrator.config.set_project_config(
    "backend-api",
    {"mode": "blocking", "tdd_min_coverage": 90}
)
```
  </details>
</div>

#### 📋 API Methods

##### 🎯 `create_epic()` - Create New Epic {#create-epic}

<div class="method-header">
  <div class="method-signature">
    <code>async create_epic(description, priority="medium", tdd_requirements=None) → Epic</code>
  </div>
  <div class="method-badges">
    <span class="badge async">⚡ Async</span>
    <span class="badge stable">✅ Stable</span>
    <span class="badge core">🏗️ Core</span>
  </div>
</div>

Create a new epic with the given description and optional TDD requirements. Epics represent high-level project initiatives that contain multiple stories.

**Parameters:**

<div class="parameter-table">

| Parameter | Type | Default | Required | Description |
|-----------|------|---------|----------|-------------|
| `description` | `str` | - | ✅ | Human-readable description of the epic |
| `priority` | `str` | `"medium"` | ❌ | Priority level: `"low"`, `"medium"`, `"high"` |
| `tdd_requirements` | `List[str]` | `None` | ❌ | TDD-specific requirements for the epic |

</div>

**Returns:** `Epic` - The created epic instance with auto-generated ID

**Raises:**
- `ValueError` - Description is empty or priority is invalid
- `StateError` - Current state doesn't allow epic creation

<div class="example-showcase">
  <div class="example-tabs">
    <button class="tab-btn active" data-tab="basic-epic">🎯 Basic</button>
    <button class="tab-btn" data-tab="tdd-epic">🔴🟢🔄 TDD</button>
    <button class="tab-btn" data-tab="advanced-epic">🚀 Advanced</button>
    <button class="tab-btn" data-tab="cli-epic">💻 CLI</button>
  </div>
  
  <div class="tab-content active" id="basic-epic">
  
```python title="🎯 Basic Epic Creation"
# ✨ Simple epic
epic = await orchestrator.create_epic(
    "Build authentication system", 
    priority="high"
)
print(f"✅ Created epic: {epic.id}")
print(f"📋 Title: {epic.title}")
print(f"🎯 Priority: {epic.priority}")
```

  </div>
  
  <div class="tab-content" id="tdd-epic">
  
```python title="🔴🟢🔄 Epic with TDD Requirements"
epic = await orchestrator.create_epic(
    "Implement payment processing",
    priority="high",
    tdd_requirements=[
        "All payment flows must have 100% test coverage",
        "Integration tests required for external APIs", 
        "Performance tests for transaction processing",
        "Security tests for PCI compliance"
    ]
)

# 📊 Access TDD requirements
for req in epic.tdd_requirements:
    print(f"📋 TDD Requirement: {req}")
```

  </div>
  
  <div class="tab-content" id="advanced-epic">
  
```python title="🚀 Advanced Epic with Context"
# 🔄 Create multiple epics concurrently
epics = await asyncio.gather(
    orchestrator.create_epic(
        "User Authentication System",
        priority="high",
        tdd_requirements=["100% test coverage", "Security audit"]
    ),
    orchestrator.create_epic(
        "Payment Integration",
        priority="medium", 
        tdd_requirements=["Integration tests", "Performance tests"]
    ),
    orchestrator.create_epic(
        "Dashboard Analytics",
        priority="low",
        tdd_requirements=["E2E tests", "Visual regression tests"]
    )
)

# 📊 Process results
for epic in epics:
    print(f"✅ Epic {epic.id}: {epic.title}")
    print(f"   📈 Priority: {epic.priority}")
    print(f"   🔴🟢🔄 TDD Requirements: {len(epic.tdd_requirements)}")
```

  </div>
  
  <div class="tab-content" id="cli-epic">
  
```bash title="💻 CLI & Discord Bot Usage"
# Discord Bot Command
/epic "Build user authentication with OAuth2 support"

# CLI (if implemented)
python -m lib.orchestrator epic create \
  --description "Build authentication system" \
  --priority high \
  --tdd-requirement "100% test coverage" \
  --tdd-requirement "Security tests required"

# Configuration file approach
cat > epic-config.yml << EOF
description: "Build authentication system"
priority: high
tdd_requirements:
  - "100% test coverage"
  - "Security audit required"  
  - "Integration tests for OAuth"
EOF

python -m lib.orchestrator epic create --config epic-config.yml
```

  </div>
</div>

<div class="response-example">
  <details>
    <summary>📤 Response Example</summary>
    
```python title="Epic Response Object"
Epic(
    id="epic-a1b2c3d4",
    title="Build authentication system",
    description="Build authentication system", 
    created_at="2025-01-19T10:30:00Z",
    status=EpicStatus.ACTIVE,
    tdd_requirements=[
        "100% test coverage",
        "Security audit required"
    ],
    tdd_constraints={
        "min_coverage": 100,
        "security_scan": True,
        "performance_threshold": "< 200ms"
    }
)
```
  </details>
</div>

<div class="error-handling">
  <details>
    <summary>⚠️ Error Handling</summary>
    
```python title="Robust Error Handling"
try:
    epic = await orchestrator.create_epic(
        description="",  # ❌ Empty description
        priority="critical"  # ❌ Invalid priority
    )
except ValueError as e:
    print(f"❌ Validation Error: {e}")
    # Handle validation errors
    
except StateError as e:
    print(f"🚫 State Error: {e}")
    print(f"💡 Current state: {e.current_state}")
    print(f"✅ Allowed commands: {e.allowed_commands}")
    # Guide user to valid next actions
    
except Exception as e:
    print(f"💥 Unexpected error: {e}")
    # Log for debugging
```
  </details>
</div>

##### 📝 `create_story()` - Create User Story {#create-story}

<div class="method-header">
  <div class="method-signature">
    <code>async create_story(epic_id, title, description, acceptance_criteria) → Story</code>
  </div>
  <div class="method-badges">
    <span class="badge async">⚡ Async</span>
    <span class="badge stable">✅ Stable</span>
  </div>
</div>

Create a new user story within an epic. Stories represent specific features or tasks that deliver value to users.

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `epic_id` | `str` | ✅ | Parent epic identifier |
| `title` | `str` | ✅ | Short, descriptive story title |
| `description` | `str` | ✅ | Detailed user story description |
| `acceptance_criteria` | `List[str]` | ✅ | Testable acceptance criteria |

**Returns:** `Story` - Created story instance with auto-generated ID

<div class="example-showcase">
  <div class="example-tabs">
    <button class="tab-btn active" data-tab="story-basic">📝 Basic Story</button>
    <button class="tab-btn" data-tab="story-advanced">🚀 Advanced</button>
  </div>
  
  <div class="tab-content active" id="story-basic">
  
```python title="📝 User Story Creation"
story = await orchestrator.create_story(
    epic_id="epic-abc123",
    title="User Registration",
    description="As a user, I want to register for an account so I can access the platform",
    acceptance_criteria=[
        "✅ User can enter email and password",
        "✅ Email validation is performed", 
        "✅ Password strength requirements are enforced",
        "✅ Confirmation email is sent",
        "✅ Account is created in database",
        "✅ User is redirected to welcome page"
    ]
)

print(f"📝 Story created: {story.id}")
print(f"🎯 Epic: {story.epic_id}")
print(f"📋 Criteria: {len(story.acceptance_criteria)} items")
```

  </div>
  
  <div class="tab-content" id="story-advanced">
  
```python title="🚀 Advanced Story with TDD Integration"
# 🔄 Create multiple related stories
stories = await asyncio.gather(
    orchestrator.create_story(
        epic_id="epic-auth-001",
        title="User Registration",
        description="As a new user, I want to create an account",
        acceptance_criteria=[
            "Email validation works",
            "Password meets security requirements",
            "Account confirmation email sent"
        ]
    ),
    orchestrator.create_story(
        epic_id="epic-auth-001", 
        title="User Login",
        description="As a registered user, I want to log into my account",
        acceptance_criteria=[
            "Valid credentials allow login",
            "Invalid credentials show error",
            "Session persists across page reloads"
        ]
    ),
    orchestrator.create_story(
        epic_id="epic-auth-001",
        title="Password Reset", 
        description="As a user, I want to reset my forgotten password",
        acceptance_criteria=[
            "Reset email contains secure token",
            "Token expires after 24 hours",
            "New password meets requirements"
        ]
    )
)

# 📊 Analyze story relationships
for story in stories:
    print(f"📝 {story.title}")
    print(f"   🎯 Epic: {story.epic_id}")
    print(f"   ✅ Criteria: {len(story.acceptance_criteria)}")
    print(f"   🔄 TDD Ready: {story.is_ready_for_sprint()}")
```

  </div>
</div>

##### `async plan_sprint(story_ids: List[str], sprint_goal: str, duration_days: int = 14) -> Sprint`

Plan a new sprint with specified stories.

**Parameters:**
- `story_ids` (List[str]): List of story IDs to include
- `sprint_goal` (str): High-level sprint objective
- `duration_days` (int, optional): Sprint duration. Defaults to 14

**Returns:**
- `Sprint`: Planned sprint instance

**Raises:**
- `ValueError`: If story IDs are invalid or sprint goal is empty
- `StateError`: If not in BACKLOG_READY state

**Example:**
```python
sprint = await orchestrator.plan_sprint(
    story_ids=["story-001", "story-002", "story-003"],
    sprint_goal="Complete user authentication flow",
    duration_days=10
)
```

##### `async start_sprint() -> bool`

Start the currently planned sprint.

**Returns:**
- `bool`: True if sprint started successfully

**Raises:**
- `StateError`: If not in SPRINT_PLANNED state
- `RuntimeError`: If no sprint is planned

**Example:**
```python
if await orchestrator.start_sprint():
    print("Sprint started successfully!")
    # Begin monitoring agent activities
```

##### `async get_state() -> State`

Get the current orchestrator state.

**Returns:**
- `State`: Current state enum value

**Example:**
```python
from lib.state_machine import State

current_state = await orchestrator.get_state()
if current_state == State.SPRINT_ACTIVE:
    print("Sprint is currently active")
```

##### `async pause_sprint(reason: str) -> bool`

Pause the active sprint with a reason.

**Parameters:**
- `reason` (str): Explanation for pausing

**Returns:**
- `bool`: True if paused successfully

##### `async resume_sprint() -> bool`

Resume a paused sprint.

**Returns:**
- `bool`: True if resumed successfully

##### `async complete_sprint(retrospective_notes: Dict[str, List[str]]) -> Sprint`

Complete the current sprint with retrospective.

**Parameters:**
- `retrospective_notes` (Dict[str, List[str]]): Retrospective data with keys:
  - "what_went_well": List of positive outcomes
  - "what_could_improve": List of improvement areas
  - "action_items": List of action items

**Returns:**
- `Sprint`: Completed sprint with retrospective data

**Example:**
```python
completed_sprint = await orchestrator.complete_sprint({
    "what_went_well": [
        "All authentication stories completed",
        "Good test coverage achieved",
        "Effective pair programming"
    ],
    "what_could_improve": [
        "Better estimation of complex tasks",
        "More frequent code reviews"
    ],
    "action_items": [
        "Set up automated security scanning",
        "Create estimation guidelines"
    ]
})
```

##### `async get_metrics() -> Dict[str, Any]`

Get comprehensive project metrics.

**Returns:**
- `Dict[str, Any]`: Metrics including velocity, completion rates, and TDD statistics

**Example:**
```python
metrics = await orchestrator.get_metrics()
print(f"Sprint velocity: {metrics['velocity']}")
print(f"Test coverage: {metrics['test_coverage']}%")
print(f"TDD compliance: {metrics['tdd_compliance']}%")
```

### State Machine

Finite state machine that enforces proper command sequencing and workflow transitions.

```python
from lib.state_machine import StateMachine, State, CommandResult

state_machine = StateMachine()
```

#### State Enum

```python
from enum import Enum

class State(Enum):
    IDLE = "IDLE"                    # Initial state
    BACKLOG_READY = "BACKLOG_READY"  # Epic created, ready for planning
    SPRINT_PLANNED = "SPRINT_PLANNED" # Sprint planned, ready to start
    SPRINT_ACTIVE = "SPRINT_ACTIVE"   # Sprint in progress
    SPRINT_PAUSED = "SPRINT_PAUSED"   # Sprint temporarily paused
    SPRINT_REVIEW = "SPRINT_REVIEW"   # Sprint complete, in review
    BLOCKED = "BLOCKED"               # System blocked, needs intervention
```

#### Methods

##### `transition(command: str, current_state: Optional[State] = None) -> CommandResult`

Execute a state transition based on command.

**Parameters:**
- `command` (str): Command to execute (e.g., "/epic", "/sprint start")
- `current_state` (State, optional): Override current state for testing

**Returns:**
- `CommandResult`: Result containing success status, new state, and any errors

**Example:**
```python
result = state_machine.transition("/sprint start")
if result.success:
    print(f"Transitioned to: {result.new_state}")
else:
    print(f"Error: {result.error_message}")
    print(f"Hint: {result.hint}")
```

##### `validate_command(command: str, current_state: State) -> bool`

Check if a command is valid in the given state.

**Parameters:**
- `command` (str): Command to validate
- `current_state` (State): State to check against

**Returns:**
- `bool`: True if command is allowed

**Example:**
```python
if state_machine.validate_command("/sprint plan", State.BACKLOG_READY):
    print("Sprint planning is allowed")
```

##### `get_allowed_commands(state: State) -> List[str]`

Get all commands allowed in a specific state.

**Parameters:**
- `state` (State): State to query

**Returns:**
- `List[str]`: List of allowed command strings

**Example:**
```python
allowed = state_machine.get_allowed_commands(State.SPRINT_ACTIVE)
print(f"Available commands: {', '.join(allowed)}")
# Output: Available commands: /sprint status, /sprint pause, /approve
```

##### `get_next_states(state: State) -> List[State]`

Get possible next states from current state.

**Parameters:**
- `state` (State): Current state

**Returns:**
- `List[State]`: List of reachable states

##### `reset() -> None`

Reset state machine to initial IDLE state.

**Example:**
```python
state_machine.reset()
assert state_machine.current_state == State.IDLE
```

---

## Data Models

### Epic

High-level project initiative containing multiple stories.

```python
from lib.data_models import Epic, EpicStatus
from datetime import datetime

# Create new epic
epic = Epic(
    title="Authentication System",
    description="Complete user authentication and authorization",
    status=EpicStatus.ACTIVE,
    tdd_requirements=["100% test coverage", "Security tests required"]
)
```

#### Attributes

| Attribute | Type | Description |
|-----------|------|-------------|
| `id` | `str` | Unique identifier (auto-generated) |
| `title` | `str` | Short title |
| `description` | `str` | Detailed description |
| `created_at` | `str` | ISO format timestamp |
| `status` | `EpicStatus` | Current status (ACTIVE, COMPLETED, ARCHIVED) |
| `tdd_requirements` | `List[str]` | TDD-specific requirements |
| `tdd_constraints` | `Dict[str, Any]` | TDD policies and constraints |

#### Methods

##### `to_dict() -> Dict[str, Any]`

Serialize epic to dictionary for storage.

```python
data = epic.to_dict()
# Save to JSON file
with open("epic.json", "w") as f:
    json.dump(data, f, indent=2)
```

##### `from_dict(data: Dict[str, Any]) -> Epic` (classmethod)

Deserialize epic from dictionary.

```python
# Load from JSON
with open("epic.json", "r") as f:
    data = json.load(f)
epic = Epic.from_dict(data)
```

### Story

User story representing a specific feature or task.

```python
from lib.data_models import Story, StoryStatus

story = Story(
    epic_id="epic-abc123",
    title="User Login",
    description="As a user, I want to log in with email and password",
    acceptance_criteria=[
        "Valid credentials allow login",
        "Invalid credentials show error",
        "Password is masked during entry",
        "Session persists across refreshes"
    ],
    priority=1,  # 1-5 scale, 1 is highest
    test_files=["test_login.py", "test_session.py"]
)
```

#### Attributes

| Attribute | Type | Description |
|-----------|------|-------------|
| `id` | `str` | Unique identifier |
| `epic_id` | `Optional[str]` | Parent epic ID |
| `title` | `str` | Short title |
| `description` | `str` | User story description |
| `acceptance_criteria` | `List[str]` | Testable criteria |
| `priority` | `int` | Priority (1-5, 1 highest) |
| `status` | `StoryStatus` | Current status |
| `sprint_id` | `Optional[str]` | Assigned sprint |
| `tdd_cycle_id` | `Optional[str]` | Active TDD cycle |
| `test_status` | `str` | Test status (not_started, red, green, refactor, complete) |
| `test_files` | `List[str]` | Associated test files |
| `ci_status` | `str` | CI pipeline status |
| `test_coverage` | `float` | Coverage percentage |
| `created_at` | `str` | Creation timestamp |

#### Methods

##### `to_dict() -> Dict[str, Any]`

Serialize story to dictionary.

##### `from_dict(data: Dict[str, Any]) -> Story` (classmethod)

Deserialize story from dictionary.

##### `is_ready_for_sprint() -> bool`

Check if story is ready for sprint planning.

```python
if story.is_ready_for_sprint():
    sprint.add_story(story.id)
```

### Sprint

Time-boxed development iteration.

```python
from lib.data_models import Sprint, SprintStatus, Retrospective

sprint = Sprint(
    goal="Complete authentication flow",
    story_ids=["story-001", "story-002"],
    status=SprintStatus.PLANNED
)

# Add retrospective after completion
sprint.retrospective = Retrospective(
    what_went_well=["Good test coverage", "All stories completed"],
    what_could_improve=["Better estimation"],
    action_items=["Create estimation template"]
)
```

#### Attributes

| Attribute | Type | Description |
|-----------|------|-------------|
| `id` | `str` | Unique identifier |
| `goal` | `str` | Sprint objective |
| `start_date` | `Optional[str]` | Start date (ISO format) |
| `end_date` | `Optional[str]` | End date (ISO format) |
| `story_ids` | `List[str]` | Included story IDs |
| `status` | `SprintStatus` | Current status |
| `retrospective` | `Optional[Retrospective]` | Sprint retrospective |
| `active_tdd_cycles` | `List[str]` | Active TDD cycle IDs |
| `tdd_metrics` | `Dict[str, Any]` | TDD performance metrics |
| `created_at` | `str` | Creation timestamp |

---

## Agent System

### BaseAgent

Abstract base class for all AI agents providing common interface and functionality.

```python
from lib.agents import BaseAgent, Task, AgentResult, TaskStatus
from typing import List, Dict, Any, Optional

class CustomAgent(BaseAgent):
    def __init__(self, name: str = "CustomAgent"):
        super().__init__(
            name=name,
            capabilities=["custom_task", "analysis"]
        )
    
    async def run(self, task: Task, dry_run: bool = False) -> AgentResult:
        # Implementation
        return AgentResult(
            success=True,
            output="Task completed",
            artifacts={"report.md": "# Analysis Report"}
        )
```

#### Constructor

```python
def __init__(
    self,
    name: str,
    capabilities: List[str],
    context_manager: Optional[ContextManager] = None
) -> None:
    """
    Initialize base agent.
    
    Args:
        name: Agent name
        capabilities: List of agent capabilities
        context_manager: Optional context manager for advanced features
    """
```

#### Core Methods

##### `async run(task: Task, dry_run: bool = False) -> AgentResult` (abstract)

Execute a task assigned to this agent.

**Parameters:**
- `task` (Task): Task specification
- `dry_run` (bool): Simulate execution without changes

**Returns:**
- `AgentResult`: Execution outcome

**Must be implemented by subclasses.**

##### `validate_task(task: Task) -> bool`

Validate if agent can handle the task.

```python
task = Task(
    id="task-123",
    agent_type="CodeAgent",
    command="implement feature",
    context={"story_id": "AUTH-001"}
)

if agent.validate_task(task):
    result = await agent.run(task)
```

##### `get_status() -> Dict[str, Any]`

Get agent status and statistics.

```python
status = agent.get_status()
print(f"Agent: {status['name']}")
print(f"Total tasks: {status['total_tasks']}")
print(f"Success rate: {status['completed_tasks'] / status['total_tasks'] * 100:.1f}%")
```

#### TDD Integration Methods

##### `set_tdd_context(state_machine: TDDStateMachine, cycle: Optional[TDDCycle] = None, task: Optional[TDDTask] = None) -> None`

Set TDD context for agent operations.

```python
from lib.tdd_state_machine import TDDStateMachine
from lib.tdd_models import TDDCycle

tdd_sm = TDDStateMachine()
cycle = TDDCycle(story_id="AUTH-001")

agent.set_tdd_context(tdd_sm, cycle)
```

##### `async execute_tdd_phase(phase: TDDState, context: Dict[str, Any]) -> AgentResult`

Execute a specific TDD phase.

```python
result = await agent.execute_tdd_phase(
    TDDState.TEST_RED,
    context={"story_id": "AUTH-001", "task_id": "task-123"}
)
```

##### `can_execute_tdd_phase(phase: TDDState) -> bool`

Check if agent can execute specific TDD phase.

```python
if agent.can_execute_tdd_phase(TDDState.CODE_GREEN):
    print("Agent can implement code")
```

#### Context Management Methods

##### `async prepare_context(task: Union[TDDTask, Dict[str, Any]], story_id: Optional[str] = None, max_tokens: Optional[int] = None) -> Optional[AgentContext]`

Prepare execution context with token management.

```python
context = await agent.prepare_context(
    task={"description": "Implement login"},
    story_id="AUTH-001",
    max_tokens=4000
)

if context:
    print(f"Context prepared: {context.get_total_token_estimate()} tokens")
```

##### `async record_decision(description: str, rationale: str = "", outcome: str = "", confidence: float = 0.0) -> Optional[str]`

Record important decisions for learning.

```python
decision_id = await agent.record_decision(
    description="Chose JWT for authentication",
    rationale="Stateless, scalable, industry standard",
    outcome="Implemented successfully",
    confidence=0.95
)
```

### Specialized Agents

#### DesignAgent

Agent specialized in system architecture, API design, and technical specifications.

```python
from lib.agents import DesignAgent

agent = DesignAgent()
result = await agent.run(
    Task(
        agent_type="DesignAgent",
        command="Design REST API for user management",
        context={"story_id": "AUTH-001"}
    )
)
```

**Capabilities:**
- System architecture design
- API specification creation
- Database schema design
- Component interface design
- Technical documentation
- Design pattern recommendations
- Security architecture

**Security Profile:**
- Read-only file access
- Documentation creation allowed
- No code modification
- No version control operations

#### CodeAgent

Agent specialized in code implementation, refactoring, and optimization.

```python
from lib.agents import CodeAgent

agent = CodeAgent()
result = await agent.run(
    Task(
        agent_type="CodeAgent",
        command="Implement user registration endpoint",
        context={
            "story_id": "AUTH-002",
            "design_doc": "api_spec.md"
        }
    )
)
```

**Capabilities:**
- Feature implementation
- Bug fixing
- Code refactoring
- Performance optimization
- Unit test implementation
- Integration development
- Code review

**Security Profile:**
- File editing allowed
- Git add and commit allowed
- Git push restricted
- Package management allowed
- System commands restricted

#### QAAgent

Agent specialized in testing, quality assurance, and validation.

```python
from lib.agents import QAAgent

agent = QAAgent()
result = await agent.run(
    Task(
        agent_type="QAAgent",
        command="Create comprehensive test suite for authentication",
        context={
            "story_id": "AUTH-001",
            "test_type": "integration"
        }
    )
)
```

**Capabilities:**
- Test suite creation
- Test execution
- Coverage analysis
- Performance testing
- Security testing
- Test documentation
- CI/CD integration

**Security Profile:**
- Test execution allowed
- Code quality tools allowed
- Read-only source access
- No production code modification

#### DataAgent

Agent specialized in data analysis, visualization, and reporting.

```python
from lib.agents import DataAgent

agent = DataAgent()
result = await agent.run(
    Task(
        agent_type="DataAgent",
        command="Analyze sprint velocity trends",
        context={
            "time_period": "last_6_months",
            "output_format": "dashboard"
        }
    )
)
```

**Capabilities:**
- Data analysis
- Metrics visualization
- Report generation
- Statistical analysis
- Trend identification
- Dashboard creation
- Data pipeline development

**Security Profile:**
- Data file access allowed
- Notebook creation allowed
- Visualization tools allowed
- Source code modification restricted

---

## Context Management

### ContextManager

Central coordination engine for intelligent context preparation and token management.

```python
from lib.context_manager import ContextManager
from lib.context.models import ContextRequest, TokenBudget

manager = ContextManager(
    project_path="/path/to/project",
    enable_caching=True,
    enable_monitoring=True
)
```

#### Constructor

```python
def __init__(
    self,
    project_path: str,
    enable_caching: bool = True,
    enable_monitoring: bool = True,
    enable_background_processing: bool = True,
    max_cache_size_mb: int = 500
) -> None:
    """
    Initialize context manager.
    
    Args:
        project_path: Root project directory
        enable_caching: Enable context caching
        enable_monitoring: Enable performance monitoring
        enable_background_processing: Enable background tasks
        max_cache_size_mb: Maximum cache size
    """
```

#### Core Methods

##### `async prepare_context(agent_type: str, task: Any, max_tokens: Optional[int] = None, story_id: Optional[str] = None) -> AgentContext`

Prepare optimized context for agent task execution.

```python
context = await manager.prepare_context(
    agent_type="CodeAgent",
    task={"description": "Implement login API"},
    max_tokens=4000,
    story_id="AUTH-001"
)

print(f"Context size: {context.get_total_token_estimate()} tokens")
print(f"Files included: {len(context.files)}")
```

##### `async record_agent_decision(agent_type: str, story_id: str, description: str, **kwargs) -> str`

Record agent decisions for learning and handoffs.

```python
decision_id = await manager.record_agent_decision(
    agent_type="DesignAgent",
    story_id="AUTH-001",
    description="Chose microservices architecture",
    rationale="Better scalability and team independence",
    confidence=0.85,
    artifacts={"diagram": "architecture.png"}
)
```

##### `async create_phase_handoff(from_agent: str, to_agent: str, story_id: str, handoff_data: Dict[str, Any]) -> str`

Create handoff between agents with context transfer.

```python
handoff_id = await manager.create_phase_handoff(
    from_agent="DesignAgent",
    to_agent="CodeAgent",
    story_id="AUTH-001",
    handoff_data={
        "design_doc": "api_spec.md",
        "key_decisions": ["JWT auth", "REST API"],
        "constraints": ["Must support 10k concurrent users"]
    }
)
```

### Context Models

#### AgentContext

Container for agent execution context with token management.

```python
from lib.context.models import AgentContext, ContextFile

context = AgentContext(
    request_id="ctx-123",
    agent_type="CodeAgent",
    story_id="AUTH-001",
    tdd_phase=TDDState.CODE_GREEN,
    files=[
        ContextFile(
            path="src/auth.py",
            content="...",
            relevance_score=0.95,
            file_type=FileType.SOURCE
        )
    ],
    max_tokens=4000
)
```

**Attributes:**
- `request_id`: Unique context identifier
- `agent_type`: Agent this context is for
- `story_id`: Associated story
- `tdd_phase`: Current TDD phase
- `files`: List of context files
- `decisions`: Recent decisions
- `token_usage`: Token statistics
- `metadata`: Additional context data

**Methods:**
- `get_total_token_estimate()`: Calculate total tokens
- `add_file()`: Add file to context
- `remove_file()`: Remove file from context
- `get_files_by_type()`: Filter files by type
- `to_dict()`: Serialize for caching

#### TokenBudget

Token allocation and management.

```python
from lib.context.models import TokenBudget

budget = TokenBudget(
    total_limit=8000,
    allocations={
        "system_prompt": 500,
        "task_description": 200,
        "source_files": 4000,
        "test_files": 2000,
        "decisions": 1000,
        "buffer": 300
    }
)

# Check if budget allows addition
if budget.can_add_tokens("source_files", 500):
    budget.use_tokens("source_files", 500)
```

---

## TDD System

### TDD State Machine

Enforces Test-Driven Development workflow with proper state transitions.

```python
from lib.tdd_state_machine import TDDStateMachine, TDDCommandResult
from lib.tdd_models import TDDState, TDDCycle

state_machine = TDDStateMachine()
```

#### TDD States

```python
class TDDState(Enum):
    DESIGN = "design"           # Create specifications
    TEST_RED = "test_red"       # Write failing tests
    CODE_GREEN = "code_green"   # Implement to pass tests
    REFACTOR = "refactor"       # Improve code quality
    COMMIT = "commit"           # Save progress
```

#### Methods

##### `validate_command(command: str, cycle: Optional[TDDCycle] = None) -> TDDCommandResult`

Validate TDD command in current state.

```python
result = state_machine.validate_command("/tdd test", cycle)
if result.success:
    print(f"New state: {result.new_state}")
else:
    print(f"Error: {result.error_message}")
    print(f"Hint: {result.hint}")
```

##### `transition(command: str, cycle: Optional[TDDCycle] = None) -> TDDCommandResult`

Execute state transition if valid.

```python
# Start with design
result = state_machine.transition("/tdd design", cycle)

# Move to writing tests
result = state_machine.transition("/tdd test", cycle)

# Implement code
result = state_machine.transition("/tdd code", cycle)
```

##### `get_allowed_commands(cycle: Optional[TDDCycle] = None) -> List[str]`

Get commands allowed in current state.

```python
commands = state_machine.get_allowed_commands(cycle)
print(f"Available: {', '.join(commands)}")
# Output: Available: /tdd refactor, /tdd commit
```

##### `can_auto_progress(cycle: Optional[TDDCycle] = None) -> bool`

Check if automatic progression is possible.

```python
if state_machine.can_auto_progress(cycle):
    next_cmd = state_machine.get_next_suggested_command(cycle)
    print(f"Suggested: {next_cmd}")
```

### TDD Models

#### TDDCycle

Complete TDD cycle for a story.

```python
from lib.tdd_models import TDDCycle, TDDTask

cycle = TDDCycle(
    story_id="AUTH-001",
    current_state=TDDState.DESIGN
)

# Add tasks
task = TDDTask(
    description="Implement user login",
    acceptance_criteria=["Valid users can login", "Invalid users rejected"]
)
cycle.add_task(task)

# Start task
cycle.start_task(task.id)

# Get progress
progress = cycle.get_progress_summary()
print(f"Progress: {progress['completed_tasks']}/{progress['total_tasks']}")
```

**Key Methods:**
- `add_task()`: Add new task to cycle
- `start_task()`: Begin working on task
- `complete_current_task()`: Mark task complete
- `get_current_task()`: Get active task
- `get_progress_summary()`: Get cycle metrics
- `calculate_overall_coverage()`: Get test coverage

#### TDDTask

Individual task within a TDD cycle.

```python
from lib.tdd_models import TDDTask, TestFile, TestResult

task = TDDTask(
    cycle_id="cycle-123",
    description="Implement password validation",
    acceptance_criteria=[
        "Minimum 8 characters",
        "Must contain number and letter",
        "Special characters optional"
    ]
)

# Add test file
test_file = TestFile(
    file_path="/tests/test_password.py",
    story_id="AUTH-001",
    test_count=5
)
task.add_test_file(test_file)

# Check readiness
if task.can_commit_tests():
    print("Tests ready to commit")
```

**Key Methods:**
- `has_passing_tests()`: Check if tests pass
- `has_failing_tests()`: Check if tests fail
- `add_test_file()`: Add test file
- `can_commit_tests()`: Ready for test commit
- `can_commit_code()`: Ready for code commit

---

## Storage & Persistence

### ProjectStorage

File-based storage system for project data.

```python
from lib.project_storage import ProjectStorage

storage = ProjectStorage(project_path="/path/to/project")
```

#### Methods

##### `save_epic(epic: Epic) -> None`

Save epic to persistent storage.

```python
epic = Epic(title="New Feature", description="...")
storage.save_epic(epic)
```

##### `load_epic(epic_id: str) -> Epic`

Load epic from storage.

```python
epic = storage.load_epic("epic-123")
```

##### `save_story(story: Story) -> None`

Save story to storage.

##### `load_story(story_id: str) -> Story`

Load story from storage.

##### `save_sprint(sprint: Sprint) -> None`

Save sprint data.

##### `load_sprint(sprint_id: str) -> Sprint`

Load sprint data.

##### `get_all_epics() -> List[Epic]`

Get all epics in project.

```python
epics = storage.get_all_epics()
for epic in epics:
    print(f"{epic.id}: {epic.title}")
```

##### `get_stories_by_epic(epic_id: str) -> List[Story]`

Get all stories for an epic.

##### `get_project_state() -> Dict[str, Any]`

Get complete project state.

```python
state = storage.get_project_state()
print(f"Total epics: {len(state['epics'])}")
print(f"Active sprints: {len(state['active_sprints'])}")
```

---

## Security

### Agent Security Profiles

Security configuration for agent tool access.

```python
from lib.agent_tool_config import get_agent_security_profile, validate_tool_access

# Get security profile
profile = get_agent_security_profile("CodeAgent")
print(f"Allowed tools: {profile['allowed_tools']}")
print(f"Blocked tools: {profile['blocked_tools']}")
```

#### Security Profiles

| Agent | Allowed Operations | Restricted Operations |
|-------|-------------------|----------------------|
| **Orchestrator** | All tools, system management | Dangerous system commands |
| **DesignAgent** | Read files, create docs, research | Code modification, git operations |
| **CodeAgent** | Edit code, git add/commit, testing | Git push, system admin, file deletion |
| **QAAgent** | Run tests, coverage tools | Source modification, git operations |
| **DataAgent** | Data processing, notebooks | Source code changes, git operations |

#### Validation Functions

##### `validate_tool_access(agent_type: str, tool: str) -> bool`

Check if agent can use specific tool.

```python
if validate_tool_access("CodeAgent", "edit_file"):
    print("CodeAgent can edit files")

if not validate_tool_access("QAAgent", "git_push"):
    print("QAAgent cannot push to git")
```

##### `get_claude_cli_flags(agent_type: str) -> Dict[str, List[str]]`

Get Claude CLI security flags.

```python
flags = get_claude_cli_flags("DesignAgent")
# Returns: {
#     "allowedTools": ["read_file", "create_file", ...],
#     "blockedTools": ["edit_file", "run_bash", ...]
# }
```

---

## Discord Integration

### Discord Bot

Human-In-The-Loop interface via Discord slash commands.

```python
from lib.discord_bot import DiscordBot
import discord

# Initialize bot with orchestrator
bot = DiscordBot(
    orchestrator=orchestrator,
    command_prefix="/",
    log_channel_name="workflow-logs"
)

# Run bot
bot.run(token=DISCORD_BOT_TOKEN)
```

#### Slash Commands

##### Project Management

**`/project register <path> [name]`**

Register a new project for orchestration.

```
/project register /home/user/myproject "My Project"
```

**`/project list`**

List all registered projects.

**`/project select <name>`**

Switch active project context.

##### Epic & Story Management

**`/epic "<description>"`**

Create a new epic.

```
/epic "Build user authentication system with OAuth2 support"
```

**`/backlog view|add_story|prioritize`**

Manage project backlog.

```
/backlog view
/backlog add_story "epic-123" "Implement password reset"
/backlog prioritize
```

##### Sprint Management

**`/sprint plan|start|status|pause|resume`**

Sprint lifecycle management.

```
/sprint plan                    # Plan next sprint
/sprint start                   # Start planned sprint
/sprint status                  # View current progress
/sprint pause "Team offsite"    # Pause with reason
/sprint resume                  # Resume paused sprint
```

##### TDD Commands

**`/tdd design|test|code|refactor|commit`**

TDD workflow commands.

```
/tdd design                     # Start design phase
/tdd test                       # Write failing tests
/tdd code                       # Implement solution
/tdd refactor                   # Improve code quality
/tdd commit                     # Save progress
```

##### Workflow Control

**`/approve [ID...]`**

Approve pending tasks or decisions.

```
/approve                        # Approve all pending
/approve task-123 task-456      # Approve specific tasks
```

**`/request_changes "<feedback>"`**

Request changes on current work.

```
/request_changes "Need better error handling in auth module"
```

**`/state`**

Interactive state visualization.

#### Event Handlers

```python
# Custom event handler
@bot.event
async def on_sprint_complete(sprint: Sprint):
    channel = bot.get_channel(SPRINT_CHANNEL_ID)
    embed = discord.Embed(
        title="Sprint Completed!",
        description=f"Sprint {sprint.id} finished successfully",
        color=discord.Color.green()
    )
    await channel.send(embed=embed)
```

---

## Error Handling

### Exception Hierarchy

```python
from lib.exceptions import (
    WorkflowError,              # Base exception
    StateError,                 # State machine errors
    AgentError,                 # Agent execution errors
    StorageError,               # Persistence errors
    SecurityError,              # Security violations
    ContextError,               # Context management errors
    TDDError                    # TDD workflow errors
)
```

#### Common Exceptions

##### StateError

Invalid state transitions or commands.

```python
try:
    await orchestrator.start_sprint()
except StateError as e:
    print(f"State error: {e}")
    print(f"Current state: {e.current_state}")
    print(f"Allowed commands: {e.allowed_commands}")
```

##### AgentError

Agent task execution failures.

```python
try:
    result = await agent.run(task)
except AgentError as e:
    print(f"Agent failed: {e}")
    print(f"Agent type: {e.agent_type}")
    print(f"Task ID: {e.task_id}")
    print(f"Retry count: {e.retry_count}")
```

##### SecurityError

Security policy violations.

```python
try:
    await code_agent.run_command("rm -rf /")
except SecurityError as e:
    print(f"Security violation: {e}")
    print(f"Blocked tool: {e.tool}")
    print(f"Agent: {e.agent_type}")
```

#### Error Recovery Patterns

```python
from lib.error_recovery import ErrorRecovery

recovery = ErrorRecovery()

# Automatic retry with backoff
result = await recovery.retry_with_backoff(
    func=agent.run,
    args=(task,),
    max_retries=3,
    backoff_factor=2.0
)

# Circuit breaker pattern
breaker = recovery.create_circuit_breaker(
    failure_threshold=5,
    recovery_timeout=60
)

@breaker
async def protected_operation():
    return await external_service.call()
```

---

## Configuration

### Configuration Schema

```yaml
# config.yml
orchestrator:
  mode: "blocking"              # blocking|partial|autonomous
  max_concurrent_projects: 3
  state_save_interval: 60       # seconds
  
agents:
  timeout_minutes: 30
  max_retries: 3
  context_window_size: 8000
  
discord:
  bot_token: "${DISCORD_BOT_TOKEN}"
  guild_id: "${DISCORD_GUILD_ID}"
  log_level: "INFO"
  
storage:
  backend: "file"               # file|database
  path: ".orch-state"
  
security:
  enable_sandboxing: true
  audit_logging: true
  
context:
  enable_caching: true
  cache_ttl_minutes: 60
  max_cache_size_mb: 500
  
tdd:
  enforce_red_green_refactor: true
  min_test_coverage: 80
  auto_progression: false
  
projects:
  - name: "backend-api"
    path: "/projects/backend"
    mode: "partial"
    tdd_enabled: true
  - name: "frontend-app"
    path: "/projects/frontend"
    mode: "autonomous"
```

### Environment Variables

```python
import os
from lib.config import Config

# Load with environment variable substitution
config = Config.from_file(
    "config.yml",
    env_vars={
        "DISCORD_BOT_TOKEN": os.environ["DISCORD_BOT_TOKEN"],
        "DISCORD_GUILD_ID": os.environ["DISCORD_GUILD_ID"]
    }
)

# Access configuration
print(config.orchestrator.mode)
print(config.agents.timeout_minutes)
```

### Dynamic Configuration

```python
# Runtime configuration updates
config.update_agent_timeout(45)
config.enable_tdd_auto_progression()

# Project-specific overrides
config.set_project_config(
    "backend-api",
    {
        "mode": "blocking",
        "tdd_min_coverage": 90
    }
)
```

---

## Code Examples

### Complete Workflow Implementation

```python
import asyncio
from lib.orchestrator import Orchestrator
from lib.agents import create_agent
from lib.context_manager import ContextManager

async def run_authentication_epic():
    """Complete example of building authentication system."""
    
    # Initialize components
    context_manager = ContextManager(project_path=".")
    orchestrator = Orchestrator(context_manager=context_manager)
    
    # Create epic
    epic = await orchestrator.create_epic(
        "Build complete authentication system",
        priority="high",
        tdd_requirements=[
            "100% test coverage for security features",
            "Integration tests for all endpoints",
            "Security audit before deployment"
        ]
    )
    
    # Create stories
    stories = []
    for story_def in [
        ("User Registration", ["Email validation", "Password requirements"]),
        ("User Login", ["JWT tokens", "Session management"]),
        ("Password Reset", ["Secure token generation", "Email delivery"]),
        ("OAuth Integration", ["Google OAuth", "GitHub OAuth"])
    ]:
        story = await orchestrator.create_story(
            epic_id=epic.id,
            title=story_def[0],
            description=f"Implement {story_def[0]}",
            acceptance_criteria=story_def[1]
        )
        stories.append(story)
    
    # Plan sprint
    sprint = await orchestrator.plan_sprint(
        story_ids=[s.id for s in stories[:2]],  # First 2 stories
        sprint_goal="Basic authentication flow",
        duration_days=10
    )
    
    # Start sprint
    await orchestrator.start_sprint()
    
    # Process each story with TDD
    for story in stories[:2]:
        await process_story_tdd(orchestrator, story)
    
    # Complete sprint
    await orchestrator.complete_sprint({
        "what_went_well": [
            "TDD helped catch edge cases early",
            "Good test coverage achieved"
        ],
        "what_could_improve": [
            "Better time estimation needed"
        ],
        "action_items": [
            "Create estimation guidelines"
        ]
    })

async def process_story_tdd(orchestrator, story):
    """Process a story through complete TDD cycle."""
    
    # Initialize agents
    design_agent = create_agent("DesignAgent")
    qa_agent = create_agent("QAAgent")
    code_agent = create_agent("CodeAgent")
    
    # Create TDD cycle
    from lib.tdd_models import TDDCycle, TDDTask
    cycle = TDDCycle(story_id=story.id)
    
    # Phase 1: Design
    design_task = Task(
        agent_type="DesignAgent",
        command=f"Create technical design for {story.title}",
        context={"story": story.to_dict()}
    )
    design_result = await design_agent.run(design_task)
    
    # Phase 2: Write failing tests
    test_task = Task(
        agent_type="QAAgent",
        command=f"Write comprehensive tests for {story.title}",
        context={
            "story": story.to_dict(),
            "design": design_result.artifacts.get("design.md")
        }
    )
    test_result = await qa_agent.run(test_task)
    
    # Phase 3: Implement code
    code_task = Task(
        agent_type="CodeAgent",
        command=f"Implement {story.title} to pass all tests",
        context={
            "story": story.to_dict(),
            "tests": test_result.artifacts,
            "design": design_result.artifacts.get("design.md")
        }
    )
    code_result = await code_agent.run(code_task)
    
    # Phase 4: Refactor
    refactor_task = Task(
        agent_type="CodeAgent",
        command="Refactor code for better quality",
        context={
            "story": story.to_dict(),
            "implementation": code_result.artifacts
        }
    )
    refactor_result = await code_agent.run(refactor_task)
    
    return {
        "design": design_result,
        "tests": test_result,
        "code": code_result,
        "refactor": refactor_result
    }

# Run the example
if __name__ == "__main__":
    asyncio.run(run_authentication_epic())
```

### Custom Agent Implementation

```python
from lib.agents import BaseAgent, Task, AgentResult

class SecurityAgent(BaseAgent):
    """Custom agent for security analysis and validation."""
    
    def __init__(self):
        super().__init__(
            name="SecurityAgent",
            capabilities=[
                "security_audit",
                "vulnerability_scan",
                "penetration_test",
                "compliance_check"
            ]
        )
    
    async def run(self, task: Task, dry_run: bool = False) -> AgentResult:
        """Execute security-related tasks."""
        
        # Prepare context
        context = await self.prepare_context(
            task=task,
            story_id=task.context.get("story_id"),
            max_tokens=6000
        )
        
        try:
            if "security_audit" in task.command:
                return await self._run_security_audit(task, context)
            elif "vulnerability_scan" in task.command:
                return await self._run_vulnerability_scan(task, context)
            else:
                return await self._general_security_check(task, context)
                
        except Exception as e:
            # Record failure for learning
            await self.record_decision(
                description="Security check failed",
                rationale=str(e),
                outcome="failure",
                confidence=0.0
            )
            
            return AgentResult(
                success=False,
                output="",
                error=str(e)
            )
    
    async def _run_security_audit(
        self, 
        task: Task, 
        context: AgentContext
    ) -> AgentResult:
        """Perform comprehensive security audit."""
        
        # Analyze code for security issues
        issues = []
        recommendations = []
        
        for file in context.get_files_by_type(FileType.SOURCE):
            # Check for common vulnerabilities
            if "password" in file.content and "plain" in file.content:
                issues.append({
                    "severity": "HIGH",
                    "file": file.path,
                    "issue": "Potential plaintext password storage"
                })
            
            if "eval(" in file.content or "exec(" in file.content:
                issues.append({
                    "severity": "CRITICAL",
                    "file": file.path,
                    "issue": "Use of eval/exec - code injection risk"
                })
        
        # Generate report
        report = self._generate_security_report(issues, recommendations)
        
        # Record decision
        await self.record_decision(
            description="Security audit completed",
            rationale=f"Found {len(issues)} security issues",
            outcome="success",
            confidence=0.9,
            artifacts={"security_report.md": report}
        )
        
        return AgentResult(
            success=True,
            output=f"Security audit complete: {len(issues)} issues found",
            artifacts={"security_report.md": report}
        )

# Register custom agent
from lib.agents import AGENT_REGISTRY
AGENT_REGISTRY["SecurityAgent"] = SecurityAgent
```

### Context Management Example

```python
from lib.context_manager import ContextManager
from lib.context.models import ContextRequest, CompressionLevel

async def smart_context_preparation():
    """Demonstrate advanced context management features."""
    
    manager = ContextManager(
        project_path=".",
        enable_caching=True,
        enable_monitoring=True
    )
    
    # Prepare context with compression
    context = await manager.prepare_context(
        agent_type="CodeAgent",
        task={
            "description": "Refactor authentication module",
            "focus_areas": ["src/auth/", "tests/auth/"]
        },
        max_tokens=4000,
        story_id="AUTH-001",
        compression_level=CompressionLevel.AGGRESSIVE
    )
    
    # Monitor token usage
    print(f"Initial tokens: {context.get_total_token_estimate()}")
    
    # Add decision from previous phase
    decisions = await manager.get_recent_decisions(
        agent_type="DesignAgent",
        story_id="AUTH-001",
        limit=5
    )
    
    for decision in decisions:
        context.add_decision(decision)
    
    print(f"After decisions: {context.get_total_token_estimate()}")
    
    # Create handoff for next agent
    handoff_id = await manager.create_phase_handoff(
        from_agent="CodeAgent",
        to_agent="QAAgent",
        story_id="AUTH-001",
        handoff_data={
            "refactored_files": ["src/auth/login.py", "src/auth/jwt.py"],
            "test_focus": ["Edge cases for JWT expiration"],
            "context_snapshot": context.to_dict()
        }
    )
    
    return context, handoff_id

# Usage
context, handoff = asyncio.run(smart_context_preparation())
```

### Monitoring and Metrics

```python
from lib.multi_project_monitoring import MultiProjectMonitor
from lib.context_monitoring import ContextMonitor

async def setup_monitoring():
    """Configure comprehensive monitoring."""
    
    # Project-level monitoring
    project_monitor = MultiProjectMonitor()
    
    # Context performance monitoring
    context_monitor = ContextMonitor()
    
    # Register callbacks
    @project_monitor.on_event("sprint_started")
    async def on_sprint_start(event):
        print(f"Sprint {event.sprint_id} started in {event.project}")
    
    @context_monitor.on_metric("token_usage_high")
    async def on_high_token_usage(metric):
        if metric.value > 7000:
            print(f"WARNING: High token usage: {metric.value}")
    
    # Start monitoring
    await project_monitor.start()
    await context_monitor.start()
    
    # Get real-time metrics
    metrics = await project_monitor.get_metrics()
    print(f"Active projects: {metrics['active_projects']}")
    print(f"Total stories: {metrics['total_stories']}")
    print(f"Average velocity: {metrics['avg_velocity']}")
    
    # Context performance
    ctx_metrics = await context_monitor.get_performance_metrics()
    print(f"Cache hit rate: {ctx_metrics['cache_hit_rate']}%")
    print(f"Avg preparation time: {ctx_metrics['avg_prep_time_ms']}ms")
```

---

## API Versioning

### Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | 2025-01-19 | Initial stable release |
| 0.9.0 | 2024-12-15 | Beta with core features |
| 0.8.0 | 2024-11-01 | Added TDD system |

### Deprecation Policy

APIs are deprecated with 3 months notice. Deprecated APIs include:
- Deprecation warnings in responses
- Migration guides in documentation
- Sunset dates in headers

### Breaking Changes

Breaking changes are only introduced in major versions. Migration tools provided:

```python
from lib.migration import migrate_to_v1

# Automatic migration
migrate_to_v1(project_path=".")
```

---

## Auto-Generation Notes

This documentation can be regenerated using:

```bash
# Generate API docs from code
python tools/documentation/generate_api_docs.py

# Include docstrings and type hints
python tools/documentation/generate_api_docs.py --include-private --format=markdown

# Generate OpenAPI spec
python tools/documentation/generate_api_docs.py --format=openapi --output=api-spec.json
```

For the latest API updates, always refer to the source code docstrings which are the source of truth.

---

## 🧪 Testing Guide {#testing-guide}

### 🚀 Live Endpoint Testing

<div class="testing-section">
  <div class="test-environment">
    <h4>🌐 Test Environment Setup</h4>
    <pre><code class="language-bash"># 🔧 Set up test environment
export DISCORD_BOT_TOKEN="your-test-token"
export TEST_PROJECT_PATH="/tmp/test-project"

# 🚀 Start test orchestrator
python -m pytest tests/integration/ -v

# 🔄 Or run specific API tests
python -m pytest tests/integration/test_orchestrator_api.py::test_create_epic -v</code></pre>
  </div>
  
  <div class="test-examples">
    <h4>🧪 API Test Examples</h4>
    
    <details>
      <summary>📋 Test Epic Creation</summary>
      
```python title="test_epic_creation.py"
import pytest
from lib.orchestrator import Orchestrator

@pytest.mark.asyncio
async def test_create_epic_basic():
    """Test basic epic creation functionality."""
    orchestrator = Orchestrator()
    
    epic = await orchestrator.create_epic(
        "Test Epic",
        priority="high"
    )
    
    assert epic.id is not None
    assert epic.title == "Test Epic"
    assert epic.status == EpicStatus.ACTIVE
    assert epic.priority == "high"

@pytest.mark.asyncio  
async def test_create_epic_with_tdd():
    """Test epic creation with TDD requirements."""
    orchestrator = Orchestrator()
    
    tdd_requirements = [
        "100% test coverage required",
        "Integration tests mandatory"
    ]
    
    epic = await orchestrator.create_epic(
        "TDD Epic",
        priority="medium",
        tdd_requirements=tdd_requirements
    )
    
    assert len(epic.tdd_requirements) == 2
    assert "100% test coverage required" in epic.tdd_requirements
```
    </details>
    
    <details>
      <summary>🔄 Test State Machine</summary>
      
```python title="test_state_machine.py"
import pytest
from lib.state_machine import StateMachine, State

def test_valid_transitions():
    """Test valid state transitions."""
    sm = StateMachine()
    
    # Test epic creation
    result = sm.transition("/epic")
    assert result.success
    assert result.new_state == State.BACKLOG_READY
    
    # Test sprint planning
    result = sm.transition("/sprint plan")
    assert result.success
    assert result.new_state == State.SPRINT_PLANNED

def test_invalid_transitions():
    """Test invalid state transitions."""
    sm = StateMachine()
    
    # Try to start sprint without planning
    result = sm.transition("/sprint start") 
    assert not result.success
    assert "Invalid state transition" in result.error_message
    assert result.hint is not None
```
    </details>
  </div>
</div>

### 📊 Performance Testing

<div class="performance-testing">
  <h4>⚡ Load Testing</h4>
  
```python title="performance_test.py"
import asyncio
import time
from lib.orchestrator import Orchestrator

async def benchmark_epic_creation(num_epics=100):
    """Benchmark epic creation performance."""
    orchestrator = Orchestrator()
    
    start_time = time.time()
    
    # Create epics concurrently
    tasks = [
        orchestrator.create_epic(f"Epic {i}", priority="medium")
        for i in range(num_epics)
    ]
    
    epics = await asyncio.gather(*tasks)
    
    end_time = time.time()
    duration = end_time - start_time
    
    print(f"📊 Created {len(epics)} epics in {duration:.2f}s")
    print(f"⚡ Rate: {len(epics)/duration:.2f} epics/second")
    
    return epics

# Run benchmark
asyncio.run(benchmark_epic_creation())
```
</div>

### 🐛 Integration Testing

<div class="integration-testing">
  <h4>🔗 End-to-End Workflow</h4>
  
```python title="integration_test.py"
import pytest
from lib.orchestrator import Orchestrator
from lib.agents import create_agent

@pytest.mark.asyncio
async def test_full_workflow():
    """Test complete epic → story → sprint → agent workflow."""
    orchestrator = Orchestrator()
    
    # 1. 🎯 Create epic
    epic = await orchestrator.create_epic(
        "Integration Test Epic",
        priority="high",
        tdd_requirements=["100% coverage"]
    )
    
    # 2. 📝 Create stories
    story = await orchestrator.create_story(
        epic_id=epic.id,
        title="Test Story",
        description="Test user story",
        acceptance_criteria=["Criterion 1", "Criterion 2"]
    )
    
    # 3. 🏃‍♂️ Plan sprint
    sprint = await orchestrator.plan_sprint(
        story_ids=[story.id],
        sprint_goal="Test sprint goal",
        duration_days=7
    )
    
    # 4. ▶️ Start sprint
    success = await orchestrator.start_sprint()
    assert success
    
    # 5. 🤖 Execute with agents
    code_agent = create_agent("CodeAgent")
    result = await code_agent.run(
        Task(
            id="test-task",
            agent_type="CodeAgent", 
            command="implement test feature",
            context={"story_id": story.id}
        )
    )
    
    assert result.success
    
    # 6. 📊 Verify metrics
    metrics = await orchestrator.get_metrics()
    assert metrics["total_epics"] >= 1
    assert metrics["active_sprints"] >= 1
```
</div>

---

## 🎨 Interactive JavaScript Components

<script>
// 🔍 API Search Functionality
function setupAPISearch() {
    const searchInput = document.getElementById('api-search');
    const searchResults = document.getElementById('search-results');
    
    if (!searchInput) return;
    
    const apiItems = [
        { name: 'create_epic', type: 'method', description: 'Create a new epic' },
        { name: 'create_story', type: 'method', description: 'Create a user story' },
        { name: 'plan_sprint', type: 'method', description: 'Plan a new sprint' },
        { name: 'Orchestrator', type: 'class', description: 'Main coordination engine' },
        { name: 'BaseAgent', type: 'class', description: 'Base agent class' },
        { name: 'Epic', type: 'model', description: 'Epic data model' },
        { name: 'Story', type: 'model', description: 'Story data model' },
        { name: 'Sprint', type: 'model', description: 'Sprint data model' }
    ];
    
    searchInput.addEventListener('input', (e) => {
        const query = e.target.value.toLowerCase();
        if (query.length < 2) {
            searchResults.innerHTML = '';
            return;
        }
        
        const results = apiItems.filter(item => 
            item.name.toLowerCase().includes(query) ||
            item.description.toLowerCase().includes(query)
        );
        
        searchResults.innerHTML = results.map(item => `
            <div class="search-result">
                <span class="result-type">${item.type}</span>
                <a href="#${item.name.toLowerCase()}">${item.name}</a>
                <span class="result-description">${item.description}</span>
            </div>
        `).join('');
    });
}

// 🎛️ Tab Functionality
function setupTabs() {
    document.addEventListener('click', (e) => {
        if (e.target.classList.contains('tab-btn')) {
            const tabName = e.target.getAttribute('data-tab');
            const container = e.target.closest('.example-tabs, .api-explorer');
            
            // Update active tab button
            container.querySelectorAll('.tab-btn').forEach(btn => 
                btn.classList.remove('active')
            );
            e.target.classList.add('active');
            
            // Update active content
            const contentContainer = container.parentElement || container;
            contentContainer.querySelectorAll('.tab-content').forEach(content => 
                content.classList.remove('active')
            );
            
            const targetContent = document.getElementById(tabName);
            if (targetContent) {
                targetContent.classList.add('active');
            }
        }
    });
}

// 📋 Copy to Clipboard
function copyToClipboard(elementId) {
    const element = document.getElementById(elementId);
    if (!element) return;
    
    const code = element.textContent || element.innerText;
    navigator.clipboard.writeText(code).then(() => {
        // Show success feedback
        const button = event.target;
        const originalText = button.textContent;
        button.textContent = '✅ Copied!';
        setTimeout(() => {
            button.textContent = originalText;
        }, 2000);
    }).catch(err => {
        console.error('Failed to copy: ', err);
    });
}

// ▶️ Run Example (placeholder)
function runExample(exampleId) {
    console.log(`Running example: ${exampleId}`);
    // Placeholder for running examples in browser
    alert('🚧 Example execution coming soon! For now, copy the code and run locally.');
}

// 📮 Postman Integration
function downloadPostmanCollection() {
    const collection = {
        info: {
            name: "AI Agent TDD-Scrum API",
            schema: "https://schema.getpostman.com/json/collection/v2.1.0/collection.json"
        },
        item: [
            {
                name: "Orchestrator",
                item: [
                    {
                        name: "Create Epic",
                        request: {
                            method: "POST",
                            header: [{"key": "Content-Type", "value": "application/json"}],
                            body: {
                                mode: "raw",
                                raw: JSON.stringify({
                                    description: "Build authentication system",
                                    priority: "high",
                                    tdd_requirements: ["100% test coverage"]
                                })
                            },
                            url: {
                                raw: "{{base_url}}/api/epics",
                                host: ["{{base_url}}"],
                                path: ["api", "epics"]
                            }
                        }
                    }
                ]
            }
        ]
    };
    
    const blob = new Blob([JSON.stringify(collection, null, 2)], 
        { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'ai-agent-tdd-scrum-api.postman_collection.json';
    a.click();
    URL.revokeObjectURL(url);
}

function openPostmanDocs() {
    window.open('https://learning.postman.com/docs/getting-started/introduction/', '_blank');
}

// 🚀 Initialize everything when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    setupAPISearch();
    setupTabs();
    
    // Add syntax highlighting classes
    document.querySelectorAll('pre code').forEach(block => {
        if (block.className === '') {
            block.className = 'language-python';
        }
    });
});
</script>

<style>
/* 🎨 Enhanced API Documentation Styles */
.api-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 1rem;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    border-radius: 8px;
    margin-bottom: 2rem;
}

.api-info {
    display: flex;
    gap: 1rem;
}

.api-version, .api-status, .api-updated {
    padding: 0.25rem 0.5rem;
    background: rgba(255,255,255,0.2);
    border-radius: 4px;
    font-size: 0.875rem;
}

.btn {
    padding: 0.5rem 1rem;
    border: none;
    border-radius: 4px;
    text-decoration: none;
    cursor: pointer;
    transition: all 0.2s;
}

.btn-primary { background: #3b82f6; color: white; }
.btn-secondary { background: #6b7280; color: white; }
.btn-outline { background: transparent; border: 1px solid white; color: white; }
.btn-sm { padding: 0.25rem 0.5rem; font-size: 0.75rem; }

.quick-start-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
    gap: 1rem;
    margin: 2rem 0;
}

.quick-start-card {
    border: 1px solid #e5e7eb;
    border-radius: 8px;
    padding: 1rem;
    background: #f9fafb;
}

.nav-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
    gap: 1rem;
    margin: 2rem 0;
}

.nav-section h3 {
    color: #374151;
    margin-bottom: 0.5rem;
}

.nav-section ul {
    list-style: none;
    padding: 0;
}

.nav-section li {
    margin-bottom: 0.25rem;
}

.search-section {
    margin: 2rem 0;
    position: relative;
}

#api-search {
    width: 100%;
    padding: 0.75rem;
    border: 2px solid #e5e7eb;
    border-radius: 8px;
    font-size: 1rem;
}

.search-results {
    position: absolute;
    top: 100%;
    left: 0;
    right: 0;
    background: white;
    border: 1px solid #e5e7eb;
    border-radius: 4px;
    box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    z-index: 1000;
    max-height: 300px;
    overflow-y: auto;
}

.search-result {
    padding: 0.5rem;
    border-bottom: 1px solid #f3f4f6;
    display: flex;
    align-items: center;
    gap: 0.5rem;
}

.result-type {
    padding: 0.125rem 0.25rem;
    background: #ddd6fe;
    border-radius: 3px;
    font-size: 0.75rem;
    font-weight: 500;
}

.component-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 1rem;
    padding: 1rem;
    background: #f8fafc;
    border-radius: 6px;
}

.component-info {
    display: flex;
    gap: 0.5rem;
}

.component-type, .component-stability, .component-async {
    padding: 0.25rem 0.5rem;
    border-radius: 4px;
    font-size: 0.75rem;
    font-weight: 500;
}

.method-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin: 1rem 0;
    padding: 1rem;
    background: #f1f5f9;
    border-radius: 6px;
}

.method-signature code {
    font-family: 'SF Mono', Monaco, 'Cascadia Code', monospace;
    font-size: 0.9rem;
    font-weight: 500;
}

.method-badges {
    display: flex;
    gap: 0.5rem;
}

.badge {
    padding: 0.25rem 0.5rem;
    border-radius: 4px;
    font-size: 0.75rem;
    font-weight: 500;
}

.badge.async { background: #fef3c7; color: #92400e; }
.badge.stable { background: #dcfce7; color: #166534; }
.badge.core { background: #dbeafe; color: #1d4ed8; }

.example-tabs, .explorer-tabs {
    display: flex;
    gap: 0.25rem;
    margin-bottom: 1rem;
    border-bottom: 2px solid #e5e7eb;
}

.tab-btn {
    padding: 0.5rem 1rem;
    border: none;
    background: none;
    cursor: pointer;
    border-bottom: 2px solid transparent;
    transition: all 0.2s;
}

.tab-btn.active {
    border-bottom-color: #3b82f6;
    color: #3b82f6;
    font-weight: 500;
}

.tab-content {
    display: none;
}

.tab-content.active {
    display: block;
}

.parameter-table table {
    width: 100%;
    border-collapse: collapse;
    margin: 1rem 0;
}

.parameter-table th,
.parameter-table td {
    padding: 0.5rem;
    border: 1px solid #e5e7eb;
    text-align: left;
}

.parameter-table th {
    background: #f9fafb;
    font-weight: 500;
}

.testing-section {
    background: #f8fafc;
    padding: 2rem;
    border-radius: 8px;
    margin: 2rem 0;
}

.postman-section {
    background: linear-gradient(135deg, #ff6b35 0%, #f7931e 100%);
    color: white;
    padding: 2rem;
    border-radius: 8px;
    margin: 2rem 0;
}

.postman-buttons {
    display: flex;
    gap: 1rem;
    margin: 1rem 0;
}

details {
    margin: 1rem 0;
}

summary {
    cursor: pointer;
    padding: 0.5rem;
    background: #f3f4f6;
    border-radius: 4px;
    font-weight: 500;
}

/* Code highlighting improvements */
pre {
    background: #1e293b;
    color: #e2e8f0;
    border-radius: 6px;
    overflow-x: auto;
}

pre code {
    display: block;
    padding: 1rem;
}

code {
    background: #f1f5f9;
    padding: 0.125rem 0.25rem;
    border-radius: 3px;
    font-family: 'SF Mono', Monaco, 'Cascadia Code', monospace;
}

/* Responsive design */
@media (max-width: 768px) {
    .api-header {
        flex-direction: column;
        gap: 1rem;
    }
    
    .quick-start-grid,
    .nav-grid {
        grid-template-columns: 1fr;
    }
    
    .component-header,
    .method-header {
        flex-direction: column;
        align-items: flex-start;
        gap: 0.5rem;
    }
}
</style>