# Installation Flow Documentation

## Overview
Comprehensive documentation for the one-click pip installation process, setup workflows, and user onboarding experience for the agent-workflow package.

## 1. Installation Methods

### 1.1 PyPI Installation (Primary Method)
```bash
# Standard installation
pip install agent-workflow

# With optional dependencies
pip install agent-workflow[dev,docs]

# Development installation
pip install -e git+https://github.com/jmontp/agent-workflow.git#egg=agent-workflow

# Specific version
pip install agent-workflow==1.2.3
```

### 1.2 Alternative Installation Methods
```bash
# From GitHub releases
pip install https://github.com/jmontp/agent-workflow/releases/download/v1.2.3/agent_workflow-1.2.3-py3-none-any.whl

# Using pipx for isolated installation
pipx install agent-workflow

# Using conda
conda install -c conda-forge agent-workflow

# Docker installation
docker run -it agent-workflow/orchestrator:latest
```

## 2. Post-Installation Setup Flow

### 2.1 First-Time Setup Wizard
**Triggered by**: `agent-orch init --interactive` or first command execution

```
╔══════════════════════════════════════════════════════╗
║             Welcome to Agent-Workflow!              ║
║                                                      ║
║  AI Agent TDD-Scrum Orchestration Framework         ║
║  Version 1.2.3                                      ║
╚══════════════════════════════════════════════════════╝

Let's set up your orchestration environment.
This will take about 3-5 minutes.

┌─ Step 1/6: System Requirements ─────────────────────┐
│ Checking system compatibility...                    │
│                                                     │
│ ✓ Python 3.11.5 (compatible)                       │
│ ✓ Operating System: Linux (supported)              │
│ ✓ Available Memory: 8.2 GB (sufficient)            │
│ ✓ Disk Space: 50 GB free (sufficient)              │
│ ✓ Network Connectivity: Online                     │
│                                                     │
│ All requirements met! ✓                            │
└─────────────────────────────────────────────────────┘

┌─ Step 2/6: Configuration Directory ─────────────────┐
│ Where should we store your configuration?           │
│                                                     │
│ Default: /home/user/.agent-workflow                 │
│ Custom path? [Enter for default]: 
│                                                     │
│ Creating directory structure...                     │
│ ✓ Configuration directory created                   │
│ ✓ Logging directory created                         │
│ ✓ Project registry initialized                      │
│ ✓ Template files installed                          │
└─────────────────────────────────────────────────────┘

┌─ Step 3/6: User Profile Selection ──────────────────┐
│ Choose your workflow profile:                       │
│                                                     │
│ [1] Solo Engineer                                   │
│     • Human approval required for key decisions    │
│     • Focus on single projects                     │
│     • Conservative AI agent permissions            │
│                                                     │
│ [2] Team Lead                                       │
│     • Manage multiple projects simultaneously      │
│     • Partial automation with oversight            │
│     • Enhanced monitoring and reporting            │
│                                                     │
│ [3] Researcher                                      │
│     • Autonomous operation for experiments         │
│     • Extended context and analysis                │
│     • Advanced AI capabilities enabled             │
│                                                     │
│ [4] Custom (Advanced)                               │
│     • Manual configuration of all settings         │
│                                                     │
│ Select profile [1]: 1
│                                                     │
│ ✓ Solo Engineer profile applied                     │
└─────────────────────────────────────────────────────┘

┌─ Step 4/6: AI Provider Setup ───────────────────────┐
│ Configure your AI provider for agent capabilities.  │
│                                                     │
│ [1] Anthropic Claude (Recommended)                  │
│ [2] OpenAI GPT                                      │
│ [3] Skip for now                                    │
│                                                     │
│ Select provider [1]: 1
│                                                     │
│ Claude API Setup:                                   │
│ API Key: [●●●●●●●●●●●●●●●●●●●●●●●●●●●●●●●●●●●●●●●●] │
│                                                     │
│ Testing connection... ✓ Valid API key              │
│ Available models:                                   │
│ • claude-3.5-sonnet (Recommended) ✓                │
│ • claude-3-haiku                                    │
│ • claude-3-opus                                     │
│                                                     │
│ Your plan limits:                                   │
│ • 50 requests/minute                                │
│ • 100,000 tokens/minute                             │
│ • $23.45 remaining balance                          │
│                                                     │
│ ✓ Claude API configured successfully                │
└─────────────────────────────────────────────────────┘

┌─ Step 5/6: Discord Integration (Optional) ──────────┐
│ Enable Discord for Human-in-the-Loop commands?     │
│                                                     │
│ Benefits:                                           │
│ • Interactive command interface                     │
│ • Real-time notifications                           │
│ • Project-specific channels                         │
│ • Visual state diagrams                             │
│                                                     │
│ Configure Discord? [Y/n]: y
│                                                     │
│ Discord Bot Setup:                                  │
│ Bot Token: [●●●●●●●●●●●●●●●●●●●●●●●●●●●●●●●●●●●●●●●●] │
│                                                     │
│ Testing connection... ✓ Bot online                 │
│                                                     │
│ Available servers:                                  │
│ [1] My Development Server (5 members)               │
│ [2] Team Workspace (12 members)                     │
│                                                     │
│ Select server [1]: 1
│                                                     │
│ Checking permissions... ✓ All required permissions │
│ Creating command channels... ✓ #agent-workflow     │
│                                                     │
│ ✓ Discord integration configured                    │
└─────────────────────────────────────────────────────┘

┌─ Step 6/6: First Project (Optional) ────────────────┐
│ Would you like to register your first project?     │
│                                                     │
│ This will help you get started immediately.        │
│                                                     │
│ Register a project? [Y/n]: y
│                                                     │
│ Project Registration:                               │
│ Path: ./my-webapp                                   │
│ Name: my-webapp                                     │
│                                                     │
│ Analyzing project...                                │
│ ✓ Valid git repository                              │
│ ✓ Python web application detected (Flask)          │
│ ✓ Dependencies available                            │
│ ⚠ No tests directory found                          │
│ ⚠ Missing README.md                                 │
│                                                     │
│ Framework: web                                      │
│ Language: python                                    │
│ Mode: blocking (from profile)                       │
│                                                     │
│ Create Discord channel? [Y/n]: y                    │
│ ✓ #orch-my-webapp channel created                   │
│                                                     │
│ ✓ Project registered successfully                   │
└─────────────────────────────────────────────────────┘

╔══════════════════════════════════════════════════════╗
║                  Setup Complete! 🎉                  ║
╚══════════════════════════════════════════════════════╝

Your agent-workflow environment is ready!

Configuration Summary:
├── Profile: Solo Engineer
├── AI Provider: Claude (claude-3.5-sonnet)
├── Discord: Connected to "My Development Server"
├── Projects: 1 registered (my-webapp)
└── Config Location: /home/user/.agent-workflow

Next Steps:
┌─────────────────────────────────────────────────────┐
│ 1. Start the orchestrator:                          │
│    agent-orch start --discord                       │
│                                                     │
│ 2. View project status:                             │
│    agent-orch status                                │
│                                                     │
│ 3. Register more projects:                          │
│    agent-orch register-project <path>               │
│                                                     │
│ 4. Discord commands (in #orch-my-webapp):           │
│    /epic "Create user authentication system"        │
│    /backlog view                                    │
│    /sprint plan                                     │
└─────────────────────────────────────────────────────┘

Documentation: https://agent-workflow.readthedocs.io
Support: https://github.com/jmontp/agent-workflow/issues

Press Enter to continue...
```

