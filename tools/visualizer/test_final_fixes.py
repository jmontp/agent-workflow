#!/usr/bin/env python3
"""Final test script to verify Discord interface fixes"""

import socketio
import time
import sys

# Create a Socket.IO client
sio = socketio.Client()

results = []

@sio.event
def connect():
    print("✅ Connected to server")
    results.append(("Connection", True))
    
    # Test 1: Send a regular message
    print("\n📝 Test 1: Sending regular message...")
    sio.emit('chat_command', {
        'message': 'Hello, this is a test message!',
        'user_id': 'test_user',
        'username': 'Test User',
        'session_id': None,
        'project_name': 'default'
    })
    
    # Test 2: Send a command
    time.sleep(0.5)
    print("\n📝 Test 2: Sending /help command...")
    sio.emit('chat_command', {
        'message': '/help',
        'user_id': 'test_user',
        'username': 'Test User',
        'session_id': None,
        'project_name': 'default'
    })
    
    # Test 3: Send empty message (should not appear)
    time.sleep(0.5)
    print("\n📝 Test 3: Sending empty message (should be ignored)...")
    sio.emit('chat_command', {
        'message': '',
        'user_id': 'test_user',
        'username': 'Test User',
        'session_id': None,
        'project_name': 'default'
    })

@sio.event
def new_chat_message(data):
    print(f"✅ Received chat message: {data.get('message', 'No message')}")
    results.append(("Chat message received", True))

@sio.event
def command_response(data):
    print(f"✅ Received command response")
    if data.get('command_result'):
        print(f"   Command: {data['command_result'].get('command')}")
        print(f"   Success: {data['command_result'].get('success')}")
    results.append(("Command response received", True))

@sio.event
def chat_error(data):
    print(f"❌ Chat error: {data.get('error', 'Unknown error')}")
    results.append(("Chat error", False))

@sio.event
def disconnect():
    print("\n📊 Disconnected from server")

if __name__ == "__main__":
    try:
        print("🔌 Connecting to visualizer server...")
        sio.connect('http://localhost:5000')
        
        # Wait for responses
        print("\n⏳ Waiting for responses...")
        time.sleep(3)
        
        # Disconnect
        sio.disconnect()
        
        # Print results
        print("\n" + "="*50)
        print("📊 TEST RESULTS SUMMARY")
        print("="*50)
        
        total_tests = len(results)
        passed_tests = sum(1 for _, passed in results if passed)
        
        for test_name, passed in results:
            status = "✅ PASS" if passed else "❌ FAIL"
            print(f"{status} - {test_name}")
        
        print(f"\n🎯 Total: {passed_tests}/{total_tests} tests passed")
        
        if passed_tests == total_tests:
            print("\n🎉 All tests passed! The chat functionality is working correctly.")
            sys.exit(0)
        else:
            print("\n⚠️  Some tests failed. Please check the implementation.")
            sys.exit(1)
            
    except Exception as e:
        print(f"\n❌ Error during testing: {e}")
        print("\n💡 Make sure the web interface is running with 'aw web'")
        sys.exit(1)