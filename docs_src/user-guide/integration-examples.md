# Integration Examples & Cookbook

Practical examples and recipes for integrating the AI Agent TDD-Scrum workflow system with various tools, services, and development environments.

## Quick Start Integration Examples

### Basic Project Integration

#### Express.js API Project
Complete setup for a Node.js Express API with TDD workflow.

```yaml
# config/express-api.yml
orchestrator:
  mode: partial
  project_path: "/workspace/express-api"
  
tdd:
  enabled: true
  test_execution:
    runner: "npm test"
    coverage_threshold: 85
    parallel_jobs: 2
    
agents:
  design_agent:
    context: "Express.js REST API with PostgreSQL"
  code_agent:
    implementation_style: "minimal"
  qa_agent:
    test_types: ["unit", "integration", "api"]
```

**Discord Workflow:**
```bash
# Initialize project
/project register /workspace/express-api "Express API"
/epic "User Management API"

# Add stories
/backlog add_story "POST /users endpoint with validation"
/backlog add_story "GET /users/:id endpoint with error handling"
/backlog add_story "PUT /users/:id endpoint with authorization"

# Plan and execute TDD sprint
/sprint plan
/sprint start

# TDD workflow for each story
/tdd start USER-001 "User creation endpoint"
/tdd design    # Creates API specification
/tdd test      # Generates Jest tests
/tdd code      # Implements endpoint
/tdd refactor  # Optimizes code
/tdd commit    # Final integration
```

#### Python Django Project
Django web application with comprehensive TDD coverage.

```yaml
# config/django-web.yml
orchestrator:
  mode: blocking
  project_path: "/workspace/django-app"
  
tdd:
  enabled: true
  test_execution:
    runner: "python manage.py test"
    coverage_threshold: 90
    parallel_jobs: 4
    
  quality_gates:
    code_green_phase:
      require_migrations: true
      validate_models: true
      
integrations:
  ci:
    provider: "github_actions"
    config_file: ".github/workflows/django.yml"
```

**TDD Integration:**
```python
# Generated test structure
# tests/tdd/USER-001/test_user_views.py
from django.test import TestCase, Client
from django.contrib.auth.models import User
import json

class UserViewTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        
    def test_user_registration_valid_data(self):
        """Test user registration with valid data"""
        response = self.client.post('/api/users/', {
            'username': 'testuser',
            'email': 'test@example.com',
            'password': 'securepass123'
        })
        self.assertEqual(response.status_code, 201)
        self.assertTrue(User.objects.filter(username='testuser').exists())
        
    def test_user_registration_invalid_email(self):
        """Test user registration with invalid email"""
        response = self.client.post('/api/users/', {
            'username': 'testuser',
            'email': 'invalid-email',
            'password': 'securepass123'
        })
        self.assertEqual(response.status_code, 400)
```

#### React Frontend Project
React application with component-based TDD.

```yaml
# config/react-frontend.yml
orchestrator:
  mode: partial
  project_path: "/workspace/react-app"
  
tdd:
  enabled: true
  test_execution:
    runner: "npm test -- --coverage"
    coverage_threshold: 80
    
  agents:
    design_agent:
      detail_level: "comprehensive"
      include_diagrams: true
    qa_agent:
      test_types: ["unit", "integration", "e2e"]
      generate_test_data: true
```

**Component TDD Example:**
```javascript
// tests/tdd/USER-PROFILE-001/UserProfile.test.js
import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { UserProfile } from '../../../src/components/UserProfile';

describe('UserProfile Component', () => {
  const mockUser = {
    id: 1,
    name: 'John Doe',
    email: 'john@example.com',
    avatar: 'https://example.com/avatar.jpg'
  };

  test('renders user information correctly', () => {
    render(<UserProfile user={mockUser} />);
    
    expect(screen.getByText('John Doe')).toBeInTheDocument();
    expect(screen.getByText('john@example.com')).toBeInTheDocument();
    expect(screen.getByRole('img')).toHaveAttribute('src', mockUser.avatar);
  });

  test('handles edit mode toggle', async () => {
    render(<UserProfile user={mockUser} />);
    
    const editButton = screen.getByText('Edit Profile');
    fireEvent.click(editButton);
    
    await waitFor(() => {
      expect(screen.getByDisplayValue('John Doe')).toBeInTheDocument();
      expect(screen.getByText('Save Changes')).toBeInTheDocument();
    });
  });
});
```

