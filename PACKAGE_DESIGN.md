# Agent-Workflow Package Design Specification

## Overview
Transform agent-workflow from a git-clone repository into a pip-installable package with comprehensive CLI registration system for seamless one-click installation and project management.

## 1. Package Structure Design

### 1.1 New Directory Structure
```
agent-workflow/
├── pyproject.toml                    # Modern Python packaging
├── setup.py                         # Fallback compatibility
├── README.md                         # PyPI description
├── LICENSE                          # Package license
├── MANIFEST.in                      # Include non-Python files
├── agent_workflow/                  # Main package (renamed from lib/)
│   ├── __init__.py                  # Package initialization
│   ├── version.py                   # Version management
│   ├── cli/                         # CLI command modules
│   │   ├── __init__.py
│   │   ├── main.py                  # Main CLI entry point
│   │   ├── init.py                  # Global initialization
│   │   ├── project.py               # Project management
│   │   ├── setup.py                 # Configuration setup
│   │   └── orchestrator.py          # Orchestrator control
│   ├── core/                        # Core orchestrator logic
│   │   ├── __init__.py
│   │   ├── orchestrator.py          # Main orchestrator
│   │   ├── state_machine.py         # State management
│   │   └── project_storage.py       # Data persistence
│   ├── agents/                      # AI agent implementations
│   │   ├── __init__.py
│   │   ├── base.py                  # Base agent class
│   │   ├── code_agent.py
│   │   ├── design_agent.py
│   │   ├── qa_agent.py
│   │   └── data_agent.py
│   ├── integrations/                # External integrations
│   │   ├── __init__.py
│   │   ├── discord_bot.py           # Discord integration
│   │   ├── claude_client.py         # Claude API client
│   │   └── github_client.py         # GitHub integration
│   ├── security/                    # Security and access control
│   │   ├── __init__.py
│   │   ├── agent_permissions.py     # Agent access control
│   │   └── credential_manager.py    # Encrypted credential storage
│   ├── config/                      # Configuration management
│   │   ├── __init__.py
│   │   ├── global_config.py         # Global configuration
│   │   ├── project_config.py        # Project-specific config
│   │   └── defaults.py              # Default configurations
│   └── templates/                   # Template files
│       ├── orch-config.yaml.template
│       ├── project-config.yaml.template
│       └── discord-config.yaml.template
├── tests/                           # Test suite (unchanged structure)
├── docs/                           # Built documentation (dist)
└── docs_src/                       # Source documentation (unchanged)
```

### 1.2 Entry Points Configuration
```toml
[project.scripts]
agent-orch = "agent_workflow.cli.main:main"
aw = "agent_workflow.cli.main:main"  # Short alias

[project.entry-points."agent_workflow.commands"]
init = "agent_workflow.cli.init:init_command"
register-project = "agent_workflow.cli.project:register_command"
setup-discord = "agent_workflow.cli.setup:setup_discord_command"
setup-api = "agent_workflow.cli.setup:setup_api_command"
start = "agent_workflow.cli.orchestrator:start_command"
status = "agent_workflow.cli.orchestrator:status_command"
configure = "agent_workflow.cli.setup:configure_command"
```

## 2. CLI Command System Design

### 2.1 Command Hierarchy
```
agent-orch
├── init                             # Initialize global environment
├── register-project <path> [name]   # Register project for orchestration
├── setup-discord --token <token>    # Configure Discord integration
├── setup-api --provider <provider>  # Configure AI API integration
├── start [project]                  # Start orchestration
├── status                           # Show global status
├── configure                        # Interactive configuration
├── projects                         # List registered projects
│   ├── list                         # List all projects
│   ├── remove <name>                # Unregister project
│   └── validate <name>              # Validate project setup
└── version                          # Show version info
```

### 2.2 Detailed Command Specifications

#### 2.2.1 `agent-orch init`
```bash
# Initialize global orchestrator environment
agent-orch init [--config-dir <path>] [--force]

Options:
  --config-dir PATH    Custom configuration directory (default: ~/.agent-workflow)
  --force             Overwrite existing configuration
  --interactive       Run interactive setup wizard
  --minimal           Create minimal configuration without integrations

Creates:
  ~/.agent-workflow/
  ├── config.yaml                   # Global configuration
  ├── credentials.enc               # Encrypted credentials
  ├── projects/                     # Project registry
  ├── logs/                        # System logs
  └── templates/                   # Configuration templates
```

