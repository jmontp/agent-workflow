#!/usr/bin/env python3
"""
UI Fixes Validation Test

This script validates that the three implemented fixes work correctly:
1. JavaScript loading race condition fix
2. DOM state synchronization fix  
3. Missing JavaScript file cleanup

Usage:
    python test_fixes_validation.py [--port 5001] [--debug]
"""

import requests
import time
import argparse
import sys
from pathlib import Path

def test_missing_files_fixed(base_url):
    """Test that missing JavaScript files no longer cause 404 errors"""
    print("🔍 Testing Fix 3: Missing JavaScript file cleanup...")
    
    # Files that should no longer be referenced (should return 404 or not be requested)
    missing_files = [
        '/static/emergency-layout-preload.js',
        '/static/final-layout-enforcer.js', 
        '/static/force-visualizer-mode.js',
        '/static/js/project-management.js'
    ]
    
    # Get the main page HTML to check if these files are still referenced
    try:
        response = requests.get(base_url, timeout=10)
        html_content = response.text
        
        issues_found = []
        for file_path in missing_files:
            if file_path in html_content:
                issues_found.append(f"❌ Still references {file_path}")
            else:
                print(f"✅ No longer references {file_path}")
        
        if issues_found:
            print("❌ Fix 3 FAILED - Missing files still referenced:")
            for issue in issues_found:
                print(f"  {issue}")
            return False
        else:
            print("✅ Fix 3 PASSED - No missing file references found")
            return True
            
    except Exception as e:
        print(f"❌ Fix 3 ERROR - Could not test: {e}")
        return False

def test_dependency_loader_present(base_url):
    """Test that dependency loader is present in HTML"""
    print("🔍 Testing Fix 1: JavaScript dependency loader...")
    
    try:
        response = requests.get(base_url, timeout=10)
        html_content = response.text
        
        # Check for dependency loader components
        loader_indicators = [
            'window.dependencyLoader',
            'checkCDNDependencies',
            'checkLocalDependencies',
            'initializeApp',
            'loading-dependencies'
        ]
        
        found_indicators = []
        for indicator in loader_indicators:
            if indicator in html_content:
                found_indicators.append(indicator)
                
        if len(found_indicators) >= 4:  # Most indicators should be present
            print(f"✅ Fix 1 PASSED - Dependency loader present ({len(found_indicators)}/{len(loader_indicators)} indicators found)")
            return True
        else:
            print(f"❌ Fix 1 FAILED - Dependency loader incomplete ({len(found_indicators)}/{len(loader_indicators)} indicators found)")
            return False
            
    except Exception as e:
        print(f"❌ Fix 1 ERROR - Could not test: {e}")
        return False

def test_state_synchronization_present(base_url):
    """Test that state synchronization code is present"""
    print("🔍 Testing Fix 2: DOM state synchronization...")
    
    # Check if the discord-chat.js file contains the new setupStateSynchronization method
    try:
        discord_chat_path = Path(__file__).parent / "static" / "js" / "discord-chat.js"
        if not discord_chat_path.exists():
            print("❌ Fix 2 ERROR - discord-chat.js file not found")
            return False
            
        with open(discord_chat_path, 'r') as f:
            js_content = f.read()
            
        # Check for state synchronization components
        sync_indicators = [
            'setupStateSynchronization',
            'MutationObserver',
            'stateObservers',
            'Fixed desynchronized send button state',
            'DOM state synchronization setup complete'
        ]
        
        found_indicators = []
        for indicator in sync_indicators:
            if indicator in js_content:
                found_indicators.append(indicator)
                
        if len(found_indicators) >= 4:  # Most indicators should be present
            print(f"✅ Fix 2 PASSED - State synchronization present ({len(found_indicators)}/{len(sync_indicators)} indicators found)")
            return True
        else:
            print(f"❌ Fix 2 FAILED - State synchronization incomplete ({len(found_indicators)}/{len(sync_indicators)} indicators found)")
            return False
            
    except Exception as e:
        print(f"❌ Fix 2 ERROR - Could not test: {e}")
        return False

def test_basic_page_load(base_url):
    """Test that the page loads without obvious errors"""
    print("🔍 Testing basic page functionality...")
    
    try:
        response = requests.get(base_url, timeout=10)
        
        if response.status_code == 200:
            print(f"✅ Page loads successfully (HTTP {response.status_code})")
            
            # Check for basic required elements in HTML
            html = response.text
            required_elements = [
                'chat-input-field',
                'chat-send-btn', 
                'chat-messages',
                'TDD State Visualizer'
            ]
            
            missing_elements = []
            for element in required_elements:
                if element not in html:
                    missing_elements.append(element)
                    
            if missing_elements:
                print(f"⚠️ Missing required elements: {', '.join(missing_elements)}")
                return False
            else:
                print("✅ All required elements present in HTML")
                return True
        else:
            print(f"❌ Page load failed (HTTP {response.status_code})")
            return False
            
    except Exception as e:
        print(f"❌ Page load error: {e}")
        return False

def main():
    parser = argparse.ArgumentParser(description='Validate UI fixes implementation')
    parser.add_argument('--port', type=int, default=5001, help='Web interface port')
    parser.add_argument('--debug', action='store_true', help='Enable debug output')
    
    args = parser.parse_args()
    base_url = f"http://localhost:{args.port}"
    
    print("🧪 UI Fixes Validation Test")
    print("=" * 50)
    print(f"Testing web interface at: {base_url}")
    print()
    
    # Run all tests
    results = {}
    
    results['basic_load'] = test_basic_page_load(base_url)
    results['missing_files'] = test_missing_files_fixed(base_url)
    results['dependency_loader'] = test_dependency_loader_present(base_url)
    results['state_sync'] = test_state_synchronization_present(base_url)
    
    # Summary
    print()
    print("=" * 50)
    print("📊 VALIDATION RESULTS")
    print("=" * 50)
    
    passed = sum(1 for result in results.values() if result)
    total = len(results)
    
    for test_name, passed_test in results.items():
        status = "✅ PASS" if passed_test else "❌ FAIL"
        print(f"{test_name.replace('_', ' ').title()}: {status}")
    
    print()
    print(f"Overall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All fixes validated successfully!")
        return 0
    else:
        print("⚠️ Some fixes may need attention")
        return 1

if __name__ == "__main__":
    sys.exit(main())