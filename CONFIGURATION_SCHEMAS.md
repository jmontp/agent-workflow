# Configuration Schemas and Management

## Overview
Comprehensive configuration schema definitions, validation rules, and management strategies for the agent-workflow package.

## 1. Global Configuration Schema

### 1.1 Main Configuration File
**Location**: `~/.agent-workflow/config.yaml`

```yaml
# Global Configuration Schema
version: "1.0"                           # Configuration schema version
created: "2024-01-15T10:30:00Z"         # ISO 8601 timestamp
last_updated: "2024-01-15T15:45:00Z"    # ISO 8601 timestamp

# Installation metadata
installation:
  id: "uuid-v4-string"                  # Unique installation identifier
  method: "pip"                         # pip, git, docker, source
  package_version: "1.2.3"             # Installed version
  python_version: "3.11.5"             # Python interpreter version
  platform: "linux"                    # linux, windows, macos
  
# User profile and defaults
global:
  user_profile: "solo-engineer"         # solo-engineer, team-lead, researcher, custom
  default_mode: "blocking"              # blocking, partial, autonomous
  log_level: "INFO"                     # DEBUG, INFO, WARN, ERROR, CRITICAL
  data_retention_days: 30               # Log and temp file retention
  max_concurrent_projects: 5            # Maximum simultaneous projects
  auto_discovery: false                 # Auto-discover projects in filesystem
  session_timeout: 3600                 # Session timeout in seconds
  
# AI provider configuration
ai_provider:
  provider: "claude"                    # claude, openai, azure-openai, local, custom
  model: "claude-3.5-sonnet"           # Default model identifier
  api_endpoint: null                    # Custom endpoint (for local/custom)
  api_version: "2023-06-01"            # API version string
  organization: null                    # Organization ID (OpenAI)
  project: null                         # Project ID (OpenAI)
  
  # Rate limiting configuration
  rate_limit:
    requests_per_minute: 50             # API requests per minute
    tokens_per_minute: 100000           # Token limit per minute
    daily_request_limit: 10000          # Daily request cap
    cost_limit_daily: 50.00             # Daily cost limit in USD
    
  # Model-specific settings
  model_settings:
    temperature: 0.1                    # Generation temperature (0.0-2.0)
    max_tokens: 4096                    # Maximum response tokens
    timeout: 30                         # Request timeout in seconds
    retry_attempts: 3                   # Failed request retries
    
  # Credential storage reference
  credentials_encrypted: true           # Whether credentials are encrypted
  credential_key: "ai_provider_key"     # Key name in credential store

# Discord integration
discord:
  enabled: true                         # Enable Discord integration
  guild_id: "1234567890123456789"      # Discord server ID
  
  # Channel configuration
  channels:
    prefix: "orch"                      # Channel name prefix
    create_automatically: true          # Auto-create project channels
    archive_on_completion: false        # Archive channels when projects complete
    category_name: "Agent Workflow"     # Channel category name
    
  # Bot configuration
  bot:
    status_message: "Orchestrating AI agents" # Bot status message
    activity_type: "watching"           # playing, streaming, listening, watching
    command_prefix: "/"                 # Slash command prefix
    sync_commands_on_start: true        # Sync slash commands on startup
    
  # Permissions and security
  permissions:
    required_permissions: [             # Required Discord permissions
      "send_messages",
      "manage_channels", 
      "embed_links",
      "add_reactions",
      "use_slash_commands",
      "manage_messages"
    ]
    admin_roles: []                     # Role IDs with admin access
    allowed_users: []                   # User IDs with access (empty = all)
    allowed_channels: []                # Channel IDs where bot works (empty = all)
    
  # Credential storage reference  
  credentials_encrypted: true
  credential_key: "discord_bot_token"

# GitHub integration
github:
  enabled: true                         # Enable GitHub integration
  api_endpoint: "https://api.github.com" # GitHub API endpoint
  
  # Authentication
  auth_method: "token"                  # token, app, oauth
  credentials_encrypted: true
  credential_key: "github_token"
  
  # Repository settings
  repositories:
    auto_detect: true                   # Auto-detect git remotes
    default_branch: "main"              # Default branch name
    
  # Pull request settings
  pull_requests:
    auto_create: true                   # Auto-create PRs for agent work
    draft_by_default: false             # Create draft PRs
    auto_merge: false                   # Auto-merge approved PRs
    require_reviews: true               # Require human review
    
# Security configuration
security:
  # Agent access control
  agent_restrictions_enabled: true      # Enable agent command restrictions
  command_approval_required: true       # Require human approval for commands
  dangerous_commands_blocked: true      # Block potentially dangerous commands
  
  # Credential encryption
  credential_encryption:
    algorithm: "Fernet"                 # Encryption algorithm
    key_derivation: "PBKDF2"           # Key derivation function
    iterations: 100000                  # Key derivation iterations
    key_file: "credentials.key"         # Encryption key file name
    
  # Audit logging
  audit_logging:
    enabled: true                       # Enable security audit logs
    log_commands: true                  # Log all executed commands
    log_file_access: true              # Log file access operations
    log_api_calls: true                # Log external API calls
    retention_days: 90                 # Audit log retention period
    
  # Network security
  network:
    allowed_domains: []                 # Allowed external domains (empty = all)
    blocked_domains: [                  # Blocked domains
      "malicious-site.com"
    ]
    use_proxy: false                    # Use HTTP proxy
    proxy_url: null                     # Proxy URL if enabled
    
# Project management
projects:
  registry_path: "projects"             # Relative path to project registry
  auto_discovery: false                 # Auto-discover projects
  discovery_paths: [                    # Paths to search for projects
    "~/workspace",
    "~/projects"
  ]
  validation_on_register: true          # Validate projects on registration
  max_concurrent: 5                     # Maximum concurrent active projects
  state_sync_interval: 60               # State sync interval in seconds
  
  # Default project settings
  defaults:
    mode: "blocking"                    # Default orchestration mode
    framework: "general"                # Default project framework
    create_discord_channel: true        # Create Discord channel by default
    enable_monitoring: true             # Enable project monitoring
    
# Monitoring and observability
monitoring:
  enabled: true                         # Enable system monitoring
  
  # Metrics collection
  metrics:
    collect_performance: true           # Collect performance metrics
    collect_usage: true                 # Collect usage statistics
    collect_errors: true                # Collect error metrics
    retention_days: 30                  # Metrics retention period
    
  # Health checks
  health_checks:
    enabled: true                       # Enable health monitoring
    interval: 300                       # Health check interval in seconds
    checks: [                          # Enabled health checks
      "disk_space",
      "memory_usage", 
      "api_connectivity",
      "discord_connection",
      "project_accessibility"
    ]
    
  # Alerting
  alerting:
    enabled: false                      # Enable alerting system
    channels: ["discord", "email"]      # Alert channels
    thresholds:
      error_rate: 0.05                  # Error rate threshold (5%)
      response_time: 5.0                # Response time threshold (5s)
      disk_usage: 0.9                   # Disk usage threshold (90%)
      
# Plugin system
plugins:
  enabled: true                         # Enable plugin system
  auto_load: true                       # Auto-load plugins on startup
  plugin_directory: "plugins"           # Plugin directory name
  allowed_sources: [                    # Allowed plugin sources
    "official",
    "community", 
    "local"
  ]
  signature_verification: true          # Verify plugin signatures
  
# Advanced features
advanced:
  # Experimental features
  experimental:
    parallel_execution: false           # Enable parallel agent execution
    context_compression: true           # Enable context compression
    smart_retries: true                 # Enable intelligent retry logic
    
  # Performance tuning
  performance:
    worker_threads: 4                   # Number of background worker threads
    cache_size: 100                     # LRU cache size (MB)
    batch_size: 10                      # Batch processing size
    
  # Development options
  development:
    debug_mode: false                   # Enable debug mode
    mock_integrations: false            # Use mock integrations for testing
    trace_api_calls: false              # Trace all API calls
```

