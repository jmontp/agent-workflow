# Multi-Project Interface Guide

## Overview

The Multi-Project Interface is a powerful Discord-style web interface that allows you to manage and monitor multiple AI orchestration projects simultaneously. This guide provides comprehensive coverage of all features and workflows.

## Quick Start

### Accessing the Interface

1. **Start the web interface:**
   ```bash
   aw web
   ```

2. **Open your browser** to `http://localhost:5000`

3. **Select your project** from the project selector

4. **Start chatting** with your AI orchestrator

### First-Time Setup

When you first access the interface:

1. **Project Registration**: Ensure your projects are registered with `aw register-project`
2. **Project Selection**: Choose your active project from the dropdown
3. **Permissions**: Verify your access permissions for the selected project
4. **Chat History**: Your previous conversations are automatically loaded

## Interface Components

### Project Selector

Located in the top-left corner, the project selector allows you to:

- **View Current Project**: Shows the currently active project name and status
- **Switch Projects**: Click to see all available projects and switch between them
- **Project Status**: Visual indicators show project health and activity

**Status Indicators:**
- 🟢 **Active**: Project is running with active workflows
- 🟡 **Idle**: Project is loaded but not actively processing
- 🟠 **Paused**: Project execution is temporarily paused
- 🔴 **Error**: Project has encountered an error
- ⚫ **Offline**: Project is not currently available

### Chat Interface

The left side of the interface provides a Discord-style chat experience:

#### Features:
- **Message History**: Complete chat history with project isolation
- **Command Support**: Full slash command integration
- **Rich Formatting**: Support for code blocks, mentions, and reactions
- **Typing Indicators**: See when team members or the bot are typing
- **Real-time Updates**: Instant message delivery and state updates

#### Message Types:
- **User Messages**: Your messages and commands
- **Bot Responses**: AI orchestrator replies and updates
- **System Messages**: Project notifications and state changes
- **Command Results**: Feedback from executed commands

### State Visualization

The right side displays real-time workflow visualizations:

#### Workflow Diagrams:
- **Current State**: Highlighted current workflow state
- **Transitions**: Available next states and transitions
- **Interactive Elements**: Click states for detailed information
- **Zoom and Pan**: Navigate large diagrams easily

#### TDD Cycle Visualization:
- **Individual Cycles**: Separate diagrams for each TDD cycle
- **Progress Indicators**: Visual progress tracking
- **Parallel Execution**: Multiple cycles running simultaneously
- **Phase Highlighting**: Current phase clearly marked

## Core Features

### Project Management

#### Switching Projects

**Method 1: Project Selector**
1. Click the project name in the top-left
2. Select the new project from the dropdown
3. Wait for the transition to complete

**Method 2: Keyboard Shortcut**
- Press `Ctrl + P` for the quick project switcher
- Type the project name or use arrow keys
- Press Enter to switch

**Method 3: Chat Command**
```
/project switch <project-name>
```

#### Project Information

Get detailed project information:
- **Command**: `/project info`
- **Shortcut**: `Ctrl + I`
- **Display**: Project path, status, team, resources, and activity

### Chat Commands

#### Project Commands
```bash
/project switch <name>     # Switch to different project
/project info              # Show project information
/project list              # List all available projects
/project status            # Show project health status
```

#### Workflow Commands
```bash
/epic "<description>"      # Create new epic
/story "<description>"     # Add story to backlog
/sprint start             # Start new sprint
/sprint status            # Show sprint information
/approve [task-id]        # Approve pending task
/state                    # Show current workflow state
```

#### Chat Management
```bash
/clear                    # Clear chat history
/history                  # Show command history
/help [command]           # Get help for commands
/ping                     # Test system connection
```

### Collaboration Features

#### Multi-User Support
- **Real-time Collaboration**: Multiple users can work on the same project
- **User Presence**: See who's currently active in each project
- **Typing Indicators**: Know when team members are typing
- **Message Sync**: All users see the same chat history

