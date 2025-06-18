# CLI Reference Manual

Complete command-line interface reference for the AI Agent TDD-Scrum workflow system, covering all scripts, tools, and operational commands.

## Overview

The system provides several CLI entry points for different operational modes, with seamless integration to a modern web-based UI portal:

- **`agent-orch ui`** - Holistic web portal with CLI integration
- **`scripts/orchestrator.py`** - Single-project orchestrator
- **`scripts/multi_project_orchestrator.py`** - Multi-project management
- **`lib/discord_bot.py`** - Discord bot interface
- **`visualizer/app.py`** - Real-time state visualizer
- **Management scripts** - Various operational tools

### UI Portal Integration

The CLI now provides holistic UI portal capabilities through the `agent-orch ui` command family, offering:

- **Cross-Platform Access**: Web portal accessible from any device with a browser
- **Bidirectional Sync**: CLI commands reflect instantly in UI, UI actions update CLI state
- **Multiple Launch Modes**: Interactive, headless, development, and production modes
- **Mobile Optimization**: Responsive design with PWA capabilities and QR code access
- **Team Collaboration**: Multi-user support with real-time synchronization
- **Security Integration**: Session-based authentication with role-based access control

## Core CLI Commands

### UI Portal Commands

#### `agent-orch ui`
Holistic web portal for comprehensive project management with CLI integration.

```bash
agent-orch ui [OPTIONS]
```

**Options:**
```bash
--port PORT                 Custom port for UI server [default: 8080]
--host HOST                 Host to bind server [default: localhost]
--mode MODE                 Launch specific UI mode [dashboard|chat|config|monitor]
--project PROJECT           Open specific project view directly
--headless                  Run background server without opening browser
--theme THEME               Set UI theme [light|dark|auto]
--dev-mode                  Enable hot-reload and development features
--production                Enable production optimizations and security
--team-mode                 Enable multi-user collaboration features
--mobile-optimized          Optimize for mobile device access
--qr-code                   Display QR code for mobile access
--browser BROWSER           Specify browser [chrome|firefox|safari|edge]
--network-detect            Auto-detect best network interface
--ssl-cert FILE             SSL certificate for HTTPS (production)
--ssl-key FILE              SSL private key for HTTPS (production)
```

**Examples:**
```bash
# Basic UI portal launch
agent-orch ui

# Development mode with hot-reload
agent-orch ui --dev-mode

# Team collaboration mode
agent-orch ui --team-mode --network-detect

# Production deployment
agent-orch ui --production --ssl-cert /etc/ssl/certs/agent-workflow.crt

# Mobile-optimized with QR code
agent-orch ui --mobile-optimized --qr-code

# Headless server mode
agent-orch ui --headless --port 8080

# Project-specific dashboard
agent-orch ui --mode dashboard --project webapp
```

#### `agent-orch ui-status`
Check UI portal server status and integration health.

```bash
agent-orch ui-status [OPTIONS]
```

**Options:**
```bash
--json                      Output in JSON format
--verbose                   Show detailed component status
--health-check              Run comprehensive health check
--performance               Include performance metrics
--integration-health        Check CLI-UI integration health
```

#### `agent-orch ui-config`
Configure UI portal settings and integrations.

```bash
agent-orch ui-config [SUBCOMMAND] [OPTIONS]
```

**Subcommands:**
```bash
setup                       Interactive UI configuration wizard
validate                    Validate current UI configuration
sync                        Synchronize CLI and UI configurations
export FILE                 Export UI configuration to file
import FILE                 Import UI configuration from file
```

#### `agent-orch ui-token`
Manage UI portal authentication tokens.

```bash
agent-orch ui-token [SUBCOMMAND] [OPTIONS]
```

**Subcommands:**
```bash
generate                    Generate new access token
list                        List active tokens
revoke TOKEN                Revoke specific token
cleanup                     Remove expired tokens
```

#### `agent-orch mobile`
Configure mobile device access and optimization.

```bash
agent-orch mobile [SUBCOMMAND] [OPTIONS]
```

**Subcommands:**
```bash
setup                       Configure mobile access
qr [PROJECT]               Generate QR code for mobile access
optimize                    Enable mobile optimizations
pwa-config                 Configure Progressive Web App features
```

### Primary Orchestrator

