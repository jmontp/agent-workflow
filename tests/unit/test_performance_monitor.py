"""
Comprehensive test coverage for tools/monitoring/performance_monitor.py

Tests cover all monitoring functionality including resource monitoring, 
alert thresholds, notifications, report generation, continuous monitoring,
and error conditions to achieve 100% coverage.
"""

import pytest
import asyncio
import json
import tempfile
import shutil
from unittest.mock import patch, MagicMock, Mock, AsyncMock
from pathlib import Path
from datetime import datetime, timedelta
from dataclasses import asdict

# Import the module under test
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from tools.monitoring.performance_monitor import PerformanceMonitor, PerformanceSnapshot


@pytest.fixture
def temp_dir():
    """Create a temporary directory for testing"""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir)


@pytest.fixture
def monitor(temp_dir):
    """Create a performance monitor instance for testing"""
    return PerformanceMonitor(
        collection_interval=1,
        storage_path=temp_dir,
        visualizer_url="http://localhost:5000"
    )


@pytest.fixture
def sample_snapshot():
    """Create a sample performance snapshot for testing"""
    return PerformanceSnapshot(
        timestamp=datetime.utcnow(),
        cpu_usage=25.5,
        memory_usage=45.2,
        disk_usage=60.0,
        network_io={"bytes_sent": 1000, "bytes_recv": 2000, "packets_sent": 10, "packets_recv": 20},
        active_processes=150,
        system_load=[1.0, 1.2, 1.5],
        workflow_state="idle",
        active_tdd_cycles=2,
        state_machine_metrics={"transitions": 5, "errors": 0},
        response_times={"api_call": 0.5, "database": 0.2}
    )


class TestPerformanceSnapshot:
    """Test PerformanceSnapshot dataclass"""
    
    def test_basic_creation(self, sample_snapshot):
        """Test basic snapshot creation"""
        assert isinstance(sample_snapshot.timestamp, datetime)
        assert sample_snapshot.cpu_usage == 25.5
        assert sample_snapshot.memory_usage == 45.2
        assert sample_snapshot.disk_usage == 60.0
        assert sample_snapshot.active_processes == 150
        assert len(sample_snapshot.system_load) == 3
    
    def test_optional_fields(self):
        """Test optional fields in snapshot"""
        snapshot = PerformanceSnapshot(
            timestamp=datetime.utcnow(),
            cpu_usage=10.0,
            memory_usage=20.0,
            disk_usage=30.0,
            network_io={},
            active_processes=100,
            system_load=[0.5]
        )
        
        assert snapshot.workflow_state is None
        assert snapshot.active_tdd_cycles == 0
        assert snapshot.state_machine_metrics is None
        assert snapshot.response_times is None
    
    def test_snapshot_serialization(self, sample_snapshot):
        """Test that snapshot can be serialized to dict"""
        snapshot_dict = asdict(sample_snapshot)
        
        assert isinstance(snapshot_dict, dict)
        assert "timestamp" in snapshot_dict
        assert "cpu_usage" in snapshot_dict
        assert "workflow_state" in snapshot_dict
        assert snapshot_dict["cpu_usage"] == 25.5


class TestPerformanceMonitorInitialization:
    """Test PerformanceMonitor initialization"""
    
    def test_default_initialization(self, temp_dir):
        """Test default monitor initialization"""
        monitor = PerformanceMonitor(storage_path=temp_dir)
        
        assert monitor.collection_interval == 30
        assert str(monitor.storage_path) == temp_dir
        assert monitor.visualizer_url == "http://localhost:5000"
        assert monitor.snapshots == []
        assert monitor.max_snapshots == 1000
        assert monitor.alerts_sent == set()
        assert monitor.last_alert_time == {}
    
    def test_custom_initialization(self, temp_dir):
        """Test custom monitor initialization"""
        monitor = PerformanceMonitor(
            collection_interval=15,
            storage_path=temp_dir,
            visualizer_url="http://custom:8080"
        )
        
        assert monitor.collection_interval == 15
        assert str(monitor.storage_path) == temp_dir
        assert monitor.visualizer_url == "http://custom:8080"
    
    def test_storage_directory_creation(self):
        """Test that storage directory is created if it doesn't exist"""
        with tempfile.TemporaryDirectory() as temp_dir:
            storage_path = os.path.join(temp_dir, "new_storage_dir")
            monitor = PerformanceMonitor(storage_path=storage_path)
            
            assert os.path.exists(storage_path)
            assert os.path.isdir(storage_path)
    
    def test_threshold_defaults(self, monitor):
        """Test default threshold values"""
        expected_thresholds = {
            "cpu_usage": 80.0,
            "memory_usage": 85.0,
            "disk_usage": 90.0,
            "response_time": 1.0
        }
        
        assert monitor.thresholds == expected_thresholds


