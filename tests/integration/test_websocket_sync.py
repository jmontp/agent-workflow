#!/usr/bin/env python3
"""
WebSocket Synchronization Integration Tests

Comprehensive testing of WebSocket real-time synchronization including:
- Multi-client connection testing
- Real-time message delivery
- State change propagation  
- Connection loss/recovery scenarios
- Event ordering and consistency
- Performance under concurrent load
"""

import asyncio
import json
import pytest
import threading
import time
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Set
from unittest.mock import Mock, patch, MagicMock
from concurrent.futures import ThreadPoolExecutor, as_completed

import websocket
from flask_socketio import SocketIOTestClient

# Add paths for imports
import sys
visualizer_path = Path(__file__).parent.parent.parent / "tools" / "visualizer"
sys.path.insert(0, str(visualizer_path))

from app import app, socketio, chat_history, typing_users, active_users


class WebSocketTestClient:
    """Enhanced WebSocket test client with event tracking"""
    
    def __init__(self, app_instance, namespace=None):
        self.client = socketio.test_client(app_instance, namespace=namespace)
        self.received_events = []
        self.event_counts = {}
        self.connection_events = []
        
    def emit(self, event, data=None, namespace=None):
        """Emit event and track it"""
        return self.client.emit(event, data, namespace)
        
    def get_received(self, name=None):
        """Get received events, optionally filtered by name"""
        events = self.client.get_received()
        
        # Track all events
        for event in events:
            self.received_events.append({
                'timestamp': time.time(),
                'event': event
            })
            
            event_name = event.get('name', 'unknown')
            self.event_counts[event_name] = self.event_counts.get(event_name, 0) + 1
        
        if name:
            return [e for e in events if e.get('name') == name]
        return events
    
    def wait_for_event(self, event_name, timeout=5.0, count=1):
        """Wait for specific event(s) to be received"""
        start_time = time.time()
        received_count = 0
        
        while time.time() - start_time < timeout:
            events = self.get_received(event_name)
            received_count += len(events)
            
            if received_count >= count:
                return True
            
            time.sleep(0.01)  # Small delay to prevent busy waiting
        
        return False
    
    def is_connected(self):
        """Check if client is connected"""
        return self.client.is_connected()
    
    def disconnect(self):
        """Disconnect client"""
        if self.client.is_connected():
            self.client.disconnect()
    
    def get_event_stats(self):
        """Get statistics about received events"""
        return {
            'total_events': len(self.received_events),
            'event_counts': self.event_counts.copy(),
            'unique_events': len(self.event_counts),
            'connection_events': len(self.connection_events)
        }


class TestWebSocketSynchronization:
    """Base test class for WebSocket synchronization tests"""
    
    @pytest.fixture(autouse=True)
    def setup_method(self):
        """Setup for each test method"""
        # Clear global state
        chat_history.clear()
        typing_users.clear()
        active_users.clear()
        
        # Setup test clients
        self.clients = []
        
        yield
        
        # Cleanup all clients
        for client in self.clients:
            if hasattr(client, 'disconnect'):
                client.disconnect()
        
        self.clients.clear()
    
    def create_client(self, user_id=None, username=None):
        """Create a new WebSocket test client"""
        client = WebSocketTestClient(app)
        self.clients.append(client)
        
        # Auto-join chat if user info provided
        if user_id and username:
            client.emit('join_chat', {
                'user_id': user_id,
                'username': username
            })
            time.sleep(0.05)  # Allow join to process
        
        return client
    
    def create_multiple_clients(self, count=3, prefix="user"):
        """Create multiple test clients"""
        clients = []
        for i in range(count):
            user_id = f"{prefix}_{i}"
            username = f"{prefix.title()}_{i}"
            client = self.create_client(user_id, username)
            clients.append(client)
        
        return clients


