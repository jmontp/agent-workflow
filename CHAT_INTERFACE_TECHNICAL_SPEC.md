# Chat Interface Technical Specification

## Overview

This document provides the detailed technical specification for integrating a Discord-like chat interface into the existing web visualizer, making Discord completely optional while providing a superior integrated experience.

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    Web Browser Client                        │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌──────────────┐  ┌──────────────────┐  │
│  │    Chat     │  │   State Viz   │  │  Agent Monitor   │  │
│  │  Component  │  │   Component   │  │    Component     │  │
│  └──────┬──────┘  └───────┬──────┘  └────────┬─────────┘  │
│         │                  │                   │            │
│  ┌──────┴──────────────────┴───────────────────┴────────┐  │
│  │              Unified WebSocket Manager                │  │
│  └───────────────────────────┬──────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                              │
                    WebSocket Connection
                              │
┌─────────────────────────────────────────────────────────────┐
│                    Flask-SocketIO Server                     │
├─────────────────────────────────────────────────────────────┤
│  ┌──────────────┐  ┌──────────────┐  ┌─────────────────┐  │
│  │Chat Handler  │  │State Handler │  │ Agent Handler   │  │
│  └──────┬───────┘  └───────┬──────┘  └────────┬────────┘  │
│         │                   │                   │           │
│  ┌──────┴───────────────────┴───────────────────┴───────┐  │
│  │                  Message Router                       │  │
│  └──────────────────────────┬───────────────────────────┘  │
│                             │                               │
│  ┌──────────────────────────┼───────────────────────────┐  │
│  │   ┌─────────────┐  ┌─────┴──────┐  ┌──────────────┐ │  │
│  │   │  Chat DB    │  │HITL Manager│  │State Machine │ │  │
│  │   │  (SQLite)   │  │            │  │              │ │  │
│  │   └─────────────┘  └────────────┘  └──────────────┘ │  │
│  └───────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

## Database Schema

```sql
-- SQLite database for chat persistence
CREATE TABLE messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    message_id TEXT UNIQUE NOT NULL,
    channel TEXT NOT NULL,
    author_type TEXT NOT NULL, -- 'user', 'agent', 'system'
    author_id TEXT NOT NULL,
    content TEXT NOT NULL,
    raw_content TEXT, -- Original with markdown/formatting
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    edited_at DATETIME,
    deleted_at DATETIME,
    thread_id TEXT,
    reply_to TEXT,
    metadata JSON
);

CREATE TABLE attachments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    message_id TEXT NOT NULL,
    file_name TEXT NOT NULL,
    file_type TEXT NOT NULL,
    file_size INTEGER,
    file_path TEXT,
    thumbnail_path TEXT,
    metadata JSON,
    FOREIGN KEY (message_id) REFERENCES messages(message_id)
);

CREATE TABLE reactions (
    message_id TEXT NOT NULL,
    user_id TEXT NOT NULL,
    reaction TEXT NOT NULL,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (message_id, user_id, reaction)
);

CREATE TABLE channels (
    name TEXT PRIMARY KEY,
    description TEXT,
    type TEXT NOT NULL, -- 'general', 'workflow', 'agent', 'error'
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    settings JSON
);

CREATE TABLE approvals (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    message_id TEXT NOT NULL,
    request_type TEXT NOT NULL,
    request_data JSON NOT NULL,
    status TEXT NOT NULL, -- 'pending', 'approved', 'rejected', 'expired'
    response_data JSON,
    requested_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    responded_at DATETIME,
    expires_at DATETIME
);

-- Indexes for performance
CREATE INDEX idx_messages_channel ON messages(channel);
CREATE INDEX idx_messages_timestamp ON messages(timestamp);
CREATE INDEX idx_messages_author ON messages(author_id);
CREATE INDEX idx_approvals_status ON approvals(status);
```

## Backend Implementation

### Enhanced Flask Application

