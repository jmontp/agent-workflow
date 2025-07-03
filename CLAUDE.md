# CLAUDE.md

This file provides comprehensive guidance to Claude Code (claude.ai/code) when working with this repository. It serves as the main navigation guide for the entire AI Agent TDD-Scrum Workflow system.

## Repository Overview

This is the **AI Agent TDD-Scrum Workflow** orchestration framework - a comprehensive system for coordinating AI agents in software development with Human-in-the-Loop oversight. The repository contains a complete, unified implementation with modern Python packaging standards and a clean, consolidated architecture.

## Project Status

**PRODUCTION READY**: Complete implementation with comprehensive testing, documentation, and compliance features. The system has achieved government audit compliance with 95%+ test coverage across critical modules.

## Repository Structure

### 🏗️ Unified Architecture Design

The repository implements a modern, unified Python package architecture:

**Main Package** (`agent_workflow/`):
- Clean, standards-compliant package structure
- CLI interface with comprehensive command system (`agent-orch`/`aw` commands)
- Modular core components (orchestrator, state machine, storage)
- Specialized AI agents with security controls
- Advanced context management and token calculation
- Professional integration points and PyPI distribution
- **See `agent_workflow/CLAUDE.md` for detailed package documentation**

**Legacy Support** (`lib/`):
- Minimal legacy modules for backward compatibility
- Multi-project coordination utilities
- Legacy Discord bot implementations

### 📁 Root Directory Organization

```
agent-workflow/
├── 🐍 Core Implementation
│   ├── agent_workflow/              # Unified Python package
│   │   ├── CLAUDE.md                # Package documentation and architecture
│   │   ├── __init__.py              # Package entry point with core exports
│   │   ├── orchestrator.py          # Simple orchestrator runner
│   │   ├── cli/                     # Command-line interface (12 commands)
│   │   │   ├── main.py              # Primary CLI entry point (agent-orch/aw)
│   │   │   ├── init.py              # Global environment initialization
│   │   │   ├── project.py           # Project registration and management
│   │   │   ├── orchestrator.py      # Orchestrator control commands
│   │   │   ├── setup.py             # Integration setup (Discord, AI)
│   │   │   ├── info.py              # System information and diagnostics
│   │   │   ├── migrate.py           # Migration from git-clone installs
│   │   │   ├── web.py               # Web interface management
│   │   │   ├── dev.py               # Development tools and utilities
│   │   │   ├── config.py            # Configuration management
│   │   │   └── utils.py             # CLI utilities and helpers
│   │   ├── core/                    # Core orchestration components
│   │   │   ├── orchestrator.py      # Central coordination engine
│   │   │   ├── state_machine.py     # Finite state machine
│   │   │   ├── models.py            # Project, Epic, Story, Sprint models
│   │   │   ├── storage.py           # File-based persistence
│   │   │   └── project_storage.py   # Project-specific storage
│   │   ├── agents/                  # AI agent implementations
│   │   │   ├── code_agent.py        # Implementation and refactoring
│   │   │   ├── design_agent.py      # Architecture and specifications
│   │   │   ├── qa_agent.py          # Testing and quality validation
│   │   │   ├── data_agent.py        # Analysis and reporting
│   │   │   └── mock_agent.py        # Testing and development
│   │   ├── context/                 # Advanced context management system
│   │   │   ├── manager.py           # Context manager
│   │   │   ├── cache.py             # Context caching
│   │   │   ├── filter.py            # Context filtering
│   │   │   ├── compressor.py        # Context compression
│   │   │   └── index.py             # Context indexing
│   │   ├── config/                  # Configuration management
│   │   │   ├── schema.py            # Configuration validation
│   │   │   └── templates.py         # Configuration templates
│   │   ├── security/                # Security framework
│   │   │   └── tool_config.py       # Agent tool access control
│   │   ├── integrations/            # External integrations
│   │   │   ├── discord/             # Discord bot integration
│   │   │   └── claude/              # AI service integration
│   │   └── templates/               # Project templates
│   └── lib/                         # Legacy support modules (18 modules)
│       ├── multi_project_*.py       # Multi-project coordination utilities
│       ├── state_broadcaster.py     # Real-time state updates
│       └── token_calculator.py      # AI token usage optimization
│
├── 🔧 Build System & Configuration
│   ├── pyproject.toml              # Modern Python packaging configuration
│   ├── setup.py                    # Legacy setup (backward compatibility)
│   ├── requirements.txt            # Production dependencies
│   ├── pytest.ini                 # Test configuration
│   └── Makefile                    # Development automation (40+ targets)
│
├── 📚 Documentation System
│   ├── docs_src/                   # MkDocs documentation source (comprehensive)
│   │   ├── CLAUDE.md               # Documentation architecture overview
│   │   ├── STYLE_GUIDE.md          # Content standards and formatting guide
│   │   ├── getting-started/        # Installation and setup guides (4 files)
│   │   ├── user-guide/            # Command reference and workflows (13 files)
│   │   ├── concepts/               # Core system concepts (3 files)
│   │   ├── architecture/           # System design and specifications (16 files)
│   │   ├── advanced/               # Deep technical content (11 files)
│   │   ├── planning/               # UI/UX design and roadmaps (7 files)
│   │   ├── development/            # API reference and contributing (4 files)
│   │   ├── deployment/             # Production deployment guides (5 files)
│   │   ├── templates/              # Documentation templates (6 files)
│   │   ├── archive/compliance/     # Government audit compliance (22 reports)
│   │   ├── stylesheets/            # Custom CSS styling (3 files)
│   │   ├── js/                     # Custom JavaScript enhancements (3 files)
│   │   └── images/                 # Documentation assets and screenshots
│   ├── mkdocs.yml                 # MkDocs configuration (advanced Material theme)
│   └── README.md                   # Quick start guide
│
├── 🧪 Testing Infrastructure
│   ├── tests/                      # Comprehensive test suite (99+ files)
│   │   ├── unit/                   # Unit tests (77 files, 95%+ coverage)
│   │   ├── integration/            # Integration tests (15+ files)
│   │   │   ├── test_multi_project_backend.py     # Backend API testing
│   │   │   ├── test_project_switching.py         # Project context switching
│   │   │   ├── test_chat_isolation.py            # Chat isolation validation
│   │   │   ├── test_responsive_design.py         # Mobile responsiveness
│   │   │   ├── run_multi_project_tests.py        # Comprehensive test runner
│   │   │   ├── validate_multi_project_system.py  # Live system validation
│   │   │   └── README_MULTI_PROJECT_TESTS.md     # Test suite documentation
│   │   ├── performance/            # Performance benchmarks
│   │   ├── security/               # Security validation
│   │   ├── acceptance/             # User acceptance tests
│   │   ├── regression/             # Regression test suite
│   │   ├── edge_cases/             # Edge case validation
│   │   └── mocks/                  # Professional mock infrastructure
│   └── coverage.json              # Coverage analysis data
│
├── 🛠️ Development Tools
│   ├── tools/                      # Specialized development utilities
│   │   ├── compliance/             # Government audit compliance monitoring
│   │   │   ├── audit_compliance_tracker.py  # Real-time compliance dashboard
│   │   │   └── monitor_compliance.py        # Lightweight compliance monitoring
│   │   ├── coverage/               # Test coverage analysis and validation
│   │   │   ├── analyze_coverage.py          # Coverage gap analysis
│   │   │   ├── test_runner.py               # Validation without external deps
│   │   │   ├── validate_tdd.py              # TDD workflow validation
│   │   │   ├── validate_test_preservation.py # Test preservation checks
│   │   │   └── coverage_analysis_global_orchestrator.py # Targeted analysis
│   │   ├── documentation/          # Automated API documentation generation
│   │   │   └── generate_api_docs.py         # AST-based doc generation (Markdown/OpenAPI)
│   │   └── visualizer/             # Real-time web-based state visualization
│   │       ├── app.py               # Flask/SocketIO web application with multi-project support
│   │       ├── CLAUDE.md            # Comprehensive visualizer documentation
│   │       ├── MULTI_PROJECT_API.md # Multi-project backend API specification
│   │       ├── PROJECT_CHAT_ISOLATION.md # Chat isolation implementation guide
│   │       ├── interface_configs.json # Project interface configuration
│   │       ├── static/              # Frontend assets (CSS, JS)
│   │       │   ├── css/discord-chat.css     # Discord-style chat interface
│   │       │   ├── js/discord-chat.js       # Chat functionality with isolation
│   │       │   ├── js/project-manager.js    # Project switching and management
│   │       │   └── visualizer.js            # Main state visualization engine
│   │       ├── templates/           # HTML templates with real-time updates
│   │       │   └── index.html       # Main interface with responsive design
│   │       ├── test_multi_project_api.py    # API endpoint testing
│   │       └── test_project_isolation.html  # Chat isolation test interface
│   └── scripts/                    # Main executable entry points (documented in scripts/CLAUDE.md)
│       ├── orchestrator.py         # Single-project orchestrator with TDD support
│       ├── multi_project_orchestrator.py  # Multi-project coordination system
│       └── CLAUDE.md               # Comprehensive scripts documentation
│
├── 🚀 Installation & Deployment
│   ├── install.sh                  # One-click installation script
│   └── orch-config.yaml           # Orchestration configuration
│
└── 📋 Project Planning & Compliance
    ├── Strategic Planning Documents (25+ files)
    │   ├── IMPLEMENTATION_ROADMAP.md
    │   ├── ARCHITECTURE_SPECIFICATIONS.md
    │   └── UI_PORTAL_IMPLEMENTATION.md
    └── Compliance Documentation
        ├── CI_CD_INTEGRATION.md
        ├── DOCUMENTATION_OPTIMIZATION.md
        └── CONFIGURATION_SCHEMAS.md
```