## CI/CD Integration

### GitHub Actions Integration

#### Complete GitHub Actions Workflow
```yaml
# .github/workflows/agent-workflow.yml
name: AI Agent TDD Workflow

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]

env:
  DISCORD_WEBHOOK: ${{ secrets.DISCORD_WEBHOOK }}
  ORCHESTRATOR_MODE: autonomous

jobs:
  tdd-validation:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Setup Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.9'
        
    - name: Install AI Agent Workflow
      run: |
        pip install -r requirements.txt
        python scripts/orchestrator.py --setup
        
    - name: Validate TDD Cycles
      run: |
        python scripts/tdd_manager.py validate-all
        python scripts/test_preservation.py verify-integrity
        
    - name: Run Preserved Tests
      run: |
        pytest tests/tdd/ --cov=src --cov-report=xml
        
    - name: Upload Coverage
      uses: codecov/codecov-action@v3
      with:
        file: ./coverage.xml
        
    - name: Notify Discord
      if: always()
      run: |
        python scripts/notify_discord.py \
          --webhook $DISCORD_WEBHOOK \
          --status ${{ job.status }} \
          --commit ${{ github.sha }}

  agent-integration:
    runs-on: ubuntu-latest
    needs: tdd-validation
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Start Test Orchestrator
      run: |
        export NO_AGENT_MODE=true
        python scripts/orchestrator.py --health-check
        
    - name: Run Integration Tests
      run: |
        pytest tests/integration/ --tb=short
        
    - name: Performance Benchmarks
      run: |
        python scripts/test_runner.py performance --output-file perf_results.json
        
    - name: Upload Artifacts
      uses: actions/upload-artifact@v3
      with:
        name: test-results
        path: |
          perf_results.json
          logs/
```

#### TDD-Specific GitHub Integration
```python
# scripts/github_tdd_integration.py
import os
import requests
from github import Github
from lib.tdd_models import TDDCycle

class GitHubTDDIntegration:
    def __init__(self, repo_name, token):
        self.github = Github(token)
        self.repo = self.github.get_repo(repo_name)
        
    async def create_tdd_branch(self, story_id):
        """Create dedicated branch for TDD cycle"""
        main_branch = self.repo.get_branch("main")
        branch_name = f"tdd/{story_id.lower()}"
        
        self.repo.create_git_ref(
            ref=f"refs/heads/{branch_name}",
            sha=main_branch.commit.sha
        )
        
        return branch_name
        
    async def create_tdd_pr(self, cycle: TDDCycle):
        """Create PR for completed TDD cycle"""
        branch_name = f"tdd/{cycle.story_id.lower()}"
        
        # Generate PR description
        description = self.generate_pr_description(cycle)
        
        pr = self.repo.create_pull(
            title=f"TDD: {cycle.story_id} - {cycle.description}",
            body=description,
            head=branch_name,
            base="main"
        )
        
        # Add TDD-specific labels
        pr.add_to_labels("tdd-cycle", "needs-review")
        
        return pr
        
    def generate_pr_description(self, cycle: TDDCycle):
        """Generate comprehensive PR description from TDD cycle"""
        return f"""
## TDD Cycle Summary

**Story ID:** {cycle.story_id}
**Description:** {cycle.description}
**Cycle Duration:** {cycle.get_duration_summary()}

## TDD Phases Completed

- ✅ **Design Phase**: Technical specifications created
- ✅ **Test Red Phase**: {len(cycle.get_test_files())} failing tests written
- ✅ **Code Green Phase**: Implementation completed, all tests passing
- ✅ **Refactor Phase**: Code optimized while maintaining green tests

## Test Coverage

- **Test Files Created:** {len(cycle.get_test_files())}
- **Test Coverage:** {cycle.overall_test_coverage:.1f}%
- **Tests Passing:** {cycle.get_passing_test_count()}

## Files Changed

{self.get_files_changed_summary(cycle)}

## Quality Metrics

- **Code Complexity:** {cycle.get_complexity_score()}
- **Technical Debt:** {cycle.get_technical_debt_score()}
- **Performance Impact:** {cycle.get_performance_impact()}

---
*Generated by AI Agent TDD-Scrum Workflow*
"""
```

