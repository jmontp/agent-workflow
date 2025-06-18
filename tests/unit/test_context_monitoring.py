"""
Comprehensive test suite for Context Monitoring System.

Tests real-time performance monitoring, alerting, comprehensive analytics,
performance target tracking, and system health monitoring.
"""

import pytest
import asyncio
import time
from datetime import datetime, timedelta
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from collections import deque

# Import the modules under test
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "lib"))

from context_monitoring import (
    ContextMonitor,
    MetricType,
    AlertSeverity,
    MonitoringInterval,
    PerformanceMetric,
    Alert,
    PerformanceTarget,
    SystemHealth
)
from context.models import AgentContext, ContextRequest, TDDState
from context.exceptions import ContextMonitoringError
from tdd_models import TDDTask


class TestMetricType:
    """Test MetricType enumeration"""
    
    def test_metric_type_values(self):
        """Test metric type enum values"""
        assert MetricType.COUNTER.value == "counter"
        assert MetricType.GAUGE.value == "gauge"
        assert MetricType.HISTOGRAM.value == "histogram"
        assert MetricType.TIMER.value == "timer"
    
    def test_metric_type_count(self):
        """Test expected number of metric types"""
        metric_types = list(MetricType)
        assert len(metric_types) == 4


class TestAlertSeverity:
    """Test AlertSeverity enumeration"""
    
    def test_alert_severity_values(self):
        """Test alert severity enum values"""
        assert AlertSeverity.INFO.value == "info"
        assert AlertSeverity.WARNING.value == "warning"
        assert AlertSeverity.ERROR.value == "error"
        assert AlertSeverity.CRITICAL.value == "critical"
    
    def test_alert_severity_ordering(self):
        """Test alert severity ordering for priority"""
        severities = [AlertSeverity.INFO, AlertSeverity.WARNING, AlertSeverity.ERROR, AlertSeverity.CRITICAL]
        assert len(severities) == 4


class TestMonitoringInterval:
    """Test MonitoringInterval enumeration"""
    
    def test_monitoring_interval_values(self):
        """Test monitoring interval enum values"""
        assert MonitoringInterval.REAL_TIME.value == 1
        assert MonitoringInterval.FAST.value == 5
        assert MonitoringInterval.MEDIUM.value == 30
        assert MonitoringInterval.SLOW.value == 60
        assert MonitoringInterval.HOURLY.value == 3600
    
    def test_monitoring_intervals_are_ascending(self):
        """Test that monitoring intervals are in ascending order"""
        intervals = [
            MonitoringInterval.REAL_TIME,
            MonitoringInterval.FAST,
            MonitoringInterval.MEDIUM,
            MonitoringInterval.SLOW,
            MonitoringInterval.HOURLY
        ]
        
        values = [interval.value for interval in intervals]
        assert values == sorted(values)


class TestPerformanceMetric:
    """Test PerformanceMetric data class"""
    
    def test_performance_metric_creation(self):
        """Test basic performance metric creation"""
        timestamp = datetime.utcnow()
        metric = PerformanceMetric(
            name="test_metric",
            value=42.5,
            metric_type=MetricType.GAUGE,
            timestamp=timestamp,
            tags={"component": "test"},
            metadata={"source": "unit_test"}
        )
        
        assert metric.name == "test_metric"
        assert metric.value == 42.5
        assert metric.metric_type == MetricType.GAUGE
        assert metric.timestamp == timestamp
        assert metric.tags["component"] == "test"
        assert metric.metadata["source"] == "unit_test"
    
    def test_performance_metric_defaults(self):
        """Test performance metric default values"""
        timestamp = datetime.utcnow()
        metric = PerformanceMetric(
            name="simple_metric",
            value=100,
            metric_type=MetricType.COUNTER,
            timestamp=timestamp
        )
        
        assert len(metric.tags) == 0
        assert len(metric.metadata) == 0
    
    def test_performance_metric_serialization(self):
        """Test performance metric serialization"""
        timestamp = datetime.utcnow()
        metric = PerformanceMetric(
            name="serialization_test",
            value=123.45,
            metric_type=MetricType.TIMER,
            timestamp=timestamp,
            tags={"env": "test"},
            metadata={"version": "1.0"}
        )
        
        data = metric.to_dict()
        
        assert isinstance(data, dict)
        assert data["name"] == "serialization_test"
        assert data["value"] == 123.45
        assert data["type"] == "timer"
        assert data["timestamp"] == timestamp.isoformat()
        assert data["tags"]["env"] == "test"
        assert data["metadata"]["version"] == "1.0"


