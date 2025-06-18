"""
Unit tests for Multi-Project Monitoring System.

Tests comprehensive monitoring, alerting, and observability for multiple
AI-assisted development projects with metrics collection and analytics.
"""

import pytest
import asyncio
import tempfile
import shutil
import json
from pathlib import Path
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, AsyncMock, MagicMock
from collections import deque

import sys
sys.path.append(str(Path(__file__).parent.parent.parent))

from lib.multi_project_monitoring import (
    MultiProjectMonitoring, Metric, Alert, Dashboard, MonitoringTarget,
    MetricType, AlertSeverity, AlertStatus
)


class TestMetric:
    """Test the Metric dataclass."""
    
    def test_metric_creation(self):
        """Test creating a Metric instance."""
        timestamp = datetime.utcnow()
        labels = {"project": "test", "environment": "dev"}
        
        metric = Metric(
            name="cpu_usage",
            value=75.5,
            metric_type=MetricType.GAUGE,
            labels=labels,
            timestamp=timestamp,
            description="CPU usage percentage",
            unit="percent"
        )
        
        assert metric.name == "cpu_usage"
        assert metric.value == 75.5
        assert metric.metric_type == MetricType.GAUGE
        assert metric.labels == labels
        assert metric.timestamp == timestamp
        assert metric.description == "CPU usage percentage"
        assert metric.unit == "percent"

    def test_metric_defaults(self):
        """Test Metric with default values."""
        metric = Metric(
            name="request_count",
            value=100,
            metric_type=MetricType.COUNTER
        )
        
        assert metric.labels == {}
        assert isinstance(metric.timestamp, datetime)
        assert metric.description == ""
        assert metric.unit == ""


class TestAlert:
    """Test the Alert dataclass."""
    
    def test_alert_creation(self):
        """Test creating an Alert instance."""
        triggered_at = datetime.utcnow()
        resolved_at = triggered_at + timedelta(minutes=5)
        acknowledged_at = triggered_at + timedelta(minutes=2)
        
        alert = Alert(
            alert_id="alert-001",
            name="High CPU Usage",
            description="CPU usage exceeded 80%",
            severity=AlertSeverity.HIGH,
            status=AlertStatus.RESOLVED,
            project_name="test-project",
            metric_name="cpu_usage",
            threshold_value=80.0,
            current_value=85.5,
            triggered_at=triggered_at,
            resolved_at=resolved_at,
            acknowledged_at=acknowledged_at,
            notifications_sent=["email", "discord"],
            escalation_level=1,
            labels={"project": "test"},
            annotations={"runbook": "cpu-troubleshooting"},
            runbook_url="https://docs.example.com/runbooks/cpu"
        )
        
        assert alert.alert_id == "alert-001"
        assert alert.name == "High CPU Usage"
        assert alert.description == "CPU usage exceeded 80%"
        assert alert.severity == AlertSeverity.HIGH
        assert alert.status == AlertStatus.RESOLVED
        assert alert.project_name == "test-project"
        assert alert.metric_name == "cpu_usage"
        assert alert.threshold_value == 80.0
        assert alert.current_value == 85.5
        assert alert.triggered_at == triggered_at
        assert alert.resolved_at == resolved_at
        assert alert.acknowledged_at == acknowledged_at
        assert alert.notifications_sent == ["email", "discord"]
        assert alert.escalation_level == 1
        assert alert.labels == {"project": "test"}
        assert alert.annotations == {"runbook": "cpu-troubleshooting"}
        assert alert.runbook_url == "https://docs.example.com/runbooks/cpu"

    def test_alert_defaults(self):
        """Test Alert with default values."""
        alert = Alert(
            alert_id="alert-002",
            name="Memory Alert",
            description="Memory usage alert",
            severity=AlertSeverity.MEDIUM
        )
        
        assert alert.status == AlertStatus.FIRING
        assert alert.project_name is None
        assert alert.metric_name is None
        assert alert.threshold_value is None
        assert alert.current_value is None
        assert isinstance(alert.triggered_at, datetime)
        assert alert.resolved_at is None
        assert alert.acknowledged_at is None
        assert alert.notifications_sent == []
        assert alert.escalation_level == 0
        assert alert.labels == {}
        assert alert.annotations == {}
        assert alert.runbook_url is None


