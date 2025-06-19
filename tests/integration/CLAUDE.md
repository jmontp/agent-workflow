# Integration Tests Documentation

This directory contains comprehensive integration tests for the AI Agent TDD-Scrum workflow system. These tests validate end-to-end functionality, cross-component interactions, and complete workflow scenarios.

## Overview

The integration test suite is designed to validate:
- Complete workflow execution from command input to agent coordination
- Cross-component interactions between orchestrator, agents, state machines, and storage
- End-to-end TDD cycles and multi-project orchestration
- Real-world scenario simulation and performance validation
- Human-in-the-loop (HITL) approval workflows and error recovery

## Test Categories

### 1. Core Integration Tests

#### `test_context_integration.py`
- **Purpose**: Tests the complete context management pipeline
- **Key Features**:
  - Full context preparation workflow
  - Agent memory integration and phase handoffs
  - Context snapshot creation and retrieval
  - Token budget optimization
  - Performance metrics collection
- **Test Scenarios**:
  - End-to-end context preparation for different agent types
  - TDD phase handoffs with context preservation
  - Multi-agent context sharing and coordination
  - Performance and scalability testing with caching

#### `test_agent_integration.py`
- **Purpose**: Tests agent-context management integration
- **Key Features**:
  - Agent context preparation with token budgets
  - Decision recording and retrieval
  - TDD phase handoff tracking
  - Agent learning analysis
  - Context snapshot workflows
- **Test Scenarios**:
  - Agents preparing context with context manager
  - Phase handoffs between Design, QA, and Code agents
  - Agent memory and learning pattern analysis
  - Performance metrics for context operations

### 2. TDD Workflow Integration

#### `test_tdd_e2e.py`
- **Purpose**: Comprehensive end-to-end TDD testing
- **Key Features**:
  - Complete TDD cycle simulation with real projects
  - Multi-story TDD workflows within sprint lifecycle
  - Performance benchmarking and reliability testing
  - Human intervention point validation
  - CI/CD integration scenarios
- **Test Infrastructure**:
  - Realistic Git repository creation
  - Performance monitoring and metrics collection
  - Test data generation for e-commerce scenarios
  - Memory usage and execution time tracking
- **Test Scenarios**:
  - Full TDD cycle: Design → Test → Code → Refactor → Commit
  - Sequential TDD cycles for multiple stories
  - Sprint integration with TDD workflows
  - Error handling and recovery mechanisms

#### `test_tdd_agent_coordination.py`
- **Purpose**: Tests TDD agent coordination workflows
- **Key Features**:
  - Complete Red-Green-Refactor cycle coordination
  - Agent security validation in TDD context
  - Artifact handoff between agents
  - Parallel TDD cycle execution
  - Metrics collection and monitoring
- **Test Scenarios**:
  - Design → QA → Code agent handoffs
  - Security boundary enforcement per TDD phase
  - Error recovery and retry mechanisms
  - Human approval gates in blocking orchestration

#### `test_tdd_orchestration.py`
- **Purpose**: Integration between orchestrator and TDD components
- **Key Features**:
  - TDD state machine integration with main workflow
  - Multiple concurrent TDD cycles
  - Resource monitoring and management
  - Agent handoff coordination
  - Data model enhancements for TDD
- **Test Scenarios**:
  - Complete TDD lifecycle with state transitions
  - TDD logs and overview functionality
  - Failure recovery mechanisms
  - Multi-cycle resource management

### 3. Orchestrator Integration

#### `test_orchestrator_commands.py`
- **Purpose**: Tests complete orchestrator command workflows
- **Key Features**:
  - Epic and story creation workflows
  - Sprint lifecycle management
  - State validation and transitions
  - Error handling and recovery
  - Approval queue management
- **Test Scenarios**:
  - `/epic`, `/approve`, `/sprint` command workflows
  - Invalid command and state transition handling
  - State persistence and recovery
  - Concurrent command execution

#### `test_integration.py`
- **Purpose**: State machine broadcasting and NO-AGENT mode
- **Key Features**:
  - State machine integration with broadcasting
  - TDD state machine broadcasting
  - Mock agent replacement in NO-AGENT mode
  - Graceful fallback handling
- **Test Scenarios**:
  - State transition broadcasting validation
  - Mock agent execution with realistic timing
  - Orchestrator integration with mock agents
  - Missing dependency graceful handling

### 4. Multi-Project Integration