### GitLab CI Integration

#### GitLab CI Pipeline
```yaml
# .gitlab-ci.yml
stages:
  - validate
  - test
  - deploy
  - notify

variables:
  ORCHESTRATOR_MODE: partial
  TDD_ENABLED: "true"

validate-tdd:
  stage: validate
  script:
    - python scripts/tdd_manager.py validate-all
    - python scripts/config_manager.py validate config/gitlab.yml
  artifacts:
    reports:
      junit: tdd-validation-report.xml

run-preserved-tests:
  stage: test
  script:
    - pytest tests/tdd/ --junitxml=tdd-tests.xml --cov=src
  coverage: '/TOTAL.+ ([0-9]{1,3}%)/'
  artifacts:
    reports:
      junit: tdd-tests.xml
      coverage_report:
        coverage_format: cobertura
        path: coverage.xml

integration-tests:
  stage: test
  services:
    - postgres:13
    - redis:6
  variables:
    NO_AGENT_MODE: "true"
  script:
    - python scripts/orchestrator.py --health-check
    - pytest tests/integration/ --tb=short
  parallel: 3

deploy-review:
  stage: deploy
  environment:
    name: review/$CI_COMMIT_REF_SLUG
    url: https://$CI_COMMIT_REF_SLUG.review.example.com
  script:
    - python scripts/deploy.py review --version $CI_COMMIT_SHA
  only:
    - merge_requests

notify-discord:
  stage: notify
  script:
    - |
      python scripts/notify_discord.py \
        --webhook $DISCORD_WEBHOOK \
        --pipeline-status $CI_PIPELINE_STATUS \
        --commit $CI_COMMIT_SHA \
        --branch $CI_COMMIT_REF_NAME
  when: always
```

### Jenkins Integration

#### Jenkins Pipeline
```groovy
// Jenkinsfile
pipeline {
    agent any
    
    environment {
        DISCORD_WEBHOOK = credentials('discord-webhook')
        ORCHESTRATOR_MODE = 'autonomous'
        NO_AGENT_MODE = 'false'
    }
    
    stages {
        stage('Setup') {
            steps {
                script {
                    sh 'python -m venv .venv'
                    sh '. .venv/bin/activate && pip install -r requirements.txt'
                }
            }
        }
        
        stage('TDD Validation') {
            parallel {
                stage('Validate Cycles') {
                    steps {
                        sh '''
                            . .venv/bin/activate
                            python scripts/tdd_manager.py validate-all
                        '''
                    }
                }
                
                stage('Test Preservation') {
                    steps {
                        sh '''
                            . .venv/bin/activate
                            python scripts/test_preservation.py verify-integrity
                        '''
                    }
                }
            }
        }
        
        stage('Execute Tests') {
            steps {
                sh '''
                    . .venv/bin/activate
                    pytest tests/tdd/ --junitxml=results.xml --cov=src
                '''
            }
            post {
                always {
                    junit 'results.xml'
                    publishHTML([
                        allowMissing: false,
                        alwaysLinkToLastBuild: false,
                        keepAll: true,
                        reportDir: 'htmlcov',
                        reportFiles: 'index.html',
                        reportName: 'Coverage Report'
                    ])
                }
            }
        }
        
        stage('Integration Tests') {
            environment {
                NO_AGENT_MODE = 'true'
            }
            steps {
                sh '''
                    . .venv/bin/activate
                    python scripts/orchestrator.py --health-check
                    pytest tests/integration/
                '''
            }
        }
        
        stage('Deploy') {
            when {
                branch 'main'
            }
            steps {
                script {
                    sh '''
                        . .venv/bin/activate
                        python scripts/deploy.py production --version ${BUILD_NUMBER}
                    '''
                }
            }
        }
    }
    
    post {
        always {
            script {
                sh '''
                    . .venv/bin/activate
                    python scripts/notify_discord.py \
                        --webhook ${DISCORD_WEBHOOK} \
                        --build-status ${currentBuild.result} \
                        --build-number ${BUILD_NUMBER}
                '''
            }
        }
    }
}
```

