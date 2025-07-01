#!/usr/bin/env python3
"""
Start the state broadcaster WebSocket server
"""
import asyncio
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'lib'))

from state_broadcaster import broadcaster

async def main():
    print("Starting state broadcaster on ws://localhost:8080...")
    await broadcaster.start_server(port=8080)
    
    # Keep the server running
    try:
        await asyncio.Future()  # Run forever
    except KeyboardInterrupt:
        print("\nShutting down state broadcaster...")
        await broadcaster.stop_server()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nBroadcaster stopped.")