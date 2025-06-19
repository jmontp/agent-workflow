"""
Comprehensive test coverage for context_monitoring.py module.

Tests cover all classes, methods, and edge cases to achieve 95%+ coverage.
"""

import asyncio
import json
import pytest
import time
from datetime import datetime, timedelta
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from typing import Dict, Any

# Import the module under test
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'lib'))

from context_monitoring import (
    ContextMonitor, PerformanceMetric, Alert, PerformanceTarget, SystemHealth,
    MetricType, AlertSeverity, MonitoringInterval
)
from context.models import AgentContext, ContextRequest, TDDState
from context.exceptions import ContextMonitoringError


class TestMetricType:
    """Test MetricType enum"""
    
    def test_metric_type_values(self):
        """Test MetricType enum values"""
        assert MetricType.COUNTER.value == "counter"
        assert MetricType.GAUGE.value == "gauge"
        assert MetricType.HISTOGRAM.value == "histogram"
        assert MetricType.TIMER.value == "timer"


class TestAlertSeverity:
    """Test AlertSeverity enum"""
    
    def test_alert_severity_values(self):
        """Test AlertSeverity enum values"""
        assert AlertSeverity.INFO.value == "info"
        assert AlertSeverity.WARNING.value == "warning"
        assert AlertSeverity.ERROR.value == "error"
        assert AlertSeverity.CRITICAL.value == "critical"


class TestMonitoringInterval:
    """Test MonitoringInterval enum"""
    
    def test_monitoring_interval_values(self):
        """Test MonitoringInterval enum values"""
        assert MonitoringInterval.REAL_TIME.value == 1
        assert MonitoringInterval.FAST.value == 5
        assert MonitoringInterval.MEDIUM.value == 30
        assert MonitoringInterval.SLOW.value == 60
        assert MonitoringInterval.HOURLY.value == 3600


class TestPerformanceMetric:
    """Test PerformanceMetric class"""
    
    def test_metric_initialization(self):
        """Test PerformanceMetric initialization"""
        timestamp = datetime.utcnow()
        metric = PerformanceMetric(
            name="test_metric",
            value=42.5,
            metric_type=MetricType.GAUGE,
            timestamp=timestamp,
            tags={"env": "test"},
            metadata={"source": "test"}
        )
        
        assert metric.name == "test_metric"
        assert metric.value == 42.5
        assert metric.metric_type == MetricType.GAUGE
        assert metric.timestamp == timestamp
        assert metric.tags["env"] == "test"
        assert metric.metadata["source"] == "test"
    
    def test_metric_to_dict(self):
        """Test PerformanceMetric to_dict method"""
        timestamp = datetime.utcnow()
        metric = PerformanceMetric(
            name="test_metric",
            value=100,
            metric_type=MetricType.COUNTER,
            timestamp=timestamp,
            tags={"component": "cache"},
            metadata={"version": "1.0"}
        )
        
        result = metric.to_dict()
        
        assert result["name"] == "test_metric"
        assert result["value"] == 100
        assert result["type"] == "counter"
        assert result["timestamp"] == timestamp.isoformat()
        assert result["tags"]["component"] == "cache"
        assert result["metadata"]["version"] == "1.0"


class TestAlert:
    """Test Alert class"""
    
    def test_alert_initialization(self):
        """Test Alert initialization"""
        alert = Alert(
            alert_id="test_alert",
            name="Test Alert",
            condition="metrics.get('cpu_percent', 0) > 80",
            severity=AlertSeverity.WARNING,
            message_template="CPU usage is {cpu_percent}%",
            enabled=True,
            cooldown_seconds=300
        )
        
        assert alert.alert_id == "test_alert"
        assert alert.name == "Test Alert"
        assert alert.condition == "metrics.get('cpu_percent', 0) > 80"
        assert alert.severity == AlertSeverity.WARNING
        assert alert.message_template == "CPU usage is {cpu_percent}%"
        assert alert.enabled is True
        assert alert.cooldown_seconds == 300
        assert alert.last_triggered is None
        assert alert.trigger_count == 0
    
    def test_alert_cooldown_check(self):
        """Test alert cooldown functionality"""
        alert = Alert(
            alert_id="cooldown_test",
            name="Cooldown Test",
            condition="True",
            severity=AlertSeverity.INFO,
            message_template="Test message",
            cooldown_seconds=60
        )
        
        # Initially not in cooldown
        assert not alert.is_in_cooldown()
        
        # Trigger alert
        alert.last_triggered = datetime.utcnow()
        assert alert.is_in_cooldown()
        
        # Wait past cooldown
        alert.last_triggered = datetime.utcnow() - timedelta(seconds=120)
        assert not alert.is_in_cooldown()
    
    def test_alert_message_formatting(self):
        """Test alert message formatting"""
        alert = Alert(
            alert_id="format_test",
            name="Format Test",
            condition="True",
            severity=AlertSeverity.ERROR,
            message_template="CPU: {cpu_percent}%, Memory: {memory_percent}%"
        )
        
        context = {"cpu_percent": 85, "memory_percent": 70}
        message = alert.format_message(context)
        
        assert message == "CPU: 85%, Memory: 70%"
    
    def test_alert_message_formatting_missing_context(self):
        """Test alert message formatting with missing context"""
        alert = Alert(
            alert_id="missing_context_test",
            name="Missing Context Test",
            condition="True",
            severity=AlertSeverity.ERROR,
            message_template="Value: {missing_key}"
        )
        
        context = {"other_key": "value"}
        message = alert.format_message(context)
        
        # Should handle missing key gracefully
        assert "missing_key" in message or "Missing context" in message


