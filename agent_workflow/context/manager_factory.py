"""
Context Manager Factory - Dynamic Context Management Switching

Factory pattern implementation for creating appropriate context managers
based on system state, configuration, and agent interface mode.
"""

import logging
import os
from enum import Enum
from pathlib import Path
from typing import Dict, Any, Optional, Union
import threading

try:
    from .context_manager import ContextManager
    from .simple_context_manager import SimpleContextManager
    from .context_config import ContextConfig, ContextMode
except ImportError:
    from context_manager import ContextManager
    from simple_context_manager import SimpleContextManager
    from context_config import ContextConfig, ContextMode

logger = logging.getLogger(__name__)


# ContextMode is imported from context_config


class ContextManagerFactory:
    """
    Factory for creating appropriate context managers based on system state.
    
    Automatically detects when to use simple vs fancy context management
    based on active agent interface and system configuration.
    """
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize context manager factory.
        
        Args:
            config_path: Path to context management configuration file
        """
        self.config_path = config_path or self._get_default_config_path()
        self.config = self._load_config()
        self._lock = threading.Lock()
        self._current_manager = None
        self._current_mode = None
        
        logger.info(f"ContextManagerFactory initialized with mode: {self.config.default_mode}")
    
    def _get_default_config_path(self) -> str:
        """Get default configuration file path"""
        return str(Path.cwd() / ".orch-state" / "context_config.yaml")
    
    def _load_config(self) -> ContextConfig:
        """Load context management configuration"""
        try:
            if Path(self.config_path).exists():
                config = ContextConfig.from_file(self.config_path)
                logger.info(f"Loaded context configuration from {self.config_path}")
                return config
            else:
                logger.info("No configuration file found, using defaults")
                return ContextConfig()
        except Exception as e:
            logger.warning(f"Failed to load context configuration: {e}, using defaults")
            return ContextConfig()
    
    def save_config(self):
        """Save current configuration to file"""
        try:
            # Ensure directory exists
            config_dir = Path(self.config_path).parent
            config_dir.mkdir(parents=True, exist_ok=True)
            
            self.config.to_file(self.config_path)
            logger.info(f"Context configuration saved to {self.config_path}")
        except Exception as e:
            logger.error(f"Failed to save context configuration: {e}")
    
    async def create_context_manager(
        self,
        project_path: Optional[str] = None,
        mode: Optional[ContextMode] = None,
        **kwargs
    ) -> Union[ContextManager, SimpleContextManager]:
        """
        Create appropriate context manager based on mode and system state.
        
        Args:
            project_path: Path to project root
            mode: Specific mode to use (overrides auto-detection)
            **kwargs: Additional arguments for context manager
            
        Returns:
            Appropriate context manager instance
        """
        with self._lock:
            # Determine mode
            effective_mode = mode or self._detect_mode()
            
            # Check if we can reuse current manager
            if (self._current_manager is not None and 
                self._current_mode == effective_mode and
                not kwargs.get('force_recreate', False)):
                return self._current_manager
            
            # Stop current manager if it exists
            if self._current_manager:
                await self._stop_current_manager()
            
            # Create new manager
            manager = await self._create_manager(effective_mode, project_path, **kwargs)
            
            # Store current manager and mode
            self._current_manager = manager
            self._current_mode = effective_mode
            
            logger.info(f"Created {effective_mode.value} context manager")
            return manager
    
    def _detect_mode(self) -> ContextMode:
        """
        Automatically detect which context mode to use.
        
        Returns:
            Detected context mode
        """
        # Check if mode is explicitly set in config
        if self.config.default_mode != ContextMode.AUTO:
            return self.config.default_mode
        
        # Auto-detection logic
        
        # 1. Check if mock interface is active
        if self._is_mock_interface_active():
            logger.debug("Mock interface detected, using SIMPLE mode")
            return ContextMode.SIMPLE
        
        # 2. Check environment variables for performance mode
        if os.getenv("AGENT_WORKFLOW_PERFORMANCE_MODE", "").lower() in ["true", "1", "on"]:
            logger.debug("Performance mode enabled, using SIMPLE mode")
            return ContextMode.SIMPLE
        
        # 3. Check if running in CI/test environment
        if self._is_ci_environment():
            logger.debug("CI environment detected, using SIMPLE mode")
            return ContextMode.SIMPLE
        
        # 4. Check system resources
        if self._is_low_resource_environment():
            logger.debug("Low resource environment detected, using SIMPLE mode")
            return ContextMode.SIMPLE
        
        # 5. Check if Claude Code is available for fancy mode
        if not self._is_claude_code_available():
            logger.debug("Claude Code not available, using SIMPLE mode")
            return ContextMode.SIMPLE
        
        # Default to fancy mode if all checks pass
        logger.debug("Full features available, using FANCY mode")
        return ContextMode.FANCY
    
    def _is_mock_interface_active(self) -> bool:
        """Check if mock agent interface is currently active"""
        try:
            # Check if the visualizer's interface manager indicates mock mode
            from tools.visualizer.agent_interfaces import interface_manager
            return interface_manager.active_interface == "mock"
        except Exception:
            # If we can't check, assume not mock
            return False
    
    def _is_ci_environment(self) -> bool:
        """Check if running in CI environment"""
        ci_indicators = [
            "CI", "CONTINUOUS_INTEGRATION", "GITHUB_ACTIONS", 
            "TRAVIS", "CIRCLECI", "GITLAB_CI", "JENKINS_URL"
        ]
        return any(os.getenv(var) for var in ci_indicators)
    
    def _is_low_resource_environment(self) -> bool:
        """Check if running in low resource environment"""
        try:
            import psutil
            
            # Check available memory (use simple mode if less than 2GB)
            available_memory = psutil.virtual_memory().available
            if available_memory < 2 * 1024 * 1024 * 1024:  # 2GB
                return True
            
            # Check CPU count (use simple mode if less than 2 cores)
            if psutil.cpu_count() < 2:
                return True
            
            return False
        except ImportError:
            # If psutil not available, assume normal resources
            return False
    
    def _is_claude_code_available(self) -> bool:
        """Check if Claude Code CLI is available for fancy mode"""
        try:
            import subprocess
            result = subprocess.run(
                ["claude-code", "--version"], 
                capture_output=True, 
                timeout=5
            )
            return result.returncode == 0
        except (subprocess.TimeoutExpired, subprocess.CalledProcessError, FileNotFoundError):
            return False
    
    async def _create_manager(
        self,
        mode: ContextMode,
        project_path: Optional[str],
        **kwargs
    ) -> Union[ContextManager, SimpleContextManager]:
        """Create context manager based on mode"""
        # Common arguments
        common_args = {
            "project_path": project_path,
            "max_tokens": kwargs.get("max_tokens", self.config.max_tokens),
        }
        
        if mode == ContextMode.FANCY:
            # Create full-featured context manager
            manager = ContextManager(
                **common_args,
                cache_ttl_seconds=self.config.cache_ttl_seconds,
                enable_intelligence=self.config.enable_intelligence,
                enable_advanced_caching=self.config.enable_advanced_caching,
                enable_monitoring=self.config.enable_monitoring,
                enable_cross_story=self.config.enable_cross_story,
                enable_background_processing=self.config.enable_background_processing,
                **kwargs
            )
            
        elif mode == ContextMode.SIMPLE:
            # Create simple context manager
            manager = SimpleContextManager(
                **common_args,
                max_files=self.config.simple_max_files,
                max_file_size=self.config.simple_max_file_size,
                enable_caching=self.config.simple_enable_caching,
                cache_size=self.config.simple_cache_size,
                **kwargs
            )
        
        else:
            raise ValueError(f"Unknown context mode: {mode}")
        
        # Start the manager
        await manager.start()
        
        return manager
    
    async def _stop_current_manager(self):
        """Stop the current context manager"""
        if self._current_manager:
            try:
                await self._current_manager.stop()
            except Exception as e:
                logger.warning(f"Error stopping current context manager: {e}")
            
            self._current_manager = None
            self._current_mode = None
    
    async def switch_mode(
        self,
        new_mode: ContextMode,
        project_path: Optional[str] = None,
        **kwargs
    ) -> Union[ContextManager, SimpleContextManager]:
        """
        Switch to a different context management mode.
        
        Args:
            new_mode: New mode to switch to
            project_path: Project path (optional)
            **kwargs: Additional arguments
            
        Returns:
            New context manager instance
        """
        logger.info(f"Switching context mode from {self._current_mode} to {new_mode}")
        
        # Update config
        self.config.default_mode = new_mode
        self.save_config()
        
        # Create new manager
        return await self.create_context_manager(
            project_path=project_path,
            mode=new_mode,
            force_recreate=True,
            **kwargs
        )
    
    def get_current_mode(self) -> Optional[ContextMode]:
        """Get currently active context mode"""
        return self._current_mode
    
    def get_current_manager(self) -> Optional[Union[ContextManager, SimpleContextManager]]:
        """Get currently active context manager"""
        return self._current_manager
    
    def get_mode_info(self, mode: Optional[ContextMode] = None) -> Dict[str, Any]:
        """
        Get information about a specific mode or current mode.
        
        Args:
            mode: Mode to get info for (defaults to current mode)
            
        Returns:
            Mode information dictionary
        """
        target_mode = mode or self._current_mode or ContextMode.AUTO
        
        mode_info = {
            ContextMode.FANCY: {
                "name": "Fancy Context Management",
                "description": "Full-featured context processing with intelligence layers",
                "features": [
                    "Intelligent file filtering",
                    "Advanced compression",
                    "Context caching with predictions",
                    "Agent memory integration",
                    "Historical context analysis",
                    "Dependency tracking",
                    "Performance monitoring",
                    "Cross-story management"
                ],
                "performance": "Higher accuracy, more processing time",
                "best_for": ["Production workflows", "Complex projects", "Full AI capabilities"]
            },
            ContextMode.SIMPLE: {
                "name": "Simple Context Management",
                "description": "High-performance context processing with minimal overhead",
                "features": [
                    "Fast file pattern matching",
                    "Simple token-based truncation",
                    "Basic caching",
                    "Minimal processing overhead",
                    "Mock interface compatibility"
                ],
                "performance": "Lower accuracy, minimal processing time",
                "best_for": ["Demo scenarios", "Mock interfaces", "High-frequency operations", "Resource-constrained environments"]
            },
            ContextMode.AUTO: {
                "name": "Automatic Mode Detection",
                "description": "Automatically chooses between fancy and simple based on system state",
                "features": [
                    "Interface detection",
                    "Resource monitoring",
                    "Environment analysis",
                    "Dynamic switching"
                ],
                "performance": "Adaptive based on detected mode",
                "best_for": ["Dynamic environments", "Mixed usage scenarios", "Default configuration"]
            }
        }
        
        return mode_info.get(target_mode, {})
    
    def get_detection_status(self) -> Dict[str, Any]:
        """Get detailed information about mode detection"""
        return {
            "current_mode": self._current_mode.value if self._current_mode else None,
            "configured_mode": self.config.default_mode.value,
            "detection_factors": {
                "mock_interface_active": self._is_mock_interface_active(),
                "performance_mode_env": os.getenv("AGENT_WORKFLOW_PERFORMANCE_MODE", "").lower() in ["true", "1", "on"],
                "ci_environment": self._is_ci_environment(),
                "low_resource_environment": self._is_low_resource_environment(),
                "claude_code_available": self._is_claude_code_available()
            },
            "auto_detected_mode": self._detect_mode().value
        }
    
    async def get_performance_comparison(self) -> Dict[str, Any]:
        """Get performance comparison between modes"""
        if not self._current_manager:
            return {"error": "No active context manager"}
        
        current_metrics = self._current_manager.get_performance_metrics()
        
        return {
            "current_mode": self._current_mode.value if self._current_mode else None,
            "current_metrics": current_metrics,
            "estimated_performance": {
                ContextMode.FANCY.value: {
                    "preparation_time": "2-10 seconds",
                    "memory_usage": "High (100-500MB)",
                    "cpu_usage": "High",
                    "accuracy": "Very High",
                    "features": "Full"
                },
                ContextMode.SIMPLE.value: {
                    "preparation_time": "0.1-1 seconds",
                    "memory_usage": "Low (10-50MB)",
                    "cpu_usage": "Low",
                    "accuracy": "Good",
                    "features": "Basic"
                }
            }
        }
    
    async def cleanup(self):
        """Clean up factory and current manager"""
        await self._stop_current_manager()
        logger.info("ContextManagerFactory cleaned up")


# Global factory instance
_factory_instance = None
_factory_lock = threading.Lock()


def get_context_manager_factory(config_path: Optional[str] = None) -> ContextManagerFactory:
    """
    Get global context manager factory instance.
    
    Args:
        config_path: Optional configuration path
        
    Returns:
        Global factory instance
    """
    global _factory_instance
    
    with _factory_lock:
        if _factory_instance is None:
            _factory_instance = ContextManagerFactory(config_path)
        return _factory_instance


async def create_context_manager(
    project_path: Optional[str] = None,
    mode: Optional[ContextMode] = None,
    **kwargs
) -> Union[ContextManager, SimpleContextManager]:
    """
    Convenience function to create context manager using global factory.
    
    Args:
        project_path: Path to project root
        mode: Specific mode to use
        **kwargs: Additional arguments
        
    Returns:
        Appropriate context manager instance
    """
    factory = get_context_manager_factory()
    return await factory.create_context_manager(
        project_path=project_path,
        mode=mode,
        **kwargs
    )