# Configuration

Configure the AI Agent TDD-Scrum workflow system for your development environment.

## Environment Variables

### Required Configuration

**`DISCORD_BOT_TOKEN`**
Your Discord bot token for the HITL interface.
```bash
export DISCORD_BOT_TOKEN="your_discord_bot_token_here"
```

### Optional Configuration

**`ANTHROPIC_API_KEY`** (for Claude integration)
```bash
export ANTHROPIC_API_KEY="your_anthropic_api_key"
```

**`GITHUB_TOKEN`** (for enhanced GitHub integration)
```bash
export GITHUB_TOKEN="your_github_personal_access_token"
```

## Project Configuration

### Single Project Setup

For managing a single project, create a simple configuration:

```yaml
# config.yml
orchestrator:
  mode: blocking  # blocking, partial, or autonomous
  project_path: "/path/to/your/project"
  project_name: "my-project"
```

### Multi-Project Setup

For managing multiple projects simultaneously:

```yaml
# config.yml
orchestrator:
  mode: blocking
  projects:
    - name: "web-app"
      path: "/path/to/web-app"
      mode: partial
    - name: "api-service" 
      path: "/path/to/api-service"
      mode: autonomous
    - name: "mobile-app"
      path: "/path/to/mobile-app"
      mode: blocking
```

## Orchestration Modes

### Blocking Mode
- Human approval required for all strategic decisions
- Safest option for critical projects
- Recommended for learning the system

### Partial Mode
- Agents execute with quarantined output for review
- Balanced automation with oversight
- Good for established workflows

### Autonomous Mode
- Full execution with monitoring and alerts
- Highest automation level
- Use only for well-tested processes

## Discord Configuration

### Bot Setup

1. Create a Discord application at [Discord Developer Portal](https://discord.com/developers/applications)
2. Create a bot and copy the token
3. Invite the bot to your server with these permissions:
   - Use Slash Commands
   - Send Messages
   - Embed Links
   - Read Message History

### Channel Configuration

The system automatically creates project-specific channels:
- Format: `hostname-projectname`
- Example: `macbook-web-app`, `ubuntu-api-service`

## Agent Configuration

### AI Integration

**Claude Code Integration:**
```bash
# Install Claude Code CLI
pip install claude-code

# Verify installation
claude --version
```

**Alternative AI Services:**
The system supports pluggable AI integrations. Implement the `BaseAgent` interface for custom AI services.

### Security Settings

Agent tool access is configured in `lib/agent_tool_config.py`:

```python
AGENT_SECURITY_PROFILES = {
    "DesignAgent": {
        "allowed_tools": ["read", "web_search", "documentation"],
        "blocked_tools": ["edit", "git", "system"]
    },
    "CodeAgent": {
        "allowed_tools": ["read", "edit", "git_add", "git_commit", "test"],
        "blocked_tools": ["git_push", "system", "delete"]
    }
    # ... other agents
}
```

## File Locations

### Configuration Files
- Main config: `config.yml` (repository root)
- User preferences: `~/.agent-workflow/preferences.yml`
- Project state: `<project>/.orch-state/status.json`

### Log Files
- System logs: `logs/orchestrator.log`
- Agent logs: `logs/agents/<agent-type>.log`
- Discord logs: `logs/discord-bot.log`

## Performance Tuning

### Resource Limits
```yaml
orchestrator:
  max_concurrent_projects: 3
  agent_timeout_minutes: 30
  state_save_interval_seconds: 60
```

### Discord Rate Limiting
```yaml
discord:
  max_commands_per_minute: 20
  response_timeout_seconds: 30
```

## Troubleshooting Configuration

### Common Issues

**Environment variables not recognized:**
```bash
# Check current environment
env | grep -E "(DISCORD|ANTHROPIC|GITHUB)"

# Set in shell profile for persistence
echo 'export DISCORD_BOT_TOKEN="your_token"' >> ~/.bashrc
source ~/.bashrc
```

**Configuration file not found:**
```bash
# Create default configuration
cp config.example.yml config.yml
# Edit with your settings
```

**Permission errors:**
```bash
# Ensure proper file permissions
chmod 600 config.yml  # Restrict access to config file
chmod +x scripts/orchestrator.py  # Make scripts executable
```

### Validation

Test your configuration:
```bash
# Validate configuration syntax
python -c "import yaml; yaml.safe_load(open('config.yml'))"

# Test Discord connection
python scripts/test-discord.py

# Test AI integration
python scripts/test-agents.py
```

## Next Steps

After configuration:
1. [Run the quick start guide](quick-start.md)
2. [Set up your first project](../user-guide/project-setup.md)
3. [Learn the HITL commands](../user-guide/hitl-commands.md)