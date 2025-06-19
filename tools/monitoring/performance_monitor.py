#!/usr/bin/env python3
"""
Performance Monitoring Utility for Agent Workflow

Simple utility to monitor and report on system performance metrics,
including state machine performance, agent response times, and resource usage.
"""

import asyncio
import logging
import time
import json
import statistics
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from pathlib import Path
import psutil
import requests

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@dataclass
class PerformanceSnapshot:
    """Performance metrics snapshot"""
    timestamp: datetime
    cpu_usage: float
    memory_usage: float
    disk_usage: float
    network_io: Dict[str, int]
    active_processes: int
    system_load: List[float]
    
    # Application-specific metrics
    workflow_state: Optional[str] = None
    active_tdd_cycles: int = 0
    state_machine_metrics: Optional[Dict] = None
    response_times: Optional[Dict] = None


class PerformanceMonitor:
    """Lightweight performance monitoring for agent workflow."""
    
    def __init__(self, 
                 collection_interval: int = 30,
                 storage_path: str = ".orch-monitoring",
                 visualizer_url: str = "http://localhost:5000"):
        """
        Initialize performance monitor.
        
        Args:
            collection_interval: Seconds between metric collections
            storage_path: Path to store monitoring data
            visualizer_url: URL of the state visualizer for app-specific metrics
        """
        self.collection_interval = collection_interval
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(exist_ok=True)
        self.visualizer_url = visualizer_url
        
        # Metrics storage
        self.snapshots: List[PerformanceSnapshot] = []
        self.max_snapshots = 1000  # Keep last 1000 snapshots
        
        # Performance thresholds
        self.thresholds = {
            "cpu_usage": 80.0,  # %
            "memory_usage": 85.0,  # %
            "disk_usage": 90.0,  # %
            "response_time": 1.0  # seconds
        }
        
        # Alert tracking
        self.alerts_sent = set()
        self.last_alert_time = {}
        
        logger.info("Performance monitor initialized")
    
    async def start_monitoring(self) -> None:
        """Start continuous performance monitoring."""
        logger.info("Starting performance monitoring...")
        
        while True:
            try:
                snapshot = await self._collect_metrics()
                self.snapshots.append(snapshot)
                
                # Maintain max snapshots limit
                if len(self.snapshots) > self.max_snapshots:
                    self.snapshots.pop(0)
                
                # Check for performance issues
                await self._check_performance_alerts(snapshot)
                
                # Save periodic reports
                if len(self.snapshots) % 10 == 0:
                    await self._save_report()
                
                await asyncio.sleep(self.collection_interval)
                
            except Exception as e:
                logger.error(f"Metrics collection error: {e}")
                await asyncio.sleep(self.collection_interval * 2)
    
    async def _collect_metrics(self) -> PerformanceSnapshot:
        """Collect current performance metrics."""
        # System metrics
        cpu_usage = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        network = psutil.net_io_counters()
        load_avg = psutil.getloadavg() if hasattr(psutil, 'getloadavg') else [0, 0, 0]
        
        # Application-specific metrics
        app_metrics = await self._collect_app_metrics()
        
        snapshot = PerformanceSnapshot(
            timestamp=datetime.utcnow(),
            cpu_usage=cpu_usage,
            memory_usage=memory.percent,
            disk_usage=(disk.used / disk.total) * 100,
            network_io={
                "bytes_sent": network.bytes_sent,
                "bytes_recv": network.bytes_recv,
                "packets_sent": network.packets_sent,
                "packets_recv": network.packets_recv
            },
            active_processes=len(psutil.pids()),
            system_load=list(load_avg),
            workflow_state=app_metrics.get("workflow_state"),
            active_tdd_cycles=app_metrics.get("active_tdd_cycles", 0),
            state_machine_metrics=app_metrics.get("state_machine_metrics"),
            response_times=app_metrics.get("response_times")
        )
        
        logger.debug(f"Collected metrics: CPU={cpu_usage:.1f}%, "
                    f"Memory={memory.percent:.1f}%, "
                    f"Disk={snapshot.disk_usage:.1f}%")
        
        return snapshot
    
    async def _collect_app_metrics(self) -> Dict[str, Any]:
        """Collect application-specific metrics from visualizer."""
        app_metrics = {}
        
        try:
            # Get current state
            response = requests.get(f"{self.visualizer_url}/api/state", timeout=5)
            if response.status_code == 200:
                state_data = response.json()
                app_metrics["workflow_state"] = state_data.get("workflow_state")
                app_metrics["active_tdd_cycles"] = len(state_data.get("tdd_cycles", {}))
            
            # Get debug info for response times
            response = requests.get(f"{self.visualizer_url}/debug", timeout=5)
            if response.status_code == 200:
                debug_data = response.json()
                app_metrics["response_times"] = {
                    "visualizer_response_time": response.elapsed.total_seconds()
                }
                
        except requests.RequestException as e:
            logger.warning(f"Could not collect app metrics: {e}")
        except Exception as e:
            logger.error(f"App metrics collection error: {e}")
        
        return app_metrics
    
    async def _check_performance_alerts(self, snapshot: PerformanceSnapshot) -> None:
        """Check for performance issues and send alerts."""
        alerts = []
        
        # Check CPU usage
        if snapshot.cpu_usage > self.thresholds["cpu_usage"]:
            alerts.append(f"High CPU usage: {snapshot.cpu_usage:.1f}%")
        
        # Check memory usage
        if snapshot.memory_usage > self.thresholds["memory_usage"]:
            alerts.append(f"High memory usage: {snapshot.memory_usage:.1f}%")
        
        # Check disk usage
        if snapshot.disk_usage > self.thresholds["disk_usage"]:
            alerts.append(f"High disk usage: {snapshot.disk_usage:.1f}%")
        
        # Check response times
        if snapshot.response_times:
            for endpoint, response_time in snapshot.response_times.items():
                if response_time > self.thresholds["response_time"]:
                    alerts.append(f"Slow response: {endpoint} took {response_time:.2f}s")
        
        # Send alerts (with rate limiting)
        for alert in alerts:
            await self._send_alert(alert, snapshot.timestamp)
    
    async def _send_alert(self, message: str, timestamp: datetime) -> None:
        """Send performance alert with rate limiting."""
        alert_key = message.split(":")[0]  # Use alert type as key
        
        # Rate limiting: don't send same alert more than once per 5 minutes
        if alert_key in self.last_alert_time:
            time_since_last = (timestamp - self.last_alert_time[alert_key]).total_seconds()
            if time_since_last < 300:  # 5 minutes
                return
        
        logger.warning(f"PERFORMANCE ALERT: {message}")
        self.last_alert_time[alert_key] = timestamp
        
        # In a real system, this would send notifications to Discord, Slack, etc.
        # For now, just log the alert
    
    async def _save_report(self) -> None:
        """Save performance report to disk."""
        try:
            report_data = {
                "generated_at": datetime.utcnow().isoformat(),
                "snapshots_count": len(self.snapshots),
                "monitoring_period": {
                    "start": self.snapshots[0].timestamp.isoformat() if self.snapshots else None,
                    "end": self.snapshots[-1].timestamp.isoformat() if self.snapshots else None
                },
                "summary": self._generate_summary(),
                "recent_snapshots": [asdict(s) for s in self.snapshots[-10:]]  # Last 10 snapshots
            }
            
            report_file = self.storage_path / f"performance_report_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json"
            with open(report_file, 'w') as f:
                json.dump(report_data, f, indent=2, default=str)
            
            logger.debug(f"Saved performance report: {report_file}")
            
        except Exception as e:
            logger.error(f"Failed to save performance report: {e}")
    
    def _generate_summary(self) -> Dict[str, Any]:
        """Generate performance summary statistics."""
        if not self.snapshots:
            return {}
        
        cpu_values = [s.cpu_usage for s in self.snapshots]
        memory_values = [s.memory_usage for s in self.snapshots]
        disk_values = [s.disk_usage for s in self.snapshots]
        
        return {
            "cpu_usage": {
                "avg": statistics.mean(cpu_values),
                "max": max(cpu_values),
                "min": min(cpu_values),
                "p95": statistics.quantiles(cpu_values, n=20)[18] if len(cpu_values) >= 20 else max(cpu_values)
            },
            "memory_usage": {
                "avg": statistics.mean(memory_values),
                "max": max(memory_values),
                "min": min(memory_values)
            },
            "disk_usage": {
                "avg": statistics.mean(disk_values),
                "max": max(disk_values),
                "min": min(disk_values)
            },
            "alerts_triggered": len(self.last_alert_time),
            "workflow_states": self._get_state_distribution()
        }
    
    def _get_state_distribution(self) -> Dict[str, int]:
        """Get distribution of workflow states."""
        state_counts = {}
        for snapshot in self.snapshots:
            if snapshot.workflow_state:
                state_counts[snapshot.workflow_state] = state_counts.get(snapshot.workflow_state, 0) + 1
        return state_counts
    
    def get_current_status(self) -> Dict[str, Any]:
        """Get current monitoring status."""
        if not self.snapshots:
            return {"status": "no_data"}
        
        latest = self.snapshots[-1]
        return {
            "status": "monitoring",
            "latest_snapshot": asdict(latest),
            "snapshots_collected": len(self.snapshots),
            "monitoring_duration_minutes": (
                (latest.timestamp - self.snapshots[0].timestamp).total_seconds() / 60
                if len(self.snapshots) > 1 else 0
            ),
            "summary": self._generate_summary()
        }


async def main():
    """Main monitoring loop."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Agent Workflow Performance Monitor')
    parser.add_argument('--interval', type=int, default=30, 
                       help='Collection interval in seconds (default: 30)')
    parser.add_argument('--visualizer-url', default='http://localhost:5000',
                       help='URL of the state visualizer (default: http://localhost:5000)')
    parser.add_argument('--storage-path', default='.orch-monitoring',
                       help='Path to store monitoring data (default: .orch-monitoring)')
    parser.add_argument('--report-only', action='store_true',
                       help='Generate summary report and exit')
    
    args = parser.parse_args()
    
    monitor = PerformanceMonitor(
        collection_interval=args.interval,
        storage_path=args.storage_path,
        visualizer_url=args.visualizer_url
    )
    
    if args.report_only:
        # Generate current status report
        status = monitor.get_current_status()
        print(json.dumps(status, indent=2, default=str))
        return
    
    try:
        await monitor.start_monitoring()
    except KeyboardInterrupt:
        logger.info("Performance monitoring stopped by user")
    except Exception as e:
        logger.error(f"Performance monitoring error: {e}")


if __name__ == "__main__":
    asyncio.run(main())