```python
# enhanced_app.py
import sqlite3
from flask import Flask, render_template, jsonify, request, send_file
from flask_socketio import SocketIO, emit, join_room, leave_room
from werkzeug.utils import secure_filename
import asyncio
import json
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional

class ChatManager:
    def __init__(self, db_path: str = "chat.db"):
        self.db_path = db_path
        self.init_database()
        self.active_users = {}
        self.typing_indicators = {}
        self.approval_manager = ApprovalManager(self)
        
    def init_database(self):
        """Initialize SQLite database"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        
        # Create tables
        with open('schema.sql', 'r') as f:
            conn.executescript(f.read())
            
        # Insert default channels
        channels = [
            ('general', 'General discussion', 'general'),
            ('workflow', 'Workflow updates', 'workflow'),
            ('agents', 'Agent activity', 'agent'),
            ('errors', 'Error reports', 'error')
        ]
        
        conn.executemany(
            'INSERT OR IGNORE INTO channels (name, description, type) VALUES (?, ?, ?)',
            channels
        )
        conn.commit()
        conn.close()
        
    async def handle_message(self, data: Dict) -> Dict:
        """Process incoming chat message"""
        message_id = str(uuid.uuid4())
        channel = data.get('channel', 'general')
        content = data.get('content', '')
        author_id = data.get('author_id', 'anonymous')
        
        # Check for commands
        if content.startswith('/'):
            return await self.handle_command(content, author_id, channel)
            
        # Store message
        message = {
            'message_id': message_id,
            'channel': channel,
            'author_type': 'user',
            'author_id': author_id,
            'content': content,
            'timestamp': datetime.now().isoformat()
        }
        
        self.store_message(message)
        
        # Process with AI if needed
        if self.should_process_with_ai(content):
            asyncio.create_task(self.process_with_ai(message))
            
        return {
            'status': 'success',
            'message': message
        }
        
    async def handle_command(self, command: str, author_id: str, channel: str) -> Dict:
        """Handle slash commands"""
        parts = command.split()
        cmd = parts[0].lower()
        args = parts[1:] if len(parts) > 1 else []
        
        command_handlers = {
            '/help': self.cmd_help,
            '/epic': self.cmd_epic,
            '/sprint': self.cmd_sprint,
            '/approve': self.cmd_approve,
            '/reject': self.cmd_reject,
            '/state': self.cmd_state,
            '/assign': self.cmd_assign,
            '/parallel': self.cmd_parallel,
            '/mode': self.cmd_mode,
            '/pause': self.cmd_pause,
            '/resume': self.cmd_resume,
            '/status': self.cmd_status
        }
        
        handler = command_handlers.get(cmd)
        if handler:
            return await handler(args, author_id, channel)
        else:
            return {
                'status': 'error',
                'message': f'Unknown command: {cmd}'
            }

class ApprovalManager:
    """Manage approval requests through chat"""
    
    def __init__(self, chat_manager):
        self.chat = chat_manager
        self.pending_approvals = {}
        
    async def create_approval_request(self, request_type: str, data: Dict) -> str:
        """Create an approval request message"""
        approval_id = str(uuid.uuid4())
        
        # Create rich approval message
        message_content = self.format_approval_message(request_type, data)
        
        # Store in database
        approval_data = {
            'id': approval_id,
            'request_type': request_type,
            'request_data': json.dumps(data),
            'status': 'pending',
            'expires_at': (datetime.now() + timedelta(minutes=30)).isoformat()
        }
        
        self.store_approval(approval_data)
        
        # Create chat message
        message = {
            'message_id': f'approval_{approval_id}',
            'channel': 'workflow',
            'author_type': 'system',
            'author_id': 'approval_system',
            'content': message_content,
            'metadata': {
                'type': 'approval_request',
                'approval_id': approval_id,
                'actions': ['approve', 'reject', 'details']
            }
        }
        
        return message
        
    def format_approval_message(self, request_type: str, data: Dict) -> str:
        """Format approval request for chat display"""
        formatters = {
            'code_change': self.format_code_change,
            'state_transition': self.format_state_transition,
            'parallel_execution': self.format_parallel_execution,
            'batch_changes': self.format_batch_changes
        }
        
        formatter = formatters.get(request_type, self.format_generic)
        return formatter(data)

class AgentMessageFormatter:
    """Format agent responses for chat display"""
    
    @staticmethod
    def format_agent_message(agent_type: str, content: str, metadata: Dict) -> Dict:
        """Format agent response as chat message"""
        # Agent emoji mapping
        agent_emojis = {
            'orchestrator': '🎭',
            'code': '💻',
            'design': '📐',
            'qa': '🧪',
            'data': '📊'
        }
        
        emoji = agent_emojis.get(agent_type, '🤖')
        
        return {
            'author': f'{emoji} {agent_type.title()} Agent',
            'content': content,
            'metadata': metadata,
            'formatting': {
                'code_blocks': AgentMessageFormatter.extract_code_blocks(content),
                'mentions': AgentMessageFormatter.extract_mentions(content),
                'links': AgentMessageFormatter.extract_links(content)
            }
        }
        
    @staticmethod
    def extract_code_blocks(content: str) -> List[Dict]:
        """Extract code blocks for syntax highlighting"""
        import re
        pattern = r'```(\w+)?\n(.*?)```'
        matches = re.findall(pattern, content, re.DOTALL)
        
        return [
            {
                'language': lang or 'text',
                'code': code.strip()
            }
            for lang, code in matches
        ]
```

