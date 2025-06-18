# Testing and Validation

This guide covers the testing capabilities of the AI Agent TDD-Scrum workflow system, including the real-time visualizer and NO-AGENT mode for state machine validation.

## Overview

The system provides two key testing features:

1. **Real-Time Visualizer**: WebSocket-based visualization of workflow and TDD state transitions
2. **NO-AGENT Mode**: Mock agents for testing state machine logic without AI API calls

## Real-Time Visualizer

The real-time visualizer provides live monitoring of workflow states, TDD cycles, and agent activities through a WebSocket interface.

### Setup

1. **Install Dependencies**
   ```bash
   pip install Flask Flask-SocketIO websockets
   ```

2. **Start the Visualizer**
   ```bash
   # In the visualizer directory
   cd visualizer
   python app.py
   ```

3. **Start the State Broadcaster**
   ```python
   # In your orchestrator or as a separate service
   import asyncio
   from lib.state_broadcaster import start_broadcaster
   
   async def main():
       await start_broadcaster(port=8080)
   
   asyncio.run(main())
   ```

4. **Access the Interface**
   - Open your browser to `http://localhost:5000`
   - The visualizer will connect to the WebSocket server on port 8080

### Features

#### Workflow State Monitoring
- Real-time display of main workflow states (IDLE → BACKLOG_READY → SPRINT_PLANNED → SPRINT_ACTIVE → SPRINT_REVIEW)
- Visual transitions with timestamps
- Project-specific state tracking

#### TDD Cycle Visualization
- Live TDD state transitions (DESIGN → TEST_RED → CODE_GREEN → REFACTOR → COMMIT)
- Story-level TDD cycle monitoring
- Test execution and commit activity

#### Agent Activity Tracking
- Agent task start/complete/failed events
- Agent coordination and handoffs
- Performance metrics and timing

### WebSocket Events

The system emits the following event types:

```javascript
// Workflow transitions
{
  "type": "workflow_transition",
  "timestamp": "2024-01-01T12:00:00Z",
  "project": "my-project",
  "old_state": "IDLE",
  "new_state": "BACKLOG_READY"
}

// TDD transitions
{
  "type": "tdd_transition",
  "timestamp": "2024-01-01T12:00:00Z",
  "project": "my-project",
  "story_id": "AUTH-1",
  "old_state": "DESIGN",
  "new_state": "TEST_RED"
}

// Agent activity
{
  "type": "agent_activity",
  "timestamp": "2024-01-01T12:00:00Z",
  "project": "my-project",
  "story_id": "AUTH-1",
  "agent_type": "QAAgent",
  "action": "task_execution",
  "status": "completed"
}
```

## NO-AGENT Mode

NO-AGENT mode replaces real AI agents with mock implementations, allowing you to test state machine logic, data flow, and integration points without making actual AI API calls.

### Setup

1. **Enable NO-AGENT Mode**
   ```bash
   export NO_AGENT_MODE=true
   ```

2. **Run the System**
   ```bash
   # All agents will now use mock implementations
   python scripts/orchestrator.py
   ```

3. **Or Set in Code**
   ```python
   import os
   os.environ['NO_AGENT_MODE'] = 'true'
   
   # Now create agents - they will be mock agents
   from lib.agents import create_agent
   agent = create_agent("DesignAgent")  # Returns MockDesignAgent
   ```

### Mock Agent Behavior

Mock agents simulate realistic behavior:

#### Execution Times
- **Design tasks**: 1.5-3 seconds
- **Test tasks**: 2-4 seconds  
- **Code tasks**: 3-6 seconds
- **Refactor tasks**: 2-4 seconds
- **Analysis tasks**: 1-2.5 seconds

#### Failure Simulation
- 10% random failure rate for testing error handling
- Realistic error messages and recovery suggestions
- Proper logging and state transitions

#### Response Generation
Mock agents generate context-appropriate responses:

```python
# Design Agent Mock Response
"""
MockDesignAgent: Design specifications completed for AUTH-1

# Mock Technical Specification

## Overview
Mock implementation specifications generated for testing purposes.

## Acceptance Criteria
- ✅ Mock criteria 1: Basic functionality validated
- ✅ Mock criteria 2: Error handling specifications
- ✅ Mock criteria 3: Integration requirements defined
"""
```

### Agent Types Available

All agent types have mock implementations:

- **MockDesignAgent**: TDD specification and design
- **MockQAAgent**: Failing test creation and validation
- **MockCodeAgent**: Implementation and refactoring
- **MockDataAgent**: Analytics and reporting

## Validation Workflows

### Complete State Machine Testing

Test the entire workflow with mock agents:

