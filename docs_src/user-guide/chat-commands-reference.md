# 💬 Chat Commands Reference - Complete Command Guide

> **Comprehensive reference for all Discord-style chat interface commands with examples, parameters, and integration details**

This reference provides complete documentation for all commands available in the Discord-style chat interface, including syntax, parameters, examples, and how commands integrate with the visual dashboard.

!!! tip "Quick Command Discovery"
    Type `/help` in any chat channel for contextual command suggestions, or use `Ctrl/Cmd + K` to open the command palette for quick access.

## 🎯 Command Categories Overview

### Core Command Categories

=== "Project Management"

    **Epic & Story Management**:
    - `/epic` - Create and manage project epics
    - `/story` - Manage individual user stories  
    - `/backlog` - Backlog operations and prioritization
    - `/approve` - Approve generated content and proposals

=== "Sprint Management"

    **Sprint Lifecycle**:
    - `/sprint` - Complete sprint management
    - `/board` - Sprint board operations
    - `/velocity` - Team velocity tracking
    - `/burndown` - Sprint burndown analysis

=== "Agent Interaction"

    **AI Agent Commands**:
    - `@agent` - Direct agent communication
    - `/agents` - Agent status and management
    - `/assign` - Task assignment to agents
    - `/interfaces` - Agent interface switching

=== "System Control"

    **Workflow & State**:
    - `/state` - State machine inspection
    - `/context` - Context management
    - `/status` - System status and health
    - `/logs` - System logs and debugging

=== "Configuration"

    **Settings & Setup**:
    - `/configure` - System configuration
    - `/theme` - Interface customization
    - `/notifications` - Notification settings
    - `/profile` - User profile management

=== "Information"

    **Help & Discovery**:
    - `/help` - Context-sensitive help
    - `/docs` - Documentation access
    - `/shortcuts` - Keyboard shortcuts
    - `/search` - Message and command search

## 📋 Detailed Command Reference

### Project Management Commands

#### `/epic` - Epic Management
Create, manage, and track high-level project initiatives.

**Syntax:**
```
/epic create "<description>" [--priority high|medium|low] [--tags tag1,tag2]
/epic list [--status active|completed|planned] [--project project_id]
/epic show <epic_id>
/epic update <epic_id> --field <value>
/epic close <epic_id> [--reason "reason"]
```

**Examples:**
```bash
# Create a new epic
/epic create "User authentication system with OAuth2 support" --priority high --tags auth,security

# List all active epics
/epic list --status active

# Show detailed epic information
/epic show AUTH-001

# Update epic priority
/epic update AUTH-001 --priority critical

# Close completed epic
/epic close AUTH-001 --reason "All stories completed and deployed"
```

**Dashboard Integration:**
- Creates new epic card in projects panel
- Updates project roadmap visualization
- Shows epic progress in real-time
- Links to related sprint boards

**Interactive Response:**
```
🤖 System                                          [3:45 PM]
✅ Epic "User Authentication System" created!

📋 Epic Details:
┌─ Epic: AUTH-001 ─────────────────────────────────────────┐
│ 🎯 Priority: HIGH                                        │
│ 🏷️ Tags: auth, security                                  │
│ 📊 Stories: 0 created, generating...                     │
│ ⏱️ Estimated Duration: Analyzing...                      │
└──────────────────────────────────────────────────────────┘

🔄 Generating user stories...
✅ 4 stories generated and ready for review

[📋 View Stories] [✅ Approve All] [✏️ Edit] [📊 Dashboard]
```

#### `/story` - Story Management
Manage individual user stories within epics.

**Syntax:**
```
/story create "<title>" "<description>" [--epic epic_id] [--points 1-13]
/story list [--epic epic_id] [--status todo|progress|testing|done]
/story show <story_id>
/story move <story_id> --status <new_status>
/story estimate <story_id> --points <points>
```

**Examples:**
```bash
# Create a new story
/story create "Login form UI component" "Create responsive login form with validation" --epic AUTH-001 --points 3

# List stories for an epic
/story list --epic AUTH-001

# Move story to in-progress
/story move AUTH-002 --status progress

# Update story estimate
/story estimate AUTH-003 --points 5
```