class TestDashboard:
    """Test the Dashboard dataclass."""
    
    def test_dashboard_creation(self):
        """Test creating a Dashboard instance."""
        created_at = datetime.utcnow()
        panels = [{"type": "graph", "title": "CPU Usage"}]
        tags = ["monitoring", "performance"]
        
        dashboard = Dashboard(
            dashboard_id="dash-001",
            name="System Metrics",
            description="System performance dashboard",
            panels=panels,
            refresh_interval=60,
            time_range="6h",
            tags=tags,
            created_at=created_at
        )
        
        assert dashboard.dashboard_id == "dash-001"
        assert dashboard.name == "System Metrics"
        assert dashboard.description == "System performance dashboard"
        assert dashboard.panels == panels
        assert dashboard.refresh_interval == 60
        assert dashboard.time_range == "6h"
        assert dashboard.tags == tags
        assert dashboard.created_at == created_at

    def test_dashboard_defaults(self):
        """Test Dashboard with default values."""
        dashboard = Dashboard(
            dashboard_id="dash-002",
            name="Basic Dashboard",
            description="Basic monitoring dashboard"
        )
        
        assert dashboard.panels == []
        assert dashboard.refresh_interval == 30
        assert dashboard.time_range == "1h"
        assert dashboard.tags == []
        assert isinstance(dashboard.created_at, datetime)


class TestMonitoringTarget:
    """Test the MonitoringTarget dataclass."""
    
    def test_monitoring_target_creation(self):
        """Test creating a MonitoringTarget instance."""
        metrics = ["cpu_usage", "memory_usage"]
        alert_rules = [{"name": "CPU Alert", "metric": "cpu_usage"}]
        labels = {"environment": "prod", "region": "us-east-1"}
        
        target = MonitoringTarget(
            target_id="target-001",
            target_type="project",
            name="Test Project",
            endpoint="http://localhost:8080",
            health_check_interval=30,
            metrics_to_collect=metrics,
            alert_rules=alert_rules,
            labels=labels,
            enabled=True
        )
        
        assert target.target_id == "target-001"
        assert target.target_type == "project"
        assert target.name == "Test Project"
        assert target.endpoint == "http://localhost:8080"
        assert target.health_check_interval == 30
        assert target.metrics_to_collect == metrics
        assert target.alert_rules == alert_rules
        assert target.labels == labels
        assert target.enabled is True

    def test_monitoring_target_defaults(self):
        """Test MonitoringTarget with default values."""
        target = MonitoringTarget(
            target_id="target-002",
            target_type="service",
            name="Test Service"
        )
        
        assert target.endpoint is None
        assert target.health_check_interval == 60
        assert target.metrics_to_collect == []
        assert target.alert_rules == []
        assert target.labels == {}
        assert target.enabled is True


@pytest.fixture
def temp_storage_dir():
    """Create a temporary storage directory."""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir)


@pytest.fixture
async def monitoring_system(temp_storage_dir):
    """Create a MultiProjectMonitoring instance for testing."""
    # Mock WebSocket availability
    with patch('lib.multi_project_monitoring.WEBSOCKETS_AVAILABLE', True), \
         patch('lib.multi_project_monitoring.PROMETHEUS_AVAILABLE', False), \
         patch('lib.multi_project_monitoring.GRAFANA_AVAILABLE', False):
        
        monitoring = MultiProjectMonitoring(
            storage_path=temp_storage_dir,
            enable_prometheus=False,
            enable_grafana=False,
            websocket_port=8765
        )
        
        yield monitoring
        
        # Clean up
        if hasattr(monitoring, '_collection_task') and monitoring._collection_task:
            monitoring._collection_task.cancel()
        if hasattr(monitoring, '_alert_task') and monitoring._alert_task:
            monitoring._alert_task.cancel()
        if hasattr(monitoring, '_websocket_task') and monitoring._websocket_task:
            monitoring._websocket_task.cancel()
        if hasattr(monitoring, '_cleanup_task') and monitoring._cleanup_task:
            monitoring._cleanup_task.cancel()


