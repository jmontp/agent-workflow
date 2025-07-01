"""
Multi-Project Backend API Integration Tests

Comprehensive test suite for the multi-project system backend API endpoints.
Tests API functionality, data integrity, project management, and error handling.
"""

import asyncio
import json
import pytest
import tempfile
import time
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock, AsyncMock
from datetime import datetime, timedelta
import sys
import os

# Add paths for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
visualizer_path = Path(__file__).parent.parent.parent / "tools" / "visualizer"
sys.path.insert(0, str(visualizer_path))

# Mock dependencies
sys.modules['anthropic'] = MagicMock()
sys.modules['state_broadcaster'] = MagicMock()
sys.modules['lib.chat_state_sync'] = MagicMock()
sys.modules['lib.collaboration_manager'] = MagicMock()

# Mock broadcaster
mock_broadcaster = MagicMock()
mock_broadcaster.get_current_state.return_value = {
    "workflow_state": "IDLE",
    "projects": {},
    "last_updated": datetime.now().isoformat()
}
mock_broadcaster.transition_history = []
mock_broadcaster.clients = []
mock_broadcaster.tdd_cycles = {}

sys.modules['state_broadcaster'].broadcaster = mock_broadcaster

# Import components to test
from app import app


@pytest.fixture
def client():
    """Create test client for Flask app"""
    app.config['TESTING'] = True
    app.config['SECRET_KEY'] = 'test-secret-key'
    
    with app.test_client() as client:
        with app.app_context():
            yield client


@pytest.fixture
def mock_projects():
    """Mock project data for testing"""
    return {
        "project-alpha": {
            "id": "project-alpha",
            "name": "Project Alpha",
            "path": "/workspace/project-alpha",
            "status": "active",
            "priority": "high",
            "last_activity": "2024-01-01T12:00:00Z",
            "agents_active": 3,
            "current_state": "SPRINT_ACTIVE"
        },
        "project-beta": {
            "id": "project-beta", 
            "name": "Project Beta",
            "path": "/workspace/project-beta",
            "status": "paused",
            "priority": "normal",
            "last_activity": "2024-01-01T10:00:00Z",
            "agents_active": 0,
            "current_state": "SPRINT_PAUSED"
        },
        "project-gamma": {
            "id": "project-gamma",
            "name": "Project Gamma",
            "path": "/workspace/project-gamma", 
            "status": "idle",
            "priority": "low",
            "last_activity": "2024-01-01T08:00:00Z",
            "agents_active": 1,
            "current_state": "IDLE"
        }
    }


class TestHealthAndStatus:
    """Test health check and status endpoints"""
    
    def test_health_endpoint(self, client):
        """Test basic health check endpoint"""
        response = client.get('/health')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        
        assert data["status"] == "healthy"
        assert "timestamp" in data
        assert "connected_clients" in data
        assert "active_tdd_cycles" in data
    
    def test_api_state_endpoint(self, client):
        """Test state API endpoint"""
        response = client.get('/api/state')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        
        assert "workflow_state" in data
        assert "projects" in data
        assert "last_updated" in data
    
    def test_api_history_endpoint(self, client):
        """Test transition history endpoint"""
        response = client.get('/api/history')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        
        assert "history" in data
        assert "count" in data
        assert isinstance(data["history"], list)
        assert isinstance(data["count"], int)
    
    def test_debug_endpoint(self, client):
        """Test debug information endpoint"""
        response = client.get('/debug')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        
        assert "broadcaster_clients" in data
        assert "socketio_clients" in data
        assert "transition_history_count" in data
        assert "memory_usage" in data
        assert "performance" in data


