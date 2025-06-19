# Unit Test Suite Documentation

This document provides comprehensive documentation for the unit test suite in the `tests/unit/` directory. The unit tests are designed to achieve government audit compliance (TIER 3-5) with >95% code coverage and comprehensive edge case testing.

## Test Categories Overview

### 1. State Machine & Workflow Tests
**Core workflow validation and state transition testing**

- `test_state_machine.py` - Main state machine (HITL workflow) with comprehensive transition validation
- `test_tdd_state_machine.py` - TDD-specific state machine testing with commit workflow validation
- `test_tdd_models.py` - TDD data models (cycles, tasks, test results)
- `test_data_models.py` - Core data models (epics, stories, sprints)

**Key Testing Patterns:**
- Table-driven transition validation
- State condition checking
- Mermaid diagram generation
- Error message quality validation
- Complex workflow sequence testing

### 2. Agent System Tests
**Agent implementation, security, and coordination testing**

#### Core Agent Tests
- `test_agents_base_agent.py` - Base agent class functionality
- `test_agents_code_agent.py` - Code agent implementation
- `test_agents_design_agent.py` - Design agent implementation  
- `test_agents_qa_agent.py` - QA agent implementation
- `test_agents_data_agent.py` - Data agent implementation

#### Agent Tool Security & Configuration
- `test_agent_tool_config.py` - **Primary security test file**
- `test_agent_tool_config_comprehensive_security.py` - Enhanced security coverage
- `test_agent_tool_config_security_coverage.py` - Security boundary validation

**Security Testing Focus:**
- Command access control validation
- Agent-specific tool restrictions
- TDD phase access permissions
- Claude CLI argument generation
- Principle of least privilege enforcement

#### Agent Coordination & Memory
- `test_agent_pool.py` - Agent pool management
- `test_agent_memory.py` - Agent memory system (40 tests)
- `test_agent_memory_enhanced_coverage.py` - Memory edge cases (26 tests)
- `test_agent_memory_final_coverage.py` - Final coverage push (14 tests)
- `test_mock_agent.py` - Mock agent for testing

### 3. Context Management Tests
**Advanced context processing and intelligence systems**

#### Core Context Components
- `test_context_manager.py` - Context manager core functionality
- `test_context_index.py` - Searchable codebase indexing
- `test_context_cache.py` - Context caching mechanisms
- `test_context_compressor.py` - Context compression algorithms
- `test_context_filter.py` - Context filtering and relevance

#### Context Intelligence & Analysis
- `test_context_intelligence.py` - AI-powered context analysis
- `test_context_learning.py` - Context learning patterns
- `test_context_monitoring.py` - Context usage monitoring
- `test_cross_project_intelligence.py` - Multi-project context sharing

#### Coverage Enhancement Files
- `test_context_*_coverage.py` - Comprehensive coverage tests for TIER 3-5 compliance
- `test_context_*_final_coverage.py` - Final coverage optimization
- `test_context_manager_government_audit_final.py` - Government audit compliance

### 4. Discord Bot & Multi-Project Tests
**HITL interface and multi-project orchestration**

- `test_discord_bot.py` - Core Discord bot functionality
- `test_discord_bot_comprehensive.py` - Comprehensive Discord testing
- `test_discord_bot_audit_compliance.py` - Government audit compliance
- `test_multi_project_*.py` - Multi-project orchestration testing
- `test_multi_project_security.py` - Multi-project security validation

### 5. Infrastructure & Integration Tests
**Core system infrastructure and external integrations**

- `test_claude_client.py` - Claude client integration
- `test_project_storage.py` - File-based project persistence
- `test_global_orchestrator.py` - Global orchestration engine
- `test_state_broadcaster.py` - State broadcasting system
- `test_resource_scheduler.py` - Resource scheduling
- `test_conflict_resolver.py` - Conflict resolution

### 6. TDD Framework Tests
**Test-Driven Development specific functionality**

- `test_tdd_agents.py` - TDD agent specializations
- `test_parallel_tdd_*.py` - Parallel TDD execution
- `test_token_calculator.py` - Token usage calculation

## Testing Infrastructure

### Mock Framework
**Location: `tests/mocks/`**

Enterprise-grade mocking infrastructure for external dependencies:
- `discord_mocks.py` - Discord API mocking
- `websocket_mocks.py` - WebSocket communications
- `github_mocks.py` - GitHub API mocking
- `filesystem_mocks.py` - File system operations
- `async_fixtures.py` - Async test patterns

### Configuration
**Location: `tests/pytest.ini`**

Comprehensive pytest configuration including:
- Test markers (slow, integration, security, etc.)
- Output formatting and logging
- Asyncio support
- Timeout configuration
- Parallel execution support

## Testing Strategies & Patterns

### 1. State Machine Testing Pattern
**Comprehensive state transition validation**

```python
def test_valid_transitions(self):
    """Test all valid state transitions according to specification"""
    test_cases = [
        # (start_state, command, expected_end_state)
        (State.IDLE, "/epic", State.BACKLOG_READY),
        (State.BACKLOG_READY, "/sprint plan", State.SPRINT_PLANNED),
        # ... more transitions
    ]
    
    for start_state, command, expected_end_state in test_cases:
        with self.subTest(start_state=start_state, command=command):
            # Test logic...
```

