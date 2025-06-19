"""
Tests for ContextManagerFactory

Tests the factory pattern implementation for context manager switching.
"""

import pytest
import asyncio
import tempfile
import shutil
import os
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import threading

# Add lib directory to path for imports
import sys
lib_path = Path(__file__).parent.parent.parent / "lib"
sys.path.insert(0, str(lib_path))

from context_manager_factory import (
    ContextManagerFactory, ContextMode, get_context_manager_factory,
    create_context_manager
)
from context_config import ContextConfig
from simple_context_manager import SimpleContextManager
from context_manager import ContextManager


class TestContextManagerFactory:
    """Test ContextManagerFactory functionality"""
    
    @pytest.fixture
    def temp_project(self):
        """Create temporary project directory"""
        temp_dir = tempfile.mkdtemp()
        project_path = Path(temp_dir)
        
        # Create test files
        (project_path / "test.py").write_text("print('test')")
        (project_path / "README.md").write_text("# Test Project")
        
        yield project_path
        
        # Cleanup
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def temp_config_path(self):
        """Create temporary config file path"""
        temp_dir = tempfile.mkdtemp()
        config_path = Path(temp_dir) / "context_config.yaml"
        
        yield str(config_path)
        
        # Cleanup
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def factory(self, temp_config_path):
        """Create ContextManagerFactory instance"""
        return ContextManagerFactory(config_path=temp_config_path)
    
    def test_initialization(self, temp_config_path):
        """Test factory initialization"""
        factory = ContextManagerFactory(config_path=temp_config_path)
        
        assert factory.config_path == temp_config_path
        assert isinstance(factory.config, ContextConfig)
        assert factory._current_manager is None
        assert factory._current_mode is None
        assert isinstance(factory._lock, threading.Lock)
    
    def test_default_config_path(self):
        """Test default configuration path generation"""
        factory = ContextManagerFactory()
        
        expected_path = str(Path.cwd() / ".orch-state" / "context_config.yaml")
        assert factory.config_path == expected_path
    
    def test_load_config_from_file(self, temp_config_path):
        """Test loading configuration from file"""
        # Create a config file
        config = ContextConfig(default_mode=ContextMode.SIMPLE, max_tokens=5000)
        config.to_file(temp_config_path)
        
        # Load it
        factory = ContextManagerFactory(config_path=temp_config_path)
        
        assert factory.config.default_mode == ContextMode.SIMPLE
        assert factory.config.max_tokens == 5000
    
    def test_load_config_fallback(self, temp_config_path):
        """Test fallback to default config when file doesn't exist"""
        # Don't create the file
        factory = ContextManagerFactory(config_path=temp_config_path)
        
        # Should use default config
        assert factory.config.default_mode == ContextMode.AUTO
        assert factory.config.max_tokens == 200000
    
    def test_save_config(self, factory, temp_config_path):
        """Test saving configuration"""
        # Modify config
        factory.config.default_mode = ContextMode.FANCY
        factory.config.max_tokens = 15000
        
        # Save it
        factory.save_config()
        
        # Verify file was created and contains correct data
        assert Path(temp_config_path).exists()
        
        # Load it back
        loaded_config = ContextConfig.from_file(temp_config_path)
        assert loaded_config.default_mode == ContextMode.FANCY
        assert loaded_config.max_tokens == 15000
    
    @patch('context_manager_factory.os.getenv')
    @patch('context_manager_factory.psutil')
    def test_detect_mode_auto_conditions(self, mock_psutil, mock_getenv, factory):
        """Test automatic mode detection under various conditions"""
        # Setup mocks
        mock_getenv.return_value = None
        mock_psutil.virtual_memory.return_value.available = 4 * 1024 * 1024 * 1024  # 4GB
        mock_psutil.cpu_count.return_value = 4
        
        # Mock other detection methods
        with patch.object(factory, '_is_mock_interface_active', return_value=False), \
             patch.object(factory, '_is_ci_environment', return_value=False), \
             patch.object(factory, '_is_claude_code_available', return_value=True):
            
            mode = factory._detect_mode()
            assert mode == ContextMode.FANCY
    
    @patch('context_manager_factory.os.getenv')
    def test_detect_mode_performance_env(self, mock_getenv, factory):
        """Test detection when performance mode is enabled via environment"""
        mock_getenv.side_effect = lambda key, default="": {
            "AGENT_WORKFLOW_PERFORMANCE_MODE": "true"
        }.get(key, default)
        
        mode = factory._detect_mode()
        assert mode == ContextMode.SIMPLE
    
    def test_detect_mode_explicit_config(self, factory):
        """Test that explicit config overrides auto-detection"""
        factory.config.default_mode = ContextMode.FANCY
        
        mode = factory._detect_mode()
        assert mode == ContextMode.FANCY
    
    @patch('context_manager_factory.os.getenv')
    def test_is_ci_environment(self, mock_getenv, factory):
        """Test CI environment detection"""
        # Test with CI environment variable
        mock_getenv.side_effect = lambda key: "true" if key == "CI" else None
        assert factory._is_ci_environment() is True
        
        # Test with GitHub Actions
        mock_getenv.side_effect = lambda key: "true" if key == "GITHUB_ACTIONS" else None
        assert factory._is_ci_environment() is True
        
        # Test with no CI variables
        mock_getenv.return_value = None
        assert factory._is_ci_environment() is False
    
    @patch('context_manager_factory.subprocess.run')
    def test_is_claude_code_available(self, mock_run, factory):
        """Test Claude Code availability detection"""
        # Test when Claude Code is available
        mock_result = Mock()
        mock_result.returncode = 0
        mock_run.return_value = mock_result
        
        assert factory._is_claude_code_available() is True
        
        # Test when Claude Code is not available
        mock_run.side_effect = FileNotFoundError()
        assert factory._is_claude_code_available() is False
        
        # Test when Claude Code returns error
        mock_result.returncode = 1
        mock_run.side_effect = None
        mock_run.return_value = mock_result
        assert factory._is_claude_code_available() is False
    
    @patch('context_manager_factory.psutil')
    def test_is_low_resource_environment(self, mock_psutil, factory):
        """Test low resource environment detection"""
        # Test with sufficient resources
        mock_psutil.virtual_memory.return_value.available = 4 * 1024 * 1024 * 1024  # 4GB
        mock_psutil.cpu_count.return_value = 4
        assert factory._is_low_resource_environment() is False
        
        # Test with low memory
        mock_psutil.virtual_memory.return_value.available = 1 * 1024 * 1024 * 1024  # 1GB
        mock_psutil.cpu_count.return_value = 4
        assert factory._is_low_resource_environment() is True
        
        # Test with low CPU
        mock_psutil.virtual_memory.return_value.available = 4 * 1024 * 1024 * 1024  # 4GB
        mock_psutil.cpu_count.return_value = 1
        assert factory._is_low_resource_environment() is True
        
        # Test when psutil is not available
        mock_psutil.side_effect = ImportError()
        assert factory._is_low_resource_environment() is False
    
    @pytest.mark.asyncio
    async def test_create_context_manager_simple(self, factory, temp_project):
        """Test creating simple context manager"""
        with patch.object(factory, '_detect_mode', return_value=ContextMode.SIMPLE):
            manager = await factory.create_context_manager(
                project_path=str(temp_project),
                mode=ContextMode.SIMPLE
            )
            
            assert isinstance(manager, SimpleContextManager)
            assert factory._current_manager is manager
            assert factory._current_mode == ContextMode.SIMPLE
    
    @pytest.mark.asyncio
    async def test_create_context_manager_fancy(self, factory, temp_project):
        """Test creating fancy context manager"""
        with patch.object(factory, '_detect_mode', return_value=ContextMode.FANCY):
            manager = await factory.create_context_manager(
                project_path=str(temp_project),
                mode=ContextMode.FANCY
            )
            
            assert isinstance(manager, ContextManager)
            assert factory._current_manager is manager
            assert factory._current_mode == ContextMode.FANCY
    
    @pytest.mark.asyncio
    async def test_create_context_manager_reuse(self, factory, temp_project):
        """Test that existing manager is reused when appropriate"""
        with patch.object(factory, '_detect_mode', return_value=ContextMode.SIMPLE):
            # Create first manager
            manager1 = await factory.create_context_manager(
                project_path=str(temp_project),
                mode=ContextMode.SIMPLE
            )
            
            # Create second manager with same mode - should reuse
            manager2 = await factory.create_context_manager(
                project_path=str(temp_project),
                mode=ContextMode.SIMPLE
            )
            
            assert manager1 is manager2
    
    @pytest.mark.asyncio
    async def test_create_context_manager_force_recreate(self, factory, temp_project):
        """Test forcing recreation of context manager"""
        with patch.object(factory, '_detect_mode', return_value=ContextMode.SIMPLE):
            # Create first manager
            manager1 = await factory.create_context_manager(
                project_path=str(temp_project),
                mode=ContextMode.SIMPLE
            )
            
            # Force recreate
            manager2 = await factory.create_context_manager(
                project_path=str(temp_project),
                mode=ContextMode.SIMPLE,
                force_recreate=True
            )
            
            assert manager1 is not manager2
    
    @pytest.mark.asyncio
    async def test_switch_mode(self, factory, temp_project):
        """Test switching between context modes"""
        # Start with simple mode
        with patch.object(factory, '_detect_mode', return_value=ContextMode.SIMPLE):
            manager1 = await factory.create_context_manager(
                project_path=str(temp_project),
                mode=ContextMode.SIMPLE
            )
            assert isinstance(manager1, SimpleContextManager)
        
        # Switch to fancy mode
        manager2 = await factory.switch_mode(
            ContextMode.FANCY,
            project_path=str(temp_project)
        )
        
        assert isinstance(manager2, ContextManager)
        assert factory._current_mode == ContextMode.FANCY
        assert factory.config.default_mode == ContextMode.FANCY
        assert factory._current_manager is manager2
    
    def test_get_current_mode(self, factory):
        """Test getting current mode"""
        assert factory.get_current_mode() is None
        
        factory._current_mode = ContextMode.SIMPLE
        assert factory.get_current_mode() == ContextMode.SIMPLE
    
    def test_get_current_manager(self, factory):
        """Test getting current manager"""
        assert factory.get_current_manager() is None
        
        mock_manager = Mock()
        factory._current_manager = mock_manager
        assert factory.get_current_manager() is mock_manager
    
    def test_get_mode_info(self, factory):
        """Test getting mode information"""
        # Test fancy mode info
        fancy_info = factory.get_mode_info(ContextMode.FANCY)
        assert fancy_info["name"] == "Fancy Context Management"
        assert "Intelligent file filtering" in fancy_info["features"]
        assert "Production workflows" in fancy_info["best_for"]
        
        # Test simple mode info
        simple_info = factory.get_mode_info(ContextMode.SIMPLE)
        assert simple_info["name"] == "Simple Context Management"
        assert "Fast file pattern matching" in simple_info["features"]
        assert "Demo scenarios" in simple_info["best_for"]
        
        # Test auto mode info
        auto_info = factory.get_mode_info(ContextMode.AUTO)
        assert auto_info["name"] == "Automatic Mode Detection"
        assert "Interface detection" in auto_info["features"]
    
    def test_get_detection_status(self, factory):
        """Test getting detection status"""
        factory._current_mode = ContextMode.SIMPLE
        
        with patch.object(factory, '_detect_mode', return_value=ContextMode.SIMPLE), \
             patch.object(factory, '_is_mock_interface_active', return_value=True), \
             patch.object(factory, '_is_ci_environment', return_value=False):
            
            status = factory.get_detection_status()
            
            assert status["current_mode"] == "simple"
            assert status["configured_mode"] == "auto"
            assert status["detection_factors"]["mock_interface_active"] is True
            assert status["detection_factors"]["ci_environment"] is False
            assert status["auto_detected_mode"] == "simple"
    
    @pytest.mark.asyncio
    async def test_get_performance_comparison(self, factory, temp_project):
        """Test getting performance comparison"""
        # Create a manager first
        with patch.object(factory, '_detect_mode', return_value=ContextMode.SIMPLE):
            await factory.create_context_manager(project_path=str(temp_project))
        
        comparison = await factory.get_performance_comparison()
        
        assert "current_mode" in comparison
        assert "current_metrics" in comparison
        assert "estimated_performance" in comparison
        assert ContextMode.FANCY.value in comparison["estimated_performance"]
        assert ContextMode.SIMPLE.value in comparison["estimated_performance"]
    
    @pytest.mark.asyncio
    async def test_get_performance_comparison_no_manager(self, factory):
        """Test performance comparison when no manager is active"""
        comparison = await factory.get_performance_comparison()
        assert "error" in comparison
    
    @pytest.mark.asyncio
    async def test_cleanup(self, factory, temp_project):
        """Test factory cleanup"""
        # Create a manager
        with patch.object(factory, '_detect_mode', return_value=ContextMode.SIMPLE):
            await factory.create_context_manager(project_path=str(temp_project))
        
        assert factory._current_manager is not None
        
        # Cleanup
        await factory.cleanup()
        
        assert factory._current_manager is None
        assert factory._current_mode is None
    
    @pytest.mark.asyncio
    async def test_stop_current_manager(self, factory):
        """Test stopping current manager"""
        # Mock manager with stop method
        mock_manager = AsyncMock()
        factory._current_manager = mock_manager
        factory._current_mode = ContextMode.SIMPLE
        
        await factory._stop_current_manager()
        
        mock_manager.stop.assert_called_once()
        assert factory._current_manager is None
        assert factory._current_mode is None
    
    @pytest.mark.asyncio
    async def test_stop_current_manager_error_handling(self, factory):
        """Test error handling when stopping manager fails"""
        # Mock manager that raises exception on stop
        mock_manager = AsyncMock()
        mock_manager.stop.side_effect = Exception("Stop failed")
        factory._current_manager = mock_manager
        
        # Should not raise exception
        await factory._stop_current_manager()
        
        assert factory._current_manager is None
        assert factory._current_mode is None
    
    def test_invalid_mode_creation(self, factory, temp_project):
        """Test error handling for invalid mode"""
        with pytest.raises(ValueError):
            asyncio.run(factory._create_manager(
                "invalid_mode",  # Invalid mode
                str(temp_project)
            ))