### 2.2 Minimal Setup (Non-Interactive)
```bash
# Quick setup without prompts
agent-orch init --minimal

Creating minimal configuration...
├── Configuration directory: ~/.agent-workflow ✓
├── Basic configuration file: Created ✓
├── Project registry: Initialized ✓
└── Encryption keys: Generated ✓

Setup complete! Configure integrations:
• AI Provider: agent-orch setup-api
• Discord: agent-orch setup-discord
• Register projects: agent-orch register-project <path>
```

### 2.3 Profile-Based Quick Setup
```bash
# Setup with predefined profiles
agent-orch init --profile solo-engineer --quick

Solo Engineer profile selected.

Configuration applied:
├── Mode: blocking (human approval required)
├── Max projects: 3 concurrent
├── Security: High (agent restrictions enabled)
├── Logging: Standard level
└── Auto-discovery: Disabled

Configure your AI provider to continue:
agent-orch setup-api --interactive
```

## 3. Integration Setup Flows

### 3.1 AI Provider Configuration Flow

#### 3.1.1 Claude API Setup
```bash
$ agent-orch setup-api --provider claude --interactive

╔══════════════════════════════════════════════════════╗
║                Claude API Setup                      ║
╚══════════════════════════════════════════════════════╝

Step 1: API Key
─────────────────
Get your API key from: https://console.anthropic.com/

API Key: [Hidden input - paste your key]

Validating API key... ✓ Valid key detected

Step 2: Account Information
──────────────────────────
Retrieved account details:
├── Organization: Personal Account
├── Plan: Pro ($20/month)
├── Usage this month: $12.34 / $20.00
├── Rate limits: 50 req/min, 100k tokens/min
└── Available models: claude-3.5-sonnet, claude-3-haiku, claude-3-opus

Step 3: Model Selection  
──────────────────────
Recommended model for your profile: claude-3.5-sonnet

[1] claude-3.5-sonnet (Recommended)
    • Best balance of capability and cost
    • Excellent for code generation
    • 200k context window

[2] claude-3-haiku  
    • Fastest responses
    • Lower cost
    • Good for simple tasks

[3] claude-3-opus
    • Highest capability  
    • Premium cost
    • Best for complex reasoning

Select model [1]: 1

Step 4: Rate Limiting
────────────────────
Configure conservative limits to avoid overage?

Your limits: 50 req/min, 100k tokens/min
Suggested: 30 req/min, 75k tokens/min, $15/day max

Apply suggested limits? [Y/n]: y

Step 5: Test Configuration
─────────────────────────
Sending test request...

Request sent: "Hello, please respond with just 'API test successful'"
Response received: "API test successful"
Latency: 1.2 seconds
Tokens used: 12

✓ Claude API configured successfully!

Configuration saved to: ~/.agent-workflow/config.yaml
Credentials encrypted: ~/.agent-workflow/credentials.enc
```

