/**
 * Chat Components Module
 * 
 * Specialized components for rendering different types of chat messages,
 * rich embeds, and interactive elements in the Discord-style interface.
 */

class ChatComponents {
    constructor() {
        this.messageRenderers = {
            'user': this.renderUserMessage.bind(this),
            'bot': this.renderBotMessage.bind(this),
            'system': this.renderSystemMessage.bind(this),
            'typing': this.renderTypingMessage.bind(this),
            'error': this.renderErrorMessage.bind(this)
        };
        
        this.commandRenderers = {
            'epic': this.renderEpicCommand.bind(this),
            'sprint': this.renderSprintCommand.bind(this),
            'approve': this.renderApprovalCommand.bind(this),
            'state': this.renderStateCommand.bind(this),
            'backlog': this.renderBacklogCommand.bind(this)
        };
        
        this.embedRenderers = {
            'workflow_state': this.renderWorkflowEmbed.bind(this),
            'tdd_cycle': this.renderTDDEmbed.bind(this),
            'epic_details': this.renderEpicEmbed.bind(this),
            'sprint_summary': this.renderSprintEmbed.bind(this),
            'error_details': this.renderErrorEmbed.bind(this)
        };
    }
    
    /**
     * Render a message based on type
     */
    renderMessage(messageData) {
        const renderer = this.messageRenderers[messageData.type];
        if (renderer) {
            return renderer(messageData);
        }
        return this.renderGenericMessage(messageData);
    }
    
    /**
     * Render user message
     */
    renderUserMessage(messageData) {
        const messageElement = document.createElement('div');
        messageElement.className = 'message user-message';
        messageElement.setAttribute('data-message-id', messageData.id);
        
        const timestamp = this.formatTimestamp(messageData.timestamp);
        const isCommand = messageData.message.startsWith('/');
        
        messageElement.innerHTML = `
            <div class="message-container">
                <div class="avatar-container">
                    <div class="avatar user-avatar">
                        <span class="avatar-text">${this.getAvatarInitials(messageData.username)}</span>
                    </div>
                </div>
                <div class="message-content-container">
                    <div class="message-header">
                        <span class="username">${this.escapeHtml(messageData.username)}</span>
                        <span class="timestamp">${timestamp}</span>
                    </div>
                    <div class="message-body ${isCommand ? 'command-message' : ''}">
                        ${this.formatMessageContent(messageData.message, isCommand)}
                    </div>
                </div>
            </div>
        `;
        
        return messageElement;
    }
    
    /**
     * Render bot message with rich formatting
     */
    renderBotMessage(messageData) {
        const messageElement = document.createElement('div');
        messageElement.className = `message bot-message ${messageData.error ? 'error-message' : ''}`;
        messageElement.setAttribute('data-message-id', messageData.id);
        
        const timestamp = this.formatTimestamp(messageData.timestamp);
        const hasCommandResult = messageData.command_result;
        
        messageElement.innerHTML = `
            <div class="message-container">
                <div class="avatar-container">
                    <div class="avatar bot-avatar">
                        <span class="bot-icon">🤖</span>
                    </div>
                </div>
                <div class="message-content-container">
                    <div class="message-header">
                        <span class="username bot-username">Agent Bot</span>
                        <span class="bot-badge">BOT</span>
                        <span class="timestamp">${timestamp}</span>
                    </div>
                    <div class="message-body">
                        ${hasCommandResult ? this.renderCommandResult(messageData.command_result) : this.formatMessageContent(messageData.message)}
                    </div>
                </div>
            </div>
        `;
        
        return messageElement;
    }
    
    /**
     * Render system message
     */
    renderSystemMessage(messageData) {
        const messageElement = document.createElement('div');
        messageElement.className = 'message system-message';
        messageElement.setAttribute('data-message-id', messageData.id);
        
        const timestamp = this.formatTimestamp(messageData.timestamp);
        
        messageElement.innerHTML = `
            <div class="system-message-container">
                <div class="system-icon">ℹ️</div>
                <div class="system-content">
                    <span class="system-text">${this.escapeHtml(messageData.message)}</span>
                    <span class="timestamp">${timestamp}</span>
                </div>
            </div>
        `;
        
        return messageElement;
    }
    