### WebSocket Event Handlers

```python
# websocket_handlers.py
@socketio.on('chat_message')
async def handle_chat_message(data):
    """Handle incoming chat message"""
    # Add user info
    data['author_id'] = request.sid
    
    # Process message
    result = await chat_manager.handle_message(data)
    
    # Broadcast to channel
    channel = data.get('channel', 'general')
    emit('new_message', result['message'], room=channel)
    
    # Update typing indicator
    await clear_typing_indicator(request.sid, channel)

@socketio.on('typing_start')
def handle_typing_start(data):
    """Handle typing indicator start"""
    channel = data.get('channel', 'general')
    user_id = request.sid
    
    chat_manager.typing_indicators[channel] = chat_manager.typing_indicators.get(channel, set())
    chat_manager.typing_indicators[channel].add(user_id)
    
    emit('typing_update', {
        'channel': channel,
        'users': list(chat_manager.typing_indicators[channel])
    }, room=channel, include_self=False)

@socketio.on('approval_response')
async def handle_approval_response(data):
    """Handle approval response from chat"""
    approval_id = data.get('approval_id')
    action = data.get('action')  # 'approve', 'reject', 'modify'
    
    # Process approval
    result = await chat_manager.approval_manager.process_approval(
        approval_id, action, data.get('modifications')
    )
    
    # Update chat with result
    emit('approval_processed', result, room='workflow')
    
    # Trigger state machine update if approved
    if action == 'approve':
        await trigger_state_machine_action(result)

@socketio.on('request_message_history')
def handle_history_request(data):
    """Send message history to client"""
    channel = data.get('channel', 'general')
    limit = data.get('limit', 50)
    before = data.get('before')  # For pagination
    
    messages = chat_manager.get_message_history(channel, limit, before)
    
    emit('message_history', {
        'channel': channel,
        'messages': messages,
        'has_more': len(messages) == limit
    })

@socketio.on('upload_file')
async def handle_file_upload(data):
    """Handle file upload to chat"""
    file_data = data.get('file')
    channel = data.get('channel')
    message = data.get('message', '')
    
    # Save file
    file_info = await save_uploaded_file(file_data)
    
    # Create message with attachment
    message_data = {
        'channel': channel,
        'content': message,
        'attachments': [file_info]
    }
    
    result = await chat_manager.handle_message(message_data)
    emit('new_message', result['message'], room=channel)
```

## Frontend Implementation

### Enhanced Chat Component