### 1.2 Configuration Validation Schema

```python
# JSON Schema for validation
GLOBAL_CONFIG_SCHEMA = {
    "type": "object",
    "required": ["version", "installation", "global"],
    "properties": {
        "version": {
            "type": "string",
            "pattern": r"^\d+\.\d+$"
        },
        "installation": {
            "type": "object",
            "required": ["id", "method", "package_version"],
            "properties": {
                "id": {"type": "string", "format": "uuid"},
                "method": {"enum": ["pip", "git", "docker", "source"]},
                "package_version": {"type": "string", "pattern": r"^\d+\.\d+\.\d+"},
                "python_version": {"type": "string"},
                "platform": {"enum": ["linux", "windows", "macos"]}
            }
        },
        "global": {
            "type": "object",
            "required": ["user_profile", "default_mode"],
            "properties": {
                "user_profile": {"enum": ["solo-engineer", "team-lead", "researcher", "custom"]},
                "default_mode": {"enum": ["blocking", "partial", "autonomous"]},
                "log_level": {"enum": ["DEBUG", "INFO", "WARN", "ERROR", "CRITICAL"]},
                "data_retention_days": {"type": "integer", "minimum": 1, "maximum": 365},
                "max_concurrent_projects": {"type": "integer", "minimum": 1, "maximum": 50},
                "session_timeout": {"type": "integer", "minimum": 300, "maximum": 86400}
            }
        },
        "ai_provider": {
            "type": "object", 
            "required": ["provider", "model"],
            "properties": {
                "provider": {"enum": ["claude", "openai", "azure-openai", "local", "custom"]},
                "model": {"type": "string", "minLength": 1},
                "rate_limit": {
                    "type": "object",
                    "properties": {
                        "requests_per_minute": {"type": "integer", "minimum": 1},
                        "tokens_per_minute": {"type": "integer", "minimum": 100},
                        "daily_request_limit": {"type": "integer", "minimum": 100},
                        "cost_limit_daily": {"type": "number", "minimum": 0}
                    }
                }
            }
        },
        "discord": {
            "type": "object",
            "properties": {
                "enabled": {"type": "boolean"},
                "guild_id": {"type": "string", "pattern": r"^\d{17,19}$"},
                "channels": {
                    "type": "object",
                    "properties": {
                        "prefix": {"type": "string", "pattern": r"^[a-z0-9-]{1,20}$"}
                    }
                }
            }
        }
    }
}
```

