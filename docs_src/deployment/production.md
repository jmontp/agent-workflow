# Production Deployment

Deploy your AI Agent TDD-Scrum workflow system to production with enterprise-grade reliability, security, and scalability.

## Deployment Picker

Choose the perfect deployment tier for your team:

<div class="deployment-picker">
  <div class="tier-card hobby">
    <div class="tier-header">
      <h3>🚀 Hobby</h3>
      <div class="price">Free</div>
    </div>
    <div class="tier-features">
      <ul>
        <li>✅ Single project</li>
        <li>✅ Community support</li>
        <li>✅ Basic monitoring</li>
        <li>✅ Docker deployment</li>
        <li>⚠️ 1GB RAM limit</li>
        <li>⚠️ Shared resources</li>
      </ul>
    </div>
    <div class="tier-actions">
      <a href="#hobby-deployment" class="btn-primary">Get Started Free</a>
    </div>
  </div>

  <div class="tier-card startup">
    <div class="tier-header">
      <h3>⚡ Startup</h3>
      <div class="price">$49<span>/month</span></div>
    </div>
    <div class="tier-features">
      <ul>
        <li>✅ Up to 10 projects</li>
        <li>✅ Priority support</li>
        <li>✅ Advanced monitoring</li>
        <li>✅ Auto-scaling</li>
        <li>✅ SSL certificates</li>
        <li>✅ 8GB RAM included</li>
      </ul>
    </div>
    <div class="tier-actions">
      <a href="#startup-deployment" class="btn-primary">Start Free Trial</a>
    </div>
  </div>

  <div class="tier-card enterprise">
    <div class="tier-header">
      <h3>🏢 Enterprise</h3>
      <div class="price">Custom</div>
    </div>
    <div class="tier-features">
      <ul>
        <li>✅ Unlimited projects</li>
        <li>✅ 24/7 enterprise support</li>
        <li>✅ Full observability suite</li>
        <li>✅ Multi-region deployment</li>
        <li>✅ SOC 2 compliance</li>
        <li>✅ Custom integrations</li>
      </ul>
    </div>
    <div class="tier-actions">
      <a href="#enterprise-deployment" class="btn-primary">Contact Sales</a>
    </div>
  </div>
</div>

## One-Click Deploy

Deploy instantly to your preferred cloud platform:

<div class="deploy-buttons">
  <a href="https://heroku.com/deploy?template=https://github.com/yourusername/agent-workflow" class="deploy-btn heroku">
    <img src="https://www.herokucdn.com/deploy/button.svg" alt="Deploy to Heroku">
  </a>
  
  <a href="https://railway.app/new/template/agent-workflow" class="deploy-btn railway">
    <img src="https://railway.app/button.svg" alt="Deploy on Railway">
  </a>
  
  <a href="https://console.aws.amazon.com/cloudformation/home#/stacks/new?stackName=agent-workflow&templateURL=https://agent-workflow-templates.s3.amazonaws.com/cloudformation.yaml" class="deploy-btn aws">
    <img src="https://s3.amazonaws.com/cloudformation-examples/cloudformation-launch-stack.png" alt="Launch Stack">
  </a>
  
  <a href="https://console.cloud.google.com/cloudshell/editor?cloudshell_git_repo=https://github.com/yourusername/agent-workflow&cloudshell_tutorial=deploy/gcp/tutorial.md" class="deploy-btn gcp">
    <img src="https://gstatic.com/cloudssh/images/open-btn.png" alt="Open in Cloud Shell">
  </a>
  
  <a href="https://portal.azure.com/#create/Microsoft.Template/uri/https%3A%2F%2Fraw.githubusercontent.com%2Fyourusername%2Fagent-workflow%2Fmain%2Fazuredeploy.json" class="deploy-btn azure">
    <img src="https://aka.ms/deploytoazurebutton" alt="Deploy to Azure">
  </a>
</div>

## Cost Calculator

Estimate your monthly costs across different deployment tiers:

<div class="cost-calculator">
  <div class="calculator-inputs">
    <div class="input-group">
      <label>Number of Projects</label>
      <input type="number" id="projects" value="1" min="1" max="100">
    </div>
    <div class="input-group">
      <label>Team Size</label>
      <input type="number" id="team-size" value="5" min="1" max="1000">
    </div>
    <div class="input-group">
      <label>Daily Active Hours</label>
      <input type="number" id="active-hours" value="8" min="1" max="24">
    </div>
    <div class="input-group">
      <label>Region</label>
      <select id="region">
        <option value="us-east-1">US East (N. Virginia)</option>
        <option value="us-west-2">US West (Oregon)</option>
        <option value="eu-west-1">Europe (Ireland)</option>
        <option value="ap-southeast-1">Asia Pacific (Singapore)</option>
      </select>
    </div>
  </div>
  
  <div class="cost-breakdown">
    <h4>Estimated Monthly Cost</h4>
    <div class="cost-items">
      <div class="cost-item">
        <span>Compute (CPU + Memory)</span>
        <span id="compute-cost">$0.00</span>
      </div>
      <div class="cost-item">
        <span>Storage (Database + Files)</span>
        <span id="storage-cost">$0.00</span>
      </div>
      <div class="cost-item">
        <span>Network (Bandwidth)</span>
        <span id="network-cost">$0.00</span>
      </div>
      <div class="cost-item">
        <span>Monitoring & Logs</span>
        <span id="monitoring-cost">$0.00</span>
      </div>
      <div class="cost-total">
        <span><strong>Total Monthly Cost</strong></span>
        <span id="total-cost"><strong>$0.00</strong></span>
      </div>
    </div>
  </div>
</div>

## Interactive Architecture

Explore the system architecture with interactive, zoomable diagrams:

<div class="architecture-viewer">
  <div class="architecture-tabs">
    <button class="tab-btn active" data-tab="overview">System Overview</button>
    <button class="tab-btn" data-tab="microservices">Microservices</button>
    <button class="tab-btn" data-tab="security">Security Layer</button>
    <button class="tab-btn" data-tab="data-flow">Data Flow</button>
  </div>
  
  <div class="architecture-content">
    <div id="overview-diagram" class="diagram-container active">
      <div class="diagram-zoom-controls">
        <button class="zoom-btn" data-action="zoom-in">+</button>
        <button class="zoom-btn" data-action="zoom-out">-</button>
        <button class="zoom-btn" data-action="reset">⌂</button>
      </div>
      <div class="diagram-svg">
        <svg viewBox="0 0 1200 800" class="architecture-svg">
          <!-- System Overview Diagram -->
          <defs>
            <linearGradient id="blueGradient" x1="0%" y1="0%" x2="100%" y2="100%">
              <stop offset="0%" style="stop-color:#3B82F6;stop-opacity:1" />
              <stop offset="100%" style="stop-color:#1E40AF;stop-opacity:1" />
            </linearGradient>
            <linearGradient id="greenGradient" x1="0%" y1="0%" x2="100%" y2="100%">
              <stop offset="0%" style="stop-color:#10B981;stop-opacity:1" />
              <stop offset="100%" style="stop-color:#047857;stop-opacity:1" />
            </linearGradient>
          </defs>
          
          <!-- Discord Layer -->
          <rect x="50" y="50" width="200" height="100" rx="10" fill="url(#blueGradient)" class="diagram-node" data-tooltip="Discord Bot - HITL Interface">
            <title>Discord Bot - Human-in-the-loop interface for command execution</title>
          </rect>
          <text x="150" y="100" text-anchor="middle" fill="white" font-weight="bold">Discord Bot</text>
          
          <!-- Orchestrator Layer -->
          <rect x="350" y="200" width="200" height="100" rx="10" fill="url(#greenGradient)" class="diagram-node" data-tooltip="Orchestrator - Central Coordination">
            <title>Orchestrator - Central workflow coordination and state management</title>
          </rect>
          <text x="450" y="250" text-anchor="middle" fill="white" font-weight="bold">Orchestrator</text>
          
          <!-- Agent Layer -->
          <rect x="50" y="350" width="150" height="80" rx="8" fill="#F59E0B" class="diagram-node" data-tooltip="Design Agent">
            <title>Design Agent - Architecture and planning</title>
          </rect>
          <text x="125" y="395" text-anchor="middle" fill="white" font-size="12">Design Agent</text>
          
          <rect x="220" y="350" width="150" height="80" rx="8" fill="#EF4444" class="diagram-node" data-tooltip="Code Agent">
            <title>Code Agent - Implementation and development</title>
          </rect>
          <text x="295" y="395" text-anchor="middle" fill="white" font-size="12">Code Agent</text>
          
          <rect x="390" y="350" width="150" height="80" rx="8" fill="#8B5CF6" class="diagram-node" data-tooltip="QA Agent">
            <title>QA Agent - Testing and quality assurance</title>
          </rect>
          <text x="465" y="395" text-anchor="middle" fill="white" font-size="12">QA Agent</text>
          
          <rect x="560" y="350" width="150" height="80" rx="8" fill="#06B6D4" class="diagram-node" data-tooltip="Data Agent">
            <title>Data Agent - Analytics and reporting</title>
          </rect>
          <text x="635" y="395" text-anchor="middle" fill="white" font-size="12">Data Agent</text>
          
          <!-- Storage Layer -->
          <rect x="800" y="200" width="150" height="80" rx="8" fill="#6B7280" class="diagram-node" data-tooltip="PostgreSQL Database">
            <title>PostgreSQL - Primary data storage</title>
          </rect>
          <text x="875" y="245" text-anchor="middle" fill="white" font-size="12">PostgreSQL</text>
          
          <rect x="800" y="300" width="150" height="80" rx="8" fill="#DC2626" class="diagram-node" data-tooltip="Redis Cache">
            <title>Redis - Caching and session storage</title>
          </rect>
          <text x="875" y="345" text-anchor="middle" fill="white" font-size="12">Redis Cache</text>
          
          <!-- Connections -->
          <line x1="150" y1="150" x2="350" y2="200" stroke="#374151" stroke-width="2" marker-end="url(#arrowhead)"/>
          <line x1="450" y1="300" x2="125" y2="350" stroke="#374151" stroke-width="2" marker-end="url(#arrowhead)"/>
          <line x1="450" y1="300" x2="295" y2="350" stroke="#374151" stroke-width="2" marker-end="url(#arrowhead)"/>
          <line x1="450" y1="300" x2="465" y2="350" stroke="#374151" stroke-width="2" marker-end="url(#arrowhead)"/>
          <line x1="450" y1="300" x2="635" y2="350" stroke="#374151" stroke-width="2" marker-end="url(#arrowhead)"/>
          <line x1="550" y1="240" x2="800" y2="240" stroke="#374151" stroke-width="2" marker-end="url(#arrowhead)"/>
          <line x1="550" y1="260" x2="800" y2="340" stroke="#374151" stroke-width="2" marker-end="url(#arrowhead)"/>
          
          <!-- Arrow marker -->
          <defs>
            <marker id="arrowhead" markerWidth="10" markerHeight="7" refX="9" refY="3.5" orient="auto">
              <polygon points="0 0, 10 3.5, 0 7" fill="#374151"/>
            </marker>
          </defs>
        </svg>
      </div>
    </div>
    
    <div id="microservices-diagram" class="diagram-container">
      <!-- Microservices architecture diagram would go here -->
      <div class="diagram-placeholder">
        <h3>Microservices Architecture</h3>
        <p>Interactive diagram showing service boundaries, APIs, and communication patterns</p>
      </div>
    </div>
    
    <div id="security-diagram" class="diagram-container">
      <!-- Security layer diagram would go here -->
      <div class="diagram-placeholder">
        <h3>Security Architecture</h3>
        <p>Interactive diagram showing security boundaries, authentication flows, and encryption</p>
      </div>
    </div>
    
    <div id="data-flow-diagram" class="diagram-container">
      <!-- Data flow diagram would go here -->
      <div class="diagram-placeholder">
        <h3>Data Flow Architecture</h3>
        <p>Interactive diagram showing data movement, processing, and storage patterns</p>
      </div>
    </div>
  </div>
