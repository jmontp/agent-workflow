# 🤖 Agent Interface Management

> **Switch seamlessly between different AI agent backends through an intuitive web interface**

The Agent Interface Management system allows you to switch between different AI agent backends depending on your needs - from local Claude Code CLI to direct Anthropic API integration to mock interfaces for testing.

## 🎯 Quick Start

Launch the web interface to access the agent interface manager:

```bash
# Start the web visualizer with interface management
cd tools/visualizer
python app.py

# Or use the CLI shortcut
agent-orch web --interface-manager
```

Navigate to the **Interface Management** panel in the web tool to begin switching between interfaces.

## 🔧 Interface Types

### Claude Code Interface (Default)
**Best for**: Production workflows with tool restrictions and security controls

```yaml
Type: claude_code
Features:
  - Local Claude Code CLI integration
  - Agent-specific tool restrictions
  - Built-in security boundaries
  - No API key required
Requirements:
  - Claude Code CLI installed and available
  - Working directory access
```

**When to use**:
- ✅ Production development workflows
- ✅ When you need agent security restrictions
- ✅ Local development without external API dependencies
- ✅ Tool access control and audit trails

### Anthropic API Interface
**Best for**: Direct API access with latest models and high performance

```yaml
Type: anthropic_api
Features:
  - Direct Anthropic API integration
  - Latest Claude model access
  - High-performance API calls
  - Full model feature support
Requirements:
  - Anthropic API key
  - Internet connectivity
  - anthropic Python package
```

**When to use**:
- ✅ Need latest Claude model features
- ✅ High-volume API usage
- ✅ Custom model parameters
- ✅ Enterprise API access

### Mock Interface
**Best for**: Testing, demonstrations, and development without AI dependencies

```yaml
Type: mock
Features:
  - Simulated AI responses
  - No external dependencies
  - Configurable response patterns
  - Demo-friendly output
Requirements:
  - None (fully self-contained)
```

**When to use**:
- ✅ Testing and development
- ✅ Demonstrations and presentations
- ✅ CI/CD environments
- ✅ Offline development

## 🎮 Web Interface Guide

### Interface Status Panel

The interface status panel shows real-time information about all available interfaces:

```
┌─ Agent Interfaces ─────────────────────────────────────┐
│                                                        │
│ 🟢 Claude Code        [ACTIVE]    ⚡ Ready            │
│    Local CLI • Tool restrictions enabled               │
│    [Test] [Configure] [Logs]                          │
│                                                        │
│ 🟡 Anthropic API      [AVAILABLE] 🔑 API Key Required │
│    Direct API • Latest models                         │
│    [Test] [Configure] [Switch To]                     │
│                                                        │
│ 🟢 Mock Interface     [AVAILABLE] 🎭 Demo Mode        │
│    Simulated • No dependencies                        │
│    [Test] [Configure] [Switch To]                     │
│                                                        │
└────────────────────────────────────────────────────────┘
```

### Status Indicators

| Indicator | Meaning | Actions Available |
|-----------|---------|-------------------|
| 🟢 **Active** | Currently selected interface | Test, Configure, View Logs |
| 🟡 **Available** | Ready to switch | Test, Configure, Switch To |
| 🔴 **Error** | Configuration or connection issue | Configure, Troubleshoot |
| ⚙️ **Configuring** | Being set up | Wait for completion |
| 🧪 **Testing** | Connection test in progress | Wait for results |

### Quick Actions

**Test Interface**: Verify connection and basic functionality
```javascript
// Sends a simple test prompt to validate the interface
Test Prompt: "Respond with 'Interface test successful'"
Expected Response: Confirmation message
```

**Configure Interface**: Modify settings and credentials
- API key management (Anthropic API)
- Timeout and performance settings
- Custom model parameters
- Security and validation options

**Switch Interface**: Change active interface
- Validates new interface before switching
- Maintains session state during transition
- Provides rollback if switch fails

## ⚙️ Configuration Management

### Anthropic API Configuration

