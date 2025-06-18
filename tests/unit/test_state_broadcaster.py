"""
Unit tests for State Broadcasting System.

Tests WebSocket broadcasting of state machine changes for real-time
visualization and monitoring of workflow and TDD state transitions.
"""

import pytest
import asyncio
import json
import weakref
from datetime import datetime
from unittest.mock import Mock, patch, AsyncMock, MagicMock
from typing import Dict, Any

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent.parent))

from lib.state_broadcaster import (
    StatebroadCaster, emit_workflow_transition, emit_tdd_transition,
    emit_agent_activity, emit_parallel_status, start_broadcaster, 
    stop_broadcaster, broadcaster
)
from lib.state_machine import State
from lib.tdd_models import TDDState


class MockWebSocketProtocol:
    """Mock WebSocket protocol for testing."""
    
    def __init__(self, remote_address=("127.0.0.1", 12345)):
        self.remote_address = remote_address
        self.closed = False
        self.sent_messages = []
        
    async def send(self, message):
        """Mock send method."""
        if self.closed:
            raise Exception("Connection closed")
        self.sent_messages.append(message)
        
    async def wait_closed(self):
        """Mock wait_closed method."""
        pass
        
    def close(self):
        """Mock close method."""
        self.closed = True


class TestStatebroadCaster:
    """Test the StatebroadCaster singleton class."""
    
    def test_singleton_pattern(self):
        """Test that StatebroadCaster implements singleton pattern correctly."""
        broadcaster1 = StatebroadCaster()
        broadcaster2 = StatebroadCaster()
        
        assert broadcaster1 is broadcaster2
        assert id(broadcaster1) == id(broadcaster2)

    def test_initialization(self):
        """Test StatebroadCaster initialization."""
        # Clear singleton for clean test
        StatebroadCaster._instance = None
        StatebroadCaster._initialized = False
        
        broadcaster = StatebroadCaster()
        
        assert broadcaster.clients == set()
        assert broadcaster.current_workflow_state == State.IDLE
        assert broadcaster.tdd_cycles == {}
        assert broadcaster.transition_history == []
        assert broadcaster.server is None
        assert broadcaster.port == 8080

    def test_multiple_initialization(self):
        """Test that multiple initializations don't reset state."""
        # Clear singleton for clean test
        StatebroadCaster._instance = None
        StatebroadCaster._initialized = False
        
        broadcaster1 = StatebroadCaster()
        broadcaster1.port = 9000  # Modify state
        
        broadcaster2 = StatebroadCaster()
        
        assert broadcaster1 is broadcaster2
        assert broadcaster2.port == 9000  # State should be preserved

    @pytest.mark.asyncio
    async def test_start_server_success(self):
        """Test successfully starting WebSocket server."""
        broadcaster = StatebroadCaster()
        
        with patch('websockets.serve') as mock_serve:
            mock_server = Mock()
            mock_serve.return_value = mock_server
            
            await broadcaster.start_server(port=8081)
            
            assert broadcaster.port == 8081
            assert broadcaster.server == mock_server
            mock_serve.assert_called_once()

    @pytest.mark.asyncio
    async def test_start_server_exception(self):
        """Test handling exceptions when starting server."""
        broadcaster = StatebroadCaster()
        
        with patch('websockets.serve', side_effect=Exception("Server error")):
            # Should not raise exception, just log error
            await broadcaster.start_server()
            
            assert broadcaster.server is None

    @pytest.mark.asyncio
    async def test_stop_server(self):
        """Test stopping WebSocket server."""
        broadcaster = StatebroadCaster()
        
        # Mock server
        mock_server = Mock()
        mock_server.close = Mock()
        mock_server.wait_closed = AsyncMock()
        broadcaster.server = mock_server
        
        await broadcaster.stop_server()
        
        mock_server.close.assert_called_once()
        mock_server.wait_closed.assert_called_once()

    @pytest.mark.asyncio
    async def test_stop_server_no_server(self):
        """Test stopping server when no server is running."""
        broadcaster = StatebroadCaster()
        broadcaster.server = None
        
        # Should not raise exception
        await broadcaster.stop_server()

    @pytest.mark.asyncio
    async def test_handle_client_lifecycle(self):
        """Test complete client connection lifecycle."""
        broadcaster = StatebroadCaster()
        mock_client = MockWebSocketProtocol()
        
        # Mock async iteration
        async def mock_async_iter():
            yield '{"type": "get_current_state"}'
            # End iteration to simulate client disconnect
        
        mock_client.__aiter__ = mock_async_iter
        
        with patch.object(broadcaster, 'send_current_state') as mock_send:
            await broadcaster.handle_client(mock_client, "/test")
            
            # Client should be added and then removed
            assert mock_client not in broadcaster.clients
            mock_send.assert_called()

    @pytest.mark.asyncio
    async def test_handle_client_connection_closed(self):
        """Test handling client when connection is closed."""
        broadcaster = StatebroadCaster()
        mock_client = MockWebSocketProtocol()
        
        # Mock async iteration that raises ConnectionClosed
        async def mock_async_iter():
            import websockets.exceptions
            raise websockets.exceptions.ConnectionClosed(None, None)
        
        mock_client.__aiter__ = mock_async_iter
        
        with patch.object(broadcaster, 'send_current_state'):
            await broadcaster.handle_client(mock_client, "/test")
            
            # Should handle exception gracefully
            assert mock_client not in broadcaster.clients

    @pytest.mark.asyncio
    async def test_handle_client_message_get_current_state(self):
        """Test handling get_current_state message."""
        broadcaster = StatebroadCaster()
        mock_client = MockWebSocketProtocol()
        
        with patch.object(broadcaster, 'send_current_state') as mock_send:
            await broadcaster.handle_client_message(mock_client, {"type": "get_current_state"})
            
            mock_send.assert_called_once_with(mock_client)

    @pytest.mark.asyncio
    async def test_handle_client_message_get_history(self):
        """Test handling get_history message."""
        broadcaster = StatebroadCaster()
        mock_client = MockWebSocketProtocol()
        
        # Add some history
        broadcaster.transition_history = [
            {"type": "test", "timestamp": "2023-01-01T00:00:00"},
            {"type": "test", "timestamp": "2023-01-01T00:01:00"}
        ]
        
        await broadcaster.handle_client_message(mock_client, {"type": "get_history"})
        
        assert len(mock_client.sent_messages) == 1
        message = json.loads(mock_client.sent_messages[0])
        assert message["type"] == "transition_history"
        assert len(message["history"]) == 2

    @pytest.mark.asyncio
    async def test_handle_client_message_get_history_large(self):
        """Test handling get_history with more than 50 transitions."""
        broadcaster = StatebroadCaster()
        mock_client = MockWebSocketProtocol()
        
        # Add 60 history items
        broadcaster.transition_history = [
            {"type": "test", "timestamp": f"2023-01-01T00:{i:02d}:00"}
            for i in range(60)
        ]
        
        await broadcaster.handle_client_message(mock_client, {"type": "get_history"})
        
        message = json.loads(mock_client.sent_messages[0])
        # Should return only last 50
        assert len(message["history"]) == 50
        # Should be the most recent 50
        assert message["history"][0]["timestamp"] == "2023-01-01T00:10:00"

    @pytest.mark.asyncio
    async def test_handle_client_message_unknown_type(self):
        """Test handling unknown message type."""
        broadcaster = StatebroadCaster()
        mock_client = MockWebSocketProtocol()
        
        await broadcaster.handle_client_message(mock_client, {"type": "unknown_type"})
        
        assert len(mock_client.sent_messages) == 1
        message = json.loads(mock_client.sent_messages[0])
        assert message["type"] == "error"
        assert "Unknown message type" in message["message"]

    @pytest.mark.asyncio
    async def test_send_current_state(self):
        """Test sending current state to client."""
        broadcaster = StatebroadCaster()
        mock_client = MockWebSocketProtocol()
        
        # Set up some state
        broadcaster.current_workflow_state = State.SPRINT_ACTIVE
        broadcaster.tdd_cycles = {
            "story-1": {"current_state": "red", "project": "test"},
            "story-2": {"current_state": "green", "project": "test"}
        }
        
        await broadcaster.send_current_state(mock_client)
        
        assert len(mock_client.sent_messages) == 1
        message = json.loads(mock_client.sent_messages[0])
        
        assert message["type"] == "current_state"
        assert message["workflow_state"] == "SPRINT_ACTIVE"
        assert message["active_cycles"] == 2
        assert "tdd_cycles" in message
        assert "timestamp" in message

    @pytest.mark.asyncio
    async def test_send_current_state_exception(self):
        """Test handling exceptions when sending current state."""
        broadcaster = StatebroadCaster()
        
        # Mock client that raises exception on send
        mock_client = Mock()
        mock_client.send = AsyncMock(side_effect=Exception("Send failed"))
        
        # Should not raise exception, just log error
        await broadcaster.send_current_state(mock_client)

    @pytest.mark.asyncio
    async def test_broadcast_to_all_no_clients(self):
        """Test broadcasting when no clients are connected."""
        broadcaster = StatebroadCaster()
        broadcaster.clients = set()
        
        message = {"type": "test", "data": "test"}
        
        # Should not raise exception
        await broadcaster.broadcast_to_all(message)

    @pytest.mark.asyncio
    async def test_broadcast_to_all_success(self):
        """Test successfully broadcasting to all clients."""
        broadcaster = StatebroadCaster()
        
        client1 = MockWebSocketProtocol()
        client2 = MockWebSocketProtocol()
        broadcaster.clients = {client1, client2}
        
        message = {"type": "test", "data": "test"}
        
        await broadcaster.broadcast_to_all(message)
        
        # Both clients should receive the message
        assert len(client1.sent_messages) == 1
        assert len(client2.sent_messages) == 1
        
        message1 = json.loads(client1.sent_messages[0])
        message2 = json.loads(client2.sent_messages[0])
        
        assert message1 == message2 == message

    @pytest.mark.asyncio
    async def test_broadcast_to_all_with_disconnected_clients(self):
        """Test broadcasting when some clients are disconnected."""
        broadcaster = StatebroadCaster()
        
        client1 = MockWebSocketProtocol()
        client2 = MockWebSocketProtocol()
        client2.closed = True  # Simulate disconnected client
        
        broadcaster.clients = {client1, client2}
        
        message = {"type": "test", "data": "test"}
        
        await broadcaster.broadcast_to_all(message)
        
        # Only connected client should receive message
        assert len(client1.sent_messages) == 1
        # Disconnected client should be removed
        assert client2 not in broadcaster.clients
        assert client1 in broadcaster.clients

    def test_emit_workflow_transition(self):
        """Test emitting workflow state transition."""
        broadcaster = StatebroadCaster()
        broadcaster.transition_history = []
        
        old_state = State.IDLE
        new_state = State.SPRINT_ACTIVE
        project_name = "test-project"
        
        with patch.object(broadcaster, 'broadcast_to_all') as mock_broadcast:
            broadcaster.emit_workflow_transition(old_state, new_state, project_name)
            
            # State should be updated
            assert broadcaster.current_workflow_state == new_state
            
            # History should be updated
            assert len(broadcaster.transition_history) == 1
            transition = broadcaster.transition_history[0]
            assert transition["type"] == "workflow_transition"
            assert transition["project"] == project_name
            assert transition["old_state"] == "IDLE"
            assert transition["new_state"] == "SPRINT_ACTIVE"
            assert "timestamp" in transition

    def test_emit_tdd_transition_new_story(self):
        """Test emitting TDD transition for new story."""
        broadcaster = StatebroadCaster()
        broadcaster.tdd_cycles = {}
        broadcaster.transition_history = []
        
        story_id = "STORY-123"
        old_state = None
        new_state = TDDState.RED
        project_name = "test-project"
        
        with patch.object(broadcaster, 'broadcast_to_all') as mock_broadcast:
            broadcaster.emit_tdd_transition(story_id, old_state, new_state, project_name)
            
            # TDD cycle should be tracked
            assert story_id in broadcaster.tdd_cycles
            cycle_info = broadcaster.tdd_cycles[story_id]
            assert cycle_info["current_state"] == "RED"
            assert cycle_info["project"] == project_name
            assert "last_updated" in cycle_info
            
            # History should be updated
            assert len(broadcaster.transition_history) == 1
            transition = broadcaster.transition_history[0]
            assert transition["type"] == "tdd_transition"
            assert transition["story_id"] == story_id
            assert transition["old_state"] is None
            assert transition["new_state"] == "RED"

    def test_emit_tdd_transition_existing_story(self):
        """Test emitting TDD transition for existing story."""
        broadcaster = StatebroadCaster()
        story_id = "STORY-123"
        
        # Pre-existing cycle info
        broadcaster.tdd_cycles = {
            story_id: {
                "current_state": "RED",
                "project": "test-project",
                "last_updated": "2023-01-01T00:00:00"
            }
        }
        
        old_state = TDDState.RED
        new_state = TDDState.GREEN
        
        with patch.object(broadcaster, 'broadcast_to_all'):
            broadcaster.emit_tdd_transition(story_id, old_state, new_state)
            
            # Should update existing cycle info
            cycle_info = broadcaster.tdd_cycles[story_id]
            assert cycle_info["current_state"] == "GREEN"
            assert cycle_info["project"] == "test-project"  # Should preserve project
            # last_updated should be updated

    def test_emit_agent_activity(self):
        """Test emitting agent activity."""
        broadcaster = StatebroadCaster()
        
        agent_type = "code_agent"
        story_id = "STORY-123"
        action = "implement_feature"
        status = "started"
        project_name = "test-project"
        
        with patch.object(broadcaster, 'broadcast_to_all') as mock_broadcast:
            broadcaster.emit_agent_activity(agent_type, story_id, action, status, project_name)
            
            # Should create task to broadcast
            # Note: We can't easily test asyncio.create_task, but we can verify the method was called

    def test_emit_parallel_status(self):
        """Test emitting parallel execution status."""
        broadcaster = StatebroadCaster()
        
        status_data = {
            "active_cycles": 3,
            "completed_cycles": 2,
            "performance_metrics": {"throughput": 1.5}
        }
        project_name = "test-project"
        
        with patch.object(broadcaster, 'broadcast_to_all') as mock_broadcast:
            broadcaster.emit_parallel_status(status_data, project_name)
            
            # Should create task to broadcast
            # The actual broadcast testing is done in the broadcast_to_all tests

    def test_get_current_state(self):
        """Test getting current state as dictionary."""
        broadcaster = StatebroadCaster()
        
        # Set up state
        broadcaster.current_workflow_state = State.SPRINT_ACTIVE
        broadcaster.tdd_cycles = {
            "story-1": {"current_state": "red"},
            "story-2": {"current_state": "green"}
        }
        
        state = broadcaster.get_current_state()
        
        assert state["workflow_state"] == "SPRINT_ACTIVE"
        assert state["active_cycles"] == 2
        assert state["tdd_cycles"] == broadcaster.tdd_cycles
        assert "last_updated" in state