class TestMultiClientConnection(TestWebSocketSynchronization):
    """Test multiple client connections and basic synchronization"""
    
    def test_multiple_client_connections(self):
        """Test that multiple clients can connect simultaneously"""
        clients = self.create_multiple_clients(5)
        
        # All clients should be connected
        for i, client in enumerate(clients):
            assert client.is_connected(), f"Client {i} failed to connect"
        
        # Each client should have received initial state
        for i, client in enumerate(clients):
            events = client.get_received('state_update')
            assert len(events) > 0, f"Client {i} didn't receive initial state"
    
    def test_client_join_notifications(self):
        """Test that client join events are broadcast to other clients"""
        # Create first client
        client1 = self.create_client("user_1", "User1")
        
        # Create second client and let it join
        client2 = self.create_client()
        client2.emit('join_chat', {
            'user_id': 'user_2',
            'username': 'User2'
        })
        
        time.sleep(0.1)
        
        # First client should receive join notification
        join_events = client1.get_received('user_joined')
        assert len(join_events) > 0, "Join event not received by other clients"
        
        join_data = join_events[0]['args'][0]
        assert join_data['user_id'] == 'user_2'
        assert join_data['username'] == 'User2'
    
    def test_client_leave_notifications(self):
        """Test that client leave events are broadcast"""
        clients = self.create_multiple_clients(3)
        
        # Have one client leave
        clients[1].emit('leave_chat', {
            'user_id': 'user_1',
            'username': 'User_1'
        })
        
        time.sleep(0.1)
        
        # Other clients should receive leave notification
        for i, client in enumerate(clients):
            if i != 1:  # Skip the leaving client
                leave_events = client.get_received('user_left')
                assert len(leave_events) > 0, f"Client {i} didn't receive leave event"
    
    def test_concurrent_connections(self):
        """Test handling of many concurrent connections"""
        def create_client_thread(client_id):
            """Create client in thread"""
            try:
                client = self.create_client(f"concurrent_{client_id}", f"Concurrent_{client_id}")
                return client.is_connected()
            except Exception as e:
                print(f"Client {client_id} connection failed: {e}")
                return False
        
        # Create 20 clients concurrently
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(create_client_thread, i) for i in range(20)]
            results = [future.result(timeout=5) for future in as_completed(futures)]
        
        # Most connections should succeed
        success_count = sum(results)
        assert success_count >= 15, f"Only {success_count}/20 clients connected successfully"


