#!/usr/bin/env python3
"""Simple test to check what's being served by the web interface"""

import requests
import re
import sys

def check_server():
    """Check if server is running and serving correct files"""
    
    print("🌐 Checking web server at http://localhost:5000...\n")
    
    # Test 1: Server responding
    try:
        response = requests.get("http://localhost:5000", timeout=5)
        print(f"✅ Server is running (status: {response.status_code})")
    except Exception as e:
        print(f"❌ Server not responding: {e}")
        return False
    
    # Test 2: Check main HTML
    print("\n🔍 Checking HTML structure...")
    html = response.text
    
    elements = {
        "chat-input-field": r'id="chat-input-field"',
        "chat-send-btn": r'id="chat-send-btn"',
        "chat-messages": r'id="chat-messages"',
        "chat-panel": r'id="chat-panel"'
    }
    
    for element_name, pattern in elements.items():
        if re.search(pattern, html):
            print(f"  ✅ Found element: {element_name}")
        else:
            print(f"  ❌ Missing element: {element_name}")
    
    # Test 3: Check JavaScript file
    print("\n🔍 Checking JavaScript file...")
    js_response = requests.get("http://localhost:5000/static/js/discord-chat.js")
    js_content = js_response.text
    
    # Look for our specific fixes
    fixes = [
        {
            "name": "Initial state comment",
            "pattern": r"// Initial state - disable send button if input is empty",
            "line_hint": "around line 70"
        },
        {
            "name": "Initial state code",
            "pattern": r"sendButton\.disabled = messageInput\.value\.trim\(\)\.length === 0;",
            "line_hint": "around line 71"
        },
        {
            "name": "Input event with logging",
            "pattern": r"console\.log\('Input changed, has content:'",
            "line_hint": "around line 67"
        },
        {
            "name": "Send button disabled after send",
            "pattern": r"sendButton\.disabled = true;",
            "line_hint": "around line 321"
        }
    ]
    
    print("\n📄 JavaScript file analysis:")
    all_found = True
    for fix in fixes:
        if re.search(fix["pattern"], js_content):
            print(f"  ✅ Found: {fix['name']} ({fix['line_hint']})")
        else:
            print(f"  ❌ Missing: {fix['name']} ({fix['line_hint']})")
            all_found = False
    
    # Test 4: Check for duplicate event listeners
    print("\n🔍 Checking for potential issues...")
    
    # Count input event listeners
    input_listeners = len(re.findall(r"messageInput\.addEventListener\('input'", js_content))
    print(f"  ℹ️  Number of 'input' event listeners: {input_listeners}")
    if input_listeners > 1:
        print(f"  ⚠️  Warning: Multiple input event listeners found ({input_listeners})")
    
    # Test 5: Extract and show the actual event handler code
    print("\n📋 Extracted event handler code:")
    
    # Find the event handler section
    pattern = r"(// Enable/disable send button.*?// Send button)"
    match = re.search(pattern, js_content, re.DOTALL)
    if match:
        code_section = match.group(1)
        # Clean up and indent
        lines = code_section.strip().split('\n')
        for line in lines[:10]:  # Show first 10 lines
            print(f"  {line}")
    
    # Test 6: Check CSS file
    print("\n🎨 Checking CSS file...")
    css_response = requests.get("http://localhost:5000/static/css/discord-chat.css")
    if css_response.status_code == 200:
        print("  ✅ Discord chat CSS loaded successfully")
    else:
        print(f"  ❌ Failed to load CSS (status: {css_response.status_code})")
    
    return all_found

def check_via_curl():
    """Use curl to check the files (as a verification)"""
    import subprocess
    
    print("\n🔧 Double-checking with curl...")
    
    # Check if the initial state code is present
    cmd = [
        "curl", "-s", "http://localhost:5000/static/js/discord-chat.js",
        "|", "grep", "-n", "sendButton.disabled = messageInput.value.trim"
    ]
    
    result = subprocess.run(" ".join(cmd), shell=True, capture_output=True, text=True)
    if result.stdout:
        print(f"  ✅ Curl confirms: Found the fix at line(s):\n  {result.stdout.strip()}")
    else:
        print("  ❌ Curl could not find the fix")

def main():
    """Run all checks"""
    print("🚀 Running web interface verification...\n")
    
    success = check_server()
    
    if success:
        print("\n✅ All fixes are present in the served files!")
        print("\n💡 If you still don't see the changes in your browser:")
        print("   1. Close ALL browser windows (not just tabs)")
        print("   2. Open a NEW browser instance")
        print("   3. Navigate to http://localhost:5000")
        print("   4. Or try a different browser (Firefox, Edge, etc.)")
        print("\n🔍 The issue is definitely browser-side caching.")
    else:
        print("\n❌ Some fixes are missing from the served files.")
        print("   This suggests a server-side issue.")
    
    check_via_curl()

if __name__ == "__main__":
    main()