**Dashboard Integration:**
- Updates sprint board in real-time
- Shows story progress in kanban view
- Updates burn-down charts
- Links to agent assignments

#### `/backlog` - Backlog Management
Manage and prioritize the product backlog.

**Syntax:**
```
/backlog view [--project project_id] [--filter filter_criteria]
/backlog add "<title>" "<description>" [--priority high|medium|low]
/backlog prioritize <item_id> --position <number>
/backlog refine <item_id> [--points points] [--tags tags]
```

**Examples:**
```bash
# View current backlog
/backlog view

# Add new backlog item
/backlog add "Mobile app notification system" "Push notifications for mobile users" --priority medium

# Move item to top priority
/backlog prioritize BACK-005 --position 1

# Refine backlog item
/backlog refine BACK-005 --points 8 --tags mobile,notifications
```

#### `/approve` - Approval Management
Approve AI-generated content and task proposals.

**Syntax:**
```
/approve <item_id> [item_id...] [--comment "approval comment"]
/approve all [--filter filter_criteria]
/approve reject <item_id> --reason "rejection reason"
/approve pending [--user user_id]
```

**Examples:**
```bash
# Approve specific items
/approve AUTH-001 AUTH-002 --comment "Looks good, proceed with implementation"

# Approve all pending items
/approve all

# Reject an item
/approve reject AUTH-003 --reason "Needs more detailed acceptance criteria"

# View pending approvals
/approve pending
```

### Sprint Management Commands

#### `/sprint` - Sprint Operations
Complete sprint lifecycle management.

**Syntax:**
```
/sprint create "<name>" --duration <days> [--start-date YYYY-MM-DD]
/sprint start [sprint_id]
/sprint status [sprint_id]
/sprint pause [sprint_id] --reason "reason"
/sprint resume [sprint_id]
/sprint complete [sprint_id] [--retrospective]
```

**Examples:**
```bash
# Create new sprint
/sprint create "Authentication Sprint 1" --duration 14 --start-date 2024-02-01

# Start current sprint
/sprint start

# Check sprint status
/sprint status

# Pause sprint with reason
/sprint pause --reason "Waiting for API design approval"

# Complete sprint with retrospective
/sprint complete --retrospective
```

**Dashboard Integration:**
- Updates sprint board status
- Shows real-time progress bars
- Updates burndown charts
- Triggers agent notifications

**Interactive Response:**
```
🤖 System                                          [4:10 PM]
🚀 Sprint "Authentication Sprint 1" started!

📊 Sprint Overview:
┌─ Sprint Status ──────────────────────────────────────────┐
│ 📅 Duration: 14 days (Feb 1 - Feb 14, 2024)            │
│ 📋 Stories: 6 total, 0 completed                        │
│ 🎯 Story Points: 24 total, 0 completed                  │
│ 👥 Team Velocity: 22 points/sprint (avg)                │
│ 📈 Confidence: 92% (based on historical data)          │
└──────────────────────────────────────────────────────────┘

🤖 Agent assignments:
• CodeAgent: 4 implementation stories
• QAAgent: 2 testing stories  
• DesignAgent: 1 review story

[📊 View Sprint Board] [📈 Burndown Chart] [🎯 Daily Standup]
```

#### `/board` - Sprint Board Operations
Interact with the kanban-style sprint board.

**Syntax:**
```
/board view [sprint_id]
/board move <story_id> --column <todo|progress|testing|done>
/board filter --assignee <agent_id> [--priority high|medium|low]
/board export [--format csv|json] [--sprint sprint_id]
```

**Examples:**
```bash
# View current sprint board
/board view

# Move story to different column
/board move AUTH-004 --column progress

# Filter board by assignee
/board filter --assignee CodeAgent

# Export board data
/board export --format csv
```

### Agent Interaction Commands

#### `@agent` - Direct Agent Communication
Mention and communicate directly with AI agents.

**Syntax:**
```
@<agent_name> <message or task>
@<agent_name> status
@<agent_name> pause
@<agent_name> resume
```