#### `scripts/orchestrator.py`
Single-project orchestration with comprehensive options.

```bash
python scripts/orchestrator.py [OPTIONS]
```

**Options:**
```bash
--config, -c FILE           Configuration file path [default: config.yml]
--project-path, -p PATH     Project directory path [required]
--mode, -m MODE            Orchestration mode [blocking|partial|autonomous]
--verbose, -v              Enable verbose logging
--debug, -d                Enable debug mode with detailed output
--dry-run                  Simulate operations without making changes
--log-file FILE            Log file path [default: logs/orchestrator.log]
--log-level LEVEL          Logging level [DEBUG|INFO|WARNING|ERROR]
--no-discord               Run without Discord integration
--health-check             Run system health check and exit
--validate-config          Validate configuration and exit
--setup                    Initialize project structure
--reset                    Reset project state (use with caution)
```

**Examples:**
```bash
# Basic usage
python scripts/orchestrator.py --project-path /home/user/my-project

# Development mode with verbose logging
python scripts/orchestrator.py -p /path/to/project -v --debug

# Production mode with custom config
python scripts/orchestrator.py -c production.yml -m autonomous -p /opt/projects/app

# Health check only
python scripts/orchestrator.py --health-check

# Setup new project
python scripts/orchestrator.py --setup -p /new/project/path
```

### Multi-Project Orchestrator

#### `scripts/multi_project_orchestrator.py`
Advanced multi-project management with enterprise features.

```bash
python scripts/multi_project_orchestrator.py [OPTIONS]
```

**Options:**
```bash
--config, -c FILE           Multi-project configuration file
--list-projects, -l         List all configured projects
--project PROJECT           Target specific project for operations
--start-all                 Start orchestration for all projects
--stop-all                  Stop all active orchestrators
--status                    Show status of all projects
--logs PROJECT              Show logs for specific project
--monitor                   Real-time monitoring mode
--health-check              Comprehensive system health check
--performance-test          Run performance benchmarks
--backup                    Create backup of all project states
--restore BACKUP_PATH       Restore from backup
--cleanup                   Clean up old logs and temporary files
--export-metrics FILE       Export performance metrics to file
--import-config FILE        Import project configuration
--validate                  Validate all project configurations
```

**Examples:**
```bash
# List all projects
python scripts/multi_project_orchestrator.py --list-projects

# Start specific project
python scripts/multi_project_orchestrator.py --project web-app

# Monitor all projects
python scripts/multi_project_orchestrator.py --monitor

# Health check with detailed output
python scripts/multi_project_orchestrator.py --health-check --verbose

# Performance testing
python scripts/multi_project_orchestrator.py --performance-test

# Backup and restore
python scripts/multi_project_orchestrator.py --backup
python scripts/multi_project_orchestrator.py --restore backups/2024-01-15_full.tar.gz
```

### Discord Bot Interface

#### `lib/discord_bot.py`
Discord bot for Human-In-The-Loop control with advanced features.

```bash
python lib/discord_bot.py [OPTIONS]
```

**Options:**
```bash
--token TOKEN               Discord bot token (or use DISCORD_BOT_TOKEN env)
--config FILE               Bot configuration file
--orchestrator-config FILE  Orchestrator configuration file
--channel-prefix PREFIX     Channel naming prefix [default: hostname-]
--command-prefix PREFIX     Command prefix [default: /]
--sync-commands             Sync slash commands on startup
--guild-only GUILD_ID       Restrict to specific guild (for testing)
--status-message MESSAGE    Custom bot status message
--activity-type TYPE        Activity type [playing|watching|listening]
--no-auto-channels          Disable automatic channel creation
--max-projects NUMBER       Maximum concurrent projects [default: 10]
--debug-mode                Enable debug features and logging
--metrics-port PORT         Metrics server port [default: 8000]
```

**Examples:**
```bash
# Basic bot startup
python lib/discord_bot.py

# Development mode with guild restriction
python lib/discord_bot.py --guild-only 123456789 --debug-mode

# Production with custom status
python lib/discord_bot.py --status-message "Managing 5 projects" --activity-type watching

# Sync commands for new bot
python lib/discord_bot.py --sync-commands
```

### State Visualizer

#### `visualizer/app.py`
Real-time workflow visualization with WebSocket interface.

```bash
cd visualizer && python app.py [OPTIONS]
```