</div>

## Hobby Deployment

Perfect for individual developers and small teams getting started.

### Quick Start with Docker

```bash
# Clone the repository
git clone https://github.com/yourusername/agent-workflow.git
cd agent-workflow

# Create environment file
cp .env.example .env

# Add your tokens
echo "DISCORD_BOT_TOKEN=your_discord_token" >> .env
echo "ANTHROPIC_API_KEY=your_anthropic_key" >> .env

# Deploy with Docker Compose
docker-compose -f docker-compose.hobby.yml up -d
```

### Hobby Docker Compose Configuration

```yaml
version: '3.8'

services:
  orchestrator:
    build: .
    environment:
      - DISCORD_BOT_TOKEN=${DISCORD_BOT_TOKEN}
      - ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}
      - ENVIRONMENT=hobby
      - LOG_LEVEL=INFO
    volumes:
      - ./projects:/app/projects
      - ./logs:/app/logs
    ports:
      - "8080:8080"
    restart: unless-stopped
    deploy:
      resources:
        limits:
          memory: 1G
          cpus: '0.5'

  redis:
    image: redis:7-alpine
    volumes:
      - redis_data:/data
    restart: unless-stopped

volumes:
  redis_data:
```

### Hobby Limitations

- **Single project** support
- **1GB RAM** limit
- **Shared CPU** resources
- **Community support** only
- **Basic monitoring** (logs only)
- **No SSL** certificates included

## Startup Deployment

Designed for growing teams that need reliability and scalability.

### Railway Deployment

Click the deploy button above or manually deploy:

```bash
# Install Railway CLI
npm install -g @railway/cli

# Login to Railway
railway login

# Deploy from template
railway deploy --template agent-workflow-startup

# Configure environment variables
railway variables set DISCORD_BOT_TOKEN=your_token
railway variables set ANTHROPIC_API_KEY=your_key
railway variables set TIER=startup
```

### Heroku Deployment

```bash
# Install Heroku CLI
npm install -g heroku

# Create Heroku app
heroku create your-agent-workflow

# Add PostgreSQL and Redis
heroku addons:create heroku-postgresql:standard-0
heroku addons:create heroku-redis:premium-0

# Configure environment
heroku config:set DISCORD_BOT_TOKEN=your_token
heroku config:set ANTHROPIC_API_KEY=your_key
heroku config:set TIER=startup

# Deploy
git push heroku main
```

### Startup Features

- **Up to 10 projects** with isolated environments
- **8GB RAM** with auto-scaling
- **Dedicated CPU** cores
- **Priority support** with 24-hour response
- **Advanced monitoring** with Prometheus/Grafana
- **SSL certificates** with automatic renewal
- **Backup & recovery** with point-in-time restoration

## Enterprise Deployment

Enterprise-grade deployment with full compliance and security features.

### Kubernetes Deployment

```yaml
# kubernetes/namespace.yaml
apiVersion: v1
kind: Namespace
metadata:
  name: agent-workflow
  labels:
    name: agent-workflow
    tier: enterprise
---
# kubernetes/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: orchestrator
  namespace: agent-workflow
spec:
  replicas: 3
  selector:
    matchLabels:
      app: orchestrator
  template:
    metadata:
      labels:
        app: orchestrator
    spec:
      securityContext:
        runAsNonRoot: true
        runAsUser: 1001
        fsGroup: 1001
      containers:
      - name: orchestrator
        image: agent-workflow:enterprise
        ports:
        - containerPort: 8080
        env:
        - name: DISCORD_BOT_TOKEN
          valueFrom:
            secretKeyRef:
              name: agent-workflow-secrets
              key: discord-token
        - name: ANTHROPIC_API_KEY
          valueFrom:
            secretKeyRef:
              name: agent-workflow-secrets
              key: anthropic-key
        - name: TIER
          value: "enterprise"
        resources:
          requests:
            memory: "2Gi"
            cpu: "1000m"
          limits:
            memory: "8Gi"
            cpu: "4000m"
        readinessProbe:
          httpGet:
            path: /health
            port: 8080
          initialDelaySeconds: 30
          periodSeconds: 10
        livenessProbe:
          httpGet:
            path: /health
            port: 8080
          initialDelaySeconds: 60
          periodSeconds: 30
        volumeMounts:
        - name: projects
          mountPath: /app/projects
        - name: logs
          mountPath: /app/logs
      volumes:
      - name: projects
        persistentVolumeClaim:
          claimName: projects-pvc
      - name: logs
        persistentVolumeClaim:
          claimName: logs-pvc
---
# kubernetes/service.yaml
apiVersion: v1
kind: Service
metadata:
  name: orchestrator-service
  namespace: agent-workflow
spec:
  selector:
    app: orchestrator
  ports:
    - protocol: TCP
      port: 80
      targetPort: 8080
  type: LoadBalancer
```

### Enterprise Features

- **Unlimited projects** with multi-tenancy
- **Multi-region deployment** for global teams
- **24/7 enterprise support** with dedicated SRE team
- **SOC 2 Type II compliance** with audit reports
- **Custom integrations** with enterprise tools
- **Advanced security** with RBAC, SSO, and audit logging
- **SLA guarantees** with 99.9% uptime commitment

## Container Orchestration

### Docker Swarm

```yaml
# docker-compose.swarm.yml
version: '3.8'

services:
  orchestrator:
    image: agent-workflow:latest
    deploy:
      replicas: 3
      update_config:
        parallelism: 1
        delay: 10s
        failure_action: rollback
      restart_policy:
        condition: on-failure
        delay: 5s
        max_attempts: 3
      placement:
        constraints:
          - node.role == worker
      resources:
        limits:
          cpus: '2'
          memory: 4G
        reservations:
          cpus: '1'
          memory: 2G
    networks:
      - agent-network
    secrets:
      - discord_token
      - anthropic_key
    volumes:
      - projects:/app/projects
      - type: tmpfs
        target: /tmp
        tmpfs:
          size: 1G

  postgres:
    image: postgres:15-alpine
    deploy:
      replicas: 1
      placement:
        constraints:
          - node.labels.postgres == true
      resources:
        limits:
          memory: 2G
        reservations:
          memory: 1G
    environment:
      POSTGRES_DB: agent_workflow
      POSTGRES_USER: agent_workflow
      POSTGRES_PASSWORD_FILE: /run/secrets/db_password
    secrets:
      - db_password
    volumes:
      - postgres_data:/var/lib/postgresql/data
    networks:
      - agent-network

  redis:
    image: redis:7-alpine
    deploy:
      replicas: 1
      placement:
        constraints:
          - node.labels.redis == true
    command: redis-server --requirepass-file /run/secrets/redis_password
    secrets:
      - redis_password
    volumes:
      - redis_data:/data
    networks:
      - agent-network

networks:
  agent-network:
    driver: overlay
    attachable: true

volumes:
  postgres_data:
  redis_data:
  projects:

secrets:
  discord_token:
    external: true
  anthropic_key:
    external: true
  db_password:
    external: true
  redis_password:
    external: true
```

Deploy to Docker Swarm:

```bash
# Initialize swarm
docker swarm init

# Create secrets
echo "your_discord_token" | docker secret create discord_token -
echo "your_anthropic_key" | docker secret create anthropic_key -
echo "secure_db_password" | docker secret create db_password -
echo "secure_redis_password" | docker secret create redis_password -

# Label nodes for service placement
docker node update --label-add postgres=true <node-id>
docker node update --label-add redis=true <node-id>

# Deploy stack
docker stack deploy -c docker-compose.swarm.yml agent-workflow
```

### Kubernetes with Helm

```yaml
# helm/values.yaml
replicaCount: 3

image:
  repository: agent-workflow
  tag: latest
  pullPolicy: IfNotPresent

service:
  type: LoadBalancer
  port: 80
  targetPort: 8080

ingress:
  enabled: true
  className: nginx
  annotations:
    cert-manager.io/cluster-issuer: letsencrypt-prod
    nginx.ingress.kubernetes.io/ssl-redirect: "true"
  hosts:
    - host: agent-workflow.example.com
      paths:
        - path: /
          pathType: Prefix
  tls:
    - secretName: agent-workflow-tls
      hosts:
        - agent-workflow.example.com

resources:
  limits:
    cpu: 4000m
    memory: 8Gi
  requests:
    cpu: 1000m
    memory: 2Gi

autoscaling:
  enabled: true
  minReplicas: 3
  maxReplicas: 10
  targetCPUUtilizationPercentage: 70
  targetMemoryUtilizationPercentage: 80

postgresql:
  enabled: true
  auth:
    postgresPassword: "secure_password"
    database: "agent_workflow"
  primary:
    persistence:
      enabled: true
      size: 100Gi
    resources:
      limits:
        memory: 4Gi
      requests:
        memory: 2Gi

redis:
  enabled: true
  auth:
    enabled: true
    password: "secure_redis_password"
  master:
    persistence:
      enabled: true
      size: 20Gi
```

