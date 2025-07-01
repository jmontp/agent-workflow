#!/usr/bin/env python3
"""
Test script for multi-project API endpoints in the visualizer web app
"""

import requests
import json
import sys
import tempfile
from pathlib import Path

# Test configuration
BASE_URL = "http://localhost:5000"
API_BASE = f"{BASE_URL}/api"

def test_endpoint(method, endpoint, data=None, expected_status=200):
    """Test an API endpoint"""
    url = f"{API_BASE}{endpoint}"
    print(f"\n=== Testing {method} {endpoint} ===")
    
    try:
        if method.upper() == "GET":
            response = requests.get(url)
        elif method.upper() == "POST":
            response = requests.post(url, json=data)
        else:
            print(f"Unsupported method: {method}")
            return False
        
        print(f"Status: {response.status_code}")
        
        if response.status_code != expected_status:
            print(f"❌ Expected status {expected_status}, got {response.status_code}")
            print(f"Response: {response.text}")
            return False
        
        try:
            result = response.json()
            print(f"✅ Response: {json.dumps(result, indent=2)}")
            return True, result
        except json.JSONDecodeError:
            print(f"❌ Invalid JSON response: {response.text}")
            return False
            
    except requests.exceptions.ConnectionError:
        print(f"❌ Failed to connect to {url}")
        print("Make sure the visualizer web app is running on localhost:5000")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_multi_project_api():
    """Test all multi-project API endpoints"""
    print("🚀 Testing Multi-Project API Endpoints")
    print("=" * 50)
    
    # Test 1: Get projects list (should work even if empty)
    success, projects_response = test_endpoint("GET", "/projects")
    if not success:
        return False
    
    multi_project_enabled = projects_response.get('multi_project_enabled', False)
    if not multi_project_enabled:
        print("\n⚠️  Multi-project management is not available")
        print("This is expected if the lib/multi_project_config.py module is not available")
        return True
    
    print(f"\n✅ Multi-project management is enabled with {projects_response.get('total_count', 0)} projects")
    
    # Test 2: Project discovery (with a temp directory)
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create a fake git repo
        git_dir = Path(temp_dir) / "test-project" / ".git"
        git_dir.mkdir(parents=True)
        
        discovery_data = {"search_paths": [temp_dir]}
        success, discovery_response = test_endpoint("POST", "/projects/discover", discovery_data)
        if not success:
            return False
        
        print(f"✅ Discovered {discovery_response.get('total_count', 0)} potential projects")
    
    # Test 3: Try to get state for a non-existent project (should return 404)
    success, _ = test_endpoint("GET", "/projects/nonexistent/state", expected_status=404)
    if not success:
        return False
    
    # Test 4: Try to get config for a non-existent project (should return 404)
    success, _ = test_endpoint("GET", "/projects/nonexistent/config", expected_status=404)
    if not success:
        return False
    
    # Test 5: Try to switch to a non-existent project (should return 404)
    switch_data = {"session_id": "test-session"}
    success, _ = test_endpoint("POST", "/projects/nonexistent/switch", switch_data, expected_status=404)
    if not success:
        return False
    
    print("\n🎉 All multi-project API tests passed!")
    return True

def test_debug_endpoint():
    """Test the debug endpoint for multi-project information"""
    print("\n🔍 Testing Debug Endpoint")
    print("=" * 30)
    
    success, debug_response = test_endpoint("GET", "/debug")
    if not success:
        return False
    
    # Check if multi-project debug info is included
    multi_project_debug = debug_response.get('multi_project', {})
    if multi_project_debug:
        print("✅ Multi-project debug information is included")
        enabled = multi_project_debug.get('enabled', False)
        if enabled:
            print(f"   - Total projects: {multi_project_debug.get('total_projects', 0)}")
            print(f"   - Active projects: {multi_project_debug.get('active_projects', 0)}")
            print(f"   - Active sessions: {multi_project_debug.get('active_sessions', 0)}")
        else:
            print(f"   - Reason disabled: {multi_project_debug.get('reason', 'Unknown')}")
    else:
        print("❌ Multi-project debug information missing")
        return False
    
    return True

def main():
    """Run all tests"""
    print("🧪 Multi-Project API Test Suite")
    print("=" * 40)
    
    # Test if the server is running
    try:
        response = requests.get(f"{BASE_URL}/health")
        if response.status_code == 200:
            print("✅ Web server is running")
        else:
            print(f"❌ Web server returned status {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to web server at localhost:5000")
        print("Please start the visualizer: python tools/visualizer/app.py")
        return False
    
    # Run all tests
    tests = [
        test_multi_project_api,
        test_debug_endpoint
    ]
    
    passed = 0
    for test in tests:
        try:
            if test():
                passed += 1
            else:
                print(f"❌ Test {test.__name__} failed")
        except Exception as e:
            print(f"❌ Test {test.__name__} raised exception: {e}")
    
    total = len(tests)
    print(f"\n📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed!")
        return True
    else:
        print("❌ Some tests failed")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)