    /**
     * Render typing indicator message
     */
    renderTypingMessage(messageData) {
        const messageElement = document.createElement('div');
        messageElement.className = 'message typing-message';
        messageElement.setAttribute('data-message-id', messageData.id);
        
        messageElement.innerHTML = `
            <div class="message-container">
                <div class="avatar-container">
                    <div class="avatar ${messageData.user_id === 'bot' ? 'bot-avatar' : 'user-avatar'}">
                        ${messageData.user_id === 'bot' ? '<span class="bot-icon">🤖</span>' : '<span class="avatar-text">' + this.getAvatarInitials(messageData.username) + '</span>'}
                    </div>
                </div>
                <div class="message-content-container">
                    <div class="typing-indicator">
                        <span class="typing-text">${this.escapeHtml(messageData.username)} is typing</span>
                        <div class="typing-dots">
                            <span class="dot"></span>
                            <span class="dot"></span>
                            <span class="dot"></span>
                        </div>
                    </div>
                </div>
            </div>
        `;
        
        return messageElement;
    }
    
    /**
     * Render error message
     */
    renderErrorMessage(messageData) {
        const messageElement = document.createElement('div');
        messageElement.className = 'message error-message';
        messageElement.setAttribute('data-message-id', messageData.id);
        
        const timestamp = this.formatTimestamp(messageData.timestamp);
        
        messageElement.innerHTML = `
            <div class="error-message-container">
                <div class="error-icon">⚠️</div>
                <div class="error-content">
                    <div class="error-title">Error</div>
                    <div class="error-text">${this.escapeHtml(messageData.message)}</div>
                    <span class="timestamp">${timestamp}</span>
                </div>
            </div>
        `;
        
        return messageElement;
    }
    
    /**
     * Render command result with rich formatting
     */
    renderCommandResult(commandResult) {
        if (!commandResult) return '';
        
        const command = commandResult.command;
        const commandType = command ? command.split(' ')[0].substring(1) : 'unknown';
        
        // Use specialized renderer if available
        const renderer = this.commandRenderers[commandType];
        if (renderer) {
            return renderer(commandResult);
        }
        
        return this.renderGenericCommandResult(commandResult);
    }
    
    /**
     * Render generic command result
     */
    renderGenericCommandResult(result) {
        let html = '<div class="command-result">';
        
        if (result.command) {
            html += `<div class="command-echo">
                <span class="command-label">Command:</span>
                <code class="command-text">${this.escapeHtml(result.command)}</code>
            </div>`;
        }
        
        if (result.success !== undefined) {
            const statusIcon = result.success ? '✅' : '❌';
            const statusClass = result.success ? 'success' : 'error';
            html += `<div class="command-status ${statusClass}">
                <span class="status-icon">${statusIcon}</span>
                <span class="status-text">${result.success ? 'Success' : 'Failed'}</span>
            </div>`;
        }
        
        if (result.response) {
            html += `<div class="command-response">
                ${this.formatMessageContent(result.response)}
            </div>`;
        }
        
        // Render embedded data if present
        if (result.embed_type && result.embed_data) {
            const embedRenderer = this.embedRenderers[result.embed_type];
            if (embedRenderer) {
                html += embedRenderer(result.embed_data);
            }
        }
        
        html += '</div>';
        return html;
    }
    
