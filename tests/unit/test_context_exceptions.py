"""
Comprehensive test suite for Context Management System Exceptions.

Tests all custom exception classes and their behavior including error handling,
metadata preservation, and inheritance relationships.
"""

import pytest
from datetime import datetime
from typing import Dict, Any

# Import the modules under test
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "lib"))

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
    
    def test_basic_creation(self):
        """Test basic exception creation"""
        error = ContextError("Test error message")
        
        assert str(error) == "Test error message"
        assert error.context_id is None
        assert error.details == {}
    
    def test_creation_with_context_id(self):
        """Test exception creation with context ID"""
        error = ContextError("Test error", context_id="ctx_123")
        
        assert str(error) == "Test error"
        assert error.context_id == "ctx_123"
        assert error.details == {}
    
    def test_creation_with_details(self):
        """Test exception creation with details"""
        details = {"key1": "value1", "key2": 42}
        error = ContextError("Test error", details=details)
        
        assert str(error) == "Test error"
        assert error.context_id is None
        assert error.details == details
    
    def test_creation_with_all_params(self):
        """Test exception creation with all parameters"""
        details = {"error_code": "E001", "timestamp": "2023-01-01T00:00:00"}
        error = ContextError("Test error", context_id="ctx_456", details=details)
        
        assert str(error) == "Test error"
        assert error.context_id == "ctx_456"
        assert error.details == details
    
    def test_inheritance(self):
        """Test that ContextError inherits from Exception"""
        error = ContextError("Test error")
        assert isinstance(error, Exception)


class TestTokenBudgetExceededError:
    """Test TokenBudgetExceededError class"""
    
    def test_basic_creation(self):
        """Test basic exception creation"""
        error = TokenBudgetExceededError(
            "Budget exceeded",
            requested_tokens=150000,
            available_tokens=100000
        )
        
        assert str(error) == "Budget exceeded"
        assert error.requested_tokens == 150000
        assert error.available_tokens == 100000
        assert error.context_id is None
        assert error.details == {}
    
    def test_creation_with_optional_params(self):
        """Test creation with optional parameters"""
        error = TokenBudgetExceededError(
            "Budget exceeded",
            requested_tokens=150000,
            available_tokens=100000,
            context_id="ctx_789",
            details={"agent_type": "CodeAgent"}
        )
        
        assert str(error) == "Budget exceeded"
        assert error.requested_tokens == 150000
        assert error.available_tokens == 100000
        assert error.context_id == "ctx_789"
        assert error.details == {"agent_type": "CodeAgent"}
    
    def test_inheritance(self):
        """Test inheritance from ContextError"""
        error = TokenBudgetExceededError("Test", 1000, 500)
        assert isinstance(error, ContextError)
        assert isinstance(error, Exception)


class TestContextNotFoundError:
    """Test ContextNotFoundError class"""
    
    def test_basic_creation(self):
        """Test basic exception creation"""
        error = ContextNotFoundError("Context not found")
        
        assert str(error) == "Context not found"
        assert error.context_id is None
        assert error.details == {}
    
    def test_inheritance(self):
        """Test inheritance from ContextError"""
        error = ContextNotFoundError("Test")
        assert isinstance(error, ContextError)
        assert isinstance(error, Exception)


class TestContextCompressionError:
    """Test ContextCompressionError class"""
    
    def test_basic_creation(self):
        """Test basic exception creation"""
        error = ContextCompressionError(
            "Compression failed",
            original_size=100000,
            target_size=50000
        )
        
        assert str(error) == "Compression failed"
        assert error.original_size == 100000
        assert error.target_size == 50000
        assert error.context_id is None
        assert error.details == {}
    
    def test_creation_with_optional_params(self):
        """Test creation with optional parameters"""
        error = ContextCompressionError(
            "Compression failed",
            original_size=100000,
            target_size=50000,
            context_id="ctx_comp",
            details={"compression_ratio": 0.5}
        )
        
        assert str(error) == "Compression failed"
        assert error.original_size == 100000
        assert error.target_size == 50000
        assert error.context_id == "ctx_comp"
        assert error.details == {"compression_ratio": 0.5}
    
    def test_inheritance(self):
        """Test inheritance from ContextError"""
        error = ContextCompressionError("Test", 1000, 500)
        assert isinstance(error, ContextError)