## Database Integration

### PostgreSQL Integration

#### Database Configuration
```yaml
# config/postgresql.yml
storage:
  type: "postgresql"
  connection:
    host: "localhost"
    port: 5432
    database: "agent_workflow"
    username: "workflow_user"
    password: "${DATABASE_PASSWORD}"
    
  pool:
    min_connections: 5
    max_connections: 20
    
tdd:
  test_execution:
    test_database: "agent_workflow_test"
    isolation_level: "transaction"
```

#### Database Schema Migration
```python
# scripts/setup_postgresql.py
import asyncpg
import asyncio
from lib.storage.postgresql_adapter import PostgreSQLAdapter

async def setup_database():
    """Setup PostgreSQL database for agent workflow"""
    
    # Create database schema
    adapter = PostgreSQLAdapter()
    await adapter.create_schema()
    
    # Create TDD-specific tables
    await adapter.execute_sql("""
        CREATE TABLE IF NOT EXISTS tdd_cycles (
            id VARCHAR(50) PRIMARY KEY,
            story_id VARCHAR(50) NOT NULL,
            current_state VARCHAR(20) NOT NULL,
            started_at TIMESTAMP DEFAULT NOW(),
            completed_at TIMESTAMP,
            metadata JSONB
        );
        
        CREATE TABLE IF NOT EXISTS tdd_tasks (
            id VARCHAR(50) PRIMARY KEY,
            cycle_id VARCHAR(50) REFERENCES tdd_cycles(id),
            description TEXT NOT NULL,
            current_state VARCHAR(20) NOT NULL,
            test_files JSONB,
            source_files JSONB,
            created_at TIMESTAMP DEFAULT NOW()
        );
        
        CREATE TABLE IF NOT EXISTS test_results (
            id SERIAL PRIMARY KEY,
            task_id VARCHAR(50) REFERENCES tdd_tasks(id),
            test_name VARCHAR(200) NOT NULL,
            status VARCHAR(20) NOT NULL,
            execution_time FLOAT,
            output TEXT,
            timestamp TIMESTAMP DEFAULT NOW()
        );
        
        CREATE INDEX idx_tdd_cycles_story_id ON tdd_cycles(story_id);
        CREATE INDEX idx_test_results_task_id ON test_results(task_id);
    """)
    
    print("✅ PostgreSQL database setup complete")

if __name__ == "__main__":
    asyncio.run(setup_database())
```

### MongoDB Integration

#### MongoDB Configuration
```yaml
# config/mongodb.yml
storage:
  type: "mongodb"
  connection:
    uri: "mongodb://localhost:27017/agent_workflow"
    options:
      maxPoolSize: 20
      retryWrites: true
      
  collections:
    tdd_cycles: "tdd_cycles"
    test_results: "test_results"
    agent_logs: "agent_logs"
```

