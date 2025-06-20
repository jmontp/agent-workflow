# Configuration Templates

This directory contains essential configuration templates for the AI Agent Workflow system. These templates provide a starting point for setting up your environment with sensible defaults and security best practices.

## Template Files

### 🔐 `.env.example`
**Environment Variables Template**

Contains all environment variables needed for the system including:
- Discord bot token
- AI provider API keys (Claude, OpenAI)
- GitHub integration token
- Security keys and secrets
- Development settings

**Usage:**
```bash
cp .env.example .env
# Edit .env with your actual values
```

### ⚙️ `config.example.yml`
**Main Configuration Template**

Primary configuration file for orchestration settings:
- Project paths and names
- Orchestration modes (blocking/partial/autonomous)
- TDD workflow settings
- Agent configurations
- Discord integration settings
- Security and logging options

**Usage:**
```bash
cp config.example.yml config.yml
# Edit config.yml for your project
```

### 🤖 `discord-bot.config.example`
**Discord Bot Configuration Template**

Detailed Discord bot settings including:
- Bot identity and branding
- Channel and permission configuration
- Command settings and cooldowns
- Notification preferences
- Role-based access control
- Appearance and formatting options

**Usage:**
```bash
cp discord-bot.config.example discord-bot.config
# Customize Discord-specific settings
```

### 🚀 `setup-config.sh`
**Interactive Setup Script**

Automated configuration script that:
- Guides you through configuration options
- Creates `.env` and `config.yml` files
- Generates secure random keys
- Sets proper file permissions
- Validates the configuration

**Usage:**
```bash
chmod +x setup-config.sh
./setup-config.sh
```

## Quick Start

### Option 1: Automated Setup (Recommended)
```bash
# Run interactive setup
./setup-config.sh
```

### Option 2: Manual Setup
```bash
# Copy templates
cp .env.example .env
cp config.example.yml config.yml

# Edit with your values
nano .env
nano config.yml

# Set permissions
chmod 600 .env
chmod 644 config.yml
```

### Option 3: CLI Setup
```bash
# Use built-in CLI wizard
agent-orch init --interactive
```

## Security Notes

⚠️ **Important Security Practices:**

1. **Never commit actual configuration files:**
   - `.env`, `config.yml`, and `discord-bot.config` are in `.gitignore`
   - Only template files (`.example`) should be committed

2. **File permissions:**
   - `.env` should be `600` (readable only by owner)
   - `config.yml` should be `644` (readable by group)

3. **API keys and tokens:**
   - Use strong, unique tokens for each environment
   - Rotate keys regularly
   - Never share tokens publicly

4. **Generated secrets:**
   - Use cryptographically secure random values
   - Different secrets for development and production

## Configuration Validation

Test your configuration:

```bash
# Basic validation
agent-orch health

# Detailed validation
agent-orch health --verbose

# Test specific components
agent-orch test-discord
agent-orch test-api
```

## Environment-Specific Configurations

### Development
```bash
# .env
ENVIRONMENT=development
DEBUG=true
```

### Production
```bash
# .env
ENVIRONMENT=production
DEBUG=false
```

## Common Configuration Patterns

### Single Project Setup
```yaml
# config.yml
orchestrator:
  mode: blocking
  project_path: "/path/to/project"
  project_name: "my-app"
```

### Multi-Project Setup
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
```

### TDD-Focused Setup
```yaml
# config.yml
tdd:
  enabled: true
  auto_start_cycles: true
  preserve_tests: true
  timeouts:
    design_phase_minutes: 20
    test_red_phase_minutes: 30
    code_green_phase_minutes: 45
```

## Troubleshooting

### Missing Configuration Files
```bash
# Recreate from templates
cp .env.example .env
cp config.example.yml config.yml
```

### Permission Errors
```bash
# Fix file permissions
chmod 600 .env
chmod 644 config.yml
```

### Invalid Configuration
```bash
# Validate YAML syntax
python -c "import yaml; yaml.safe_load(open('config.yml'))"

# Test environment variables
agent-orch health --check-env
```

### API Connection Issues
```bash
# Test individual APIs
agent-orch test-api --provider claude
agent-orch test-api --provider openai
agent-orch test-discord --token-only
```

## Configuration Schema

For advanced users, configuration schemas are available:

- **Environment Schema:** See `.env.example` comments
- **YAML Schema:** See `config.example.yml` structure
- **Validation Rules:** Built into `agent-orch` CLI

## Getting Help

- **Documentation:** [Configuration Guide](docs/getting-started/configuration.md)
- **Discord Setup:** [Discord Setup Guide](docs/deployment/discord-setup.md)
- **CLI Reference:** [CLI Commands](docs/user-guide/cli-reference.md)
- **Troubleshooting:** [Common Issues](docs/user-guide/troubleshooting.md)

## Template Maintenance

These templates are automatically updated with new features. When updating:

1. Check for new variables in `.env.example`
2. Review new sections in `config.example.yml`
3. Update your actual config files as needed
4. Test configuration after updates

---

**Need help?** Run `./setup-config.sh` for an interactive setup experience or check the [documentation](docs/) for detailed guides.