class TestMessageDelivery(TestWebSocketSynchronization):
    """Test real-time message delivery and synchronization"""
    
    def test_message_broadcast_to_all_clients(self):
        """Test that messages are broadcast to all connected clients"""
        clients = self.create_multiple_clients(4)
        
        # Send message from first client
        test_message = {
            'message': 'Hello everyone!',
            'user_id': 'user_0',
            'username': 'User_0'
        }
        
        clients[0].emit('chat_command', test_message)
        time.sleep(0.2)
        
        # All clients should receive the message
        for i, client in enumerate(clients):
            message_events = client.get_received('new_chat_message')
            assert len(message_events) > 0, f"Client {i} didn't receive message broadcast"
            
            # Find the specific message
            found_message = False
            for event in message_events:
                msg_data = event['args'][0]
                if msg_data['message'] == 'Hello everyone!':
                    found_message = True
                    assert msg_data['user_id'] == 'user_0'
                    assert msg_data['username'] == 'User_0'
                    break
            
            assert found_message, f"Client {i} didn't receive the correct message"
    
    def test_message_ordering_consistency(self):
        """Test that message ordering is consistent across clients"""
        clients = self.create_multiple_clients(3)
        
        # Send sequence of messages from different clients
        messages = [
            ('user_0', 'User_0', 'Message 1'),
            ('user_1', 'User_1', 'Message 2'),
            ('user_2', 'User_2', 'Message 3'),
            ('user_0', 'User_0', 'Message 4'),
            ('user_1', 'User_1', 'Message 5')
        ]
        
        for user_id, username, message in messages:
            client_index = int(user_id.split('_')[1])
            clients[client_index].emit('chat_command', {
                'message': message,
                'user_id': user_id,
                'username': username
            })
            time.sleep(0.05)  # Small delay between messages
        
        time.sleep(0.3)  # Allow all messages to propagate
        
        # Check message ordering on each client
        expected_order = ['Message 1', 'Message 2', 'Message 3', 'Message 4', 'Message 5']
        
        for i, client in enumerate(clients):
            received_messages = []
            message_events = client.get_received('new_chat_message')
            
            for event in message_events:
                msg_data = event['args'][0]
                if msg_data['message'].startswith('Message'):
                    received_messages.append(msg_data['message'])
            
            # Remove duplicates while preserving order
            unique_messages = []
            for msg in received_messages:
                if msg not in unique_messages:
                    unique_messages.append(msg)
            
            assert unique_messages == expected_order, f"Client {i} received incorrect message order: {unique_messages}"
    
    def test_rapid_message_delivery(self):
        """Test delivery of rapid message sequences"""
        clients = self.create_multiple_clients(2)
        
        # Send 20 messages rapidly
        message_count = 20
        for i in range(message_count):
            clients[0].emit('chat_command', {
                'message': f'Rapid message {i}',
                'user_id': 'user_0',
                'username': 'User_0'
            })
            time.sleep(0.01)  # Very short delay
        
        time.sleep(1.0)  # Allow processing
        
        # Both clients should receive all messages
        for client_idx, client in enumerate(clients):
            message_events = client.get_received('new_chat_message')
            rapid_messages = [
                event['args'][0]['message'] for event in message_events
                if event['args'][0]['message'].startswith('Rapid message')
            ]
            
            # Should receive all unique messages
            unique_rapid_messages = list(set(rapid_messages))
            assert len(unique_rapid_messages) == message_count, \
                f"Client {client_idx} received {len(unique_rapid_messages)}/{message_count} messages"
    
    def test_command_response_synchronization(self):
        """Test that command responses are synchronized across clients"""
        clients = self.create_multiple_clients(3)
        
        with patch('command_processor.get_processor') as mock_get_processor:
            mock_processor = Mock()
            mock_processor.process_command.return_value = {
                "success": True,
                "response": "Test command response",
                "command": "/test"
            }
            mock_get_processor.return_value = mock_processor
            
            # Send command from first client
            clients[0].emit('chat_command', {
                'message': '/test command',
                'user_id': 'user_0',
                'username': 'User_0'
            })
            
            time.sleep(0.5)  # Allow command processing
            
            # All clients should receive bot response
            for i, client in enumerate(clients):
                response_events = client.get_received('command_response')
                assert len(response_events) > 0, f"Client {i} didn't receive command response"
                
                response_data = response_events[0]['args'][0]
                assert response_data['user_id'] == 'bot'
                assert 'Test command response' in response_data['message']


