# Testing Plan - AI Agent TDD-Scrum Workflow

## Testing Strategy

The testing strategy covers both the framework itself and the Test-Driven Development functionality that the system orchestrates. This includes testing the dual state machine architecture, TDD cycle management, and test preservation workflows.

### Test Pyramid
1. **Unit Tests (70%)** - Individual component testing
2. **Integration Tests (20%)** - Component interaction testing  
3. **End-to-End Tests (10%)** - Full workflow testing

### Test Categories

#### 1. Dual State Machine Tests

**Workflow State Machine:**
- **File**: `tests/unit/test_state_machine.py`
- **Coverage**: All workflow state transitions and command validations
- **Approach**: Table-driven tests with (current_state, command) → expected_result

```python
workflow_test_cases = [
    ("IDLE", "/epic", "BACKLOG_READY", True),
    ("IDLE", "/sprint start", "IDLE", False),  # Invalid transition
    ("SPRINT_ACTIVE", "/sprint pause", "SPRINT_PAUSED", True),
    # ... comprehensive matrix
]
```

**TDD State Machine:**
- **File**: `tests/unit/test_tdd_state_machine.py` ✅
- **Coverage**: All TDD state transitions and command validations
- **Approach**: Table-driven tests with TDD context validation

```python
tdd_test_cases = [
    ("DESIGN", "/tdd test", "TEST_RED", True, {}),
    ("TEST_RED", "/tdd commit-tests", "CODE_GREEN", True, {"has_failing_tests": True}),
    ("CODE_GREEN", "/tdd commit-code", "REFACTOR", True, {"has_passing_tests": True}),
    ("DESIGN", "/tdd code", "DESIGN", False, {}),  # Invalid - need tests first
    # ... comprehensive TDD matrix
]
```

**State Coordination:**
- **File**: `tests/unit/test_state_coordination.py`
- **Coverage**: Dual state machine coordination and synchronization
- **Approach**: Integration tests for workflow and TDD state interactions

#### 2. Enhanced Agent Library Tests
- **Files**: 
  - `tests/unit/test_base_agent.py`
  - `tests/unit/test_design_agent.py`
  - `tests/unit/test_code_agent.py`
  - `tests/unit/test_qa_agent.py`
  - `tests/unit/test_data_agent.py`
  - `tests/unit/test_agent_tool_config.py` ✅
  - `tests/unit/test_tdd_phase_manager.py`
  - `tests/unit/test_test_preservation.py`
- **Coverage**: 
  - Agent initialization and configuration
  - Task execution with dry-run mode
  - **TDD Phase Execution**: TDD-specific agent capabilities
  - **Test Preservation**: Test file lifecycle management
  - Error handling and retry logic for both workflow and TDD tasks
  - **Agent Security**: Tool access control and command restrictions
  - Claude Code integration (mocked)
  - **TDD Agent Coordination**: Handoffs between TDD phases

#### 3. Discord Bot Tests
- **Files**:
  - `tests/unit/test_discord_bot.py`
  - `tests/unit/test_command_parser.py`
  - `tests/unit/test_state_visualizer.py`
- **Coverage**:
  - Slash command parsing and validation
  - Interactive state visualization
  - Button handling and user interactions
  - Channel management (create project channels)
  - Error message formatting

#### 4. Orchestrator Tests
- **Files**:
  - `tests/unit/test_orchestrator.py`
  - `tests/unit/test_project_manager.py`
  - `tests/unit/test_approval_gate.py`
- **Coverage**:
  - Multi-project coordination
  - HITL approval workflow
  - Task dispatch and retry logic
  - State persistence and recovery

#### 5. Integration Tests
- **Files**:
  - `tests/integration/test_discord_orchestrator.py`
  - `tests/integration/test_agent_coordination.py`
  - `tests/integration/test_state_persistence.py`
  - `tests/integration/test_tdd_workflow_integration.py`
  - `tests/integration/test_dual_state_coordination.py`
  - `tests/integration/test_test_preservation_integration.py`
- **Coverage**:
  - Discord → Orchestrator → Agent workflows (including TDD commands)
  - Dual state machine integration with Discord UI
  - Multi-agent task coordination with TDD phase handoffs
  - Project state persistence across restarts (workflow + TDD)
  - **TDD Workflow Integration**: Complete TDD cycle execution
  - **Test Preservation Integration**: Test file lifecycle across phases
  - **State Coordination**: Workflow and TDD state synchronization

#### 6. End-to-End Tests
- **Files**:
  - `tests/e2e/test_complete_workflow.py`
  - `tests/e2e/test_approval_scenarios.py`
  - `test_tdd_e2e.py` ✅
  - `tests/e2e/test_dual_state_e2e.py`
- **Coverage**:
  - Complete epic → sprint → TDD cycles → implementation workflow
  - HITL approval gates and escalation for both workflow and TDD decisions
  - Multi-project orchestration scenarios with parallel TDD cycles
  - Error recovery and retry scenarios in TDD workflows
  - **Complete TDD Cycles**: DESIGN → TEST_RED → CODE_GREEN → REFACTOR → COMMIT
  - **Test Preservation E2E**: Full test file lifecycle from creation to integration

#### 7. TDD-Specific Test Categories