class TestResourceMonitoring:
    """Test resource monitoring functionality"""
    
    @pytest.mark.asyncio
    @patch('tools.monitoring.performance_monitor.psutil.cpu_percent')
    @patch('tools.monitoring.performance_monitor.psutil.virtual_memory')
    @patch('tools.monitoring.performance_monitor.psutil.disk_usage')
    @patch('tools.monitoring.performance_monitor.psutil.net_io_counters')
    @patch('tools.monitoring.performance_monitor.psutil.getloadavg')
    @patch('tools.monitoring.performance_monitor.psutil.pids')
    async def test_collect_metrics_success(self, mock_pids, mock_loadavg, mock_net, 
                                         mock_disk, mock_memory, mock_cpu, monitor):
        """Test successful metrics collection"""
        # Mock system metrics
        mock_cpu.return_value = 15.5
        mock_memory.return_value = Mock(percent=30.2)
        mock_disk.return_value = Mock(used=500, total=1000)
        mock_net.return_value = Mock(
            bytes_sent=1000, bytes_recv=2000,
            packets_sent=10, packets_recv=20
        )
        mock_loadavg.return_value = [0.5, 0.8, 1.0]
        mock_pids.return_value = [1, 2, 3, 4, 5]
        
        # Mock app metrics
        with patch.object(monitor, '_collect_app_metrics', return_value={}):
            snapshot = await monitor._collect_metrics()
        
        assert snapshot.cpu_usage == 15.5
        assert snapshot.memory_usage == 30.2
        assert snapshot.disk_usage == 50.0  # 500/1000 * 100
        assert snapshot.network_io["bytes_sent"] == 1000
        assert snapshot.network_io["bytes_recv"] == 2000
        assert snapshot.active_processes == 5
        assert snapshot.system_load == [0.5, 0.8, 1.0]
    
    @patch('tools.monitoring.performance_monitor.psutil.cpu_percent')
    @patch('tools.monitoring.performance_monitor.psutil.virtual_memory')
    @patch('tools.monitoring.performance_monitor.psutil.disk_usage')
    @patch('tools.monitoring.performance_monitor.psutil.net_io_counters')
    @patch('tools.monitoring.performance_monitor.hasattr')
    @patch('tools.monitoring.performance_monitor.psutil.pids')
    @pytest.mark.asyncio
    async def test_collect_metrics_no_loadavg(self, mock_pids, mock_hasattr, mock_net,
                                            mock_disk, mock_memory, mock_cpu, monitor):
        """Test metrics collection when getloadavg is not available"""
        # Mock system metrics
        mock_cpu.return_value = 20.0
        mock_memory.return_value = Mock(percent=40.0)
        mock_disk.return_value = Mock(used=600, total=1000)
        mock_net.return_value = Mock(
            bytes_sent=2000, bytes_recv=3000,
            packets_sent=20, packets_recv=30
        )
        mock_hasattr.return_value = False  # No getloadavg
        mock_pids.return_value = [1, 2, 3]
        
        # Mock app metrics
        with patch.object(monitor, '_collect_app_metrics', return_value={}):
            snapshot = await monitor._collect_metrics()
        
        assert snapshot.cpu_usage == 20.0
        assert snapshot.memory_usage == 40.0
        assert snapshot.disk_usage == 60.0
        assert snapshot.system_load == [0, 0, 0]  # Default when loadavg not available
        assert snapshot.active_processes == 3
    
    @patch('tools.monitoring.performance_monitor.requests.get')
    @pytest.mark.asyncio
    async def test_collect_app_metrics_success(self, mock_get, monitor):
        """Test successful application metrics collection"""
        # Mock successful state response
        state_response = Mock()
        state_response.status_code = 200
        state_response.json.return_value = {
            "workflow_state": "processing",
            "tdd_cycles": {"cycle1": {}, "cycle2": {}}
        }
        
        # Mock successful debug response
        debug_response = Mock()
        debug_response.status_code = 200
        debug_response.json.return_value = {"debug": "data"}
        debug_response.elapsed.total_seconds.return_value = 0.25
        
        mock_get.side_effect = [state_response, debug_response]
        
        app_metrics = await monitor._collect_app_metrics()
        
        assert app_metrics["workflow_state"] == "processing"
        assert app_metrics["active_tdd_cycles"] == 2
        assert app_metrics["response_times"]["visualizer_response_time"] == 0.25
    
    @patch('tools.monitoring.performance_monitor.requests.get')
    @pytest.mark.asyncio
    async def test_collect_app_metrics_state_error(self, mock_get, monitor):
        """Test app metrics collection with state endpoint error"""
        # Mock failed state response
        state_response = Mock()
        state_response.status_code = 404
        
        # Mock successful debug response
        debug_response = Mock()
        debug_response.status_code = 200
        debug_response.json.return_value = {}
        debug_response.elapsed.total_seconds.return_value = 0.1
        
        mock_get.side_effect = [state_response, debug_response]
        
        app_metrics = await monitor._collect_app_metrics()
        
        assert "workflow_state" not in app_metrics
        assert "active_tdd_cycles" not in app_metrics
        assert app_metrics["response_times"]["visualizer_response_time"] == 0.1
    
    @patch('tools.monitoring.performance_monitor.requests.get')
    @pytest.mark.asyncio
    async def test_collect_app_metrics_network_error(self, mock_get, monitor):
        """Test app metrics collection with network error"""
        import requests
        mock_get.side_effect = requests.RequestException("Network error")
        
        app_metrics = await monitor._collect_app_metrics()
        
        assert app_metrics == {}
    
    @patch('tools.monitoring.performance_monitor.requests.get')
    @pytest.mark.asyncio
    async def test_collect_app_metrics_general_error(self, mock_get, monitor):
        """Test app metrics collection with general error"""
        mock_get.side_effect = Exception("General error")
        
        app_metrics = await monitor._collect_app_metrics()
        
        assert app_metrics == {}