**Examples:**
```bash
# Assign task to specific agent
@CodeAgent implement the user login form with validation and error handling

# Check agent status
@CodeAgent status

# Request agent to review code
@DesignAgent please review the authentication flow architecture

# Pause agent work
@QAAgent pause current task
```

**Interactive Response:**
```
👤 You                                            [2:30 PM]
@CodeAgent implement user login form with validation

🤖 CodeAgent                                      [2:30 PM]
✅ Task received! Starting implementation...

📋 Implementation Plan:
1. Create LoginForm.tsx component
2. Add form validation logic  
3. Implement error handling
4. Add unit tests
5. Update routing

⏱️ Estimated completion: 45 minutes
🔄 Status: IN_PROGRESS

I'll keep you updated on progress. You can check status anytime with `@CodeAgent status`

[📊 View Progress] [⏸️ Pause Task] [🔧 Modify Requirements]
```

#### `/agents` - Agent Management
Monitor and manage AI agent status and performance.

**Syntax:**
```
/agents status [--detailed]
/agents performance [--timeframe 1h|24h|7d]
/agents assign <task_id> --agent <agent_name>
/agents unassign <task_id>
/agents restart <agent_name>
```

**Examples:**
```bash
# View all agent status
/agents status --detailed

# Check agent performance metrics
/agents performance --timeframe 24h

# Assign task to specific agent
/agents assign AUTH-005 --agent QAAgent

# Restart problematic agent
/agents restart DataAgent
```

#### `/interfaces` - Interface Management
Switch between different AI backend interfaces.

**Syntax:**
```
/interfaces list
/interfaces switch <interface_name>
/interfaces test [interface_name]
/interfaces performance
/interfaces configure <interface_name> [--settings]
```

**Examples:**
```bash
# List available interfaces
/interfaces list

# Switch to different interface
/interfaces switch anthropic-api

# Test interface connection
/interfaces test claude-code

# View interface performance
/interfaces performance
```

**Dashboard Integration:**
- Updates interface status indicators
- Shows real-time performance metrics
- Displays connection quality indicators
- Triggers interface health checks

### System Control Commands

#### `/state` - State Machine Operations
Inspect and interact with the workflow state machine.

**Syntax:**
```
/state current
/state diagram [--interactive]
/state history [--limit 10]
/state transition <new_state> [--force]
/state validate
```

**Examples:**
```bash
# View current state
/state current

# Show interactive state diagram
/state diagram --interactive

# View state transition history
/state history --limit 5

# Force state transition (admin only)
/state transition SPRINT_ACTIVE --force
```

**Interactive Response:**
```
🤖 System                                          [3:20 PM]
📊 Current System State: SPRINT_ACTIVE

🗺️ State Machine Visualization:
```
[Interactive state diagram would appear here]
```

📋 Current State Details:
• State: SPRINT_ACTIVE
• Duration: 2 days, 14 hours  
• Valid Transitions: SPRINT_PAUSED, SPRINT_REVIEW
• Active Agents: 3 of 4
• Pending Approvals: 2

⚠️ State Validation: ✅ All constraints satisfied

[🔄 View Transitions] [📊 State History] [🎯 Next Actions]
```

#### `/context` - Context Management
Manage AI context and processing modes.

**Syntax:**
```
/context status
/context mode <auto|fancy|simple>
/context refresh [--project project_id]
/context files [--pattern "*.py"]
/context clear [--confirm]
```

**Examples:**
```bash
# Check context status
/context status

# Switch to simple mode for faster processing
/context mode simple

# Refresh project context
/context refresh --project my-webapp

# View context files
/context files --pattern "*.ts"
```

#### `/status` - System Status
Check system health and performance.

**Syntax:**
```
/status overview
/status agents
/status performance
/status connections
/status errors [--recent]
```

**Examples:**
```bash
# System overview
/status overview

# Detailed agent status
/status agents

# Performance metrics
/status performance

# Recent errors
/status errors --recent
```

### Configuration Commands

#### `/configure` - System Configuration
Configure system settings and preferences.

**Syntax:**
```
/configure show [--category category_name]
/configure set <setting_name> <value>
/configure reset <setting_name>
/configure export [--format json|yaml]
/configure import <config_data>
```

