"""
Multi-Project Monitoring and Observability System

Comprehensive monitoring, alerting, and observability for multiple AI-assisted
development projects with real-time dashboards, metrics collection, and analytics.
"""

import asyncio
import logging
import time
import json
import statistics
from typing import Dict, List, Optional, Any, Set, Tuple, Callable
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from collections import defaultdict, deque

# Try to import optional dependencies
try:
    import websockets
    WEBSOCKETS_AVAILABLE = True
except ImportError:
    WEBSOCKETS_AVAILABLE = False

try:
    import aiohttp
    AIOHTTP_AVAILABLE = True
except ImportError:
    AIOHTTP_AVAILABLE = False

# Try to import optional dependencies
try:
    import prometheus_client
    PROMETHEUS_AVAILABLE = True
except ImportError:
    PROMETHEUS_AVAILABLE = False

try:
    import grafana_api
    GRAFANA_AVAILABLE = True
except ImportError:
    GRAFANA_AVAILABLE = False

logger = logging.getLogger(__name__)


class MetricType(Enum):
    """Types of metrics to collect"""
    COUNTER = "counter"       # Monotonically increasing
    GAUGE = "gauge"          # Point-in-time value
    HISTOGRAM = "histogram"   # Distribution of values
    SUMMARY = "summary"      # Statistical summary


class AlertSeverity(Enum):
    """Alert severity levels"""
    CRITICAL = "critical"    # Immediate attention required
    HIGH = "high"           # Important but not critical
    MEDIUM = "medium"       # Moderate importance
    LOW = "low"            # Informational
    INFO = "info"          # General information


class AlertStatus(Enum):
    """Alert status"""
    FIRING = "firing"        # Alert is active
    RESOLVED = "resolved"    # Alert has been resolved
    ACKNOWLEDGED = "acknowledged"  # Alert has been acknowledged
    SILENCED = "silenced"    # Alert has been silenced


@dataclass
class Metric:
    """A metric data point"""
    name: str
    value: float
    metric_type: MetricType
    labels: Dict[str, str] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.utcnow)
    description: str = ""
    unit: str = ""


@dataclass
class Alert:
    """An alert triggered by monitoring conditions"""
    alert_id: str
    name: str
    description: str
    severity: AlertSeverity
    status: AlertStatus = AlertStatus.FIRING
    
    # Source information
    project_name: Optional[str] = None
    metric_name: Optional[str] = None
    threshold_value: Optional[float] = None
    current_value: Optional[float] = None
    
    # Timing
    triggered_at: datetime = field(default_factory=datetime.utcnow)
    resolved_at: Optional[datetime] = None
    acknowledged_at: Optional[datetime] = None
    
    # Notification tracking
    notifications_sent: List[str] = field(default_factory=list)
    escalation_level: int = 0
    
    # Additional context
    labels: Dict[str, str] = field(default_factory=dict)
    annotations: Dict[str, str] = field(default_factory=dict)
    runbook_url: Optional[str] = None


@dataclass
class Dashboard:
    """Dashboard configuration"""
    dashboard_id: str
    name: str
    description: str
    panels: List[Dict[str, Any]] = field(default_factory=list)
    refresh_interval: int = 30  # seconds
    time_range: str = "1h"  # 1h, 6h, 24h, 7d, etc.
    tags: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class MonitoringTarget:
    """A target to monitor (project, service, etc.)"""
    target_id: str
    target_type: str  # "project", "service", "agent", "resource"
    name: str
    endpoint: Optional[str] = None
    health_check_interval: int = 60  # seconds
    metrics_to_collect: List[str] = field(default_factory=list)
    alert_rules: List[Dict[str, Any]] = field(default_factory=list)
    labels: Dict[str, str] = field(default_factory=dict)
    enabled: bool = True