#### `test_multi_project_orchestration.py`
- **Purpose**: Comprehensive multi-project orchestration testing
- **Key Features**:
  - Multi-project configuration management
  - Global orchestrator coordination
  - Resource allocation and scheduling
  - Cross-project intelligence and knowledge sharing
  - Security and isolation
  - Monitoring and observability
- **Test Components**:
  - **Configuration Management**: Project registration, discovery, dependency management
  - **Global Orchestrator**: Lifecycle management, project coordination, status reporting
  - **Resource Scheduler**: Project registration, task scheduling, resource optimization
  - **Cross-Project Intelligence**: Pattern identification, insight generation, knowledge transfer
  - **Security System**: User management, access control, secret management, project isolation
  - **Monitoring System**: Target registration, metric recording, alert management
- **Integration Scenarios**:
  - Complete multi-project workflow simulation
  - Error handling across system components
  - Performance testing under simulated load

### 5. Parallel Processing Integration

#### `test_parallel_tdd_execution.py`
- **Purpose**: Tests parallel TDD execution capabilities
- **Key Features**:
  - Parallel TDD engine lifecycle management
  - Multiple concurrent cycle execution
  - Conflict detection and resolution
  - Resource pool management
  - Performance optimization
- **Test Components**:
  - **Parallel TDD Engine**: Unified engine for parallel execution
  - **TDD Coordinator**: Cycle management and resource allocation
  - **Agent Pool**: Dynamic agent scaling and load balancing
  - **Conflict Resolver**: File modification tracking and conflict analysis
  - **Enhanced State Machine**: Parallel state tracking and dependencies
- **Performance Benchmarks**:
  - Throughput testing with multiple cycles
  - Conflict resolution performance
  - Memory and CPU usage optimization

### 6. Specialized Integration Tests

#### `test_claude_integration.py`
- **Purpose**: Tests Claude Code integration specifically
- **Key Features**:
  - Claude Code availability detection
  - Code generation and analysis
  - Fallback behavior when Claude Code unavailable
- **Test Scenarios**:
  - Simple code generation requests
  - Code analysis and review
  - Error handling for missing Claude Code

#### `test_intelligence_demo.py`
- **Purpose**: Demonstrates context intelligence capabilities
- **Key Features**:
  - Context index building and searching
  - Dependency analysis and file relationships
  - Intelligent context preparation with relevance scoring
  - Compression analysis and optimization
  - Multi-factor relevance scoring algorithm
- **Demo Scenarios**:
  - Codebase search with different query types
  - File dependency analysis and tracking
  - Context preparation with focus areas
  - Performance metrics and project statistics

## Running Integration Tests

### Prerequisites
```bash
# Install required dependencies
pip install pytest pytest-asyncio pytest-cov
pip install discord.py pygithub pyyaml
pip install tempfile shutil pathlib
```

### Basic Test Execution
```bash
# Run all integration tests
pytest tests/integration/ -v

# Run specific test categories
pytest tests/integration/test_tdd_*.py -v
pytest tests/integration/test_multi_project_*.py -v
pytest tests/integration/test_orchestrator_*.py -v

# Run with coverage
pytest tests/integration/ --cov=lib/ --cov-report=html

# Run excluding slow tests
pytest tests/integration/ -m "not slow"

# Run only slow performance tests
pytest tests/integration/ -m "slow"
```

### Advanced Test Options
```bash
# Run with detailed output
pytest tests/integration/ -v -s

# Run specific test methods
pytest tests/integration/test_tdd_e2e.py::test_complete_tdd_workflow -v

# Run with timeout for long-running tests
pytest tests/integration/ --timeout=300

# Run parallel tests (if pytest-xdist installed)
pytest tests/integration/ -n auto
```

### Environment Variables
```bash
# Enable NO_AGENT_MODE for testing without real agents
export NO_AGENT_MODE=true

# Set Discord bot token for Discord integration tests
export DISCORD_BOT_TOKEN="your_test_token"

# Enable debug logging
export DEBUG=true
```

## Test Patterns and Best Practices

### 1. Mock and Fixture Usage
- **Extensive Mocking**: Tests use mocks for external dependencies (Discord, GitHub, Claude Code)
- **Realistic Fixtures**: Temporary directories, Git repositories, and project structures
- **Agent Mocking**: Sophisticated agent mocks with realistic execution patterns
- **State Persistence**: Tests validate state persistence and recovery

### 2. Error Simulation and Recovery
- **Failure Injection**: Tests inject failures at various points to validate recovery
- **Timeout Handling**: Tests include timeout scenarios for network operations
- **Graceful Degradation**: Validates system behavior when components are unavailable
- **Human Intervention**: Simulates approval workflows and escalation patterns

