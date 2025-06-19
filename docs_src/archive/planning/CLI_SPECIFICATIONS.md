# CLI Command Specifications

## Overview
Detailed specifications for all CLI commands in the agent-workflow package, including usage patterns, error handling, and interactive flows.

## Command Categories

### 1. Initialization Commands

#### `agent-orch init`
**Purpose**: Initialize global orchestrator environment

**Usage**:
```bash
agent-orch init [OPTIONS]
```

**Options**:
- `--config-dir PATH`: Custom configuration directory (default: ~/.agent-workflow)
- `--force`: Overwrite existing configuration
- `--interactive`: Run interactive setup wizard  
- `--minimal`: Create minimal configuration without integrations
- `--profile PROFILE`: Use predefined profile (solo-engineer|team-lead|researcher)
- `--dry-run`: Show what would be created without making changes

**Interactive Flow**:
```
Welcome to Agent-Workflow Setup!

1. Configuration Directory
   Default: /home/user/.agent-workflow
   Custom path? [Enter for default]: 

2. User Profile Selection
   [1] Solo Engineer (blocking mode, focused workflow)
   [2] Team Lead (partial mode, multi-project management)  
   [3] Researcher (autonomous mode, experiment tracking)
   [4] Custom (manual configuration)
   
   Select profile [1]: 

3. Create Sample Project?
   Would you like to register a sample project? [y/N]: 

4. Setup Integrations Now?
   Configure Discord bot? [y/N]: 
   Configure AI provider? [y/N]: 

Setup complete! Next steps:
  - Configure integrations: agent-orch configure
  - Register projects: agent-orch register-project <path>
  - Start orchestration: agent-orch start
```

**Output Files Created**:
```
~/.agent-workflow/
├── config.yaml              # Global configuration
├── credentials.key           # Encryption key
├── projects/
│   └── registry.yaml        # Project registry
├── logs/                    # Log directory
└── templates/               # Configuration templates
```

**Error Scenarios**:
- Existing configuration without `--force`: "Configuration already exists. Use --force to overwrite."
- Permission denied: "Cannot create directory. Check permissions for: ~/.agent-workflow"
- Invalid profile: "Unknown profile 'invalid'. Available: solo-engineer, team-lead, researcher"

---

### 2. Project Management Commands

#### `agent-orch register-project`
**Purpose**: Register existing project for orchestration

**Usage**:
```bash
agent-orch register-project <PATH> [NAME] [OPTIONS]
```

**Arguments**:
- `PATH`: Path to project directory (required)
- `NAME`: Project name (optional, defaults to directory name)

**Options**:
- `--mode {blocking,partial,autonomous}`: Orchestration mode (default: from profile)
- `--framework {general,web,api,ml,mobile,desktop}`: Project type (default: general)
- `--validate`: Validate project structure before registration
- `--create-channel`: Auto-create Discord channel
- `--language LANG`: Primary programming language
- `--repository URL`: Git repository URL
- `--description TEXT`: Project description
- `--force`: Overwrite existing registration

**Interactive Validation Flow**:
```bash
$ agent-orch register-project ./webapp --validate

Validating project: webapp
├── Path exists: ✓ /home/user/webapp
├── Git repository: ✓ Clean working directory
├── Project structure: ✓ Standard web application
├── Dependencies: ✓ requirements.txt found
├── Tests: ⚠ No test directory found
└── Documentation: ⚠ No README.md found

Warnings found. Continue registration? [y/N]: y

Project 'webapp' registered successfully!
├── Mode: partial (inherited from profile)
├── Framework: web (auto-detected)
├── Discord channel: #orch-webapp (will be created)
└── Configuration: ~/.agent-workflow/projects/webapp.yaml

Next steps:
  - Start orchestration: agent-orch start webapp
  - View project status: agent-orch status --project webapp
```

**Auto-Detection Logic**:
- **Web**: package.json, requirements.txt with flask/django, Gemfile with rails
- **API**: presence of API frameworks (fastapi, express, spring-boot)
- **ML**: requirements.txt with tensorflow/pytorch, .ipynb files
- **Mobile**: android/, ios/, flutter/, react-native/
- **Desktop**: electron/, .pro files, setup.py with tkinter

