# 🎛️ CLI Command Palette

> **Your interactive command center for the AI Agent TDD-Scrum workflow system**

<div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 20px; border-radius: 10px; color: white; margin: 20px 0;">
  <h2 style="margin: 0; color: white;">⚡ Command Palette Design</h2>
  <p style="margin: 10px 0 0 0;">Find, learn, and execute commands with progressive disclosure</p>
</div>

## 🔍 Command Search & Discovery

### Quick Search Box
```bash
# Type to search commands, descriptions, and examples
[🔍 Search commands...] ⌨️ agent-orch init  ↩️
```

**Popular searches:**
- `init` - Initialize environment
- `start discord` - Start with Discord bot
- `register project` - Add new project
- `status` - Check system status

---

## ⭐ Most Used Commands

<div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 15px; margin: 20px 0;">

### 🚀 **Quick Start**
```bash
agent-orch init --interactive
```
<details>
<summary>📖 Interactive setup wizard</summary>

Creates configuration, sets up AI provider, and guides through Discord setup.

**Copy & Paste Ready:**
```bash
# Full first-time setup
agent-orch init --interactive
agent-orch setup-api --interactive  
agent-orch setup-discord --interactive
```
</details>

### 🎯 **Start Working**
```bash
agent-orch start --discord
```
<details>
<summary>📖 Launch orchestration with Discord</summary>

Starts the orchestrator with Discord bot integration for HITL commands.

**Copy & Paste Ready:**
```bash
# Start with Discord integration
agent-orch start --discord

# Background daemon mode
agent-orch start --daemon --discord
```
</details>

### 📁 **Add Project**
```bash
agent-orch register-project .
```
<details>
<summary>📖 Register current directory</summary>

Adds current directory as a managed project with auto-detection.

**Copy & Paste Ready:**
```bash
# Register current directory
agent-orch register-project .

# Register with validation and Discord channel
agent-orch register-project . --validate --create-channel
```
</details>

### 📊 **Check Status**
```bash
agent-orch status --brief
```
<details>
<summary>📖 System health overview</summary>

Quick status check for orchestrator and all registered projects.

**Copy & Paste Ready:**
```bash
# Quick status
agent-orch status --brief

# Watch live updates
agent-orch status --watch
```
</details>

</div>

---

## 📋 Table of Contents