#### Team Communication
- **@mentions**: Notify specific users with `@username`
- **Project References**: Link to other projects with `#project-name`
- **Message Reactions**: React to messages with emoji
- **Thread Support**: Organize conversations with message threads

## Accessibility Features

### Keyboard Navigation

**Global Shortcuts:**
- `Ctrl + P`: Quick project switcher
- `Ctrl + I`: Project information
- `Ctrl + /`: Show keyboard shortcuts
- `F1`: Open help documentation
- `F11`: Toggle full-screen mode

**Chat Shortcuts:**
- `Enter`: Send message
- `Shift + Enter`: New line in message
- `↑`: Edit last message
- `Tab`: Auto-complete commands
- `Ctrl + F`: Search chat history

**Diagram Shortcuts:**
- `+`/`-`: Zoom in/out
- `0`: Reset zoom
- `Arrow Keys`: Pan diagram
- `Home`: Center diagram

### Visual Accessibility

#### High Contrast Mode
- **Activation**: `Ctrl + Shift + H` or Settings → Accessibility
- **Benefits**: Enhanced color contrast for better visibility
- **Compatibility**: Works with all system themes

#### Large Text Mode
- **Activation**: `Ctrl + Shift + L` or Settings → Accessibility
- **Benefits**: Increased font sizes throughout interface
- **Options**: Multiple size levels available

#### Screen Reader Support
- **Full ARIA Labels**: All elements properly labeled
- **Live Regions**: Real-time updates announced
- **Navigation Aids**: Logical tab order and skip links

### Motor Accessibility

- **Keyboard-Only Navigation**: Complete interface accessible via keyboard
- **Focus Indicators**: Clear visual focus indicators
- **Alternative Interactions**: Keyboard alternatives to mouse actions
- **Customizable Controls**: Adjustable interaction methods

## Mobile Interface

### Responsive Design

The interface automatically adapts to mobile devices:

- **Stacked Layout**: Chat and diagrams stack vertically
- **Touch Optimization**: Touch-friendly controls and gestures
- **Responsive Navigation**: Simplified navigation for mobile
- **Performance Optimization**: Efficient loading and rendering

### Touch Gestures

#### Chat Interface:
- **Tap**: Select input or send message
- **Long Press**: Context menu for messages
- **Swipe Left**: Show/hide project sidebar
- **Swipe Right**: Show/hide settings

#### Diagram Interface:
- **Pinch**: Zoom in/out
- **Two-finger Pan**: Move diagram
- **Double Tap**: Reset zoom
- **Long Press**: Show state details

### Mobile Features

- **Project Quick-Switch**: Slide-up panel for project selection
- **Notification Integration**: Push notifications when backgrounded
- **Offline Support**: Basic functionality when disconnected
- **Battery Optimization**: Efficient resource usage

## Advanced Features

### Project Isolation

Each project maintains complete isolation:

- **Separate Chat History**: Each project has its own chat history
- **Independent State**: Workflow states are project-specific
- **User Sessions**: User context switches between projects
- **Resource Isolation**: Projects don't interfere with each other

### Real-Time Updates

The interface provides instant updates:

- **WebSocket Communication**: Real-time message delivery
- **State Synchronization**: Instant workflow state updates
- **Multi-User Sync**: Changes reflected for all users immediately
- **Connection Management**: Automatic reconnection handling

### Integration Features

#### Discord Bot Integration
- **Command Sync**: Commands work in both web and Discord
- **Status Sync**: Project status reflected in Discord
- **Notification Bridge**: Important updates sent to Discord

#### Development Tools Integration
- **Git Integration**: Repository status and commit information
- **CI/CD Status**: Build and deployment status updates
- **Issue Tracking**: Integration with GitHub issues and PRs

## Troubleshooting

### Common Issues

#### Connection Problems

