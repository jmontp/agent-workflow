# Multi-Project Interface User Guide

## Overview

The Multi-Project Interface provides a comprehensive Discord-style web interface for managing and monitoring multiple AI orchestration projects simultaneously. This guide covers all features, keyboard shortcuts, accessibility options, and troubleshooting procedures.

## Table of Contents

1. [Getting Started](#getting-started)
2. [Interface Overview](#interface-overview)
3. [Project Management](#project-management)
4. [Chat Interface](#chat-interface)
5. [State Visualization](#state-visualization)
6. [Keyboard Shortcuts](#keyboard-shortcuts)
7. [Accessibility Features](#accessibility-features)
8. [Mobile Interface](#mobile-interface)
9. [Collaboration Features](#collaboration-features)
10. [Troubleshooting](#troubleshooting)

## Getting Started

### Prerequisites

- Agent Workflow system installed (`pip install agent-workflow`)
- At least one project registered with the orchestrator
- Web browser with JavaScript enabled (Chrome, Firefox, Safari, Edge)

### Quick Start

1. **Start the web interface:**
   ```bash
   aw web
   ```
   or
   ```bash
   agent-orch web
   ```

2. **Open your browser** to `http://localhost:5000`

3. **Select your project** from the project selector in the top-left corner

4. **Start interacting** with your project through the chat interface

### First Time Setup

When you first access the interface:

1. **Project Selection**: Choose your active project from the dropdown
2. **Permission Check**: Confirm your access permissions
3. **Chat History**: Your previous chat history will be loaded automatically
4. **State Sync**: The current project state will be displayed

## Interface Overview

### Main Components

#### 1. Project Selector (Top-Left Corner)
- **Current Project Display**: Shows the currently active project name
- **Dropdown Menu**: Click to see all available projects
- **Project Status Indicators**: 
  - 🟢 Active and running
  - 🟡 Idle or paused
  - 🔴 Error or offline
  - ⚪ Unknown status

#### 2. Chat Interface (Left Side)
- **Message Area**: Scrollable chat history with Discord-style formatting
- **Input Field**: Type messages and commands
- **Send Button**: Click or press Enter to send
- **Typing Indicators**: Shows when other users or the bot are typing

#### 3. State Visualization (Right Side)
- **Workflow Diagram**: Visual representation of the current project state
- **TDD Cycle Diagrams**: Individual test-driven development cycles
- **Interactive Elements**: Click on states to see details

#### 4. Status Bar (Bottom)
- **Connection Status**: WebSocket connection indicator
- **Project Info**: Current project statistics
- **User Count**: Number of active users in the project

### Interface Modes

#### Desktop Mode (Default)
- Full two-column layout with chat and visualization side-by-side
- Complete keyboard navigation support
- All features available

#### Mobile Mode (Auto-detected)
- Stacked layout with swipeable sections
- Touch-optimized controls
- Simplified navigation

#### Compact Mode (Manual Toggle)
- Reduced spacing and smaller fonts
- Ideal for smaller screens or when screen real estate is limited
- Toggle with `Ctrl + Shift + C`

## Project Management

### Switching Projects

#### Method 1: Project Selector
1. Click the project name in the top-left corner
2. Select the new project from the dropdown
3. Wait for the transition animation to complete

#### Method 2: Keyboard Shortcut
- Press `Ctrl + P` to open the project quick-switcher
- Type the project name or use arrow keys to navigate
- Press Enter to switch

#### Method 3: Chat Command
Type in the chat: `/project switch <project-name>`

### Project Information

View detailed project information:
- **Chat Command**: `/project info`
- **Keyboard**: `Ctrl + I`
- **Button**: Click the info icon next to the project name

**Information Displayed:**
- Project path and repository URL
- Current workflow state
- Active team members
- Resource usage statistics
- Last activity timestamp

### Project Status

Projects can have the following statuses:

| Status | Indicator | Description |
|--------|-----------|-------------|
| Active | 🟢 | Project is running with active workflows |
| Idle | 🟡 | Project is loaded but not actively processing |
| Paused | 🟠 | Project execution is temporarily paused |
| Error | 🔴 | Project has encountered an error |
| Offline | ⚫ | Project is not currently available |

## Chat Interface

### Message Types

#### User Messages
- **Standard Text**: Regular conversation messages
- **Commands**: Messages starting with `/` (slash commands)
- **Code Blocks**: Formatted code using triple backticks
- **Mentions**: @username to notify specific users

#### Bot Messages
- **Responses**: Replies to user commands and queries
- **Notifications**: System updates and state changes
- **Errors**: Error messages with troubleshooting information
- **Progress Updates**: Real-time workflow progress

#### System Messages
- **User Join/Leave**: When users join or leave the project
- **State Transitions**: Workflow state changes
- **Project Events**: Project-level notifications

### Slash Commands

#### Project Management
- `/project switch <name>` - Switch to a different project
- `/project info` - Show current project information
- `/project list` - List all available projects
- `/project status` - Show project status and health

#### Workflow Control
- `/epic "<description>"` - Create a new epic
- `/story "<description>"` - Add a story to the backlog
- `/sprint start` - Start a new sprint
- `/sprint status` - Show current sprint information
- `/approve [task-id]` - Approve a pending task
- `/state` - Show current workflow state

#### Chat Management
- `/clear` - Clear the current chat history
- `/history` - Show command history
- `/help [command]` - Show help for commands

#### System Commands
- `/ping` - Test connection to the system
- `/debug` - Show debugging information
- `/version` - Show system version information

### Message Formatting

#### Text Formatting
- **Bold**: `**text**` or `__text__`
- **Italic**: `*text*` or `_text_`
- **Code**: `` `code` `` for inline, ```` ```code``` ```` for blocks
- **Strikethrough**: `~~text~~`

#### Special Formatting
- **User Mentions**: `@username`
- **Project References**: `#project-name`
- **Epic/Story IDs**: `#EPIC-123` or `#STORY-456`

### Chat Features

#### Message History
- **Automatic Saving**: All messages are saved locally and on the server
- **Project Isolation**: Each project maintains separate chat history
- **Search**: Use `Ctrl + F` to search chat history
- **Export**: Use `/export` command to download chat history

#### Typing Indicators
- See when other users are typing
- Automatic timeout after 3 seconds of inactivity
- Project-specific (only shows users in the same project)

#### Message Reactions
- Click the reaction button (🙂) to add emoji reactions
- Common reactions: 👍, 👎, ❤️, 😄, 😮, 😢, 😡
- See who reacted by hovering over reactions

## State Visualization

### Workflow State Diagram

#### Understanding the Diagram
- **Nodes**: Represent different workflow states
- **Edges**: Show possible transitions between states
- **Current State**: Highlighted in blue with a thick border
- **Possible Transitions**: Available next states are highlighted in green

#### Interactive Features
- **Click States**: Click on any state to see detailed information
- **Hover Effects**: Hover over transitions to see trigger conditions
- **Zoom Controls**: Use mouse wheel or zoom buttons to adjust view
- **Pan**: Click and drag to move the diagram around

### TDD Cycle Visualization

#### Individual Cycles
Each active TDD cycle is displayed as a separate diagram showing:
- **Red Phase**: Write failing test
- **Green Phase**: Make test pass
- **Refactor Phase**: Improve code quality
- **Current Phase**: Highlighted with animation

#### Parallel Cycles
Multiple TDD cycles can run simultaneously:
- Each cycle has its own diagram
- Progress indicators show completion percentage
- Dependencies between cycles are shown with arrows

### Diagram Controls

#### Zoom and Pan
- **Zoom In**: `+` key or mouse wheel up
- **Zoom Out**: `-` key or mouse wheel down
- **Reset Zoom**: `0` key or double-click empty space
- **Pan**: Click and drag, or use arrow keys

#### Layout Options
- **Vertical**: Default stacked layout
- **Horizontal**: Side-by-side layout (desktop only)
- **Compact**: Condensed view for small screens
- **Full Screen**: `F11` to toggle full-screen mode

## Keyboard Shortcuts

### Global Shortcuts

| Shortcut | Action |
|----------|--------|
| `Ctrl + P` | Quick project switcher |
| `Ctrl + I` | Project information |
| `Ctrl + /` | Show/hide shortcuts help |
| `Ctrl + ,` | Open settings |
| `F1` | Open help documentation |
| `F11` | Toggle full-screen mode |

### Chat Shortcuts

| Shortcut | Action |
|----------|--------|
| `Enter` | Send message |
| `Shift + Enter` | New line in message |
| `Ctrl + Enter` | Send message (alternative) |
| `↑` | Edit last message |
| `↓` | Navigate message history |
| `Tab` | Auto-complete commands/mentions |
| `Escape` | Cancel editing/clear input |
| `Ctrl + F` | Search chat history |
| `Ctrl + K` | Quick command picker |

### Navigation Shortcuts

| Shortcut | Action |
|----------|--------|
| `Ctrl + 1` | Focus chat input |
| `Ctrl + 2` | Focus state diagram |
| `Ctrl + 3` | Focus project selector |
| `Tab` | Navigate between interface elements |
| `Shift + Tab` | Navigate backwards |
| `Space` | Scroll down (when not in input) |
| `Shift + Space` | Scroll up |

### Diagram Shortcuts

| Shortcut | Action |
|----------|--------|
| `+` / `=` | Zoom in |
| `-` | Zoom out |
| `0` | Reset zoom |
| `Arrow Keys` | Pan diagram |
| `Home` | Center diagram |
| `End` | Fit diagram to view |

### Accessibility Shortcuts

| Shortcut | Action |
|----------|--------|
| `Ctrl + Shift + H` | Toggle high contrast mode |
| `Ctrl + Shift + L` | Toggle large text mode |
| `Ctrl + Shift + R` | Toggle reduced motion |
| `Ctrl + Shift + S` | Toggle screen reader mode |

## Accessibility Features

### Visual Accessibility

#### High Contrast Mode
- **Activation**: `Ctrl + Shift + H` or Settings → Accessibility
- **Features**: Enhanced color contrast for better visibility
- **Compatible**: Works with all system themes

#### Large Text Mode
- **Activation**: `Ctrl + Shift + L` or Settings → Accessibility
- **Features**: Increases font sizes throughout the interface
- **Scalable**: Multiple size options available

#### Color Blindness Support
- **Activation**: Settings → Accessibility → Color Blindness
- **Options**: Protanopia, Deuteranopia, Tritanopia support
- **Alternative**: Pattern and shape indicators alongside color

### Motor Accessibility

#### Keyboard Navigation
- **Full Navigation**: Complete interface accessible via keyboard
- **Focus Indicators**: Clear visual focus indicators
- **Logical Order**: Tab order follows visual layout
- **Skip Links**: Jump to main content areas

#### Mouse Alternatives
- **Click Alternatives**: Enter/Space key activation
- **Drag Alternatives**: Keyboard-based pan and zoom
- **Hover Alternatives**: Focus-based information display

### Cognitive Accessibility

#### Reduced Motion
- **Activation**: `Ctrl + Shift + R` or Settings → Accessibility
- **Features**: Disables animations and transitions
- **Respects**: System `prefers-reduced-motion` setting

#### Clear Navigation
- **Breadcrumbs**: Clear indication of current location
- **Consistent Layout**: Predictable interface organization
- **Error Prevention**: Clear validation and confirmation dialogs

### Screen Reader Support

#### ARIA Labels
- **Complete Coverage**: All interface elements properly labeled
- **Dynamic Updates**: Live regions for real-time updates
- **Context Information**: Detailed descriptions for complex elements

#### Screen Reader Mode
- **Activation**: `Ctrl + Shift + S` or automatic detection
- **Features**: Enhanced descriptions and navigation aids
- **Compatibility**: Tested with NVDA, JAWS, and VoiceOver

## Mobile Interface

### Responsive Design

#### Automatic Detection
- **Viewport**: Automatically detects mobile devices
- **Touch**: Optimizes for touch interaction
- **Orientation**: Adapts to portrait/landscape changes

#### Layout Adaptations
- **Stacked Layout**: Chat and diagrams stack vertically
- **Collapsible Sections**: Tap headers to expand/collapse
- **Bottom Navigation**: Key actions moved to bottom for thumb access

### Touch Gestures

#### Chat Interface
- **Tap**: Select input field or send message
- **Long Press**: Context menu for messages
- **Swipe Left**: Show/hide project sidebar
- **Swipe Right**: Show/hide settings panel

#### Diagram Interface
- **Pinch**: Zoom in/out of diagrams
- **Two-finger Pan**: Move diagram around
- **Double Tap**: Reset zoom to fit view
- **Long Press**: Show state details

### Mobile-Specific Features

#### Project Switching
- **Slide-up Panel**: Swipe up from project name to show all projects
- **Quick Actions**: Tap and hold for quick project actions
- **Recent Projects**: Easy access to recently used projects

#### Notification Integration
- **Push Notifications**: Receive notifications when app is backgrounded
- **Badge Updates**: App icon shows unread message count
- **Sound Alerts**: Configurable notification sounds

### Offline Support

#### Cached Content
- **Message History**: Recent messages cached for offline viewing
- **Project List**: Available projects cached locally
- **State Information**: Last known state preserved

#### Sync on Reconnect
- **Automatic Sync**: Seamlessly syncs when connection restored
- **Conflict Resolution**: Handles conflicts when multiple devices used
- **Queue Management**: Queues actions for execution when online

## Collaboration Features

### Multi-User Support

#### User Presence
- **Online Indicators**: See who's currently active in each project
- **Typing Indicators**: Real-time typing status
- **User List**: Expandable list of all project members

#### Real-Time Collaboration
- **Shared Chat**: All users see the same chat history
- **Synchronized State**: State changes reflected for all users
- **Concurrent Editing**: Multiple users can work simultaneously

### Permission System

#### User Roles
- **Owner**: Full control over project settings and workflows
- **Admin**: Can manage workflows and approve tasks
- **Developer**: Can submit work and participate in discussions
- **Viewer**: Read-only access to project information

#### Permission-Based Features
- **Command Access**: Certain commands restricted by role
- **Workflow Control**: Approval permissions based on role
- **Settings Access**: Configuration changes require appropriate permissions

### Team Communication

#### Mentions and Notifications
- **@mentions**: Notify specific users with @username
- **@channel**: Notify all project members
- **@here**: Notify only currently active members

#### Status Updates
- **Custom Status**: Set your availability and current focus
- **Auto-Status**: Automatically show "away" when inactive
- **Do Not Disturb**: Mute notifications during focus time

## Troubleshooting

### Common Issues

#### Connection Problems

**Issue**: "Connection Lost" error message
**Solutions**:
1. Check your internet connection
2. Refresh the page (F5)
3. Clear browser cache and cookies
4. Try a different browser or incognito mode
5. Contact system administrator if problem persists

**Issue**: WebSocket connection failures
**Solutions**:
1. Check if port 5000 is blocked by firewall
2. Verify the orchestrator is running (`aw status`)
3. Restart the web interface (`aw web-stop && aw web`)
4. Check browser console for specific error messages

#### Project Loading Issues

**Issue**: Projects not appearing in selector
**Solutions**:
1. Verify projects are registered (`aw projects`)
2. Check project status (`aw project-info <name>`)
3. Refresh project list (Ctrl + R in project selector)
4. Restart orchestrator if needed

**Issue**: Project switching not working
**Solutions**:
1. Wait for current operations to complete
2. Clear browser cache and reload
3. Use `/project switch <name>` command instead
4. Check browser console for JavaScript errors

#### Chat Problems

**Issue**: Messages not sending
**Solutions**:
1. Check connection status indicator
2. Verify you have permission to send messages
3. Try refreshing the page
4. Check if message is too long (limit: 2000 characters)
5. Ensure WebSocket connection is active

**Issue**: Chat history not loading
**Solutions**:
1. Clear browser localStorage
2. Refresh the page
3. Check if project has been recently switched
4. Verify project access permissions

#### Visualization Issues

**Issue**: Diagrams not displaying
**Solutions**:
1. Enable JavaScript in your browser
2. Clear browser cache
3. Check browser console for Mermaid errors
4. Try refreshing the page
5. Use a supported browser (Chrome, Firefox, Safari, Edge)

**Issue**: Diagrams are too small/large
**Solutions**:
1. Use zoom controls (+ and - keys)
2. Reset zoom with 0 key
3. Check browser zoom level (Ctrl + 0 to reset)
4. Switch to full-screen mode (F11)

### Browser-Specific Issues

#### Chrome
- **Issue**: Auto-refresh not working
- **Solution**: Check if "Disable cache" is enabled in DevTools

#### Firefox
- **Issue**: WebSocket connection intermittent
- **Solution**: Update Firefox to latest version

#### Safari
- **Issue**: Some CSS features not displaying correctly
- **Solution**: Enable "Develop" menu and check feature support

#### Mobile Browsers
- **Issue**: Touch gestures not responding
- **Solution**: Ensure JavaScript and touch events are enabled

### Performance Issues

#### Slow Loading
**Causes**: Large chat history, complex diagrams, slow network
**Solutions**:
1. Clear old chat history (`/clear` command)
2. Close unused browser tabs
3. Check network speed and connection quality
4. Use compact mode for better performance

#### High Memory Usage
**Causes**: Long-running sessions, memory leaks
**Solutions**:
1. Refresh the page periodically
2. Close and reopen browser
3. Use incognito/private mode
4. Check browser task manager for memory usage

### Debug Mode

#### Enabling Debug Mode
1. Add `?debug=true` to the URL
2. Or use the command `/debug enable`

#### Debug Information
- WebSocket connection status
- Message queue status
- Performance metrics
- Error logs and stack traces

#### Collecting Debug Information
1. Open browser DevTools (F12)
2. Go to Console tab
3. Reproduce the issue
4. Copy console output
5. Include this information when reporting issues

### Getting Help

#### Built-in Help
- Press `F1` for context-sensitive help
- Use `/help` command for command reference
- Check status bar for quick tips

#### Documentation
- Full documentation available at `/docs`
- Video tutorials at `/tutorials`
- FAQ section covers most common questions

#### Support Channels
- In-app support chat (click help icon)
- GitHub issues for bug reports
- Community forums for general discussion

#### Reporting Issues
When reporting issues, please include:
1. Browser and version information
2. Operating system details
3. Steps to reproduce the problem
4. Screenshot or video if applicable
5. Browser console output (if available)
6. Current project and orchestrator status

This comprehensive guide should help you make the most of the Multi-Project Interface. For additional support or feature requests, please consult the documentation or contact your system administrator.