"""
Comprehensive test coverage for context/exceptions.py module.

Tests cover all exception classes and their methods to achieve 95%+ coverage.
"""

import pytest
from typing import Dict, Any

# Import the module under test
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'lib'))

from context.exceptions import (
    ContextError,
    TokenBudgetExceededError,
    ContextNotFoundError,
    ContextCompressionError,
    AgentMemoryError,
    ContextFilterError,
    ContextIndexError,
    ContextStorageError,
    ContextValidationError,
    ContextTimeoutError,
    ContextCacheError,
    ContextMonitoringError,
    ContextBackgroundError,
    ContextLearningError
)


class TestContextError:
    """Test base ContextError class"""
    
    def test_basic_initialization(self):
        """Test basic ContextError initialization"""
        error = ContextError("Basic error message")
        
        assert str(error) == "Basic error message"
        assert error.context_id is None
        assert error.details == {}
    
    def test_initialization_with_context_id(self):
        """Test ContextError with context_id"""
        error = ContextError("Error with context", context_id="ctx-123")
        
        assert str(error) == "Error with context"
        assert error.context_id == "ctx-123"
        assert error.details == {}
    
    def test_initialization_with_details(self):
        """Test ContextError with details"""
        details = {"component": "test", "operation": "load"}
        error = ContextError("Error with details", details=details)
        
        assert str(error) == "Error with details"
        assert error.context_id is None
        assert error.details == details
    
    def test_initialization_with_all_parameters(self):
        """Test ContextError with all parameters"""
        details = {"error_code": 500, "timestamp": "2023-01-01T00:00:00Z"}
        error = ContextError(
            "Complete error",
            context_id="ctx-456",
            details=details
        )
        
        assert str(error) == "Complete error"
        assert error.context_id == "ctx-456"
        assert error.details == details
    
    def test_inheritance_from_exception(self):
        """Test that ContextError inherits from Exception"""
        error = ContextError("Test")
        
        assert isinstance(error, Exception)
        assert isinstance(error, ContextError)
    
    def test_details_default_to_empty_dict(self):
        """Test that details default to empty dict when None"""
        error = ContextError("Test", details=None)
        
        assert error.details == {}
        assert isinstance(error.details, dict)


class TestTokenBudgetExceededError:
    """Test TokenBudgetExceededError class"""
    
    def test_basic_initialization(self):
        """Test basic TokenBudgetExceededError initialization"""
        error = TokenBudgetExceededError(
            "Token budget exceeded",
            requested_tokens=150000,
            available_tokens=100000
        )
        
        assert str(error) == "Token budget exceeded"
        assert error.requested_tokens == 150000
        assert error.available_tokens == 100000
        assert error.context_id is None
        assert error.details == {}
    
    def test_initialization_with_kwargs(self):
        """Test TokenBudgetExceededError with additional kwargs"""
        error = TokenBudgetExceededError(
            "Budget exceeded in context preparation",
            requested_tokens=200000,
            available_tokens=180000,
            context_id="ctx-789",
            details={"agent": "code_agent", "story": "story-123"}
        )
        
        assert str(error) == "Budget exceeded in context preparation"
        assert error.requested_tokens == 200000
        assert error.available_tokens == 180000
        assert error.context_id == "ctx-789"
        assert error.details["agent"] == "code_agent"
    
    def test_inheritance_from_context_error(self):
        """Test that TokenBudgetExceededError inherits from ContextError"""
        error = TokenBudgetExceededError("Test", 1000, 500)
        
        assert isinstance(error, ContextError)
        assert isinstance(error, TokenBudgetExceededError)
    
    def test_token_values_preserved(self):
        """Test that token values are preserved correctly"""
        error = TokenBudgetExceededError(
            "Token test",
            requested_tokens=75000,
            available_tokens=50000
        )
        
        # Values should be exactly as provided
        assert error.requested_tokens == 75000
        assert error.available_tokens == 50000
        
        # Should handle zero values
        error_zero = TokenBudgetExceededError("Zero test", 0, 0)
        assert error_zero.requested_tokens == 0
        assert error_zero.available_tokens == 0


