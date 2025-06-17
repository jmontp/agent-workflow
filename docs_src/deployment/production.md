# Production Deployment

Guide for deploying the AI Agent TDD-Scrum workflow system to production environments.

## Overview

This guide covers production deployment strategies for running the orchestrator reliably in various environments, from small teams to enterprise scale.

## Deployment Options

### Option 1: Self-Hosted Server

Best for: Small to medium teams with dedicated infrastructure.

**Requirements:**
- Linux server (Ubuntu 20.04+ or CentOS 8+)
- Python 3.8+ 
- 4GB RAM minimum, 8GB recommended
- 20GB disk space minimum
- Stable internet connection

**Setup:**
```bash
# Create dedicated user
sudo useradd -m -s /bin/bash agent-workflow
sudo su - agent-workflow

# Clone and setup
git clone https://github.com/jmontp/agent-workflow.git
cd agent-workflow
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Option 2: Docker Deployment

Best for: Containerized environments and easier scaling.

**Dockerfile:**
```dockerfile
FROM python:3.9-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create non-root user
RUN useradd -m -u 1001 agent-workflow
USER agent-workflow

# Expose port for health checks
EXPOSE 8080

CMD ["python", "scripts/orchestrator.py"]
```

**Docker Compose:**
```yaml
version: '3.8'

services:
  orchestrator:
    build: .
    environment:
      - DISCORD_BOT_TOKEN=${DISCORD_BOT_TOKEN}
      - ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}
      - ENVIRONMENT=production
    volumes:
      - ./config:/app/config
      - ./logs:/app/logs
      - ./projects:/app/projects
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "python", "scripts/health-check.py"]
      interval: 30s
      timeout: 10s
      retries: 3

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./ssl:/etc/ssl
    depends_on:
      - orchestrator
    restart: unless-stopped
```

### Option 3: Cloud Deployment

#### AWS Deployment

**EC2 Instance:**
```bash
# Launch EC2 instance (t3.medium recommended)
# Install Docker and Docker Compose
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh
sudo usermod -aG docker ubuntu

# Deploy with docker-compose
git clone https://github.com/jmontp/agent-workflow.git
cd agent-workflow
cp .env.example .env
# Edit .env with production values
docker-compose up -d
```

**ECS Deployment:**
```json
{
  "family": "agent-workflow",
  "taskRoleArn": "arn:aws:iam::ACCOUNT:role/agent-workflow-task-role",
  "executionRoleArn": "arn:aws:iam::ACCOUNT:role/agent-workflow-execution-role",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "1024",
  "memory": "2048",
  "containerDefinitions": [
    {
      "name": "orchestrator",
      "image": "your-registry/agent-workflow:latest",
      "essential": true,
      "environment": [
        {"name": "ENVIRONMENT", "value": "production"}
      ],
      "secrets": [
        {
          "name": "DISCORD_BOT_TOKEN",
          "valueFrom": "arn:aws:secretsmanager:region:account:secret:discord-token"
        }
      ]
    }
  ]
}
```

#### Google Cloud Platform

**Cloud Run Deployment:**
```yaml
# cloudbuild.yaml
steps:
  - name: 'gcr.io/cloud-builders/docker'
    args: ['build', '-t', 'gcr.io/$PROJECT_ID/agent-workflow:$COMMIT_SHA', '.']
  - name: 'gcr.io/cloud-builders/docker'
    args: ['push', 'gcr.io/$PROJECT_ID/agent-workflow:$COMMIT_SHA']
  - name: 'gcr.io/google.com/cloudsdktool/cloud-sdk'
    entrypoint: 'gcloud'
    args:
      - 'run'
      - 'deploy'
      - 'agent-workflow'
      - '--image=gcr.io/$PROJECT_ID/agent-workflow:$COMMIT_SHA'
      - '--region=us-central1'
      - '--platform=managed'
      - '--memory=2Gi'
      - '--cpu=1'
```

## Configuration Management

### Environment Variables

**Production Environment Variables:**
```bash
# Core Configuration
ENVIRONMENT=production
DISCORD_BOT_TOKEN=your_production_token
LOG_LEVEL=INFO

# AI Integration
ANTHROPIC_API_KEY=your_anthropic_key
OPENAI_API_KEY=your_openai_key  # If using OpenAI

# Database (if using external storage)
DATABASE_URL=postgresql://user:pass@host:5432/dbname

# Monitoring
SENTRY_DSN=your_sentry_dsn
DATADOG_API_KEY=your_datadog_key

# Security
JWT_SECRET=your_jwt_secret
ENCRYPTION_KEY=your_encryption_key
```

### Configuration Files

**Production config.yml:**
```yaml
orchestrator:
  mode: blocking
  max_concurrent_projects: 10
  state_save_interval: 30
  backup_interval: 3600

discord:
  command_timeout: 300
  max_commands_per_minute: 60
  error_channel_id: "123456789"