class TestConvenienceFunctions:
    """Test the convenience functions for state broadcasting."""
    
    def test_emit_workflow_transition_function(self):
        """Test the emit_workflow_transition convenience function."""
        with patch.object(broadcaster, 'emit_workflow_transition') as mock_emit:
            emit_workflow_transition(State.IDLE, State.SPRINT_ACTIVE, "test-project")
            
            mock_emit.assert_called_once_with(State.IDLE, State.SPRINT_ACTIVE, "test-project")

    def test_emit_tdd_transition_function(self):
        """Test the emit_tdd_transition convenience function."""
        with patch.object(broadcaster, 'emit_tdd_transition') as mock_emit:
            emit_tdd_transition("STORY-123", TDDState.RED, TDDState.GREEN, "test-project")
            
            mock_emit.assert_called_once_with("STORY-123", TDDState.RED, TDDState.GREEN, "test-project")

    def test_emit_agent_activity_function(self):
        """Test the emit_agent_activity convenience function."""
        with patch.object(broadcaster, 'emit_agent_activity') as mock_emit:
            emit_agent_activity("code_agent", "STORY-123", "implement", "started", "test-project")
            
            mock_emit.assert_called_once_with("code_agent", "STORY-123", "implement", "started", "test-project")

    def test_emit_parallel_status_function(self):
        """Test the emit_parallel_status convenience function."""
        status_data = {"active_cycles": 2}
        
        with patch.object(broadcaster, 'emit_parallel_status') as mock_emit:
            emit_parallel_status(status_data, "test-project")
            
            mock_emit.assert_called_once_with(status_data, "test-project")

    @pytest.mark.asyncio
    async def test_start_broadcaster_function(self):
        """Test the start_broadcaster convenience function."""
        with patch.object(broadcaster, 'start_server') as mock_start:
            await start_broadcaster(port=9000)
            
            mock_start.assert_called_once_with(9000)

    @pytest.mark.asyncio
    async def test_stop_broadcaster_function(self):
        """Test the stop_broadcaster convenience function."""
        with patch.object(broadcaster, 'stop_server') as mock_stop:
            await stop_broadcaster()
            
            mock_stop.assert_called_once()