class TestContextNotFoundError:
    """Test ContextNotFoundError class"""
    
    def test_basic_initialization(self):
        """Test basic ContextNotFoundError initialization"""
        error = ContextNotFoundError("Context not found")
        
        assert str(error) == "Context not found"
        assert isinstance(error, ContextError)
    
    def test_initialization_with_parameters(self):
        """Test ContextNotFoundError with parameters"""
        error = ContextNotFoundError(
            "Context not found for story",
            context_id="missing-ctx",
            details={"story_id": "story-404", "agent": "design_agent"}
        )
        
        assert str(error) == "Context not found for story"
        assert error.context_id == "missing-ctx"
        assert error.details["story_id"] == "story-404"
    
    def test_simple_inheritance(self):
        """Test that ContextNotFoundError is a simple ContextError subclass"""
        error = ContextNotFoundError("Test")
        
        assert isinstance(error, ContextError)
        assert isinstance(error, ContextNotFoundError)
        assert hasattr(error, 'context_id')
        assert hasattr(error, 'details')


class TestContextCompressionError:
    """Test ContextCompressionError class"""
    
    def test_basic_initialization(self):
        """Test basic ContextCompressionError initialization"""
        error = ContextCompressionError(
            "Compression failed",
            original_size=100000,
            target_size=50000
        )
        
        assert str(error) == "Compression failed"
        assert error.original_size == 100000
        assert error.target_size == 50000
        assert error.context_id is None
    
    def test_initialization_with_kwargs(self):
        """Test ContextCompressionError with additional kwargs"""
        error = ContextCompressionError(
            "Failed to compress context to target size",
            original_size=200000,
            target_size=100000,
            context_id="comp-ctx",
            details={"compression_ratio": 0.5, "method": "smart_truncation"}
        )
        
        assert str(error) == "Failed to compress context to target size"
        assert error.original_size == 200000
        assert error.target_size == 100000
        assert error.context_id == "comp-ctx"
        assert error.details["compression_ratio"] == 0.5
        assert error.details["method"] == "smart_truncation"
    
    def test_size_values_handling(self):
        """Test size values handling in ContextCompressionError"""
        # Test with large numbers
        error = ContextCompressionError(
            "Large compression",
            original_size=1000000,
            target_size=250000
        )
        assert error.original_size == 1000000
        assert error.target_size == 250000
        
        # Test with zero values
        error_zero = ContextCompressionError("Zero compression", 0, 0)
        assert error_zero.original_size == 0
        assert error_zero.target_size == 0
    
    def test_inheritance_properties(self):
        """Test inheritance and property access"""
        error = ContextCompressionError("Test", 1000, 500)
        
        assert isinstance(error, ContextError)
        assert hasattr(error, 'original_size')
        assert hasattr(error, 'target_size')
        assert hasattr(error, 'context_id')
        assert hasattr(error, 'details')