**Examples:**
```bash
# Show all configuration
/configure show

# Set notification preference
/configure set notifications.sound true

# Reset to default
/configure reset theme.dark_mode

# Export configuration
/configure export --format json
```

#### `/theme` - Interface Customization
Customize the chat interface appearance.

**Syntax:**
```
/theme list
/theme set <theme_name>
/theme customize --accent <color> [--density compact|comfortable|spacious]
/theme reset
```

**Examples:**
```bash
# List available themes
/theme list

# Switch to dark theme
/theme set dark

# Customize with accent color
/theme customize --accent blue --density comfortable
```

### Information & Help Commands

#### `/help` - Context-Sensitive Help
Get help with commands and features.

**Syntax:**
```
/help [command_name]
/help search <query>
/help category <category>
/help shortcuts
```

**Examples:**
```bash
# General help
/help

# Help for specific command
/help sprint

# Search help topics
/help search "agent management"

# View keyboard shortcuts
/help shortcuts
```

#### `/search` - Message and Command Search
Search through chat history and commands.

**Syntax:**
```
/search "<query>" [--timeframe 1d|1w|1m] [--user user_name] [--channel channel_name]
/search commands <partial_command>
/search history [--user user_name] [--limit 10]
```

**Examples:**
```bash
# Search messages
/search "authentication" --timeframe 1w

# Search commands
/search commands "sprint"

# View command history
/search history --limit 5
```

## 🎹 Keyboard Shortcuts Integration

Many commands can be triggered with keyboard shortcuts:

| Shortcut | Command Equivalent | Description |
|----------|-------------------|-------------|
| `Ctrl/Cmd + K` | `/help` | Quick command palette |
| `Ctrl/Cmd + /` | - | Focus chat input |
| `Ctrl/Cmd + D` | `/dashboard` | Switch to dashboard |
| `Ctrl/Cmd + S` | `/state current` | View current state |
| `Ctrl/Cmd + A` | `/agents status` | Agent status overview |
| `↑/↓` | `/search history` | Navigate command history |

## 🔄 Command Auto-Completion

The chat interface provides intelligent auto-completion:

**Command Discovery:**
```
Type: /spr
Suggestions:
├─ /sprint start    - Start current sprint
├─ /sprint status   - View sprint progress  
├─ /sprint pause    - Pause current sprint
└─ /sprint complete - Complete sprint
```

**Parameter Completion:**
```
Type: /story create "
Auto-suggestions based on:
├─ Current epic context
├─ Similar existing stories
├─ Project conventions
└─ Template patterns
```

## 📊 Dashboard Integration Summary

Commands automatically trigger dashboard updates:

**Real-Time Updates:**
- Project cards refresh on epic/story changes
- Sprint board updates on status changes  
- Agent status indicators update on assignments
- Performance metrics update on system commands
- State visualizations update on transitions

**Visual Feedback:**
- Success animations for completed commands
- Progress indicators for long-running operations
- Error highlights for failed commands
- Notification badges for pending actions

## 🚀 Quick Command Reference Card

**Most Used Commands:**
```bash
# Project Flow
/epic create "feature description"    # Create new epic
/approve all                         # Approve generated stories  
/sprint start                        # Begin sprint
/board view                          # Check progress

# Agent Communication  
@CodeAgent implement feature X       # Direct task assignment
/agents status                       # Check agent workload
/interfaces switch claude-code       # Change AI backend

# System Management
/state current                       # Check workflow state
/status overview                     # System health check
/context mode simple                 # Fast context processing
/help shortcuts                      # View all shortcuts
```

**Emergency Commands:**
```bash
/agents restart <agent>              # Restart hung agent
/sprint pause --reason "reason"      # Emergency sprint pause
/state transition IDLE --force       # Force state reset (admin)
/logs errors --recent                # Quick error diagnosis
```

---

This comprehensive command reference provides everything needed to master the Discord-style chat interface. Commands are designed to be intuitive, powerful, and seamlessly integrated with the visual dashboard for the ultimate AI development experience. 💬✨