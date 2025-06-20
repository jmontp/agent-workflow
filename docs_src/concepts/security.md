# Security Model

The AI Agent system implements comprehensive security controls to ensure safe operation in development environments.

## Principle of Least Privilege

Each agent type has specific tool access restrictions based on their function:

### Agent Access Levels

**Orchestrator Agent**
- **Allowed**: Full bash access including file operations, git operations (including push), system management
- **Restricted**: Only the most dangerous commands (sudo, format, dd, shred)
- **Purpose**: System coordination and workflow management

**DesignAgent**
- **Allowed**: File reading, documentation creation, web research, basic file operations
- **Restricted**: Code editing, version control, system administration
- **Purpose**: Architecture design and specifications

**CodeAgent**
- **Allowed**: File editing, git add/commit, pytest/coverage commands, package management, code quality tools
- **Restricted**: File deletion, git push, system administration
- **Purpose**: Feature implementation and code changes

**QAAgent**
- **Allowed**: Test file creation, test execution, pytest/coverage commands, code quality analysis
- **Restricted**: Code modification (except test files), git commit/push operations
- **Purpose**: Test creation and quality validation

**DataAgent**
- **Allowed**: Data file access, notebook creation, visualization tools, data processing commands
- **Restricted**: Source code modification, version control, testing commands
- **Purpose**: Data analysis and reporting

## Security Boundaries

### Command Access Control
The system enforces tool restrictions through:
- Claude Code CLI flags (`--allowedTools`/`--disallowedTools`)
- Automatic security boundary application
- Runtime validation of agent actions
- Comprehensive audit logging

### TDD Workflow Security
During TDD cycles, additional security controls apply:
- **QA Agents**: Can create and modify test files during TEST_RED phase, execute pytest commands
- **Code Agents**: Can execute pytest/coverage commands for validation, cannot modify test files
- **Test Command Access**: Both QA and Code agents have access to pytest, coverage, and related testing tools
- **Phase-based Restrictions**: Tool access varies by TDD phase (TEST_RED, CODE_GREEN, REFACTOR)
- **Story-level Isolation**: TDD cycles isolated per story to prevent cross-contamination

### Human Approval Gates
Critical operations require explicit approval:
- Code deployment and publishing
- System configuration changes
- Security-sensitive code modifications
- External service integrations

### Safe Defaults
The system operates with secure defaults:
- Agents cannot execute dangerous system commands
- Version control operations are limited by agent type
- File system access is scoped appropriately
- Network access follows least-privilege principles

## Data Protection

### Project Isolation
Each project maintains separate:
- State files and configuration
- Agent execution contexts
- Access permissions and policies
- Audit trails and logs

### Sensitive Information Handling
The system protects:
- API keys and tokens (never committed to repositories)
- Database credentials and connection strings
- User personal information and preferences
- Proprietary code and business logic

## Compliance and Auditing

### Activity Logging
All agent actions are logged:
- Command execution and results
- File modifications and version control
- Human approval decisions
- Error conditions and escalations

### Security Testing
The security model is validated through:
- Automated test suite for access controls
- Integration tests for boundary enforcement
- Manual security review processes
- Regular security policy updates

## Best Practices

### For Users
- Review agent actions before approval
- Use appropriate agent types for tasks
- Monitor system logs for unusual activity
- Keep orchestrator software updated

### For Developers
- Follow security testing requirements
- Document new agent capabilities
- Implement proper error handling
- Validate all security boundary changes

The security model ensures that AI agents operate safely within defined boundaries while maintaining the flexibility needed for effective development assistance.