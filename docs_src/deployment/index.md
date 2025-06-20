# 🚀 Deployment

Production deployment guides and configuration for the AI Agent TDD-Scrum Workflow system.

## Deployment Options

The system supports multiple deployment strategies for different use cases and environments.

<div class="grid cards" markdown>

-   :material-discord:{ .lg .middle } **Discord Setup**

    ---
    
    Configure Discord bot and server integration
    
    [:octicons-arrow-right-24: Discord](discord-setup.md)

-   :material-server:{ .lg .middle } **Production Deployment**

    ---
    
    Production-ready server deployment with monitoring
    
    [:octicons-arrow-right-24: Production](production.md)

-   :material-github:{ .lg .middle } **GitHub Pages**

    ---
    
    Deploy documentation site to GitHub Pages
    
    [:octicons-arrow-right-24: GitHub Pages](github-pages.md)

-   :material-wrench:{ .lg .middle } **Operations Guide**

    ---
    
    System operations and troubleshooting procedures
    
    [:octicons-arrow-right-24: Operations](operations.md)

</div>

## Quick Deployment Overview

### Local Development

```bash
# Basic local setup
git clone https://github.com/jmontp/agent-workflow.git
cd agent-workflow
make install
export DISCORD_BOT_TOKEN="your_token_here"
make run
```

### Production Server

```bash
# Production deployment with virtual environment
python3 -m venv /opt/agent-workflow/venv
source /opt/agent-workflow/venv/bin/activate
pip install agent-workflow

# Set environment variables
export DISCORD_BOT_TOKEN="your_token"
export ENVIRONMENT="production"

# Start the orchestrator
agent-orch start
```

### Cloud Deployment

Supports deployment on major cloud platforms using standard Python deployment methods:

- **AWS**: EC2 instances with systemd services
- **Google Cloud**: Compute Engine with process management
- **Azure**: Virtual Machines with standard Python deployment
- **DigitalOcean**: Droplets with virtual environments and systemd

## Configuration Management

### Environment Variables

Required environment variables for production:

```bash
# Discord Integration
DISCORD_BOT_TOKEN="your_discord_bot_token"
DISCORD_GUILD_ID="your_guild_id"  # Optional: restrict to specific server

# AI Integration
CLAUDE_API_KEY="your_claude_api_key"  # Optional: enhanced AI capabilities
OPENAI_API_KEY="your_openai_api_key"  # Alternative AI provider

# Database Configuration
DATABASE_URL="postgresql://user:pass@host:5432/dbname"  # Optional: external DB

# Security
SECRET_KEY="your_secret_key"
JWT_SECRET="your_jwt_secret"

# Monitoring
SENTRY_DSN="your_sentry_dsn"  # Optional: error tracking
PROMETHEUS_PORT="9090"        # Optional: metrics

# Application
ENVIRONMENT="production"
LOG_LEVEL="INFO"
DEBUG="false"
```

### Configuration Files

#### `config/production.yaml`

```yaml
# Production configuration
server:
  host: "0.0.0.0"
  port: 8080
  workers: 4

database:
  pool_size: 20
  max_overflow: 30
  pool_timeout: 30

security:
  rate_limit: 100  # requests per minute
  max_projects: 50
  session_timeout: 3600

monitoring:
  enable_metrics: true
  health_check_interval: 30
  log_retention_days: 30

agents:
  max_concurrent: 10
  timeout_seconds: 300
  memory_limit_mb: 1024
```

## Security Configuration

### Production Security Checklist

- [ ] **Environment Variables**: All secrets in environment variables
- [ ] **HTTPS**: TLS/SSL certificates configured
- [ ] **Firewall**: Restrict access to required ports only
- [ ] **Authentication**: Discord OAuth properly configured
- [ ] **Rate Limiting**: Request rate limits enabled
- [ ] **Logging**: Security events logged and monitored
- [ ] **Backups**: Regular backup strategy implemented
- [ ] **Updates**: Automated security updates enabled

### Discord Bot Security

```python
# Bot permissions (minimum required)
DISCORD_PERMISSIONS = [
    'send_messages',
    'use_slash_commands',
    'read_message_history',
    'embed_links',
    'attach_files'
]

# Restrict to specific servers
ALLOWED_GUILDS = [
    'your_development_server_id',
    'your_production_server_id'
]
```