class TestAgentMemoryError:
    """Test AgentMemoryError class"""
    
    def test_basic_initialization(self):
        """Test basic AgentMemoryError initialization"""
        error = AgentMemoryError(
            "Memory operation failed",
            agent_type="code_agent"
        )
        
        assert str(error) == "Memory operation failed"
        assert error.agent_type == "code_agent"
        assert error.story_id is None
        assert error.context_id is None
    
    def test_initialization_with_story_id(self):
        """Test AgentMemoryError with story_id"""
        error = AgentMemoryError(
            "Failed to store agent memory",
            agent_type="design_agent",
            story_id="story-456"
        )
        
        assert str(error) == "Failed to store agent memory"
        assert error.agent_type == "design_agent"
        assert error.story_id == "story-456"
    
    def test_initialization_with_all_parameters(self):
        """Test AgentMemoryError with all parameters"""
        error = AgentMemoryError(
            "Memory corruption detected",
            agent_type="qa_agent",
            story_id="story-789",
            context_id="mem-ctx",
            details={"operation": "store", "corruption_type": "json_parse_error"}
        )
        
        assert str(error) == "Memory corruption detected"
        assert error.agent_type == "qa_agent"
        assert error.story_id == "story-789"
        assert error.context_id == "mem-ctx"
        assert error.details["operation"] == "store"
        assert error.details["corruption_type"] == "json_parse_error"
    
    def test_agent_type_required(self):
        """Test that agent_type is required and preserved"""
        error = AgentMemoryError("Test", agent_type="test_agent")
        
        assert error.agent_type == "test_agent"
        assert isinstance(error, ContextError)
    
    def test_story_id_optional(self):
        """Test that story_id is optional"""
        error = AgentMemoryError("Test", agent_type="test_agent", story_id=None)
        
        assert error.agent_type == "test_agent"
        assert error.story_id is None


class TestContextFilterError:
    """Test ContextFilterError class"""
    
    def test_basic_initialization(self):
        """Test basic ContextFilterError initialization"""
        error = ContextFilterError("Filter operation failed")
        
        assert str(error) == "Filter operation failed"
        assert isinstance(error, ContextError)
        assert hasattr(error, 'context_id')
        assert hasattr(error, 'details')
    
    def test_initialization_with_parameters(self):
        """Test ContextFilterError with parameters"""
        error = ContextFilterError(
            "Failed to apply relevance filter",
            context_id="filter-ctx",
            details={"filter_type": "relevance", "threshold": 0.5}
        )
        
        assert str(error) == "Failed to apply relevance filter"
        assert error.context_id == "filter-ctx"
        assert error.details["filter_type"] == "relevance"
        assert error.details["threshold"] == 0.5
    
    def test_simple_subclass_behavior(self):
        """Test that ContextFilterError behaves as simple ContextError subclass"""
        error = ContextFilterError("Test filter error")
        
        assert isinstance(error, ContextError)
        assert type(error).__name__ == "ContextFilterError"


class TestContextIndexError:
    """Test ContextIndexError class"""
    
    def test_basic_initialization(self):
        """Test basic ContextIndexError initialization"""
        error = ContextIndexError("Index operation failed")
        
        assert str(error) == "Index operation failed"
        assert error.index_path is None
        assert error.context_id is None
    
    def test_initialization_with_index_path(self):
        """Test ContextIndexError with index_path"""
        error = ContextIndexError(
            "Failed to build index",
            index_path="/path/to/index"
        )
        
        assert str(error) == "Failed to build index"
        assert error.index_path == "/path/to/index"
    
    def test_initialization_with_all_parameters(self):
        """Test ContextIndexError with all parameters"""
        error = ContextIndexError(
            "Index corruption detected",
            index_path="/corrupted/index",
            context_id="idx-ctx",
            details={"index_type": "vector", "corruption_level": "severe"}
        )
        
        assert str(error) == "Index corruption detected"
        assert error.index_path == "/corrupted/index"
        assert error.context_id == "idx-ctx"
        assert error.details["index_type"] == "vector"
        assert error.details["corruption_level"] == "severe"
    
    def test_index_path_optional(self):
        """Test that index_path is optional"""
        error = ContextIndexError("Test", index_path=None)
        
        assert error.index_path is None
        assert isinstance(error, ContextError)
    
    def test_inheritance_and_attributes(self):
        """Test inheritance and attribute presence"""
        error = ContextIndexError("Test")
        
        assert isinstance(error, ContextError)
        assert hasattr(error, 'index_path')
        assert hasattr(error, 'context_id')
        assert hasattr(error, 'details')