```yaml
# Interface configuration
interface_type: anthropic_api
enabled: true
api_key: "sk-ant-..."  # Your Anthropic API key
model: "claude-3-sonnet-20240229"
max_tokens: 4000
temperature: 0.7
timeout: 300

# Advanced settings
custom_settings:
  retry_attempts: 3
  rate_limit: 100
  enable_streaming: true
```

**Security Note**: API keys are encrypted at rest and masked in logs.

### Claude Code Configuration

```yaml
# Interface configuration  
interface_type: claude_code
enabled: true
timeout: 300
max_tokens: 4000

# Agent-specific restrictions
agent_restrictions:
  design_agent:
    allowed_tools: ["read", "grep", "git_status"]
    disallowed_tools: ["edit", "write", "rm"]
  code_agent:
    allowed_tools: ["read", "edit", "write", "git_add", "git_commit"]
    disallowed_tools: ["git_push", "rm"]
```

### Mock Interface Configuration

```yaml
# Interface configuration
interface_type: mock
enabled: true
response_delay: 1.0  # Simulate processing time
failure_rate: 0.05   # 5% simulated failures

# Response customization
custom_settings:
  agent_personas: true
  code_generation: true
  error_simulation: true
```

## 🔄 Switching Interfaces

### Automatic Switching
The system can automatically switch interfaces based on conditions:

```python
# Auto-switch rules (configured via web interface)
auto_switch_rules:
  - condition: "api_rate_limit_exceeded"
    action: "switch_to_claude_code"
    
  - condition: "claude_code_unavailable"  
    action: "switch_to_mock"
    
  - condition: "demo_mode_enabled"
    action: "switch_to_mock"
```

### Manual Switching
Switch interfaces through the web interface:

1. **Validate Target Interface**: System tests connection before switching
2. **Graceful Transition**: Current operations complete before switch
3. **State Preservation**: Active sessions and context maintained
4. **Rollback Available**: Automatic rollback if switch fails

### Command Line Switching

```bash
# Check current interface status
curl http://localhost:5000/api/interfaces

# Switch to Anthropic API
curl -X POST http://localhost:5000/api/interfaces/anthropic_api/switch

# Test interface connection
curl -X POST http://localhost:5000/api/interfaces/claude_code/test
```

## 🧪 Testing and Validation

### Interface Testing Panel

The web interface provides comprehensive testing tools:

**Connection Test**:
- Validates API keys and authentication
- Tests basic request/response functionality
- Measures response time and reliability

**Agent Test**:
- Tests each agent type with the interface
- Validates tool restrictions and security
- Measures agent-specific performance

**Load Test**:
- Simulates concurrent requests
- Measures performance under load
- Identifies rate limiting and timeouts

### Test Results Interpretation

```json
{
  "interface": "anthropic_api",
  "test_results": {
    "connection": {
      "status": "success",
      "response_time": 234,
      "authentication": "valid"
    },
    "agent_compatibility": {
      "design_agent": "✅ Compatible",
      "code_agent": "✅ Compatible", 
      "qa_agent": "✅ Compatible",
      "data_agent": "✅ Compatible"
    },
    "performance": {
      "avg_response_time": 1.2,
      "success_rate": 99.8,
      "rate_limit": "100/minute"
    }
  }
}
```

## 🔐 Security and Best Practices

### API Key Management

**Secure Storage**:
- API keys encrypted at rest using system keyring
- Keys never logged or displayed in full
- Automatic key rotation support

**Access Control**:
- Interface switching requires authentication
- Audit logging for all interface changes
- Role-based access to interface management

**Key Security Best Practices**:
```bash
# Use environment variables for API keys
export ANTHROPIC_API_KEY="sk-ant-..."

# Or secure configuration files with restricted permissions
chmod 600 ~/.agent-workflow/api-keys.yml

# Enable audit logging
export AGENT_INTERFACE_AUDIT=true
```

### Security Validation

Each interface includes security validation:

```python
# Input sanitization
def sanitize_prompt(prompt: str) -> ValidationResult:
    """Validate and sanitize user prompts"""
    # Remove potentially harmful content
    # Validate length and format
    # Apply content filtering
    
# API key validation  
def validate_api_key(key: str) -> bool:
    """Validate API key format and permissions"""
    # Check key format
    # Verify permissions
    # Test authentication
```

