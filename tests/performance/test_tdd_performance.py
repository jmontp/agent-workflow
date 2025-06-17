#!/usr/bin/env python3
"""
Performance Testing Suite for TDD Implementation.

This module provides comprehensive performance validation including:
- TDD cycle performance timing
- Agent response time validation
- Storage operation performance
- Memory usage monitoring
- Concurrent load testing
- Performance regression detection
"""

import asyncio
import time
import psutil
import gc
import statistics
from pathlib import Path
from typing import Dict, List, Any, Optional
from unittest.mock import AsyncMock, Mock
import pytest
import sys
import tempfile
import shutil

# Add project paths to sys.path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "lib"))
sys.path.insert(0, str(project_root / "scripts"))

from orchestrator import Orchestrator
from data_models import Epic, Story
from tdd_models import TDDCycle, TestResult, TestStatus
from project_storage import ProjectStorage


class PerformanceMonitor:
    """Performance monitoring and metrics collection"""
    
    def __init__(self):
        self.metrics: Dict[str, Any] = {}
        self.start_time: Optional[float] = None
        self.start_memory: Optional[float] = None
        
    def start_monitoring(self, test_name: str):
        """Start performance monitoring for a test"""
        self.start_time = time.time()
        self.start_memory = self._get_memory_usage()
        self.metrics[test_name] = {
            "start_time": self.start_time,
            "start_memory": self.start_memory,
            "operations": [],
            "checkpoints": []
        }
        
    def checkpoint(self, test_name: str, operation: str):
        """Record a performance checkpoint"""
        if test_name in self.metrics:
            now = time.time()
            memory = self._get_memory_usage()
            self.metrics[test_name]["checkpoints"].append({
                "operation": operation,
                "timestamp": now,
                "memory": memory,
                "elapsed": now - self.metrics[test_name]["start_time"]
            })
    
    def record_operation(self, test_name: str, operation: str, duration: float, **kwargs):
        """Record a specific operation's performance"""
        if test_name in self.metrics:
            self.metrics[test_name]["operations"].append({
                "operation": operation,
                "duration": duration,
                "timestamp": time.time(),
                **kwargs
            })
    
    def end_monitoring(self, test_name: str) -> Dict[str, Any]:
        """End monitoring and return comprehensive metrics"""
        if test_name not in self.metrics:
            return {}
            
        end_time = time.time()
        end_memory = self._get_memory_usage()
        
        metrics = self.metrics[test_name]
        metrics.update({
            "end_time": end_time,
            "end_memory": end_memory,
            "total_duration": end_time - metrics["start_time"],
            "memory_delta": end_memory - metrics["start_memory"],
            "peak_memory": max(cp["memory"] for cp in metrics["checkpoints"]) if metrics["checkpoints"] else end_memory
        })
        
        return metrics
    
    def _get_memory_usage(self) -> float:
        """Get current memory usage in MB"""
        try:
            process = psutil.Process()
            return process.memory_info().rss / 1024 / 1024
        except Exception:
            return 0.0