class TestMultiProjectMonitoring:
    """Test the MultiProjectMonitoring class."""
    
    def test_monitoring_initialization(self, temp_storage_dir):
        """Test MultiProjectMonitoring initialization."""
        monitoring = MultiProjectMonitoring(
            storage_path=temp_storage_dir,
            enable_prometheus=True,
            enable_grafana=True,
            websocket_port=9000
        )
        
        assert str(monitoring.storage_path) == temp_storage_dir
        assert monitoring.websocket_port == 9000
        assert monitoring.targets == {}
        assert isinstance(monitoring.metrics, dict)
        assert monitoring.alerts == {}
        assert monitoring.dashboards == {}
        assert monitoring.websocket_clients == set()

    def test_monitoring_initialization_defaults(self, temp_storage_dir):
        """Test MultiProjectMonitoring with default values."""
        with patch('lib.multi_project_monitoring.PROMETHEUS_AVAILABLE', False), \
             patch('lib.multi_project_monitoring.GRAFANA_AVAILABLE', False):
            
            monitoring = MultiProjectMonitoring(storage_path=temp_storage_dir)
            
            assert monitoring.enable_prometheus is False
            assert monitoring.enable_grafana is False
            assert monitoring.websocket_port == 8765

    @pytest.mark.asyncio
    async def test_start_and_stop(self, monitoring_system):
        """Test starting and stopping the monitoring system."""
        with patch.object(monitoring_system, '_start_websocket_server') as mock_ws:
            mock_ws.return_value = AsyncMock()
            
            await monitoring_system.start()
            
            # Check that background tasks are created
            assert monitoring_system._collection_task is not None
            assert monitoring_system._alert_task is not None
            assert monitoring_system._cleanup_task is not None
            
            await monitoring_system.stop()
            
            # Tasks should be cancelled
            assert monitoring_system._collection_task.cancelled()
            assert monitoring_system._alert_task.cancelled()
            assert monitoring_system._cleanup_task.cancelled()

    @pytest.mark.asyncio
    async def test_start_without_websockets(self, temp_storage_dir):
        """Test starting monitoring system without WebSocket support."""
        with patch('lib.multi_project_monitoring.WEBSOCKETS_AVAILABLE', False):
            monitoring = MultiProjectMonitoring(
                storage_path=temp_storage_dir,
                websocket_port=8765
            )
            
            await monitoring.start()
            
            # WebSocket task should not be created
            assert monitoring._websocket_task is None
            
            await monitoring.stop()

    def test_register_target_success(self, monitoring_system):
        """Test successfully registering a monitoring target."""
        target = MonitoringTarget(
            target_id="project-1",
            target_type="project",
            name="Test Project"
        )
        
        result = monitoring_system.register_target(target)
        
        assert result is True
        assert "project-1" in monitoring_system.targets
        assert monitoring_system.targets["project-1"] == target

    def test_register_target_duplicate(self, monitoring_system):
        """Test registering duplicate target."""
        target = MonitoringTarget(
            target_id="project-1",
            target_type="project",
            name="Test Project"
        )
        
        # Register once
        result1 = monitoring_system.register_target(target)
        assert result1 is True
        
        # Try to register again
        result2 = monitoring_system.register_target(target)
        assert result2 is False

    def test_register_project_target_default_setup(self, monitoring_system):
        """Test that project targets get default metrics and alerts."""
        target = MonitoringTarget(
            target_id="project-1",
            target_type="project",
            name="Test Project"
        )
        
        monitoring_system.register_target(target)
        
        registered_target = monitoring_system.targets["project-1"]
        
        # Should have default metrics
        assert "project_cpu_usage" in registered_target.metrics_to_collect
        assert "project_memory_usage" in registered_target.metrics_to_collect
        assert "project_active_agents" in registered_target.metrics_to_collect
        
        # Should have default alert rules
        assert len(registered_target.alert_rules) > 0
        alert_names = [rule["name"] for rule in registered_target.alert_rules]
        assert "High CPU Usage" in alert_names
        assert "High Memory Usage" in alert_names

    def test_unregister_target_success(self, monitoring_system):
        """Test successfully unregistering a target."""
        target = MonitoringTarget(
            target_id="project-1",
            target_type="project",
            name="Test Project"
        )
        
        monitoring_system.register_target(target)
        assert "project-1" in monitoring_system.targets
        
        result = monitoring_system.unregister_target("project-1")
        
        assert result is True
        assert "project-1" not in monitoring_system.targets

    def test_unregister_target_not_found(self, monitoring_system):
        """Test unregistering non-existent target."""
        result = monitoring_system.unregister_target("nonexistent")
        assert result is False

    def test_record_metric(self, monitoring_system):
        """Test recording a metric."""
        metric = Metric(
            name="cpu_usage",
            value=75.5,
            metric_type=MetricType.GAUGE,
            labels={"project": "test"}
        )
        
        monitoring_system.record_metric(metric)
        
        metric_key = monitoring_system._get_metric_key(metric)
        assert metric_key in monitoring_system.metrics
        assert len(monitoring_system.metrics[metric_key]) == 1
        assert monitoring_system.metrics[metric_key][0] == metric

    def test_record_multiple_metrics(self, monitoring_system):
        """Test recording multiple metrics."""
        for i in range(5):
            metric = Metric(
                name="cpu_usage",
                value=70.0 + i,
                metric_type=MetricType.GAUGE,
                labels={"project": "test"}
            )
            monitoring_system.record_metric(metric)
        
        metric_key = "cpu_usage_project=test"
        assert len(monitoring_system.metrics[metric_key]) == 5

    def test_get_metric_key(self, monitoring_system):
        """Test generating metric keys."""
        # Metric without labels
        metric1 = Metric("cpu_usage", 75.0, MetricType.GAUGE)
        key1 = monitoring_system._get_metric_key(metric1)
        assert key1 == "cpu_usage"
        
        # Metric with labels
        metric2 = Metric("cpu_usage", 75.0, MetricType.GAUGE, {"project": "test", "env": "prod"})
        key2 = monitoring_system._get_metric_key(metric2)
        assert key2 == "cpu_usage_env=prod_project=test"  # Sorted labels

    def test_create_dashboard_success(self, monitoring_system):
        """Test successfully creating a dashboard."""
        dashboard = Dashboard(
            dashboard_id="dash-1",
            name="Test Dashboard",
            description="Test dashboard description"
        )
        
        result = monitoring_system.create_dashboard(dashboard)
        
        assert result is True
        assert "dash-1" in monitoring_system.dashboards
        assert monitoring_system.dashboards["dash-1"] == dashboard

    def test_create_dashboard_duplicate(self, monitoring_system):
        """Test creating duplicate dashboard."""
        dashboard = Dashboard(
            dashboard_id="dash-1",
            name="Test Dashboard",
            description="Test dashboard description"
        )
        
        # Create once
        result1 = monitoring_system.create_dashboard(dashboard)
        assert result1 is True
        
        # Try to create again
        result2 = monitoring_system.create_dashboard(dashboard)
        assert result2 is False

    def test_add_alert_rule_success(self, monitoring_system):
        """Test successfully adding an alert rule."""
        target = MonitoringTarget(
            target_id="project-1",
            target_type="project",
            name="Test Project"
        )
        monitoring_system.register_target(target)
        
        alert_rule = {
            "name": "Custom Alert",
            "metric": "custom_metric",
            "condition": "greater_than",
            "threshold": 90.0
        }
        
        result = monitoring_system.add_alert_rule("project-1", alert_rule)
        
        assert result is True
        assert alert_rule in monitoring_system.targets["project-1"].alert_rules

    def test_add_alert_rule_target_not_found(self, monitoring_system):
        """Test adding alert rule to non-existent target."""
        alert_rule = {"name": "Test Alert"}
        
        result = monitoring_system.add_alert_rule("nonexistent", alert_rule)
        assert result is False

    def test_get_metrics_by_name(self, monitoring_system):
        """Test getting metrics by name."""
        # Add test metrics
        for i in range(3):
            metric = Metric(
                name="cpu_usage",
                value=70.0 + i,
                metric_type=MetricType.GAUGE,
                labels={"project": "test"}
            )
            monitoring_system.record_metric(metric)
        
        # Add different metric
        other_metric = Metric(
            name="memory_usage",
            value=80.0,
            metric_type=MetricType.GAUGE,
            labels={"project": "test"}
        )
        monitoring_system.record_metric(other_metric)
        
        # Get CPU metrics
        cpu_metrics = monitoring_system.get_metrics("cpu_usage")
        assert len(cpu_metrics) == 3
        
        # Get memory metrics
        memory_metrics = monitoring_system.get_metrics("memory_usage")
        assert len(memory_metrics) == 1

    def test_get_metrics_with_labels(self, monitoring_system):
        """Test getting metrics with label filtering."""
        # Add metrics with different labels
        metric1 = Metric("cpu_usage", 70.0, MetricType.GAUGE, {"project": "test1"})
        metric2 = Metric("cpu_usage", 80.0, MetricType.GAUGE, {"project": "test2"})
        metric3 = Metric("cpu_usage", 90.0, MetricType.GAUGE, {"project": "test1", "env": "prod"})
        
        monitoring_system.record_metric(metric1)
        monitoring_system.record_metric(metric2)
        monitoring_system.record_metric(metric3)
        
        # Filter by project
        test1_metrics = monitoring_system.get_metrics("cpu_usage", {"project": "test1"})
        assert len(test1_metrics) == 2
        
        # Filter by project and env
        prod_metrics = monitoring_system.get_metrics("cpu_usage", {"project": "test1", "env": "prod"})
        assert len(prod_metrics) == 1

    def test_get_metrics_with_time_range(self, monitoring_system):
        """Test getting metrics with time filtering."""
        now = datetime.utcnow()
        old_time = now - timedelta(hours=2)
        recent_time = now - timedelta(minutes=10)
        
        # Add metrics with different timestamps
        old_metric = Metric("cpu_usage", 70.0, MetricType.GAUGE, timestamp=old_time)
        recent_metric = Metric("cpu_usage", 80.0, MetricType.GAUGE, timestamp=recent_time)
        current_metric = Metric("cpu_usage", 90.0, MetricType.GAUGE, timestamp=now)
        
        monitoring_system.record_metric(old_metric)
        monitoring_system.record_metric(recent_metric)
        monitoring_system.record_metric(current_metric)
        
        # Get recent metrics only
        start_time = now - timedelta(hours=1)
        recent_metrics = monitoring_system.get_metrics("cpu_usage", start_time=start_time)
        assert len(recent_metrics) == 2  # recent_metric and current_metric
        
        # Get metrics in specific range
        end_time = now - timedelta(minutes=5)
        range_metrics = monitoring_system.get_metrics("cpu_usage", start_time=start_time, end_time=end_time)
        assert len(range_metrics) == 1  # only recent_metric

    def test_get_active_alerts(self, monitoring_system):
        """Test getting active alerts."""
        # Add alerts with different statuses
        alert1 = Alert("alert-1", "Alert 1", "Description", AlertSeverity.HIGH, AlertStatus.FIRING)
        alert2 = Alert("alert-2", "Alert 2", "Description", AlertSeverity.MEDIUM, AlertStatus.RESOLVED)
        alert3 = Alert("alert-3", "Alert 3", "Description", AlertSeverity.LOW, AlertStatus.FIRING)
        
        monitoring_system.alerts["alert-1"] = alert1
        monitoring_system.alerts["alert-2"] = alert2
        monitoring_system.alerts["alert-3"] = alert3
        
        # Get all active alerts
        active_alerts = monitoring_system.get_active_alerts()
        assert len(active_alerts) == 2  # alert1 and alert3
        
        # Get active alerts by severity
        high_alerts = monitoring_system.get_active_alerts(AlertSeverity.HIGH)
        assert len(high_alerts) == 1
        assert high_alerts[0].alert_id == "alert-1"

    def test_acknowledge_alert_success(self, monitoring_system):
        """Test successfully acknowledging an alert."""
        alert = Alert("alert-1", "Test Alert", "Description", AlertSeverity.MEDIUM)
        monitoring_system.alerts["alert-1"] = alert
        
        result = monitoring_system.acknowledge_alert("alert-1", "test_user")
        
        assert result is True
        assert alert.status == AlertStatus.ACKNOWLEDGED
        assert alert.acknowledged_at is not None
        assert alert.annotations["acknowledged_by"] == "test_user"

    def test_acknowledge_alert_not_found(self, monitoring_system):
        """Test acknowledging non-existent alert."""
        result = monitoring_system.acknowledge_alert("nonexistent")
        assert result is False

    def test_resolve_alert_success(self, monitoring_system):
        """Test successfully resolving an alert."""
        alert = Alert("alert-1", "Test Alert", "Description", AlertSeverity.MEDIUM)
        monitoring_system.alerts["alert-1"] = alert
        
        result = monitoring_system.resolve_alert("alert-1")
        
        assert result is True
        assert alert.status == AlertStatus.RESOLVED
        assert alert.resolved_at is not None

    def test_resolve_alert_not_found(self, monitoring_system):
        """Test resolving non-existent alert."""
        result = monitoring_system.resolve_alert("nonexistent")
        assert result is False

    def test_get_monitoring_status(self, monitoring_system):
        """Test getting comprehensive monitoring status."""
        # Add test data
        target = MonitoringTarget("target-1", "project", "Test Project", enabled=True)
        monitoring_system.register_target(target)
        
        metric = Metric("cpu_usage", 75.0, MetricType.GAUGE)
        monitoring_system.record_metric(metric)
        
        alert = Alert("alert-1", "Test Alert", "Description", AlertSeverity.HIGH)
        monitoring_system.alerts["alert-1"] = alert
        
        dashboard = Dashboard("dash-1", "Test Dashboard", "Description")
        monitoring_system.create_dashboard(dashboard)
        
        status = monitoring_system.get_monitoring_status()
        
        assert "monitoring_system" in status
        assert "targets" in status
        assert "alert_summary" in status
        assert "recent_metrics" in status
        assert "websocket_clients" in status
        
        system_status = status["monitoring_system"]
        assert system_status["active_targets"] == 1
        assert system_status["total_targets"] == 1
        assert system_status["active_alerts"] == 1
        assert system_status["total_dashboards"] == 1
        assert 0.0 <= system_status["health_score"] <= 1.0

    def test_calculate_system_health_score(self, monitoring_system):
        """Test calculating system health score."""
        # Test with no targets (should return 1.0)
        score = monitoring_system._calculate_system_health_score()
        assert score == 1.0
        
        # Add targets and alerts
        target = MonitoringTarget("target-1", "project", "Test Project")
        monitoring_system.register_target(target)
        
        # Add critical alert (should reduce score)
        critical_alert = Alert("alert-1", "Critical", "Description", AlertSeverity.CRITICAL)
        monitoring_system.alerts["alert-1"] = critical_alert
        
        score_with_critical = monitoring_system._calculate_system_health_score()
        assert score_with_critical < 1.0
        assert score_with_critical >= 0.0

    def test_get_recent_metrics_summary(self, monitoring_system):
        """Test getting recent metrics summary."""
        # Add metrics with different timestamps
        now = datetime.utcnow()
        old_metric = Metric("cpu_usage", 70.0, MetricType.GAUGE, timestamp=now - timedelta(minutes=10))
        recent_metric = Metric("cpu_usage", 80.0, MetricType.GAUGE, timestamp=now - timedelta(minutes=2))
        
        monitoring_system.record_metric(old_metric)
        monitoring_system.record_metric(recent_metric)
        
        summary = monitoring_system._get_recent_metrics_summary()
        
        assert "recent_metrics_count" in summary
        assert "total_metric_series" in summary
        assert "collection_rate" in summary
        assert summary["total_metric_series"] == 1  # Same metric key

    @pytest.mark.asyncio
    async def test_collect_target_metrics(self, monitoring_system):
        """Test collecting metrics from a target."""
        target = MonitoringTarget("project-1", "project", "Test Project")
        
        # Mock the record_metric method to track calls
        original_record = monitoring_system.record_metric
        recorded_metrics = []
        
        def mock_record(metric):
            recorded_metrics.append(metric)
            return original_record(metric)
        
        monitoring_system.record_metric = mock_record
        
        await monitoring_system._collect_target_metrics(target)
        
        # Should have recorded some project metrics
        assert len(recorded_metrics) > 0
        metric_names = [m.name for m in recorded_metrics]
        assert "project_cpu_usage" in metric_names
        assert "project_memory_usage" in metric_names

    @pytest.mark.asyncio
    async def test_evaluate_single_alert_rule_triggered(self, monitoring_system):
        """Test evaluating an alert rule that should trigger."""
        target = MonitoringTarget("project-1", "project", "Test Project")
        monitoring_system.register_target(target)
        
        # Add metric that exceeds threshold
        metric = Metric(
            "project_cpu_usage",
            85.0,  # Above threshold
            MetricType.GAUGE,
            {"target_id": "project-1"}
        )
        monitoring_system.record_metric(metric)
        
        alert_rule = {
            "name": "High CPU Usage",
            "metric": "project_cpu_usage",
            "condition": "greater_than",
            "threshold": 80.0,
            "severity": "high"
        }
        
        await monitoring_system._evaluate_single_alert_rule(target, alert_rule)
        
        # Should have created an alert
        alert_id = "project-1_high_cpu_usage"
        assert alert_id in monitoring_system.alerts
        alert = monitoring_system.alerts[alert_id]
        assert alert.severity == AlertSeverity.HIGH
        assert alert.current_value == 85.0

    @pytest.mark.asyncio
    async def test_evaluate_single_alert_rule_not_triggered(self, monitoring_system):
        """Test evaluating an alert rule that should not trigger."""
        target = MonitoringTarget("project-1", "project", "Test Project")
        monitoring_system.register_target(target)
        
        # Add metric that doesn't exceed threshold
        metric = Metric(
            "project_cpu_usage",
            75.0,  # Below threshold
            MetricType.GAUGE,
            {"target_id": "project-1"}
        )
        monitoring_system.record_metric(metric)
        
        alert_rule = {
            "name": "High CPU Usage",
            "metric": "project_cpu_usage",
            "condition": "greater_than",
            "threshold": 80.0,
            "severity": "high"
        }
        
        await monitoring_system._evaluate_single_alert_rule(target, alert_rule)
        
        # Should not have created an alert
        alert_id = "project-1_high_cpu_usage"
        assert alert_id not in monitoring_system.alerts

    @pytest.mark.asyncio
    async def test_evaluate_alert_rule_resolution(self, monitoring_system):
        """Test alert rule that resolves existing alert."""
        target = MonitoringTarget("project-1", "project", "Test Project")
        monitoring_system.register_target(target)
        
        # Create existing firing alert
        alert_id = "project-1_high_cpu_usage"
        alert = Alert(alert_id, "High CPU", "Description", AlertSeverity.HIGH, AlertStatus.FIRING)
        monitoring_system.alerts[alert_id] = alert
        
        # Add metric that's now below threshold
        metric = Metric(
            "project_cpu_usage",
            75.0,  # Below threshold
            MetricType.GAUGE,
            {"target_id": "project-1"}
        )
        monitoring_system.record_metric(metric)
        
        alert_rule = {
            "name": "High CPU Usage",
            "metric": "project_cpu_usage",
            "condition": "greater_than",
            "threshold": 80.0,
            "severity": "high"
        }
        
        await monitoring_system._evaluate_single_alert_rule(target, alert_rule)
        
        # Alert should be resolved
        assert alert.status == AlertStatus.RESOLVED

    @pytest.mark.asyncio
    async def test_evaluate_alert_rule_missing_data(self, monitoring_system):
        """Test evaluating alert rule with missing required data."""
        target = MonitoringTarget("project-1", "project", "Test Project")
        
        # Alert rule missing required fields
        alert_rule = {
            "name": "Incomplete Rule"
            # Missing metric, condition, threshold
        }
        
        # Should not raise exception
        await monitoring_system._evaluate_single_alert_rule(target, alert_rule)
        
        # Should not have created any alerts
        assert len(monitoring_system.alerts) == 0

    @pytest.mark.asyncio
    async def test_evaluate_alert_rule_no_metrics(self, monitoring_system):
        """Test evaluating alert rule when no metrics are available."""
        target = MonitoringTarget("project-1", "project", "Test Project")
        
        alert_rule = {
            "name": "CPU Alert",
            "metric": "nonexistent_metric",
            "condition": "greater_than",
            "threshold": 80.0,
            "severity": "high"
        }
        
        # Should not raise exception
        await monitoring_system._evaluate_single_alert_rule(target, alert_rule)
        
        # Should not have created any alerts
        assert len(monitoring_system.alerts) == 0

    @pytest.mark.asyncio
    async def test_handle_new_alert(self, monitoring_system):
        """Test handling a newly triggered alert."""
        alert = Alert("alert-1", "Test Alert", "Description", AlertSeverity.HIGH)
        
        with patch.object(monitoring_system, '_send_alert_notifications') as mock_notify, \
             patch.object(monitoring_system, '_send_alert_update') as mock_update:
            
            await monitoring_system._handle_new_alert(alert)
            
            mock_notify.assert_called_once_with(alert)
            mock_update.assert_called_once_with(alert)

    @pytest.mark.asyncio
    async def test_cleanup_old_data(self, monitoring_system):
        """Test cleaning up old monitoring data."""
        # Add old resolved alert
        old_time = datetime.utcnow() - timedelta(hours=25)
        old_alert = Alert("old-alert", "Old Alert", "Description", AlertSeverity.LOW, AlertStatus.RESOLVED)
        old_alert.resolved_at = old_time
        
        # Add recent resolved alert
        recent_time = datetime.utcnow() - timedelta(hours=1)
        recent_alert = Alert("recent-alert", "Recent Alert", "Description", AlertSeverity.LOW, AlertStatus.RESOLVED)
        recent_alert.resolved_at = recent_time
        
        monitoring_system.alerts["old-alert"] = old_alert
        monitoring_system.alerts["recent-alert"] = recent_alert
        
        await monitoring_system._cleanup_old_data()
        
        # Old alert should be cleaned up, recent should remain
        assert "old-alert" not in monitoring_system.alerts
        assert "recent-alert" in monitoring_system.alerts

    def test_cleanup_target_data(self, monitoring_system):
        """Test cleaning up data related to a target."""
        target_id = "project-1"
        
        # Add metrics with target label
        metric = Metric("cpu_usage", 75.0, MetricType.GAUGE, {"target_id": target_id})
        monitoring_system.record_metric(metric)
        
        # Add alert with target label
        alert = Alert("alert-1", "Test Alert", "Description", AlertSeverity.HIGH)
        alert.labels = {"target_id": target_id}
        monitoring_system.alerts["alert-1"] = alert
        
        monitoring_system._cleanup_target_data(target_id)
        
        # Data should be cleaned up
        metric_keys = [key for key in monitoring_system.metrics.keys() if target_id in key]
        assert len(metric_keys) == 0
        assert "alert-1" not in monitoring_system.alerts

    @pytest.mark.asyncio
    async def test_send_metric_update_no_clients(self, monitoring_system):
        """Test sending metric update with no WebSocket clients."""
        metric = Metric("cpu_usage", 75.0, MetricType.GAUGE)
        
        # Should not raise exception
        await monitoring_system._send_metric_update(metric)

    @pytest.mark.asyncio
    async def test_send_alert_update_no_clients(self, monitoring_system):
        """Test sending alert update with no WebSocket clients."""
        alert = Alert("alert-1", "Test Alert", "Description", AlertSeverity.HIGH)
        
        # Should not raise exception
        await monitoring_system._send_alert_update(alert)

    def test_load_monitoring_config_no_files(self, monitoring_system):
        """Test loading monitoring config when no config files exist."""
        # Should not raise exception
        monitoring_system._load_monitoring_config()
        
        # Should have empty configuration
        assert len(monitoring_system.targets) == 0
        assert len(monitoring_system.dashboards) == 0

    def test_save_and_load_monitoring_config(self, monitoring_system):
        """Test saving and loading monitoring configuration."""
        # Add test data
        target = MonitoringTarget("project-1", "project", "Test Project")
        monitoring_system.register_target(target)
        
        dashboard = Dashboard("dash-1", "Test Dashboard", "Description")
        monitoring_system.create_dashboard(dashboard)
        
        # Save configuration
        monitoring_system._save_monitoring_config()
        
        # Clear data and reload
        monitoring_system.targets.clear()
        monitoring_system.dashboards.clear()
        
        monitoring_system._load_monitoring_config()
        
        # Data should be restored
        assert "project-1" in monitoring_system.targets
        assert "dash-1" in monitoring_system.dashboards
        
        restored_target = monitoring_system.targets["project-1"]
        assert restored_target.target_id == "project-1"
        assert restored_target.name == "Test Project"

    @pytest.mark.asyncio
    async def test_monitoring_loops_exception_handling(self, monitoring_system):
        """Test that monitoring loops handle exceptions gracefully."""
        # Mock methods to raise exceptions
        with patch.object(monitoring_system, '_collect_metrics_from_targets', side_effect=Exception("Test error")):
            # Should not raise exception, just log and continue
            await monitoring_system._collect_metrics_from_targets()
        
        with patch.object(monitoring_system, '_evaluate_alert_rules', side_effect=Exception("Test error")):
            # Should not raise exception, just log and continue
            await monitoring_system._evaluate_alert_rules()
        
        with patch.object(monitoring_system, '_cleanup_old_data', side_effect=Exception("Test error")):
            # Should not raise exception, just log and continue
            await monitoring_system._cleanup_old_data()

    def test_setup_default_project_metrics(self, monitoring_system):
        """Test setting up default metrics for project targets."""
        target = MonitoringTarget("project-1", "project", "Test Project")
        
        # Clear existing metrics/alerts for clean test
        target.metrics_to_collect.clear()
        target.alert_rules.clear()
        
        monitoring_system._setup_default_project_metrics(target)
        
        # Should have default metrics
        expected_metrics = [
            "project_cpu_usage",
            "project_memory_usage",
            "project_active_agents",
            "project_tdd_cycles_completed",
            "project_stories_in_progress",
            "project_error_rate",
            "project_build_time",
            "project_test_execution_time"
        ]
        
        for metric in expected_metrics:
            assert metric in target.metrics_to_collect
        
        # Should have default alert rules
        assert len(target.alert_rules) > 0
        rule_names = [rule["name"] for rule in target.alert_rules]
        assert "High CPU Usage" in rule_names
        assert "High Memory Usage" in rule_names
        assert "High Error Rate" in rule_names

    def test_metric_deque_size_limit(self, monitoring_system):
        """Test that metric storage respects deque size limits."""
        # Add more metrics than the deque limit (1000)
        for i in range(1200):
            metric = Metric("test_metric", float(i), MetricType.COUNTER)
            monitoring_system.record_metric(metric)
        
        metric_key = "test_metric"
        metric_deque = monitoring_system.metrics[metric_key]
        
        # Should be limited to 1000 items
        assert len(metric_deque) == 1000
        
        # Should contain the most recent 1000 items
        assert metric_deque[0].value == 200.0  # First item should be value 200
        assert metric_deque[-1].value == 1199.0  # Last item should be value 1199