class TestAlertSystem:
    """Test alert system functionality"""
    
    @pytest.mark.asyncio
    async def test_check_performance_alerts_no_alerts(self, monitor, sample_snapshot):
        """Test alert checking with no alerts triggered"""
        # Modify snapshot to have values below thresholds
        sample_snapshot.cpu_usage = 50.0
        sample_snapshot.memory_usage = 60.0
        sample_snapshot.disk_usage = 70.0
        sample_snapshot.response_times = {"api": 0.5}
        
        with patch.object(monitor, '_send_alert') as mock_send_alert:
            await monitor._check_performance_alerts(sample_snapshot)
        
        mock_send_alert.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_check_performance_alerts_cpu_alert(self, monitor, sample_snapshot):
        """Test CPU usage alert"""
        sample_snapshot.cpu_usage = 90.0  # Above 80% threshold
        sample_snapshot.memory_usage = 60.0
        sample_snapshot.disk_usage = 70.0
        sample_snapshot.response_times = None
        
        with patch.object(monitor, '_send_alert') as mock_send_alert:
            await monitor._check_performance_alerts(sample_snapshot)
        
        mock_send_alert.assert_called_once()
        call_args = mock_send_alert.call_args[0]
        assert "High CPU usage: 90.0%" in call_args[0]
    
    @pytest.mark.asyncio
    async def test_check_performance_alerts_memory_alert(self, monitor, sample_snapshot):
        """Test memory usage alert"""
        sample_snapshot.cpu_usage = 50.0
        sample_snapshot.memory_usage = 90.0  # Above 85% threshold
        sample_snapshot.disk_usage = 70.0
        sample_snapshot.response_times = None
        
        with patch.object(monitor, '_send_alert') as mock_send_alert:
            await monitor._check_performance_alerts(sample_snapshot)
        
        mock_send_alert.assert_called_once()
        call_args = mock_send_alert.call_args[0]
        assert "High memory usage: 90.0%" in call_args[0]
    
    @pytest.mark.asyncio
    async def test_check_performance_alerts_disk_alert(self, monitor, sample_snapshot):
        """Test disk usage alert"""
        sample_snapshot.cpu_usage = 50.0
        sample_snapshot.memory_usage = 60.0
        sample_snapshot.disk_usage = 95.0  # Above 90% threshold
        sample_snapshot.response_times = None
        
        with patch.object(monitor, '_send_alert') as mock_send_alert:
            await monitor._check_performance_alerts(sample_snapshot)
        
        mock_send_alert.assert_called_once()
        call_args = mock_send_alert.call_args[0]
        assert "High disk usage: 95.0%" in call_args[0]
    
    @pytest.mark.asyncio
    async def test_check_performance_alerts_response_time_alert(self, monitor, sample_snapshot):
        """Test response time alert"""
        sample_snapshot.cpu_usage = 50.0
        sample_snapshot.memory_usage = 60.0
        sample_snapshot.disk_usage = 70.0
        sample_snapshot.response_times = {"slow_endpoint": 2.5}  # Above 1.0s threshold
        
        with patch.object(monitor, '_send_alert') as mock_send_alert:
            await monitor._check_performance_alerts(sample_snapshot)
        
        mock_send_alert.assert_called_once()
        call_args = mock_send_alert.call_args[0]
        assert "Slow response: slow_endpoint took 2.50s" in call_args[0]
    
    @pytest.mark.asyncio
    async def test_check_performance_alerts_multiple_alerts(self, monitor, sample_snapshot):
        """Test multiple alerts triggered simultaneously"""
        sample_snapshot.cpu_usage = 90.0  # Above threshold
        sample_snapshot.memory_usage = 90.0  # Above threshold
        sample_snapshot.disk_usage = 70.0  # Below threshold
        sample_snapshot.response_times = {"endpoint": 2.0}  # Above threshold
        
        with patch.object(monitor, '_send_alert') as mock_send_alert:
            await monitor._check_performance_alerts(sample_snapshot)
        
        # Should be called 3 times (CPU, memory, response time)
        assert mock_send_alert.call_count == 3
    
    @pytest.mark.asyncio
    async def test_send_alert_first_time(self, monitor):
        """Test sending alert for the first time"""
        timestamp = datetime.utcnow()
        
        await monitor._send_alert("High CPU usage: 90%", timestamp)
        
        assert "High CPU usage" in monitor.last_alert_time
        assert monitor.last_alert_time["High CPU usage"] == timestamp
    
    @pytest.mark.asyncio
    async def test_send_alert_rate_limiting(self, monitor):
        """Test alert rate limiting"""
        timestamp1 = datetime.utcnow()
        timestamp2 = timestamp1 + timedelta(minutes=2)  # Only 2 minutes later
        
        # Send first alert
        await monitor._send_alert("High CPU usage: 90%", timestamp1)
        
        # Try to send second alert too soon
        await monitor._send_alert("High CPU usage: 95%", timestamp2)
        
        # Should only have one entry in last_alert_time
        assert len(monitor.last_alert_time) == 1
        assert monitor.last_alert_time["High CPU usage"] == timestamp1
    
    @pytest.mark.asyncio
    async def test_send_alert_after_cooldown(self, monitor):
        """Test sending alert after cooldown period"""
        timestamp1 = datetime.utcnow()
        timestamp2 = timestamp1 + timedelta(minutes=6)  # 6 minutes later (> 5 min cooldown)
        
        # Send first alert
        await monitor._send_alert("High CPU usage: 90%", timestamp1)
        
        # Send second alert after cooldown
        await monitor._send_alert("High CPU usage: 95%", timestamp2)
        
        # Should update the last alert time
        assert monitor.last_alert_time["High CPU usage"] == timestamp2