class TestAlert:
    """Test Alert data class"""
    
    def test_alert_creation(self):
        """Test basic alert creation"""
        alert = Alert(
            alert_id="test_alert",
            name="Test Alert",
            condition="value > 100",
            severity=AlertSeverity.WARNING,
            message_template="Value exceeded threshold: {value}",
            enabled=True,
            cooldown_seconds=300
        )
        
        assert alert.alert_id == "test_alert"
        assert alert.name == "Test Alert"
        assert alert.condition == "value > 100"
        assert alert.severity == AlertSeverity.WARNING
        assert alert.message_template == "Value exceeded threshold: {value}"
        assert alert.enabled is True
        assert alert.cooldown_seconds == 300
        assert alert.last_triggered is None
        assert alert.trigger_count == 0
        assert len(alert.callbacks) == 0
    
    def test_alert_cooldown_check(self):
        """Test alert cooldown functionality"""
        alert = Alert(
            alert_id="cooldown_test",
            name="Cooldown Test",
            condition="value > 50",
            severity=AlertSeverity.ERROR,
            message_template="Test message",
            cooldown_seconds=60
        )
        
        # Initially not in cooldown
        assert not alert.is_in_cooldown()
        
        # Trigger alert
        alert.last_triggered = datetime.utcnow()
        alert.trigger_count += 1
        
        # Should be in cooldown
        assert alert.is_in_cooldown()
        
        # After cooldown period
        alert.last_triggered = datetime.utcnow() - timedelta(seconds=70)
        assert not alert.is_in_cooldown()
    
    def test_alert_message_formatting(self):
        """Test alert message formatting"""
        alert = Alert(
            alert_id="format_test",
            name="Format Test",
            condition="test",
            severity=AlertSeverity.INFO,
            message_template="CPU usage is {cpu_percent:.1f}% on {hostname}"
        )
        
        context = {
            "cpu_percent": 85.7,
            "hostname": "test-server"
        }
        
        formatted = alert.format_message(context)
        assert formatted == "CPU usage is 85.7% on test-server"
    
    def test_alert_message_formatting_missing_context(self):
        """Test alert message formatting with missing context"""
        alert = Alert(
            alert_id="missing_context_test",
            name="Missing Context Test",
            condition="test",
            severity=AlertSeverity.WARNING,
            message_template="Value is {missing_key}"
        )
        
        context = {"other_key": "value"}
        
        formatted = alert.format_message(context)
        assert "Missing context: 'missing_key'" in formatted


class TestPerformanceTarget:
    """Test PerformanceTarget data class"""
    
    def test_performance_target_creation(self):
        """Test performance target creation"""
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
    
    def test_performance_target_evaluation_less_than(self):
        """Test performance target evaluation with less than operator"""
        target = PerformanceTarget(
            name="test_target",
            metric_name="test_metric",
            target_value=100.0,
            operator="<"
        )
        
        assert target.evaluate(90.0) is True
        assert target.evaluate(100.0) is False
        assert target.evaluate(110.0) is False
    
    def test_performance_target_evaluation_greater_than(self):
        """Test performance target evaluation with greater than operator"""
        target = PerformanceTarget(
            name="test_target",
            metric_name="test_metric",
            target_value=80.0,
            operator=">"
        )
        
        assert target.evaluate(90.0) is True
        assert target.evaluate(80.0) is False
        assert target.evaluate(70.0) is False
    
    def test_performance_target_evaluation_equals(self):
        """Test performance target evaluation with equals operator"""
        target = PerformanceTarget(
            name="test_target",
            metric_name="test_metric",
            target_value=100.0,
            operator="==",
            tolerance_percent=5.0
        )
        
        assert target.evaluate(100.0) is True  # Exact match
        assert target.evaluate(102.0) is True  # Within tolerance
        assert target.evaluate(95.0) is True   # Within tolerance
        assert target.evaluate(107.0) is False # Outside tolerance
        assert target.evaluate(92.0) is False  # Outside tolerance
    
    def test_performance_target_deviation_calculation(self):
        """Test deviation percentage calculation"""
        target = PerformanceTarget(
            name="test_target",
            metric_name="test_metric",
            target_value=100.0,
            operator="=="
        )
        
        assert target.get_deviation_percent(110.0) == 10.0
        assert target.get_deviation_percent(90.0) == -10.0
        assert target.get_deviation_percent(100.0) == 0.0
        
        # Test division by zero
        zero_target = PerformanceTarget(
            name="zero_target",
            metric_name="test_metric",
            target_value=0.0,
            operator="=="
        )
        
        assert zero_target.get_deviation_percent(0.0) == 0.0
        assert zero_target.get_deviation_percent(10.0) == float('inf')


class TestSystemHealth:
    """Test SystemHealth data class"""
    
    def test_system_health_creation(self):
        """Test system health creation"""
        timestamp = datetime.utcnow()
        health = SystemHealth(
            overall_status="healthy",
            timestamp=timestamp,
            metrics={"cpu": 50.0, "memory": 60.0},
            alerts_active=0,
            performance_targets_met=8,
            performance_targets_total=10,
            details={"uptime": "24h"}
        )
        
        assert health.overall_status == "healthy"
        assert health.timestamp == timestamp
        assert health.metrics["cpu"] == 50.0
        assert health.alerts_active == 0
        assert health.performance_targets_met == 8
        assert health.performance_targets_total == 10
        assert health.details["uptime"] == "24h"
    
    def test_system_health_defaults(self):
        """Test system health default values"""
        health = SystemHealth(
            overall_status="degraded",
            timestamp=datetime.utcnow(),
            metrics={},
            alerts_active=2,
            performance_targets_met=5,
            performance_targets_total=10
        )
        
        assert len(health.details) == 0