class MultiProjectMonitoring:
    """
    Comprehensive monitoring and observability system for multi-project orchestration.
    
    Provides real-time metrics collection, alerting, dashboards, and analytics
    across multiple AI-assisted development projects.
    """
    
    def __init__(
        self,
        storage_path: str = ".orch-global/monitoring",
        enable_prometheus: bool = True,
        enable_grafana: bool = False,
        websocket_port: int = 8765
    ):
        """
        Initialize multi-project monitoring system.
        
        Args:
            storage_path: Path to store monitoring data
            enable_prometheus: Whether to enable Prometheus metrics
            enable_grafana: Whether to enable Grafana integration
            websocket_port: Port for WebSocket real-time updates
        """
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        self.enable_prometheus = enable_prometheus and PROMETHEUS_AVAILABLE
        self.enable_grafana = enable_grafana and GRAFANA_AVAILABLE
        self.websocket_port = websocket_port
        
        # Monitoring state
        self.targets: Dict[str, MonitoringTarget] = {}
        self.metrics: Dict[str, deque] = defaultdict(lambda: deque(maxlen=1000))  # Store last 1000 points
        self.alerts: Dict[str, Alert] = {}
        self.dashboards: Dict[str, Dashboard] = {}
        
        # Real-time clients
        self.websocket_clients: Set[websockets.WebSocketServerProtocol] = set()
        
        # Background tasks
        self._collection_task: Optional[asyncio.Task] = None
        self._alert_task: Optional[asyncio.Task] = None
        self._websocket_task: Optional[asyncio.Task] = None
        self._cleanup_task: Optional[asyncio.Task] = None
        
        # Prometheus integration
        if self.enable_prometheus:
            self._setup_prometheus_metrics()
        
        # Alert handlers
        self.alert_handlers: List[Callable[[Alert], None]] = []
        
        # Load existing configuration
        self._load_monitoring_config()
        
        logger.info("Multi-project monitoring system initialized")
    
    async def start(self) -> None:
        """Start the monitoring system"""
        # Start background tasks
        self._collection_task = asyncio.create_task(self._metrics_collection_loop())
        self._alert_task = asyncio.create_task(self._alert_evaluation_loop())
        self._cleanup_task = asyncio.create_task(self._cleanup_loop())
        
        # Start WebSocket server for real-time updates
        if self.websocket_port and WEBSOCKETS_AVAILABLE:
            self._websocket_task = asyncio.create_task(self._start_websocket_server())
        elif self.websocket_port:
            logger.warning("WebSocket server requested but websockets library not available")
        
        logger.info("Multi-project monitoring system started")
    
    async def stop(self) -> None:
        """Stop the monitoring system"""
        # Cancel background tasks
        tasks = [self._collection_task, self._alert_task, self._websocket_task, self._cleanup_task]
        for task in tasks:
            if task:
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass
        
        # Close WebSocket connections
        if self.websocket_clients:
            await asyncio.gather(
                *[client.close() for client in self.websocket_clients],
                return_exceptions=True
            )
        
        # Save configuration
        self._save_monitoring_config()
        
        logger.info("Multi-project monitoring system stopped")
    
    def register_target(self, target: MonitoringTarget) -> bool:
        """
        Register a monitoring target.
        
        Args:
            target: Monitoring target to register
            
        Returns:
            True if registered successfully, False otherwise
        """
        if target.target_id in self.targets:
            logger.warning(f"Target '{target.target_id}' already registered")
            return False
        
        self.targets[target.target_id] = target
        
        # Setup default metrics for project targets
        if target.target_type == "project":
            self._setup_default_project_metrics(target)
        
        logger.info(f"Registered monitoring target: {target.name} ({target.target_type})")
        return True
    
    def unregister_target(self, target_id: str) -> bool:
        """
        Unregister a monitoring target.
        
        Args:
            target_id: ID of target to unregister
            
        Returns:
            True if unregistered successfully, False otherwise
        """
        if target_id not in self.targets:
            logger.warning(f"Target '{target_id}' not registered")
            return False
        
        del self.targets[target_id]
        
        # Clean up related metrics and alerts
        self._cleanup_target_data(target_id)
        
        logger.info(f"Unregistered monitoring target: {target_id}")
        return True
    
    def record_metric(self, metric: Metric) -> None:
        """
        Record a metric data point.
        
        Args:
            metric: Metric to record
        """
        metric_key = self._get_metric_key(metric)
        self.metrics[metric_key].append(metric)
        
        # Update Prometheus metrics if enabled
        if self.enable_prometheus:
            self._update_prometheus_metric(metric)
        
        # Send real-time update to WebSocket clients
        asyncio.create_task(self._send_metric_update(metric))
    
    def create_dashboard(self, dashboard: Dashboard) -> bool:
        """
        Create a monitoring dashboard.
        
        Args:
            dashboard: Dashboard configuration
            
        Returns:
            True if created successfully, False otherwise
        """
        if dashboard.dashboard_id in self.dashboards:
            logger.warning(f"Dashboard '{dashboard.dashboard_id}' already exists")
            return False
        
        self.dashboards[dashboard.dashboard_id] = dashboard
        
        logger.info(f"Created dashboard: {dashboard.name}")
        return True
    
    def add_alert_rule(self, target_id: str, alert_rule: Dict[str, Any]) -> bool:
        """
        Add an alert rule to a monitoring target.
        
        Args:
            target_id: ID of target to add rule to
            alert_rule: Alert rule configuration
            
        Returns:
            True if added successfully, False otherwise
        """
        if target_id not in self.targets:
            logger.error(f"Target '{target_id}' not found")
            return False
        
        target = self.targets[target_id]
        target.alert_rules.append(alert_rule)
        
        logger.info(f"Added alert rule to target {target_id}: {alert_rule.get('name', 'Unnamed')}")
        return True
    
    def get_metrics(
        self,
        metric_name: str,
        labels: Optional[Dict[str, str]] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> List[Metric]:
        """
        Get metrics matching criteria.
        
        Args:
            metric_name: Name of metric to retrieve
            labels: Label filters
            start_time: Start time for filtering
            end_time: End time for filtering
            
        Returns:
            List of matching metrics
        """
        matching_metrics = []
        
        for metric_key, metric_deque in self.metrics.items():
            for metric in metric_deque:
                # Check metric name
                if metric.name != metric_name:
                    continue
                
                # Check labels
                if labels:
                    if not all(metric.labels.get(k) == v for k, v in labels.items()):
                        continue
                
                # Check time range
                if start_time and metric.timestamp < start_time:
                    continue
                if end_time and metric.timestamp > end_time:
                    continue
                
                matching_metrics.append(metric)
        
        return sorted(matching_metrics, key=lambda m: m.timestamp)
    
    def get_active_alerts(self, severity: Optional[AlertSeverity] = None) -> List[Alert]:
        """
        Get active alerts.
        
        Args:
            severity: Filter by severity level
            
        Returns:
            List of active alerts
        """
        active_alerts = [
            alert for alert in self.alerts.values()
            if alert.status == AlertStatus.FIRING
        ]
        
        if severity:
            active_alerts = [a for a in active_alerts if a.severity == severity]
        
        return sorted(active_alerts, key=lambda a: a.triggered_at, reverse=True)
    
    def acknowledge_alert(self, alert_id: str, acknowledged_by: str = "") -> bool:
        """
        Acknowledge an alert.
        
        Args:
            alert_id: ID of alert to acknowledge
            acknowledged_by: Who acknowledged the alert
            
        Returns:
            True if acknowledged successfully, False otherwise
        """
        if alert_id not in self.alerts:
            return False
        
        alert = self.alerts[alert_id]
        alert.status = AlertStatus.ACKNOWLEDGED
        alert.acknowledged_at = datetime.utcnow()
        alert.annotations["acknowledged_by"] = acknowledged_by
        
        logger.info(f"Acknowledged alert: {alert.name}")
        return True
    
    def resolve_alert(self, alert_id: str) -> bool:
        """
        Resolve an alert.
        
        Args:
            alert_id: ID of alert to resolve
            
        Returns:
            True if resolved successfully, False otherwise
        """
        if alert_id not in self.alerts:
            return False
        
        alert = self.alerts[alert_id]
        alert.status = AlertStatus.RESOLVED
        alert.resolved_at = datetime.utcnow()
        
        logger.info(f"Resolved alert: {alert.name}")
        return True
    
    def get_monitoring_status(self) -> Dict[str, Any]:
        """Get comprehensive monitoring status"""
        active_targets = len([t for t in self.targets.values() if t.enabled])
        total_metrics = sum(len(deque) for deque in self.metrics.values())
        active_alerts = len(self.get_active_alerts())
        
        # Calculate system health score
        health_score = self._calculate_system_health_score()
        
        return {
            "monitoring_system": {
                "active_targets": active_targets,
                "total_targets": len(self.targets),
                "total_metrics": total_metrics,
                "active_alerts": active_alerts,
                "total_dashboards": len(self.dashboards),
                "health_score": health_score,
                "prometheus_enabled": self.enable_prometheus,
                "grafana_enabled": self.enable_grafana
            },
            "targets": {
                target_id: {
                    "name": target.name,
                    "type": target.target_type,
                    "enabled": target.enabled,
                    "metrics_count": len(target.metrics_to_collect),
                    "alert_rules": len(target.alert_rules)
                }
                for target_id, target in self.targets.items()
            },
            "alert_summary": {
                "critical": len([a for a in self.get_active_alerts() if a.severity == AlertSeverity.CRITICAL]),
                "high": len([a for a in self.get_active_alerts() if a.severity == AlertSeverity.HIGH]),
                "medium": len([a for a in self.get_active_alerts() if a.severity == AlertSeverity.MEDIUM]),
                "low": len([a for a in self.get_active_alerts() if a.severity == AlertSeverity.LOW])
            },
            "recent_metrics": self._get_recent_metrics_summary(),
            "websocket_clients": len(self.websocket_clients)
        }
    
    # Private methods
    
    def _setup_default_project_metrics(self, target: MonitoringTarget):
        """Setup default metrics for project targets"""
        default_metrics = [
            "project_cpu_usage",
            "project_memory_usage",
            "project_active_agents",
            "project_tdd_cycles_completed",
            "project_stories_in_progress",
            "project_error_rate",
            "project_build_time",
            "project_test_execution_time"
        ]
        
        target.metrics_to_collect.extend(default_metrics)
        
        # Add default alert rules
        default_alerts = [
            {
                "name": "High CPU Usage",
                "metric": "project_cpu_usage",
                "condition": "greater_than",
                "threshold": 80.0,
                "severity": "high",
                "duration": "5m"
            },
            {
                "name": "High Memory Usage",
                "metric": "project_memory_usage", 
                "condition": "greater_than",
                "threshold": 85.0,
                "severity": "high",
                "duration": "5m"
            },
            {
                "name": "High Error Rate",
                "metric": "project_error_rate",
                "condition": "greater_than",
                "threshold": 5.0,
                "severity": "critical",
                "duration": "2m"
            }
        ]
        
        target.alert_rules.extend(default_alerts)
    
    def _get_metric_key(self, metric: Metric) -> str:
        """Generate unique key for metric storage"""
        label_str = "_".join(f"{k}={v}" for k, v in sorted(metric.labels.items()))
        return f"{metric.name}_{label_str}" if label_str else metric.name
    
    def _setup_prometheus_metrics(self):
        """Setup Prometheus metrics collection"""
        if not PROMETHEUS_AVAILABLE:
            return
        
        # Create Prometheus metric instances
        self.prometheus_metrics = {
            "counter": prometheus_client.Counter,
            "gauge": prometheus_client.Gauge,
            "histogram": prometheus_client.Histogram,
            "summary": prometheus_client.Summary
        }
        
        # Registry for custom metrics
        self.prometheus_registry = prometheus_client.CollectorRegistry()
        
        logger.info("Prometheus metrics setup completed")
    
    def _update_prometheus_metric(self, metric: Metric):
        """Update Prometheus metric"""
        if not self.enable_prometheus:
            return
        
        # This would update the corresponding Prometheus metric
        # Implementation depends on specific Prometheus client setup
        pass
    
    async def _metrics_collection_loop(self):
        """Background metrics collection loop"""
        logger.info("Started metrics collection loop")
        
        while True:
            try:
                await self._collect_metrics_from_targets()
                await asyncio.sleep(30)  # Collect every 30 seconds
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Metrics collection error: {str(e)}")
                await asyncio.sleep(60)
    
    async def _alert_evaluation_loop(self):
        """Background alert evaluation loop"""
        logger.info("Started alert evaluation loop")
        
        while True:
            try:
                await self._evaluate_alert_rules()
                await asyncio.sleep(60)  # Evaluate every minute
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Alert evaluation error: {str(e)}")
                await asyncio.sleep(120)
    
    async def _cleanup_loop(self):
        """Background cleanup loop"""
        logger.info("Started cleanup loop")
        
        while True:
            try:
                await self._cleanup_old_data()
                await asyncio.sleep(3600)  # Cleanup every hour
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Cleanup error: {str(e)}")
    
    async def _start_websocket_server(self):
        """Start WebSocket server for real-time updates"""
        if not WEBSOCKETS_AVAILABLE:
            logger.warning("Cannot start WebSocket server - websockets library not available")
            return
        
        async def handle_client(websocket, path):
            self.websocket_clients.add(websocket)
            logger.info(f"New WebSocket client connected: {websocket.remote_address}")
            
            try:
                # Send initial monitoring status
                status = self.get_monitoring_status()
                await websocket.send(json.dumps({
                    "type": "status",
                    "data": status
                }))
                
                # Keep connection alive
                await websocket.wait_closed()
            except websockets.exceptions.ConnectionClosed:
                pass
            finally:
                self.websocket_clients.discard(websocket)
                logger.info(f"WebSocket client disconnected: {websocket.remote_address}")
        
        try:
            server = await websockets.serve(handle_client, "localhost", self.websocket_port)
            logger.info(f"WebSocket server started on port {self.websocket_port}")
            await server.wait_closed()
        except Exception as e:
            logger.error(f"WebSocket server error: {str(e)}")
    
    async def _collect_metrics_from_targets(self):
        """Collect metrics from all monitoring targets"""
        for target in self.targets.values():
            if not target.enabled:
                continue
            
            try:
                await self._collect_target_metrics(target)
            except Exception as e:
                logger.error(f"Failed to collect metrics from target {target.target_id}: {str(e)}")
    
    async def _collect_target_metrics(self, target: MonitoringTarget):
        """Collect metrics from a specific target"""
        # This would implement actual metrics collection
        # For now, generate some sample metrics for demonstration
        
        if target.target_type == "project":
            # Simulate project metrics
            base_labels = {"project": target.name, "target_id": target.target_id}
            
            metrics = [
                Metric("project_cpu_usage", 45.5, MetricType.GAUGE, base_labels, description="CPU usage percentage"),
                Metric("project_memory_usage", 67.2, MetricType.GAUGE, base_labels, description="Memory usage percentage"),
                Metric("project_active_agents", 3, MetricType.GAUGE, base_labels, description="Number of active agents"),
                Metric("project_tdd_cycles_completed", 1, MetricType.COUNTER, base_labels, description="TDD cycles completed"),
            ]
            
            for metric in metrics:
                self.record_metric(metric)
    
    async def _evaluate_alert_rules(self):
        """Evaluate alert rules for all targets"""
        for target in self.targets.values():
            if not target.enabled:
                continue
            
            for alert_rule in target.alert_rules:
                try:
                    await self._evaluate_single_alert_rule(target, alert_rule)
                except Exception as e:
                    logger.error(f"Failed to evaluate alert rule {alert_rule.get('name', 'unknown')}: {str(e)}")
    
    async def _evaluate_single_alert_rule(self, target: MonitoringTarget, alert_rule: Dict[str, Any]):
        """Evaluate a single alert rule"""
        metric_name = alert_rule.get("metric")
        condition = alert_rule.get("condition")
        threshold = alert_rule.get("threshold")
        severity = alert_rule.get("severity", "medium")
        
        if not all([metric_name, condition, threshold]):
            return
        
        # Get recent metrics for evaluation
        recent_metrics = self.get_metrics(
            metric_name,
            labels={"target_id": target.target_id},
            start_time=datetime.utcnow() - timedelta(minutes=10)
        )
        
        if not recent_metrics:
            return
        
        # Evaluate condition
        latest_metric = recent_metrics[-1]
        alert_triggered = False
        
        if condition == "greater_than" and latest_metric.value > threshold:
            alert_triggered = True
        elif condition == "less_than" and latest_metric.value < threshold:
            alert_triggered = True
        elif condition == "equals" and latest_metric.value == threshold:
            alert_triggered = True
        
        # Create or update alert
        alert_id = f"{target.target_id}_{alert_rule.get('name', 'unnamed').replace(' ', '_').lower()}"
        
        if alert_triggered:
            if alert_id not in self.alerts or self.alerts[alert_id].status == AlertStatus.RESOLVED:
                # Create new alert
                alert = Alert(
                    alert_id=alert_id,
                    name=alert_rule.get("name", "Unnamed Alert"),
                    description=f"{metric_name} is {condition} {threshold} (current: {latest_metric.value})",
                    severity=AlertSeverity(severity),
                    project_name=target.name,
                    metric_name=metric_name,
                    threshold_value=threshold,
                    current_value=latest_metric.value,
                    labels={"target_id": target.target_id}
                )
                
                self.alerts[alert_id] = alert
                await self._handle_new_alert(alert)
        else:
            # Check if we should resolve existing alert
            if alert_id in self.alerts and self.alerts[alert_id].status == AlertStatus.FIRING:
                self.resolve_alert(alert_id)
    
    async def _handle_new_alert(self, alert: Alert):
        """Handle a newly triggered alert"""
        logger.warning(f"Alert triggered: {alert.name} - {alert.description}")
        
        # Send notifications
        await self._send_alert_notifications(alert)
        
        # Send real-time update to WebSocket clients
        await self._send_alert_update(alert)
        
        # Call registered alert handlers
        for handler in self.alert_handlers:
            try:
                handler(alert)
            except Exception as e:
                logger.error(f"Alert handler error: {str(e)}")
    
    async def _send_alert_notifications(self, alert: Alert):
        """Send alert notifications"""
        # This would implement actual notification sending
        # (Discord, Slack, email, webhook, etc.)
        pass
    
    async def _send_metric_update(self, metric: Metric):
        """Send metric update to WebSocket clients"""
        if not self.websocket_clients:
            return
        
        update_message = json.dumps({
            "type": "metric_update",
            "data": {
                "name": metric.name,
                "value": metric.value,
                "labels": metric.labels,
                "timestamp": metric.timestamp.isoformat()
            }
        })
        
        # Send to all connected clients
        if WEBSOCKETS_AVAILABLE:
            disconnected_clients = set()
            for client in self.websocket_clients:
                try:
                    await client.send(update_message)
                except websockets.exceptions.ConnectionClosed:
                    disconnected_clients.add(client)
            
            # Remove disconnected clients
            self.websocket_clients -= disconnected_clients
    
    async def _send_alert_update(self, alert: Alert):
        """Send alert update to WebSocket clients"""
        if not self.websocket_clients:
            return
        
        update_message = json.dumps({
            "type": "alert_update",
            "data": {
                "alert_id": alert.alert_id,
                "name": alert.name,
                "description": alert.description,
                "severity": alert.severity.value,
                "status": alert.status.value,
                "project_name": alert.project_name,
                "triggered_at": alert.triggered_at.isoformat()
            }
        })
        
        # Send to all connected clients
        if WEBSOCKETS_AVAILABLE:
            disconnected_clients = set()
            for client in self.websocket_clients:
                try:
                    await client.send(update_message)
                except websockets.exceptions.ConnectionClosed:
                    disconnected_clients.add(client)
            
            # Remove disconnected clients
            self.websocket_clients -= disconnected_clients
    
    def _cleanup_target_data(self, target_id: str):
        """Clean up data related to a target"""
        # Remove metrics
        keys_to_remove = [key for key in self.metrics.keys() if target_id in key]
        for key in keys_to_remove:
            del self.metrics[key]
        
        # Remove alerts
        alerts_to_remove = [alert_id for alert_id, alert in self.alerts.items() if alert.labels.get("target_id") == target_id]
        for alert_id in alerts_to_remove:
            del self.alerts[alert_id]
    
    async def _cleanup_old_data(self):
        """Clean up old monitoring data"""
        cutoff_time = datetime.utcnow() - timedelta(hours=24)
        
        # Clean up old resolved alerts
        old_alerts = [
            alert_id for alert_id, alert in self.alerts.items()
            if alert.status == AlertStatus.RESOLVED and alert.resolved_at and alert.resolved_at < cutoff_time
        ]
        
        for alert_id in old_alerts:
            del self.alerts[alert_id]
        
        logger.debug(f"Cleaned up {len(old_alerts)} old alerts")
    
    def _calculate_system_health_score(self) -> float:
        """Calculate overall system health score (0.0 to 1.0)"""
        if not self.targets:
            return 1.0
        
        # Factor in alert severity
        active_alerts = self.get_active_alerts()
        alert_penalty = 0.0
        
        for alert in active_alerts:
            if alert.severity == AlertSeverity.CRITICAL:
                alert_penalty += 0.3
            elif alert.severity == AlertSeverity.HIGH:
                alert_penalty += 0.2
            elif alert.severity == AlertSeverity.MEDIUM:
                alert_penalty += 0.1
            else:
                alert_penalty += 0.05
        
        # Factor in target availability
        enabled_targets = len([t for t in self.targets.values() if t.enabled])
        availability_score = enabled_targets / len(self.targets) if self.targets else 1.0
        
        # Combine factors
        health_score = max(0.0, availability_score - alert_penalty)
        return min(1.0, health_score)
    
    def _get_recent_metrics_summary(self) -> Dict[str, Any]:
        """Get summary of recent metrics"""
        cutoff_time = datetime.utcnow() - timedelta(minutes=5)
        recent_count = 0
        
        for metric_deque in self.metrics.values():
            for metric in metric_deque:
                if metric.timestamp >= cutoff_time:
                    recent_count += 1
        
        return {
            "recent_metrics_count": recent_count,
            "total_metric_series": len(self.metrics),
            "collection_rate": recent_count / 5.0 if recent_count > 0 else 0.0  # metrics per minute
        }
    
    def _load_monitoring_config(self):
        """Load monitoring configuration from storage"""
        try:
            # Load targets
            targets_file = self.storage_path / "targets.json"
            if targets_file.exists():
                with open(targets_file, 'r') as f:
                    targets_data = json.load(f)
                    for target_id, target_dict in targets_data.items():
                        self.targets[target_id] = MonitoringTarget(**target_dict)
            
            # Load dashboards
            dashboards_file = self.storage_path / "dashboards.json"
            if dashboards_file.exists():
                with open(dashboards_file, 'r') as f:
                    dashboards_data = json.load(f)
                    for dashboard_id, dashboard_dict in dashboards_data.items():
                        if 'created_at' in dashboard_dict:
                            dashboard_dict['created_at'] = datetime.fromisoformat(dashboard_dict['created_at'])
                        self.dashboards[dashboard_id] = Dashboard(**dashboard_dict)
            
            logger.info(f"Loaded monitoring config: {len(self.targets)} targets, {len(self.dashboards)} dashboards")
            
        except Exception as e:
            logger.error(f"Failed to load monitoring config: {str(e)}")
    
    def _save_monitoring_config(self):
        """Save monitoring configuration to storage"""
        try:
            # Save targets
            targets_data = {}
            for target_id, target in self.targets.items():
                targets_data[target_id] = asdict(target)
            
            with open(self.storage_path / "targets.json", 'w') as f:
                json.dump(targets_data, f, indent=2)
            
            # Save dashboards
            dashboards_data = {}
            for dashboard_id, dashboard in self.dashboards.items():
                dashboard_dict = asdict(dashboard)
                dashboard_dict['created_at'] = dashboard.created_at.isoformat()
                dashboards_data[dashboard_id] = dashboard_dict
            
            with open(self.storage_path / "dashboards.json", 'w') as f:
                json.dump(dashboards_data, f, indent=2)
            
            logger.debug("Saved monitoring configuration")
            
        except Exception as e:
            logger.error(f"Failed to save monitoring config: {str(e)}")