## 2. Project Configuration Schema

### 2.1 Project Registry
**Location**: `~/.agent-workflow/projects/registry.yaml`

```yaml
# Project Registry Schema
version: "1.0"
created: "2024-01-15T10:30:00Z"
last_updated: "2024-01-15T15:45:00Z"

# Global project settings
settings:
  auto_sync: true                       # Auto-sync project states
  backup_enabled: true                  # Enable project backups
  concurrent_limit: 5                   # Maximum concurrent projects
  
# Registered projects
projects:
  webapp:
    # Basic information
    name: "webapp"                      # Project display name
    path: "/home/user/projects/webapp"  # Absolute path to project
    registered: "2024-01-15T10:30:00Z" # Registration timestamp
    last_active: "2024-01-15T15:45:00Z"# Last activity timestamp
    
    # Configuration
    mode: "partial"                     # blocking, partial, autonomous
    framework: "web"                    # web, api, ml, mobile, desktop, general
    language: "python"                  # Primary programming language
    status: "active"                    # active, idle, paused, error, archived
    
    # Integration settings
    discord:
      channel_id: "1234567890123456789" # Discord channel ID
      channel_name: "#orch-webapp"      # Channel name
      created: "2024-01-15T10:35:00Z"  # Channel creation time
      
    github:
      repository: "https://github.com/user/webapp" # Repository URL
      default_branch: "main"            # Default branch
      auto_pr: true                     # Auto-create pull requests
      
    # Project metadata
    metadata:
      description: "E-commerce web application" # Project description
      version: "1.2.0"                 # Current version
      maintainer: "user@example.com"   # Project maintainer
      tags: ["web", "ecommerce", "python", "flask"] # Project tags
      
    # Framework-specific settings
    framework_config:
      web:
        port: 5000                      # Development server port
        static_dir: "static"            # Static files directory
        template_dir: "templates"       # Template directory
        
    # State management
    state:
      current: "SPRINT_ACTIVE"          # Current state machine state
      last_transition: "2024-01-15T14:00:00Z" # Last state change
      state_file: ".orch-state/status.json" # State file path
      
    # Monitoring and health
    health:
      last_check: "2024-01-15T15:45:00Z" # Last health check
      status: "healthy"                 # healthy, warning, error
      issues: []                        # Current health issues
      
    # Agent assignments
    agents:
      design: "enabled"                 # Design agent status
      code: "enabled"                   # Code agent status  
      qa: "enabled"                     # QA agent status
      data: "disabled"                  # Data agent status
      
  # Second project example
  api-project:
    name: "api-project"
    path: "/home/user/projects/api"
    registered: "2024-01-14T09:15:00Z"
    last_active: "2024-01-15T14:30:00Z"
    mode: "blocking"
    framework: "api"
    language: "python"
    status: "idle"
    
    discord:
      channel_id: "9876543210987654321"
      channel_name: "#orch-api-project"
      created: "2024-01-14T09:20:00Z"
      
    github:
      repository: "https://github.com/user/api"
      default_branch: "main"
      auto_pr: false
      
    metadata:
      description: "REST API service"
      version: "0.8.0"
      maintainer: "user@example.com"
      tags: ["api", "rest", "python", "fastapi"]
      
    framework_config:
      api:
        port: 8000
        docs_url: "/docs"
        openapi_url: "/openapi.json"
        
    state:
      current: "BACKLOG_READY"
      last_transition: "2024-01-15T13:00:00Z"
      state_file: ".orch-state/status.json"
      
    health:
      last_check: "2024-01-15T15:30:00Z"
      status: "warning"
      issues: ["uncommitted_changes"]
      
    agents:
      design: "enabled"
      code: "enabled"
      qa: "enabled" 
      data: "enabled"

# Registry statistics
statistics:
  total_projects: 2
  active_projects: 1
  frameworks:
    web: 1
    api: 1
  languages:
    python: 2
```

