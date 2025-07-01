# Multi-Project Integration Tests

Comprehensive integration test suite for the AI Agent TDD-Scrum Workflow multi-project system. This test suite validates backend API functionality, project switching capabilities, chat isolation, responsive design, and overall system integration.

## Test Modules

### 1. Backend API Tests (`test_multi_project_backend.py`)
Tests the backend API endpoints and data integrity:

- **Health and Status**: System health checks, state endpoints, debug information
- **Project Management API**: Project CRUD operations, configuration updates, state management
- **Chat API**: Message sending, history retrieval, autocomplete functionality
- **Collaboration API**: Session management, user permissions, project collaboration
- **Context Management API**: Context modes, switching, performance testing
- **Metrics and Monitoring**: Prometheus metrics, performance monitoring
- **Error Handling**: Malformed requests, concurrent operations, edge cases
- **Data Integrity**: Chat history persistence, state consistency, validation

### 2. Project Switching Tests (`test_project_switching.py`)
Tests project switching functionality and UI integration:

- **Project Switching API**: Switch validation, force switching, status monitoring
- **Project Switching UI**: WebSocket integration, state synchronization
- **State Preservation**: Chat history isolation, workflow state preservation, agent context
- **Project Validation**: Existence checks, dependency validation, state validation
- **Concurrent Operations**: Multiple switches, active operations, conflict resolution
- **Performance**: Switch timing, memory usage, bulk operations
- **Error Handling**: Nonexistent projects, corrupted state, network failures
- **End-to-End Integration**: Complete switching workflow with collaboration

### 3. Chat Isolation Tests (`test_chat_isolation.py`)
Tests chat functionality isolation and security:

- **Basic Chat Isolation**: Project-specific routing, user sessions, context isolation
- **WebSocket Chat Isolation**: Room separation, user isolation, typing indicators
- **Chat History Isolation**: Project-specific history, user filtering, session filtering
- **Command Isolation**: Project-specific commands, state isolation, autocomplete context
- **Concurrent Chat Operations**: Multi-project messages, WebSocket connections, race conditions
- **Chat Security Isolation**: Message sanitization, user permissions, information leakage
- **Recovery Mechanisms**: Connection failures, processing failures, error recovery

### 4. Responsive Design Tests (`test_responsive_design.py`)
Tests mobile responsiveness and accessibility:

- **Mobile Responsiveness**: Page loading, CSS optimization, JavaScript functionality, touch interfaces
- **Tablet Responsiveness**: Layout adaptation, interaction patterns, orientation handling
- **Desktop Responsiveness**: Full functionality, multi-column layouts, advanced features
- **Accessibility Features**: Semantic HTML, ARIA labels, keyboard navigation, color contrast
- **Cross-Browser Compatibility**: Chrome, Firefox, Safari, Edge compatibility
- **Performance Optimization**: Load times, API performance, caching, compression
- **Screen Size Adaptation**: Small, medium, large, ultra-wide screen support
- **User Experience**: Loading states, error handling, progressive enhancement, offline support

## Test Runners

### Comprehensive Test Runner (`run_multi_project_tests.py`)
Full-featured test runner with reporting and categorization:

```bash
# Run all tests
python tests/integration/run_multi_project_tests.py

# Run specific categories
python tests/integration/run_multi_project_tests.py --categories backend switching

# Fast mode (stop on first failure)
python tests/integration/run_multi_project_tests.py --fast

# Verbose output
python tests/integration/run_multi_project_tests.py --verbose

# Quick validation only
python tests/integration/run_multi_project_tests.py --quick

# List available categories
python tests/integration/run_multi_project_tests.py --list-categories
```

**Available Categories:**
- `backend`: Backend API endpoints and data integrity (CRITICAL)
- `switching`: Project switching and state synchronization (CRITICAL) 
- `isolation`: Chat isolation and security boundaries (CRITICAL)
- `responsive`: Mobile responsiveness and accessibility

### System Validator (`validate_multi_project_system.py`)
Live system validation for running instances:

```bash
# Validate running system
python tests/integration/validate_multi_project_system.py

# Custom URL
python tests/integration/validate_multi_project_system.py --url http://localhost:8080

# Quick health check only
python tests/integration/validate_multi_project_system.py --quick

# Save report to file
python tests/integration/validate_multi_project_system.py --output validation_report.json
```

**Validation Tests:**
- System health and connectivity
- API endpoint functionality
- Chat functionality
- Project isolation
- Context management
- Interface management
- Performance benchmarks
- Error handling

## Usage Examples

### Running Tests in Development

```bash
# Quick validation during development
cd /mnt/c/Users/jmontp/Documents/workspace/agent-workflow
python tests/integration/run_multi_project_tests.py --quick

# Full test suite
python tests/integration/run_multi_project_tests.py --verbose

# Test specific functionality
python tests/integration/run_multi_project_tests.py --categories backend isolation
```

### CI/CD Integration

```bash
# In CI pipeline
python tests/integration/run_multi_project_tests.py --fast
exit_code=$?

# Validate running system
python tests/integration/validate_multi_project_system.py --url $DEPLOYMENT_URL
validation_exit_code=$?

# Combine results
if [ $exit_code -eq 0 ] && [ $validation_exit_code -eq 0 ]; then
    echo "All tests passed"
    exit 0
else
    echo "Tests failed"
    exit 1
fi
```