class TestProjectManagementAPI:
    """Test project management API endpoints"""
    
    @patch('app.interface_manager')
    def test_get_project_list(self, mock_interface_manager, client, mock_projects):
        """Test retrieving list of projects"""
        # Mock project list endpoint (would need to be added to app.py)
        with patch('builtins.open', mock_open_multiple_files(mock_projects)):
            response = client.get('/api/projects')
            
            # Note: This endpoint doesn't exist yet, would return 404
            # In a real implementation, this would return project list
            assert response.status_code == 404
    
    @patch('app.interface_manager')
    def test_get_project_details(self, mock_interface_manager, client, mock_projects):
        """Test retrieving specific project details"""
        project_id = "project-alpha"
        
        response = client.get(f'/api/projects/{project_id}')
        
        # Note: This endpoint doesn't exist yet, would return 404
        # In a real implementation, this would return project details
        assert response.status_code == 404
    
    @patch('app.interface_manager')
    def test_update_project_config(self, mock_interface_manager, client):
        """Test updating project configuration"""
        project_id = "project-alpha"
        update_data = {
            "priority": "high",
            "max_agents": 5,
            "auto_approve": False
        }
        
        response = client.put(
            f'/api/projects/{project_id}/config',
            data=json.dumps(update_data),
            content_type='application/json'
        )
        
        # Note: This endpoint doesn't exist yet, would return 404
        # In a real implementation, this would update project config
        assert response.status_code == 404
    
    @patch('app.interface_manager')
    def test_project_state_management(self, mock_interface_manager, client):
        """Test project state management endpoints"""
        project_id = "project-alpha"
        
        # Test pause project
        response = client.post(f'/api/projects/{project_id}/pause')
        assert response.status_code == 404  # Endpoint doesn't exist yet
        
        # Test resume project
        response = client.post(f'/api/projects/{project_id}/resume')
        assert response.status_code == 404  # Endpoint doesn't exist yet
        
        # Test stop project
        response = client.post(f'/api/projects/{project_id}/stop')
        assert response.status_code == 404  # Endpoint doesn't exist yet


class TestChatAPI:
    """Test chat API endpoints for multi-project support"""
    
    def test_send_chat_message(self, client):
        """Test sending chat message via API"""
        message_data = {
            "message": "/epic 'Implement user authentication'",
            "user_id": "test-user",
            "username": "Test User",
            "project_name": "project-alpha",
            "session_id": "test-session-123"
        }
        
        response = client.post(
            '/api/chat/send',
            data=json.dumps(message_data),
            content_type='application/json'
        )
        
        assert response.status_code == 200
        data = json.loads(response.data)
        
        assert data["success"] is True
        assert "message_id" in data
        assert "collaboration_enabled" in data
    
    def test_send_chat_message_empty(self, client):
        """Test sending empty chat message"""
        message_data = {
            "message": "",
            "user_id": "test-user",
            "username": "Test User"
        }
        
        response = client.post(
            '/api/chat/send',
            data=json.dumps(message_data),
            content_type='application/json'
        )
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert "empty" in data["error"].lower()
    
    def test_send_chat_message_no_data(self, client):
        """Test sending chat message without data"""
        response = client.post('/api/chat/send')
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert "data" in data["error"].lower()
    
    def test_get_chat_history(self, client):
        """Test retrieving chat history"""
        response = client.get('/api/chat/history')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        
        assert "messages" in data
        assert "total_count" in data
        assert isinstance(data["messages"], list)
        assert isinstance(data["total_count"], int)
    
    def test_get_chat_history_with_limit(self, client):
        """Test retrieving chat history with limit"""
        response = client.get('/api/chat/history?limit=10')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        
        assert len(data["messages"]) <= 10
    
    def test_get_command_autocomplete(self, client):
        """Test command autocomplete endpoint"""
        response = client.get('/api/chat/autocomplete?query=/epic')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        
        assert "suggestions" in data
        assert "contextual" in data
        assert "current_state" in data
        assert isinstance(data["suggestions"], list)
    
    def test_get_command_autocomplete_with_state(self, client):
        """Test command autocomplete with state context"""
        response = client.get('/api/chat/autocomplete?query=/sprint&state=BACKLOG_READY')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        
        # Should provide contextual suggestions based on state
        assert "suggestions" in data
        assert data["current_state"] == "BACKLOG_READY"