## 🔧 Build System & Configuration

### Modern Python Packaging (`pyproject.toml`)
- **Package Name**: `agent-workflow` (v1.0.0)
- **Python Support**: 3.8+ (tested on 3.8-3.12)
- **Build System**: setuptools with modern `pyproject.toml` configuration
- **CLI Entry Points**: `agent-orch` and `aw` commands with 10 subcommands
- **Dependencies**: 15+ production dependencies with version constraints
- **Optional Features**: `dev`, `docs`, `web`, `ai` dependency groups
- **Code Quality**: Black, flake8, mypy, pytest configuration
- **Type Checking**: Full mypy configuration with strict typing

### Development Automation (`Makefile`)
The Makefile provides 40+ targets organized into categories:

**Setup & Installation**:
- `make install` - Install dependencies
- `make setup` - Complete project setup  
- `make dev-setup` - Development environment

**Testing** (8 comprehensive targets):
- `make test` - Run comprehensive test suite
- `make test-unit` - Unit tests only
- `make test-integration` - Integration tests
- `make test-security` - Security validation
- `make test-performance` - Performance benchmarks
- `make test-ci` - CI/CD optimized suite

**Code Quality**:
- `make lint` - Linting with flake8 and mypy
- `make format` - Code formatting with black
- `make validate` - Comprehensive validation

**Documentation**:
- `make docs` - Build and serve MkDocs
- `make serve-docs` - Local documentation server
- `make build-docs` - Static documentation build

