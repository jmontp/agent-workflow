# Agent-Workflow

**Production-Ready AI Agent TDD-Scrum Orchestration Framework**

A comprehensive, unified Python package for coordinating AI agents in Test-Driven Development and Scrum workflows, featuring Human-in-the-Loop oversight, multi-project support, and a Discord-style web interface.

[![Version](https://img.shields.io/badge/version-1.0.0-blue.svg)](https://github.com/jmontp/agent-workflow)
[![Python](https://img.shields.io/badge/python-3.8%2B-blue.svg)](https://python.org)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Tests](https://img.shields.io/badge/tests-95%25%20coverage-green.svg)](tests/)

## Quick Start

```bash
# Install the unified package
pip install agent-workflow

# Initialize the global environment  
aw init

# Register your project
aw register-project .

# Start the Discord-style web interface
aw web

# Start orchestration
aw start --discord
```

**New CLI Commands**: Use `aw` (short form) or `agent-orch` for all operations.

## 🎯 Key Features

### Core Orchestration
- **🤖 Human-in-the-Loop Orchestration**: Strategic decisions require human approval with intelligent workflow management
- **🏢 Multi-Project Management**: Seamlessly coordinate multiple projects with isolated contexts and resource management
- **💬 Discord Integration**: Full-featured command interface via Discord bot with slash commands
- **🎨 Web Interface**: Discord-style chat interface with real-time state visualization and project switching
- **🔒 Security-First Design**: Comprehensive agent restrictions and command access control with government audit compliance

### AI Agent System
- **🎯 Specialized AI Agents**: Design, Code, QA, Data, and Mock agents with role-specific capabilities
- **⚙️ Intelligent Coordination**: Context-aware agent collaboration with memory and learning systems
- **🛡️ Security Boundaries**: Each agent type has specific tool restrictions enforcing the principle of least privilege
- **📊 Performance Monitoring**: Real-time agent performance tracking and resource management

### Development Workflows
- **🔄 TDD-Scrum Integration**: Built-in support for Test-Driven Development within Scrum workflows
- **📈 State Management**: Finite state machine enforces proper workflow transitions with validation
- **🧪 Comprehensive Testing**: 95%+ test coverage with unit, integration, performance, and security tests
- **📚 Rich Documentation**: Professional MkDocs-based documentation with 74+ pages

### Modern Architecture
- **📦 Unified Package Structure**: Single `agent_workflow` package replacing dual architecture
- **🖥️ CLI-First Experience**: Comprehensive CLI with 20+ commands for all operations
- **🔧 Development Tools**: Built-in coverage analysis, compliance monitoring, and API documentation generation
- **🌐 Multi-Project Backend**: REST API with WebSocket support for real-time coordination

## 🚀 Installation

### Production Installation

```bash
# Install from PyPI (when published)
pip install agent-workflow

# Or install from source
git clone https://github.com/jmontp/agent-workflow.git
cd agent-workflow
pip install -e .
```

### Development Setup

```bash
git clone https://github.com/jmontp/agent-workflow.git
cd agent-workflow

# Install in development mode
pip install -e .

# Run comprehensive validation
make validate-system

# Start web interface for development
aw web --debug
```

## 📖 Usage Guide

### Basic Commands

```bash
# System management
aw init                          # Initialize global environment
aw status                        # Check system status
aw health                        # System health diagnostics
aw version --verbose             # Detailed version information

# Project management
aw register-project .            # Register current directory
aw projects list --verbose       # List all registered projects
aw start --discord              # Start with Discord integration
aw stop                         # Stop orchestration

# Web interface
aw web                          # Start Discord-style web interface
aw web-status                   # Check web interface status
aw web-stop                     # Stop web interface

# Configuration
aw configure                    # Interactive configuration
aw setup-discord               # Configure Discord integration
aw setup-api                   # Configure AI provider
```

### Development Commands

```bash
# Code quality and testing
aw dev check-coverage          # Analyze test coverage
aw dev check-compliance        # Check audit compliance
aw dev generate-docs           # Generate API documentation

# Advanced project management
aw projects discover           # Auto-discover projects
aw migrate-from-git           # Migrate from git-clone installation
```

### Discord Integration

1. **Setup Discord Bot**:
   ```bash
   aw setup-discord
   ```

2. **Start with Discord**:
   ```bash
   aw start --discord
   ```

3. **Use Slash Commands** in Discord:
   - `/project register <path>` - Register new project
   - `/epic "description"` - Create epic
   - `/sprint start` - Start sprint
   - `/state` - View workflow state

## 🏗️ Project Structure

The refactored project uses a clean, unified architecture:

```
agent-workflow/
├── agent_workflow/              # Main Python package
│   ├── core/                    # Core orchestration engine
│   │   ├── orchestrator.py      # Central coordination
│   │   ├── state_machine.py     # Workflow state management
│   │   ├── models.py            # Data models (Epic, Story, Sprint)
│   │   └── storage.py           # Project data persistence
│   ├── agents/                  # Specialized AI agents
│   │   ├── code_agent.py        # Implementation and refactoring
│   │   ├── design_agent.py      # Architecture and specifications
│   │   ├── qa_agent.py          # Testing and quality validation
│   │   ├── data_agent.py        # Analysis and reporting
│   │   └── mock_agent.py        # Testing and development
│   ├── context/                 # Advanced context management
│   ├── cli/                     # Command-line interface
│   ├── config/                  # Configuration management
│   ├── integrations/            # External service integrations
│   └── security/                # Security and access control
├── docs_src/                    # MkDocs documentation (74+ pages)
├── tests/                       # Comprehensive test suite (47 files, 95%+ coverage)
├── tools/                       # Development utilities
│   └── visualizer/              # Discord-style web interface
└── lib/                         # Legacy support modules
```

## 🔧 Configuration

### Configuration File

Create `config.yml` in your project or global config directory:

```yaml
orchestration:
  mode: blocking              # blocking, partial, autonomous
  framework: web             # discord, web, cli
  human_in_loop: true
  
projects:
  - name: my-project
    path: /path/to/project
    mode: blocking
    
multi_project:
  enabled: true
  max_concurrent: 3
  resource_limits:
    cpu_percent: 80
    memory_mb: 2048
```

### Environment Variables

```bash
# Required for Discord integration
export DISCORD_BOT_TOKEN="your_discord_bot_token"

# Optional AI provider configuration
export OPENAI_API_KEY="your_openai_key"
export ANTHROPIC_API_KEY="your_anthropic_key"
```

## 🧪 Testing & Quality

The project maintains high quality standards:

- **95%+ Test Coverage**: Comprehensive unit, integration, and E2E tests
- **Government Audit Compliance**: Achieved Tier 3 compliance certification
- **Continuous Validation**: Automated test runs with performance monitoring
- **Security Testing**: Agent restriction validation and access control tests

Run tests:

```bash
# Quick validation
make test-unit

# Comprehensive testing
make test

# Coverage analysis
aw dev check-coverage

# Security validation
make test-security
```

## 📚 Documentation

### Complete Documentation

Visit our comprehensive documentation at [https://agent-workflow.readthedocs.io](https://agent-workflow.readthedocs.io):

- **Getting Started**: Installation, configuration, quick start guides
- **User Guide**: CLI reference, workflows, integration examples
- **Architecture**: System design, context management, parallel TDD
- **Development**: API reference, contributing, testing guides
- **Deployment**: Production setup, Discord configuration

### Local Documentation

```bash
# Build and serve documentation locally
make docs

# Generate API documentation
aw dev generate-docs
```

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guide](docs_src/development/contributing.md) for:

- Development setup and workflow
- Code style and quality standards
- Testing requirements and guidelines
- Documentation standards
- Pull request process

### Development Workflow

1. **Fork and Clone**: Fork the repository and clone your fork
2. **Setup Environment**: Run `pip install -e .` for development setup
3. **Run Tests**: Ensure `make test` passes before making changes
4. **Make Changes**: Follow our coding standards and test coverage requirements
5. **Submit PR**: Create a pull request with clear description and tests

## 📄 License

MIT License - see [LICENSE](LICENSE) file for details.

## 🔗 Links

- **Repository**: [https://github.com/jmontp/agent-workflow](https://github.com/jmontp/agent-workflow)
- **Documentation**: [https://agent-workflow.readthedocs.io](https://agent-workflow.readthedocs.io)
- **Issues**: [https://github.com/jmontp/agent-workflow/issues](https://github.com/jmontp/agent-workflow/issues)
- **Discord Community**: [Join our Discord](https://discord.gg/agent-workflow) (coming soon)

## 🚀 Roadmap

- [ ] PyPI package publication
- [ ] Additional AI provider integrations
- [ ] Enhanced multi-user collaboration features
- [ ] Plugin system for custom agents
- [ ] Mobile-responsive web interface improvements