```bash
# 1. Enable NO-AGENT mode
export NO_AGENT_MODE=true

# 2. Start real-time visualizer
cd visualizer && python app.py &

# 3. Start orchestrator with broadcasting
python scripts/orchestrator.py &

# 4. Run through complete workflow
# In Discord or via API:
/epic "User Authentication System"
/sprint plan
/sprint start
/tdd start AUTH-1 "Login endpoint implementation"
/tdd design
/tdd test
/tdd code
/tdd refactor
/tdd commit
```

### TDD Cycle Validation

Test TDD state machine transitions:

```bash
# Start a TDD cycle
/tdd start AUTH-1 "User login endpoint"

# Follow TDD workflow
/tdd design      # DESIGN state
/tdd test        # → TEST_RED
/tdd commit-tests # Commit failing tests  
/tdd code        # → CODE_GREEN
/tdd commit-code # Commit implementation
/tdd refactor    # → REFACTOR
/tdd commit-refactor # → COMMIT

# Check status and logs
/tdd status
/tdd logs AUTH-1
/tdd overview
```

### Error Handling Testing

Test error conditions and recovery:

```bash
# Test invalid transitions
/tdd code  # Should fail in DESIGN state
/tdd refactor  # Should fail before CODE_GREEN

# Test failure recovery (mock agents will occasionally fail)
# Retry mechanisms and escalation workflows

# Test resource limits
# Start multiple TDD cycles to test concurrency limits
```

## Performance Testing

### Load Testing with Mock Agents

```python
# Generate load with multiple concurrent tasks
import asyncio
from lib.agents import create_agent

async def load_test():
    agents = [create_agent("CodeAgent") for _ in range(10)]
    tasks = []
    
    for i, agent in enumerate(agents):
        task = Task(
            id=f"load-test-{i}",
            agent_type="CodeAgent", 
            command=f"Implement feature {i}",
            context={"story_id": f"LOAD-{i}"}
        )
        tasks.append(agent.run(task))
    
    results = await asyncio.gather(*tasks)
    # Analyze timing and success rates

asyncio.run(load_test())
```

### Metrics Collection

Monitor performance through the visualizer:

- Agent execution times
- State transition frequencies  
- Error rates and patterns
- Resource utilization

## Troubleshooting

### Common Issues

#### Visualizer Not Connecting
```bash
# Check WebSocket server
netstat -an | grep 8080

# Check state broadcaster logs
tail -f logs/state_broadcaster.log
```

#### Mock Agents Not Loading
```bash
# Verify environment variable
echo $NO_AGENT_MODE

# Check import paths
python -c "from lib.agents.mock_agent import MockAgent; print('OK')"
```

#### State Broadcasting Fails
```bash
# Check for missing dependencies
pip install websockets

# Verify graceful fallback
python -c "from lib.state_machine import StateMachine; sm = StateMachine(); print('OK')"
```

### Debug Mode

Enable detailed logging:

```python
import logging
logging.basicConfig(level=logging.DEBUG)

# Run with debug logging
python scripts/orchestrator.py
```

### Validation Checklist

- [ ] Real-time visualizer connects and displays states
- [ ] NO-AGENT mode successfully replaces real agents  
- [ ] Mock agents generate realistic responses and timing
- [ ] State machine transitions broadcast correctly
- [ ] TDD cycles complete successfully with mock agents
- [ ] Error handling and recovery workflows function
- [ ] Performance metrics are collected and displayed
- [ ] All integration points work with mock implementations

## Integration Testing

### End-to-End Workflow

Complete integration test with visualization:

1. **Setup Environment**
   ```bash
   export NO_AGENT_MODE=true
   pip install Flask Flask-SocketIO websockets
   ```

2. **Start Services**
   ```bash
   # Terminal 1: Visualizer
   cd visualizer && python app.py
   
   # Terminal 2: Orchestrator with broadcasting
   python scripts/orchestrator.py
   ```

3. **Execute Test Sequence**
   ```bash
   # Create epic and stories
   /epic "Complete Authentication System"
   /backlog add_story "User registration endpoint" 
   /backlog add_story "User login endpoint"
   /backlog add_story "Password reset flow"
   
   # Plan and start sprint
   /sprint plan
   /sprint start
   
   # Execute TDD cycles for each story
   /tdd start AUTH-1 "Registration endpoint"
   # ... complete TDD cycle
   
   /tdd start AUTH-2 "Login endpoint"  
   # ... complete TDD cycle
   
   # Complete sprint
   /sprint status
   /feedback "Sprint completed successfully"
   ```

4. **Validate Results**
   - Check visualizer shows all transitions
   - Verify state consistency
   - Confirm mock agents executed correctly
   - Review performance metrics

This comprehensive testing approach ensures the system functions correctly at all levels while providing visibility into the workflow execution process.