class TestAgentMemoryError:
    """Test AgentMemoryError class"""
    
    def test_basic_creation(self):
        """Test basic exception creation"""
        error = AgentMemoryError("Memory error", agent_type="CodeAgent")
        
        assert str(error) == "Memory error"
        assert error.agent_type == "CodeAgent"
        assert error.story_id is None
        assert error.context_id is None
        assert error.details == {}
    
    def test_creation_with_story_id(self):
        """Test creation with story ID"""
        error = AgentMemoryError(
            "Memory error",
            agent_type="QAAgent",
            story_id="story_123"
        )
        
        assert str(error) == "Memory error"
        assert error.agent_type == "QAAgent"
        assert error.story_id == "story_123"
    
    def test_creation_with_all_params(self):
        """Test creation with all parameters"""
        error = AgentMemoryError(
            "Memory error",
            agent_type="DesignAgent",
            story_id="story_456",
            context_id="ctx_mem",
            details={"operation": "store"}
        )
        
        assert str(error) == "Memory error"
        assert error.agent_type == "DesignAgent"
        assert error.story_id == "story_456"
        assert error.context_id == "ctx_mem"
        assert error.details == {"operation": "store"}
    
    def test_inheritance(self):
        """Test inheritance from ContextError"""
        error = AgentMemoryError("Test", "Agent")
        assert isinstance(error, ContextError)


class TestContextFilterError:
    """Test ContextFilterError class"""
    
    def test_basic_creation(self):
        """Test basic exception creation"""
        error = ContextFilterError("Filter error")
        
        assert str(error) == "Filter error"
        assert error.context_id is None
        assert error.details == {}
    
    def test_inheritance(self):
        """Test inheritance from ContextError"""
        error = ContextFilterError("Test")
        assert isinstance(error, ContextError)


class TestContextIndexError:
    """Test ContextIndexError class"""
    
    def test_basic_creation(self):
        """Test basic exception creation"""
        error = ContextIndexError("Index error")
        
        assert str(error) == "Index error"
        assert error.index_path is None
        assert error.context_id is None
        assert error.details == {}
    
    def test_creation_with_index_path(self):
        """Test creation with index path"""
        error = ContextIndexError("Index error", index_path="/path/to/index")
        
        assert str(error) == "Index error"
        assert error.index_path == "/path/to/index"
    
    def test_creation_with_all_params(self):
        """Test creation with all parameters"""
        error = ContextIndexError(
            "Index error",
            index_path="/path/to/index",
            context_id="ctx_idx",
            details={"operation": "build"}
        )
        
        assert str(error) == "Index error"
        assert error.index_path == "/path/to/index"
        assert error.context_id == "ctx_idx"
        assert error.details == {"operation": "build"}
    
    def test_inheritance(self):
        """Test inheritance from ContextError"""
        error = ContextIndexError("Test")
        assert isinstance(error, ContextError)


class TestContextStorageError:
    """Test ContextStorageError class"""
    
    def test_basic_creation(self):
        """Test basic exception creation"""
        error = ContextStorageError("Storage error")
        
        assert str(error) == "Storage error"
        assert error.storage_path is None
        assert error.context_id is None
        assert error.details == {}
    
    def test_creation_with_storage_path(self):
        """Test creation with storage path"""
        error = ContextStorageError("Storage error", storage_path="/path/to/storage")
        
        assert str(error) == "Storage error"
        assert error.storage_path == "/path/to/storage"
    
    def test_inheritance(self):
        """Test inheritance from ContextError"""
        error = ContextStorageError("Test")
        assert isinstance(error, ContextError)