```javascript
// chat-interface.js
class EnhancedChatInterface {
    constructor(socketIO) {
        this.socket = socketIO;
        this.currentChannel = 'general';
        this.messageCache = new Map();
        this.userSettings = this.loadUserSettings();
        this.commandHandler = new CommandHandler(this);
        this.messageFormatter = new MessageFormatter();
        this.fileUploader = new FileUploader(this);
        
        this.init();
    }
    
    init() {
        this.createDOM();
        this.bindEvents();
        this.setupSocketHandlers();
        this.loadInitialData();
    }
    
    createDOM() {
        const template = `
            <div class="chat-container">
                <!-- Left Sidebar -->
                <div class="chat-sidebar">
                    <div class="workspace-header">
                        <h3>AI Workflow</h3>
                        <button class="workspace-settings">⚙️</button>
                    </div>
                    
                    <div class="channel-section">
                        <div class="section-header">
                            <span>Channels</span>
                            <button class="add-channel">+</button>
                        </div>
                        <div class="channel-list">
                            <div class="channel-item active" data-channel="general">
                                <span class="channel-icon">#</span>
                                <span class="channel-name">general</span>
                                <span class="unread-count hidden">0</span>
                            </div>
                            <div class="channel-item" data-channel="workflow">
                                <span class="channel-icon">#</span>
                                <span class="channel-name">workflow</span>
                                <span class="unread-count hidden">0</span>
                            </div>
                            <div class="channel-item" data-channel="agents">
                                <span class="channel-icon">#</span>
                                <span class="channel-name">agents</span>
                                <span class="unread-count hidden">0</span>
                            </div>
                            <div class="channel-item" data-channel="errors">
                                <span class="channel-icon">#</span>
                                <span class="channel-name">errors</span>
                                <span class="unread-count hidden">0</span>
                            </div>
                        </div>
                    </div>
                    
                    <div class="direct-messages">
                        <div class="section-header">
                            <span>Agents</span>
                        </div>
                        <div class="dm-list">
                            <div class="dm-item" data-agent="orchestrator">
                                <span class="status-dot online"></span>
                                <span class="agent-icon">🎭</span>
                                <span class="agent-name">Orchestrator</span>
                            </div>
                            <div class="dm-item" data-agent="code">
                                <span class="status-dot"></span>
                                <span class="agent-icon">💻</span>
                                <span class="agent-name">Code Agent</span>
                            </div>
                        </div>
                    </div>
                    
                    <div class="user-section">
                        <div class="user-info">
                            <span class="user-avatar">👤</span>
                            <div class="user-details">
                                <span class="username">Developer</span>
                                <span class="user-status">Working in Flow Mode</span>
                            </div>
                        </div>
                    </div>
                </div>
                
                <!-- Main Chat Area -->
                <div class="chat-main">
                    <div class="chat-header">
                        <div class="header-info">
                            <h3 class="channel-title"># general</h3>
                            <span class="channel-description">General discussion</span>
                        </div>
                        <div class="header-actions">
                            <button class="btn-icon" title="Search messages">🔍</button>
                            <button class="btn-icon" title="Pinned messages">📌</button>
                            <button class="btn-icon" title="Channel settings">⚙️</button>
                        </div>
                    </div>
                    
                    <div class="messages-container" id="messages">
                        <div class="messages-list"></div>
                        <div class="typing-indicator hidden">
                            <span class="typing-dots">
                                <span></span><span></span><span></span>
                            </span>
                            <span class="typing-text"></span>
                        </div>
                    </div>
                    
                    <div class="chat-input-container">
                        <div class="chat-input-wrapper">
                            <button class="btn-attach" title="Attach files">📎</button>
                            <div class="input-field">
                                <div class="input-content" contenteditable="true" 
                                     placeholder="Message #general"></div>
                                <div class="command-suggestions hidden"></div>
                            </div>
                            <div class="input-actions">
                                <button class="btn-emoji" title="Emoji">😊</button>
                                <button class="btn-send" title="Send message">
                                    <svg viewBox="0 0 24 24" width="20" height="20">
                                        <path d="M2 21l21-9L2 3v7l15 2-15 2v7z"/>
                                    </svg>
                                </button>
                            </div>
                        </div>
                        <div class="input-footer">
                            <span class="char-count">0</span>
                            <span class="input-hints">
                                <kbd>/</kbd> for commands • 
                                <kbd>Shift+Enter</kbd> for new line
                            </span>
                        </div>
                    </div>
                </div>
                
                <!-- Right Sidebar -->
                <div class="chat-right-sidebar">
                    <div class="sidebar-tabs">
                        <button class="tab active" data-tab="context">Context</button>
                        <button class="tab" data-tab="approvals">Approvals</button>
                        <button class="tab" data-tab="files">Files</button>
                    </div>
                    
                    <div class="sidebar-content">
                        <!-- Context Tab -->
                        <div class="tab-panel active" data-panel="context">
                            <div class="workflow-status">
                                <h4>Current State</h4>
                                <div class="state-badge">SPRINT_ACTIVE</div>
                                <div class="mini-state-diagram"></div>
                            </div>
                            
                            <div class="active-agents">
                                <h4>Active Agents</h4>
                                <div class="agent-list"></div>
                            </div>
                            
                            <div class="current-tasks">
                                <h4>Current Tasks</h4>
                                <div class="task-list"></div>
                            </div>
                        </div>
                        
                        <!-- Approvals Tab -->
                        <div class="tab-panel" data-panel="approvals">
                            <div class="pending-approvals">
                                <h4>Pending Approvals</h4>
                                <div class="approval-list"></div>
                            </div>
                        </div>
                        
                        <!-- Files Tab -->
                        <div class="tab-panel" data-panel="files">
                            <div class="recent-files">
                                <h4>Recent Files</h4>
                                <div class="file-list"></div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        `;
        
        // Insert into page
        document.getElementById('chat-root').innerHTML = template;
    }
    
    setupMessageHandlers() {
        // Enhanced message rendering with rich content
        this.messageRenderer = new MessageRenderer({
            renderCode: true,
            renderMentions: true,
            renderEmoji: true,
            renderAttachments: true,
            renderApprovals: true,
            syntaxHighlighter: 'prism'  // or 'highlight.js'
        });
    }
    
    async handleApprovalMessage(message) {
        const approvalUI = new ApprovalUI(message);
        
        approvalUI.on('approve', async (data) => {
            await this.socket.emit('approval_response', {
                approval_id: message.approval_id,
                action: 'approve',
                data: data
            });
        });
        
        approvalUI.on('reject', async (reason) => {
            await this.socket.emit('approval_response', {
                approval_id: message.approval_id,
                action: 'reject',
                reason: reason
            });
        });
        
        return approvalUI.render();
    }
}

// Command handler with autocomplete
class CommandHandler {
    constructor(chat) {
        this.chat = chat;
        this.commands = this.loadCommands();
        this.history = [];
        this.historyIndex = -1;
    }
    
    loadCommands() {
        return [
            {
                name: '/help',
                description: 'Show available commands',
                usage: '/help [command]',
                category: 'general'
            },
            {
                name: '/epic',
                description: 'Create or manage epics',
                usage: '/epic "<title>" "<description>"',
                category: 'workflow',
                autocomplete: async (args) => {
                    if (args.length === 0) {
                        return ['create', 'list', 'update', 'close'];
                    }
                }
            },
            {
                name: '/sprint',
                description: 'Sprint management',
                usage: '/sprint [plan|start|pause|resume|end]',
                category: 'workflow',
                subcommands: {
                    plan: { args: ['<duration>'], description: 'Plan a new sprint' },
                    start: { args: [], description: 'Start the planned sprint' },
                    pause: { args: ['[reason]'], description: 'Pause current sprint' },
                    resume: { args: [], description: 'Resume paused sprint' },
                    end: { args: [], description: 'End current sprint' }
                }
            },
            {
                name: '/assign',
                description: 'Assign task to agent',
                usage: '/assign <agent> "<task>"',
                category: 'agents',
                autocomplete: async (args) => {
                    if (args.length === 0) {
                        return ['orchestrator', 'code', 'design', 'qa', 'data'];
                    }
                }
            },
            {
                name: '/parallel',
                description: 'Execute tasks in parallel',
                usage: '/parallel "<task1>" "<task2>" ...',
                category: 'execution'
            },
            {
                name: '/mode',
                description: 'Switch workflow mode',
                usage: '/mode [strict|rapid|flow|expert|learning]',
                category: 'settings',
                autocomplete: async (args) => {
                    return ['strict', 'rapid', 'flow', 'expert', 'learning'];
                }
            }
        ];
    }
    
    getSuggestions(input) {
        if (!input.startsWith('/')) return [];
        
        const parts = input.slice(1).split(' ');
        const cmdName = '/' + parts[0];
        const args = parts.slice(1);
        
        // Find matching commands
        if (args.length === 0) {
            // Still typing command name
            return this.commands
                .filter(cmd => cmd.name.startsWith(cmdName))
                .map(cmd => ({
                    text: cmd.name,
                    description: cmd.description,
                    usage: cmd.usage,
                    category: cmd.category
                }));
        } else {
            // Command entered, get argument suggestions
            const command = this.commands.find(cmd => cmd.name === cmdName);
            if (command && command.autocomplete) {
                return command.autocomplete(args);
            }
        }
        
        return [];
    }
}
```