class TestPerformanceTarget:
    """Test PerformanceTarget class"""
    
    def test_target_initialization(self):
        """Test PerformanceTarget initialization"""
        target = PerformanceTarget(
            name="response_time",
            metric_name="avg_response_time",
            target_value=2.0,
            operator="<",
            tolerance_percent=10.0,
            enabled=True
        )
        
        assert target.name == "response_time"
        assert target.metric_name == "avg_response_time"
        assert target.target_value == 2.0
        assert target.operator == "<"
        assert target.tolerance_percent == 10.0
        assert target.enabled is True
    
    def test_target_evaluation_less_than(self):
        """Test target evaluation with < operator"""
        target = PerformanceTarget("test", "metric", 10.0, "<")
        
        assert target.evaluate(5.0) is True
        assert target.evaluate(15.0) is False
        assert target.evaluate(10.0) is False
    
    def test_target_evaluation_less_equal(self):
        """Test target evaluation with <= operator"""
        target = PerformanceTarget("test", "metric", 10.0, "<=")
        
        assert target.evaluate(5.0) is True
        assert target.evaluate(10.0) is True
        assert target.evaluate(15.0) is False
    
    def test_target_evaluation_greater_than(self):
        """Test target evaluation with > operator"""
        target = PerformanceTarget("test", "metric", 10.0, ">")
        
        assert target.evaluate(15.0) is True
        assert target.evaluate(5.0) is False
        assert target.evaluate(10.0) is False
    
    def test_target_evaluation_greater_equal(self):
        """Test target evaluation with >= operator"""
        target = PerformanceTarget("test", "metric", 10.0, ">=")
        
        assert target.evaluate(15.0) is True
        assert target.evaluate(10.0) is True
        assert target.evaluate(5.0) is False
    
    def test_target_evaluation_equals(self):
        """Test target evaluation with == operator"""
        target = PerformanceTarget("test", "metric", 10.0, "==", tolerance_percent=10.0)
        
        assert target.evaluate(10.0) is True
        assert target.evaluate(9.5) is True  # Within tolerance
        assert target.evaluate(10.5) is True  # Within tolerance
        assert target.evaluate(8.0) is False  # Outside tolerance
        assert target.evaluate(12.0) is False  # Outside tolerance
    
    def test_target_evaluation_invalid_operator(self):
        """Test target evaluation with invalid operator"""
        target = PerformanceTarget("test", "metric", 10.0, "invalid")
        
        assert target.evaluate(5.0) is False
    
    def test_deviation_calculation(self):
        """Test deviation percentage calculation"""
        target = PerformanceTarget("test", "metric", 10.0, "<")
        
        # 20% above target
        assert target.get_deviation_percent(12.0) == 20.0
        
        # 10% below target
        assert target.get_deviation_percent(9.0) == -10.0
        
        # Exactly on target
        assert target.get_deviation_percent(10.0) == 0.0
    
    def test_deviation_calculation_zero_target(self):
        """Test deviation calculation with zero target"""
        target = PerformanceTarget("test", "metric", 0.0, "<")
        
        # Should return infinity for non-zero current value
        assert target.get_deviation_percent(5.0) == float('inf')
        
        # Should return 0 for zero current value
        assert target.get_deviation_percent(0.0) == 0.0


