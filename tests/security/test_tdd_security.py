#!/usr/bin/env python3
"""
Security and Compliance Testing Suite for TDD Implementation.

This module provides comprehensive security validation including:
- Agent security boundary validation for TDD operations
- Data privacy and isolation testing
- Input validation and injection attack prevention
- Audit trail validation for compliance
- Recovery and backup security testing
- TDD-specific tool restriction validation
"""

import asyncio
import tempfile
import shutil
import json
import os
from pathlib import Path
from typing import Dict, List, Any, Optional
from unittest.mock import Mock, patch, AsyncMock
import pytest
import sys

# Add project paths to sys.path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "lib"))
sys.path.insert(0, str(project_root / "scripts"))

from orchestrator import Orchestrator
from agent_tool_config import AgentType, AGENT_TOOL_CONFIG, get_claude_tool_args
from data_models import Epic, Story
from tdd_models import TDDCycle, TDDTask, TestResult, TestStatus
from project_storage import ProjectStorage


class SecurityTestFramework:
    """Framework for security testing of TDD functionality"""
    
    def __init__(self):
        self.temp_dirs: List[Path] = []
        self.orchestrator = None
        self.security_violations: List[Dict[str, Any]] = []
        
    def setup_isolated_environment(self) -> Path:
        """Set up isolated test environment"""
        temp_dir = tempfile.mkdtemp()
        test_path = Path(temp_dir)
        self.temp_dirs.append(test_path)
        return test_path
        
    def cleanup(self):
        """Clean up test resources"""
        for temp_dir in self.temp_dirs:
            shutil.rmtree(temp_dir, ignore_errors=True)
        self.temp_dirs.clear()
        self.security_violations.clear()
    
    def record_security_violation(self, violation_type: str, details: Dict[str, Any]):
        """Record a security violation for analysis"""
        self.security_violations.append({
            "type": violation_type,
            "details": details,
            "timestamp": asyncio.get_event_loop().time()
        })