### Message Rendering System

```javascript
// message-renderer.js
class MessageRenderer {
    constructor(options) {
        this.options = options;
        this.codeHighlighter = new CodeHighlighter(options.syntaxHighlighter);
        this.emojiParser = new EmojiParser();
        this.mentionParser = new MentionParser();
    }
    
    render(message) {
        const messageEl = document.createElement('div');
        messageEl.className = `message ${message.author_type}`;
        messageEl.dataset.messageId = message.message_id;
        
        // Different layouts for different message types
        switch (message.metadata?.type) {
            case 'approval_request':
                return this.renderApprovalMessage(message);
            case 'agent_response':
                return this.renderAgentMessage(message);
            case 'code_snippet':
                return this.renderCodeMessage(message);
            case 'file_upload':
                return this.renderFileMessage(message);
            default:
                return this.renderStandardMessage(message);
        }
    }
    
    renderApprovalMessage(message) {
        const template = `
            <div class="message approval-request">
                <div class="message-icon">⚠️</div>
                <div class="message-content">
                    <div class="approval-header">
                        <h4>Approval Required</h4>
                        <span class="approval-id">#${message.approval_id.slice(0, 8)}</span>
                    </div>
                    <div class="approval-body">
                        ${this.renderContent(message.content)}
                    </div>
                    <div class="approval-changes">
                        ${this.renderChanges(message.changes)}
                    </div>
                    <div class="approval-actions">
                        <button class="btn btn-approve" data-action="approve">
                            ✅ Approve
                        </button>
                        <button class="btn btn-reject" data-action="reject">
                            ❌ Reject
                        </button>
                        <button class="btn btn-modify" data-action="modify">
                            ✏️ Modify
                        </button>
                        <button class="btn btn-details" data-action="details">
                            📋 Details
                        </button>
                    </div>
                    <div class="approval-footer">
                        <span class="expires-in">Expires in 30 minutes</span>
                    </div>
                </div>
            </div>
        `;
        
        const el = this.createElementFromTemplate(template);
        this.bindApprovalActions(el, message);
        return el;
    }
    
    renderAgentMessage(message) {
        const template = `
            <div class="message agent-message">
                <div class="message-header">
                    <span class="author">
                        <span class="agent-icon">${message.author_icon}</span>
                        ${message.author}
                    </span>
                    <span class="timestamp">${this.formatTime(message.timestamp)}</span>
                </div>
                <div class="message-body">
                    <div class="agent-status">
                        ${this.renderAgentStatus(message.metadata)}
                    </div>
                    <div class="message-content">
                        ${this.renderContent(message.content)}
                    </div>
                    ${message.code_blocks ? this.renderCodeBlocks(message.code_blocks) : ''}
                    ${message.attachments ? this.renderAttachments(message.attachments) : ''}
                </div>
                <div class="message-actions">
                    <button class="action-btn" title="Reply">💬</button>
                    <button class="action-btn" title="React">😊</button>
                    <button class="action-btn" title="More">⋮</button>
                </div>
            </div>
        `;
        
        return this.createElementFromTemplate(template);
    }
    
    renderCodeBlocks(blocks) {
        return blocks.map(block => `
            <div class="code-block">
                <div class="code-header">
                    <span class="language">${block.language}</span>
                    <button class="copy-btn" title="Copy code">📋</button>
                </div>
                <pre><code class="language-${block.language}">${
                    this.codeHighlighter.highlight(block.code, block.language)
                }</code></pre>
            </div>
        `).join('');
    }
}
```