agents:
  timeout_minutes: 45
  max_retries: 5
  claude_model: "claude-3-sonnet"

logging:
  level: INFO
  format: json
  rotation: daily
  retention_days: 30

monitoring:
  health_check_interval: 60
  metrics_collection: true
  alert_thresholds:
    error_rate: 0.05
    response_time: 30
```

## Process Management

### Systemd Service (Linux)

**`/etc/systemd/system/agent-workflow.service`:**
```ini
[Unit]
Description=AI Agent Workflow Orchestrator
After=network.target
Wants=network.target

[Service]
Type=simple
User=agent-workflow
Group=agent-workflow
WorkingDirectory=/home/agent-workflow/agent-workflow
Environment=PATH=/home/agent-workflow/agent-workflow/venv/bin
ExecStart=/home/agent-workflow/agent-workflow/venv/bin/python scripts/orchestrator.py
ExecReload=/bin/kill -HUP $MAINPID
Restart=always
RestartSec=10

# Environment variables
EnvironmentFile=/home/agent-workflow/.env

# Security
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ProtectHome=true
ReadWritePaths=/home/agent-workflow/agent-workflow/logs
ReadWritePaths=/home/agent-workflow/agent-workflow/projects

[Install]
WantedBy=multi-user.target
```

**Service Management:**
```bash
# Enable and start service
sudo systemctl enable agent-workflow
sudo systemctl start agent-workflow

# Check status
sudo systemctl status agent-workflow

