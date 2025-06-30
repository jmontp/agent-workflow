#!/usr/bin/env python3
"""
Integration Tests for Discord-Style Chat Interface

Comprehensive testing of the Discord-style chat functionality including:
- Chat API endpoints
- WebSocket events and real-time communication
- Command execution and validation
- Error handling and edge cases
- Real-time synchronization between clients
"""

import asyncio
import json
import pytest
import threading
import time
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List
from unittest.mock import Mock, patch, MagicMock

import requests
import websocket
from flask import Flask
from flask_socketio import SocketIOTestClient


# Add paths for imports
import sys
visualizer_path = Path(__file__).parent.parent.parent / "tools" / "visualizer"
sys.path.insert(0, str(visualizer_path))

from app import app, socketio, chat_history, typing_users, active_users


class TestDiscordChatIntegration:
    """Integration tests for Discord-style chat interface"""
    
    @pytest.fixture(autouse=True)
    def setup_method(self):
        """Setup for each test method"""
        # Clear global state
        chat_history.clear()
        typing_users.clear() 
        active_users.clear()
        
        # Setup test client
        self.client = app.test_client()
        self.socketio_client = socketio.test_client(app)
        
        # Test user data
        self.test_user = {
            "user_id": "test_user_123",
            "username": "TestUser"
        }
        
        self.test_bot = {
            "user_id": "bot",
            "username": "Agent Bot"
        }
        
        yield
        
        # Cleanup
        if hasattr(self, 'socketio_client') and self.socketio_client.is_connected():
            self.socketio_client.disconnect()


class TestChatAPIEndpoints(TestDiscordChatIntegration):
    """Test chat REST API endpoints"""
    
    def test_send_chat_message_success(self):
        """Test successful message sending"""
        message_data = {
            "message": "Hello, this is a test message!",
            "user_id": self.test_user["user_id"],
            "username": self.test_user["username"]
        }
        
        response = self.client.post('/api/chat/send', 
                                  json=message_data,
                                  content_type='application/json')
        
        assert response.status_code == 200
        data = response.get_json()
        assert data["success"] is True
        assert "message_id" in data
        
        # Verify message was added to history
        assert len(chat_history) == 1
        assert chat_history[0]["message"] == message_data["message"]
        assert chat_history[0]["user_id"] == message_data["user_id"]
        assert chat_history[0]["username"] == message_data["username"]
        assert chat_history[0]["type"] == "user"
    
    def test_send_chat_message_validation(self):
        """Test message validation"""
        # Test empty message
        response = self.client.post('/api/chat/send', 
                                  json={"message": "", "user_id": "test", "username": "Test"},
                                  content_type='application/json')
        assert response.status_code == 400
        
        # Test missing data
        response = self.client.post('/api/chat/send', 
                                  json={},
                                  content_type='application/json')
        assert response.status_code == 400
        
        # Test no JSON data
        response = self.client.post('/api/chat/send')
        assert response.status_code == 400
    
    def test_send_command_message(self):
        """Test sending a command message"""
        with patch('command_processor.process_command') as mock_process:
            mock_process.return_value = {
                "success": True,
                "response": "Command processed successfully",
                "command": "/help"
            }
            
            message_data = {
                "message": "/help",
                "user_id": self.test_user["user_id"],
                "username": self.test_user["username"]
            }
            
            response = self.client.post('/api/chat/send', 
                                      json=message_data,
                                      content_type='application/json')
            
            assert response.status_code == 200
            # Give some time for async command processing
            time.sleep(0.1)
            
            # Verify command processor was called
            mock_process.assert_called_once_with("/help", self.test_user["user_id"])
    
    def test_get_chat_history(self):
        """Test retrieving chat history"""
        # Add some test messages
        test_messages = [
            {"id": str(uuid.uuid4()), "user_id": "user1", "username": "User1", 
             "message": "Message 1", "timestamp": datetime.now().isoformat(), "type": "user"},
            {"id": str(uuid.uuid4()), "user_id": "user2", "username": "User2", 
             "message": "Message 2", "timestamp": datetime.now().isoformat(), "type": "user"},
        ]
        
        chat_history.extend(test_messages)
        
        response = self.client.get('/api/chat/history')
        assert response.status_code == 200
        
        data = response.get_json()
        assert "messages" in data
        assert "total_count" in data
        assert data["total_count"] == 2
        assert len(data["messages"]) == 2
        
        # Test limit parameter
        response = self.client.get('/api/chat/history?limit=1')
        data = response.get_json()
        assert len(data["messages"]) == 1
        assert data["total_count"] == 2  # Total count should still be 2
    
    def test_get_chat_history_limit_bounds(self):
        """Test chat history limit boundaries"""
        # Test maximum limit
        response = self.client.get('/api/chat/history?limit=200')
        data = response.get_json()
        # Should be capped at 100
        assert len(data["messages"]) <= 100
        
        # Test with no messages
        response = self.client.get('/api/chat/history')
        data = response.get_json()
        assert data["messages"] == []
        assert data["total_count"] == 0
    
    def test_command_autocomplete(self):
        """Test command autocomplete functionality"""
        # Test basic autocomplete
        response = self.client.get('/api/chat/autocomplete')
        assert response.status_code == 200
        
        data = response.get_json()
        assert "suggestions" in data
        assert len(data["suggestions"]) <= 10
        
        # Verify expected commands are present
        command_names = [cmd["command"] for cmd in data["suggestions"]]
        assert "/epic" in command_names
        assert "/help" in command_names
        assert "/state" in command_names
    
    def test_command_autocomplete_search(self):
        """Test autocomplete with search query"""
        # Test filtering
        response = self.client.get('/api/chat/autocomplete?query=sprint')
        data = response.get_json()
        
        # All suggestions should contain 'sprint'
        for suggestion in data["suggestions"]:
            assert ('sprint' in suggestion["command"].lower() or 
                   'sprint' in suggestion["description"].lower())
    
    def test_chat_history_overflow_management(self):
        """Test chat history size management"""
        # Add more than 100 messages to test overflow
        for i in range(105):
            chat_history.append({
                "id": str(uuid.uuid4()),
                "user_id": f"user_{i}",
                "username": f"User{i}",
                "message": f"Message {i}",
                "timestamp": datetime.now().isoformat(),
                "type": "user"
            })
        
        # Send a new message which should trigger overflow management
        message_data = {
            "message": "New message",
            "user_id": "new_user",
            "username": "NewUser"
        }
        
        response = self.client.post('/api/chat/send', 
                                  json=message_data,
                                  content_type='application/json')
        
        assert response.status_code == 200
        # History should be capped at 100
        assert len(chat_history) == 100
        # Latest message should be present
        assert chat_history[-1]["message"] == "New message"