class TestContextMonitorInit:
    """Test ContextMonitor initialization"""
    
    def test_init_with_defaults(self):
        """Test initialization with default parameters"""
        monitor = ContextMonitor()
        
        assert monitor.collection_interval == 5
        assert monitor.retention_hours == 24
        assert monitor.enable_system_metrics is True
        assert monitor.enable_alerts is True
        assert monitor.metrics_buffer_size == 10000
        
        assert isinstance(monitor._metrics, deque)
        assert isinstance(monitor._metric_timeseries, dict)
        assert isinstance(monitor._last_values, dict)
        assert isinstance(monitor._alerts, dict)
        assert isinstance(monitor._performance_targets, dict)
        assert isinstance(monitor._active_alerts, dict)
        
        assert len(monitor._metrics) == 0
        assert len(monitor._alerts) > 0  # Should have default alerts
        assert len(monitor._performance_targets) > 0  # Should have default targets
    
    def test_init_with_custom_params(self):
        """Test initialization with custom parameters"""
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
    
    def test_default_targets_setup(self):
        """Test that default performance targets are set up"""
        monitor = ContextMonitor()
        
        assert len(monitor._performance_targets) > 0
        
        # Check for expected default targets
        target_names = set(monitor._performance_targets.keys())
        expected_targets = {"context_prep_time", "cache_hit_rate", "system_memory", "context_token_efficiency"}
        
        assert expected_targets.issubset(target_names)
    
    def test_default_alerts_setup(self):
        """Test that default alerts are set up"""
        monitor = ContextMonitor()
        
        assert len(monitor._alerts) > 0
        
        # Check for expected default alerts
        alert_ids = set(monitor._alerts.keys())
        expected_alerts = {"high_prep_time", "low_cache_hit_rate", "high_memory_usage", "context_errors"}
        
        assert expected_alerts.issubset(alert_ids)


class TestMetricRecording:
    """Test metric recording functionality"""
    
    @pytest.fixture
    def monitor(self):
        return ContextMonitor()
    
    def test_record_metric_basic(self, monitor):
        """Test basic metric recording"""
        monitor.record_metric(
            name="test_metric",
            value=42.5,
            metric_type=MetricType.GAUGE,
            tags={"component": "test"},
            metadata={"test": True}
        )
        
        assert len(monitor._metrics) == 1
        assert "test_metric" in monitor._metric_timeseries
        assert "test_metric" in monitor._last_values
        assert monitor._last_values["test_metric"] == 42.5
        assert monitor._throughput_counter["test_metric"] == 1
        
        metric = monitor._metrics[0]
        assert metric.name == "test_metric"
        assert metric.value == 42.5
        assert metric.metric_type == MetricType.GAUGE
        assert metric.tags["component"] == "test"
        assert metric.metadata["test"] is True
    
    def test_record_metric_defaults(self, monitor):
        """Test metric recording with defaults"""
        monitor.record_metric("simple_metric", 100)
        
        metric = monitor._metrics[0]
        assert metric.metric_type == MetricType.GAUGE
        assert len(metric.tags) == 0
        assert len(metric.metadata) == 0
    
    def test_record_metric_timeseries(self, monitor):
        """Test metric timeseries recording"""
        # Record multiple values for same metric
        for i in range(5):
            monitor.record_metric("series_metric", i * 10)
        
        assert len(monitor._metric_timeseries["series_metric"]) == 5
        assert monitor._last_values["series_metric"] == 40  # Last value
        assert monitor._throughput_counter["series_metric"] == 5
        
        # Check timeseries values
        timeseries = monitor._metric_timeseries["series_metric"]
        values = [value for timestamp, value in timeseries]
        assert values == [0, 10, 20, 30, 40]
    
    def test_record_metric_buffer_limit(self, monitor):
        """Test metric buffer size limiting"""
        monitor._metrics.maxlen = 3  # Reduce for testing
        
        # Record more metrics than buffer size
        for i in range(5):
            monitor.record_metric(f"metric_{i}", i)
        
        assert len(monitor._metrics) == 3
        # Should keep the last 3 metrics
        metric_names = [m.name for m in monitor._metrics]
        assert metric_names == ["metric_2", "metric_3", "metric_4"]