class TestReportGeneration:
    """Test report generation functionality"""
    
    @pytest.mark.asyncio
    async def test_save_report_empty_snapshots(self, monitor):
        """Test saving report with no snapshots"""
        await monitor._save_report()
        
        # Check that report files are created
        report_files = list(monitor.storage_path.glob("performance_report_*.json"))
        assert len(report_files) == 1
        
        # Check report content
        with open(report_files[0], 'r') as f:
            report_data = json.load(f)
        
        assert report_data["snapshots_count"] == 0
        assert report_data["monitoring_period"]["start"] is None
        assert report_data["monitoring_period"]["end"] is None
        assert report_data["summary"] == {}
        assert report_data["recent_snapshots"] == []
    
    @pytest.mark.asyncio
    async def test_save_report_with_snapshots(self, monitor, sample_snapshot):
        """Test saving report with snapshots"""
        # Add some snapshots
        monitor.snapshots = [sample_snapshot] * 5
        
        await monitor._save_report()
        
        # Check that report files are created
        report_files = list(monitor.storage_path.glob("performance_report_*.json"))
        assert len(report_files) == 1
        
        # Check report content
        with open(report_files[0], 'r') as f:
            report_data = json.load(f)
        
        assert report_data["snapshots_count"] == 5
        assert report_data["monitoring_period"]["start"] is not None
        assert report_data["monitoring_period"]["end"] is not None
        assert len(report_data["recent_snapshots"]) == 5
        assert "summary" in report_data
    
    @pytest.mark.asyncio
    async def test_save_report_error_handling(self, monitor):
        """Test error handling in report saving"""
        # Make storage path read-only to cause write error
        monitor.storage_path.chmod(0o444)
        
        try:
            # Should not raise exception, just log error
            await monitor._save_report()
        except Exception as e:
            pytest.fail(f"save_report should not raise exception: {e}")
        finally:
            # Restore permissions
            monitor.storage_path.chmod(0o755)
    
    def test_generate_summary_empty(self, monitor):
        """Test summary generation with empty snapshots"""
        summary = monitor._generate_summary()
        assert summary == {}
    
    def test_generate_summary_with_data(self, monitor, sample_snapshot):
        """Test summary generation with snapshot data"""
        # Add multiple snapshots with different values
        snapshots = []
        for i in range(5):
            snapshot = PerformanceSnapshot(
                timestamp=datetime.utcnow(),
                cpu_usage=10.0 + i * 10,  # 10, 20, 30, 40, 50
                memory_usage=20.0 + i * 5,  # 20, 25, 30, 35, 40
                disk_usage=30.0 + i * 2,  # 30, 32, 34, 36, 38
                network_io={},
                active_processes=100,
                system_load=[],
                workflow_state=f"state_{i}"
            )
            snapshots.append(snapshot)
        
        monitor.snapshots = snapshots
        summary = monitor._generate_summary()
        
        # Check CPU stats
        assert summary["cpu_usage"]["avg"] == 30.0  # (10+20+30+40+50)/5
        assert summary["cpu_usage"]["max"] == 50.0
        assert summary["cpu_usage"]["min"] == 10.0
        
        # Check memory stats
        assert summary["memory_usage"]["avg"] == 30.0  # (20+25+30+35+40)/5
        assert summary["memory_usage"]["max"] == 40.0
        assert summary["memory_usage"]["min"] == 20.0
        
        # Check disk stats
        assert summary["disk_usage"]["avg"] == 34.0  # (30+32+34+36+38)/5
        assert summary["disk_usage"]["max"] == 38.0
        assert summary["disk_usage"]["min"] == 30.0
        
        # Check alerts
        assert summary["alerts_triggered"] == 0  # No alerts triggered yet
        
        # Check workflow states
        state_dist = summary["workflow_states"]
        assert len(state_dist) == 5
        for i in range(5):
            assert state_dist[f"state_{i}"] == 1
    
    def test_get_state_distribution(self, monitor):
        """Test workflow state distribution calculation"""
        # Create snapshots with different states
        snapshots = [
            PerformanceSnapshot(
                timestamp=datetime.utcnow(),
                cpu_usage=10, memory_usage=20, disk_usage=30,
                network_io={}, active_processes=100, system_load=[],
                workflow_state="idle"
            ),
            PerformanceSnapshot(
                timestamp=datetime.utcnow(),
                cpu_usage=10, memory_usage=20, disk_usage=30,
                network_io={}, active_processes=100, system_load=[],
                workflow_state="processing"
            ),
            PerformanceSnapshot(
                timestamp=datetime.utcnow(),
                cpu_usage=10, memory_usage=20, disk_usage=30,
                network_io={}, active_processes=100, system_load=[],
                workflow_state="idle"
            ),
            PerformanceSnapshot(
                timestamp=datetime.utcnow(),
                cpu_usage=10, memory_usage=20, disk_usage=30,
                network_io={}, active_processes=100, system_load=[],
                workflow_state=None  # Should be ignored
            )
        ]
        
        monitor.snapshots = snapshots
        state_dist = monitor._get_state_distribution()
        
        assert state_dist["idle"] == 2
        assert state_dist["processing"] == 1
        assert len(state_dist) == 2  # None state not counted