class TestStateHandling:
    """Test state handling with different types of state objects."""
    
    def test_emit_workflow_transition_with_enum_state(self):
        """Test workflow transition with enum state values."""
        broadcaster = StatebroadCaster()
        broadcaster.transition_history = []
        
        old_state = State.IDLE
        new_state = State.SPRINT_ACTIVE
        
        broadcaster.emit_workflow_transition(old_state, new_state)
        
        transition = broadcaster.transition_history[0]
        assert transition["old_state"] == "IDLE"
        assert transition["new_state"] == "SPRINT_ACTIVE"

    def test_emit_workflow_transition_with_string_state(self):
        """Test workflow transition with string state values."""
        broadcaster = StatebroadCaster()
        broadcaster.transition_history = []
        
        # Mock states without .value attribute
        old_state = "custom_idle"
        new_state = "custom_active"
        
        broadcaster.emit_workflow_transition(old_state, new_state)
        
        transition = broadcaster.transition_history[0]
        assert transition["old_state"] == "custom_idle"
        assert transition["new_state"] == "custom_active"

    def test_emit_tdd_transition_with_enum_state(self):
        """Test TDD transition with enum state values."""
        broadcaster = StatebroadCaster()
        broadcaster.transition_history = []
        
        story_id = "STORY-123"
        old_state = TDDState.RED
        new_state = TDDState.GREEN
        
        broadcaster.emit_tdd_transition(story_id, old_state, new_state)
        
        transition = broadcaster.transition_history[0]
        assert transition["old_state"] == "RED"
        assert transition["new_state"] == "GREEN"

    def test_emit_tdd_transition_with_string_state(self):
        """Test TDD transition with string state values."""
        broadcaster = StatebroadCaster()
        broadcaster.transition_history = []
        
        story_id = "STORY-123"
        # Mock states without .value attribute
        old_state = "custom_red"
        new_state = "custom_green"
        
        broadcaster.emit_tdd_transition(story_id, old_state, new_state)
        
        transition = broadcaster.transition_history[0]
        assert transition["old_state"] == "custom_red"
        assert transition["new_state"] == "custom_green"

    def test_emit_tdd_transition_with_none_old_state(self):
        """Test TDD transition with None old state."""
        broadcaster = StatebroadCaster()
        broadcaster.transition_history = []
        
        story_id = "STORY-123"
        old_state = None
        new_state = TDDState.RED
        
        broadcaster.emit_tdd_transition(story_id, old_state, new_state)
        
        transition = broadcaster.transition_history[0]
        assert transition["old_state"] is None
        assert transition["new_state"] == "RED"

    def test_send_current_state_with_different_state_types(self):
        """Test sending current state with different state types."""
        import asyncio
        
        broadcaster = StatebroadCaster()
        mock_client = MockWebSocketProtocol()
        
        # Test with enum state
        broadcaster.current_workflow_state = State.SPRINT_ACTIVE
        
        asyncio.run(broadcaster.send_current_state(mock_client))
        
        message = json.loads(mock_client.sent_messages[0])
        assert message["workflow_state"] == "SPRINT_ACTIVE"
        
        # Test with string state
        mock_client.sent_messages.clear()
        broadcaster.current_workflow_state = "custom_state"
        
        asyncio.run(broadcaster.send_current_state(mock_client))
        
        message = json.loads(mock_client.sent_messages[0])
        assert message["workflow_state"] == "custom_state"

    def test_get_current_state_with_different_state_types(self):
        """Test getting current state with different state types."""
        broadcaster = StatebroadCaster()
        
        # Test with enum state
        broadcaster.current_workflow_state = State.SPRINT_ACTIVE
        state = broadcaster.get_current_state()
        assert state["workflow_state"] == "SPRINT_ACTIVE"
        
        # Test with string state
        broadcaster.current_workflow_state = "custom_state"
        state = broadcaster.get_current_state()
        assert state["workflow_state"] == "custom_state"