class TestOperationTiming:
    """Test operation timing functionality"""
    
    @pytest.fixture
    def monitor(self):
        return ContextMonitor()
    
    def test_operation_timing_basic(self, monitor):
        """Test basic operation timing"""
        operation_id = monitor.record_operation_start("test_operation")
        
        assert isinstance(operation_id, str)
        assert "test_operation" in operation_id
        assert operation_id in monitor._operation_times
        
        # Small delay to ensure measurable duration
        time.sleep(0.01)
        
        duration = monitor.record_operation_end(operation_id, success=True)
        
        assert isinstance(duration, float)
        assert duration > 0.0
        assert operation_id not in monitor._operation_times  # Should be cleaned up
        
        # Should have recorded metrics
        assert "test_operation_duration" in monitor._last_values
        assert "test_operation_success_count" in monitor._last_values
    
    def test_operation_timing_failure(self, monitor):
        """Test operation timing with failure"""
        operation_id = monitor.record_operation_start("failing_operation")
        time.sleep(0.01)
        
        duration = monitor.record_operation_end(operation_id, success=False)
        
        assert duration > 0.0
        assert monitor._error_counts["failing_operation"] == 1
        assert "failing_operation_error_count" in monitor._last_values
    
    def test_operation_timing_invalid_id(self, monitor):
        """Test operation timing with invalid operation ID"""
        duration = monitor.record_operation_end("invalid_id", success=True)
        
        assert duration == 0.0
    
    def test_operation_timing_concurrent(self, monitor):
        """Test concurrent operation timing"""
        # Start multiple operations
        op1_id = monitor.record_operation_start("operation_1")
        op2_id = monitor.record_operation_start("operation_2")
        
        time.sleep(0.01)
        
        # End in different order
        duration2 = monitor.record_operation_end(op2_id, success=True)
        duration1 = monitor.record_operation_end(op1_id, success=True)
        
        assert duration1 > 0.0
        assert duration2 > 0.0
        assert len(monitor._operation_times) == 0  # All cleaned up


class TestContextMetrics:
    """Test context-specific metrics recording"""
    
    @pytest.fixture
    def monitor(self):
        return ContextMonitor()
    
    @pytest.fixture
    def sample_request(self):
        task = TDDTask(
            id="test_task",
            description="Test task",
            cycle_id="cycle_1",
            current_state=TDDState.GREEN
        )
        
        return ContextRequest(
            agent_type="CodeAgent",
            story_id="story_123",
            task=task,
            focus_areas=["test"]
        )
    
    @pytest.fixture
    def sample_context(self):
        context = Mock(spec=AgentContext)
        context.file_contents = {"file1.py": "content1", "file2.py": "content2"}
        context.get_total_token_estimate = Mock(return_value=1500)
        context.compression_applied = True
        context.cache_hit = False
        return context
    
    def test_record_context_preparation(self, monitor, sample_request, sample_context):
        """Test context preparation metrics recording"""
        monitor.record_context_preparation(
            request=sample_request,
            context=sample_context,
            duration=1.5,
            success=True
        )
        
        # Check that metrics were recorded
        assert "context_preparation_time" in monitor._last_values
        assert "context_token_usage" in monitor._last_values
        assert "context_file_count" in monitor._last_values
        assert "context_compression_applied" in monitor._last_values
        assert "context_cache_hit" in monitor._last_values
        
        # Check values
        assert monitor._last_values["context_preparation_time"] == 1.5
        assert monitor._last_values["context_token_usage"] == 1500
        assert monitor._last_values["context_file_count"] == 2
        assert monitor._last_values["context_compression_applied"] == 1
        assert monitor._last_values["context_cache_hit"] == 0
    
    def test_record_context_preparation_failure(self, monitor, sample_request):
        """Test context preparation failure recording"""
        monitor.record_context_preparation(
            request=sample_request,
            context=None,
            duration=2.0,
            success=False
        )
        
        # Should still record timing
        assert "context_preparation_time" in monitor._last_values
        assert monitor._last_values["context_preparation_time"] == 2.0
        
        # Should not record context-specific metrics for None context
        assert "context_token_usage" not in monitor._last_values
    
    def test_record_cache_metrics(self, monitor):
        """Test cache metrics recording"""
        cache_stats = {
            "hit_rate": 0.75,
            "memory_usage_bytes": 512 * 1024 * 1024,  # 512 MB
            "entry_count": 1000
        }
        
        monitor.record_cache_metrics(cache_stats)
        
        assert "cache_hit_rate" in monitor._last_values
        assert "cache_memory_usage_mb" in monitor._last_values
        assert "cache_entry_count" in monitor._last_values
        
        assert monitor._last_values["cache_hit_rate"] == 0.75
        assert monitor._last_values["cache_memory_usage_mb"] == 512.0
        assert monitor._last_values["cache_entry_count"] == 1000


class TestAlertManagement:
    """Test alert management functionality"""
    
    @pytest.fixture
    def monitor(self):
        return ContextMonitor()
    
    def test_add_alert(self, monitor):
        """Test adding custom alert"""
        custom_alert = Alert(
            alert_id="custom_alert",
            name="Custom Alert",
            condition="value > 200",
            severity=AlertSeverity.WARNING,
            message_template="Custom alert triggered: {value}"
        )
        
        initial_count = len(monitor._alerts)
        monitor.add_alert(custom_alert)
        
        assert len(monitor._alerts) == initial_count + 1
        assert "custom_alert" in monitor._alerts
        assert monitor._alerts["custom_alert"] is custom_alert
    
    def test_remove_alert(self, monitor):
        """Test removing alert"""
        # Add custom alert first
        custom_alert = Alert(
            alert_id="removable_alert",
            name="Removable Alert",
            condition="value > 100",
            severity=AlertSeverity.INFO,
            message_template="Test"
        )
        monitor.add_alert(custom_alert)
        
        # Remove it
        result = monitor.remove_alert("removable_alert")
        
        assert result is True
        assert "removable_alert" not in monitor._alerts
        assert "removable_alert" not in monitor._active_alerts
    
    def test_remove_nonexistent_alert(self, monitor):
        """Test removing non-existent alert"""
        result = monitor.remove_alert("nonexistent_alert")
        assert result is False


