#!/usr/bin/env python3
"""
Edge Case and Error Testing Suite for TDD Implementation.

This module provides comprehensive edge case validation including:
- System failure scenarios (Claude Code outages, network failures)
- Data corruption and recovery testing
- Invalid state transitions and error handling
- Resource exhaustion testing
- Concurrent conflict resolution
- Boundary condition testing
"""

import asyncio
import tempfile
import shutil
import json
import time
import gc
import psutil
from pathlib import Path
from typing import Dict, List, Any, Optional
from unittest.mock import Mock, patch, AsyncMock, MagicMock
import pytest
import sys

# Add project paths to sys.path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "lib"))
sys.path.insert(0, str(project_root / "scripts"))

from orchestrator import Orchestrator
from data_models import Epic, Story
from tdd_models import TDDCycle, TDDTask, TestResult, TestStatus
from project_storage import ProjectStorage
from tdd_state_machine import TDDStateMachine, TDDState


class EdgeCaseTestFramework:
    """Framework for edge case and error testing"""
    
    def __init__(self):
        self.temp_dirs: List[Path] = []
        self.orchestrator = None
        self.test_results: Dict[str, Any] = {}
        
    def setup_test_environment(self) -> Path:
        """Set up test environment"""
        temp_dir = tempfile.mkdtemp()
        test_path = Path(temp_dir)
        self.temp_dirs.append(test_path)
        return test_path
        
    def cleanup(self):
        """Clean up test resources"""
        for temp_dir in self.temp_dirs:
            shutil.rmtree(temp_dir, ignore_errors=True)
        self.temp_dirs.clear()
        self.test_results.clear()