**Issue**: "Connection Lost" error
**Solutions**:
1. Check internet connection
2. Refresh the page (F5)
3. Clear browser cache
4. Try incognito/private mode

**Issue**: WebSocket connection failures
**Solutions**:
1. Check if port 5000 is accessible
2. Verify orchestrator is running (`aw status`)
3. Restart web interface (`aw web-stop && aw web`)

#### Project Loading Issues

**Issue**: Projects not appearing
**Solutions**:
1. Verify projects are registered (`aw projects`)
2. Check project status (`aw project-info <name>`)
3. Refresh project list (Ctrl + R in selector)

**Issue**: Cannot switch projects
**Solutions**:
1. Wait for current operations to complete
2. Use `/project switch <name>` command
3. Clear browser cache and reload

#### Chat Problems

**Issue**: Messages not sending
**Solutions**:
1. Check connection status
2. Verify message length (max 2000 characters)
3. Check WebSocket connection
4. Try refreshing the page

#### Performance Issues

**Issue**: Slow loading or responses
**Solutions**:
1. Clear chat history (`/clear`)
2. Close unused browser tabs
3. Check network speed
4. Use compact mode for better performance

### Browser Support

**Fully Supported:**
- Chrome 90+
- Firefox 88+
- Safari 14+
- Edge 90+

**Limited Support:**
- Internet Explorer (not recommended)
- Older mobile browsers

### Debug Mode

Enable debug mode for troubleshooting:

1. Add `?debug=true` to URL
2. Open browser DevTools (F12)
3. Check Console for error messages
4. Use Network tab to monitor requests

## Best Practices

### Efficient Workflow

1. **Use Keyboard Shortcuts**: Learn common shortcuts for faster navigation
2. **Project Organization**: Keep related projects grouped logically
3. **Command History**: Use arrow keys to repeat previous commands
4. **Search Features**: Use Ctrl+F to search chat history

### Team Collaboration

1. **Clear Communication**: Use @mentions for important messages
2. **Project Context**: Always include project context in discussions
3. **Status Updates**: Keep team informed of project status changes
4. **Documentation**: Use commands to document decisions and progress

### Performance Optimization

1. **Regular Cleanup**: Clear old chat history periodically
2. **Browser Maintenance**: Clear cache and cookies regularly
3. **Resource Management**: Monitor browser memory usage
4. **Connection Quality**: Ensure stable internet connection

## Integration Examples

### Command Automation

Create custom scripts for common workflows:

```javascript
// Auto-switch to project and start sprint
function quickStart(projectName) {
    chat.sendCommand(`/project switch ${projectName}`);
    setTimeout(() => {
        chat.sendCommand('/sprint start');
    }, 1000);
}
```

### Notification Integration

Set up custom notifications:

```javascript
// Listen for critical state changes
chat.onStateUpdate((data) => {
    if (data.new_state === 'ERROR') {
        showNotification(`Project ${data.project_name} has an error!`);
    }
});
```

### External Tool Integration

Connect with external tools:

```bash
# Webhook for CI/CD integration
curl -X POST http://localhost:5000/api/v1/projects/my-project/chat/send \
  -H "Content-Type: application/json" \
  -d '{"message": "Build completed successfully!", "type": "system"}'
```

## Additional Resources

### Documentation
- [API Documentation](../visualizer/API_DOCUMENTATION.md)
- [Deployment Guide](../visualizer/DEPLOYMENT_GUIDE.md)
- [Architecture Overview](../architecture/overview.md)

### Video Tutorials
- Interface Overview (Coming Soon)
- Project Management Workflows (Coming Soon)
- Advanced Features Tour (Coming Soon)

### Community Support
- GitHub Issues for bug reports
- Community forums for questions
- Documentation feedback welcome

This comprehensive guide covers all aspects of the Multi-Project Interface. For additional help or to report issues, please refer to the troubleshooting section or contact your system administrator.