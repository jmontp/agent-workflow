# CLAUDE.md - Tests Directory Documentation

This file provides comprehensive guidance to Claude Code when working with the test infrastructure in this repository.

## Test Suite Overview

This repository contains a **comprehensive enterprise-grade test suite** with **107+ test files** designed for **government audit compliance** with **95%+ coverage requirements**. The test infrastructure supports **multi-layered validation** from unit tests to full end-to-end workflows.

### Test Categories and Organization

```
tests/
├── unit/                    # 80+ unit test files - individual component testing
├── integration/             # 11 integration test files - component interaction testing
├── acceptance/              # User acceptance testing - real-world usage scenarios
├── performance/             # Performance and load testing - system performance validation
├── security/                # Security compliance testing - government audit requirements
├── edge_cases/              # Edge case testing - robustness and failure scenarios
├── regression/              # Regression testing - backward compatibility validation
├── mocks/                   # Enterprise mock infrastructure - external dependency simulation
├── reports/                 # Test report output directory
├── conftest.py              # Enterprise test configuration and fixtures
├── pytest.ini               # Pytest configuration with government compliance markers
└── run_comprehensive_tests.py  # Orchestrated test suite runner
```

### Key Test Infrastructure Components

#### 1. **Enterprise Test Configuration** (`conftest.py`)
- **771 lines** of comprehensive test fixtures and infrastructure
- **Cross-module compatible fixtures** for integrated testing
- **Enterprise mock frameworks** (Discord, WebSocket, GitHub, FileSystem)
- **Performance monitoring** and **security compliance validation**
- **Government audit compliance** validation hooks

#### 2. **Mock Infrastructure** (`mocks/`)
- **Comprehensive external dependency mocking**:
  - `discord_mocks.py` - Discord API (discord.py) simulation
  - `websocket_mocks.py` - WebSocket server/client simulation
  - `github_mocks.py` - GitHub API (PyGithub) simulation
  - `filesystem_mocks.py` - File system operation simulation
  - `async_fixtures.py` - Async test patterns and utilities

#### 3. **State Machine Testing** 
The repository contains **extensive state machine simulation testing**:

- **`test_state_machine.py`** (724 lines): Main workflow state machine testing
  - Complete state transition validation (IDLE → BACKLOG_READY → SPRINT_PLANNED → SPRINT_ACTIVE → SPRINT_REVIEW)
  - Command validation for all workflow states
  - **Mermaid diagram generation testing**
  - **TDD integration testing** with active cycle tracking
  - **Complex workflow sequence validation**
  - **Error conditions and helpful hints testing**

- **`test_tdd_state_machine.py`** (700 lines): TDD-specific state machine testing
  - TDD cycle transitions (DESIGN → TEST_RED → CODE_GREEN → REFACTOR → COMMIT)
  - **Test preservation workflow** with commit command validation
  - **Condition-based transitions** (failing tests, passing tests, committed tests)
  - **Comprehensive TDD workflow simulation**

#### 4. **Government Audit Compliance Testing**

The test suite is designed for **TIER 3+ government audit compliance**:

- **95%+ coverage requirements** for all critical modules
- **Security compliance validation** in `security/test_tdd_security.py`
- **Performance benchmarking** with specific targets:
  - TDD Cycle Time: < 5 minutes
  - Agent Response Time: < 30 seconds  
  - Storage Operations: < 1 second
  - Memory Usage: < 500MB peak
- **Comprehensive audit trail testing**

## Test Categories in Detail

### Unit Tests (`unit/` - 80+ files)

**Coverage-focused individual component testing**:

#### State Management Tests:
- `test_state_machine.py` - Main workflow state machine (724 lines)
- `test_tdd_state_machine.py` - TDD workflow state machine (700 lines)
- `test_state_broadcaster.py` - State change broadcasting

#### Agent System Tests:
- `test_agent_memory.py` + comprehensive coverage variants
- `test_agent_pool.py` - Agent coordination and pooling
- `test_agent_tool_config.py` + security coverage variants
- Individual agent tests: `test_*_agent.py` files

#### Context Management Tests (TIER 3 Compliance):
- `test_context_manager.py` + multiple coverage variants
- `test_context_index.py` + comprehensive coverage files
- `test_context_*.py` - Context filtering, caching, compression, monitoring
- Achieved **95%+ coverage** for government audit compliance

#### Core Infrastructure Tests:
- `test_data_models.py` - Epic, Story, Sprint data models
- `test_project_storage.py` + audit coverage variants
- `test_discord_bot.py` + comprehensive coverage files
- `test_global_orchestrator.py` + coverage variants