class TestContextStorageError:
    """Test ContextStorageError class"""
    
    def test_basic_initialization(self):
        """Test basic ContextStorageError initialization"""
        error = ContextStorageError("Storage operation failed")
        
        assert str(error) == "Storage operation failed"
        assert error.storage_path is None
        assert error.context_id is None
    
    def test_initialization_with_storage_path(self):
        """Test ContextStorageError with storage_path"""
        error = ContextStorageError(
            "Failed to write to storage",
            storage_path="/storage/path"
        )
        
        assert str(error) == "Failed to write to storage"
        assert error.storage_path == "/storage/path"
    
    def test_initialization_with_all_parameters(self):
        """Test ContextStorageError with all parameters"""
        error = ContextStorageError(
            "Storage quota exceeded",
            storage_path="/full/storage",
            context_id="storage-ctx",
            details={"quota_limit": "100GB", "current_usage": "105GB"}
        )
        
        assert str(error) == "Storage quota exceeded"
        assert error.storage_path == "/full/storage"
        assert error.context_id == "storage-ctx"
        assert error.details["quota_limit"] == "100GB"
        assert error.details["current_usage"] == "105GB"
    
    def test_storage_path_handling(self):
        """Test storage path handling"""
        # Test with various path formats
        error1 = ContextStorageError("Test", storage_path="/unix/path")
        assert error1.storage_path == "/unix/path"
        
        error2 = ContextStorageError("Test", storage_path="C:\\Windows\\Path")
        assert error2.storage_path == "C:\\Windows\\Path"
        
        error3 = ContextStorageError("Test", storage_path="")
        assert error3.storage_path == ""
    
    def test_storage_error_inheritance(self):
        """Test ContextStorageError inheritance"""
        error = ContextStorageError("Test")
        
        assert isinstance(error, ContextError)
        assert hasattr(error, 'storage_path')


class TestContextValidationError:
    """Test ContextValidationError class"""
    
    def test_basic_initialization(self):
        """Test basic ContextValidationError initialization"""
        error = ContextValidationError("Validation failed")
        
        assert str(error) == "Validation failed"
        assert error.validation_errors == []
        assert error.context_id is None
    
    def test_initialization_with_validation_errors(self):
        """Test ContextValidationError with validation_errors"""
        validation_errors = [
            "Field 'agent_type' is required",
            "Field 'story_id' must be non-empty",
            "Field 'max_tokens' must be positive"
        ]
        
        error = ContextValidationError(
            "Multiple validation errors",
            validation_errors=validation_errors
        )
        
        assert str(error) == "Multiple validation errors"
        assert error.validation_errors == validation_errors
        assert len(error.validation_errors) == 3
    
    def test_initialization_with_all_parameters(self):
        """Test ContextValidationError with all parameters"""
        validation_errors = ["Invalid context format"]
        
        error = ContextValidationError(
            "Context validation failed",
            validation_errors=validation_errors,
            context_id="val-ctx",
            details={"validator": "schema_validator", "schema_version": "1.0"}
        )
        
        assert str(error) == "Context validation failed"
        assert error.validation_errors == validation_errors
        assert error.context_id == "val-ctx"
        assert error.details["validator"] == "schema_validator"
    
    def test_validation_errors_default(self):
        """Test that validation_errors defaults to empty list"""
        error = ContextValidationError("Test", validation_errors=None)
        
        assert error.validation_errors == []
        assert isinstance(error.validation_errors, list)
    
    def test_validation_errors_list_handling(self):
        """Test validation errors list handling"""
        # Test with empty list
        error1 = ContextValidationError("Test", validation_errors=[])
        assert error1.validation_errors == []
        
        # Test with single error
        error2 = ContextValidationError("Test", validation_errors=["Single error"])
        assert len(error2.validation_errors) == 1
        assert error2.validation_errors[0] == "Single error"
        
        # Test with multiple errors
        errors = ["Error 1", "Error 2", "Error 3"]
        error3 = ContextValidationError("Test", validation_errors=errors)
        assert error3.validation_errors == errors
    
    def test_validation_error_inheritance(self):
        """Test ContextValidationError inheritance"""
        error = ContextValidationError("Test")
        
        assert isinstance(error, ContextError)
        assert hasattr(error, 'validation_errors')