class TestChatWebSocketEvents(TestDiscordChatIntegration):
    """Test WebSocket events and real-time communication"""
    
    def test_websocket_connection_and_state_update(self):
        """Test WebSocket connection and initial state update"""
        assert self.socketio_client.is_connected()
        
        # Should receive initial state update on connection
        received_events = self.socketio_client.get_received()
        
        # Look for state_update event
        state_events = [event for event in received_events if event['name'] == 'state_update']
        assert len(state_events) > 0
    
    def test_chat_command_via_websocket(self):
        """Test sending chat commands via WebSocket"""
        with patch('command_processor.process_command') as mock_process:
            mock_process.return_value = {
                "success": True,
                "response": "Test command response",
                "command": "/test"
            }
            
            # Send command via WebSocket
            self.socketio_client.emit('chat_command', {
                "message": "/test command",
                "user_id": self.test_user["user_id"],
                "username": self.test_user["username"]
            })
            
            # Give time for processing
            time.sleep(0.2)
            
            # Check received events
            received_events = self.socketio_client.get_received()
            
            # Should receive new_chat_message and typing indicators
            message_events = [e for e in received_events if e['name'] == 'new_chat_message']
            assert len(message_events) > 0
            
            typing_events = [e for e in received_events if e['name'] == 'typing_indicator']
            assert len(typing_events) > 0
    
    def test_websocket_message_broadcast(self):
        """Test message broadcasting to multiple clients"""
        # Create second client
        client2 = socketio.test_client(app)
        
        try:
            # Send message from first client
            self.socketio_client.emit('chat_command', {
                "message": "Hello from client 1",
                "user_id": "client1",
                "username": "Client1"
            })
            
            time.sleep(0.1)
            
            # Both clients should receive the message
            client1_events = self.socketio_client.get_received()
            client2_events = client2.get_received()
            
            # Check that both clients received new_chat_message
            client1_messages = [e for e in client1_events if e['name'] == 'new_chat_message']
            client2_messages = [e for e in client2_events if e['name'] == 'new_chat_message']
            
            assert len(client1_messages) > 0
            assert len(client2_messages) > 0
            
        finally:
            client2.disconnect()
    
    def test_typing_indicators(self):
        """Test typing indicator functionality"""
        # Start typing
        self.socketio_client.emit('start_typing', {
            "user_id": self.test_user["user_id"],
            "username": self.test_user["username"]
        })
        
        # User should be added to typing users
        assert self.test_user["user_id"] in typing_users
        
        # Stop typing
        self.socketio_client.emit('stop_typing', {
            "user_id": self.test_user["user_id"],
            "username": self.test_user["username"]
        })
        
        # User should be removed from typing users
        assert self.test_user["user_id"] not in typing_users
    
    def test_join_and_leave_chat(self):
        """Test join and leave chat functionality"""
        # Join chat
        self.socketio_client.emit('join_chat', {
            "user_id": self.test_user["user_id"],
            "username": self.test_user["username"]
        })
        
        # User should be added to active users
        assert self.test_user["user_id"] in active_users
        
        # Check for user_joined event
        received_events = self.socketio_client.get_received()
        join_events = [e for e in received_events if e['name'] == 'user_joined']
        assert len(join_events) > 0
        
        # Leave chat
        self.socketio_client.emit('leave_chat', {
            "user_id": self.test_user["user_id"],
            "username": self.test_user["username"]
        })
        
        # User should be removed from active users
        assert self.test_user["user_id"] not in active_users
        assert self.test_user["user_id"] not in typing_users
    
    def test_request_chat_history_websocket(self):
        """Test requesting chat history via WebSocket"""
        # Add test message to history
        chat_history.append({
            "id": str(uuid.uuid4()),
            "user_id": "test",
            "username": "Test",
            "message": "Test message",
            "timestamp": datetime.now().isoformat(),
            "type": "user"
        })
        
        # Request history
        self.socketio_client.emit('request_chat_history', {"limit": 10})
        
        # Check for chat_history event
        received_events = self.socketio_client.get_received()
        history_events = [e for e in received_events if e['name'] == 'chat_history']
        
        assert len(history_events) > 0
        history_data = history_events[0]['args'][0]
        assert "messages" in history_data
        assert len(history_data["messages"]) == 1
        assert history_data["total_count"] == 1