### Integration Tests (`integration/` - 11 files)

**Component interaction and workflow testing**:
- `test_tdd_e2e.py` - Complete TDD workflow end-to-end testing
- `test_orchestrator_commands.py` - Multi-component command processing
- `test_agent_integration.py` - Agent coordination testing
- `test_context_integration.py` - Context system integration
- `test_parallel_tdd_execution.py` - Parallel TDD workflow coordination

### Performance Tests (`performance/`)

**System performance validation**:
- `test_tdd_performance.py` - TDD cycle performance benchmarking
- Validates against specific performance targets
- Memory usage monitoring and resource constraint testing

### Security Tests (`security/`)

**Government audit security compliance**:
- `test_tdd_security.py` - Comprehensive security validation
- Agent security boundary testing
- Data privacy and isolation validation
- Input validation and injection attack prevention

### Edge Case Tests (`edge_cases/`)

**Robustness and failure scenario testing**:
- `test_tdd_edge_cases.py` - System failure simulation
- Data corruption recovery testing
- Resource exhaustion behavior validation
- Boundary condition testing

### Acceptance Tests (`acceptance/`)

**Real-world usage scenario validation**:
- `test_tdd_user_acceptance.py` - Developer workflow simulation
- User experience validation
- Error recovery scenarios

### Regression Tests (`regression/`)

**Backward compatibility validation**:
- `test_tdd_regression.py` - API stability testing
- Configuration compatibility validation
- Documentation accuracy verification

## Test Execution Patterns

### Running Specific Test Categories

```bash
# Run all tests
python tests/run_comprehensive_tests.py

# Run specific categories
python tests/run_comprehensive_tests.py --categories e2e performance security

# Run unit tests only
pytest tests/unit/ -v

# Run with specific markers
pytest -m "unit and not slow" -v
pytest -m "government_audit" -v
pytest -m "security" -v

# Run state machine tests specifically
pytest tests/unit/test_state_machine.py -v
pytest tests/unit/test_tdd_state_machine.py -v

# Run coverage-focused tests
pytest tests/unit/test_*_coverage.py -v
```

### Performance-Optimized Testing

```bash
# Parallel execution (when pytest-xdist available)
pytest -n auto tests/unit/

# Quick validation during development
pytest tests/unit/test_basic_*.py -v

# Comprehensive validation before release
python tests/run_comprehensive_tests.py --save-report
```

## Coverage Requirements and Compliance

### Government Audit Compliance Targets

| Component Category | Coverage Target | Compliance Level |
|-------------------|----------------|------------------|
| Core State Machines | 95%+ | TIER 3+ |
| Agent System | 95%+ | TIER 3+ |
| Context Management | 95%+ | TIER 3+ |
| Security Components | 98%+ | TIER 5 |
| Data Storage | 95%+ | TIER 3+ |
| Discord Integration | 95%+ | TIER 3+ |

### Critical Modules with Achieved Coverage

**Successfully achieved 95%+ coverage**:
- `lib/context_manager.py` - Context management system
- `lib/context_index.py` - Code indexing and search (341 lines)
- `lib/discord_bot.py` - Discord integration
- `lib/project_storage.py` - Data persistence
- `lib/state_machine.py` - Main workflow state machine
- `lib/tdd_state_machine.py` - TDD workflow state machine

## Mock Infrastructure Overview

### Enterprise Mock Framework Features

The test suite includes **comprehensive mock infrastructure** for external dependencies:

#### Discord API Mocking (`mocks/discord_mocks.py`)
- Full Discord API simulation with realistic behavior
- Mock guilds, channels, users, and message handling
- Interactive command simulation for HITL testing

#### WebSocket Mocking (`mocks/websocket_mocks.py`)
- WebSocket server and client simulation
- Real-time communication testing
- Connection management and error simulation

#### GitHub API Mocking (`mocks/github_mocks.py`)
- Repository operations simulation
- Branch management and PR testing
- Realistic GitHub workflow simulation

#### File System Mocking (`mocks/filesystem_mocks.py`)
- Safe file system operation testing
- Project structure simulation
- File permission and error testing

### Cross-Module Integration Testing

The mock framework supports **integrated testing scenarios**:
- `integrated_mock_environment` fixture provides full external dependency simulation
- **Realistic government project structures** with security compliance
- **Performance monitoring** and **resource tracking**

## State Machine Testing Approach