class TestContextValidationError:
    """Test ContextValidationError class"""
    
    def test_basic_creation(self):
        """Test basic exception creation"""
        error = ContextValidationError("Validation error")
        
        assert str(error) == "Validation error"
        assert error.validation_errors == []
        assert error.context_id is None
        assert error.details == {}
    
    def test_creation_with_validation_errors(self):
        """Test creation with validation errors"""
        validation_errors = ["Error 1", "Error 2", "Error 3"]
        error = ContextValidationError(
            "Validation failed",
            validation_errors=validation_errors
        )
        
        assert str(error) == "Validation failed"
        assert error.validation_errors == validation_errors
    
    def test_creation_with_all_params(self):
        """Test creation with all parameters"""
        validation_errors = ["Missing field", "Invalid type"]
        error = ContextValidationError(
            "Validation failed",
            validation_errors=validation_errors,
            context_id="ctx_val",
            details={"field": "test_field"}
        )
        
        assert str(error) == "Validation failed"
        assert error.validation_errors == validation_errors
        assert error.context_id == "ctx_val"
        assert error.details == {"field": "test_field"}
    
    def test_inheritance(self):
        """Test inheritance from ContextError"""
        error = ContextValidationError("Test")
        assert isinstance(error, ContextError)


class TestContextTimeoutError:
    """Test ContextTimeoutError class"""
    
    def test_basic_creation(self):
        """Test basic exception creation"""
        error = ContextTimeoutError(
            "Operation timed out",
            operation="context_preparation",
            timeout_seconds=30.0
        )
        
        assert str(error) == "Operation timed out"
        assert error.operation == "context_preparation"
        assert error.timeout_seconds == 30.0
        assert error.context_id is None
        assert error.details == {}
    
    def test_creation_with_all_params(self):
        """Test creation with all parameters"""
        error = ContextTimeoutError(
            "Operation timed out",
            operation="context_preparation",
            timeout_seconds=30.0,
            context_id="ctx_timeout",
            details={"agent_type": "CodeAgent"}
        )
        
        assert str(error) == "Operation timed out"
        assert error.operation == "context_preparation"
        assert error.timeout_seconds == 30.0
        assert error.context_id == "ctx_timeout"
        assert error.details == {"agent_type": "CodeAgent"}
    
    def test_inheritance(self):
        """Test inheritance from ContextError"""
        error = ContextTimeoutError("Test", "op", 10.0)
        assert isinstance(error, ContextError)


class TestContextCacheError:
    """Test ContextCacheError class"""
    
    def test_basic_creation(self):
        """Test basic exception creation"""
        error = ContextCacheError("Cache error")
        
        assert str(error) == "Cache error"
        assert error.cache_key is None
        assert error.context_id is None
        assert error.details == {}
    
    def test_creation_with_cache_key(self):
        """Test creation with cache key"""
        error = ContextCacheError("Cache error", cache_key="cache_123")
        
        assert str(error) == "Cache error"
        assert error.cache_key == "cache_123"
    
    def test_inheritance(self):
        """Test inheritance from ContextError"""
        error = ContextCacheError("Test")
        assert isinstance(error, ContextError)


class TestContextMonitoringError:
    """Test ContextMonitoringError class"""
    
    def test_basic_creation(self):
        """Test basic exception creation"""
        error = ContextMonitoringError("Monitoring error")
        
        assert str(error) == "Monitoring error"
        assert error.metric_type is None
        assert error.context_id is None
        assert error.details == {}
    
    def test_creation_with_metric_type(self):
        """Test creation with metric type"""
        error = ContextMonitoringError("Monitoring error", metric_type="counter")
        
        assert str(error) == "Monitoring error"
        assert error.metric_type == "counter"
    
    def test_inheritance(self):
        """Test inheritance from ContextError"""
        error = ContextMonitoringError("Test")
        assert isinstance(error, ContextError)