class TestContextTimeoutError:
    """Test ContextTimeoutError class"""
    
    def test_basic_initialization(self):
        """Test basic ContextTimeoutError initialization"""
        error = ContextTimeoutError(
            "Operation timed out",
            operation="context_preparation",
            timeout_seconds=30.0
        )
        
        assert str(error) == "Operation timed out"
        assert error.operation == "context_preparation"
        assert error.timeout_seconds == 30.0
        assert error.context_id is None
    
    def test_initialization_with_all_parameters(self):
        """Test ContextTimeoutError with all parameters"""
        error = ContextTimeoutError(
            "Context loading timed out",
            operation="context_load",
            timeout_seconds=60.5,
            context_id="timeout-ctx",
            details={"started_at": "2023-01-01T10:00:00Z", "method": "file_load"}
        )
        
        assert str(error) == "Context loading timed out"
        assert error.operation == "context_load"
        assert error.timeout_seconds == 60.5
        assert error.context_id == "timeout-ctx"
        assert error.details["started_at"] == "2023-01-01T10:00:00Z"
        assert error.details["method"] == "file_load"
    
    def test_timeout_values_handling(self):
        """Test timeout values handling"""
        # Test with integer timeout
        error1 = ContextTimeoutError("Test", "op", 30)
        assert error1.timeout_seconds == 30
        
        # Test with float timeout
        error2 = ContextTimeoutError("Test", "op", 30.5)
        assert error2.timeout_seconds == 30.5
        
        # Test with zero timeout
        error3 = ContextTimeoutError("Test", "op", 0.0)
        assert error3.timeout_seconds == 0.0
    
    def test_operation_name_preservation(self):
        """Test that operation name is preserved correctly"""
        operations = [
            "context_preparation",
            "file_loading",
            "compression",
            "cache_warming",
            "background_processing"
        ]
        
        for op in operations:
            error = ContextTimeoutError("Test", op, 10.0)
            assert error.operation == op
    
    def test_timeout_error_inheritance(self):
        """Test ContextTimeoutError inheritance"""
        error = ContextTimeoutError("Test", "op", 1.0)
        
        assert isinstance(error, ContextError)
        assert hasattr(error, 'operation')
        assert hasattr(error, 'timeout_seconds')


class TestContextCacheError:
    """Test ContextCacheError class"""
    
    def test_basic_initialization(self):
        """Test basic ContextCacheError initialization"""
        error = ContextCacheError("Cache operation failed")
        
        assert str(error) == "Cache operation failed"
        assert error.cache_key is None
        assert error.context_id is None
    
    def test_initialization_with_cache_key(self):
        """Test ContextCacheError with cache_key"""
        error = ContextCacheError(
            "Cache miss for key",
            cache_key="cache-key-123"
        )
        
        assert str(error) == "Cache miss for key"
        assert error.cache_key == "cache-key-123"
    
    def test_initialization_with_all_parameters(self):
        """Test ContextCacheError with all parameters"""
        error = ContextCacheError(
            "Cache eviction failed",
            cache_key="evict-key",
            context_id="cache-ctx",
            details={"eviction_strategy": "LRU", "cache_size": "100MB"}
        )
        
        assert str(error) == "Cache eviction failed"
        assert error.cache_key == "evict-key"
        assert error.context_id == "cache-ctx"
        assert error.details["eviction_strategy"] == "LRU"
        assert error.details["cache_size"] == "100MB"
    
    def test_cache_key_handling(self):
        """Test cache key handling"""
        # Test with various key formats
        keys = [
            "simple-key",
            "key_with_underscores",
            "key-with-dashes",
            "KeyWithCamelCase",
            "key123with456numbers",
            "",  # Empty key
            "very-long-key-name-that-might-be-generated-by-hash-function-12345"
        ]
        
        for key in keys:
            error = ContextCacheError("Test", cache_key=key)
            assert error.cache_key == key
    
    def test_cache_error_inheritance(self):
        """Test ContextCacheError inheritance"""
        error = ContextCacheError("Test")
        
        assert isinstance(error, ContextError)
        assert hasattr(error, 'cache_key')