### Configuration Files

**Core Configuration**:
- `orch-config.yaml` - Multi-project orchestration settings
- `pytest.ini` - Comprehensive test configuration with async support
- `requirements.txt` - Production dependencies with version constraints
- `mkdocs.yml` - Professional documentation configuration

**Security & Quality**:
- Black configuration in `pyproject.toml` (line-length: 88)
- MyPy strict typing configuration
- Pytest markers for test categorization
- Coverage reporting configuration

## 🐍 Core System Architecture

### Orchestration Engine
- **Main CLI Interface** (`agent_workflow/cli/main.py`): Primary entry point with `agent-orch`/`aw` commands
- **Core Orchestrator** (`agent_workflow/core/orchestrator.py`): Central coordination engine
- **State Machine** (`agent_workflow/core/state_machine.py`): Finite state machine with strict transitions
- **Legacy Scripts** (`scripts/`): Legacy orchestrator scripts for backward compatibility
- **Resource Management** (`lib/resource_scheduler.py`): Agent pool and resource management

### AI Agent System
- **Specialized Agents** (`agent_workflow/agents/`):
  - **Design Agent** (`design_agent.py`): Architecture and technical specifications
  - **Code Agent** (`code_agent.py`): Implementation and refactoring
  - **QA Agent** (`qa_agent.py`): Testing and quality validation
  - **Data Agent** (`data_agent.py`): Analysis and reporting
  - **Mock Agent** (`mock_agent.py`): Testing and development
- **Agent Memory** (`lib/agent_memory.py`): Context-aware agent memory system
- **Agent Pool** (`lib/agent_pool.py`): Dynamic agent lifecycle management

### Context Management System
- **Context Manager** (`agent_workflow/context/manager.py`): Advanced context handling
- **Context Cache** (`agent_workflow/context/cache.py`): Efficient context caching
- **Context Filter** (`agent_workflow/context/filter.py`): Context relevance filtering
- **Context Compressor** (`agent_workflow/context/compressor.py`): Context size optimization
- **Context Index** (`agent_workflow/context/index.py`): Context search and retrieval
- **Background Processing** (`agent_workflow/context/background.py`): Async context operations
- **Learning System** (`agent_workflow/context/learning.py`): Context adaptation

### Security & Control
- **Agent Tool Config** (`agent_workflow/security/tool_config.py`): Command access control
- **Multi-Project Security** (`lib/multi_project_security.py`): Cross-project isolation
- **Token Calculator** (`lib/token_calculator.py`): AI token usage optimization

### Integration Layer
- **Discord Integration** (`agent_workflow/integrations/discord/`): Discord bot and command interface
- **Claude Integration** (`agent_workflow/integrations/claude/`): AI service integration
- **Web Interface** (`tools/visualizer/`): Discord-style web interface with real-time updates
- **Cross-Project Intelligence** (`lib/cross_project_intelligence.py`): Knowledge sharing

### Data & Storage
- **Data Models** (`agent_workflow/core/models.py`): Epic, Story, Sprint, TDD entities
- **Project Storage** (`agent_workflow/core/storage.py`): File-based persistence
- **Project-Specific Storage** (`agent_workflow/core/project_storage.py`): Project data management
- **State Broadcaster** (`lib/state_broadcaster.py`): Real-time state updates

## 📋 CLI Command System

The system provides comprehensive CLI commands via `agent-orch` or `aw`:

### Project Management
- `init` - Initialize orchestration environment
- `register-project` - Register new project repository
- `projects` - List and manage projects with multi-project support
- `project-switch` - Switch active project context
- `project-info` - Get detailed project information and status

### Orchestration Control
- `start` - Start orchestration engine (single or multi-project mode)
- `stop` - Stop orchestration gracefully with project cleanup
- `status` - Check system status across all projects
- `restart` - Restart orchestration with state preservation

### Multi-Project Management
- `multi-project-start` - Start multi-project orchestration daemon
- `multi-project-status` - Get status of all registered projects
- `multi-project-stop` - Stop multi-project orchestration
- `project-discover` - Discover and register projects automatically

### Web Interface Control
- `web` - Start web visualizer interface
- `web-stop` - Stop web interface
- `web-status` - Check web interface status
- `web-restart` - Restart web interface with multi-project support

### Configuration & Setup
- `setup-discord` - Configure Discord integration
- `setup-api` - Configure AI API integration
- `configure` - Interactive configuration wizard
- `config` - Configuration management commands

### Development Tools
- `dev check-coverage` - Analyze test coverage of the codebase
- `dev check-compliance` - Check government audit compliance status
- `dev generate-docs` - Generate API documentation from source code

### System Information
- `version` - Display version information
- `health` - System health check with project status
- `migrate-from-git` - Migrate from git-clone installation

## 🔧 Refactoring and Architectural Decisions

### Major Refactoring Completed (Phase 1-4)

The repository has undergone comprehensive refactoring to achieve a modern, unified architecture:

**Phase 1: Architectural Unification**
- Consolidated dual architecture into single `agent_workflow` package
- Migrated all core functionality from `lib/` to proper package structure
- Unified data models and interfaces

**Phase 2: Test and Documentation Consolidation**
- Reduced test files from 99+ to 47 while maintaining 95%+ coverage
- Streamlined documentation with dual-stream architecture
- Preserved all compliance achievements and quality metrics

**Phase 3: Enhanced Tooling**
- Integrated development tools into CLI (`aw dev` commands)
- Unified configuration system with single `config.yml`
- Updated web visualizer for new architecture

**Phase 4: Final Validation and Documentation**
- Comprehensive system validation completed
- Updated all documentation to reflect unified architecture
- Production readiness confirmed

