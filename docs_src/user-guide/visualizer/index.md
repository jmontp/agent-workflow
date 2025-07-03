# Visualizer Quick Start Guide

The Visualizer provides a real-time web interface for monitoring AI agent workflows, project states, and multi-project orchestration.

## Quick Start

### 1. Launch the Visualizer

```bash
# Start the web interface
aw web

# Or specify custom port
aw web --port 8080
```

### 2. Access the Interface

Open your browser to `http://localhost:5000` (or your custom port)

### 3. Key Features at a Glance

- **Project Switching**: Use the dropdown to switch between registered projects
- **Real-time State Diagrams**: Watch workflow progress in live Mermaid diagrams
- **Discord-style Chat**: Send commands and see responses in real-time
- **Multi-project Management**: Monitor multiple projects simultaneously

## Common Tasks

### Switch Projects
1. Click the project dropdown in the top-left
2. Select your target project
3. Chat and state will automatically switch context

### Send Commands
1. Use the chat interface on the right panel
2. Type slash commands like `/state` or `/epic "new feature"`
3. See real-time responses from AI agents

### Monitor Workflow
1. State diagrams update automatically
2. Green nodes indicate completed states
3. Current state is highlighted in blue

## Troubleshooting

### Interface Not Loading
- Ensure the web server is running with `aw web`
- Check no other services are using port 5000
- Hard refresh with Ctrl+F5 (Windows/Linux) or Cmd+Shift+R (Mac)

### Commands Not Working
- Verify you've selected the correct project
- Check the orchestrator is running with `aw status`
- Ensure Discord bot is configured if using Discord integration

### State Not Updating
- Refresh the page to resync state
- Check websocket connection in browser console
- Restart web interface: `aw web-stop && aw web`

## Next Steps

- **Daily Tasks**: See [daily-tasks.md](daily-tasks.md) for common workflows
- **Commands**: Full reference at [commands.md](commands.md)
- **Troubleshooting**: Detailed fixes at [troubleshooting.md](troubleshooting.md)