#!/usr/bin/env python3
"""
Real-Time State Visualizer Web Application

Flask application with WebSocket support for real-time visualization
of workflow and TDD state machine transitions.
"""

import asyncio
import json
import logging
import os
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, Any

from flask import Flask, render_template, jsonify, request
from flask_socketio import SocketIO, emit
import websockets

# Add lib directory to path  
lib_path = Path(__file__).parent.parent.parent / "lib"
sys.path.insert(0, str(lib_path))

from state_broadcaster import broadcaster

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Flask app setup
app = Flask(__name__)
app.config['SECRET_KEY'] = 'state-visualizer-dev-key'
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

# Global state for tracking
current_state = {
    "workflow_state": "IDLE",
    "tdd_cycles": {},
    "last_updated": datetime.now().isoformat(),
    "transition_history": []
}


@app.route('/')
def index():
    """Main visualizer page"""
    return render_template('index.html')


@app.route('/api/state')
def get_current_state():
    """JSON API endpoint for current state"""
    return jsonify(broadcaster.get_current_state())


@app.route('/api/history')
def get_transition_history():
    """JSON API endpoint for transition history"""
    return jsonify({
        "history": broadcaster.transition_history[-50:],  # Last 50 transitions
        "count": len(broadcaster.transition_history)
    })


@app.route('/health')
def health_check():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "connected_clients": len(broadcaster.clients),
        "active_tdd_cycles": len(broadcaster.tdd_cycles)
    })


@socketio.on('connect')
def handle_connect():
    """Handle new SocketIO client connection"""
    logger.info(f"SocketIO client connected: {request.sid}")
    
    # Send current state to new client
    current_state = broadcaster.get_current_state()
    emit('state_update', current_state)


@socketio.on('disconnect')
def handle_disconnect():
    """Handle SocketIO client disconnection"""
    logger.info(f"SocketIO client disconnected: {request.sid}")


@socketio.on('request_state')
def handle_state_request():
    """Handle client request for current state"""
    current_state = broadcaster.get_current_state()
    emit('state_update', current_state)


@socketio.on('request_history')
def handle_history_request():
    """Handle client request for transition history"""
    emit('history_update', {
        "history": broadcaster.transition_history[-50:],
        "count": len(broadcaster.transition_history)
    })


class StateMonitor:
    """Monitor state broadcaster and relay to SocketIO clients"""
    
    def __init__(self, socketio_app):
        self.socketio = socketio_app
        self.running = False
        self.websocket_client = None
        
    async def start_monitoring(self):
        """Start monitoring the state broadcaster WebSocket"""
        self.running = True
        broadcaster_uri = "ws://localhost:8080"
        
        logger.info("Starting state monitor...")
        
        while self.running:
            try:
                # Connect to state broadcaster
                async with websockets.connect(broadcaster_uri) as websocket:
                    self.websocket_client = websocket
                    logger.info("Connected to state broadcaster")
                    
                    # Listen for state updates
                    async for message in websocket:
                        try:
                            data = json.loads(message)
                            self.handle_state_update(data)
                        except json.JSONDecodeError as e:
                            logger.error(f"Invalid JSON from broadcaster: {e}")
                        except Exception as e:
                            logger.error(f"Error processing state update: {e}")
                            
            except ConnectionRefusedError:
                logger.warning("State broadcaster not available, retrying in 5 seconds...")
                await asyncio.sleep(5)
            except Exception as e:
                logger.error(f"State monitor error: {e}")
                await asyncio.sleep(5)
                
    def handle_state_update(self, data: Dict[str, Any]):
        """Handle state update from broadcaster and relay to SocketIO clients"""
        update_type = data.get("type")
        
        if update_type == "workflow_transition":
            logger.info(f"Workflow transition: {data.get('old_state')} → {data.get('new_state')}")
            self.socketio.emit('workflow_transition', data)
            
        elif update_type == "tdd_transition":
            logger.info(f"TDD transition [{data.get('story_id')}]: {data.get('old_state')} → {data.get('new_state')}")
            self.socketio.emit('tdd_transition', data)
            
        elif update_type == "agent_activity":
            logger.info(f"Agent activity [{data.get('story_id')}]: {data.get('agent_type')} {data.get('action')} - {data.get('status')}")
            self.socketio.emit('agent_activity', data)
            
        elif update_type == "current_state":
            self.socketio.emit('state_update', data)
            
        # Always emit generic update for debugging
        self.socketio.emit('raw_update', data)
        
    def stop_monitoring(self):
        """Stop the state monitoring"""
        self.running = False
        if self.websocket_client:
            asyncio.create_task(self.websocket_client.close())


# Global state monitor
state_monitor = StateMonitor(socketio)


def run_visualizer(host='localhost', port=5000, debug=False):
    """Run the visualizer web application"""
    logger.info(f"Starting State Visualizer on http://{host}:{port}")
    
    # Start state monitoring in background
    import threading
    import asyncio
    
    def monitor_thread():
        """Thread function for state monitoring"""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(state_monitor.start_monitoring())
        except Exception as e:
            logger.error(f"State monitoring error: {e}")
        finally:
            loop.close()
    
    monitor_thread = threading.Thread(target=monitor_thread, daemon=True)
    monitor_thread.start()
    
    # Run Flask-SocketIO app
    try:
        socketio.run(
            app,
            host=host,
            port=port,
            debug=debug,
            allow_unsafe_werkzeug=True
        )
    finally:
        state_monitor.stop_monitoring()


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='TDD State Visualizer')
    parser.add_argument('--host', default='localhost', help='Host to bind to')
    parser.add_argument('--port', type=int, default=5000, help='Port to bind to')
    parser.add_argument('--debug', action='store_true', help='Enable debug mode')
    
    args = parser.parse_args()
    
    run_visualizer(args.host, args.port, args.debug)