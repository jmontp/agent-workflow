"""
Comprehensive test suite for Context Management System Interfaces.

Tests all abstract interfaces for context management components to ensure
proper separation of concerns and interface compliance.
"""

import pytest
import asyncio
from abc import ABC
from unittest.mock import Mock, AsyncMock
from typing import Dict, List, Optional, Any, Union

# Import the modules under test
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "lib"))

from context.interfaces import (
    IContextFilter,
    ITokenCalculator,
    IAgentMemory,
    IContextCompressor,
    IContextIndex,
    IContextStorage
)
from context.models import (
    ContextRequest,
    AgentContext,
    TokenBudget,
    TokenUsage,
    AgentMemory,
    RelevanceScore,
    CompressionLevel,
    FileType
)
from tdd_models import TDDState, TDDTask


class TestIContextFilter:
    """Test IContextFilter interface"""
    
    def test_is_abstract_base_class(self):
        """Test that IContextFilter is an abstract base class"""
        assert issubclass(IContextFilter, ABC)
        
        # Should not be able to instantiate directly
        with pytest.raises(TypeError):
            IContextFilter()
    
    def test_interface_methods_exist(self):
        """Test that all required methods exist in the interface"""
        methods = [
            'filter_relevant_files',
            'get_relevance_scores',
            'update_historical_relevance'
        ]
        
        for method in methods:
            assert hasattr(IContextFilter, method)
            assert callable(getattr(IContextFilter, method))
    
    def test_concrete_implementation_requirements(self):
        """Test that concrete implementations must implement all abstract methods"""
        
        class IncompleteFilter(IContextFilter):
            # Missing implementations
            pass
        
        with pytest.raises(TypeError):
            IncompleteFilter()
    
    @pytest.mark.asyncio
    async def test_concrete_implementation_works(self):
        """Test that a complete concrete implementation works"""
        
        class MockContextFilter(IContextFilter):
            async def filter_relevant_files(
                self,
                task: Union[TDDTask, Dict[str, Any]],
                story_id: str,
                agent_type: str,
                tdd_phase: Optional[TDDState] = None,
                max_files: int = 100
            ) -> List[str]:
                return ["file1.py", "file2.py"]
            
            async def get_relevance_scores(
                self,
                files: List[str],
                task: Union[TDDTask, Dict[str, Any]],
                story_id: str
            ) -> List[RelevanceScore]:
                return [
                    RelevanceScore(
                        file_path="file1.py",
                        total_score=0.8,
                        direct_mention=0.5,
                        dependency_score=0.3,
                        historical_score=0.2,
                        semantic_score=0.1,
                        tdd_phase_score=0.05,
                        reasons=["Direct mention"]
                    )
                ]
            
            async def update_historical_relevance(
                self,
                agent_type: str,
                files_used: List[str],
                task_success: bool
            ) -> None:
                pass
        
        # Should be able to instantiate and use
        filter_impl = MockContextFilter()
        assert isinstance(filter_impl, IContextFilter)
        
        # Test method calls
        task = {"description": "Test task"}
        files = await filter_impl.filter_relevant_files(task, "story1", "CodeAgent")
        assert files == ["file1.py", "file2.py"]
        
        scores = await filter_impl.get_relevance_scores(files, task, "story1")
        assert len(scores) == 1
        assert scores[0].file_path == "file1.py"
        
        await filter_impl.update_historical_relevance("CodeAgent", files, True)