**Error Scenarios**:
- Path doesn't exist: "Project path does not exist: /invalid/path"
- Already registered: "Project 'webapp' already registered. Use --force to overwrite."
- Invalid git repo: "Path is not a git repository. Initialize with: git init"
- Permission denied: "Cannot access project directory. Check permissions."

#### `agent-orch projects`
**Purpose**: Manage registered projects

**Usage**:
```bash
agent-orch projects <SUBCOMMAND> [OPTIONS]
```

**Subcommands**:

##### `agent-orch projects list`
```bash
Registered Projects:

webapp                    Status: active    Mode: partial
├── Path: /home/user/webapp
├── Framework: web (Python/Flask)
├── Discord: #orch-webapp
├── Last active: 2 minutes ago
└── Repository: https://github.com/user/webapp

api-project              Status: idle      Mode: blocking  
├── Path: /home/user/api
├── Framework: api (Python/FastAPI)
├── Discord: #orch-api-project
├── Last active: 1 hour ago
└── Repository: https://github.com/user/api

Summary: 2 projects registered, 1 active, 0 errors
```

##### `agent-orch projects remove <NAME>`
```bash
$ agent-orch projects remove webapp

Remove project 'webapp'?
├── Path: /home/user/webapp
├── Discord channel: #orch-webapp (will be archived)
├── Configuration files: Will be deleted
└── Project files: Will remain unchanged

Continue? [y/N]: y
Project 'webapp' removed successfully.
```

##### `agent-orch projects validate <NAME>`
```bash
$ agent-orch projects validate webapp

Validating project: webapp
├── Registration: ✓ Valid configuration
├── Path access: ✓ Directory accessible  
├── Git status: ✓ Clean working directory
├── Dependencies: ✓ All requirements met
├── Discord channel: ✓ #orch-webapp exists
├── Permissions: ✓ Read/write access confirmed
└── State files: ✓ .orch-state/ directory valid

Project 'webapp' validation passed!
```

---

### 3. Configuration Commands

#### `agent-orch setup-discord`
**Purpose**: Configure Discord bot integration

**Usage**:
```bash
agent-orch setup-discord [OPTIONS]
```

**Options**:
- `--token TOKEN`: Discord bot token
- `--guild-id ID`: Discord server ID
- `--interactive`: Interactive setup with validation
- `--test-connection`: Test connection after setup
- `--create-channels`: Auto-create channels for registered projects
- `--channel-prefix PREFIX`: Channel naming prefix (default: "orch")

**Interactive Flow**:
```
Discord Bot Setup

1. Bot Token
   Enter your Discord bot token: [hidden input]
   Testing connection... ✓ Valid token

2. Server Selection
   Available servers:
   [1] My Development Server (ID: 1234567890)
   [2] Team Workspace (ID: 0987654321)
   
   Select server [1]: 1

3. Permissions Check
   ├── Send Messages: ✓ Granted
   ├── Manage Channels: ✓ Granted  
   ├── Embed Links: ✓ Granted
   ├── Add Reactions: ✓ Granted
   └── Use Slash Commands: ✓ Granted

4. Channel Configuration
   Channel prefix: orch
   Existing projects will get channels:
   ├── #orch-webapp (will be created)
   └── #orch-api-project (will be created)
   
   Create channels now? [y/N]: y

5. Test Message
   Sending test message to #orch-general... ✓ Success

Discord bot configured successfully!
Bot invite link: https://discord.com/oauth2/authorize?client_id=...
```

**Validation Checks**:
- Token format validation
- Bot permissions verification
- Server access confirmation
- Channel creation permissions
- Webhook capabilities

#### `agent-orch setup-api`
**Purpose**: Configure AI provider integration

**Usage**:
```bash
agent-orch setup-api [OPTIONS]
```

**Options**:
- `--provider {claude,openai,local}`: AI provider (default: claude)
- `--key KEY`: API key
- `--endpoint URL`: Custom API endpoint
- `--model MODEL`: Default model name
- `--interactive`: Interactive setup with validation
- `--test-connection`: Test API connection
- `--rate-limit LIMIT`: Requests per minute limit

