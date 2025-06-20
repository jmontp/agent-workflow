# 🚀 Quick Start - Choose Your Adventure

```ascii
    ╔═══════════════════════════════════════════════════════════════╗
    ║   Welcome to AI Agent Workflow - Your AI Team Awaits! 🤖     ║
    ║   Choose your path and watch AI agents transform your code!   ║
    ╚═══════════════════════════════════════════════════════════════╝
```

## 🎯 Choose Your Path

<div align="center">

| 🏃 **Speed Run** | 🎓 **Guided Tour** | 🏗️ **Full Setup** |
|:---:|:---:|:---:|
| **2 minutes** | **10 minutes** | **20 minutes** |
| *Just the basics* | *Learn as you go* | *Production ready* |
| Mock AI agents | Real AI + Discord | Multi-project + CI/CD |
| Perfect for demos | Perfect for learning | Perfect for teams |
| **[Start Speed Run ⚡](#speed-run)** | **[Start Tour 🎓](#guided-tour)** | **[Start Setup 🏗️](#full-setup)** |

</div>

## 🏃 Speed Run (2 minutes) {#speed-run}

> **Goal**: Get AI agents working in 2 minutes flat - perfect for demos and first impressions!

### Step 1 of 3: One-Line Install ⚡

```bash
# Install and verify in one command
curl -fsSL https://raw.githubusercontent.com/jmontp/agent-workflow/main/install.sh | bash
```

**Step 1 of 3 Complete!** ✅ *AI Agent Workflow installed*

### Step 2 of 3: Quick Start ⚡

```bash
# Initialize with mock agents (instant setup)
agent-orch init --profile solo-engineer --minimal

# Register current directory as a project
agent-orch register-project . "speed-demo" --mode autonomous

# Start orchestration
agent-orch start --discord=false
```

**Step 2 of 3 Complete!** ✅ *AI agents are running*

### Step 3 of 3: See the Magic ⚡

```bash
# Create your first epic
agent-orch epic "Create a hello world API"

# Watch agents work (they'll plan, code, and test automatically)
agent-orch status --watch
```

**🎉 Speed Run Complete!** You just orchestrated AI agents in under 2 minutes!

!!! warning "⚠️ For Production Use"
    
    Speed run uses mock agents. For real AI, review [Essential Best Practices](#essential-best-practices) for API key security and testing patterns.

**Step 3 of 3 Complete!** ✅ *Witnessed AI agent collaboration*

---

## 🎓 Guided Tour (10 minutes) {#guided-tour}

> **Goal**: Learn the core concepts while building a real project with AI assistance

### Prerequisites Check (30 seconds)

Open your terminal and verify:

```bash
# Check Python (need 3.8+)
$ python3 --version
Python 3.9.7  ✅

# Check pip
$ pip3 --version
pip 21.2.4  ✅

# Check git (optional but recommended)
$ git --version
git version 2.32.0  ✅
```

!!! tip "Platform Notes"
    - **Windows**: Use WSL2 or PowerShell as Administrator
    - **macOS**: Use Terminal or iTerm2
    - **Linux**: Any terminal works great

### Step 1 of 5: Install Agent Workflow ⚡

**Progress: ████░░░░░░░░░░░░░░░░ 20%**

```bash
# Install the latest version
$ pip install agent-workflow

# Verify installation
$ agent-orch version

    ╭─────────────────────────────────────╮
    │  Agent Workflow v1.0.0 🎉          │
    │  Ready to orchestrate AI agents!    │
    │  Short alias: aw                    │
    ╰─────────────────────────────────────╯
```

**Step 1 of 5 Complete!** ✅ *Agent Workflow installed and verified*

### 🔧 Troubleshooting Installation

<details>
<summary>Click if you see any errors...</summary>

**Permission denied error:**
```bash
$ pip install --user agent-workflow
```

**Old pip version:**
```bash
$ python -m pip install --upgrade pip
$ pip install agent-workflow
```

**Alternative: Use installation script:**
```bash
$ curl -fsSL https://raw.githubusercontent.com/jmontp/agent-workflow/main/install.sh | bash
```
</details>

### Step 2 of 5: Setup Your Environment ⚡

**Progress: ████████░░░░░░░░░░░░ 40%**

```bash
# Initialize with guided setup
$ agent-orch init --profile solo-engineer --interactive

🎯 Setting up AI Agent Workflow...

? AI provider for this tour:
  > Mock (Recommended for learning)
    Claude (Anthropic) 
    OpenAI (GPT-4)

? Enable Discord bot? [y/N]: y
? Discord setup:
  > Skip for now (Learn basics first)
    Configure now (Advanced)

✨ Environment configured:
  ✅ ~/.agent-workflow/config.yaml
  ✅ Mock AI agents ready for learning
  ✅ Discord integration prepared

🎓 Ready for your first project!
```

**Step 2 of 5 Complete!** ✅ *Environment configured for learning*

!!! tip "💡 First Time with AI Agents?"
    
    Before working with real code, review the [Essential Best Practices](#essential-best-practices) section below for security and testing guidance.

```bash
# Register current directory as your first project
$ agent-orch register-project . "my-first-api" --framework web

📋 Registering project: my-first-api

🔍 Analyzing project structure...
  ✅ Valid directory structure
  ✅ Git repository detected
  ✅ Web framework type set

🎯 Project registered successfully!
  📂 Path: /current/directory
  🏷️ Name: my-first-api
  🎭 Mode: blocking (requires your approval)
  🔧 Framework: web
```

**Step 3 of 5 Complete!** ✅ *Project registered and ready*

### Step 4 of 5: Start Your AI Agent Team ⚡

**Progress: ████████████████░░░░ 80%**

```bash
# Start orchestration for your project
$ agent-orch start --discord

╭─────────────────────────────────────────────────────╮
│  🚀 AI Agent Orchestrator Starting...               │
├─────────────────────────────────────────────────────┤
│  Project: my-first-api                              │
│  Mode: Human-in-the-Loop (blocking)                 │
│  Agents: 4 ready (Design, Code, QA, Data)          │
│  Discord: Connected to #orch-my-first-api           │
╰─────────────────────────────────────────────────────╯

[ORCHESTRATOR] State: IDLE → READY
[DISCORD] Join #orch-my-first-api for interactive controls
[ORCHESTRATOR] Ready for your first epic!
```

**Step 4 of 5 Complete!** ✅ *AI agents are running and ready*

### Step 5 of 5: Watch AI Agents Work ⚡

**Progress: ████████████████████ 100%**

Choose your preferred interface to create your first epic:

**Option A: Discord Commands (Recommended)**
```
Go to your Discord server and type in #orch-my-first-api:
/epic "Build a Hello World API with TDD"

Watch the magic happen live! 🎭
```

**Option B: CLI Commands**
```bash
# Create your first epic
$ agent-orch epic "Build a Hello World API with TDD"

📋 Creating Epic: Build a Hello World API with TDD

[DESIGN AGENT] 🎨 Analyzing requirements...
  ↳ Identified 3 user stories
  ↳ Created TDD-focused architecture

[ORCHESTRATOR] Stories created:
  • API-1: Setup project structure & testing framework
  • API-2: Create hello endpoint with tests
  • API-3: Add documentation and CI/CD

🎯 Epic created! Ready for sprint planning.

# Watch the agents plan and execute
$ agent-orch sprint plan
$ agent-orch sprint start
```

**Real-time collaboration in action:**

```
[QA AGENT] 🧪 Writing test for API-1...
  ↳ test_project_structure.py ✅
  ↳ Status: 🔴 RED (test failing as expected)

[CODE AGENT] 💻 Implementing API-1...
  ↳ Creating Flask app structure
  ↳ Installing pytest, flask
  ↳ Status: 🟢 GREEN (tests passing!)

[DESIGN AGENT] 🔍 Reviewing implementation...
  ↳ Architecture approved ✅
  ↳ Ready for human approval

[ORCHESTRATOR] 🎯 Requesting approval for API-2...
  ↳ Discord: /approve API-2 or /request_changes
```

### 🎉 Guided Tour Complete!

```ascii
    ╔═══════════════════════════════════════════════════════╗
    ║   🏆 Achievement Unlocked: AI Agent Orchestrator! 🏆  ║
    ║                                                       ║
    ║   You just learned to:                                ║
    ║   • Setup AI agent workflows                          ║
    ║   • Register and manage projects                      ║
    ║   • Experience human-in-the-loop TDD                  ║
    ║   • Use Discord for real-time collaboration           ║
    ║                                                       ║
    ║   Time: 10 minutes well spent! 🎓                     ║
    ╚═══════════════════════════════════════════════════════╝
```

**Step 5 of 5 Complete!** ✅ *You've mastered the basics!*

**Next Steps:**
- [Enable real AI agents](#enable-real-ai) with Claude or OpenAI
- [Try the Full Setup](#full-setup) for production features
- [Join our Discord community](https://discord.gg/agent-workflow) to share your success!

---

## 🏗️ Full Setup (20 minutes) {#full-setup}

> **Goal**: Production-ready setup with real AI, Discord integration, and multi-project orchestration

### Prerequisites: Everything from Guided Tour

Complete the [Guided Tour](#guided-tour) first, then continue here for production features.

### Step 1 of 7: Enable Real AI Providers ⚡ {#enable-real-ai}

**Progress: ██░░░░░░░░░░░░░░░░░░ 14%**

**Choose your AI provider:**

**Option A: Claude (Anthropic) - Recommended**
```bash
# Configure Claude integration
$ agent-orch setup-api --provider claude --interactive

? Anthropic API Key: [Enter your key from console.anthropic.com]
? Default model: claude-3-sonnet-20240229
? Rate limit (requests/minute): 30

✅ Claude integration configured!
🧪 Testing connection... Success!

[CLAUDE] Ready to orchestrate real AI agents
```

**Option B: OpenAI (GPT-4)**
```bash
# Configure OpenAI integration  
$ agent-orch setup-api --provider openai --interactive

? OpenAI API Key: [Enter your key from platform.openai.com]
? Default model: gpt-4-turbo-preview
? Rate limit (requests/minute): 20

✅ OpenAI integration configured!
🧪 Testing connection... Success!

[OPENAI] Ready for production workflows
```

**Step 1 of 7 Complete!** ✅ *Real AI agents configured*

---

## 🛡️ Essential Best Practices

!!! warning "Critical Security & Development Practices"
    
    Before proceeding with production AI agents, follow these essential practices:

### 🔐 API Key Security

**Never commit API keys to repositories:**

```bash
# ❌ WRONG - Don't do this
echo "ANTHROPIC_API_KEY=sk-ant-api03-..." >> config.yml

# ✅ CORRECT - Use environment variables
export ANTHROPIC_API_KEY="sk-ant-api03-..."
echo "ANTHROPIC_API_KEY" >> .gitignore
```

**Use secure environment management:**

```bash
# Create .env file (never commit)
echo "ANTHROPIC_API_KEY=your-key-here" > .env
echo "DISCORD_BOT_TOKEN=your-token-here" >> .env
echo ".env" >> .gitignore

# Load in your shell
source .env
```

### 🧪 Testing Best Practices

**Always run tests before AI agent changes:**

```bash
# Before starting AI agents on real code
pytest tests/ -v
make test  # If Makefile exists

# Check test coverage
pytest --cov=src tests/
```

**Basic test structure example:**

```python
def test_api_endpoint():
    """Test basic API functionality"""
    try:
        # NOTE: No /api/health endpoint - use CLI health command instead
        import subprocess
        result = subprocess.run(['agent-orch', 'health', '--check-all'], capture_output=True)
        response = type('Response', (), {'status_code': 200 if result.returncode == 0 else 500, 'json': {'status': 'healthy' if result.returncode == 0 else 'error'}})()
        assert response.status_code == 200
        assert 'status' in response.json
    except Exception as e:
        pytest.fail(f"API test failed: {e}")
```

### 🚨 Error Handling Patterns

**Always use try-catch for AI operations:**

```python
# In your code when working with AI agents
try:
    result = risky_operation()
    return result
except APIError as e:
    logger.error(f"API error: {e}")
    return fallback_value()
except Exception as e:
    logger.error(f"Unexpected error: {e}")
    raise  # Re-raise for debugging
```

### 📋 Quick Safety Checklist

Before using AI agents in production:

- [ ] API keys stored as environment variables
- [ ] `.env` and sensitive files in `.gitignore`
- [ ] Tests pass locally (`pytest` or `make test`)
- [ ] Code backed up or in version control
- [ ] Start with `--mode blocking` for human approval
- [ ] Review agent changes before approval

---

### Step 2 of 7: Discord Bot Integration ⚡

**Progress: ████░░░░░░░░░░░░░░░░ 28%**

```bash
# Setup Discord bot with guided wizard
$ agent-orch setup-discord --interactive

🎭 Discord Bot Setup Wizard

? Discord Bot Token: [Create at https://discord.com/developers/applications]
? Discord Server ID: [Right-click your server → Copy Server ID]
? Auto-create project channels? [Y/n]: Y
? Channel naming prefix: orch

🔗 Setting up Discord integration...
  ✅ Bot token validated
  ✅ Server permissions verified
  ✅ Project channels created:
     • #orch-my-first-api
     • #orch-general

🎉 Discord bot connected!
  📱 Use /help in Discord to see available commands
  💬 Real-time collaboration is now active
```

**Step 2 of 7 Complete!** ✅ *Discord bot operational*

```bash
# Register multiple projects for orchestration
$ agent-orch projects list

📋 Registered Projects:
  • my-first-api (Web/Flask) - Active
  
$ agent-orch register-project ~/work/mobile-app "MyMobileApp" --framework mobile
$ agent-orch register-project ~/work/data-pipeline "Analytics" --framework ml

📋 Multi-project setup complete:
  🌐 my-first-api (Web/Flask) - #orch-my-first-api
  📱 MyMobileApp (Mobile) - #orch-mymobileapp  
  📊 Analytics (ML/Data) - #orch-analytics

🎯 Each project has dedicated Discord channels
💻 Switch between projects seamlessly
```

**Step 3 of 7 Complete!** ✅ *Multi-project orchestration ready*

### Step 4 of 7: Advanced Workflow Configuration ⚡

**Progress: ████████░░░░░░░░░░░░ 56%**

```bash
# Configure advanced orchestration modes
$ agent-orch configure --section projects --wizard

? Default orchestration mode:
  > blocking (Human approval required)
    partial (Autonomous with review)
    autonomous (Full automation)

? Enable parallel execution? [Y/n]: Y
? Max concurrent agents per project: 4
? Sprint duration (days): 7
? Approval timeout (minutes): 30

✅ Advanced workflow configured!
  🚦 Human-in-the-loop controls active
  ⚡ Parallel execution enabled
  📊 Custom sprint cycles
```

**Step 4 of 7 Complete!** ✅ *Advanced workflows configured*

```bash
# Enable comprehensive monitoring and health checks
$ agent-orch start --daemon --port 8080

🏥 Health monitoring enabled:
  📊 Real-time metrics at http://localhost:8080
  📈 Performance dashboards
  🚨 Automatic alerts for failures
  📝 Comprehensive logging

# View system health
$ agent-orch health --check-all

🏥 System Health Report:
  ✅ All agents operational
  ✅ Discord bot connected
  ✅ AI providers responding
  ✅ Projects synchronized
  📊 Average response time: 2.3s
  💾 Memory usage: 45% (normal)
```

**Step 5 of 7 Complete!** ✅ *Production monitoring active*

### Step 6 of 7: Security & Compliance ⚡

**Progress: ████████████░░░░░░░░ 84%**

```bash
# Configure security policies
$ agent-orch configure --section security

🔒 Security Configuration:
? Enable audit logging? [Y/n]: Y
? Require code review approvals? [Y/n]: Y  
? Enable backup before changes? [Y/n]: Y
? Restrict file system access? [Y/n]: Y

✅ Security policies configured:
  📝 All actions logged for audit
  👥 Human approvals required for critical changes
  💾 Automatic backups before modifications
  🔒 Sandboxed agent operations
```

**Step 6 of 7 Complete!** ✅ *Security policies enforced*

```bash
# Optional: Enable team collaboration features
$ agent-orch configure --wizard

🏢 Team Collaboration Setup:
? Enable shared project state? [Y/n]: Y
? Auto-sync with team members? [Y/n]: Y
? Enable cross-project intelligence? [Y/n]: Y

🚀 Production deployment ready:
  📡 Multi-user collaboration enabled
  🔄 Real-time state synchronization
  🧠 Shared AI knowledge across projects
  ⚡ High availability configuration
  📈 Enterprise-grade monitoring
```

**Progress: ████████████████████ 100%**

### 🎉 Full Setup Complete!

```ascii
    ╔═══════════════════════════════════════════════════════╗
    ║   🏆 Achievement Unlocked: Production Ready! 🏆       ║
    ║                                                       ║
    ║   You now have:                                       ║
    ║   • Real AI agents with Claude/OpenAI                 ║
    ║   • Discord bot for team collaboration                ║
    ║   • Multi-project orchestration                       ║
    ║   • Advanced workflows & monitoring                   ║
    ║   • Security & compliance policies                    ║
    ║   • Production deployment configuration               ║
    ║                                                       ║
    ║   Time: 20 minutes to production mastery! 🏗️          ║
    ╚═══════════════════════════════════════════════════════╝
```

**Step 7 of 7 Complete!** ✅ *Production-ready AI agent orchestration!*

---

Congratulations on completing your chosen adventure! Here are your next steps based on what you accomplished:

### 🏃 If you completed Speed Run:
- **Level up**: Try the [Guided Tour](#guided-tour) to learn the concepts
- **Go production**: Jump to [Full Setup](#full-setup) for real AI
- **Share success**: Post in [Discord community](https://discord.gg/agent-workflow) with #speedrun

### 🎓 If you completed Guided Tour:
- **Enable real AI**: [Setup Claude or OpenAI](#enable-real-ai) for production workflows
- **Advanced features**: Continue with [Full Setup](#full-setup) 
- **Build something real**: Create your first production project!

### 🏗️ If you completed Full Setup:
- **Master advanced workflows**: [Multi-project orchestration guide](../user-guide/multi-project-orchestration.md)
- **Customize agents**: [Agent configuration reference](../user-guide/cli-reference.md#agent-configuration)
- **Enterprise features**: [Production deployment guide](../deployment/production.md)

---

## 🚀 Universal Next Steps

No matter which path you took, these features await:

### 🎮 Interactive Learning
- **Try the examples**: [Integration examples](../user-guide/integration-examples.md) with real code
- **Master commands**: [Complete CLI reference](../user-guide/cli-reference.md) with all options
- **Understand workflows**: [TDD workflow guide](../user-guide/tdd-workflow.md) with best practices

### 🤝 Community & Support
- **Join Discord**: [Active community](https://discord.gg/agent-workflow) with help and showcases
- **Read FAQ**: [Common questions](../user-guide/faq.md) and troubleshooting tips
- **Contribute**: [Contributing guide](../development/contributing.md) to help improve the project

### 🏢 Enterprise Features
- **Multi-project orchestration**: Manage multiple codebases simultaneously
- **Team collaboration**: Real-time synchronization across team members
- **Custom agent behaviors**: Tailor AI agents to your specific workflows
- **Advanced security**: Role-based access and audit trails

### 🔧 Power User Features
```bash
# Custom agent configurations
$ agent-orch configure agents --wizard

# Advanced workflow automation
$ agent-orch workflows create "custom-tdd-flow"

# Performance optimization
$ agent-orch optimize --profile production

# Integration with CI/CD
$ agent-orch integrate github-actions
```

---

## 📚 Command Cheat Sheet

<div align="center">

| **Setup & Config** | **Project Management** | **AI & Discord** |
|:---|:---|:---|
| `agent-orch init` | `register-project <path>` | `setup-api --provider claude` |
| `agent-orch configure` | `projects list` | `setup-discord --interactive` |
| `agent-orch health` | `status --project <name>` | `start --discord` |

| **Workflow Commands** | **Advanced** | **Help & Info** |
|:---|:---|:---|
| `epic "description"` | `configure --wizard` | `agent-orch help` |
| `sprint plan` | `health --check-all` | `version --verbose` |
| `sprint start` | `migrate-from-git <path>` | Visit [docs](../index.md) |

</div>

**Aliases**: Use `aw` instead of `agent-orch` for all commands!

## 🛠️ Troubleshooting

<details>
<summary><b>🚨 Installation Failed</b></summary>

**Try these solutions in order:**

```bash
# 1. Update pip first
python -m pip install --upgrade pip

# 2. Try user installation
pip install --user agent-workflow

# 3. Use installation script
curl -fsSL https://raw.githubusercontent.com/jmontp/agent-workflow/main/install.sh | bash

# 4. Install from source (if all else fails)
git clone https://github.com/jmontp/agent-workflow.git
cd agent-workflow && pip install -e .
```
</details>

<details>
<summary><b>🤖 Agents Not Responding</b></summary>

```bash
# Check system health
agent-orch health --check-all

# Restart with verbose logging
agent-orch stop && agent-orch start --verbose

# Reset configuration if needed
agent-orch configure --reset

# Check AI provider status
agent-orch setup-api --test-connection
```
</details>

<details>
<summary><b>🎭 Discord Integration Issues</b></summary>

```bash
# Verify Discord setup
agent-orch setup-discord --test-connection

# Check bot permissions in Discord server
# Ensure bot has "Send Messages" and "Use Slash Commands"

# Re-run Discord setup
agent-orch setup-discord --interactive
```
</details>

<details>
<summary><b>🆘 Still Need Help?</b></summary>

**Get support from the community:**
- 💬 [Discord Community](https://discord.gg/agent-workflow) - Live help from experts
- 📖 [Troubleshooting Guide](../user-guide/troubleshooting.md) - Comprehensive solutions
- 🐛 [GitHub Issues](https://github.com/jmontp/agent-workflow/issues) - Report bugs
- 📧 [Email Support](mailto:support@agent-workflow.dev) - Direct assistance

**When reporting issues, include:**
- Your operating system and Python version
- Full error messages and stack traces  
- Output of `agent-orch health --verbose`
- Steps to reproduce the problem
</details>

---

## 🌟 Final Tips

!!! tip "🏃 Challenge Yourself"
    **Speed Run Challenge**: Install to working AI agents in under 2 minutes! Share your time on Discord with #speedrun

!!! info "🎓 Recommended Learning Path"
    1. **Start here**: Complete Speed Run (2 min) ✅
    2. **Learn concepts**: Complete Guided Tour (10 min)
    3. **Go production**: Complete Full Setup (20 min)
    4. **Master advanced**: [User Guide](../user-guide/index.md)
    5. **Customize everything**: [Development Guide](../development/index.md)

!!! success "🎉 You're an AI Agent Orchestrator!"
    You've just learned to command AI agents like a conductor leads an orchestra. Now build something amazing!

---

<div align="center">

**🤖 Built with AI agents, for AI agent enthusiasts**

[⭐ Star on GitHub](https://github.com/jmontp/agent-workflow) | [📖 Documentation](../index.md) | [💬 Discord Community](https://discord.gg/agent-workflow) | [🐛 Report Issues](https://github.com/jmontp/agent-workflow/issues)

*"The best way to predict the future is to build it with AI agents." - Agent Workflow Team*

</div>