#### 2.2.2 `agent-orch register-project`
```bash
# Register project for orchestration
agent-orch register-project <path> [name] [options]

Arguments:
  path                 Path to project directory (absolute or relative)
  name                 Project name (optional, defaults to directory name)

Options:
  --mode MODE         Orchestration mode: blocking|partial|autonomous (default: blocking)
  --validate          Validate project structure before registration
  --create-channel    Auto-create Discord channel for project
  --framework TYPE    Project framework: general|web|api|ml|mobile (default: general)

Examples:
  agent-orch register-project ./my-webapp webapp --mode partial
  agent-orch register-project /home/user/api-project --validate --create-channel
```

#### 2.2.3 `agent-orch setup-discord`
```bash
# Configure Discord integration
agent-orch setup-discord [options]

Options:
  --token TOKEN       Discord bot token
  --guild-id ID       Discord server ID
  --interactive       Interactive setup with validation
  --test-connection   Test Discord connection
  --create-channels   Auto-create project channels

Interactive Flow:
  1. Prompt for bot token with validation
  2. Test connection and permissions
  3. List available guilds for selection
  4. Configure channel naming convention
  5. Set up webhook permissions
```

#### 2.2.4 `agent-orch setup-api`
```bash
# Configure AI API integration
agent-orch setup-api [options]

Options:
  --provider PROVIDER  API provider: claude|openai|local (default: claude)
  --key KEY           API key
  --endpoint URL      Custom API endpoint (for local/custom providers)
  --model MODEL       Default model name
  --interactive       Interactive setup with validation
  --test-connection   Test API connection

Interactive Flow:
  1. Select AI provider
  2. Enter API credentials with validation
  3. Test connection and model access
  4. Configure rate limiting and quotas
  5. Set default model preferences
```

#### 2.2.5 `agent-orch start`
```bash
# Start orchestration
agent-orch start [project] [options]

Arguments:
  project             Project name to start (optional, starts all if omitted)

Options:
  --mode MODE         Override orchestration mode for this session
  --discord           Start with Discord bot integration
  --daemon            Run as background daemon
  --log-level LEVEL   Set logging level: DEBUG|INFO|WARN|ERROR (default: INFO)
  --config FILE       Use custom configuration file

Examples:
  agent-orch start webapp --discord
  agent-orch start --daemon --log-level DEBUG
  agent-orch start my-project --mode autonomous
```

#### 2.2.6 `agent-orch status`
```bash
# Show global orchestration status
agent-orch status [options]

Options:
  --project PROJECT   Show status for specific project
  --verbose           Show detailed status information
  --json              Output in JSON format
  --watch             Continuously update status display

Output Format:
  Global Status:
  ├── Configuration: ✓ Valid
  ├── Discord Bot: ✓ Connected (3 channels)
  ├── AI Provider: ✓ Claude (API key valid)
  └── Projects: 2 registered, 1 active

  Projects:
  ├── webapp (active)
  │   ├── State: SPRINT_ACTIVE
  │   ├── Discord: #hostname-webapp
  │   └── Last Activity: 2 minutes ago
  └── api-project (idle)
      ├── State: BACKLOG_READY
      ├── Discord: #hostname-api-project
      └── Last Activity: 1 hour ago
```

#### 2.2.7 `agent-orch configure`
```bash
# Interactive configuration wizard
agent-orch configure [options]

Options:
  --section SECTION   Configure specific section: global|discord|api|projects
  --reset            Reset configuration to defaults
  --export FILE      Export configuration to file
  --import FILE      Import configuration from file

Interactive Flow:
  1. Display current configuration status
  2. Present menu of configuration options
  3. Guide through each configuration step
  4. Validate settings as they're entered
  5. Save and test complete configuration
```

## 3. Configuration Management System

