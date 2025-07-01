# Discord Chat Troubleshooting Guide

## Current Issue
The send button in the Discord-style chat interface is not enabling when typing text, preventing messages from being sent.

## Diagnostics Created

### 1. **Browser Console Diagnostic** (`diagnose_chat_issue.js`)
Open http://localhost:5000 and paste the contents of this file into the browser console (F12). It will:
- Check if all required classes are loaded
- Verify global instances exist
- Test DOM elements
- Attempt to recreate the issue
- Provide a diagnostic summary

### 2. **Simple Test Page** (`test_simple_chat.html`)
Navigate to http://localhost:5000/test_simple_chat.html to test the chat functionality in isolation. This helps determine if the issue is with:
- The basic event handling logic
- The integration with the larger application
- Browser-specific behavior

### 3. **Diagnostic Frame Test** (`diagnose_send_issue.html`)
Open this file directly in your browser. It loads the main app in an iframe and provides:
- Real-time diagnostic tools
- Debug code injection
- Socket.IO testing
- Comprehensive logging

## Solutions Implemented

### 1. **Enhanced Debug Logging**
Added extensive console logging to:
- `visualizer.js` - Chat initialization process
- `discord-chat.js` - Event handler attachment

### 2. **Failsafe Initialization** (`chat-init-failsafe.js`)
Created a robust initialization system that:
- Retries initialization up to 10 times
- Waits for all dependencies to load
- Provides manual initialization fallback
- Includes debug helpers

## Immediate Actions to Try

1. **Hard Refresh & Check Console**
   ```
   1. Press Ctrl+F5 (Windows/Linux) or Cmd+Shift+R (Mac)
   2. Open browser console (F12)
   3. Look for the initialization logs
   4. Check for any red error messages
   ```

2. **Run Console Diagnostic**
   ```javascript
   // Paste in console:
   Copy the contents of diagnose_chat_issue.js
   ```

3. **Test Simple Page**
   ```
   Navigate to: http://localhost:5000/test_simple_chat.html
   This tests if basic functionality works
   ```

4. **Manual Initialization**
   If chat isn't working, try in console:
   ```javascript
   initializeChatManually()
   ```

5. **Debug Current State**
   ```javascript
   debugChat()
   ```

## Common Causes & Solutions

### Cause 1: Timing Issue
**Symptom**: `window.discordChat` is undefined
**Solution**: The failsafe script should handle this automatically

### Cause 2: Socket Not Connected
**Symptom**: Socket.IO connection failed
**Solution**: Check if server is running properly

### Cause 3: DOM Elements Missing
**Symptom**: Input/button elements not found
**Solution**: Check if chat panel HTML is loaded

### Cause 4: JavaScript Error
**Symptom**: Red errors in console
**Solution**: Check error message and stack trace

## Quick Fixes to Try

1. **Force Enable Button** (Console):
   ```javascript
   document.getElementById('chat-send-btn').disabled = false;
   ```

2. **Test Socket Directly** (Console):
   ```javascript
   if (window.discordChat?.socket) {
       window.discordChat.socket.emit('chat_command', {
           message: 'Test message',
           user_id: 'test',
           username: 'Test User',
           session_id: null,
           project_name: 'default'
       });
   }
   ```

3. **Recreate Event Handlers** (Console):
   ```javascript
   const input = document.getElementById('chat-input-field');
   const button = document.getElementById('chat-send-btn');
   
   input.addEventListener('input', (e) => {
       button.disabled = e.target.value.trim().length === 0;
       console.log('Input changed, button disabled:', button.disabled);
   });
   
   button.addEventListener('click', () => {
       console.log('Button clicked!');
       if (window.discordChat) {
           window.discordChat.sendMessage();
       }
   });
   ```

## If Nothing Works

1. **Check Network Tab**:
   - Open F12 → Network tab
   - Refresh page
   - Ensure all JS files load (no 404s)

2. **Try Different Browser**:
   - Test in Firefox, Edge, or Safari
   - Rules out Chrome-specific issues

3. **Check for Conflicting Extensions**:
   - Try in incognito mode
   - Disable ad blockers temporarily

4. **Server Logs**:
   - Check terminal where `aw web` is running
   - Look for any error messages

## Expected Console Output (When Working)

```
🛡️ Chat initialization failsafe loaded
=== Chat Initialization Debug ===
Socket available: true
Socket connected: true
DiscordChat class available: function
ChatComponents class available: function
Chat components found, initializing...
Creating ChatComponents...
ChatComponents created successfully
Creating DiscordChat...
DiscordChat created successfully
window.discordChat set to: DiscordChat {socket: Socket, visualizer: StateVisualizer, ...}
Discord chat system initialized successfully
=== Chat Initialization Complete ===
✅ Event handlers attached successfully
```

## File Locations

All diagnostic files are in: `/tools/visualizer/`
- `diagnose_chat_issue.js` - Console diagnostic
- `test_simple_chat.html` - Simple test page
- `diagnose_send_issue.html` - Frame-based diagnostic
- `console_diagnostic.js` - Older console test
- `static/js/chat-init-failsafe.js` - Failsafe initialization

## Last Resort

If the chat still doesn't work after all these steps:
1. The issue might be in the server-side WebSocket handling
2. Check if there are any Content Security Policy issues
3. Look for any proxy or firewall blocking WebSocket connections