Install with Helm:

```bash
# Add Helm repository
helm repo add agent-workflow https://charts.agent-workflow.com
helm repo update

# Install with custom values
helm install agent-workflow agent-workflow/agent-workflow \
  --namespace agent-workflow \
  --create-namespace \
  --values values.yaml \
  --set secrets.discordToken="your_discord_token" \
  --set secrets.anthropicKey="your_anthropic_key"
```

## Monitoring & Observability

### Prometheus + Grafana Stack

```yaml
# monitoring/docker-compose.yml
version: '3.8'

services:
  prometheus:
    image: prom/prometheus:latest
    container_name: prometheus
    ports:
      - "9090:9090"
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml
      - prometheus_data:/prometheus
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.path=/prometheus'
      - '--web.console.libraries=/usr/share/prometheus/console_libraries'
      - '--web.console.templates=/usr/share/prometheus/consoles'
      - '--storage.tsdb.retention.time=30d'
      - '--web.enable-lifecycle'

  grafana:
    image: grafana/grafana:latest
    container_name: grafana
    ports:
      - "3000:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin
      - GF_USERS_ALLOW_SIGN_UP=false
    volumes:
      - grafana_data:/var/lib/grafana
      - ./grafana/dashboards:/etc/grafana/provisioning/dashboards
      - ./grafana/datasources:/etc/grafana/provisioning/datasources

  node-exporter:
    image: prom/node-exporter:latest
    container_name: node-exporter
    ports:
      - "9100:9100"
    volumes:
      - /proc:/host/proc:ro
      - /sys:/host/sys:ro
      - /:/rootfs:ro
    command:
      - '--path.procfs=/host/proc'
      - '--path.rootfs=/rootfs'
      - '--path.sysfs=/host/sys'
      - '--collector.filesystem.mount-points-exclude=^/(sys|proc|dev|host|etc)($$|/)'

  cadvisor:
    image: gcr.io/cadvisor/cadvisor:latest
    container_name: cadvisor
    ports:
      - "8081:8080"
    volumes:
      - /:/rootfs:ro
      - /var/run:/var/run:ro
      - /sys:/sys:ro
      - /var/lib/docker/:/var/lib/docker:ro
      - /dev/disk/:/dev/disk:ro
    privileged: true
    devices:
      - /dev/kmsg

  jaeger:
    image: jaegertracing/all-in-one:latest
    container_name: jaeger
    ports:
      - "14268:14268"
      - "16686:16686"
    environment:
      - COLLECTOR_OTLP_ENABLED=true

volumes:
  prometheus_data:
  grafana_data:
```

### Prometheus Configuration

```yaml
# monitoring/prometheus.yml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

rule_files:
  - "alerts.yml"

alerting:
  alertmanagers:
    - static_configs:
        - targets:
          - alertmanager:9093

scrape_configs:
  - job_name: 'prometheus'
    static_configs:
      - targets: ['localhost:9090']

  - job_name: 'agent-workflow'
    static_configs:
      - targets: ['orchestrator:8080']
    metrics_path: '/metrics'
    scrape_interval: 5s

  - job_name: 'node-exporter'
    static_configs:
      - targets: ['node-exporter:9100']

  - job_name: 'cadvisor'
    static_configs:
      - targets: ['cadvisor:8080']

  - job_name: 'redis'
    static_configs:
      - targets: ['redis:6379']

  - job_name: 'postgres'
    static_configs:
      - targets: ['postgres:5432']
```

### Custom Metrics Implementation

```python
# lib/metrics.py
from prometheus_client import Counter, Histogram, Gauge, start_http_server
import time

# Custom metrics for agent workflow
agent_tasks_total = Counter(
    'agent_tasks_total',
    'Total number of agent tasks executed',
    ['agent_type', 'status']
)

agent_task_duration = Histogram(
    'agent_task_duration_seconds',
    'Time spent executing agent tasks',
    ['agent_type'],
    buckets=[0.1, 0.5, 1.0, 2.5, 5.0, 10.0, 30.0, 60.0, 300.0]
)

active_projects = Gauge(
    'active_projects',
    'Number of active projects being managed'
)

discord_commands_total = Counter(
    'discord_commands_total',
    'Total number of Discord commands received',
    ['command', 'status']
)

orchestrator_state = Gauge(
    'orchestrator_state',
    'Current state of the orchestrator',
    ['project_name', 'state']
)

def track_agent_task(agent_type: str):
    """Decorator to track agent task execution"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                agent_tasks_total.labels(agent_type=agent_type, status='success').inc()
                return result
            except Exception as e:
                agent_tasks_total.labels(agent_type=agent_type, status='error').inc()
                raise
            finally:
                duration = time.time() - start_time
                agent_task_duration.labels(agent_type=agent_type).observe(duration)
        return wrapper
    return decorator

def start_metrics_server(port=8000):
    """Start Prometheus metrics server"""
    start_http_server(port)
```

### Grafana Dashboards

```json
{
  "dashboard": {
    "title": "Agent Workflow Overview",
    "panels": [
      {
        "title": "Agent Task Success Rate",
        "type": "stat",
        "targets": [
          {
            "expr": "rate(agent_tasks_total{status=\"success\"}[5m]) / rate(agent_tasks_total[5m])"
          }
        ]
      },
      {
        "title": "Active Projects",
        "type": "singlestat",
        "targets": [
          {
            "expr": "active_projects"
          }
        ]
      },
      {
        "title": "Agent Task Duration",
        "type": "graph",
        "targets": [
          {
            "expr": "histogram_quantile(0.95, agent_task_duration_seconds_bucket)"
          }
        ]
      },
      {
        "title": "Discord Commands",
        "type": "graph",
        "targets": [
          {
            "expr": "rate(discord_commands_total[5m])"
          }
        ]
      }
    ]
  }
}
```

## Security Hardening

### SSL/TLS Configuration

```nginx
# nginx/ssl.conf
server {
    listen 80;
    server_name agent-workflow.yourdomain.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name agent-workflow.yourdomain.com;

    # SSL configuration
    ssl_certificate /etc/letsencrypt/live/agent-workflow.yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/agent-workflow.yourdomain.com/privkey.pem;
    
    # SSL security settings
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES128-GCM-SHA256:ECDHE-RSA-AES256-GCM-SHA384:ECDHE-RSA-AES128-SHA256:ECDHE-RSA-AES256-SHA384;
    ssl_prefer_server_ciphers on;
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 10m;
    
    # HSTS
    add_header Strict-Transport-Security "max-age=63072000; includeSubDomains; preload" always;
    
    # Security headers
    add_header X-Frame-Options DENY always;
    add_header X-Content-Type-Options nosniff always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;
    add_header Content-Security-Policy "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline';" always;

    # Rate limiting
    limit_req_zone $binary_remote_addr zone=api:10m rate=10r/s;
    limit_req zone=api burst=20 nodelay;

    location / {
        proxy_pass http://orchestrator:8080;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Timeouts
        proxy_connect_timeout 30s;
        proxy_send_timeout 30s;
        proxy_read_timeout 30s;
    }
    
    # Health check endpoint
    location /health {
        access_log off;
        proxy_pass http://orchestrator:8080/health;
    }
}
```

### Firewall Configuration

```bash
#!/bin/bash
# security/firewall-setup.sh

# UFW firewall rules for production deployment
sudo ufw --force reset

# Default policies
sudo ufw default deny incoming
sudo ufw default allow outgoing

# SSH access (change port as needed)
sudo ufw allow 22/tcp

# HTTP/HTTPS
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp

# Monitoring (restrict to internal network)
sudo ufw allow from 10.0.0.0/8 to any port 9090
sudo ufw allow from 10.0.0.0/8 to any port 3000

# Database access (internal only)
sudo ufw allow from 10.0.0.0/8 to any port 5432
sudo ufw allow from 10.0.0.0/8 to any port 6379

# Enable firewall
sudo ufw --force enable

# Log firewall events
sudo ufw logging on
```

### Secrets Management

```yaml
# secrets/docker-compose.secrets.yml
version: '3.8'

services:
  vault:
    image: vault:latest
    container_name: vault
    ports:
      - "8200:8200"
    environment:
      VAULT_DEV_ROOT_TOKEN_ID: myroot
      VAULT_DEV_LISTEN_ADDRESS: 0.0.0.0:8200
    cap_add:
      - IPC_LOCK
    volumes:
      - vault_data:/vault/data
      - ./vault/config:/vault/config
    command: vault server -config=/vault/config/vault.hcl

  consul:
    image: consul:latest
    container_name: consul
    ports:
      - "8500:8500"
    environment:
      CONSUL_BIND_INTERFACE: eth0
    volumes:
      - consul_data:/consul/data

volumes:
  vault_data:
  consul_data:
```

### Environment Security

```bash
# security/env-setup.sh
#!/bin/bash

# Create secure environment file
cat > .env.production << EOF
# Environment Configuration
ENVIRONMENT=production
DEBUG=false
LOG_LEVEL=INFO

# Discord Configuration
DISCORD_BOT_TOKEN=\${DISCORD_BOT_TOKEN}
DISCORD_CLIENT_ID=\${DISCORD_CLIENT_ID}
DISCORD_CLIENT_SECRET=\${DISCORD_CLIENT_SECRET}

# Anthropic Configuration
ANTHROPIC_API_KEY=\${ANTHROPIC_API_KEY}

# Database Configuration
POSTGRES_HOST=postgres
POSTGRES_PORT=5432
POSTGRES_DB=agent_workflow
POSTGRES_USER=agent_workflow
POSTGRES_PASSWORD=\${POSTGRES_PASSWORD}

# Redis Configuration
REDIS_HOST=redis
REDIS_PORT=6379
REDIS_PASSWORD=\${REDIS_PASSWORD}

# Security Configuration
SECRET_KEY=\${SECRET_KEY}
ENCRYPTION_KEY=\${ENCRYPTION_KEY}
JWT_SECRET=\${JWT_SECRET}

# Monitoring Configuration
PROMETHEUS_ENABLED=true
GRAFANA_ENABLED=true
JAEGER_ENABLED=true

# Rate Limiting
RATE_LIMIT_ENABLED=true
RATE_LIMIT_REQUESTS_PER_MINUTE=60
EOF

# Set secure permissions
chmod 600 .env.production
```