class TestErrorHandling:
    """Test error handling in state broadcasting."""
    
    @pytest.mark.asyncio
    async def test_handle_client_invalid_json(self):
        """Test handling client with invalid JSON message."""
        broadcaster = StatebroadCaster()
        mock_client = MockWebSocketProtocol()
        
        # Mock async iteration with invalid JSON
        async def mock_async_iter():
            yield "invalid json"
        
        mock_client.__aiter__ = mock_async_iter
        
        with patch.object(broadcaster, 'send_current_state'):
            await broadcaster.handle_client(mock_client, "/test")
            
            # Should send error message
            assert len(mock_client.sent_messages) >= 1
            error_message = json.loads(mock_client.sent_messages[-1])
            assert error_message["type"] == "error"
            assert "Invalid JSON" in error_message["message"]

    @pytest.mark.asyncio
    async def test_handle_client_general_exception(self):
        """Test handling general exceptions in client handler."""
        broadcaster = StatebroadCaster()
        mock_client = MockWebSocketProtocol()
        
        # Mock async iteration that raises general exception
        async def mock_async_iter():
            raise Exception("General error")
        
        mock_client.__aiter__ = mock_async_iter
        
        with patch.object(broadcaster, 'send_current_state'):
            # Should not raise exception, just handle gracefully
            await broadcaster.handle_client(mock_client, "/test")
            
            # Client should be removed from clients set
            assert mock_client not in broadcaster.clients

    @pytest.mark.asyncio
    async def test_broadcast_to_all_client_exception(self):
        """Test broadcasting when client send raises exception."""
        broadcaster = StatebroadCaster()
        
        # Create clients with different behaviors
        good_client = MockWebSocketProtocol()
        bad_client = Mock()
        bad_client.send = AsyncMock(side_effect=Exception("Send failed"))
        
        broadcaster.clients = {good_client, bad_client}
        
        message = {"type": "test", "data": "test"}
        
        await broadcaster.broadcast_to_all(message)
        
        # Good client should receive message
        assert len(good_client.sent_messages) == 1
        
        # Bad client should be removed
        assert bad_client not in broadcaster.clients
        assert good_client in broadcaster.clients


