# Troubleshooting

Common issues and solutions for the AI Agent TDD-Scrum workflow system.

## Discord Bot Issues

### Bot doesn't respond to commands

**Symptoms:** Commands are sent but no response from the bot.

**Solutions:**
1. Verify the Discord bot token is set correctly:
   ```bash
   echo $DISCORD_BOT_TOKEN
   ```
2. Check bot permissions in your Discord server:
   - Use Slash Commands
   - Send Messages
   - Embed Links
   - Read Message History
3. Ensure the bot was invited with the correct OAuth2 scopes:
   - `bot`
   - `applications.commands`

### Commands return "Unknown interaction"

**Symptoms:** Discord shows "This interaction failed" message.

**Solutions:**
1. Restart the bot to refresh slash command registration
2. Wait up to 1 hour for global commands to sync
3. Use guild-specific commands for faster testing

## Installation Issues

### Import errors or missing dependencies

**Symptoms:** `ModuleNotFoundError` when running the system.

**Solutions:**
1. Install all dependencies:
   ```bash
   pip install -r requirements.txt
   ```
2. Verify Python version (3.8+ required):
   ```bash
   python --version
   ```
3. Use a virtual environment to avoid conflicts:
   ```bash
   python -m venv venv
   source venv/bin/activate  # Linux/Mac
   # or
   venv\Scripts\activate     # Windows
   ```

### Tests failing

**Symptoms:** `pytest` command shows failures.

**Solutions:**
1. Run unit tests only (skip integration tests):
   ```bash
   pytest tests/unit/ -v
   ```
2. Install test dependencies:
   ```bash
   pip install pytest pytest-asyncio
   ```
3. Set required environment variables for integration tests:
   ```bash
   export DISCORD_BOT_TOKEN="test_token"
   ```

## State Machine Issues

### Invalid command errors

**Symptoms:** "Command not allowed in current state" messages.

**Solutions:**
1. Check current state:
   ```
   /state
   ```
2. Follow the proper command sequence:
   - `IDLE` → `/epic` → `BACKLOG_READY`
   - `BACKLOG_READY` → `/sprint plan` → `SPRINT_PLANNED`
   - `SPRINT_PLANNED` → `/sprint start` → `SPRINT_ACTIVE`
3. Use `/state` to see allowed commands for your current state

### Stuck in blocked state

**Symptoms:** System shows `BLOCKED` state and won't accept commands.

**Solutions:**
1. Use `/suggest_fix` to provide guidance to agents
2. Use `/skip_task` to abandon the current task
3. Restart the orchestrator if the state becomes corrupted

## Agent Issues

### Agents not executing tasks

**Symptoms:** Sprint starts but no progress is made.

**Solutions:**
1. Verify Claude Code integration is working:
   ```bash
   claude --version
   ```
2. Check agent permissions and tool access
3. Review orchestrator logs for error messages
4. Ensure project repository is properly configured

### AI responses are too verbose or incorrect

**Symptoms:** Agents produce low-quality output.

**Solutions:**
1. Provide more specific task descriptions
2. Use `/request_changes` to guide agent improvements
3. Check that agents have appropriate context about the project
4. Verify the AI model configuration

## Configuration Issues

### Multi-project setup not working

**Symptoms:** Only one project is managed, others are ignored.

**Solutions:**
1. Verify project configuration YAML syntax
2. Ensure each project has a unique identifier
3. Check that project paths are accessible
4. Review orchestrator logs for configuration errors

### Environment variables not recognized

**Symptoms:** "Environment variable not set" errors.

**Solutions:**
1. Set variables in your shell profile:
   ```bash
   echo 'export DISCORD_BOT_TOKEN="your_token"' >> ~/.bashrc
   source ~/.bashrc
   ```
2. Use a `.env` file for development:
   ```bash
   echo 'DISCORD_BOT_TOKEN=your_token' > .env
   ```
3. Verify variables are set in the current session:
   ```bash
   env | grep DISCORD
   ```

## Performance Issues

### Slow response times

**Symptoms:** Commands take longer than 30 seconds to respond.

**Solutions:**
1. Check network connectivity to Discord and AI services
2. Reduce the scope of tasks in sprints
3. Monitor system resources (CPU, memory)
4. Consider running fewer concurrent projects