## Integration Points

### 1. State Machine Integration

```python
# chat_state_integration.py
class ChatStateIntegration:
    def __init__(self, state_machine, chat_manager):
        self.state_machine = state_machine
        self.chat = chat_manager
        
        # Register state change listeners
        self.state_machine.on_transition(self.handle_state_transition)
        self.state_machine.on_blocked(self.handle_blocked_state)
        
    async def handle_state_transition(self, transition):
        """Send state transitions to chat"""
        # Create informative message
        message = {
            'channel': 'workflow',
            'author_type': 'system',
            'author_id': 'state_machine',
            'content': f"🔄 State transition: **{transition.from_state}** → **{transition.to_state}**",
            'metadata': {
                'type': 'state_transition',
                'transition': transition.to_dict(),
                'timestamp': datetime.now().isoformat()
            }
        }
        
        # Send to chat
        await self.chat.broadcast_message(message)
        
        # Update sidebar widget
        await self.update_workflow_widget(transition.to_state)
```

### 2. Discord Bot Migration Path

```python
# discord_migration.py
class DiscordMigrationBridge:
    """Bridge to support existing Discord bot while migrating to web chat"""
    
    def __init__(self, discord_bot, web_chat):
        self.discord = discord_bot
        self.chat = web_chat
        self.sync_enabled = True
        
    async def sync_discord_to_web(self, discord_message):
        """Sync Discord messages to web chat"""
        if not self.sync_enabled:
            return
            
        # Convert Discord message format
        web_message = {
            'channel': self.map_discord_channel(discord_message.channel.name),
            'author_type': 'user',
            'author_id': f'discord_{discord_message.author.id}',
            'content': discord_message.content,
            'metadata': {
                'source': 'discord',
                'original_id': discord_message.id
            }
        }
        
        # Send to web chat
        await self.chat.handle_message(web_message)
        
    async def sync_web_to_discord(self, web_message):
        """Sync web chat messages to Discord"""
        if not self.sync_enabled:
            return
            
        # Find Discord channel
        channel = self.discord.get_channel(
            self.map_web_channel(web_message['channel'])
        )
        
        if channel:
            # Format for Discord
            embed = self.create_discord_embed(web_message)
            await channel.send(embed=embed)
```

