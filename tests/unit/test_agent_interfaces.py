"""
Unit tests for agent interface management system

Tests the agent interface classes, configuration, and switching functionality
"""

import asyncio
import json
import pytest
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock, MagicMock
import os
import sys

# Add the visualizer directory to the path
visualizer_path = Path(__file__).parent.parent.parent / "tools" / "visualizer"
sys.path.insert(0, str(visualizer_path))

# Mock imports that might not be available in test environment
sys.modules['anthropic'] = MagicMock()

# Import the modules to test
from agent_interfaces import (
    InterfaceType, InterfaceStatus, InterfaceConfig,
    BaseAgentInterface, ClaudeCodeInterface, AnthropicAPIInterface, 
    MockInterface, InterfaceManager
)

# Mock AgentType for testing
from unittest.mock import MagicMock
AgentType = MagicMock()
AgentType.CODE = "CODE"
AgentType.DESIGN = "DESIGN"
AgentType.QA = "QA"


class TestInterfaceConfig:
    """Test InterfaceConfig data class"""
    
    def test_interface_config_creation(self):
        """Test basic interface config creation"""
        config = InterfaceConfig(
            interface_type="test_type",
            enabled=True,
            api_key="test_key",
            timeout=300
        )
        
        assert config.interface_type == "test_type"
        assert config.enabled is True
        assert config.api_key == "test_key"
        assert config.timeout == 300
        assert config.custom_settings == {}
    
    def test_interface_config_defaults(self):
        """Test interface config with defaults"""
        config = InterfaceConfig(interface_type="test")
        
        assert config.enabled is True
        assert config.timeout == 300
        assert config.max_tokens == 4000
        assert config.model == "claude-3-sonnet-20240229"
        assert config.temperature == 0.7
        assert config.custom_settings == {}
    
    def test_to_dict_conversion(self):
        """Test converting config to dictionary"""
        config = InterfaceConfig(
            interface_type="test",
            enabled=False,
            api_key="sk-test-key",
            custom_settings={"test": "value"}
        )
        
        data = config.to_dict()
        
        assert isinstance(data, dict)
        assert data["interface_type"] == "test"
        assert data["enabled"] is False
        assert data["api_key"] == "sk-test-key"
        assert data["custom_settings"]["test"] == "value"
    
    def test_from_dict_creation(self):
        """Test creating config from dictionary"""
        data = {
            "interface_type": "test",
            "enabled": True,
            "api_key": "sk-test",
            "timeout": 600,
            "custom_settings": {"test": "value"}
        }
        
        config = InterfaceConfig.from_dict(data)
        
        assert config.interface_type == "test"
        assert config.enabled is True
        assert config.api_key == "sk-test"
        assert config.timeout == 600
        assert config.custom_settings["test"] == "value"
    
    def test_mask_sensitive_data(self):
        """Test masking sensitive data in config"""
        config = InterfaceConfig(
            interface_type="test",
            api_key="sk-ant-1234567890abcdef1234567890abcdef"
        )
        
        masked = config.mask_sensitive_data()
        
        assert "api_key" in masked
        assert masked["api_key"] == "sk-...90abcdef"
        
        # Test short key
        config.api_key = "short"
        masked = config.mask_sensitive_data()
        assert masked["api_key"] == "sk-***"


