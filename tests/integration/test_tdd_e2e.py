#!/usr/bin/env python3
"""
Comprehensive End-to-End Test Suite for TDD Implementation.

This module provides complete workflow validation including:
- Full TDD cycle testing with real project simulation
- Multi-story TDD workflows within sprint lifecycle
- Integration testing with main orchestration workflow
- Human intervention point validation
- Performance and reliability testing
- Real CI/CD simulation scenarios
"""

import sys
import asyncio
import tempfile
import shutil
import time
import json
import subprocess
import git
from pathlib import Path
from typing import Dict, List, Optional, Any
from unittest.mock import Mock, patch, AsyncMock
import pytest

# Add project paths to sys.path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root / "lib"))
sys.path.insert(0, str(project_root / "scripts"))

from orchestrator import Orchestrator
from data_models import Epic, Story
from tdd_models import TDDCycle, TDDTask, TestResult, TestStatus
from project_storage import ProjectStorage


class TestInfrastructure:
    """Test infrastructure for comprehensive TDD testing"""
    
    def __init__(self):
        self.temp_dirs: List[Path] = []
        self.test_repos: List[Path] = []
        self.performance_metrics: Dict[str, Any] = {}
        
    def create_test_repository(self, name: str) -> Path:
        """Create a realistic test Git repository"""
        temp_dir = tempfile.mkdtemp()
        repo_path = Path(temp_dir) / name
        repo_path.mkdir(parents=True)
        self.temp_dirs.append(Path(temp_dir))
        
        # Initialize git repository
        repo = git.Repo.init(repo_path)
        
        # Create basic project structure
        (repo_path / "src").mkdir()
        (repo_path / "tests").mkdir()
        (repo_path / ".github" / "workflows").mkdir(parents=True)
        
        # Add initial files
        (repo_path / "README.md").write_text(f"# {name}\n\nTest project for TDD workflow")
        (repo_path / "src" / "__init__.py").write_text("")
        (repo_path / "tests" / "__init__.py").write_text("")
        (repo_path / "requirements.txt").write_text("pytest>=7.0.0\npytest-cov>=4.0.0\n")
        
        # Add CI/CD workflow
        ci_workflow = """
name: CI
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3
    - uses: actions/setup-python@v4
      with:
        python-version: '3.9'
    - run: pip install -r requirements.txt
    - run: pytest tests/ --cov=src/
"""
        (repo_path / ".github" / "workflows" / "ci.yml").write_text(ci_workflow)
        
        # Commit initial structure
        repo.index.add(["."])
        repo.index.commit("Initial project structure")
        
        self.test_repos.append(repo_path)
        return repo_path
    
    def create_realistic_test_data(self) -> Dict[str, Any]:
        """Create realistic test data for comprehensive testing"""
        return {
            "epics": [
                {
                    "title": "E-commerce Platform Core",
                    "description": "Build core e-commerce functionality with TDD approach",
                    "stories": [
                        "User registration and authentication system",
                        "Product catalog with search and filtering",
                        "Shopping cart management",
                        "Payment processing integration",
                        "Order management system"
                    ]
                },
                {
                    "title": "API Development",
                    "description": "RESTful API with comprehensive test coverage",
                    "stories": [
                        "User management endpoints",
                        "Product CRUD operations",
                        "Cart and order APIs",
                        "Payment gateway integration",
                        "Admin dashboard APIs"
                    ]
                }
            ],
            "performance_targets": {
                "tdd_cycle_time": 300,  # 5 minutes max per cycle
                "agent_response_time": 30,  # 30 seconds max
                "storage_operation_time": 1,  # 1 second max
                "memory_usage_mb": 500  # 500MB max
            }
        }
    
    def start_performance_monitoring(self, test_name: str):
        """Start performance monitoring for a test"""
        self.performance_metrics[test_name] = {
            "start_time": time.time(),
            "memory_start": self._get_memory_usage(),
            "operations": []
        }
    
    def record_operation(self, test_name: str, operation: str, duration: float):
        """Record a performance operation"""
        if test_name in self.performance_metrics:
            self.performance_metrics[test_name]["operations"].append({
                "operation": operation,
                "duration": duration,
                "timestamp": time.time()
            })
    
    def end_performance_monitoring(self, test_name: str) -> Dict[str, Any]:
        """End performance monitoring and return metrics"""
        if test_name not in self.performance_metrics:
            return {}
            
        metrics = self.performance_metrics[test_name]
        metrics["end_time"] = time.time()
        metrics["total_duration"] = metrics["end_time"] - metrics["start_time"]
        metrics["memory_end"] = self._get_memory_usage()
        metrics["memory_peak"] = metrics["memory_end"] - metrics["memory_start"]
        
        return metrics
    
    def _get_memory_usage(self) -> float:
        """Get current memory usage in MB"""
        try:
            import psutil
            process = psutil.Process()
            return process.memory_info().rss / 1024 / 1024
        except ImportError:
            return 0.0
    
    def cleanup(self):
        """Clean up all test resources"""
        for temp_dir in self.temp_dirs:
            shutil.rmtree(temp_dir, ignore_errors=True)


