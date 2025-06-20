#!/bin/bash

# Agent Workflow Configuration Setup Script
# This script helps you create your initial configuration files

set -e

echo "🚀 Agent Workflow Configuration Setup"
echo "======================================"
echo

# Check if running from correct directory
if [ ! -f "pyproject.toml" ] || [ ! -f ".env.example" ]; then
    echo "❌ Error: Please run this script from the agent-workflow root directory"
    exit 1
fi

# Function to prompt for input with default value
prompt_with_default() {
    local prompt="$1"
    local default="$2"
    local var_name="$3"
    
    echo -n "$prompt"
    if [ -n "$default" ]; then
        echo -n " (default: $default)"
    fi
    echo -n ": "
    
    read -r input
    if [ -z "$input" ] && [ -n "$default" ]; then
        input="$default"
    fi
    
    eval "$var_name='$input'"
}

# Function to generate random string
generate_random() {
    openssl rand -hex 32 2>/dev/null || python3 -c "import secrets; print(secrets.token_hex(32))" 2>/dev/null || echo "change_me_$(date +%s)"
}

echo "This script will help you create your configuration files."
echo "You can press Enter to accept default values or provide your own."
echo

# Check for existing config files
if [ -f ".env" ]; then
    echo "⚠️  .env file already exists. Creating backup..."
    cp .env .env.backup.$(date +%s)
    echo "   Backup created: .env.backup.$(date +%s)"
fi

if [ -f "config.yml" ]; then
    echo "⚠️  config.yml file already exists. Creating backup..."
    cp config.yml config.yml.backup.$(date +%s)
    echo "   Backup created: config.yml.backup.$(date +%s)"
fi

echo

# Collect configuration information
echo "📋 Configuration Information"
echo "----------------------------"

# Project settings
prompt_with_default "Project name" "my-project" PROJECT_NAME
prompt_with_default "Project path" "$(pwd)" PROJECT_PATH
prompt_with_default "Orchestration mode (blocking/partial/autonomous)" "blocking" ORCHESTRATION_MODE

# Discord settings
echo
echo "🤖 Discord Bot Configuration"
echo "Get your bot token from: https://discord.com/developers/applications"
prompt_with_default "Discord bot token (leave empty to skip)" "" DISCORD_BOT_TOKEN

# AI Provider settings
echo
echo "🧠 AI Provider Configuration"
echo "Choose your AI provider:"
echo "1. Claude (Anthropic) - Recommended"
echo "2. OpenAI"
echo "3. Skip for now"
prompt_with_default "AI Provider choice (1/2/3)" "1" AI_PROVIDER_CHOICE

case $AI_PROVIDER_CHOICE in
    1)
        echo "Get your Claude API key from: https://console.anthropic.com/"
        prompt_with_default "Anthropic API key (leave empty to skip)" "" ANTHROPIC_API_KEY
        ;;
    2)
        echo "Get your OpenAI API key from: https://platform.openai.com/api-keys"
        prompt_with_default "OpenAI API key (leave empty to skip)" "" OPENAI_API_KEY
        ;;
    *)
        echo "Skipping AI provider configuration..."
        ;;
esac

# Optional GitHub integration
echo
echo "🔗 GitHub Integration (Optional)"
echo "Get a personal access token from: https://github.com/settings/tokens"
prompt_with_default "GitHub token (leave empty to skip)" "" GITHUB_TOKEN

# Generate security keys
echo
echo "🔐 Generating Security Keys"
SECRET_KEY=$(generate_random)
JWT_SECRET=$(generate_random)
echo "   Generated SECRET_KEY: ${SECRET_KEY:0:10}..."
echo "   Generated JWT_SECRET: ${JWT_SECRET:0:10}..."

# Create .env file
echo
echo "📝 Creating .env file..."
cat > .env << EOF
# Agent Workflow Environment Configuration
# Generated on $(date)

# ====================================================================
# DISCORD BOT CONFIGURATION
# ====================================================================
DISCORD_BOT_TOKEN=${DISCORD_BOT_TOKEN}

# ====================================================================
# AI PROVIDER CONFIGURATION
# ====================================================================
EOF

if [ -n "$ANTHROPIC_API_KEY" ]; then
    echo "ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}" >> .env
fi

if [ -n "$OPENAI_API_KEY" ]; then
    echo "OPENAI_API_KEY=${OPENAI_API_KEY}" >> .env
fi

cat >> .env << EOF

# ====================================================================
# GITHUB INTEGRATION
# ====================================================================
GITHUB_TOKEN=${GITHUB_TOKEN}

