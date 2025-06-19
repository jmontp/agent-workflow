# Configuration

Configure the AI Agent TDD-Scrum workflow system for your development environment.

## Environment Variables

### Required Configuration

**`DISCORD_BOT_TOKEN`**
Your Discord bot token for the HITL interface.
```bash
export DISCORD_BOT_TOKEN="your_discord_bot_token_here"
```

### Optional Configuration

**`ANTHROPIC_API_KEY`** (for Claude integration)
```bash
export ANTHROPIC_API_KEY="your_anthropic_api_key"
```

**`GITHUB_TOKEN`** (for enhanced GitHub integration)
```bash
export GITHUB_TOKEN="your_github_personal_access_token"
```

## Project Configuration

### Single Project Setup

For managing a single project, create a simple configuration:

```yaml
# config.yml
orchestrator:
  mode: blocking  # blocking, partial, or autonomous
  project_path: "/path/to/your/project"
  project_name: "my-project"
```

### Multi-Project Setup

For managing multiple projects simultaneously:

```yaml
# config.yml
orchestrator:
  mode: blocking
  projects:
    - name: "web-app"
      path: "/path/to/web-app"
      mode: partial
    - name: "api-service" 
      path: "/path/to/api-service"
      mode: autonomous
    - name: "mobile-app"
      path: "/path/to/mobile-app"
      mode: blocking
```

## Orchestration Modes

### Blocking Mode
- Human approval required for all strategic decisions
- Safest option for critical projects
- Recommended for learning the system

### Partial Mode
- Agents execute with quarantined output for review
- Balanced automation with oversight
- Good for established workflows

### Autonomous Mode
- Full execution with monitoring and alerts
- Highest automation level
- Use only for well-tested processes

## Discord Configuration

### Bot Setup