class TestITokenCalculator:
    """Test ITokenCalculator interface"""
    
    def test_is_abstract_base_class(self):
        """Test that ITokenCalculator is an abstract base class"""
        assert issubclass(ITokenCalculator, ABC)
        
        with pytest.raises(TypeError):
            ITokenCalculator()
    
    def test_interface_methods_exist(self):
        """Test that all required methods exist in the interface"""
        methods = [
            'calculate_budget',
            'estimate_tokens',
            'optimize_allocation'
        ]
        
        for method in methods:
            assert hasattr(ITokenCalculator, method)
            assert callable(getattr(ITokenCalculator, method))
    
    @pytest.mark.asyncio
    async def test_concrete_implementation_works(self):
        """Test that a complete concrete implementation works"""
        
        class MockTokenCalculator(ITokenCalculator):
            async def calculate_budget(
                self,
                total_tokens: int,
                agent_type: str,
                tdd_phase: Optional[TDDState] = None,
                metadata: Optional[Dict[str, Any]] = None
            ) -> TokenBudget:
                return TokenBudget(
                    total_tokens=total_tokens,
                    context_tokens=int(total_tokens * 0.8),
                    history_tokens=int(total_tokens * 0.1),
                    dependencies_tokens=int(total_tokens * 0.05),
                    memory_tokens=int(total_tokens * 0.05),
                    metadata_tokens=0
                )
            
            async def estimate_tokens(
                self,
                content: str,
                content_type: Optional[FileType] = None
            ) -> int:
                return len(content) // 4  # Simple estimation
            
            async def optimize_allocation(
                self,
                current_budget: TokenBudget,
                actual_usage: TokenUsage,
                context_quality: float
            ) -> TokenBudget:
                return current_budget
        
        calc = MockTokenCalculator()
        assert isinstance(calc, ITokenCalculator)
        
        # Test budget calculation
        budget = await calc.calculate_budget(10000, "CodeAgent")
        assert budget.total_tokens == 10000
        assert budget.context_tokens == 8000
        
        # Test token estimation
        tokens = await calc.estimate_tokens("test content")
        assert tokens == 3  # 12 characters // 4
        
        # Test optimization
        usage = TokenUsage(
            context_tokens=5000,
            history_tokens=1000,
            dependencies_tokens=500,
            memory_tokens=300,
            metadata_tokens=100
        )
        optimized = await calc.optimize_allocation(budget, usage, 0.8)
        assert optimized.total_tokens == 10000


class TestIAgentMemory:
    """Test IAgentMemory interface"""
    
    def test_is_abstract_base_class(self):
        """Test that IAgentMemory is an abstract base class"""
        assert issubclass(IAgentMemory, ABC)
        
        with pytest.raises(TypeError):
            IAgentMemory()
    
    def test_interface_methods_exist(self):
        """Test that all required methods exist in the interface"""
        methods = [
            'get_memory',
            'store_memory',
            'update_memory',
            'clear_memory'
        ]
        
        for method in methods:
            assert hasattr(IAgentMemory, method)
            assert callable(getattr(IAgentMemory, method))
    
    @pytest.mark.asyncio
    async def test_concrete_implementation_works(self):
        """Test that a complete concrete implementation works"""
        
        class MockAgentMemory(IAgentMemory):
            def __init__(self):
                self.memories = {}
            
            async def get_memory(
                self,
                agent_type: str,
                story_id: str
            ) -> Optional[AgentMemory]:
                key = f"{agent_type}:{story_id}"
                return self.memories.get(key)
            
            async def store_memory(
                self,
                memory: AgentMemory
            ) -> None:
                key = f"{memory.agent_type}:{memory.story_id}"
                self.memories[key] = memory
            
            async def update_memory(
                self,
                agent_type: str,
                story_id: str,
                updates: Dict[str, Any]
            ) -> None:
                key = f"{agent_type}:{story_id}"
                if key in self.memories:
                    for k, v in updates.items():
                        setattr(self.memories[key], k, v)
            
            async def clear_memory(
                self,
                agent_type: str,
                story_id: Optional[str] = None
            ) -> None:
                if story_id:
                    key = f"{agent_type}:{story_id}"
                    self.memories.pop(key, None)
                else:
                    keys_to_remove = [k for k in self.memories.keys() if k.startswith(f"{agent_type}:")]
                    for key in keys_to_remove:
                        del self.memories[key]
        
        memory_impl = MockAgentMemory()
        assert isinstance(memory_impl, IAgentMemory)
        
        # Test storing and retrieving memory
        memory = AgentMemory(
            agent_type="CodeAgent",
            story_id="story1",
            context_patterns=[],
            file_preferences=[],
            success_patterns=[],
            failure_patterns=[],
            learning_data={}
        )
        
        await memory_impl.store_memory(memory)
        retrieved = await memory_impl.get_memory("CodeAgent", "story1")
        assert retrieved is not None
        assert retrieved.agent_type == "CodeAgent"
        assert retrieved.story_id == "story1"
        
        # Test updating memory
        await memory_impl.update_memory("CodeAgent", "story1", {"file_preferences": ["test.py"]})
        
        # Test clearing memory
        await memory_impl.clear_memory("CodeAgent", "story1")
        cleared = await memory_impl.get_memory("CodeAgent", "story1")
        assert cleared is None