**Options:**
```bash
--host HOST                 Host to bind to [default: localhost]
--port PORT                 Port to bind to [default: 5000]
--debug                     Enable Flask debug mode
--websocket-host HOST       WebSocket server host [default: localhost]
--websocket-port PORT       WebSocket server port [default: 8080]
--auto-connect              Auto-connect to orchestrator on startup
--theme THEME               UI theme [light|dark|auto]
--update-interval MS        Update interval in milliseconds [default: 1000]
--max-history NUMBER        Max state history to display [default: 100]
```

**Examples:**
```bash
# Basic visualizer
cd visualizer && python app.py

# Production with external access
cd visualizer && python app.py --host 0.0.0.0 --port 8080

# Development with auto-refresh
cd visualizer && python app.py --debug --update-interval 500
```

## Management Scripts

### Database Operations

#### `scripts/db_manager.py`
Database management and maintenance operations.

```bash
python scripts/db_manager.py [COMMAND] [OPTIONS]
```

**Commands:**
```bash
init                        Initialize database schema
migrate                     Run database migrations
backup [--output FILE]     Create database backup
restore --input FILE       Restore from backup
vacuum                      Vacuum and optimize database
repair                      Repair corrupted data
export --format FORMAT     Export data [json|csv|yaml]
import --file FILE          Import data from file
stats                       Show database statistics
clean --older-than DAYS     Clean old records
```

**Examples:**
```bash
# Initialize new database
python scripts/db_manager.py init

# Create backup
python scripts/db_manager.py backup --output backups/db_$(date +%Y%m%d).sql

# Clean old data
python scripts/db_manager.py clean --older-than 30

# Export metrics
python scripts/db_manager.py export --format json > metrics.json
```

### Configuration Management

#### `scripts/config_manager.py`
Configuration file management and validation.

```bash
python scripts/config_manager.py [COMMAND] [OPTIONS]
```

**Commands:**
```bash
validate FILE               Validate configuration file
generate-template TYPE      Generate configuration template
merge FILE1 FILE2          Merge configuration files
diff FILE1 FILE2           Compare configuration files
encrypt FILE                Encrypt sensitive configuration
decrypt FILE                Decrypt configuration file
lint FILE                   Check configuration best practices
convert --from FORMAT       Convert between formats
```

**Examples:**
```bash
# Validate configuration
python scripts/config_manager.py validate config/production.yml

# Generate template
python scripts/config_manager.py generate-template multi-project > new-config.yml

# Encrypt secrets
python scripts/config_manager.py encrypt config/secrets.yml

# Compare configs
python scripts/config_manager.py diff config/dev.yml config/prod.yml
```

### Log Management

#### `scripts/log_manager.py`
Log file management and analysis tools.

```bash
python scripts/log_manager.py [COMMAND] [OPTIONS]
```

**Commands:**
```bash
analyze [FILE]              Analyze log files for patterns
rotate                      Rotate log files
compress --older-than DAYS  Compress old log files
search PATTERN              Search across all log files
tail --follow               Follow live log output
errors --since TIME         Show errors since timestamp
metrics --interval MINUTES  Extract metrics from logs
report --format FORMAT      Generate log report
```

**Examples:**
```bash
# Analyze recent logs
python scripts/log_manager.py analyze logs/orchestrator.log

# Search for errors
python scripts/log_manager.py search "ERROR|CRITICAL"

# Follow live logs
python scripts/log_manager.py tail --follow

# Generate daily report
python scripts/log_manager.py report --format html > daily_report.html
```

### Testing Utilities

#### `scripts/test_runner.py`
Advanced test execution and management.

```bash
python scripts/test_runner.py [COMMAND] [OPTIONS]
```

**Commands:**
```bash
run [PATTERN]               Run tests matching pattern
coverage                    Run tests with coverage
performance                 Run performance tests
integration                 Run integration tests only
security                    Run security tests
regression                  Run regression test suite
smoke                       Run smoke tests
report --format FORMAT     Generate test report
```

**Options:**
```bash
--parallel WORKERS          Number of parallel workers
--verbose, -v               Verbose output
--fail-fast                 Stop on first failure
--retry-failures            Retry failed tests
--timeout SECONDS           Test timeout
--markers MARKERS           Run tests with specific markers
--output-file FILE          Output results to file
--junit-xml FILE            Generate JUnit XML report
```