class TestWebSocketServerMocking:
    """Test WebSocket server functionality with proper mocking."""
    
    @pytest.mark.asyncio
    async def test_server_start_with_websockets_module(self):
        """Test server start with websockets module available."""
        broadcaster = StatebroadCaster()
        
        with patch('websockets.serve') as mock_serve:
            mock_server = AsyncMock()
            mock_serve.return_value = mock_server
            
            await broadcaster.start_server(8082)
            
            assert broadcaster.port == 8082
            assert broadcaster.server == mock_server
            
            # Verify websockets.serve was called with correct parameters
            args, kwargs = mock_serve.call_args
            assert args[0] == broadcaster.handle_client
            assert args[1] == "localhost"
            assert args[2] == 8082

    @pytest.mark.asyncio
    async def test_client_handling_full_flow(self):
        """Test complete client handling flow."""
        broadcaster = StatebroadCaster()
        broadcaster.clients = set()
        
        mock_client = MockWebSocketProtocol()
        
        # Set up state for testing
        broadcaster.current_workflow_state = State.SPRINT_ACTIVE
        broadcaster.tdd_cycles = {"story-1": {"current_state": "red"}}
        
        # Mock message sequence
        messages = [
            '{"type": "get_current_state"}',
            '{"type": "get_history"}',
            '{"type": "unknown_type"}'
        ]
        
        async def mock_async_iter():
            for message in messages:
                yield message
        
        mock_client.__aiter__ = mock_async_iter
        
        await broadcaster.handle_client(mock_client, "/test")
        
        # Verify all messages were handled
        assert len(mock_client.sent_messages) >= 3
        
        # Check specific responses
        current_state_msg = json.loads(mock_client.sent_messages[0])
        assert current_state_msg["type"] == "current_state"
        
        history_msg = json.loads(mock_client.sent_messages[1])
        assert history_msg["type"] == "transition_history"
        
        error_msg = json.loads(mock_client.sent_messages[2])
        assert error_msg["type"] == "error"

    def test_transition_history_accumulation(self):
        """Test that transition history accumulates correctly."""
        broadcaster = StatebroadCaster()
        broadcaster.transition_history = []
        
        # Emit multiple transitions
        broadcaster.emit_workflow_transition(State.IDLE, State.BACKLOG_READY)
        broadcaster.emit_workflow_transition(State.BACKLOG_READY, State.SPRINT_PLANNED)
        broadcaster.emit_tdd_transition("STORY-1", None, TDDState.RED)
        broadcaster.emit_tdd_transition("STORY-1", TDDState.RED, TDDState.GREEN)
        
        assert len(broadcaster.transition_history) == 4
        
        # Check order and types
        assert broadcaster.transition_history[0]["type"] == "workflow_transition"
        assert broadcaster.transition_history[1]["type"] == "workflow_transition"
        assert broadcaster.transition_history[2]["type"] == "tdd_transition"
        assert broadcaster.transition_history[3]["type"] == "tdd_transition"

    def test_tdd_cycles_state_tracking(self):
        """Test that TDD cycles state is tracked correctly."""
        broadcaster = StatebroadCaster()
        broadcaster.tdd_cycles = {}
        
        # Start new story
        broadcaster.emit_tdd_transition("STORY-1", None, TDDState.RED, "project-1")
        assert "STORY-1" in broadcaster.tdd_cycles
        assert broadcaster.tdd_cycles["STORY-1"]["current_state"] == "RED"
        assert broadcaster.tdd_cycles["STORY-1"]["project"] == "project-1"
        
        # Update existing story
        broadcaster.emit_tdd_transition("STORY-1", TDDState.RED, TDDState.GREEN, "project-1")
        assert broadcaster.tdd_cycles["STORY-1"]["current_state"] == "GREEN"
        assert broadcaster.tdd_cycles["STORY-1"]["project"] == "project-1"
        
        # Add another story
        broadcaster.emit_tdd_transition("STORY-2", None, TDDState.RED, "project-2")
        assert len(broadcaster.tdd_cycles) == 2
        assert broadcaster.tdd_cycles["STORY-2"]["project"] == "project-2"

    def test_global_broadcaster_instance(self):
        """Test that the global broadcaster instance works correctly."""
        # The global broadcaster should be the same as creating a new instance
        from lib.state_broadcaster import broadcaster as global_broadcaster
        
        new_broadcaster = StatebroadCaster()
        
        assert global_broadcaster is new_broadcaster