class TDDPerformanceTest:
    """TDD-specific performance testing"""
    
    def __init__(self):
        self.monitor = PerformanceMonitor()
        self.orchestrator = None
        self.temp_dirs: List[Path] = []
        
    async def setup_test_environment(self) -> Path:
        """Set up isolated test environment"""
        temp_dir = tempfile.mkdtemp()
        test_path = Path(temp_dir)
        self.temp_dirs.append(test_path)
        
        self.orchestrator = Orchestrator()
        return test_path
    
    def cleanup(self):
        """Clean up test resources"""
        for temp_dir in self.temp_dirs:
            shutil.rmtree(temp_dir, ignore_errors=True)
        self.temp_dirs.clear()
        
        # Force garbage collection
        gc.collect()
    
    async def test_tdd_cycle_performance(self) -> Dict[str, Any]:
        """Test complete TDD cycle performance"""
        test_name = "tdd_cycle_performance"
        self.monitor.start_monitoring(test_name)
        
        try:
            await self.setup_test_environment()
            self.monitor.checkpoint(test_name, "environment_setup")
            
            # Create epic
            start_time = time.time()
            epic_result = await self.orchestrator.handle_command(
                "/epic", "default",
                description="Performance test epic",
                title="Perf Test Epic"
            )
            epic_duration = time.time() - start_time
            self.monitor.record_operation(test_name, "epic_creation", epic_duration)
            self.monitor.checkpoint(test_name, "epic_created")
            
            if not epic_result["success"]:
                return {"success": False, "error": "Epic creation failed"}
            
            epic_id = epic_result["epic_id"]
            
            # Create story
            start_time = time.time()
            story_result = await self.orchestrator.handle_command(
                "/backlog add_story", "default",
                description="Performance test story",
                feature=epic_id
            )
            story_duration = time.time() - start_time
            self.monitor.record_operation(test_name, "story_creation", story_duration)
            self.monitor.checkpoint(test_name, "story_created")
            
            if not story_result["success"]:
                return {"success": False, "error": "Story creation failed"}
            
            story_id = story_result["story_id"]
            
            # Start TDD cycle
            start_time = time.time()
            tdd_result = await self.orchestrator.handle_command(
                "/tdd start", "default",
                story_id=story_id,
                task_description="Performance test implementation"
            )
            tdd_start_duration = time.time() - start_time
            self.monitor.record_operation(test_name, "tdd_start", tdd_start_duration)
            self.monitor.checkpoint(test_name, "tdd_started")
            
            if not tdd_result["success"]:
                return {"success": False, "error": "TDD start failed"}
            
            cycle_id = tdd_result["cycle_id"]
            
            # Execute TDD phases
            phases = ["design", "test", "code", "refactor", "commit"]
            for phase in phases:
                start_time = time.time()
                
                # Add test simulation for appropriate phases
                if phase == "test":
                    await self._simulate_test_phase(cycle_id)
                elif phase == "code":
                    await self._simulate_code_phase(cycle_id)
                
                phase_result = await self.orchestrator.handle_command(f"/tdd {phase}", "default")
                phase_duration = time.time() - start_time
                
                self.monitor.record_operation(test_name, f"tdd_{phase}", phase_duration)
                self.monitor.checkpoint(test_name, f"tdd_{phase}_completed")
                
                if not phase_result["success"]:
                    return {"success": False, "error": f"TDD {phase} failed"}
            
            # Get final metrics
            performance_data = self.monitor.end_monitoring(test_name)
            
            return {
                "success": True,
                "performance": performance_data,
                "cycle_id": cycle_id,
                "operations_count": len(performance_data["operations"])
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def test_agent_response_times(self) -> Dict[str, Any]:
        """Test agent response time performance"""
        test_name = "agent_response_times"
        self.monitor.start_monitoring(test_name)
        
        try:
            await self.setup_test_environment()
            
            # Test multiple agent operations
            operations = [
                ("/epic", {"description": "Agent response test", "title": "Response Test"}),
                ("/backlog add_story", {"description": "Response test story", "feature": None}),
                ("/state", {}),
                ("/tdd status", {})
            ]
            
            response_times = []
            
            for i, (command, params) in enumerate(operations):
                start_time = time.time()
                
                # Adjust parameters for story creation
                if command == "/backlog add_story" and i > 0:
                    # Get epic from previous operation
                    params["feature"] = "test-epic-id"
                
                try:
                    result = await self.orchestrator.handle_command(command, "default", **params)
                    response_time = time.time() - start_time
                    response_times.append(response_time)
                    
                    self.monitor.record_operation(
                        test_name, 
                        f"command_{command.replace('/', '')}", 
                        response_time,
                        success=result.get("success", False)
                    )
                    
                except Exception as e:
                    response_time = time.time() - start_time
                    response_times.append(response_time)
                    self.monitor.record_operation(
                        test_name, 
                        f"command_{command.replace('/', '')}_error", 
                        response_time,
                        error=str(e)
                    )
            
            performance_data = self.monitor.end_monitoring(test_name)
            
            return {
                "success": True,
                "performance": performance_data,
                "response_times": response_times,
                "avg_response_time": statistics.mean(response_times),
                "max_response_time": max(response_times),
                "min_response_time": min(response_times)
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def test_storage_performance(self) -> Dict[str, Any]:
        """Test storage operation performance"""
        test_name = "storage_performance"
        self.monitor.start_monitoring(test_name)
        
        try:
            test_path = await self.setup_test_environment()
            storage = ProjectStorage(test_path / "test_project")
            
            # Test multiple storage operations
            storage_operations = []
            
            # Test TDD cycle save/load performance
            for i in range(10):
                # Create test TDD cycle
                cycle = TDDCycle(
                    story_id=f"story-{i}",
                    task_description=f"Test task {i}"
                )
                
                # Test save operation
                start_time = time.time()
                storage.save_tdd_cycle(cycle)
                save_duration = time.time() - start_time
                storage_operations.append(save_duration)
                self.monitor.record_operation(test_name, f"tdd_save_{i}", save_duration)
                
                # Test load operation
                start_time = time.time()
                loaded_cycle = storage.get_tdd_cycle(cycle.cycle_id)
                load_duration = time.time() - start_time
                storage_operations.append(load_duration)
                self.monitor.record_operation(test_name, f"tdd_load_{i}", load_duration)
                
                # Verify data integrity
                assert loaded_cycle is not None
                assert loaded_cycle.story_id == cycle.story_id
            
            performance_data = self.monitor.end_monitoring(test_name)
            
            return {
                "success": True,
                "performance": performance_data,
                "storage_operations": len(storage_operations),
                "avg_operation_time": statistics.mean(storage_operations),
                "max_operation_time": max(storage_operations),
                "min_operation_time": min(storage_operations)
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def test_memory_usage_patterns(self) -> Dict[str, Any]:
        """Test memory usage patterns during TDD operations"""
        test_name = "memory_usage_patterns"
        self.monitor.start_monitoring(test_name)
        
        try:
            await self.setup_test_environment()
            
            # Run multiple TDD cycles to test memory patterns
            memory_samples = []
            
            for cycle_num in range(5):
                self.monitor.checkpoint(test_name, f"cycle_{cycle_num}_start")
                
                # Create epic and story
                epic_result = await self.orchestrator.handle_command(
                    "/epic", "default",
                    description=f"Memory test epic {cycle_num}",
                    title=f"Memory Epic {cycle_num}"
                )
                
                if epic_result["success"]:
                    story_result = await self.orchestrator.handle_command(
                        "/backlog add_story", "default",
                        description=f"Memory test story {cycle_num}",
                        feature=epic_result["epic_id"]
                    )
                    
                    if story_result["success"]:
                        # Start and complete TDD cycle
                        tdd_result = await self.orchestrator.handle_command(
                            "/tdd start", "default",
                            story_id=story_result["story_id"],
                            task_description=f"Memory test task {cycle_num}"
                        )
                        
                        if tdd_result["success"]:
                            # Complete basic TDD phases
                            for phase in ["design", "test", "code"]:
                                await self.orchestrator.handle_command(f"/tdd {phase}", "default")
                                memory_samples.append(self._get_current_memory())
                
                self.monitor.checkpoint(test_name, f"cycle_{cycle_num}_end")
                
                # Force garbage collection
                gc.collect()
            
            performance_data = self.monitor.end_monitoring(test_name)
            
            return {
                "success": True,
                "performance": performance_data,
                "memory_samples": memory_samples,
                "memory_growth": memory_samples[-1] - memory_samples[0] if memory_samples else 0,
                "peak_memory": max(memory_samples) if memory_samples else 0
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def test_concurrent_load(self) -> Dict[str, Any]:
        """Test system behavior under concurrent TDD operations"""
        test_name = "concurrent_load"
        self.monitor.start_monitoring(test_name)
        
        try:
            await self.setup_test_environment()
            
            # Create multiple concurrent TDD workflows
            concurrent_tasks = []
            num_concurrent = 3  # Moderate concurrency for testing
            
            for i in range(num_concurrent):
                task = self._run_concurrent_tdd_workflow(i)
                concurrent_tasks.append(task)
            
            # Run all tasks concurrently
            start_time = time.time()
            results = await asyncio.gather(*concurrent_tasks, return_exceptions=True)
            total_duration = time.time() - start_time
            
            # Analyze results
            successful_tasks = sum(1 for r in results if isinstance(r, dict) and r.get("success"))
            failed_tasks = len(results) - successful_tasks
            
            performance_data = self.monitor.end_monitoring(test_name)
            
            return {
                "success": successful_tasks > 0,
                "performance": performance_data,
                "concurrent_tasks": num_concurrent,
                "successful_tasks": successful_tasks,
                "failed_tasks": failed_tasks,
                "total_duration": total_duration,
                "avg_task_duration": total_duration / num_concurrent
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def _run_concurrent_tdd_workflow(self, task_id: int) -> Dict[str, Any]:
        """Run a single TDD workflow for concurrent testing"""
        try:
            # Create unique epic and story
            epic_result = await self.orchestrator.handle_command(
                "/epic", "default",
                description=f"Concurrent test epic {task_id}",
                title=f"Concurrent Epic {task_id}"
            )
            
            if not epic_result["success"]:
                return {"success": False, "error": "Epic creation failed", "task_id": task_id}
            
            story_result = await self.orchestrator.handle_command(
                "/backlog add_story", "default",
                description=f"Concurrent test story {task_id}",
                feature=epic_result["epic_id"]
            )
            
            if not story_result["success"]:
                return {"success": False, "error": "Story creation failed", "task_id": task_id}
            
            # Start TDD cycle
            tdd_result = await self.orchestrator.handle_command(
                "/tdd start", "default",
                story_id=story_result["story_id"],
                task_description=f"Concurrent task {task_id}"
            )
            
            if not tdd_result["success"]:
                return {"success": False, "error": "TDD start failed", "task_id": task_id}
            
            return {"success": True, "task_id": task_id, "cycle_id": tdd_result["cycle_id"]}
            
        except Exception as e:
            return {"success": False, "error": str(e), "task_id": task_id}
    
    async def _simulate_test_phase(self, cycle_id: str):
        """Simulate test phase for performance testing"""
        try:
            project = self.orchestrator.projects["default"]
            active_cycle = project.storage.get_active_tdd_cycle()
            
            if active_cycle and active_cycle.get_current_task():
                test_result = TestResult(
                    test_file="test_performance.py",
                    test_name="test_performance_feature",
                    status=TestStatus.RED,
                    output="Performance test simulation"
                )
                active_cycle.get_current_task().test_results.append(test_result)
                project.storage.save_tdd_cycle(active_cycle)
        except Exception:
            pass  # Ignore simulation errors
    
    async def _simulate_code_phase(self, cycle_id: str):
        """Simulate code phase for performance testing"""
        try:
            project = self.orchestrator.projects["default"]
            active_cycle = project.storage.get_active_tdd_cycle()
            
            if active_cycle and active_cycle.get_current_task():
                test_result = TestResult(
                    test_file="test_performance.py",
                    test_name="test_performance_feature",
                    status=TestStatus.GREEN,
                    output="Performance test passed"
                )
                active_cycle.get_current_task().test_results.append(test_result)
                project.storage.save_tdd_cycle(active_cycle)
        except Exception:
            pass  # Ignore simulation errors
    
    def _get_current_memory(self) -> float:
        """Get current memory usage"""
        try:
            process = psutil.Process()
            return process.memory_info().rss / 1024 / 1024
        except Exception:
            return 0.0


class PerformanceBenchmark:
    """Performance benchmarking and validation"""
    
    # Performance targets
    PERFORMANCE_TARGETS = {
        "tdd_cycle_time": 300,  # 5 minutes max
        "agent_response_time": 30,  # 30 seconds max
        "storage_operation_time": 1,  # 1 second max
        "memory_usage_mb": 500,  # 500MB max
        "concurrent_tasks": 3,  # Minimum concurrent tasks
    }
    
    def __init__(self):
        self.test_suite = TDDPerformanceTest()
        self.results: Dict[str, Any] = {}
    
    async def run_performance_benchmark(self) -> Dict[str, Any]:
        """Run complete performance benchmark suite"""
        print("Running TDD Performance Benchmark Suite...")
        
        try:
            # Test 1: TDD Cycle Performance
            print("1. Testing TDD cycle performance...")
            cycle_result = await self.test_suite.test_tdd_cycle_performance()
            self.results["tdd_cycle"] = cycle_result
            self._validate_cycle_performance(cycle_result)
            
            # Test 2: Agent Response Times
            print("2. Testing agent response times...")
            response_result = await self.test_suite.test_agent_response_times()
            self.results["agent_response"] = response_result
            self._validate_response_performance(response_result)
            
            # Test 3: Storage Performance
            print("3. Testing storage performance...")
            storage_result = await self.test_suite.test_storage_performance()
            self.results["storage"] = storage_result
            self._validate_storage_performance(storage_result)
            
            # Test 4: Memory Usage
            print("4. Testing memory usage patterns...")
            memory_result = await self.test_suite.test_memory_usage_patterns()
            self.results["memory"] = memory_result
            self._validate_memory_performance(memory_result)
            
            # Test 5: Concurrent Load
            print("5. Testing concurrent load...")
            concurrent_result = await self.test_suite.test_concurrent_load()
            self.results["concurrent"] = concurrent_result
            self._validate_concurrent_performance(concurrent_result)
            
            # Generate overall assessment
            overall_success = all(
                result.get("success", False) for result in self.results.values()
            )
            
            return {
                "success": overall_success,
                "results": self.results,
                "performance_report": self._generate_performance_report()
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
        finally:
            self.test_suite.cleanup()
    
    def _validate_cycle_performance(self, result: Dict[str, Any]):
        """Validate TDD cycle performance against targets"""
        if result.get("success") and "performance" in result:
            performance = result["performance"]
            total_duration = performance.get("total_duration", 0)
            
            result["performance_check"] = {
                "meets_time_target": total_duration <= self.PERFORMANCE_TARGETS["tdd_cycle_time"],
                "actual_duration": total_duration,
                "target_duration": self.PERFORMANCE_TARGETS["tdd_cycle_time"]
            }
    
    def _validate_response_performance(self, result: Dict[str, Any]):
        """Validate agent response performance against targets"""
        if result.get("success") and "avg_response_time" in result:
            avg_response = result["avg_response_time"]
            max_response = result["max_response_time"]
            
            result["performance_check"] = {
                "meets_avg_target": avg_response <= self.PERFORMANCE_TARGETS["agent_response_time"],
                "meets_max_target": max_response <= self.PERFORMANCE_TARGETS["agent_response_time"] * 2,
                "actual_avg": avg_response,
                "actual_max": max_response,
                "target": self.PERFORMANCE_TARGETS["agent_response_time"]
            }
    
    def _validate_storage_performance(self, result: Dict[str, Any]):
        """Validate storage performance against targets"""
        if result.get("success") and "avg_operation_time" in result:
            avg_operation = result["avg_operation_time"]
            max_operation = result["max_operation_time"]
            
            result["performance_check"] = {
                "meets_avg_target": avg_operation <= self.PERFORMANCE_TARGETS["storage_operation_time"],
                "meets_max_target": max_operation <= self.PERFORMANCE_TARGETS["storage_operation_time"] * 2,
                "actual_avg": avg_operation,
                "actual_max": max_operation,
                "target": self.PERFORMANCE_TARGETS["storage_operation_time"]
            }
    
    def _validate_memory_performance(self, result: Dict[str, Any]):
        """Validate memory performance against targets"""
        if result.get("success") and "peak_memory" in result:
            peak_memory = result["peak_memory"]
            
            result["performance_check"] = {
                "meets_memory_target": peak_memory <= self.PERFORMANCE_TARGETS["memory_usage_mb"],
                "actual_peak": peak_memory,
                "target": self.PERFORMANCE_TARGETS["memory_usage_mb"]
            }
    
    def _validate_concurrent_performance(self, result: Dict[str, Any]):
        """Validate concurrent performance against targets"""
        if result.get("success") and "successful_tasks" in result:
            successful_tasks = result["successful_tasks"]
            
            result["performance_check"] = {
                "meets_concurrent_target": successful_tasks >= self.PERFORMANCE_TARGETS["concurrent_tasks"],
                "actual_successful": successful_tasks,
                "target": self.PERFORMANCE_TARGETS["concurrent_tasks"]
            }
    
    def _generate_performance_report(self) -> Dict[str, Any]:
        """Generate comprehensive performance report"""
        report = {
            "summary": {},
            "recommendations": [],
            "performance_scores": {}
        }
        
        # Calculate performance scores
        for test_name, result in self.results.items():
            if result.get("success") and "performance_check" in result:
                check = result["performance_check"]
                
                # Simple scoring based on meeting targets
                score = 100
                for key, value in check.items():
                    if key.startswith("meets_") and not value:
                        score -= 20
                
                report["performance_scores"][test_name] = score
        
        # Overall score
        if report["performance_scores"]:
            report["overall_score"] = statistics.mean(report["performance_scores"].values())
        else:
            report["overall_score"] = 0
        
        # Generate recommendations
        if report["overall_score"] < 80:
            report["recommendations"].append("Performance optimization needed")
        if report["overall_score"] < 60:
            report["recommendations"].append("Critical performance issues detected")
        
        return report


# Test execution functions
async def test_tdd_cycle_performance():
    """Test TDD cycle performance"""
    benchmark = PerformanceBenchmark()
    return await benchmark.run_performance_benchmark()


async def main():
    """Run TDD performance tests"""
    print("="*60)
    print("TDD PERFORMANCE TEST SUITE")
    print("="*60)
    
    try:
        # Run performance benchmark
        result = await test_tdd_cycle_performance()
        
        if result["success"]:
            print("\n✅ ALL PERFORMANCE TESTS PASSED")
            
            # Print performance report
            if "performance_report" in result:
                report = result["performance_report"]
                print(f"\nOverall Performance Score: {report['overall_score']:.1f}/100")
                
                for test_name, score in report["performance_scores"].items():
                    print(f"  {test_name}: {score}/100")
                
                if report["recommendations"]:
                    print("\nRecommendations:")
                    for rec in report["recommendations"]:
                        print(f"  • {rec}")
            
            return 0
        else:
            print(f"\n❌ PERFORMANCE TESTS FAILED: {result.get('error', 'Unknown error')}")
            return 1
            
    except Exception as e:
        print(f"\n❌ PERFORMANCE TEST SUITE FAILED: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    import sys
    sys.exit(asyncio.run(main()))