### 2.2 Individual Project Configuration
**Location**: `{project_path}/.orch-state/config.yaml`

```yaml
# Individual Project Configuration
project:
  name: "webapp"
  type: "web"
  version: "1.2.0"
  
# Orchestration settings
orchestration:
  mode: "partial"                       # Overrides global default
  auto_commit: true                     # Auto-commit agent changes
  require_approval: true                # Require human approval
  notification_level: "important"       # all, important, errors, none
  
# Agent configuration
agents:
  design:
    enabled: true
    permissions: ["read", "document"]
    tools: ["web_fetch", "file_read", "diagram_create"]
    
  code: 
    enabled: true
    permissions: ["read", "write", "commit"]
    tools: ["file_edit", "git_commit", "test_run"]
    restrictions: ["no_delete", "no_push"]
    
  qa:
    enabled: true
    permissions: ["read", "test"]
    tools: ["test_run", "coverage_report", "lint_check"]
    
  data:
    enabled: false
    permissions: ["read"]
    tools: ["data_analyze", "visualize"]

# State machine configuration
state_machine:
  initial_state: "IDLE"
  timeout_minutes: 30                   # State timeout
  auto_transitions: true                # Allow automatic transitions
  
  # Custom state hooks
  hooks:
    on_enter_sprint_active:
      - "notify_discord"
      - "update_github_status"
    on_exit_sprint_review:
      - "archive_sprint_data"
      - "generate_report"

# Integration overrides
integrations:
  discord:
    notifications:
      state_changes: true
      agent_actions: true
      errors: true
      completions: true
      
  github:
    branch_protection: true
    auto_pr_creation: true
    pr_template: ".github/PULL_REQUEST_TEMPLATE.md"
    
# Custom workflows
workflows:
  feature_development:
    steps:
      - "design_review"
      - "implementation"
      - "testing"
      - "code_review"
      - "deployment"
    parallel_agents: false
    
  bug_fix:
    steps:
      - "investigation" 
      - "fix_implementation"
      - "regression_testing"
    parallel_agents: true

# Project-specific settings
project_settings:
  web:
    development_server:
      host: "localhost"
      port: 5000
      debug: true
      auto_reload: true
      
    testing:
      framework: "pytest"
      coverage_threshold: 80
      parallel_tests: true
      
    deployment:
      target: "production"
      health_check_url: "/health"
      rollback_enabled: true
```

## 3. Credential Management Schema

### 3.1 Encrypted Credentials File
**Location**: `~/.agent-workflow/credentials.enc`