## Monitoring and Observability

### Health Checks

The system provides health check endpoints:

```bash
# Application health - use CLI command instead of HTTP endpoints
agent-orch health --check-all

# System health (includes configuration, dependencies, integrations)
agent-orch health --check-all --verbose

# Export health report for monitoring
agent-orch health --check-all --export-report health-report.json

# NOTE: No HTTP health endpoints (/health, /health/db, /health/discord) are currently implemented
# Health checking is done via the CLI command which validates:
# - System requirements (Python version, platform)
# - Configuration files and settings
# - Dependencies availability
# - Integration status (Discord, AI provider)
# - File system permissions
# - Performance metrics (when --check-all flag is used)
```

### Metrics

**NOTE**: The main orchestrator does not currently expose `/metrics` endpoints. However, the visualizer app (`tools/visualizer/app.py`) does provide metrics:

- `/metrics` endpoint in visualizer app (port 5000) - Prometheus-compatible metrics
- Metrics include workflow state, TDD cycles, connected clients

Prometheus metrics available at `http://localhost:5000/metrics` (when visualizer is running):

- **Agent Execution Time**: Time spent executing agents
- **Command Success Rate**: Success/failure rate of commands
- **Active Projects**: Number of active projects
- **Resource Usage**: CPU, memory, and disk usage

### Logging

Structured logging configuration:

```json
{
  "timestamp": "2024-01-15T10:30:00Z",
  "level": "INFO",
  "component": "orchestrator",
  "project_id": "myproject",
  "event": "sprint_started",
  "user_id": "user123",
  "duration_ms": 150
}
```

## Backup and Recovery

### Data Backup Strategy

```bash
# Database backup (if using external DB)
pg_dump $DATABASE_URL > backup_$(date +%Y%m%d_%H%M%S).sql

# Project data backup
tar -czf projects_backup_$(date +%Y%m%d).tar.gz /data/projects/

# Configuration backup
cp -r config/ backups/config_$(date +%Y%m%d)/
```

### Disaster Recovery

1. **Automated Backups**: Daily backup to cloud storage
2. **Health Monitoring**: Automated failure detection
3. **Recovery Procedures**: Documented recovery steps
4. **Testing**: Regular disaster recovery testing

## Scaling Considerations

### Horizontal Scaling

```ini
# Multiple systemd services for horizontal scaling
# /etc/systemd/system/agent-workflow@.service
[Unit]
Description=AI Agent Workflow Orchestrator (Instance %i)
After=network.target

[Service]
Type=simple
User=agent-workflow
WorkingDirectory=/opt/agent-workflow
Environment=PATH=/opt/agent-workflow/venv/bin
Environment=DISCORD_BOT_TOKEN=your_token_here
Environment=ENVIRONMENT=production
Environment=INSTANCE_ID=%i
ExecStart=/opt/agent-workflow/venv/bin/agent-orch start --instance %i
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target

# Enable multiple instances:
# systemctl enable agent-workflow@1.service
# systemctl enable agent-workflow@2.service
# systemctl enable agent-workflow@3.service
```

### Performance Optimization

- **Connection Pooling**: Database connection management
- **Caching**: Redis for session and temporary data
- **CDN**: Static asset delivery optimization
- **Load Balancing**: Request distribution

## Troubleshooting Deployment Issues

### Common Issues

1. **Discord Bot Not Responding**
   - Check token validity
   - Verify bot permissions
   - Check server invite status

2. **Database Connection Errors**
   - Verify connection string
   - Check firewall rules
   - Validate credentials

3. **High Memory Usage**
   - Monitor agent execution
   - Check for memory leaks
   - Optimize context management

4. **Slow Response Times**
   - Check database performance
   - Monitor agent execution time
   - Optimize network latency

### Debugging Commands

```bash
# Check application logs
journalctl -u agent-workflow -f

# Monitor resource usage
htop -p $(pgrep -f agent-orch)

# Test Discord connectivity
python -c "import discord; print('Discord connection OK')"

# Check system health
agent-orch health
```

## Next Steps

For specific deployment scenarios:

- **[Discord Setup](discord-setup.md)** - Configure Discord bot and integration
- **[Production Deployment](production.md)** - Complete production setup guide
- **[GitHub Pages](github-pages.md)** - Deploy documentation site