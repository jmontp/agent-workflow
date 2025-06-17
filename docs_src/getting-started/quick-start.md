# Quick Start Guide

Get the AI Agent TDD-Scrum Workflow system running in under 5 minutes.

## Prerequisites

- **Python 3.8+** installed
- **Discord Bot Token** (see [Discord Setup](../deployment/discord-setup.md))
- **Git** for cloning the repository

## 1. Clone and Install

```bash
# Clone the repository
git clone https://github.com/jmontp/agent-workflow.git
cd agent-workflow

# Install dependencies
make install
```

Or manually:
```bash
pip install -r requirements.txt
```

## 2. Configure Environment

Set up your Discord bot token:

```bash
export DISCORD_BOT_TOKEN="your_discord_bot_token_here"
```

**Note:** The system works without AI integration for testing. For full AI capabilities, you can integrate with Claude Code or other AI services.

## 3. Run the System

### Option A: Discord Bot (Recommended)
```bash
make run
```

This starts the Discord bot with the orchestrator backend.

### Option B: Orchestrator Only
```bash
make orchestrator
```

This runs the orchestrator without Discord integration (useful for testing).

## 4. Test in Discord

1. **Invite your bot** to a Discord server
2. **Try basic commands**:
   ```
   /state
   /epic "Build a todo app"
   /approve
   /sprint plan
   /sprint start
   ```

3. **Monitor TDD workflow**:
   ```
   /tdd overview
   /tdd status TODO-1
   /sprint status
   ```

## 5. Verify Installation

Run the test suite to ensure everything works:

```bash
make test
```

## Example TDD Workflow

Once your system is running, try this complete TDD workflow:

```bash
# 1. Create epic and stories
/epic "Build user authentication system"
/approve AUTH-1 AUTH-2

# 2. Plan and start sprint
/sprint plan AUTH-1 AUTH-2
/sprint start

# 3. Monitor TDD progress
/tdd overview
# Shows: AUTH-1 in DESIGN phase, AUTH-2 in DESIGN phase

# 4. Check specific story progress
/tdd status AUTH-1
# Shows: "AUTH-1 in TEST_RED phase - 12 failing tests written"

# 5. Review TDD cycle if needed
/tdd review_cycle AUTH-1

# 6. Monitor sprint completion
/sprint status
# Shows overall sprint progress with TDD cycle status
```

## Next Steps

- [**Read the TDD Workflow Guide**](../user-guide/tdd-workflow.md) for complete TDD implementation
- [**Read the User Guide**](../user-guide/hitl-commands.md) for complete command reference
- [**Configure Projects**](configuration.md) for multi-project setups
- [**Explore Workflows**](../user-guide/workflow-sequences.md) for common usage patterns

## Troubleshooting

### Common Issues

**Bot doesn't respond to commands:**
- Verify `DISCORD_BOT_TOKEN` is set correctly
- Check bot permissions in Discord server
- Ensure bot is invited with appropriate scopes

**Import errors:**
- Run `make install` to ensure all dependencies are installed
- Check Python version is 3.8+

**Tests failing:**
- Some tests require Discord token for integration tests
- Use `make test-unit` to run only unit tests

### Getting Help

- Check the `/state` command in Discord to see system status
- Review logs for error messages
- See [Contributing Guide](../development/contributing.md) for support options

---

**Success!** Your AI Agent TDD-Scrum Workflow system is now running. Start with `/epic "Your first project"` in Discord.