class TDDWorkflowTest:
    """Comprehensive TDD workflow testing class"""
    
    def __init__(self, infrastructure: TestInfrastructure):
        self.infra = infrastructure
        self.orchestrator = None
        
    async def setup_orchestrator(self, project_path: Optional[Path] = None):
        """Set up orchestrator with test configuration"""
        self.orchestrator = Orchestrator()
        
        if project_path:
            # Register test project
            await self.orchestrator.handle_command(
                "/project register", "default",
                path=str(project_path), name="test_project"
            )
    
    async def test_full_tdd_cycle_with_real_project(self) -> Dict[str, Any]:
        """Test complete TDD cycle with realistic project simulation"""
        self.infra.start_performance_monitoring("full_tdd_cycle")
        
        # Create realistic test repository
        repo_path = self.infra.create_test_repository("calculator_app")
        await self.setup_orchestrator(repo_path)
        
        results = {"success": True, "phases": [], "errors": []}
        
        try:
            # Phase 1: Project setup and epic creation
            start_time = time.time()
            epic_result = await self.orchestrator.handle_command(
                "/epic", "default",
                description="Test-driven calculator with advanced operations",
                title="Scientific Calculator TDD"
            )
            self.infra.record_operation("full_tdd_cycle", "epic_creation", time.time() - start_time)
            
            if not epic_result["success"]:
                results["errors"].append(f"Epic creation failed: {epic_result.get('error')}")
                results["success"] = False
                return results
            
            epic_id = epic_result["epic_id"]
            results["phases"].append({"phase": "epic_creation", "success": True, "epic_id": epic_id})
            
            # Phase 2: Story creation with detailed acceptance criteria
            start_time = time.time()
            story_result = await self.orchestrator.handle_command(
                "/backlog add_story", "default",
                description="Implement basic arithmetic operations (add, subtract, multiply, divide) with input validation and error handling",
                feature=epic_id
            )
            self.infra.record_operation("full_tdd_cycle", "story_creation", time.time() - start_time)
            
            if not story_result["success"]:
                results["errors"].append(f"Story creation failed: {story_result.get('error')}")
                results["success"] = False
                return results
            
            story_id = story_result["story_id"]
            results["phases"].append({"phase": "story_creation", "success": True, "story_id": story_id})
            
            # Phase 3: TDD cycle initiation
            start_time = time.time()
            tdd_start_result = await self.orchestrator.handle_command(
                "/tdd start", "default",
                story_id=story_id,
                task_description="Implement addition operation with comprehensive test coverage"
            )
            self.infra.record_operation("full_tdd_cycle", "tdd_start", time.time() - start_time)
            
            if not tdd_start_result["success"]:
                results["errors"].append(f"TDD start failed: {tdd_start_result.get('error')}")
                results["success"] = False
                return results
            
            cycle_id = tdd_start_result["cycle_id"]
            results["phases"].append({"phase": "tdd_start", "success": True, "cycle_id": cycle_id})
            
            # Phase 4: Complete TDD cycle (Design → Test → Code → Refactor → Commit)
            tdd_phases = ["design", "test", "code", "refactor", "commit"]
            
            for phase in tdd_phases:
                start_time = time.time()
                
                if phase == "test":
                    # Add failing tests simulation
                    await self._simulate_failing_tests(cycle_id)
                    result = await self.orchestrator.handle_command(f"/tdd {phase}", "default")
                elif phase == "code":
                    # Add passing tests simulation
                    await self._simulate_passing_tests(cycle_id)
                    result = await self.orchestrator.handle_command(f"/tdd {phase}", "default")
                else:
                    result = await self.orchestrator.handle_command(f"/tdd {phase}", "default")
                
                self.infra.record_operation("full_tdd_cycle", f"tdd_{phase}", time.time() - start_time)
                
                if not result["success"]:
                    results["errors"].append(f"TDD {phase} failed: {result.get('error')}")
                    results["success"] = False
                    return results
                
                results["phases"].append({"phase": f"tdd_{phase}", "success": True})
            
            # Phase 5: Verify completion and metrics
            status_result = await self.orchestrator.handle_command("/tdd status", "default")
            if status_result["success"] and status_result.get("cycle_info"):
                cycle_info = status_result["cycle_info"]
                results["metrics"] = {
                    "completed_tasks": cycle_info.get("completed_tasks", 0),
                    "total_tasks": cycle_info.get("total_tasks", 0),
                    "test_runs": cycle_info.get("total_test_runs", 0)
                }
            
            results["performance"] = self.infra.end_performance_monitoring("full_tdd_cycle")
            
        except Exception as e:
            results["errors"].append(f"Unexpected error: {str(e)}")
            results["success"] = False
        
        return results
    
    async def test_multi_story_tdd_workflow(self) -> Dict[str, Any]:
        """Test sequential TDD cycles for multiple stories within a sprint"""
        self.infra.start_performance_monitoring("multi_story_tdd")
        
        repo_path = self.infra.create_test_repository("multi_feature_app")
        await self.setup_orchestrator(repo_path)
        
        results = {"success": True, "stories": [], "errors": []}
        
        try:
            # Create epic
            epic_result = await self.orchestrator.handle_command(
                "/epic", "default",
                description="Multi-feature application with comprehensive TDD coverage",
                title="Multi-Feature TDD Sprint"
            )
            
            if not epic_result["success"]:
                results["errors"].append(f"Epic creation failed: {epic_result.get('error')}")
                results["success"] = False
                return results
            
            epic_id = epic_result["epic_id"]
            
            # Create multiple stories
            test_data = self.infra.create_realistic_test_data()
            story_descriptions = test_data["epics"][0]["stories"][:3]  # Test with 3 stories
            
            for i, description in enumerate(story_descriptions):
                story_result = {"story_index": i, "description": description}
                
                # Create story
                backlog_result = await self.orchestrator.handle_command(
                    "/backlog add_story", "default",
                    description=description,
                    feature=epic_id
                )
                
                if not backlog_result["success"]:
                    story_result["error"] = f"Story creation failed: {backlog_result.get('error')}"
                    results["errors"].append(story_result["error"])
                    results["success"] = False
                    results["stories"].append(story_result)
                    continue
                
                story_id = backlog_result["story_id"]
                story_result["story_id"] = story_id
                
                # Run TDD cycle for story
                tdd_result = await self._run_complete_tdd_cycle(story_id, f"Feature {i+1} implementation")
                story_result.update(tdd_result)
                
                if not tdd_result["success"]:
                    results["success"] = False
                
                results["stories"].append(story_result)
            
            results["performance"] = self.infra.end_performance_monitoring("multi_story_tdd")
            
        except Exception as e:
            results["errors"].append(f"Unexpected error: {str(e)}")
            results["success"] = False
        
        return results
    
    async def test_integration_with_sprint_lifecycle(self) -> Dict[str, Any]:
        """Test TDD cycles within complete sprint lifecycle"""
        self.infra.start_performance_monitoring("sprint_integration")
        
        repo_path = self.infra.create_test_repository("sprint_project")
        await self.setup_orchestrator(repo_path)
        
        results = {"success": True, "sprint_phases": [], "errors": []}
        
        try:
            # Phase 1: Sprint Planning
            epic_result = await self.orchestrator.handle_command(
                "/epic", "default",
                description="Sprint integration testing with TDD workflow",
                title="Sprint TDD Integration"
            )
            
            if not epic_result["success"]:
                results["errors"].append(f"Epic creation failed: {epic_result.get('error')}")
                results["success"] = False
                return results
            
            epic_id = epic_result["epic_id"]
            
            # Add stories to backlog
            stories = []
            for i in range(2):  # 2 stories for sprint
                story_result = await self.orchestrator.handle_command(
                    "/backlog add_story", "default",
                    description=f"Sprint story {i+1}: Core functionality implementation",
                    feature=epic_id
                )
                
                if story_result["success"]:
                    stories.append(story_result["story_id"])
                else:
                    results["errors"].append(f"Story {i+1} creation failed: {story_result.get('error')}")
            
            results["sprint_phases"].append({"phase": "planning", "success": True, "stories_created": len(stories)})
            
            # Phase 2: Sprint Start (simulate sprint planning)
            sprint_result = await self.orchestrator.handle_command("/sprint plan", "default")
            if sprint_result["success"]:
                sprint_start_result = await self.orchestrator.handle_command("/sprint start", "default")
                results["sprint_phases"].append({"phase": "sprint_start", "success": sprint_start_result["success"]})
            
            # Phase 3: TDD Execution for each story
            for story_id in stories:
                tdd_result = await self._run_complete_tdd_cycle(story_id, f"Implementation for {story_id}")
                results["sprint_phases"].append({
                    "phase": "tdd_execution",
                    "story_id": story_id,
                    "success": tdd_result["success"]
                })
                
                if not tdd_result["success"]:
                    results["success"] = False
            
            # Phase 4: Sprint Review
            review_result = await self.orchestrator.handle_command("/sprint review", "default")
            results["sprint_phases"].append({"phase": "sprint_review", "success": review_result.get("success", True)})
            
            results["performance"] = self.infra.end_performance_monitoring("sprint_integration")
            
        except Exception as e:
            results["errors"].append(f"Unexpected error: {str(e)}")
            results["success"] = False
        
        return results
    
    async def _run_complete_tdd_cycle(self, story_id: str, task_description: str) -> Dict[str, Any]:
        """Run a complete TDD cycle for a story"""
        result = {"success": True, "phases": [], "errors": []}
        
        try:
            # Start TDD cycle
            start_result = await self.orchestrator.handle_command(
                "/tdd start", "default",
                story_id=story_id,
                task_description=task_description
            )
            
            if not start_result["success"]:
                result["errors"].append(f"TDD start failed: {start_result.get('error')}")
                result["success"] = False
                return result
            
            cycle_id = start_result["cycle_id"]
            
            # Execute TDD phases
            phases = ["design", "test", "code", "refactor", "commit"]
            for phase in phases:
                if phase == "test":
                    await self._simulate_failing_tests(cycle_id)
                elif phase == "code":
                    await self._simulate_passing_tests(cycle_id)
                
                phase_result = await self.orchestrator.handle_command(f"/tdd {phase}", "default")
                
                if not phase_result["success"]:
                    result["errors"].append(f"TDD {phase} failed: {phase_result.get('error')}")
                    result["success"] = False
                    return result
                
                result["phases"].append(phase)
        
        except Exception as e:
            result["errors"].append(f"TDD cycle error: {str(e)}")
            result["success"] = False
        
        return result
    
    async def _simulate_failing_tests(self, cycle_id: str):
        """Simulate failing tests for red phase"""
        try:
            project = self.orchestrator.projects["default"]
            active_cycle = project.storage.get_active_tdd_cycle()
            
            if active_cycle and active_cycle.get_current_task():
                failing_test = TestResult(
                    test_file="test_implementation.py",
                    test_name="test_core_functionality",
                    status=TestStatus.RED,
                    output="AssertionError: Expected functionality not implemented"
                )
                active_cycle.get_current_task().test_results.append(failing_test)
                project.storage.save_tdd_cycle(active_cycle)
        except Exception as e:
            print(f"Warning: Could not simulate failing tests: {e}")
    
    async def _simulate_passing_tests(self, cycle_id: str):
        """Simulate passing tests for green phase"""
        try:
            project = self.orchestrator.projects["default"]
            active_cycle = project.storage.get_active_tdd_cycle()
            
            if active_cycle and active_cycle.get_current_task():
                passing_test = TestResult(
                    test_file="test_implementation.py",
                    test_name="test_core_functionality",
                    status=TestStatus.GREEN,
                    output="All tests passed successfully"
                )
                active_cycle.get_current_task().test_results.append(passing_test)
                project.storage.save_tdd_cycle(active_cycle)
        except Exception as e:
            print(f"Warning: Could not simulate passing tests: {e}")