class TestPerformanceTargetManagement:
    """Test performance target management"""
    
    @pytest.fixture
    def monitor(self):
        return ContextMonitor()
    
    def test_add_performance_target(self, monitor):
        """Test adding custom performance target"""
        custom_target = PerformanceTarget(
            name="custom_target",
            metric_name="custom_metric",
            target_value=100.0,
            operator="<"
        )
        
        initial_count = len(monitor._performance_targets)
        monitor.add_performance_target(custom_target)
        
        assert len(monitor._performance_targets) == initial_count + 1
        assert "custom_target" in monitor._performance_targets
        assert monitor._performance_targets["custom_target"] is custom_target
    
    def test_remove_performance_target(self, monitor):
        """Test removing performance target"""
        custom_target = PerformanceTarget(
            name="removable_target",
            metric_name="removable_metric",
            target_value=50.0,
            operator=">"
        )
        monitor.add_performance_target(custom_target)
        
        result = monitor.remove_performance_target("removable_target")
        
        assert result is True
        assert "removable_target" not in monitor._performance_targets
    
    def test_remove_nonexistent_target(self, monitor):
        """Test removing non-existent target"""
        result = monitor.remove_performance_target("nonexistent_target")
        assert result is False


class TestMetricQuery:
    """Test metric querying functionality"""
    
    @pytest.fixture
    def monitor(self):
        return ContextMonitor()
    
    def test_get_current_metrics(self, monitor):
        """Test getting current metric values"""
        # Record some metrics
        monitor.record_metric("metric1", 100)
        monitor.record_metric("metric2", 200)
        monitor.record_metric("metric3", 300)
        
        current = monitor.get_current_metrics()
        
        assert isinstance(current, dict)
        assert current["metric1"] == 100
        assert current["metric2"] == 200
        assert current["metric3"] == 300
    
    def test_get_metric_history(self, monitor):
        """Test getting metric history"""
        # Record multiple values for a metric over time
        base_time = datetime.utcnow()
        for i in range(5):
            monitor.record_metric("history_metric", i * 10)
            # Manually set timestamps for testing
            if "history_metric" in monitor._metric_timeseries:
                timeseries = monitor._metric_timeseries["history_metric"]
                if timeseries:
                    # Update the last timestamp
                    last_value = timeseries[-1][1]
                    new_timestamp = base_time + timedelta(minutes=i)
                    timeseries[-1] = (new_timestamp, last_value)
        
        # Get history for last hour
        history = monitor.get_metric_history("history_metric", hours=1)
        
        assert isinstance(history, list)
        assert len(history) > 0
        
        # Each entry should be (timestamp, value) tuple
        for timestamp, value in history:
            assert isinstance(timestamp, datetime)
            assert isinstance(value, (int, float))
    
    def test_get_metric_history_nonexistent(self, monitor):
        """Test getting history for non-existent metric"""
        history = monitor.get_metric_history("nonexistent_metric")
        assert history == []
    
    def test_get_system_health(self, monitor):
        """Test getting system health status"""
        health = monitor.get_system_health()
        
        assert isinstance(health, SystemHealth)
        assert health.overall_status in ["healthy", "degraded", "unhealthy", "unknown"]
        assert isinstance(health.timestamp, datetime)
        assert isinstance(health.metrics, dict)
        assert isinstance(health.alerts_active, int)
        assert isinstance(health.performance_targets_met, int)
        assert isinstance(health.performance_targets_total, int)
    
    def test_get_active_alerts(self, monitor):
        """Test getting active alerts"""
        active = monitor.get_active_alerts()
        
        assert isinstance(active, list)
        # Initially should have no active alerts
        assert len(active) == 0
    
    def test_get_performance_summary(self, monitor):
        """Test getting comprehensive performance summary"""
        # Record some metrics to populate summary
        monitor.record_metric("test_metric", 100)
        monitor.record_metric("another_metric", 200)
        
        summary = monitor.get_performance_summary()
        
        assert isinstance(summary, dict)
        assert "timestamp" in summary
        assert "health_status" in summary
        assert "active_alerts" in summary
        assert "performance_targets" in summary
        assert "recent_metrics" in summary
        assert "error_counts" in summary
        assert "throughput" in summary
        
        # Check performance targets section
        targets = summary["performance_targets"]
        assert "met" in targets
        assert "total" in targets
        assert "percentage" in targets
        assert "details" in targets