### Memory usage growing over time

**Symptoms:** System memory usage increases during operation.

**Solutions:**
1. Restart the orchestrator periodically
2. Monitor for memory leaks in agent processes
3. Reduce the frequency of state saves
4. Clear old log files and temporary data

## TDD Workflow Issues

### TDD State Machine Problems

**Symptoms:** TDD commands return "not allowed in current state" errors.

**Solutions:**
1. Check current TDD state for the story:
   ```bash
   /tdd status <STORY_ID>
   ```
2. Follow the proper TDD sequence:
   - `DESIGN` → `/tdd test` → `TEST_RED`
   - `TEST_RED` → `/tdd commit-tests` → `CODE_GREEN`
   - `CODE_GREEN` → `/tdd commit-code` → `REFACTOR`
   - `REFACTOR` → `/tdd commit-refactor` → `COMMIT`
3. Use `/tdd next` to auto-advance to the logical next state
4. Check transition conditions with `/tdd status --verbose`

### TDD Cycle Failures

**Symptoms:** TDD cycles get stuck in specific phases without progressing.

**Common Scenarios:**

**Stuck in TEST_RED:**
```bash
# Check if tests are actually failing
/tdd run_tests <STORY_ID>

# Provide guidance to QA agent
/suggest_fix "Tests need to cover edge case for null input"

# Manual transition if tests are ready
/tdd commit-tests <STORY_ID>
```

**Stuck in CODE_GREEN:**
```bash
# Check test status
/tdd run_tests <STORY_ID>

# Review failing tests
/tdd status <STORY_ID> --show-failures

# Provide implementation guidance
/suggest_fix "Use bcrypt for password hashing in auth.py"

# Manual advance if tests are passing
/tdd commit-code <STORY_ID>
```

**Stuck in REFACTOR:**
```bash
# Check if refactoring broke tests
/tdd run_tests <STORY_ID>

# If tests are broken, automatic rollback occurs
# Otherwise provide refactoring guidance
/suggest_fix "Extract user validation into separate function"

# Complete refactoring
/tdd commit-refactor <STORY_ID>
```

### Test Preservation Problems

**Symptoms:** Test files not being preserved or committed properly.

**Solutions:**
1. Check test file status:
   ```bash
   /tdd status <STORY_ID> --show-files
   ```
2. Verify test directory structure:
   ```bash
   # Should exist: tests/tdd/<story-id>/
   # Check with: ls -la tests/tdd/
   ```
3. Manual test file commit:
   ```bash
   /tdd commit-tests <STORY_ID> --force
   ```
4. Check test file permissions and git status
5. Verify CI pipeline has access to test files

### Agent Coordination Issues in TDD

**Symptoms:** Multiple agents interfering with each other during TDD cycles.

**Solutions:**
1. Check agent assignments:
   ```bash
   /tdd status --show-agents
   ```
2. Pause conflicting cycles:
   ```bash
   /tdd pause <STORY_ID>
   ```
3. Review agent permissions and tool access:
   ```bash
   # QA Agent should only create tests in TEST_RED
   # Code Agent should only modify implementation in CODE_GREEN/REFACTOR
   ```
4. Use agent-specific guidance:
   ```bash
   /suggest_fix <STORY_ID> --agent QAAgent "Focus on integration tests"
   /suggest_fix <STORY_ID> --agent CodeAgent "Implement authentication logic"
   ```

### TDD Recovery Procedures

**Emergency Recovery:**
```bash
# Stop all TDD cycles
/tdd halt_all --confirm

# Reset specific TDD cycle
/tdd reset <STORY_ID> --to-state DESIGN

# Restart with preserved data
/tdd start <STORY_ID> --resume-from-backup
```

**Data Recovery:**
```bash
# Check TDD data integrity
/tdd validate <STORY_ID>

# Restore from backup
/tdd restore <STORY_ID> --from-timestamp 2024-01-15T10:30:00

# Manual state reconstruction
/tdd reconstruct <STORY_ID> --from-git-history
```

**Conflict Resolution:**
```bash
# When multiple agents modify same files
/tdd resolve_conflict <STORY_ID> --strategy merge
/tdd resolve_conflict <STORY_ID> --strategy agent-priority
/tdd resolve_conflict <STORY_ID> --strategy manual-review
```