#### MongoDB Document Models
```python
# lib/storage/mongodb_models.py
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime
import uuid

class MongoDBTDDStorage:
    def __init__(self, connection_uri):
        self.client = AsyncIOMotorClient(connection_uri)
        self.db = self.client.agent_workflow
        
    async def save_tdd_cycle(self, cycle):
        """Save TDD cycle to MongoDB"""
        document = {
            "_id": cycle.id,
            "story_id": cycle.story_id,
            "current_state": cycle.current_state.value,
            "tasks": [task.to_dict() for task in cycle.tasks],
            "started_at": cycle.started_at,
            "completed_at": cycle.completed_at,
            "metadata": {
                "total_test_runs": cycle.total_test_runs,
                "total_refactors": cycle.total_refactors,
                "overall_test_coverage": cycle.overall_test_coverage
            },
            "updated_at": datetime.utcnow()
        }
        
        await self.db.tdd_cycles.replace_one(
            {"_id": cycle.id},
            document,
            upsert=True
        )
        
    async def get_active_cycles(self):
        """Get all active TDD cycles"""
        cursor = self.db.tdd_cycles.find({
            "current_state": {"$ne": "COMMIT"},
            "completed_at": None
        })
        
        cycles = []
        async for document in cursor:
            cycle = self.document_to_cycle(document)
            cycles.append(cycle)
            
        return cycles
```

## Cloud Platform Integration

### AWS Integration

#### AWS ECS Deployment
```yaml
# aws/ecs-task-definition.json
{
  "family": "agent-workflow",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "1024",
  "memory": "2048",
  "executionRoleArn": "arn:aws:iam::ACCOUNT:role/ecsTaskExecutionRole",
  "taskRoleArn": "arn:aws:iam::ACCOUNT:role/agent-workflow-task-role",
  "containerDefinitions": [
    {
      "name": "orchestrator",
      "image": "your-registry/agent-workflow:latest",
      "essential": true,
      "portMappings": [
        {
          "containerPort": 8080,
          "protocol": "tcp"
        }
      ],
      "environment": [
        {"name": "ORCHESTRATOR_MODE", "value": "autonomous"},
        {"name": "AWS_REGION", "value": "us-east-1"}
      ],
      "secrets": [
        {
          "name": "DISCORD_BOT_TOKEN",
          "valueFrom": "arn:aws:secretsmanager:us-east-1:ACCOUNT:secret:discord-token"
        }
      ],
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/ecs/agent-workflow",
          "awslogs-region": "us-east-1",
          "awslogs-stream-prefix": "ecs"
        }
      }
    }
  ]
}
```

#### AWS Lambda Integration
```python
# aws/lambda_tdd_processor.py
import json
import boto3
from lib.tdd_models import TDDCycle
from lib.storage.s3_adapter import S3TDDStorage

def lambda_handler(event, context):
    """AWS Lambda function for processing TDD events"""
    
    # Parse SQS message
    for record in event['Records']:
        message = json.loads(record['body'])
        event_type = message['event_type']
        
        if event_type == 'tdd_cycle_completed':
            await process_completed_cycle(message['cycle_id'])
        elif event_type == 'test_results_available':
            await process_test_results(message['task_id'])
            
    return {
        'statusCode': 200,
        'body': json.dumps('TDD events processed successfully')
    }

async def process_completed_cycle(cycle_id):
    """Process completed TDD cycle"""
    storage = S3TDDStorage()
    cycle = await storage.load_cycle(cycle_id)
    
    # Generate completion report
    report = generate_cycle_report(cycle)
    
    # Store in S3
    s3 = boto3.client('s3')
    s3.put_object(
        Bucket='agent-workflow-reports',
        Key=f'tdd-reports/{cycle_id}/completion-report.json',
        Body=json.dumps(report),
        ContentType='application/json'
    )
    
    # Send SNS notification
    sns = boto3.client('sns')
    sns.publish(
        TopicArn='arn:aws:sns:us-east-1:ACCOUNT:tdd-notifications',
        Message=f'TDD Cycle {cycle_id} completed successfully',
        Subject='TDD Cycle Completion'
    )
```

### Google Cloud Platform

#### GCP Cloud Run Deployment
```yaml
# gcp/cloudbuild.yaml
steps:
  # Build the container image
  - name: 'gcr.io/cloud-builders/docker'
    args: ['build', '-t', 'gcr.io/$PROJECT_ID/agent-workflow:$COMMIT_SHA', '.']
    
  # Push the container image to Container Registry
  - name: 'gcr.io/cloud-builders/docker'
    args: ['push', 'gcr.io/$PROJECT_ID/agent-workflow:$COMMIT_SHA']
    
  # Deploy container image to Cloud Run
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
      - '--cpu=2'
      - '--max-instances=10'
      - '--set-env-vars=ORCHESTRATOR_MODE=autonomous'
      - '--set-secrets=DISCORD_BOT_TOKEN=discord-token:latest'

options:
  logging: CLOUD_LOGGING_ONLY
```