```python
# Credential storage structure (encrypted)
{
    "version": "1.0",
    "algorithm": "Fernet", 
    "created": "2024-01-15T10:30:00Z",
    "last_updated": "2024-01-15T15:45:00Z",
    "credentials": {
        "ai_provider_key": {
            "type": "api_key",
            "provider": "claude",
            "encrypted_value": "gAAAAABh...", # Fernet encrypted
            "created": "2024-01-15T10:30:00Z",
            "last_used": "2024-01-15T15:45:00Z",
            "metadata": {
                "description": "Claude API key",
                "scope": "global",
                "expires": null
            }
        },
        "discord_bot_token": {
            "type": "oauth_token",
            "provider": "discord", 
            "encrypted_value": "gAAAAABh...",
            "created": "2024-01-15T10:32:00Z",
            "last_used": "2024-01-15T15:44:00Z",
            "metadata": {
                "description": "Discord bot token",
                "scope": "bot",
                "expires": null,
                "permissions": ["bot", "slash_commands"]
            }
        },
        "github_token": {
            "type": "personal_access_token",
            "provider": "github",
            "encrypted_value": "gAAAAABh...",
            "created": "2024-01-15T10:34:00Z", 
            "last_used": "2024-01-15T15:30:00Z",
            "metadata": {
                "description": "GitHub personal access token",
                "scope": "repo,workflow",
                "expires": "2025-01-15T00:00:00Z"
            }
        }
    }
}
```

### 3.2 Encryption Key Management
**Location**: `~/.agent-workflow/credentials.key`

```python
# Key derivation and storage
class CredentialEncryption:
    def __init__(self, password: str = None):
        if password is None:
            password = self._generate_machine_key()
        
        # Derive key using PBKDF2
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=self._get_salt(),
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
        self.fernet = Fernet(key)
    
    def _generate_machine_key(self) -> str:
        """Generate key from machine characteristics"""
        import platform, getpass, socket
        machine_info = f"{platform.node()}{getpass.getuser()}{socket.gethostname()}"
        return hashlib.sha256(machine_info.encode()).hexdigest()
```

## 4. Profile-Based Configuration Templates

### 4.1 Solo Engineer Profile
```yaml
# ~/.agent-workflow/profiles/solo-engineer.yaml
profile_name: "solo-engineer"
description: "Optimized for individual developers working with AI assistance"

defaults:
  global:
    default_mode: "blocking"
    max_concurrent_projects: 3
    session_timeout: 1800
    
  ai_provider:
    rate_limit:
      requests_per_minute: 30
      cost_limit_daily: 20.00
      
  discord:
    channels:
      create_automatically: true
      archive_on_completion: true
      
  security:
    command_approval_required: true
    dangerous_commands_blocked: true
    
  projects:
    defaults:
      mode: "blocking"
      create_discord_channel: true
      enable_monitoring: true
      
workflow_templates:
  feature_development:
    approval_gates: ["design", "implementation", "testing"]
    parallel_execution: false
    
  bug_fix:
    approval_gates: ["investigation", "fix"]
    parallel_execution: true
```

### 4.2 Team Lead Profile  
```yaml
# ~/.agent-workflow/profiles/team-lead.yaml
profile_name: "team-lead"
description: "Optimized for team leaders managing multiple projects"

defaults:
  global:
    default_mode: "partial"
    max_concurrent_projects: 10
    session_timeout: 3600
    
  ai_provider:
    rate_limit:
      requests_per_minute: 100
      cost_limit_daily: 100.00
      
  discord:
    channels:
      create_automatically: true
      archive_on_completion: false
      category_name: "Team Projects"
      
  security:
    command_approval_required: false
    audit_logging:
      enabled: true
      retention_days: 180
      
  monitoring:
    enabled: true
    alerting:
      enabled: true
      channels: ["discord", "email"]
      
workflow_templates:
  team_feature:
    approval_gates: ["architecture_review"]
    parallel_execution: true
    delegation_enabled: true
    
  release_preparation:
    approval_gates: ["qa_signoff", "security_review"]
    automated_testing: true
```

### 4.3 Researcher Profile
```yaml  
# ~/.agent-workflow/profiles/researcher.yaml
profile_name: "researcher"
description: "Optimized for research and experimentation"

defaults:
  global:
    default_mode: "autonomous"
    max_concurrent_projects: 2
    data_retention_days: 90
    
  ai_provider:
    model_settings:
      temperature: 0.3
      max_tokens: 8192
    rate_limit:
      requests_per_minute: 60
      cost_limit_daily: 50.00
      
  advanced:
    experimental:
      parallel_execution: true
      context_compression: true
      smart_retries: true
      
  monitoring:
    metrics:
      collect_performance: true
      collect_usage: true
      retention_days: 90
      
workflow_templates:
  experiment:
    approval_gates: []
    parallel_execution: true
    data_collection: true
    
  analysis:
    approval_gates: ["methodology_review"]
    automated_reporting: true
```

