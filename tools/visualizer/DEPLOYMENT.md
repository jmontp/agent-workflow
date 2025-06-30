# Discord-Style Web Interface Deployment Guide

This guide covers deployment of the fully integrated Discord-style web visualization interface for the AI Agent TDD-Scrum Workflow system.

## Features Overview

The integrated interface provides:

### 🎯 Core Features
- **Discord-Style Chat**: Real-time chat interface with slash commands
- **State Visualization**: Live Mermaid diagrams for workflow and TDD states
- **Multi-User Collaboration**: Session management with permission levels
- **Agent Management**: Interface switching between Claude Code, Anthropic API, and Mock
- **Contextual Autocomplete**: Smart command suggestions based on current state
- **Responsive Design**: Works on desktop, tablet, and mobile devices

### 💬 Chat Interface Features
- Real-time messaging with WebSocket support
- Slash command system (`/epic`, `/sprint start`, `/approve`, etc.)
- Typing indicators and user presence
- Command history with arrow key navigation
- Message formatting with code highlighting
- Error handling with helpful suggestions

### 👥 Collaboration Features
- Multi-user sessions with permission management (viewer, contributor, maintainer, admin)
- Resource locking to prevent conflicts
- Real-time synchronization across all connected users
- Activity tracking and audit logs
- Session management with automatic cleanup

### 📊 Visualization Features
- Interactive state machine diagrams
- Real-time state transition highlighting
- TDD cycle progress tracking
- Agent activity monitoring
- Performance metrics dashboard

## Quick Deployment

### Using the CLI (Recommended)

```bash
# Install the package if not already installed
pip install agent-workflow

# Start the interface
aw web

# Or with custom options
aw web --port 8080 --host 0.0.0.0

# Run as daemon
aw web --daemon

# Check status
aw web-status

# Stop the interface
aw web-stop
```

### Direct Python Execution

```bash
# Navigate to the visualizer directory
cd tools/visualizer

# Install dependencies
pip install flask flask-socketio websockets

# Run the application
python app.py --host localhost --port 5000
```

## Configuration Options

### Environment Variables

```bash
# Discord Bot (optional - for Discord integration)
export DISCORD_BOT_TOKEN="your-bot-token"

# Database (optional - for persistence)
export DATABASE_URL="sqlite:///workflow.db"

# Security (optional - for production)
export SECRET_KEY="your-secret-key"

# Logging
export LOG_LEVEL="INFO"  # DEBUG, INFO, WARN, ERROR
```

### Application Configuration

The interface supports several configuration options:

```bash
# Basic options
python app.py --host 0.0.0.0 --port 5000 --debug

# Production options
python app.py --host 0.0.0.0 --port 80 --no-debug
```

## Production Deployment

### Using Docker

Create a `Dockerfile`:

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Copy requirements
COPY requirements.txt .
RUN pip install -r requirements.txt

# Copy application
COPY tools/visualizer/ ./visualizer/
COPY lib/ ./lib/

# Expose port
EXPOSE 5000

# Run application
CMD ["python", "visualizer/app.py", "--host", "0.0.0.0", "--port", "5000"]
```

Build and run:

```bash
docker build -t agent-workflow-web .
docker run -p 5000:5000 agent-workflow-web
```

### Using Docker Compose

Create `docker-compose.yml`:

```yaml
version: '3.8'

services:
  web:
    build: .
    ports:
      - "5000:5000"
    environment:
      - LOG_LEVEL=INFO
      - SECRET_KEY=your-production-secret-key
    volumes:
      - ./data:/app/data
    restart: unless-stopped

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./ssl:/etc/nginx/ssl
    depends_on:
      - web
    restart: unless-stopped
```

### Using systemd (Linux)

Create `/etc/systemd/system/agent-workflow-web.service`:

```ini
[Unit]
Description=Agent Workflow Web Interface
After=network.target

[Service]
Type=simple
User=www-data
WorkingDirectory=/opt/agent-workflow
ExecStart=/usr/bin/python3 tools/visualizer/app.py --host 0.0.0.0 --port 5000
Restart=always
RestartSec=3
Environment=LOG_LEVEL=INFO

[Install]
WantedBy=multi-user.target
```

Enable and start:

```bash
sudo systemctl daemon-reload
sudo systemctl enable agent-workflow-web
sudo systemctl start agent-workflow-web
```

### Nginx Reverse Proxy

Create `/etc/nginx/sites-available/agent-workflow`:

```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # WebSocket support
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "Upgrade";
        proxy_cache_bypass $http_upgrade;
    }
}
```

Enable the site:

```bash
sudo ln -s /etc/nginx/sites-available/agent-workflow /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

## Dependencies

### Required Python Packages

```txt
Flask>=2.3.0
Flask-SocketIO>=5.3.0
python-socketio>=5.8.0
websockets>=11.0
PyYAML>=6.0
aiohttp>=3.8.0
```

### Optional Dependencies

```txt
# For Discord integration
discord.py>=2.3.0

# For GitHub integration  
PyGithub>=1.59.0

# For enhanced security
python-jose[cryptography]>=3.3.0

# For production WSGI
gunicorn>=21.2.0
```

Install all dependencies:

```bash
pip install -r requirements.txt
```

## Security Considerations

### Authentication & Authorization

The interface includes built-in permission management:

- **Viewer**: Read-only access, can view state and history
- **Contributor**: Can execute basic commands like `/epic` and `/backlog`
- **Maintainer**: Can manage sprints and approve stories
- **Admin**: Full access including project registration

### Network Security

For production deployment:

1. **Use HTTPS**: Configure SSL/TLS certificates
2. **Firewall**: Restrict access to necessary ports only
3. **Rate Limiting**: Implement rate limiting for API endpoints
4. **CORS**: Configure appropriate CORS policies

### Session Security

```python
# In production, set secure session configuration
app.config.update(
    SECRET_KEY='your-strong-secret-key',
    SESSION_COOKIE_SECURE=True,
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE='Lax'
)
```

## Performance Optimization

### For High Traffic

1. **Use Gunicorn**: 
   ```bash
   gunicorn -w 4 -b 0.0.0.0:5000 --worker-class eventlet app:app
   ```

2. **Enable Compression**:
   ```python
   from flask_compress import Compress
   Compress(app)
   ```

3. **Use Redis for Sessions**:
   ```python
   app.config['SESSION_TYPE'] = 'redis'
   app.config['SESSION_REDIS'] = redis.from_url('redis://localhost:6379')
   ```

4. **CDN for Static Assets**: Serve CSS/JS files from a CDN

### Memory Management

- Configure appropriate worker memory limits
- Implement periodic cleanup of old sessions
- Use connection pooling for database connections

## Monitoring & Logging

### Health Checks

The application provides several monitoring endpoints:

- `/health` - Basic health check
- `/metrics` - Prometheus-compatible metrics
- `/debug` - Debug information (development only)

### Logging Configuration

```python
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/var/log/agent-workflow/app.log'),
        logging.StreamHandler()
    ]
)
```

### Metrics Collection

Example Prometheus configuration:

```yaml
scrape_configs:
  - job_name: 'agent-workflow'
    static_configs:
      - targets: ['localhost:5000']
    metrics_path: '/metrics'
    scrape_interval: 30s
```

## Troubleshooting

### Common Issues

1. **Port Already in Use**:
   ```bash
   # Find process using port
   sudo lsof -i :5000
   # Kill process
   sudo kill -9 <PID>
   ```

2. **WebSocket Connection Failed**:
   - Check firewall settings
   - Verify proxy configuration for WebSocket upgrade
   - Check browser console for errors

3. **Collaboration Features Not Working**:
   - Ensure collaboration_manager.py is properly imported
   - Check for any missing async dependencies
   - Verify session storage is working

4. **State Synchronization Issues**:
   - Check state_broadcaster WebSocket connection
   - Verify state machine imports
   - Review application logs for errors

### Debug Mode

Enable debug mode for development:

```bash
python app.py --debug
```

This enables:
- Detailed error messages
- Auto-reloading on code changes
- Enhanced logging
- Debug endpoints

### Log Analysis

Common log patterns to monitor:

```bash
# WebSocket connections
grep "SocketIO client connected" /var/log/agent-workflow/app.log

# Command execution
grep "Processing command" /var/log/agent-workflow/app.log

# Collaboration events
grep "Collaboration" /var/log/agent-workflow/app.log

# Errors
grep "ERROR" /var/log/agent-workflow/app.log
```

## API Reference

### WebSocket Events

**Client to Server:**
- `chat_command` - Send a chat command
- `join_chat` - Join chat session
- `start_typing` - Start typing indicator
- `stop_typing` - Stop typing indicator
- `request_state` - Request current state

**Server to Client:**
- `new_chat_message` - New message broadcast
- `command_response` - Command execution result
- `typing_indicator` - User typing status
- `workflow_transition` - State machine transition
- `collaboration_user_joined` - User joined session

### REST API Endpoints

**Chat API:**
- `POST /api/chat/send` - Send message
- `GET /api/chat/history` - Get message history
- `GET /api/chat/autocomplete` - Get command suggestions

**Collaboration API:**
- `POST /api/collaboration/join` - Join collaboration session
- `POST /api/collaboration/leave` - Leave session
- `GET /api/collaboration/status/<project>` - Get collaboration status

**State API:**
- `GET /api/state` - Get current state
- `GET /api/history` - Get transition history

## Support & Maintenance

### Regular Maintenance

1. **Log Rotation**: Configure logrotate for application logs
2. **Session Cleanup**: Old sessions are automatically cleaned up
3. **Database Maintenance**: Periodic cleanup of old transition history
4. **Security Updates**: Keep dependencies updated

### Backup Procedures

Important data to backup:
- Project configuration files
- State transition history
- User session data (if persisted)
- Application logs

### Update Procedures

1. Stop the application
2. Backup current installation
3. Update code and dependencies
4. Run any database migrations
5. Restart the application
6. Verify functionality

## Getting Help

- **GitHub Issues**: Report bugs and feature requests
- **Documentation**: Check docs_src/ for detailed guides
- **Logs**: Check application logs for error details
- **Debug Mode**: Use debug mode for development issues

For additional support, refer to the main project documentation and community resources.