### 3.1 Global Configuration Structure
```yaml
# ~/.agent-workflow/config.yaml
version: "1.0"
created: "2024-01-15T10:30:00Z"
last_updated: "2024-01-15T15:45:00Z"

global:
  installation_id: "uuid-here"
  user_profile: "solo-engineer"  # or "team-lead", "researcher"
  default_mode: "blocking"       # blocking, partial, autonomous
  log_level: "INFO"
  data_retention_days: 30

ai_provider:
  provider: "claude"             # claude, openai, local
  model: "claude-3.5-sonnet"
  api_endpoint: null             # for custom providers
  rate_limit:
    requests_per_minute: 50
    tokens_per_minute: 100000
  credentials_encrypted: true

discord:
  enabled: true
  guild_id: "1234567890"
  channel_prefix: "orch"         # Results in #orch-projectname
  bot_permissions: ["send_messages", "manage_channels", "embed_links"]
  webhook_url_encrypted: true

security:
  agent_restrictions_enabled: true
  command_approval_required: true
  dangerous_commands_blocked: true
  credential_encryption_key: "path/to/key"

projects:
  registry_path: "~/.agent-workflow/projects"
  auto_discovery: false
  validation_on_register: true
  max_concurrent: 5
```

### 3.2 Project Registry Structure
```yaml
# ~/.agent-workflow/projects/registry.yaml
projects:
  webapp:
    name: "webapp"
    path: "/home/user/projects/webapp"
    registered: "2024-01-15T10:30:00Z"
    last_active: "2024-01-15T15:45:00Z"
    mode: "partial"
    framework: "web"
    discord_channel: "#orch-webapp"
    status: "active"
    metadata:
      language: "python"
      framework: "flask"
      repository: "https://github.com/user/webapp"
  
  api-project:
    name: "api-project"
    path: "/home/user/projects/api"
    registered: "2024-01-14T09:15:00Z"
    last_active: "2024-01-15T14:30:00Z"
    mode: "blocking"
    framework: "api"
    discord_channel: "#orch-api-project"
    status: "idle"
    metadata:
      language: "python"
      framework: "fastapi"
      repository: "https://github.com/user/api"
```

### 3.3 Credential Management
```python
# Encrypted credential storage using cryptography library
class CredentialManager:
    def __init__(self, config_dir: Path):
        self.config_dir = config_dir
        self.key_file = config_dir / "credentials.key"
        self.creds_file = config_dir / "credentials.enc"
    
    def store_credential(self, key: str, value: str) -> None:
        """Store encrypted credential"""
        
    def retrieve_credential(self, key: str) -> str:
        """Retrieve and decrypt credential"""
        
    def list_credentials(self) -> List[str]:
        """List available credential keys"""
        
    def delete_credential(self, key: str) -> None:
        """Delete stored credential"""
```

## 4. Installation Flow Design

### 4.1 PyPI Package Configuration
```toml
# pyproject.toml
[build-system]
requires = ["setuptools>=61.0", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "agent-workflow"
version = "1.0.0"
description = "AI Agent TDD-Scrum Orchestration Framework"
readme = "README.md"
license = {text = "MIT"}
authors = [
    {name = "Agent-Workflow Contributors", email = "contact@agent-workflow.dev"}
]
keywords = ["ai", "agents", "tdd", "scrum", "orchestration", "workflow"]
classifiers = [
    "Development Status :: 4 - Beta",
    "Intended Audience :: Developers",
    "License :: OSI Approved :: MIT License",
    "Programming Language :: Python :: 3",
    "Programming Language :: Python :: 3.8",
    "Programming Language :: Python :: 3.9",
    "Programming Language :: Python :: 3.10",
    "Programming Language :: Python :: 3.11",
    "Topic :: Software Development :: Libraries :: Python Modules",
    "Topic :: Software Development :: Quality Assurance",
    "Topic :: Software Development :: Testing",
]
requires-python = ">=3.8"
dependencies = [
    "discord.py>=2.3.0",
    "PyGithub>=1.59.0",
    "PyYAML>=6.0",
    "cryptography>=41.0.0",
    "click>=8.1.0",
    "rich>=13.0.0",
    "tabulate>=0.9.0",
    "python-dotenv>=1.0.0",
    "aiofiles>=23.0.0",
    "watchdog>=3.0.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=7.4.0",
    "pytest-asyncio>=0.21.0",
    "pytest-cov>=4.1.0",
    "black>=23.0.0",
    "flake8>=6.0.0",
    "mypy>=1.5.0",
]
docs = [
    "mkdocs>=1.5.0",
    "mkdocs-material>=9.2.0",
    "mkdocs-mermaid2-plugin>=1.1.0",
]

[project.urls]
Homepage = "https://github.com/agent-workflow/agent-workflow"
Documentation = "https://agent-workflow.readthedocs.io"
Repository = "https://github.com/agent-workflow/agent-workflow"
"Bug Reports" = "https://github.com/agent-workflow/agent-workflow/issues"

[project.scripts]
agent-orch = "agent_workflow.cli.main:main"
aw = "agent_workflow.cli.main:main"

[tool.setuptools.packages.find]
where = ["."]
include = ["agent_workflow*"]

[tool.setuptools.package-data]
agent_workflow = [
    "templates/*.yaml",
    "templates/*.yml",
    "templates/*.json",
    "config/*.yaml",
    "config/*.yml",
]
```