## High Availability

### Load Balancer Configuration

```yaml
# ha/haproxy.cfg
global
    daemon
    maxconn 4096
    log stdout local0
    
defaults
    mode http
    timeout connect 5000ms
    timeout client 50000ms
    timeout server 50000ms
    option httplog
    option dontlognull
    option redispatch
    retries 3

# Frontend configuration
frontend agent_workflow_frontend
    bind *:80
    bind *:443 ssl crt /etc/ssl/certs/agent-workflow.pem
    redirect scheme https if !{ ssl_fc }
    
    # Health check endpoint
    acl health_check path_beg /health
    use_backend health_backend if health_check
    
    # Default backend
    default_backend agent_workflow_backend

# Backend configuration
backend agent_workflow_backend
    balance roundrobin
    option httpchk GET /health
    
    # Orchestrator instances
    server orchestrator-1 orchestrator-1:8080 check
    server orchestrator-2 orchestrator-2:8080 check
    server orchestrator-3 orchestrator-3:8080 check

# Health check backend
backend health_backend
    balance roundrobin
    server health-1 orchestrator-1:8080 check
    server health-2 orchestrator-2:8080 check
    server health-3 orchestrator-3:8080 check

# Statistics
listen stats
    bind *:8404
    stats enable
    stats uri /stats
    stats refresh 30s
    stats hide-version
```

### Database High Availability

```yaml
# ha/postgres-ha.yml
version: '3.8'

services:
  postgres-master:
    image: postgres:15-alpine
    environment:
      POSTGRES_DB: agent_workflow
      POSTGRES_USER: agent_workflow
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
      POSTGRES_REPLICATION_USER: replicator
      POSTGRES_REPLICATION_PASSWORD: ${REPLICATION_PASSWORD}
    volumes:
      - postgres_master_data:/var/lib/postgresql/data
      - ./postgres/master-setup.sql:/docker-entrypoint-initdb.d/master-setup.sql
    command: |
      postgres
      -c wal_level=replica
      -c max_wal_senders=3
      -c max_replication_slots=3
      -c hot_standby=on
      -c archive_mode=on
      -c archive_command='cp %p /var/lib/postgresql/archive/%f'

  postgres-replica-1:
    image: postgres:15-alpine
    environment:
      PGUSER: replicator
      POSTGRES_PASSWORD: ${REPLICATION_PASSWORD}
      POSTGRES_MASTER_SERVICE: postgres-master
    volumes:
      - postgres_replica1_data:/var/lib/postgresql/data
    command: |
      bash -c "
      pg_basebackup -h postgres-master -D /var/lib/postgresql/data -U replicator -v -P -W
      echo 'standby_mode = on' >> /var/lib/postgresql/data/recovery.conf
      echo 'primary_conninfo = host=postgres-master port=5432 user=replicator' >> /var/lib/postgresql/data/recovery.conf
      postgres
      "
    depends_on:
      - postgres-master

  postgres-replica-2:
    image: postgres:15-alpine
    environment:
      PGUSER: replicator
      POSTGRES_PASSWORD: ${REPLICATION_PASSWORD}
      POSTGRES_MASTER_SERVICE: postgres-master
    volumes:
      - postgres_replica2_data:/var/lib/postgresql/data
    command: |
      bash -c "
      pg_basebackup -h postgres-master -D /var/lib/postgresql/data -U replicator -v -P -W
      echo 'standby_mode = on' >> /var/lib/postgresql/data/recovery.conf
      echo 'primary_conninfo = host=postgres-master port=5432 user=replicator' >> /var/lib/postgresql/data/recovery.conf
      postgres
      "
    depends_on:
      - postgres-master

  pgpool:
    image: pgpool/pgpool:latest
    environment:
      PGPOOL_BACKEND_HOSTNAME0: postgres-master
      PGPOOL_BACKEND_PORT0: 5432
      PGPOOL_BACKEND_WEIGHT0: 1
      PGPOOL_BACKEND_HOSTNAME1: postgres-replica-1
      PGPOOL_BACKEND_PORT1: 5432
      PGPOOL_BACKEND_WEIGHT1: 1
      PGPOOL_BACKEND_HOSTNAME2: postgres-replica-2
      PGPOOL_BACKEND_PORT2: 5432
      PGPOOL_BACKEND_WEIGHT2: 1
      PGPOOL_ENABLE_LOAD_BALANCING: "yes"
      PGPOOL_MASTER_SLAVE_MODE: "on"
    ports:
      - "5432:5432"
    depends_on:
      - postgres-master
      - postgres-replica-1
      - postgres-replica-2

volumes:
  postgres_master_data:
  postgres_replica1_data:
  postgres_replica2_data:
```

### Redis High Availability

```yaml
# ha/redis-ha.yml
version: '3.8'

services:
  redis-master:
    image: redis:7-alpine
    container_name: redis-master
    ports:
      - "6379:6379"
    command: redis-server --appendonly yes --requirepass ${REDIS_PASSWORD}
    volumes:
      - redis_master_data:/data

  redis-replica-1:
    image: redis:7-alpine
    container_name: redis-replica-1
    ports:
      - "6380:6379"
    command: redis-server --appendonly yes --requirepass ${REDIS_PASSWORD} --slaveof redis-master 6379 --masterauth ${REDIS_PASSWORD}
    volumes:
      - redis_replica1_data:/data
    depends_on:
      - redis-master

  redis-replica-2:
    image: redis:7-alpine
    container_name: redis-replica-2
    ports:
      - "6381:6379"
    command: redis-server --appendonly yes --requirepass ${REDIS_PASSWORD} --slaveof redis-master 6379 --masterauth ${REDIS_PASSWORD}
    volumes:
      - redis_replica2_data:/data
    depends_on:
      - redis-master

  redis-sentinel-1:
    image: redis:7-alpine
    container_name: redis-sentinel-1
    ports:
      - "26379:26379"
    command: redis-sentinel /usr/local/etc/redis/sentinel.conf
    volumes:
      - ./redis/sentinel.conf:/usr/local/etc/redis/sentinel.conf
    depends_on:
      - redis-master

  redis-sentinel-2:
    image: redis:7-alpine
    container_name: redis-sentinel-2
    ports:
      - "26380:26379"
    command: redis-sentinel /usr/local/etc/redis/sentinel.conf
    volumes:
      - ./redis/sentinel.conf:/usr/local/etc/redis/sentinel.conf
    depends_on:
      - redis-master

  redis-sentinel-3:
    image: redis:7-alpine
    container_name: redis-sentinel-3
    ports:
      - "26381:26379"
    command: redis-sentinel /usr/local/etc/redis/sentinel.conf
    volumes:
      - ./redis/sentinel.conf:/usr/local/etc/redis/sentinel.conf
    depends_on:
      - redis-master

volumes:
  redis_master_data:
  redis_replica1_data:
  redis_replica2_data:
```

## Performance Optimization

### Application Performance

```python
# lib/performance.py
import asyncio
import aiohttp
import aiocache
from functools import wraps
import time

# Cache configuration
cache = aiocache.Cache(aiocache.SimpleMemoryCache)

def async_cached(ttl=300):
    """Async cache decorator with TTL"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            cache_key = f"{func.__name__}:{hash(str(args) + str(kwargs))}"
            cached_result = await cache.get(cache_key)
            if cached_result is not None:
                return cached_result
            
            result = await func(*args, **kwargs)
            await cache.set(cache_key, result, ttl=ttl)
            return result
        return wrapper
    return decorator

def rate_limit(calls_per_second=10):
    """Rate limiting decorator"""
    def decorator(func):
        last_called = [0.0]
        
        @wraps(func)
        async def wrapper(*args, **kwargs):
            elapsed = time.time() - last_called[0]
            left_to_wait = 1.0 / calls_per_second - elapsed
            if left_to_wait > 0:
                await asyncio.sleep(left_to_wait)
            ret = await func(*args, **kwargs)
            last_called[0] = time.time()
            return ret
        return wrapper
    return decorator

class ConnectionPool:
    """HTTP connection pool for external APIs"""
    
    def __init__(self, max_connections=100, max_connections_per_host=30):
        connector = aiohttp.TCPConnector(
            limit=max_connections,
            limit_per_host=max_connections_per_host,
            ttl_dns_cache=300,
            use_dns_cache=True,
            keepalive_timeout=30,
            enable_cleanup_closed=True
        )
        self.session = aiohttp.ClientSession(
            connector=connector,
            timeout=aiohttp.ClientTimeout(total=30, connect=10)
        )
    
    async def close(self):
        await self.session.close()
```

### Database Optimization

```sql
-- database/performance.sql

-- Indexes for common queries
CREATE INDEX CONCURRENTLY idx_projects_status ON projects(status);
CREATE INDEX CONCURRENTLY idx_tasks_agent_type ON tasks(agent_type);
CREATE INDEX CONCURRENTLY idx_tasks_created_at ON tasks(created_at);
CREATE INDEX CONCURRENTLY idx_executions_status_created ON executions(status, created_at);

-- Partial indexes for active records
CREATE INDEX CONCURRENTLY idx_active_projects ON projects(id) WHERE status = 'active';
CREATE INDEX CONCURRENTLY idx_pending_tasks ON tasks(id) WHERE status = 'pending';

-- Composite indexes for complex queries
CREATE INDEX CONCURRENTLY idx_tasks_project_status ON tasks(project_id, status);
CREATE INDEX CONCURRENTLY idx_executions_task_status ON executions(task_id, status);

-- Text search indexes
CREATE INDEX CONCURRENTLY idx_projects_name_gin ON projects USING gin(to_tsvector('english', name));
CREATE INDEX CONCURRENTLY idx_tasks_description_gin ON tasks USING gin(to_tsvector('english', description));

-- Analyze tables for better query planning
ANALYZE projects;
ANALYZE tasks;
ANALYZE executions;
ANALYZE agents;

-- Vacuum and reindex maintenance
VACUUM ANALYZE;
REINDEX DATABASE agent_workflow;
```

### Caching Strategy

