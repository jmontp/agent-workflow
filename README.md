# AI Agent TDD-Scrum Workflow

A Human-In-The-Loop (HITL) orchestration framework that coordinates multiple specialized AI agents through a Discord interface, following a research-mode Scrum methodology optimized for solo engineers working with AI assistance.

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- Discord Bot Token
- Optional: Anthropic API Key for AI capabilities

### Installation
```bash
# Clone repository
git clone https://github.com/jmontp/agent-workflow.git
cd agent-workflow

# Install dependencies
make install
# or: pip install -r requirements.txt
```

### Configuration
```bash
# Set required environment variable
export DISCORD_BOT_TOKEN="your_discord_bot_token"

# Optional: Set for AI capabilities
export ANTHROPIC_API_KEY="your_anthropic_api_key"
```

### Run
```bash
# Run Discord bot with orchestrator
make run
# or: python lib/discord_bot.py

# Run orchestrator only (no Discord)
make orchestrator
# or: python scripts/orchestrator.py
```

## 📋 Available Commands

The system implements a finite state machine with these Discord slash commands:

- `/epic "<description>"` - Define high-level initiatives
- `/approve [IDs]` - Approve proposed stories or tasks
- `/sprint plan|start|status|pause|resume` - Sprint lifecycle management  
- `/backlog view|add_story|prioritize` - Backlog management
- `/request_changes "<description>"` - Request modifications during review
- `/suggest_fix "<description>"` - Provide hints for blocked tasks
- `/skip_task` - Skip currently blocked task
- `/feedback "<description>"` - Complete sprint retrospective
- `/state` - Interactive state inspection with visualization

## 🏗️ Architecture

### Directory Structure
```
docs/           # Documentation and C4 diagrams
scripts/        # Executable orchestrator
lib/            # Core library code
  ├── agents/   # Specialized AI agents
  ├── state_machine.py  # Workflow state management
  └── discord_bot.py    # Discord interface
tests/          # Comprehensive test suite
```

### Core Components

- **Orchestrator**: Central coordination engine managing multi-project workflows
- **State Machine**: Enforces proper command sequencing through workflow states
- **Agent Library**: Specialized AI agents (Design, Code, QA, Data) with common interface
- **Discord Bot**: Primary HITL interface with slash commands and interactive UI

### Key Features

- **Multi-Project Support**: Orchestrate multiple projects simultaneously
- **HITL Approval Gates**: Human oversight for strategic decisions
- **Interactive State Visualization**: Discord UI for workflow inspection
- **Comprehensive Testing**: Unit, integration, and E2E test coverage
- **Flexible Orchestration**: Blocking, partial, or autonomous execution modes

## 🧪 Testing

```bash
# Run full test suite
make test
pytest tests/

# Run with coverage
make test-coverage

# Run specific test categories
make test-unit          # Unit tests only
make test-integration   # Integration tests only

# Run specific tests
pytest tests/unit/test_state_machine.py -v
```

## 🔧 Development

```bash
# Set up development environment
make dev-setup

# Code formatting
make format

# Linting
make lint

# Clean up generated files
make clean
```

## 📖 Documentation

- [HITL Commands](docs/HITL_COMMANDS.md) - Complete command reference
- [State Machine](docs/command_state_machine.md) - Workflow state specification
- [Sequence Diagrams](docs/sequence_diagram.md) - Interaction patterns
- [C4 Architecture](docs/) - System architecture diagrams
- [Testing Plan](docs/testing-plan.md) - Comprehensive testing strategy

## 🤖 Agent Capabilities

### DesignAgent
- System architecture creation
- Component design and interfaces
- Design review and validation
- Technical specifications

### CodeAgent  
- Feature implementation
- Bug fixing and debugging
- Code refactoring
- Performance optimization

### QAAgent
- Test suite creation
- Test execution and reporting
- Quality validation
- Coverage analysis

### DataAgent
- Data analysis and insights
- Pipeline creation
- Quality validation
- Metrics and reporting

## 🔄 Workflow States

The system enforces a finite state machine:

```
IDLE → BACKLOG_READY → SPRINT_PLANNED → SPRINT_ACTIVE → SPRINT_REVIEW → IDLE
                                           ↓
                                      SPRINT_PAUSED
                                           ↓
                                       BLOCKED
```

Each state allows specific commands, with helpful error messages for invalid transitions.

## 🎛️ Configuration

### Project Configuration
Create YAML configuration files defining projects and orchestration modes:

```yaml
projects:
  - name: "my_project"
    path: "/path/to/project"
    orchestration: "blocking"  # blocking|partial|autonomous
```

### Environment Variables
- `DISCORD_BOT_TOKEN`: Required for Discord integration
- `ANTHROPIC_API_KEY`: Optional for AI agent capabilities
- `HOSTNAME`: Used for Discord channel naming (default: localhost)

## 🚨 Error Handling

The system provides comprehensive error handling:
- Invalid commands show helpful hints
- State validation prevents illegal transitions
- Agent failures trigger escalation workflows
- Comprehensive logging for debugging

## 🤝 Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open Pull Request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- Built for research-mode software development
- Optimized for solo engineers working with AI assistance
- Inspired by Scrum methodology with minimal ceremony
- Designed for maximum development momentum