**Interactive Flow**:
```
AI Provider Setup

1. Provider Selection
   [1] Anthropic Claude (Recommended)
   [2] OpenAI GPT
   [3] Local/Custom API
   
   Select provider [1]: 1

2. API Credentials
   Claude API key: [hidden input]
   Testing connection... ✓ Valid API key
   Available models:
   ├── claude-3.5-sonnet (Recommended)
   ├── claude-3-haiku
   └── claude-3-opus
   
   Default model [claude-3.5-sonnet]: 

3. Rate Limiting
   Your plan allows:
   ├── 50 requests per minute
   ├── 100,000 tokens per minute
   └── $20.00 remaining credit
   
   Set conservative limits? [Y/n]: y

4. Test Request
   Sending test request... ✓ Success
   Response time: 1.2s
   Tokens used: 15

AI provider configured successfully!
Monthly usage will be tracked and reported.
```

#### `agent-orch configure`
**Purpose**: Interactive configuration management

**Usage**:
```bash
agent-orch configure [OPTIONS]
```

**Options**:
- `--section {global,discord,api,projects,security}`: Configure specific section
- `--reset`: Reset configuration to defaults
- `--export FILE`: Export configuration to file
- `--import FILE`: Import configuration from file
- `--validate`: Validate current configuration
- `--wizard`: Run full configuration wizard

**Interactive Menu**:
```
Agent-Workflow Configuration

Current Status:
├── Global config: ✓ Valid
├── Discord bot: ✓ Connected (3 channels)
├── AI provider: ✓ Claude API (key valid)
├── Projects: 2 registered, 1 active
└── Security: ✓ All restrictions enabled

Configuration Options:
[1] Global Settings (logging, defaults, profiles)
[2] Discord Integration (bot token, channels, permissions)
[3] AI Provider (API keys, models, rate limits)
[4] Project Management (registration, validation, discovery)
[5] Security Settings (agent restrictions, approvals)
[6] Import/Export Configuration
[7] Reset to Defaults
[8] Validate All Settings

Select option [1-8]: 1

Global Settings:
├── User Profile: solo-engineer
├── Default Mode: blocking
├── Log Level: INFO
├── Data Retention: 30 days
├── Max Concurrent Projects: 3
└── Auto-discovery: disabled

Modify settings? [y/N]: 
```

---

### 4. Orchestration Control Commands

#### `agent-orch start`
**Purpose**: Start orchestration for projects

**Usage**:
```bash
agent-orch start [PROJECT] [OPTIONS]
```

**Arguments**:
- `PROJECT`: Specific project name (optional, starts all if omitted)

**Options**:
- `--mode {blocking,partial,autonomous}`: Override orchestration mode
- `--discord`: Start with Discord bot integration
- `--daemon`: Run as background daemon
- `--log-level {DEBUG,INFO,WARN,ERROR}`: Set logging level
- `--config FILE`: Use custom configuration file
- `--port PORT`: API port for status/control (default: 8080)
- `--no-browser`: Don't open status page in browser

**Output**:
```bash
$ agent-orch start webapp --discord

Starting Agent-Workflow Orchestrator...

├── Configuration loaded: ✓ ~/.agent-workflow/config.yaml
├── Discord bot starting: ✓ Connected to server
├── AI provider ready: ✓ Claude API (claude-3.5-sonnet)
└── Project registration: ✓ webapp loaded

Project: webapp
├── Path: /home/user/webapp
├── Mode: partial (overridden from blocking)
├── State: IDLE
├── Discord: #orch-webapp
└── Framework: web (Python/Flask)

Orchestrator started successfully!
├── Discord bot: Online in 'My Development Server'
├── Status page: http://localhost:8080
├── Logs: ~/.agent-workflow/logs/orchestrator.log
└── PID file: ~/.agent-workflow/orchestrator.pid

Available commands in Discord:
  /epic "description"     - Create new epic
  /backlog view          - View project backlog  
  /sprint plan           - Plan new sprint
  /state                 - Show current state
  
Press Ctrl+C to stop or run in daemon mode: agent-orch start --daemon
```

**Daemon Mode**:
```bash
$ agent-orch start --daemon

Orchestrator started as daemon
├── PID: 12345
├── Logs: ~/.agent-workflow/logs/orchestrator.log
├── Status: agent-orch status
└── Stop: agent-orch stop

Monitor with: tail -f ~/.agent-workflow/logs/orchestrator.log
```

#### `agent-orch status`
**Purpose**: Display orchestrator and project status

**Usage**:
```bash
agent-orch status [OPTIONS]
```