#### 3.1.2 OpenAI Setup
```bash
$ agent-orch setup-api --provider openai --interactive

╔══════════════════════════════════════════════════════╗
║                 OpenAI API Setup                     ║
╚══════════════════════════════════════════════════════╝

Step 1: API Key
─────────────────
Get your API key from: https://platform.openai.com/api-keys

API Key: [sk-...hidden...]

Organization ID (optional): [Enter if you have one]

Validating credentials... ✓ Valid API key

Step 2: Account Information
──────────────────────────
Retrieved account details:
├── Organization: Personal
├── Plan: Pay-as-you-go  
├── Current balance: $23.45
├── Rate limits: 500 req/min, 150k TPM
└── Available models: gpt-4, gpt-4-turbo, gpt-3.5-turbo

Step 3: Model Selection
──────────────────────
Recommended model for agent workflows: gpt-4-turbo

[1] gpt-4-turbo (Recommended)
    • Latest GPT-4 with 128k context
    • Good for complex code tasks
    • $0.01/1k input tokens

[2] gpt-4
    • Original GPT-4 model
    • 8k context window  
    • $0.03/1k input tokens

[3] gpt-3.5-turbo
    • Fast and economical
    • Good for simple tasks
    • $0.001/1k input tokens

Select model [1]: 1

✓ OpenAI API configured successfully!
```