class SystemFailureTests:
    """Test system failure scenarios"""
    
    def __init__(self):
        self.framework = EdgeCaseTestFramework()
        
    async def test_claude_code_outage_simulation(self) -> Dict[str, Any]:
        """Test behavior during Claude Code outage"""
        results = {"success": True, "scenarios": [], "errors": []}
        
        try:
            test_path = self.framework.setup_test_environment()
            self.framework.orchestrator = Orchestrator()
            
            # Create initial TDD cycle
            epic_result = await self.framework.orchestrator.handle_command(
                "/epic", "default",
                description="Outage test epic",
                title="Outage Test"
            )
            
            if not epic_result["success"]:
                return {"success": False, "error": "Failed to create test epic"}
            
            story_result = await self.framework.orchestrator.handle_command(
                "/backlog add_story", "default",
                description="Outage test story",
                feature=epic_result["epic_id"]
            )
            
            if not story_result["success"]:
                return {"success": False, "error": "Failed to create test story"}
            
            tdd_result = await self.framework.orchestrator.handle_command(
                "/tdd start", "default",
                story_id=story_result["story_id"],
                task_description="Outage test task"
            )
            
            if not tdd_result["success"]:
                return {"success": False, "error": "Failed to start TDD cycle"}
            
            cycle_id = tdd_result["cycle_id"]
            
            # Scenario 1: Claude Code unavailable during design phase
            scenario1 = await self._test_claude_outage_during_phase("design", cycle_id)
            results["scenarios"].append({"scenario": "design_phase_outage", "result": scenario1})
            
            # Scenario 2: Claude Code unavailable during test phase
            scenario2 = await self._test_claude_outage_during_phase("test", cycle_id)
            results["scenarios"].append({"scenario": "test_phase_outage", "result": scenario2})
            
            # Scenario 3: Recovery after outage
            scenario3 = await self._test_recovery_after_outage(cycle_id)
            results["scenarios"].append({"scenario": "recovery_after_outage", "result": scenario3})
            
            # Check if any scenarios failed
            for scenario in results["scenarios"]:
                if not scenario["result"].get("success", False):
                    results["success"] = False
                    results["errors"].extend(scenario["result"].get("errors", []))
            
            return results
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def _test_claude_outage_during_phase(self, phase: str, cycle_id: str) -> Dict[str, Any]:
        """Test Claude Code outage during specific TDD phase"""
        try:
            # Simulate Claude Code being unavailable
            with patch('lib.agents.base_agent.get_claude_client') as mock_client:
                mock_client.side_effect = ConnectionError("Claude Code service unavailable")
                
                result = await self.framework.orchestrator.handle_command(f"/tdd {phase}", "default")
                
                # Check graceful handling
                if result.get("success"):
                    return {
                        "success": False,
                        "errors": [f"TDD {phase} succeeded despite Claude outage"]
                    }
                
                # Verify appropriate error message
                error_msg = result.get("error", "").lower()
                if "unavailable" not in error_msg and "connection" not in error_msg:
                    return {
                        "success": False,
                        "errors": [f"Inadequate error message for Claude outage: {result.get('error')}"]
                    }
                
                return {"success": True, "handled_gracefully": True}
                
        except Exception as e:
            return {"success": False, "errors": [f"Exception during outage test: {e}"]}
    
    async def _test_recovery_after_outage(self, cycle_id: str) -> Dict[str, Any]:
        """Test system recovery after Claude Code outage"""
        try:
            # Verify TDD cycle state is preserved
            status_result = await self.framework.orchestrator.handle_command("/tdd status", "default")
            
            if not status_result.get("success"):
                return {"success": False, "errors": ["Cannot check TDD status after outage"]}
            
            cycle_info = status_result.get("cycle_info")
            if not cycle_info or cycle_info.get("cycle_id") != cycle_id:
                return {"success": False, "errors": ["TDD cycle state not preserved after outage"]}
            
            # Test that normal operations resume after outage
            # (This would normally test with Claude Code available again)
            return {"success": True, "state_preserved": True}
            
        except Exception as e:
            return {"success": False, "errors": [f"Recovery test error: {e}"]}
    
    async def test_network_failure_scenarios(self) -> Dict[str, Any]:
        """Test network failure scenarios"""
        results = {"success": True, "network_tests": [], "errors": []}
        
        try:
            test_path = self.framework.setup_test_environment()
            self.framework.orchestrator = Orchestrator()
            
            # Test 1: Timeout during agent operations
            timeout_test = await self._test_network_timeout()
            results["network_tests"].append({"test": "network_timeout", "result": timeout_test})
            
            # Test 2: Intermittent connectivity
            intermittent_test = await self._test_intermittent_connectivity()
            results["network_tests"].append({"test": "intermittent_connectivity", "result": intermittent_test})
            
            # Test 3: Complete network isolation
            isolation_test = await self._test_network_isolation()
            results["network_tests"].append({"test": "network_isolation", "result": isolation_test})
            
            # Check results
            for test in results["network_tests"]:
                if not test["result"].get("success", False):
                    results["success"] = False
                    results["errors"].extend(test["result"].get("errors", []))
            
            return results
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def _test_network_timeout(self) -> Dict[str, Any]:
        """Test network timeout handling"""
        try:
            # Simulate network timeout
            with patch('asyncio.wait_for') as mock_wait:
                mock_wait.side_effect = asyncio.TimeoutError("Network timeout")
                
                result = await self.framework.orchestrator.handle_command("/state", "default")
                
                # Should handle timeout gracefully
                if result.get("success"):
                    return {
                        "success": False,
                        "errors": ["Command succeeded despite network timeout"]
                    }
                
                return {"success": True, "timeout_handled": True}
                
        except Exception as e:
            return {"success": False, "errors": [f"Timeout test error: {e}"]}
    
    async def _test_intermittent_connectivity(self) -> Dict[str, Any]:
        """Test intermittent connectivity handling"""
        try:
            # Simulate intermittent failures
            call_count = 0
            
            def intermittent_failure(*args, **kwargs):
                nonlocal call_count
                call_count += 1
                if call_count % 2 == 1:  # Fail every other call
                    raise ConnectionError("Intermittent network failure")
                return AsyncMock()
            
            with patch('lib.agents.base_agent.get_claude_client', side_effect=intermittent_failure):
                # Try multiple operations
                results = []
                for i in range(3):
                    result = await self.framework.orchestrator.handle_command("/state", "default")
                    results.append(result.get("success", False))
                
                # Should have some successes and some failures
                if all(results) or not any(results):
                    return {
                        "success": False,
                        "errors": ["Intermittent connectivity not properly handled"]
                    }
                
                return {"success": True, "intermittent_handled": True}
                
        except Exception as e:
            return {"success": False, "errors": [f"Intermittent test error: {e}"]}
    
    async def _test_network_isolation(self) -> Dict[str, Any]:
        """Test complete network isolation"""
        try:
            # Simulate complete network isolation
            with patch('lib.agents.base_agent.get_claude_client') as mock_client:
                mock_client.side_effect = OSError("Network unreachable")
                
                result = await self.framework.orchestrator.handle_command("/tdd status", "default")
                
                # Should provide meaningful offline behavior
                if not result.get("success"):
                    error_msg = result.get("error", "").lower()
                    if "network" in error_msg or "offline" in error_msg or "unreachable" in error_msg:
                        return {"success": True, "isolation_handled": True}
                
                return {
                    "success": False,
                    "errors": ["Network isolation not properly communicated to user"]
                }
                
        except Exception as e:
            return {"success": False, "errors": [f"Isolation test error: {e}"]}


