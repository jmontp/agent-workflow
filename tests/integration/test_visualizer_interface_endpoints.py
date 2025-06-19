"""
Integration tests for the visualizer interface management endpoints

Tests the Flask app endpoints for interface switching and configuration
"""

import asyncio
import json
import pytest
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import sys
import os

# Add the visualizer directory to the path
visualizer_path = Path(__file__).parent.parent.parent / "tools" / "visualizer"
sys.path.insert(0, str(visualizer_path))

# Mock dependencies that might not be available in test environment
sys.modules['anthropic'] = MagicMock()
sys.modules['state_broadcaster'] = MagicMock()

# Mock the broadcaster
mock_broadcaster = MagicMock()
mock_broadcaster.get_current_state.return_value = {"test": "state"}
mock_broadcaster.transition_history = []
mock_broadcaster.clients = []
mock_broadcaster.tdd_cycles = {}

sys.modules['state_broadcaster'].broadcaster = mock_broadcaster

# Import Flask app
from app import app, socketio


@pytest.fixture
def client():
    """Create test client"""
    app.config['TESTING'] = True
    app.config['SECRET_KEY'] = 'test-secret-key'
    
    with app.test_client() as client:
        with app.app_context():
            yield client


@pytest.fixture
def mock_interface_manager():
    """Mock interface manager for testing"""
    mock_manager = MagicMock()
    
    # Mock interface status
    mock_manager.get_interface_status.return_value = {
        "active_interface": "mock",
        "interfaces": {
            "claude_code": {
                "enabled": True,
                "status": "disconnected",
                "request_count": 0,
                "error_count": 0
            },
            "anthropic_api": {
                "enabled": False,
                "status": "not_initialized",
                "request_count": 0,
                "error_count": 0
            },
            "mock": {
                "enabled": True,
                "status": "connected",
                "request_count": 5,
                "error_count": 0
            }
        }
    }
    
    # Mock interface types
    mock_manager.interfaceTypes = [
        {"type": "claude_code", "name": "Claude Code"},
        {"type": "anthropic_api", "name": "Anthropic API"},
        {"type": "mock", "name": "Mock Interface"}
    ]
    
    # Mock configurations
    mock_manager.configs = {
        "mock": MagicMock(
            enabled=True,
            timeout=300,
            mask_sensitive_data=lambda: {"enabled": True, "timeout": 300}
        )
    }
    
    return mock_manager


class TestInterfaceStatusEndpoints:
    """Test interface status and information endpoints"""
    
    def test_get_interfaces_status(self, client, mock_interface_manager):
        """Test getting interface status"""
        with patch('app.interface_manager', mock_interface_manager):
            response = client.get('/api/interfaces')
            
            assert response.status_code == 200
            data = json.loads(response.data)
            
            assert "active_interface" in data
            assert "interfaces" in data
            assert data["active_interface"] == "mock"
            assert "claude_code" in data["interfaces"]
            assert "anthropic_api" in data["interfaces"]
            assert "mock" in data["interfaces"]
    
    def test_get_interfaces_status_error(self, client):
        """Test getting interface status with error"""
        mock_manager = MagicMock()
        mock_manager.get_interface_status.side_effect = Exception("Test error")
        
        with patch('app.interface_manager', mock_manager):
            response = client.get('/api/interfaces')
            
            assert response.status_code == 500
            data = json.loads(response.data)
            assert "error" in data
    
    def test_get_interface_types(self, client):
        """Test getting available interface types"""
        response = client.get('/api/interfaces/types')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        
        assert "interface_types" in data
        assert "agent_types" in data
        
        # Check interface types
        interface_types = {it["type"] for it in data["interface_types"]}
        assert "claude_code" in interface_types
        assert "anthropic_api" in interface_types
        assert "mock" in interface_types
        
        # Check agent types
        agent_types = {at["type"] for at in data["agent_types"]}
        assert "Orchestrator" in agent_types
        assert "DesignAgent" in agent_types
        assert "CodeAgent" in agent_types
        assert "QAAgent" in agent_types
        assert "DataAgent" in agent_types