class TestContextMonitoringError:
    """Test ContextMonitoringError class"""
    
    def test_basic_initialization(self):
        """Test basic ContextMonitoringError initialization"""
        error = ContextMonitoringError("Monitoring operation failed")
        
        assert str(error) == "Monitoring operation failed"
        assert error.metric_type is None
        assert error.context_id is None
    
    def test_initialization_with_metric_type(self):
        """Test ContextMonitoringError with metric_type"""
        error = ContextMonitoringError(
            "Failed to record metric",
            metric_type="performance"
        )
        
        assert str(error) == "Failed to record metric"
        assert error.metric_type == "performance"
    
    def test_initialization_with_all_parameters(self):
        """Test ContextMonitoringError with all parameters"""
        error = ContextMonitoringError(
            "Alert evaluation failed",
            metric_type="alert",
            context_id="mon-ctx",
            details={"alert_id": "high_memory", "severity": "critical"}
        )
        
        assert str(error) == "Alert evaluation failed"
        assert error.metric_type == "alert"
        assert error.context_id == "mon-ctx"
        assert error.details["alert_id"] == "high_memory"
        assert error.details["severity"] == "critical"
    
    def test_metric_type_values(self):
        """Test various metric type values"""
        metric_types = [
            "counter",
            "gauge",
            "histogram",
            "timer",
            "alert",
            "target",
            "health"
        ]
        
        for metric_type in metric_types:
            error = ContextMonitoringError("Test", metric_type=metric_type)
            assert error.metric_type == metric_type
    
    def test_monitoring_error_inheritance(self):
        """Test ContextMonitoringError inheritance"""
        error = ContextMonitoringError("Test")
        
        assert isinstance(error, ContextError)
        assert hasattr(error, 'metric_type')


class TestContextBackgroundError:
    """Test ContextBackgroundError class"""
    
    def test_basic_initialization(self):
        """Test basic ContextBackgroundError initialization"""
        error = ContextBackgroundError("Background task failed")
        
        assert str(error) == "Background task failed"
        assert error.task_id is None
        assert error.context_id is None
    
    def test_initialization_with_task_id(self):
        """Test ContextBackgroundError with task_id"""
        error = ContextBackgroundError(
            "Background processing failed",
            task_id="bg-task-123"
        )
        
        assert str(error) == "Background processing failed"
        assert error.task_id == "bg-task-123"
    
    def test_initialization_with_all_parameters(self):
        """Test ContextBackgroundError with all parameters"""
        error = ContextBackgroundError(
            "Cache warming task crashed",
            task_id="cache-warm-456",
            context_id="bg-ctx",
            details={"task_type": "cache_warming", "retry_count": 3}
        )
        
        assert str(error) == "Cache warming task crashed"
        assert error.task_id == "cache-warm-456"
        assert error.context_id == "bg-ctx"
        assert error.details["task_type"] == "cache_warming"
        assert error.details["retry_count"] == 3
    
    def test_task_id_formats(self):
        """Test various task ID formats"""
        task_ids = [
            "simple-task",
            "task_123",
            "TASK-UUID-4567-8910",
            "background.task.name",
            "",  # Empty task ID
            "very-long-task-identifier-with-many-parts-and-numbers-123456789"
        ]
        
        for task_id in task_ids:
            error = ContextBackgroundError("Test", task_id=task_id)
            assert error.task_id == task_id
    
    def test_background_error_inheritance(self):
        """Test ContextBackgroundError inheritance"""
        error = ContextBackgroundError("Test")
        
        assert isinstance(error, ContextError)
        assert hasattr(error, 'task_id')