```python
# lib/cache.py
import redis
import json
import pickle
from typing import Any, Optional
from datetime import timedelta

class CacheManager:
    """Multi-level caching with Redis and in-memory fallback"""
    
    def __init__(self, redis_url: str = None):
        self.redis_client = redis.from_url(redis_url) if redis_url else None
        self.local_cache = {}
        self.cache_stats = {
            'hits': 0,
            'misses': 0,
            'redis_hits': 0,
            'local_hits': 0
        }
    
    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache with fallback strategy"""
        # Try local cache first
        if key in self.local_cache:
            self.cache_stats['hits'] += 1
            self.cache_stats['local_hits'] += 1
            return self.local_cache[key]['value']
        
        # Try Redis cache
        if self.redis_client:
            try:
                value = self.redis_client.get(key)
                if value:
                    decoded_value = pickle.loads(value)
                    # Store in local cache for faster access
                    self.local_cache[key] = {
                        'value': decoded_value,
                        'timestamp': time.time()
                    }
                    self.cache_stats['hits'] += 1
                    self.cache_stats['redis_hits'] += 1
                    return decoded_value
            except Exception as e:
                print(f"Redis cache error: {e}")
        
        self.cache_stats['misses'] += 1
        return None
    
    async def set(self, key: str, value: Any, ttl: int = 300):
        """Set value in cache with TTL"""
        # Store in local cache
        self.local_cache[key] = {
            'value': value,
            'timestamp': time.time(),
            'ttl': ttl
        }
        
        # Store in Redis cache
        if self.redis_client:
            try:
                self.redis_client.setex(
                    key, 
                    ttl, 
                    pickle.dumps(value)
                )
            except Exception as e:
                print(f"Redis cache error: {e}")
    
    async def invalidate(self, pattern: str):
        """Invalidate cache entries matching pattern"""
        # Clear local cache
        keys_to_remove = [k for k in self.local_cache.keys() if pattern in k]
        for key in keys_to_remove:
            del self.local_cache[key]
        
        # Clear Redis cache
        if self.redis_client:
            try:
                keys = self.redis_client.keys(f"*{pattern}*")
                if keys:
                    self.redis_client.delete(*keys)
            except Exception as e:
                print(f"Redis cache error: {e}")
    
    def get_stats(self) -> dict:
        """Get cache performance statistics"""
        total_requests = self.cache_stats['hits'] + self.cache_stats['misses']
        hit_rate = (self.cache_stats['hits'] / total_requests * 100) if total_requests > 0 else 0
        
        return {
            'hit_rate': round(hit_rate, 2),
            'total_requests': total_requests,
            'cache_size': len(self.local_cache),
            **self.cache_stats
        }

# Global cache instance
cache_manager = CacheManager()
```

## Disaster Recovery

### Backup Strategy

```bash
#!/bin/bash
# backup/backup.sh

set -e

# Configuration
BACKUP_DIR="/var/backups/agent-workflow"
POSTGRES_CONTAINER="agent-workflow-postgres"
REDIS_CONTAINER="agent-workflow-redis"
S3_BUCKET="agent-workflow-backups"
RETENTION_DAYS=30

# Create backup directory
mkdir -p "$BACKUP_DIR"

# Timestamp for this backup
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

echo "Starting backup at $(date)"

# PostgreSQL backup
echo "Backing up PostgreSQL database..."
docker exec "$POSTGRES_CONTAINER" pg_dump -U agent_workflow agent_workflow | gzip > "$BACKUP_DIR/postgres_$TIMESTAMP.sql.gz"

# Redis backup
echo "Backing up Redis data..."
docker exec "$REDIS_CONTAINER" redis-cli --rdb /tmp/dump.rdb
docker cp "$REDIS_CONTAINER:/tmp/dump.rdb" "$BACKUP_DIR/redis_$TIMESTAMP.rdb"

# Application data backup
echo "Backing up application data..."
tar -czf "$BACKUP_DIR/projects_$TIMESTAMP.tar.gz" -C /var/lib/docker/volumes/agent-workflow_projects/_data .
tar -czf "$BACKUP_DIR/logs_$TIMESTAMP.tar.gz" -C /var/lib/docker/volumes/agent-workflow_logs/_data .

# Configuration backup
echo "Backing up configuration..."
tar -czf "$BACKUP_DIR/config_$TIMESTAMP.tar.gz" docker-compose.yml .env nginx/ monitoring/

# Upload to S3
echo "Uploading backups to S3..."
aws s3 sync "$BACKUP_DIR" "s3://$S3_BUCKET/$(date +%Y/%m/%d)/"

# Cleanup old backups
echo "Cleaning up old backups..."
find "$BACKUP_DIR" -name "*.gz" -mtime +$RETENTION_DAYS -delete
find "$BACKUP_DIR" -name "*.rdb" -mtime +$RETENTION_DAYS -delete

# Verify backup integrity
echo "Verifying backup integrity..."
gunzip -t "$BACKUP_DIR/postgres_$TIMESTAMP.sql.gz"
tar -tzf "$BACKUP_DIR/projects_$TIMESTAMP.tar.gz" > /dev/null

echo "Backup completed successfully at $(date)"

# Send notification
curl -X POST "$SLACK_WEBHOOK_URL" \
  -H 'Content-type: application/json' \
  --data "{\"text\":\"✅ Backup completed successfully for agent-workflow at $(date)\"}"
```

### Restore Procedures

```bash
#!/bin/bash
# backup/restore.sh

set -e

# Configuration
BACKUP_DIR="/var/backups/agent-workflow"
POSTGRES_CONTAINER="agent-workflow-postgres"
REDIS_CONTAINER="agent-workflow-redis"

# Check if backup timestamp is provided
if [ -z "$1" ]; then
    echo "Usage: $0 <backup_timestamp>"
    echo "Available backups:"
    ls -la "$BACKUP_DIR" | grep -E "(postgres|redis|projects|logs|config)_[0-9]{8}_[0-9]{6}"
    exit 1
fi

TIMESTAMP=$1

echo "Starting restore from backup timestamp: $TIMESTAMP"

# Stop services
echo "Stopping services..."
docker-compose down

# Restore PostgreSQL
echo "Restoring PostgreSQL database..."
docker-compose up -d postgres
sleep 10
gunzip -c "$BACKUP_DIR/postgres_$TIMESTAMP.sql.gz" | docker exec -i "$POSTGRES_CONTAINER" psql -U agent_workflow -d agent_workflow

# Restore Redis
echo "Restoring Redis data..."
docker cp "$BACKUP_DIR/redis_$TIMESTAMP.rdb" "$REDIS_CONTAINER:/data/dump.rdb"
docker-compose restart redis

# Restore application data
echo "Restoring application data..."
docker volume rm agent-workflow_projects agent-workflow_logs
docker volume create agent-workflow_projects
docker volume create agent-workflow_logs

# Extract to temporary container
docker run --rm -v agent-workflow_projects:/data -v "$BACKUP_DIR":/backup alpine sh -c "cd /data && tar -xzf /backup/projects_$TIMESTAMP.tar.gz"
docker run --rm -v agent-workflow_logs:/data -v "$BACKUP_DIR":/backup alpine sh -c "cd /data && tar -xzf /backup/logs_$TIMESTAMP.tar.gz"

# Restore configuration
echo "Restoring configuration..."
tar -xzf "$BACKUP_DIR/config_$TIMESTAMP.tar.gz"

# Start all services
echo "Starting all services..."
docker-compose up -d

# Wait for services to be ready
echo "Waiting for services to be ready..."
sleep 30

# Verify restore
echo "Verifying restore..."
docker-compose exec orchestrator python scripts/health-check.py

echo "Restore completed successfully!"
```

### Disaster Recovery Testing

```bash
#!/bin/bash
# dr/test-disaster-recovery.sh

set -e

# Configuration
DR_ENVIRONMENT="dr-test"
PRODUCTION_BACKUP_S3="s3://agent-workflow-backups/latest/"
DR_STACK_NAME="agent-workflow-dr"

echo "Starting disaster recovery test..."

# Create DR environment
echo "Creating DR environment..."
aws cloudformation create-stack \
  --stack-name "$DR_STACK_NAME" \
  --template-body file://cloudformation/dr-template.yaml \
  --parameters ParameterKey=Environment,ParameterValue="$DR_ENVIRONMENT" \
  --capabilities CAPABILITY_IAM

# Wait for stack creation
echo "Waiting for stack creation..."
aws cloudformation wait stack-create-complete --stack-name "$DR_STACK_NAME"

# Get DR environment details
DR_INSTANCE_ID=$(aws cloudformation describe-stacks \
  --stack-name "$DR_STACK_NAME" \
  --query 'Stacks[0].Outputs[?OutputKey==`InstanceId`].OutputValue' \
  --output text)

DR_PUBLIC_IP=$(aws cloudformation describe-stacks \
  --stack-name "$DR_STACK_NAME" \
  --query 'Stacks[0].Outputs[?OutputKey==`PublicIP`].OutputValue' \
  --output text)

# Deploy application to DR environment
echo "Deploying application to DR environment..."
ssh -i ~/.ssh/agent-workflow-key.pem ec2-user@"$DR_PUBLIC_IP" << 'EOF'
  # Clone repository
  git clone https://github.com/yourusername/agent-workflow.git
  cd agent-workflow
  
  # Download latest backup
  aws s3 sync s3://agent-workflow-backups/latest/ ./backups/
  
  # Restore from backup
  ./backup/restore.sh $(ls backups/postgres_*.sql.gz | head -1 | sed 's/.*postgres_\([0-9_]*\)\.sql\.gz/\1/')
  
  # Start services
  docker-compose up -d
EOF

# Run DR tests
echo "Running DR tests..."
./tests/dr-tests.sh "$DR_PUBLIC_IP"

# Cleanup DR environment
echo "Cleaning up DR environment..."
aws cloudformation delete-stack --stack-name "$DR_STACK_NAME"

echo "Disaster recovery test completed successfully!"
```

## Security Best Practices

### Security Hardening Checklist