### 3.2 Discord Bot Setup Flow
```bash
$ agent-orch setup-discord --interactive

╔══════════════════════════════════════════════════════╗
║               Discord Bot Setup                       ║
╚══════════════════════════════════════════════════════╝

Step 1: Bot Creation
───────────────────
Need to create a Discord bot? 

[1] I already have a bot token
[2] Help me create a new bot
[3] Skip Discord setup

Select option [1]: 2

Creating Discord Bot:
┌─────────────────────────────────────────────────────┐
│ 1. Go to: https://discord.com/developers/applications │
│ 2. Click "New Application"                           │
│ 3. Enter name: "Agent Workflow Bot"                 │
│ 4. Go to "Bot" section                              │
│ 5. Click "Add Bot"                                  │
│ 6. Copy the bot token                               │
│ 7. Enable "Message Content Intent" (required)       │
└─────────────────────────────────────────────────────┘

Bot token: [Hidden input]

Testing bot token... ✓ Valid token

Step 2: Server Selection
───────────────────────
The bot needs to be added to a Discord server.

Bot invite URL: 
https://discord.com/oauth2/authorize?client_id=123456789&scope=bot+applications.commands&permissions=388160

Required permissions:
├── Send Messages ✓
├── Manage Channels ✓  
├── Embed Links ✓
├── Add Reactions ✓
├── Use Slash Commands ✓
└── Manage Messages ✓

Add bot to server and press Enter when ready...

Checking bot access...

Available servers:
[1] My Development Server (Bot added ✓)
[2] Team Workspace (No access)

Select server [1]: 1

✓ Server access confirmed

Step 3: Channel Configuration
────────────────────────────
Channel setup options:

Prefix for project channels: [orch] 
Category name: [Agent Workflow]

Create initial channels?
├── #agent-workflow (general commands)
├── #orch-status (system status)
└── Project channels (created automatically)

Create channels? [Y/n]: y

Creating channels...
├── #agent-workflow ✓ Created
├── #orch-status ✓ Created  
└── Category "Agent Workflow" ✓ Created

Step 4: Command Registration
──────────────────────────
Registering slash commands...

Commands to register:
├── /epic - Create project epics
├── /backlog - Manage project backlog
├── /sprint - Sprint management
├── /state - View project state
├── /approve - Approve pending tasks
├── /status - System status
└── /help - Command help

Registering commands... ✓ 7 commands registered

Step 5: Test Integration
───────────────────────
Sending test message to #agent-workflow...

Test message sent ✓
Bot response received ✓
Slash commands available ✓

✓ Discord integration configured successfully!

Your bot is now online in "My Development Server"
Test it with: /help in #agent-workflow
```

## 4. Project Registration Flows

