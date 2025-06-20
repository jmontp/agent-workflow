# Health Monitoring & System Diagnostics

> **Comprehensive health checking and system diagnostics for the AI Agent TDD-Scrum workflow system**

## ✅ Current Health Checking Capabilities

The system provides health monitoring through CLI commands and specific application endpoints, not through general HTTP health APIs.

### 🎛️ CLI Health Command

The primary health checking mechanism is the `agent-orch health` CLI command:

```bash
# Basic health check
agent-orch health

# Comprehensive health check
agent-orch health --check-all

# Health check with auto-fix
agent-orch health --check-all --fix-issues

# Export health report
agent-orch health --check-all --export-report health-$(date +%Y%m%d).json

# Project-specific health check
agent-orch health --project my-project
```

### 📊 Health Check Categories

The CLI health command validates these system areas:

#### System Requirements
- Python version (3.8+ required)
- Platform compatibility (Linux, macOS, Windows)
- Memory and disk space availability
- Basic system resources

#### Configuration Health
- Configuration directory existence (`~/.agent-workflow/`)
- Configuration file validity (`config.yaml`)
- Project registry existence and validity
- File permissions and access rights

#### Dependencies
- **Required dependencies**: click, rich, PyYAML
- **Optional dependencies**: discord.py, PyGithub, cryptography, aiofiles, requests
- Version compatibility checks
- Import validation

#### Integration Status
- Discord bot configuration and token
- AI provider configuration (Claude, OpenAI, etc.)
- GitHub integration setup
- External service connectivity

#### File System Health (with `--check-all`)
- Configuration directory read/write access
- Temporary space availability
- Log directory permissions
- Project directories access

#### Performance Metrics (with `--check-all`)
- CPU usage monitoring
- Memory consumption tracking
- Disk I/O performance
- Network connectivity status

### 🌐 Visualizer Health Endpoints

The web visualizer (`tools/visualizer/app.py`) provides HTTP health endpoints:

```bash
# Visualizer health check (port 5000)
curl http://localhost:5000/health

# Prometheus-compatible metrics
curl http://localhost:5000/metrics

# Debug information
curl http://localhost:5000/debug
```

**Visualizer Health Response**:
```json
{
  "status": "healthy",
  "timestamp": "2025-01-19T15:30:00Z",
  "connected_clients": 3,
  "active_tdd_cycles": 2
}
```

## ❌ Non-Existent Health Endpoints

**Important**: The following endpoints do NOT exist and should not be referenced in deployment configurations:

### Main Orchestrator Endpoints
- ❌ `http://localhost:8080/health` - Not implemented
- ❌ `http://localhost:8080/health/db` - Not implemented  
- ❌ `http://localhost:8080/health/discord` - Not implemented
- ❌ `http://localhost:8080/metrics` - Not implemented
- ❌ `http://localhost:8080/api/*` - No REST API implemented

### Database Health Endpoints
- ❌ `/health/db` - No database health endpoints
- ❌ `/health/storage` - Not implemented

**Use Instead**: CLI command `agent-orch health --check-all` which validates configuration files and dependencies.

## 🔧 Deployment Health Checks

For production deployments, use these approaches instead of HTTP health endpoints:

### Kubernetes Health Checks
```yaml
# Use CLI command instead of HTTP endpoint
readinessProbe:
  exec:
    command:
    - agent-orch
    - health
    - --check-all
  initialDelaySeconds: 30
  periodSeconds: 30

livenessProbe:
  exec:
    command:
    - python
    - -c
    - "import os; exit(0 if os.path.exists('.orch-state') else 1)"
  initialDelaySeconds: 60
  periodSeconds: 60
```

### Docker Health Checks
```dockerfile
# Add to Dockerfile
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
  CMD agent-orch health --check-all || exit 1
```

### Load Balancer Health Checks
```bash
# HAProxy configuration - use TCP check instead of HTTP
backend agent_workflow_backend
    balance roundrobin
    option tcp-check
    
    # Check if orchestrator process is running
    server orchestrator-1 orchestrator-1:22 check
```