### Key Architectural Changes

1. **Unified Package Structure**: Replaced dual architecture with single `agent_workflow` package
2. **CLI-First Experience**: Enhanced CLI with integrated development tools
3. **Consolidated Configuration**: Single configuration file replacing multiple configs
4. **Modern Import Patterns**: Proper Python package imports throughout
5. **Legacy Support**: Minimal `lib/` directory for backward compatibility

### Development Workflow

- **Primary Interface**: Use `aw` CLI for all operations
- **Package Development**: All new code goes in `agent_workflow/` package
- **Testing**: Comprehensive test suite with real-time validation
- **Documentation**: Professional MkDocs system with 74+ pages

## 🧪 Testing & Quality Assurance

### Comprehensive Test Suite (99+ files)
The testing infrastructure achieves 95%+ coverage across critical modules:

**Unit Tests** (`tests/unit/` - 77 files):
- Individual module testing with comprehensive mocking
- Security validation for all agent restrictions
- Context management system validation
- State machine transition testing

**Integration Tests** (`tests/integration/` - 9 files):
- Cross-module interaction testing
- Discord bot integration validation
- Multi-project orchestration testing
- End-to-end workflow validation

**Specialized Testing**:
- **Performance Tests**: Benchmark critical operations
- **Security Tests**: Validate agent restrictions and access controls
- **Acceptance Tests**: User scenario validation
- **Regression Tests**: Prevent functionality degradation
- **Edge Case Tests**: Boundary condition validation

### Professional Mock Infrastructure (`tests/mocks/`)
- **Discord Mocks**: Complete Discord API simulation
- **GitHub Mocks**: Repository interaction simulation
- **WebSocket Mocks**: Real-time communication testing
- **Async Fixtures**: Comprehensive async test support

### Coverage & Compliance
- **Government Audit Compliance**: Achieved Tier 3 compliance
- **Real-time Coverage Monitoring**: Continuous coverage tracking
- **Compliance Dashboard**: Live compliance status
- **Achievement Documentation**: 19 preserved compliance records

## 🚀 Installation & Setup

### Quick Installation
```bash
# One-click installation (recommended)
curl -sSL https://raw.githubusercontent.com/jmontp/agent-workflow/main/install.sh | bash

# Or via pip
pip install agent-workflow

# Initialize environment
agent-orch init

# Register a project
agent-orch register-project /path/to/project

# Start orchestration
agent-orch start
```

### Development Setup
```bash
# Clone repository
git clone https://github.com/jmontp/agent-workflow.git
cd agent-workflow

# Setup development environment
make dev-setup

# Run comprehensive validation
make validate-system
```

## 💻 Development Commands

### Core Orchestration
```bash
# Modern CLI interface
agent-orch start                 # Start orchestration engine
agent-orch status                # Check system status
agent-orch projects              # List registered projects

# Script interface (see scripts/CLAUDE.md for comprehensive documentation)
python scripts/orchestrator.py          # Single-project orchestrator with TDD support
python scripts/multi_project_orchestrator.py --interactive  # Multi-project coordination
python scripts/multi_project_orchestrator.py --daemon       # Multi-project daemon mode

# Discord bot integration
python lib/discord_bot.py               # Start Discord bot
python lib/multi_project_discord_bot.py # Multi-project Discord bot
```

### Testing & Validation
```bash
# Comprehensive testing
make test                        # Run all tests
make test-unit                   # Unit tests only (77 files)
make test-integration           # Integration tests (9 files)
make test-security              # Security validation
make test-performance           # Performance benchmarks

# Direct pytest commands
pytest tests/ -v                # Full test suite with verbose output
pytest tests/unit/ -m "not slow"  # Fast unit tests only
pytest tests/integration/ --tb=short  # Integration tests with short traceback

# Coverage analysis
python tools/coverage/analyze_coverage.py       # Generate coverage report
python tools/coverage/test_runner.py            # Advanced test runner
python tools/coverage/validate_tdd.py           # TDD validation
```

### Code Quality & Compliance
```bash
# Code formatting and quality
make format                      # Format with black and isort
make lint                        # Lint with flake8 and mypy
make validate                    # Comprehensive validation

# Compliance monitoring
python tools/compliance/monitor_compliance.py   # Live compliance tracking
python tools/compliance/audit_compliance_tracker.py  # Audit compliance

# Security validation
python tests/unit/test_agent_tool_config.py     # Agent security validation
python tests/security/test_tdd_security.py      # Security test suite
```

### Documentation & API
```bash
# Documentation system
make docs                        # Build and serve documentation
make serve-docs                  # Local documentation server
mkdocs serve                     # Direct MkDocs serving
mkdocs build                     # Build static documentation

# API documentation
python tools/documentation/generate_api_docs.py  # Generate API docs
```

### Development Utilities

#### Development Tools Suite (`tools/`)
Comprehensive set of specialized utilities organized by category:

```bash
# Compliance Monitoring
python tools/compliance/audit_compliance_tracker.py   # Real-time compliance dashboard
python tools/compliance/monitor_compliance.py         # Lightweight compliance monitoring

# Coverage Analysis & Validation
python tools/coverage/analyze_coverage.py             # Coverage gap analysis
python tools/coverage/test_runner.py                  # System validation without deps
python tools/coverage/validate_tdd.py                 # TDD workflow validation
python tools/coverage/validate_test_preservation.py   # Test preservation checks
python tools/coverage/coverage_analysis_global_orchestrator.py  # Targeted analysis

# API Documentation Generation
python tools/documentation/generate_api_docs.py --format markdown  # Markdown docs
python tools/documentation/generate_api_docs.py --format openapi   # OpenAPI spec
python tools/documentation/generate_api_docs.py --include-private  # Include privates

# Real-time State Visualization
cd tools/visualizer && python app.py                  # Web-based state dashboard
cd tools/visualizer && python app.py --host 0.0.0.0 --port 8080  # Custom host/port
```

