# 🛠️ Operations Guide

Quick operational guidance for common system administration tasks.

## Discord Bot Operations

### Restart Discord Bot

**Quick restart** (most common):
```bash
# Kill current bot process and restart
pkill -f discord_bot.py && python lib/discord_bot.py
```

**Check bot status**:
```bash
# Check if bot process is running
ps aux | grep discord_bot.py | grep -v grep

# Verify Discord token is set
echo $DISCORD_BOT_TOKEN | wc -c  # Should output ~72
```

**Multi-project bot restart**:
```bash
# For multi-project orchestration
pkill -f multi_project_discord_bot.py && python lib/multi_project_discord_bot.py
```

### Discord Bot Troubleshooting

**Bot appears offline**:
1. Check token: `echo $DISCORD_BOT_TOKEN`
2. Restart: `pkill -f discord_bot.py && python lib/discord_bot.py`
3. Check logs: `tail -f logs/discord_bot.log`

**Commands not responding**:
1. Verify bot permissions in Discord server
2. Check slash command registration
3. Restart with: `python lib/discord_bot.py --register-commands`

## File Permission Issues

### Quick Permission Fix

**Fix common permission problems**:
```bash
# Fix project directory permissions
chmod -R u+rw .

# Fix .orch-state directory (critical)
mkdir -p .orch-state
chmod 700 .orch-state

# Fix Python script permissions
find . -name "*.py" -exec chmod 644 {} \;
find . -name "*.sh" -exec chmod 755 {} \;
```

### Permission Diagnostics

**Check current permissions**:
```bash
# Check project directory
ls -la . | head -10

# Check .orch-state specifically
ls -la .orch-state/ 2>/dev/null || echo ".orch-state not found"

# Current user and groups
whoami && groups
```

**Test write permissions**:
```bash
# Test if you can write to project directory
touch test_write.tmp && rm test_write.tmp && echo "Write OK" || echo "Write FAILED"

# Test .orch-state write
touch .orch-state/test.tmp && rm .orch-state/test.tmp && echo ".orch-state OK" || echo ".orch-state FAILED"
```

## System Diagnostics

### Health Check

**Quick system validation**:
```bash
# One-line health check
python --version && echo $DISCORD_BOT_TOKEN | cut -c1-10 && pip show discord.py pytest PyYAML PyGithub | grep Version
```

**Comprehensive health check**:
```bash
#!/bin/bash
echo "=== System Health Check ==="

# Python version
echo "Python: $(python --version)"

# Environment variables
echo "Discord token: $(echo $DISCORD_BOT_TOKEN | cut -c1-10)..."

# Dependencies
echo -e "\nCore dependencies:"
pip show discord.py PyYAML PyGithub pytest | grep "Name\|Version"

# File system
echo -e "\nFile system:"
echo "Project dir writable: $(touch test.tmp && rm test.tmp && echo YES || echo NO)"
echo ".orch-state exists: $([ -d .orch-state ] && echo YES || echo NO)"

# Process check
echo -e "\nProcesses:"
echo "Discord bot running: $(pgrep -f discord_bot.py >/dev/null && echo YES || echo NO)"
```

### Environment Validation

**Check required environment**:
```bash
# Required environment variables
env | grep -E "(DISCORD_BOT_TOKEN|CLAUDE_API_KEY)" || echo "Missing environment variables"

# Python dependencies
python -c "
try:
    import discord, yaml, github, pytest
    print('✓ All core dependencies available')
except ImportError as e:
    print(f'✗ Missing dependency: {e}')
"
```

**Validate configuration**:
```bash
# Check YAML configuration
python -c "
import yaml
try:
    with open('orch-config.yaml', 'r') as f:
        config = yaml.safe_load(f)
    print('✓ Configuration file valid')
except Exception as e:
    print(f'✗ Configuration error: {e}')
"
```

## Process Management

### Orchestrator Operations

**Start orchestrator**:
```bash
# Single project mode
python scripts/orchestrator.py

# Multi-project mode  
python scripts/multi_project_orchestrator.py --interactive
```

**Stop orchestrator gracefully**:
```bash
# Send interrupt signal
pkill -INT -f orchestrator.py

# Force kill if needed
pkill -9 -f orchestrator.py
```

**Check orchestrator status**:
```bash
# Check if running
pgrep -f orchestrator.py && echo "Running" || echo "Stopped"

# View recent logs
tail -20 logs/orchestrator.log 2>/dev/null || echo "No logs found"
```

### Agent Process Management

**Check agent processes**:
```bash
# List all agent-related processes
ps aux | grep -E "(discord_bot|orchestrator|agent)" | grep -v grep
```

**Kill all agent processes**:
```bash
# Emergency stop all
pkill -f "discord_bot.py"
pkill -f "orchestrator.py"
pkill -f "multi_project"
```

## Common Issues

### "Permission Denied" Errors

```bash
# Fix immediately
chmod 700 .orch-state
chmod u+rw .
```

### Discord Bot Not Responding

```bash
# Quick restart sequence
pkill -f discord_bot.py
sleep 2
python lib/discord_bot.py &
```

### Environment Setup Issues

```bash
# Reset environment
export DISCORD_BOT_TOKEN="your_token_here"
pip install -r requirements.txt
```

### File System Issues

```bash
# Check disk space
df -h .

# Check for .orch-state issues
rm -rf .orch-state && mkdir .orch-state && chmod 700 .orch-state
```

## Emergency Procedures

### Complete System Reset

```bash
#!/bin/bash
echo "Emergency system reset..."

# Stop all processes
pkill -f discord_bot.py
pkill -f orchestrator.py

# Reset file permissions
chmod -R u+rw .
chmod 700 .orch-state

# Reinstall dependencies
pip install -r requirements.txt

# Restart core services
python lib/discord_bot.py &
echo "System reset complete"
```

### Backup Current State

```bash
# Backup .orch-state
cp -r .orch-state .orch-state.backup.$(date +%Y%m%d_%H%M%S)

# Backup logs
mkdir -p backups
cp -r logs backups/logs.$(date +%Y%m%d_%H%M%S) 2>/dev/null || echo "No logs to backup"
```

## CLI Operations

### Modern CLI Commands

**Using agent-orch or aw command**:
```bash
# System health check
agent-orch health

# Check orchestrator status
agent-orch status

# Start orchestration engine
agent-orch start

# Stop orchestrator gracefully
agent-orch stop

# List registered projects
agent-orch projects
```

### Utility Tools

**System monitoring and compliance**:
```bash
# Real-time compliance monitoring
python tools/compliance/monitor_compliance.py

# Performance monitoring
python tools/monitoring/performance_monitor.py

# System visualization dashboard
cd tools/visualizer && python app.py
```

**Coverage and testing validation**:
```bash
# Test runner without external dependencies
python tools/coverage/test_runner.py

# Coverage analysis
python tools/coverage/analyze_coverage.py

# TDD workflow validation
python tools/coverage/validate_tdd.py
```

## Monitoring

### Log Monitoring

```bash
# Watch Discord bot logs
tail -f logs/discord_bot.log

# Watch orchestrator logs  
tail -f logs/orchestrator.log

# Watch all logs
tail -f logs/*.log
```

### Resource Monitoring

```bash
# Check memory usage
ps aux | grep -E "(discord_bot|orchestrator)" | awk '{print $4, $11}'

# Check CPU usage
top -p $(pgrep -f "discord_bot\|orchestrator" | tr '\n' ',' | sed 's/,$//')
```

---

**For detailed troubleshooting, see the [Troubleshooting Guide](../user-guide/troubleshooting.md)**