### CI/CD Integration Issues

**Symptoms:** TDD cycles not triggering CI or CI failures blocking progress.

**Solutions:**
1. Check CI status for TDD workflow:
   ```bash
   /tdd ci_status <STORY_ID>
   ```
2. Retry failed CI runs:
   ```bash
   /tdd retry_ci <STORY_ID>
   ```
3. Override CI failures (with justification):
   ```bash
   /tdd override_ci <STORY_ID> --reason "Flaky test infrastructure"
   ```
4. Manual CI trigger:
   ```bash
   /tdd trigger_ci <STORY_ID> --tests-only
   ```

### Test Coverage Issues

**Symptoms:** TDD cycles failing due to insufficient test coverage.

**Solutions:**
1. Check coverage metrics:
   ```bash
   /tdd coverage <STORY_ID>
   ```
2. Adjust coverage thresholds:
   ```bash
   /tdd configure <STORY_ID> --coverage-threshold 85
   ```
3. Generate coverage reports:
   ```bash
   /tdd coverage_report <STORY_ID> --detailed
   ```
4. Guidance for improving coverage:
   ```bash
   /suggest_fix <STORY_ID> "Add tests for error handling paths"
   ```

### Performance Issues in TDD

**Symptoms:** TDD cycles taking too long or consuming excessive resources.

**Solutions:**
1. Check TDD cycle timing:
   ```bash
   /tdd metrics <STORY_ID> --timing
   ```
2. Optimize test execution:
   ```bash
   /tdd configure <STORY_ID> --parallel-tests --test-timeout 30s
   ```
3. Reduce scope of TDD cycles:
   ```bash
   /tdd split <STORY_ID> --max-tasks 3
   ```
4. Monitor resource usage:
   ```bash
   /tdd resources --show-memory --show-cpu
   ```

### TDD Configuration Issues

**Symptoms:** TDD workflows behaving unexpectedly due to configuration problems.

**Solutions:**
1. Validate TDD configuration:
   ```bash
   /tdd config validate
   ```
2. Reset to defaults:
   ```bash
   /tdd config reset --confirm
   ```
3. Export current configuration:
   ```bash
   /tdd config export > tdd_config_backup.yml
   ```
4. Check story-specific overrides:
   ```bash
   /tdd config show <STORY_ID>
   ```

### Common Error Messages

**"TDD cycle not found for story"**
- Story may not be in active sprint
- Use `/sprint status` to verify story inclusion
- Manually start TDD cycle: `/tdd start <STORY_ID>`

**"Tests already committed for this task"**
- TDD cycle has already progressed past TEST_RED
- Check current state: `/tdd status <STORY_ID>`
- Use `/tdd next` to advance to next logical state

**"No test files found in TDD directory"**
- QA Agent may not have created tests yet
- Check agent status and logs
- Manual test file creation may be needed

**"Test preservation directory not accessible"**
- File system permissions issue
- Check directory ownership and permissions
- Verify tests/tdd/ directory exists and is writable

### TDD Debugging Commands

**Detailed Status:**
```bash
/tdd debug <STORY_ID>
# Shows complete state machine status, agent assignments, file locations
```

**Trace TDD History:**
```bash
/tdd trace <STORY_ID>
# Shows complete history of state transitions and commands
```

**Validate TDD Integrity:**
```bash
/tdd integrity_check <STORY_ID>
# Validates data consistency and file integrity
```

## Getting Additional Help

If these solutions don't resolve your issue:

1. **Check the logs:** Look for error messages in the console output
2. **Use debug mode:** Run with increased verbosity for more details
3. **Review state:** Use `/state` command to understand system status
4. **Check TDD state:** Use `/tdd status <STORY_ID>` for TDD-specific issues
5. **Search documentation:** Check the [User Guide](hitl-commands.md) and [TDD Workflow](tdd-workflow.md) for command details
6. **Report issues:** Create an issue on the project repository with:
   - System information (OS, Python version)
   - Complete error messages
   - Steps to reproduce the problem
   - Expected vs actual behavior
   - TDD state and story information (for TDD issues)