```markdown
## Security Hardening Checklist

### Infrastructure Security
- [ ] Use non-root containers with specific user IDs
- [ ] Enable read-only root filesystem where possible
- [ ] Implement resource limits and quotas
- [ ] Use secrets management (Vault, AWS Secrets Manager)
- [ ] Enable container image scanning
- [ ] Implement network segmentation
- [ ] Use private container registries
- [ ] Enable audit logging for all services

### Application Security
- [ ] Implement input validation and sanitization
- [ ] Use parameterized queries to prevent SQL injection
- [ ] Enable CSRF protection
- [ ] Implement rate limiting
- [ ] Use secure session management
- [ ] Enable HTTPS everywhere with HSTS
- [ ] Implement proper error handling (no sensitive data in errors)
- [ ] Use secure random number generation

### Authentication & Authorization
- [ ] Implement multi-factor authentication
- [ ] Use OAuth 2.0 with PKCE for API access
- [ ] Implement role-based access control (RBAC)
- [ ] Use JWT tokens with proper expiration
- [ ] Implement session timeout
- [ ] Use strong password policies
- [ ] Enable account lockout after failed attempts
- [ ] Implement privilege escalation controls

### Data Protection
- [ ] Encrypt data at rest using AES-256
- [ ] Encrypt data in transit using TLS 1.3
- [ ] Implement key rotation policies
- [ ] Use secure key management
- [ ] Implement data backup encryption
- [ ] Enable database encryption
- [ ] Implement PII data classification
- [ ] Use data masking for non-production environments

### Monitoring & Compliance
- [ ] Enable security event logging
- [ ] Implement intrusion detection
- [ ] Set up vulnerability scanning
- [ ] Implement compliance monitoring
- [ ] Enable audit trail logging
- [ ] Set up security alerting
- [ ] Implement incident response procedures
- [ ] Regular security assessments
```

### OWASP Security Headers

```python
# lib/security_middleware.py
from flask import Flask, request, g
import time
import hashlib
import secrets

class SecurityMiddleware:
    """Security middleware for Flask applications"""
    
    def __init__(self, app: Flask):
        self.app = app
        self.setup_security_headers()
        self.setup_rate_limiting()
        self.setup_csrf_protection()
    
    def setup_security_headers(self):
        """Configure security headers"""
        @self.app.after_request
        def add_security_headers(response):
            # HSTS
            response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains; preload'
            
            # XSS Protection
            response.headers['X-XSS-Protection'] = '1; mode=block'
            
            # Content Type Options
            response.headers['X-Content-Type-Options'] = 'nosniff'
            
            # Frame Options
            response.headers['X-Frame-Options'] = 'DENY'
            
            # Referrer Policy
            response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
            
            # Content Security Policy
            response.headers['Content-Security-Policy'] = (
                "default-src 'self'; "
                "script-src 'self' 'unsafe-inline' 'unsafe-eval'; "
                "style-src 'self' 'unsafe-inline'; "
                "img-src 'self' data: https:; "
                "font-src 'self' data:; "
                "connect-src 'self' https://api.anthropic.com; "
                "frame-ancestors 'none'; "
                "base-uri 'self';"
            )
            
            # Permissions Policy
            response.headers['Permissions-Policy'] = (
                "geolocation=(), "
                "microphone=(), "
                "camera=(), "
                "payment=(), "
                "usb=(), "
                "bluetooth=()"
            )
            
            return response
    
    def setup_rate_limiting(self):
        """Configure rate limiting"""
        rate_limit_storage = {}
        
        @self.app.before_request
        def check_rate_limit():
            client_ip = request.environ.get('HTTP_X_FORWARDED_FOR', request.remote_addr)
            current_time = time.time()
            
            # Clean old entries
            cutoff_time = current_time - 60  # 1 minute window
            rate_limit_storage = {
                ip: requests for ip, requests in rate_limit_storage.items()
                if any(req_time > cutoff_time for req_time in requests)
            }
            
            # Check rate limit
            if client_ip in rate_limit_storage:
                requests_in_window = [req_time for req_time in rate_limit_storage[client_ip] if req_time > cutoff_time]
                if len(requests_in_window) >= 100:  # 100 requests per minute
                    return {'error': 'Rate limit exceeded'}, 429
            
            # Record request
            if client_ip not in rate_limit_storage:
                rate_limit_storage[client_ip] = []
            rate_limit_storage[client_ip].append(current_time)
    
    def setup_csrf_protection(self):
        """Configure CSRF protection"""
        @self.app.before_request
        def check_csrf():
            if request.method in ['POST', 'PUT', 'DELETE', 'PATCH']:
                token = request.form.get('csrf_token') or request.headers.get('X-CSRF-Token')
                if not token or not self.validate_csrf_token(token):
                    return {'error': 'CSRF token validation failed'}, 403
    
    def validate_csrf_token(self, token: str) -> bool:
        """Validate CSRF token"""
        try:
            # Implement proper CSRF token validation
            # This is a simplified example
            expected_token = hashlib.sha256(
                f"{g.get('user_id', 'anonymous')}:{self.app.secret_key}".encode()
            ).hexdigest()
            return secrets.compare_digest(token, expected_token)
        except Exception:
            return False
```

## Compliance & Auditing

### SOC 2 Compliance

```yaml
# compliance/soc2-controls.yml
soc2_controls:
  cc1_control_environment:
    - name: "Security Policies"
      description: "Documented security policies and procedures"
      implementation: "Security policy documentation in /docs/security/"
      evidence: "Policy documents, training records"
      
    - name: "Access Controls"
      description: "Role-based access control implementation"
      implementation: "RBAC in lib/auth.py with Discord integration"
      evidence: "Access logs, role assignments"
      
    - name: "Risk Assessment"
      description: "Regular security risk assessments"
      implementation: "Quarterly security reviews and vulnerability scans"
      evidence: "Risk assessment reports, scan results"

  cc2_communication:
    - name: "Security Awareness"
      description: "Security awareness training for team members"
      implementation: "Monthly security training sessions"
      evidence: "Training materials, completion records"
      
    - name: "Incident Communication"
      description: "Incident response communication procedures"
      implementation: "Incident response playbook in /docs/incident-response/"
      evidence: "Incident reports, communication logs"

  cc3_risk_assessment:
    - name: "Threat Modeling"
      description: "Regular threat modeling exercises"
      implementation: "Quarterly threat modeling sessions"
      evidence: "Threat model documents, mitigation plans"
      
    - name: "Vulnerability Management"
      description: "Continuous vulnerability scanning and remediation"
      implementation: "Automated vulnerability scanning with Nessus/OpenVAS"
      evidence: "Scan reports, remediation tracking"

  cc4_monitoring:
    - name: "Security Monitoring"
      description: "24/7 security monitoring and alerting"
      implementation: "SIEM integration with Splunk/ELK stack"
      evidence: "Monitoring logs, alert configurations"
      
    - name: "Audit Logging"
      description: "Comprehensive audit logging"
      implementation: "Centralized logging with immutable audit trails"
      evidence: "Log retention policies, audit reports"

  cc5_logical_access:
    - name: "User Provisioning"
      description: "Automated user provisioning and deprovisioning"
      implementation: "Identity management with SCIM integration"
      evidence: "Provisioning logs, access reviews"
      
    - name: "Privileged Access"
      description: "Privileged access management"
      implementation: "Just-in-time privileged access with HashiCorp Vault"
      evidence: "Access logs, privilege escalation records"
```

### Audit Logging Implementation

```python
# lib/audit_logger.py
import json
import time
from datetime import datetime
from typing import Dict, Any, Optional
from cryptography.fernet import Fernet
import hashlib

class AuditLogger:
    """Secure audit logging with encryption and integrity verification"""
    
    def __init__(self, encryption_key: bytes, log_file: str = "/var/log/agent-workflow/audit.log"):
        self.fernet = Fernet(encryption_key)
        self.log_file = log_file
        self.sequence_number = 0
        self.last_hash = None
    
    def log_event(self, event_type: str, user_id: str, details: Dict[str, Any], 
                  sensitive_data: Optional[Dict[str, Any]] = None):
        """Log audit event with encryption and chaining"""
        
        # Create audit record
        audit_record = {
            'timestamp': datetime.utcnow().isoformat(),
            'sequence_number': self.sequence_number,
            'event_type': event_type,
            'user_id': user_id,
            'details': details,
            'session_id': details.get('session_id'),
            'ip_address': details.get('ip_address'),
            'user_agent': details.get('user_agent'),
            'previous_hash': self.last_hash
        }
        
        # Encrypt sensitive data if provided
        if sensitive_data:
            encrypted_data = self.fernet.encrypt(json.dumps(sensitive_data).encode())
            audit_record['encrypted_data'] = encrypted_data.decode()
        
        # Calculate hash for integrity
        record_json = json.dumps(audit_record, sort_keys=True)
        current_hash = hashlib.sha256(record_json.encode()).hexdigest()
        audit_record['record_hash'] = current_hash
        
        # Write to log file
        with open(self.log_file, 'a') as f:
            f.write(json.dumps(audit_record) + '\n')
        
        # Update sequence and hash
        self.sequence_number += 1
        self.last_hash = current_hash
    
    def log_authentication(self, user_id: str, success: bool, ip_address: str, 
                          user_agent: str, session_id: str):
        """Log authentication events"""
        self.log_event(
            event_type='authentication',
            user_id=user_id,
            details={
                'success': success,
                'ip_address': ip_address,
                'user_agent': user_agent,
                'session_id': session_id,
                'timestamp': time.time()
            }
        )
    
    def log_authorization(self, user_id: str, resource: str, action: str, 
                         granted: bool, session_id: str):
        """Log authorization events"""
        self.log_event(
            event_type='authorization',
            user_id=user_id,
            details={
                'resource': resource,
                'action': action,
                'granted': granted,
                'session_id': session_id,
                'timestamp': time.time()
            }
        )
    
    def log_data_access(self, user_id: str, data_type: str, operation: str, 
                       record_count: int, session_id: str):
        """Log data access events"""
        self.log_event(
            event_type='data_access',
            user_id=user_id,
            details={
                'data_type': data_type,
                'operation': operation,
                'record_count': record_count,
                'session_id': session_id,
                'timestamp': time.time()
            }
        )
    
    def log_configuration_change(self, user_id: str, component: str, 
                                old_value: str, new_value: str, session_id: str):
        """Log configuration changes"""
        self.log_event(
            event_type='configuration_change',
            user_id=user_id,
            details={
                'component': component,
                'session_id': session_id,
                'timestamp': time.time()
            },
            sensitive_data={
                'old_value': old_value,
                'new_value': new_value
            }
        )
    
    def verify_log_integrity(self) -> bool:
        """Verify audit log integrity"""
        try:
            with open(self.log_file, 'r') as f:
                previous_hash = None
                for line_num, line in enumerate(f, 1):
                    try:
                        record = json.loads(line.strip())
                        
                        # Verify hash chain
                        if previous_hash != record.get('previous_hash'):
                            print(f"Hash chain broken at line {line_num}")
                            return False
                        
                        # Verify record hash
                        record_copy = record.copy()
                        record_hash = record_copy.pop('record_hash')
                        calculated_hash = hashlib.sha256(
                            json.dumps(record_copy, sort_keys=True).encode()
                        ).hexdigest()
                        
                        if record_hash != calculated_hash:
                            print(f"Record hash mismatch at line {line_num}")
                            return False
                        
                        previous_hash = record_hash
                        
                    except json.JSONDecodeError:
                        print(f"Invalid JSON at line {line_num}")
                        return False
                        
            return True
        except Exception as e:
            print(f"Error verifying log integrity: {e}")
            return False

# Global audit logger instance
audit_logger = None

def initialize_audit_logger(encryption_key: bytes):
    """Initialize global audit logger"""
    global audit_logger
    audit_logger = AuditLogger(encryption_key)
```