## Performance Optimizations

### 1. Message Caching

```javascript
class MessageCache {
    constructor(maxSize = 1000) {
        this.cache = new Map();
        this.maxSize = maxSize;
        this.accessOrder = [];
    }
    
    get(messageId) {
        const message = this.cache.get(messageId);
        if (message) {
            // Update access order for LRU
            this.updateAccessOrder(messageId);
        }
        return message;
    }
    
    set(messageId, message) {
        // Evict oldest if at capacity
        if (this.cache.size >= this.maxSize) {
            this.evictOldest();
        }
        
        this.cache.set(messageId, message);
        this.accessOrder.push(messageId);
    }
}
```

### 2. Virtual Scrolling for Messages

```javascript
class VirtualMessageScroller {
    constructor(container, messageHeight = 80) {
        this.container = container;
        this.messageHeight = messageHeight;
        this.visibleRange = { start: 0, end: 50 };
        this.messages = [];
        this.messageElements = new Map();
        
        this.setupScrollHandler();
    }
    
    renderVisibleMessages() {
        const scrollTop = this.container.scrollTop;
        const containerHeight = this.container.clientHeight;
        
        // Calculate visible range
        const start = Math.floor(scrollTop / this.messageHeight);
        const end = Math.ceil((scrollTop + containerHeight) / this.messageHeight);
        
        // Remove messages outside range
        for (let i = this.visibleRange.start; i < start; i++) {
            this.removeMessage(i);
        }
        for (let i = end + 1; i <= this.visibleRange.end; i++) {
            this.removeMessage(i);
        }
        
        // Render messages in range
        for (let i = start; i <= end && i < this.messages.length; i++) {
            if (!this.messageElements.has(i)) {
                this.renderMessage(i);
            }
        }
        
        this.visibleRange = { start, end };
    }
}
```