class TestContextLearningError:
    """Test ContextLearningError class"""
    
    def test_basic_initialization(self):
        """Test basic ContextLearningError initialization"""
        error = ContextLearningError("Learning operation failed")
        
        assert str(error) == "Learning operation failed"
        assert error.learning_type is None
        assert error.context_id is None
    
    def test_initialization_with_learning_type(self):
        """Test ContextLearningError with learning_type"""
        error = ContextLearningError(
            "Pattern learning failed",
            learning_type="pattern_detection"
        )
        
        assert str(error) == "Pattern learning failed"
        assert error.learning_type == "pattern_detection"
    
    def test_initialization_with_all_parameters(self):
        """Test ContextLearningError with all parameters"""
        error = ContextLearningError(
            "Model training failed",
            learning_type="neural_network",
            context_id="learn-ctx",
            details={"model_type": "transformer", "epoch": 5, "loss": "high"}
        )
        
        assert str(error) == "Model training failed"
        assert error.learning_type == "neural_network"
        assert error.context_id == "learn-ctx"
        assert error.details["model_type"] == "transformer"
        assert error.details["epoch"] == 5
        assert error.details["loss"] == "high"
    
    def test_learning_type_values(self):
        """Test various learning type values"""
        learning_types = [
            "pattern_detection",
            "neural_network",
            "reinforcement_learning",
            "supervised_learning",
            "unsupervised_learning",
            "transfer_learning",
            "meta_learning"
        ]
        
        for learning_type in learning_types:
            error = ContextLearningError("Test", learning_type=learning_type)
            assert error.learning_type == learning_type
    
    def test_learning_error_inheritance(self):
        """Test ContextLearningError inheritance"""
        error = ContextLearningError("Test")
        
        assert isinstance(error, ContextError)
        assert hasattr(error, 'learning_type')


class TestExceptionHierarchy:
    """Test exception hierarchy and inheritance"""
    
    def test_all_exceptions_inherit_from_context_error(self):
        """Test that all context exceptions inherit from ContextError"""
        exception_classes = [
            TokenBudgetExceededError,
            ContextNotFoundError,
            ContextCompressionError,
            AgentMemoryError,
            ContextFilterError,
            ContextIndexError,
            ContextStorageError,
            ContextValidationError,
            ContextTimeoutError,
            ContextCacheError,
            ContextMonitoringError,
            ContextBackgroundError,
            ContextLearningError
        ]
        
        for exc_class in exception_classes:
            # Create minimal instance for each exception type
            if exc_class == TokenBudgetExceededError:
                instance = exc_class("Test", 1000, 500)
            elif exc_class == ContextCompressionError:
                instance = exc_class("Test", 1000, 500)
            elif exc_class == AgentMemoryError:
                instance = exc_class("Test", "agent")
            elif exc_class == ContextIndexError:
                instance = exc_class("Test")
            elif exc_class == ContextStorageError:
                instance = exc_class("Test")
            elif exc_class == ContextValidationError:
                instance = exc_class("Test")
            elif exc_class == ContextTimeoutError:
                instance = exc_class("Test", "op", 1.0)
            elif exc_class == ContextCacheError:
                instance = exc_class("Test")
            elif exc_class == ContextMonitoringError:
                instance = exc_class("Test")
            elif exc_class == ContextBackgroundError:
                instance = exc_class("Test")
            elif exc_class == ContextLearningError:
                instance = exc_class("Test")
            else:
                instance = exc_class("Test")
            
            assert isinstance(instance, ContextError)
            assert isinstance(instance, Exception)
    
    def test_exception_can_be_raised_and_caught(self):
        """Test that exceptions can be raised and caught properly"""
        # Test base ContextError
        with pytest.raises(ContextError) as exc_info:
            raise ContextError("Test context error")
        assert str(exc_info.value) == "Test context error"
        
        # Test specific exception
        with pytest.raises(TokenBudgetExceededError) as exc_info:
            raise TokenBudgetExceededError("Token test", 1000, 500)
        assert exc_info.value.requested_tokens == 1000
        
        # Test catching specific exception as base exception
        with pytest.raises(ContextError) as exc_info:
            raise ContextNotFoundError("Not found test")
        assert isinstance(exc_info.value, ContextNotFoundError)
    
    def test_exception_chaining(self):
        """Test exception chaining support"""
        try:
            try:
                raise ValueError("Original error")
            except ValueError as e:
                raise ContextError("Context error") from e
        except ContextError as context_err:
            assert isinstance(context_err.__cause__, ValueError)
            assert str(context_err.__cause__) == "Original error"
    
    def test_exception_attributes_preserved_through_inheritance(self):
        """Test that base attributes are preserved in subclasses"""
        # Test with complex subclass
        error = TokenBudgetExceededError(
            "Token error",
            requested_tokens=1000,
            available_tokens=500,
            context_id="test-ctx",
            details={"component": "test"}
        )
        
        # Base ContextError attributes should be preserved
        assert hasattr(error, 'context_id')
        assert hasattr(error, 'details')
        assert error.context_id == "test-ctx"
        assert error.details["component"] == "test"
        
        # Subclass-specific attributes should also be present
        assert hasattr(error, 'requested_tokens')
        assert hasattr(error, 'available_tokens')
        assert error.requested_tokens == 1000
        assert error.available_tokens == 500