class TestContinuousMonitoring:
    """Test continuous monitoring functionality"""
    
    @pytest.mark.asyncio
    async def test_start_monitoring_collection_cycle(self, monitor):
        """Test one collection cycle of monitoring"""
        # Mock the metrics collection
        with patch.object(monitor, '_collect_metrics') as mock_collect, \
             patch.object(monitor, '_check_performance_alerts') as mock_check_alerts, \
             patch.object(monitor, '_save_report') as mock_save_report, \
             patch('asyncio.sleep') as mock_sleep:
            
            # Setup mock to return a sample snapshot
            sample_snapshot = PerformanceSnapshot(
                timestamp=datetime.utcnow(),
                cpu_usage=25.0, memory_usage=30.0, disk_usage=40.0,
                network_io={}, active_processes=100, system_load=[]
            )
            mock_collect.return_value = sample_snapshot
            
            # Make sleep raise an exception to break the loop after one iteration
            mock_sleep.side_effect = KeyboardInterrupt()
            
            try:
                await monitor.start_monitoring()
            except KeyboardInterrupt:
                pass
            
            # Verify the monitoring cycle
            mock_collect.assert_called_once()
            mock_check_alerts.assert_called_once_with(sample_snapshot)
            assert len(monitor.snapshots) == 1
            assert monitor.snapshots[0] == sample_snapshot
    
    @pytest.mark.asyncio
    async def test_start_monitoring_max_snapshots_limit(self, monitor):
        """Test that monitoring respects max snapshots limit"""
        # Set a low max snapshots limit for testing
        monitor.max_snapshots = 3
        
        # Mock metrics collection to return different snapshots
        snapshots = []
        for i in range(5):
            snapshot = PerformanceSnapshot(
                timestamp=datetime.utcnow(),
                cpu_usage=10.0 + i, memory_usage=20.0 + i, disk_usage=30.0 + i,
                network_io={}, active_processes=100, system_load=[]
            )
            snapshots.append(snapshot)
        
        with patch.object(monitor, '_collect_metrics') as mock_collect, \
             patch.object(monitor, '_check_performance_alerts'), \
             patch.object(monitor, '_save_report'), \
             patch('asyncio.sleep') as mock_sleep:
            
            mock_collect.side_effect = snapshots
            
            # Simulate 5 collection cycles
            sleep_count = 0
            def sleep_side_effect(duration):
                nonlocal sleep_count
                sleep_count += 1
                if sleep_count >= 5:
                    raise KeyboardInterrupt()
            
            mock_sleep.side_effect = sleep_side_effect
            
            try:
                await monitor.start_monitoring()
            except KeyboardInterrupt:
                pass
            
            # Should only keep the last 3 snapshots
            assert len(monitor.snapshots) == 3
            assert monitor.snapshots[0].cpu_usage == 12.0  # Last 3: indices 2, 3, 4
            assert monitor.snapshots[1].cpu_usage == 13.0
            assert monitor.snapshots[2].cpu_usage == 14.0
    
    @pytest.mark.asyncio
    async def test_start_monitoring_periodic_reports(self, monitor):
        """Test periodic report generation during monitoring"""
        with patch.object(monitor, '_collect_metrics') as mock_collect, \
             patch.object(monitor, '_check_performance_alerts'), \
             patch.object(monitor, '_save_report') as mock_save_report, \
             patch('asyncio.sleep') as mock_sleep:
            
            # Create mock snapshots
            sample_snapshot = PerformanceSnapshot(
                timestamp=datetime.utcnow(),
                cpu_usage=25.0, memory_usage=30.0, disk_usage=40.0,
                network_io={}, active_processes=100, system_load=[]
            )
            mock_collect.return_value = sample_snapshot
            
            # Simulate 12 collection cycles (should trigger report on 10th)
            sleep_count = 0
            def sleep_side_effect(duration):
                nonlocal sleep_count
                sleep_count += 1
                if sleep_count >= 12:
                    raise KeyboardInterrupt()
            
            mock_sleep.side_effect = sleep_side_effect
            
            try:
                await monitor.start_monitoring()
            except KeyboardInterrupt:
                pass
            
            # Should have called save_report once (at 10th snapshot)
            mock_save_report.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_start_monitoring_error_handling(self, monitor):
        """Test error handling during monitoring"""
        with patch.object(monitor, '_collect_metrics') as mock_collect, \
             patch('asyncio.sleep') as mock_sleep:
            
            # Make collect_metrics raise an exception
            mock_collect.side_effect = Exception("Collection error")
            
            # Make sleep raise KeyboardInterrupt after first error
            sleep_count = 0
            def sleep_side_effect(duration):
                nonlocal sleep_count
                sleep_count += 1
                if sleep_count >= 2:  # Sleep twice (normal interval + error interval)
                    raise KeyboardInterrupt()
            
            mock_sleep.side_effect = sleep_side_effect
            
            try:
                await monitor.start_monitoring()
            except KeyboardInterrupt:
                pass
            
            # Should have attempted collection and handled the error
            # Due to retry logic, might be called more than once
            assert mock_collect.call_count >= 1
            # Should have slept at least once for error recovery
            assert mock_sleep.call_count >= 1
            # Error sleep should be double the normal interval
            error_sleep_call = mock_sleep.call_args_list[0]
            assert error_sleep_call[0][0] == monitor.collection_interval * 2