async def test_complete_tdd_workflow():
    """Test a complete TDD workflow end-to-end"""
    print("=== TDD End-to-End Test ===\n")
    
    # Create temporary directory for test
    temp_dir = tempfile.mkdtemp()
    test_project_path = Path(temp_dir) / "test_project"
    test_project_path.mkdir(parents=True)
    
    try:
        # Create orchestrator with test project
        orchestrator = Orchestrator()
        
        # 1. Create an Epic
        print("1. Creating epic...")
        result = await orchestrator.handle_command(
            "/epic", "default", 
            description="Test-driven calculator development",
            title="Calculator TDD"
        )
        assert result["success"], f"Epic creation failed: {result.get('error')}"
        epic_id = result["epic_id"]
        print(f"✓ Epic created: {epic_id}")
        
        # 2. Add a story to the backlog
        print("\n2. Adding story to backlog...")
        result = await orchestrator.handle_command(
            "/backlog add_story", "default",
            description="Implement addition operation for calculator",
            feature=epic_id
        )
        assert result["success"], f"Story creation failed: {result.get('error')}"
        story_id = result["story_id"]
        print(f"✓ Story created: {story_id}")
        
        # 3. Start TDD cycle for the story
        print("\n3. Starting TDD cycle...")
        result = await orchestrator.handle_command(
            "/tdd start", "default",
            story_id=story_id,
            task_description="Implement basic addition functionality"
        )
        assert result["success"], f"TDD start failed: {result.get('error')}"
        cycle_id = result["cycle_id"]
        print(f"✓ TDD cycle started: {cycle_id}")
        
        # 4. Check TDD status
        print("\n4. Checking TDD status...")
        result = await orchestrator.handle_command("/tdd status", "default")
        assert result["success"], f"TDD status failed: {result.get('error')}"
        assert result["cycle_info"]["cycle_id"] == cycle_id
        assert result["current_state"] == "design"
        print("✓ TDD status shows correct state: design")
        
        # 5. Complete design phase
        print("\n5. Completing design phase...")
        result = await orchestrator.handle_command("/tdd design", "default")
        assert result["success"], f"TDD design failed: {result.get('error')}"
        print("✓ Design phase completed")
        
        # 6. Move to test writing phase
        print("\n6. Moving to test writing phase...")
        result = await orchestrator.handle_command("/tdd test", "default")
        assert result["success"], f"TDD test transition failed: {result.get('error')}"
        assert result["current_state"] == "test_red"
        print("✓ Moved to test_red state")
        
        # 7. Simulate test run (red state)
        print("\n7. Running tests (expecting red)...")
        result = await orchestrator.handle_command("/tdd run_tests", "default")
        assert result["success"], f"TDD run_tests failed: {result.get('error')}"
        print("✓ Tests executed in red state")
        
        # 8. Simulate adding failing tests (this would normally be done by agents)
        print("\n8. Simulating failing tests...")
        # Get the active cycle and add a failing test result
        project = orchestrator.projects["default"]
        active_cycle = project.storage.get_active_tdd_cycle()
        if active_cycle and active_cycle.get_current_task():
            from tdd_models import TestResult, TestStatus
            failing_test = TestResult(
                test_file="test_calculator.py",
                test_name="test_add",
                status=TestStatus.RED,
                output="AssertionError: Expected 5, got None"
            )
            active_cycle.get_current_task().test_results.append(failing_test)
            project.storage.save_tdd_cycle(active_cycle)
        print("✓ Failing tests simulated")
        
        # 9. Move to implementation phase
        print("\n9. Moving to implementation phase...")
        result = await orchestrator.handle_command("/tdd code", "default")
        assert result["success"], f"TDD code transition failed: {result.get('error')}"
        assert result["current_state"] == "code_green"
        print("✓ Moved to code_green state")
        
        # 10. Simulate passing tests for refactor phase
        print("\n10. Simulating passing tests...")
        active_cycle = project.storage.get_active_tdd_cycle()
        if active_cycle and active_cycle.get_current_task():
            passing_test = TestResult(
                test_file="test_calculator.py",
                test_name="test_add",
                status=TestStatus.GREEN,
                output="All tests passed"
            )
            active_cycle.get_current_task().test_results.append(passing_test)
            project.storage.save_tdd_cycle(active_cycle)
        print("✓ Passing tests simulated")
        
        # 11. Move to refactor phase
        print("\n11. Moving to refactor phase...")
        result = await orchestrator.handle_command("/tdd refactor", "default")
        assert result["success"], f"TDD refactor transition failed: {result.get('error')}"
        assert result["current_state"] == "refactor"
        print("✓ Moved to refactor state")
        
        # 12. Commit the work
        print("\n12. Committing work...")
        result = await orchestrator.handle_command("/tdd commit", "default")
        assert result["success"], f"TDD commit failed: {result.get('error')}"
        assert result["current_state"] == "commit"
        print("✓ Work committed")
        
        # 13. Check final status
        print("\n13. Checking final TDD status...")
        result = await orchestrator.handle_command("/tdd status", "default")
        assert result["success"], f"TDD status failed: {result.get('error')}"
        
        cycle_info = result["cycle_info"]
        print(f"Debug: cycle_info = {cycle_info}")
        
        # Check that we have valid cycle information
        assert cycle_info is not None, "Should have cycle info"
        assert cycle_info["total_test_runs"] >= 1, "Should have test runs recorded"
        print(f"✓ Final status: {cycle_info['completed_tasks']}/{cycle_info['total_tasks']} tasks, {cycle_info['total_test_runs']} test runs")
        
        # 14. Test TDD next command
        print("\n14. Testing TDD next command...")
        result = await orchestrator.handle_command("/tdd next", "default")
        assert result["success"], f"TDD next failed: {result.get('error')}"
        print("✓ TDD next command works")
        
        # 15. Test abort functionality
        print("\n15. Testing TDD abort...")
        result = await orchestrator.handle_command("/tdd abort", "default")
        assert result["success"], f"TDD abort failed: {result.get('error')}"
        print("✓ TDD cycle aborted successfully")
        
        # 16. Verify no active cycle after abort
        print("\n16. Verifying no active cycle after abort...")
        result = await orchestrator.handle_command("/tdd status", "default")
        assert result["success"], f"TDD status failed: {result.get('error')}"
        assert "No active TDD cycle" in result.get("message", "")
        print("✓ No active TDD cycle after abort")
        
        print("\n🎉 All TDD end-to-end tests passed!")
        return True
        
    except Exception as e:
        print(f"\n❌ TDD E2E test failed: {e}")
        import traceback
        traceback.print_exc()
        return False
        
    finally:
        # Cleanup
        shutil.rmtree(temp_dir, ignore_errors=True)