class TestCommandExecution(TestDiscordChatIntegration):
    """Test command execution and validation"""
    
    def test_epic_command_execution(self):
        """Test /epic command execution"""
        with patch('command_processor.get_processor') as mock_get_processor:
            mock_processor = Mock()
            mock_processor.process_command.return_value = {
                "success": True,
                "response": "Epic created successfully",
                "command": "/epic",
                "epic_data": {"epic_id": "epic_123"}
            }
            mock_get_processor.return_value = mock_processor
            
            message_data = {
                "message": "/epic \"Test epic description\"",
                "user_id": self.test_user["user_id"],
                "username": self.test_user["username"]
            }
            
            response = self.client.post('/api/chat/send', 
                                      json=message_data,
                                      content_type='application/json')
            
            assert response.status_code == 200
            time.sleep(0.1)  # Allow async processing
            
            # Verify command was processed
            mock_processor.process_command.assert_called_once()
    
    def test_sprint_command_execution(self):
        """Test /sprint command execution"""
        with patch('command_processor.get_processor') as mock_get_processor:
            mock_processor = Mock()
            mock_processor.process_command.return_value = {
                "success": True,
                "response": "Sprint status retrieved",
                "command": "/sprint",
                "sprint_data": {"status": "active"}
            }
            mock_get_processor.return_value = mock_processor
            
            message_data = {
                "message": "/sprint status",
                "user_id": self.test_user["user_id"],
                "username": self.test_user["username"]
            }
            
            response = self.client.post('/api/chat/send', 
                                      json=message_data,
                                      content_type='application/json')
            
            assert response.status_code == 200
    
    def test_command_error_handling(self):
        """Test command error handling"""
        with patch('command_processor.get_processor') as mock_get_processor:
            mock_processor = Mock()
            mock_processor.process_command.side_effect = Exception("Command processing failed")
            mock_get_processor.return_value = mock_processor
            
            message_data = {
                "message": "/invalid_command",
                "user_id": self.test_user["user_id"],
                "username": self.test_user["username"]
            }
            
            response = self.client.post('/api/chat/send', 
                                      json=message_data,
                                      content_type='application/json')
            
            assert response.status_code == 200
            time.sleep(0.1)  # Allow async processing
            
            # Should have bot error response in history
            bot_messages = [msg for msg in chat_history if msg["user_id"] == "bot" and msg.get("error")]
            assert len(bot_messages) > 0
    
    def test_help_command_execution(self):
        """Test /help command execution"""
        with patch('command_processor.get_processor') as mock_get_processor:
            mock_processor = Mock()
            mock_processor.process_command.return_value = {
                "success": True,
                "response": "Available commands: /epic, /sprint, /help...",
                "command": "/help"
            }
            mock_get_processor.return_value = mock_processor
            
            message_data = {
                "message": "/help",
                "user_id": self.test_user["user_id"],
                "username": self.test_user["username"]
            }
            
            response = self.client.post('/api/chat/send', 
                                      json=message_data,
                                      content_type='application/json')
            
            assert response.status_code == 200
    
    def test_command_parameter_validation(self):
        """Test command parameter validation"""
        test_cases = [
            {
                "command": "/epic",  # Missing description
                "expected_error": True
            },
            {
                "command": "/project register",  # Missing path
                "expected_error": True
            },
            {
                "command": "/request_changes",  # Missing description
                "expected_error": True
            }
        ]
        
        for case in test_cases:
            with patch('command_processor.get_processor') as mock_get_processor:
                mock_processor = Mock()
                mock_processor.process_command.return_value = {
                    "success": False,
                    "response": f"Error in command: {case['command']}",
                    "error": "Missing required parameter"
                }
                mock_get_processor.return_value = mock_processor
                
                message_data = {
                    "message": case["command"],
                    "user_id": self.test_user["user_id"],
                    "username": self.test_user["username"]
                }
                
                response = self.client.post('/api/chat/send', 
                                          json=message_data,
                                          content_type='application/json')
                
                assert response.status_code == 200