class TestInterfaceSwitchingEndpoints:
    """Test interface switching endpoints"""
    
    def test_switch_interface_success(self, client, mock_interface_manager):
        """Test successful interface switching"""
        mock_interface_manager.switch_interface.return_value = {
            "success": True,
            "old_interface": "claude_code",
            "active_interface": "mock",
            "message": "Successfully switched to mock"
        }
        
        with patch('app.interface_manager', mock_interface_manager):
            response = client.post('/api/interfaces/mock/switch')
            
            assert response.status_code == 200
            data = json.loads(response.data)
            
            assert data["success"] is True
            assert data["active_interface"] == "mock"
            mock_interface_manager.switch_interface.assert_called_once_with("mock")
    
    def test_switch_interface_failure(self, client, mock_interface_manager):
        """Test failed interface switching"""
        mock_interface_manager.switch_interface.return_value = {
            "success": False,
            "error": "Interface not available",
            "active_interface": "claude_code"
        }
        
        with patch('app.interface_manager', mock_interface_manager):
            response = client.post('/api/interfaces/unknown/switch')
            
            assert response.status_code == 400
            data = json.loads(response.data)
            
            assert data["success"] is False
            assert "not available" in data["error"]
    
    def test_switch_interface_exception(self, client, mock_interface_manager):
        """Test interface switching with exception"""
        mock_interface_manager.switch_interface.side_effect = Exception("Async error")
        
        with patch('app.interface_manager', mock_interface_manager):
            response = client.post('/api/interfaces/mock/switch')
            
            assert response.status_code == 500
            data = json.loads(response.data)
            
            assert data["success"] is False
            assert "error" in data


class TestInterfaceTestingEndpoints:
    """Test interface testing endpoints"""
    
    def test_test_interface_success(self, client, mock_interface_manager):
        """Test successful interface testing"""
        mock_interface = MagicMock()
        mock_interface.test_connection.return_value = {
            "success": True,
            "message": "Interface test successful"
        }
        
        mock_interface_manager.interfaces = {"mock": mock_interface}
        mock_interface_manager.initialize_interface.return_value = True
        
        with patch('app.interface_manager', mock_interface_manager):
            response = client.post('/api/interfaces/mock/test')
            
            assert response.status_code == 200
            data = json.loads(response.data)
            
            assert data["success"] is True
            assert "successful" in data["message"]
    
    def test_test_interface_not_available(self, client, mock_interface_manager):
        """Test testing interface that's not available"""
        mock_interface_manager.interfaces = {}
        mock_interface_manager.initialize_interface.return_value = False
        
        with patch('app.interface_manager', mock_interface_manager):
            response = client.post('/api/interfaces/nonexistent/test')
            
            assert response.status_code == 500
            data = json.loads(response.data)
            
            assert data["success"] is False
    
    def test_test_interface_initialization_needed(self, client, mock_interface_manager):
        """Test testing interface that needs initialization"""
        mock_interface = MagicMock()
        mock_interface.test_connection.return_value = {
            "success": True,
            "message": "Test passed"
        }
        
        # Interface not in interfaces dict initially
        mock_interface_manager.interfaces = {}
        mock_interface_manager.initialize_interface.return_value = True
        
        # After initialization, interface is available
        def side_effect(interface_type):
            if interface_type == "mock":
                mock_interface_manager.interfaces["mock"] = mock_interface
            return True
        
        mock_interface_manager.initialize_interface.side_effect = side_effect
        
        with patch('app.interface_manager', mock_interface_manager):
            response = client.post('/api/interfaces/mock/test')
            
            assert response.status_code == 200
            data = json.loads(response.data)
            
            assert data["success"] is True
            mock_interface_manager.initialize_interface.assert_called_once_with("mock")