#### System Validation
```bash
# System validation
make quick-check                 # Emergency validation
make production-check           # Production readiness validation
make ci-simulation              # Simulate CI/CD pipeline
```

**Note**: All tools in `tools/` directory include built-in help via `--help` flag and comprehensive documentation in `tools/CLAUDE.md`

## 📚 Documentation System

### MkDocs Professional Configuration
The documentation system uses MkDocs Material with:
- **74 navigation pages** organized in 9 sections
- **Professional theme** with Inter/JetBrains Mono fonts
- **Advanced features**: search, navigation, code highlighting
- **Mermaid diagrams** with zoom functionality
- **GitHub integration** with edit/view actions
- **Analytics support** with cookie consent
- **Version management** with mike

### Documentation Structure
- **Getting Started**: Installation, quick start, configuration
- **User Guide**: Commands, workflows, troubleshooting (9 guides)
- **Architecture**: System design, context management, parallel TDD (11 specs)
- **Advanced Topics**: Detailed technical implementation (10 topics)
- **Development**: API reference, contributing, testing (3 guides)
- **Deployment**: Discord setup, production deployment (4 guides)
- **Planning**: UI portal, websocket API, user journeys (6 specs)

## ⚙️ Configuration Management

### Multi-Project Configuration (`orch-config.yaml`)
- **Global Settings**: Resource limits, scheduling, security
- **Project Registration**: 12 registered projects with individual settings
- **Resource Management**: CPU, memory, disk limits per project
- **Security Controls**: Project isolation, access controls
- **Work Hours**: Configurable working hours per project

### Environment Configuration
Required environment variables:
- `DISCORD_BOT_TOKEN` - Discord bot authentication
- Optional: `GOOGLE_ANALYTICS_KEY` - Documentation analytics

### Dependencies
**Production Dependencies** (from `requirements.txt`):
- Discord.py 2.3.0+ - Discord integration
- PyGithub 1.59.0+ - GitHub API integration
- PyYAML 6.0+ - Configuration management
- websockets 11.0+ - WebSocket communication
- aiohttp 3.8.0+ - Async HTTP client
- Flask 2.3.0+ - Web dashboard
- pytest 7.4.0+ - Testing framework
- mkdocs-material 9.4.0+ - Documentation

## 🔒 Security & Agent Control

### Agent Security Architecture
The system implements comprehensive security controls:

**Agent Types & Restrictions**:
- **Orchestrator Agent**: Full system access (with safety limits)
- **Code Agent**: File editing, git operations, testing
- **Design Agent**: Read-only access, documentation creation
- **QA Agent**: Testing tools only, no code modification
- **Data Agent**: Data processing, analysis tools only

**Security Features**:
- Command access control per agent type
- Tool restriction enforcement via Claude Code CLI flags
- Multi-project isolation with resource limits
- Comprehensive security testing (95+ test cases)

## 🎯 Important Notes for Claude Code

### Repository Navigation
1. **Primary Implementation**: Most functionality in `lib/` directory (42 modules)
2. **Modern Interface**: CLI commands in `agent_workflow/cli/` (8 commands)  
3. **Core Scripts**: Essential executables in `scripts/` (2 files)
4. **Documentation**: Comprehensive guides in `docs_src/` (74+ pages)
5. **Testing**: Extensive test suite in `tests/` (99+ files)

### Development Workflow
1. **Setup**: Use `make dev-setup` for complete environment
2. **Testing**: Always run `make test-unit` before changes
3. **Validation**: Use `make validate` for comprehensive checks
4. **Security**: Run security tests after any agent-related changes
5. **Documentation**: Update docs in `docs_src/` as needed

### Key Patterns
- **Dual Architecture**: Both modern package and legacy library
- **Multi-Project Support**: Single orchestrator, multiple projects
- **HITL Workflow**: Human approval for strategic decisions
- **State Management**: Finite state machine with strict transitions
- **Security First**: Comprehensive agent access controls
- **Test-Driven**: 95%+ coverage with professional test infrastructure

### System Capabilities
- **Production Ready**: Complete implementation with compliance
- **Scalable**: Multi-project orchestration with resource management
- **Secure**: Government audit compliance achieved
- **Extensible**: Plugin architecture for new agents and integrations
- **Observable**: Real-time monitoring and compliance dashboards with comprehensive development tools

This repository represents a complete, production-ready AI agent orchestration framework with comprehensive documentation, testing, and compliance features.

## Dependencies

Install Python dependencies:
```bash
pip install discord.py pygithub pyyaml pytest pytest-asyncio mkdocs-material
```

Core dependencies: `discord.py`, `pygithub`, `pyyaml`, `pytest`, `mkdocs-material`

## Configuration

### Required Environment Variables
- `DISCORD_BOT_TOKEN`: Required for Discord bot functionality

### AI Integration
- **Claude Code**: The system integrates with Claude Code CLI for AI capabilities
- **Agent Security**: Each agent type uses restricted Claude clients with tool access controls
- **Automatic Detection**: System automatically detects if Claude Code is available
- **Graceful Fallback**: Uses placeholder implementations when Claude Code is not available

### Configuration Files
- YAML project configuration files define orchestration modes and project paths
- Individual project directories contain `.orch-state/status.json` for runtime state
- Agent security profiles defined in `lib/agent_tool_config.py`

## HITL Command System

The system implements a finite state machine with these key commands:

### Project Management
- `/project register <path> [name]` - Register new project repository
- `/epic "<description>"` - Define high-level initiatives with persistent storage
- `/backlog view|add_story|prioritize` - Backlog management with file persistence
- `/sprint plan|start|status|pause|resume` - Sprint lifecycle management

### Workflow Control  
- `/approve [ID]` - Approve queued tasks
- `/request_changes "<description>"` - Request modifications on PRs
- `/state` - Interactive state inspection with diagram visualization

### Data Persistence
- All project management data stored in project repositories under `.orch-state/`
- Epics, stories, and sprints persisted as JSON files
- Architecture decisions and best practices maintained as markdown
- Complete audit trail through git version control

Commands are validated against current state - invalid commands return helpful error messages with suggested alternatives.

## Implementation Details

### Agent System
- **Complete Implementation**: All agents are fully implemented with sophisticated capabilities
- **Security Model**: Command access control enforced via Claude Code CLI flags (`--allowedTools`/`--disallowedTools`)
- **Agent Types**: Orchestrator (full access), CodeAgent (edit+commit), DesignAgent (read-only), QAAgent (test-only), DataAgent (analysis-only)
- **Pattern**: All agents inherit from `BaseAgent` with standardized `async def run(task, dry_run=False)` interface
- **Specializations**: DesignAgent (architecture), CodeAgent (implementation), QAAgent (testing), DataAgent (analysis)

### Security Architecture
- **Command Access Control**: Each agent type has specific tool restrictions
- **Principle of Least Privilege**: Agents can only access tools necessary for their function
- **Automatic Enforcement**: Security boundaries applied transparently via Claude CLI
- **Comprehensive Testing**: All security restrictions validated in test suite

### Testing Framework
- **Comprehensive Test Suite**: Unit, integration, and E2E tests with >90% coverage target
- **Security Testing**: Agent tool access control validation in `tests/unit/test_agent_tool_config.py`
- **State Machine Testing**: Table-driven tests for all transitions and error conditions
- **Mocked Dependencies**: Discord, Claude Code, and GitHub APIs mocked for testing
- **Test Categories**: Unit tests in `tests/unit/`, integration tests in `tests/integration/`

### Discord Integration
- **Full Slash Command Support**: All HITL commands implemented with interactive UI
- **State Visualization**: Interactive buttons for state inspection and command discovery
- **Project Channels**: Automatic channel creation per project with naming convention
- **Error Handling**: Comprehensive error messages with helpful hints and suggestions

### Multi-Project Orchestration
The system provides comprehensive multi-project orchestration capabilities with advanced coordination and isolation features:

#### Core Multi-Project Features
- **Project Isolation**: Complete separation of project contexts, states, and chat history
- **Concurrent Execution**: Multiple projects can run simultaneously with independent workflows
- **Resource Management**: Per-project resource limits (CPU, memory, agents) with intelligent scheduling
- **Cross-Project Intelligence**: Optional knowledge sharing between related projects
- **Web-Based Management**: Full-featured web interface for project switching and monitoring

#### Project Configuration Modes
Projects are defined in YAML configuration with multiple orchestration modes:
- **blocking**: Requires human approval for all strategic decisions
- **partial**: Executes with quarantined output for review  
- **autonomous**: Full execution with monitoring and alerts
- **collaborative**: Multi-user project support with role-based permissions

#### Web Interface Integration
- **Discord-Style Chat**: Project-specific chat interfaces with complete isolation
- **Real-Time State Visualization**: Live workflow state diagrams with project switching
- **Project Management**: Registration, configuration, and monitoring through web UI
- **Session Management**: User sessions tracked across projects with proper isolation
- **WebSocket Room Management**: Project-specific real-time communication channels

#### Backend API Architecture
Comprehensive REST API for multi-project management:
- **Project Discovery**: Automatic detection and registration of projects
- **State Management**: Project-specific workflow state handling
- **Chat Isolation**: Project-scoped chat history and command processing  
- **Context Switching**: Seamless project context switching with state preservation
- **Resource Monitoring**: Real-time resource usage and performance metrics

#### Integration Testing
Complete integration test suite validates multi-project functionality:
- **Backend API Tests**: All endpoints and data integrity validation
- **Project Switching Tests**: Context switching and state preservation
- **Chat Isolation Tests**: Project-specific communication boundaries
- **Responsive Design Tests**: Mobile and accessibility compliance
- **System Validation**: Live system testing and health monitoring

## Documentation Strategy

### MkDocs Structure
The documentation is organized in `docs_src/` for MkDocs build system:

```
docs_src/
├── index.md                    # Project overview
├── getting-started/
│   ├── installation.md         # Setup instructions
│   └── quick-start.md          # Getting started guide
├── user-guide/
│   ├── hitl-commands.md        # Command reference
│   ├── state-machine.md        # Workflow states
│   ├── user-profile.md         # User configuration
│   └── workflow-sequences.md   # Sequence diagrams
├── architecture/
│   ├── overview.md             # System architecture
│   ├── security.md             # Security model and agent restrictions
│   ├── component.md            # Component design
│   ├── container.md            # Container architecture
│   ├── context.md              # System context
│   └── code.md                 # Code organization
├── development/
│   └── testing.md              # Testing strategy
└── deployment/                 # Deployment guides
```

### Documentation Architecture & Strategy

The `docs_src/` directory implements a comprehensive MkDocs-based documentation system with professional standards:

#### Documentation Organization Strategy
- **User Journey Focus**: Content organized by user experience level and needs
- **Progressive Disclosure**: Information complexity increases with user expertise
- **Multi-Audience Support**: Separate sections for users, developers, architects, and compliance
- **Task-Oriented Structure**: Documentation organized around what users want to accomplish