class TestErrorHandling(TestDiscordChatIntegration):
    """Test error handling and edge cases"""
    
    def test_api_error_responses(self):
        """Test API error response formats"""
        # Test malformed JSON
        response = self.client.post('/api/chat/send', 
                                  data="invalid json",
                                  content_type='application/json')
        assert response.status_code == 400
        
        # Test server error simulation
        with patch('app.chat_history.append', side_effect=Exception("Database error")):
            message_data = {
                "message": "Test message",
                "user_id": "test",
                "username": "Test"
            }
            
            response = self.client.post('/api/chat/send', 
                                      json=message_data,
                                      content_type='application/json')
            assert response.status_code == 500
    
    def test_websocket_error_handling(self):
        """Test WebSocket error handling"""
        # Test invalid WebSocket events
        self.socketio_client.emit('chat_command', {})  # Missing required fields
        
        received_events = self.socketio_client.get_received()
        error_events = [e for e in received_events if e['name'] == 'command_error']
        assert len(error_events) > 0
    
    def test_command_processor_unavailable(self):
        """Test behavior when command processor is unavailable"""
        with patch('command_processor.process_command', side_effect=ImportError("Module not found")):
            message_data = {
                "message": "/help",
                "user_id": self.test_user["user_id"],
                "username": self.test_user["username"]
            }
            
            response = self.client.post('/api/chat/send', 
                                      json=message_data,
                                      content_type='application/json')
            
            # Should not crash, should handle gracefully
            assert response.status_code == 200
    
    def test_concurrent_message_handling(self):
        """Test handling multiple concurrent messages"""
        def send_message(message_text, user_id):
            """Helper to send message"""
            message_data = {
                "message": message_text,
                "user_id": user_id,
                "username": f"User_{user_id}"
            }
            return self.client.post('/api/chat/send', 
                                  json=message_data,
                                  content_type='application/json')
        
        # Send multiple messages concurrently
        import concurrent.futures
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = []
            for i in range(10):
                future = executor.submit(send_message, f"Message {i}", f"user_{i}")
                futures.append(future)
            
            # Wait for all to complete
            responses = [future.result() for future in futures]
        
        # All should succeed
        for response in responses:
            assert response.status_code == 200
        
        # Should have 10 messages in history
        assert len(chat_history) == 10


