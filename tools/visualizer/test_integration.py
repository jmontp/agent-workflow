#!/usr/bin/env python3
"""
Integration Test for Discord-Style Web Interface

Comprehensive test suite to verify all components are properly integrated
and working together seamlessly.
"""

import asyncio
import json
import sys
import time
import threading
from pathlib import Path
from urllib.parse import urljoin
import requests
import websocket
from typing import Dict, Any, List

# Add lib directory to path
lib_path = Path(__file__).parent.parent.parent / "lib"
sys.path.insert(0, str(lib_path))

class IntegrationTester:
    """Comprehensive integration tester for the Discord-style web interface"""
    
    def __init__(self, base_url: str = "http://localhost:5000"):
        self.base_url = base_url
        self.websocket_url = f"ws://localhost:5000/socket.io/?EIO=4&transport=websocket"
        self.session = requests.Session()
        self.ws = None
        self.received_messages = []
        self.test_results = []
        self.user_id = "test_user_001"
        self.username = "Integration Tester"
        self.session_id = None
        
    def log_result(self, test_name: str, success: bool, message: str = ""):
        """Log test result"""
        status = "✅ PASS" if success else "❌ FAIL"
        self.test_results.append({
            "test": test_name,
            "success": success,
            "message": message
        })
        print(f"{status} {test_name}: {message}")
    
    def test_basic_connectivity(self) -> bool:
        """Test basic HTTP connectivity to the interface"""
        try:
            response = self.session.get(self.base_url, timeout=10)
            success = response.status_code == 200
            
            if success:
                # Check for required elements in HTML
                content = response.text
                required_elements = [
                    'id="chat-panel"',
                    'id="chat-messages"', 
                    'id="chat-input-field"',
                    'discord-chat.css',
                    'discord-chat.js'
                ]
                
                missing_elements = [elem for elem in required_elements if elem not in content]
                if missing_elements:
                    success = False
                    message = f"Missing elements: {missing_elements}"
                else:
                    message = "All required elements found"
            else:
                message = f"HTTP {response.status_code}"
            
            self.log_result("Basic Connectivity", success, message)
            return success
            
        except Exception as e:
            self.log_result("Basic Connectivity", False, str(e))
            return False
    
    def test_api_endpoints(self) -> bool:
        """Test all API endpoints are accessible"""
        endpoints = [
            ("/api/state", "GET"),
            ("/api/history", "GET"),
            ("/health", "GET"),
            ("/api/chat/history", "GET"),
            ("/api/chat/autocomplete?query=/help", "GET"),
            ("/api/interfaces", "GET"),
            ("/api/context/status", "GET"),
            ("/api/collaboration/status/default", "GET")
        ]
        
        all_success = True
        failed_endpoints = []
        
        for endpoint, method in endpoints:
            try:
                url = urljoin(self.base_url, endpoint)
                response = self.session.request(method, url, timeout=5)
                
                if response.status_code in [200, 503]:  # 503 acceptable for optional features
                    # Verify JSON response
                    try:
                        data = response.json()
                        success = isinstance(data, dict)
                    except:
                        success = False
                        
                    if not success:
                        failed_endpoints.append(f"{endpoint} (invalid JSON)")
                        all_success = False
                else:
                    failed_endpoints.append(f"{endpoint} (HTTP {response.status_code})")
                    all_success = False
                    
            except Exception as e:
                failed_endpoints.append(f"{endpoint} ({str(e)})")
                all_success = False
        
        message = "All endpoints working" if all_success else f"Failed: {failed_endpoints}"
        self.log_result("API Endpoints", all_success, message)
        return all_success
    
    def test_chat_api(self) -> bool:
        """Test chat API functionality"""
        try:
            # Test sending a chat message
            chat_data = {
                "message": "Test message from integration test",
                "user_id": self.user_id,
                "username": self.username,
                "project_name": "test_project"
            }
            
            response = self.session.post(
                urljoin(self.base_url, "/api/chat/send"),
                json=chat_data,
                timeout=5
            )
            
            if response.status_code != 200:
                self.log_result("Chat API", False, f"Send failed: HTTP {response.status_code}")
                return False
            
            result = response.json()
            if not result.get("success"):
                self.log_result("Chat API", False, f"Send failed: {result}")
                return False
            
            # Test getting chat history
            response = self.session.get(
                urljoin(self.base_url, "/api/chat/history"),
                timeout=5
            )
            
            if response.status_code != 200:
                self.log_result("Chat API", False, f"History failed: HTTP {response.status_code}")
                return False
            
            history = response.json()
            if "messages" not in history:
                self.log_result("Chat API", False, "No messages in history")
                return False
            
            self.log_result("Chat API", True, "Send and history working")
            return True
            
        except Exception as e:
            self.log_result("Chat API", False, str(e))
            return False
    
    def test_command_processing(self) -> bool:
        """Test command processing functionality"""
        try:
            # Test help command
            chat_data = {
                "message": "/help",
                "user_id": self.user_id,
                "username": self.username,
                "project_name": "test_project"
            }
            
            response = self.session.post(
                urljoin(self.base_url, "/api/chat/send"),
                json=chat_data,
                timeout=10
            )
            
            if response.status_code != 200:
                self.log_result("Command Processing", False, f"HTTP {response.status_code}")
                return False
            
            result = response.json()
            if not result.get("success"):
                self.log_result("Command Processing", False, f"Command failed: {result}")
                return False
            
            # Give some time for command processing
            time.sleep(2)
            
            # Check if command was processed by looking at history
            response = self.session.get(
                urljoin(self.base_url, "/api/chat/history"),
                timeout=5
            )
            
            if response.status_code == 200:
                history = response.json()
                messages = history.get("messages", [])
                
                # Look for bot response to help command
                help_response_found = any(
                    msg.get("type") == "bot" and "help" in msg.get("message", "").lower()
                    for msg in messages
                )
                
                if help_response_found:
                    self.log_result("Command Processing", True, "Help command processed")
                    return True
            
            self.log_result("Command Processing", False, "No bot response found")
            return False
            
        except Exception as e:
            self.log_result("Command Processing", False, str(e))
            return False
    
    def test_autocomplete(self) -> bool:
        """Test command autocomplete functionality"""
        try:
            response = self.session.get(
                urljoin(self.base_url, "/api/chat/autocomplete?query=/h"),
                timeout=5
            )
            
            if response.status_code != 200:
                self.log_result("Autocomplete", False, f"HTTP {response.status_code}")
                return False
            
            data = response.json()
            suggestions = data.get("suggestions", [])
            
            if not suggestions:
                self.log_result("Autocomplete", False, "No suggestions returned")
                return False
            
            # Check if help command is suggested
            help_found = any("/help" in suggestion.get("command", "") for suggestion in suggestions)
            
            if help_found:
                self.log_result("Autocomplete", True, f"Found {len(suggestions)} suggestions")
                return True
            else:
                self.log_result("Autocomplete", False, "Help command not in suggestions")
                return False
            
        except Exception as e:
            self.log_result("Autocomplete", False, str(e))
            return False
    
    def test_collaboration_api(self) -> bool:
        """Test collaboration API functionality"""
        try:
            # Try to join collaboration session
            collab_data = {
                "user_id": self.user_id,
                "project_name": "test_project",
                "permission_level": "contributor"
            }
            
            response = self.session.post(
                urljoin(self.base_url, "/api/collaboration/join"),
                json=collab_data,
                timeout=5
            )
            
            # Collaboration might not be available (503) - that's OK
            if response.status_code == 503:
                self.log_result("Collaboration API", True, "Not available (expected)")
                return True
            
            if response.status_code != 200:
                self.log_result("Collaboration API", False, f"HTTP {response.status_code}")
                return False
            
            result = response.json()
            if result.get("success"):
                self.session_id = result.get("session_id")
                self.log_result("Collaboration API", True, "Session joined successfully")
                return True
            else:
                self.log_result("Collaboration API", False, f"Join failed: {result}")
                return False
            
        except Exception as e:
            self.log_result("Collaboration API", False, str(e))
            return False
    
    def test_interface_management(self) -> bool:
        """Test agent interface management functionality"""
        try:
            # Get interface status
            response = self.session.get(
                urljoin(self.base_url, "/api/interfaces"),
                timeout=5
            )
            
            if response.status_code != 200:
                self.log_result("Interface Management", False, f"HTTP {response.status_code}")
                return False
            
            data = response.json()
            
            # Check if we have interface information
            if "interfaces" not in data and "active_interface" not in data:
                self.log_result("Interface Management", False, "No interface data")
                return False
            
            # Test getting interface types
            response = self.session.get(
                urljoin(self.base_url, "/api/interfaces/types"),
                timeout=5
            )
            
            if response.status_code != 200:
                self.log_result("Interface Management", False, "Types endpoint failed")
                return False
            
            types_data = response.json()
            if "interface_types" not in types_data:
                self.log_result("Interface Management", False, "No interface types")
                return False
            
            interface_types = types_data["interface_types"]
            expected_types = ["CLAUDE_CODE", "ANTHROPIC_API", "MOCK"]
            found_types = [iface["type"] for iface in interface_types]
            
            missing_types = [t for t in expected_types if t not in found_types]
            if missing_types:
                self.log_result("Interface Management", False, f"Missing types: {missing_types}")
                return False
            
            self.log_result("Interface Management", True, f"Found {len(interface_types)} interface types")
            return True
            
        except Exception as e:
            self.log_result("Interface Management", False, str(e))
            return False
    
    def test_static_assets(self) -> bool:
        """Test that static assets are loading properly"""
        static_files = [
            "/static/style.css",
            "/static/visualizer.js",
            "/static/css/discord-chat.css",
            "/static/js/discord-chat.js",
            "/static/js/chat-components.js"
        ]
        
        all_success = True
        failed_files = []
        
        for static_file in static_files:
            try:
                response = self.session.get(
                    urljoin(self.base_url, static_file),
                    timeout=5
                )
                
                if response.status_code != 200:
                    failed_files.append(f"{static_file} (HTTP {response.status_code})")
                    all_success = False
                elif len(response.content) == 0:
                    failed_files.append(f"{static_file} (empty)")
                    all_success = False
                    
            except Exception as e:
                failed_files.append(f"{static_file} ({str(e)})")
                all_success = False
        
        message = "All assets loading" if all_success else f"Failed: {failed_files}"
        self.log_result("Static Assets", all_success, message)
        return all_success
    
    def test_responsive_design(self) -> bool:
        """Test responsive design elements"""
        try:
            # Get main page
            response = self.session.get(self.base_url, timeout=5)
            if response.status_code != 200:
                self.log_result("Responsive Design", False, f"HTTP {response.status_code}")
                return False
            
            content = response.text
            
            # Check for responsive design elements
            responsive_elements = [
                'viewport" content="width=device-width',
                '@media',
                'class="app-layout"',
                'class="chat-panel"'
            ]
            
            missing_elements = [elem for elem in responsive_elements if elem not in content]
            
            if missing_elements:
                self.log_result("Responsive Design", False, f"Missing: {missing_elements}")
                return False
            
            self.log_result("Responsive Design", True, "Responsive elements found")
            return True
            
        except Exception as e:
            self.log_result("Responsive Design", False, str(e))
            return False
    
    def run_all_tests(self) -> Dict[str, Any]:
        """Run all integration tests"""
        print("🚀 Starting Discord-Style Web Interface Integration Tests")
        print("=" * 70)
        
        # Run all tests
        tests = [
            ("Basic Connectivity", self.test_basic_connectivity),
            ("API Endpoints", self.test_api_endpoints),
            ("Chat API", self.test_chat_api),
            ("Command Processing", self.test_command_processing),
            ("Autocomplete", self.test_autocomplete),
            ("Collaboration API", self.test_collaboration_api),
            ("Interface Management", self.test_interface_management),
            ("Static Assets", self.test_static_assets),
            ("Responsive Design", self.test_responsive_design)
        ]
        
        passed = 0
        total = len(tests)
        
        for test_name, test_func in tests:
            try:
                success = test_func()
                if success:
                    passed += 1
            except Exception as e:
                self.log_result(test_name, False, f"Exception: {str(e)}")
        
        # Cleanup collaboration session if created
        if self.session_id:
            try:
                self.session.post(
                    urljoin(self.base_url, "/api/collaboration/leave"),
                    json={"session_id": self.session_id},
                    timeout=5
                )
            except:
                pass
        
        print("\n" + "=" * 70)
        print(f"📊 Test Summary: {passed}/{total} tests passed")
        
        # Print failed tests
        failed_tests = [result for result in self.test_results if not result["success"]]
        if failed_tests:
            print(f"\n❌ Failed Tests ({len(failed_tests)}):")
            for result in failed_tests:
                print(f"   • {result['test']}: {result['message']}")
        
        # Overall result
        overall_success = passed == total
        status = "🎉 ALL TESTS PASSED" if overall_success else f"⚠️  {total - passed} TESTS FAILED"
        print(f"\n{status}")
        
        return {
            "overall_success": overall_success,
            "passed": passed,
            "total": total,
            "results": self.test_results
        }


def main():
    """Main test runner"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Integration test for Discord-style web interface")
    parser.add_argument("--url", default="http://localhost:5000", help="Base URL for testing")
    parser.add_argument("--json", action="store_true", help="Output results as JSON")
    parser.add_argument("--wait", type=int, default=0, help="Wait seconds before starting tests")
    
    args = parser.parse_args()
    
    if args.wait > 0:
        print(f"⏱️  Waiting {args.wait} seconds for server to start...")
        time.sleep(args.wait)
    
    tester = IntegrationTester(args.url)
    results = tester.run_all_tests()
    
    if args.json:
        print(json.dumps(results, indent=2))
    
    # Exit with appropriate code
    sys.exit(0 if results["overall_success"] else 1)


if __name__ == "__main__":
    main()