### Manual Testing

```bash
# Start the system
cd tools/visualizer
python app.py &
APP_PID=$!

# Wait for startup
sleep 5

# Run validation
python ../../tests/integration/validate_multi_project_system.py

# Stop the system
kill $APP_PID
```

## Test Configuration

### Environment Variables
- `PYTEST_TIMEOUT`: Test timeout in seconds (default: 300)
- `TEST_BASE_URL`: Base URL for system validation (default: http://localhost:5000)
- `TEST_VERBOSE`: Enable verbose output (default: false)

### Mock Configuration
Tests use comprehensive mocking to isolate functionality:

```python
# Backend mocks
sys.modules['anthropic'] = MagicMock()
sys.modules['state_broadcaster'] = MagicMock()
sys.modules['lib.chat_state_sync'] = MagicMock()
sys.modules['lib.collaboration_manager'] = MagicMock()

# Test-specific mocks
mock_broadcaster.get_current_state.return_value = {
    "workflow_state": "IDLE",
    "projects": {"project-alpha": {"state": "ACTIVE"}},
    "last_updated": datetime.now().isoformat()
}
```

## Test Reports

### Summary Report
Text-based summary with module results:

```
Multi-Project Integration Test Summary
==================================================

Test Run: 2024-01-01 12:00:00
Total Duration: 45.67s
Modules Tested: 4

Overall Results:
  Passed: 127
  Failed: 3
  Errors: 0
  Skipped: 8

Module Results:
------------------------------

test_multi_project_backend:
  Status: passed
  Duration: 12.34s
  Passed: 45, Failed: 0
```

### JSON Report
Machine-readable report for CI/CD integration:

```json
{
  "test_run": {
    "timestamp": "2024-01-01T12:00:00",
    "total_duration": 45.67,
    "modules_tested": 4
  },
  "overall_stats": {
    "total_passed": 127,
    "total_failed": 3,
    "total_errors": 0,
    "total_skipped": 8
  },
  "module_results": [...]
}
```

### Validation Report
Live system validation results:

```json
{
  "validation_run": {
    "timestamp": "2024-01-01T12:00:00",
    "target_url": "http://localhost:5000",
    "total_duration": 15.23
  },
  "summary": {
    "total_tests": 8,
    "passed": 8,
    "failed": 0,
    "overall_success": true
  },
  "results": [...]
}
```

## Integration with Main Test Suite

### Adding to Makefile
```makefile
test-multi-project:
	python tests/integration/run_multi_project_tests.py

test-multi-project-quick:
	python tests/integration/run_multi_project_tests.py --quick

validate-system:
	python tests/integration/validate_multi_project_system.py

.PHONY: test-multi-project test-multi-project-quick validate-system
```

### Integration with pytest.ini
```ini
[tool:pytest]
testpaths = tests/unit tests/integration
python_files = test_*.py
python_classes = Test*
python_functions = test_*
markers =
    integration: marks tests as integration tests
    multi_project: marks tests as multi-project specific
    slow: marks tests as slow running
```

## Troubleshooting

### Common Issues

1. **Import Errors**
   ```bash
   # Ensure project root is in Python path
   export PYTHONPATH=/mnt/c/Users/jmontp/Documents/workspace/agent-workflow:$PYTHONPATH
   ```

2. **Mock Failures**
   ```python
   # Check mock setup in conftest.py or test files
   # Ensure all required modules are mocked
   ```

3. **Connection Errors**
   ```bash
   # Ensure system is running for validation tests
   python tools/visualizer/app.py &
   sleep 5
   python tests/integration/validate_multi_project_system.py
   ```

4. **Test Timeouts**
   ```bash
   # Increase timeout for slow environments
   python tests/integration/run_multi_project_tests.py --timeout 600
   ```

### Debug Mode

```bash
# Run with maximum verbosity
python tests/integration/run_multi_project_tests.py --verbose

# Run single test module
python -m pytest tests/integration/test_multi_project_backend.py -v -s

# Run specific test
python -m pytest tests/integration/test_multi_project_backend.py::TestHealthAndStatus::test_health_endpoint -v -s
```

## Contributing

### Adding New Tests

1. **Create test module**: Follow naming convention `test_*.py`
2. **Add to runner**: Update `TEST_MODULES` and `TEST_CATEGORIES` in runner
3. **Document tests**: Add description to this README
4. **Include mocks**: Ensure proper mocking for isolation

### Test Categories

- **CRITICAL**: Must pass for system functionality
- **NON-CRITICAL**: Important but not blocking

### Performance Standards

- **Unit tests**: < 1s per test
- **Integration tests**: < 30s per module
- **System validation**: < 60s total
- **API responses**: < 1s average

## Architecture Notes

### Test Isolation
- Each test module is independent
- Comprehensive mocking prevents external dependencies
- Temporary directories for file operations
- Clean state between tests

### Multi-Project Focus
- Tests specifically validate multi-project capabilities
- Project isolation and switching
- Concurrent project operations
- Cross-project security boundaries

### Real-World Scenarios
- Tests simulate actual usage patterns
- Error conditions and edge cases
- Performance under load
- Recovery mechanisms

This comprehensive test suite ensures the multi-project system works correctly across all components and use cases, providing confidence in deployments and system reliability.