class TestStatusAndInformation:
    """Test status and information methods"""
    
    def test_get_current_status_no_data(self, monitor):
        """Test status when no snapshots collected"""
        status = monitor.get_current_status()
        
        assert status["status"] == "no_data"
    
    def test_get_current_status_single_snapshot(self, monitor, sample_snapshot):
        """Test status with single snapshot"""
        monitor.snapshots = [sample_snapshot]
        
        status = monitor.get_current_status()
        
        assert status["status"] == "monitoring"
        assert status["snapshots_collected"] == 1
        assert status["monitoring_duration_minutes"] == 0
        assert "latest_snapshot" in status
        assert "summary" in status
        assert status["latest_snapshot"]["cpu_usage"] == sample_snapshot.cpu_usage
    
    def test_get_current_status_multiple_snapshots(self, monitor, sample_snapshot):
        """Test status with multiple snapshots"""
        # Create snapshots with time differences
        start_time = datetime.utcnow()
        end_time = start_time + timedelta(minutes=30)
        
        snapshot1 = PerformanceSnapshot(
            timestamp=start_time,
            cpu_usage=10, memory_usage=20, disk_usage=30,
            network_io={}, active_processes=100, system_load=[]
        )
        snapshot2 = PerformanceSnapshot(
            timestamp=end_time,
            cpu_usage=20, memory_usage=30, disk_usage=40,
            network_io={}, active_processes=110, system_load=[]
        )
        
        monitor.snapshots = [snapshot1, snapshot2]
        
        status = monitor.get_current_status()
        
        assert status["status"] == "monitoring"
        assert status["snapshots_collected"] == 2
        assert status["monitoring_duration_minutes"] == 30.0
        assert status["latest_snapshot"]["cpu_usage"] == 20  # Latest snapshot