### Compliance Monitoring

```python
# lib/compliance_monitor.py
import asyncio
import aiohttp
from datetime import datetime, timedelta
from typing import List, Dict, Any
import json

class ComplianceMonitor:
    """Automated compliance monitoring and reporting"""
    
    def __init__(self):
        self.compliance_rules = self.load_compliance_rules()
        self.violations = []
    
    def load_compliance_rules(self) -> List[Dict[str, Any]]:
        """Load compliance rules from configuration"""
        with open('compliance/rules.json', 'r') as f:
            return json.load(f)
    
    async def check_access_controls(self) -> Dict[str, Any]:
        """Check access control compliance"""
        violations = []
        
        # Check for users without MFA
        users_without_mfa = await self.get_users_without_mfa()
        if users_without_mfa:
            violations.append({
                'rule': 'MFA_REQUIRED',
                'severity': 'HIGH',
                'description': 'Users without multi-factor authentication',
                'affected_users': users_without_mfa,
                'remediation': 'Enable MFA for all users'
            })
        
        # Check for excessive privileges
        over_privileged_users = await self.check_excessive_privileges()
        if over_privileged_users:
            violations.append({
                'rule': 'LEAST_PRIVILEGE',
                'severity': 'MEDIUM',
                'description': 'Users with excessive privileges',
                'affected_users': over_privileged_users,
                'remediation': 'Review and reduce user privileges'
            })
        
        return {
            'category': 'access_controls',
            'violations': violations,
            'last_checked': datetime.utcnow().isoformat()
        }
    
    async def check_data_encryption(self) -> Dict[str, Any]:
        """Check data encryption compliance"""
        violations = []
        
        # Check database encryption
        if not await self.verify_database_encryption():
            violations.append({
                'rule': 'DATA_ENCRYPTION_AT_REST',
                'severity': 'HIGH',
                'description': 'Database encryption not enabled',
                'remediation': 'Enable database encryption'
            })
        
        # Check backup encryption
        if not await self.verify_backup_encryption():
            violations.append({
                'rule': 'BACKUP_ENCRYPTION',
                'severity': 'HIGH',
                'description': 'Backup encryption not enabled',
                'remediation': 'Enable backup encryption'
            })
        
        return {
            'category': 'data_encryption',
            'violations': violations,
            'last_checked': datetime.utcnow().isoformat()
        }
    
    async def check_audit_logging(self) -> Dict[str, Any]:
        """Check audit logging compliance"""
        violations = []
        
        # Check log retention
        if not await self.verify_log_retention():
            violations.append({
                'rule': 'LOG_RETENTION',
                'severity': 'MEDIUM',
                'description': 'Audit log retention period not compliant',
                'remediation': 'Configure proper log retention (minimum 1 year)'
            })
        
        # Check log integrity
        if not await self.verify_log_integrity():
            violations.append({
                'rule': 'LOG_INTEGRITY',
                'severity': 'HIGH',
                'description': 'Audit log integrity verification failed',
                'remediation': 'Investigate potential log tampering'
            })
        
        return {
            'category': 'audit_logging',
            'violations': violations,
            'last_checked': datetime.utcnow().isoformat()
        }
    
    async def generate_compliance_report(self) -> Dict[str, Any]:
        """Generate comprehensive compliance report"""
        report = {
            'report_date': datetime.utcnow().isoformat(),
            'compliance_checks': [],
            'overall_status': 'COMPLIANT',
            'total_violations': 0,
            'high_severity_violations': 0,
            'medium_severity_violations': 0,
            'low_severity_violations': 0
        }
        
        # Run all compliance checks
        checks = [
            self.check_access_controls(),
            self.check_data_encryption(),
            self.check_audit_logging()
        ]
        
        results = await asyncio.gather(*checks)
        
        # Aggregate results
        for result in results:
            report['compliance_checks'].append(result)
            
            for violation in result['violations']:
                report['total_violations'] += 1
                severity = violation['severity']
                if severity == 'HIGH':
                    report['high_severity_violations'] += 1
                    report['overall_status'] = 'NON_COMPLIANT'
                elif severity == 'MEDIUM':
                    report['medium_severity_violations'] += 1
                else:
                    report['low_severity_violations'] += 1
        
        return report
    
    async def get_users_without_mfa(self) -> List[str]:
        """Get list of users without MFA enabled"""
        # Implementation would query user database
        # This is a placeholder
        return []
    
    async def check_excessive_privileges(self) -> List[str]:
        """Check for users with excessive privileges"""
        # Implementation would analyze user roles and permissions
        # This is a placeholder
        return []
    
    async def verify_database_encryption(self) -> bool:
        """Verify database encryption is enabled"""
        # Implementation would check database encryption settings
        # This is a placeholder
        return True
    
    async def verify_backup_encryption(self) -> bool:
        """Verify backup encryption is enabled"""
        # Implementation would check backup encryption settings
        # This is a placeholder
        return True
    
    async def verify_log_retention(self) -> bool:
        """Verify log retention compliance"""
        # Implementation would check log retention settings
        # This is a placeholder
        return True
    
    async def verify_log_integrity(self) -> bool:
        """Verify audit log integrity"""
        # Implementation would verify log integrity
        # This is a placeholder
        return True

# Global compliance monitor instance
compliance_monitor = ComplianceMonitor()
```

## Deployment Checklist

### Pre-Deployment Checklist

```markdown
## Pre-Deployment Checklist

### Environment Setup
- [ ] Production environment configured
- [ ] DNS records configured
- [ ] SSL certificates installed and configured
- [ ] Load balancer configured
- [ ] Database servers configured with replication
- [ ] Cache servers configured with clustering
- [ ] Monitoring systems deployed
- [ ] Log aggregation configured
- [ ] Backup systems configured and tested

### Security Configuration
- [ ] Firewall rules configured
- [ ] Security groups configured
- [ ] Secrets management configured
- [ ] Encryption at rest enabled
- [ ] Encryption in transit enabled
- [ ] Access controls configured
- [ ] Audit logging enabled
- [ ] Vulnerability scanning completed
- [ ] Penetration testing completed

### Application Configuration
- [ ] Environment variables configured
- [ ] Database migrations completed
- [ ] Application configuration validated
- [ ] Health checks configured
- [ ] Metrics collection configured
- [ ] Error tracking configured
- [ ] Performance monitoring configured
- [ ] Feature flags configured
- [ ] Rate limiting configured

### Testing & Validation
- [ ] Unit tests passing
- [ ] Integration tests passing
- [ ] End-to-end tests passing
- [ ] Performance tests passing
- [ ] Security tests passing
- [ ] Load testing completed
- [ ] Disaster recovery testing completed
- [ ] Rollback procedures tested
- [ ] Monitoring and alerting tested

### Documentation & Training
- [ ] Deployment documentation updated
- [ ] Runbook documentation updated
- [ ] Incident response procedures documented
- [ ] Team training completed
- [ ] Support documentation updated
- [ ] User documentation updated
- [ ] API documentation updated
- [ ] Compliance documentation updated
```

### Post-Deployment Checklist

```markdown
## Post-Deployment Checklist

### Verification
- [ ] Application is accessible via HTTPS
- [ ] Health checks are passing
- [ ] Database connectivity verified
- [ ] Cache connectivity verified
- [ ] External API connectivity verified
- [ ] SSL certificate validation
- [ ] DNS resolution verified
- [ ] Load balancer health checks passing
- [ ] Monitoring systems receiving data

### Performance Validation
- [ ] Response times within acceptable limits
- [ ] Throughput meets requirements
- [ ] Error rates within acceptable limits
- [ ] Database performance acceptable
- [ ] Cache hit rates acceptable
- [ ] Memory usage within limits
- [ ] CPU usage within limits
- [ ] Disk usage within limits
- [ ] Network usage within limits

### Security Validation
- [ ] Security headers configured correctly
- [ ] HTTPS redirect working
- [ ] Authentication working correctly
- [ ] Authorization working correctly
- [ ] Rate limiting working correctly
- [ ] Input validation working correctly
- [ ] Error handling not exposing sensitive data
- [ ] Audit logging working correctly
- [ ] Security monitoring active

### Monitoring & Alerting
- [ ] Application metrics being collected
- [ ] Infrastructure metrics being collected
- [ ] Log aggregation working
- [ ] Alerting rules configured
- [ ] Notification channels configured
- [ ] Dashboard access verified
- [ ] Escalation procedures tested
- [ ] On-call rotation updated
- [ ] Incident response team notified

### Documentation & Communication
- [ ] Deployment notes documented
- [ ] Known issues documented
- [ ] Rollback procedures documented
- [ ] Stakeholders notified
- [ ] Team briefed on changes
- [ ] Support team briefed
- [ ] Customer communication sent
- [ ] Change management updated
```

## Troubleshooting Guide

### Common Issues and Solutions

```markdown
## Common Production Issues

### High Memory Usage
**Symptoms:** Application becomes slow, OOM errors
**Causes:** Memory leaks, inefficient caching, large datasets
**Solutions:**
- Increase memory limits in Docker/Kubernetes
- Implement memory profiling
- Optimize caching strategies
- Add memory monitoring alerts

### Database Connection Issues
**Symptoms:** Connection timeouts, pool exhaustion
**Causes:** Connection pool misconfiguration, long-running queries
**Solutions:**
- Increase connection pool size
- Optimize slow queries
- Implement connection monitoring
- Add database read replicas

### Redis Connection Issues
**Symptoms:** Cache misses, connection timeouts
**Causes:** Redis server overload, network issues
**Solutions:**
- Scale Redis cluster
- Optimize cache usage patterns
- Implement cache monitoring
- Add Redis Sentinel for high availability

### SSL Certificate Issues
**Symptoms:** Certificate warnings, HTTPS errors
**Causes:** Expired certificates, misconfigured certificates
**Solutions:**
- Implement certificate auto-renewal
- Monitor certificate expiration
- Verify certificate chain
- Update certificate configuration

### Performance Degradation
**Symptoms:** Slow response times, high CPU usage
**Causes:** Inefficient queries, resource contention
**Solutions:**
- Implement performance monitoring
- Optimize database queries
- Scale application horizontally
- Implement caching strategies
```