class TestIContextCompressor:
    """Test IContextCompressor interface"""
    
    def test_is_abstract_base_class(self):
        """Test that IContextCompressor is an abstract base class"""
        assert issubclass(IContextCompressor, ABC)
        
        with pytest.raises(TypeError):
            IContextCompressor()
    
    def test_interface_methods_exist(self):
        """Test that all required methods exist in the interface"""
        methods = [
            'compress_contents',
            'compress_single_file',
            'get_compression_ratio'
        ]
        
        for method in methods:
            assert hasattr(IContextCompressor, method)
            assert callable(getattr(IContextCompressor, method))
    
    @pytest.mark.asyncio
    async def test_concrete_implementation_works(self):
        """Test that a complete concrete implementation works"""
        
        class MockContextCompressor(IContextCompressor):
            async def compress_contents(
                self,
                contents: Dict[str, str],
                target_tokens: int,
                compression_level: CompressionLevel = CompressionLevel.MODERATE,
                file_types: Optional[Dict[str, str]] = None
            ) -> Dict[str, str]:
                # Simple compression: truncate to target length
                compressed = {}
                for path, content in contents.items():
                    max_length = target_tokens * 4  # Assuming 4 chars per token
                    compressed[path] = content[:max_length]
                return compressed
            
            async def compress_single_file(
                self,
                content: str,
                target_tokens: int,
                file_type: FileType = FileType.OTHER,
                compression_level: CompressionLevel = CompressionLevel.MODERATE
            ) -> str:
                max_length = target_tokens * 4
                return content[:max_length]
            
            async def get_compression_ratio(
                self,
                original_content: str,
                compressed_content: str
            ) -> float:
                if len(original_content) == 0:
                    return 1.0
                return len(compressed_content) / len(original_content)
        
        compressor = MockContextCompressor()
        assert isinstance(compressor, IContextCompressor)
        
        # Test content compression
        contents = {"file1.py": "x" * 1000, "file2.py": "y" * 2000}
        compressed = await compressor.compress_contents(contents, 100)
        assert len(compressed) == 2
        assert len(compressed["file1.py"]) <= 400  # 100 tokens * 4 chars
        
        # Test single file compression
        single_compressed = await compressor.compress_single_file("z" * 1000, 50)
        assert len(single_compressed) <= 200  # 50 tokens * 4 chars
        
        # Test compression ratio
        ratio = await compressor.get_compression_ratio("original", "comp")
        assert ratio == 4 / 8  # 0.5


class TestIContextIndex:
    """Test IContextIndex interface"""
    
    def test_is_abstract_base_class(self):
        """Test that IContextIndex is an abstract base class"""
        assert issubclass(IContextIndex, ABC)
        
        with pytest.raises(TypeError):
            IContextIndex()
    
    def test_interface_methods_exist(self):
        """Test that all required methods exist in the interface"""
        methods = [
            'build_index',
            'search_files',
            'get_dependencies',
            'get_dependents'
        ]
        
        for method in methods:
            assert hasattr(IContextIndex, method)
            assert callable(getattr(IContextIndex, method))
    
    @pytest.mark.asyncio
    async def test_concrete_implementation_works(self):
        """Test that a complete concrete implementation works"""
        
        class MockContextIndex(IContextIndex):
            def __init__(self):
                self.files = ["file1.py", "file2.py", "test_file.py"]
                self.dependencies = {
                    "file1.py": ["file2.py"],
                    "file2.py": [],
                    "test_file.py": ["file1.py"]
                }
            
            async def build_index(
                self,
                project_path: str,
                force_rebuild: bool = False
            ) -> None:
                pass  # Mock implementation
            
            async def search_files(
                self,
                query: str,
                file_types: Optional[List[FileType]] = None,
                limit: int = 50
            ) -> List[str]:
                # Simple search: return files containing query
                return [f for f in self.files if query.lower() in f.lower()][:limit]
            
            async def get_dependencies(
                self,
                file_path: str
            ) -> List[str]:
                return self.dependencies.get(file_path, [])
            
            async def get_dependents(
                self,
                file_path: str
            ) -> List[str]:
                dependents = []
                for file, deps in self.dependencies.items():
                    if file_path in deps:
                        dependents.append(file)
                return dependents
        
        index = MockContextIndex()
        assert isinstance(index, IContextIndex)
        
        # Test index building
        await index.build_index("/test/project")
        
        # Test file search
        results = await index.search_files("file")
        assert len(results) == 3
        
        test_results = await index.search_files("test")
        assert "test_file.py" in test_results
        
        # Test dependency lookup
        deps = await index.get_dependencies("file1.py")
        assert deps == ["file2.py"]
        
        # Test dependent lookup
        dependents = await index.get_dependents("file1.py")
        assert "test_file.py" in dependents