class TestContextBackgroundError:
    """Test ContextBackgroundError class"""
    
    def test_basic_creation(self):
        """Test basic exception creation"""
        error = ContextBackgroundError("Background error")
        
        assert str(error) == "Background error"
        assert error.task_id is None
        assert error.context_id is None
        assert error.details == {}
    
    def test_creation_with_task_id(self):
        """Test creation with task ID"""
        error = ContextBackgroundError("Background error", task_id="task_123")
        
        assert str(error) == "Background error"
        assert error.task_id == "task_123"
    
    def test_inheritance(self):
        """Test inheritance from ContextError"""
        error = ContextBackgroundError("Test")
        assert isinstance(error, ContextError)


class TestContextLearningError:
    """Test ContextLearningError class"""
    
    def test_basic_creation(self):
        """Test basic exception creation"""
        error = ContextLearningError("Learning error")
        
        assert str(error) == "Learning error"
        assert error.learning_type is None
        assert error.context_id is None
        assert error.details == {}
    
    def test_creation_with_learning_type(self):
        """Test creation with learning type"""
        error = ContextLearningError("Learning error", learning_type="pattern_discovery")
        
        assert str(error) == "Learning error"
        assert error.learning_type == "pattern_discovery"
    
    def test_inheritance(self):
        """Test inheritance from ContextError"""
        error = ContextLearningError("Test")
        assert isinstance(error, ContextError)


class TestExceptionChaining:
    """Test exception chaining and context preservation"""
    
    def test_exception_chaining_with_cause(self):
        """Test that exceptions can be chained properly"""
        try:
            try:
                raise ValueError("Original error")
            except ValueError as e:
                raise ContextError("Context error occurred") from e
        except ContextError as ce:
            assert str(ce) == "Context error occurred"
            assert isinstance(ce.__cause__, ValueError)
            assert str(ce.__cause__) == "Original error"
    
    def test_context_preservation_across_exceptions(self):
        """Test that context information is preserved across exception types"""
        details = {"operation": "test", "timestamp": datetime.utcnow().isoformat()}
        
        # Create different exception types with same context
        errors = [
            ContextError("Test error", "ctx_123", details),
            TokenBudgetExceededError("Budget error", 1000, 500, context_id="ctx_123", details=details),
            AgentMemoryError("Memory error", "Agent", context_id="ctx_123", details=details),
            ContextTimeoutError("Timeout", "op", 30.0, context_id="ctx_123", details=details)
        ]
        
        for error in errors:
            assert error.context_id == "ctx_123"
            assert error.details == details


class TestExceptionErrorMessages:
    """Test exception error message formatting"""
    
    def test_meaningful_error_messages(self):
        """Test that error messages are meaningful and descriptive"""
        # Test specific error scenarios
        token_error = TokenBudgetExceededError(
            "Token budget of 100000 exceeded by request for 150000 tokens",
            requested_tokens=150000,
            available_tokens=100000
        )
        assert "100000" in str(token_error)
        assert "150000" in str(token_error)
        
        compression_error = ContextCompressionError(
            "Failed to compress content from 100KB to 50KB target",
            original_size=100000,
            target_size=50000
        )
        assert "100KB" in str(compression_error) or "100000" in str(compression_error)
        
        timeout_error = ContextTimeoutError(
            "Context preparation timed out after 30 seconds",
            operation="context_preparation",
            timeout_seconds=30.0
        )
        assert "30" in str(timeout_error)
    
    def test_empty_message_handling(self):
        """Test handling of empty or None messages"""
        error = ContextError("")
        assert str(error) == ""
        
        # Test that None message doesn't break the exception
        try:
            error = ContextError(None)  # type: ignore
        except Exception as e:
            # Should not raise an exception during creation
            assert False, f"Exception creation failed: {e}"


