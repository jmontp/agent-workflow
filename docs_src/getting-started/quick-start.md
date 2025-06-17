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

## 5. Verify Installation

Run the test suite to ensure everything works:

```bash
make test
```

## Next Steps

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