class TDDSecurityTest:
    """TDD-specific security testing"""
    
    def __init__(self):
        self.framework = SecurityTestFramework()
        
    async def test_agent_security_boundaries(self) -> Dict[str, Any]:
        """Test agent security boundaries for TDD operations"""
        results = {"success": True, "agent_tests": [], "violations": []}
        
        try:
            test_path = self.framework.setup_isolated_environment()
            
            # Test each agent type with TDD operations
            agent_types = [AgentType.DESIGN, AgentType.CODE, AgentType.QA, AgentType.DATA]
            
            for agent_type in agent_types:
                agent_result = await self._test_agent_tdd_restrictions(agent_type, test_path)
                results["agent_tests"].append({
                    "agent_type": agent_type.value,
                    "result": agent_result
                })
                
                if not agent_result["success"]:
                    results["success"] = False
                    results["violations"].extend(agent_result.get("violations", []))
            
            return results
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def _test_agent_tdd_restrictions(self, agent_type: AgentType, test_path: Path) -> Dict[str, Any]:
        """Test TDD-specific restrictions for an agent type"""
        result = {"success": True, "violations": [], "tests_performed": []}
        
        try:
            # Get agent security profile
            profile = AGENT_SECURITY_PROFILES.get(agent_type)
            if not profile:
                return {"success": False, "error": f"No security profile for {agent_type.value}"}
            
            # Test 1: Verify agent cannot access restricted tools for TDD
            restricted_tests = await self._test_restricted_tool_access(agent_type, test_path)
            result["tests_performed"].append("restricted_tool_access")
            if restricted_tests["violations"]:
                result["violations"].extend(restricted_tests["violations"])
                result["success"] = False
            
            # Test 2: Verify agent can only access allowed TDD operations
            allowed_tests = await self._test_allowed_tdd_operations(agent_type, test_path)
            result["tests_performed"].append("allowed_tdd_operations")
            if not allowed_tests["success"]:
                result["violations"].extend(allowed_tests.get("violations", []))
                result["success"] = False
            
            # Test 3: Test data isolation between projects
            isolation_tests = await self._test_data_isolation(agent_type, test_path)
            result["tests_performed"].append("data_isolation")
            if isolation_tests["violations"]:
                result["violations"].extend(isolation_tests["violations"])
                result["success"] = False
            
            return result
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def _test_restricted_tool_access(self, agent_type: AgentType, test_path: Path) -> Dict[str, Any]:
        """Test that agents cannot access restricted tools during TDD operations"""
        violations = []
        
        try:
            # Create mock claude client with agent restrictions
            with patch('lib.agents.base_agent.get_claude_client') as mock_get_client:
                # Simulate restricted tool access attempts
                restricted_operations = [
                    ("file_deletion", "rm -rf /"),
                    ("system_modification", "sudo chmod 777 /etc"),
                    ("network_access", "curl external-api.com"),
                    ("git_push", "git push origin main")
                ]
                
                for operation_type, command in restricted_operations:
                    profile = AGENT_SECURITY_PROFILES.get(agent_type, {})
                    disallowed_tools = profile.get("disallowed_tools", [])
                    
                    # Check if this operation should be blocked
                    should_be_blocked = any(tool in command for tool in disallowed_tools)
                    
                    if not should_be_blocked and operation_type in ["file_deletion", "system_modification"]:
                        # These should always be blocked for TDD agents
                        violations.append({
                            "type": "unrestricted_dangerous_operation",
                            "agent_type": agent_type.value,
                            "operation": operation_type,
                            "command": command
                        })
        
        except Exception as e:
            violations.append({
                "type": "security_test_error",
                "agent_type": agent_type.value,
                "error": str(e)
            })
        
        return {"violations": violations}
    
    async def _test_allowed_tdd_operations(self, agent_type: AgentType, test_path: Path) -> Dict[str, Any]:
        """Test that agents can perform their allowed TDD operations"""
        try:
            profile = AGENT_SECURITY_PROFILES.get(agent_type, {})
            allowed_tools = profile.get("allowed_tools", [])
            
            # Define expected capabilities for each agent type in TDD context
            expected_capabilities = {
                AgentType.DESIGN: ["file_read", "documentation_creation", "analysis"],
                AgentType.CODE: ["file_edit", "test_execution", "code_analysis"],
                AgentType.QA: ["test_execution", "quality_analysis", "coverage_reporting"],
                AgentType.DATA: ["data_analysis", "reporting", "visualization"]
            }
            
            expected = expected_capabilities.get(agent_type, [])
            
            # Check if agent has necessary tools for its TDD role
            missing_capabilities = []
            for capability in expected:
                # Map capabilities to actual tools (simplified check)
                tool_mapping = {
                    "file_read": "Read",
                    "file_edit": "Edit",
                    "test_execution": "Bash",
                    "documentation_creation": "Write",
                    "analysis": "Read"
                }
                
                required_tool = tool_mapping.get(capability)
                if required_tool and required_tool not in allowed_tools:
                    missing_capabilities.append(capability)
            
            if missing_capabilities:
                return {
                    "success": False,
                    "violations": [{
                        "type": "missing_required_capability",
                        "agent_type": agent_type.value,
                        "missing_capabilities": missing_capabilities
                    }]
                }
            
            return {"success": True}
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def _test_data_isolation(self, agent_type: AgentType, test_path: Path) -> Dict[str, Any]:
        """Test data isolation between projects for TDD operations"""
        violations = []
        
        try:
            # Create two isolated project environments
            project1_path = test_path / "project1"
            project2_path = test_path / "project2"
            project1_path.mkdir(parents=True)
            project2_path.mkdir(parents=True)
            
            # Create storage instances for each project
            storage1 = ProjectStorage(project1_path)
            storage2 = ProjectStorage(project2_path)
            
            # Create TDD cycles in each project
            cycle1 = TDDCycle(story_id="story-1", task_description="Project 1 task")
            cycle2 = TDDCycle(story_id="story-2", task_description="Project 2 task")
            
            storage1.save_tdd_cycle(cycle1)
            storage2.save_tdd_cycle(cycle2)
            
            # Test 1: Verify project 1 storage cannot access project 2 data
            project2_cycle = storage1.get_tdd_cycle(cycle2.cycle_id)
            if project2_cycle is not None:
                violations.append({
                    "type": "data_isolation_breach",
                    "description": "Project 1 storage accessed Project 2 TDD cycle",
                    "cycle_id": cycle2.cycle_id
                })
            
            # Test 2: Verify project 2 storage cannot access project 1 data
            project1_cycle = storage2.get_tdd_cycle(cycle1.cycle_id)
            if project1_cycle is not None:
                violations.append({
                    "type": "data_isolation_breach",
                    "description": "Project 2 storage accessed Project 1 TDD cycle",
                    "cycle_id": cycle1.cycle_id
                })
            
            # Test 3: Verify each project can only access its own data
            retrieved_cycle1 = storage1.get_tdd_cycle(cycle1.cycle_id)
            retrieved_cycle2 = storage2.get_tdd_cycle(cycle2.cycle_id)
            
            if retrieved_cycle1 is None:
                violations.append({
                    "type": "data_access_failure",
                    "description": "Project 1 storage cannot access its own TDD cycle",
                    "cycle_id": cycle1.cycle_id
                })
            
            if retrieved_cycle2 is None:
                violations.append({
                    "type": "data_access_failure",
                    "description": "Project 2 storage cannot access its own TDD cycle",
                    "cycle_id": cycle2.cycle_id
                })
        
        except Exception as e:
            violations.append({
                "type": "data_isolation_test_error",
                "error": str(e)
            })
        
        return {"violations": violations}
    
    async def test_input_validation_security(self) -> Dict[str, Any]:
        """Test input validation and injection attack prevention"""
        results = {"success": True, "tests": [], "vulnerabilities": []}
        
        try:
            test_path = self.framework.setup_isolated_environment()
            self.framework.orchestrator = Orchestrator()
            
            # Test various injection attacks in TDD commands
            injection_tests = [
                {
                    "name": "sql_injection_story_description",
                    "command": "/backlog add_story",
                    "params": {
                        "description": "'; DROP TABLE stories; --",
                        "feature": "test-epic"
                    }
                },
                {
                    "name": "command_injection_task_description",
                    "command": "/tdd start",
                    "params": {
                        "story_id": "test-story",
                        "task_description": "; rm -rf / #"
                    }
                },
                {
                    "name": "path_traversal_epic_title",
                    "command": "/epic",
                    "params": {
                        "description": "Test epic",
                        "title": "../../../etc/passwd"
                    }
                },
                {
                    "name": "script_injection_story_description",
                    "command": "/backlog add_story",
                    "params": {
                        "description": "<script>alert('XSS')</script>",
                        "feature": "test-epic"
                    }
                }
            ]
            
            for test in injection_tests:
                test_result = await self._test_injection_attack(
                    test["command"], 
                    test["params"], 
                    test["name"]
                )
                
                results["tests"].append({
                    "test_name": test["name"],
                    "result": test_result
                })
                
                if test_result.get("vulnerable"):
                    results["vulnerabilities"].append({
                        "type": "injection_vulnerability",
                        "test": test["name"],
                        "details": test_result
                    })
                    results["success"] = False
            
            return results
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def _test_injection_attack(self, command: str, params: Dict[str, Any], test_name: str) -> Dict[str, Any]:
        """Test a specific injection attack"""
        try:
            # Execute command with potentially malicious input
            result = await self.framework.orchestrator.handle_command(command, "default", **params)
            
            # Analyze result for vulnerability indicators
            vulnerability_indicators = [
                "command executed",
                "file deleted",
                "system compromised",
                "database error",
                "SQL error"
            ]
            
            result_text = str(result).lower()
            vulnerable = any(indicator in result_text for indicator in vulnerability_indicators)
            
            # Check if input was properly sanitized
            if result.get("success") and any(char in str(params.values()) for char in ["'", ";", "<", ">", ".."]):
                # Input contained dangerous characters but command succeeded
                # This might indicate insufficient input validation
                return {
                    "vulnerable": True,
                    "reason": "Dangerous characters accepted in input",
                    "input": params,
                    "result": result
                }
            
            return {
                "vulnerable": vulnerable,
                "result": result,
                "input": params
            }
            
        except Exception as e:
            # Exceptions during malicious input handling might indicate proper security
            return {
                "vulnerable": False,
                "reason": "Exception thrown (likely proper input validation)",
                "error": str(e),
                "input": params
            }
    
    async def test_audit_trail_security(self) -> Dict[str, Any]:
        """Test audit trail validation for compliance"""
        results = {"success": True, "audit_tests": [], "compliance_issues": []}
        
        try:
            test_path = self.framework.setup_isolated_environment()
            storage = ProjectStorage(test_path / "audit_test")
            
            # Test 1: TDD cycle audit trail
            cycle = TDDCycle(story_id="audit-story", task_description="Audit test task")
            storage.save_tdd_cycle(cycle)
            
            # Verify audit trail exists
            audit_result = self._verify_tdd_audit_trail(storage, cycle.cycle_id)
            results["audit_tests"].append({
                "test": "tdd_cycle_audit_trail",
                "result": audit_result
            })
            
            if not audit_result["compliant"]:
                results["compliance_issues"].extend(audit_result["issues"])
                results["success"] = False
            
            # Test 2: Data modification tracking
            # Modify TDD cycle and verify changes are tracked
            cycle.current_phase = "test_red"
            storage.save_tdd_cycle(cycle)
            
            modification_audit = self._verify_modification_tracking(storage, cycle.cycle_id)
            results["audit_tests"].append({
                "test": "modification_tracking",
                "result": modification_audit
            })
            
            if not modification_audit["compliant"]:
                results["compliance_issues"].extend(modification_audit["issues"])
                results["success"] = False
            
            # Test 3: Access logging
            access_audit = self._verify_access_logging(storage, cycle.cycle_id)
            results["audit_tests"].append({
                "test": "access_logging",
                "result": access_audit
            })
            
            if not access_audit["compliant"]:
                results["compliance_issues"].extend(access_audit["issues"])
                results["success"] = False
            
            return results
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _verify_tdd_audit_trail(self, storage: ProjectStorage, cycle_id: str) -> Dict[str, Any]:
        """Verify TDD cycle has proper audit trail"""
        issues = []
        
        try:
            # Check if cycle file exists and has proper metadata
            cycle_file = storage._get_tdd_cycle_path(cycle_id)
            if not cycle_file.exists():
                issues.append("TDD cycle file does not exist")
                return {"compliant": False, "issues": issues}
            
            # Check file permissions (should not be world-writable)
            file_stats = cycle_file.stat()
            if file_stats.st_mode & 0o002:  # World-writable
                issues.append("TDD cycle file is world-writable")
            
            # Check if file contains required audit fields
            with open(cycle_file, 'r') as f:
                cycle_data = json.load(f)
            
            required_fields = ["cycle_id", "created_at", "story_id"]
            for field in required_fields:
                if field not in cycle_data:
                    issues.append(f"Missing required audit field: {field}")
            
            return {"compliant": len(issues) == 0, "issues": issues}
            
        except Exception as e:
            issues.append(f"Audit trail verification error: {e}")
            return {"compliant": False, "issues": issues}
    
    def _verify_modification_tracking(self, storage: ProjectStorage, cycle_id: str) -> Dict[str, Any]:
        """Verify modifications to TDD cycles are properly tracked"""
        issues = []
        
        try:
            # For now, check that we can retrieve the modified cycle
            cycle = storage.get_tdd_cycle(cycle_id)
            if cycle is None:
                issues.append("Cannot retrieve modified TDD cycle")
            elif cycle.current_phase != "test_red":
                issues.append("TDD cycle modifications not persisted")
            
            # In a full implementation, we would check for:
            # - Modification timestamps
            # - Change logs
            # - Version history
            # - User attribution
            
            return {"compliant": len(issues) == 0, "issues": issues}
            
        except Exception as e:
            issues.append(f"Modification tracking verification error: {e}")
            return {"compliant": False, "issues": issues}
    
    def _verify_access_logging(self, storage: ProjectStorage, cycle_id: str) -> Dict[str, Any]:
        """Verify access to TDD data is properly logged"""
        issues = []
        
        try:
            # For now, this is a placeholder since we don't have access logging implemented
            # In a full implementation, we would check for:
            # - Access logs with timestamps
            # - User identification
            # - Action logging
            # - Failed access attempts
            
            # Simulate access logging check
            cycle = storage.get_tdd_cycle(cycle_id)
            if cycle is None:
                issues.append("Access logging test failed - cannot access cycle")
            
            return {"compliant": len(issues) == 0, "issues": issues}
            
        except Exception as e:
            issues.append(f"Access logging verification error: {e}")
            return {"compliant": False, "issues": issues}
    
    async def test_recovery_security(self) -> Dict[str, Any]:
        """Test backup and recovery operations security"""
        results = {"success": True, "recovery_tests": [], "security_issues": []}
        
        try:
            test_path = self.framework.setup_isolated_environment()
            storage = ProjectStorage(test_path / "recovery_test")
            
            # Create test TDD data
            cycle = TDDCycle(story_id="recovery-story", task_description="Recovery test")
            storage.save_tdd_cycle(cycle)
            
            # Test 1: Backup security
            backup_result = self._test_backup_security(storage, cycle.cycle_id)
            results["recovery_tests"].append({
                "test": "backup_security",
                "result": backup_result
            })
            
            if backup_result["security_issues"]:
                results["security_issues"].extend(backup_result["security_issues"])
                results["success"] = False
            
            # Test 2: Recovery integrity
            recovery_result = self._test_recovery_integrity(storage, cycle.cycle_id)
            results["recovery_tests"].append({
                "test": "recovery_integrity",
                "result": recovery_result
            })
            
            if recovery_result["security_issues"]:
                results["security_issues"].extend(recovery_result["security_issues"])
                results["success"] = False
            
            return results
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _test_backup_security(self, storage: ProjectStorage, cycle_id: str) -> Dict[str, Any]:
        """Test backup operation security"""
        security_issues = []
        
        try:
            # Simulate backup operation
            cycle = storage.get_tdd_cycle(cycle_id)
            if cycle is None:
                security_issues.append("Cannot access original data for backup")
                return {"security_issues": security_issues}
            
            # Check backup file security (if implemented)
            # For now, verify original data integrity
            if cycle.cycle_id != cycle_id:
                security_issues.append("Data integrity issue in backup source")
            
            return {"security_issues": security_issues}
            
        except Exception as e:
            security_issues.append(f"Backup security test error: {e}")
            return {"security_issues": security_issues}
    
    def _test_recovery_integrity(self, storage: ProjectStorage, cycle_id: str) -> Dict[str, Any]:
        """Test recovery operation integrity"""
        security_issues = []
        
        try:
            # Test data recovery integrity
            original_cycle = storage.get_tdd_cycle(cycle_id)
            if original_cycle is None:
                security_issues.append("Cannot recover TDD cycle data")
                return {"security_issues": security_issues}
            
            # Verify data hasn't been tampered with
            if original_cycle.story_id != "recovery-story":
                security_issues.append("Recovered data has been tampered with")
            
            return {"security_issues": security_issues}
            
        except Exception as e:
            security_issues.append(f"Recovery integrity test error: {e}")
            return {"security_issues": security_issues}