### 4.1 Interactive Project Registration
```bash
$ agent-orch register-project ./my-webapp --validate --interactive

╔══════════════════════════════════════════════════════╗
║              Project Registration                     ║
╚══════════════════════════════════════════════════════╝

Analyzing project: ./my-webapp

Step 1: Path Validation
──────────────────────
├── Path exists: ✓ /home/user/my-webapp
├── Directory accessible: ✓ Read/write permissions
├── Git repository: ✓ Clean working directory
└── Parent directory: ✓ Valid location

Step 2: Project Analysis
───────────────────────
Detecting project characteristics...

├── Language Detection:
│   ├── Python files: 47 files ✓
│   ├── JavaScript files: 12 files
│   └── Primary language: Python ✓
│
├── Framework Detection:
│   ├── requirements.txt: Flask==2.3.0 found ✓
│   ├── app.py: Flask application detected ✓
│   ├── templates/: Template directory found ✓
│   └── Framework: Web (Flask) ✓
│
├── Project Structure:
│   ├── Source code: ✓ Well organized
│   ├── Tests: ⚠ tests/ directory missing  
│   ├── Documentation: ⚠ README.md missing
│   ├── Configuration: ✓ .env.example found
│   └── Dependencies: ✓ All requirements met

Step 3: Git Integration
──────────────────────
├── Repository URL: https://github.com/user/my-webapp ✓
├── Default branch: main ✓
├── Recent commits: 15 commits in last week ✓
├── Uncommitted changes: None ✓
└── Remote access: ✓ Push/pull available

Step 4: Configuration  
─────────────────────
Project settings:

Name: my-webapp
Framework: web
Language: python
Mode: blocking (from profile)

Override any settings? [y/N]: y

[1] Change project name
[2] Change orchestration mode  
[3] Change framework type
[4] Add description
[5] Continue with current settings

Select option [5]: 4

Description: E-commerce web application with Flask backend

Step 5: Discord Integration
──────────────────────────
Create Discord channel for this project?

Channel name: #orch-my-webapp
Category: Agent Workflow

Create channel? [Y/n]: y

Creating Discord channel...
├── Channel created: #orch-my-webapp ✓
├── Permissions configured ✓
├── Welcome message sent ✓
└── Slash commands enabled ✓

Step 6: Initial Setup
────────────────────
Setting up project orchestration...

├── Creating .orch-state/ directory ✓
├── Initializing project configuration ✓
├── Setting up state tracking ✓
├── Registering with global registry ✓
└── Enabling monitoring ✓

╔══════════════════════════════════════════════════════╗
║            Registration Complete! 🎉                 ║
╚══════════════════════════════════════════════════════╝

Project: my-webapp
├── Path: /home/user/my-webapp
├── Framework: web (Python/Flask)  
├── Mode: blocking
├── Discord: #orch-my-webapp
├── State: IDLE
└── Status: Ready for orchestration

Warnings to address:
├── Missing tests/ directory
│   └── Suggested: mkdir tests && touch tests/__init__.py
└── Missing README.md
    └── Suggested: Create project documentation

Next steps:
┌─────────────────────────────────────────────────────┐
│ 1. Start orchestration:                             │
│    agent-orch start my-webapp --discord             │
│                                                     │
│ 2. Create first epic (in Discord #orch-my-webapp):  │
│    /epic "Add user authentication system"           │
│                                                     │
│ 3. View project status:                             │
│    agent-orch status --project my-webapp            │
└─────────────────────────────────────────────────────┘
```

### 4.2 Batch Project Registration
```bash
$ agent-orch register-project ~/workspace --discover --batch

╔══════════════════════════════════════════════════════╗
║            Batch Project Discovery                    ║
╚══════════════════════════════════════════════════════╝

Scanning directory: /home/user/workspace

Found potential projects:
┌─────────────────────────────────────────────────────┐
│ [1] my-webapp                                       │
│     Path: ~/workspace/my-webapp                     │
│     Type: Web (Python/Flask)                       │
│     Git: ✓ Clean repository                        │
│                                                     │
│ [2] api-service                                     │  
│     Path: ~/workspace/api-service                   │
│     Type: API (Python/FastAPI)                     │
│     Git: ✓ Clean repository                        │
│                                                     │
│ [3] mobile-app                                      │
│     Path: ~/workspace/mobile-app                    │
│     Type: Mobile (React Native)                     │
│     Git: ⚠ Uncommitted changes                      │
│                                                     │
│ [4] data-analysis                                   │
│     Path: ~/workspace/data-analysis                 │
│     Type: Data Science (Jupyter)                   │
│     Git: ✓ Clean repository                        │
└─────────────────────────────────────────────────────┘

Select projects to register [1,2,4]: 1,2,4

Registering selected projects...

my-webapp:
├── Framework: web ✓
├── Mode: blocking ✓  
├── Discord channel: #orch-my-webapp ✓
└── Registration: ✓ Complete

api-service:
├── Framework: api ✓
├── Mode: blocking ✓
├── Discord channel: #orch-api-service ✓  
└── Registration: ✓ Complete

data-analysis:
├── Framework: ml ✓
├── Mode: blocking ✓
├── Discord channel: #orch-data-analysis ✓
└── Registration: ✓ Complete

✓ 3 projects registered successfully!

Skipped projects:
└── mobile-app (uncommitted changes - fix and register manually)

Summary:
├── Total discovered: 4 projects
├── Successfully registered: 3 projects
├── Skipped: 1 project  
└── Ready for orchestration: 3 projects

Start orchestration: agent-orch start --discord
```