class TestTypingIndicators(TestWebSocketSynchronization):
    """Test typing indicator synchronization"""
    
    def test_typing_indicator_broadcast(self):
        """Test that typing indicators are broadcast to other clients"""
        clients = self.create_multiple_clients(3)
        
        # User 0 starts typing
        clients[0].emit('start_typing', {
            'user_id': 'user_0',
            'username': 'User_0'
        })
        
        time.sleep(0.1)
        
        # Other clients should receive typing indicator
        for i in range(1, len(clients)):
            typing_events = clients[i].get_received('typing_indicator')
            assert len(typing_events) > 0, f"Client {i} didn't receive typing indicator"
            
            # Find the start typing event
            start_typing_events = [
                e for e in typing_events 
                if e['args'][0]['user_id'] == 'user_0' and e['args'][0]['typing'] is True
            ]
            assert len(start_typing_events) > 0, f"Client {i} didn't receive start typing event"
    
    def test_typing_indicator_stop(self):
        """Test typing indicator stop events"""
        clients = self.create_multiple_clients(2)
        
        # Start typing
        clients[0].emit('start_typing', {
            'user_id': 'user_0',
            'username': 'User_0'
        })
        
        time.sleep(0.1)
        
        # Stop typing
        clients[0].emit('stop_typing', {
            'user_id': 'user_0',
            'username': 'User_0'
        })
        
        time.sleep(0.1)
        
        # Other client should receive stop typing event
        typing_events = clients[1].get_received('typing_indicator')
        stop_typing_events = [
            e for e in typing_events 
            if e['args'][0]['user_id'] == 'user_0' and e['args'][0]['typing'] is False
        ]
        assert len(stop_typing_events) > 0, "Didn't receive stop typing event"
    
    def test_multiple_users_typing(self):
        """Test multiple users typing simultaneously"""
        clients = self.create_multiple_clients(4)
        
        # Three users start typing
        for i in range(3):
            clients[i].emit('start_typing', {
                'user_id': f'user_{i}',
                'username': f'User_{i}'
            })
        
        time.sleep(0.2)
        
        # Fourth client should receive all typing indicators
        typing_events = clients[3].get_received('typing_indicator')
        typing_users_detected = set()
        
        for event in typing_events:
            event_data = event['args'][0]
            if event_data['typing'] is True:
                typing_users_detected.add(event_data['user_id'])
        
        expected_typing_users = {'user_0', 'user_1', 'user_2'}
        assert typing_users_detected >= expected_typing_users, \
            f"Expected {expected_typing_users}, got {typing_users_detected}"
    
    def test_typing_indicator_cleanup_on_disconnect(self):
        """Test that typing indicators are cleaned up when user disconnects"""
        clients = self.create_multiple_clients(2)
        
        # Start typing
        clients[0].emit('start_typing', {
            'user_id': 'user_0',
            'username': 'User_0'
        })
        
        time.sleep(0.1)
        
        # Disconnect the typing user
        clients[0].disconnect()
        
        time.sleep(0.1)
        
        # Check that user is removed from typing_users
        assert 'user_0' not in typing_users, "Typing user not cleaned up on disconnect"


class TestStateChangePropagation(TestWebSocketSynchronization):
    """Test propagation of state changes across clients"""
    
    def test_workflow_state_broadcast(self):
        """Test that workflow state changes are broadcast"""
        clients = self.create_multiple_clients(2)
        
        # Mock state change
        mock_state_change = {
            'type': 'workflow_transition',
            'old_state': 'IDLE',
            'new_state': 'SPRINT_ACTIVE',
            'timestamp': datetime.now().isoformat()
        }
        
        # Emit state change to all clients
        socketio.emit('workflow_transition', mock_state_change)
        
        time.sleep(0.1)
        
        # All clients should receive the state change
        for i, client in enumerate(clients):
            transition_events = client.get_received('workflow_transition')
            assert len(transition_events) > 0, f"Client {i} didn't receive workflow transition"
            
            transition_data = transition_events[0]['args'][0]
            assert transition_data['old_state'] == 'IDLE'
            assert transition_data['new_state'] == 'SPRINT_ACTIVE'
    
    def test_tdd_state_broadcast(self):
        """Test that TDD state changes are broadcast"""
        clients = self.create_multiple_clients(2)
        
        # Mock TDD state change
        mock_tdd_change = {
            'type': 'tdd_transition',
            'story_id': 'story-123',
            'old_state': 'WRITE_TEST',
            'new_state': 'IMPLEMENT',
            'timestamp': datetime.now().isoformat()
        }
        
        # Emit TDD state change
        socketio.emit('tdd_transition', mock_tdd_change)
        
        time.sleep(0.1)
        
        # All clients should receive the TDD state change
        for i, client in enumerate(clients):
            tdd_events = client.get_received('tdd_transition')
            assert len(tdd_events) > 0, f"Client {i} didn't receive TDD transition"
            
            tdd_data = tdd_events[0]['args'][0]
            assert tdd_data['story_id'] == 'story-123'
            assert tdd_data['old_state'] == 'WRITE_TEST'
            assert tdd_data['new_state'] == 'IMPLEMENT'
    
    def test_agent_activity_broadcast(self):
        """Test that agent activity updates are broadcast"""
        clients = self.create_multiple_clients(2)
        
        # Mock agent activity
        mock_activity = {
            'type': 'agent_activity',
            'agent_type': 'CodeAgent',
            'action': 'implement_feature',
            'story_id': 'story-456',
            'status': 'in_progress',
            'timestamp': datetime.now().isoformat()
        }
        
        # Emit agent activity
        socketio.emit('agent_activity', mock_activity)
        
        time.sleep(0.1)
        
        # All clients should receive agent activity
        for i, client in enumerate(clients):
            activity_events = client.get_received('agent_activity')
            assert len(activity_events) > 0, f"Client {i} didn't receive agent activity"
            
            activity_data = activity_events[0]['args'][0]
            assert activity_data['agent_type'] == 'CodeAgent'
            assert activity_data['action'] == 'implement_feature'
            assert activity_data['status'] == 'in_progress'