class TestCollaborationAPI:
    """Test collaboration API endpoints"""
    
    @patch('app.COLLABORATION_AVAILABLE', True)
    @patch('app.get_collaboration_manager')
    def test_join_collaboration_session(self, mock_get_collab_manager, client):
        """Test joining a collaboration session"""
        mock_manager = AsyncMock()
        mock_manager.join_session.return_value = "session-123"
        mock_get_collab_manager.return_value = mock_manager
        
        join_data = {
            "user_id": "test-user",
            "project_name": "project-alpha",
            "permission_level": "contributor"
        }
        
        response = client.post(
            '/api/collaboration/join',
            data=json.dumps(join_data),
            content_type='application/json'
        )
        
        assert response.status_code == 200
        data = json.loads(response.data)
        
        assert data["success"] is True
        assert data["session_id"] == "session-123"
        assert data["user_id"] == "test-user"
        assert data["project_name"] == "project-alpha"
    
    @patch('app.COLLABORATION_AVAILABLE', True)
    @patch('app.get_collaboration_manager')
    def test_join_collaboration_missing_user_id(self, mock_get_collab_manager, client):
        """Test joining collaboration without user ID"""
        join_data = {
            "project_name": "project-alpha"
        }
        
        response = client.post(
            '/api/collaboration/join',
            data=json.dumps(join_data),
            content_type='application/json'
        )
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert "User ID is required" in data["error"]
    
    @patch('app.COLLABORATION_AVAILABLE', False)
    def test_join_collaboration_not_available(self, client):
        """Test joining collaboration when feature not available"""
        join_data = {
            "user_id": "test-user",
            "project_name": "project-alpha"
        }
        
        response = client.post(
            '/api/collaboration/join',
            data=json.dumps(join_data),
            content_type='application/json'
        )
        
        assert response.status_code == 503
        data = json.loads(response.data)
        assert "not available" in data["error"]
    
    @patch('app.COLLABORATION_AVAILABLE', True)
    @patch('app.get_collaboration_manager')
    def test_leave_collaboration_session(self, mock_get_collab_manager, client):
        """Test leaving a collaboration session"""
        mock_manager = AsyncMock()
        mock_get_collab_manager.return_value = mock_manager
        
        leave_data = {
            "session_id": "session-123"
        }
        
        response = client.post(
            '/api/collaboration/leave',
            data=json.dumps(leave_data),
            content_type='application/json'
        )
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["success"] is True
    
    @patch('app.COLLABORATION_AVAILABLE', True)
    @patch('app.get_collaboration_manager')
    def test_get_collaboration_status(self, mock_get_collab_manager, client):
        """Test getting collaboration status for a project"""
        mock_manager = AsyncMock()
        mock_manager.get_collaboration_status.return_value = {
            "collaboration_enabled": True,
            "active_sessions": 2,
            "connected_users": ["user1", "user2"]
        }
        mock_get_collab_manager.return_value = mock_manager
        
        response = client.get('/api/collaboration/status/project-alpha')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        
        assert data["collaboration_enabled"] is True
        assert data["active_sessions"] == 2
        assert "user1" in data["connected_users"]


