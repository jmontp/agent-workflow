# 📊 Performance Monitoring & Optimization

> **Monitor, analyze, and optimize your AI agent workflow for peak performance**

The Performance Monitoring system provides comprehensive insights into system performance, helping you optimize response times, resource usage, and overall efficiency across different scenarios and configurations.

## 🚀 Quick Start

Access performance monitoring through multiple interfaces:

```bash
# Direct performance monitoring tool
python tools/monitoring/performance_monitor.py

# Generate performance report
python tools/monitoring/performance_monitor.py --report-only

# Custom monitoring configuration
python tools/monitoring/performance_monitor.py --interval 60 --storage-path ./monitoring
```

## 📈 Performance Dashboard

### Real-Time Metrics Overview

The performance dashboard provides a comprehensive view of system health:

```
┌─ Performance Dashboard ────────────────────────────────────────┐
│                                                                │
│ 🎯 System Overview                              Last 24h      │
│ ├─ Interface: Claude Code                       🟢 Healthy    │
│ ├─ Context Mode: FANCY                          ⚡ 2.3s avg   │
│ └─ Active Projects: 3                           📊 99.1% up   │
│                                                                │
│ ┌─ Key Performance Indicators ─────────────────────────────┐  │
│ │ Response Time:    [████████░░] 2.3s  (Target: <3s)      │  │
│ │ Memory Usage:     [██████░░░░] 245MB (Limit: 1GB)       │  │
│ │ Success Rate:     [██████████] 99.1% (Target: >95%)     │  │
│ │ Cache Hit Rate:   [████████░░] 78%   (Target: >70%)     │  │
│ │ Token Efficiency: [█████████░] 88%   (Target: >80%)     │  │
│ └───────────────────────────────────────────────────────────┘  │
│                                                                │
│ ┌─ Performance Trends ──────────────────────────────────────┐  │
│ │     Response Time (last 6h)                              │  │
│ │ 4s │                                                     │  │
│ │ 3s │     ██                                              │  │
│ │ 2s │ ██  ██  ██     ██  ██                               │  │
│ │ 1s │ ██  ██  ██  ██ ██  ██  ██                           │  │
│ │ 0s └────────────────────────────────────────────────────┘  │
│ │     12   2    4    6    8   10   12   2    4    6pm     │  │
│ └───────────────────────────────────────────────────────────┘  │
│                                                                │
│ [Detailed Metrics] [Export Report] [Configure Alerts]         │
└────────────────────────────────────────────────────────────────┘
```

### Performance Categories

**System Performance**:
- CPU usage and load averages
- Memory consumption and allocation
- Disk I/O and network activity
- Process count and resource limits

**Application Performance**:
- Context preparation times
- Agent response latencies
- Interface switching overhead
- State machine transition speed

**AI Performance**:
- Token usage and efficiency
- Model response quality
- Context accuracy metrics
- Cache performance statistics

## 🔍 Detailed Metrics Analysis

### Context Management Performance

Monitor context processing across different modes:

```yaml
Context Performance Metrics:
  FANCY Mode:
    avg_preparation_time: 2.3s
    memory_usage: 245MB
    accuracy_score: 0.95
    cache_hit_rate: 0.78
    file_processing_rate: 23/150
    
  SIMPLE Mode:
    avg_preparation_time: 0.2s
    memory_usage: 35MB
    accuracy_score: 0.82
    cache_hit_rate: 0.65
    file_processing_rate: 10/150
    
  Performance Comparison:
    speed_improvement: 11.5x faster
    memory_savings: 6x less
    accuracy_tradeoff: 13% reduction
```

### Interface Performance Comparison

Track performance across different agent interfaces:

```json
{
  "interface_performance": {
    "claude_code": {
      "avg_response_time": 1.2,
      "success_rate": 0.991,
      "error_rate": 0.009,
      "timeout_rate": 0.001,
      "features": ["tool_restrictions", "local_execution"]
    },
    "anthropic_api": {
      "avg_response_time": 0.8,
      "success_rate": 0.996,
      "error_rate": 0.003,
      "timeout_rate": 0.001,
      "rate_limit_hits": 5,
      "cost_per_1k_tokens": 0.015
    },
    "mock": {
      "avg_response_time": 0.1,
      "success_rate": 0.999,
      "error_rate": 0.001,
      "timeout_rate": 0.000,
      "features": ["demo_mode", "ci_compatible"]
    }
  }
}
```