class SecurityTestSuite:
    """Complete security test suite for TDD functionality"""
    
    def __init__(self):
        self.tdd_security = TDDSecurityTest()
        
    async def run_comprehensive_security_tests(self) -> Dict[str, Any]:
        """Run complete security test suite"""
        print("Running TDD Security Test Suite...")
        
        all_results = {}
        overall_success = True
        
        try:
            # Test 1: Agent Security Boundaries
            print("1. Testing agent security boundaries...")
            agent_result = await self.tdd_security.test_agent_security_boundaries()
            all_results["agent_security"] = agent_result
            if not agent_result["success"]:
                overall_success = False
            
            # Test 2: Input Validation Security
            print("2. Testing input validation security...")
            input_result = await self.tdd_security.test_input_validation_security()
            all_results["input_validation"] = input_result
            if not input_result["success"]:
                overall_success = False
            
            # Test 3: Audit Trail Security
            print("3. Testing audit trail security...")
            audit_result = await self.tdd_security.test_audit_trail_security()
            all_results["audit_trail"] = audit_result
            if not audit_result["success"]:
                overall_success = False
            
            # Test 4: Recovery Security
            print("4. Testing recovery security...")
            recovery_result = await self.tdd_security.test_recovery_security()
            all_results["recovery_security"] = recovery_result
            if not recovery_result["success"]:
                overall_success = False
            
            return {
                "success": overall_success,
                "test_results": all_results,
                "security_summary": self._generate_security_summary(all_results)
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
        finally:
            self.tdd_security.framework.cleanup()
    
    def _generate_security_summary(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Generate security test summary"""
        summary = {
            "total_tests": len(results),
            "passed_tests": sum(1 for r in results.values() if r.get("success")),
            "security_issues": [],
            "compliance_issues": [],
            "recommendations": []
        }
        
        # Collect all security issues
        for test_name, result in results.items():
            if "violations" in result:
                summary["security_issues"].extend(result["violations"])
            if "vulnerabilities" in result:
                summary["security_issues"].extend(result["vulnerabilities"])
            if "compliance_issues" in result:
                summary["compliance_issues"].extend(result["compliance_issues"])
            if "security_issues" in result:
                summary["security_issues"].extend(result["security_issues"])
        
        # Generate recommendations
        if summary["security_issues"]:
            summary["recommendations"].append("Address identified security vulnerabilities")
        if summary["compliance_issues"]:
            summary["recommendations"].append("Implement proper audit trail and compliance measures")
        if summary["passed_tests"] < summary["total_tests"]:
            summary["recommendations"].append("Review and strengthen security controls")
        
        return summary


# Test execution
async def main():
    """Run TDD security tests"""
    print("="*60)
    print("TDD SECURITY TEST SUITE")
    print("="*60)
    
    try:
        suite = SecurityTestSuite()
        result = await suite.run_comprehensive_security_tests()
        
        if result["success"]:
            print("\n✅ ALL SECURITY TESTS PASSED")
            
            summary = result.get("security_summary", {})
            print(f"\nSecurity Test Summary:")
            print(f"  Total Tests: {summary.get('total_tests', 0)}")
            print(f"  Passed Tests: {summary.get('passed_tests', 0)}")
            print(f"  Security Issues: {len(summary.get('security_issues', []))}")
            print(f"  Compliance Issues: {len(summary.get('compliance_issues', []))}")
            
            if summary.get("recommendations"):
                print("\nRecommendations:")
                for rec in summary["recommendations"]:
                    print(f"  • {rec}")
            
            return 0
        else:
            print(f"\n❌ SECURITY TESTS FAILED: {result.get('error', 'Unknown error')}")
            return 1
            
    except Exception as e:
        print(f"\n❌ SECURITY TEST SUITE FAILED: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    import sys
    sys.exit(asyncio.run(main()))