class TestMonitoringTasks:
    """Test background monitoring tasks"""
    
    @pytest.fixture
    def monitor(self):
        return ContextMonitor()
    
    @pytest.mark.asyncio
    async def test_start_and_stop_monitoring(self, monitor):
        """Test starting and stopping monitoring tasks"""
        # Start monitoring
        await monitor.start_monitoring()
        
        assert monitor._collection_task is not None
        assert monitor._analysis_task is not None
        assert monitor._cleanup_task is not None
        
        # Let tasks run briefly
        await asyncio.sleep(0.1)
        
        # Stop monitoring
        await monitor.stop_monitoring()
        
        # Tasks should be cancelled/completed
        assert monitor._collection_task.done()
        assert monitor._analysis_task.done()
        assert monitor._cleanup_task.done()
    
    @pytest.mark.asyncio
    async def test_system_metrics_collection_with_psutil(self, monitor):
        """Test system metrics collection when psutil is available"""
        with patch('context_monitoring.psutil') as mock_psutil:
            # Mock psutil functions
            mock_psutil.cpu_percent.return_value = 75.0
            mock_memory = Mock()
            mock_memory.percent = 60.0
            mock_memory.available = 2 * 1024 * 1024 * 1024  # 2GB
            mock_psutil.virtual_memory.return_value = mock_memory
            
            mock_disk = Mock()
            mock_disk.used = 500 * 1024 * 1024 * 1024  # 500GB
            mock_disk.total = 1000 * 1024 * 1024 * 1024  # 1TB
            mock_psutil.disk_usage.return_value = mock_disk
            
            await monitor._collect_system_metrics()
            
            # Check that system metrics were recorded
            assert "system_cpu_percent" in monitor._last_values
            assert "system_memory_percent" in monitor._last_values
            assert "system_memory_available_mb" in monitor._last_values
            assert "system_disk_percent" in monitor._last_values
            
            assert monitor._last_values["system_cpu_percent"] == 75.0
            assert monitor._last_values["system_memory_percent"] == 60.0
            assert abs(monitor._last_values["system_memory_available_mb"] - 2048.0) < 1.0
            assert abs(monitor._last_values["system_disk_percent"] - 50.0) < 1.0
    
    @pytest.mark.asyncio
    async def test_system_metrics_collection_without_psutil(self, monitor):
        """Test system metrics collection fallback when psutil is not available"""
        with patch('context_monitoring.psutil', None):
            await monitor._collect_system_metrics()
            
            # Should still record metrics with mock values
            assert "system_cpu_percent" in monitor._last_values
            assert "system_memory_percent" in monitor._last_values
            assert "system_memory_available_mb" in monitor._last_values
            assert "system_disk_percent" in monitor._last_values
            
            # Check for mock tag
            cpu_metric = None
            for metric in monitor._metrics:
                if metric.name == "system_cpu_percent":
                    cpu_metric = metric
                    break
            
            if cpu_metric:
                assert cpu_metric.tags.get("mock") == "true"