**TDD Models Testing:**
- **File**: `tests/unit/test_tdd_models.py` ✅
- **Coverage**: TDDCycle, TDDTask, TestFile, TestResult data models
- **Approach**: Unit tests for all model methods and state transitions

**Test File Lifecycle Testing:**
- **Files**: 
  - `tests/unit/test_test_file_lifecycle.py`
  - `tests/integration/test_test_preservation_workflow.py`
- **Coverage**: Test file creation, preservation, promotion, and integration
- **Approach**: Mock filesystem operations and git commands

**TDD Metrics and Analytics Testing:**
- **Files**:
  - `tests/unit/test_tdd_metrics.py`
  - `tests/integration/test_tdd_analytics.py`
- **Coverage**: TDD cycle time metrics, test coverage tracking, quality gates
- **Approach**: Time-series data validation and metric calculation testing

## Test Implementation Structure

### Mock Strategy
- **Discord API**: Mock discord.py interactions (including TDD command handling)
- **Anthropic API**: Mock AI model responses with realistic outputs for TDD phases
- **GitHub API**: Mock repository operations, CI results, and test file commits
- **File System**: Use temporary directories for state persistence (workflow + TDD)
- **Test Execution**: Mock test runners and coverage tools
- **CI/CD Systems**: Mock CI pipeline integration and test result reporting

### Test Data
- **Fixtures**: `tests/fixtures/`
  - Sample project configurations (including TDD settings)
  - Mock Discord interactions (workflow + TDD commands)
  - Predefined AI responses for TDD phases
  - Test state machine configurations (dual state machines)
  - **TDD Fixtures**:
    - Sample TDD cycles and tasks
    - Mock test files and test results
    - Test coverage data samples
    - TDD metrics test data

### Performance Tests
- **Load Testing**: Multiple concurrent projects
- **Stress Testing**: High-frequency command processing  
- **Memory Testing**: Long-running orchestrator instances

## Test Execution

### Continuous Testing
```bash
# Unit tests (fast feedback)
pytest tests/unit/ -v

# TDD-specific unit tests
pytest tests/unit/test_tdd_*.py -v

# Integration tests (moderate speed)
pytest tests/integration/ -v

# TDD integration tests
pytest tests/integration/*tdd*.py -v

# Full test suite (comprehensive)
pytest tests/ -v --cov=lib --cov=scripts

# TDD E2E tests
pytest test_tdd_e2e.py -v

# Performance tests (separate run)
pytest tests/performance/ -v
```

### Test Coverage Targets
- **Unit Tests**: ≥95% line coverage (including TDD modules)
- **Integration Tests**: ≥90% feature coverage (including TDD workflows)
- **E2E Tests**: 100% critical path coverage (including complete TDD cycles)
- **TDD Functionality**: ≥98% coverage for TDD state machine and data models
- **Test Preservation**: 100% coverage for test file lifecycle management

### Test Environment Setup
```bash
# Test dependencies
pip install pytest pytest-cov pytest-asyncio pytest-mock

# Discord testing with mock bot
export DISCORD_BOT_TOKEN="test_token"
export ANTHROPIC_API_KEY="test_key"

# Test database setup
mkdir -p tests/tmp
```

## Quality Gates

### Pre-commit Hooks
- Run unit tests
- Check code coverage
- Lint code style
- Validate type hints

### CI/CD Pipeline
1. **Fast Tests**: Unit tests on every commit
2. **Integration Tests**: On pull request
3. **E2E Tests**: On main branch merge
4. **Performance Tests**: Nightly runs

### Test-Driven Development Process
1. Write failing test for new feature
2. Implement minimal code to pass test  
3. Refactor while maintaining test coverage
4. Add integration tests for feature interactions
5. Add E2E test for user-facing workflows

## Test Scenarios Priority

### High Priority (Must Test)
- **Dual State Machine**: Workflow and TDD command validation
- **TDD State Transitions**: All TDD phase transitions and conditions
- **Test Preservation**: Test file lifecycle and preservation workflow
- HITL approval workflows (workflow + TDD decisions)
- **Enhanced Agent Execution**: TDD-capable agent task execution
- **Agent security and tool restrictions** ✅
- Discord command parsing (workflow + TDD commands)
- **Dual State Persistence**: Workflow and TDD state persistence
- **Agent TDD Coordination**: Handoffs between TDD phases

### Medium Priority (Should Test)  
- Multi-project coordination (with parallel TDD cycles)
- **TDD Error Handling**: Recovery from failed TDD phases
- **TDD Performance**: Performance under load with multiple TDD cycles
- **Dual State Visualization**: Both workflow and TDD state visualization
- Configuration management (including TDD settings)
- **TDD Metrics**: Cycle time tracking and quality metrics
- **Test Coverage Integration**: Coverage reporting and CI integration

### Low Priority (Nice to Test)
- Edge case error scenarios (including TDD edge cases)
- **TDD Stress Testing**: Many concurrent TDD cycles beyond normal limits
- UI polish and formatting (including TDD visualizations)
- Advanced Discord features (including TDD interactive elements)
- **TDD Analytics**: Advanced TDD metrics and reporting features
- **Test File Recovery**: Advanced test preservation recovery scenarios