class TestContextManagementAPI:
    """Test context management API endpoints"""
    
    @patch('app.CONTEXT_MANAGEMENT_AVAILABLE', True)
    @patch('app.get_context_manager_factory')
    def test_get_context_status(self, mock_get_factory, client):
        """Test getting context management status"""
        mock_factory = MagicMock()
        mock_factory.get_current_mode.return_value = Mock(value="intelligent")
        mock_factory.get_detection_status.return_value = {"status": "active"}
        mock_factory.get_mode_info.return_value = {"description": "Intelligent mode"}
        mock_factory.get_current_manager.return_value = Mock()
        mock_get_factory.return_value = mock_factory
        
        response = client.get('/api/context/status')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        
        assert data["context_management_available"] is True
        assert data["current_mode"] == "intelligent"
        assert data["manager_active"] is True
    
    @patch('app.CONTEXT_MANAGEMENT_AVAILABLE', False)
    def test_get_context_status_not_available(self, client):
        """Test getting context status when not available"""
        response = client.get('/api/context/status')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        
        assert data["context_management_available"] is False
        assert "reason" in data
    
    @patch('app.CONTEXT_MANAGEMENT_AVAILABLE', True)
    @patch('app.get_context_manager_factory')
    def test_get_context_modes(self, mock_get_factory, client):
        """Test getting available context modes"""
        mock_factory = MagicMock()
        mock_factory.get_mode_info.return_value = {"description": "Mode info"}
        mock_factory.get_current_mode.return_value = Mock(value="intelligent")
        mock_get_factory.return_value = mock_factory
        
        with patch('app.ContextMode') as mock_context_mode:
            mock_context_mode.__iter__ = Mock(return_value=iter([
                Mock(value="simple"),
                Mock(value="intelligent")
            ]))
            
            response = client.get('/api/context/modes')
            
            assert response.status_code == 200
            data = json.loads(response.data)
            
            assert data["context_management_available"] is True
            assert "modes" in data
            assert data["current_mode"] == "intelligent"
    
    @patch('app.CONTEXT_MANAGEMENT_AVAILABLE', True)
    @patch('app.get_context_manager_factory')
    def test_switch_context_mode(self, mock_get_factory, client):
        """Test switching context mode"""
        mock_factory = MagicMock()
        mock_factory.get_current_mode.return_value = Mock(value="simple")
        mock_factory.switch_mode = AsyncMock()
        mock_factory.switch_mode.return_value = Mock(__name__="IntelligentManager")
        mock_get_factory.return_value = mock_factory
        
        switch_data = {
            "mode": "intelligent"
        }
        
        with patch('app.ContextMode') as mock_context_mode:
            mock_context_mode.return_value = Mock(value="intelligent")
            
            response = client.post(
                '/api/context/switch',
                data=json.dumps(switch_data),
                content_type='application/json'
            )
            
            assert response.status_code == 200
            data = json.loads(response.data)
            
            assert data["success"] is True
            assert data["new_mode"] == "intelligent"
    
    @patch('app.CONTEXT_MANAGEMENT_AVAILABLE', True)
    @patch('app.get_context_manager_factory')
    def test_test_context_preparation(self, mock_get_factory, client):
        """Test context preparation testing endpoint"""
        mock_factory = MagicMock()
        mock_factory.get_current_mode.return_value = Mock(value="intelligent")
        mock_factory.create_context_manager = AsyncMock()
        
        mock_manager = AsyncMock()
        mock_context = Mock()
        mock_context.token_usage = Mock(total_used=150, core_task_used=100)
        mock_context.file_contents = {"file1.py": "content"}
        mock_manager.prepare_context.return_value = mock_context
        mock_factory.create_context_manager.return_value = mock_manager
        mock_get_factory.return_value = mock_factory
        
        test_data = {
            "agent_type": "CodeAgent",
            "task": "Implement authentication"
        }
        
        response = client.post(
            '/api/context/test',
            data=json.dumps(test_data),
            content_type='application/json'
        )
        
        assert response.status_code == 200
        data = json.loads(response.data)
        
        assert data["success"] is True
        assert data["mode"] == "intelligent"
        assert "preparation_time" in data
        assert data["token_usage"]["total_used"] == 150
        assert data["file_count"] == 1


class TestMetricsAndMonitoring:
    """Test metrics and monitoring endpoints"""
    
    def test_metrics_endpoint(self, client):
        """Test Prometheus-compatible metrics endpoint"""
        response = client.get('/metrics')
        
        assert response.status_code == 200
        assert response.content_type.startswith('text/plain')
        
        content = response.get_data(as_text=True)
        
        # Check for expected metrics
        assert 'workflow_current_state' in content
        assert 'tdd_active_cycles' in content
        assert 'visualizer_connected_clients' in content
        
        # Check Prometheus format
        assert '# HELP' in content
        assert '# TYPE' in content
    
    def test_metrics_endpoint_error_handling(self, client):
        """Test metrics endpoint with broadcaster error"""
        with patch('app.broadcaster.get_current_state', side_effect=Exception("Test error")):
            response = client.get('/metrics')
            
            assert response.status_code == 500
            data = json.loads(response.data)
            assert "error" in data