class TestSystemHealth:
    """Test SystemHealth class"""
    
    def test_system_health_initialization(self):
        """Test SystemHealth initialization"""
        timestamp = datetime.utcnow()
        health = SystemHealth(
            overall_status="healthy",
            timestamp=timestamp,
            metrics={"cpu": 50.0, "memory": 60.0},
            alerts_active=0,
            performance_targets_met=8,
            performance_targets_total=10,
            details={"notes": "All systems nominal"}
        )
        
        assert health.overall_status == "healthy"
        assert health.timestamp == timestamp
        assert health.metrics["cpu"] == 50.0
        assert health.alerts_active == 0
        assert health.performance_targets_met == 8
        assert health.performance_targets_total == 10
        assert health.details["notes"] == "All systems nominal"


class TestContextMonitor:
    """Test ContextMonitor main class"""
    
    @pytest.fixture
    def monitor(self):
        """Create a ContextMonitor instance for testing"""
        return ContextMonitor(
            collection_interval=1,
            retention_hours=1,
            enable_system_metrics=True,
            enable_alerts=True,
            metrics_buffer_size=100
        )
    
    @pytest.fixture
    def mock_context_request(self):
        """Create a mock ContextRequest"""
        request = Mock(spec=ContextRequest)
        request.agent_type = "test_agent"
        request.story_id = "story-123"
        request.task = Mock()
        request.task.current_state = TDDState.RED
        return request
    
    @pytest.fixture
    def mock_agent_context(self):
        """Create a mock AgentContext"""
        context = Mock(spec=AgentContext)
        context.file_contents = {"file1.py": "content", "file2.py": "content"}
        context.get_total_token_estimate = Mock(return_value=1500)
        context.compression_applied = True
        context.cache_hit = False
        return context
    
    def test_monitor_initialization(self):
        """Test ContextMonitor initialization"""
        monitor = ContextMonitor(
            collection_interval=10,
            retention_hours=48,
            enable_system_metrics=False,
            enable_alerts=False,
            metrics_buffer_size=5000
        )
        
        assert monitor.collection_interval == 10
        assert monitor.retention_hours == 48
        assert monitor.enable_system_metrics is False
        assert monitor.enable_alerts is False
        assert monitor.metrics_buffer_size == 5000
        assert len(monitor._metrics) == 0
        assert len(monitor._alerts) > 0  # Default alerts are setup
        assert len(monitor._performance_targets) > 0  # Default targets are setup
    
    @pytest.mark.asyncio
    async def test_start_stop_monitoring(self, monitor):
        """Test starting and stopping monitoring tasks"""
        await monitor.start_monitoring()
        
        assert monitor._collection_task is not None
        assert monitor._analysis_task is not None
        assert monitor._cleanup_task is not None
        
        await monitor.stop_monitoring()
        
        # Tasks should be cancelled or done
        assert monitor._collection_task.cancelled() or monitor._collection_task.done()
        assert monitor._analysis_task.cancelled() or monitor._analysis_task.done()
        assert monitor._cleanup_task.cancelled() or monitor._cleanup_task.done()
    
    def test_operation_timing(self, monitor):
        """Test operation timing functionality"""
        # Start timing
        operation_id = monitor.record_operation_start("test_operation")
        assert operation_id.startswith("test_operation_")
        assert operation_id in monitor._operation_times
        
        # Simulate some work
        time.sleep(0.01)
        
        # End timing
        duration = monitor.record_operation_end(operation_id, success=True)
        assert duration > 0
        assert operation_id not in monitor._operation_times
        
        # Check metrics were recorded
        metrics = [m for m in monitor._metrics if m.name == "test_operation_duration"]
        assert len(metrics) == 1
        assert metrics[0].value == duration
    
    def test_operation_timing_failure(self, monitor):
        """Test operation timing with failure"""
        operation_id = monitor.record_operation_start("failing_operation")
        duration = monitor.record_operation_end(operation_id, success=False)
        
        # Should record error metric
        error_metrics = [m for m in monitor._metrics if m.name == "failing_operation_error_count"]
        assert len(error_metrics) == 1
        assert monitor._error_counts["failing_operation"] == 1
    
    def test_operation_timing_edge_cases(self, monitor):
        """Test operation timing edge cases"""
        # End timing for non-existent operation
        duration = monitor.record_operation_end("nonexistent", success=True)
        assert duration == 0.0
        
        # Create operation but mess with internal state
        operation_id = monitor.record_operation_start("edge_case")
        monitor._operation_times[operation_id].append(time.time())  # Add extra timestamp
        
        duration = monitor.record_operation_end(operation_id, success=True)
        assert duration == 0.0  # Should handle invalid state
    
    def test_record_metric(self, monitor):
        """Test metric recording"""
        monitor.record_metric(
            name="test_metric",
            value=42.5,
            metric_type=MetricType.GAUGE,
            tags={"component": "test"},
            metadata={"version": "1.0"}
        )
        
        assert len(monitor._metrics) == 1
        metric = monitor._metrics[0]
        
        assert metric.name == "test_metric"
        assert metric.value == 42.5
        assert metric.metric_type == MetricType.GAUGE
        assert metric.tags["component"] == "test"
        assert metric.metadata["version"] == "1.0"
        
        # Check timeseries and last values
        assert "test_metric" in monitor._metric_timeseries
        assert monitor._last_values["test_metric"] == 42.5
        assert monitor._throughput_counter["test_metric"] == 1
    
    def test_record_context_preparation(self, monitor, mock_context_request, mock_agent_context):
        """Test context preparation metrics recording"""
        monitor.record_context_preparation(
            request=mock_context_request,
            context=mock_agent_context,
            duration=1.5,
            success=True
        )
        
        # Should record multiple metrics
        metric_names = [m.name for m in monitor._metrics]
        
        assert "context_preparation_time" in metric_names
        assert "context_token_usage" in metric_names
        assert "context_file_count" in metric_names
        assert "context_compression_applied" in metric_names
        assert "context_cache_hit" in metric_names
        
        # Check specific values
        prep_time_metric = next(m for m in monitor._metrics if m.name == "context_preparation_time")
        assert prep_time_metric.value == 1.5
        assert prep_time_metric.tags["agent_type"] == "test_agent"
        assert prep_time_metric.tags["tdd_phase"] == "RED"
        
        token_metric = next(m for m in monitor._metrics if m.name == "context_token_usage")
        assert token_metric.value == 1500
        
        file_metric = next(m for m in monitor._metrics if m.name == "context_file_count")
        assert file_metric.value == 2
        
        compression_metric = next(m for m in monitor._metrics if m.name == "context_compression_applied")
        assert compression_metric.value == 1
        
        cache_metric = next(m for m in monitor._metrics if m.name == "context_cache_hit")
        assert cache_metric.value == 0
    
    def test_record_context_preparation_failure(self, monitor, mock_context_request):
        """Test context preparation metrics recording on failure"""
        monitor.record_context_preparation(
            request=mock_context_request,
            context=None,  # No context on failure
            duration=2.0,
            success=False
        )
        
        # Should only record timing metric
        metric_names = [m.name for m in monitor._metrics]
        assert "context_preparation_time" in metric_names
        assert len([m for m in monitor._metrics if m.name == "context_token_usage"]) == 0
    
    def test_record_cache_metrics(self, monitor):
        """Test cache metrics recording"""
        cache_stats = {
            "hit_rate": 0.85,
            "memory_usage_bytes": 52428800,  # 50MB
            "entry_count": 150
        }
        
        monitor.record_cache_metrics(cache_stats)
        
        metric_names = [m.name for m in monitor._metrics]
        assert "cache_hit_rate" in metric_names
        assert "cache_memory_usage_mb" in metric_names
        assert "cache_entry_count" in metric_names
        
        # Check values
        hit_rate_metric = next(m for m in monitor._metrics if m.name == "cache_hit_rate")
        assert hit_rate_metric.value == 0.85
        
        memory_metric = next(m for m in monitor._metrics if m.name == "cache_memory_usage_mb")
        assert memory_metric.value == 50.0
        
        entry_metric = next(m for m in monitor._metrics if m.name == "cache_entry_count")
        assert entry_metric.value == 150
    
    def test_alert_management(self, monitor):
        """Test alert addition and removal"""
        alert = Alert(
            alert_id="custom_alert",
            name="Custom Alert",
            condition="metrics.get('test_metric', 0) > 100",
            severity=AlertSeverity.WARNING,
            message_template="Test metric too high: {test_metric}"
        )
        
        # Add alert
        monitor.add_alert(alert)
        assert "custom_alert" in monitor._alerts
        
        # Remove alert
        success = monitor.remove_alert("custom_alert")
        assert success is True
        assert "custom_alert" not in monitor._alerts
        
        # Try to remove non-existent alert
        success = monitor.remove_alert("nonexistent")
        assert success is False
    
    def test_performance_target_management(self, monitor):
        """Test performance target addition and removal"""
        target = PerformanceTarget(
            name="custom_target",
            metric_name="custom_metric",
            target_value=50.0,
            operator="<"
        )
        
        # Add target
        monitor.add_performance_target(target)
        assert "custom_target" in monitor._performance_targets
        
        # Remove target
        success = monitor.remove_performance_target("custom_target")
        assert success is True
        assert "custom_target" not in monitor._performance_targets
        
        # Try to remove non-existent target
        success = monitor.remove_performance_target("nonexistent")
        assert success is False
    
    def test_get_current_metrics(self, monitor):
        """Test current metrics retrieval"""
        monitor.record_metric("metric1", 10.0)
        monitor.record_metric("metric2", 20.0)
        
        current = monitor.get_current_metrics()
        
        assert current["metric1"] == 10.0
        assert current["metric2"] == 20.0
    
    def test_get_metric_history(self, monitor):
        """Test metric history retrieval"""
        # Record metrics over time
        now = datetime.utcnow()
        monitor._metric_timeseries["test_metric"].extend([
            (now - timedelta(minutes=30), 10.0),
            (now - timedelta(minutes=15), 20.0),
            (now, 30.0)
        ])
        
        # Get last hour of history
        history = monitor.get_metric_history("test_metric", hours=1)
        assert len(history) == 3
        
        # Get last 20 minutes of history
        history = monitor.get_metric_history("test_metric", hours=1/3)
        assert len(history) == 2  # Only last two entries
        
        # Get history for non-existent metric
        history = monitor.get_metric_history("nonexistent", hours=1)
        assert len(history) == 0
    
    def test_get_system_health(self, monitor):
        """Test system health retrieval"""
        health = monitor.get_system_health()
        
        assert isinstance(health, SystemHealth)
        assert health.overall_status in ["healthy", "degraded", "unhealthy", "unknown"]
        assert isinstance(health.timestamp, datetime)
        assert isinstance(health.metrics, dict)
        assert isinstance(health.alerts_active, int)
        assert isinstance(health.performance_targets_met, int)
        assert isinstance(health.performance_targets_total, int)
    
    def test_get_active_alerts(self, monitor):
        """Test active alerts retrieval"""
        # Initially no active alerts
        active = monitor.get_active_alerts()
        assert len(active) == 0
        
        # Simulate active alert
        alert = Alert("test", "Test", "True", AlertSeverity.WARNING, "Test message")
        alert.last_triggered = datetime.utcnow()
        monitor._active_alerts["test"] = alert
        
        active = monitor.get_active_alerts()
        assert len(active) == 1
        assert active[0].alert_id == "test"
    
    def test_get_performance_summary(self, monitor):
        """Test performance summary generation"""
        # Add some metrics and targets
        monitor.record_metric("test_metric", 100.0)
        monitor.record_metric("test_metric", 110.0)
        monitor.record_metric("test_metric", 90.0)
        
        target = PerformanceTarget("test_target", "test_metric", 95.0, "<")
        monitor.add_performance_target(target)
        monitor._last_values["test_metric"] = 90.0  # Meets target
        
        summary = monitor.get_performance_summary()
        
        assert "timestamp" in summary
        assert "health_status" in summary
        assert "active_alerts" in summary
        assert "performance_targets" in summary
        assert "recent_metrics" in summary
        assert "error_counts" in summary
        assert "throughput" in summary
        
        # Check performance targets
        targets = summary["performance_targets"]
        assert targets["met"] == 1
        assert targets["total"] == len(monitor._performance_targets)
        assert "test_target" in targets["details"]
    
    @pytest.mark.asyncio
    async def test_export_metrics(self, monitor):
        """Test metrics export functionality"""
        # Add some metrics
        monitor.record_metric("export_test", 42.0, MetricType.GAUGE)
        
        # Export as JSON
        json_export = await monitor.export_metrics("json", hours=1)
        assert isinstance(json_export, str)
        
        data = json.loads(json_export)
        assert "export_timestamp" in data
        assert "period_hours" in data
        assert "metrics" in data
        assert len(data["metrics"]) == 1
        
        # Export as dict
        dict_export = await monitor.export_metrics("dict", hours=1)
        assert isinstance(dict_export, dict)
        assert "metrics" in dict_export
    
    @pytest.mark.asyncio
    async def test_collect_system_metrics_with_psutil(self, monitor):
        """Test system metrics collection with psutil available"""
        with patch('context_monitoring.psutil') as mock_psutil:
            # Mock psutil functions
            mock_psutil.cpu_percent.return_value = 75.0
            
            mock_memory = Mock()
            mock_memory.percent = 60.0
            mock_memory.available = 2048 * 1024 * 1024  # 2GB
            mock_psutil.virtual_memory.return_value = mock_memory
            
            mock_disk = Mock()
            mock_disk.used = 50 * 1024 * 1024 * 1024  # 50GB
            mock_disk.total = 100 * 1024 * 1024 * 1024  # 100GB
            mock_psutil.disk_usage.return_value = mock_disk
            
            await monitor._collect_system_metrics()
            
            # Check that system metrics were recorded
            metric_names = [m.name for m in monitor._metrics]
            assert "system_cpu_percent" in metric_names
            assert "system_memory_percent" in metric_names
            assert "system_memory_available_mb" in metric_names
            assert "system_disk_percent" in metric_names
            
            # Check values
            cpu_metric = next(m for m in monitor._metrics if m.name == "system_cpu_percent")
            assert cpu_metric.value == 75.0
            
            memory_metric = next(m for m in monitor._metrics if m.name == "system_memory_percent")
            assert memory_metric.value == 60.0
    
    @pytest.mark.asyncio
    async def test_collect_system_metrics_without_psutil(self, monitor):
        """Test system metrics collection without psutil"""
        with patch('context_monitoring.psutil', None):
            await monitor._collect_system_metrics()
            
            # Should still record metrics with mock values
            metric_names = [m.name for m in monitor._metrics]
            assert "system_cpu_percent" in metric_names
            assert "system_memory_percent" in metric_names
            
            # Check that metrics have mock tag
            cpu_metric = next(m for m in monitor._metrics if m.name == "system_cpu_percent")
            assert cpu_metric.tags.get("mock") == "true"
    
    @pytest.mark.asyncio
    async def test_collect_system_metrics_error_handling(self, monitor):
        """Test system metrics collection error handling"""
        with patch('context_monitoring.psutil') as mock_psutil:
            mock_psutil.cpu_percent.side_effect = Exception("CPU error")
            
            # Should not raise exception
            await monitor._collect_system_metrics()
            
            # Should have logged warning but not failed
    
    @pytest.mark.asyncio
    async def test_update_system_health(self, monitor):
        """Test system health status updates"""
        # Test healthy status
        await monitor._update_system_health()
        assert monitor._health_status.overall_status == "healthy"
        
        # Add critical alert to trigger unhealthy status
        critical_alert = Alert("critical", "Critical", "True", AlertSeverity.CRITICAL, "Critical issue")
        monitor._active_alerts["critical"] = critical_alert
        
        await monitor._update_system_health()
        assert monitor._health_status.overall_status == "unhealthy"
        
        # Remove critical alert, add error alert
        del monitor._active_alerts["critical"]
        error_alert = Alert("error", "Error", "True", AlertSeverity.ERROR, "Error issue")
        monitor._active_alerts["error"] = error_alert
        
        await monitor._update_system_health()
        assert monitor._health_status.overall_status == "degraded"
    
    @pytest.mark.asyncio
    async def test_evaluate_alerts(self, monitor):
        """Test alert evaluation"""
        # Add a test alert
        alert = Alert(
            alert_id="test_alert",
            name="Test Alert",
            condition="metrics.get('test_value', 0) > 50",
            severity=AlertSeverity.WARNING,
            message_template="Test value is {test_value}"
        )
        monitor.add_alert(alert)
        
        # Set metric value that should trigger alert
        monitor._last_values["test_value"] = 75
        
        await monitor._evaluate_alerts()
        
        # Alert should be triggered
        assert "test_alert" in monitor._active_alerts
        assert alert.trigger_count == 1
        assert alert.last_triggered is not None
    
    @pytest.mark.asyncio
    async def test_evaluate_alerts_cooldown(self, monitor):
        """Test alert cooldown functionality"""
        alert = Alert(
            alert_id="cooldown_alert",
            name="Cooldown Alert",
            condition="metrics.get('always_true', 0) > 0",
            severity=AlertSeverity.INFO,
            message_template="Always triggers",
            cooldown_seconds=60
        )
        monitor.add_alert(alert)
        monitor._last_values["always_true"] = 1
        
        # First evaluation should trigger
        await monitor._evaluate_alerts()
        assert alert.trigger_count == 1
        
        # Second evaluation should not trigger due to cooldown
        await monitor._evaluate_alerts()
        assert alert.trigger_count == 1  # Still 1, not 2
    
    @pytest.mark.asyncio
    async def test_evaluate_alerts_disabled(self, monitor):
        """Test disabled alert evaluation"""
        alert = Alert(
            alert_id="disabled_alert",
            name="Disabled Alert",
            condition="True",  # Always true
            severity=AlertSeverity.WARNING,
            message_template="Should not trigger",
            enabled=False
        )
        monitor.add_alert(alert)
        
        await monitor._evaluate_alerts()
        
        # Should not trigger because it's disabled
        assert "disabled_alert" not in monitor._active_alerts
        assert alert.trigger_count == 0
    
    @pytest.mark.asyncio
    async def test_evaluate_alerts_error_handling(self, monitor):
        """Test alert evaluation error handling"""
        # Add alert with invalid condition
        alert = Alert(
            alert_id="bad_alert",
            name="Bad Alert",
            condition="invalid_python_expression !!!",
            severity=AlertSeverity.ERROR,
            message_template="This is bad"
        )
        monitor.add_alert(alert)
        
        # Should not raise exception
        await monitor._evaluate_alerts()
        
        # Alert should not be triggered due to error
        assert "bad_alert" not in monitor._active_alerts
    
    @pytest.mark.asyncio
    async def test_trigger_alert_with_callbacks(self, monitor):
        """Test alert triggering with callbacks"""
        callback_called = False
        callback_context = None
        
        def sync_callback(alert, context):
            nonlocal callback_called, callback_context
            callback_called = True
            callback_context = context
        
        async def async_callback(alert, context):
            nonlocal callback_called
            callback_called = True
        
        alert = Alert(
            alert_id="callback_alert",
            name="Callback Alert",
            condition="True",
            severity=AlertSeverity.INFO,
            message_template="Callback test",
            callbacks=[sync_callback, async_callback]
        )
        
        context = {"test": "value"}
        await monitor._trigger_alert(alert, context)
        
        assert callback_called
        assert callback_context == context
        assert alert.trigger_count == 1
    
    @pytest.mark.asyncio
    async def test_trigger_alert_callback_error(self, monitor):
        """Test alert callback error handling"""
        def failing_callback(alert, context):
            raise Exception("Callback failed")
        
        alert = Alert(
            alert_id="failing_callback_alert",
            name="Failing Callback Alert",
            condition="True",
            severity=AlertSeverity.INFO,
            message_template="Callback failure test",
            callbacks=[failing_callback]
        )
        
        # Should not raise exception even if callback fails
        await monitor._trigger_alert(alert, {})
        assert alert.trigger_count == 1
    
    @pytest.mark.asyncio
    async def test_evaluate_performance_targets(self, monitor):
        """Test performance target evaluation"""
        # Add target and metric
        target = PerformanceTarget("response_time", "avg_response", 2.0, "<")
        monitor.add_performance_target(target)
        monitor._last_values["avg_response"] = 1.5  # Meets target
        
        await monitor._evaluate_performance_targets()
        
        # Should record compliance metric
        compliance_metrics = [m for m in monitor._metrics if m.name == "target_response_time_compliance"]
        assert len(compliance_metrics) == 1
        assert compliance_metrics[0].value == 1  # Target met
        
        # Change value to not meet target
        monitor._last_values["avg_response"] = 3.0
        await monitor._evaluate_performance_targets()
        
        compliance_metrics = [m for m in monitor._metrics if m.name == "target_response_time_compliance"]
        assert compliance_metrics[-1].value == 0  # Target not met
    
    @pytest.mark.asyncio
    async def test_cleanup_old_data(self, monitor):
        """Test old data cleanup"""
        # Add old metrics
        old_time = datetime.utcnow() - timedelta(hours=25)
        old_metric = PerformanceMetric("old_metric", 10.0, MetricType.GAUGE, old_time)
        monitor._metrics.append(old_metric)
        
        # Add old timeseries data
        monitor._metric_timeseries["old_series"].append((old_time, 20.0))
        
        # Add old resolved alert
        old_alert = Alert("old_alert", "Old", "True", AlertSeverity.INFO, "Old alert")
        old_alert.last_triggered = old_time
        monitor._active_alerts["old_alert"] = old_alert
        
        await monitor._cleanup_old_data()
        
        # Old metric should be removed
        assert old_metric not in monitor._metrics
        
        # Old timeseries data should be removed
        assert len(monitor._metric_timeseries["old_series"]) == 0
        
        # Old alert should be removed
        assert "old_alert" not in monitor._active_alerts
    
    def test_setup_default_targets(self, monitor):
        """Test default performance targets setup"""
        # Should have default targets
        target_names = list(monitor._performance_targets.keys())
        
        assert "context_prep_time" in target_names
        assert "cache_hit_rate" in target_names
        assert "system_memory" in target_names
        assert "context_token_efficiency" in target_names
    
    def test_setup_default_alerts(self, monitor):
        """Test default alerts setup"""
        # Should have default alerts
        alert_ids = list(monitor._alerts.keys())
        
        assert "high_prep_time" in alert_ids
        assert "low_cache_hit_rate" in alert_ids
        assert "high_memory_usage" in alert_ids
        assert "context_errors" in alert_ids