1. Create a Discord application at [Discord Developer Portal](https://discord.com/developers/applications)
2. Create a bot and copy the token
3. Invite the bot to your server with these permissions:
   - Use Slash Commands
   - Send Messages
   - Embed Links
   - Read Message History

### Channel Configuration

The system automatically creates project-specific channels:
- Format: `hostname-projectname`
- Example: `macbook-web-app`, `ubuntu-api-service`

## Agent Configuration

### AI Integration

**Claude Code Integration:**
```bash
# Install Claude Code CLI
pip install claude-code

# Verify installation
claude --version
```

**Alternative AI Services:**
The system supports pluggable AI integrations. Implement the `BaseAgent` interface for custom AI services.

### Security Settings

Agent tool access is configured in `lib/agent_tool_config.py`:

```python
AGENT_SECURITY_PROFILES = {
    "DesignAgent": {
        "allowed_tools": ["read", "web_search", "documentation"],
        "blocked_tools": ["edit", "git", "system"]
    },
    "CodeAgent": {
        "allowed_tools": ["read", "edit", "git_add", "git_commit", "test"],
        "blocked_tools": ["git_push", "system", "delete"]
    }
    # ... other agents
}
```

## File Locations

### Configuration Files
- Main config: `config.yml` (repository root)
- User preferences: `~/.agent-workflow/preferences.yml`
- Project state: `<project>/.orch-state/status.json`

### Log Files
- System logs: `logs/orchestrator.log`
- Agent logs: `logs/agents/<agent-type>.log`
- Discord logs: `logs/discord-bot.log`

## Performance Tuning

### Resource Limits
```yaml
orchestrator:
  max_concurrent_projects: 3
  agent_timeout_minutes: 30
  state_save_interval_seconds: 60
```

### Discord Rate Limiting
```yaml
discord:
  max_commands_per_minute: 20
  response_timeout_seconds: 30
```

## Troubleshooting Configuration

### Common Issues

**Environment variables not recognized:**
```bash
# Check current environment
env | grep -E "(DISCORD|ANTHROPIC|GITHUB)"

# Set in shell profile for persistence
echo 'export DISCORD_BOT_TOKEN="your_token"' >> ~/.bashrc
source ~/.bashrc
```

**Configuration file not found:**
```bash
# Create default configuration
cp config.example.yml config.yml
# Edit with your settings
```

**Permission errors:**
```bash
# Ensure proper file permissions
chmod 600 config.yml  # Restrict access to config file
chmod +x scripts/orchestrator.py  # Make scripts executable
```

### Validation

Test your configuration:
```bash
# Validate configuration syntax
python -c "import yaml; yaml.safe_load(open('config.yml'))"

# Test Discord connection
python tools/compliance/monitor_compliance.py --test-discord

# Test AI integration
python tools/coverage/test_runner.py
```

## TDD Configuration

### TDD State Machine Settings

Configure TDD behavior in your project configuration:

```yaml
# config.yml
orchestrator:
  mode: blocking
  tdd:
    enabled: true
    auto_start_cycles: true  # Automatically start TDD for active stories
    preserve_tests: true     # Enable test preservation workflow
    parallel_execution: true # Allow multiple TDD cycles simultaneously
    
    # State machine configuration
    state_machine:
      auto_transitions: true    # Enable /tdd next auto-advancement
      require_conditions: true  # Enforce transition conditions
      validation_mode: strict   # strict, relaxed, or disabled
    
    # Test preservation settings
    test_preservation:
      base_directory: "tests/tdd"
      structure_mode: "story_based"  # story_based or flat
      integration_target: "tests/unit"  # Where to move tests after completion
      backup_enabled: true
      max_backup_age_days: 30
```

### TDD Cycle Timeouts

Configure timeouts for different TDD phases:

```yaml
tdd:
  timeouts:
    design_phase_minutes: 30      # Design Agent specification creation
    test_red_phase_minutes: 45    # QA Agent test writing
    code_green_phase_minutes: 60  # Code Agent implementation
    refactor_phase_minutes: 30    # Code Agent refactoring
    commit_phase_minutes: 15      # Final commit and cleanup
    
    # Global timeout settings
    max_cycle_hours: 4           # Maximum time for complete TDD cycle
    stuck_detection_minutes: 15  # How long before marking phase as stuck
    auto_recovery_enabled: true  # Enable automatic recovery attempts
```

### Test Execution Configuration

Configure how tests are executed during TDD cycles:

```yaml
tdd:
  test_execution:
    runner: "pytest"              # Test runner: pytest, unittest, nose2
    parallel_jobs: 4              # Number of parallel test jobs
    timeout_seconds: 300          # Individual test timeout
    coverage_threshold: 90        # Minimum coverage percentage
    
    # Test discovery
    test_patterns:
      - "test_*.py"
      - "*_test.py"
    
    # Coverage configuration
    coverage:
      enabled: true
      fail_under: 90
      exclude_patterns:
        - "*/migrations/*"
        - "*/venv/*"
        - "test_*"
    
    # CI integration
    ci_integration:
      enabled: true
      provider: "github_actions"  # github_actions, gitlab_ci, jenkins
      trigger_on_commit: true
      require_passing_ci: true
```

### Agent Behavior in TDD

Configure how agents behave during TDD cycles:

```yaml
tdd:
  agents:
    design_agent:
      max_specification_length: 2000
      include_diagrams: true
      detail_level: "comprehensive"  # minimal, standard, comprehensive
      
    qa_agent:
      test_types:
        - "unit"
        - "integration"
        - "acceptance"
      mock_external_services: true
      generate_test_data: true
      
    code_agent:
      implementation_style: "minimal"  # minimal, complete, extensive
      refactor_automatically: true
      apply_best_practices: true
      
    # Agent coordination
    coordination:
      exclusive_phases: true        # Only one agent active per phase
      handoff_validation: true      # Validate work before handoff
      conflict_resolution: "human"  # human, automatic, priority_based
```

### TDD Quality Gates

Configure quality requirements for TDD progression:

```yaml
tdd:
  quality_gates:
    test_red_phase:
      min_test_count: 3
      require_failing_tests: true
      max_test_errors: 0
      
    code_green_phase:
      require_all_tests_passing: true
      max_complexity_score: 10
      min_coverage_increase: 5  # Percentage points
      
    refactor_phase:
      maintain_test_coverage: true
      max_complexity_regression: 0
      code_quality_threshold: 8.0  # SonarQube-style rating
      
    commit_phase:
      require_commit_message: true
      run_full_test_suite: true
      validate_ci_config: true
```

### TDD Metrics and Monitoring

Configure metrics collection and monitoring:

```yaml
tdd:
  metrics:
    collection_enabled: true
    
    # Cycle metrics
    track_cycle_times: true
    track_phase_durations: true
    track_success_rates: true
    
    # Quality metrics
    track_test_coverage: true
    track_code_complexity: true
    track_refactor_frequency: true
    
    # Export configuration
    export:
      format: "json"  # json, csv, prometheus
      interval_minutes: 15
      destination: "logs/tdd_metrics.json"
      
    # Alerting
    alerts:
      stuck_cycle_threshold_minutes: 60
      low_coverage_threshold: 80
      high_complexity_threshold: 15
      notification_webhook: "https://hooks.slack.com/..."
```

### Environment-Specific TDD Settings

Configure TDD behavior for different environments:

```yaml
# Development environment
development:
  tdd:
    timeouts:
      design_phase_minutes: 15    # Faster for dev
      test_red_phase_minutes: 20
    quality_gates:
      code_green_phase:
        min_coverage_increase: 2  # Relaxed for dev
    test_execution:
      parallel_jobs: 2            # Lower resource usage

# Production environment  
production:
  tdd:
    timeouts:
      design_phase_minutes: 60    # More thorough for prod
      test_red_phase_minutes: 90
    quality_gates:
      code_green_phase:
        min_coverage_increase: 10 # Stricter for prod
    test_execution:
      parallel_jobs: 8            # Full resource utilization
```

### TDD Integration Settings

Configure integration with external tools and services:

```yaml
tdd:
  integrations:
    # Git integration
    git:
      auto_commit_tests: true
      commit_message_template: "TDD: {phase} for {story_id} - {description}"
      branch_strategy: "feature"  # feature, tdd_cycles, main
      
    # CI/CD integration  
    ci:
      provider: "github_actions"
      config_file: ".github/workflows/tdd.yml"
      trigger_events:
        - "test_commit"
        - "code_commit" 
        - "refactor_commit"
      
    # Code quality tools
    quality_tools:
      sonarqube:
        enabled: true
        server_url: "https://sonar.company.com"
        project_key: "my-project"
      
      codecov:
        enabled: true
        token: "${CODECOV_TOKEN}"
        
    # Notification services
    notifications:
      slack:
        webhook_url: "${SLACK_WEBHOOK}"
        channels:
          - "#tdd-cycles"
          - "#development"
      
      email:
        smtp_server: "smtp.company.com"
        from_address: "tdd-bot@company.com"
        recipients:
          - "team-lead@company.com"
```

### Validating TDD Configuration

Test your TDD configuration:

```bash
# Validate TDD configuration syntax
python -c "import yaml; yaml.safe_load(open('config.yml'))"

# Test TDD state machine initialization
python -c "
from lib.tdd_state_machine import TDDStateMachine
machine = TDDStateMachine()
print('TDD state machine initialized successfully')
"

# Validate TDD directory structure
python tools/coverage/validate_tdd.py

# Test TDD integration with main system
python scripts/test_tdd_integration.py
```

### Common TDD Configuration Issues

**TDD cycles not starting automatically:**
```yaml
# Ensure auto_start_cycles is enabled
tdd:
  auto_start_cycles: true
```

**Test preservation not working:**
```yaml
# Check directory permissions and paths
tdd:
  test_preservation:
    base_directory: "tests/tdd"  # Must be writable
    structure_mode: "story_based"
```

**Agent coordination conflicts:**
```yaml
# Enable exclusive phases to prevent conflicts
tdd:
  agents:
    coordination:
      exclusive_phases: true
      handoff_validation: true
```

**Performance issues with large test suites:**
```yaml
# Optimize test execution
tdd:
  test_execution:
    parallel_jobs: 8
    timeout_seconds: 60  # Reduce if needed
```

## Next Steps

After configuration:
1. [Run the quick start guide](quick-start.md)
2. [Set up your first project](../user-guide/project-setup.md)
3. [Learn the HITL commands](../user-guide/hitl-commands.md)
4. [Explore TDD workflows](../user-guide/tdd-workflow.md)