class TestExceptionUsagePatterns:
    """Test common exception usage patterns"""
    
    def test_exception_with_context_information(self):
        """Test exceptions used with rich context information"""
        details = {
            "timestamp": "2023-01-01T12:00:00Z",
            "user_id": "user-123",
            "operation": "context_preparation",
            "file_count": 15,
            "token_estimate": 125000
        }
        
        error = ContextError(
            "Context preparation failed due to token limit",
            context_id="prep-ctx-456",
            details=details
        )
        
        assert error.details["timestamp"] == "2023-01-01T12:00:00Z"
        assert error.details["user_id"] == "user-123"
        assert error.details["file_count"] == 15
        assert error.context_id == "prep-ctx-456"
    
    def test_exception_serialization_compatibility(self):
        """Test that exceptions work with common serialization patterns"""
        error = ContextValidationError(
            "Validation failed",
            validation_errors=["Field missing", "Invalid format"],
            context_id="val-123",
            details={"schema_version": "1.0"}
        )
        
        # Test that we can access all attributes needed for serialization
        error_dict = {
            "type": type(error).__name__,
            "message": str(error),
            "context_id": error.context_id,
            "details": error.details,
            "validation_errors": error.validation_errors
        }
        
        assert error_dict["type"] == "ContextValidationError"
        assert error_dict["message"] == "Validation failed"
        assert error_dict["context_id"] == "val-123"
        assert error_dict["validation_errors"] == ["Field missing", "Invalid format"]
    
    def test_exception_debugging_information(self):
        """Test that exceptions provide good debugging information"""
        error = ContextTimeoutError(
            "Operation timed out after 30 seconds",
            operation="file_loading",
            timeout_seconds=30.0,
            context_id="timeout-ctx",
            details={
                "file_path": "/path/to/large/file.txt",
                "file_size_mb": 500,
                "start_time": "2023-01-01T10:00:00Z"
            }
        )
        
        # Should have all information needed for debugging
        debug_info = {
            "error_type": type(error).__name__,
            "message": str(error),
            "operation": error.operation,
            "timeout": error.timeout_seconds,
            "context": error.context_id,
            "file_info": {
                "path": error.details.get("file_path"),
                "size": error.details.get("file_size_mb"),
                "start": error.details.get("start_time")
            }
        }
        
        assert debug_info["operation"] == "file_loading"
        assert debug_info["timeout"] == 30.0
        assert debug_info["file_info"]["path"] == "/path/to/large/file.txt"
        assert debug_info["file_info"]["size"] == 500


if __name__ == "__main__":
    pytest.main([__file__, "-v"])