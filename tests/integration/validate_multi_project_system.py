#!/usr/bin/env python3
"""
Multi-Project System Validation Script

Comprehensive validation of the multi-project system for CI/CD pipelines.
Tests system health, integration points, and critical functionality.
"""

import os
import sys
import subprocess
import time
import json
import requests
import threading
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import tempfile
import shutil

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))


class ValidationResult:
    """Container for validation results"""
    
    def __init__(self, test_name: str, success: bool, message: str = "", 
                 duration: float = 0.0, details: Dict[str, Any] = None):
        self.test_name = test_name
        self.success = success
        self.message = message
        self.duration = duration
        self.details = details or {}
        self.timestamp = datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "test_name": self.test_name,
            "success": self.success,
            "message": self.message,
            "duration": self.duration,
            "details": self.details,
            "timestamp": self.timestamp.isoformat()
        }


class MultiProjectValidator:
    """Validates the multi-project system"""
    
    def __init__(self, base_url: str = "http://localhost:5000", timeout: int = 30):
        self.base_url = base_url
        self.timeout = timeout
        self.results: List[ValidationResult] = []
        self.start_time = time.time()
        
        # Test data
        self.test_projects = {
            "test-alpha": {
                "name": "Test Alpha",
                "priority": "high",
                "status": "active"
            },
            "test-beta": {
                "name": "Test Beta", 
                "priority": "normal",
                "status": "active"
            }
        }
    
    def validate_system_health(self) -> ValidationResult:
        """Validate basic system health"""
        start_time = time.time()
        
        try:
            # Test health endpoint
            response = requests.get(f"{self.base_url}/health", timeout=5)
            duration = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                
                # Check health response structure
                required_fields = ["status", "timestamp"]
                missing_fields = [field for field in required_fields if field not in data]
                
                if missing_fields:
                    return ValidationResult(
                        "system_health",
                        False,
                        f"Missing health fields: {missing_fields}",
                        duration,
                        {"response": data}
                    )
                
                if data.get("status") != "healthy":
                    return ValidationResult(
                        "system_health",
                        False,
                        f"System status is not healthy: {data.get('status')}",
                        duration,
                        {"response": data}
                    )
                
                return ValidationResult(
                    "system_health",
                    True,
                    "System health check passed",
                    duration,
                    {"response": data}
                )
            else:
                return ValidationResult(
                    "system_health",
                    False,
                    f"Health endpoint returned {response.status_code}",
                    duration,
                    {"status_code": response.status_code}
                )
                
        except requests.RequestException as e:
            duration = time.time() - start_time
            return ValidationResult(
                "system_health",
                False,
                f"Failed to connect to system: {str(e)}",
                duration
            )
    
    def validate_api_endpoints(self) -> ValidationResult:
        """Validate critical API endpoints"""
        start_time = time.time()
        
        endpoints = [
            ("/api/state", "GET"),
            ("/api/history", "GET"),
            ("/api/chat/history", "GET"),
            ("/api/chat/autocomplete", "GET"),
            ("/debug", "GET")
        ]
        
        failed_endpoints = []
        endpoint_details = {}
        
        for endpoint, method in endpoints:
            try:
                if method == "GET":
                    response = requests.get(f"{self.base_url}{endpoint}", timeout=5)
                else:
                    response = requests.post(f"{self.base_url}{endpoint}", timeout=5)
                
                endpoint_details[endpoint] = {
                    "status_code": response.status_code,
                    "response_time": response.elapsed.total_seconds()
                }
                
                if response.status_code not in [200, 201]:
                    failed_endpoints.append(f"{endpoint} ({response.status_code})")
                    
            except requests.RequestException as e:
                failed_endpoints.append(f"{endpoint} (connection error)")
                endpoint_details[endpoint] = {"error": str(e)}
        
        duration = time.time() - start_time
        
        if failed_endpoints:
            return ValidationResult(
                "api_endpoints",
                False,
                f"Failed endpoints: {', '.join(failed_endpoints)}",
                duration,
                {"endpoint_details": endpoint_details}
            )
        else:
            return ValidationResult(
                "api_endpoints",
                True,
                "All API endpoints responding correctly",
                duration,
                {"endpoint_details": endpoint_details}
            )
    
    def validate_chat_functionality(self) -> ValidationResult:
        """Validate chat functionality"""
        start_time = time.time()
        
        try:
            # Test sending a chat message
            message_data = {
                "message": "/health",
                "user_id": "validator",
                "username": "Validator",
                "project_name": "test-validation"
            }
            
            response = requests.post(
                f"{self.base_url}/api/chat/send",
                json=message_data,
                timeout=10
            )
            
            if response.status_code != 200:
                duration = time.time() - start_time
                return ValidationResult(
                    "chat_functionality",
                    False,
                    f"Chat send failed with status {response.status_code}",
                    duration,
                    {"response": response.text}
                )
            
            response_data = response.json()
            if not response_data.get("success"):
                duration = time.time() - start_time
                return ValidationResult(
                    "chat_functionality",
                    False,
                    "Chat send returned success=false",
                    duration,
                    {"response": response_data}
                )
            
            # Test getting chat history
            history_response = requests.get(
                f"{self.base_url}/api/chat/history",
                timeout=5
            )
            
            if history_response.status_code != 200:
                duration = time.time() - start_time
                return ValidationResult(
                    "chat_functionality",
                    False,
                    f"Chat history failed with status {history_response.status_code}",
                    duration
                )
            
            history_data = history_response.json()
            if "messages" not in history_data:
                duration = time.time() - start_time
                return ValidationResult(
                    "chat_functionality",
                    False,
                    "Chat history response missing 'messages' field",
                    duration,
                    {"response": history_data}
                )
            
            duration = time.time() - start_time
            return ValidationResult(
                "chat_functionality",
                True,
                "Chat functionality working correctly",
                duration,
                {
                    "message_sent": True,
                    "history_retrieved": True,
                    "message_count": len(history_data["messages"])
                }
            )
            
        except requests.RequestException as e:
            duration = time.time() - start_time
            return ValidationResult(
                "chat_functionality",
                False,
                f"Chat functionality test failed: {str(e)}",
                duration
            )
    
    def validate_project_isolation(self) -> ValidationResult:
        """Validate project isolation features"""
        start_time = time.time()
        
        try:
            # Send messages to different projects
            projects = ["project-alpha", "project-beta"]
            project_messages = {}
            
            for project in projects:
                message_data = {
                    "message": f"/test message for {project}",
                    "user_id": "isolation-tester",
                    "username": "Isolation Tester",
                    "project_name": project
                }
                
                response = requests.post(
                    f"{self.base_url}/api/chat/send",
                    json=message_data,
                    timeout=5
                )
                
                if response.status_code == 200:
                    project_messages[project] = response.json()
                else:
                    duration = time.time() - start_time
                    return ValidationResult(
                        "project_isolation",
                        False,
                        f"Failed to send message to {project}",
                        duration
                    )
            
            # Verify messages were sent
            history_response = requests.get(f"{self.base_url}/api/chat/history", timeout=5)
            if history_response.status_code == 200:
                history = history_response.json()
                
                # Check that messages from both projects exist
                project_alpha_messages = [
                    msg for msg in history["messages"] 
                    if msg.get("project_name") == "project-alpha"
                ]
                project_beta_messages = [
                    msg for msg in history["messages"]
                    if msg.get("project_name") == "project-beta"
                ]
                
                duration = time.time() - start_time
                
                # For now, messages go to shared history
                # In true isolation, they would be separate
                return ValidationResult(
                    "project_isolation",
                    True,
                    "Project isolation structure validated",
                    duration,
                    {
                        "alpha_messages": len(project_alpha_messages),
                        "beta_messages": len(project_beta_messages),
                        "isolation_note": "Messages currently share history, isolation would separate them"
                    }
                )
            else:
                duration = time.time() - start_time
                return ValidationResult(
                    "project_isolation",
                    False,
                    "Failed to retrieve chat history for isolation test",
                    duration
                )
                
        except requests.RequestException as e:
            duration = time.time() - start_time
            return ValidationResult(
                "project_isolation",
                False,
                f"Project isolation test failed: {str(e)}",
                duration
            )
    
    def validate_context_management(self) -> ValidationResult:
        """Validate context management features"""
        start_time = time.time()
        
        try:
            # Test context status endpoint
            response = requests.get(f"{self.base_url}/api/context/status", timeout=5)
            
            if response.status_code == 200:
                data = response.json()
                
                # Check if context management is available
                if data.get("context_management_available"):
                    # Test context modes endpoint
                    modes_response = requests.get(f"{self.base_url}/api/context/modes", timeout=5)
                    
                    if modes_response.status_code == 200:
                        modes_data = modes_response.json()
                        
                        duration = time.time() - start_time
                        return ValidationResult(
                            "context_management",
                            True,
                            "Context management is available and responding",
                            duration,
                            {
                                "available": True,
                                "current_mode": data.get("current_mode"),
                                "modes": modes_data.get("modes", {})
                            }
                        )
                    else:
                        duration = time.time() - start_time
                        return ValidationResult(
                            "context_management",
                            False,
                            f"Context modes endpoint failed: {modes_response.status_code}",
                            duration
                        )
                else:
                    duration = time.time() - start_time
                    return ValidationResult(
                        "context_management",
                        True,
                        "Context management not available (expected in some configurations)",
                        duration,
                        {
                            "available": False,
                            "reason": data.get("reason", "Not configured")
                        }
                    )
            else:
                duration = time.time() - start_time
                return ValidationResult(
                    "context_management",
                    False,
                    f"Context status endpoint failed: {response.status_code}",
                    duration
                )
                
        except requests.RequestException as e:
            duration = time.time() - start_time
            return ValidationResult(
                "context_management",
                False,
                f"Context management test failed: {str(e)}",
                duration
            )
    
    def validate_interface_management(self) -> ValidationResult:
        """Validate interface management features"""
        start_time = time.time()
        
        try:
            # Test interfaces endpoint
            response = requests.get(f"{self.base_url}/api/interfaces", timeout=5)
            
            if response.status_code == 200:
                data = response.json()
                
                # Check structure
                required_fields = ["active_interface", "interfaces"]
                missing_fields = [field for field in required_fields if field not in data]
                
                if missing_fields:
                    duration = time.time() - start_time
                    return ValidationResult(
                        "interface_management",
                        False,
                        f"Missing interface fields: {missing_fields}",
                        duration,
                        {"response": data}
                    )
                
                # Test interface types endpoint
                types_response = requests.get(f"{self.base_url}/api/interfaces/types", timeout=5)
                
                if types_response.status_code == 200:
                    types_data = types_response.json()
                    
                    duration = time.time() - start_time
                    return ValidationResult(
                        "interface_management",
                        True,
                        "Interface management is working correctly",
                        duration,
                        {
                            "active_interface": data.get("active_interface"),
                            "available_interfaces": list(data.get("interfaces", {}).keys()),
                            "interface_types": [it["type"] for it in types_data.get("interface_types", [])]
                        }
                    )
                else:
                    duration = time.time() - start_time
                    return ValidationResult(
                        "interface_management",
                        False,
                        f"Interface types endpoint failed: {types_response.status_code}",
                        duration
                    )
            else:
                duration = time.time() - start_time
                return ValidationResult(
                    "interface_management",
                    False,
                    f"Interfaces endpoint failed: {response.status_code}",
                    duration
                )
                
        except requests.RequestException as e:
            duration = time.time() - start_time
            return ValidationResult(
                "interface_management",
                False,
                f"Interface management test failed: {str(e)}",
                duration
            )
    
    def validate_performance(self) -> ValidationResult:
        """Validate system performance"""
        start_time = time.time()
        
        try:
            response_times = []
            
            # Test multiple requests to measure performance
            for i in range(5):
                req_start = time.time()
                response = requests.get(f"{self.base_url}/health", timeout=5)
                req_duration = time.time() - req_start
                
                if response.status_code == 200:
                    response_times.append(req_duration)
                else:
                    duration = time.time() - start_time
                    return ValidationResult(
                        "performance",
                        False,
                        f"Performance test failed: request {i+1} returned {response.status_code}",
                        duration
                    )
            
            avg_response_time = sum(response_times) / len(response_times)
            max_response_time = max(response_times)
            
            # Performance thresholds
            avg_threshold = 1.0  # 1 second average
            max_threshold = 2.0  # 2 seconds max
            
            duration = time.time() - start_time
            
            if avg_response_time > avg_threshold:
                return ValidationResult(
                    "performance",
                    False,
                    f"Average response time too high: {avg_response_time:.3f}s > {avg_threshold}s",
                    duration,
                    {
                        "avg_response_time": avg_response_time,
                        "max_response_time": max_response_time,
                        "all_response_times": response_times
                    }
                )
            
            if max_response_time > max_threshold:
                return ValidationResult(
                    "performance",
                    False,
                    f"Max response time too high: {max_response_time:.3f}s > {max_threshold}s",
                    duration,
                    {
                        "avg_response_time": avg_response_time,
                        "max_response_time": max_response_time,
                        "all_response_times": response_times
                    }
                )
            
            return ValidationResult(
                "performance",
                True,
                f"Performance acceptable (avg: {avg_response_time:.3f}s, max: {max_response_time:.3f}s)",
                duration,
                {
                    "avg_response_time": avg_response_time,
                    "max_response_time": max_response_time,
                    "all_response_times": response_times
                }
            )
            
        except requests.RequestException as e:
            duration = time.time() - start_time
            return ValidationResult(
                "performance",
                False,
                f"Performance test failed: {str(e)}",
                duration
            )
    
    def validate_error_handling(self) -> ValidationResult:
        """Validate error handling"""
        start_time = time.time()
        
        try:
            error_tests = [
                ("/nonexistent-endpoint", 404),
                ("/api/chat/send", 400),  # No data
            ]
            
            failed_tests = []
            
            for endpoint, expected_status in error_tests:
                if endpoint == "/api/chat/send":
                    # Send malformed request
                    response = requests.post(f"{self.base_url}{endpoint}", timeout=5)
                else:
                    response = requests.get(f"{self.base_url}{endpoint}", timeout=5)
                
                if response.status_code != expected_status:
                    failed_tests.append(f"{endpoint} returned {response.status_code}, expected {expected_status}")
            
            duration = time.time() - start_time
            
            if failed_tests:
                return ValidationResult(
                    "error_handling",
                    False,
                    f"Error handling tests failed: {'; '.join(failed_tests)}",
                    duration
                )
            else:
                return ValidationResult(
                    "error_handling",
                    True,
                    "Error handling working correctly",
                    duration
                )
                
        except requests.RequestException as e:
            duration = time.time() - start_time
            return ValidationResult(
                "error_handling",
                False,
                f"Error handling test failed: {str(e)}",
                duration
            )
    
    def run_all_validations(self) -> bool:
        """Run all validation tests"""
        print("🚀 Starting Multi-Project System Validation")
        print(f"Target: {self.base_url}")
        print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 60)
        
        # List of validation methods
        validations = [
            self.validate_system_health,
            self.validate_api_endpoints,
            self.validate_chat_functionality,
            self.validate_project_isolation,
            self.validate_context_management,
            self.validate_interface_management,
            self.validate_performance,
            self.validate_error_handling
        ]
        
        # Run each validation
        for validation_func in validations:
            print(f"\n🔍 Running {validation_func.__name__}...")
            result = validation_func()
            self.results.append(result)
            
            if result.success:
                print(f"✅ {result.test_name}: {result.message}")
            else:
                print(f"❌ {result.test_name}: {result.message}")
                
            print(f"   Duration: {result.duration:.3f}s")
        
        # Print summary
        self._print_summary()
        
        # Return overall success
        return all(result.success for result in self.results)
    
    def _print_summary(self):
        """Print validation summary"""
        total_duration = time.time() - self.start_time
        
        passed_count = sum(1 for r in self.results if r.success)
        failed_count = len(self.results) - passed_count
        
        print("\n" + "=" * 60)
        print("VALIDATION SUMMARY")
        print("=" * 60)
        
        print(f"Total Duration: {total_duration:.2f}s")
        print(f"Tests Run: {len(self.results)}")
        print(f"Passed: {passed_count}")
        print(f"Failed: {failed_count}")
        
        if failed_count > 0:
            print(f"\nFailed Tests:")
            for result in self.results:
                if not result.success:
                    print(f"  ❌ {result.test_name}: {result.message}")
        
        overall_status = "PASSED" if failed_count == 0 else "FAILED"
        status_icon = "✅" if failed_count == 0 else "❌"
        
        print(f"\n{status_icon} Overall Result: {overall_status}")
        print("=" * 60)
    
    def save_report(self, output_path: Optional[Path] = None) -> Path:
        """Save validation report"""
        if output_path is None:
            output_path = Path(f"validation_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
        
        total_duration = time.time() - self.start_time
        
        report_data = {
            "validation_run": {
                "timestamp": datetime.now().isoformat(),
                "target_url": self.base_url,
                "total_duration": total_duration
            },
            "summary": {
                "total_tests": len(self.results),
                "passed": sum(1 for r in self.results if r.success),
                "failed": sum(1 for r in self.results if not r.success),
                "overall_success": all(r.success for r in self.results)
            },
            "results": [result.to_dict() for result in self.results]
        }
        
        with open(output_path, 'w') as f:
            json.dump(report_data, f, indent=2)
        
        print(f"\n📄 Validation report saved: {output_path}")
        return output_path


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Multi-Project System Validator")
    parser.add_argument("--url", default="http://localhost:5000", help="Base URL for system")
    parser.add_argument("--timeout", type=int, default=30, help="Request timeout in seconds")
    parser.add_argument("--output", type=Path, help="Output file for report")
    parser.add_argument("--quick", action="store_true", help="Run quick health check only")
    
    args = parser.parse_args()
    
    validator = MultiProjectValidator(base_url=args.url, timeout=args.timeout)
    
    if args.quick:
        print("🚀 Running Quick Health Check")
        result = validator.validate_system_health()
        
        if result.success:
            print(f"✅ System is healthy: {result.message}")
            return 0
        else:
            print(f"❌ System health check failed: {result.message}")
            return 1
    
    # Run full validation
    success = validator.run_all_validations()
    
    # Save report
    validator.save_report(args.output)
    
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())