### 4.2 Installation Steps
```bash
# 1. One-click installation
pip install agent-workflow

# 2. Initialize global environment
agent-orch init --interactive

# 3. Configure integrations (optional)
agent-orch setup-discord --interactive
agent-orch setup-api --provider claude --interactive

# 4. Register existing projects
agent-orch register-project ./my-project --validate

# 5. Start orchestration
agent-orch start --discord
```

### 4.3 First-Time Setup Wizard
```python
# Interactive setup flow
def first_time_setup():
    """
    1. Welcome message and system requirements check
    2. Create configuration directory
    3. Generate encryption keys
    4. Configure AI provider (with test)
    5. Configure Discord (optional, with test)
    6. Set up first project (optional)
    7. Launch orchestrator (optional)
    """
```

## 5. Migration Strategy

### 5.1 Backward Compatibility
- Support existing git-clone installations during transition period
- Provide migration utility: `agent-orch migrate-from-git <path>`
- Preserve existing project state files
- Import existing configurations automatically

### 5.2 Migration Command
```bash
# Migrate from git-clone installation
agent-orch migrate-from-git /path/to/cloned/repo [options]

Options:
  --preserve-config   Keep existing configuration files
  --import-projects   Auto-discover and register projects
  --backup-first      Create backup before migration
  --dry-run          Show what would be migrated without changes

Process:
  1. Detect existing installation type
  2. Backup current configuration
  3. Import global settings
  4. Register discovered projects
  5. Test migrated configuration
  6. Provide rollback instructions
```

### 5.3 Deployment Considerations
- **Cross-platform compatibility**: Windows, macOS, Linux
- **Python version support**: 3.8+
- **Virtual environment friendly**: Works in venv/conda
- **Docker support**: Official Docker images
- **CI/CD integration**: GitHub Actions, Jenkins plugins

## 6. Advanced Features

### 6.1 Plugin System Design
```python
# Plugin architecture for extensibility
class PluginManager:
    def __init__(self):
        self.plugins = {}
        
    def register_plugin(self, name: str, plugin_class: Type[BasePlugin]):
        """Register new plugin"""
        
    def load_plugins_from_directory(self, path: Path):
        """Auto-discover plugins"""
        
    def execute_plugin_hook(self, hook_name: str, *args, **kwargs):
        """Execute plugin hooks"""
```

### 6.2 Configuration Profiles
```yaml
# Support for different usage profiles
profiles:
  solo-engineer:
    default_mode: "blocking"
    max_concurrent_projects: 3
    approval_timeout: 300
    
  team-lead:
    default_mode: "partial"
    max_concurrent_projects: 10
    approval_timeout: 600
    delegation_enabled: true
    
  researcher:
    default_mode: "autonomous"
    max_concurrent_projects: 1
    detailed_logging: true
    experiment_tracking: true
```

### 6.3 Health Monitoring
```bash
# System health and diagnostics
agent-orch health [options]

Options:
  --check-all         Run comprehensive health check
  --fix-issues        Attempt to fix detected issues
  --export-report     Export health report

Health Checks:
  ✓ Configuration files valid
  ✓ Credentials accessible
  ✓ Discord bot connected
  ✓ AI provider reachable
  ✓ Project paths accessible
  ✗ Project 'webapp' has uncommitted changes
  ⚠ Rate limit approaching for AI provider
```

This comprehensive design provides the foundation for transforming agent-workflow into a professional, pip-installable package with sophisticated CLI management capabilities while maintaining all existing functionality and providing smooth migration paths for current users.