**Options**:
- `--project PROJECT`: Show status for specific project
- `--verbose`: Show detailed status information
- `--json`: Output in JSON format
- `--watch`: Continuously update status display
- `--health`: Include health check information

**Standard Output**:
```bash
Agent-Workflow Status

System Status:
├── Orchestrator: ✓ Running (PID: 12345)
├── Configuration: ✓ Valid
├── Discord Bot: ✓ Connected (3 active channels)
├── AI Provider: ✓ Claude API (quota: 75% remaining)
└── Health: ✓ All systems operational

Active Projects (1/3):
webapp                    Status: SPRINT_ACTIVE
├── Path: /home/user/webapp
├── Mode: partial
├── Discord: #orch-webapp (5 messages today)
├── Current Sprint: Sprint 3 (Day 2/14)
├── Stories: 3 active, 7 completed, 2 backlog
├── Last Activity: Agent committed feature/user-auth (2 min ago)
└── Next Review: Tomorrow 14:00

Idle Projects:
api-project              Status: BACKLOG_READY
├── Path: /home/user/api  
├── Mode: blocking
├── Discord: #orch-api-project
├── Backlog: 5 stories prioritized
└── Last Activity: 2 hours ago

Recent Activity:
├── 14:23 - webapp: CodeAgent completed story AW-123
├── 14:20 - webapp: Tests passed (96% coverage)
├── 14:15 - webapp: Human approved PR review
├── 13:45 - api-project: DesignAgent created architecture doc
└── 13:30 - System: Health check passed

Resource Usage:
├── API Calls: 1,247 today (limit: 50,000)
├── Disk Space: 2.3GB used (~/.agent-workflow/)
├── Memory: 156MB (orchestrator + agents)
└── Active Connections: Discord (1), GitHub (2)
```

**Watch Mode**:
```bash
$ agent-orch status --watch

[Updates every 5 seconds, press 'q' to quit]

Agent-Workflow Status (Last updated: 14:25:30)
...
[Status refreshes automatically]
```

#### `agent-orch stop`
**Purpose**: Stop orchestrator and cleanup

**Usage**:
```bash
agent-orch stop [OPTIONS]
```

**Options**:
- `--force`: Force stop without graceful shutdown
- `--save-state`: Save current state before stopping
- `--project PROJECT`: Stop specific project only

**Output**:
```bash
$ agent-orch stop

Stopping Agent-Workflow Orchestrator...

├── Saving project states: ✓ 2 projects saved
├── Completing active tasks: ✓ 1 task finished
├── Disconnecting Discord bot: ✓ Bot offline
├── Closing AI provider connections: ✓ Connections closed
├── Stopping background processes: ✓ All processes stopped
└── Cleanup complete: ✓ PID file removed

Orchestrator stopped successfully.
Final status saved to: ~/.agent-workflow/logs/shutdown-2024-01-15-14-25.log
```

---

### 5. Information Commands

#### `agent-orch version`
**Purpose**: Display version and system information

**Usage**:
```bash
agent-orch version [OPTIONS]
```

**Options**:
- `--check-updates`: Check for available updates
- `--verbose`: Show detailed system information

**Output**:
```bash
Agent-Workflow v1.2.3

Installation:
├── Package: pip install agent-workflow
├── Location: /usr/local/lib/python3.11/site-packages/agent_workflow
├── Configuration: ~/.agent-workflow
└── Python: 3.11.5 (/usr/bin/python3)

Components:
├── Core Orchestrator: v1.2.3
├── Discord Integration: v1.2.3
├── AI Agents: v1.2.3
├── Security System: v1.2.3
└── CLI Tools: v1.2.3

Dependencies:
├── discord.py: 2.3.2 ✓
├── PyGithub: 1.59.1 ✓
├── PyYAML: 6.0.1 ✓
├── cryptography: 41.0.7 ✓
└── click: 8.1.7 ✓

System:
├── OS: Linux 5.15.0 (Ubuntu 22.04)
├── Architecture: x86_64
├── Available Memory: 16.0 GB
└── Disk Space: 250 GB free

Latest version: v1.2.4 available
Upgrade with: pip install --upgrade agent-workflow
```

#### `agent-orch health`
**Purpose**: System health check and diagnostics

**Usage**:
```bash
agent-orch health [OPTIONS]
```