### 2. Security Validation Pattern
**Agent tool access control testing**

```python
def test_agent_restrictions(self):
    """Test that agents have appropriate tool restrictions"""
    allowed = get_allowed_tools(AgentType.DESIGN)
    disallowed = get_disallowed_tools(AgentType.DESIGN)
    
    # Validate security boundaries
    for dangerous_cmd in RESTRICTED_COMMANDS:
        self.assertIn(f"Bash({dangerous_cmd})", disallowed)
```

### 3. Coverage Enhancement Pattern
**Systematic coverage improvement**

Files follow a progression pattern:
1. `test_*.py` - Base functionality testing
2. `test_*_coverage.py` - Enhanced edge case coverage
3. `test_*_final_coverage.py` - Target specific uncovered lines
4. `test_*_government_audit_final.py` - Government compliance

### 4. Mock Integration Pattern
**Consistent mock usage across tests**

```python
from tests.mocks import MockDiscordBot, MockFileSystem

class TestWithMocks(unittest.TestCase):
    def setUp(self):
        self.mock_discord = MockDiscordBot()
        self.mock_fs = MockFileSystem()
```

### 5. Async Testing Pattern
**Comprehensive async operation testing**

```python
@pytest.mark.asyncio
async def test_async_functionality(self):
    """Test async operations with proper setup/teardown"""
    # Async test implementation
```

## Coverage Targets & Achievement

### Government Audit Compliance Levels
- **TIER 3**: 90%+ coverage, comprehensive error handling
- **TIER 4**: 95%+ coverage, security validation, performance metrics
- **TIER 5**: 98%+ coverage, complete edge case coverage

### Coverage Summary by Component
- **State Machine**: 95%+ (comprehensive transition coverage)
- **Agent System**: 92-95% (security-focused testing)
- **Context Management**: 95%+ (TIER 3 compliant)
- **Discord Bot**: 95%+ (audit compliant)
- **Project Storage**: 95%+ (complete persistence coverage)

### Coverage Enhancement Files
Files with `*_coverage.py`, `*_final_coverage.py` naming pattern specifically target uncovered lines and edge cases for audit compliance.

## Running Tests

### Run All Unit Tests
```bash
pytest tests/unit/ -v
```

### Run Specific Test Categories
```bash
# State machine tests
pytest tests/unit/test_*state_machine*.py -v

# Agent security tests
pytest tests/unit/test_agent_tool_config*.py -v

# Context management tests
pytest tests/unit/test_context_*.py -v

# Coverage-focused tests
pytest tests/unit/test_*_coverage.py -v
```

### Run Tests by Marker
```bash
# Security tests
pytest tests/unit/ -m security -v

# Slow tests
pytest tests/unit/ -m slow -v

# Skip slow tests
pytest tests/unit/ -m "not slow" -v
```

### Run with Coverage
```bash
pytest tests/unit/ --cov=lib --cov-report=html --cov-report=term-missing
```

## Key Test Quality Features

### 1. Government Audit Compliance
- Systematic error scenario testing
- Security input validation
- Resource management verification
- Performance monitoring integration
- Complete audit trail capability

### 2. Production-Ready Testing
- Comprehensive mock infrastructure
- Async operation validation
- Concurrent access testing
- Database transaction safety
- Memory leak prevention

### 3. Security Boundary Testing
- Agent tool access control validation
- Command injection prevention
- Input sanitization verification
- Privilege escalation prevention
- Cross-agent security isolation

### 4. Performance Validation
- Timing measurement and limits
- Memory usage tracking
- Cache hit rate monitoring
- Resource utilization validation
- Scalability boundary testing

## Test Maintenance Guidelines

### 1. Adding New Tests
- Follow existing naming conventions
- Use appropriate test markers
- Include edge case testing
- Validate error conditions
- Document test purpose clearly

### 2. Coverage Enhancement
- Target specific uncovered lines
- Add comprehensive error scenarios
- Include boundary condition testing
- Validate security implications
- Test concurrent operations

### 3. Mock Usage
- Use consistent mock patterns
- Validate mock behavior realism
- Include failure scenario testing
- Test timeout handling
- Verify cleanup operations

### 4. Security Testing
- Test all agent access boundaries
- Validate command restrictions
- Include privilege escalation tests
- Test input sanitization
- Verify security configuration

## Documentation Files

### Test Summaries
- `TEST_SUMMARY.md` - Context index test coverage summary
- `AGENT_MEMORY_COVERAGE_SUMMARY.md` - Agent memory coverage details

### Coverage Reports
Generated coverage reports provide detailed line-by-line analysis for audit compliance validation.

## Integration with CI/CD

The unit test suite is designed for integration with continuous integration systems:
- Parallel execution support
- Configurable test selection
- Comprehensive reporting
- Performance metrics tracking
- Security validation automation

This unit test suite provides the foundation for reliable, secure, and auditable AI agent workflow orchestration with comprehensive coverage and enterprise-grade quality assurance.