class TestConfigurationEndpoints:
    """Test interface configuration endpoints"""
    
    def test_get_interface_config(self, client, mock_interface_manager):
        """Test getting interface configuration"""
        with patch('app.interface_manager', mock_interface_manager):
            response = client.get('/api/interfaces/mock/config')
            
            assert response.status_code == 200
            data = json.loads(response.data)
            
            assert "enabled" in data
            assert "timeout" in data
    
    def test_get_interface_config_not_found(self, client, mock_interface_manager):
        """Test getting config for non-existent interface"""
        mock_interface_manager.configs = {}
        
        with patch('app.interface_manager', mock_interface_manager):
            response = client.get('/api/interfaces/nonexistent/config')
            
            assert response.status_code == 404
            data = json.loads(response.data)
            assert "not found" in data["error"]
    
    def test_update_interface_config_success(self, client, mock_interface_manager):
        """Test successful configuration update"""
        mock_interface_manager.update_interface_config.return_value = {
            "success": True,
            "message": "Configuration updated",
            "needs_reinitialization": False,
            "masked_config": {"enabled": True, "timeout": 600}
        }
        
        config_data = {
            "enabled": True,
            "timeout": 600,
            "api_key": "new-key"
        }
        
        with patch('app.interface_manager', mock_interface_manager):
            response = client.put(
                '/api/interfaces/mock/config',
                data=json.dumps(config_data),
                content_type='application/json'
            )
            
            assert response.status_code == 200
            data = json.loads(response.data)
            
            assert data["success"] is True
            mock_interface_manager.update_interface_config.assert_called_once_with(
                "mock", config_data
            )
    
    def test_update_interface_config_failure(self, client, mock_interface_manager):
        """Test failed configuration update"""
        mock_interface_manager.update_interface_config.return_value = {
            "success": False,
            "error": "Invalid configuration"
        }
        
        with patch('app.interface_manager', mock_interface_manager):
            response = client.put(
                '/api/interfaces/mock/config',
                data=json.dumps({"invalid": "config"}),
                content_type='application/json'
            )
            
            assert response.status_code == 400
            data = json.loads(response.data)
            
            assert data["success"] is False
            assert "Invalid configuration" in data["error"]
    
    def test_update_interface_config_no_data(self, client, mock_interface_manager):
        """Test configuration update without data"""
        with patch('app.interface_manager', mock_interface_manager):
            response = client.put('/api/interfaces/mock/config')
            
            assert response.status_code == 400
            data = json.loads(response.data)
            assert "No configuration data" in data["error"]


class TestInitializationEndpoints:
    """Test interface initialization endpoints"""
    
    def test_initialize_interface_success(self, client, mock_interface_manager):
        """Test successful interface initialization"""
        mock_interface_manager.initialize_interface.return_value = True
        
        with patch('app.interface_manager', mock_interface_manager):
            response = client.post('/api/interfaces/mock/initialize')
            
            assert response.status_code == 200
            data = json.loads(response.data)
            
            assert data["success"] is True
            assert "initialized" in data["message"]
            mock_interface_manager.initialize_interface.assert_called_once_with("mock")
    
    def test_initialize_interface_failure(self, client, mock_interface_manager):
        """Test failed interface initialization"""
        mock_interface_manager.initialize_interface.return_value = False
        
        with patch('app.interface_manager', mock_interface_manager):
            response = client.post('/api/interfaces/mock/initialize')
            
            assert response.status_code == 500
            data = json.loads(response.data)
            
            assert data["success"] is False
            assert "failed" in data["error"]