    /**
     * Render epic command result
     */
    renderEpicCommand(result) {
        let html = '<div class="command-result epic-result">';
        
        if (result.command) {
            html += `<div class="command-header">
                <span class="command-icon">📋</span>
                <span class="command-title">Epic Created</span>
            </div>`;
        }
        
        if (result.data && result.data.epic) {
            const epic = result.data.epic;
            html += `<div class="epic-card">
                <div class="epic-title">${this.escapeHtml(epic.title || epic.description)}</div>
                <div class="epic-details">
                    <div class="epic-id">Epic ID: ${epic.id}</div>
                    <div class="epic-status">Status: ${epic.status || 'Active'}</div>
                </div>
            </div>`;
        }
        
        if (result.response) {
            html += `<div class="command-response">${this.formatMessageContent(result.response)}</div>`;
        }
        
        html += '</div>';
        return html;
    }
    
    /**
     * Render sprint command result
     */
    renderSprintCommand(result) {
        let html = '<div class="command-result sprint-result">';
        
        const sprintAction = result.command ? result.command.split(' ')[1] : 'unknown';
        const actionIcons = {
            'plan': '📋',
            'start': '🚀',
            'pause': '⏸️',
            'resume': '▶️',
            'status': '📊'
        };
        
        html += `<div class="command-header">
            <span class="command-icon">${actionIcons[sprintAction] || '🏃'}</span>
            <span class="command-title">Sprint ${sprintAction.charAt(0).toUpperCase() + sprintAction.slice(1)}</span>
        </div>`;
        
        if (result.data && result.data.sprint) {
            const sprint = result.data.sprint;
            html += `<div class="sprint-card">
                <div class="sprint-title">Sprint ${sprint.id || 'Current'}</div>
                <div class="sprint-details">
                    <div class="sprint-status">Status: ${sprint.status}</div>
                    <div class="sprint-progress">Progress: ${sprint.completed_stories || 0}/${sprint.total_stories || 0} stories</div>
                </div>
            </div>`;
        }
        
        if (result.response) {
            html += `<div class="command-response">${this.formatMessageContent(result.response)}</div>`;
        }
        
        html += '</div>';
        return html;
    }
    
    /**
     * Render approval command result
     */
    renderApprovalCommand(result) {
        let html = '<div class="command-result approval-result">';
        
        html += `<div class="command-header">
            <span class="command-icon">✅</span>
            <span class="command-title">Approval Processed</span>
        </div>`;
        
        if (result.data && result.data.approved_items) {
            html += '<div class="approval-list">';
            result.data.approved_items.forEach(item => {
                html += `<div class="approval-item">
                    <span class="approval-icon">✅</span>
                    <span class="approval-text">${this.escapeHtml(item.title || item.description)}</span>
                </div>`;
            });
            html += '</div>';
        }
        
        if (result.response) {
            html += `<div class="command-response">${this.formatMessageContent(result.response)}</div>`;
        }
        
        html += '</div>';
        return html;
    }
    
    /**
     * Render state command result
     */
    renderStateCommand(result) {
        let html = '<div class="command-result state-result">';
        
        html += `<div class="command-header">
            <span class="command-icon">📊</span>
            <span class="command-title">Current State</span>
        </div>`;
        
        if (result.data) {
            html += '<div class="state-overview">';
            
            if (result.data.workflow_state) {
                html += `<div class="state-item">
                    <span class="state-label">Workflow:</span>
                    <span class="state-value workflow-state">${result.data.workflow_state}</span>
                </div>`;
            }
            
            if (result.data.tdd_cycles) {
                html += `<div class="state-item">
                    <span class="state-label">Active TDD Cycles:</span>
                    <span class="state-value tdd-count">${result.data.tdd_cycles.length || 0}</span>
                </div>`;
            }
            
            if (result.data.current_sprint) {
                html += `<div class="state-item">
                    <span class="state-label">Current Sprint:</span>
                    <span class="state-value sprint-info">${result.data.current_sprint.id} (${result.data.current_sprint.status})</span>
                </div>`;
            }
            
            html += '</div>';
        }
        
        if (result.response) {
            html += `<div class="command-response">${this.formatMessageContent(result.response)}</div>`;
        }
        
        html += '</div>';
        return html;
    }
    