## 5. Migration from Git Installation

### 5.1 Migration Flow
```bash
$ agent-orch migrate-from-git ~/old-agent-workflow --interactive

╔══════════════════════════════════════════════════════╗
║            Migration from Git Installation           ║
╚══════════════════════════════════════════════════════╝

Source: /home/user/old-agent-workflow

Step 1: Source Analysis
──────────────────────
Analyzing existing installation...

├── Installation type: ✓ Git clone detected
├── Version: ✓ v0.9.5 (compatible)
├── Configuration files: ✓ Found valid configs  
├── Project data: ✓ 2 projects with state data
├── Credentials: ✓ API keys present
└── Dependencies: ✓ All requirements compatible

Step 2: Backup Creation
──────────────────────
Create backup before migration?

Backup location: ~/.agent-workflow.backup-2024-01-15-143022

Create backup? [Y/n]: y

Creating backup...
├── Configuration files ✓
├── Project state data ✓  
├── Credentials (encrypted) ✓
├── Log files ✓
└── Backup complete ✓

Backup saved: ~/.agent-workflow.backup-2024-01-15-143022

Step 3: Configuration Migration
──────────────────────────────
Migrating configuration files...

Old config structure → New config structure:
├── orchestrator.yaml → config.yaml ✓
├── projects/ → projects/registry.yaml ✓
├── .env → credentials.enc (encrypted) ✓
├── discord-config.yaml → config.yaml [discord] ✓
└── agent-permissions.yaml → config.yaml [security] ✓

Converting configurations...
├── Global settings ✓
├── AI provider settings ✓
├── Discord configuration ✓
├── Security policies ✓
└── User preferences ✓

Step 4: Project Discovery
────────────────────────
Found projects in old installation:

my-webapp:
├── Path: /home/user/projects/my-webapp
├── State: BACKLOG_READY  
├── Last active: 2 hours ago
├── Discord: #webapp-dev
└── Migration: ✓ Ready

api-project:
├── Path: /home/user/projects/api-project  
├── State: SPRINT_ACTIVE
├── Last active: 15 minutes ago
├── Discord: #api-dev
└── Migration: ✓ Ready

Migrate project registrations? [Y/n]: y

Step 5: Credential Migration
───────────────────────────
Migrating stored credentials...

├── Claude API key ✓ Encrypted and migrated
├── Discord bot token ✓ Encrypted and migrated  
├── GitHub token ✓ Encrypted and migrated
└── All credentials secured ✓

Step 6: State Data Preservation
──────────────────────────────
Preserving project state data...

my-webapp:
├── .orch-state/status.json ✓ Preserved
├── .orch-state/backlog.json ✓ Preserved
├── .orch-state/sprints/ ✓ Preserved (3 sprints)
└── .orch-state/history.json ✓ Preserved

api-project:
├── .orch-state/status.json ✓ Preserved
├── .orch-state/backlog.json ✓ Preserved
├── .orch-state/sprints/ ✓ Preserved (5 sprints)
└── .orch-state/history.json ✓ Preserved

Step 7: Final Validation
───────────────────────
Validating migrated installation...

├── Configuration syntax ✓ Valid
├── Credential access ✓ Working
├── Project registrations ✓ Valid
├── Discord connectivity ✓ Connected
├── AI provider ✓ API accessible
└── State consistency ✓ All data intact

╔══════════════════════════════════════════════════════╗
║              Migration Complete! 🎉                  ║
╚══════════════════════════════════════════════════════╝

Migration Summary:
├── Configuration: ✓ Successfully migrated
├── Projects: ✓ 2 projects registered  
├── Credentials: ✓ All credentials secured
├── State data: ✓ All history preserved
├── Integrations: ✓ Discord and AI provider working
└── Backup: ✓ Created at ~/.agent-workflow.backup-...

Your installation has been successfully migrated!

Next steps:
┌─────────────────────────────────────────────────────┐
│ 1. Test the installation:                           │
│    agent-orch status                                │
│                                                     │
│ 2. Start orchestration:                             │
│    agent-orch start --discord                       │
│                                                     │
│ 3. Remove old installation (after testing):        │
│    rm -rf ~/old-agent-workflow                      │
│                                                     │
│ 4. Rollback if needed:                              │
│    agent-orch restore-backup ~/.agent-workflow.backup-... │
└─────────────────────────────────────────────────────┘

Old installation preserved until you're ready to remove it.
```

