# Tools Directory Documentation

This directory contains development utilities organized by category to support the AI Agent TDD-Scrum workflow system's development, testing, and monitoring workflows.

## Overview

The tools/ directory provides specialized utilities for:
- **Compliance Monitoring**: Government audit compliance tracking and validation
- **Coverage Analysis**: Test coverage validation and TDD workflow verification  
- **Documentation Generation**: Automated API documentation from source code
- **State Visualization**: Real-time web-based monitoring of workflow states
- **Validation Tools**: Diagram validation and visual consistency checking

## Directory Structure

```
tools/
├── compliance/          # Audit and compliance monitoring tools
│   ├── audit_compliance_tracker.py
│   └── monitor_compliance.py
├── coverage/           # Test coverage analysis and validation tools
│   ├── analyze_coverage.py
│   ├── coverage_analysis_global_orchestrator.py
│   ├── test_runner.py
│   ├── validate_tdd.py
│   └── validate_test_preservation.py
├── documentation/      # API documentation generation tools
│   └── generate_api_docs.py
├── validation/         # Diagram validation and visual consistency tools
│   ├── diagram_validator.py
│   └── README.md
└── visualizer/         # Web-based state visualization interface
    ├── app.py
    ├── static/
    │   ├── style.css
    │   └── visualizer.js
    └── templates/
        └── index.html
```

## Tool Categories

### Compliance Tools (`compliance/`)

Tools for tracking government audit compliance and ensuring quality standards.

#### `audit_compliance_tracker.py`
**Purpose**: Real-time monitoring system for tracking test coverage across all lib modules
**Features**:
- Lightweight implementation optimized for disk space constraints
- Module discovery and coverage gap analysis
- Priority scoring for modules needing attention
- Effort estimation for reaching 95% coverage target
- Government audit compliance dashboard
- XML and JSON coverage data parsing
- Progress visualization with bars and metrics

**Usage**:
```bash
cd tools/compliance
python3 audit_compliance_tracker.py
```

**Key Functions**:
- `ComplianceTracker.generate_dashboard()`: Full compliance analysis
- `_calculate_module_coverage()`: Per-module coverage calculation
- `_prioritize_modules()`: Priority scoring based on gaps and effort
- `_estimate_completion_effort()`: Time and resource estimation

#### `monitor_compliance.py`
**Purpose**: Lightweight monitoring script for quick compliance status checks
**Features**:
- Quick coverage check using existing coverage.xml
- Disk space monitoring and warnings
- Module compliance rate calculation
- Tier-based progress assessment
- Minimal resource usage for continuous monitoring

**Usage**:
```bash
cd tools/compliance
python3 monitor_compliance.py
```

**Integration**: Designed for CI/CD pipelines and automated monitoring systems

### Coverage Tools (`coverage/`)

Comprehensive test coverage analysis and TDD workflow validation utilities.

#### `analyze_coverage.py`
**Purpose**: Simple coverage analysis to identify lib files needing tests
**Features**:
- Discovery of all Python files in lib directory
- Test file mapping and coverage calculation
- Identification of files without corresponding tests
- Coverage percentage reporting

**Usage**:
```bash
cd tools/coverage
python3 analyze_coverage.py
```

#### `test_runner.py`
**Purpose**: Simple test runner for core functionality validation without external dependencies
**Features**:
- Import validation for all core modules
- State machine functionality testing
- Agent system validation
- Claude client integration testing
- Orchestrator command handling verification
- Graceful fallback when Claude Code not available

**Usage**:
```bash
cd tools/coverage
python3 test_runner.py
```

**Test Categories**:
- `test_imports()`: Module import validation
- `test_state_machine()`: State transition testing
- `test_agents()`: Agent instantiation and task handling
- `test_claude_client()`: AI integration testing
- `test_orchestrator()`: Command processing validation

#### `validate_tdd.py`
**Purpose**: Validation script for TDD models and state machine functionality
**Features**:
- TDD models serialization testing
- State machine transition validation
- Cycle and task lifecycle verification
- Integration workflow testing
- Complete TDD workflow validation

**Usage**:
```bash
cd tools/coverage
python3 validate_tdd.py
```

#### `coverage_analysis_global_orchestrator.py`
**Purpose**: Specialized coverage analysis for global orchestrator module
**Features**:
- Targeted analysis for critical orchestration component
- Module import verification
- Code line counting and estimation

**Usage**:
```bash
cd tools/coverage
python3 coverage_analysis_global_orchestrator.py
```

#### `validate_test_preservation.py`
**Purpose**: Validation for TDD test preservation workflow
**Features**:
- Test file lifecycle validation
- Status promotion verification
- Test preservation guarantee validation
- Temporary directory testing

**Usage**:
```bash
cd tools/coverage
python3 validate_test_preservation.py
```

### Documentation Tools (`documentation/`)

Automated API documentation generation from source code analysis.

