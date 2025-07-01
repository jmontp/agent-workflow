#!/usr/bin/env python3
"""Test script to verify chat functionality"""

import socketio
import time

# Create a Socket.IO client
sio = socketio.Client()

@sio.event
def connect():
    print("Connected to server")
    
    # Send a test chat command
    print("Sending test message...")
    sio.emit('chat_command', {
        'message': '/help',
        'user_id': 'test_user',
        'username': 'Test User',
        'session_id': None,
        'project_name': 'default'
    })

@sio.event
def new_chat_message(data):
    print(f"Received chat message: {data}")

@sio.event
def command_response(data):
    print(f"Received command response: {data}")

@sio.event
def disconnect():
    print("Disconnected from server")

if __name__ == "__main__":
    try:
        print("Connecting to visualizer server...")
        sio.connect('http://localhost:5000')
        
        # Wait for response
        time.sleep(2)
        
        sio.disconnect()
    except Exception as e:
        print(f"Error: {e}")