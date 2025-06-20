# 🛠️ Development Tools

The project includes a comprehensive suite of development utilities in the `tools/` directory, organized by category to support development, testing, and monitoring workflows.

## Overview

The tools directory provides five main categories of utilities:

<div class="grid cards" markdown>

-   :material-chart-line:{ .lg .middle } **Compliance Monitoring**

    ---
    
    Track government audit compliance and quality standards
    
    [:octicons-arrow-right-24: Compliance Tools](#compliance-tools)

-   :material-test-tube:{ .lg .middle } **Coverage Analysis**

    ---
    
    Test coverage validation and TDD workflow verification
    
    [:octicons-arrow-right-24: Coverage Tools](#coverage-tools)

-   :material-file-document:{ .lg .middle } **Documentation Generation**

    ---
    
    Automated API documentation from source code
    
    [:octicons-arrow-right-24: Documentation Tools](#documentation-tools)

-   :material-monitor-dashboard:{ .lg .middle } **State Visualization**

    ---
    
    Real-time web-based monitoring of workflow states
    
    [:octicons-arrow-right-24: Visualizer Tools](#visualizer-tools)

-   :material-file-tree:{ .lg .middle } **Dependency Tracking**

    ---
    
    Intelligent file dependency tracking and consistency maintenance
    
    [:octicons-arrow-right-24: Dependency Tools](#dependency-tools)

</div>

## Compliance Tools

### Real-time Compliance Tracker

Monitor test coverage and government audit compliance in real-time.

```bash
python tools/compliance/audit_compliance_tracker.py
```

**Key Features:**
- Real-time dashboard for tracking test coverage across all modules
- Government audit compliance monitoring (95% coverage target)
- Priority scoring for modules needing attention
- Effort estimation for reaching coverage targets
- XML and JSON coverage data parsing

### Lightweight Compliance Monitor

Quick compliance status checks for CI/CD integration.

```bash
python tools/compliance/monitor_compliance.py
```

**Key Features:**
- Minimal resource usage for continuous monitoring
- Disk space monitoring and warnings
- Tier-based progress assessment
- Designed for automated monitoring systems

## Coverage Tools

### Coverage Analysis

Identify library files that need test coverage.

```bash
python tools/coverage/analyze_coverage.py
```

**Key Features:**
- Discovery of all Python files in lib directory
- Test file mapping and coverage calculation
- Identification of files without corresponding tests
- Coverage percentage reporting

### Test Runner

Simple test runner for core functionality validation without external dependencies.

```bash
python tools/coverage/test_runner.py
```

**Key Features:**
- Import validation for all core modules
- State machine functionality testing
- Agent system validation
- Claude client integration testing
- Graceful fallback when Claude Code not available

### TDD Validation

Validate TDD models and state machine functionality.

```bash
python tools/coverage/validate_tdd.py
```

**Key Features:**
- TDD models serialization testing
- State machine transition validation
- Cycle and task lifecycle verification
- Complete TDD workflow validation

### Test Preservation Validation

Ensure TDD test preservation workflow integrity.

```bash
python tools/coverage/validate_test_preservation.py
```

**Key Features:**
- Test file lifecycle validation
- Status promotion verification
- Test preservation guarantee validation
- Temporary directory testing

## Documentation Tools

### API Documentation Generator

Extract docstrings, type hints, and method signatures to generate comprehensive API documentation.

```bash
# Generate Markdown documentation
python tools/documentation/generate_api_docs.py --format markdown --output api_docs.md

# Generate OpenAPI specification
python tools/documentation/generate_api_docs.py --format openapi --output api_spec.json

# Include private methods
python tools/documentation/generate_api_docs.py --include-private --format markdown
```

**Key Features:**
- AST-based source code analysis
- Multiple output formats (Markdown, OpenAPI)
- Class hierarchy extraction
- Method signature parsing with type annotations
- Decorator and inheritance analysis
- Private method filtering option

## Visualizer Tools

### Real-time State Visualization

Web-based interface for monitoring workflow and TDD states in real-time.

```bash
# Run with defaults (localhost:5000)
python tools/visualizer/app.py

# Custom host and port
python tools/visualizer/app.py --host 0.0.0.0 --port 8080 --debug
```

**Key Features:**
- Flask/SocketIO web application
- Real-time state broadcasting integration
- Interactive state machine diagrams
- Multi-client support with connection management
- Health monitoring and metrics
- Automatic reconnection with exponential backoff

**Web Interface Components:**
- **Main Dashboard**: Responsive interface with dual state machine diagrams
- **TDD Cycle Management**: Active cycle visualization and monitoring
- **Activity Log**: Real-time logging with filtering and auto-scroll
- **Connection Status**: Live connection monitoring and status indicators

## Dependency Tools

### Dependency Tracker

Intelligent system for maintaining consistency across code, tests, and documentation.

```bash
# Scan and build dependency map
python tools/dependencies/tracker.py

# Check dependencies for a specific file
python tools/dependencies/tracker.py --file lib/agents/code_agent.py --related

# Export dependency graph
python tools/dependencies/tracker.py --export-graph
```

**Key Features:**
- AST-based Python import analysis
- Convention-based test/documentation mapping
- Markdown reference extraction
- Bidirectional dependency graphs
- YAML export/import for dependency data

### File Watcher

Real-time monitoring of file changes with automatic dependency updates.

```bash
# Start continuous file watching
python tools/dependencies/watcher.py
```

**Key Features:**
- Real-time file monitoring with watchdog
- Debounced update processing
- Concurrent update execution
- Integration with Claude Code for intelligent updates

### Dependency Updater

Apply updates to dependent files when source files change.

```bash
# Preview updates without applying changes
python tools/dependencies/updater.py lib/some_module.py --dry-run

# Apply updates to dependent files
python tools/dependencies/updater.py lib/some_module.py
```

**Key Features:**
- Intelligent update suggestions
- Dry-run mode for previewing changes
- Integration with version control
- Validation before applying updates

## Additional Utilities

### Documentation Link Auditor

Comprehensive tool for checking documentation integrity.

```bash
python tools/audit_links.py
```

**Key Features:**
- Checks all markdown files for broken internal links
- Validates external resource availability
- Identifies invalid image references and incorrect file paths
- Detects anchor issues and missing references
- Generates detailed audit reports in JSON format

### Documentation Link Fixer

Automated fixing tool for common documentation link issues.

```bash
python tools/fix_documentation_links.py
```

**Key Features:**
- Fixes template placeholder links
- Corrects common link formatting issues
- Updates relative path references
- Batch processing of documentation files
- Preview mode for reviewing changes before applying

## Development Workflow Integration

### Daily Development

1. **System Validation**: Run `test_runner.py` before coding
2. **Real-time Monitoring**: Use visualizer during development
3. **Dependency Tracking**: Start file watcher for automatic updates
4. **Coverage Analysis**: Check coverage after changes
5. **Documentation**: Update API docs after interface changes
6. **Link Validation**: Audit documentation links before commits

### Release Preparation

1. **Compliance Check**: Run `audit_compliance_tracker.py` for full analysis
2. **Coverage Validation**: Ensure all modules meet targets
3. **Documentation**: Generate updated API documentation
4. **TDD Validation**: Verify workflow integrity
5. **Link Auditing**: Comprehensive documentation link validation
6. **Dependency Validation**: Ensure all dependencies are current

### Continuous Integration

1. **Compliance Monitoring**: Use `monitor_compliance.py` for CI checks
2. **Coverage Reporting**: Integrate with CI metrics
3. **State Monitoring**: Deploy visualizer for runtime monitoring
4. **Auto-documentation**: Generate docs on commits

## Tool Dependencies

### Core Requirements
- **Python 3.7+**: All tools require modern Python
- **Flask/SocketIO**: Web interface components
- **AST**: Documentation generation (built-in)
- **JSON/XML**: Coverage data parsing (built-in)

### Optional Enhancements
- **pytest-cov**: Enhanced coverage integration
- **Mermaid**: Diagram rendering (CDN-based)
- **WebSocket libraries**: Real-time communication

## Security Considerations

- **Web Interface**: CORS configuration for secure access
- **File Access**: Tools operate within project boundaries
- **Network Access**: Standard ports for WebSocket connections
- **Data Privacy**: No sensitive data exposed in visualizations

## Performance Characteristics

- **Lightweight**: Minimal resource usage for monitoring
- **Efficient**: Optimized for disk space constraints
- **Real-time**: Efficient WebSocket communication
- **Scalable**: Multiple client connection support

!!! info "Complete Documentation"
    For detailed technical documentation of all tools, see [`tools/CLAUDE.md`](https://github.com/jmontp/agent-workflow/blob/main/tools/CLAUDE.md) in the repository.