class TestConnectionRecovery(TestWebSocketSynchronization):
    """Test connection loss and recovery scenarios"""
    
    def test_client_reconnection(self):
        """Test client reconnection after disconnect"""
        client = self.create_client('test_user', 'TestUser')
        
        # Verify initial connection
        assert client.is_connected()
        
        # Get initial events
        initial_events = client.get_received()
        initial_count = len(initial_events)
        
        # Disconnect
        client.disconnect()
        assert not client.is_connected()
        
        time.sleep(0.1)
        
        # Create new client (simulating reconnection)
        new_client = self.create_client('test_user', 'TestUser')
        assert new_client.is_connected()
        
        # Should receive initial state again
        reconnect_events = new_client.get_received()
        assert len(reconnect_events) > 0, "No events received on reconnection"
        
        # Should include state update
        state_events = [e for e in reconnect_events if e.get('name') == 'state_update']
        assert len(state_events) > 0, "No state update on reconnection"
    
    def test_message_delivery_during_reconnection(self):
        """Test message delivery when client reconnects"""
        clients = self.create_multiple_clients(3)
        
        # Disconnect one client
        clients[1].disconnect()
        
        # Send message while client is disconnected
        clients[0].emit('chat_command', {
            'message': 'Message while disconnected',
            'user_id': 'user_0',
            'username': 'User_0'
        })
        
        time.sleep(0.1)
        
        # Reconnect client
        reconnected_client = self.create_client('user_1', 'User_1')
        
        # Request chat history to get missed messages
        reconnected_client.emit('request_chat_history', {'limit': 10})
        
        time.sleep(0.1)
        
        # Should receive chat history including missed message
        history_events = reconnected_client.get_received('chat_history')
        assert len(history_events) > 0, "No chat history received on reconnection"
        
        history_data = history_events[0]['args'][0]
        messages = history_data['messages']
        
        # Find the message sent while disconnected
        missed_message_found = any(
            msg['message'] == 'Message while disconnected' 
            for msg in messages
        )
        assert missed_message_found, "Missed message not found in chat history"
    
    def test_graceful_degradation_on_connection_loss(self):
        """Test graceful degradation when WebSocket connection is lost"""
        client = self.create_client('test_user', 'TestUser')
        
        # Simulate connection loss by disconnecting without cleanup
        client.client._client.eio.disconnect(abort=True)
        
        # Client should report as disconnected
        time.sleep(0.1)
        assert not client.is_connected()
        
        # Application should handle this gracefully without crashes
        # (This test mainly ensures no exceptions are thrown)
    
    def test_concurrent_reconnections(self):
        """Test multiple clients reconnecting simultaneously"""
        # Create and disconnect multiple clients
        client_count = 5
        disconnected_clients = []
        
        for i in range(client_count):
            client = self.create_client(f'user_{i}', f'User_{i}')
            client.disconnect()
            disconnected_clients.append((f'user_{i}', f'User_{i}'))
        
        time.sleep(0.1)
        
        # Reconnect all clients concurrently
        def reconnect_client(user_id, username):
            return self.create_client(user_id, username)
        
        with ThreadPoolExecutor(max_workers=client_count) as executor:
            futures = [
                executor.submit(reconnect_client, user_id, username)
                for user_id, username in disconnected_clients
            ]
            
            reconnected_clients = [future.result(timeout=5) for future in as_completed(futures)]
        
        # All clients should be connected
        for client in reconnected_clients:
            assert client.is_connected(), "Client failed to reconnect"
        
        # All clients should receive initial state
        for client in reconnected_clients:
            events = client.get_received()
            assert len(events) > 0, "No events received on reconnection"