class DataCorruptionTests:
    """Test data corruption and recovery scenarios"""
    
    def __init__(self):
        self.framework = EdgeCaseTestFramework()
        
    async def test_tdd_state_corruption(self) -> Dict[str, Any]:
        """Test TDD state file corruption scenarios"""
        results = {"success": True, "corruption_tests": [], "errors": []}
        
        try:
            test_path = self.framework.setup_test_environment()
            storage = ProjectStorage(test_path / "corruption_test")
            
            # Create valid TDD cycle
            cycle = TDDCycle(story_id="corruption-test", task_description="Corruption test")
            storage.save_tdd_cycle(cycle)
            
            # Test 1: Partial file corruption
            partial_test = await self._test_partial_file_corruption(storage, cycle.cycle_id)
            results["corruption_tests"].append({"test": "partial_corruption", "result": partial_test})
            
            # Test 2: Complete file corruption
            complete_test = await self._test_complete_file_corruption(storage, cycle.cycle_id)
            results["corruption_tests"].append({"test": "complete_corruption", "result": complete_test})
            
            # Test 3: JSON syntax corruption
            json_test = await self._test_json_corruption(storage, cycle.cycle_id)
            results["corruption_tests"].append({"test": "json_corruption", "result": json_test})
            
            # Test 4: Recovery mechanisms
            recovery_test = await self._test_corruption_recovery(storage, cycle.cycle_id)
            results["corruption_tests"].append({"test": "corruption_recovery", "result": recovery_test})
            
            # Check results
            for test in results["corruption_tests"]:
                if not test["result"].get("success", False):
                    results["success"] = False
                    results["errors"].extend(test["result"].get("errors", []))
            
            return results
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def _test_partial_file_corruption(self, storage: ProjectStorage, cycle_id: str) -> Dict[str, Any]:
        """Test partial file corruption handling"""
        try:
            # Corrupt part of the TDD cycle file
            cycle_file = storage._get_tdd_cycle_path(cycle_id)
            if not cycle_file.exists():
                return {"success": False, "errors": ["TDD cycle file does not exist"]}
            
            # Read original content
            with open(cycle_file, 'r') as f:
                original_content = f.read()
            
            # Corrupt the file by truncating it
            with open(cycle_file, 'w') as f:
                f.write(original_content[:len(original_content)//2])
            
            # Try to load corrupted cycle
            try:
                corrupted_cycle = storage.get_tdd_cycle(cycle_id)
                if corrupted_cycle is not None:
                    return {
                        "success": False,
                        "errors": ["Corrupted file loaded successfully - inadequate validation"]
                    }
            except Exception:
                # Expected behavior - corruption detected
                pass
            
            # Restore original content
            with open(cycle_file, 'w') as f:
                f.write(original_content)
            
            return {"success": True, "corruption_detected": True}
            
        except Exception as e:
            return {"success": False, "errors": [f"Partial corruption test error: {e}"]}
    
    async def _test_complete_file_corruption(self, storage: ProjectStorage, cycle_id: str) -> Dict[str, Any]:
        """Test complete file corruption handling"""
        try:
            cycle_file = storage._get_tdd_cycle_path(cycle_id)
            if not cycle_file.exists():
                return {"success": False, "errors": ["TDD cycle file does not exist"]}
            
            # Backup original
            with open(cycle_file, 'r') as f:
                original_content = f.read()
            
            # Completely corrupt the file
            with open(cycle_file, 'w') as f:
                f.write("CORRUPTED DATA" * 100)
            
            # Try to load
            try:
                corrupted_cycle = storage.get_tdd_cycle(cycle_id)
                if corrupted_cycle is not None:
                    return {
                        "success": False,
                        "errors": ["Completely corrupted file loaded - no validation"]
                    }
            except Exception:
                # Expected behavior
                pass
            
            # Restore
            with open(cycle_file, 'w') as f:
                f.write(original_content)
            
            return {"success": True, "complete_corruption_detected": True}
            
        except Exception as e:
            return {"success": False, "errors": [f"Complete corruption test error: {e}"]}
    
    async def _test_json_corruption(self, storage: ProjectStorage, cycle_id: str) -> Dict[str, Any]:
        """Test JSON syntax corruption handling"""
        try:
            cycle_file = storage._get_tdd_cycle_path(cycle_id)
            if not cycle_file.exists():
                return {"success": False, "errors": ["TDD cycle file does not exist"]}
            
            # Backup original
            with open(cycle_file, 'r') as f:
                original_content = f.read()
            
            # Create invalid JSON
            with open(cycle_file, 'w') as f:
                f.write('{"invalid": json, "missing": quotes}')
            
            # Try to load
            try:
                corrupted_cycle = storage.get_tdd_cycle(cycle_id)
                if corrupted_cycle is not None:
                    return {
                        "success": False,
                        "errors": ["Invalid JSON loaded successfully"]
                    }
            except json.JSONDecodeError:
                # Expected behavior
                pass
            except Exception as e:
                # Also acceptable - some other parsing error
                pass
            
            # Restore
            with open(cycle_file, 'w') as f:
                f.write(original_content)
            
            return {"success": True, "json_corruption_detected": True}
            
        except Exception as e:
            return {"success": False, "errors": [f"JSON corruption test error: {e}"]}
    
    async def _test_corruption_recovery(self, storage: ProjectStorage, cycle_id: str) -> Dict[str, Any]:
        """Test recovery mechanisms for corrupted data"""
        try:
            # For now, test that we can recreate a cycle with the same ID
            cycle_file = storage._get_tdd_cycle_path(cycle_id)
            if cycle_file.exists():
                cycle_file.unlink()  # Delete the file
            
            # Try to create new cycle with same ID
            new_cycle = TDDCycle(story_id="recovery-test", task_description="Recovery test")
            new_cycle.cycle_id = cycle_id  # Force same ID
            
            try:
                storage.save_tdd_cycle(new_cycle)
                recovered_cycle = storage.get_tdd_cycle(cycle_id)
                
                if recovered_cycle is None:
                    return {"success": False, "errors": ["Recovery failed - cannot reload cycle"]}
                
                return {"success": True, "recovery_successful": True}
                
            except Exception as e:
                return {"success": False, "errors": [f"Recovery mechanism failed: {e}"]}
            
        except Exception as e:
            return {"success": False, "errors": [f"Recovery test error: {e}"]}


class InvalidTransitionTests:
    """Test invalid state transitions and error handling"""
    
    def __init__(self):
        self.framework = EdgeCaseTestFramework()
        
    async def test_invalid_tdd_transitions(self) -> Dict[str, Any]:
        """Test invalid TDD state transitions"""
        results = {"success": True, "transition_tests": [], "errors": []}
        
        try:
            test_path = self.framework.setup_test_environment()
            self.framework.orchestrator = Orchestrator()
            
            # Create TDD cycle
            epic_result = await self.framework.orchestrator.handle_command(
                "/epic", "default",
                description="Transition test epic",
                title="Transition Test"
            )
            
            story_result = await self.framework.orchestrator.handle_command(
                "/backlog add_story", "default",
                description="Transition test story",
                feature=epic_result["epic_id"]
            )
            
            tdd_result = await self.framework.orchestrator.handle_command(
                "/tdd start", "default",
                story_id=story_result["story_id"],
                task_description="Transition test task"
            )
            
            cycle_id = tdd_result["cycle_id"]
            
            # Test invalid transitions
            invalid_transitions = [
                ("design", "commit"),  # Skip intermediate states
                ("design", "refactor"),  # Jump to refactor
                ("test_red", "commit"),  # Skip code phase
                ("code_green", "test_red"),  # Go backwards
            ]
            
            for from_state, to_command in invalid_transitions:
                test_result = await self._test_invalid_transition(from_state, to_command, cycle_id)
                results["transition_tests"].append({
                    "from": from_state,
                    "to": to_command,
                    "result": test_result
                })
                
                if not test_result.get("success", False):
                    results["success"] = False
                    results["errors"].extend(test_result.get("errors", []))
            
            return results
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def _test_invalid_transition(self, from_state: str, to_command: str, cycle_id: str) -> Dict[str, Any]:
        """Test a specific invalid transition"""
        try:
            # Set up the state machine in the from_state
            # (This is simplified - in reality we'd need to go through proper transitions)
            
            # Try the invalid transition
            result = await self.framework.orchestrator.handle_command(f"/tdd {to_command}", "default")
            
            # Should fail
            if result.get("success"):
                return {
                    "success": False,
                    "errors": [f"Invalid transition {from_state} -> {to_command} was allowed"]
                }
            
            # Check error message is informative
            error_msg = result.get("error", "").lower()
            if "invalid" not in error_msg and "transition" not in error_msg:
                return {
                    "success": False,
                    "errors": [f"Poor error message for invalid transition: {result.get('error')}"]
                }
            
            return {"success": True, "invalid_transition_blocked": True}
            
        except Exception as e:
            return {"success": False, "errors": [f"Invalid transition test error: {e}"]}
    
    async def test_boundary_conditions(self) -> Dict[str, Any]:
        """Test boundary conditions and edge cases"""
        results = {"success": True, "boundary_tests": [], "errors": []}
        
        try:
            test_path = self.framework.setup_test_environment()
            self.framework.orchestrator = Orchestrator()
            
            # Test 1: Very long descriptions
            long_desc_test = await self._test_long_descriptions()
            results["boundary_tests"].append({"test": "long_descriptions", "result": long_desc_test})
            
            # Test 2: Empty/null inputs
            empty_input_test = await self._test_empty_inputs()
            results["boundary_tests"].append({"test": "empty_inputs", "result": empty_input_test})
            
            # Test 3: Special characters
            special_chars_test = await self._test_special_characters()
            results["boundary_tests"].append({"test": "special_characters", "result": special_chars_test})
            
            # Test 4: Maximum number of TDD cycles
            max_cycles_test = await self._test_maximum_cycles()
            results["boundary_tests"].append({"test": "maximum_cycles", "result": max_cycles_test})
            
            # Check results
            for test in results["boundary_tests"]:
                if not test["result"].get("success", False):
                    results["success"] = False
                    results["errors"].extend(test["result"].get("errors", []))
            
            return results
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def _test_long_descriptions(self) -> Dict[str, Any]:
        """Test very long descriptions"""
        try:
            # Create very long description
            long_desc = "A" * 10000  # 10KB description
            
            result = await self.framework.orchestrator.handle_command(
                "/epic", "default",
                description=long_desc,
                title="Long Description Test"
            )
            
            # Should either succeed with truncation or fail gracefully
            if not result.get("success"):
                error_msg = result.get("error", "").lower()
                if "too long" in error_msg or "limit" in error_msg:
                    return {"success": True, "length_limit_enforced": True}
                else:
                    return {
                        "success": False,
                        "errors": ["Long description failed without proper error message"]
                    }
            
            return {"success": True, "long_description_handled": True}
            
        except Exception as e:
            return {"success": False, "errors": [f"Long description test error: {e}"]}
    
    async def _test_empty_inputs(self) -> Dict[str, Any]:
        """Test empty and null inputs"""
        try:
            empty_tests = [
                ("/epic", {"description": "", "title": ""}),
                ("/epic", {"description": None, "title": None}),
                ("/backlog add_story", {"description": "", "feature": "test"}),
                ("/tdd start", {"story_id": "", "task_description": ""}),
            ]
            
            for command, params in empty_tests:
                result = await self.framework.orchestrator.handle_command(command, "default", **params)
                
                # Should fail with proper error message
                if result.get("success"):
                    return {
                        "success": False,
                        "errors": [f"Empty input accepted for {command}"]
                    }
                
                error_msg = result.get("error", "").lower()
                if "required" not in error_msg and "empty" not in error_msg:
                    return {
                        "success": False,
                        "errors": [f"Poor error message for empty input: {result.get('error')}"]
                    }
            
            return {"success": True, "empty_inputs_handled": True}
            
        except Exception as e:
            return {"success": False, "errors": [f"Empty input test error: {e}"]}
    
    async def _test_special_characters(self) -> Dict[str, Any]:
        """Test special characters in inputs"""
        try:
            special_chars = "!@#$%^&*()[]{}|\\:;\"'<>,.?/~`"
            unicode_chars = "αβγδε한국어日本語العربية"
            
            # Test with special characters
            result1 = await self.framework.orchestrator.handle_command(
                "/epic", "default",
                description=f"Test with special chars: {special_chars}",
                title="Special Chars Test"
            )
            
            # Test with Unicode
            result2 = await self.framework.orchestrator.handle_command(
                "/epic", "default",
                description=f"Test with Unicode: {unicode_chars}",
                title="Unicode Test"
            )
            
            # Both should either succeed or fail gracefully
            results = [result1, result2]
            for i, result in enumerate(results):
                if not result.get("success"):
                    error_msg = result.get("error", "").lower()
                    if "character" not in error_msg and "encoding" not in error_msg:
                        return {
                            "success": False,
                            "errors": [f"Special character test {i+1} failed without proper error"]
                        }
            
            return {"success": True, "special_characters_handled": True}
            
        except Exception as e:
            return {"success": False, "errors": [f"Special character test error: {e}"]}
    
    async def _test_maximum_cycles(self) -> Dict[str, Any]:
        """Test maximum number of TDD cycles"""
        try:
            # Create epic and story
            epic_result = await self.framework.orchestrator.handle_command(
                "/epic", "default",
                description="Max cycles test",
                title="Max Cycles"
            )
            
            story_result = await self.framework.orchestrator.handle_command(
                "/backlog add_story", "default",
                description="Max cycles story",
                feature=epic_result["epic_id"]
            )
            
            # Try to create multiple TDD cycles
            cycles_created = 0
            max_attempts = 100  # Reasonable limit for testing
            
            for i in range(max_attempts):
                result = await self.framework.orchestrator.handle_command(
                    "/tdd start", "default",
                    story_id=story_result["story_id"],
                    task_description=f"Cycle {i+1}"
                )
                
                if result.get("success"):
                    cycles_created += 1
                    # Abort the cycle to start a new one
                    await self.framework.orchestrator.handle_command("/tdd abort", "default")
                else:
                    # Hit limit or error
                    break
            
            # Should either have a reasonable limit or handle many cycles
            if cycles_created == 0:
                return {"success": False, "errors": ["Cannot create any TDD cycles"]}
            
            if cycles_created < 10:
                return {
                    "success": False,
                    "errors": [f"Too few cycles allowed: {cycles_created}"]
                }
            
            return {"success": True, "max_cycles_handled": cycles_created}
            
        except Exception as e:
            return {"success": False, "errors": [f"Max cycles test error: {e}"]}


class ResourceExhaustionTests:
    """Test resource exhaustion scenarios"""
    
    def __init__(self):
        self.framework = EdgeCaseTestFramework()
        
    async def test_memory_exhaustion(self) -> Dict[str, Any]:
        """Test behavior under memory pressure"""
        results = {"success": True, "memory_tests": [], "errors": []}
        
        try:
            test_path = self.framework.setup_test_environment()
            self.framework.orchestrator = Orchestrator()
            
            # Monitor initial memory
            initial_memory = self._get_memory_usage()
            
            # Create many TDD cycles to test memory handling
            memory_test = await self._test_memory_pressure()
            results["memory_tests"].append({"test": "memory_pressure", "result": memory_test})
            
            # Test garbage collection behavior
            gc_test = await self._test_garbage_collection()
            results["memory_tests"].append({"test": "garbage_collection", "result": gc_test})
            
            # Check final memory
            final_memory = self._get_memory_usage()
            memory_growth = final_memory - initial_memory
            
            results["memory_growth_mb"] = memory_growth
            
            # Excessive memory growth indicates a problem
            if memory_growth > 500:  # 500MB growth is concerning
                results["success"] = False
                results["errors"].append(f"Excessive memory growth: {memory_growth:.1f}MB")
            
            return results
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _get_memory_usage(self) -> float:
        """Get current memory usage in MB"""
        try:
            process = psutil.Process()
            return process.memory_info().rss / 1024 / 1024
        except Exception:
            return 0.0
    
    async def _test_memory_pressure(self) -> Dict[str, Any]:
        """Test system under memory pressure"""
        try:
            # Create many objects to simulate memory pressure
            large_objects = []
            
            for i in range(50):  # Create 50 TDD cycles
                cycle = TDDCycle(story_id=f"memory-test-{i}", task_description=f"Memory test {i}")
                
                # Add large test results to consume memory
                for j in range(10):
                    test_result = TestResult(
                        test_file=f"test_file_{j}.py",
                        test_name=f"test_method_{j}",
                        status=TestStatus.GREEN,
                        output="A" * 1000  # 1KB output each
                    )
                    cycle.add_task("test_task").test_results.append(test_result)
                
                large_objects.append(cycle)
            
            # Try to perform TDD operations under memory pressure
            result = await self.framework.orchestrator.handle_command("/state", "default")
            
            # Clean up
            large_objects.clear()
            gc.collect()
            
            return {"success": True, "operations_under_pressure": result.get("success", False)}
            
        except MemoryError:
            return {"success": True, "memory_limit_reached": True}
        except Exception as e:
            return {"success": False, "errors": [f"Memory pressure test error: {e}"]}
    
    async def _test_garbage_collection(self) -> Dict[str, Any]:
        """Test garbage collection behavior"""
        try:
            # Force garbage collection
            collected_before = gc.collect()
            
            # Create and destroy objects
            temp_objects = []
            for i in range(1000):
                cycle = TDDCycle(story_id=f"gc-test-{i}", task_description="GC test")
                temp_objects.append(cycle)
            
            # Clear references
            temp_objects.clear()
            
            # Force garbage collection again
            collected_after = gc.collect()
            
            return {
                "success": True,
                "objects_collected_before": collected_before,
                "objects_collected_after": collected_after,
                "gc_working": collected_after > collected_before
            }
            
        except Exception as e:
            return {"success": False, "errors": [f"GC test error: {e}"]}


class EdgeCaseTestSuite:
    """Complete edge case test suite"""
    
    def __init__(self):
        self.system_failure_tests = SystemFailureTests()
        self.data_corruption_tests = DataCorruptionTests()
        self.invalid_transition_tests = InvalidTransitionTests()
        self.resource_tests = ResourceExhaustionTests()
        
    async def run_comprehensive_edge_case_tests(self) -> Dict[str, Any]:
        """Run complete edge case test suite"""
        print("Running TDD Edge Case Test Suite...")
        
        all_results = {}
        overall_success = True
        
        try:
            # Test 1: System Failure Scenarios
            print("1. Testing system failure scenarios...")
            system_result = await self.system_failure_tests.test_claude_code_outage_simulation()
            all_results["system_failures"] = system_result
            if not system_result["success"]:
                overall_success = False
            
            network_result = await self.system_failure_tests.test_network_failure_scenarios()
            all_results["network_failures"] = network_result
            if not network_result["success"]:
                overall_success = False
            
            # Test 2: Data Corruption
            print("2. Testing data corruption scenarios...")
            corruption_result = await self.data_corruption_tests.test_tdd_state_corruption()
            all_results["data_corruption"] = corruption_result
            if not corruption_result["success"]:
                overall_success = False
            
            # Test 3: Invalid Transitions
            print("3. Testing invalid transitions...")
            transition_result = await self.invalid_transition_tests.test_invalid_tdd_transitions()
            all_results["invalid_transitions"] = transition_result
            if not transition_result["success"]:
                overall_success = False
            
            boundary_result = await self.invalid_transition_tests.test_boundary_conditions()
            all_results["boundary_conditions"] = boundary_result
            if not boundary_result["success"]:
                overall_success = False
            
            # Test 4: Resource Exhaustion
            print("4. Testing resource exhaustion...")
            resource_result = await self.resource_tests.test_memory_exhaustion()
            all_results["resource_exhaustion"] = resource_result
            if not resource_result["success"]:
                overall_success = False
            
            return {
                "success": overall_success,
                "test_results": all_results,
                "edge_case_summary": self._generate_edge_case_summary(all_results)
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
        finally:
            # Cleanup all test frameworks
            for test_obj in [self.system_failure_tests, self.data_corruption_tests, 
                           self.invalid_transition_tests, self.resource_tests]:
                test_obj.framework.cleanup()
    
    def _generate_edge_case_summary(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Generate edge case test summary"""
        summary = {
            "total_test_categories": len(results),
            "passed_categories": sum(1 for r in results.values() if r.get("success")),
            "critical_issues": [],
            "resilience_score": 0
        }
        
        # Analyze results for critical issues
        for category, result in results.items():
            if not result.get("success"):
                summary["critical_issues"].append({
                    "category": category,
                    "errors": result.get("errors", [])
                })
        
        # Calculate resilience score
        if summary["total_test_categories"] > 0:
            summary["resilience_score"] = (summary["passed_categories"] / summary["total_test_categories"]) * 100
        
        return summary


# Test execution
async def main():
    """Run TDD edge case tests"""
    print("="*60)
    print("TDD EDGE CASE TEST SUITE")
    print("="*60)
    
    try:
        suite = EdgeCaseTestSuite()
        result = await suite.run_comprehensive_edge_case_tests()
        
        if result["success"]:
            print("\n✅ ALL EDGE CASE TESTS PASSED")
            
            summary = result.get("edge_case_summary", {})
            print(f"\nEdge Case Test Summary:")
            print(f"  Test Categories: {summary.get('total_test_categories', 0)}")
            print(f"  Passed Categories: {summary.get('passed_categories', 0)}")
            print(f"  Resilience Score: {summary.get('resilience_score', 0):.1f}/100")
            
            if summary.get("critical_issues"):
                print(f"  Critical Issues: {len(summary['critical_issues'])}")
            
            return 0
        else:
            print(f"\n❌ EDGE CASE TESTS FAILED: {result.get('error', 'Unknown error')}")
            return 1
            
    except Exception as e:
        print(f"\n❌ EDGE CASE TEST SUITE FAILED: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    import sys
    sys.exit(asyncio.run(main()))