class TestExceptionChaining:
    """Test exception chaining and complex scenarios"""
    
    def test_exception_chaining(self):
        """Test chaining exceptions with causes"""
        original_error = ValueError("Original error")
        
        try:
            raise original_error
        except ValueError as e:
            try:
                raise ContextError("Context processing failed") from e
            except ContextError as context_error:
                assert context_error.__cause__ is original_error
                assert "Context processing failed" in str(context_error)
    
    def test_multiple_inheritance_check(self):
        """Test that all exceptions properly inherit from ContextError and Exception"""
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
            # Create instance with minimal required args
            if exc_class == TokenBudgetExceededError:
                instance = exc_class("Test", requested_tokens=1000, available_tokens=500)
            elif exc_class == ContextCompressionError:
                instance = exc_class("Test", original_size=1000, target_size=500)
            elif exc_class == AgentMemoryError:
                instance = exc_class("Test", agent_type="TestAgent")
            elif exc_class == ContextIndexError:
                instance = exc_class("Test", index_path="/test/path")
            elif exc_class == ContextStorageError:
                instance = exc_class("Test", storage_path="/test/path")
            elif exc_class == ContextValidationError:
                instance = exc_class("Test", validation_errors=["error1"])
            elif exc_class == ContextTimeoutError:
                instance = exc_class("Test", operation="test_op", timeout_seconds=30.0)
            elif exc_class == ContextCacheError:
                instance = exc_class("Test", cache_key="test_key")
            elif exc_class == ContextMonitoringError:
                instance = exc_class("Test", metric_type="counter")
            elif exc_class == ContextBackgroundError:
                instance = exc_class("Test", task_id="task_123")
            elif exc_class == ContextLearningError:
                instance = exc_class("Test", learning_type="pattern")
            else:
                instance = exc_class("Test")
            
            # Check inheritance
            assert isinstance(instance, ContextError)
            assert isinstance(instance, Exception)
            assert issubclass(exc_class, ContextError)
            assert issubclass(exc_class, Exception)
    
    def test_complex_details_preservation(self):
        """Test that complex details are preserved correctly"""
        complex_details = {
            "timestamp": datetime.now().isoformat(),
            "user_id": 12345,
            "nested_data": {
                "level1": {
                    "level2": ["item1", "item2", {"key": "value"}]
                }
            },
            "list_data": [1, 2, 3, "string", True, None],
            "none_value": None,
            "boolean_true": True,
            "boolean_false": False
        }
        
        error = ContextError(
            "Complex error",
            context_id="ctx_complex",
            details=complex_details
        )
        
        assert error.details == complex_details
        assert error.details["timestamp"] == complex_details["timestamp"]
        assert error.details["nested_data"]["level1"]["level2"][2]["key"] == "value"
        assert error.details["list_data"][4] is True
        assert error.details["none_value"] is None
    
    def test_kwargs_handling_in_specialized_exceptions(self):
        """Test that specialized exceptions properly handle kwargs"""
        # Test that context_id and details are properly passed through kwargs
        token_error = TokenBudgetExceededError(
            "Budget exceeded",
            requested_tokens=1000,
            available_tokens=500,
            context_id="ctx_budget",
            details={"operation": "context_prep"}
        )
        
        assert token_error.requested_tokens == 1000
        assert token_error.available_tokens == 500
        assert token_error.context_id == "ctx_budget"
        assert token_error.details["operation"] == "context_prep"
        
        # Test AgentMemoryError with full kwargs
        memory_error = AgentMemoryError(
            "Memory operation failed",
            agent_type="TestAgent",
            story_id="story_123",
            context_id="ctx_memory",
            details={"error_code": 500}
        )
        
        assert memory_error.agent_type == "TestAgent"
        assert memory_error.story_id == "story_123"
        assert memory_error.context_id == "ctx_memory"
        assert memory_error.details["error_code"] == 500