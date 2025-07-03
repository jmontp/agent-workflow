# Visualizer Tool Documentation

This document provides comprehensive guidance for working with the Discord-style web visualization interface in the `tools/visualizer/` directory.

## Overview

The visualizer is a Flask/SocketIO web application that provides:
- Real-time Discord-style chat interface with slash commands
- Live state machine visualization using Mermaid diagrams
- Multi-user collaboration support
- Agent interface management
- Responsive design for desktop and mobile

## Architecture

### Backend (`app.py`)
- Flask web server with SocketIO for real-time communication
- WebSocket connection to state broadcaster
- Command processor for handling Discord-style commands
- Mock orchestrator support for standalone testing

### Import Structure (Updated)
The visualizer now uses a prioritized import pattern following the new `agent_workflow` package structure:

**Pattern**: `agent_workflow` → `local/lib` → `fallback`

**Key Imports**:
- `agent_workflow.core.state_broadcaster` → `lib.state_broadcaster` → mock
- `agent_workflow.security.tool_config` → `lib.multi_project_security` → fallback
- `agent_workflow.context.manager_factory` → `lib.context_manager_factory` → fallback
- `agent_workflow.integrations.*` → `local modules` → `lib.*` → fallback

This ensures compatibility with both the new unified package structure and legacy lib-based installations.

### Frontend Components
- `static/js/discord-chat.js` - Main Discord chat implementation
- `static/js/chat-components.js` - Reusable chat UI components
- `static/css/discord-chat.css` - Discord-style theming
- `static/visualizer.js` - State visualization logic
- `templates/index.html` - Main HTML template

## Common Issues and Troubleshooting

### 🔴 CRITICAL: Changes Not Reflecting After Code Updates

**Problem**: After making code changes to the visualizer, running `aw web` shows old version

**Root Causes**:
1. **Python Package Installation Mode**: Package installed in site-packages instead of editable mode
2. **Browser Cache**: Browser serving cached JavaScript/CSS files

**Solution**:
```bash
# 1. Stop the web interface
aw web-stop

# 2. Reinstall package in editable mode
pip uninstall -y agent-workflow --break-system-packages
pip install -e . --user --break-system-packages

# 3. Clear any processes on port 5000
lsof -ti:5000 | xargs kill -9 2>/dev/null || true

# 4. Start web interface
aw web

# 5. In browser, do a hard refresh:
# Windows/Linux: Ctrl+F5 or Ctrl+Shift+R
# Mac: Cmd+Shift+R
# Or use incognito/private window
```

### ✅ RESOLVED: Recent Issues Fixed

1. **Chat Send Button Not Working**
   - **Issue**: TypeError in ChatComponents due to missing methods
   - **Fix**: Added `renderEpicEmbed` and `renderSprintEmbed` methods
   - **File**: `static/js/chat-components.js`

2. **Main Page Cannot Scroll**
   - **Issue**: CSS overflow:hidden preventing scrolling
   - **Fix**: Changed to overflow-y:auto in `.main-content`
   - **File**: `static/css/discord-chat.css`

3. **Chat Close Button Not Working**
   - **Issue**: Missing event handler for chat-close-btn
   - **Fix**: Added click handler in `initializeEventHandlers()`
   - **File**: `static/js/discord-chat.js`

4. **Mermaid Diagrams Font Too Small**
   - **Issue**: Default font size too small to read
   - **Fix**: Added CSS rules for 16px base font size
   - **File**: `static/style.css`

5. **Diagrams Too Cramped Side-by-Side**
   - **Issue**: Horizontal layout too narrow
   - **Fix**: Changed grid to single column vertical layout
   - **File**: `static/style.css`

### 🟡 Element ID Consistency Issues

**Problem**: "Initialization Error: Failed to initialize the state visualizer"

**Root Cause**: JavaScript looking for elements with wrong IDs

**Common Mismatches**:
- `message-input` → `chat-input-field`
- `send-button` → `chat-send-btn`
- `autocomplete-dropdown` → `chat-autocomplete`
- `typing-indicator` → `typing-indicators`

**Debug Strategy**:
1. Open browser DevTools (F12)
2. Check Console for null reference errors
3. Search for `getElementById()` calls in JS files
4. Verify IDs match between HTML and JavaScript

### 🟡 Chat Send Button Disabled

**Problem**: Send button stays disabled even with text input

**Solution Added**:
```javascript
// In discord-chat.js initializeEventHandlers()
// Set initial button state
sendButton.disabled = messageInput.value.trim().length === 0;

// After sending message
sendButton.disabled = true;
```

### 🟡 Diagram Scrolling Issues

**Problem**: Can't scroll to see full state diagrams

**Solution**: Already implemented in CSS
```css
.diagram-wrapper {
    overflow: auto;
    max-height: 600px;
}
```

If still not working, check:
1. Parent container doesn't have `overflow: hidden`
2. Browser zoom level (reset with Ctrl+0)
3. Custom scrollbar styles are applied

## Development Workflow

### Testing Changes
```bash
# 1. Make code changes
# 2. If changing Python files, restart web interface
aw web-stop && aw web

# 3. If only changing JS/CSS, just hard refresh browser
# Ctrl+F5 (Windows/Linux) or Cmd+Shift+R (Mac)
```

### Running Tests
```bash
# Basic connection test
cd tools/visualizer
python3 test_chat.py

# Comprehensive test
python3 test_final_fixes.py
```

### Debug Mode
```bash
# Run with debug logging
aw web --debug --log-level DEBUG

# Run on different port
aw web --port 8080

# Run without opening browser
aw web --no-browser
```

## Key Files Reference

### Configuration
- `orch-config.yaml` - Multi-project orchestration config
- `.web-interface.pid` - Process ID tracking

### Core Implementation
- `app.py` - Main Flask application
- `command_processor.py` - Discord command handling
- `state_monitor.py` - WebSocket state monitoring

### Frontend Assets
- `static/js/discord-chat.js` - Chat interface (950+ lines)
- `static/js/chat-components.js` - UI components (719 lines)
- `static/css/discord-chat.css` - Styling (925 lines)
- `static/visualizer.js` - State visualization
- `templates/index.html` - HTML structure

### Test Files
- `test_chat.py` - Basic WebSocket test
- `test_final_fixes.py` - Comprehensive test suite
- `CHAT_DEBUG_SUMMARY.md` - Debugging documentation
- `DISCORD_INTERFACE_FIXES.md` - Fix documentation

## WebSocket Events

### Client → Server
- `chat_command` - Send chat message/command
- `request_state` - Request current state
- `request_interface_status` - Request interface status
- `start_typing` / `stop_typing` - Typing indicators
- `join_chat` / `leave_chat` - User presence

### Server → Client
- `new_chat_message` - Broadcast chat message
- `command_response` - Command execution result
- `state_update` - State machine updates
- `interface_status` - Interface status updates
- `typing_indicator` - User typing status
- `bot_typing` - Bot typing indicator

## Important Notes

1. **Editable Installation Required**: Always install package with `pip install -e .` for development
2. **Browser Cache**: Use hard refresh or incognito mode when testing frontend changes
3. **Port Conflicts**: Default port 5000 may conflict with other services
4. **Mock Mode**: Runs with mock orchestrator if real orchestrator unavailable
5. **Multi-Client**: Supports multiple browser connections simultaneously