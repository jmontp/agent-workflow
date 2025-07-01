# Multi-Project Visualizer Deployment Guide

## Overview

This guide covers the complete deployment process for the Multi-Project Visualizer, from development to production environments. It includes security considerations, monitoring procedures, and operational guidelines.

## Table of Contents

1. [Deployment Architecture](#deployment-architecture)
2. [Environment Configuration](#environment-configuration)
3. [Production Deployment](#production-deployment)
4. [Security Configuration](#security-configuration)
5. [Monitoring and Health Checks](#monitoring-and-health-checks)
6. [Scaling and Performance](#scaling-and-performance)
7. [Backup and Recovery](#backup-and-recovery)
8. [Troubleshooting](#troubleshooting)
9. [Maintenance Procedures](#maintenance-procedures)

## Deployment Architecture

### System Components

```mermaid
graph TB
    subgraph "Load Balancer Layer"
        LB[Load Balancer<br/>nginx/HAProxy]
    end
    
    subgraph "Application Layer"
        APP1[Visualizer Instance 1<br/>Flask + SocketIO]
        APP2[Visualizer Instance 2<br/>Flask + SocketIO]
        APP3[Visualizer Instance N<br/>Flask + SocketIO]
    end
    
    subgraph "Orchestration Layer"
        ORCH1[Orchestrator 1<br/>Project A, B]
        ORCH2[Orchestrator 2<br/>Project C, D]
        ORCH3[Orchestrator N<br/>Project X, Y]
    end
    
    subgraph "Data Layer"
        REDIS[Redis<br/>Session Store<br/>WebSocket Scaling]
        FS[Shared Storage<br/>Project Files<br/>Configuration]
    end
    
    subgraph "Monitoring"
        PROM[Prometheus<br/>Metrics Collection]
        GRAF[Grafana<br/>Dashboards]
        LOG[Centralized Logging<br/>ELK Stack]
    end
    
    LB --> APP1
    LB --> APP2
    LB --> APP3
    
    APP1 --> ORCH1
    APP1 --> ORCH2
    APP2 --> ORCH2
    APP2 --> ORCH3
    APP3 --> ORCH1
    APP3 --> ORCH3
    
    APP1 --> REDIS
    APP2 --> REDIS
    APP3 --> REDIS
    
    APP1 --> FS
    APP2 --> FS
    APP3 --> FS
    
    APP1 --> PROM
    APP2 --> PROM
    APP3 --> PROM
    
    PROM --> GRAF
    APP1 --> LOG
    APP2 --> LOG
    APP3 --> LOG
```

### Deployment Models

#### Single-Node Development
- All components on one server
- Suitable for development and small teams
- Minimal resource requirements

#### Multi-Node Production
- Load-balanced application instances
- Shared Redis for session management
- Centralized monitoring and logging
- High availability and scalability

#### Container-Based Deployment
- Docker containers for easy deployment
- Kubernetes orchestration for scaling
- Service mesh for inter-service communication

## Environment Configuration

### Development Environment

#### Prerequisites
```bash
# System requirements
- Python 3.8+
- Node.js 16+ (for frontend assets)
- Redis 6+ (optional, for multi-instance)
- Git 2.0+

# Python dependencies
pip install agent-workflow[web]

# Or from source
git clone https://github.com/jmontp/agent-workflow.git
cd agent-workflow
pip install -e .[web,dev]
```

#### Configuration Files

**development.env**:
```bash
# Flask configuration
FLASK_ENV=development
FLASK_DEBUG=true
SECRET_KEY=dev-secret-key-change-in-production

# Server configuration
HOST=localhost
PORT=5000
WORKERS=1

# Redis configuration (optional)
REDIS_URL=redis://localhost:6379/0

# Logging
LOG_LEVEL=DEBUG
LOG_FORMAT=detailed
```

**orch-config-dev.yaml**:
```yaml
projects:
  test-project:
    path: "/path/to/test-project"
    status: "active"
    priority: "normal"
    description: "Development test project"
    
global_settings:
  max_parallel_projects: 3
  resource_limits:
    max_memory_mb: 512
    max_disk_mb: 1024
  
web_interface:
  host: "localhost"
  port: 5000
  debug: true
  auto_reload: true
```

#### Starting Development Server

```bash
# Using CLI
aw web --debug --port 5000 --host localhost

# Or using Python directly
cd tools/visualizer
python app.py --debug

# With auto-reload
FLASK_ENV=development python app.py
```

### Staging Environment

#### Configuration

**staging.env**:
```bash
# Flask configuration
FLASK_ENV=production
FLASK_DEBUG=false
SECRET_KEY=staging-secret-key-randomly-generated

# Server configuration
HOST=0.0.0.0
PORT=5000
WORKERS=2

# Redis configuration
REDIS_URL=redis://staging-redis:6379/0

# Security
FORCE_HTTPS=true
SESSION_COOKIE_SECURE=true
SESSION_COOKIE_HTTPONLY=true

# Logging
LOG_LEVEL=INFO
LOG_FORMAT=json
SENTRY_DSN=https://your-sentry-dsn
```

**orch-config-staging.yaml**:
```yaml
projects:
  staging-project-1:
    path: "/var/projects/staging-project-1"
    status: "active"
    priority: "high"
    description: "Staging environment project 1"
    
  staging-project-2:
    path: "/var/projects/staging-project-2"
    status: "active"
    priority: "normal"
    description: "Staging environment project 2"

global_settings:
  max_parallel_projects: 5
  resource_limits:
    max_memory_mb: 2048
    max_disk_mb: 4096
  
web_interface:
  host: "0.0.0.0"
  port: 5000
  debug: false
  workers: 2
  
security:
  allowed_origins:
    - "https://staging.yourcompany.com"
  csrf_protection: true
  rate_limiting: true
```

### Production Environment

#### System Requirements

**Hardware Specifications**:
- **CPU**: 4+ cores (8+ recommended for high load)
- **RAM**: 8GB minimum (16GB+ recommended)
- **Storage**: 100GB+ SSD (depends on project count and history)
- **Network**: Gigabit Ethernet

**Operating System**:
- Ubuntu 20.04 LTS or later
- CentOS 8+ / RHEL 8+
- Alpine Linux (for containers)

#### Production Configuration

**production.env**:
```bash
# Flask configuration
FLASK_ENV=production
FLASK_DEBUG=false
SECRET_KEY=production-secret-key-use-strong-random-key

# Server configuration
HOST=0.0.0.0
PORT=5000
WORKERS=4

# Redis configuration
REDIS_URL=redis://prod-redis-cluster:6379/0
REDIS_CLUSTER=true

# Database (if using persistent storage)
DATABASE_URL=postgresql://user:pass@prod-db:5432/visualizer

# Security
FORCE_HTTPS=true
SESSION_COOKIE_SECURE=true
SESSION_COOKIE_HTTPONLY=true
SESSION_COOKIE_SAMESITE=Strict
CSRF_PROTECTION=true

# Logging
LOG_LEVEL=INFO
LOG_FORMAT=json
LOG_FILE=/var/log/visualizer/app.log
SENTRY_DSN=https://your-production-sentry-dsn

# Monitoring
PROMETHEUS_METRICS=true
HEALTH_CHECK_ENDPOINT=true

# Performance
STATIC_FILE_CACHE=3600
GZIP_COMPRESSION=true
```

## Production Deployment

### Docker Deployment

#### Dockerfile

```dockerfile
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Install the package
RUN pip install -e .[web]

# Create non-root user
RUN useradd --create-home --shell /bin/bash visualizer
RUN chown -R visualizer:visualizer /app
USER visualizer

# Expose port
EXPOSE 5000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:5000/health || exit 1

# Start command
CMD ["gunicorn", "--config", "gunicorn.conf.py", "tools.visualizer.app:app"]
```

#### docker-compose.yml

```yaml
version: '3.8'

services:
  visualizer:
    build: .
    ports:
      - "5000:5000"
    environment:
      - FLASK_ENV=production
      - REDIS_URL=redis://redis:6379/0
    volumes:
      - ./projects:/var/projects:ro
      - ./logs:/var/log/visualizer
    depends_on:
      - redis
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:5000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
    deploy:
      replicas: 2
      resources:
        limits:
          memory: 1G
          cpus: '1.0'
        reservations:
          memory: 512M
          cpus: '0.5'

  redis:
    image: redis:7-alpine
    volumes:
      - redis_data:/data
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 30s
      timeout: 10s
      retries: 3

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
      - ./ssl:/etc/nginx/ssl:ro
    depends_on:
      - visualizer
    restart: unless-stopped

volumes:
  redis_data:
```

#### gunicorn.conf.py

```python
import os

# Server socket
bind = f"0.0.0.0:{os.getenv('PORT', 5000)}"
backlog = 2048

# Worker processes
workers = int(os.getenv('WORKERS', 4))
worker_class = "eventlet"
worker_connections = 1000
max_requests = 1000
max_requests_jitter = 50
preload_app = True
timeout = 120
keepalive = 2

# Logging
loglevel = os.getenv('LOG_LEVEL', 'info').lower()
accesslog = '/var/log/visualizer/access.log'
errorlog = '/var/log/visualizer/error.log'
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)s'

# Process naming
proc_name = 'visualizer'

# Security
limit_request_line = 4094
limit_request_fields = 100
limit_request_field_size = 8190

# Performance
preload_app = True
max_requests = 1000
max_requests_jitter = 50

def when_ready(server):
    server.log.info("Visualizer server is ready. Listening on: %s", server.address)

def worker_int(worker):
    worker.log.info("worker received INT or QUIT signal")

def pre_fork(server, worker):
    server.log.info("Worker spawned (pid: %s)", worker.pid)

def post_fork(server, worker):
    server.log.info("Worker spawned (pid: %s)", worker.pid)
```

### Kubernetes Deployment

#### visualizer-deployment.yaml

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: visualizer
  labels:
    app: visualizer
spec:
  replicas: 3
  selector:
    matchLabels:
      app: visualizer
  template:
    metadata:
      labels:
        app: visualizer
    spec:
      containers:
      - name: visualizer
        image: your-registry/visualizer:latest
        ports:
        - containerPort: 5000
        env:
        - name: FLASK_ENV
          value: "production"
        - name: REDIS_URL
          valueFrom:
            secretKeyRef:
              name: visualizer-secrets
              key: redis-url
        - name: SECRET_KEY
          valueFrom:
            secretKeyRef:
              name: visualizer-secrets
              key: secret-key
        volumeMounts:
        - name: projects
          mountPath: /var/projects
          readOnly: true
        - name: config
          mountPath: /app/config
        resources:
          requests:
            memory: "512Mi"
            cpu: "500m"
          limits:
            memory: "1Gi"
            cpu: "1000m"
        livenessProbe:
          httpGet:
            path: /health
            port: 5000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /ready
            port: 5000
          initialDelaySeconds: 5
          periodSeconds: 5
      volumes:
      - name: projects
        persistentVolumeClaim:
          claimName: projects-pvc
      - name: config
        configMap:
          name: visualizer-config
---
apiVersion: v1
kind: Service
metadata:
  name: visualizer-service
spec:
  selector:
    app: visualizer
  ports:
  - protocol: TCP
    port: 80
    targetPort: 5000
  type: ClusterIP
---
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: visualizer-ingress
  annotations:
    kubernetes.io/ingress.class: nginx
    cert-manager.io/cluster-issuer: letsencrypt-prod
    nginx.ingress.kubernetes.io/websocket-services: visualizer-service
    nginx.ingress.kubernetes.io/proxy-read-timeout: "3600"
    nginx.ingress.kubernetes.io/proxy-send-timeout: "3600"
spec:
  tls:
  - hosts:
    - visualizer.yourcompany.com
    secretName: visualizer-tls
  rules:
  - host: visualizer.yourcompany.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: visualizer-service
            port:
              number: 80
```

### Traditional Server Deployment

#### System Setup

```bash
#!/bin/bash
# production-setup.sh

# Update system
sudo apt update && sudo apt upgrade -y

# Install dependencies
sudo apt install -y python3.11 python3.11-venv python3-pip nginx redis-server git curl

# Create application user
sudo useradd --system --shell /bin/bash --home /opt/visualizer visualizer
sudo mkdir -p /opt/visualizer
sudo chown visualizer:visualizer /opt/visualizer

# Switch to app user
sudo -u visualizer bash << 'EOF'
cd /opt/visualizer

# Create virtual environment
python3.11 -m venv venv
source venv/bin/activate

# Install application
pip install agent-workflow[web]

# Create directories
mkdir -p logs config projects
EOF

# Setup systemd service
sudo tee /etc/systemd/system/visualizer.service > /dev/null << 'EOF'
[Unit]
Description=Multi-Project Visualizer
After=network.target redis.service

[Service]
Type=exec
User=visualizer
Group=visualizer
WorkingDirectory=/opt/visualizer
Environment=PATH=/opt/visualizer/venv/bin
ExecStart=/opt/visualizer/venv/bin/gunicorn --config /opt/visualizer/gunicorn.conf.py tools.visualizer.app:app
ExecReload=/bin/kill -s HUP $MAINPID
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Enable and start service
sudo systemctl daemon-reload
sudo systemctl enable visualizer
sudo systemctl start visualizer
```

#### Nginx Configuration

```nginx
# /etc/nginx/sites-available/visualizer
upstream visualizer {
    server 127.0.0.1:5000;
    # Add additional servers for load balancing
    # server 127.0.0.1:5001;
    # server 127.0.0.1:5002;
}

server {
    listen 80;
    server_name visualizer.yourcompany.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name visualizer.yourcompany.com;

    # SSL configuration
    ssl_certificate /etc/ssl/certs/visualizer.crt;
    ssl_certificate_key /etc/ssl/private/visualizer.key;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512:ECDHE-RSA-AES256-GCM-SHA384:DHE-RSA-AES256-GCM-SHA384;
    ssl_prefer_server_ciphers off;

    # Security headers
    add_header X-Frame-Options DENY;
    add_header X-Content-Type-Options nosniff;
    add_header X-XSS-Protection "1; mode=block";
    add_header Strict-Transport-Security "max-age=63072000; includeSubDomains; preload";

    # Gzip compression
    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_types text/plain text/css text/xml text/javascript application/javascript application/xml+rss application/json;

    # Static files
    location /static/ {
        alias /opt/visualizer/static/;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }

    # WebSocket support
    location /socket.io/ {
        proxy_pass http://visualizer;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 86400;
        proxy_send_timeout 86400;
    }

    # Main application
    location / {
        proxy_pass http://visualizer;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 300;
        proxy_send_timeout 300;
    }

    # Health check endpoint
    location /health {
        proxy_pass http://visualizer;
        access_log off;
    }
}
```

## Security Configuration

### SSL/TLS Setup

#### Let's Encrypt with Certbot

```bash
# Install certbot
sudo apt install certbot python3-certbot-nginx

# Generate certificate
sudo certbot --nginx -d visualizer.yourcompany.com

# Verify auto-renewal
sudo systemctl status certbot.timer
sudo certbot renew --dry-run
```

#### Custom SSL Certificate

```bash
# Generate private key
sudo openssl genrsa -out /etc/ssl/private/visualizer.key 4096

# Generate certificate signing request
sudo openssl req -new -key /etc/ssl/private/visualizer.key -out /tmp/visualizer.csr

# After getting certificate from CA, install it
sudo cp visualizer.crt /etc/ssl/certs/
sudo chmod 644 /etc/ssl/certs/visualizer.crt
sudo chmod 600 /etc/ssl/private/visualizer.key
```

### Firewall Configuration

```bash
# UFW (Ubuntu)
sudo ufw allow ssh
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw --force enable

# iptables (CentOS/RHEL)
sudo firewall-cmd --permanent --add-service=http
sudo firewall-cmd --permanent --add-service=https
sudo firewall-cmd --permanent --add-service=ssh
sudo firewall-cmd --reload
```

### Application Security

#### Environment Variables

```bash
# Generate secure secret key
python3 -c "import secrets; print(secrets.token_urlsafe(32))"

# Set in production environment
export SECRET_KEY="your-generated-secret-key"
export SESSION_COOKIE_SECURE=true
export SESSION_COOKIE_HTTPONLY=true
export FORCE_HTTPS=true
```

#### Rate Limiting Configuration

```python
# In app.py or config
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

limiter = Limiter(
    app,
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"],
    storage_uri="redis://localhost:6379"
)

# Apply to specific endpoints
@app.route('/api/v1/projects')
@limiter.limit("10 per minute")
def get_projects():
    # ...
```

#### CORS Configuration

```python
from flask_cors import CORS

# Production CORS settings
CORS(app, 
     origins=['https://visualizer.yourcompany.com'],
     supports_credentials=True,
     methods=['GET', 'POST', 'PUT', 'DELETE'],
     allow_headers=['Content-Type', 'Authorization'])
```

### User Authentication

#### Integration with Corporate SSO

```python
from flask_oidc import OpenIDConnect

app.config.update({
    'OIDC_CLIENT_SECRETS': '/opt/visualizer/config/client_secrets.json',
    'OIDC_ID_TOKEN_COOKIE_SECURE': True,
    'OIDC_REQUIRE_VERIFIED_EMAIL': True,
})

oidc = OpenIDConnect(app)

@app.route('/login')
@oidc.require_login
def login():
    return redirect(url_for('index'))

@app.route('/logout')
def logout():
    oidc.logout()
    return redirect(url_for('index'))
```

## Monitoring and Health Checks

### Health Check Endpoints

```python
@app.route('/health')
def health_check():
    """Simple health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.utcnow().isoformat(),
        'version': app.config.get('VERSION', 'unknown')
    })

@app.route('/ready')
def readiness_check():
    """Readiness check with dependency validation"""
    checks = {
        'redis': check_redis_connection(),
        'projects': check_project_access(),
        'orchestrator': check_orchestrator_connection()
    }
    
    all_healthy = all(checks.values())
    status_code = 200 if all_healthy else 503
    
    return jsonify({
        'status': 'ready' if all_healthy else 'not ready',
        'checks': checks,
        'timestamp': datetime.utcnow().isoformat()
    }), status_code

@app.route('/metrics')
def metrics():
    """Prometheus metrics endpoint"""
    if not app.config.get('PROMETHEUS_METRICS'):
        abort(404)
    
    from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
    return Response(generate_latest(), mimetype=CONTENT_TYPE_LATEST)
```

### Prometheus Metrics

```python
from prometheus_client import Counter, Histogram, Gauge

# Define metrics
REQUEST_COUNT = Counter('http_requests_total', 'Total HTTP requests', ['method', 'endpoint', 'status'])
REQUEST_DURATION = Histogram('http_request_duration_seconds', 'HTTP request duration')
ACTIVE_CONNECTIONS = Gauge('websocket_connections_active', 'Active WebSocket connections')
PROJECT_COUNT = Gauge('projects_total', 'Total number of projects')

# Instrument application
@app.before_request
def before_request():
    request.start_time = time.time()

@app.after_request
def after_request(response):
    duration = time.time() - request.start_time
    REQUEST_DURATION.observe(duration)
    REQUEST_COUNT.labels(
        method=request.method,
        endpoint=request.endpoint or 'unknown',
        status=response.status_code
    ).inc()
    return response
```

### Centralized Logging

#### Structured Logging Configuration

```python
import structlog
import logging.config

LOGGING_CONFIG = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'json': {
            'format': '%(message)s',
            'class': 'pythonjsonlogger.jsonlogger.JsonFormatter',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'json',
            'stream': 'ext://sys.stdout',
        },
        'file': {
            'class': 'logging.handlers.RotatingFileHandler',
            'formatter': 'json',
            'filename': '/var/log/visualizer/app.log',
            'maxBytes': 10485760,  # 10MB
            'backupCount': 5,
        },
    },
    'loggers': {
        '': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': False,
        },
    }
}

logging.config.dictConfig(LOGGING_CONFIG)
logger = structlog.get_logger()
```

#### ELK Stack Integration

**filebeat.yml**:
```yaml
filebeat.inputs:
- type: log
  enabled: true
  paths:
    - /var/log/visualizer/*.log
  fields:
    service: visualizer
    environment: production
  fields_under_root: true

output.elasticsearch:
  hosts: ["elasticsearch:9200"]
  index: "visualizer-%{+yyyy.MM.dd}"

processors:
- decode_json_fields:
    fields: ["message"]
    target: ""
    overwrite_keys: true
```

### Monitoring Dashboard

#### Grafana Dashboard Configuration

```json
{
  "dashboard": {
    "title": "Visualizer Monitoring",
    "panels": [
      {
        "title": "Request Rate",
        "type": "graph",
        "targets": [
          {
            "expr": "rate(http_requests_total[5m])",
            "legendFormat": "{{method}} {{endpoint}}"
          }
        ]
      },
      {
        "title": "Response Time",
        "type": "graph",
        "targets": [
          {
            "expr": "histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))",
            "legendFormat": "95th percentile"
          }
        ]
      },
      {
        "title": "Active WebSocket Connections",
        "type": "singlestat",
        "targets": [
          {
            "expr": "websocket_connections_active",
            "legendFormat": "Connections"
          }
        ]
      },
      {
        "title": "Error Rate",
        "type": "graph",
        "targets": [
          {
            "expr": "rate(http_requests_total{status=~\"5..\"}[5m])",
            "legendFormat": "5xx errors"
          }
        ]
      }
    ]
  }
}
```

## Scaling and Performance

### Horizontal Scaling

#### Load Balancer Configuration

**HAProxy Configuration**:
```
global
    daemon
    maxconn 4096

defaults
    mode http
    timeout connect 5000ms
    timeout client 50000ms
    timeout server 50000ms

frontend visualizer_frontend
    bind *:80
    bind *:443 ssl crt /etc/ssl/certs/visualizer.pem
    redirect scheme https if !{ ssl_fc }
    default_backend visualizer_backend

backend visualizer_backend
    balance roundrobin
    option httpchk GET /health
    server viz1 10.0.1.10:5000 check
    server viz2 10.0.1.11:5000 check
    server viz3 10.0.1.12:5000 check
```

#### Session Affinity

```python
# Redis session store for sticky sessions
from flask_session import Session
import redis

app.config['SESSION_TYPE'] = 'redis'
app.config['SESSION_REDIS'] = redis.from_url('redis://localhost:6379')
app.config['SESSION_PERMANENT'] = False
app.config['SESSION_USE_SIGNER'] = True
app.config['SESSION_KEY_PREFIX'] = 'visualizer:'

Session(app)
```

### Performance Optimization

#### Caching Strategy

```python
from flask_caching import Cache

cache = Cache(app, config={
    'CACHE_TYPE': 'redis',
    'CACHE_REDIS_URL': 'redis://localhost:6379/1',
    'CACHE_DEFAULT_TIMEOUT': 300
})

@app.route('/api/v1/projects')
@cache.cached(timeout=60, key_prefix='projects_list')
def get_projects():
    # Expensive operation cached for 1 minute
    return get_all_projects()

@cache.memoize(timeout=300)
def get_project_state(project_name):
    # Project state cached for 5 minutes
    return load_project_state(project_name)
```

#### Database Optimization

```python
# Connection pooling
from sqlalchemy.pool import StaticPool

engine = create_engine(
    DATABASE_URL,
    poolclass=StaticPool,
    pool_size=20,
    max_overflow=30,
    pool_pre_ping=True,
    pool_recycle=3600
)
```

#### WebSocket Scaling

```python
# Redis adapter for Socket.IO scaling
import socketio

mgr = socketio.RedisManager('redis://localhost:6379')
sio = socketio.Server(client_manager=mgr)

# Kubernetes scaling with Redis
socketio_app = socketio.WSGIApp(sio, app)
```

### Resource Management

#### CPU and Memory Limits

```yaml
# Kubernetes resource limits
resources:
  requests:
    memory: "512Mi"
    cpu: "500m"
  limits:
    memory: "2Gi"
    cpu: "2000m"
```

#### Auto-scaling Configuration

```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: visualizer-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: visualizer
  minReplicas: 2
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
```

## Backup and Recovery

### Data Backup Strategy

#### Project Data Backup

```bash
#!/bin/bash
# backup-projects.sh

BACKUP_DIR="/var/backups/visualizer"
PROJECT_DIR="/var/projects"
DATE=$(date +%Y%m%d_%H%M%S)

# Create backup directory
mkdir -p "$BACKUP_DIR/$DATE"

# Backup project files
tar -czf "$BACKUP_DIR/$DATE/projects.tar.gz" -C "$PROJECT_DIR" .

# Backup configuration
cp /opt/visualizer/config/orch-config.yaml "$BACKUP_DIR/$DATE/"

# Backup Redis data
redis-cli --rdb "$BACKUP_DIR/$DATE/dump.rdb"

# Cleanup old backups (keep 30 days)
find "$BACKUP_DIR" -type d -mtime +30 -exec rm -rf {} \;

echo "Backup completed: $BACKUP_DIR/$DATE"
```

#### Database Backup

```bash
#!/bin/bash
# backup-database.sh

DB_URL="postgresql://user:pass@localhost:5432/visualizer"
BACKUP_DIR="/var/backups/visualizer/db"
DATE=$(date +%Y%m%d_%H%M%S)

mkdir -p "$BACKUP_DIR"

# Create database dump
pg_dump "$DB_URL" | gzip > "$BACKUP_DIR/visualizer_$DATE.sql.gz"

# Cleanup old backups
find "$BACKUP_DIR" -name "*.sql.gz" -mtime +7 -delete

echo "Database backup completed: visualizer_$DATE.sql.gz"
```

### Disaster Recovery

#### Recovery Procedures

```bash
#!/bin/bash
# restore-from-backup.sh

BACKUP_DATE="$1"
BACKUP_DIR="/var/backups/visualizer/$BACKUP_DATE"

if [[ ! -d "$BACKUP_DIR" ]]; then
    echo "Backup not found: $BACKUP_DIR"
    exit 1
fi

# Stop services
sudo systemctl stop visualizer
sudo systemctl stop redis

# Restore project files
sudo rm -rf /var/projects/*
sudo tar -xzf "$BACKUP_DIR/projects.tar.gz" -C /var/projects/

# Restore configuration
sudo cp "$BACKUP_DIR/orch-config.yaml" /opt/visualizer/config/

# Restore Redis data
sudo cp "$BACKUP_DIR/dump.rdb" /var/lib/redis/

# Restore database (if using PostgreSQL)
if [[ -f "$BACKUP_DIR/visualizer.sql.gz" ]]; then
    zcat "$BACKUP_DIR/visualizer.sql.gz" | psql "$DB_URL"
fi

# Start services
sudo systemctl start redis
sudo systemctl start visualizer

echo "Recovery completed from backup: $BACKUP_DATE"
```

### High Availability Setup

#### Master-Slave Redis Configuration

**Master (redis-master.conf)**:
```
bind 0.0.0.0
port 6379
requirepass your-redis-password
```

**Slave (redis-slave.conf)**:
```
bind 0.0.0.0
port 6379
slaveof redis-master 6379
masterauth your-redis-password
requirepass your-redis-password
```

#### Database Replication

```yaml
# PostgreSQL streaming replication
apiVersion: postgresql.cnpg.io/v1
kind: Cluster
metadata:
  name: postgres-cluster
spec:
  instances: 3
  primaryUpdateStrategy: unsupervised
  postgresql:
    parameters:
      max_connections: "200"
      shared_buffers: "256MB"
      effective_cache_size: "1GB"
```

## Troubleshooting

### Common Issues

#### High Memory Usage

**Symptoms**:
- Application consuming excessive memory
- Out of memory errors
- Slow response times

**Diagnosis**:
```bash
# Check memory usage
free -h
ps aux --sort=-%mem | head -20

# Check application memory
sudo -u visualizer ps -o pid,ppid,cmd,%mem,%cpu --sort=-%mem -C python

# Memory profiling
python -m memory_profiler app.py
```

**Solutions**:
1. Tune garbage collection
2. Implement connection pooling
3. Add memory limits to containers
4. Scale horizontally

#### WebSocket Connection Issues

**Symptoms**:
- Clients unable to connect via WebSocket
- Frequent disconnections
- Real-time updates not working

**Diagnosis**:
```bash
# Check WebSocket connections
netstat -tulpn | grep :5000
ss -tulpn | grep :5000

# Check nginx configuration
nginx -t
sudo systemctl status nginx

# Check application logs
tail -f /var/log/visualizer/app.log | grep -i websocket
```

**Solutions**:
1. Verify nginx WebSocket proxy configuration
2. Check firewall rules for WebSocket traffic
3. Tune WebSocket timeout settings
4. Enable WebSocket sticky sessions

#### Redis Connection Problems

**Symptoms**:
- Session data not persisting
- Scaling issues with multiple instances
- Cache misses

**Diagnosis**:
```bash
# Test Redis connection
redis-cli ping
redis-cli info replication

# Check Redis logs
tail -f /var/log/redis/redis-server.log

# Monitor Redis performance
redis-cli --latency-history
```

**Solutions**:
1. Verify Redis configuration
2. Check network connectivity
3. Tune Redis memory settings
4. Monitor Redis performance metrics

### Performance Issues

#### Slow API Responses

**Diagnosis Tools**:
```python
# Response time profiling
import time
from functools import wraps

def profile_time(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        start = time.time()
        result = f(*args, **kwargs)
        duration = time.time() - start
        logger.info(f"Function {f.__name__} took {duration:.3f}s")
        return result
    return wrapper
```

**Performance Monitoring**:
```bash
# Monitor system resources
htop
iotop
nethogs

# Database query analysis
EXPLAIN ANALYZE SELECT * FROM projects WHERE status = 'active';

# Application profiling
python -m cProfile -o profile.stats app.py
```

### Log Analysis

#### Centralized Log Search

```bash
# Search for errors
grep -r "ERROR" /var/log/visualizer/

# Search for specific patterns
journalctl -u visualizer | grep -i "websocket"

# Elasticsearch queries (if using ELK)
curl -X GET "elasticsearch:9200/visualizer-*/_search" -H 'Content-Type: application/json' -d'
{
  "query": {
    "bool": {
      "must": [
        {"match": {"level": "ERROR"}},
        {"range": {"@timestamp": {"gte": "now-1h"}}}
      ]
    }
  }
}'
```

#### Log Rotation

```bash
# Logrotate configuration
sudo tee /etc/logrotate.d/visualizer > /dev/null << 'EOF'
/var/log/visualizer/*.log {
    daily
    missingok
    rotate 52
    compress
    delaycompress
    notifempty
    create 644 visualizer visualizer
    postrotate
        systemctl reload visualizer
    endscript
}
EOF
```

## Maintenance Procedures

### Regular Maintenance Tasks

#### Daily Tasks

```bash
#!/bin/bash
# daily-maintenance.sh

# Check service status
systemctl is-active visualizer
systemctl is-active redis
systemctl is-active nginx

# Monitor disk usage
df -h
du -sh /var/log/visualizer/

# Check for errors in logs
grep -c "ERROR" /var/log/visualizer/app.log

# Backup critical data
/opt/scripts/backup-projects.sh
```

#### Weekly Tasks

```bash
#!/bin/bash
# weekly-maintenance.sh

# Update system packages
sudo apt update && sudo apt list --upgradable

# Analyze log patterns
/opt/scripts/analyze-logs.sh

# Performance report
/opt/scripts/performance-report.sh

# Security scan
/opt/scripts/security-check.sh
```

#### Monthly Tasks

```bash
#!/bin/bash
# monthly-maintenance.sh

# Full system backup
/opt/scripts/full-backup.sh

# Certificate renewal check
certbot certificates

# Performance tuning review
/opt/scripts/performance-tuning.sh

# Capacity planning analysis
/opt/scripts/capacity-analysis.sh
```

### Update Procedures

#### Application Updates

```bash
#!/bin/bash
# update-application.sh

# Backup current version
/opt/scripts/backup-projects.sh

# Stop services
sudo systemctl stop visualizer

# Update application
sudo -u visualizer bash << 'EOF'
cd /opt/visualizer
source venv/bin/activate
pip install --upgrade agent-workflow[web]
EOF

# Run database migrations (if any)
sudo -u visualizer /opt/visualizer/venv/bin/flask db upgrade

# Start services
sudo systemctl start visualizer

# Verify deployment
curl -f http://localhost:5000/health
```

#### System Updates

```bash
#!/bin/bash
# system-update.sh

# Create system snapshot (if using LVM)
sudo lvcreate -L 10G -s -n visualizer-snapshot /dev/vg/root

# Update system packages
sudo apt update && sudo apt upgrade -y

# Reboot if kernel updated
if [[ -f /var/run/reboot-required ]]; then
    sudo reboot
fi

# Verify services after reboot
sleep 60
systemctl is-active visualizer
systemctl is-active redis
systemctl is-active nginx
```

### Security Updates

#### Certificate Renewal

```bash
#!/bin/bash
# renew-certificates.sh

# Check certificate expiration
openssl x509 -in /etc/ssl/certs/visualizer.crt -text -noout | grep "Not After"

# Renew Let's Encrypt certificates
sudo certbot renew --quiet

# Reload nginx
sudo systemctl reload nginx

# Verify certificate
echo | openssl s_client -connect visualizer.yourcompany.com:443 2>/dev/null | openssl x509 -noout -dates
```

#### Security Patches

```bash
#!/bin/bash
# security-patches.sh

# Check for security updates
sudo apt list --upgradable | grep -i security

# Apply security updates
sudo unattended-upgrade

# Update Python dependencies
sudo -u visualizer bash << 'EOF'
cd /opt/visualizer
source venv/bin/activate
pip list --outdated
pip install --upgrade-strategy only-if-needed --upgrade agent-workflow[web]
EOF

# Restart services
sudo systemctl restart visualizer
```

This comprehensive deployment guide provides all the necessary information to successfully deploy, secure, monitor, and maintain the Multi-Project Visualizer in production environments. Follow the procedures outlined here to ensure a robust and reliable deployment.