#### GCP Pub/Sub Integration
```python
# gcp/pubsub_tdd_handler.py
from google.cloud import pubsub_v1
import json
import asyncio

class PubSubTDDHandler:
    def __init__(self, project_id, subscription_name):
        self.subscriber = pubsub_v1.SubscriberClient()
        self.subscription_path = self.subscriber.subscription_path(
            project_id, subscription_name
        )
        
    def start_listening(self):
        """Start listening for TDD events"""
        flow_control = pubsub_v1.types.FlowControl(max_messages=100)
        
        self.subscriber.subscribe(
            self.subscription_path,
            callback=self.handle_message,
            flow_control=flow_control
        )
        
    def handle_message(self, message):
        """Handle incoming TDD event message"""
        try:
            event = json.loads(message.data.decode('utf-8'))
            
            if event['type'] == 'tdd_state_change':
                asyncio.run(self.process_state_change(event))
            elif event['type'] == 'test_execution_complete':
                asyncio.run(self.process_test_results(event))
                
            message.ack()
            
        except Exception as e:
            print(f"Error processing message: {e}")
            message.nack()
            
    async def process_state_change(self, event):
        """Process TDD state change event"""
        print(f"TDD State Change: {event['cycle_id']} -> {event['new_state']}")
        
        # Update monitoring dashboards
        await self.update_monitoring_metrics(event)
        
        # Send notifications if needed
        if event['new_state'] == 'BLOCKED':
            await self.send_alert(event)
```

## Monitoring & Observability Integration

### Prometheus & Grafana

#### Prometheus Configuration
```yaml
# prometheus/prometheus.yml
global:
  scrape_interval: 15s
  
scrape_configs:
  - job_name: 'agent-workflow'
    static_configs:
      - targets: ['localhost:8000']
    metrics_path: '/metrics'
    scrape_interval: 10s
    
  - job_name: 'tdd-metrics'
    static_configs:
      - targets: ['localhost:8001']
    metrics_path: '/tdd/metrics'
    scrape_interval: 30s

rule_files:
  - "alert_rules.yml"
  
alerting:
  alertmanagers:
    - static_configs:
        - targets:
          - alertmanager:9093
```

#### Custom Metrics Export
```python
# monitoring/prometheus_exporter.py
from prometheus_client import Counter, Histogram, Gauge, start_http_server
import asyncio
import time

class TDDPrometheusExporter:
    def __init__(self):
        # Define TDD-specific metrics
        self.tdd_cycles_total = Counter(
            'tdd_cycles_total',
            'Total number of TDD cycles',
            ['status', 'project']
        )
        
        self.tdd_phase_duration = Histogram(
            'tdd_phase_duration_seconds',
            'Duration of TDD phases',
            ['phase', 'project']
        )
        
        self.active_tdd_cycles = Gauge(
            'active_tdd_cycles',
            'Number of active TDD cycles',
            ['project']
        )
        
        self.test_coverage = Gauge(
            'test_coverage_percentage',
            'Test coverage percentage',
            ['project', 'story_id']
        )
        
    async def export_metrics(self):
        """Export TDD metrics to Prometheus"""
        while True:
            # Update active cycles count
            active_cycles = await self.get_active_cycles()
            for project, count in active_cycles.items():
                self.active_tdd_cycles.labels(project=project).set(count)
                
            # Update coverage metrics
            coverage_data = await self.get_coverage_metrics()
            for project, stories in coverage_data.items():
                for story_id, coverage in stories.items():
                    self.test_coverage.labels(
                        project=project,
                        story_id=story_id
                    ).set(coverage)
                    
            await asyncio.sleep(30)  # Export every 30 seconds
            
    def record_cycle_completion(self, project, status):
        """Record TDD cycle completion"""
        self.tdd_cycles_total.labels(
            status=status,
            project=project
        ).inc()
        
    def record_phase_duration(self, phase, project, duration):
        """Record TDD phase duration"""
        self.tdd_phase_duration.labels(
            phase=phase,
            project=project
        ).observe(duration)

# Start Prometheus metrics server
if __name__ == "__main__":
    exporter = TDDPrometheusExporter()
    start_http_server(8001)
    asyncio.run(exporter.export_metrics())
```