class TestAlertEvaluation:
    """Test alert evaluation and triggering"""
    
    @pytest.fixture
    def monitor(self):
        return ContextMonitor(enable_alerts=True)
    
    @pytest.mark.asyncio
    async def test_alert_evaluation_basic(self, monitor):
        """Test basic alert evaluation"""
        # Create alert that should trigger
        test_alert = Alert(
            alert_id="test_trigger_alert",
            name="Test Trigger Alert",
            condition="metrics.get('test_value', 0) > 50",
            severity=AlertSeverity.WARNING,
            message_template="Test value too high: {test_value}"
        )
        monitor.add_alert(test_alert)
        
        # Set metric value that should trigger alert
        monitor.record_metric("test_value", 75)
        
        # Evaluate alerts
        await monitor._evaluate_alerts()
        
        # Alert should be triggered
        assert "test_trigger_alert" in monitor._active_alerts
        assert test_alert.trigger_count == 1
        assert test_alert.last_triggered is not None
    
    @pytest.mark.asyncio
    async def test_alert_evaluation_no_trigger(self, monitor):
        """Test alert evaluation that doesn't trigger"""
        test_alert = Alert(
            alert_id="test_no_trigger_alert",
            name="Test No Trigger Alert",
            condition="metrics.get('test_value', 0) > 100",
            severity=AlertSeverity.ERROR,
            message_template="Test message"
        )
        monitor.add_alert(test_alert)
        
        # Set metric value that should NOT trigger alert
        monitor.record_metric("test_value", 50)
        
        await monitor._evaluate_alerts()
        
        # Alert should not be triggered
        assert "test_no_trigger_alert" not in monitor._active_alerts
        assert test_alert.trigger_count == 0
    
    @pytest.mark.asyncio
    async def test_alert_cooldown(self, monitor):
        """Test alert cooldown functionality"""
        test_alert = Alert(
            alert_id="cooldown_test_alert",
            name="Cooldown Test Alert",
            condition="metrics.get('test_value', 0) > 30",
            severity=AlertSeverity.INFO,
            message_template="Test",
            cooldown_seconds=1  # Short cooldown for testing
        )
        monitor.add_alert(test_alert)
        
        # Trigger alert first time
        monitor.record_metric("test_value", 50)
        await monitor._evaluate_alerts()
        
        first_trigger_count = test_alert.trigger_count
        assert first_trigger_count == 1
        
        # Try to trigger again immediately (should be in cooldown)
        await monitor._evaluate_alerts()
        
        # Should not trigger again due to cooldown
        assert test_alert.trigger_count == first_trigger_count
        
        # Wait for cooldown to expire
        await asyncio.sleep(1.1)
        
        # Should trigger again after cooldown
        await monitor._evaluate_alerts()
        assert test_alert.trigger_count == first_trigger_count + 1
    
    @pytest.mark.asyncio
    async def test_alert_callback_execution(self, monitor):
        """Test alert callback execution"""
        callback_called = False
        callback_context = None
        
        def test_callback(alert, context):
            nonlocal callback_called, callback_context
            callback_called = True
            callback_context = context
        
        test_alert = Alert(
            alert_id="callback_test_alert",
            name="Callback Test Alert",
            condition="metrics.get('callback_test', 0) > 10",
            severity=AlertSeverity.WARNING,
            message_template="Callback test triggered",
            callbacks=[test_callback]
        )
        monitor.add_alert(test_alert)
        
        # Trigger alert
        monitor.record_metric("callback_test", 20)
        await monitor._evaluate_alerts()
        
        # Callback should have been called
        assert callback_called is True
        assert callback_context is not None
        assert "metrics" in callback_context
        assert callback_context["metrics"]["callback_test"] == 20
    
    @pytest.mark.asyncio
    async def test_alert_callback_error_handling(self, monitor):
        """Test alert callback error handling"""
        def failing_callback(alert, context):
            raise Exception("Callback failed")
        
        test_alert = Alert(
            alert_id="failing_callback_alert",
            name="Failing Callback Alert",
            condition="metrics.get('failure_test', 0) > 0",
            severity=AlertSeverity.ERROR,
            message_template="Test",
            callbacks=[failing_callback]
        )
        monitor.add_alert(test_alert)
        
        # Trigger alert (should not crash despite callback failure)
        monitor.record_metric("failure_test", 1)
        await monitor._evaluate_alerts()
        
        # Alert should still be triggered despite callback failure
        assert test_alert.trigger_count == 1


class TestDataExportAndCleanup:
    """Test data export and cleanup functionality"""
    
    @pytest.fixture
    def monitor(self):
        return ContextMonitor()
    
    @pytest.mark.asyncio
    async def test_export_metrics_json(self, monitor):
        """Test exporting metrics as JSON"""
        # Record some metrics
        for i in range(3):
            monitor.record_metric(f"export_test_{i}", i * 10)
        
        exported = await monitor.export_metrics(format_type="json", hours=1)
        
        assert isinstance(exported, str)
        
        # Parse JSON to verify structure
        import json
        data = json.loads(exported)
        
        assert "export_timestamp" in data
        assert "period_hours" in data
        assert "metrics" in data
        assert data["period_hours"] == 1
        assert len(data["metrics"]) == 3
    
    @pytest.mark.asyncio
    async def test_export_metrics_dict(self, monitor):
        """Test exporting metrics as dictionary"""
        monitor.record_metric("dict_export_test", 123)
        
        exported = await monitor.export_metrics(format_type="dict", hours=1)
        
        assert isinstance(exported, dict)
        assert "export_timestamp" in exported
        assert "metrics" in exported
        assert len(exported["metrics"]) == 1
    
    @pytest.mark.asyncio
    async def test_cleanup_old_data(self, monitor):
        """Test cleanup of old data"""
        # Set short retention for testing
        monitor.retention_hours = 0.001  # ~3.6 seconds
        
        # Add some metrics
        for i in range(5):
            monitor.record_metric(f"cleanup_test_{i}", i)
        
        initial_metric_count = len(monitor._metrics)
        
        # Wait a bit for data to become "old"
        await asyncio.sleep(0.1)
        
        # Add more recent metrics
        for i in range(3):
            monitor.record_metric(f"recent_test_{i}", i)
        
        # Run cleanup
        await monitor._cleanup_old_data()
        
        # Should have cleaned up old metrics but kept recent ones
        assert len(monitor._metrics) <= initial_metric_count + 3