    /**
     * Render backlog command result
     */
    renderBacklogCommand(result) {
        let html = '<div class="command-result backlog-result">';
        
        const backlogAction = result.command ? result.command.split(' ')[1] : 'unknown';
        const actionIcons = {
            'view': '👁️',
            'add_story': '➕',
            'prioritize': '🔄'
        };
        
        html += `<div class="command-header">
            <span class="command-icon">${actionIcons[backlogAction] || '📋'}</span>
            <span class="command-title">Backlog ${backlogAction.charAt(0).toUpperCase() + backlogAction.slice(1)}</span>
        </div>`;
        
        if (result.data && result.data.stories) {
            html += '<div class="story-list">';
            result.data.stories.slice(0, 5).forEach(story => { // Show first 5 stories
                html += `<div class="story-item">
                    <div class="story-priority">P${story.priority || 'N/A'}</div>
                    <div class="story-content">
                        <div class="story-title">${this.escapeHtml(story.title)}</div>
                        <div class="story-status">${story.status || 'Backlog'}</div>
                    </div>
                </div>`;
            });
            if (result.data.stories.length > 5) {
                html += `<div class="story-more">... and ${result.data.stories.length - 5} more stories</div>`;
            }
            html += '</div>';
        }
        
        if (result.response) {
            html += `<div class="command-response">${this.formatMessageContent(result.response)}</div>`;
        }
        
        html += '</div>';
        return html;
    }
    
    /**
     * Render workflow state embed
     */
    renderWorkflowEmbed(embedData) {
        return `<div class="embed workflow-embed">
            <div class="embed-header">
                <span class="embed-icon">🔄</span>
                <span class="embed-title">Workflow State</span>
            </div>
            <div class="embed-content">
                <div class="state-display">${embedData.current_state}</div>
                <div class="state-description">${embedData.description || ''}</div>
            </div>
        </div>`;
    }
    
    /**
     * Render TDD cycle embed
     */
    renderTDDEmbed(embedData) {
        return `<div class="embed tdd-embed">
            <div class="embed-header">
                <span class="embed-icon">🧪</span>
                <span class="embed-title">TDD Cycle</span>
            </div>
            <div class="embed-content">
                <div class="cycle-info">
                    <div class="cycle-story">Story: ${embedData.story_id}</div>
                    <div class="cycle-state">${embedData.current_state}</div>
                </div>
            </div>
        </div>`;
    }
    
    /**
     * Render error embed
     */
    renderErrorEmbed(embedData) {
        return `<div class="embed error-embed">
            <div class="embed-header">
                <span class="embed-icon">⚠️</span>
                <span class="embed-title">Error Details</span>
            </div>
            <div class="embed-content">
                <div class="error-message">${this.escapeHtml(embedData.message)}</div>
                ${embedData.details ? `<div class="error-details">${this.escapeHtml(embedData.details)}</div>` : ''}
            </div>
        </div>`;
    }
    
    /**
     * Render epic embed
     */
    renderEpicEmbed(embedData) {
        return `<div class="embed epic-embed">
            <div class="embed-header">
                <span class="embed-icon">📋</span>
                <span class="embed-title">Epic: ${this.escapeHtml(embedData.title || 'Epic Details')}</span>
            </div>
            <div class="embed-content">
                <div class="embed-description">${this.escapeHtml(embedData.description || '')}</div>
                <div class="embed-fields">
                    <div class="embed-field">
                        <div class="field-name">Epic ID</div>
                        <div class="field-value">${this.escapeHtml(embedData.epic_id || 'Unknown')}</div>
                    </div>
                    <div class="embed-field">
                        <div class="field-name">Status</div>
                        <div class="field-value">${this.escapeHtml(embedData.status || 'Active')}</div>
                    </div>
                    <div class="embed-field">
                        <div class="field-name">Stories</div>
                        <div class="field-value">${embedData.story_count || '0'}</div>
                    </div>
                </div>
            </div>
        </div>`;
    }
    