class TestGlobalFactory:
    """Test global factory functions"""
    
    def test_get_context_manager_factory_singleton(self):
        """Test that global factory returns singleton"""
        factory1 = get_context_manager_factory()
        factory2 = get_context_manager_factory()
        
        assert factory1 is factory2
        assert isinstance(factory1, ContextManagerFactory)
    
    @pytest.mark.asyncio
    async def test_create_context_manager_convenience_function(self):
        """Test convenience function for creating context manager"""
        with patch('context_manager_factory._factory_instance') as mock_instance:
            mock_factory = Mock()
            mock_factory.create_context_manager = AsyncMock(return_value=Mock())
            mock_instance = mock_factory
            
            # This would normally create a manager, but we'll mock it
            with patch('context_manager_factory.get_context_manager_factory', return_value=mock_factory):
                manager = await create_context_manager(
                    project_path="/test/path",
                    mode=ContextMode.SIMPLE
                )
                
                mock_factory.create_context_manager.assert_called_once_with(
                    project_path="/test/path",
                    mode=ContextMode.SIMPLE
                )


class TestContextModeDetectionIntegration:
    """Integration tests for context mode detection"""
    
    @pytest.fixture
    def factory_with_mocks(self, temp_config_path):
        """Create factory with commonly used mocks"""
        factory = ContextManagerFactory(config_path=temp_config_path)
        
        # Set up default mock returns
        with patch.object(factory, '_is_mock_interface_active', return_value=False), \
             patch.object(factory, '_is_ci_environment', return_value=False), \
             patch.object(factory, '_is_low_resource_environment', return_value=False), \
             patch.object(factory, '_is_claude_code_available', return_value=True):
            
            yield factory
    
    def test_auto_detection_priority_mock_interface(self, factory_with_mocks):
        """Test that mock interface detection has high priority"""
        factory = factory_with_mocks
        
        with patch.object(factory, '_is_mock_interface_active', return_value=True):
            mode = factory._detect_mode()
            assert mode == ContextMode.SIMPLE
    
    @patch('context_manager_factory.os.getenv')
    def test_auto_detection_priority_performance_env(self, mock_getenv, factory_with_mocks):
        """Test that performance mode environment variable has high priority"""
        factory = factory_with_mocks
        mock_getenv.side_effect = lambda key, default="": {
            "AGENT_WORKFLOW_PERFORMANCE_MODE": "true"
        }.get(key, default)
        
        mode = factory._detect_mode()
        assert mode == ContextMode.SIMPLE
    
    def test_auto_detection_priority_ci(self, factory_with_mocks):
        """Test that CI environment detection works"""
        factory = factory_with_mocks
        
        with patch.object(factory, '_is_ci_environment', return_value=True):
            mode = factory._detect_mode()
            assert mode == ContextMode.SIMPLE
    
    def test_auto_detection_priority_resources(self, factory_with_mocks):
        """Test that low resource detection works"""
        factory = factory_with_mocks
        
        with patch.object(factory, '_is_low_resource_environment', return_value=True):
            mode = factory._detect_mode()
            assert mode == ContextMode.SIMPLE
    
    def test_auto_detection_priority_claude_code(self, factory_with_mocks):
        """Test that Claude Code availability affects detection"""
        factory = factory_with_mocks
        
        with patch.object(factory, '_is_claude_code_available', return_value=False):
            mode = factory._detect_mode()
            assert mode == ContextMode.SIMPLE
    
    def test_auto_detection_default_fancy(self, factory_with_mocks):
        """Test that default is fancy when all conditions are met"""
        factory = factory_with_mocks
        
        # All conditions should favor fancy mode
        mode = factory._detect_mode()
        assert mode == ContextMode.FANCY