#### Grafana Dashboard Configuration
```json
{
  "dashboard": {
    "title": "AI Agent TDD Workflow",
    "panels": [
      {
        "title": "Active TDD Cycles",
        "type": "stat",
        "targets": [
          {
            "expr": "sum(active_tdd_cycles)",
            "legendFormat": "Active Cycles"
          }
        ]
      },
      {
        "title": "TDD Phase Duration",
        "type": "graph",
        "targets": [
          {
            "expr": "tdd_phase_duration_seconds",
            "legendFormat": "{{phase}} - {{project}}"
          }
        ]
      },
      {
        "title": "Test Coverage by Project",
        "type": "heatmap",
        "targets": [
          {
            "expr": "test_coverage_percentage",
            "legendFormat": "{{project}} - {{story_id}}"
          }
        ]
      },
      {
        "title": "TDD Cycle Success Rate",
        "type": "stat",
        "targets": [
          {
            "expr": "rate(tdd_cycles_total{status=\"completed\"}[1h]) / rate(tdd_cycles_total[1h]) * 100",
            "legendFormat": "Success Rate %"
          }
        ]
      }
    ]
  }
}
```

### ELK Stack Integration

#### Logstash Configuration
```ruby
# logstash/pipeline/agent-workflow.conf
input {
  file {
    path => "/opt/agent-workflow/logs/*.log"
    start_position => "beginning"
    codec => "json"
  }
  
  beats {
    port => 5044
  }
}

filter {
  if [logger_name] == "tdd_state_machine" {
    mutate {
      add_tag => ["tdd"]
    }
    
    if [message] =~ /transition/ {
      grok {
        match => { 
          "message" => "TDD transition: %{WORD:old_state} → %{WORD:new_state} for %{WORD:story_id}"
        }
      }
    }
  }
  
  if [logger_name] == "agent_execution" {
    mutate {
      add_tag => ["agent"]
    }
    
    if [duration] {
      mutate {
        convert => { "duration" => "float" }
      }
    }
  }
}

output {
  elasticsearch {
    hosts => ["elasticsearch:9200"]
    index => "agent-workflow-%{+YYYY.MM.dd}"
  }
  
  if "tdd" in [tags] {
    elasticsearch {
      hosts => ["elasticsearch:9200"]
      index => "tdd-cycles-%{+YYYY.MM.dd}"
    }
  }
}
```

#### Kibana Dashboard Export
```json
{
  "objects": [
    {
      "type": "visualization",
      "id": "tdd-state-transitions",
      "attributes": {
        "title": "TDD State Transitions",
        "visState": {
          "type": "line",
          "params": {
            "grid": {"categoryLines": false, "style": {"color": "#eee"}}
          }
        },
        "kibanaSavedObjectMeta": {
          "searchSourceJSON": {
            "index": "tdd-cycles-*",
            "query": {
              "match": {
                "logger_name": "tdd_state_machine"
              }
            }
          }
        }
      }
    }
  ]
}
```

## Notification Integration

### Slack Integration