# View logs
sudo journalctl -u agent-workflow -f
```

### Supervisor (Alternative)

**`/etc/supervisor/conf.d/agent-workflow.conf`:**
```ini
[program:agent-workflow]
command=/home/agent-workflow/agent-workflow/venv/bin/python scripts/orchestrator.py
directory=/home/agent-workflow/agent-workflow
user=agent-workflow
autostart=true
autorestart=true
stderr_logfile=/var/log/agent-workflow/error.log
stdout_logfile=/var/log/agent-workflow/output.log
environment=DISCORD_BOT_TOKEN="your_token"
```

## Security

### SSL/TLS Configuration

**Nginx SSL Configuration:**
```nginx
server {
    listen 443 ssl http2;
    server_name workflow.yourdomain.com;

    ssl_certificate /etc/ssl/certs/workflow.crt;
    ssl_certificate_key /etc/ssl/private/workflow.key;
    
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE+AESGCM:ECDHE+CHACHA20:DHE+AESGCM:DHE+CHACHA20:!aNULL:!MD5:!DSS;
    ssl_prefer_server_ciphers off;
    
    location /health {
        proxy_pass http://127.0.0.1:8080/health;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

### Secret Management

**Using HashiCorp Vault:**
```python
import hvac

# vault_client.py
class VaultClient:
    def __init__(self, vault_url, vault_token):
        self.client = hvac.Client(url=vault_url, token=vault_token)
    
    def get_secret(self, path):
        response = self.client.secrets.kv.v2.read_secret_version(path=path)
        return response['data']['data']

# Usage in orchestrator
vault = VaultClient(os.environ['VAULT_URL'], os.environ['VAULT_TOKEN'])
discord_token = vault.get_secret('agent-workflow/discord')['token']
```

**Using AWS Secrets Manager:**
```python
import boto3

def get_secret(secret_name, region='us-east-1'):
    session = boto3.session.Session()
    client = session.client('secretsmanager', region_name=region)
    response = client.get_secret_value(SecretId=secret_name)
    return json.loads(response['SecretString'])
```

### Firewall Configuration

**UFW (Ubuntu):**
```bash
# Basic firewall setup
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow ssh
sudo ufw allow 80
sudo ufw allow 443
sudo ufw enable
```

**Security Groups (AWS):**
```json
{
  "GroupName": "agent-workflow-sg",
  "Description": "Security group for Agent Workflow",
  "IpPermissions": [
    {
      "IpProtocol": "tcp",
      "FromPort": 22,
      "ToPort": 22,
      "IpRanges": [{"CidrIp": "your.office.ip/32"}]
    },
    {
      "IpProtocol": "tcp", 
      "FromPort": 443,
      "ToPort": 443,
      "IpRanges": [{"CidrIp": "0.0.0.0/0"}]
    }
  ]
}
```

## Monitoring

### Health Checks

**Health Check Script:**
```python
#!/usr/bin/env python3
# scripts/health-check.py

import asyncio
import sys
from lib.orchestrator import Orchestrator

async def health_check():
    try:
        orchestrator = Orchestrator()
        state = await orchestrator.get_state()
        
        # Check if orchestrator is responsive
        if state is None:
            return False
            
        # Check Discord connection
        if not orchestrator.discord_bot.is_ready():
            return False
            
        return True
    except Exception as e:
        print(f"Health check failed: {e}")
        return False

if __name__ == "__main__":
    healthy = asyncio.run(health_check())
    sys.exit(0 if healthy else 1)
```

### Logging

**Structured Logging Configuration:**
```python
import logging
import json
from datetime import datetime

class JSONFormatter(logging.Formatter):
    def format(self, record):
        log_entry = {
            'timestamp': datetime.utcnow().isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno
        }
        
        if record.exc_info:
            log_entry['exception'] = self.formatException(record.exc_info)
            
        return json.dumps(log_entry)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(message)s',
    handlers=[
        logging.FileHandler('/var/log/agent-workflow/app.log'),
        logging.StreamHandler()
    ]
)

for handler in logging.root.handlers:
    handler.setFormatter(JSONFormatter())
```

### Metrics Collection

**Prometheus Metrics:**
```python
from prometheus_client import Counter, Histogram, Gauge, start_http_server

# Define metrics
commands_total = Counter('discord_commands_total', 'Total Discord commands processed', ['command', 'status'])
agent_execution_duration = Histogram('agent_execution_seconds', 'Agent task execution time', ['agent_type'])
active_sprints = Gauge('active_sprints_total', 'Number of active sprints')

# Usage in code
commands_total.labels(command='epic', status='success').inc()
agent_execution_duration.labels(agent_type='CodeAgent').observe(task_duration)
active_sprints.set(len(active_sprint_list))

# Start metrics server
start_http_server(8000)
```

## Backup and Recovery

### Data Backup

**Backup Script:**
```bash
#!/bin/bash
# scripts/backup.sh

BACKUP_DIR="/backup/agent-workflow"
DATE=$(date +%Y%m%d_%H%M%S)
PROJECT_DIR="/home/agent-workflow/agent-workflow"

# Create backup directory
mkdir -p $BACKUP_DIR/$DATE

# Backup configuration
cp -r $PROJECT_DIR/config $BACKUP_DIR/$DATE/

# Backup project data
cp -r $PROJECT_DIR/projects $BACKUP_DIR/$DATE/

# Backup logs (last 7 days)
find $PROJECT_DIR/logs -mtime -7 -type f -exec cp {} $BACKUP_DIR/$DATE/logs/ \;

# Compress backup
tar -czf $BACKUP_DIR/agent-workflow-$DATE.tar.gz -C $BACKUP_DIR $DATE
rm -rf $BACKUP_DIR/$DATE

# Clean old backups (keep 30 days)
find $BACKUP_DIR -name "*.tar.gz" -mtime +30 -delete

echo "Backup completed: agent-workflow-$DATE.tar.gz"
```

### Database Backup (if using external DB)

**PostgreSQL Backup:**
```bash
#!/bin/bash
# Automated database backup
pg_dump -h localhost -U agent_workflow -d agent_workflow_prod > backup_$(date +%Y%m%d_%H%M%S).sql

# Upload to S3
aws s3 cp backup_*.sql s3://your-backup-bucket/database/
```

## Scaling

### Horizontal Scaling

**Multiple Orchestrator Instances:**
```python
# Load balancer configuration for multiple instances
# Use Redis for shared state management

import redis
import json

class SharedStateManager:
    def __init__(self, redis_url):
        self.redis = redis.from_url(redis_url)
    
    def save_state(self, project_id, state):
        self.redis.set(f"project:{project_id}:state", json.dumps(state))
    
    def load_state(self, project_id):
        data = self.redis.get(f"project:{project_id}:state")
        return json.loads(data) if data else None
```

### Resource Optimization

**Memory and CPU Optimization:**
```python
# Optimize agent execution
import asyncio
from concurrent.futures import ThreadPoolExecutor

class OptimizedOrchestrator:
    def __init__(self, max_workers=4):
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        self.semaphore = asyncio.Semaphore(max_workers)
    
    async def execute_agent_task(self, agent, task):
        async with self.semaphore:
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(
                self.executor, 
                agent.run, 
                task
            )
```

## Troubleshooting

### Common Production Issues

**High Memory Usage:**
```bash
# Monitor memory usage
ps aux | grep python | head -10
free -h

# Tune Python garbage collection
export PYTHONGC=1  # Enable garbage collection debug
```

**Discord Rate Limiting:**
```python
# Implement exponential backoff
import asyncio
from discord.errors import HTTPException

async def send_with_retry(channel, message, max_retries=3):
    for attempt in range(max_retries):
        try:
            return await channel.send(message)
        except HTTPException as e:
            if e.status == 429:  # Rate limited
                retry_after = e.response.headers.get('Retry-After', 1)
                await asyncio.sleep(float(retry_after))
            else:
                raise
    raise Exception("Max retries exceeded")
```

### Log Analysis

**Common Log Patterns:**
```bash
# Find errors in last hour
grep -i error /var/log/agent-workflow/app.log | tail -100

# Monitor agent failures
grep "AgentExecutionError" /var/log/agent-workflow/app.log

# Check Discord connection issues
grep "discord" /var/log/agent-workflow/app.log | grep -i "error\|timeout"
```

Your production deployment is now ready for reliable, scalable operation!