**Options**:
- `--check-all`: Run comprehensive health check
- `--fix-issues`: Attempt to fix detected issues
- `--export-report`: Export health report to file
- `--project PROJECT`: Check specific project health

**Output**:
```bash
Agent-Workflow Health Check

System Health:
├── Configuration Files: ✓ All valid
├── Directory Permissions: ✓ Read/write access confirmed
├── Credential Encryption: ✓ Keys accessible
├── Log Files: ✓ Rotating properly (2.1 MB used)
└── Disk Space: ✓ 250 GB available

Integration Health:
├── Discord Bot: ✓ Connected and responsive
│   ├── Guild Access: ✓ Permissions confirmed
│   ├── Channel Access: ✓ 3 channels accessible
│   └── API Rate Limit: ✓ Well within limits
├── AI Provider: ✓ Claude API operational
│   ├── Authentication: ✓ API key valid
│   ├── Model Access: ✓ claude-3.5-sonnet available
│   ├── Rate Limits: ✓ 25% of quota used
│   └── Response Time: ✓ Average 1.1s
└── Version Control: ✓ Git integration working

Project Health:
webapp                    Status: ✓ Healthy
├── Path Access: ✓ Directory accessible
├── Git Repository: ✓ Clean working directory
├── Dependencies: ✓ All requirements satisfied
├── State Files: ✓ .orch-state/ valid
├── Discord Integration: ✓ Channel responsive
└── Recent Activity: ✓ Active 2 minutes ago

api-project              Status: ⚠ Warnings
├── Path Access: ✓ Directory accessible
├── Git Repository: ⚠ 3 uncommitted changes detected
├── Dependencies: ✓ All requirements satisfied
├── State Files: ✓ .orch-state/ valid
├── Discord Integration: ✓ Channel responsive
└── Recent Activity: ⚠ Idle for 2 hours

Issues Detected:
├── api-project: Uncommitted changes may cause conflicts
└── Suggested action: Review and commit changes

Overall Health: ✓ Good (1 warning)
Run with --fix-issues to attempt automatic fixes.
```

---

### 6. UI Portal Integration Commands

#### `agent-orch ui`
**Purpose**: Launch holistic web portal for comprehensive project management

**Usage**:
```bash
agent-orch ui [OPTIONS]
```

**Options**:
- `--port PORT`: Custom port for UI server (default: 8080)
- `--host HOST`: Host to bind server (default: localhost) 
- `--mode {dashboard,chat,config,monitor}`: Launch specific UI mode
- `--project PROJECT`: Open specific project view directly
- `--headless`: Run background server without opening browser
- `--theme {light,dark,auto}`: Set UI theme (default: auto)
- `--config FILE`: Custom UI configuration file
- `--ssl-cert FILE`: SSL certificate for HTTPS (production)
- `--ssl-key FILE`: SSL private key for HTTPS (production)
- `--dev-mode`: Enable hot-reload and development features
- `--production`: Enable production optimizations
- `--api-port PORT`: Backend API port (default: 8000)
- `--websocket-port PORT`: WebSocket server port (default: 8001)
- `--no-auth`: Disable authentication (development only)
- `--session-timeout MINUTES`: Session timeout duration (default: 60)
- `--team-mode`: Enable multi-user collaboration features
- `--mobile-optimized`: Optimize for mobile device access
- `--qr-code`: Display QR code for mobile access
- `--browser BROWSER`: Specify browser to open (chrome, firefox, safari, edge)
- `--network-detect`: Auto-detect best network interface
- `--cors-origins ORIGINS`: Comma-separated list of allowed CORS origins