#### Slack Bot Configuration
```python
# integrations/slack_bot.py
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler
import asyncio

class SlackTDDBot:
    def __init__(self, bot_token, app_token):
        self.app = App(token=bot_token)
        self.handler = SocketModeHandler(self.app, app_token)
        self.setup_commands()
        
    def setup_commands(self):
        """Setup Slack slash commands"""
        
        @self.app.command("/tdd-status")
        def handle_tdd_status(ack, respond, command):
            ack()
            
            project = command.get('text', '').strip()
            status = asyncio.run(self.get_tdd_status(project))
            
            respond({
                "response_type": "in_channel",
                "blocks": [
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": f"*TDD Status for {project}*\n{status}"
                        }
                    }
                ]
            })
            
        @self.app.command("/tdd-metrics")
        def handle_tdd_metrics(ack, respond, command):
            ack()
            
            metrics = asyncio.run(self.get_tdd_metrics())
            
            respond({
                "response_type": "ephemeral",
                "attachments": [
                    {
                        "color": "good",
                        "title": "TDD Metrics Dashboard",
                        "fields": [
                            {
                                "title": "Active Cycles",
                                "value": str(metrics['active_cycles']),
                                "short": True
                            },
                            {
                                "title": "Avg Cycle Time",
                                "value": f"{metrics['avg_cycle_time']:.1f} min",
                                "short": True
                            }
                        ]
                    }
                ]
            })
            
    async def send_tdd_notification(self, channel, event):
        """Send TDD event notification to Slack"""
        if event['type'] == 'cycle_completed':
            await self.send_cycle_completion(channel, event)
        elif event['type'] == 'cycle_blocked':
            await self.send_cycle_blocked(channel, event)
            
    async def send_cycle_completion(self, channel, event):
        """Send cycle completion notification"""
        cycle = event['cycle']
        
        self.app.client.chat_postMessage(
            channel=channel,
            blocks=[
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"🎉 *TDD Cycle Completed*\n"
                               f"*Story:* {cycle['story_id']}\n"
                               f"*Duration:* {cycle['duration']}\n"
                               f"*Coverage:* {cycle['coverage']:.1f}%"
                    }
                },
                {
                    "type": "actions",
                    "elements": [
                        {
                            "type": "button",
                            "text": {"type": "plain_text", "text": "View Details"},
                            "url": f"https://dashboard.example.com/tdd/{cycle['id']}"
                        }
                    ]
                }
            ]
        )
```

### Microsoft Teams Integration

#### Teams Webhook Integration
```python
# integrations/teams_webhook.py
import aiohttp
import json
from datetime import datetime

class TeamsWebhookNotifier:
    def __init__(self, webhook_url):
        self.webhook_url = webhook_url
        
    async def send_tdd_update(self, event):
        """Send TDD update to Microsoft Teams"""
        card = self.create_adaptive_card(event)
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                self.webhook_url,
                headers={'Content-Type': 'application/json'},
                data=json.dumps(card)
            ) as response:
                return response.status == 200
                
    def create_adaptive_card(self, event):
        """Create Adaptive Card for TDD event"""
        if event['type'] == 'state_transition':
            return {
                "type": "message",
                "attachments": [
                    {
                        "contentType": "application/vnd.microsoft.card.adaptive",
                        "content": {
                            "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
                            "type": "AdaptiveCard",
                            "version": "1.0",
                            "body": [
                                {
                                    "type": "TextBlock",
                                    "text": "TDD State Transition",
                                    "weight": "bolder",
                                    "size": "medium"
                                },
                                {
                                    "type": "FactSet",
                                    "facts": [
                                        {
                                            "title": "Story:",
                                            "value": event['story_id']
                                        },
                                        {
                                            "title": "From:",
                                            "value": event['old_state']
                                        },
                                        {
                                            "title": "To:",
                                            "value": event['new_state']
                                        },
                                        {
                                            "title": "Time:",
                                            "value": datetime.now().strftime('%H:%M:%S')
                                        }
                                    ]
                                }
                            ],
                            "actions": [
                                {
                                    "type": "Action.OpenUrl",
                                    "title": "View Cycle",
                                    "url": f"https://dashboard.example.com/tdd/{event['cycle_id']}"
                                }
                            ]
                        }
                    }
                ]
            }
```

This comprehensive integration guide provides practical examples for connecting the AI Agent TDD-Scrum workflow system with various tools, platforms, and services commonly used in software development workflows.