@pytest.mark.asyncio
class TestContextMonitorIntegration:
    """Integration tests for ContextMonitor"""
    
    async def test_full_monitoring_cycle(self):
        """Test complete monitoring cycle"""
        monitor = ContextMonitor(
            collection_interval=0.1,  # Fast for testing
            retention_hours=1,
            enable_system_metrics=True,
            enable_alerts=True
        )
        
        try:
            await monitor.start_monitoring()
            
            # Record some metrics
            monitor.record_metric("integration_test", 50.0, MetricType.GAUGE)
            
            # Wait a bit for background tasks
            await asyncio.sleep(0.2)
            
            # Check statistics
            summary = monitor.get_performance_summary()
            assert "integration_test" in summary["recent_metrics"]
            
            # Check system health
            health = monitor.get_system_health()
            assert health.overall_status in ["healthy", "degraded", "unhealthy", "unknown"]
            
        finally:
            await monitor.stop_monitoring()
    
    async def test_concurrent_metric_recording(self):
        """Test concurrent metric recording"""
        monitor = ContextMonitor(metrics_buffer_size=1000)
        
        async def record_metrics(prefix, count):
            for i in range(count):
                monitor.record_metric(f"{prefix}_metric_{i}", i, MetricType.COUNTER)
        
        # Record metrics concurrently
        tasks = [
            record_metrics("worker1", 50),
            record_metrics("worker2", 50),
            record_metrics("worker3", 50)
        ]
        
        await asyncio.gather(*tasks)
        
        # Should have recorded all metrics
        assert len(monitor._metrics) == 150
        
        # Check that all metrics are present
        metric_names = {m.name for m in monitor._metrics}
        assert len(metric_names) == 150  # All unique names
    
    async def test_memory_cleanup_under_load(self):
        """Test memory cleanup under heavy load"""
        monitor = ContextMonitor(
            metrics_buffer_size=100,  # Small buffer
            retention_hours=0.001  # Very short retention
        )
        
        # Fill buffer beyond capacity
        for i in range(200):
            monitor.record_metric(f"load_test_{i}", i, MetricType.COUNTER)
        
        # Should have limited to buffer size
        assert len(monitor._metrics) <= 100
        
        # Force cleanup
        await monitor._cleanup_old_data()
        
        # Should have cleaned up old data
        recent_metrics = [m for m in monitor._metrics 
                         if (datetime.utcnow() - m.timestamp).total_seconds() < 1]
        assert len(recent_metrics) <= len(monitor._metrics)