    /**
     * Render sprint embed
     */
    renderSprintEmbed(embedData) {
        return `<div class="embed sprint-embed">
            <div class="embed-header">
                <span class="embed-icon">🏃</span>
                <span class="embed-title">Sprint ${this.escapeHtml(embedData.sprint_id || 'Summary')}</span>
            </div>
            <div class="embed-content">
                <div class="embed-description">${this.escapeHtml(embedData.description || '')}</div>
                <div class="embed-fields">
                    <div class="embed-field">
                        <div class="field-name">Status</div>
                        <div class="field-value">${this.escapeHtml(embedData.status || 'Active')}</div>
                    </div>
                    <div class="embed-field">
                        <div class="field-name">Progress</div>
                        <div class="field-value">${embedData.progress || '0%'}</div>
                    </div>
                    <div class="embed-field">
                        <div class="field-name">Stories</div>
                        <div class="field-value">${embedData.completed_stories || 0}/${embedData.total_stories || 0}</div>
                    </div>
                </div>
            </div>
        </div>`;
    }
    
    /**
     * Render generic message
     */
    renderGenericMessage(messageData) {
        const messageElement = document.createElement('div');
        messageElement.className = 'message generic-message';
        messageElement.setAttribute('data-message-id', messageData.id);
        
        const timestamp = this.formatTimestamp(messageData.timestamp);
        
        messageElement.innerHTML = `
            <div class="message-container">
                <div class="message-content-container">
                    <div class="message-header">
                        <span class="username">${this.escapeHtml(messageData.username || 'Unknown')}</span>
                        <span class="timestamp">${timestamp}</span>
                    </div>
                    <div class="message-body">
                        ${this.formatMessageContent(messageData.message || '')}
                    </div>
                </div>
            </div>
        `;
        
        return messageElement;
    }
    