# ====================================================================
# SECURITY SETTINGS
# ====================================================================
SECRET_KEY=${SECRET_KEY}
JWT_SECRET=${JWT_SECRET}

# ====================================================================
# DEVELOPMENT SETTINGS
# ====================================================================
ENVIRONMENT=development
DEBUG=true
WEB_PORT=8080
API_PORT=8081
EOF

echo "   ✅ .env file created"

# Create config.yml file
echo
echo "📝 Creating config.yml file..."
cat > config.yml << EOF
# Agent Workflow Configuration
# Generated on $(date)

orchestrator:
  mode: ${ORCHESTRATION_MODE}
  project_path: "${PROJECT_PATH}"
  project_name: "${PROJECT_NAME}"
  max_concurrent_agents: 3
  agent_timeout_minutes: 30

discord:
  auto_create_channels: true
  max_commands_per_minute: 20
  response_timeout_seconds: 30
  enable_notifications: true
  notification_events:
    - sprint_start
    - task_complete
    - approval_needed
    - error_alerts

tdd:
  enabled: true
  auto_start_cycles: true
  preserve_tests: true
  parallel_execution: false
  timeouts:
    design_phase_minutes: 30
    test_red_phase_minutes: 45
    code_green_phase_minutes: 60
    refactor_phase_minutes: 30
    commit_phase_minutes: 15
  test_execution:
    runner: "pytest"
    parallel_jobs: 4
    timeout_seconds: 300
    coverage_threshold: 90

agents:
  default_timeout_minutes: 30
  max_retries: 3
  design_agent:
    detail_level: "standard"
  qa_agent:
    test_types: ["unit", "integration"]
  code_agent:
    implementation_style: "minimal"

security:
  enable_project_isolation: true
  enforce_agent_restrictions: true

logging:
  level: INFO
  orchestrator_log: "logs/orchestrator.log"
  agent_log: "logs/agents.log"
  discord_log: "logs/discord-bot.log"

development:
  debug_mode: false
  mock_mode: false
  web_interface:
    enabled: true
    host: "localhost"
    port: 8080
EOF

echo "   ✅ config.yml file created"

# Create logs directory
echo
echo "📁 Creating logs directory..."
mkdir -p logs
echo "   ✅ logs directory created"

# Set proper permissions
echo
echo "🔒 Setting file permissions..."
chmod 600 .env
chmod 644 config.yml
echo "   ✅ Permissions set (.env: 600, config.yml: 644)"

# Verification
echo
echo "🔍 Verifying Configuration"
echo "-------------------------"

# Check if agent-orch command is available
if command -v agent-orch >/dev/null 2>&1; then
    echo "   ✅ agent-orch command found"
    
    # Test configuration
    echo "   🧪 Testing configuration..."
    if agent-orch health --config config.yml >/dev/null 2>&1; then
        echo "   ✅ Configuration test passed"
    else
        echo "   ⚠️  Configuration test failed (this is normal if APIs aren't configured yet)"
    fi
else
    echo "   ⚠️  agent-orch command not found. Please install with: pip install agent-workflow"
fi

# Summary
echo
echo "🎉 Configuration Setup Complete!"
echo "================================"
echo
echo "📁 Created files:"
echo "   • .env (environment variables)"
echo "   • config.yml (main configuration)"
echo "   • logs/ (log directory)"
echo
echo "🔐 Security notes:"
echo "   • .env file contains sensitive information"
echo "   • File permissions have been set appropriately"
echo "   • .env is excluded from git (see .gitignore)"
echo
echo "🚀 Next steps:"
echo "   1. Review and edit .env file if needed"
echo "   2. Review and edit config.yml file if needed"
echo "   3. Test installation: agent-orch version"
echo "   4. Test configuration: agent-orch health"
echo "   5. Initialize system: agent-orch init"
echo "   6. Start orchestration: agent-orch start"
echo
echo "📚 Documentation:"
echo "   • Configuration guide: docs/getting-started/configuration.md"
echo "   • Discord setup: docs/deployment/discord-setup.md"
echo "   • Quick start: docs/getting-started/quick-start.md"
echo

if [ -n "$DISCORD_BOT_TOKEN" ]; then
    echo "🤖 Discord Bot Ready:"
    echo "   • Token configured in .env"
    echo "   • Start bot: python lib/discord_bot.py"
    echo "   • Test in Discord: /state"
    echo
fi

echo "Happy orchestrating! 🎯"