class TestMockInterface:
    """Test MockInterface implementation"""
    
    @pytest.fixture
    def mock_config(self):
        return InterfaceConfig(
            interface_type=InterfaceType.MOCK.value,
            custom_settings={
                "response_delay": 0.1,  # Fast for testing
                "failure_rate": 0.0     # No failures for basic tests
            }
        )
    
    @pytest.fixture
    def mock_interface(self, mock_config):
        return MockInterface(mock_config)
    
    @pytest.mark.asyncio
    async def test_mock_interface_initialization(self, mock_interface):
        """Test mock interface initialization"""
        success = await mock_interface.initialize()
        
        assert success is True
        assert mock_interface.status == InterfaceStatus.CONNECTED
        assert mock_interface.connection_time is not None
        assert mock_interface.last_error is None
    
    @pytest.mark.asyncio
    async def test_mock_interface_test_connection(self, mock_interface):
        """Test mock interface connection test"""
        await mock_interface.initialize()
        
        result = await mock_interface.test_connection()
        
        assert result["success"] is True
        assert "Mock interface test successful" in result["message"]
        assert result["simulated"] is True
    
    @pytest.mark.asyncio
    async def test_mock_interface_generate_response(self, mock_interface):
        """Test mock interface response generation"""
        await mock_interface.initialize()
        
        response = await mock_interface.generate_response(
            "Test prompt", 
            AgentType.CODE,
            {"language": "python"}
        )
        
        assert isinstance(response, str)
        assert len(response) > 0
        assert "CODE" in response or "Code Agent" in response
        assert mock_interface.request_count == 1
    
    @pytest.mark.asyncio
    async def test_mock_interface_analyze_code(self, mock_interface):
        """Test mock interface code analysis"""
        await mock_interface.initialize()
        
        analysis = await mock_interface.analyze_code(
            "def test(): pass",
            "review",
            AgentType.QA
        )
        
        assert isinstance(analysis, str)
        assert len(analysis) > 0
        assert "analysis" in analysis.lower()
        assert mock_interface.request_count == 1
    
    @pytest.mark.asyncio
    async def test_mock_interface_with_failures(self):
        """Test mock interface with simulated failures"""
        config = InterfaceConfig(
            interface_type=InterfaceType.MOCK.value,
            custom_settings={
                "response_delay": 0.1,
                "failure_rate": 1.0  # Always fail
            }
        )
        interface = MockInterface(config)
        await interface.initialize()
        
        with pytest.raises(RuntimeError, match="Simulated.*failure"):
            await interface.generate_response("test", AgentType.CODE)
        
        assert interface.error_count == 1
    
    @pytest.mark.asyncio
    async def test_mock_interface_status_info(self, mock_interface):
        """Test getting status information"""
        await mock_interface.initialize()
        await mock_interface.generate_response("test", AgentType.CODE)
        
        status = mock_interface.get_status_info()
        
        assert status["interface_type"] == InterfaceType.MOCK.value
        assert status["status"] == InterfaceStatus.CONNECTED.value
        assert status["request_count"] == 1
        assert status["error_count"] == 0
        assert status["uptime"] is not None
    
    @pytest.mark.asyncio
    async def test_mock_interface_shutdown(self, mock_interface):
        """Test mock interface shutdown"""
        await mock_interface.initialize()
        await mock_interface.shutdown()
        
        assert mock_interface.status == InterfaceStatus.DISCONNECTED


class TestClaudeCodeInterface:
    """Test ClaudeCodeInterface implementation"""
    
    @pytest.fixture
    def claude_config(self):
        return InterfaceConfig(
            interface_type=InterfaceType.CLAUDE_CODE.value,
            timeout=300
        )
    
    @pytest.mark.asyncio
    async def test_claude_interface_initialization_no_client(self, claude_config):
        """Test Claude interface when ClaudeCodeClient is not available"""
        with patch('agent_interfaces.ClaudeCodeClient', None):
            interface = ClaudeCodeInterface(claude_config)
            
            success = await interface.initialize()
            
            assert success is False
            assert interface.status == InterfaceStatus.ERROR
            assert "not available" in interface.last_error
    
    @pytest.mark.asyncio
    async def test_claude_interface_initialization_unavailable(self, claude_config):
        """Test Claude interface when Claude CLI is not available"""
        mock_client = Mock()
        mock_client.available = False
        
        with patch('agent_interfaces.ClaudeCodeClient', return_value=mock_client):
            interface = ClaudeCodeInterface(claude_config)
            
            success = await interface.initialize()
            
            assert success is False
            assert interface.status == InterfaceStatus.ERROR
            assert "not available" in interface.last_error
    
    @pytest.mark.asyncio
    async def test_claude_interface_initialization_success(self, claude_config):
        """Test successful Claude interface initialization"""
        mock_client = Mock()
        mock_client.available = True
        
        with patch('agent_interfaces.ClaudeCodeClient', return_value=mock_client):
            interface = ClaudeCodeInterface(claude_config)
            
            success = await interface.initialize()
            
            assert success is True
            assert interface.status == InterfaceStatus.CONNECTED
            assert interface.claude_client is not None
    
    @pytest.mark.asyncio
    async def test_claude_interface_test_connection(self, claude_config):
        """Test Claude interface connection test"""
        mock_client = Mock()
        mock_client.available = True
        mock_client.generate_code = AsyncMock(return_value="def hello(): print('Hello')")
        
        with patch('agent_interfaces.ClaudeCodeClient', return_value=mock_client):
            interface = ClaudeCodeInterface(claude_config)
            await interface.initialize()
            
            result = await interface.test_connection()
            
            assert result["success"] is True
            assert interface.status == InterfaceStatus.CONNECTED
    
    @pytest.mark.asyncio
    async def test_claude_interface_test_connection_failure(self, claude_config):
        """Test Claude interface connection test failure"""
        mock_client = Mock()
        mock_client.available = True
        mock_client.generate_code = AsyncMock(return_value="")
        
        with patch('agent_interfaces.ClaudeCodeClient', return_value=mock_client):
            interface = ClaudeCodeInterface(claude_config)
            await interface.initialize()
            
            result = await interface.test_connection()
            
            assert result["success"] is False
            assert interface.status == InterfaceStatus.ERROR
    
    @pytest.mark.asyncio
    async def test_claude_interface_generate_response(self, claude_config):
        """Test Claude interface response generation"""
        mock_client_class = Mock()
        mock_client_instance = Mock()
        mock_client_instance.generate_code = AsyncMock(return_value="Generated code")
        mock_client_class.return_value = mock_client_instance
        
        original_client = Mock()
        original_client.available = True
        
        with patch('agent_interfaces.ClaudeCodeClient', side_effect=[original_client, mock_client_instance]):
            interface = ClaudeCodeInterface(claude_config)
            await interface.initialize()
            
            response = await interface.generate_response("test prompt", AgentType.CODE)
            
            assert response == "Generated code"
            assert interface.request_count == 1