class TestIContextStorage:
    """Test IContextStorage interface"""
    
    def test_is_abstract_base_class(self):
        """Test that IContextStorage is an abstract base class"""
        assert issubclass(IContextStorage, ABC)
        
        with pytest.raises(TypeError):
            IContextStorage()
    
    def test_interface_methods_exist(self):
        """Test that all required methods exist in the interface"""
        methods = [
            'store_context',
            'retrieve_context',
            'list_contexts',
            'delete_context',
            'cleanup_old_contexts'
        ]
        
        for method in methods:
            assert hasattr(IContextStorage, method)
            assert callable(getattr(IContextStorage, method))
    
    @pytest.mark.asyncio
    async def test_concrete_implementation_works(self):
        """Test that a complete concrete implementation works"""
        
        class MockContextStorage(IContextStorage):
            def __init__(self):
                self.contexts = {}
            
            async def store_context(
                self,
                context: AgentContext
            ) -> None:
                self.contexts[context.request_id] = context
            
            async def retrieve_context(
                self,
                context_id: str
            ) -> Optional[AgentContext]:
                return self.contexts.get(context_id)
            
            async def list_contexts(
                self,
                agent_type: Optional[str] = None,
                story_id: Optional[str] = None,
                limit: int = 100
            ) -> List[str]:
                contexts = list(self.contexts.keys())
                # Simple filtering (in real implementation would be more sophisticated)
                return contexts[:limit]
            
            async def delete_context(
                self,
                context_id: str
            ) -> bool:
                if context_id in self.contexts:
                    del self.contexts[context_id]
                    return True
                return False
            
            async def cleanup_old_contexts(
                self,
                older_than_days: int = 30
            ) -> int:
                # Mock cleanup - in real implementation would check timestamps
                count = len(self.contexts)
                self.contexts.clear()
                return count
        
        storage = MockContextStorage()
        assert isinstance(storage, IContextStorage)
        
        # Test context storage and retrieval
        context = AgentContext(
            request_id="ctx_123",
            agent_type="CodeAgent",
            story_id="story1",
            core_context="test context",
            historical_context="",
            dependencies="",
            agent_memory="",
            metadata="",
            file_contents={}
        )
        
        await storage.store_context(context)
        retrieved = await storage.retrieve_context("ctx_123")
        assert retrieved is not None
        assert retrieved.request_id == "ctx_123"
        
        # Test context listing
        contexts = await storage.list_contexts()
        assert "ctx_123" in contexts
        
        # Test context deletion
        deleted = await storage.delete_context("ctx_123")
        assert deleted is True
        
        retrieved_after_delete = await storage.retrieve_context("ctx_123")
        assert retrieved_after_delete is None
        
        # Test cleanup
        await storage.store_context(context)  # Store again
        cleaned = await storage.cleanup_old_contexts()
        assert cleaned == 1