class TestGenerationEndpoints:
    """Test agent generation endpoints"""
    
    def test_generate_with_interface_success(self, client, mock_interface_manager):
        """Test successful generation with interface"""
        mock_interface = MagicMock()
        mock_interface.generate_response.return_value = "Generated response text"
        
        mock_interface_manager.get_active_interface.return_value = mock_interface
        mock_interface_manager.active_interface = "mock"
        
        request_data = {
            "prompt": "Generate a Python function",
            "agent_type": "CODE",
            "context": {"language": "python"}
        }
        
        with patch('app.interface_manager', mock_interface_manager):
            response = client.post(
                '/api/interfaces/generate',
                data=json.dumps(request_data),
                content_type='application/json'
            )
            
            assert response.status_code == 200
            data = json.loads(response.data)
            
            assert data["success"] is True
            assert data["response"] == "Generated response text"
            assert data["interface_type"] == "mock"
            assert data["agent_type"] == "CODE"
    
    def test_generate_with_interface_no_prompt(self, client, mock_interface_manager):
        """Test generation without prompt"""
        request_data = {
            "agent_type": "CODE"
        }
        
        with patch('app.interface_manager', mock_interface_manager):
            response = client.post(
                '/api/interfaces/generate',
                data=json.dumps(request_data),
                content_type='application/json'
            )
            
            assert response.status_code == 400
            data = json.loads(response.data)
            
            assert data["success"] is False
            assert "required" in data["error"]
    
    def test_generate_with_interface_invalid_agent_type(self, client, mock_interface_manager):
        """Test generation with invalid agent type"""
        request_data = {
            "prompt": "Test prompt",
            "agent_type": "INVALID"
        }
        
        with patch('app.interface_manager', mock_interface_manager):
            response = client.post(
                '/api/interfaces/generate',
                data=json.dumps(request_data),
                content_type='application/json'
            )
            
            assert response.status_code == 400
            data = json.loads(response.data)
            
            assert data["success"] is False
            assert "Invalid agent type" in data["error"]
    
    def test_generate_with_interface_no_active_interface(self, client, mock_interface_manager):
        """Test generation with no active interface"""
        mock_interface_manager.get_active_interface.return_value = None
        
        request_data = {
            "prompt": "Test prompt",
            "agent_type": "CODE"
        }
        
        with patch('app.interface_manager', mock_interface_manager):
            response = client.post(
                '/api/interfaces/generate',
                data=json.dumps(request_data),
                content_type='application/json'
            )
            
            assert response.status_code == 400
            data = json.loads(response.data)
            
            assert data["success"] is False
            assert "No active interface" in data["error"]
    
    def test_analyze_with_interface_success(self, client, mock_interface_manager):
        """Test successful code analysis with interface"""
        mock_interface = MagicMock()
        mock_interface.analyze_code.return_value = "Code analysis result"
        
        mock_interface_manager.get_active_interface.return_value = mock_interface
        mock_interface_manager.active_interface = "mock"
        
        request_data = {
            "code": "def hello(): print('Hello')",
            "analysis_type": "review",
            "agent_type": "QA"
        }
        
        with patch('app.interface_manager', mock_interface_manager):
            response = client.post(
                '/api/interfaces/analyze',
                data=json.dumps(request_data),
                content_type='application/json'
            )
            
            assert response.status_code == 200
            data = json.loads(response.data)
            
            assert data["success"] is True
            assert data["analysis"] == "Code analysis result"
            assert data["interface_type"] == "mock"
            assert data["agent_type"] == "QA"
            assert data["analysis_type"] == "review"
    
    def test_analyze_with_interface_no_code(self, client, mock_interface_manager):
        """Test analysis without code"""
        request_data = {
            "analysis_type": "review",
            "agent_type": "QA"
        }
        
        with patch('app.interface_manager', mock_interface_manager):
            response = client.post(
                '/api/interfaces/analyze',
                data=json.dumps(request_data),
                content_type='application/json'
            )
            
            assert response.status_code == 400
            data = json.loads(response.data)
            
            assert data["success"] is False
            assert "required" in data["error"]


class TestWebSocketIntegration:
    """Test WebSocket integration with interface management"""
    
    def test_websocket_events_defined(self):
        """Test that interface-related WebSocket events are defined"""
        # Get the SocketIO instance and check for our handlers
        socketio_instance = socketio
        
        # Check that our event handlers are registered
        handlers = socketio_instance.handlers['/']
        
        # These should be defined in the app
        assert 'request_interface_status' in handlers
        assert 'switch_interface' in handlers
    
    def test_interface_status_request_handler(self, client, mock_interface_manager):
        """Test WebSocket interface status request handler"""
        socketio_client = socketio.test_client(app)
        
        with patch('app.interface_manager', mock_interface_manager):
            # Emit the request
            socketio_client.emit('request_interface_status')
            
            # Check that response was received
            received = socketio_client.get_received()
            
            # Should receive interface_status event
            status_events = [r for r in received if r['name'] == 'interface_status']
            assert len(status_events) > 0
            
            status_data = status_events[0]['args'][0]
            assert 'active_interface' in status_data


class TestErrorHandlingAndEdgeCases:
    """Test error handling and edge cases"""
    
    def test_endpoints_with_invalid_json(self, client):
        """Test endpoints with invalid JSON data"""
        response = client.post(
            '/api/interfaces/generate',
            data="invalid json",
            content_type='application/json'
        )
        
        assert response.status_code == 400
    
    def test_endpoints_with_missing_interface_manager(self, client):
        """Test endpoints when interface manager is not available"""
        with patch('app.interface_manager', None):
            response = client.get('/api/interfaces')
            
            # Should handle gracefully
            assert response.status_code == 500
    
    def test_concurrent_interface_operations(self, client, mock_interface_manager):
        """Test concurrent interface operations"""
        import threading
        import time
        
        results = []
        
        def make_request():
            with app.test_client() as test_client:
                response = test_client.get('/api/interfaces')
                results.append(response.status_code)
        
        # Start multiple concurrent requests
        threads = []
        for _ in range(5):
            thread = threading.Thread(target=make_request)
            threads.append(thread)
        
        with patch('app.interface_manager', mock_interface_manager):
            for thread in threads:
                thread.start()
            
            for thread in threads:
                thread.join()
        
        # All requests should succeed
        assert all(status == 200 for status in results)
        assert len(results) == 5


if __name__ == "__main__":
    pytest.main([__file__, "-v"])