    /**
     * Format message content with markdown-like formatting
     */
    formatMessageContent(content, isCommand = false) {
        if (!content) return '';
        
        // Escape HTML first
        let formatted = this.escapeHtml(content);
        
        // Handle commands specially
        if (isCommand) {
            formatted = `<span class="command-text">${formatted}</span>`;
        }
        
        // Convert line breaks
        formatted = formatted.replace(/\n/g, '<br>');
        
        // Format inline code
        formatted = formatted.replace(/`([^`]+)`/g, '<code class="inline-code">$1</code>');
        
        // Format bold text
        formatted = formatted.replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>');
        
        // Format italic text
        formatted = formatted.replace(/\*([^*]+)\*/g, '<em>$1</em>');
        
        // Format URLs
        const urlRegex = /(https?:\/\/[^\s<>"{}|\\^`[\]]+)/g;
        formatted = formatted.replace(urlRegex, '<a href="$1" target="_blank" rel="noopener noreferrer" class="message-link">$1</a>');
        
        return formatted;
    }
    
    /**
     * Format timestamp for display
     */
    formatTimestamp(timestamp) {
        const date = new Date(timestamp);
        const now = new Date();
        
        // If today, show time only
        if (this.isSameDay(date, now)) {
            return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
        }
        
        // If yesterday, show "Yesterday"
        const yesterday = new Date(now);
        yesterday.setDate(yesterday.getDate() - 1);
        if (this.isSameDay(date, yesterday)) {
            return 'Yesterday ' + date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
        }
        
        // If this week, show day name
        const daysDiff = Math.floor((now - date) / (1000 * 60 * 60 * 24));
        if (daysDiff < 7) {
            return date.toLocaleDateString([], { weekday: 'short' }) + ' ' + 
                   date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
        }
        
        // Otherwise show date
        return date.toLocaleDateString([], { month: 'short', day: 'numeric' }) + ' ' +
               date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    }
    
    /**
     * Check if two dates are the same day
     */
    isSameDay(date1, date2) {
        return date1.getFullYear() === date2.getFullYear() &&
               date1.getMonth() === date2.getMonth() &&
               date1.getDate() === date2.getDate();
    }
    
    /**
     * Get avatar initials from username
     */
    getAvatarInitials(username) {
        if (!username) return '?';
        
        const words = username.trim().split(/\s+/);
        if (words.length === 1) {
            return words[0].charAt(0).toUpperCase();
        }
        
        return (words[0].charAt(0) + words[words.length - 1].charAt(0)).toUpperCase();
    }
    
    /**
     * Escape HTML to prevent XSS
     */
    escapeHtml(text) {
        if (!text) return '';
        
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
    
    /**
     * Create autocomplete dropdown
     */
    createAutocompleteDropdown(suggestions, selectedIndex = -1) {
        const dropdown = document.createElement('div');
        dropdown.className = 'autocomplete-dropdown';
        dropdown.id = 'autocomplete-dropdown';
        
        if (!suggestions || suggestions.length === 0) {
            dropdown.style.display = 'none';
            return dropdown;
        }
        
        const html = suggestions.map((suggestion, index) => `
            <div class="autocomplete-item ${index === selectedIndex ? 'selected' : ''}" 
                 data-index="${index}">
                <div class="autocomplete-command">${this.escapeHtml(suggestion.command)}</div>
                <div class="autocomplete-description">${this.escapeHtml(suggestion.description)}</div>
            </div>
        `).join('');
        
        dropdown.innerHTML = html;
        return dropdown;
    }
    
    /**
     * Update autocomplete selection
     */
    updateAutocompleteSelection(dropdown, selectedIndex) {
        const items = dropdown.querySelectorAll('.autocomplete-item');
        items.forEach((item, index) => {
            item.classList.toggle('selected', index === selectedIndex);
        });
    }
    
    /**
     * Create typing indicator element
     */
    createTypingIndicator(username, isBot = false) {
        const indicator = document.createElement('div');
        indicator.className = 'typing-indicator-container';
        indicator.id = 'typing-indicator';
        
        indicator.innerHTML = `
            <div class="typing-indicator">
                <div class="avatar-container">
                    <div class="avatar ${isBot ? 'bot-avatar' : 'user-avatar'}">
                        ${isBot ? '<span class="bot-icon">🤖</span>' : '<span class="avatar-text">' + this.getAvatarInitials(username) + '</span>'}
                    </div>
                </div>
                <div class="typing-content">
                    <span class="typing-text">${this.escapeHtml(username)} is typing</span>
                    <div class="typing-dots">
                        <span class="dot"></span>
                        <span class="dot"></span>
                        <span class="dot"></span>
                    </div>
                </div>
            </div>
        `;
        
        return indicator;
    }
    
    /**
     * Create message input component
     */
    createMessageInput() {
        const inputContainer = document.createElement('div');
        inputContainer.className = 'message-input-container';
        
        inputContainer.innerHTML = `
            <div class="input-wrapper">
                <textarea id="message-input" 
                         class="message-input" 
                         placeholder="Type a message or command..."
                         rows="1"
                         maxlength="2000"></textarea>
                <button id="send-button" class="send-button" type="button">
                    <svg width="24" height="24" viewBox="0 0 24 24" fill="currentColor">
                        <path d="M2.01 21L23 12 2.01 3 2 10l15 2-15 2z"/>
                    </svg>
                </button>
            </div>
            <div class="input-footer">
                <div class="input-hints">
                    <span class="hint">Type <code>/</code> for commands</span>
                    <span class="hint">Use <kbd>↑</kbd><kbd>↓</kbd> for history</span>
                    <span class="hint"><kbd>Shift</kbd>+<kbd>Enter</kbd> for new line</span>
                </div>
            </div>
        `;
        
        return inputContainer;
    }
}

// Export for module usage
if (typeof module !== 'undefined' && module.exports) {
    module.exports = ChatComponents;
}

// Also expose to window for browser usage
if (typeof window !== 'undefined') {
    window.ChatComponents = ChatComponents;
}