#### `generate_api_docs.py`
**Purpose**: Extract docstrings, type hints, and method signatures to generate comprehensive API documentation
**Features**:
- AST-based source code analysis
- Multiple output formats (Markdown, OpenAPI)
- Class hierarchy extraction
- Method signature parsing with type annotations
- Decorator and inheritance analysis
- Package-based organization
- Private method filtering option

**Usage**:
```bash
cd tools/documentation

# Generate Markdown documentation
python3 generate_api_docs.py --format markdown --output api_docs.md

# Generate OpenAPI specification
python3 generate_api_docs.py --format openapi --output api_spec.json

# Include private methods
python3 generate_api_docs.py --include-private --format markdown

# Analyze specific directory
python3 generate_api_docs.py --directory scripts --format markdown
```

**Data Models**:
- `APIMethod`: Method/function representation with signatures and metadata
- `APIClass`: Class representation with methods, attributes, and inheritance
- `APIModule`: Module representation with classes, functions, and constants

**Output Formats**:
- **Markdown**: Human-readable documentation with hierarchical organization
- **OpenAPI**: Machine-readable API specification for REST endpoints

### Validation Tools (`validation/`)

Diagram validation and visual consistency tools for maintaining documentation quality.

#### `diagram_validator.py`
**Purpose**: Comprehensive Mermaid diagram validation for syntax, theme, and content consistency

**Features**:
- **Syntax Validation**: Checks for common Mermaid syntax errors (unmatched brackets, missing diagram types)
- **Theme Consistency**: Enforces dark theme across all diagrams (`%%{init: {'theme': 'dark'}}%%`)
- **State Machine Validation**: Validates state diagrams against known state machine states
- **Command Validation**: Checks command references in transitions against valid commands
- **Auto-Fix Capability**: Automatically fixes common issues (missing themes, incorrect themes)
- **Multiple Output Formats**: Human-readable reports or JSON for CI integration

**Usage**:
```bash
# Basic validation
python3 tools/validation/diagram_validator.py

# Verbose output with detailed reporting
python3 tools/validation/diagram_validator.py --verbose

# Auto-fix common issues
python3 tools/validation/diagram_validator.py --fix --verbose

# JSON output for CI integration
python3 tools/validation/diagram_validator.py --json --exit-code
```

**Validation Rules**:
- **Theme Consistency**: All diagrams must use dark theme
- **State Machine Alignment**: State names must match known states (IDLE, BACKLOG_READY, etc.)
- **Command Recognition**: Commands in transitions should match valid workflow commands
- **Syntax Correctness**: Basic syntax validation for common errors

**Integration Points**:
- Pre-commit hooks for diagram validation
- CI/CD pipeline integration with exit codes
- Documentation build process validation
- Development workflow quality checks

### Visualizer Tools (`visualizer/`)

Real-time web-based visualization interface for workflow and TDD state monitoring with Discord-style chat.

#### `app.py`
**Purpose**: Flask application with WebSocket support for real-time state visualization
**Features**:
- SocketIO integration for real-time updates
- State broadcasting integration
- REST API endpoints for state access
- Health monitoring and metrics
- Multi-client support with connection management
- Automatic reconnection with exponential backoff
- Discord-style chat interface with slash commands
- Vertical state diagram layout for better readability

**Usage**:
```bash
cd tools/visualizer

# Run with defaults (localhost:5000)
python3 app.py

# Custom host and port
python3 app.py --host 0.0.0.0 --port 8080 --debug
```

**API Endpoints**:
- `GET /`: Main visualizer interface
- `GET /api/state`: JSON API for current state
- `GET /api/history`: Transition history API
- `GET /health`: Health check with metrics

**WebSocket Events**:
- `workflow_transition`: Workflow state changes
- `tdd_transition`: TDD cycle state changes
- `agent_activity`: Agent execution events
- `state_update`: Full state synchronization

#### Frontend Components (`static/` and `templates/`)

**`visualizer.js`**: Real-time frontend client
- SocketIO client with automatic reconnection
- Mermaid diagram integration with state highlighting
- Activity logging with filtering and auto-scroll
- TDD cycle management and visualization
- Connection status monitoring

**`index.html`**: Main visualizer interface
- Responsive design with status bar
- Dual state machine diagrams (Workflow + TDD)
- Active TDD cycles panel
- Real-time activity log
- Connection status indicators

**`style.css`**: Visualization styling
- State-based color coding
- Responsive grid layout
- Interactive diagram highlighting
- Activity log formatting

## Integration with Main System

### Development Workflow Integration

1. **Coverage Monitoring**: 
   - `audit_compliance_tracker.py` integrates with CI/CD for continuous compliance monitoring
   - `test_runner.py` provides quick validation without heavy test suite overhead

2. **Documentation Pipeline**:
   - `generate_api_docs.py` can be automated in build processes
   - Integrates with MkDocs documentation system

3. **Real-time Monitoring**:
   - Visualizer connects to `state_broadcaster` for live state updates
   - Provides debugging interface for workflow development

### Testing and Validation