class TestRealTimeSynchronization(TestDiscordChatIntegration):
    """Test real-time synchronization between clients"""
    
    def test_multi_client_message_sync(self):
        """Test message synchronization across multiple clients"""
        clients = []
        
        try:
            # Create multiple clients
            for i in range(3):
                client = socketio.test_client(app)
                clients.append(client)
                
                # Join chat
                client.emit('join_chat', {
                    "user_id": f"user_{i}",
                    "username": f"User_{i}"
                })
            
            time.sleep(0.1)
            
            # Send message from first client
            clients[0].emit('chat_command', {
                "message": "Hello everyone!",
                "user_id": "user_0",
                "username": "User_0"
            })
            
            time.sleep(0.2)
            
            # All clients should receive the message
            for i, client in enumerate(clients):
                received_events = client.get_received()
                message_events = [e for e in received_events if e['name'] == 'new_chat_message']
                assert len(message_events) > 0
                
                # Find the broadcast message
                broadcast_messages = [e for e in message_events 
                                    if e['args'][0]['message'] == 'Hello everyone!']
                assert len(broadcast_messages) > 0
                
        finally:
            # Clean up clients
            for client in clients:
                if client.is_connected():
                    client.disconnect()
    
    def test_typing_indicator_synchronization(self):
        """Test typing indicator synchronization"""
        client2 = socketio.test_client(app)
        
        try:
            # User starts typing on client 1
            self.socketio_client.emit('start_typing', {
                "user_id": self.test_user["user_id"],
                "username": self.test_user["username"]
            })
            
            time.sleep(0.1)
            
            # Client 2 should receive typing indicator
            client2_events = client2.get_received()
            typing_events = [e for e in client2_events if e['name'] == 'typing_indicator']
            
            # Should have typing indicator for the user
            typing_indicators = [e for e in typing_events 
                               if e['args'][0]['user_id'] == self.test_user["user_id"] 
                               and e['args'][0]['typing'] is True]
            assert len(typing_indicators) > 0
            
        finally:
            client2.disconnect()
    
    def test_state_synchronization(self):
        """Test workflow state synchronization"""
        # Mock state broadcaster
        with patch('app.broadcaster') as mock_broadcaster:
            mock_broadcaster.get_current_state.return_value = {
                "workflow_state": "SPRINT_ACTIVE",
                "tdd_cycles": {},
                "last_updated": datetime.now().isoformat()
            }
            
            # Request state from client
            self.socketio_client.emit('request_state')
            
            # Should receive state update
            received_events = self.socketio_client.get_received()
            state_events = [e for e in received_events if e['name'] == 'state_update']
            assert len(state_events) > 0
            
            state_data = state_events[0]['args'][0]
            assert state_data['workflow_state'] == 'SPRINT_ACTIVE'
    
    def test_connection_resilience(self):
        """Test connection handling and resilience"""
        # Test disconnect and reconnect
        original_sid = self.socketio_client.eio_sid
        
        # Disconnect
        self.socketio_client.disconnect()
        assert not self.socketio_client.is_connected()
        
        time.sleep(0.1)
        
        # Reconnect
        self.socketio_client = socketio.test_client(app)
        assert self.socketio_client.is_connected()
        
        # Should get initial state on reconnect
        received_events = self.socketio_client.get_received()
        state_events = [e for e in received_events if e['name'] == 'state_update']
        assert len(state_events) > 0