### Resource Utilization Tracking

Monitor system resource consumption:

```
┌─ Resource Utilization (Real-Time) ────────────────────────────┐
│                                                               │
│ CPU Usage:        [████████░░] 78%  (8 cores, 3.2GHz avg)   │
│ Memory:           [██████░░░░] 6.2GB / 16GB (38%)            │
│ Disk I/O:         [███░░░░░░░] Read: 45MB/s Write: 12MB/s    │
│ Network:          [██░░░░░░░░] Up: 2MB/s Down: 1.5MB/s       │
│                                                               │
│ ┌─ Top Processes ──────────────────────────────────────────┐ │
│ │ agent-workflow   CPU: 45%  MEM: 2.1GB  PID: 1234        │ │
│ │ claude-code      CPU: 23%  MEM: 512MB  PID: 5678        │ │
│ │ web-visualizer   CPU: 8%   MEM: 256MB  PID: 9012        │ │
│ │ state-monitor    CPU: 2%   MEM: 64MB   PID: 3456        │ │
│ └──────────────────────────────────────────────────────────┘ │
│                                                               │
│ [Process Details] [Resource Alerts] [Optimization Tips]      │
└───────────────────────────────────────────────────────────────┘
```

## ⚡ Performance Optimization

### Automatic Optimization Recommendations

The system provides intelligent optimization suggestions:

```yaml
Optimization Analysis:
  current_performance_score: 78/100
  
  recommendations:
    high_priority:
      - "Switch to SIMPLE context mode for testing (40% faster)"
      - "Enable context pre-warming (15% improvement)"
      - "Increase cache size to 100 contexts (12% better hit rate)"
      
    medium_priority:
      - "Consider Anthropic API for latency-critical operations"
      - "Optimize file filtering patterns for better accuracy"
      - "Enable background processing for large projects"
      
    low_priority:
      - "Update to latest Claude model for better performance"
      - "Configure agent pool sizing based on CPU cores"
      - "Set up performance monitoring alerts"

  potential_improvements:
    response_time: "-35% (2.3s → 1.5s)"
    memory_usage: "-25% (245MB → 184MB)"
    accuracy: "+8% (95% → 97%)"
```

### Performance Tuning Configuration

Optimize system performance through configuration:

```yaml
# performance_config.yaml
performance_optimization:
  # Context Management Tuning
  context:
    mode_selection_strategy: "performance_first"  # accuracy_first, balanced, performance_first
    cache_size: 100
    preload_common_contexts: true
    background_optimization: true
    
  # Interface Optimization
  interfaces:
    primary: "anthropic_api"      # For latency-critical operations
    fallback: "claude_code"       # For tool-restricted operations
    testing: "mock"               # For CI/CD pipelines
    
  # Resource Management
  resources:
    max_memory_usage: "1GB"
    cpu_limit: "80%"
    concurrent_operations: 4
    
  # Performance Thresholds
  thresholds:
    max_response_time: 3.0
    min_success_rate: 0.95
    max_memory_usage: 0.8
    min_cache_hit_rate: 0.7
```

### Performance Testing Framework

**Current Implementation**: Basic performance monitoring and validation:

```bash
# Run performance monitoring with custom intervals
python tools/monitoring/performance_monitor.py --interval 10

# Generate performance summary report
python tools/monitoring/performance_monitor.py --report-only

# Test monitoring functionality (if tests exist)
python -m pytest tests/unit/test_performance_monitor.py -v

# Test visualizer endpoints
curl http://localhost:5000/health
curl http://localhost:5000/metrics
curl http://localhost:5000/debug
```

**Note**: Comprehensive load testing and performance benchmarking frameworks are not currently implemented. The system provides basic monitoring suitable for development and operational visibility.

Sample performance report output:

```json
{
  "status": "monitoring",
  "latest_snapshot": {
    "timestamp": "2024-01-01T12:00:00Z",
    "cpu_usage": 25.5,
    "memory_usage": 45.2,
    "disk_usage": 60.0,
    "active_processes": 150
  },
  "snapshots_collected": 120,
  "monitoring_duration_minutes": 60.0,
  "summary": {
    "cpu_usage": {
      "avg": 30.0,
      "max": 50.0,
      "min": 10.0
    },
    "memory_usage": {
      "avg": 40.0,
      "max": 70.0,
      "min": 20.0
    }
  }
}
```

## 📊 Monitoring Tools & Endpoints

### Metrics Export

**Current Implementation**: The system provides basic metrics collection and export through:

1. **JSON Reports**: Performance data stored as structured JSON files
2. **Prometheus-compatible endpoint**: Basic metrics in Prometheus format (via visualizer)
3. **File-based logging**: System performance logged to `.orch-monitoring/` directory

```bash
# View stored performance reports
ls -la .orch-monitoring/performance_report_*.json

# View latest performance data
python tools/monitoring/performance_monitor.py --report-only | jq .

# Get Prometheus-compatible metrics (if visualizer is running)
curl http://localhost:5000/metrics

# Monitor in real-time (basic console output)
watch -n 30 'python tools/monitoring/performance_monitor.py --report-only'
```

**Note**: Full Prometheus/Grafana integration is not currently implemented. The system provides basic metrics collection suitable for development and basic production monitoring.

### System Health Monitoring

**Current Implementation**: The system provides health monitoring through:

1. **Visualizer Health Endpoint**: Basic health check via web interface
2. **Discord Bot Status**: Monitor bot connectivity and responsiveness
3. **File-based Performance Reports**: System resource monitoring via performance monitor

```bash
# Check system health via visualizer (if running)
curl http://localhost:5000/health

# Check system health using performance monitor
python tools/monitoring/performance_monitor.py --report-only

# Basic system resource check
python -c "import psutil; print(f'CPU: {psutil.cpu_percent()}%, Memory: {psutil.virtual_memory().percent}%')"

# Check for running processes
ps aux | grep -E "(orchestrator|discord|agent)" | grep -v grep

# Discord bot status (if configured)
# Bot reports connectivity status in Discord channels
```

**Note**: Dedicated health check REST API endpoints beyond the visualizer are not currently implemented.

### Real-Time Monitoring

**Current Implementation**: The system provides real-time monitoring through:

1. **Web Visualizer**: Real-time state visualization via WebSocket
2. **Performance Monitor**: Continuous system resource monitoring
3. **Discord Integration**: Real-time status updates via Discord bot

```bash
# Start web-based real-time visualizer
cd tools/visualizer && python app.py
# Then visit http://localhost:5000 for real-time state monitoring

# Start continuous performance monitoring (console output)
python tools/monitoring/performance_monitor.py --interval 10

# Watch performance reports update
watch -n 30 'ls -la .orch-monitoring/ | tail -5'

# Simple real-time system monitoring
watch -n 5 'python -c "import psutil; print(f\"CPU: {psutil.cpu_percent()}%, Memory: {psutil.virtual_memory().percent}%\")"'

# Real-time state via API (if visualizer running)
watch -n 5 'curl -s http://localhost:5000/api/state | jq .'
```

**Available Real-time Data**:
- Workflow state transitions
- TDD cycle progress
- System resource usage
- Connected client count
- Discord bot status

## 🚨 Alerting & Notifications

### Alert Configuration

Set up intelligent performance alerts:

```yaml
# alerts_config.yaml
alerts:
  response_time:
    threshold: 5.0  # seconds
    severity: "warning"
    cooldown: 300   # 5 minutes
    action: "suggest_simple_mode"
    
  memory_usage:
    threshold: 0.9  # 90% of available memory
    severity: "critical"
    cooldown: 60
    action: "force_simple_mode"
    
  success_rate:
    threshold: 0.95  # Below 95% success rate
    severity: "warning"
    cooldown: 600   # 10 minutes
    action: "interface_health_check"
    
  interface_failure:
    consecutive_failures: 3
    severity: "critical"
    cooldown: 0
    action: "automatic_fallback"

notification_channels:
  - type: "webhook"
    url: "https://hooks.slack.com/your-webhook"
  - type: "email"
    recipients: ["admin@yourcompany.com"]
  - type: "desktop"
    enabled: true
```

