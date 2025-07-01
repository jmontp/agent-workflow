#!/usr/bin/env python3
"""Test the web interface for network issues"""
import requests
import json

def test_endpoints():
    base_url = "http://localhost:5000"
    
    print("Testing web interface endpoints...")
    
    # Test main page
    try:
        resp = requests.get(f"{base_url}/")
        print(f"✓ Main page: {resp.status_code}")
        if resp.status_code != 200:
            print(f"  Error: {resp.text[:200]}")
    except Exception as e:
        print(f"✗ Main page failed: {e}")
    
    # Test static files
    static_files = [
        "/static/visualizer.js",
        "/static/js/discord-chat.js",
        "/static/js/chat-components.js",
        "/static/style.css",
        "/static/css/discord-chat.css"
    ]
    
    for file in static_files:
        try:
            resp = requests.get(f"{base_url}{file}")
            status = "✓" if resp.status_code == 200 else "✗"
            print(f"{status} {file}: {resp.status_code}")
        except Exception as e:
            print(f"✗ {file} failed: {e}")
    
    # Test API endpoints
    api_endpoints = [
        "/health",
        "/api/state",
        "/api/history",
        "/api/interfaces",
        "/api/interfaces/types",
        "/api/chat/history"
    ]
    
    for endpoint in api_endpoints:
        try:
            resp = requests.get(f"{base_url}{endpoint}")
            status = "✓" if resp.status_code == 200 else "✗"
            print(f"{status} {endpoint}: {resp.status_code}")
            if resp.status_code == 200 and endpoint == "/health":
                data = resp.json()
                print(f"  Connected clients: {data.get('connected_clients', 0)}")
                print(f"  Status: {data.get('status', 'unknown')}")
        except Exception as e:
            print(f"✗ {endpoint} failed: {e}")
    
    # Test Socket.IO endpoint
    try:
        resp = requests.get(f"{base_url}/socket.io/?EIO=4&transport=polling")
        status = "✓" if resp.status_code == 200 else "✗"
        print(f"{status} Socket.IO endpoint: {resp.status_code}")
        if resp.status_code == 200:
            print(f"  Response: {resp.text[:100]}")
    except Exception as e:
        print(f"✗ Socket.IO endpoint failed: {e}")

if __name__ == "__main__":
    test_endpoints()