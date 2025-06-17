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

## Getting Additional Help

If these solutions don't resolve your issue:

1. **Check the logs:** Look for error messages in the console output
2. **Use debug mode:** Run with increased verbosity for more details
3. **Review state:** Use `/state` command to understand system status
4. **Search documentation:** Check the [User Guide](hitl-commands.md) for command details
5. **Report issues:** Create an issue on the project repository with:
   - System information (OS, Python version)
   - Complete error messages
   - Steps to reproduce the problem
   - Expected vs actual behavior