#### MkDocs Build System Features
- **Material Design Theme**: Professional, responsive design with advanced navigation
- **Enhanced Functionality**: Mermaid diagrams, code highlighting, search, and image zoom
- **Performance Optimization**: Minification, instant loading, and progressive enhancement
- **Accessibility Standards**: Screen reader support, mobile-responsive design
- **Analytics Integration**: Google Analytics with user feedback collection

#### Documentation Categories Overview
1. **Getting Started** (4 files): Installation, quick start, configuration
2. **User Guide** (13 files): Commands, workflows, integration examples, troubleshooting
3. **Core Concepts** (3 files): System overview, security model
4. **Architecture** (16 files): Detailed technical specifications and design decisions
5. **Advanced Topics** (11 files): Deep technical content for power users
6. **Planning & Design** (7 files): UI/UX specifications and development roadmaps
7. **Development** (4 files): API reference, contributing guidelines, testing
8. **Deployment** (5 files): Production setup, Discord configuration, GitHub Pages
9. **Templates** (6 files): Standardized documentation templates
10. **Archive/Compliance** (22 files): Government audit reports and compliance certificates

#### Content Standards & Quality Control
- **Style Guide**: Comprehensive formatting and writing standards (`STYLE_GUIDE.md`)
- **Template System**: Reusable templates for consistent content creation
- **Visual Standards**: Consistent icon usage, diagram styling, and formatting
- **Quality Checklist**: Pre-publication validation for content, visual, UX, and technical quality
- **Cross-Reference System**: Strategic linking for optimal user navigation

#### Custom Enhancements
- **JavaScript**: Mermaid diagram zoom, universal search, enhanced navigation
- **CSS**: Professional color schemes, responsive design, accessibility features
- **Macros**: Python-based content generation and automation
- **Images**: Organized visual assets with proper alt text and responsive sizing

**Detailed Documentation**: See `/mnt/c/Users/jmontp/Documents/workspace/agent-workflow/docs_src/CLAUDE.md` for complete documentation architecture overview.

## Agent Security Profiles

### Orchestrator Agent
- **Access Level**: Full system access
- **Allowed**: All tools including rm, git commit, git push
- **Restricted**: Still blocks dangerous system commands (sudo, format, dd)
- **Use Case**: System-level workflow management and coordination

### Code Agent
- **Access Level**: Code modification and version control
- **Allowed**: File editing, git add/commit, testing tools, package management
- **Restricted**: File deletion, git push, system administration
- **Use Case**: Feature implementation, bug fixes, code refactoring

### Design Agent  
- **Access Level**: Read-only analysis and documentation
- **Allowed**: File reading, documentation creation, web research
- **Restricted**: Code editing, version control, system commands
- **Use Case**: Architecture design, technical specifications, code review

### QA Agent
- **Access Level**: Testing and quality analysis only
- **Allowed**: Test execution, code quality tools, coverage analysis
- **Restricted**: Code modification, version control, file creation
- **Use Case**: Test creation, quality validation, coverage reporting

### Data Agent
- **Access Level**: Data processing and analysis
- **Allowed**: Data file access, notebook creation, visualization tools
- **Restricted**: Source code modification, version control
- **Use Case**: Data analysis, reporting, metrics visualization

## Security Guidelines for Claude Code Integration

When working with this repository, Claude Code should be aware of:

1. **Agent Context**: If working within an agent context, tool access is automatically restricted
2. **Security Boundaries**: Different agent types have different permissions
3. **Test Requirements**: All security-related changes must include tests
4. **Documentation Updates**: Security changes require documentation updates

## Repository Organization & Cleanup

### Clean Structure Achievement
This repository has undergone comprehensive cleanup achieving:
- **80% file reduction**: 150+ → 31 files in root directory
- **Organized utilities**: All development tools moved to `tools/` with categorical organization
- **Professional structure**: Clear separation of executables, utilities, tests, and documentation
- **Preserved achievements**: All compliance documents archived in `docs_src/archive/compliance/`

### File Location Guide
- **Main executables**: `scripts/` (2 core scripts + documentation - see `scripts/CLAUDE.md`)
- **Development utilities**: `tools/` (organized by function)
- **Test suite**: `tests/` (99+ comprehensive test files)
- **Documentation**: `docs_src/` (MkDocs source + archived achievements)
- **Core libraries**: `lib/` (42 modules)

### Utility Tools Organization
- **Coverage/Testing**: `tools/coverage/` - Analysis, validation, test running utilities
- **Compliance**: `tools/compliance/` - Government audit monitoring and tracking
- **Documentation**: `tools/documentation/` - API documentation generation
- **Visualization**: `tools/visualizer/` - Web-based state visualization interface

## Automatic Dependency Tracking System

The repository includes an intelligent dependency tracking system in `tools/dependencies/` that maintains consistency across code, tests, and documentation:

### Key Features
- **Automatic Mapping**: Identifies relationships between code, tests, and documentation
- **Real-time Monitoring**: Watches for file changes and suggests updates
- **Convention-based**: Uses naming patterns (e.g., `lib/module.py` → `tests/unit/test_module.py`)
- **Claude Integration**: Designed to work with Claude Code for intelligent updates

### Usage
```bash
# Check dependencies for a file
python3 tools/dependencies/tracker.py --related lib/some_module.py

# Preview what would be updated
python3 tools/dependencies/updater.py lib/some_module.py --dry-run

# Start real-time monitoring
python3 tools/dependencies/watcher.py

# Run initial setup
python3 tools/dependencies/setup.py
```

### Configuration
- **`.dependency-config.yaml`**: Configure update strategies and automation levels
- **`dependencies.yaml`**: Generated dependency map for the entire project
- **Pre-commit hooks**: Automatic validation before commits
- **VS Code integration**: Tasks for quick dependency checking