class TestPerformanceAndLoad(TestDiscordChatIntegration):
    """Test performance characteristics and load handling"""
    
    def test_message_history_performance(self):
        """Test performance with large message history"""
        # Add large number of messages
        large_history = []
        for i in range(1000):
            message = {
                "id": str(uuid.uuid4()),
                "user_id": f"user_{i % 10}",
                "username": f"User_{i % 10}",
                "message": f"Message {i} - " + "x" * 100,  # Longer messages
                "timestamp": datetime.now().isoformat(),
                "type": "user"
            }
            large_history.append(message)
        
        chat_history.extend(large_history)
        
        # Test API response time
        start_time = time.time()
        response = self.client.get('/api/chat/history?limit=50')
        end_time = time.time()
        
        assert response.status_code == 200
        # Should respond within reasonable time (< 1 second)
        assert (end_time - start_time) < 1.0
        
        data = response.get_json()
        assert len(data["messages"]) == 50
        assert data["total_count"] >= 1000
    
    def test_concurrent_websocket_connections(self):
        """Test handling multiple concurrent WebSocket connections"""
        clients = []
        
        try:
            # Create multiple concurrent connections
            for i in range(10):
                client = socketio.test_client(app)
                clients.append(client)
                assert client.is_connected()
            
            # All should be able to send messages
            for i, client in enumerate(clients):
                client.emit('chat_command', {
                    "message": f"Message from client {i}",
                    "user_id": f"client_{i}",
                    "username": f"Client_{i}"
                })
            
            time.sleep(0.2)
            
            # Verify all messages were received
            assert len(chat_history) == 10
            
        finally:
            # Clean up all clients
            for client in clients:
                if client.is_connected():
                    client.disconnect()
    
    def test_websocket_message_throughput(self):
        """Test WebSocket message throughput"""
        # Send multiple messages rapidly
        message_count = 50
        start_time = time.time()
        
        for i in range(message_count):
            self.socketio_client.emit('chat_command', {
                "message": f"Rapid message {i}",
                "user_id": "speed_test",
                "username": "SpeedTest"
            })
        
        # Wait for processing
        time.sleep(1.0)
        
        end_time = time.time()
        
        # Should handle all messages
        user_messages = [msg for msg in chat_history if msg["user_id"] == "speed_test"]
        assert len(user_messages) == message_count
        
        # Calculate throughput (should be reasonable)
        throughput = message_count / (end_time - start_time)
        assert throughput > 10  # At least 10 messages per second


@pytest.mark.asyncio 
class TestAsyncWebSocketHandling(TestDiscordChatIntegration):
    """Test asynchronous WebSocket event handling"""
    
    async def test_async_command_processing(self):
        """Test asynchronous command processing"""
        with patch('command_processor.get_processor') as mock_get_processor:
            # Simulate slow command processing
            async def slow_process_command(message, user_id):
                await asyncio.sleep(0.1)
                return {
                    "success": True,
                    "response": "Slow command completed",
                    "command": message
                }
            
            mock_processor = Mock()
            mock_processor.process_command = slow_process_command
            mock_get_processor.return_value = mock_processor
            
            # Send command
            self.socketio_client.emit('chat_command', {
                "message": "/slow_command",
                "user_id": "async_test",
                "username": "AsyncTest"
            })
            
            # Should not block
            await asyncio.sleep(0.2)
            
            # Command should have been processed
            user_messages = [msg for msg in chat_history if msg["user_id"] == "async_test"]
            assert len(user_messages) > 0
    
    async def test_websocket_event_ordering(self):
        """Test that WebSocket events maintain proper ordering"""
        events_order = []
        
        # Send sequence of events rapidly
        for i in range(5):
            self.socketio_client.emit('start_typing', {
                "user_id": f"order_test_{i}",
                "username": f"OrderTest_{i}"
            })
            
            self.socketio_client.emit('chat_command', {
                "message": f"Message {i}",
                "user_id": f"order_test_{i}", 
                "username": f"OrderTest_{i}"
            })
            
            self.socketio_client.emit('stop_typing', {
                "user_id": f"order_test_{i}",
                "username": f"OrderTest_{i}"
            })
        
        await asyncio.sleep(0.5)
        
        # Messages should appear in order
        messages = [msg for msg in chat_history if msg["user_id"].startswith("order_test_")]
        for i, msg in enumerate(messages):
            assert f"Message {i}" in msg["message"]


def run_integration_tests():
    """Run all integration tests"""
    pytest.main([__file__, "-v", "--tb=short"])


if __name__ == "__main__":
    run_integration_tests()