## 5. Configuration Management System

### 5.1 Configuration Loader
```python
class ConfigurationManager:
    def __init__(self, config_dir: Path):
        self.config_dir = config_dir
        self.config_file = config_dir / "config.yaml"
        self.schema_validator = SchemaValidator()
        
    def load_configuration(self) -> Dict[str, Any]:
        """Load and validate configuration"""
        if not self.config_file.exists():
            raise ConfigurationError("Configuration file not found")
            
        with open(self.config_file) as f:
            config = yaml.safe_load(f)
            
        # Validate against schema
        self.schema_validator.validate(config, GLOBAL_CONFIG_SCHEMA)
        
        # Apply profile defaults
        if config.get("global", {}).get("user_profile"):
            config = self._apply_profile_defaults(config)
            
        return config
        
    def save_configuration(self, config: Dict[str, Any]) -> None:
        """Validate and save configuration"""
        self.schema_validator.validate(config, GLOBAL_CONFIG_SCHEMA)
        
        config["last_updated"] = datetime.now(timezone.utc).isoformat()
        
        with open(self.config_file, 'w') as f:
            yaml.dump(config, f, default_flow_style=False, sort_keys=False)
            
    def merge_configuration(self, updates: Dict[str, Any]) -> Dict[str, Any]:
        """Merge configuration updates"""
        current = self.load_configuration()
        merged = self._deep_merge(current, updates)
        return merged
```

### 5.2 Schema Validation
```python
class SchemaValidator:
    def __init__(self):
        self.schemas = {
            "global": GLOBAL_CONFIG_SCHEMA,
            "project": PROJECT_CONFIG_SCHEMA,
            "credentials": CREDENTIALS_SCHEMA
        }
        
    def validate(self, data: Dict[str, Any], schema: Dict[str, Any]) -> None:
        """Validate data against JSON schema"""
        try:
            jsonschema.validate(instance=data, schema=schema)
        except jsonschema.ValidationError as e:
            raise ConfigurationError(f"Configuration validation failed: {e.message}")
            
    def validate_configuration_file(self, file_path: Path, schema_type: str) -> List[str]:
        """Validate configuration file and return issues"""
        issues = []
        
        try:
            with open(file_path) as f:
                data = yaml.safe_load(f)
                
            self.validate(data, self.schemas[schema_type])
            
        except yaml.YAMLError as e:
            issues.append(f"YAML syntax error: {e}")
        except ConfigurationError as e:
            issues.append(str(e))
        except FileNotFoundError:
            issues.append(f"Configuration file not found: {file_path}")
            
        return issues
```

### 5.3 Migration System
```python
class ConfigurationMigrator:
    def __init__(self):
        self.migrations = {
            "0.9": self._migrate_from_0_9,
            "1.0": self._migrate_from_1_0
        }
        
    def migrate_configuration(self, old_config: Dict[str, Any], 
                            old_version: str) -> Dict[str, Any]:
        """Migrate configuration from old version"""
        if old_version not in self.migrations:
            raise ConfigurationError(f"No migration path from version {old_version}")
            
        return self.migrations[old_version](old_config)
        
    def _migrate_from_0_9(self, old_config: Dict[str, Any]) -> Dict[str, Any]:
        """Migrate from version 0.9.x"""
        new_config = {
            "version": "1.0",
            "created": datetime.now(timezone.utc).isoformat(),
            "installation": {
                "id": str(uuid.uuid4()),
                "method": "migration",
                "package_version": "1.0.0"
            }
        }
        
        # Map old structure to new structure
        if "orchestrator" in old_config:
            new_config["global"] = {
                "user_profile": "solo-engineer",  # Default for old installs
                "default_mode": old_config["orchestrator"].get("mode", "blocking")
            }
            
        return new_config
```

This comprehensive configuration system provides robust schema validation, profile-based defaults, credential encryption, and smooth migration paths while maintaining flexibility for different use cases and deployment scenarios.