**Examples:**
```bash
# Run all tests with coverage
python scripts/test_runner.py coverage --parallel 4

# Run specific test pattern
python scripts/test_runner.py run "test_tdd_*" --verbose

# Performance testing
python scripts/test_runner.py performance --timeout 300

# Generate comprehensive report
python scripts/test_runner.py report --format html --output-file test_report.html
```

## TDD-Specific CLI Tools

### TDD Cycle Manager

#### `scripts/tdd_manager.py`
TDD cycle management and analysis tools.

```bash
python scripts/tdd_manager.py [COMMAND] [OPTIONS]
```

**Commands:**
```bash
list-cycles [PROJECT]       List active TDD cycles
status CYCLE_ID             Get detailed cycle status
start STORY_ID              Start new TDD cycle
pause CYCLE_ID              Pause TDD cycle
resume CYCLE_ID             Resume paused cycle
abort CYCLE_ID              Abort TDD cycle
reset CYCLE_ID --to-state   Reset cycle to specific state
validate CYCLE_ID           Validate cycle integrity
metrics [--period DAYS]     Show TDD metrics
export CYCLE_ID             Export cycle data
import FILE                 Import cycle data
```

**Examples:**
```bash
# List all active cycles
python scripts/tdd_manager.py list-cycles

# Get detailed status
python scripts/tdd_manager.py status tdd-cycle-abc123

# Start new cycle
python scripts/tdd_manager.py start AUTH-001

# Get weekly metrics
python scripts/tdd_manager.py metrics --period 7
```

### Test Preservation Manager

#### `scripts/test_preservation.py`
Test file preservation and integration management.

```bash
python scripts/test_preservation.py [COMMAND] [OPTIONS]
```

**Commands:**
```bash
preserve STORY_ID           Preserve test files for story
integrate STORY_ID          Integrate tests into main suite
validate-structure          Validate test directory structure
cleanup --older-than DAYS   Clean up old preserved tests
migrate-tests SOURCE DEST   Migrate test files
verify-integrity            Verify test file integrity
report                      Generate preservation report
```

**Examples:**
```bash
# Preserve tests for completed story
python scripts/test_preservation.py preserve AUTH-001

# Integrate tests into main suite
python scripts/test_preservation.py integrate AUTH-001

# Clean up old test files
python scripts/test_preservation.py cleanup --older-than 30
```

## DevOps and Operations

### Deployment Scripts

#### `scripts/deploy.py`
Deployment automation and management.

```bash
python scripts/deploy.py [ENVIRONMENT] [OPTIONS]
```

**Environments:**
- `development` - Local development deployment
- `staging` - Staging environment deployment  
- `production` - Production deployment

**Options:**
```bash
--config FILE               Deployment configuration
--version VERSION           Specific version to deploy
--rollback                  Rollback to previous version
--health-check              Run health check after deployment
--skip-tests                Skip test execution
--force                     Force deployment (bypass checks)
--dry-run                   Show what would be deployed
--notify WEBHOOK            Notification webhook URL
```

**Examples:**
```bash
# Deploy to staging
python scripts/deploy.py staging --health-check

# Production deployment with version
python scripts/deploy.py production --version v1.2.3 --notify $SLACK_WEBHOOK

# Rollback production
python scripts/deploy.py production --rollback

# Dry run for production
python scripts/deploy.py production --dry-run
```

### Monitoring Scripts

#### `scripts/monitor.py`
System monitoring and alerting.

```bash
python scripts/monitor.py [COMMAND] [OPTIONS]
```

**Commands:**
```bash
start                       Start monitoring daemon
stop                        Stop monitoring daemon
status                      Show monitoring status
check-health                Run health checks
alert-test                  Test alerting configuration
metrics                     Display current metrics
dashboard                   Launch monitoring dashboard
```

**Options:**
```bash
--interval SECONDS          Monitoring interval [default: 60]
--alert-threshold VALUE     Alert threshold configuration
--webhook URL               Webhook for notifications
--dashboard-port PORT       Dashboard port [default: 8080]
--config FILE               Monitoring configuration
```

