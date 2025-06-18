"""
Context Monitoring - Real-time Performance Monitoring and Alerting

Advanced monitoring system for context management operations with real-time metrics,
performance tracking, alerting, and comprehensive analytics.
"""

import asyncio
import logging
import time
import json

# Graceful fallback for psutil
try:
    import psutil
except ImportError:
    psutil = None
from typing import Dict, List, Optional, Any, Callable, Union, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, field, asdict
from enum import Enum
from collections import deque, defaultdict

try:
    from .context.models import AgentContext, ContextRequest, TDDState
    from .context.exceptions import ContextMonitoringError
except ImportError:
    from context.models import AgentContext, ContextRequest, TDDState
    from context.exceptions import ContextMonitoringError

logger = logging.getLogger(__name__)


class MetricType(Enum):
    """Types of metrics to track"""
    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    TIMER = "timer"


class AlertSeverity(Enum):
    """Alert severity levels"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class MonitoringInterval(Enum):
    """Monitoring interval settings"""
    REAL_TIME = 1
    FAST = 5
    MEDIUM = 30
    SLOW = 60
    HOURLY = 3600


@dataclass
class PerformanceMetric:
    """Single performance metric data point"""
    
    name: str
    value: Union[int, float]
    metric_type: MetricType
    timestamp: datetime
    tags: Dict[str, str] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            "name": self.name,
            "value": self.value,
            "type": self.metric_type.value,
            "timestamp": self.timestamp.isoformat(),
            "tags": self.tags,
            "metadata": self.metadata
        }


@dataclass
class Alert:
    """Alert configuration and state"""
    
    alert_id: str
    name: str
    condition: str  # Python expression to evaluate
    severity: AlertSeverity
    message_template: str
    enabled: bool = True
    cooldown_seconds: int = 300  # 5 minutes
    last_triggered: Optional[datetime] = None
    trigger_count: int = 0
    callbacks: List[Callable] = field(default_factory=list)
    
    def is_in_cooldown(self) -> bool:
        """Check if alert is in cooldown period"""
        if not self.last_triggered:
            return False
        return (datetime.utcnow() - self.last_triggered).total_seconds() < self.cooldown_seconds
    
    def format_message(self, context: Dict[str, Any]) -> str:
        """Format alert message with context variables"""
        try:
            return self.message_template.format(**context)
        except KeyError as e:
            return f"{self.message_template} (Missing context: {e})"


@dataclass
class PerformanceTarget:
    """Performance target configuration"""
    
    name: str
    metric_name: str
    target_value: float
    operator: str  # "<", "<=", ">", ">=", "=="
    tolerance_percent: float = 10.0  # Allowed deviation percentage
    enabled: bool = True
    
    def evaluate(self, current_value: float) -> bool:
        """Evaluate if current value meets the target"""
        if self.operator == "<":
            return current_value < self.target_value
        elif self.operator == "<=":
            return current_value <= self.target_value
        elif self.operator == ">":
            return current_value > self.target_value
        elif self.operator == ">=":
            return current_value >= self.target_value
        elif self.operator == "==":
            tolerance = self.target_value * (self.tolerance_percent / 100.0)
            return abs(current_value - self.target_value) <= tolerance
        return False
    
    def get_deviation_percent(self, current_value: float) -> float:
        """Calculate deviation percentage from target"""
        if self.target_value == 0:
            return float('inf') if current_value != 0 else 0.0
        return ((current_value - self.target_value) / self.target_value) * 100.0


@dataclass
class SystemHealth:
    """System health status"""
    
    overall_status: str  # "healthy", "degraded", "unhealthy"
    timestamp: datetime
    metrics: Dict[str, float]
    alerts_active: int
    performance_targets_met: int
    performance_targets_total: int
    details: Dict[str, Any] = field(default_factory=dict)


class ContextMonitor:
    """
    Advanced context monitoring system.
    
    Features:
    - Real-time performance metrics collection
    - Configurable alerts and notifications
    - Performance target tracking
    - System health monitoring
    - Historical data aggregation
    - Custom metric plugins
    """
    
    def __init__(
        self,
        collection_interval: int = 5,
        retention_hours: int = 24,
        enable_system_metrics: bool = True,
        enable_alerts: bool = True,
        metrics_buffer_size: int = 10000
    ):
        """
        Initialize context monitoring system.
        
        Args:
            collection_interval: Metrics collection interval in seconds
            retention_hours: How long to retain metrics data
            enable_system_metrics: Whether to collect system-level metrics
            enable_alerts: Whether to enable alerting
            metrics_buffer_size: Maximum metrics to keep in memory
        """
        self.collection_interval = collection_interval
        self.retention_hours = retention_hours
        self.enable_system_metrics = enable_system_metrics
        self.enable_alerts = enable_alerts
        self.metrics_buffer_size = metrics_buffer_size
        
        # Metrics storage
        self._metrics: deque[PerformanceMetric] = deque(maxlen=metrics_buffer_size)
        self._metric_timeseries: Dict[str, deque] = defaultdict(lambda: deque(maxlen=1000))
        self._last_values: Dict[str, float] = {}
        
        # Alerts and targets
        self._alerts: Dict[str, Alert] = {}
        self._performance_targets: Dict[str, PerformanceTarget] = {}
        self._active_alerts: Dict[str, Alert] = {}
        
        # Background tasks
        self._collection_task: Optional[asyncio.Task] = None
        self._analysis_task: Optional[asyncio.Task] = None
        self._cleanup_task: Optional[asyncio.Task] = None
        
        # Performance tracking
        self._operation_times: Dict[str, deque] = defaultdict(lambda: deque(maxlen=100))
        self._error_counts: Dict[str, int] = defaultdict(int)
        self._throughput_counter: Dict[str, int] = defaultdict(int)
        
        # System health
        self._health_status = SystemHealth(
            overall_status="unknown",
            timestamp=datetime.utcnow(),
            metrics={},
            alerts_active=0,
            performance_targets_met=0,
            performance_targets_total=0
        )
        
        self._setup_default_targets()
        self._setup_default_alerts()
        
        logger.info(f"ContextMonitor initialized with {collection_interval}s interval")
    
    async def start_monitoring(self) -> None:
        """Start background monitoring tasks"""
        self._collection_task = asyncio.create_task(self._metrics_collector())
        self._analysis_task = asyncio.create_task(self._metrics_analyzer())
        self._cleanup_task = asyncio.create_task(self._cleanup_worker())
        
        logger.info("Context monitoring started")
    
    async def stop_monitoring(self) -> None:
        """Stop monitoring tasks"""
        tasks = [self._collection_task, self._analysis_task, self._cleanup_task]
        
        for task in tasks:
            if task and not task.done():
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass
        
        logger.info("Context monitoring stopped")
    
    def record_operation_start(self, operation_name: str) -> str:
        """Start timing an operation"""
        operation_id = f"{operation_name}_{int(time.time() * 1000000)}"
        self._operation_times[operation_id] = deque([time.time()], maxlen=2)
        return operation_id
    
    def record_operation_end(self, operation_id: str, success: bool = True) -> float:
        """End timing an operation and record metrics"""
        if operation_id not in self._operation_times:
            logger.warning(f"Operation {operation_id} not found for timing")
            return 0.0
        
        times = self._operation_times[operation_id]
        if len(times) != 1:
            logger.warning(f"Invalid timing state for operation {operation_id}")
            return 0.0
        
        start_time = times[0]
        duration = time.time() - start_time
        
        # Extract operation name
        operation_name = operation_id.rsplit('_', 1)[0]
        
        # Record timing metric
        self.record_metric(
            name=f"{operation_name}_duration",
            value=duration,
            metric_type=MetricType.TIMER,
            tags={"operation": operation_name, "success": str(success)}
        )
        
        # Record success/error
        if success:
            self.record_metric(
                name=f"{operation_name}_success_count",
                value=1,
                metric_type=MetricType.COUNTER,
                tags={"operation": operation_name}
            )
        else:
            self._error_counts[operation_name] += 1
            self.record_metric(
                name=f"{operation_name}_error_count",
                value=1,
                metric_type=MetricType.COUNTER,
                tags={"operation": operation_name}
            )
        
        # Clean up
        del self._operation_times[operation_id]
        
        return duration
    
    def record_metric(
        self,
        name: str,
        value: Union[int, float],
        metric_type: MetricType = MetricType.GAUGE,
        tags: Optional[Dict[str, str]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """Record a performance metric"""
        metric = PerformanceMetric(
            name=name,
            value=value,
            metric_type=metric_type,
            timestamp=datetime.utcnow(),
            tags=tags or {},
            metadata=metadata or {}
        )
        
        self._metrics.append(metric)
        self._metric_timeseries[name].append((metric.timestamp, value))
        self._last_values[name] = value
        
        # Update throughput
        self._throughput_counter[name] += 1
    
    def record_context_preparation(
        self,
        request: ContextRequest,
        context: AgentContext,
        duration: float,
        success: bool = True
    ) -> None:
        """Record context preparation metrics"""
        base_tags = {
            "agent_type": request.agent_type,
            "story_id": request.story_id,
            "success": str(success)
        }
        
        if hasattr(request.task, 'current_state') and request.task.current_state:
            base_tags["tdd_phase"] = request.task.current_state.value
        
        # Record timing
        self.record_metric(
            name="context_preparation_time",
            value=duration,
            metric_type=MetricType.TIMER,
            tags=base_tags
        )
        
        if success and context:
            # Record token usage
            token_usage = context.get_total_token_estimate() if hasattr(context, 'get_total_token_estimate') else 0
            self.record_metric(
                name="context_token_usage",
                value=token_usage,
                metric_type=MetricType.GAUGE,
                tags=base_tags
            )
            
            # Record file count
            file_count = len(context.file_contents) if context.file_contents else 0
            self.record_metric(
                name="context_file_count",
                value=file_count,
                metric_type=MetricType.GAUGE,
                tags=base_tags
            )
            
            # Record compression status
            if hasattr(context, 'compression_applied'):
                self.record_metric(
                    name="context_compression_applied",
                    value=1 if context.compression_applied else 0,
                    metric_type=MetricType.GAUGE,
                    tags=base_tags
                )
            
            # Record cache hit
            if hasattr(context, 'cache_hit'):
                self.record_metric(
                    name="context_cache_hit",
                    value=1 if context.cache_hit else 0,
                    metric_type=MetricType.GAUGE,
                    tags=base_tags
                )
    
    def record_cache_metrics(self, cache_stats: Dict[str, Any]) -> None:
        """Record cache performance metrics"""
        cache_tags = {"component": "context_cache"}
        
        # Hit rate
        if "hit_rate" in cache_stats:
            self.record_metric(
                name="cache_hit_rate",
                value=cache_stats["hit_rate"],
                metric_type=MetricType.GAUGE,
                tags=cache_tags
            )
        
        # Memory usage
        if "memory_usage_bytes" in cache_stats:
            self.record_metric(
                name="cache_memory_usage_mb",
                value=cache_stats["memory_usage_bytes"] / (1024 * 1024),
                metric_type=MetricType.GAUGE,
                tags=cache_tags
            )
        
        # Entry count
        if "entry_count" in cache_stats:
            self.record_metric(
                name="cache_entry_count",
                value=cache_stats["entry_count"],
                metric_type=MetricType.GAUGE,
                tags=cache_tags
            )
    
    def add_alert(self, alert: Alert) -> None:
        """Add a new alert configuration"""
        self._alerts[alert.alert_id] = alert
        logger.info(f"Added alert: {alert.name}")
    
    def remove_alert(self, alert_id: str) -> bool:
        """Remove an alert configuration"""
        if alert_id in self._alerts:
            del self._alerts[alert_id]
            if alert_id in self._active_alerts:
                del self._active_alerts[alert_id]
            logger.info(f"Removed alert: {alert_id}")
            return True
        return False
    
    def add_performance_target(self, target: PerformanceTarget) -> None:
        """Add a performance target"""
        self._performance_targets[target.name] = target
        logger.info(f"Added performance target: {target.name}")
    
    def remove_performance_target(self, target_name: str) -> bool:
        """Remove a performance target"""
        if target_name in self._performance_targets:
            del self._performance_targets[target_name]
            logger.info(f"Removed performance target: {target_name}")
            return True
        return False
    
    def get_current_metrics(self) -> Dict[str, Any]:
        """Get current metric values"""
        return dict(self._last_values)
    
    def get_metric_history(
        self,
        metric_name: str,
        hours: int = 1
    ) -> List[Tuple[datetime, float]]:
        """Get historical values for a metric"""
        if metric_name not in self._metric_timeseries:
            return []
        
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        history = []
        
        for timestamp, value in self._metric_timeseries[metric_name]:
            if timestamp >= cutoff_time:
                history.append((timestamp, value))
        
        return history
    
    def get_system_health(self) -> SystemHealth:
        """Get current system health status"""
        return self._health_status
    
    def get_active_alerts(self) -> List[Alert]:
        """Get currently active alerts"""
        return list(self._active_alerts.values())
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """Get comprehensive performance summary"""
        current_time = datetime.utcnow()
        
        # Calculate recent metrics
        recent_metrics = {}
        for name, values in self._metric_timeseries.items():
            if values:
                recent_values = [v for t, v in values if (current_time - t).total_seconds() < 300]
                if recent_values:
                    recent_metrics[name] = {
                        "current": recent_values[-1],
                        "average": sum(recent_values) / len(recent_values),
                        "min": min(recent_values),
                        "max": max(recent_values),
                        "count": len(recent_values)
                    }
        
        # Performance target status
        targets_met = 0
        targets_total = len(self._performance_targets)
        target_details = {}
        
        for target_name, target in self._performance_targets.items():
            if target.enabled and target.metric_name in self._last_values:
                current_value = self._last_values[target.metric_name]
                is_met = target.evaluate(current_value)
                deviation = target.get_deviation_percent(current_value)
                
                if is_met:
                    targets_met += 1
                
                target_details[target_name] = {
                    "target_value": target.target_value,
                    "current_value": current_value,
                    "is_met": is_met,
                    "deviation_percent": deviation,
                    "operator": target.operator
                }
        
        return {
            "timestamp": current_time.isoformat(),
            "health_status": self._health_status.overall_status,
            "active_alerts": len(self._active_alerts),
            "performance_targets": {
                "met": targets_met,
                "total": targets_total,
                "percentage": (targets_met / targets_total * 100) if targets_total > 0 else 0,
                "details": target_details
            },
            "recent_metrics": recent_metrics,
            "error_counts": dict(self._error_counts),
            "throughput": dict(self._throughput_counter)
        }
    
    async def export_metrics(
        self,
        format_type: str = "json",
        hours: int = 1
    ) -> Union[str, Dict[str, Any]]:
        """Export metrics data"""
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        
        exported_data = {
            "export_timestamp": datetime.utcnow().isoformat(),
            "period_hours": hours,
            "metrics": []
        }
        
        for metric in self._metrics:
            if metric.timestamp >= cutoff_time:
                exported_data["metrics"].append(metric.to_dict())
        
        if format_type == "json":
            return json.dumps(exported_data, indent=2)
        else:
            return exported_data
    
    # Private methods
    
    async def _metrics_collector(self) -> None:
        """Background task for metrics collection"""
        while True:
            try:
                await asyncio.sleep(self.collection_interval)
                
                # Collect system metrics if enabled
                if self.enable_system_metrics:
                    await self._collect_system_metrics()
                
                # Update system health
                await self._update_system_health()
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in metrics collector: {str(e)}")
    
    async def _metrics_analyzer(self) -> None:
        """Background task for metrics analysis and alerting"""
        while True:
            try:
                await asyncio.sleep(10)  # Check every 10 seconds
                
                if self.enable_alerts:
                    await self._evaluate_alerts()
                
                await self._evaluate_performance_targets()
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in metrics analyzer: {str(e)}")
    
    async def _cleanup_worker(self) -> None:
        """Background task for data cleanup"""
        while True:
            try:
                await asyncio.sleep(3600)  # Clean every hour
                await self._cleanup_old_data()
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in cleanup worker: {str(e)}")
    
    async def _collect_system_metrics(self) -> None:
        """Collect system-level metrics"""
        try:
            if psutil is None:
                # Fallback values when psutil is not available
                self.record_metric(
                    name="system_cpu_percent",
                    value=50.0,  # Mock moderate usage
                    metric_type=MetricType.GAUGE,
                    tags={"component": "system", "mock": "true"}
                )
                self.record_metric(
                    name="system_memory_percent",
                    value=60.0,  # Mock moderate usage
                    metric_type=MetricType.GAUGE,
                    tags={"component": "system", "mock": "true"}
                )
                self.record_metric(
                    name="system_memory_available_mb",
                    value=2048.0,  # Mock 2GB available
                    metric_type=MetricType.GAUGE,
                    tags={"component": "system", "mock": "true"}
                )
                self.record_metric(
                    name="system_disk_percent",
                    value=70.0,  # Mock moderate usage
                    metric_type=MetricType.GAUGE,
                    tags={"component": "system", "mock": "true"}
                )
                return
            
            # CPU usage
            cpu_percent = psutil.cpu_percent(interval=1)
            self.record_metric(
                name="system_cpu_percent",
                value=cpu_percent,
                metric_type=MetricType.GAUGE,
                tags={"component": "system"}
            )
            
            # Memory usage
            memory = psutil.virtual_memory()
            self.record_metric(
                name="system_memory_percent",
                value=memory.percent,
                metric_type=MetricType.GAUGE,
                tags={"component": "system"}
            )
            
            self.record_metric(
                name="system_memory_available_mb",
                value=memory.available / (1024 * 1024),
                metric_type=MetricType.GAUGE,
                tags={"component": "system"}
            )
            
            # Disk usage
            disk = psutil.disk_usage('/')
            self.record_metric(
                name="system_disk_percent",
                value=(disk.used / disk.total) * 100,
                metric_type=MetricType.GAUGE,
                tags={"component": "system"}
            )
            
        except Exception as e:
            logger.warning(f"Error collecting system metrics: {str(e)}")
    
    async def _update_system_health(self) -> None:
        """Update overall system health status"""
        # Determine health based on active alerts and performance targets
        critical_alerts = sum(1 for alert in self._active_alerts.values() 
                             if alert.severity == AlertSeverity.CRITICAL)
        error_alerts = sum(1 for alert in self._active_alerts.values() 
                          if alert.severity == AlertSeverity.ERROR)
        
        targets_met = 0
        targets_total = len(self._performance_targets)
        
        for target in self._performance_targets.values():
            if target.enabled and target.metric_name in self._last_values:
                if target.evaluate(self._last_values[target.metric_name]):
                    targets_met += 1
        
        # Determine overall status
        if critical_alerts > 0:
            status = "unhealthy"
        elif error_alerts > 0 or (targets_total > 0 and targets_met / targets_total < 0.8):
            status = "degraded"
        else:
            status = "healthy"
        
        self._health_status = SystemHealth(
            overall_status=status,
            timestamp=datetime.utcnow(),
            metrics=dict(self._last_values),
            alerts_active=len(self._active_alerts),
            performance_targets_met=targets_met,
            performance_targets_total=targets_total,
            details={
                "critical_alerts": critical_alerts,
                "error_alerts": error_alerts,
                "target_success_rate": targets_met / targets_total if targets_total > 0 else 1.0
            }
        )
    
    async def _evaluate_alerts(self) -> None:
        """Evaluate alert conditions"""
        for alert_id, alert in self._alerts.items():
            if not alert.enabled or alert.is_in_cooldown():
                continue
            
            try:
                # Prepare context for condition evaluation
                context = {
                    "metrics": self._last_values,
                    "error_counts": self._error_counts,
                    "active_alerts": len(self._active_alerts)
                }
                
                # Evaluate condition
                if eval(alert.condition, {"__builtins__": {}}, context):
                    await self._trigger_alert(alert, context)
                
            except Exception as e:
                logger.error(f"Error evaluating alert {alert_id}: {str(e)}")
    
    async def _trigger_alert(self, alert: Alert, context: Dict[str, Any]) -> None:
        """Trigger an alert"""
        alert.last_triggered = datetime.utcnow()
        alert.trigger_count += 1
        self._active_alerts[alert.alert_id] = alert
        
        message = alert.format_message(context)
        logger.warning(f"ALERT [{alert.severity.value.upper()}] {alert.name}: {message}")
        
        # Execute callbacks
        for callback in alert.callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(alert, context)
                else:
                    callback(alert, context)
            except Exception as e:
                logger.error(f"Error executing alert callback: {str(e)}")
    
    async def _evaluate_performance_targets(self) -> None:
        """Evaluate performance targets"""
        for target_name, target in self._performance_targets.items():
            if not target.enabled or target.metric_name not in self._last_values:
                continue
            
            current_value = self._last_values[target.metric_name]
            is_met = target.evaluate(current_value)
            
            # Record target compliance
            self.record_metric(
                name=f"target_{target_name}_compliance",
                value=1 if is_met else 0,
                metric_type=MetricType.GAUGE,
                tags={"target": target_name}
            )
    
    async def _cleanup_old_data(self) -> None:
        """Clean up old metrics data"""
        cutoff_time = datetime.utcnow() - timedelta(hours=self.retention_hours)
        
        # Clean metrics
        cleaned_count = 0
        while self._metrics and self._metrics[0].timestamp < cutoff_time:
            self._metrics.popleft()
            cleaned_count += 1
        
        # Clean timeseries data
        for name, series in self._metric_timeseries.items():
            while series and series[0][0] < cutoff_time:
                series.popleft()
        
        # Clear resolved alerts older than 1 hour
        alert_cutoff = datetime.utcnow() - timedelta(hours=1)
        resolved_alerts = []
        
        for alert_id, alert in self._active_alerts.items():
            if alert.last_triggered and alert.last_triggered < alert_cutoff:
                resolved_alerts.append(alert_id)
        
        for alert_id in resolved_alerts:
            del self._active_alerts[alert_id]
        
        if cleaned_count > 0:
            logger.debug(f"Cleaned up {cleaned_count} old metrics and {len(resolved_alerts)} resolved alerts")
    
    def _setup_default_targets(self) -> None:
        """Setup default performance targets"""
        targets = [
            PerformanceTarget(
                name="context_prep_time",
                metric_name="context_preparation_time",
                target_value=2.0,  # 2 seconds
                operator="<"
            ),
            PerformanceTarget(
                name="cache_hit_rate",
                metric_name="cache_hit_rate",
                target_value=0.8,  # 80%
                operator=">="
            ),
            PerformanceTarget(
                name="system_memory",
                metric_name="system_memory_percent",
                target_value=90.0,  # 90%
                operator="<"
            ),
            PerformanceTarget(
                name="context_token_efficiency",
                metric_name="context_token_usage",
                target_value=180000,  # 90% of 200k limit
                operator="<"
            )
        ]
        
        for target in targets:
            self._performance_targets[target.name] = target
    
    def _setup_default_alerts(self) -> None:
        """Setup default alert configurations"""
        alerts = [
            Alert(
                alert_id="high_prep_time",
                name="High Context Preparation Time",
                condition="metrics.get('context_preparation_time', 0) > 5.0",
                severity=AlertSeverity.WARNING,
                message_template="Context preparation time exceeded 5 seconds: {context_preparation_time:.2f}s"
            ),
            Alert(
                alert_id="low_cache_hit_rate",
                name="Low Cache Hit Rate",
                condition="metrics.get('cache_hit_rate', 1.0) < 0.5",
                severity=AlertSeverity.WARNING,
                message_template="Cache hit rate below 50%: {cache_hit_rate:.1%}"
            ),
            Alert(
                alert_id="high_memory_usage",
                name="High Memory Usage",
                condition="metrics.get('system_memory_percent', 0) > 95.0",
                severity=AlertSeverity.ERROR,
                message_template="System memory usage critical: {system_memory_percent:.1f}%"
            ),
            Alert(
                alert_id="context_errors",
                name="Context Preparation Errors",
                condition="error_counts.get('context_preparation', 0) > 5",
                severity=AlertSeverity.ERROR,
                message_template="Multiple context preparation errors: {context_preparation_error_count}"
            )
        ]
        
        for alert in alerts:
            self._alerts[alert.alert_id] = alert