**Interactive Mode Output**:
```bash
$ agent-orch ui

Starting Agent-Workflow UI Portal...

├── Configuration loaded: ✓ ~/.agent-workflow/config.yaml
├── UI server starting: ✓ http://localhost:8080
├── API backend ready: ✓ http://localhost:8000
├── WebSocket server: ✓ ws://localhost:8001
├── Authentication: ✓ Session-based auth enabled
├── Network detection: ✓ localhost + LAN access available
└── Browser detection: ✓ Opening default browser (Chrome)

UI Portal Components:
├── Dashboard: Real-time project overview with analytics
├── Chat Interface: Discord-like command interface with history
├── Configuration: Visual setup and management panels
├── Monitoring: Advanced analytics, logs, and performance metrics
├── Multi-Project: Cross-project coordination and comparison
└── Team Collaboration: Multi-user features and shared workspaces

Portal started successfully!
├── Web Interface: http://localhost:8080
├── API Documentation: http://localhost:8000/docs
├── Health Check: http://localhost:8080/health
├── Session Storage: Redis (localhost:6379)
├── WebSocket Test: http://localhost:8000/ws-test
└── Log Output: ~/.agent-workflow/logs/ui-portal.log

Active Projects (3):
├── webapp (SPRINT_ACTIVE) - http://localhost:8080/project/webapp
├── api-project (BACKLOG_READY) - http://localhost:8080/project/api-project  
└── ml-model (IDLE) - http://localhost:8080/project/ml-model

Integration Status:
├── CLI-UI Sync: ✓ Real-time bidirectional synchronization
├── Discord Mirror: ✓ Commands mirrored between interfaces
├── Configuration Hot-reload: ✓ Changes apply without restart
├── Mobile Access: ✓ Responsive design enabled
└── Team Features: ✓ Multi-user collaboration ready

Access Methods:
├── Desktop: http://localhost:8080 (Primary interface)
├── Mobile: http://192.168.1.100:8080 (LAN access)
├── QR Code: agent-orch ui --qr-code (For quick mobile access)
├── Team Sharing: agent-orch ui-token generate --team-access
└── API Access: http://localhost:8000 (Programmatic interface)

Press Ctrl+C to stop or run in headless mode: agent-orch ui --headless
```

**Headless Mode Output**:
```bash
$ agent-orch ui --headless --port 8080

UI Portal started in headless mode
├── PID: 12345
├── Web Interface: http://localhost:8080
├── API Backend: http://localhost:8000
├── WebSocket: ws://localhost:8001
├── Logs: ~/.agent-workflow/logs/ui-portal.log
└── Process Management: ~/.agent-workflow/ui-portal.pid

Management Commands:
├── Status: agent-orch ui-status
├── Stop: agent-orch ui-stop
├── Restart: agent-orch ui-restart
└── Logs: tail -f ~/.agent-workflow/logs/ui-portal.log
```

#### `agent-orch ui-status`
**Purpose**: Check UI portal server status and health

**Usage**:
```bash
agent-orch ui-status [OPTIONS]
```

**Options**:
- `--json`: Output in JSON format
- `--verbose`: Show detailed component status
- `--health-check`: Run comprehensive health check
- `--performance`: Include performance metrics

**Output**:
```bash
UI Portal Status

Server Status:
├── UI Server: ✓ Running (PID: 12345, Port: 8080)
├── API Backend: ✓ Running (PID: 12346, Port: 8000)
├── WebSocket: ✓ Connected (15 active connections)
├── Session Store: ✓ Redis connected (localhost:6379)
└── Uptime: 2 hours, 34 minutes

Integration Status:
├── CLI-UI Sync: ✓ Real-time synchronization active
├── Discord Mirror: ✓ Commands mirrored between interfaces
├── Configuration Hot-reload: ✓ Changes apply without restart
├── Mobile Access: ✓ Responsive design enabled
└── Team Features: ✓ Multi-user collaboration ready

Active Sessions:
├── Total Users: 3 active sessions
├── Projects Viewed: webapp (2 users), api-project (1 user)
├── Commands Executed: 47 today
└── Average Response Time: 145ms

Health Metrics:
├── Error Rate: 0.2% (2 errors in 1000 requests)
├── Availability: 99.98% uptime
├── Performance: P95 response time 250ms
└── Security: ✓ No security alerts
```

#### `agent-orch ui-config`
**Purpose**: Configure UI portal settings and integrations

**Usage**:
```bash
agent-orch ui-config [SUBCOMMAND] [OPTIONS]
```

**Subcommands**:
- `setup`: Interactive UI configuration wizard
- `validate`: Validate current UI configuration
- `sync`: Synchronize CLI and UI configurations
- `export`: Export UI configuration to file
- `import`: Import UI configuration from file

#### Cross-Process Communication and Integration

**Configuration Sharing Mechanisms**:
- **Automatic Sync**: File system watchers detect configuration changes
- **Hot-reload**: UI portal reloads configuration without restart
- **Bidirectional Updates**: CLI changes reflect in UI, UI changes update CLI
- **Session Persistence**: Shared authentication and session state
- **Real-time Broadcasting**: WebSocket-based state synchronization