### 3. Performance Validation
- **Execution Time Tracking**: All major operations are timed and validated
- **Memory Usage Monitoring**: Tests track memory consumption patterns
- **Throughput Testing**: Validates system performance under load
- **Resource Optimization**: Tests resource allocation and optimization algorithms

### 4. End-to-End Scenarios
- **Complete Workflows**: Tests execute complete user journeys from start to finish
- **Multi-Component Integration**: Validates interaction between all system components
- **State Machine Validation**: Ensures proper state transitions and validation
- **Data Persistence**: Validates data integrity across component boundaries

## Integration Test Architecture

### Test Infrastructure Components

#### `TestInfrastructure` (in test_tdd_e2e.py)
- Creates realistic test repositories with Git integration
- Provides performance monitoring and metrics collection
- Manages test data and cleanup operations
- Supports CI/CD workflow simulation

#### Mock Systems
- **Agent Mocks**: Realistic agent behavior simulation
- **External Service Mocks**: Discord, GitHub, Claude Code mocking
- **File System Mocks**: Safe file operation testing
- **Network Mocks**: API call simulation and validation

#### Test Data Management
- **Realistic Scenarios**: E-commerce platform development scenarios
- **Performance Targets**: Defined SLAs for various operations
- **Multi-Project Configurations**: Complex project dependency scenarios
- **User Stories**: Comprehensive acceptance criteria and test scenarios

## Expected Outcomes

### Success Criteria
1. **All Core Workflows**: Epic creation, story management, TDD cycles complete successfully
2. **State Consistency**: State machines maintain consistency across transitions
3. **Data Integrity**: All data persistence operations maintain integrity
4. **Performance Targets**: Operations complete within defined time limits
5. **Error Recovery**: System recovers gracefully from expected failure scenarios
6. **Resource Management**: Efficient resource utilization without leaks

### Performance Expectations
- **TDD Cycle Completion**: < 5 minutes per cycle (mocked agents)
- **Agent Response Time**: < 30 seconds per operation
- **Storage Operations**: < 1 second for data persistence
- **Memory Usage**: < 500MB peak usage during testing
- **Concurrent Operations**: Support for 3+ parallel TDD cycles

### Quality Metrics
- **Test Coverage**: > 90% coverage for integration scenarios
- **Success Rate**: > 95% test pass rate in CI/CD
- **Performance Consistency**: < 10% variance in execution times
- **Error Handling**: 100% of expected error scenarios handled gracefully

## Troubleshooting Integration Tests

### Common Issues

#### 1. Test Timeouts
```bash
# Increase timeout for slow operations
pytest tests/integration/ --timeout=600

# Run with debug output
pytest tests/integration/ -v -s --tb=long
```

#### 2. Resource Cleanup
```bash
# Manual cleanup of test artifacts
rm -rf /tmp/test_*
pkill -f "python.*test"
```

#### 3. Mock Configuration Issues
- Verify agent mocks are properly configured
- Check that external service mocks return expected responses
- Validate file system permissions for temporary directories

#### 4. State Machine Issues
- Ensure proper state initialization in fixtures
- Validate state transitions are properly mocked
- Check for race conditions in async operations

### Debugging Tips
1. **Use `-s` flag**: Shows print statements and debug output
2. **Enable logging**: Set DEBUG=true for detailed logging
3. **Run single tests**: Isolate failing tests for easier debugging
4. **Check fixtures**: Verify fixture setup and teardown
5. **Validate mocks**: Ensure mocks match expected interfaces

## Contributing to Integration Tests

### Adding New Tests
1. **Follow naming conventions**: `test_<component>_<feature>.py`
2. **Use appropriate fixtures**: Reuse existing fixtures when possible
3. **Include performance validation**: Add timing and resource checks
4. **Test error scenarios**: Include failure and recovery testing
5. **Document test purpose**: Clear docstrings and comments

### Test Organization
- **Group related tests**: Use test classes for logical grouping
- **Share fixtures**: Use conftest.py for common fixtures
- **Mark slow tests**: Use `@pytest.mark.slow` for performance tests
- **Include integration markers**: Use `@pytest.mark.integration`

### Quality Standards
- **Comprehensive coverage**: Test all major code paths
- **Realistic scenarios**: Use real-world use cases
- **Performance awareness**: Include timing and resource validation
- **Error resilience**: Test failure and recovery scenarios
- **Documentation**: Clear test documentation and examples

This integration test suite provides comprehensive validation of the AI Agent TDD-Scrum workflow system, ensuring reliable operation across all components and realistic usage scenarios.