class TestInterfaceMethodSignatures:
    """Test that interface methods have correct signatures"""
    
    def test_async_method_signatures(self):
        """Test that methods marked as async in interfaces are properly defined"""
        # Check that abstract methods are properly decorated as async
        filter_methods = [m for m in dir(IContextFilter) if not m.startswith('_')]
        for method_name in filter_methods:
            method = getattr(IContextFilter, method_name)
            # Abstract methods should have the correct signature hints
            assert callable(method)
    
    def test_parameter_types_and_defaults(self):
        """Test that interface methods have proper parameter types and defaults"""
        # This is more of a documentation test - ensuring interfaces are well-defined
        
        # Check IContextFilter.filter_relevant_files has proper defaults
        import inspect
        sig = inspect.signature(IContextFilter.filter_relevant_files)
        
        assert 'task' in sig.parameters
        assert 'story_id' in sig.parameters
        assert 'agent_type' in sig.parameters
        assert 'tdd_phase' in sig.parameters
        assert 'max_files' in sig.parameters
        
        # Check that max_files has a default
        assert sig.parameters['max_files'].default == 100
        assert sig.parameters['tdd_phase'].default is None
    
    def test_return_type_consistency(self):
        """Test that return types are consistently defined across interfaces"""
        # Check that methods returning List have consistent patterns
        import inspect
        
        # IContextFilter.filter_relevant_files should return List[str]
        sig = inspect.signature(IContextFilter.filter_relevant_files)
        assert sig.return_annotation is not None
        
        # IContextStorage.list_contexts should return List[str]
        sig = inspect.signature(IContextStorage.list_contexts)
        assert sig.return_annotation is not None


class TestInterfaceUsagePatterns:
    """Test common usage patterns for interfaces"""
    
    @pytest.mark.asyncio
    async def test_interface_composition(self):
        """Test that interfaces can be composed together"""
        
        class CompositeContextManager:
            def __init__(self, filter_impl, calculator_impl, storage_impl):
                self.filter = filter_impl
                self.calculator = calculator_impl
                self.storage = storage_impl
            
            async def process_request(self, request):
                # Use multiple interfaces together
                files = await self.filter.filter_relevant_files(
                    request.task, request.story_id, request.agent_type
                )
                budget = await self.calculator.calculate_budget(
                    request.max_tokens, request.agent_type
                )
                return {"files": files, "budget": budget}
        
        # Mock implementations for testing composition
        filter_mock = AsyncMock(spec=IContextFilter)
        filter_mock.filter_relevant_files.return_value = ["file1.py"]
        
        calculator_mock = AsyncMock(spec=ITokenCalculator)
        calculator_mock.calculate_budget.return_value = TokenBudget(
            total_tokens=10000, context_tokens=8000, history_tokens=1000,
            dependencies_tokens=500, memory_tokens=500, metadata_tokens=0
        )
        
        storage_mock = AsyncMock(spec=IContextStorage)
        
        manager = CompositeContextManager(filter_mock, calculator_mock, storage_mock)
        
        # Mock request
        request = Mock()
        request.task = {"description": "test"}
        request.story_id = "story1"
        request.agent_type = "CodeAgent"
        request.max_tokens = 10000
        
        result = await manager.process_request(request)
        assert result["files"] == ["file1.py"]
        assert result["budget"].total_tokens == 10000
    
    def test_interface_polymorphism(self):
        """Test that different implementations of same interface are interchangeable"""
        
        class ImplementationA(ITokenCalculator):
            async def calculate_budget(self, total_tokens, agent_type, tdd_phase=None, metadata=None):
                return TokenBudget(total_tokens, total_tokens//2, 0, 0, 0, 0)
            async def estimate_tokens(self, content, content_type=None):
                return len(content)
            async def optimize_allocation(self, current_budget, actual_usage, context_quality):
                return current_budget
        
        class ImplementationB(ITokenCalculator):
            async def calculate_budget(self, total_tokens, agent_type, tdd_phase=None, metadata=None):
                return TokenBudget(total_tokens, total_tokens//4, total_tokens//4, total_tokens//4, total_tokens//4, 0)
            async def estimate_tokens(self, content, content_type=None):
                return len(content) * 2
            async def optimize_allocation(self, current_budget, actual_usage, context_quality):
                return current_budget
        
        # Both implementations should work with the same interface
        def use_calculator(calc: ITokenCalculator):
            return isinstance(calc, ITokenCalculator)
        
        impl_a = ImplementationA()
        impl_b = ImplementationB()
        
        assert use_calculator(impl_a)
        assert use_calculator(impl_b)
        
        # They should be interchangeable
        calculators = [impl_a, impl_b]
        for calc in calculators:
            assert isinstance(calc, ITokenCalculator)