- [Command Palette Navigation](#command-palette-navigation)
- [Core Command Categories](#core-command-categories)
- [Discord Bot Commands](#discord-bot-commands)
- [Interactive Examples](#interactive-examples)
- [Shell Autocomplete](#shell-autocomplete)
- [Advanced Usage Patterns](#advanced-usage-patterns)
- [Troubleshooting Guide](#troubleshooting-guide)

## 🎛️ Command Palette Navigation

### Interactive Command Discovery
```bash
# Access command palette mode
agent-orch --help-interactive

# Search by category
agent-orch search "project management"

# Get command suggestions
agent-orch suggest setup
```

### Quick Command Launcher
<div style="background: #f8f9fa; padding: 15px; border-radius: 8px; border-left: 4px solid #007bff;">

**Type to filter commands:**
```
> setup
  ✅ setup-api        Configure AI provider integration
  ✅ setup-discord    Configure Discord bot integration
  
> project
  ✅ register-project Register project for orchestration
  ✅ projects list    Show all registered projects
  
> start
  ✅ start --discord  Start orchestration with Discord
  ✅ status --brief   Quick system status check
```
</div>

---

## 📚 Core Command Categories

### 🏗️ **Setup & Initialization**
<details>
<summary><strong>Essential first-time setup commands</strong></summary>

| Command | Purpose | Interactive |
|---------|---------|-------------|
| `init` | Initialize global environment | ✅ |
| `setup-api` | Configure AI provider | ✅ |
| `setup-discord` | Configure Discord bot | ✅ |
| `configure` | Manage all settings | ✅ |

**Quick Setup Flow:**
```bash
# Interactive guided setup (recommended)
agent-orch init --interactive
agent-orch setup-api --interactive
agent-orch setup-discord --interactive
```
</details>

### 📁 **Project Management**
<details>
<summary><strong>Manage projects and repositories</strong></summary>

| Command | Purpose | Auto-Detection |
|---------|---------|----------------|
| `register-project` | Add project to orchestration | ✅ Framework, Language, Git |
| `projects list` | Show all registered projects | - |
| `projects validate` | Check project configuration | ✅ |
| `projects remove` | Remove project registration | - |

**Common Patterns:**
```bash
# Register current directory with auto-detection
agent-orch register-project .

# Register with full configuration
agent-orch register-project ~/my-app \
  --framework web \
  --language javascript \
  --mode blocking \
  --create-channel
```
</details>

### 🎮 **Orchestration Control**
<details>
<summary><strong>Start, stop, and monitor orchestration</strong></summary>

| Command | Purpose | Background Mode |
|---------|---------|-----------------|
| `start` | Start orchestration | ✅ `--daemon` |
| `stop` | Stop orchestration | ✅ Graceful |
| `status` | System status check | ✅ `--watch` |
| `health` | Health diagnostics | ✅ Auto-fix |

**Power User Commands:**
```bash
# Start all projects with Discord integration
agent-orch start --discord --daemon

# Watch live status updates
agent-orch status --watch --verbose

# Health check with auto-fix
agent-orch health --check-all --fix-issues
```
</details>

### ⚙️ **Configuration Management**
<details>
<summary><strong>Advanced configuration and migration</strong></summary>

| Command | Purpose | Backup Support |
|---------|---------|----------------|
| `configure` | Interactive config management | ✅ |
| `migrate-from-git` | Migrate from git installation | ✅ |
| `version` | Version and update check | - |

**Configuration Workflows:**
```bash
# Full configuration wizard
agent-orch configure --wizard

# Export configuration backup
agent-orch configure --export config-backup.yaml

# Migration from git clone
agent-orch migrate-from-git ~/agent-workflow-git \
  --backup-first \
  --import-projects
```
</details>

### 🌐 **Web Interface Management**
<details>
<summary><strong>Web tool and interface management</strong></summary>

| Command | Purpose | Advanced Features |
|---------|---------|-------------------|
| `web` | Launch web interface | ✅ Multiple modes |
| `web --interface-manager` | Launch with interface panel | ✅ |
| `web --context-manager` | Launch with context controls | ✅ |
| `web --performance-mode` | Launch in performance mode | ✅ |

**Web Interface Workflows:**
```bash
# Launch full web interface
agent-orch web

# Launch with interface management panel
agent-orch web --interface-manager --port 8080

# Launch with context management controls
agent-orch web --context-manager --debug

# Developer mode with all features
agent-orch web --dev-mode --interface-manager --context-manager

# Team collaboration mode
agent-orch web --team-mode --network-detect --qr-code
```
</details>

---

## 🤖 Discord Bot Commands

### HITL Command Interface
The Discord bot provides the primary Human-In-The-Loop interface for workflow management.

**Available Discord Commands:**
```
/epic <description>              - Define high-level initiatives
/backlog view|add_story         - Manage product backlog  
/sprint plan|start|status       - Sprint lifecycle management
/approve [items]                - Approve pending tasks
/request_changes <description>  - Request modifications
/state                         - Interactive state visualization
/project register <path>        - Register new project
```

### Interactive Command Cards
<div style="background: #f0f4f8; padding: 20px; border-radius: 10px; margin: 15px 0;">

**🎯 Epic Definition**
```discord
/epic "Build user authentication system with OAuth integration"
```
<details>
<summary>📋 Creates new epic with persistent storage</summary>

- Automatically creates Epic ID
- Stores in project's `.orch-state/epics.json`
- Triggers backlog planning state transition
- Notifies team members

**Example Response:**
```
✅ Epic #EP001 created: "Build user authentication system with OAuth integration"
📍 Project state: IDLE → BACKLOG_READY
🎯 Next: Use /backlog add_story to break down into stories
```
</details>

**📋 Backlog Management**
```discord
/backlog add_story "Implement OAuth login flow" feature:EP001 priority:high
```
<details>
<summary>📋 Manages product and sprint backlogs</summary>

- Creates stories linked to epics
- Supports priority management
- Auto-generates story IDs
- Enables sprint planning

**Example Response:**
```
✅ Story #ST001 added to backlog
📝 "Implement OAuth login flow"
🏷️ Epic: EP001 | Priority: High
📊 Backlog: 5 stories ready for sprint planning
```
</details>

</div>

---

## 🎨 Interactive Examples

### Progressive Disclosure Interface

#### Beginner → Setup Wizard
```bash
# 🟢 BEGINNER LEVEL
agent-orch init --interactive

# Guided prompts:
? Choose your role: Solo Engineer / Team Lead / Researcher
? AI Provider: Claude (Anthropic) / OpenAI / Local Model  
? Discord Integration: Yes / No / Later
? Default orchestration mode: Blocking / Partial / Autonomous
```

#### Intermediate → Project Management  
```bash
# 🟡 INTERMEDIATE LEVEL  
agent-orch register-project ~/my-webapp \
  --framework web \
  --mode blocking \
  --validate \
  --create-channel

# Auto-detection results:
✅ Framework: React (detected from package.json)
✅ Language: TypeScript (detected from tsconfig.json)  
✅ Git: https://github.com/user/my-webapp (detected from remote)
✅ Discord: #orch-my-webapp channel created
```

#### Advanced → Multi-Project Orchestration
```bash
# 🔴 ADVANCED LEVEL
# Start multiple projects with different modes
agent-orch start \
  --discord \
  --daemon \
  --config multi-project.yaml \
  --log-level DEBUG \
  --port 9090

# Custom configuration:
projects:
  webapp: {mode: blocking, priority: high}
  api-server: {mode: partial, priority: medium}  
  ml-pipeline: {mode: autonomous, priority: low}
```

### Copy-Paste Command Collections

#### 🚀 **New Project Setup**
```bash
# Complete new project workflow
mkdir awesome-app && cd awesome-app
git init
echo "# Awesome App" > README.md
agent-orch register-project . --validate --create-channel
agent-orch start --discord
```

#### 📊 **Daily Status Check**
```bash
# Morning development routine
agent-orch status --brief
agent-orch health --check-all
agent-orch projects list --verbose
```

#### 🔧 **Troubleshooting Toolkit**
```bash
# Debug failing orchestration
agent-orch stop --save-state
agent-orch start --log-level DEBUG --no-browser
agent-orch health --check-all --export-report debug-report.json
```

---

## ⌨️ Shell Autocomplete & Snippets

### One-Command Setup
```bash
# Bash
echo 'eval "$(_AGENT_ORCH_COMPLETE=bash_source agent-orch)"' >> ~/.bashrc

# Zsh  
echo 'eval "$(_AGENT_ORCH_COMPLETE=zsh_source agent-orch)"' >> ~/.zshrc

# Fish
echo 'eval (env _AGENT_ORCH_COMPLETE=fish_source agent-orch)' >> ~/.config/fish/config.fish
```

### Smart Autocomplete Features
<div style="background: #f8f9fa; padding: 15px; border-radius: 8px; margin: 15px 0;">

**Tab Completion Examples:**
```bash
# Command completion
agent-orch <TAB>
# → configure  health  init  projects  register-project  setup-api  setup-discord  start  status  stop  version

# Option completion  
agent-orch start --<TAB>
# → --daemon  --discord  --log-level  --mode  --port

# Project name completion
agent-orch status --project <TAB>
# → webapp  api-server  ml-pipeline

# Path completion with validation
agent-orch register-project <TAB>
# → ./  ../  ~/projects/webapp/  (shows only valid directories)
```

**Smart Context Awareness:**
- Only shows available options for current state
- Validates paths and project names
- Suggests commonly used flag combinations
- Shows brief descriptions for complex commands
</div>

### Custom Shell Aliases
```bash
# Add to your shell profile (~/.bashrc, ~/.zshrc)
alias ao='agent-orch'                    # Short command
alias aos='agent-orch status --brief'    # Quick status
alias aol='agent-orch projects list'     # List projects  
alias aod='agent-orch start --discord'   # Start with Discord
alias aoh='agent-orch health --check-all' # Health check

# Power user aliases
alias ao-setup='agent-orch init --interactive && agent-orch setup-api --interactive'
alias ao-daily='agent-orch status --brief && agent-orch projects list --verbose'
alias ao-debug='agent-orch start --log-level DEBUG --no-browser'
```

---

## 🚀 Advanced Usage Patterns

### Command Chaining & Workflows
```bash
# Conditional execution
agent-orch health --check-all && agent-orch start --discord

# Sequential setup with error handling
agent-orch init --interactive || exit 1
agent-orch setup-api --interactive || exit 1  
agent-orch register-project . --validate || exit 1
agent-orch start --discord

# Background monitoring
agent-orch start --daemon --discord &
agent-orch status --watch &
```

### Configuration Management
```bash
# Environment-specific configs
agent-orch start --config ~/.agent-workflow/dev.yaml     # Development
agent-orch start --config ~/.agent-workflow/prod.yaml    # Production  
agent-orch start --config ~/.agent-workflow/test.yaml    # Testing

# Export and share configurations
agent-orch configure --export team-config.yaml
# Team members can import:
agent-orch configure --import team-config.yaml
```

### Multi-Project Orchestration Patterns
```bash
# Start specific project combinations
agent-orch start webapp api-server --mode partial
agent-orch start ml-pipeline --mode autonomous --daemon

# Project-specific health monitoring
for project in webapp api-server worker; do
  agent-orch status --project $project --json >> status-report.json
done

# Bulk project operations
agent-orch projects list --json | jq -r '.[].name' | \
  xargs -I {} agent-orch projects validate {}
```

---

## 🛠️ Troubleshooting Guide

### Quick Diagnostics
<div style="background: #fff3cd; padding: 15px; border-radius: 8px; border-left: 4px solid #ffc107; margin: 15px 0;">

**⚡ One-Liner Health Check**
```bash
agent-orch health --check-all --fix-issues --export-report health-$(date +%Y%m%d).json
```

**📊 System Status Dashboard**
```bash
# Comprehensive status in one command
agent-orch status --verbose --health --json | jq '{
  orchestrator: .orchestrator.status,
  projects: [.projects[] | {name: .name, state: .state, tasks: .active_tasks}],
  health: {
    api_connection: .health.api_connection,
    discord_connection: .health.discord_connection,
    disk_space: .health.disk_space
  }
}'
```
</div>

### Common Issues & Solutions

#### 🔴 **"Command not found: agent-orch"**
<details>
<summary>Click for solutions</summary>

```bash
# Check if installed
pip show agent-workflow

# Install/reinstall
pip install --user --upgrade agent-workflow

# Add to PATH (if needed)
export PATH="$HOME/.local/bin:$PATH"  # Linux/Mac
export PATH="$APPDATA/Python/Scripts:$PATH"  # Windows

# Use Python module directly as fallback
python -m agent_workflow.cli init
```
</details>

#### 🔴 **"Discord bot not responding"**
<details>
<summary>Click for solutions</summary>

```bash
# Test Discord configuration
agent-orch setup-discord --test-connection

# Verify bot permissions
agent-orch configure --section discord --validate

# Re-register slash commands
agent-orch start --discord --sync-commands

# Debug mode
DISCORD_BOT_DEBUG=1 agent-orch start --discord --log-level DEBUG
```
</details>

#### 🔴 **"API rate limit exceeded"**
<details>
<summary>Click for solutions</summary>

```bash
# Check current rate limits
agent-orch configure --section api

# Increase rate limit
agent-orch setup-api --rate-limit 100

# Switch API provider temporarily
agent-orch setup-api --provider openai --interactive

# Enable request queuing
agent-orch configure --section api --set request_queuing=true
```
</details>

#### 🔴 **"Project registration failed"**
<details>
<summary>Click for solutions</summary>

```bash
# Validate project structure first
agent-orch register-project . --validate --dry-run

# Force re-registration
agent-orch register-project . --force

# Manual configuration
agent-orch register-project . \
  --framework general \
  --language python \
  --mode blocking

# Debug registration process
agent-orch register-project . --verbose --validate
```
</details>

### Debug Mode Commands
```bash
# Global debug mode
AGENT_WORKFLOW_DEBUG=1 agent-orch <command>

# Component-specific debugging
ORCHESTRATOR_DEBUG=1 agent-orch start
DISCORD_BOT_DEBUG=1 agent-orch start --discord
API_CLIENT_DEBUG=1 agent-orch setup-api --test-connection

# Trace mode for detailed logging
AGENT_WORKFLOW_TRACE=1 agent-orch start --log-level DEBUG
```

---

## 📊 Command Reference Card

<div style="background: #f8f9fa; padding: 20px; border-radius: 10px; font-family: monospace; margin: 20px 0;">

```
┌────────────────────────────────────────────────────────────────────┐
│                    🎛️ AGENT-ORCH COMMAND PALETTE                  │
├────────────────────────────────────────────────────────────────────┤
│ 🚀 QUICK START                                                    │
│   agent-orch init --interactive           # Complete setup wizard │
│   agent-orch register-project .           # Add current project   │
│   agent-orch start --discord              # Launch with Discord   │
│                                                                    │
│ 📊 DAILY OPERATIONS                                               │
│   agent-orch status --brief               # Quick status check    │
│   agent-orch projects list --verbose      # Detailed project info │
│   agent-orch health --check-all           # System diagnostics    │
│                                                                    │
│ 🎮 ORCHESTRATION CONTROL                                          │
│   agent-orch start --daemon --discord     # Background service    │
│   agent-orch stop --save-state            # Graceful shutdown     │
│   agent-orch status --watch               # Live monitoring       │
│                                                                    │
│ ⚙️ CONFIGURATION                                                   │
│   agent-orch configure --wizard           # Full config wizard    │
│   agent-orch setup-api --interactive      # AI provider setup     │
│   agent-orch setup-discord --interactive  # Discord bot setup     │
│                                                                    │
│ 🤖 DISCORD COMMANDS (in Discord channels)                        │
│   /epic "description"                     # Define epic           │
│   /backlog add_story "story"              # Add user story        │
│   /sprint plan                            # Plan sprint           │
│   /approve                                # Approve pending items │
│   /state                                  # Interactive state UI  │
└────────────────────────────────────────────────────────────────────┘
```
</div>

---

<div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 25px; border-radius: 10px; color: white; text-align: center; margin: 30px 0;">
  <h2 style="margin: 0; color: white;">🎯 Master the Command Palette</h2>
  <p style="margin: 15px 0 0 0; font-size: 1.1em;">
    Start with <code style="background: rgba(255,255,255,0.2); padding: 3px 8px; border-radius: 4px; font-weight: bold;">agent-orch init --interactive</code>
  </p>
  <p style="margin: 10px 0 0 0; opacity: 0.9;">
    Progressive disclosure from beginner to power user workflows
  </p>
</div>