### Alert Actions

Automatic responses to performance issues:

```python
# Automatic performance responses
{
  "suggest_simple_mode": {
    "description": "Suggest switching to SIMPLE context mode",
    "automated": False,
    "user_confirmation": True
  },
  "force_simple_mode": {
    "description": "Automatically switch to SIMPLE mode",
    "automated": True,
    "rollback_after": "1 hour"
  },
  "interface_health_check": {
    "description": "Run interface diagnostics",
    "automated": True,
    "report_results": True
  },
  "automatic_fallback": {
    "description": "Switch to backup interface",
    "automated": True,
    "notify_admin": True
  }
}
```

## 📋 Performance Reports

### Automated Reporting

Generate comprehensive performance reports:

```bash
# Generate daily performance report
python tools/monitoring/performance_monitor.py --report daily

# Generate custom report for date range
python tools/monitoring/performance_monitor.py --report \
  --start "2024-01-01" --end "2024-01-07" \
  --format json --output performance_report.json
```

Sample performance report:

```yaml
Performance Report: 2024-01-01 to 2024-01-07
=====================================

Executive Summary:
  - Overall Performance Score: 85/100 (Good)
  - Average Response Time: 1.8s (Target: <3s) ✅
  - System Uptime: 99.7% (Target: >99%) ✅
  - Success Rate: 97.3% (Target: >95%) ✅

Key Metrics:
  Context Management:
    - FANCY mode usage: 78% of operations
    - SIMPLE mode usage: 22% of operations
    - Average preparation time: 1.8s (FANCY), 0.3s (SIMPLE)
    - Context accuracy: 94% (FANCY), 81% (SIMPLE)
    
  Interface Performance:
    - Claude Code: 65% usage, 1.2s avg response
    - Anthropic API: 30% usage, 0.9s avg response
    - Mock: 5% usage, 0.1s avg response
    
  Resource Utilization:
    - Peak memory usage: 450MB
    - Average CPU usage: 34%
    - Disk I/O: Normal levels
    - Network: Minimal usage

Recommendations:
  1. Consider enabling context pre-warming for 15% improvement
  2. Increase cache size from 50 to 100 contexts
  3. Set up automatic switching to SIMPLE mode under load
  4. Configure alerting for memory usage above 80%

Performance Trends:
  - Response times improving: -12% vs previous week
  - Memory usage stable: +2% vs previous week
  - Success rate improving: +1.3% vs previous week
```

## 🔧 Troubleshooting Performance Issues

### Common Performance Problems

**Slow Operation Response**:
```bash
# Check system performance during operations
python tools/monitoring/performance_monitor.py --report-only

# Monitor resource usage during operations
watch -n 5 'python -c "import psutil; print(f\"CPU: {psutil.cpu_percent()}%, Memory: {psutil.virtual_memory().percent}%\")"'

# Solutions:
# 1. Monitor system resources for bottlenecks
# 2. Check for high memory or CPU usage
# 3. Review application logs for errors
# 4. Consider system resource limits
```

**High Memory Usage**:
```bash
# Monitor memory usage patterns
python tools/monitoring/performance_monitor.py --report-only

# Check current memory usage
python -c "import psutil; mem=psutil.virtual_memory(); print(f'Memory: {mem.percent}% ({mem.used//1024//1024}MB used)')"

# Solutions:
# 1. Monitor memory usage with performance monitor
# 2. Restart services if memory usage is consistently high
# 3. Check for memory leaks in application logs
# 4. Consider increasing system memory
```

**System Performance Issues**:
```bash
# Check overall system performance
python tools/monitoring/performance_monitor.py --report-only

# Check for running processes
ps aux | grep -E "(python|orchestrator)" | grep -v grep

# Solutions:
# 1. Monitor system resources regularly
# 2. Check application logs for errors
# 3. Restart services if needed
# 4. Review system configuration
```