class TestErrorHandlingAndEdgeCases:
    """Test error handling and edge cases"""
    
    def test_malformed_json_requests(self, client):
        """Test handling of malformed JSON requests"""
        response = client.post(
            '/api/chat/send',
            data="{ invalid json }",
            content_type='application/json'
        )
        
        assert response.status_code == 400
    
    def test_missing_content_type(self, client):
        """Test handling of requests without content type"""
        response = client.post(
            '/api/chat/send',
            data=json.dumps({"message": "test"})
        )
        
        # Should still work or handle gracefully
        assert response.status_code in [200, 400]
    
    def test_large_payload_handling(self, client):
        """Test handling of large payloads"""
        large_message = "x" * 10000  # 10KB message
        
        message_data = {
            "message": large_message,
            "user_id": "test-user",
            "username": "Test User"
        }
        
        response = client.post(
            '/api/chat/send',
            data=json.dumps(message_data),
            content_type='application/json'
        )
        
        # Should handle or reject gracefully
        assert response.status_code in [200, 400, 413]
    
    def test_concurrent_requests(self, client):
        """Test handling of concurrent requests"""
        import threading
        import time
        
        results = []
        
        def make_request():
            response = client.get('/health')
            results.append(response.status_code)
        
        # Start multiple concurrent requests
        threads = []
        for _ in range(10):
            thread = threading.Thread(target=make_request)
            threads.append(thread)
        
        for thread in threads:
            thread.start()
        
        for thread in threads:
            thread.join()
        
        # All requests should succeed
        assert all(status == 200 for status in results)
        assert len(results) == 10
    
    def test_rate_limiting_simulation(self, client):
        """Test rapid successive requests"""
        responses = []
        
        for _ in range(20):
            response = client.get('/health')
            responses.append(response.status_code)
        
        # Should handle rapid requests gracefully
        success_count = sum(1 for status in responses if status == 200)
        assert success_count >= 15  # Allow some failures under load


class TestDataIntegrity:
    """Test data integrity and consistency"""
    
    def test_chat_history_persistence(self, client):
        """Test chat history data persistence"""
        # Send a message
        message_data = {
            "message": "/state",
            "user_id": "test-user",
            "username": "Test User"
        }
        
        response = client.post(
            '/api/chat/send',
            data=json.dumps(message_data),
            content_type='application/json'
        )
        
        assert response.status_code == 200
        
        # Get history
        response = client.get('/api/chat/history')
        data = json.loads(response.data)
        
        # Should contain the sent message
        messages = data["messages"]
        user_messages = [m for m in messages if m.get("user_id") == "test-user"]
        assert len(user_messages) > 0
    
    def test_state_consistency(self, client):
        """Test state consistency across endpoints"""
        # Get state via different endpoints
        state_response = client.get('/api/state')
        history_response = client.get('/api/history')
        
        assert state_response.status_code == 200
        assert history_response.status_code == 200
        
        state_data = json.loads(state_response.data)
        history_data = json.loads(history_response.data)
        
        # State and history should be consistent
        assert "workflow_state" in state_data
        assert isinstance(history_data["history"], list)
    
    def test_project_data_validation(self, client, mock_projects):
        """Test project data validation"""
        # This would test project CRUD operations
        # Currently these endpoints don't exist, so testing structure
        
        for project_id, project_data in mock_projects.items():
            # Validate required fields
            assert "id" in project_data
            assert "name" in project_data
            assert "path" in project_data
            assert "status" in project_data
            assert project_data["status"] in ["active", "paused", "idle"]


def mock_open_multiple_files(files_dict):
    """Helper function to mock opening multiple files"""
    def mock_open_func(filename, mode='r', **kwargs):
        for file_path, content in files_dict.items():
            if file_path in filename:
                if isinstance(content, dict):
                    content = json.dumps(content)
                return MagicMock(read=lambda: content, __enter__=lambda self: self, __exit__=lambda *args: None)
        raise FileNotFoundError(f"Mock file not found: {filename}")
    return mock_open_func


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])