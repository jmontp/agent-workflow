# Installation Guide

Detailed installation instructions for the AI Agent TDD-Scrum Workflow system.

## System Requirements

### Python Environment
- **Python 3.8 or higher**
- **pip package manager**
- **Virtual environment** (recommended)

### External Services
- **Discord Application** with bot token
- **Git** for repository management
- **Optional**: AI service integration

## Installation Methods

### Method 1: Direct Installation (Recommended)

```bash
# Clone repository
git clone https://github.com/jmontp/agent-workflow.git
cd agent-workflow

# Create virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
make install
```

### Method 2: Development Installation

For contributors and developers:

```bash
# Clone repository
git clone https://github.com/jmontp/agent-workflow.git
cd agent-workflow

# Set up development environment
make dev-setup

# This installs additional development tools:
# - black (code formatting)
# - flake8 (linting)
# - pytest plugins
```

### Method 3: Manual Installation

If Make is not available:

```bash
# Install core dependencies
pip install discord.py>=2.3.0
pip install pygithub>=1.59.0  
pip install pyyaml>=6.0
pip install anthropic>=0.3.0

# Install testing dependencies
pip install pytest>=7.4.0
pip install pytest-asyncio>=0.21.0
pip install pytest-mock>=3.11.0
pip install pytest-cov>=4.1.0
```

## Documentation Setup (Optional)

To build and serve documentation locally:

```bash
# Install MkDocs and dependencies
pip install mkdocs
pip install mkdocs-material
pip install mkdocs-mermaid2-plugin

# Serve documentation locally
mkdocs serve
```

Access documentation at: `http://localhost:8000`

## Verification

### 1. Check Installation
```bash
# Verify Python modules
python -c "import discord, yaml, anthropic; print('All modules imported successfully')"

# Run basic tests
make test-unit
```

### 2. Environment Setup
```bash
# Check required environment variables
echo $DISCORD_BOT_TOKEN
```

### 3. System Test
```bash
# Run orchestrator in test mode
python scripts/orchestrator.py --help

# Run Discord bot in test mode  
python lib/discord_bot.py --help
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