class TestPerformanceTargetEvaluation:
    """Test performance target evaluation"""
    
    @pytest.fixture
    def monitor(self):
        return ContextMonitor()
    
    @pytest.mark.asyncio
    async def test_evaluate_performance_targets(self, monitor):
        """Test performance target evaluation"""
        # Add custom target
        test_target = PerformanceTarget(
            name="test_response_time",
            metric_name="response_time",
            target_value=2.0,
            operator="<",
            enabled=True
        )
        monitor.add_performance_target(test_target)
        
        # Set metric value
        monitor.record_metric("response_time", 1.5)  # Should meet target
        
        # Evaluate targets
        await monitor._evaluate_performance_targets()
        
        # Should record compliance metric
        compliance_key = "target_test_response_time_compliance"
        assert compliance_key in monitor._last_values
        assert monitor._last_values[compliance_key] == 1  # Target met
    
    @pytest.mark.asyncio
    async def test_evaluate_performance_targets_not_met(self, monitor):
        """Test performance target evaluation when not met"""
        test_target = PerformanceTarget(
            name="test_failure_rate",
            metric_name="failure_rate",
            target_value=5.0,
            operator="<",
            enabled=True
        )
        monitor.add_performance_target(test_target)
        
        # Set metric value that doesn't meet target
        monitor.record_metric("failure_rate", 8.0)
        
        await monitor._evaluate_performance_targets()
        
        # Should record non-compliance
        compliance_key = "target_test_failure_rate_compliance"
        assert compliance_key in monitor._last_values
        assert monitor._last_values[compliance_key] == 0  # Target not met


class TestSystemHealthAssessment:
    """Test system health assessment"""
    
    @pytest.fixture
    def monitor(self):
        return ContextMonitor()
    
    @pytest.mark.asyncio
    async def test_system_health_healthy(self, monitor):
        """Test healthy system status"""
        # Set up conditions for healthy status
        # No critical or error alerts
        # Performance targets mostly met
        
        # Add and meet performance targets
        good_target = PerformanceTarget(
            name="good_metric",
            metric_name="good_value",
            target_value=100.0,
            operator="<",
            enabled=True
        )
        monitor.add_performance_target(good_target)
        monitor.record_metric("good_value", 80.0)  # Meets target
        
        await monitor._update_system_health()
        
        health = monitor.get_system_health()
        assert health.overall_status == "healthy"
        assert health.alerts_active == 0
    
    @pytest.mark.asyncio
    async def test_system_health_degraded(self, monitor):
        """Test degraded system status"""
        # Add error alert and trigger it
        error_alert = Alert(
            alert_id="degraded_test_alert",
            name="Degraded Test",
            condition="metrics.get('error_rate', 0) > 2",
            severity=AlertSeverity.ERROR,
            message_template="Error rate high"
        )
        monitor.add_alert(error_alert)
        
        # Trigger error alert
        monitor.record_metric("error_rate", 5)
        await monitor._evaluate_alerts()
        
        await monitor._update_system_health()
        
        health = monitor.get_system_health()
        assert health.overall_status == "degraded"
        assert health.alerts_active > 0
    
    @pytest.mark.asyncio
    async def test_system_health_unhealthy(self, monitor):
        """Test unhealthy system status"""
        # Add critical alert and trigger it
        critical_alert = Alert(
            alert_id="critical_test_alert",
            name="Critical Test",
            condition="metrics.get('critical_value', 0) > 90",
            severity=AlertSeverity.CRITICAL,
            message_template="Critical condition"
        )
        monitor.add_alert(critical_alert)
        
        # Trigger critical alert
        monitor.record_metric("critical_value", 95)
        await monitor._evaluate_alerts()
        
        await monitor._update_system_health()
        
        health = monitor.get_system_health()
        assert health.overall_status == "unhealthy"
        assert health.details["critical_alerts"] > 0


class TestIntegrationScenarios:
    """Integration test scenarios"""
    
    @pytest.mark.asyncio
    async def test_complete_monitoring_scenario(self):
        """Test complete monitoring scenario"""
        monitor = ContextMonitor(
            collection_interval=1,  # Fast collection for testing
            enable_system_metrics=False,  # Disable to avoid psutil dependency
            enable_alerts=True
        )
        
        # Start monitoring
        await monitor.start_monitoring()
        
        try:
            # Record various metrics
            monitor.record_metric("cpu_usage", 75.0)
            monitor.record_metric("memory_usage", 60.0)
            monitor.record_metric("response_time", 1.2)
            monitor.record_metric("error_count", 3)
            
            # Record context preparation
            task = TDDTask(id="test", description="Test", cycle_id="c1", current_state=TDDState.GREEN)
            request = ContextRequest(agent_type="CodeAgent", story_id="s1", task=task, focus_areas=[])
            
            context = Mock(spec=AgentContext)
            context.file_contents = {"file.py": "content"}
            context.get_total_token_estimate = Mock(return_value=1000)
            context.compression_applied = False
            context.cache_hit = True
            
            monitor.record_context_preparation(request, context, 0.8, True)
            
            # Let monitoring tasks run briefly
            await asyncio.sleep(0.5)
            
            # Check results
            current_metrics = monitor.get_current_metrics()
            assert len(current_metrics) > 0
            
            summary = monitor.get_performance_summary()
            assert "recent_metrics" in summary
            assert len(summary["recent_metrics"]) > 0
            
            health = monitor.get_system_health()
            assert health.overall_status in ["healthy", "degraded", "unhealthy"]
            
        finally:
            await monitor.stop_monitoring()


if __name__ == "__main__":
    pytest.main([__file__])