See `tools/dependencies/README.md` for complete documentation.

## Important Notes for Claude Code

### Navigation & Structure
- **Documentation Location**: Primary docs are in `docs_src/` (MkDocs format)
- **Dependency Tracking**: Use `tools/dependencies/` to identify affected files when making changes
- **Clean Structure**: Repository follows professional organization with tools separated from executables
- **ALWAYS use editable install**: `pip install -e .` to avoid development issues

### Key System Components
- **Security Testing**: Always run `tests/unit/test_agent_tool_config.py` after security changes
- **Agent Restrictions**: Each agent type has specific tool limitations for security
- **State Management**: The system uses finite state machines with strict validation
- **HITL Workflow**: Human approval is required for strategic decisions

### Web Interface & Visualizer (`tools/visualizer/`)
- **Discord Chat**: Fully functional chat interface with slash commands
- **State Diagrams**: Vertical layout with Mermaid diagrams (recently changed from side-by-side)
- **Recent Fixes**: 
  - ✅ Chat send button (fixed missing methods in ChatComponents)
  - ✅ Main page scrolling (changed overflow to auto)
  - ✅ Chat close button (added event handler)
  - ✅ Mermaid diagram font size (increased to 16px)
- **Troubleshooting**: See `tools/visualizer/TROUBLESHOOTING_CHAT.md` for issues

## 🔧 Phase 2 Consolidation Achievements

### Test Suite Consolidation (Epic 2.1) ✅
**Major Achievement**: Successfully reduced test files from 99+ to 47 files (52% reduction)

**Key Consolidations**:
- `test_agent_memory*.py` (4 files) → `test_agent_memory.py` (comprehensive coverage)
- `test_context_manager*.py` (6 files) → `test_context_manager.py` + core files
- `test_discord_bot*.py` (5 files) → `test_discord_bot.py`
- `test_multi_project_security*.py` (6 files) → `test_multi_project_security.py`
- `test_project_storage*.py` (6 files) → `test_project_storage.py`

**Benefits**:
- Simplified maintenance and navigation
- Preserved 95%+ test coverage
- Eliminated redundant coverage/comprehensive variants
- Maintained government audit compliance

### Documentation Consolidation (Epic 2.2) ✅
**Major Achievement**: Streamlined documentation from 62+ scattered files to organized structure

**Key Actions**:
- Deleted 8 summary/report files (AUDIT_COMPLIANCE_ACHIEVEMENT_REPORT.md, etc.)
- Created user-oriented documentation stream: `docs_src/user-guide/visualizer/`
- Created engineering documentation stream: `docs_src/architecture/visualizer/`
- Enhanced CLAUDE.md files with troubleshooting patterns

**New Documentation Structure**:
```
docs_src/
├── user-guide/visualizer/           # Task-oriented user guides
│   ├── index.md                     # Quick start hub
│   └── daily-tasks.md               # Common workflows
├── architecture/visualizer/         # Engineering reference
│   ├── overview.md                  # System architecture
│   └── decisions/                   # Architecture Decision Records
│       └── ADR-001-websocket.md     # WebSocket communication
```

## 🚨 Critical Troubleshooting Guide

### Development Environment Issues

#### 1. **Changes Not Reflecting After Code Updates**
This is the most common issue when developing with this repository.

**Quick Fix**:
```bash
# For package changes not reflecting
pip uninstall -y agent-workflow --break-system-packages
pip install -e . --user --break-system-packages

# For web interface specifically
aw web-stop
lsof -ti:5000 | xargs kill -9 2>/dev/null || true
aw web
# Then hard refresh browser: Ctrl+F5 (Windows/Linux) or Cmd+Shift+R (Mac)
```

**Detailed Solutions**:
- **Package Installation Issues**: See `agent_workflow/CLAUDE.md` → Troubleshooting section
- **Web Interface Issues**: See `tools/visualizer/CLAUDE.md` → Common Issues section
- **Browser Cache**: Always hard refresh or use incognito mode for frontend changes

#### 2. **Web Interface Specific Problems**
- **"Initialization Error" banner**: Element ID mismatches - see `tools/visualizer/CLAUDE.md`
- **Chat not working**: Check browser console for errors, ensure WebSocket connection
- **Can't scroll diagrams**: Check CSS overflow properties
- **Port 5000 in use**: Kill existing process or use `--port` flag

#### 3. **Installation Problems**
- **"Externally managed environment"**: Use `--user --break-system-packages` flags
- **Commands not found**: Add `~/.local/bin` to PATH
- **Import errors**: Ensure editable install with `pip install -e .`

### Quick Debug Checklist

1. ✅ **Is package installed in editable mode?**
   ```bash
   pip show agent-workflow | grep Location
   # Should show your working directory, NOT site-packages
   ```

2. ✅ **Are there processes blocking ports?**
   ```bash
   lsof -i:5000  # Check web interface port
   lsof -i:5001  # Check state broadcaster port
   ```

3. ✅ **Browser cache cleared?**
   - Hard refresh: Ctrl+F5 or Cmd+Shift+R
   - Or use incognito/private window

4. ✅ **Check logs for errors**
   ```bash
   aw web --debug --log-level DEBUG
   ```

### Where to Find More Help

- **Package Issues**: `agent_workflow/CLAUDE.md` - Comprehensive troubleshooting
- **Web Interface**: `tools/visualizer/CLAUDE.md` - Discord interface debugging
- **Test Issues**: Run test scripts in `tools/visualizer/test_*.py`
- **General Structure**: This file (root CLAUDE.md) for repository overview