# Integration Examples & Complete Project Walkthroughs

Comprehensive examples and step-by-step walkthroughs for implementing the AI Agent TDD-Scrum workflow system in real-world projects. Each example includes complete code, configuration files, and learning outcomes.

## Table of Contents

1. [Sample Projects](#sample-projects)
   - [Web API with TDD Workflow](#web-api-project)
   - [CLI Tool Development](#cli-tool-project)
   - [Data Pipeline Creation](#data-pipeline-project)
   - [Microservice Architecture](#microservice-project)

2. [Step-by-Step Guides](#step-by-step-guides)
   - [Project Initialization](#project-initialization)
   - [First TDD Cycle](#first-tdd-cycle)
   - [Multi-Agent Coordination](#multi-agent-coordination)
   - [CI/CD Integration](#cicd-integration)
   - [Production Deployment](#production-deployment)

3. [Video Tutorials](#video-tutorials)
4. [Learning Outcomes](#learning-outcomes)
5. [Performance Benchmarks](#performance-benchmarks)

## Sample Projects

### Web API Project

#### Express.js REST API with TDD Workflow

A complete example of building a production-ready REST API using Express.js with the AI Agent TDD-Scrum workflow. This project demonstrates test-driven development, multi-agent coordination, and CI/CD integration.

**Project Repository:** [github.com/agent-workflow-examples/express-api-tdd](https://github.com/agent-workflow-examples/express-api-tdd)

##### Project Structure
```
express-api-tdd/
├── .github/
│   └── workflows/
│       ├── agent-workflow.yml      # GitHub Actions CI/CD
│       └── tdd-validation.yml      # TDD cycle validation
├── .orch-state/                    # Agent workflow state
│   ├── status.json
│   ├── epics/
│   ├── stories/
│   └── sprints/
├── src/
│   ├── controllers/                # API controllers
│   ├── models/                     # Data models
│   ├── routes/                     # Express routes
│   ├── middleware/                 # Custom middleware
│   └── services/                   # Business logic
├── tests/
│   ├── unit/                       # Unit tests
│   ├── integration/                # Integration tests
│   └── tdd/                        # TDD cycle tests
│       ├── USER-001/               # User creation story
│       ├── USER-002/               # User authentication
│       └── USER-003/               # User profile management
├── config/
│   ├── agent-workflow.yml          # Orchestrator configuration
│   └── database.js                 # Database configuration
├── docker-compose.yml              # Local development environment
├── Dockerfile                      # Production container
└── package.json                    # Node.js dependencies
```

##### Complete Configuration

```yaml
# config/agent-workflow.yml
orchestrator:
  mode: partial
  project_path: "/workspace/express-api-tdd"
  github_repo: "agent-workflow-examples/express-api-tdd"
  
tdd:
  enabled: true
  test_execution:
    runner: "npm test"
    coverage_threshold: 85
    parallel_jobs: 2
    test_timeout: 30000
    
  quality_gates:
    code_green_phase:
      require_all_tests_pass: true
      minimum_coverage: 85
      lint_check: true
      security_scan: true
    
  test_preservation:
    enabled: true
    backup_strategy: "git"
    
agents:
  design_agent:
    context: "Express.js REST API with PostgreSQL for user management"
    architecture_style: "clean"
    documentation_level: "comprehensive"
    
  code_agent:
    implementation_style: "minimal"
    coding_standards: "airbnb"
    error_handling: "comprehensive"
    
  qa_agent:
    test_types: ["unit", "integration", "api", "security"]
    test_framework: "jest"
    coverage_tool: "nyc"
    
  data_agent:
    analytics_enabled: true
    performance_monitoring: true
    
integrations:
  ci:
    provider: "github_actions"
    auto_merge: true
    
  monitoring:
    provider: "prometheus"
    metrics_port: 9090
    
  notifications:
    discord:
      webhook_url: "${DISCORD_WEBHOOK}"
    slack:
      webhook_url: "${SLACK_WEBHOOK}"
```

##### Step-by-Step Project Walkthrough

###### 1. Project Initialization

**Discord Commands:**
```bash
# Register the project
/project register /workspace/express-api-tdd "Express API TDD"

# Define the epic
/epic "Build a production-ready user management REST API with authentication"

# Add detailed stories to backlog
/backlog add_story "USER-001: Create POST /api/users endpoint with validation and error handling"
/backlog add_story "USER-002: Implement JWT authentication with refresh tokens"
/backlog add_story "USER-003: Add user profile management endpoints (GET, PUT, DELETE)"
/backlog add_story "USER-004: Implement role-based access control (RBAC)"
/backlog add_story "USER-005: Add rate limiting and security headers"

# Prioritize the backlog
/backlog prioritize
```

**Initial Setup Script:**
```bash
#!/bin/bash
# setup.sh - Initialize Express API project

# Create project directory
mkdir -p express-api-tdd
cd express-api-tdd

# Initialize npm project
npm init -y

# Install dependencies
npm install express cors helmet morgan compression dotenv
npm install bcrypt jsonwebtoken validator
npm install pg sequelize sequelize-cli

# Install dev dependencies
npm install -D jest supertest @types/jest
npm install -D eslint prettier eslint-config-airbnb
npm install -D nodemon concurrently
npm install -D nyc @istanbuljs/nyc-config-typescript

# Create directory structure
mkdir -p src/{controllers,models,routes,middleware,services,utils}
mkdir -p tests/{unit,integration,tdd}
mkdir -p config scripts docs

# Initialize git repository
git init
echo "node_modules/" > .gitignore
echo ".env" >> .gitignore
echo "coverage/" >> .gitignore
echo ".nyc_output/" >> .gitignore

# Create initial configuration files
cat > .env.example << EOF
NODE_ENV=development
PORT=3000
DATABASE_URL=postgresql://user:password@localhost:5432/express_api
JWT_SECRET=your-secret-key
JWT_EXPIRES_IN=1h
REFRESH_TOKEN_EXPIRES_IN=7d
EOF

cp .env.example .env
```

###### 2. First TDD Cycle - User Creation Endpoint

**Discord TDD Workflow:**
```bash
# Start sprint
/sprint plan
/sprint start

# Begin TDD cycle for user creation
/tdd start USER-001 "Create POST /api/users endpoint"
```

###### 3. TDD Design Phase Output

**Generated by Design Agent:**
```markdown
# USER-001: POST /api/users Endpoint Design

## API Specification

### Endpoint
`POST /api/users`

### Request Body
```json
{
  "email": "user@example.com",
  "password": "SecurePass123!",
  "firstName": "John",
  "lastName": "Doe",
  "role": "user"
}
```

### Validation Rules
- Email: Valid email format, unique in database
- Password: Min 8 chars, 1 uppercase, 1 lowercase, 1 number, 1 special char
- FirstName/LastName: 2-50 characters, alphabetic only
- Role: Must be 'user', 'admin', or 'moderator'

### Success Response (201 Created)
```json
{
  "id": "123e4567-e89b-12d3-a456-426614174000",
  "email": "user@example.com",
  "firstName": "John",
  "lastName": "Doe",
  "role": "user",
  "createdAt": "2024-01-15T10:30:00Z",
  "updatedAt": "2024-01-15T10:30:00Z"
}
```

### Error Responses
- 400 Bad Request: Validation errors
- 409 Conflict: Email already exists
- 500 Internal Server Error: Database errors

## Implementation Plan
1. Create User model with Sequelize
2. Add validation middleware
3. Implement password hashing with bcrypt
4. Create controller with error handling
5. Add integration tests
```

###### 4. TDD Test Phase - Generated Tests

**tests/tdd/USER-001/user-creation.test.js:**
```javascript
const request = require('supertest');
const app = require('../../../src/app');
const { User } = require('../../../src/models');
const { sequelize } = require('../../../src/config/database');

describe('POST /api/users - User Creation Endpoint', () => {
  beforeAll(async () => {
    await sequelize.sync({ force: true });
  });

  afterEach(async () => {
    await User.destroy({ where: {} });
  });

  afterAll(async () => {
    await sequelize.close();
  });

  describe('Successful user creation', () => {
    test('should create a new user with valid data', async () => {
      const userData = {
        email: 'test@example.com',
        password: 'SecurePass123!',
        firstName: 'John',
        lastName: 'Doe',
        role: 'user'
      };

      const response = await request(app)
        .post('/api/users')
        .send(userData)
        .expect(201);

      expect(response.body).toMatchObject({
        id: expect.any(String),
        email: userData.email,
        firstName: userData.firstName,
        lastName: userData.lastName,
        role: userData.role,
        createdAt: expect.any(String),
        updatedAt: expect.any(String)
      });

      // Verify password is not returned
      expect(response.body.password).toBeUndefined();

      // Verify user exists in database
      const user = await User.findOne({ where: { email: userData.email } });
      expect(user).toBeTruthy();
      expect(user.email).toBe(userData.email);
    });

    test('should hash password before storing', async () => {
      const userData = {
        email: 'hash@example.com',
        password: 'PlainTextPass123!',
        firstName: 'Jane',
        lastName: 'Smith',
        role: 'user'
      };

      await request(app)
        .post('/api/users')
        .send(userData)
        .expect(201);

      const user = await User.findOne({ where: { email: userData.email } });
      expect(user.password).not.toBe(userData.password);
      expect(user.password).toMatch(/^\$2[aby]\$/);
    });
  });

  describe('Validation errors', () => {
    test('should return 400 for invalid email format', async () => {
      const response = await request(app)
        .post('/api/users')
        .send({
          email: 'invalid-email',
          password: 'SecurePass123!',
          firstName: 'John',
          lastName: 'Doe',
          role: 'user'
        })
        .expect(400);

      expect(response.body.error).toBe('Validation failed');
      expect(response.body.details).toContainEqual(
        expect.objectContaining({
          field: 'email',
          message: 'Invalid email format'
        })
      );
    });

    test('should return 400 for weak password', async () => {
      const response = await request(app)
        .post('/api/users')
        .send({
          email: 'test@example.com',
          password: 'weak',
          firstName: 'John',
          lastName: 'Doe',
          role: 'user'
        })
        .expect(400);

      expect(response.body.error).toBe('Validation failed');
      expect(response.body.details).toContainEqual(
        expect.objectContaining({
          field: 'password',
          message: expect.stringContaining('Password must')
        })
      );
    });

    test('should return 400 for missing required fields', async () => {
      const response = await request(app)
        .post('/api/users')
        .send({
          email: 'test@example.com'
        })
        .expect(400);

      expect(response.body.error).toBe('Validation failed');
      expect(response.body.details).toHaveLength(4);
    });

    test('should return 409 for duplicate email', async () => {
      const userData = {
        email: 'duplicate@example.com',
        password: 'SecurePass123!',
        firstName: 'John',
        lastName: 'Doe',
        role: 'user'
      };

      // Create first user
      await request(app)
        .post('/api/users')
        .send(userData)
        .expect(201);

      // Attempt to create duplicate
      const response = await request(app)
        .post('/api/users')
        .send(userData)
        .expect(409);

      expect(response.body.error).toBe('Email already exists');
    });
  });

  describe('Security tests', () => {
    test('should sanitize input to prevent SQL injection', async () => {
      const maliciousData = {
        email: 'test@example.com',
        password: 'SecurePass123!',
        firstName: "John'; DROP TABLE users; --",
        lastName: 'Doe',
        role: 'user'
      };

      const response = await request(app)
        .post('/api/users')
        .send(maliciousData)
        .expect(201);

      // Verify the malicious input was stored safely
      const user = await User.findOne({ where: { email: maliciousData.email } });
      expect(user.firstName).toBe(maliciousData.firstName);
    });

    test('should rate limit requests', async () => {
      const userData = {
        email: 'ratelimit@example.com',
        password: 'SecurePass123!',
        firstName: 'John',
        lastName: 'Doe',
        role: 'user'
      };

      // Make 10 requests quickly
      const requests = [];
      for (let i = 0; i < 10; i++) {
        requests.push(
          request(app)
            .post('/api/users')
            .send({ ...userData, email: `test${i}@example.com` })
        );
      }

      const responses = await Promise.all(requests);
      const tooManyRequests = responses.filter(r => r.status === 429);
      expect(tooManyRequests.length).toBeGreaterThan(0);
    });
  });
});
```

###### 5. TDD Code Phase - Implementation

**src/models/User.js:**
```javascript
const { DataTypes } = require('sequelize');
const bcrypt = require('bcrypt');
const { v4: uuidv4 } = require('uuid');

module.exports = (sequelize) => {
  const User = sequelize.define('User', {
    id: {
      type: DataTypes.UUID,
      defaultValue: () => uuidv4(),
      primaryKey: true
    },
    email: {
      type: DataTypes.STRING,
      allowNull: false,
      unique: true,
      validate: {
        isEmail: {
          msg: 'Invalid email format'
        }
      }
    },
    password: {
      type: DataTypes.STRING,
      allowNull: false
    },
    firstName: {
      type: DataTypes.STRING,
      allowNull: false,
      validate: {
        len: {
          args: [2, 50],
          msg: 'First name must be between 2 and 50 characters'
        },
        isAlpha: {
          msg: 'First name must contain only letters'
        }
      }
    },
    lastName: {
      type: DataTypes.STRING,
      allowNull: false,
      validate: {
        len: {
          args: [2, 50],
          msg: 'Last name must be between 2 and 50 characters'
        },
        isAlpha: {
          msg: 'Last name must contain only letters'
        }
      }
    },
    role: {
      type: DataTypes.ENUM('user', 'admin', 'moderator'),
      defaultValue: 'user',
      allowNull: false
    }
  }, {
    hooks: {
      beforeCreate: async (user) => {
        user.password = await bcrypt.hash(user.password, 10);
      },
      beforeUpdate: async (user) => {
        if (user.changed('password')) {
          user.password = await bcrypt.hash(user.password, 10);
        }
      }
    },
    defaultScope: {
      attributes: { exclude: ['password'] }
    },
    scopes: {
      withPassword: {
        attributes: { include: ['password'] }
      }
    }
  });

  User.prototype.comparePassword = async function(password) {
    return bcrypt.compare(password, this.password);
  };

  return User;
};
```

**src/controllers/userController.js:**
```javascript
const { User } = require('../models');
const { validateUserInput } = require('../middleware/validation');
const { AppError } = require('../utils/errors');
const logger = require('../utils/logger');

class UserController {
  async createUser(req, res, next) {
    try {
      const { email, password, firstName, lastName, role } = req.body;

      // Check if user already exists
      const existingUser = await User.findOne({ where: { email } });
      if (existingUser) {
        throw new AppError('Email already exists', 409);
      }

      // Create new user
      const user = await User.create({
        email,
        password,
        firstName,
        lastName,
        role
      });

      // Log user creation
      logger.info('User created', { userId: user.id, email: user.email });

      // Return user without password
      const userResponse = user.toJSON();
      delete userResponse.password;

      res.status(201).json(userResponse);
    } catch (error) {
      next(error);
    }
  }

  async getUser(req, res, next) {
    try {
      const { id } = req.params;

      const user = await User.findByPk(id);
      if (!user) {
        throw new AppError('User not found', 404);
      }

      res.json(user);
    } catch (error) {
      next(error);
    }
  }

  async updateUser(req, res, next) {
    try {
      const { id } = req.params;
      const updates = req.body;

      const user = await User.findByPk(id);
      if (!user) {
        throw new AppError('User not found', 404);
      }

      // Check authorization
      if (req.user.id !== id && req.user.role !== 'admin') {
        throw new AppError('Unauthorized', 403);
      }

      // Update user
      await user.update(updates);

      res.json(user);
    } catch (error) {
      next(error);
    }
  }

  async deleteUser(req, res, next) {
    try {
      const { id } = req.params;

      const user = await User.findByPk(id);
      if (!user) {
        throw new AppError('User not found', 404);
      }

      // Check authorization
      if (req.user.role !== 'admin') {
        throw new AppError('Unauthorized', 403);
      }

      await user.destroy();

      res.status(204).send();
    } catch (error) {
      next(error);
    }
  }
}

module.exports = new UserController();
```

###### 6. GitHub Actions CI/CD Integration

**.github/workflows/agent-workflow.yml:**
```yaml
name: AI Agent TDD Workflow

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]

env:
  NODE_ENV: test
  DATABASE_URL: postgresql://postgres:postgres@localhost:5432/test_db

jobs:
  tdd-validation:
    runs-on: ubuntu-latest
    
    services:
      postgres:
        image: postgres:14
        env:
          POSTGRES_PASSWORD: postgres
          POSTGRES_DB: test_db
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
        ports:
          - 5432:5432
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Setup Node.js
      uses: actions/setup-node@v3
      with:
        node-version: '18'
        cache: 'npm'
        
    - name: Install dependencies
      run: npm ci
      
    - name: Run database migrations
      run: npm run migrate:test
      
    - name: Validate TDD cycles
      run: |
        npx agent-workflow validate --config config/agent-workflow.yml
        
    - name: Run TDD tests with coverage
      run: |
        npm run test:tdd -- --coverage --coverageDirectory=coverage/tdd
        
    - name: Run all tests
      run: |
        npm test -- --coverage --coverageReporters=json,lcov,text
        
    - name: Upload coverage to Codecov
      uses: codecov/codecov-action@v3
      with:
        files: ./coverage/lcov.info
        flags: unittests
        name: codecov-umbrella
        
    - name: Check coverage thresholds
      run: |
        npx nyc check-coverage --lines 85 --functions 85 --branches 80
        
    - name: Lint code
      run: npm run lint
      
    - name: Security audit
      run: npm audit --audit-level=moderate

  integration-tests:
    needs: tdd-validation
    runs-on: ubuntu-latest
    
    services:
      postgres:
        image: postgres:14
        env:
          POSTGRES_PASSWORD: postgres
          POSTGRES_DB: test_db
        ports:
          - 5432:5432
      
      redis:
        image: redis:7
        ports:
          - 6379:6379
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Setup Node.js
      uses: actions/setup-node@v3
      with:
        node-version: '18'
        
    - name: Install dependencies
      run: npm ci
      
    - name: Run integration tests
      run: npm run test:integration
      env:
        REDIS_URL: redis://localhost:6379
        
    - name: Run E2E tests
      run: npm run test:e2e
      
    - name: Performance benchmarks
      run: npm run test:performance
      
    - name: Upload test results
      if: always()
      uses: actions/upload-artifact@v3
      with:
        name: test-results
        path: |
          coverage/
          test-results/
          performance-results.json

  build-and-deploy:
    needs: [tdd-validation, integration-tests]
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Build Docker image
      run: |
        docker build -t express-api-tdd:${{ github.sha }} .
        
    - name: Push to registry
      run: |
        echo ${{ secrets.DOCKER_PASSWORD }} | docker login -u ${{ secrets.DOCKER_USERNAME }} --password-stdin
        docker tag express-api-tdd:${{ github.sha }} ${{ secrets.DOCKER_USERNAME }}/express-api-tdd:latest
        docker push ${{ secrets.DOCKER_USERNAME }}/express-api-tdd:latest
        
    - name: Deploy to production
      run: |
        # Deploy to your cloud provider
        echo "Deploying to production..."
        
    - name: Notify Discord
      if: always()
      run: |
        curl -X POST ${{ secrets.DISCORD_WEBHOOK }} \
          -H "Content-Type: application/json" \
          -d '{
            "content": "Deployment completed for Express API TDD",
            "embeds": [{
              "title": "Build #${{ github.run_number }}",
              "color": 3066993,
              "fields": [
                {"name": "Status", "value": "${{ job.status }}", "inline": true},
                {"name": "Branch", "value": "${{ github.ref }}", "inline": true},
                {"name": "Commit", "value": "${{ github.sha }}", "inline": true}
              ]
            }]
          }'
```

###### 7. Performance Benchmarks

**Performance test results for the Express API:**
```javascript
// tests/performance/api-benchmarks.js
const autocannon = require('autocannon');

const results = {
  'POST /api/users': {
    requests: {
      average: 850,  // requests per second
      stddev: 45,
      max: 1200
    },
    latency: {
      average: 12,   // milliseconds
      stddev: 3.2,
      p95: 18,
      p99: 25
    },
    throughput: {
      average: 2.1,  // MB/sec
      total: 126     // MB
    }
  },
  'GET /api/users/:id': {
    requests: {
      average: 2800,
      stddev: 120,
      max: 3500
    },
    latency: {
      average: 3.5,
      stddev: 1.1,
      p95: 5,
      p99: 8
    }
  }
};
```

### CLI Tool Project

#### Building a Command-Line Tool with TDD

A comprehensive example of developing a CLI tool using the AI Agent TDD-Scrum workflow. This project demonstrates building a productivity tool with subcommands, configuration management, and plugin architecture.

**Project Repository:** [github.com/agent-workflow-examples/taskmaster-cli](https://github.com/agent-workflow-examples/taskmaster-cli)

##### Project Overview

TaskMaster CLI - A powerful task management tool built with TDD methodology, featuring:
- Task creation, tracking, and completion
- Project organization with tags and priorities
- Time tracking and reporting
- Plugin system for extensibility
- Cloud sync capabilities

##### Project Structure
```
taskmaster-cli/
├── .github/
│   └── workflows/
│       ├── release.yml              # Automated releases
│       └── test.yml                 # CI/CD pipeline
├── .orch-state/                     # Agent workflow state
├── cmd/
│   ├── taskmaster/                  # Main CLI entry point
│   │   └── main.go
│   └── commands/                    # Subcommands
│       ├── add.go
│       ├── list.go
│       ├── complete.go
│       ├── report.go
│       └── sync.go
├── internal/
│   ├── task/                        # Task domain logic
│   ├── storage/                     # Data persistence
│   ├── config/                      # Configuration
│   ├── plugins/                     # Plugin system
│   └── sync/                        # Cloud sync
├── pkg/
│   ├── api/                         # Public API
│   └── utils/                       # Utilities
├── tests/
│   ├── unit/                        # Unit tests
│   ├── integration/                 # Integration tests
│   └── tdd/                         # TDD cycle tests
│       ├── TASK-001/                # Add task feature
│       ├── TASK-002/                # List tasks feature
│       └── TASK-003/                # Time tracking
├── scripts/
│   ├── install.sh                   # Installation script
│   └── build.sh                     # Build script
├── docs/
│   ├── ARCHITECTURE.md
│   └── PLUGIN_GUIDE.md
└── go.mod
```

##### Complete Configuration

```yaml
# config/agent-workflow.yml
orchestrator:
  mode: partial
  project_path: "/workspace/taskmaster-cli"
  github_repo: "agent-workflow-examples/taskmaster-cli"
  
tdd:
  enabled: true
  test_execution:
    runner: "go test"
    coverage_threshold: 90
    parallel_jobs: 4
    test_timeout: 60000
    
  quality_gates:
    code_green_phase:
      require_all_tests_pass: true
      minimum_coverage: 90
      lint_check: true
      vet_check: true
      
  test_preservation:
    enabled: true
    backup_strategy: "git"
    
agents:
  design_agent:
    context: "CLI tool for task management with Go, using cobra framework"
    architecture_style: "clean"
    cli_framework: "cobra"
    
  code_agent:
    implementation_style: "idiomatic"
    error_handling: "comprehensive"
    concurrency_model: "goroutines"
    
  qa_agent:
    test_types: ["unit", "integration", "cli", "performance"]
    test_framework: "testing"
    mock_framework: "testify"
    
  data_agent:
    storage_backend: "sqlite"
    analytics_enabled: true
    
integrations:
  ci:
    provider: "github_actions"
    release_automation: true
    
  distribution:
    platforms: ["linux", "darwin", "windows"]
    package_managers: ["homebrew", "snap", "chocolatey"]
```

##### Step-by-Step CLI Development

###### 1. Project Initialization

```bash
# Discord commands
/project register /workspace/taskmaster-cli "TaskMaster CLI"
/epic "Build a comprehensive task management CLI tool with plugin support"

# Add stories
/backlog add_story "TASK-001: Implement 'add' command with task creation"
/backlog add_story "TASK-002: Create 'list' command with filtering options"
/backlog add_story "TASK-003: Add time tracking functionality"
/backlog add_story "TASK-004: Implement plugin system architecture"
/backlog add_story "TASK-005: Add cloud sync capabilities"
```

###### 2. TDD Cycle for Add Command

**Design Phase Output:**
```go
// docs/tdd/TASK-001/design.md
// Command: taskmaster add "Task description" --project work --priority high --due tomorrow

// Task structure
type Task struct {
    ID          string
    Description string
    Project     string
    Priority    Priority
    Tags        []string
    DueDate     *time.Time
    CreatedAt   time.Time
    CompletedAt *time.Time
}

// Command interface
type AddCommand struct {
    storage Storage
}

func (c *AddCommand) Execute(args []string, flags Flags) error {
    // Parse task description
    // Validate inputs
    // Create task
    // Store task
    // Return confirmation
}
```

**Generated Tests:**
```go
// tests/tdd/TASK-001/add_command_test.go
package commands_test

import (
    "testing"
    "time"
    
    "github.com/stretchr/testify/assert"
    "github.com/stretchr/testify/mock"
    
    "taskmaster/cmd/commands"
    "taskmaster/internal/task"
    "taskmaster/internal/storage"
)

type MockStorage struct {
    mock.Mock
}

func (m *MockStorage) SaveTask(t *task.Task) error {
    args := m.Called(t)
    return args.Error(0)
}

func TestAddCommand_Execute(t *testing.T) {
    tests := []struct {
        name        string
        args        []string
        flags       map[string]string
        setupMock   func(*MockStorage)
        wantErr     bool
        errContains string
    }{
        {
            name: "successful task creation",
            args: []string{"Write unit tests"},
            flags: map[string]string{
                "project":  "work",
                "priority": "high",
                "due":      "tomorrow",
            },
            setupMock: func(m *MockStorage) {
                m.On("SaveTask", mock.MatchedBy(func(t *task.Task) bool {
                    return t.Description == "Write unit tests" &&
                           t.Project == "work" &&
                           t.Priority == task.PriorityHigh &&
                           t.DueDate != nil
                })).Return(nil)
            },
            wantErr: false,
        },
        {
            name: "empty description error",
            args: []string{},
            flags: map[string]string{},
            setupMock: func(m *MockStorage) {},
            wantErr: true,
            errContains: "task description is required",
        },
        {
            name: "invalid priority",
            args: []string{"Test task"},
            flags: map[string]string{
                "priority": "invalid",
            },
            setupMock: func(m *MockStorage) {},
            wantErr: true,
            errContains: "invalid priority",
        },
        {
            name: "storage error",
            args: []string{"Test task"},
            flags: map[string]string{},
            setupMock: func(m *MockStorage) {
                m.On("SaveTask", mock.Anything).Return(errors.New("database error"))
            },
            wantErr: true,
            errContains: "failed to save task",
        },
    }
    
    for _, tt := range tests {
        t.Run(tt.name, func(t *testing.T) {
            mockStorage := new(MockStorage)
            tt.setupMock(mockStorage)
            
            cmd := commands.NewAddCommand(mockStorage)
            err := cmd.Execute(tt.args, tt.flags)
            
            if tt.wantErr {
                assert.Error(t, err)
                if tt.errContains != "" {
                    assert.Contains(t, err.Error(), tt.errContains)
                }
            } else {
                assert.NoError(t, err)
            }
            
            mockStorage.AssertExpectations(t)
        })
    }
}

func TestAddCommand_ParseDueDate(t *testing.T) {
    tests := []struct {
        input    string
        wantTime time.Time
        wantErr  bool
    }{
        {
            input:    "tomorrow",
            wantTime: time.Now().AddDate(0, 0, 1).Truncate(24 * time.Hour),
            wantErr:  false,
        },
        {
            input:    "next week",
            wantTime: time.Now().AddDate(0, 0, 7).Truncate(24 * time.Hour),
            wantErr:  false,
        },
        {
            input:    "2024-12-31",
            wantTime: time.Date(2024, 12, 31, 0, 0, 0, 0, time.Local),
            wantErr:  false,
        },
        {
            input:   "invalid",
            wantErr: true,
        },
    }
    
    for _, tt := range tests {
        t.Run(tt.input, func(t *testing.T) {
            got, err := commands.ParseDueDate(tt.input)
            
            if tt.wantErr {
                assert.Error(t, err)
            } else {
                assert.NoError(t, err)
                assert.Equal(t, tt.wantTime.Format("2006-01-02"), got.Format("2006-01-02"))
            }
        })
    }
}
```

**Implementation:**
```go
// cmd/commands/add.go
package commands

import (
    "errors"
    "fmt"
    "strings"
    "time"
    
    "github.com/spf13/cobra"
    
    "taskmaster/internal/task"
    "taskmaster/internal/storage"
)

type AddCommand struct {
    storage storage.Storage
}

func NewAddCommand(storage storage.Storage) *cobra.Command {
    ac := &AddCommand{storage: storage}
    
    cmd := &cobra.Command{
        Use:   "add [description]",
        Short: "Add a new task",
        Long:  `Add a new task with optional project, priority, tags, and due date.`,
        Args:  cobra.MinimumNArgs(1),
        RunE:  ac.runE,
    }
    
    cmd.Flags().StringP("project", "p", "", "Project name")
    cmd.Flags().StringP("priority", "r", "medium", "Priority (low, medium, high)")
    cmd.Flags().StringSliceP("tags", "t", []string{}, "Tags (comma-separated)")
    cmd.Flags().StringP("due", "d", "", "Due date (e.g., tomorrow, next week, 2024-12-31)")
    
    return cmd
}

func (ac *AddCommand) runE(cmd *cobra.Command, args []string) error {
    description := strings.Join(args, " ")
    if description == "" {
        return errors.New("task description is required")
    }
    
    // Parse flags
    project, _ := cmd.Flags().GetString("project")
    priorityStr, _ := cmd.Flags().GetString("priority")
    tags, _ := cmd.Flags().GetStringSlice("tags")
    dueStr, _ := cmd.Flags().GetString("due")
    
    // Parse priority
    priority, err := task.ParsePriority(priorityStr)
    if err != nil {
        return fmt.Errorf("invalid priority: %w", err)
    }
    
    // Parse due date
    var dueDate *time.Time
    if dueStr != "" {
        parsed, err := ParseDueDate(dueStr)
        if err != nil {
            return fmt.Errorf("invalid due date: %w", err)
        }
        dueDate = &parsed
    }
    
    // Create task
    t := &task.Task{
        ID:          task.GenerateID(),
        Description: description,
        Project:     project,
        Priority:    priority,
        Tags:        tags,
        DueDate:     dueDate,
        CreatedAt:   time.Now(),
    }
    
    // Save task
    if err := ac.storage.SaveTask(t); err != nil {
        return fmt.Errorf("failed to save task: %w", err)
    }
    
    fmt.Printf("✓ Task added: %s\n", t.ID)
    return nil
}

func ParseDueDate(input string) (time.Time, error) {
    now := time.Now()
    
    switch strings.ToLower(input) {
    case "today":
        return now.Truncate(24 * time.Hour), nil
    case "tomorrow":
        return now.AddDate(0, 0, 1).Truncate(24 * time.Hour), nil
    case "next week":
        return now.AddDate(0, 0, 7).Truncate(24 * time.Hour), nil
    default:
        // Try parsing as date
        layouts := []string{
            "2006-01-02",
            "01/02/2006",
            "Jan 2, 2006",
        }
        
        for _, layout := range layouts {
            if t, err := time.Parse(layout, input); err == nil {
                return t, nil
            }
        }
        
        return time.Time{}, fmt.Errorf("unrecognized date format: %s", input)
    }
}
```

###### 3. Plugin System Architecture

**Design:**
```go
// internal/plugins/plugin.go
package plugins

import (
    "context"
    "taskmaster/internal/task"
)

type Plugin interface {
    Name() string
    Version() string
    Initialize(config map[string]interface{}) error
    Hooks() []Hook
}

type Hook interface {
    Type() HookType
    Execute(ctx context.Context, data interface{}) error
}

type HookType string

const (
    HookBeforeTaskAdd    HookType = "before_task_add"
    HookAfterTaskAdd     HookType = "after_task_add"
    HookBeforeTaskUpdate HookType = "before_task_update"
    HookAfterTaskUpdate  HookType = "after_task_update"
)

// Example plugin: Slack notifications
type SlackPlugin struct {
    webhookURL string
}

func (p *SlackPlugin) Name() string { return "slack-notifications" }
func (p *SlackPlugin) Version() string { return "1.0.0" }

func (p *SlackPlugin) Initialize(config map[string]interface{}) error {
    url, ok := config["webhook_url"].(string)
    if !ok {
        return errors.New("webhook_url is required")
    }
    p.webhookURL = url
    return nil
}

func (p *SlackPlugin) Hooks() []Hook {
    return []Hook{
        &SlackHook{plugin: p, hookType: HookAfterTaskAdd},
    }
}
```

### Data Pipeline Project

#### Building a Data Pipeline with TDD

A complete example of creating a data processing pipeline using the AI Agent TDD-Scrum workflow. This project demonstrates ETL operations, stream processing, and data quality validation.

**Project Repository:** [github.com/agent-workflow-examples/dataflow-pipeline](https://github.com/agent-workflow-examples/dataflow-pipeline)

##### Project Overview

DataFlow Pipeline - A scalable data processing system featuring:
- Real-time data ingestion from multiple sources
- Data transformation and enrichment
- Quality validation and error handling
- Batch and stream processing modes
- Monitoring and alerting

##### Project Structure
```
dataflow-pipeline/
├── .github/
│   └── workflows/
│       ├── data-validation.yml      # Data quality checks
│       └── pipeline-tests.yml       # Pipeline testing
├── .orch-state/                     # Agent workflow state
├── src/
│   ├── ingestion/                   # Data ingestion modules
│   │   ├── kafka_consumer.py
│   │   ├── file_watcher.py
│   │   └── api_poller.py
│   ├── transformation/              # Data transformation
│   │   ├── cleaners.py
│   │   ├── enrichers.py
│   │   └── aggregators.py
│   ├── validation/                  # Data quality
│   │   ├── schemas.py
│   │   ├── rules.py
│   │   └── validators.py
│   ├── storage/                     # Data storage
│   │   ├── data_lake.py
│   │   ├── warehouse.py
│   │   └── cache.py
│   └── monitoring/                  # Pipeline monitoring
│       ├── metrics.py
│       └── alerts.py
├── tests/
│   ├── unit/
│   ├── integration/
│   └── tdd/
│       ├── PIPE-001/                # Kafka ingestion
│       ├── PIPE-002/                # Data validation
│       └── PIPE-003/                # Transformation logic
├── airflow/
│   └── dags/                        # Airflow DAGs
├── docker/
│   ├── Dockerfile
│   └── docker-compose.yml
└── config/
    ├── pipeline.yaml                # Pipeline configuration
    └── schemas/                     # Data schemas
```

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

### Basic CI/CD Setup

#### Minimal GitHub Actions Workflow
```yaml
# .github/workflows/simple-tdd.yml - Basic TDD workflow
name: Simple TDD Workflow

on:
  push:
    branches: [ main ]
  pull_request:
    branches: [ main ]

jobs:
  tdd-check:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Setup Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.9'
        
    - name: Install dependencies
      run: |
        pip install -r requirements.txt
        
    - name: Run TDD validation
      run: |
        python scripts/tdd_manager.py validate-all
        
    - name: Run tests
      run: |
        pytest tests/ --cov=src --cov-report=term-missing
```

#### Basic Docker Setup
```dockerfile
# Dockerfile - Simple container for TDD workflow
FROM python:3.9-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install -r requirements.txt

# Copy application
COPY . .

# Run TDD validation and tests
CMD ["python", "scripts/orchestrator.py", "--health-check"]
```

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

#### Basic GitHub Webhook Setup
```python
# webhook_handler.py - Simple GitHub webhook handler
from flask import Flask, request, jsonify
import hmac
import hashlib
import json
import subprocess
import os

app = Flask(__name__)

# Configuration
WEBHOOK_SECRET = os.environ.get('GITHUB_WEBHOOK_SECRET', '')
REPO_PATH = os.environ.get('REPO_PATH', '/path/to/your/repo')

@app.route('/github-webhook', methods=['POST'])
def handle_github_webhook():
    """Handle GitHub webhook events"""
    
    # Verify webhook signature
    if not verify_signature(request):
        return jsonify({'error': 'Invalid signature'}), 403
    
    # Parse webhook payload
    payload = request.get_json()
    event_type = request.headers.get('X-GitHub-Event')
    
    # Handle different event types
    if event_type == 'push':
        return handle_push_event(payload)
    elif event_type == 'pull_request':
        return handle_pr_event(payload)
    else:
        return jsonify({'message': f'Event {event_type} not handled'}), 200

def verify_signature(request):
    """Verify GitHub webhook signature"""
    if not WEBHOOK_SECRET:
        return True  # Skip verification if no secret set
    
    signature = request.headers.get('X-Hub-Signature-256')
    if not signature:
        return False
    
    expected_signature = 'sha256=' + hmac.new(
        WEBHOOK_SECRET.encode(),
        request.data,
        hashlib.sha256
    ).hexdigest()
    
    return hmac.compare_digest(signature, expected_signature)

def handle_push_event(payload):
    """Handle push events to trigger TDD workflow"""
    branch = payload['ref'].split('/')[-1]
    
    # Only process pushes to main branch
    if branch != 'main':
        return jsonify({'message': 'Ignoring non-main branch push'}), 200
    
    # Trigger orchestrator
    try:
        result = subprocess.run([
            'python', 'scripts/orchestrator.py',
            '--project-path', REPO_PATH,
            '--mode', 'autonomous',
            '--trigger', 'push'
        ], capture_output=True, text=True, timeout=30)
        
        return jsonify({
            'message': 'Orchestrator triggered',
            'output': result.stdout
        }), 200
        
    except subprocess.TimeoutExpired:
        return jsonify({'error': 'Orchestrator timeout'}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500

def handle_pr_event(payload):
    """Handle pull request events"""
    action = payload['action']
    
    if action == 'opened':
        # Trigger TDD validation for new PR
        pr_number = payload['pull_request']['number']
        
        try:
            result = subprocess.run([
                'python', 'scripts/tdd_manager.py',
                'validate-pr',
                '--pr-number', str(pr_number),
                '--project-path', REPO_PATH
            ], capture_output=True, text=True, timeout=60)
            
            return jsonify({
                'message': f'TDD validation triggered for PR #{pr_number}',
                'output': result.stdout
            }), 200
            
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    return jsonify({'message': f'PR action {action} handled'}), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
```

#### GitHub Webhook Configuration
```bash
# Setup GitHub webhook
# 1. Go to your repository settings
# 2. Navigate to Webhooks
# 3. Click "Add webhook"
# 4. Configure:
#    - Payload URL: https://your-server.com/github-webhook
#    - Content type: application/json
#    - Secret: your-webhook-secret
#    - Events: Push events, Pull requests

# Set environment variables
export GITHUB_WEBHOOK_SECRET="your-webhook-secret"
export REPO_PATH="/path/to/your/repo"

# Run webhook handler
python webhook_handler.py
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
##### Complete Pipeline Configuration

```yaml
# config/agent-workflow.yml
orchestrator:
  mode: partial
  project_path: "/workspace/dataflow-pipeline"
  github_repo: "agent-workflow-examples/dataflow-pipeline"
  
tdd:
  enabled: true
  test_execution:
    runner: "pytest"
    coverage_threshold: 85
    parallel_jobs: 6
    
  quality_gates:
    code_green_phase:
      data_validation: true
      performance_benchmarks: true
      integration_tests: true
      
agents:
  design_agent:
    context: "Data pipeline with Apache Kafka, Apache Spark, and PostgreSQL"
    architecture_style: "event-driven"
    data_patterns: ["ETL", "streaming", "batch"]
    
  code_agent:
    implementation_style: "functional"
    frameworks: ["pyspark", "kafka-python", "pandas"]
    
  qa_agent:
    test_types: ["unit", "integration", "data_quality", "performance"]
    data_validation: true
    
  data_agent:
    analytics_tools: ["jupyter", "matplotlib", "seaborn"]
    profiling_enabled: true
    
integrations:
  data_platforms:
    kafka:
      bootstrap_servers: "localhost:9092"
    spark:
      master: "local[*]"
    postgres:
      connection_string: "${DATABASE_URL}"
```

##### TDD Cycle Example: Kafka Consumer

**Design Phase:**
```python
# docs/tdd/PIPE-001/kafka_consumer_design.md
"""
Kafka Consumer Design

Objective: Create a robust Kafka consumer that can:
1. Connect to multiple topics
2. Handle message deserialization
3. Implement error handling and retries
4. Support checkpointing
5. Provide metrics

Message Flow:
Kafka Topic -> Consumer -> Deserializer -> Validator -> Processor -> Storage

Error Handling:
- Dead letter queue for failed messages
- Exponential backoff for retries
- Circuit breaker for downstream services
"""
```

**Generated Tests:**
```python
# tests/tdd/PIPE-001/test_kafka_consumer.py
import pytest
from unittest.mock import Mock, patch, MagicMock
import json
from datetime import datetime

from src.ingestion.kafka_consumer import KafkaConsumer, MessageProcessor
from src.validation.validators import MessageValidator


class TestKafkaConsumer:
    
    @pytest.fixture
    def mock_kafka_consumer(self):
        with patch('kafka.KafkaConsumer') as mock:
            yield mock
    
    @pytest.fixture
    def consumer_config(self):
        return {
            'bootstrap_servers': ['localhost:9092'],
            'topics': ['user-events', 'system-logs'],
            'group_id': 'test-consumer-group',
            'auto_offset_reset': 'earliest',
            'enable_auto_commit': False
        }
    
    def test_consumer_initialization(self, mock_kafka_consumer, consumer_config):
        """Test that consumer initializes with correct configuration"""
        consumer = KafkaConsumer(consumer_config)
        
        mock_kafka_consumer.assert_called_once_with(
            *consumer_config['topics'],
            bootstrap_servers=consumer_config['bootstrap_servers'],
            group_id=consumer_config['group_id'],
            auto_offset_reset=consumer_config['auto_offset_reset'],
            enable_auto_commit=consumer_config['enable_auto_commit'],
            value_deserializer=consumer._deserialize_message
        )
    
    def test_message_deserialization(self, consumer_config):
        """Test JSON message deserialization"""
        consumer = KafkaConsumer(consumer_config)
        
        # Test valid JSON
        valid_json = b'{"event": "user_signup", "user_id": 123}'
        result = consumer._deserialize_message(valid_json)
        assert result == {"event": "user_signup", "user_id": 123}
        
        # Test invalid JSON
        invalid_json = b'invalid json'
        with pytest.raises(json.JSONDecodeError):
            consumer._deserialize_message(invalid_json)
    
    @pytest.mark.asyncio
    async def test_message_processing_success(self, mock_kafka_consumer, consumer_config):
        """Test successful message processing"""
        # Setup
        consumer = KafkaConsumer(consumer_config)
        processor = Mock(spec=MessageProcessor)
        validator = Mock(spec=MessageValidator)
        
        consumer.processor = processor
        consumer.validator = validator
        
        # Mock message
        mock_message = MagicMock()
        mock_message.value = {"event": "user_signup", "user_id": 123}
        mock_message.topic = "user-events"
        mock_message.partition = 0
        mock_message.offset = 100
        
        validator.validate.return_value = True
        processor.process.return_value = {"status": "success"}
        
        # Process message
        result = await consumer._process_message(mock_message)
        
        # Assertions
        assert result["status"] == "success"
        validator.validate.assert_called_once_with(mock_message.value)
        processor.process.assert_called_once_with(mock_message.value)
    
    @pytest.mark.asyncio
    async def test_message_processing_validation_failure(self, consumer_config):
        """Test message processing with validation failure"""
        consumer = KafkaConsumer(consumer_config)
        validator = Mock(spec=MessageValidator)
        validator.validate.return_value = False
        consumer.validator = validator
        
        mock_message = MagicMock()
        mock_message.value = {"invalid": "data"}
        
        with pytest.raises(ValueError) as exc_info:
            await consumer._process_message(mock_message)
        
        assert "Message validation failed" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_retry_mechanism(self, consumer_config):
        """Test retry mechanism with exponential backoff"""
        consumer = KafkaConsumer(consumer_config)
        processor = Mock(spec=MessageProcessor)
        
        # Simulate failures then success
        processor.process.side_effect = [
            Exception("First attempt failed"),
            Exception("Second attempt failed"),
            {"status": "success"}
        ]
        
        consumer.processor = processor
        consumer.validator = Mock(return_value=True)
        
        mock_message = MagicMock()
        mock_message.value = {"data": "test"}
        
        result = await consumer._process_message_with_retry(mock_message, max_retries=3)
        
        assert result["status"] == "success"
        assert processor.process.call_count == 3
    
    def test_dead_letter_queue(self, consumer_config):
        """Test that failed messages go to DLQ"""
        consumer = KafkaConsumer(consumer_config)
        dlq_producer = Mock()
        consumer.dlq_producer = dlq_producer
        
        failed_message = {
            "original_message": {"data": "test"},
            "error": "Processing failed after max retries",
            "timestamp": datetime.utcnow().isoformat(),
            "topic": "user-events",
            "partition": 0,
            "offset": 100
        }
        
        consumer._send_to_dlq(failed_message)
        
        dlq_producer.send.assert_called_once()
        call_args = dlq_producer.send.call_args[0]
        assert call_args[0] == "dead-letter-queue"
        assert json.loads(call_args[1]) == failed_message
    
    @pytest.mark.integration
    async def test_end_to_end_consumer_flow(self, kafka_test_cluster):
        """Integration test with real Kafka cluster"""
        # This would run against a test Kafka instance
        config = {
            'bootstrap_servers': kafka_test_cluster.bootstrap_servers,
            'topics': ['test-topic'],
            'group_id': 'integration-test-group'
        }
        
        consumer = KafkaConsumer(config)
        
        # Produce test message
        producer = kafka_test_cluster.get_producer()
        test_message = {"event": "test", "timestamp": datetime.utcnow().isoformat()}
        producer.send('test-topic', json.dumps(test_message).encode())
        producer.flush()
        
        # Consume and verify
        messages = await consumer.consume_batch(max_messages=1, timeout=5)
        assert len(messages) == 1
        assert messages[0]['event'] == 'test'
```

**Implementation:**
```python
# src/ingestion/kafka_consumer.py
import json
import asyncio
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
import backoff

from kafka import KafkaConsumer as KafkaClient
from kafka import KafkaProducer
from kafka.errors import KafkaError

from src.validation.validators import MessageValidator
from src.monitoring.metrics import MetricsCollector


logger = logging.getLogger(__name__)


class KafkaConsumer:
    """Robust Kafka consumer with error handling and monitoring"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.topics = config['topics']
        self.consumer = self._create_consumer()
        self.validator = MessageValidator()
        self.processor = None
        self.metrics = MetricsCollector()
        self.dlq_producer = self._create_dlq_producer()
        
    def _create_consumer(self) -> KafkaClient:
        """Create Kafka consumer with configuration"""
        return KafkaClient(
            *self.topics,
            bootstrap_servers=self.config['bootstrap_servers'],
            group_id=self.config['group_id'],
            auto_offset_reset=self.config.get('auto_offset_reset', 'earliest'),
            enable_auto_commit=self.config.get('enable_auto_commit', False),
            value_deserializer=self._deserialize_message,
            max_poll_records=self.config.get('max_poll_records', 500)
        )
    
    def _create_dlq_producer(self) -> KafkaProducer:
        """Create producer for dead letter queue"""
        return KafkaProducer(
            bootstrap_servers=self.config['bootstrap_servers'],
            value_serializer=lambda v: json.dumps(v).encode('utf-8')
        )
    
    def _deserialize_message(self, message: bytes) -> Dict[str, Any]:
        """Deserialize JSON message"""
        try:
            return json.loads(message.decode('utf-8'))
        except json.JSONDecodeError as e:
            logger.error(f"Failed to deserialize message: {e}")
            raise
    
    async def consume(self) -> None:
        """Main consumption loop"""
        logger.info(f"Starting consumer for topics: {self.topics}")
        
        try:
            for message in self.consumer:
                try:
                    await self._process_message(message)
                    self.consumer.commit()
                    self.metrics.increment('messages_processed')
                except Exception as e:
                    logger.error(f"Error processing message: {e}")
                    await self._handle_failed_message(message, e)
                    self.metrics.increment('messages_failed')
        except KeyboardInterrupt:
            logger.info("Consumer stopped by user")
        finally:
            self.consumer.close()
    
    async def _process_message(self, message) -> Dict[str, Any]:
        """Process a single message"""
        self.metrics.increment('messages_received')
        
        # Validate message
        if not self.validator.validate(message.value):
            raise ValueError("Message validation failed")
        
        # Process with retry
        result = await self._process_message_with_retry(message)
        
        # Log success
        logger.info(f"Processed message from {message.topic}:{message.partition}:{message.offset}")
        
        return result
    
    @backoff.on_exception(
        backoff.expo,
        Exception,
        max_tries=3,
        max_time=60
    )
    async def _process_message_with_retry(self, message, max_retries: int = 3) -> Dict[str, Any]:
        """Process message with exponential backoff retry"""
        if not self.processor:
            raise ValueError("No processor configured")
        
        return self.processor.process(message.value)
    
    async def _handle_failed_message(self, message, error: Exception) -> None:
        """Handle messages that failed processing"""
        failed_message = {
            "original_message": message.value,
            "error": str(error),
            "timestamp": datetime.utcnow().isoformat(),
            "topic": message.topic,
            "partition": message.partition,
            "offset": message.offset,
            "consumer_group": self.config['group_id']
        }
        
        self._send_to_dlq(failed_message)
    
    def _send_to_dlq(self, failed_message: Dict[str, Any]) -> None:
        """Send failed message to dead letter queue"""
        try:
            future = self.dlq_producer.send(
                'dead-letter-queue',
                json.dumps(failed_message).encode('utf-8')
            )
            future.get(timeout=10)
            logger.info(f"Sent message to DLQ: {failed_message['offset']}")
        except Exception as e:
            logger.error(f"Failed to send to DLQ: {e}")
    
    async def consume_batch(self, max_messages: int = 100, timeout: int = 10) -> List[Dict[str, Any]]:
        """Consume messages in batch mode"""
        messages = []
        end_time = asyncio.get_event_loop().time() + timeout
        
        while len(messages) < max_messages and asyncio.get_event_loop().time() < end_time:
            records = self.consumer.poll(timeout_ms=1000)
            
            for topic_partition, msgs in records.items():
                for msg in msgs:
                    messages.append(msg.value)
                    if len(messages) >= max_messages:
                        break
        
        return messages


class MessageProcessor:
    """Process validated messages"""
    
    def __init__(self, storage_backend):
        self.storage = storage_backend
    
    def process(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """Process message and store results"""
        # Transform message
        transformed = self.transform(message)
        
        # Enrich with additional data
        enriched = self.enrich(transformed)
        
        # Store in backend
        result = self.storage.store(enriched)
        
        return {
            "status": "success",
            "message_id": message.get('id'),
            "stored_at": datetime.utcnow().isoformat()
        }
    
    def transform(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """Apply transformations to message"""
        # Implementation here
        return message
    
    def enrich(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """Enrich message with additional data"""
        # Implementation here
        return message
```

### Microservice Architecture Project

#### Building Microservices with TDD

A comprehensive example of developing a microservice architecture using the AI Agent TDD-Scrum workflow. This project demonstrates service decomposition, API gateway patterns, and distributed system testing.

**Project Repository:** [github.com/agent-workflow-examples/microservices-platform](https://github.com/agent-workflow-examples/microservices-platform)

##### Project Overview

E-Commerce Microservices Platform featuring:
- User Service: Authentication and user management
- Product Service: Product catalog and inventory
- Order Service: Order processing and fulfillment
- Payment Service: Payment processing
- Notification Service: Email and SMS notifications
- API Gateway: Request routing and authentication

##### Project Structure
```
microservices-platform/
├── .github/
│   └── workflows/
│       ├── service-tests.yml        # Per-service testing
│       └── integration-tests.yml    # Cross-service tests
├── .orch-state/                     # Agent workflow state
├── services/
│   ├── api-gateway/
│   │   ├── src/
│   │   ├── tests/
│   │   └── Dockerfile
│   ├── user-service/
│   │   ├── src/
│   │   ├── tests/
│   │   └── Dockerfile
│   ├── product-service/
│   │   ├── src/
│   │   ├── tests/
│   │   └── Dockerfile
│   ├── order-service/
│   │   ├── src/
│   │   ├── tests/
│   │   └── Dockerfile
│   └── notification-service/
│       ├── src/
│       ├── tests/
│       └── Dockerfile
├── shared/
│   ├── proto/                       # Protocol buffers
│   ├── schemas/                     # Shared schemas
│   └── libraries/                   # Shared libraries
├── infrastructure/
│   ├── kubernetes/                  # K8s manifests
│   ├── terraform/                   # Infrastructure as code
│   └── monitoring/                  # Monitoring config
├── tests/
│   ├── integration/                 # Cross-service tests
│   ├── e2e/                        # End-to-end tests
│   └── tdd/
│       ├── MICRO-001/              # API Gateway
│       ├── MICRO-002/              # Service communication
│       └── MICRO-003/              # Distributed transactions
└── docker-compose.yml              # Local development
```

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

## WebSocket API Integration

### Real-Time State Monitoring

#### Basic WebSocket Connection
```javascript
// client.js - Basic WebSocket connection to monitor TDD state
const WebSocket = require('ws');

class TDDStateMonitor {
    constructor(host = 'localhost', port = 8765) {
        this.wsUrl = `ws://${host}:${port}`;
        this.ws = null;
        this.reconnectInterval = 5000;
    }
    
    connect() {
        try {
            this.ws = new WebSocket(this.wsUrl);
            
            this.ws.on('open', () => {
                console.log('Connected to TDD State Broadcaster');
                this.requestCurrentState();
            });
            
            this.ws.on('message', (data) => {
                const event = JSON.parse(data);
                this.handleStateEvent(event);
            });
            
            this.ws.on('close', () => {
                console.log('Connection closed. Attempting to reconnect...');
                setTimeout(() => this.connect(), this.reconnectInterval);
            });
            
            this.ws.on('error', (error) => {
                console.error('WebSocket error:', error);
            });
            
        } catch (error) {
            console.error('Failed to connect:', error);
            setTimeout(() => this.connect(), this.reconnectInterval);
        }
    }
    
    requestCurrentState() {
        if (this.ws && this.ws.readyState === WebSocket.OPEN) {
            this.ws.send(JSON.stringify({
                type: 'get_current_state'
            }));
        }
    }
    
    handleStateEvent(event) {
        switch (event.type) {
            case 'workflow_state_changed':
                console.log(`Workflow: ${event.old_state} → ${event.new_state}`);
                break;
            case 'tdd_state_changed':
                console.log(`TDD [${event.story_id}]: ${event.old_state} → ${event.new_state}`);
                break;
            case 'current_state':
                console.log('Current State:', event.data);
                break;
            default:
                console.log('Unknown event:', event);
        }
    }
}

// Usage
const monitor = new TDDStateMonitor();
monitor.connect();
```

#### Python WebSocket Client
```python
# websocket_client.py - Python client for TDD state monitoring
import asyncio
import json
import logging
import websockets
from datetime import datetime

class TDDWebSocketClient:
    def __init__(self, host='localhost', port=8765):
        self.uri = f"ws://{host}:{port}"
        self.websocket = None
        self.logger = logging.getLogger(__name__)
        
    async def connect(self):
        """Connect to the TDD state broadcaster"""
        try:
            self.websocket = await websockets.connect(self.uri)
            self.logger.info("Connected to TDD State Broadcaster")
            
            # Request current state
            await self.send_message({
                "type": "get_current_state"
            })
            
            # Listen for messages
            await self.listen()
            
        except Exception as e:
            self.logger.error(f"Connection failed: {e}")
            
    async def send_message(self, message):
        """Send message to server"""
        if self.websocket:
            await self.websocket.send(json.dumps(message))
            
    async def listen(self):
        """Listen for state updates"""
        async for message in self.websocket:
            try:
                event = json.loads(message)
                await self.handle_event(event)
            except json.JSONDecodeError as e:
                self.logger.error(f"Invalid JSON received: {e}")
                
    async def handle_event(self, event):
        """Handle incoming state events"""
        event_type = event.get('type')
        timestamp = datetime.now().strftime('%H:%M:%S')
        
        if event_type == 'workflow_state_changed':
            print(f"[{timestamp}] Workflow: {event['old_state']} → {event['new_state']}")
            
        elif event_type == 'tdd_state_changed':
            story_id = event.get('story_id', 'Unknown')
            print(f"[{timestamp}] TDD [{story_id}]: {event['old_state']} → {event['new_state']}")
            
        elif event_type == 'current_state':
            print(f"[{timestamp}] Current State:")
            print(f"  Workflow: {event['data']['workflow_state']}")
            print(f"  Active TDD Cycles: {len(event['data']['tdd_cycles'])}")
            
        else:
            print(f"[{timestamp}] Unknown event: {event_type}")

# Usage
async def main():
    client = TDDWebSocketClient()
    await client.connect()

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())
```

#### HTML Dashboard Integration
```html
<!-- dashboard.html - Simple web dashboard for TDD monitoring -->
<!DOCTYPE html>
<html>
<head>
    <title>TDD State Monitor</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; }
        .status { padding: 10px; margin: 10px 0; border-radius: 5px; }
        .idle { background-color: #f0f0f0; }
        .active { background-color: #e7f3ff; }
        .error { background-color: #ffe7e7; }
        .log { background-color: #f9f9f9; padding: 10px; height: 300px; overflow-y: scroll; }
    </style>
</head>
<body>
    <h1>TDD Workflow Monitor</h1>
    
    <div id="connectionStatus" class="status idle">Disconnected</div>
    
    <div>
        <h3>Current State</h3>
        <p>Workflow: <span id="workflowState">Unknown</span></p>
        <p>Active TDD Cycles: <span id="activeCycles">0</span></p>
    </div>
    
    <div>
        <h3>Event Log</h3>
        <div id="eventLog" class="log"></div>
    </div>
    
    <script>
        class TDDDashboard {
            constructor() {
                this.ws = null;
                this.reconnectDelay = 5000;
                this.init();
            }
            
            init() {
                this.connectWebSocket();
            }
            
            connectWebSocket() {
                try {
                    this.ws = new WebSocket('ws://localhost:8765');
                    
                    this.ws.onopen = () => {
                        this.updateConnectionStatus('Connected', 'active');
                        this.requestCurrentState();
                    };
                    
                    this.ws.onmessage = (event) => {
                        const data = JSON.parse(event.data);
                        this.handleMessage(data);
                    };
                    
                    this.ws.onclose = () => {
                        this.updateConnectionStatus('Disconnected', 'idle');
                        setTimeout(() => this.connectWebSocket(), this.reconnectDelay);
                    };
                    
                    this.ws.onerror = (error) => {
                        this.updateConnectionStatus('Error', 'error');
                        this.logEvent('Connection error: ' + error);
                    };
                    
                } catch (error) {
                    this.updateConnectionStatus('Failed', 'error');
                    setTimeout(() => this.connectWebSocket(), this.reconnectDelay);
                }
            }
            
            requestCurrentState() {
                if (this.ws && this.ws.readyState === WebSocket.OPEN) {
                    this.ws.send(JSON.stringify({
                        type: 'get_current_state'
                    }));
                }
            }
            
            handleMessage(data) {
                const timestamp = new Date().toLocaleTimeString();
                
                switch (data.type) {
                    case 'workflow_state_changed':
                        document.getElementById('workflowState').textContent = data.new_state;
                        this.logEvent(`${timestamp} - Workflow: ${data.old_state} → ${data.new_state}`);
                        break;
                        
                    case 'tdd_state_changed':
                        const storyId = data.story_id || 'Unknown';
                        this.logEvent(`${timestamp} - TDD [${storyId}]: ${data.old_state} → ${data.new_state}`);
                        break;
                        
                    case 'current_state':
                        document.getElementById('workflowState').textContent = data.data.workflow_state;
                        document.getElementById('activeCycles').textContent = Object.keys(data.data.tdd_cycles).length;
                        this.logEvent(`${timestamp} - State updated`);
                        break;
                }
            }
            
            updateConnectionStatus(status, className) {
                const statusEl = document.getElementById('connectionStatus');
                statusEl.textContent = status;
                statusEl.className = `status ${className}`;
            }
            
            logEvent(message) {
                const logEl = document.getElementById('eventLog');
                logEl.innerHTML += message + '<br>';
                logEl.scrollTop = logEl.scrollHeight;
            }
        }
        
        // Initialize dashboard
        new TDDDashboard();
    </script>
</body>
</html>
```

## Integration Summary

This comprehensive integration guide provides practical examples for connecting the AI Agent TDD-Scrum workflow system with various tools, platforms, and services commonly used in software development workflows.

### Quick Start Integration Checklist

**WebSocket API Integration:**
- ✅ JavaScript client for real-time state monitoring
- ✅ Python async client for TDD state tracking
- ✅ HTML dashboard for web-based monitoring

**GitHub Integration:**
- ✅ Basic webhook handler for repository events
- ✅ TDD-specific GitHub API integration
- ✅ Pull request automation and validation

**CI/CD Integration:**
- ✅ Minimal GitHub Actions workflow
- ✅ Basic Docker containerization
- ✅ Complete CI/CD pipeline examples

All examples are designed to be minimal working implementations that can be extended based on specific project requirements.