**Examples:**
```bash
# Start monitoring with 30-second intervals
python scripts/monitor.py start --interval 30

# Test alert system
python scripts/monitor.py alert-test --webhook $ALERT_WEBHOOK

# Launch dashboard
python scripts/monitor.py dashboard --dashboard-port 9090
```

## Utility Commands

### Data Management

#### `scripts/data_utils.py`
Data manipulation and analysis utilities.

```bash
python scripts/data_utils.py [COMMAND] [OPTIONS]
```

**Commands:**
```bash
export --format FORMAT     Export system data
import --file FILE          Import data from file
migrate --from VERSION     Migrate data format
validate                    Validate data integrity
compress                    Compress data files
decompress FILE             Decompress data files
analyze                     Analyze data patterns
report                      Generate data report
```

### System Maintenance

#### `scripts/maintenance.py`
System maintenance and cleanup operations.

```bash
python scripts/maintenance.py [COMMAND] [OPTIONS]
```

**Commands:**
```bash
cleanup                     General system cleanup
vacuum                      Database vacuum and optimization
rotate-logs                 Rotate log files
compress-backups            Compress old backups
update-dependencies         Update system dependencies
health-check                Comprehensive health check
repair                      Repair system issues
optimize                    Optimize system performance
```

**Examples:**
```bash
# Daily maintenance
python scripts/maintenance.py cleanup
python scripts/maintenance.py rotate-logs
python scripts/maintenance.py vacuum

# Weekly maintenance
python scripts/maintenance.py compress-backups
python scripts/maintenance.py optimize

# Health check
python scripts/maintenance.py health-check --verbose
```

## Environment Variables

### Core Configuration
```bash
# Required
export DISCORD_BOT_TOKEN="your_discord_bot_token"

# Optional but recommended
export ANTHROPIC_API_KEY="your_anthropic_api_key"
export GITHUB_TOKEN="your_github_token"

# System configuration
export HOSTNAME="your_hostname"
export LOG_LEVEL="INFO"                    # DEBUG|INFO|WARNING|ERROR
export ORCHESTRATOR_MODE="blocking"       # blocking|partial|autonomous
export NO_AGENT_MODE="false"             # true for testing with mock agents

# Performance tuning
export MAX_CONCURRENT_PROJECTS="5"
export AGENT_TIMEOUT_MINUTES="30"
export STATE_SAVE_INTERVAL="60"

# Storage configuration
export DATA_DIRECTORY="/opt/agent-workflow/data"
export LOG_DIRECTORY="/opt/agent-workflow/logs"
export BACKUP_DIRECTORY="/opt/agent-workflow/backups"

# Monitoring
export METRICS_ENABLED="true"
export METRICS_PORT="8000"
export HEALTH_CHECK_INTERVAL="300"

# Security
export ENCRYPTION_KEY="your_encryption_key"
export API_RATE_LIMIT="100"
export ALLOWED_HOSTS="localhost,your-domain.com"
```