## 📊 Monitoring and Analytics

### Interface Performance Metrics

The system tracks detailed performance metrics:

```yaml
Metrics Tracked:
  - Response times (avg, p95, p99)
  - Success/failure rates
  - Token usage and costs
  - API rate limiting
  - Error types and frequencies
  - Agent compatibility scores
```

### Real-Time Dashboard

Access performance data through the web interface:
- Live performance charts
- Interface comparison graphs  
- Cost analysis and optimization
- Error rate monitoring
- Usage pattern analysis

### Performance Optimization

**Automatic Optimization**:
- Interface selection based on performance
- Load balancing across available interfaces
- Fallback chains for reliability
- Performance threshold alerting

## 🔧 Troubleshooting

### Common Issues

**Interface Connection Failed**:
```bash
# Check interface status
curl http://localhost:5000/api/interfaces/status

# Validate configuration
curl http://localhost:5000/api/interfaces/anthropic_api/config

# Test connection manually
curl -X POST http://localhost:5000/api/interfaces/anthropic_api/test
```

**API Key Issues**:
- Verify key format: `sk-ant-...` for Anthropic
- Check key permissions and rate limits
- Validate key expiration date
- Test key with direct API call

**Claude Code Interface Issues**:
```bash
# Verify Claude Code installation
claude-code --version

# Check PATH and permissions
which claude-code

# Test basic functionality
claude-code --help
```

**Performance Issues**:
- Monitor response times in dashboard
- Check rate limiting and quotas
- Validate network connectivity
- Review error logs for patterns

### Error Codes Reference

| Error Code | Description | Solution |
|------------|-------------|----------|
| `INTERFACE_UNAVAILABLE` | Interface not responding | Check configuration and restart |
| `AUTHENTICATION_FAILED` | Invalid API credentials | Verify API key and permissions |
| `RATE_LIMIT_EXCEEDED` | API quota exceeded | Wait or switch interface |
| `TIMEOUT_ERROR` | Request timeout | Increase timeout or check network |
| `VALIDATION_FAILED` | Input validation error | Check prompt format and content |

### Debug Mode

Enable debug logging for detailed troubleshooting:

```bash
# Enable debug mode
export AGENT_INTERFACE_DEBUG=true

# View debug logs
tail -f logs/interface-manager.log

# Component-specific debugging
export CLAUDE_CODE_DEBUG=true
export ANTHROPIC_API_DEBUG=true
```

## 🚀 Advanced Usage

### Custom Interface Development

Extend the system with custom interfaces:

```python
class CustomAgentInterface(BaseAgentInterface):
    """Custom interface implementation"""
    
    async def initialize(self) -> bool:
        """Initialize custom interface"""
        pass
        
    async def generate_response(self, prompt: str, agent_type: AgentType, context: Dict) -> str:
        """Generate response using custom backend"""
        pass
        
    async def test_connection(self) -> Dict[str, Any]:
        """Test custom interface connection"""
        pass
```

### Batch Operations

Perform bulk operations across interfaces:

```python
# Test all interfaces
POST /api/interfaces/test-all

# Switch interface for specific agents
POST /api/interfaces/batch-switch
{
  "rules": [
    {"agent_type": "design", "interface": "claude_code"},
    {"agent_type": "code", "interface": "anthropic_api"}
  ]
}
```

### Integration with CI/CD

Automate interface management in CI/CD pipelines:

```yaml
# GitHub Actions example
- name: Configure Mock Interface for Tests
  run: |
    curl -X POST http://localhost:5000/api/interfaces/mock/switch
    curl -X POST http://localhost:5000/api/interfaces/mock/test
```

---

## 📚 Next Steps

- **[Context Management Guide](context-management.md)**: Optimize context processing modes
- **[Web Tool Guide](ui-portal-guide.md)**: Comprehensive web interface documentation  
- **[Performance Monitoring](performance-monitoring.md)**: Monitor and optimize system performance
- **[API Reference](../development/api-reference.md)**: Complete API documentation

The agent interface management system provides flexible, secure, and high-performance backend switching for your AI agent workflows. Choose the right interface for each situation and seamlessly switch as your needs evolve.