## Security Considerations

### 1. Input Sanitization

```javascript
class MessageSanitizer {
    sanitize(content) {
        // Prevent XSS
        const div = document.createElement('div');
        div.textContent = content;
        let sanitized = div.innerHTML;
        
        // Allow specific formatting
        sanitized = this.preserveFormatting(sanitized);
        
        // Sanitize file paths
        sanitized = this.sanitizeFilePaths(sanitized);
        
        return sanitized;
    }
    
    preserveFormatting(content) {
        // Preserve markdown-style formatting
        return content
            .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
            .replace(/\*(.*?)\*/g, '<em>$1</em>')
            .replace(/`(.*?)`/g, '<code>$1</code>')
            .replace(/\n/g, '<br>');
    }
}
```

### 2. File Upload Security

```python
class SecureFileUploader:
    ALLOWED_EXTENSIONS = {
        'txt', 'md', 'py', 'js', 'json', 'yaml', 'yml',
        'png', 'jpg', 'jpeg', 'gif', 'pdf', 'csv'
    }
    MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
    
    def validate_file(self, file_data):
        # Check file size
        if len(file_data) > self.MAX_FILE_SIZE:
            raise ValueError("File too large")
            
        # Check extension
        filename = secure_filename(file_data['filename'])
        ext = filename.rsplit('.', 1)[1].lower()
        
        if ext not in self.ALLOWED_EXTENSIONS:
            raise ValueError(f"File type .{ext} not allowed")
            
        # Scan for malicious content
        if self.contains_malicious_content(file_data['content']):
            raise ValueError("Malicious content detected")
            
        return True
```

## Deployment Architecture

```yaml
# docker-compose.yml for integrated deployment
version: '3.8'

services:
  web-interface:
    build: ./web-interface
    ports:
      - "5000:5000"
    environment:
      - FLASK_ENV=production
      - DATABASE_URL=sqlite:///data/chat.db
      - REDIS_URL=redis://redis:6379
    volumes:
      - ./data:/app/data
      - ./uploads:/app/uploads
    depends_on:
      - redis
      
  state-broadcaster:
    build: ./state-broadcaster
    ports:
      - "8080:8080"
    depends_on:
      - redis
      
  redis:
    image: redis:alpine
    volumes:
      - redis-data:/data
      
  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./ssl:/etc/nginx/ssl
    depends_on:
      - web-interface

volumes:
  redis-data:
```

## Migration Plan

### Phase 1: Deploy alongside Discord (Week 1)
- Deploy web chat interface
- Implement message syncing
- Test with small group

### Phase 2: Feature parity (Week 2)
- Implement all Discord commands
- Add file handling
- Polish UI/UX

### Phase 3: Migration incentives (Week 3)
- Add web-only features
- Improve performance
- Create migration guide

### Phase 4: Discord optional (Week 4)
- Make Discord bot optional
- Full feature availability in web
- Monitor usage metrics

This comprehensive implementation provides a Discord-like experience fully integrated with the workflow system, making Discord completely optional while providing a superior integrated experience.