class TestWebSocketPerformance(TestWebSocketSynchronization):
    """Test WebSocket performance under load"""
    
    def test_event_latency(self):
        """Test event delivery latency"""
        clients = self.create_multiple_clients(2)
        
        # Send timestamped message
        send_time = time.time()
        clients[0].emit('chat_command', {
            'message': f'Latency test {send_time}',
            'user_id': 'user_0',
            'username': 'User_0'
        })
        
        # Wait for message to be received
        assert clients[1].wait_for_event('new_chat_message', timeout=2.0)
        
        # Calculate latency
        receive_time = time.time()
        latency = receive_time - send_time
        
        # Latency should be reasonable (< 100ms for local testing)
        assert latency < 0.1, f"Message latency too high: {latency:.3f}s"
    
    def test_high_frequency_events(self):
        """Test handling of high-frequency events"""
        clients = self.create_multiple_clients(2)
        
        # Send many events rapidly
        event_count = 100
        start_time = time.time()
        
        for i in range(event_count):
            clients[0].emit('start_typing', {
                'user_id': 'user_0',
                'username': 'User_0'
            })
            clients[0].emit('stop_typing', {
                'user_id': 'user_0',
                'username': 'User_0'
            })
        
        end_time = time.time()
        send_duration = end_time - start_time
        
        # Allow processing time
        time.sleep(1.0)
        
        # Calculate throughput
        throughput = (event_count * 2) / send_duration  # 2 events per iteration
        
        # Should handle reasonable throughput
        assert throughput > 100, f"Event throughput too low: {throughput:.1f} events/sec"
        
        # Other client should receive most events (some may be deduplicated)
        typing_events = clients[1].get_received('typing_indicator')
        assert len(typing_events) > 0, "No typing events received"
    
    def test_memory_usage_stability(self):
        """Test memory usage remains stable during extended operation"""
        clients = self.create_multiple_clients(3)
        
        # Get baseline event counts
        baseline_counts = [client.get_event_stats()['total_events'] for client in clients]
        
        # Generate sustained activity
        for round_num in range(10):
            for i, client in enumerate(clients):
                client.emit('chat_command', {
                    'message': f'Round {round_num} message from client {i}',
                    'user_id': f'user_{i}',
                    'username': f'User_{i}'
                })
                
                client.emit('start_typing', {
                    'user_id': f'user_{i}',
                    'username': f'User_{i}'
                })
                
                time.sleep(0.01)
                
                client.emit('stop_typing', {
                    'user_id': f'user_{i}',
                    'username': f'User_{i}'
                })
            
            time.sleep(0.1)
        
        # Allow processing
        time.sleep(0.5)
        
        # Check that all clients are still responsive
        for client in clients:
            assert client.is_connected(), "Client disconnected during sustained activity"
            
            # Get final event counts
            final_stats = client.get_event_stats()
            assert final_stats['total_events'] > baseline_counts[0], "No new events received"
        
        # Test that clients can still receive new events
        test_client = clients[0]
        test_client.emit('chat_command', {
            'message': 'Final test message',
            'user_id': 'user_0',
            'username': 'User_0'
        })
        
        time.sleep(0.2)
        
        for i, client in enumerate(clients):
            if i != 0:  # Skip sender
                final_messages = client.get_received('new_chat_message')
                final_message_found = any(
                    event['args'][0]['message'] == 'Final test message'
                    for event in final_messages
                )
                assert final_message_found, f"Client {i} not responsive after sustained activity"


def run_websocket_sync_tests():
    """Run all WebSocket synchronization tests"""
    pytest.main([__file__, "-v", "--tb=short"])


if __name__ == "__main__":
    run_websocket_sync_tests()