1. **TDD Workflow Validation**:
   - `validate_tdd.py` ensures TDD models work correctly
   - `validate_test_preservation.py` verifies test preservation guarantees

2. **Coverage Analysis**:
   - Tools integrate with pytest-cov for comprehensive coverage reporting
   - Support both XML and JSON coverage formats

3. **Compliance Tracking**:
   - Government audit compliance monitoring with 95% coverage targets
   - Multi-tier progression tracking

### Command Line Integration

All tools support command-line operation and can be integrated into:
- CI/CD pipelines
- Development scripts
- Automated monitoring systems
- Documentation generation workflows

## Tool Usage Patterns

### Daily Development Workflow

1. **Before Coding**: Run `test_runner.py` to validate system integrity
2. **During Development**: Use visualizer for real-time state monitoring
3. **After Changes**: Run coverage analysis to identify test gaps
4. **Documentation Updates**: Generate API docs after interface changes
5. **Diagram Changes**: Validate Mermaid diagrams with `diagram_validator.py --fix`

### Release Preparation

1. **Compliance Check**: Run `audit_compliance_tracker.py` for full analysis
2. **Coverage Validation**: Ensure all modules meet coverage targets
3. **Documentation Generation**: Update API documentation
4. **TDD Validation**: Verify TDD workflow integrity
5. **Visual Consistency**: Validate all diagrams with `diagram_validator.py`

### Continuous Integration

1. **Monitor Compliance**: Use `monitor_compliance.py` for lightweight checks
2. **Coverage Reporting**: Integrate coverage tools with CI metrics
3. **State Monitoring**: Deploy visualizer for runtime monitoring
4. **Documentation Automation**: Auto-generate docs on commits
5. **Diagram Validation**: Add `diagram_validator.py --json --exit-code` to CI pipeline

## Dependencies

### Core Dependencies
- **Python 3.7+**: All tools require modern Python
- **Flask/SocketIO**: Visualizer web interface
- **AST**: Documentation generation (built-in)
- **JSON/XML**: Coverage data parsing (built-in)

### Optional Dependencies
- **pytest-cov**: Enhanced coverage integration
- **Mermaid**: Diagram rendering (CDN-based)
- **WebSocket libraries**: Real-time communication

### System Integration
- **Git**: Version control integration
- **CI/CD**: Pipeline integration support
- **Docker**: Containerization support for visualizer

## Security Considerations

1. **Web Interface**: Visualizer includes CORS configuration
2. **File Access**: Tools operate within project boundaries
3. **Network Access**: WebSocket connections use standard ports
4. **Data Privacy**: No sensitive data exposed in visualizations

## Performance Characteristics

1. **Lightweight Monitoring**: Quick compliance checks with minimal resource usage
2. **Disk Space Optimization**: Tools designed for constrained environments
3. **Real-time Updates**: Efficient WebSocket communication
4. **Scalable Architecture**: Supports multiple client connections

The tools directory provides a comprehensive suite of development utilities that enhance the AI Agent TDD-Scrum workflow system with monitoring, validation, documentation, and visualization capabilities.

## Common Development Issues

### Web Visualizer Not Updating
If changes to the visualizer aren't showing after code updates:

1. **Python Package Issue**: Package needs reinstalling in editable mode
   ```bash
   pip uninstall -y agent-workflow --break-system-packages
   pip install -e . --user --break-system-packages
   ```

2. **Browser Cache Issue**: Browser serving old JavaScript/CSS files
   - Hard refresh: Ctrl+F5 (Windows/Linux) or Cmd+Shift+R (Mac)
   - Or use incognito/private window

3. **Process Issue**: Old process still running on port
   ```bash
   lsof -ti:5000 | xargs kill -9 2>/dev/null || true
   ```

**Complete Fix Sequence**:
```bash
aw web-stop
pip install -e . --user --break-system-packages
aw web
# Then Ctrl+F5 in browser
```

### Troubleshooting Resources
- **Visualizer Specific Issues**: See `tools/visualizer/CLAUDE.md` for comprehensive Discord interface debugging
- **Package Installation Issues**: See `agent_workflow/CLAUDE.md` for detailed troubleshooting
- **Test Scripts**: Use `tools/visualizer/test_*.py` to verify functionality
- **General Issues**: See root `CLAUDE.md` for repository-wide troubleshooting guide

### Recent Visualizer Improvements (2025-07-01)
1. **Discord Chat Interface**: Fixed send button functionality by adding missing ChatComponents methods
2. **Main Page Scrolling**: Fixed scrolling issue by changing CSS overflow property
3. **Chat Close Button**: Added proper event handler for closing chat panel
4. **Mermaid Diagram Fonts**: Increased font size to 16px for better readability
5. **Diagram Layout**: Changed from side-by-side to vertical stacking for more space
6. **Failsafe Initialization**: Added `chat-init-failsafe.js` for robust chat initialization
7. **Comprehensive Diagnostics**: Created multiple test tools and troubleshooting guide