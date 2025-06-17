# Testing Plan - AI Agent TDD-Scrum Workflow

## Testing Strategy

### Test Pyramid
1. **Unit Tests (70%)** - Individual component testing
2. **Integration Tests (20%)** - Component interaction testing  
3. **End-to-End Tests (10%)** - Full workflow testing

### Test Categories

#### 1. State Machine Tests
- **File**: `tests/unit/test_state_machine.py`
- **Coverage**: All state transitions and command validations
- **Approach**: Table-driven tests with (current_state, command) → expected_result

```python
test_cases = [
    ("IDLE", "/epic", "BACKLOG_READY", True),
    ("IDLE", "/sprint start", "IDLE", False),  # Invalid transition
    ("SPRINT_ACTIVE", "/sprint pause", "SPRINT_PAUSED", True),
    # ... comprehensive matrix
]
```

#### 2. Agent Library Tests
- **Files**: 
  - `tests/unit/test_base_agent.py`
  - `tests/unit/test_design_agent.py`
  - `tests/unit/test_code_agent.py`
  - `tests/unit/test_qa_agent.py`
  - `tests/unit/test_data_agent.py`
- **Coverage**: 
  - Agent initialization and configuration
  - Task execution with dry-run mode
  - Error handling and retry logic
  - Anthropic API integration (mocked)

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
- **Coverage**:
  - Discord → Orchestrator → Agent workflows
  - State machine integration with Discord UI
  - Multi-agent task coordination
  - Project state persistence across restarts

#### 6. End-to-End Tests
- **Files**:
  - `tests/e2e/test_complete_workflow.py`
  - `tests/e2e/test_approval_scenarios.py`
- **Coverage**:
  - Complete epic → sprint → implementation workflow
  - HITL approval gates and escalation
  - Multi-project orchestration scenarios
  - Error recovery and retry scenarios

## Test Implementation Structure

### Mock Strategy
- **Discord API**: Mock discord.py interactions
- **Anthropic API**: Mock AI model responses with realistic outputs
- **GitHub API**: Mock repository operations and CI results
- **File System**: Use temporary directories for state persistence

### Test Data
- **Fixtures**: `tests/fixtures/`
  - Sample project configurations
  - Mock Discord interactions
  - Predefined AI responses
  - Test state machine configurations

### Performance Tests
- **Load Testing**: Multiple concurrent projects
- **Stress Testing**: High-frequency command processing  
- **Memory Testing**: Long-running orchestrator instances

## Test Execution

### Continuous Testing
```bash
# Unit tests (fast feedback)
pytest tests/unit/ -v

# Integration tests (moderate speed)
pytest tests/integration/ -v

# Full test suite (comprehensive)
pytest tests/ -v --cov=lib --cov=scripts

# Performance tests (separate run)
pytest tests/performance/ -v
```

### Test Coverage Targets
- **Unit Tests**: ≥95% line coverage
- **Integration Tests**: ≥90% feature coverage
- **E2E Tests**: 100% critical path coverage

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
- State machine command validation
- HITL approval workflows
- Agent task execution
- Discord command parsing
- Project state persistence

### Medium Priority (Should Test)  
- Multi-project coordination
- Error handling and recovery
- Performance under load
- State visualization
- Configuration management

### Low Priority (Nice to Test)
- Edge case error scenarios
- Stress testing beyond normal limits
- UI polish and formatting
- Advanced Discord features