### Debugging Commands

```bash
# Application debugging
docker logs -f agent-workflow-orchestrator
docker exec -it agent-workflow-orchestrator /bin/bash
docker stats agent-workflow-orchestrator

# Database debugging
docker exec -it agent-workflow-postgres psql -U agent_workflow -d agent_workflow
SELECT * FROM pg_stat_activity WHERE state = 'active';
SELECT * FROM pg_locks WHERE NOT GRANTED;

# Redis debugging
docker exec -it agent-workflow-redis redis-cli
INFO memory
MONITOR
SLOWLOG GET 10

# Network debugging
docker network ls
docker network inspect agent-workflow_agent-network
netstat -tulpn | grep :8080
telnet localhost 8080

# Performance debugging
htop
iotop
iostat -x 1
vmstat 1
```

## Conclusion

This production deployment guide provides comprehensive coverage of enterprise-grade deployment strategies for the AI Agent TDD-Scrum workflow system. The guide includes:

- **Multi-tier deployment options** from hobby to enterprise
- **One-click deployment** to major cloud platforms
- **Interactive cost calculator** for deployment planning
- **Comprehensive security hardening** with compliance features
- **High availability** with disaster recovery procedures
- **Performance optimization** strategies
- **Monitoring and observability** solutions
- **Compliance frameworks** including SOC 2

For additional support or enterprise consulting, contact our team at [enterprise@agent-workflow.com](mailto:enterprise@agent-workflow.com).

<style>
.deployment-picker {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 2rem;
  margin: 2rem 0;
}

.tier-card {
  border: 2px solid #e5e7eb;
  border-radius: 12px;
  padding: 1.5rem;
  background: #f9fafb;
  transition: all 0.3s ease;
}

.tier-card:hover {
  border-color: #3b82f6;
  box-shadow: 0 4px 12px rgba(59, 130, 246, 0.15);
}

.tier-card.startup {
  border-color: #10b981;
  background: linear-gradient(135deg, #ecfdf5 0%, #f0fdf4 100%);
}

.tier-card.enterprise {
  border-color: #8b5cf6;
  background: linear-gradient(135deg, #f3f4f6 0%, #faf7ff 100%);
}

.tier-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1rem;
}

.tier-header h3 {
  margin: 0;
  font-size: 1.25rem;
  font-weight: 600;
}

.price {
  font-size: 1.5rem;
  font-weight: 700;
  color: #1f2937;
}

.price span {
  font-size: 0.875rem;
  font-weight: 400;
  color: #6b7280;
}

.tier-features ul {
  list-style: none;
  padding: 0;
  margin: 0;
}

.tier-features li {
  padding: 0.5rem 0;
  font-size: 0.875rem;
}

.btn-primary {
  display: inline-block;
  background: #3b82f6;
  color: white;
  padding: 0.75rem 1.5rem;
  border-radius: 8px;
  text-decoration: none;
  font-weight: 500;
  text-align: center;
  transition: background-color 0.2s;
}

.btn-primary:hover {
  background: #2563eb;
}

.deploy-buttons {
  display: flex;
  flex-wrap: wrap;
  gap: 1rem;
  margin: 2rem 0;
}

.deploy-btn {
  display: inline-block;
  transition: transform 0.2s;
}

.deploy-btn:hover {
  transform: translateY(-2px);
}

.cost-calculator {
  border: 2px solid #e5e7eb;
  border-radius: 12px;
  padding: 2rem;
  margin: 2rem 0;
  background: #f9fafb;
}

.calculator-inputs {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 1rem;
  margin-bottom: 2rem;
}

.input-group label {
  display: block;
  font-weight: 500;
  margin-bottom: 0.5rem;
}

.input-group input,
.input-group select {
  width: 100%;
  padding: 0.5rem;
  border: 1px solid #d1d5db;
  border-radius: 6px;
  font-size: 0.875rem;
}

.cost-breakdown {
  border-top: 1px solid #e5e7eb;
  padding-top: 1rem;
}

.cost-item {
  display: flex;
  justify-content: space-between;
  padding: 0.5rem 0;
  font-size: 0.875rem;
}

.cost-total {
  display: flex;
  justify-content: space-between;
  padding: 1rem 0;
  border-top: 2px solid #e5e7eb;
  margin-top: 1rem;
  font-size: 1.125rem;
}

.architecture-viewer {
  border: 2px solid #e5e7eb;
  border-radius: 12px;
  margin: 2rem 0;
  background: white;
}

.architecture-tabs {
  display: flex;
  border-bottom: 1px solid #e5e7eb;
}

.tab-btn {
  flex: 1;
  padding: 1rem;
  border: none;
  background: none;
  cursor: pointer;
  font-weight: 500;
  color: #6b7280;
  transition: all 0.2s;
}

.tab-btn.active {
  color: #3b82f6;
  border-bottom: 2px solid #3b82f6;
  background: #f8fafc;
}

.tab-btn:hover {
  background: #f3f4f6;
}

.architecture-content {
  position: relative;
}

.diagram-container {
  display: none;
  padding: 2rem;
}

.diagram-container.active {
  display: block;
}

.diagram-zoom-controls {
  position: absolute;
  top: 1rem;
  right: 1rem;
  display: flex;
  gap: 0.5rem;
  z-index: 10;
}

.zoom-btn {
  width: 2rem;
  height: 2rem;
  border: 1px solid #d1d5db;
  border-radius: 4px;
  background: white;
  cursor: pointer;
  font-weight: bold;
  transition: all 0.2s;
}

.zoom-btn:hover {
  background: #f3f4f6;
  border-color: #9ca3af;
}

.diagram-svg {
  width: 100%;
  height: 500px;
  overflow: hidden;
}

.architecture-svg {
  width: 100%;
  height: 100%;
}

.diagram-node {
  cursor: pointer;
  transition: all 0.2s;
}

.diagram-node:hover {
  opacity: 0.8;
  transform: scale(1.05);
}

.diagram-placeholder {
  text-align: center;
  padding: 4rem 2rem;
  color: #6b7280;
}

.diagram-placeholder h3 {
  margin-bottom: 1rem;
  color: #374151;
}
</style>

<script>
// Cost Calculator Logic
document.addEventListener('DOMContentLoaded', function() {
  const costInputs = document.querySelectorAll('.calculator-inputs input, .calculator-inputs select');
  const costElements = {
    compute: document.getElementById('compute-cost'),
    storage: document.getElementById('storage-cost'),
    network: document.getElementById('network-cost'),
    monitoring: document.getElementById('monitoring-cost'),
    total: document.getElementById('total-cost')
  };
  
  function calculateCosts() {
    const projects = parseInt(document.getElementById('projects').value) || 1;
    const teamSize = parseInt(document.getElementById('team-size').value) || 5;
    const activeHours = parseInt(document.getElementById('active-hours').value) || 8;
    const region = document.getElementById('region').value;
    
    // Regional multipliers
    const regionMultipliers = {
      'us-east-1': 1.0,
      'us-west-2': 1.1,
      'eu-west-1': 1.15,
      'ap-southeast-1': 1.2
    };
    
    const multiplier = regionMultipliers[region] || 1.0;
    
    // Calculate costs
    const computeCost = projects * (20 + (teamSize * 2) + (activeHours * 0.5)) * multiplier;
    const storageCost = projects * (10 + (teamSize * 1)) * multiplier;
    const networkCost = projects * (5 + (teamSize * 0.5)) * multiplier;
    const monitoringCost = projects * (15 + (teamSize * 1)) * multiplier;
    
    const totalCost = computeCost + storageCost + networkCost + monitoringCost;
    
    // Update UI
    if (costElements.compute) costElements.compute.textContent = `$${computeCost.toFixed(2)}`;
    if (costElements.storage) costElements.storage.textContent = `$${storageCost.toFixed(2)}`;
    if (costElements.network) costElements.network.textContent = `$${networkCost.toFixed(2)}`;
    if (costElements.monitoring) costElements.monitoring.textContent = `$${monitoringCost.toFixed(2)}`;
    if (costElements.total) costElements.total.textContent = `$${totalCost.toFixed(2)}`;
  }
  
  // Add event listeners
  costInputs.forEach(input => {
    input.addEventListener('input', calculateCosts);
    input.addEventListener('change', calculateCosts);
  });
  
  // Initial calculation
  calculateCosts();
  
  // Architecture Viewer Logic
  const tabButtons = document.querySelectorAll('.tab-btn');
  const diagramContainers = document.querySelectorAll('.diagram-container');
  
  tabButtons.forEach(button => {
    button.addEventListener('click', function() {
      const tabName = this.getAttribute('data-tab');
      
      // Update active tab
      tabButtons.forEach(btn => btn.classList.remove('active'));
      this.classList.add('active');
      
      // Update active diagram
      diagramContainers.forEach(container => {
        container.classList.remove('active');
        if (container.id === `${tabName}-diagram`) {
          container.classList.add('active');
        }
      });
    });
  });
  
  // Zoom controls
  const zoomButtons = document.querySelectorAll('.zoom-btn');
  
  zoomButtons.forEach(button => {
    button.addEventListener('click', function() {
      const action = this.getAttribute('data-action');
      const svg = this.closest('.diagram-container').querySelector('.architecture-svg');
      
      if (!svg) return;
      
      const currentTransform = svg.style.transform || 'scale(1)';
      const currentScale = parseFloat(currentTransform.match(/scale\(([^)]+)\)/)?.[1] || 1);
      
      let newScale = currentScale;
      
      switch (action) {
        case 'zoom-in':
          newScale = Math.min(currentScale * 1.2, 3);
          break;
        case 'zoom-out':
          newScale = Math.max(currentScale / 1.2, 0.5);
          break;
        case 'reset':
          newScale = 1;
          break;
      }
      
      svg.style.transform = `scale(${newScale})`;
      svg.style.transformOrigin = 'center center';
    });
  });
});
</script>