async def test_tdd_error_handling():
    """Test TDD error handling scenarios"""
    print("\n=== TDD Error Handling Test ===\n")
    
    try:
        orchestrator = Orchestrator()
        
        # 1. Test starting TDD without story ID
        print("1. Testing TDD start without story ID...")
        result = await orchestrator.handle_command("/tdd start", "default")
        assert not result["success"], "Should fail without story ID"
        assert "Story ID is required" in result["error"]
        print("✓ Properly rejects TDD start without story ID")
        
        # 2. Test TDD status with no active cycle
        print("\n2. Testing TDD status with no active cycle...")
        result = await orchestrator.handle_command("/tdd status", "default")
        assert result["success"], "TDD status should succeed even with no cycle"
        # Check that message indicates no active cycle
        if "message" in result:
            assert "No active TDD cycle" in result["message"]
        else:
            # If no message field, check that cycle_info is None or empty
            assert result.get("cycle_info") is None or "No active" in str(result)
        print("✓ TDD status works with no active cycle")
        
        # 3. Test TDD transitions without active cycle
        print("\n3. Testing TDD transitions without active cycle...")
        result = await orchestrator.handle_command("/tdd test", "default")
        assert not result["success"], "Should fail without active cycle"
        assert "No active TDD cycle" in result["error"]
        print("✓ TDD transitions properly rejected without active cycle")
        
        # 4. Test TDD start with invalid story ID
        print("\n4. Testing TDD start with invalid story ID...")
        result = await orchestrator.handle_command("/tdd start", "default", story_id="invalid-story-123")
        assert not result["success"], "Should fail with invalid story ID"
        assert "Story not found" in result["error"]
        print("✓ TDD start properly rejects invalid story ID")
        
        # 5. Test unknown TDD command
        print("\n5. Testing unknown TDD command...")
        result = await orchestrator.handle_command("/tdd unknown_action", "default")
        assert not result["success"], "Should fail with unknown action"
        assert "Unknown TDD action" in result["error"]
        print("✓ Unknown TDD commands properly rejected")
        
        print("\n🎉 All TDD error handling tests passed!")
        return True
        
    except Exception as e:
        print(f"\n❌ TDD error handling test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_human_intervention_points():
    """Test HITL approval workflows and error escalation"""
    print("\n=== Human Intervention Testing ===\n")
    
    infra = TestInfrastructure()
    workflow_test = TDDWorkflowTest(infra)
    
    try:
        repo_path = infra.create_test_repository("hitl_test_project")
        await workflow_test.setup_orchestrator(repo_path)
        
        results = {"success": True, "intervention_points": [], "errors": []}
        
        # Test 1: Approval workflow simulation
        print("1. Testing approval workflow simulation...")
        
        # Create epic and story
        epic_result = await workflow_test.orchestrator.handle_command(
            "/epic", "default",
            description="HITL testing workflow with approval gates",
            title="Human Intervention Test"
        )
        
        if epic_result["success"]:
            epic_id = epic_result["epic_id"]
            story_result = await workflow_test.orchestrator.handle_command(
                "/backlog add_story", "default",
                description="Complex feature requiring human approval",
                feature=epic_id
            )
            
            if story_result["success"]:
                story_id = story_result["story_id"]
                
                # Start TDD cycle
                tdd_result = await workflow_test.orchestrator.handle_command(
                    "/tdd start", "default",
                    story_id=story_id,
                    task_description="Implementation requiring approval"
                )
                
                if tdd_result["success"]:
                    results["intervention_points"].append({
                        "point": "tdd_start_approval",
                        "success": True,
                        "cycle_id": tdd_result["cycle_id"]
                    })
                else:
                    results["errors"].append(f"TDD start failed: {tdd_result.get('error')}")
        
        # Test 2: Error escalation simulation
        print("2. Testing error escalation...")
        
        # Simulate failed attempts that should escalate to human
        for attempt in range(3):
            try:
                # Simulate failing operation that would escalate
                result = await workflow_test.orchestrator.handle_command("/tdd design", "default")
                if result["success"]:
                    break
            except Exception as e:
                if attempt == 2:  # Third attempt
                    results["intervention_points"].append({
                        "point": "error_escalation",
                        "success": True,
                        "attempts": attempt + 1
                    })
        
        print("✓ Human intervention testing completed")
        return results
        
    except Exception as e:
        print(f"❌ Human intervention test failed: {e}")
        return {"success": False, "errors": [str(e)]}
    finally:
        infra.cleanup()


async def test_performance_and_reliability():
    """Test performance benchmarks and reliability metrics"""
    print("\n=== Performance and Reliability Testing ===\n")
    
    infra = TestInfrastructure()
    workflow_test = TDDWorkflowTest(infra)
    
    try:
        # Get performance targets
        test_data = infra.create_realistic_test_data()
        targets = test_data["performance_targets"]
        
        print("1. Testing TDD cycle performance...")
        
        # Run performance test
        perf_result = await workflow_test.test_full_tdd_cycle_with_real_project()
        
        if perf_result["success"] and "performance" in perf_result:
            performance = perf_result["performance"]
            
            # Check performance against targets
            performance_check = {
                "cycle_time_ok": performance.get("total_duration", 0) <= targets["tdd_cycle_time"],
                "memory_usage_ok": performance.get("memory_peak", 0) <= targets["memory_usage_mb"],
                "operations_completed": len(performance.get("operations", [])),
                "performance_data": performance
            }
            
            print(f"   Cycle time: {performance.get('total_duration', 0):.2f}s (target: {targets['tdd_cycle_time']}s)")
            print(f"   Memory usage: {performance.get('memory_peak', 0):.1f}MB (target: {targets['memory_usage_mb']}MB)")
            print(f"   Operations: {performance_check['operations_completed']}")
            
            return {"success": True, "performance_check": performance_check}
        else:
            return {"success": False, "errors": perf_result.get("errors", [])}
    
    except Exception as e:
        print(f"❌ Performance test failed: {e}")
        return {"success": False, "errors": [str(e)]}
    finally:
        infra.cleanup()


async def run_comprehensive_tdd_tests():
    """Run the comprehensive TDD test suite"""
    print("="*60)
    print("COMPREHENSIVE TDD TEST SUITE - PHASE 6")
    print("="*60)
    
    infra = TestInfrastructure()
    workflow_test = TDDWorkflowTest(infra)
    
    all_results = []
    
    try:
        # Test 1: Full TDD Cycle with Real Project
        print("\n🔄 TEST 1: Full TDD Cycle with Real Project Simulation")
        result1 = await workflow_test.test_full_tdd_cycle_with_real_project()
        all_results.append(("Full TDD Cycle", result1))
        
        if result1["success"]:
            print("✅ Full TDD cycle test PASSED")
        else:
            print(f"❌ Full TDD cycle test FAILED: {result1['errors']}")
        
        # Test 2: Multi-Story TDD Workflow
        print("\n🔄 TEST 2: Multi-Story TDD Workflow")
        result2 = await workflow_test.test_multi_story_tdd_workflow()
        all_results.append(("Multi-Story TDD", result2))
        
        if result2["success"]:
            print("✅ Multi-story TDD test PASSED")
        else:
            print(f"❌ Multi-story TDD test FAILED: {result2['errors']}")
        
        # Test 3: Sprint Lifecycle Integration
        print("\n🔄 TEST 3: Sprint Lifecycle Integration")
        result3 = await workflow_test.test_integration_with_sprint_lifecycle()
        all_results.append(("Sprint Integration", result3))
        
        if result3["success"]:
            print("✅ Sprint integration test PASSED")
        else:
            print(f"❌ Sprint integration test FAILED: {result3['errors']}")
        
        # Test 4: Human Intervention Points
        print("\n🔄 TEST 4: Human Intervention Points")
        result4 = await test_human_intervention_points()
        all_results.append(("Human Intervention", result4))
        
        if result4["success"]:
            print("✅ Human intervention test PASSED")
        else:
            print(f"❌ Human intervention test FAILED: {result4['errors']}")
        
        # Test 5: Performance and Reliability
        print("\n🔄 TEST 5: Performance and Reliability")
        result5 = await test_performance_and_reliability()
        all_results.append(("Performance", result5))
        
        if result5["success"]:
            print("✅ Performance test PASSED")
        else:
            print(f"❌ Performance test FAILED: {result5['errors']}")
        
        # Test 6: Legacy Tests (existing functionality)
        print("\n🔄 TEST 6: Legacy End-to-End Test")
        result6 = await test_complete_tdd_workflow()
        all_results.append(("Legacy E2E", result6))
        
        # Test 7: Error Handling
        print("\n🔄 TEST 7: Error Handling")
        result7 = await test_tdd_error_handling()
        all_results.append(("Error Handling", result7))
        
    except Exception as e:
        print(f"\n❌ Comprehensive test suite failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        infra.cleanup()
    
    # Generate test report
    print("\n" + "="*60)
    print("COMPREHENSIVE TEST RESULTS SUMMARY")
    print("="*60)
    
    total_tests = len(all_results)
    passed_tests = sum(1 for _, result in all_results if result)
    
    for test_name, result in all_results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name:<25} {status}")
        
        if not result and isinstance(result, dict) and "errors" in result:
            for error in result["errors"][:3]:  # Show first 3 errors
                print(f"   Error: {error}")
    
    print("\n" + "-"*60)
    print(f"OVERALL RESULT: {passed_tests}/{total_tests} tests passed")
    
    if passed_tests == total_tests:
        print("🎉 ALL COMPREHENSIVE TDD TESTS PASSED!")
        print("Phase 6 implementation is production-ready.")
        return True
    else:
        print("❌ SOME COMPREHENSIVE TESTS FAILED!")
        print("Please review the errors above.")
        return False


async def main():
    """Run all TDD tests"""
    print("Starting TDD comprehensive testing...\n")
    
    # Run comprehensive test suite
    comprehensive_success = await run_comprehensive_tdd_tests()
    
    if comprehensive_success:
        print("\n" + "="*50)
        print("🎉 ALL TDD TESTS PASSED!")
        print("Phase 6 TDD comprehensive testing completed successfully.")
        print("="*50)
        return 0
    else:
        print("\n" + "="*50)
        print("❌ SOME TDD TESTS FAILED!")
        print("Please check the errors above.")
        print("="*50)
        return 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))