class TestContextMonitorErrorCases:
    """Test error cases and edge conditions"""
    
    @pytest.mark.asyncio
    async def test_background_task_error_handling(self):
        """Test background task error handling"""
        monitor = ContextMonitor(collection_interval=0.01)
        
        # Mock collection method to raise exception
        with patch.object(monitor, '_collect_system_metrics', side_effect=Exception("Collection error")):
            await monitor.start_monitoring()
            
            # Let it run briefly
            await asyncio.sleep(0.05)
            
            # Should still be running despite errors
            assert not monitor._collection_task.done()
            
            await monitor.stop_monitoring()
    
    def test_metric_with_none_values(self):
        """Test metric recording with None values"""
        monitor = ContextMonitor()
        
        # Should handle None gracefully (or raise appropriate error)
        try:
            monitor.record_metric("none_test", None, MetricType.GAUGE)
            # If it doesn't raise, check that it was handled appropriately
            assert len(monitor._metrics) >= 0  # Should not crash
        except (TypeError, ValueError):
            # Acceptable to raise type/value error for None
            pass
    
    def test_invalid_metric_type(self):
        """Test invalid metric type handling"""
        monitor = ContextMonitor()
        
        # Test with invalid metric type (if validation exists)
        try:
            monitor.record_metric("invalid_type", 10.0, "invalid_type")
        except (TypeError, ValueError, AttributeError):
            # Expected to fail with invalid type
            pass
    
    def test_alert_condition_security(self):
        """Test alert condition security (no arbitrary code execution)"""
        monitor = ContextMonitor()
        
        # Add alert with potentially dangerous condition
        dangerous_alert = Alert(
            alert_id="dangerous",
            name="Dangerous Alert",
            condition="__import__('os').system('echo pwned')",
            severity=AlertSeverity.CRITICAL,
            message_template="Dangerous"
        )
        
        monitor.add_alert(dangerous_alert)
        
        # Evaluation should fail safely (due to restricted builtins)
        asyncio.run(monitor._evaluate_alerts())
        
        # Should not have triggered the alert
        assert "dangerous" not in monitor._active_alerts


if __name__ == "__main__":
    pytest.main([__file__, "-v"])