### UI Portal Configuration
```bash
# UI Portal server settings
export UI_PORTAL_ENABLED="true"
export UI_PORTAL_PORT="8080"
export UI_PORTAL_HOST="localhost"            # Use 0.0.0.0 for external access
export UI_API_PORT="8000"
export UI_WEBSOCKET_PORT="8001"

# UI Portal features
export UI_THEME="auto"                       # light|dark|auto
export UI_AUTO_LAUNCH="true"                 # Auto-launch browser
export UI_MOBILE_OPTIMIZED="true"
export UI_PWA_ENABLED="true"
export UI_QR_CODE_ENABLED="true"

# Team collaboration
export UI_TEAM_MODE="false"                  # Enable multi-user features
export UI_MAX_CONCURRENT_USERS="50"
export UI_SESSION_TIMEOUT="3600"            # Session timeout in seconds
export UI_SHARED_COMMAND_HISTORY="true"

# Security and authentication
export UI_AUTH_METHOD="session"             # session|token|none
export UI_SESSION_SECRET="your_session_secret"
export UI_CORS_ORIGINS="*"                  # Comma-separated origins
export UI_RATE_LIMIT="1000"                 # Requests per hour per user

# SSL/TLS configuration
export UI_HTTPS_ENABLED="false"             # Enable HTTPS
export UI_SSL_CERT_PATH="/path/to/cert.pem"
export UI_SSL_KEY_PATH="/path/to/key.pem"
export UI_SSL_REDIRECT="true"               # Redirect HTTP to HTTPS

# Development settings
export UI_DEV_MODE="false"                  # Enable development features
export UI_HOT_RELOAD="false"                # Enable hot module replacement
export UI_DEBUG_MODE="false"                # Enable debug logging
export UI_SOURCE_MAPS="false"               # Generate source maps

# Performance optimization
export UI_CACHE_ENABLED="true"
export UI_CACHE_TTL="3600"                  # Cache TTL in seconds
export UI_COMPRESSION_ENABLED="true"
export UI_STATIC_CDN_URL=""                 # CDN URL for static assets

# Mobile and PWA settings
export UI_PWA_NAME="Agent-Workflow Portal"
export UI_PWA_SHORT_NAME="AgentWorkflow"
export UI_PWA_THEME_COLOR="#1976d2"
export UI_PWA_BACKGROUND_COLOR="#ffffff"
export UI_OFFLINE_SUPPORT="true"
export UI_PUSH_NOTIFICATIONS="true"

# Integration settings
export UI_CLI_SYNC_ENABLED="true"           # Enable CLI-UI synchronization
export UI_DISCORD_MIRROR="true"             # Mirror Discord commands
export UI_CONFIG_HOT_RELOAD="true"          # Auto-reload configuration
export UI_STATE_BROADCAST="true"            # Real-time state broadcasting

# Network and browser settings
export UI_NETWORK_AUTO_DETECT="true"        # Auto-detect network interfaces
export UI_BROWSER_AUTO_LAUNCH="true"        # Auto-launch browser
export UI_PREFERRED_BROWSER=""              # chrome|firefox|safari|edge
export UI_BROWSER_DEV_TOOLS="false"         # Open with dev tools
```

### TDD-Specific Variables
```bash
# TDD configuration
export TDD_ENABLED="true"
export TDD_AUTO_START="true"
export TDD_PRESERVE_TESTS="true"
export TDD_PARALLEL_EXECUTION="true"

# Test execution
export TEST_RUNNER="pytest"
export TEST_PARALLEL_JOBS="4"
export TEST_TIMEOUT_SECONDS="300"
export COVERAGE_THRESHOLD="90"

# Test preservation
export TEST_PRESERVATION_DIR="tests/tdd"
export TEST_INTEGRATION_DIR="tests/unit"
export TEST_BACKUP_ENABLED="true"
```

## Configuration File Locations

### Standard Locations
```bash
# Main configuration
./config.yml                          # Default configuration
./config/production.yml               # Production configuration
./config/development.yml              # Development configuration

# Project-specific
./.orch-state/config.json             # Project runtime configuration
./.orch-state/status.json             # Project state

# User configuration
~/.agent-workflow/config.yml          # User global configuration
~/.agent-workflow/preferences.yml     # User preferences

# Environment-specific
/etc/agent-workflow/config.yml        # System-wide configuration
/opt/agent-workflow/config.yml        # Installation configuration
```

## Exit Codes

The CLI tools use standard exit codes:

```bash
0   Success
1   General error
2   Configuration error
3   Permission error
4   Network error
5   API error
10  Validation error
20  Agent execution error
30  TDD cycle error
50  System resource error
99  Unknown error
```

## Troubleshooting CLI Issues

### Common Problems

#### Command Not Found
```bash
# Check Python path
python -c "import sys; print(sys.path)"

# Verify script permissions
ls -la scripts/orchestrator.py

# Check virtual environment
which python
echo $VIRTUAL_ENV
```

#### Permission Errors
```bash
# Fix script permissions
chmod +x scripts/*.py

# Check file ownership
ls -la config/
sudo chown -R $USER:$USER .
```

#### Configuration Errors
```bash
# Validate configuration
python scripts/config_manager.py validate config.yml

# Check environment variables
env | grep -E "(DISCORD|ANTHROPIC|GITHUB)"

# Test basic imports
python -c "import lib.discord_bot; print('OK')"
```

#### Performance Issues
```bash
# Check system resources
top -p $(pgrep -f orchestrator)
df -h
free -m

# Enable debug logging
export LOG_LEVEL=DEBUG
python scripts/orchestrator.py --debug
```

This comprehensive CLI reference provides complete documentation for all command-line interfaces and operational tools in the AI Agent TDD-Scrum workflow system.