class TestEdgeCasesAndErrorConditions:
    """Test edge cases and error conditions"""
    
    @pytest.mark.asyncio
    async def test_metrics_collection_with_missing_psutil_functions(self, monitor):
        """Test metrics collection when some psutil functions are missing"""
        with patch('tools.monitoring.performance_monitor.psutil.cpu_percent', side_effect=AttributeError()), \
             patch('tools.monitoring.performance_monitor.psutil.virtual_memory', side_effect=AttributeError()), \
             patch('tools.monitoring.performance_monitor.psutil.disk_usage', side_effect=OSError()), \
             patch('tools.monitoring.performance_monitor.psutil.net_io_counters', side_effect=AttributeError()), \
             patch('tools.monitoring.performance_monitor.psutil.pids', return_value=[1, 2, 3]):
            
            # Should handle errors gracefully
            try:
                with patch.object(monitor, '_collect_app_metrics', return_value={}):
                    await monitor._collect_metrics()
                pytest.fail("Should have raised an exception")
            except (AttributeError, OSError):
                pass  # Expected
    
    @pytest.mark.asyncio
    async def test_app_metrics_with_invalid_json(self, monitor):
        """Test app metrics collection with invalid JSON response"""
        with patch('tools.monitoring.performance_monitor.requests.get') as mock_get:
            # Mock response that raises JSON decode error
            response = Mock()
            response.status_code = 200
            response.json.side_effect = json.JSONDecodeError("Invalid JSON", "", 0)
            mock_get.return_value = response
            
            app_metrics = await monitor._collect_app_metrics()
            
            assert app_metrics == {}
    
    @pytest.mark.asyncio
    async def test_app_metrics_with_timeout(self, monitor):
        """Test app metrics collection with timeout"""
        import requests
        with patch('tools.monitoring.performance_monitor.requests.get') as mock_get:
            mock_get.side_effect = requests.Timeout("Request timeout")
            
            app_metrics = await monitor._collect_app_metrics()
            
            assert app_metrics == {}
    
    def test_snapshot_with_none_values(self):
        """Test snapshot creation with None values"""
        snapshot = PerformanceSnapshot(
            timestamp=datetime.utcnow(),
            cpu_usage=None,  # Invalid but should be handled
            memory_usage=50.0,
            disk_usage=60.0,
            network_io=None,
            active_processes=100,
            system_load=None
        )
        
        # Should not raise an exception
        assert snapshot.timestamp is not None
        assert snapshot.cpu_usage is None
    
    @pytest.mark.asyncio
    async def test_report_generation_with_filesystem_errors(self, monitor, sample_snapshot):
        """Test report generation with filesystem errors"""
        monitor.snapshots = [sample_snapshot]
        
        # Mock open to raise permission error
        with patch('builtins.open', side_effect=PermissionError("Access denied")):
            # Should not raise exception, just log error
            await monitor._save_report()
    
    def test_summary_generation_with_empty_quantiles(self, monitor):
        """Test summary generation when not enough data for quantiles"""
        # Create just one snapshot (not enough for quantiles)
        snapshot = PerformanceSnapshot(
            timestamp=datetime.utcnow(),
            cpu_usage=50.0, memory_usage=60.0, disk_usage=70.0,
            network_io={}, active_processes=100, system_load=[]
        )
        monitor.snapshots = [snapshot]
        
        summary = monitor._generate_summary()
        
        # Should use max value when not enough data for quantiles
        assert summary["cpu_usage"]["avg"] == 50.0
        assert summary["cpu_usage"]["max"] == 50.0
        assert summary["cpu_usage"]["min"] == 50.0
        assert summary["cpu_usage"]["p95"] == 50.0  # Falls back to max
    
    @pytest.mark.asyncio
    async def test_alert_with_edge_case_values(self, monitor):
        """Test alert system with edge case values"""
        snapshot = PerformanceSnapshot(
            timestamp=datetime.utcnow(),
            cpu_usage=float('inf'),  # Edge case value
            memory_usage=-5.0,  # Invalid value
            disk_usage=101.0,  # Over 100%
            network_io={}, active_processes=100, system_load=[],
            response_times={"test": float('nan')}  # NaN value
        )
        
        # Should handle edge cases without crashing
        with patch.object(monitor, '_send_alert') as mock_send_alert:
            await monitor._check_performance_alerts(snapshot)
        
        # Should still call alerts for the values that trigger thresholds
        assert mock_send_alert.call_count >= 1