### Debug Mode

Enable comprehensive performance debugging:

```bash
# Enable performance debugging
export PERFORMANCE_DEBUG=true
export CONTEXT_TIMING_DEBUG=true
export INTERFACE_TIMING_DEBUG=true

# View detailed performance logs
tail -f logs/performance.log

# Component-specific debugging
export CONTEXT_MANAGER_PROFILE=true
export INTERFACE_MANAGER_PROFILE=true
```

## 🚀 Advanced Performance Features

### Performance Profiling

**Current Implementation**: Basic performance monitoring and Python profiling:

```python
# Performance monitoring via our tool
import sys
sys.path.append('tools/monitoring')
from performance_monitor import PerformanceMonitor

monitor = PerformanceMonitor()
status = monitor.get_current_status()
print(f"Performance status: {status}")

# Python's built-in profiling for detailed analysis
import cProfile
import pstats

# Profile a function
cProfile.run('your_function_here()', 'profile_output.prof')
stats = pstats.Stats('profile_output.prof')
stats.sort_stats('cumulative').print_stats(10)
```

**Available Profiling Data**:
- CPU and memory usage over time
- System resource consumption
- Application response times (via visualizer)
- State transition performance

**Note**: Advanced profiling tools and performance analysis frameworks are not currently integrated.

### Load Testing

**Current Implementation**: Basic system monitoring under load:

```bash
# Monitor system performance during operations
python tools/monitoring/performance_monitor.py --interval 5 &

# Run normal workflow operations while monitoring
# (Start orchestrator, Discord bot, visualizer simultaneously)

# Monitor resource usage during operations
watch -n 5 'ps aux | grep -E "(python|orchestrator|discord)" | grep -v grep'

# Test visualizer under load (basic)
for i in {1..10}; do
  curl -s http://localhost:5000/api/state > /dev/null &
done
wait
```

**Manual Load Testing Steps**:
1. Start performance monitor with short interval
2. Launch multiple system components (orchestrator, bot, visualizer)
3. Generate typical workflow activity via Discord commands
4. Monitor resource usage and response times
5. Review performance reports in `.orch-monitoring/`

**Note**: Automated load testing tools and stress testing frameworks are not currently implemented.

### Custom Metrics

**Current Implementation**: Extensible monitoring via class inheritance and custom endpoints:

```python
# Extend the existing PerformanceMonitor class
import sys
sys.path.append('tools/monitoring')
from performance_monitor import PerformanceMonitor
from datetime import datetime

class CustomPerformanceMonitor(PerformanceMonitor):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.custom_metrics = {}
    
    def record_custom_metric(self, name, value, tags=None):
        """Record a custom metric"""
        self.custom_metrics[name] = {
            "value": value,
            "tags": tags or {},
            "timestamp": datetime.utcnow().isoformat()
        }
    
    def get_custom_metrics(self):
        """Get all custom metrics"""
        return self.custom_metrics

# Usage example
custom_monitor = CustomPerformanceMonitor()
custom_monitor.record_custom_metric("workflow_completion_time", 45.2, {"project": "myapp"})
custom_monitor.record_custom_metric("discord_command_count", 23)
```

**Custom Metric Storage Options**:
- Extend PerformanceMonitor class for application-specific metrics
- Add custom endpoints to visualizer app.py
- Store metrics in JSON reports alongside system metrics
- Log custom metrics via Python logging

**Note**: A dedicated custom metrics framework with time-series storage is not currently implemented.

---

## 📚 Next Steps

- **[Agent Interface Management](agent-interface-management.md)**: Optimize backend selection for performance
- **[Context Management](context-management.md)**: Choose the right context mode for your workload
- **[Web Portal Guide](ui-portal-guide.md)**: Access performance monitoring through web interface
- **[API Reference](../development/api-reference.md)**: Complete API documentation for monitoring endpoints

The performance monitoring system provides comprehensive insights to help you optimize your AI agent workflow for maximum efficiency and reliability. Use the tools and metrics to identify bottlenecks, optimize resource usage, and ensure consistent high-performance operation.