**Browser Integration and URL Handling**:
- **Cross-platform Detection**: Automatic browser detection and launching
- **Network Interface Analysis**: Intelligent network configuration
- **Mobile Optimization**: Responsive design and PWA support
- **QR Code Generation**: Quick mobile device access
- **Deep Linking**: Direct access to specific features and projects

**Security Token System**:
```bash
# Generate UI access tokens
$ agent-orch ui-token generate --expires 24h --permissions full

Generated UI access token:
├── Token: ui_abc123def456ghi789
├── Expires: 2024-01-16 14:30:00 UTC
├── Permissions: Full system access
├── Access URL: http://localhost:8080/auth?token=ui_abc123def456ghi789
└── Revoke: agent-orch ui-token revoke ui_abc123def456ghi789
```

---

### 7. Advanced Commands

#### `agent-orch migrate-from-git`
**Purpose**: Migrate from git-clone installation

**Usage**:
```bash
agent-orch migrate-from-git <SOURCE_PATH> [OPTIONS]
```

**Arguments**:
- `SOURCE_PATH`: Path to existing git-clone installation

**Options**:
- `--backup-first`: Create backup before migration
- `--import-projects`: Auto-discover and register projects
- `--preserve-config`: Keep existing configuration files
- `--dry-run`: Show migration plan without executing

**Migration Process**:
```bash
$ agent-orch migrate-from-git /home/user/old-agent-workflow --backup-first

Agent-Workflow Migration Tool

Source Analysis:
├── Installation Type: ✓ Git clone detected
├── Version: ✓ Compatible (v0.9.x)
├── Configuration: ✓ Found existing config files
├── Projects: ✓ 2 projects discovered
├── State Data: ✓ Project state files found
└── Dependencies: ✓ All requirements met

Migration Plan:
├── Backup current setup: ~/.agent-workflow.backup-2024-01-15
├── Import global configuration
├── Convert project configurations
├── Register discovered projects:
│   ├── webapp (/home/user/projects/webapp)
│   └── api-project (/home/user/projects/api)
├── Import credentials (encrypted)
├── Preserve state data
└── Update file paths and references

Proceed with migration? [y/N]: y

Executing Migration:
├── Creating backup: ✓ Backup saved
├── Installing new configuration: ✓ Complete
├── Converting project configs: ✓ 2 projects converted
├── Registering projects: ✓ 2 projects registered
├── Importing credentials: ✓ Encrypted and stored
├── Preserving state data: ✓ All states preserved
└── Validating migration: ✓ All checks passed

Migration completed successfully!

Next Steps:
├── Test configuration: agent-orch status
├── Start orchestrator: agent-orch start
├── Remove old installation: rm -rf /home/user/old-agent-workflow
└── Rollback if needed: agent-orch restore-backup ~/.agent-workflow.backup-2024-01-15

Old installation can be safely removed after testing.
```

#### `agent-orch plugin`
**Purpose**: Manage plugins and extensions

**Usage**:
```bash
agent-orch plugin <SUBCOMMAND> [OPTIONS]
```

**Subcommands**:
- `list`: List installed plugins
- `install <name>`: Install plugin from registry
- `remove <name>`: Remove installed plugin
- `enable <name>`: Enable disabled plugin
- `disable <name>`: Disable plugin
- `info <name>`: Show plugin information

**Example**:
```bash
$ agent-orch plugin list

Installed Plugins:

github-enterprise        Status: enabled   Version: 1.0.2
├── Description: GitHub Enterprise Server integration
├── Author: Agent-Workflow Team
├── Hooks: git_operations, pr_creation
└── Configuration: ~/.agent-workflow/plugins/github-enterprise.yaml

slack-notifications      Status: disabled  Version: 0.8.1
├── Description: Slack integration for notifications
├── Author: Community
├── Hooks: notification_send, alert_trigger
└── Configuration: ~/.agent-workflow/plugins/slack.yaml

Available Updates:
└── github-enterprise: v1.0.3 available

Install new plugins: agent-orch plugin install <name>
Plugin registry: https://plugins.agent-workflow.dev
```

This comprehensive CLI specification provides detailed command interfaces, interactive flows, error handling, and user experience patterns for the complete agent-workflow package system.