class TestCommandLineInterface:
    """Test command line interface functionality"""
    
    @patch('tools.monitoring.performance_monitor.PerformanceMonitor')
    @patch('tools.monitoring.performance_monitor.asyncio.run')
    @pytest.mark.asyncio
    async def test_main_default_args(self, mock_asyncio_run, mock_monitor_class):
        """Test main function with default arguments"""
        from tools.monitoring.performance_monitor import main
        
        # Mock sys.argv
        with patch('sys.argv', ['performance_monitor.py']):
            await main()
        
        # Verify monitor was created with defaults
        mock_monitor_class.assert_called_once_with(
            collection_interval=30,
            storage_path='.orch-monitoring',
            visualizer_url='http://localhost:5000'
        )
    
    @patch('tools.monitoring.performance_monitor.PerformanceMonitor')
    @patch('tools.monitoring.performance_monitor.asyncio.run')
    @pytest.mark.asyncio
    async def test_main_custom_args(self, mock_asyncio_run, mock_monitor_class):
        """Test main function with custom arguments"""
        from tools.monitoring.performance_monitor import main
        
        # Mock sys.argv with custom arguments
        with patch('sys.argv', [
            'performance_monitor.py',
            '--interval', '15',
            '--visualizer-url', 'http://custom:8080',
            '--storage-path', '/custom/path'
        ]):
            await main()
        
        # Verify monitor was created with custom values
        mock_monitor_class.assert_called_once_with(
            collection_interval=15,
            storage_path='/custom/path',
            visualizer_url='http://custom:8080'
        )
    
    @patch('tools.monitoring.performance_monitor.PerformanceMonitor')
    @patch('tools.monitoring.performance_monitor.print')
    @patch('tools.monitoring.performance_monitor.json.dumps')
    @pytest.mark.asyncio
    async def test_main_report_only_mode(self, mock_json_dumps, mock_print, mock_monitor_class):
        """Test main function in report-only mode"""
        from tools.monitoring.performance_monitor import main
        
        # Setup mock monitor instance
        mock_monitor = Mock()
        mock_status = {"status": "test", "data": "example"}
        mock_monitor.get_current_status.return_value = mock_status
        mock_monitor_class.return_value = mock_monitor
        
        mock_json_dumps.return_value = '{"status": "test"}'
        
        # Mock sys.argv with report-only flag
        with patch('sys.argv', ['performance_monitor.py', '--report-only']):
            await main()
        
        # Verify report was generated and printed
        mock_monitor.get_current_status.assert_called_once()
        mock_json_dumps.assert_called_once_with(mock_status, indent=2, default=str)
        mock_print.assert_called_once_with('{"status": "test"}')
    
    @patch('tools.monitoring.performance_monitor.PerformanceMonitor')
    @patch('tools.monitoring.performance_monitor.asyncio.run')
    @pytest.mark.asyncio
    async def test_main_keyboard_interrupt(self, mock_asyncio_run, mock_monitor_class):
        """Test main function handling KeyboardInterrupt"""
        from tools.monitoring.performance_monitor import main
        
        # Setup mock monitor to raise KeyboardInterrupt
        mock_monitor = Mock()
        mock_monitor.start_monitoring.side_effect = KeyboardInterrupt()
        mock_monitor_class.return_value = mock_monitor
        
        with patch('sys.argv', ['performance_monitor.py']):
            # Should not raise exception
            await main()
    
    @patch('tools.monitoring.performance_monitor.PerformanceMonitor')
    @patch('tools.monitoring.performance_monitor.asyncio.run')
    @pytest.mark.asyncio
    async def test_main_general_exception(self, mock_asyncio_run, mock_monitor_class):
        """Test main function handling general exception"""
        from tools.monitoring.performance_monitor import main
        
        # Setup mock monitor to raise general exception
        mock_monitor = Mock()
        mock_monitor.start_monitoring.side_effect = Exception("Test error")
        mock_monitor_class.return_value = mock_monitor
        
        with patch('sys.argv', ['performance_monitor.py']):
            # Should not raise exception
            await main()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])