## 6. Error Handling and Recovery

### 6.1 Common Installation Issues
```bash
# Permission denied during pip install
$ pip install agent-workflow
ERROR: Could not install packages due to an OSError: [Errno 13] Permission denied

Solution:
$ pip install --user agent-workflow
# OR
$ python -m pip install --user agent-workflow

# Python version compatibility
$ pip install agent-workflow  
ERROR: agent-workflow requires Python '>=3.8' but found '3.7.12'

Solution:
Upgrade Python to 3.8+ or use pyenv:
$ pyenv install 3.11.5
$ pyenv global 3.11.5

# Missing system dependencies
$ agent-orch init
ERROR: libffi-dev not found

Solution (Ubuntu/Debian):
$ sudo apt-get install libffi-dev python3-dev

Solution (macOS):
$ brew install libffi

# Network connectivity issues
$ agent-orch setup-api --provider claude
ERROR: Could not connect to Claude API

Diagnostics:
$ agent-orch health --check-network
├── Internet connectivity: ✓ Online
├── DNS resolution: ✓ Working  
├── Claude API endpoint: ✗ Blocked
├── Suggested: Check firewall/proxy settings
└── Proxy configuration: agent-orch configure --section network
```

### 6.2 Recovery Procedures
```bash
# Reset configuration to defaults
$ agent-orch configure --reset
Warning: This will reset all configuration to defaults.
Backup current config? [Y/n]: y

Backup created: ~/.agent-workflow.backup-2024-01-15-143045
Resetting configuration...
├── Global settings ✓ Reset to defaults
├── Integration settings ✓ Cleared
├── Project registry ✓ Preserved
├── Credentials ✓ Preserved  
└── Logs ✓ Preserved

Configuration reset complete.
Run setup again: agent-orch configure --wizard

# Restore from backup
$ agent-orch restore-backup ~/.agent-workflow.backup-2024-01-15-143045
Restoring from backup...

Backup contents:
├── Configuration: config.yaml (12KB)
├── Credentials: credentials.enc (2KB)
├── Projects: registry.yaml (5KB)
├── Logs: 15 files (2.3MB)
└── Created: 2024-01-15 14:30:45

Restore all components? [Y/n]: y

├── Stopping orchestrator ✓
├── Backing up current state ✓
├── Restoring configuration ✓
├── Restoring credentials ✓
├── Restoring project registry ✓
├── Validating restored config ✓
└── Restoration complete ✓

Restart orchestrator: agent-orch start

# Repair corrupted installation
$ agent-orch repair --full-check
Agent-Workflow Repair Tool

Checking installation integrity...
├── Package files ✓ All files present
├── Configuration syntax ✗ Invalid YAML in config.yaml  
├── Credential encryption ✓ Keys accessible
├── Project registrations ✓ All valid
├── Directory permissions ✓ Read/write access
└── Dependencies ✓ All requirements met

Issues found: 1

Repair configuration file? [Y/n]: y
├── Backing up corrupted file ✓
├── Regenerating from defaults ✓  
├── Preserving user preferences ✓
├── Validating new configuration ✓
└── Configuration repaired ✓

All issues resolved!
```

This comprehensive installation flow documentation provides users with clear guidance through every aspect of setting up and configuring the agent-workflow package, from initial installation through advanced migration scenarios and error recovery.