### Monitoring Scripts
```bash
#!/bin/bash
# health-monitor.sh - Custom health monitoring script

# Check CLI health command
if agent-orch health --check-all >/dev/null 2>&1; then
    echo "✅ System healthy"
    exit 0
else
    echo "❌ System unhealthy"
    # Send alert to monitoring system
    curl -X POST "$ALERT_WEBHOOK_URL" -d '{"status": "unhealthy", "timestamp": "'$(date -Iseconds)'"}'
    exit 1
fi
```

## 📈 Health Monitoring Best Practices

### Daily Health Checks
```bash
# Add to cron or monitoring system
0 9 * * * /usr/local/bin/agent-orch health --check-all --export-report /var/log/agent-workflow/health-$(date +\%Y\%m\%d).json
```

### Integration with Monitoring Systems

#### Prometheus Integration
```yaml
# prometheus.yml
scrape_configs:
  - job_name: 'agent-workflow-visualizer'
    static_configs:
      - targets: ['localhost:5000']
    metrics_path: '/metrics'
    scrape_interval: 30s
```

#### Grafana Dashboard
```json
{
  "dashboard": {
    "title": "Agent Workflow Health",
    "panels": [
      {
        "title": "System Health Status",
        "type": "stat",
        "targets": [
          {
            "expr": "up{job=\"agent-workflow-visualizer\"}",
            "legendFormat": "Visualizer Status"
          }
        ]
      }
    ]
  }
}
```

### Health Check Automation
```python
# health_check_automation.py
import subprocess
import json
import logging
from datetime import datetime

def automated_health_check():
    """Automated health check with logging and alerting"""
    try:
        result = subprocess.run(
            ['agent-orch', 'health', '--check-all', '--export-report', '/tmp/health.json'],
            capture_output=True, text=True, timeout=60
        )
        
        if result.returncode == 0:
            logging.info("✅ Health check passed")
            return True
        else:
            logging.error(f"❌ Health check failed: {result.stderr}")
            # Send alert to monitoring system
            send_alert("health_check_failed", result.stderr)
            return False
            
    except subprocess.TimeoutExpired:
        logging.error("❌ Health check timed out")
        send_alert("health_check_timeout", "Health check exceeded 60 seconds")
        return False
    except Exception as e:
        logging.error(f"❌ Health check error: {e}")
        send_alert("health_check_error", str(e))
        return False

def send_alert(alert_type: str, message: str):
    """Send alert to monitoring system"""
    # Implementation depends on your monitoring system
    pass

if __name__ == "__main__":
    automated_health_check()
```

## 🚨 Troubleshooting Health Issues

### Common Health Check Failures

#### "Command not found: agent-orch"
```bash
# Verify installation
pip list | grep agent-workflow

# Reinstall if needed
pip install --upgrade agent-workflow

# Check PATH
which agent-orch
```

#### "Configuration directory not found"
```bash
# Initialize configuration
agent-orch init --interactive

# Manually create directory
mkdir -p ~/.agent-workflow
```

#### "Dependencies missing"
```bash
# Install missing dependencies
pip install discord.py PyGithub PyYAML

# Full dependency install
pip install -r requirements.txt
```

#### "Integration not configured"
```bash
# Set up Discord integration
agent-orch setup-discord --interactive

# Set up AI provider
agent-orch setup-api --interactive
```

## 📝 Health Check Output Examples

### Successful Health Check
```
✅ Overall health: GOOD

System Health: PASS
Configuration Health: PASS  
Dependencies Health: PASS
Integrations Health: PASS
```

### Failed Health Check
```
❌ Overall health: ISSUES DETECTED

System Health: PASS
Configuration Health: FAIL
  ❌ config_file_valid
  ❌ registry_exists
Dependencies Health: FAIL
  ❌ required_discord.py
Integrations Health: PASS
```

## 🔮 Future Health Monitoring Features

**Planned Enhancements** (not currently implemented):

- HTTP health endpoints for main orchestrator
- Database connection health checks
- Real-time health dashboard
- Advanced performance monitoring
- Automated remediation capabilities
- Integration with popular monitoring tools (Datadog, New Relic)

**Current Status**: All health monitoring is CLI-based with visualizer web endpoints for real-time metrics.