class TestAnthropicAPIInterface:
    """Test AnthropicAPIInterface implementation"""
    
    @pytest.fixture
    def anthropic_config(self):
        return InterfaceConfig(
            interface_type=InterfaceType.ANTHROPIC_API.value,
            api_key="sk-ant-test-key-1234567890",
            model="claude-3-sonnet-20240229"
        )
    
    @pytest.mark.asyncio
    async def test_anthropic_interface_no_sdk(self, anthropic_config):
        """Test Anthropic interface when SDK is not available"""
        with patch('agent_interfaces.ANTHROPIC_AVAILABLE', False):
            interface = AnthropicAPIInterface(anthropic_config)
            
            success = await interface.initialize()
            
            assert success is False
            assert interface.status == InterfaceStatus.ERROR
            assert "not available" in interface.last_error
    
    @pytest.mark.asyncio
    async def test_anthropic_interface_no_api_key(self):
        """Test Anthropic interface without API key"""
        config = InterfaceConfig(
            interface_type=InterfaceType.ANTHROPIC_API.value,
            api_key=None
        )
        interface = AnthropicAPIInterface(config)
        
        success = await interface.initialize()
        
        assert success is False
        assert interface.status == InterfaceStatus.ERROR
        assert "API key required" in interface.last_error
    
    @pytest.mark.asyncio
    async def test_anthropic_interface_initialization_success(self, anthropic_config):
        """Test successful Anthropic interface initialization"""
        mock_anthropic = MagicMock()
        
        with patch('agent_interfaces.ANTHROPIC_AVAILABLE', True), \
             patch('agent_interfaces.anthropic.AsyncAnthropic', return_value=mock_anthropic):
            interface = AnthropicAPIInterface(anthropic_config)
            
            success = await interface.initialize()
            
            assert success is True
            assert interface.status == InterfaceStatus.CONNECTED
            assert interface.client is not None
    
    @pytest.mark.asyncio
    async def test_anthropic_interface_test_connection(self, anthropic_config):
        """Test Anthropic interface connection test"""
        mock_response = Mock()
        mock_response.content = [Mock(text="API connection test successful")]
        mock_response.model = "claude-3-sonnet-20240229"
        mock_response.usage = Mock(input_tokens=10, output_tokens=5)
        
        mock_client = Mock()
        mock_client.messages.create = AsyncMock(return_value=mock_response)
        
        with patch('agent_interfaces.ANTHROPIC_AVAILABLE', True), \
             patch('agent_interfaces.anthropic.AsyncAnthropic', return_value=mock_client):
            interface = AnthropicAPIInterface(anthropic_config)
            await interface.initialize()
            
            result = await interface.test_connection()
            
            assert result["success"] is True
            assert result["model"] == "claude-3-sonnet-20240229"
            assert "usage" in result
    
    @pytest.mark.asyncio
    async def test_anthropic_interface_generate_response(self, anthropic_config):
        """Test Anthropic interface response generation"""
        mock_response = Mock()
        mock_response.content = [Mock(text="Generated response")]
        
        mock_client = Mock()
        mock_client.messages.create = AsyncMock(return_value=mock_response)
        
        with patch('agent_interfaces.ANTHROPIC_AVAILABLE', True), \
             patch('agent_interfaces.anthropic.AsyncAnthropic', return_value=mock_client):
            interface = AnthropicAPIInterface(anthropic_config)
            await interface.initialize()
            
            response = await interface.generate_response("test prompt", AgentType.CODE)
            
            assert response == "Generated response"
            assert interface.request_count == 1
    
    @pytest.mark.asyncio
    async def test_anthropic_interface_system_message_building(self, anthropic_config):
        """Test system message building for different agent types"""
        mock_response = Mock()
        mock_response.content = [Mock(text="Response")]
        
        mock_client = Mock()
        mock_client.messages.create = AsyncMock(return_value=mock_response)
        
        with patch('agent_interfaces.ANTHROPIC_AVAILABLE', True), \
             patch('agent_interfaces.anthropic.AsyncAnthropic', return_value=mock_client):
            interface = AnthropicAPIInterface(anthropic_config)
            await interface.initialize()
            
            # Test different agent types
            await interface.generate_response("test", AgentType.DESIGN)
            
            call_args = mock_client.messages.create.call_args
            system_message = call_args[1]['system']
            
            assert "DesignAgent" in system_message
            assert "CANNOT modify existing code" in system_message


