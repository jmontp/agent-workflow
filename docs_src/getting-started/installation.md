# Installation Guide

This comprehensive guide will help you install and set up the AI Agent TDD-Scrum Workflow system with clear, step-by-step instructions.

## Prerequisites

### System Requirements

- **Operating System**: Linux, macOS, or Windows (with WSL2 recommended)
- **Python**: Version 3.9 or higher
- **Git**: Version 2.20 or higher
- **Memory**: Minimum 4GB RAM, 8GB+ recommended for multi-project setups
- **Storage**: At least 2GB free space

### Required Accounts & Tokens

You'll need these before starting:

1. **Discord Bot Token** (REQUIRED)
   - Create a Discord application at [Discord Developer Portal](https://discord.com/developers/applications)
   - Create a bot and copy the token
   - Invite bot to your server with permissions below

2. **Claude Code CLI** (HIGHLY RECOMMENDED)
   - Sign up at [claude.ai](https://claude.ai)
   - Install Claude Code CLI from [official docs](https://docs.anthropic.com/en/docs/claude-code)

3. **GitHub Token** (Optional)
   - Create at [GitHub Settings > Tokens](https://github.com/settings/tokens)
   - Enables advanced git operations

## Quick Start Installation

### 🚀 One-Command Setup

```bash
curl -sSL https://raw.githubusercontent.com/your-username/agent-workflow/main/install.sh | bash
```

### 📋 Manual Installation (Recommended)

#### Step 1: Clone Repository
```bash
git clone https://github.com/your-username/agent-workflow.git
cd agent-workflow
```

#### Step 2: Create Virtual Environment
```bash
# Create isolated Python environment
python3 -m venv .venv

# Activate environment
source .venv/bin/activate  # Linux/macOS
# OR
.venv\Scripts\activate     # Windows
```

#### Step 3: Install Dependencies
```bash
# Core dependencies
pip install -r requirements.txt

# Verify installation
python -c "import discord, yaml, websockets; print('✅ Core dependencies installed')"
```

#### Step 4: Configure Environment
```bash
# Copy environment template
cp .env.example .env

# Edit with your tokens (use your preferred editor)
nano .env
```

Required `.env` content:
```bash
# REQUIRED: Discord bot token
DISCORD_BOT_TOKEN=your_discord_bot_token_here

# RECOMMENDED: Claude API settings
ANTHROPIC_API_KEY=your_claude_api_key_here
ANTHROPIC_MODEL=claude-3-sonnet-20240229

# OPTIONAL: GitHub integration
GITHUB_TOKEN=your_github_token_here

# SYSTEM: Basic configuration
HOSTNAME=localhost
LOG_LEVEL=INFO
ORCHESTRATOR_MODE=blocking
```

#### Step 5: Initialize System
```bash
# Initialize project structure
python scripts/multi_project_orchestrator.py --setup

# Run health check
python scripts/multi_project_orchestrator.py --health-check
```

#### Step 6: Verify Installation
```bash
# Run test suite
pytest tests/ -v

# Expected: All core tests pass
# Note: Some integration tests may require additional setup
```

## Detailed Installation Options

### Option A: Production Installation

For running the system in production:

```bash
# 1. System dependencies (Ubuntu/Debian)
sudo apt update && sudo apt install -y python3 python3-pip python3-venv git curl

# 2. Clone and setup
git clone https://github.com/your-username/agent-workflow.git
cd agent-workflow
python3 -m venv .venv
source .venv/bin/activate

# 3. Install production dependencies
pip install --upgrade pip
pip install -r requirements.txt
pip install gunicorn supervisor  # For production deployment

# 4. Configure for production
cp config/production.env .env
# Edit .env with production values
```

### Option B: Development Installation

For development and contribution:

```bash
# 1. Clone with development branch
git clone -b develop https://github.com/your-username/agent-workflow.git
cd agent-workflow

# 2. Setup development environment
python3 -m venv .venv
source .venv/bin/activate

# 3. Install with development tools
pip install -e .
pip install -r requirements-dev.txt

# 4. Setup pre-commit hooks
pre-commit install

# 5. Run full test suite
pytest tests/ --cov=lib --cov-report=html
open htmlcov/index.html  # View coverage report
```

### Option C: Docker Installation

For containerized deployment:

```bash
# 1. Clone repository
git clone https://github.com/your-username/agent-workflow.git
cd agent-workflow

# 2. Copy environment
cp .env.example .env
# Edit .env with your tokens

# 3. Build and run
docker-compose up -d

# 4. Check status
docker-compose ps
docker-compose logs orchestrator
```

## Discord Bot Setup

### Step 1: Create Discord Application

1. Visit [Discord Developer Portal](https://discord.com/developers/applications)
2. Click **"New Application"**
3. Name your application (e.g., "AI Agent Workflow")
4. Go to **"Bot"** section in sidebar
5. Click **"Add Bot"** 
6. Copy the **Bot Token**
7. Add token to your `.env` file

### Step 2: Configure Bot Permissions

Your bot needs these permissions:

- ✅ **Send Messages** - Post command responses
- ✅ **Use Slash Commands** - Enable `/epic`, `/sprint`, etc.
- ✅ **Create Public Threads** - For threaded discussions
- ✅ **Embed Links** - Rich message formatting
- ✅ **Attach Files** - Share generated files
- ✅ **Read Message History** - Context awareness
- ✅ **Manage Channels** - Create project channels

### Step 3: Invite Bot to Server

Use this URL template (replace `YOUR_CLIENT_ID`):

```
https://discord.com/api/oauth2/authorize?client_id=YOUR_CLIENT_ID&permissions=274877918208&scope=bot%20applications.commands
```

Find your Client ID in the **"General Information"** tab.

## Platform-Specific Instructions

### 🐧 Linux (Ubuntu/Debian)

```bash
# Update system packages
sudo apt update && sudo apt upgrade -y

# Install system dependencies
sudo apt install -y python3 python3-pip python3-venv git curl build-essential

# Install the workflow system
git clone https://github.com/your-username/agent-workflow.git
cd agent-workflow
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Test installation
python -c "import lib.discord_bot; print('✅ Installation successful')"
```

### 🍎 macOS

```bash
# Install Homebrew (if not already installed)
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install dependencies
brew install python@3.11 git

# Install the workflow system
git clone https://github.com/your-username/agent-workflow.git
cd agent-workflow
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Test installation
python -c "import lib.discord_bot; print('✅ Installation successful')"
```

### 🪟 Windows (with WSL2 - Recommended)

```powershell
# In PowerShell (as Administrator)
wsl --install -d Ubuntu
wsl --set-default-version 2

# Restart computer, then in WSL2 terminal:
sudo apt update && sudo apt install -y python3 python3-pip python3-venv git

# Install the workflow system
git clone https://github.com/your-username/agent-workflow.git
cd agent-workflow
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 🪟 Windows (Native)

```cmd
# Install Python 3.9+ from python.org
# Install Git from git-scm.com

# In Command Prompt or PowerShell:
git clone https://github.com/your-username/agent-workflow.git
cd agent-workflow
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

## Verification & Testing

### ✅ Installation Health Check

```bash
# Test 1: Import verification
python -c "
import lib.discord_bot
import lib.state_machine
import lib.data_models
print('✅ All core modules import successfully')
"

# Test 2: Discord integration check
python -c "
import os
if os.getenv('DISCORD_BOT_TOKEN'):
    print('✅ Discord token configured')
else:
    print('❌ Discord token missing - check .env file')
"

# Test 3: System health check  
python scripts/multi_project_orchestrator.py --health-check
```

Expected output:
```
✅ Configuration loaded
✅ State machine initialized
✅ Discord integration ready  
✅ Claude integration available
✅ System ready for operation
```

### 🧪 Test Suite Execution

```bash
# Quick test - core functionality
pytest tests/unit/test_state_machine.py -v
pytest tests/unit/test_data_models.py -v

# Integration tests (requires Discord token)
pytest tests/integration/ -v

# Full test suite with coverage
pytest tests/ --cov=lib --cov-report=term-missing

# Performance tests
pytest tests/performance/ -v --durations=10
```

### 📊 Coverage Report

```bash
# Generate detailed coverage report
pytest tests/ --cov=lib --cov-report=html

# View in browser
open htmlcov/index.html  # macOS
xdg-open htmlcov/index.html  # Linux
start htmlcov/index.html  # Windows
```

## Documentation Setup (Optional)

### Local Documentation Server

```bash
# Install documentation dependencies
pip install mkdocs mkdocs-material mkdocs-mermaid2-plugin

# Serve documentation locally
mkdocs serve

# Access at: http://localhost:8000
```

### Build Static Documentation

```bash
# Build documentation
mkdocs build

# Deploy to GitHub Pages
mkdocs gh-deploy
```

## Configuration Files

The system expects certain configuration files:

### Project Configuration (Optional)
Create `config/projects.yaml`:
```yaml
projects:
  - name: "my_project"
    path: "/path/to/project"
    orchestration: "blocking"
```

### Environment Variables
Required variables:
```bash
export DISCORD_BOT_TOKEN="your_discord_bot_token"
```

Optional variables:
```bash
export HOSTNAME="your_hostname"  # For Discord channel naming
export LOG_LEVEL="INFO"          # Logging level
```

## Platform-Specific Notes

### Windows
```bash
# Use Windows paths
set DISCORD_BOT_TOKEN=your_token

# Activate virtual environment
venv\Scripts\activate

# Run with Python
python lib/discord_bot.py
```

### macOS/Linux
```bash
# Use Unix paths
export DISCORD_BOT_TOKEN="your_token"

# Activate virtual environment
source venv/bin/activate

# Run with Make
make run
```

### WSL (Windows Subsystem for Linux)
The system is fully compatible with WSL. Follow Linux instructions above.

## Docker Installation (Alternative)

For containerized deployment:

```dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
CMD ["python", "lib/discord_bot.py"]
```

```bash
# Build and run
docker build -t agent-workflow .
docker run -e DISCORD_BOT_TOKEN="your_token" agent-workflow
```

## Troubleshooting Installation

### Common Issues

**Permission Errors:**
```bash
# Use user installation
pip install --user -r requirements.txt
```

**Version Conflicts:**
```bash
# Create clean virtual environment
python -m venv fresh_venv
source fresh_venv/bin/activate
pip install -r requirements.txt
```

**Discord.py Installation Issues:**
```bash
# Update pip first
pip install --upgrade pip

# Install with specific version
pip install discord.py==2.3.0
```

**Import Errors:**
- Ensure virtual environment is activated
- Check Python path includes project directory
- Verify all dependencies installed correctly

### Dependency Issues

If you encounter dependency conflicts:

```bash
# Check installed packages
pip list

# Create requirements lock file
pip freeze > requirements-lock.txt

# Clean install from lock file
pip install -r requirements-lock.txt
```

### Performance Optimization

For better performance:

```bash
# Install with optimizations
pip install --upgrade pip setuptools wheel

# Use faster package resolution
pip install --use-feature=fast-deps -r requirements.txt
```

## Next Steps

After successful installation:

1. [**Configure Discord Bot**](../deployment/discord-setup.md)
2. [**Set up Project Configuration**](configuration.md)  
3. [**Try Quick Start Guide**](quick-start.md)
4. [**Read User Guide**](../user-guide/hitl-commands.md)

---

!!! success "Installation Complete"
    Your AI Agent TDD-Scrum Workflow system is now installed and ready for configuration!