### Main Workflow State Machine Testing

**`test_state_machine.py`** provides comprehensive validation:

#### Complete State Transition Testing:
```python
# Example test pattern from actual test suite
test_cases = [
    (State.IDLE, "/epic", State.BACKLOG_READY),
    (State.BACKLOG_READY, "/sprint plan", State.SPRINT_PLANNED),
    (State.SPRINT_PLANNED, "/sprint start", State.SPRINT_ACTIVE),
    (State.SPRINT_ACTIVE, "/sprint pause", State.SPRINT_PAUSED),
    # ... comprehensive transition matrix validation
]
```

#### TDD Integration Testing:
- **Active TDD cycle tracking** and validation
- **Sprint transition blocking** when TDD cycles are active
- **TDD workflow status reporting** integration
- **Transition listener system** for coordination

### TDD State Machine Testing

**`test_tdd_state_machine.py`** validates TDD-specific workflows:

#### TDD Cycle Transitions:
- DESIGN → TEST_RED → CODE_GREEN → REFACTOR → COMMIT
- **Condition-based transitions** (failing tests required, passing tests required)
- **Test preservation workflow** with commit commands

#### Test Preservation Workflow:
- `/tdd commit-tests` - Commit failing tests (TEST_RED → CODE_GREEN)
- `/tdd commit-code` - Commit passing implementation (CODE_GREEN → REFACTOR)  
- `/tdd commit-refactor` - Commit refactored code (REFACTOR → COMMIT)

## Quality Gates and Validation

### Production Readiness Requirements

The test suite enforces these quality gates:

1. **All Tests Pass**: 100% test suite success rate
2. **Performance Acceptable**: All performance targets met
3. **Security Validated**: Zero critical security issues
4. **Coverage Achieved**: >95% line coverage for critical modules
5. **Government Compliance**: TIER 3+ audit requirements satisfied

### Test Quality Metrics

- **Test Reliability**: >99% test pass rate in CI environment
- **Performance Compliance**: All performance targets consistently met
- **Security Compliance**: All security requirements satisfied
- **User Experience**: Validated through comprehensive acceptance testing

### Coverage Validation Tools

```bash
# Generate coverage reports
pytest --cov=lib --cov-report=html tests/unit/

# Validate specific module coverage
pytest --cov=lib.context_manager --cov-report=term-missing tests/unit/test_context_manager*.py

# Run coverage-focused test suites
pytest tests/unit/test_*_coverage.py --cov=lib --cov-fail-under=95
```

## Development Workflow Integration

### Pre-Commit Testing

```bash
# Quick validation during development
pytest tests/unit/test_basic_*.py -x

# Test specific component changes
pytest tests/unit/test_state_machine.py::TestStateMachine::test_valid_transitions -v

# Security validation
pytest -m security tests/security/ -v
```

### Release Validation

```bash
# Complete test suite with reporting
python tests/run_comprehensive_tests.py --save-report

# Government compliance validation
pytest -m government_audit -v

# Performance benchmarking
pytest tests/performance/ -v --durations=10
```

### Continuous Integration Support

The test suite is optimized for CI/CD environments:
- **Fast feedback** with quick unit/integration tests
- **Parallel execution** support for performance
- **Detailed reporting** for development teams
- **Quality gate enforcement** for deployment decisions

## Important Notes for Claude Code

### When Working with Tests:

1. **State Machine Tests**: Always run both `test_state_machine.py` and `test_tdd_state_machine.py` when modifying state logic
2. **Coverage Requirements**: Maintain 95%+ coverage for critical modules - use coverage-focused test files
3. **Mock Infrastructure**: Use the enterprise mock framework rather than creating simple mocks
4. **Security Testing**: Always run security tests when modifying agent permissions or data handling
5. **Performance Testing**: Validate performance targets when modifying TDD cycle timing

### Test File Patterns:

- `test_*_coverage.py` - Coverage-focused comprehensive tests
- `test_*_comprehensive.py` - Enterprise-grade comprehensive testing
- `test_*_audit.py` - Government audit compliance testing
- `test_*_security.py` - Security validation testing
- `test_*_final.py` - Final validation testing

### Critical Test Dependencies:

- **pytest**: Core testing framework
- **pytest-asyncio**: Async test support
- **pytest-cov**: Coverage analysis
- **pytest-xdist**: Parallel execution (optional)

The test infrastructure is designed to ensure **production readiness**, **government audit compliance**, and **enterprise-grade reliability** for the AI Agent TDD-Scrum workflow system.