class TestInterfaceManager:
    """Test InterfaceManager class"""
    
    @pytest.fixture
    def temp_config_file(self):
        """Create a temporary config file for testing"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            config_data = {
                "configs": {
                    "mock": {
                        "interface_type": "mock",
                        "enabled": True,
                        "custom_settings": {"response_delay": 0.1}
                    }
                },
                "active_interface": "mock"
            }
            json.dump(config_data, f)
            f.flush()
            yield f.name
        os.unlink(f.name)
    
    @pytest.fixture
    def interface_manager(self, temp_config_file):
        """Create interface manager with temporary config"""
        manager = InterfaceManager()
        manager.config_file = Path(temp_config_file)
        manager.load_configurations()
        return manager
    
    def test_interface_manager_initialization(self):
        """Test interface manager initialization"""
        manager = InterfaceManager()
        
        assert isinstance(manager.interfaces, dict)
        assert isinstance(manager.configs, dict)
        assert manager.active_interface is not None or len(manager.configs) == 0
    
    def test_interface_manager_config_loading(self, interface_manager):
        """Test configuration loading"""
        assert "mock" in interface_manager.configs
        assert interface_manager.active_interface == "mock"
        assert interface_manager.configs["mock"].enabled is True
    
    def test_interface_manager_config_saving(self, interface_manager):
        """Test configuration saving"""
        # Modify configuration
        interface_manager.configs["mock"].timeout = 600
        interface_manager.active_interface = "claude_code"
        
        # Save
        interface_manager.save_configurations()
        
        # Reload and verify
        interface_manager.load_configurations()
        assert interface_manager.configs["mock"].timeout == 600
        assert interface_manager.active_interface == "claude_code"
    
    @pytest.mark.asyncio
    async def test_interface_manager_initialize_interface(self, interface_manager):
        """Test interface initialization"""
        success = await interface_manager.initialize_interface("mock")
        
        assert success is True
        assert "mock" in interface_manager.interfaces
        assert isinstance(interface_manager.interfaces["mock"], MockInterface)
    
    @pytest.mark.asyncio
    async def test_interface_manager_switch_interface(self, interface_manager):
        """Test interface switching"""
        # First initialize mock interface
        await interface_manager.initialize_interface("mock")
        
        result = await interface_manager.switch_interface("mock")
        
        assert result["success"] is True
        assert result["active_interface"] == "mock"
        assert interface_manager.active_interface == "mock"
    
    @pytest.mark.asyncio
    async def test_interface_manager_switch_to_unknown_interface(self, interface_manager):
        """Test switching to unknown interface"""
        result = await interface_manager.switch_interface("unknown")
        
        assert result["success"] is False
        assert "Unknown interface type" in result["error"]
    
    def test_interface_manager_get_interface_status(self, interface_manager):
        """Test getting interface status"""
        status = interface_manager.get_interface_status()
        
        assert "active_interface" in status
        assert "interfaces" in status
        assert isinstance(status["interfaces"], dict)
    
    def test_interface_manager_update_interface_config(self, interface_manager):
        """Test updating interface configuration"""
        result = interface_manager.update_interface_config("mock", {
            "enabled": False,
            "timeout": 900,
            "custom_response_delay": 2.0
        })
        
        assert result["success"] is True
        assert interface_manager.configs["mock"].enabled is False
        assert interface_manager.configs["mock"].timeout == 900
        assert interface_manager.configs["mock"].custom_settings["response_delay"] == 2.0
    
    def test_interface_manager_update_unknown_interface_config(self, interface_manager):
        """Test updating configuration for unknown interface"""
        result = interface_manager.update_interface_config("unknown", {"enabled": True})
        
        assert result["success"] is False
        assert "Unknown interface type" in result["error"]
    
    @pytest.mark.asyncio
    async def test_interface_manager_get_active_interface(self, interface_manager):
        """Test getting active interface"""
        # Initialize mock interface
        await interface_manager.initialize_interface("mock")
        interface_manager.active_interface = "mock"
        
        active = await interface_manager.get_active_interface()
        
        assert active is not None
        assert isinstance(active, MockInterface)
    
    @pytest.mark.asyncio
    async def test_interface_manager_get_active_interface_none(self, interface_manager):
        """Test getting active interface when none is set"""
        interface_manager.active_interface = None
        
        active = await interface_manager.get_active_interface()
        
        assert active is None
    
    @pytest.mark.asyncio
    async def test_interface_manager_shutdown_all(self, interface_manager):
        """Test shutting down all interfaces"""
        # Initialize some interfaces
        await interface_manager.initialize_interface("mock")
        
        assert len(interface_manager.interfaces) > 0
        
        await interface_manager.shutdown_all()
        
        assert len(interface_manager.interfaces) == 0


class TestIntegrationScenarios:
    """Test complete integration scenarios"""
    
    @pytest.mark.asyncio
    async def test_complete_interface_workflow(self):
        """Test complete workflow: config -> init -> test -> switch -> use"""
        # Create manager
        manager = InterfaceManager()
        
        # Configure mock interface
        manager.configs["mock"] = InterfaceConfig(
            interface_type=InterfaceType.MOCK.value,
            enabled=True,
            custom_settings={"response_delay": 0.1, "failure_rate": 0.0}
        )
        
        # Initialize interface
        init_success = await manager.initialize_interface("mock")
        assert init_success is True
        
        # Test interface
        interface = manager.interfaces["mock"]
        test_result = await interface.test_connection()
        assert test_result["success"] is True
        
        # Switch to interface
        switch_result = await manager.switch_interface("mock")
        assert switch_result["success"] is True
        
        # Use interface
        active_interface = await manager.get_active_interface()
        response = await active_interface.generate_response(
            "Generate a simple function", 
            AgentType.CODE
        )
        assert isinstance(response, str)
        assert len(response) > 0
        
        # Verify status
        status = manager.get_interface_status()
        assert status["active_interface"] == "mock"
        assert status["interfaces"]["mock"]["status"] == "connected"
        assert status["interfaces"]["mock"]["request_count"] > 0
    
    @pytest.mark.asyncio
    async def test_error_handling_and_recovery(self):
        """Test error handling and recovery scenarios"""
        manager = InterfaceManager()
        
        # Test switching to non-existent interface
        result = await manager.switch_interface("nonexistent")
        assert result["success"] is False
        
        # Test with failing mock interface
        manager.configs["failing_mock"] = InterfaceConfig(
            interface_type=InterfaceType.MOCK.value,
            enabled=True,
            custom_settings={"response_delay": 0.1, "failure_rate": 1.0}
        )
        
        await manager.initialize_interface("failing_mock")
        
        # Test should fail
        interface = manager.interfaces["failing_mock"]
        test_result = await interface.test_connection()
        assert test_result["success"] is False
        
        # Interface should be in error state
        status_info = interface.get_status_info()
        assert status_info["error_count"] > 0
    
    @pytest.mark.asyncio
    async def test_concurrent_interface_operations(self):
        """Test concurrent interface operations"""
        manager = InterfaceManager()
        
        # Setup multiple mock interfaces
        interfaces_to_test = ["mock1", "mock2", "mock3"]
        
        for i, name in enumerate(interfaces_to_test):
            manager.configs[name] = InterfaceConfig(
                interface_type=InterfaceType.MOCK.value,
                enabled=True,
                custom_settings={"response_delay": 0.1 * (i + 1)}
            )
        
        # Initialize all interfaces concurrently
        init_tasks = [
            manager.initialize_interface(name) 
            for name in interfaces_to_test
        ]
        init_results = await asyncio.gather(*init_tasks)
        
        # All should succeed
        assert all(init_results)
        
        # Test all interfaces concurrently
        test_tasks = [
            manager.interfaces[name].test_connection()
            for name in interfaces_to_test
        ]
        test_results = await asyncio.gather(*test_tasks)
        
        # All tests should succeed
        assert all(result["success"] for result in test_results)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])