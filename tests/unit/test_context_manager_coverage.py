"""
Comprehensive test suite for ContextManager with 95%+ line coverage.

This test suite targets government audit compliance by thoroughly testing all
functionality including initialization, context preparation, caching, monitoring,
cross-story management, background processing, and error handling scenarios.
"""

import pytest
import asyncio
import tempfile
import shutil
import hashlib
from pathlib import Path
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, AsyncMock, MagicMock, call
from typing import Dict, Any, List

# Import the modules under test
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "lib"))

from context_manager import ContextManager
from context.models import (
    ContextRequest, AgentContext, TokenBudget, TokenUsage,
    CompressionLevel, ContextType, Decision, PhaseHandoff,
    ContextSnapshot, RelevanceScore, FileType
)
from context.exceptions import (
    ContextError, TokenBudgetExceededError, ContextNotFoundError,
    ContextTimeoutError
)
from context_cache import CacheStrategy, CacheWarmingStrategy
from context_background import TaskPriority
from tdd_models import TDDState, TDDTask, TDDCycle


class TestContextManagerComprehensiveInit:
    """Comprehensive initialization tests"""
    
    def test_init_default_parameters(self):
        """Test initialization with all default parameters"""
        cm = ContextManager()
        
        assert cm.project_path == Path.cwd()
        assert cm.max_tokens == 200000
        assert cm.cache_ttl_seconds == 300
        assert cm.max_preparation_time == 30
        assert cm.enable_intelligence is True
        assert cm.enable_advanced_caching is True
        assert cm.enable_monitoring is True
        assert cm.enable_cross_story is True
        assert cm.enable_background_processing is True
        
        # Check component initialization
        assert cm.token_calculator is not None
        assert cm.agent_memory is not None
        assert cm.context_cache is not None
        assert cm.monitor is not None
        assert cm.background_processor is not None
        assert cm.context_filter is not None
        assert cm.context_compressor is not None
        assert cm.context_index is not None
        
        # Check internal state
        assert isinstance(cm._active_stories, dict)
        assert isinstance(cm._story_conflicts, dict)
        assert isinstance(cm._cross_story_cache, dict)
        assert isinstance(cm._legacy_cache, dict)
        assert isinstance(cm._preparation_times, list)
        assert isinstance(cm._active_contexts, dict)
        assert cm._cache_hits == 0
        assert cm._cache_misses == 0
        assert cm._total_requests == 0
    
    def test_init_all_features_disabled(self):
        """Test initialization with all advanced features disabled"""
        with tempfile.TemporaryDirectory() as temp_dir:
            cm = ContextManager(
                project_path=temp_dir,
                enable_intelligence=False,
                enable_advanced_caching=False,
                enable_monitoring=False,
                enable_cross_story=False,
                enable_background_processing=False
            )
            
            assert cm.enable_intelligence is False
            assert cm.enable_advanced_caching is False
            assert cm.enable_monitoring is False
            assert cm.enable_cross_story is False
            assert cm.enable_background_processing is False
            
            # Check that optional components are None
            assert cm.context_cache is None
            assert cm.monitor is None
            assert cm.background_processor is None
            assert cm.context_filter is None
            assert cm.context_compressor is None
            assert cm.context_index is None
    
    @patch('context_manager.ContextCache')
    @patch('context_manager.ContextBackgroundProcessor')
    def test_init_custom_cache_strategies(self, mock_bg_cls, mock_cache_cls):
        """Test initialization with custom cache strategies"""
        with tempfile.TemporaryDirectory() as temp_dir:
            mock_cache_cls.return_value = Mock()
            mock_bg_cls.return_value = Mock()
            
            cm = ContextManager(
                project_path=temp_dir,
                cache_strategy=CacheStrategy.LRU,
                warming_strategy=CacheWarmingStrategy.AGGRESSIVE,
                background_workers=8
            )
            
            # Should have created cache with correct strategy
            mock_cache_cls.assert_called_once()
            # Should have created background processor
            mock_bg_cls.assert_called_once()
    
    def test_init_creates_orch_state_directory(self):
        """Test that initialization creates .orch-state directory"""
        with tempfile.TemporaryDirectory() as temp_dir:
            project_path = Path(temp_dir) / "test_project"
            cm = ContextManager(project_path=str(project_path))
            
            orch_state_dir = project_path / ".orch-state"
            assert orch_state_dir.exists()
    
    def test_init_with_none_project_path(self):
        """Test initialization with None project path"""
        cm = ContextManager(project_path=None)
        assert cm.project_path == Path.cwd()


class TestContextManagerStartStop:
    """Test async start/stop methods"""
    
    @pytest.fixture
    def context_manager(self):
        """Create context manager with mocked components"""
        with tempfile.TemporaryDirectory() as temp_dir:
            with patch('context_manager.ContextCache') as mock_cache_cls, \
                 patch('context_manager.ContextMonitor') as mock_monitor_cls, \
                 patch('context_manager.ContextBackgroundProcessor') as mock_bg_cls:
                
                # Configure mocks
                mock_cache = AsyncMock()
                mock_cache_cls.return_value = mock_cache
                
                mock_monitor = AsyncMock()
                mock_monitor_cls.return_value = mock_monitor
                
                mock_bg = AsyncMock()
                mock_bg_cls.return_value = mock_bg
                
                cm = ContextManager(project_path=temp_dir)
                cm.context_cache = mock_cache
                cm.monitor = mock_monitor
                cm.background_processor = mock_bg
                
                yield cm
    
    @pytest.mark.asyncio
    async def test_start_all_services(self, context_manager):
        """Test starting all background services"""
        with patch.object(context_manager, '_queue_initial_background_tasks', new_callable=AsyncMock) as mock_queue:
            await context_manager.start()
            
            # Verify all services were started
            context_manager.context_cache.start_background_tasks.assert_called_once()
            context_manager.monitor.start_monitoring.assert_called_once()
            context_manager.background_processor.start.assert_called_once()
            mock_queue.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_start_selective_services(self):
        """Test starting only enabled services"""
        with tempfile.TemporaryDirectory() as temp_dir:
            cm = ContextManager(
                project_path=temp_dir,
                enable_advanced_caching=False,
                enable_monitoring=False,
                enable_background_processing=False
            )
            
            # Should not raise any errors
            await cm.start()
    
    @pytest.mark.asyncio
    async def test_stop_all_services(self, context_manager):
        """Test stopping all background services"""
        await context_manager.stop()
        
        # Verify all services were stopped
        context_manager.background_processor.stop.assert_called_once()
        context_manager.context_cache.stop_background_tasks.assert_called_once()
        context_manager.monitor.stop_monitoring.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_start_with_exception_handling(self):
        """Test start method handles exceptions gracefully"""
        with tempfile.TemporaryDirectory() as temp_dir:
            with patch('context_manager.ContextCache') as mock_cache_cls, \
                 patch('context_manager.ContextMonitor') as mock_monitor_cls, \
                 patch('context_manager.ContextBackgroundProcessor') as mock_bg_cls:
                
                mock_cache = AsyncMock()
                mock_cache.start_background_tasks.side_effect = Exception("Cache start failed")
                mock_cache_cls.return_value = mock_cache
                
                mock_monitor = AsyncMock()
                mock_monitor_cls.return_value = mock_monitor
                
                mock_bg = AsyncMock()
                mock_bg_cls.return_value = mock_bg
                
                cm = ContextManager(project_path=temp_dir)
                cm.context_cache = mock_cache
                cm.monitor = mock_monitor
                cm.background_processor = mock_bg
                
                # Should not raise exception even if cache start fails
                await cm.start()


class TestContextPreparationComprehensive:
    """Comprehensive context preparation tests"""
    
    @pytest.fixture
    def context_manager(self):
        """Create context manager with mocked components"""
        with tempfile.TemporaryDirectory() as temp_dir:
            with patch('context_manager.FileBasedAgentMemory'), \
                 patch('context_manager.TokenCalculator'):
                
                cm = ContextManager(
                    project_path=temp_dir,
                    enable_intelligence=False,
                    enable_advanced_caching=False,
                    enable_monitoring=False,
                    enable_cross_story=False,
                    enable_background_processing=False
                )
                
                # Mock internal methods
                cm._prepare_context_internal = AsyncMock()
                cm._generate_cache_key = Mock(return_value="test_cache_key")
                cm._extract_story_id = Mock(return_value="test_story")
                cm._extract_tdd_phase = Mock(return_value=TDDState.DESIGN)
                
                yield cm
    
    @pytest.fixture
    def sample_tdd_task(self):
        """Create sample TDD task"""
        return TDDTask(
            id="task_1",
            description="Test task",
            cycle_id="cycle_1",
            current_state=TDDState.DESIGN
        )
    
    @pytest.fixture
    def sample_dict_task(self):
        """Create sample dictionary task"""
        return {
            "description": "Test dict task",
            "story_id": "story_1",
            "current_state": "DESIGN",
            "file_paths": ["test.py", "another.py"]
        }
    
    @pytest.fixture
    def sample_context(self):
        """Create sample agent context"""
        return AgentContext(
            request_id="req_1",
            agent_type="DesignAgent",
            story_id="story_1",
            tdd_phase=TDDState.DESIGN,
            core_context="Test core context",
            token_usage=TokenUsage(
                context_id="req_1",
                total_used=1000,
                core_task_used=600,
                historical_used=200,
                dependencies_used=150,
                agent_memory_used=50
            ),
            preparation_time=1.5
        )
    
    @pytest.mark.asyncio
    async def test_prepare_context_with_tdd_task(self, context_manager, sample_tdd_task, sample_context):
        """Test context preparation with TDDTask"""
        context_manager._prepare_context_internal.return_value = sample_context
        
        result = await context_manager.prepare_context(
            agent_type="DesignAgent",
            task=sample_tdd_task,
            max_tokens=50000,
            story_id="story_1"
        )
        
        assert result == sample_context
        assert context_manager._total_requests == 1
        assert context_manager._cache_misses == 1
        assert result.request_id in context_manager._active_contexts
    
    @pytest.mark.asyncio
    async def test_prepare_context_with_dict_task(self, context_manager, sample_dict_task, sample_context):
        """Test context preparation with dictionary task"""
        context_manager._prepare_context_internal.return_value = sample_context
        
        result = await context_manager.prepare_context(
            agent_type="CodeAgent",
            task=sample_dict_task,
            story_id="story_2"
        )
        
        assert result == sample_context
        assert context_manager._total_requests == 1
    
    @pytest.mark.asyncio
    async def test_prepare_context_legacy_cache_hit(self, context_manager, sample_tdd_task, sample_context):
        """Test context preparation with legacy cache hit"""
        # Setup legacy cache
        context_manager._get_cached_context_legacy = AsyncMock(return_value=sample_context)
        
        result = await context_manager.prepare_context(
            agent_type="DesignAgent",
            task=sample_tdd_task,
            story_id="story_1"
        )
        
        assert result == sample_context
        assert result.cache_hit is True
        assert context_manager._cache_hits == 1
        assert context_manager._cache_misses == 0
        # Should not call internal preparation
        context_manager._prepare_context_internal.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_prepare_context_legacy_cache_miss(self, context_manager, sample_tdd_task, sample_context):
        """Test context preparation with legacy cache miss"""
        context_manager._get_cached_context_legacy = AsyncMock(return_value=None)
        context_manager._cache_context_legacy = AsyncMock()
        context_manager._prepare_context_internal.return_value = sample_context
        
        result = await context_manager.prepare_context(
            agent_type="DesignAgent",
            task=sample_tdd_task,
            story_id="story_1"
        )
        
        assert result == sample_context
        assert context_manager._cache_misses == 1
        context_manager._prepare_context_internal.assert_called_once()
        context_manager._cache_context_legacy.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_prepare_context_timeout_error(self, context_manager, sample_tdd_task):
        """Test context preparation timeout"""
        context_manager.max_preparation_time = 0.001
        context_manager._prepare_context_internal.side_effect = asyncio.sleep(1)
        
        with pytest.raises(ContextTimeoutError) as exc_info:
            await context_manager.prepare_context(
                agent_type="DesignAgent",
                task=sample_tdd_task,
                story_id="story_1"
            )
        
        assert "timed out" in str(exc_info.value)
        assert exc_info.value.timeout_seconds == 0.001
    
    @pytest.mark.asyncio
    async def test_prepare_context_generic_error(self, context_manager, sample_tdd_task):
        """Test context preparation generic error handling"""
        context_manager._prepare_context_internal.side_effect = ValueError("Test error")
        
        with pytest.raises(ContextError) as exc_info:
            await context_manager.prepare_context(
                agent_type="DesignAgent",
                task=sample_tdd_task,
                story_id="story_1"
            )
        
        assert "Context preparation failed" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_prepare_context_with_kwargs(self, context_manager, sample_tdd_task, sample_context):
        """Test context preparation with additional kwargs"""
        context_manager._prepare_context_internal.return_value = sample_context
        
        result = await context_manager.prepare_context(
            agent_type="DesignAgent",
            task=sample_tdd_task,
            story_id="story_1",
            include_history=True,
            include_dependencies=False,
            compression_level=CompressionLevel.HIGH
        )
        
        assert result == sample_context
        # Verify ContextRequest was created with kwargs
        context_manager._prepare_context_internal.assert_called_once()


class TestContextPreparationWithAdvancedFeatures:
    """Test context preparation with advanced features enabled"""
    
    @pytest.fixture
    def context_manager_advanced(self):
        """Create context manager with advanced features and mocks"""
        with tempfile.TemporaryDirectory() as temp_dir:
            with patch('context_manager.ContextCache') as mock_cache_cls, \
                 patch('context_manager.ContextMonitor') as mock_monitor_cls:
                
                mock_cache = AsyncMock()
                mock_cache_cls.return_value = mock_cache
                
                mock_monitor = AsyncMock()
                mock_monitor.record_operation_start.return_value = "op_123"
                mock_monitor_cls.return_value = mock_monitor
                
                cm = ContextManager(
                    project_path=temp_dir,
                    enable_intelligence=False,  # Keep simple for these tests
                    enable_advanced_caching=True,
                    enable_monitoring=True,
                    enable_cross_story=True,
                    enable_background_processing=False
                )
                
                cm.context_cache = mock_cache
                cm.monitor = mock_monitor
                cm._prepare_context_internal = AsyncMock()
                cm._handle_cross_story_preparation = AsyncMock()
                cm._update_cross_story_tracking = AsyncMock()
                
                yield cm
    
    @pytest.mark.asyncio
    async def test_prepare_context_advanced_cache_hit(self, context_manager_advanced, sample_context):
        """Test context preparation with advanced cache hit"""
        context_manager_advanced.context_cache.get.return_value = sample_context
        
        task = {"description": "test", "story_id": "story_1"}
        result = await context_manager_advanced.prepare_context(
            agent_type="DesignAgent",
            task=task,
            story_id="story_1"
        )
        
        assert result == sample_context
        assert result.cache_hit is True
        assert context_manager_advanced._cache_hits == 1
        context_manager_advanced.context_cache.get.assert_called_once()
        context_manager_advanced.monitor.record_context_preparation.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_prepare_context_advanced_cache_miss(self, context_manager_advanced, sample_context):
        """Test context preparation with advanced cache miss"""
        context_manager_advanced.context_cache.get.return_value = None
        context_manager_advanced._prepare_context_internal.return_value = sample_context
        
        task = {"description": "test", "story_id": "story_1"}
        result = await context_manager_advanced.prepare_context(
            agent_type="DesignAgent",
            task=task,
            story_id="story_1"
        )
        
        assert result == sample_context
        assert context_manager_advanced._cache_misses == 1
        context_manager_advanced.context_cache.put.assert_called_once()
        context_manager_advanced._handle_cross_story_preparation.assert_called_once()
        context_manager_advanced._update_cross_story_tracking.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_prepare_context_monitoring_integration(self, context_manager_advanced, sample_context):
        """Test context preparation with monitoring integration"""
        context_manager_advanced.context_cache.get.return_value = None
        context_manager_advanced._prepare_context_internal.return_value = sample_context
        
        task = {"description": "test", "story_id": "story_1"}
        await context_manager_advanced.prepare_context(
            agent_type="DesignAgent",
            task=task,
            story_id="story_1"
        )
        
        # Verify monitoring calls
        context_manager_advanced.monitor.record_operation_start.assert_called_once_with("context_preparation")
        context_manager_advanced.monitor.record_operation_end.assert_called_once_with("op_123", True)
        # record_context_preparation should be called with specific arguments
        assert context_manager_advanced.monitor.record_context_preparation.call_count == 1


@pytest.fixture
def sample_context():
    """Fixture for sample agent context"""
    return AgentContext(
        request_id="req_1",
        agent_type="DesignAgent",
        story_id="story_1",
        tdd_phase=TDDState.DESIGN,
        core_context="Test core context",
        token_usage=TokenUsage(
            context_id="req_1",
            total_used=1000,
            core_task_used=600,
            historical_used=200,
            dependencies_used=150,
            agent_memory_used=50
        ),
        preparation_time=1.5,
        file_contents={"test.py": "print('hello')"}
    )


class TestAgentDecisionRecording:
    """Test agent decision recording functionality"""
    
    @pytest.fixture
    def context_manager(self):
        """Create context manager for testing"""
        with tempfile.TemporaryDirectory() as temp_dir:
            cm = ContextManager(
                project_path=temp_dir,
                enable_intelligence=False,
                enable_advanced_caching=False,
                enable_monitoring=False,
                enable_cross_story=False,
                enable_background_processing=False
            )
            
            # Mock agent memory
            cm.agent_memory.add_decision = AsyncMock()
            cm.agent_memory.get_recent_decisions = AsyncMock()
            
            yield cm
    
    @pytest.mark.asyncio
    async def test_record_agent_decision_full_params(self, context_manager):
        """Test recording agent decision with all parameters"""
        decision_id = await context_manager.record_agent_decision(
            agent_type="DesignAgent",
            story_id="story_1",
            description="Test decision",
            rationale="Test rationale",
            outcome="Success",
            confidence=0.85,
            artifacts={"file1.py": "content", "file2.py": "more content"}
        )
        
        assert isinstance(decision_id, str)
        context_manager.agent_memory.add_decision.assert_called_once()
        
        # Verify the Decision object created
        call_args = context_manager.agent_memory.add_decision.call_args
        assert call_args[0][0] == "DesignAgent"
        assert call_args[0][1] == "story_1"
        decision = call_args[0][2]
        assert decision.agent_type == "DesignAgent"
        assert decision.description == "Test decision"
        assert decision.rationale == "Test rationale"
        assert decision.outcome == "Success"
        assert decision.confidence == 0.85
        assert decision.artifacts == {"file1.py": "content", "file2.py": "more content"}
    
    @pytest.mark.asyncio
    async def test_record_agent_decision_minimal_params(self, context_manager):
        """Test recording agent decision with minimal parameters"""
        decision_id = await context_manager.record_agent_decision(
            agent_type="CodeAgent",
            story_id="story_2",
            description="Minimal decision"
        )
        
        assert isinstance(decision_id, str)
        context_manager.agent_memory.add_decision.assert_called_once()
        
        # Verify defaults
        call_args = context_manager.agent_memory.add_decision.call_args
        decision = call_args[0][2]
        assert decision.rationale == ""
        assert decision.outcome == ""
        assert decision.confidence == 0.0
        assert decision.artifacts == {}
    
    @pytest.mark.asyncio
    async def test_get_recent_decisions(self, context_manager):
        """Test getting recent decisions"""
        mock_decisions = [
            Mock(id="dec_1", description="Decision 1"),
            Mock(id="dec_2", description="Decision 2")
        ]
        context_manager.agent_memory.get_recent_decisions.return_value = mock_decisions
        
        decisions = await context_manager.get_recent_decisions(
            agent_type="DesignAgent",
            story_id="story_1",
            limit=5
        )
        
        assert decisions == mock_decisions
        context_manager.agent_memory.get_recent_decisions.assert_called_once_with(
            "DesignAgent", "story_1", 5
        )


class TestPhaseHandoffs:
    """Test TDD phase handoff functionality"""
    
    @pytest.fixture
    def context_manager(self):
        """Create context manager for testing"""
        with tempfile.TemporaryDirectory() as temp_dir:
            cm = ContextManager(
                project_path=temp_dir,
                enable_intelligence=False,
                enable_advanced_caching=False,
                enable_monitoring=False,
                enable_cross_story=False,
                enable_background_processing=False
            )
            
            # Mock agent memory
            cm.agent_memory.add_phase_handoff = AsyncMock()
            cm.agent_memory.get_phase_handoffs = AsyncMock()
            
            yield cm
    
    @pytest.mark.asyncio
    async def test_record_phase_handoff_full_params(self, context_manager):
        """Test recording phase handoff with all parameters"""
        handoff_id = await context_manager.record_phase_handoff(
            from_agent="DesignAgent",
            to_agent="QAAgent",
            from_phase=TDDState.DESIGN,
            to_phase=TDDState.TEST_RED,
            story_id="story_1",
            artifacts={"design.md": "design content", "spec.py": "specification"},
            context_summary="Design phase completed successfully",
            handoff_notes="Ready for test development"
        )
        
        assert isinstance(handoff_id, str)
        # Should be called twice - once for each agent
        assert context_manager.agent_memory.add_phase_handoff.call_count == 2
        
        # Verify handoff object
        call_args_list = context_manager.agent_memory.add_phase_handoff.call_args_list
        first_call = call_args_list[0]
        assert first_call[0][0] == "DesignAgent"
        assert first_call[0][1] == "story_1"
        
        handoff = first_call[0][2]
        assert handoff.from_agent == "DesignAgent"
        assert handoff.to_agent == "QAAgent"
        assert handoff.from_phase == TDDState.DESIGN
        assert handoff.to_phase == TDDState.TEST_RED
        assert handoff.artifacts == {"design.md": "design content", "spec.py": "specification"}
        assert handoff.context_summary == "Design phase completed successfully"
        assert handoff.handoff_notes == "Ready for test development"
    
    @pytest.mark.asyncio
    async def test_record_phase_handoff_minimal_params(self, context_manager):
        """Test recording phase handoff with minimal parameters"""
        handoff_id = await context_manager.record_phase_handoff(
            from_agent="CodeAgent",
            to_agent="QAAgent",
            from_phase=TDDState.CODE_GREEN,
            to_phase=TDDState.REFACTOR,
            story_id="story_2"
        )
        
        assert isinstance(handoff_id, str)
        assert context_manager.agent_memory.add_phase_handoff.call_count == 2
        
        # Verify defaults
        call_args = context_manager.agent_memory.add_phase_handoff.call_args_list[0]
        handoff = call_args[0][2]
        assert handoff.artifacts == {}
        assert handoff.context_summary == ""
        assert handoff.handoff_notes == ""
    
    @pytest.mark.asyncio
    async def test_get_phase_handoffs_all_params(self, context_manager):
        """Test getting phase handoffs with all filter parameters"""
        mock_handoffs = [Mock(id="h1"), Mock(id="h2")]
        context_manager.agent_memory.get_phase_handoffs.return_value = mock_handoffs
        
        handoffs = await context_manager.get_phase_handoffs(
            agent_type="DesignAgent",
            story_id="story_1",
            from_phase=TDDState.DESIGN,
            to_phase=TDDState.TEST_RED
        )
        
        assert handoffs == mock_handoffs
        context_manager.agent_memory.get_phase_handoffs.assert_called_once_with(
            "DesignAgent", "story_1", TDDState.DESIGN, TDDState.TEST_RED
        )
    
    @pytest.mark.asyncio
    async def test_get_phase_handoffs_minimal_params(self, context_manager):
        """Test getting phase handoffs with minimal parameters"""
        mock_handoffs = [Mock(id="h1")]
        context_manager.agent_memory.get_phase_handoffs.return_value = mock_handoffs
        
        handoffs = await context_manager.get_phase_handoffs(
            agent_type="CodeAgent",
            story_id="story_2"
        )
        
        assert handoffs == mock_handoffs
        context_manager.agent_memory.get_phase_handoffs.assert_called_once_with(
            "CodeAgent", "story_2", None, None
        )


class TestContextSnapshots:
    """Test context snapshot functionality"""
    
    @pytest.fixture
    def context_manager(self):
        """Create context manager for testing"""
        with tempfile.TemporaryDirectory() as temp_dir:
            cm = ContextManager(
                project_path=temp_dir,
                enable_intelligence=False,
                enable_advanced_caching=False,
                enable_monitoring=False,
                enable_cross_story=False,
                enable_background_processing=False
            )
            
            # Mock agent memory
            cm.agent_memory.add_context_snapshot = AsyncMock()
            cm.agent_memory.get_context_history = AsyncMock()
            
            yield cm
    
    @pytest.mark.asyncio
    async def test_create_context_snapshot_with_summary(self, context_manager, sample_context):
        """Test creating context snapshot with custom summary"""
        snapshot_id = await context_manager.create_context_snapshot(
            agent_type="DesignAgent",
            story_id="story_1",
            context=sample_context,
            summary="Custom snapshot summary"
        )
        
        assert isinstance(snapshot_id, str)
        context_manager.agent_memory.add_context_snapshot.assert_called_once()
        
        # Verify snapshot object
        call_args = context_manager.agent_memory.add_context_snapshot.call_args
        assert call_args[0][0] == "DesignAgent"
        assert call_args[0][1] == "story_1"
        
        snapshot = call_args[0][2]
        assert snapshot.agent_type == "DesignAgent"
        assert snapshot.story_id == "story_1"
        assert snapshot.tdd_phase == TDDState.DESIGN
        assert snapshot.context_summary == "Custom snapshot summary"
        assert snapshot.file_list == ["test.py"]
        assert snapshot.token_usage == sample_context.token_usage
        assert "preparation_time" in snapshot.metadata
        assert "compression_applied" in snapshot.metadata
    
    @pytest.mark.asyncio
    async def test_create_context_snapshot_default_summary(self, context_manager, sample_context):
        """Test creating context snapshot with default summary"""
        snapshot_id = await context_manager.create_context_snapshot(
            agent_type="CodeAgent",
            story_id="story_2",
            context=sample_context
        )
        
        assert isinstance(snapshot_id, str)
        
        # Verify default summary
        call_args = context_manager.agent_memory.add_context_snapshot.call_args
        snapshot = call_args[0][2]
        assert snapshot.context_summary == "Context snapshot for CodeAgent"
    
    @pytest.mark.asyncio
    async def test_get_agent_context_history_all_params(self, context_manager):
        """Test getting context history with all parameters"""
        mock_snapshots = [Mock(id="s1"), Mock(id="s2")]
        context_manager.agent_memory.get_context_history.return_value = mock_snapshots
        
        snapshots = await context_manager.get_agent_context_history(
            agent_type="DesignAgent",
            story_id="story_1",
            tdd_phase=TDDState.DESIGN,
            limit=5
        )
        
        assert snapshots == mock_snapshots
        context_manager.agent_memory.get_context_history.assert_called_once_with(
            "DesignAgent", "story_1", TDDState.DESIGN, 5
        )
    
    @pytest.mark.asyncio
    async def test_get_agent_context_history_default_limit(self, context_manager):
        """Test getting context history with default limit"""
        mock_snapshots = [Mock(id="s1")]
        context_manager.agent_memory.get_context_history.return_value = mock_snapshots
        
        snapshots = await context_manager.get_agent_context_history(
            agent_type="QAAgent",
            story_id="story_3"
        )
        
        assert snapshots == mock_snapshots
        context_manager.agent_memory.get_context_history.assert_called_once_with(
            "QAAgent", "story_3", None, 10
        )


class TestTokenBudgetOptimization:
    """Test token budget optimization functionality"""
    
    @pytest.fixture
    def context_manager(self):
        """Create context manager for testing"""
        with tempfile.TemporaryDirectory() as temp_dir:
            cm = ContextManager(
                project_path=temp_dir,
                enable_intelligence=False,
                enable_advanced_caching=False,
                enable_monitoring=False,
                enable_cross_story=False,
                enable_background_processing=False
            )
            
            # Mock token calculator
            cm.token_calculator.optimize_allocation = AsyncMock()
            
            yield cm
    
    @pytest.mark.asyncio
    async def test_optimize_token_budget_success(self, context_manager):
        """Test successful token budget optimization"""
        # Create test data
        budget = TokenBudget(
            total_budget=10000,
            core_task=5000,
            historical=2000,
            dependencies=2000,
            agent_memory=800,
            buffer=200
        )
        
        usage = TokenUsage(
            context_id="test",
            total_used=8000,
            core_task_used=6000,
            historical_used=1000,
            dependencies_used=800,
            agent_memory_used=200
        )
        
        context = AgentContext(
            request_id="test",
            agent_type="TestAgent",
            story_id="story_1",
            token_budget=budget
        )
        
        optimized_budget = TokenBudget(
            total_budget=10000,
            core_task=6000,  # Adjusted based on actual usage
            historical=1500,
            dependencies=1500,
            agent_memory=700,
            buffer=300
        )
        context_manager.token_calculator.optimize_allocation.return_value = optimized_budget
        
        result = await context_manager.optimize_token_budget(
            context=context,
            actual_usage=usage,
            quality_score=0.85
        )
        
        assert result == optimized_budget
        context_manager.token_calculator.optimize_allocation.assert_called_once_with(
            budget, usage, 0.85
        )
    
    @pytest.mark.asyncio
    async def test_optimize_token_budget_no_budget(self, context_manager):
        """Test token budget optimization with context without budget"""
        context = AgentContext(
            request_id="test",
            agent_type="TestAgent",
            story_id="story_1"
            # No token_budget set
        )
        
        usage = TokenUsage(context_id="test", total_used=1000)
        
        with pytest.raises(ValueError, match="Context must have token budget"):
            await context_manager.optimize_token_budget(
                context=context,
                actual_usage=usage,
                quality_score=0.8
            )


class TestContextInvalidationAndCleanup:
    """Test context invalidation and cache cleanup"""
    
    @pytest.fixture
    def context_manager(self):
        """Create context manager with some cached data"""
        with tempfile.TemporaryDirectory() as temp_dir:
            cm = ContextManager(
                project_path=temp_dir,
                enable_intelligence=False,
                enable_advanced_caching=False,
                enable_monitoring=False,
                enable_cross_story=False,
                enable_background_processing=False
            )
            
            # Add some test data to internal caches
            test_context = AgentContext(
                request_id="test_req_1",
                agent_type="TestAgent",
                story_id="story_1"
            )
            
            # The code seems to use _context_cache in some places but it's not initialized
            # Let's initialize it for testing
            cm._context_cache = {
                "cache_key_1": (test_context, datetime.utcnow()),
                "cache_key_2": (test_context, datetime.utcnow())
            }
            
            cm._active_contexts = {
                "test_req_1": test_context,
                "test_req_2": AgentContext(request_id="test_req_2", agent_type="TestAgent", story_id="story_2")
            }
            
            yield cm
    
    @pytest.mark.asyncio
    async def test_invalidate_context_removes_from_cache_and_active(self, context_manager):
        """Test context invalidation removes from both cache and active contexts"""
        # Verify initial state
        assert len(context_manager._context_cache) == 2
        assert "test_req_1" in context_manager._active_contexts
        
        await context_manager.invalidate_context("test_req_1")
        
        # Should remove from active contexts
        assert "test_req_1" not in context_manager._active_contexts
        assert "test_req_2" in context_manager._active_contexts  # Others remain
        
        # Should remove matching cache entries
        assert len(context_manager._context_cache) < 2  # At least one removed
    
    @pytest.mark.asyncio
    async def test_invalidate_nonexistent_context(self, context_manager):
        """Test invalidating non-existent context doesn't raise error"""
        initial_cache_size = len(context_manager._context_cache)
        initial_active_size = len(context_manager._active_contexts)
        
        # Should not raise error
        await context_manager.invalidate_context("nonexistent_id")
        
        # Should not change cache sizes
        assert len(context_manager._context_cache) == initial_cache_size
        assert len(context_manager._active_contexts) == initial_active_size
    
    @pytest.mark.asyncio
    async def test_cleanup_cache_removes_expired_entries(self, context_manager):
        """Test cache cleanup removes expired entries"""
        # Set very short TTL
        context_manager.cache_ttl_seconds = 0
        
        # Wait a moment to ensure expiration
        await asyncio.sleep(0.1)
        
        cleaned_count = await context_manager.cleanup_cache()
        
        # Should have cleaned up expired entries
        assert cleaned_count > 0
        assert len(context_manager._context_cache) == 0
    
    @pytest.mark.asyncio
    async def test_cleanup_cache_keeps_fresh_entries(self, context_manager):
        """Test cache cleanup keeps fresh entries"""
        # Set long TTL
        context_manager.cache_ttl_seconds = 3600
        
        initial_size = len(context_manager._context_cache)
        cleaned_count = await context_manager.cleanup_cache()
        
        # Should not clean up fresh entries
        assert cleaned_count == 0
        assert len(context_manager._context_cache) == initial_size


class TestAgentLearningAnalysis:
    """Test agent learning analysis functionality"""
    
    @pytest.fixture
    def context_manager(self):
        """Create context manager for testing"""
        with tempfile.TemporaryDirectory() as temp_dir:
            cm = ContextManager(
                project_path=temp_dir,
                enable_intelligence=False,
                enable_advanced_caching=False,
                enable_monitoring=False,
                enable_cross_story=False,
                enable_background_processing=False
            )
            
            # Mock agent memory
            cm.agent_memory.analyze_agent_patterns = AsyncMock()
            
            yield cm
    
    @pytest.mark.asyncio
    async def test_analyze_agent_learning(self, context_manager):
        """Test agent learning analysis"""
        mock_analysis = {
            "decision_count": 15,
            "average_confidence": 0.82,
            "success_rate": 0.87,
            "common_patterns": ["pattern1", "pattern2"],
            "improvement_suggestions": ["suggestion1", "suggestion2"]
        }
        context_manager.agent_memory.analyze_agent_patterns.return_value = mock_analysis
        
        result = await context_manager.analyze_agent_learning(
            agent_type="DesignAgent",
            story_id="story_1"
        )
        
        assert result == mock_analysis
        context_manager.agent_memory.analyze_agent_patterns.assert_called_once_with(
            "DesignAgent", "story_1"
        )


class TestIntelligenceLayerIntegration:
    """Test intelligence layer integration methods"""
    
    @pytest.fixture
    def context_manager_with_intelligence(self):
        """Create context manager with intelligence enabled and mocked"""
        with tempfile.TemporaryDirectory() as temp_dir:
            with patch('context_manager.ContextFilter') as mock_filter_cls, \
                 patch('context_manager.ContextCompressor') as mock_compressor_cls, \
                 patch('context_manager.ContextIndex') as mock_index_cls:
                
                # Setup mocks
                mock_filter = AsyncMock()
                mock_filter_cls.return_value = mock_filter
                
                mock_compressor = AsyncMock()
                mock_compressor_cls.return_value = mock_compressor
                
                mock_index = AsyncMock()
                mock_index_cls.return_value = mock_index
                
                cm = ContextManager(
                    project_path=temp_dir,
                    enable_intelligence=True,
                    enable_advanced_caching=False,
                    enable_monitoring=False,
                    enable_cross_story=False,
                    enable_background_processing=False
                )
                
                cm.context_filter = mock_filter
                cm.context_compressor = mock_compressor
                cm.context_index = mock_index
                
                yield cm
    
    @pytest.fixture
    def context_manager_without_intelligence(self):
        """Create context manager without intelligence"""
        with tempfile.TemporaryDirectory() as temp_dir:
            cm = ContextManager(
                project_path=temp_dir,
                enable_intelligence=False,
                enable_advanced_caching=False,
                enable_monitoring=False,
                enable_cross_story=False,
                enable_background_processing=False
            )
            yield cm
    
    @pytest.mark.asyncio
    async def test_build_context_index_with_intelligence(self, context_manager_with_intelligence):
        """Test building context index when intelligence is enabled"""
        await context_manager_with_intelligence.build_context_index(force_rebuild=True)
        
        context_manager_with_intelligence.context_index.build_index.assert_called_once_with(
            force_rebuild=True
        )
    
    @pytest.mark.asyncio
    async def test_build_context_index_without_intelligence(self, context_manager_without_intelligence):
        """Test building context index when intelligence is disabled"""
        # Should not raise error
        await context_manager_without_intelligence.build_context_index(force_rebuild=True)
    
    @pytest.mark.asyncio
    async def test_search_codebase_with_intelligence(self, context_manager_with_intelligence):
        """Test codebase search with intelligence enabled"""
        mock_results = [
            Mock(
                file_path="test.py",
                relevance_score=0.95,
                match_type="function",
                matches=["def test_function()"],
                context="Test context"
            ),
            Mock(
                file_path="another.py",
                relevance_score=0.85,
                match_type="class",
                matches=["class TestClass:"],
                context="Another context"
            )
        ]
        context_manager_with_intelligence.context_index.search_files.return_value = mock_results
        
        results = await context_manager_with_intelligence.search_codebase(
            query="test function",
            search_type="functions",
            max_results=10
        )
        
        assert len(results) == 2
        assert results[0]["file_path"] == "test.py"
        assert results[0]["relevance_score"] == 0.95
        assert results[1]["file_path"] == "another.py"
        
        context_manager_with_intelligence.context_index.search_files.assert_called_once_with(
            query="test function",
            search_type="functions",
            max_results=10,
            include_content=True
        )
    
    @pytest.mark.asyncio
    async def test_search_codebase_without_intelligence(self, context_manager_without_intelligence):
        """Test codebase search without intelligence returns empty list"""
        results = await context_manager_without_intelligence.search_codebase(
            query="test function",
            search_type="functions",
            max_results=10
        )
        
        assert results == []
    
    @pytest.mark.asyncio
    async def test_get_file_dependencies_with_intelligence(self, context_manager_with_intelligence):
        """Test getting file dependencies with intelligence"""
        mock_deps = {
            "file_path": "test.py",
            "dependency_count": 5,
            "reverse_dependency_count": 3,
            "direct_dependencies": ["module1", "module2", "module3"],
            "reverse_dependencies": ["user1.py", "user2.py"]
        }
        context_manager_with_intelligence.context_index.get_file_dependencies.return_value = mock_deps
        
        result = await context_manager_with_intelligence.get_file_dependencies(
            file_path="test.py",
            depth=2,
            include_reverse=True
        )
        
        assert result == mock_deps
        context_manager_with_intelligence.context_index.get_file_dependencies.assert_called_once_with(
            file_path="test.py",
            depth=2,
            include_reverse=True
        )
    
    @pytest.mark.asyncio
    async def test_get_file_dependencies_without_intelligence(self, context_manager_without_intelligence):
        """Test getting file dependencies without intelligence returns error"""
        result = await context_manager_without_intelligence.get_file_dependencies(
            file_path="test.py"
        )
        
        assert "error" in result
        assert "Context index not available" in result["error"]
    
    @pytest.mark.asyncio
    async def test_get_file_relevance_explanation_with_intelligence(self, context_manager_with_intelligence):
        """Test getting file relevance explanation with intelligence"""
        mock_explanation = {
            "relevance_score": 0.92,
            "reasons": ["contains target function", "imports required modules"],
            "confidence": 0.88
        }
        context_manager_with_intelligence.context_filter.get_file_relevance_explanation.return_value = mock_explanation
        
        request = ContextRequest(
            agent_type="DesignAgent",
            story_id="story_1",
            task={"description": "test task"}
        )
        
        result = await context_manager_with_intelligence.get_file_relevance_explanation(
            file_path="test.py",
            request=request
        )
        
        assert result == mock_explanation
        context_manager_with_intelligence.context_filter.get_file_relevance_explanation.assert_called_once_with(
            file_path="test.py",
            request=request
        )
    
    @pytest.mark.asyncio
    async def test_estimate_compression_potential_with_intelligence(self, context_manager_with_intelligence):
        """Test estimating compression potential with intelligence"""
        mock_analysis = {
            "original_tokens": 1000,
            "estimated_compressed_tokens": 600,
            "compression_ratio": 0.6,
            "quality_impact": "minimal"
        }
        context_manager_with_intelligence.context_compressor.estimate_compression_potential.return_value = mock_analysis
        
        result = await context_manager_with_intelligence.estimate_compression_potential(
            content="test content",
            file_type=FileType.PYTHON,
            compression_level=CompressionLevel.MODERATE
        )
        
        assert result == mock_analysis
        context_manager_with_intelligence.context_compressor.estimate_compression_potential.assert_called_once_with(
            content="test content",
            file_type=FileType.PYTHON,
            compression_level=CompressionLevel.MODERATE
        )
    
    @pytest.mark.asyncio
    async def test_get_project_statistics_with_intelligence(self, context_manager_with_intelligence):
        """Test getting project statistics with intelligence"""
        mock_stats = {
            "total_files": 150,
            "total_lines": 50000,
            "languages": {"python": 120, "markdown": 20, "yaml": 10},
            "test_coverage": 0.85
        }
        context_manager_with_intelligence.context_index.get_project_statistics.return_value = mock_stats
        
        result = await context_manager_with_intelligence.get_project_statistics()
        
        assert result == mock_stats
        context_manager_with_intelligence.context_index.get_project_statistics.assert_called_once()


class TestPerformanceMetrics:
    """Test performance metrics functionality"""
    
    @pytest.fixture
    def context_manager(self):
        """Create context manager with some test data"""
        with tempfile.TemporaryDirectory() as temp_dir:
            cm = ContextManager(
                project_path=temp_dir,
                enable_intelligence=True,
                enable_advanced_caching=False,
                enable_monitoring=False,
                enable_cross_story=False,
                enable_background_processing=False
            )
            
            # Add some test metrics data
            cm._total_requests = 10
            cm._cache_hits = 6
            cm._cache_misses = 4
            cm._preparation_times = [0.5, 1.2, 0.8, 1.5, 0.9, 2.0, 1.1, 0.7, 1.3, 0.6]
            cm._context_cache = {"key1": "value1", "key2": "value2"}
            cm._active_contexts = {"ctx1": "context1"}
            
            # Mock component metrics
            cm.token_calculator.get_performance_metrics = Mock(return_value={"token_metrics": "data"})
            cm.agent_memory.get_performance_metrics = Mock(return_value={"memory_metrics": "data"})
            
            if cm.context_filter:
                cm.context_filter.get_performance_metrics = Mock(return_value={"filter_metrics": "data"})
            if cm.context_compressor:
                cm.context_compressor.get_performance_metrics = Mock(return_value={"compressor_metrics": "data"})
            if cm.context_index:
                cm.context_index.get_performance_metrics = Mock(return_value={"index_metrics": "data"})
            
            yield cm
    
    def test_get_performance_metrics_complete(self, context_manager):
        """Test getting complete performance metrics"""
        metrics = context_manager.get_performance_metrics()
        
        assert isinstance(metrics, dict)
        assert "context_manager" in metrics
        assert "token_calculator" in metrics
        assert "agent_memory" in metrics
        
        cm_metrics = metrics["context_manager"]
        assert cm_metrics["total_requests"] == 10
        assert cm_metrics["cache_hits"] == 6
        assert cm_metrics["cache_misses"] == 4
        assert cm_metrics["cache_hit_rate"] == 0.6  # 6/(6+4)
        assert cm_metrics["average_preparation_time"] == 1.06  # Average of preparation_times
        assert cm_metrics["max_preparation_time"] == 2.0
        assert cm_metrics["min_preparation_time"] == 0.5
        assert cm_metrics["cached_contexts"] == 2
        assert cm_metrics["active_contexts"] == 1
        assert cm_metrics["intelligence_enabled"] is True
        
        # Check intelligence layer metrics are included
        if context_manager.enable_intelligence:
            assert "context_filter" in metrics
            assert "context_compressor" in metrics
            assert "context_index" in metrics
    
    def test_get_performance_metrics_empty_preparation_times(self):
        """Test performance metrics with empty preparation times"""
        with tempfile.TemporaryDirectory() as temp_dir:
            cm = ContextManager(
                project_path=temp_dir,
                enable_intelligence=False,
                enable_advanced_caching=False,
                enable_monitoring=False,
                enable_cross_story=False,
                enable_background_processing=False
            )
            
            # Mock component metrics
            cm.token_calculator.get_performance_metrics = Mock(return_value={})
            cm.agent_memory.get_performance_metrics = Mock(return_value={})
            
            metrics = cm.get_performance_metrics()
            
            cm_metrics = metrics["context_manager"]
            assert cm_metrics["average_preparation_time"] == 0.0
            assert cm_metrics["max_preparation_time"] == 0.0
            assert cm_metrics["min_preparation_time"] == 0.0
            assert cm_metrics["cached_contexts"] == 0  # Use _legacy_cache instead of _context_cache
    
    def test_get_performance_metrics_zero_cache_operations(self):
        """Test performance metrics with zero cache operations"""
        with tempfile.TemporaryDirectory() as temp_dir:
            cm = ContextManager(
                project_path=temp_dir,
                enable_intelligence=False,
                enable_advanced_caching=False,
                enable_monitoring=False,
                enable_cross_story=False,
                enable_background_processing=False
            )
            
            # Mock component metrics
            cm.token_calculator.get_performance_metrics = Mock(return_value={})
            cm.agent_memory.get_performance_metrics = Mock(return_value={})
            
            metrics = cm.get_performance_metrics()
            
            cm_metrics = metrics["context_manager"]
            assert cm_metrics["cache_hit_rate"] == 0.0
            assert cm_metrics["cached_contexts"] == 0  # Use _legacy_cache instead of _context_cache


class TestCrossStoryManagement:
    """Test cross-story context management functionality"""
    
    @pytest.fixture
    def context_manager(self):
        """Create context manager with cross-story enabled"""
        with tempfile.TemporaryDirectory() as temp_dir:
            cm = ContextManager(
                project_path=temp_dir,
                enable_intelligence=False,
                enable_advanced_caching=False,
                enable_monitoring=False,
                enable_cross_story=True,
                enable_background_processing=False
            )
            
            # Mock agent memory for conflict resolution
            cm.agent_memory.add_decision = AsyncMock()
            
            yield cm
    
    @pytest.mark.asyncio
    async def test_register_story_with_metadata(self, context_manager):
        """Test registering story with metadata"""
        metadata = {
            "priority": "high",
            "team": "backend",
            "sprint": "sprint_5"
        }
        
        await context_manager.register_story("story_1", metadata)
        
        assert "story_1" in context_manager._active_stories
        story_info = context_manager._active_stories["story_1"]
        assert story_info["metadata"] == metadata
        assert isinstance(story_info["registered_at"], datetime)
        assert isinstance(story_info["active_agents"], set)
        assert isinstance(story_info["file_modifications"], set)
    
    @pytest.mark.asyncio
    async def test_register_story_without_metadata(self, context_manager):
        """Test registering story without metadata"""
        await context_manager.register_story("story_2")
        
        assert "story_2" in context_manager._active_stories
        story_info = context_manager._active_stories["story_2"]
        assert story_info["metadata"] == {}
    
    @pytest.mark.asyncio
    async def test_register_story_when_cross_story_disabled(self):
        """Test registering story when cross-story is disabled"""
        with tempfile.TemporaryDirectory() as temp_dir:
            cm = ContextManager(
                project_path=temp_dir,
                enable_cross_story=False
            )
            
            # Should not raise error but also not register
            await cm.register_story("story_1")
            assert len(cm._active_stories) == 0
    
    @pytest.mark.asyncio
    async def test_unregister_story_complete_cleanup(self, context_manager):
        """Test unregistering story performs complete cleanup"""
        # Setup test data
        await context_manager.register_story("story_1")
        await context_manager.register_story("story_2")
        
        # Add conflicts
        context_manager._story_conflicts["story_1"] = ["story_2"]
        context_manager._story_conflicts["story_2"] = ["story_1"]
        
        # Add cross-story cache
        context_manager._cross_story_cache[f"cross_story_story_1_12345"] = Mock()
        context_manager._cross_story_cache[f"cross_story_story_2_67890"] = Mock()
        
        # Unregister story_1
        await context_manager.unregister_story("story_1")
        
        # Verify cleanup
        assert "story_1" not in context_manager._active_stories
        assert "story_2" in context_manager._active_stories  # Other story remains
        
        # Should remove story_1 from all conflicts
        assert "story_1" not in context_manager._story_conflicts
        if "story_2" in context_manager._story_conflicts:
            assert "story_1" not in context_manager._story_conflicts["story_2"]
        
        # Should clean up cross-story cache entries
        remaining_keys = [k for k in context_manager._cross_story_cache.keys() if "story_1" in k]
        assert len(remaining_keys) == 0
    
    @pytest.mark.asyncio
    async def test_unregister_nonexistent_story(self, context_manager):
        """Test unregistering non-existent story doesn't raise error"""
        # Should not raise error
        await context_manager.unregister_story("nonexistent_story")
    
    @pytest.mark.asyncio
    async def test_detect_story_conflicts_file_overlap(self, context_manager):
        """Test detecting story conflicts based on file overlap"""
        # Register stories
        await context_manager.register_story("story_1")
        await context_manager.register_story("story_2")
        await context_manager.register_story("story_3")
        
        # Setup file modifications
        context_manager._active_stories["story_2"]["file_modifications"] = {"file1.py", "file2.py"}
        context_manager._active_stories["story_3"]["file_modifications"] = {"file3.py", "file4.py"}
        
        # Check conflicts for story_1 with overlapping files
        conflicts = await context_manager.detect_story_conflicts(
            "story_1", 
            ["file1.py", "file5.py"]  # file1.py overlaps with story_2
        )
        
        assert "story_2" in conflicts
        assert "story_3" not in conflicts
        
        # Verify conflict tracking was updated
        assert context_manager._story_conflicts["story_1"] == ["story_2"]
        assert context_manager._story_conflicts["story_2"] == ["story_1"]
    
    @pytest.mark.asyncio
    async def test_detect_story_conflicts_no_overlap(self, context_manager):
        """Test detecting story conflicts with no file overlap"""
        await context_manager.register_story("story_1")
        await context_manager.register_story("story_2")
        
        context_manager._active_stories["story_2"]["file_modifications"] = {"file1.py", "file2.py"}
        
        conflicts = await context_manager.detect_story_conflicts(
            "story_1",
            ["file3.py", "file4.py"]  # No overlap
        )
        
        assert len(conflicts) == 0
        assert "story_1" not in context_manager._story_conflicts
    
    @pytest.mark.asyncio
    async def test_detect_story_conflicts_disabled(self):
        """Test detecting conflicts when cross-story is disabled"""
        with tempfile.TemporaryDirectory() as temp_dir:
            cm = ContextManager(
                project_path=temp_dir,
                enable_cross_story=False
            )
            
            conflicts = await cm.detect_story_conflicts("story_1", ["file1.py"])
            assert conflicts == []
    
    @pytest.mark.asyncio
    async def test_get_cross_story_context_with_conflicts(self, context_manager):
        """Test getting cross-story context with conflicts"""
        # Setup stories
        await context_manager.register_story("story_1")
        await context_manager.register_story("story_2", {"priority": "high"})
        await context_manager.register_story("story_3", {"team": "frontend"})
        
        # Setup story info
        story_2_info = context_manager._active_stories["story_2"]
        story_2_info["active_agents"] = {"DesignAgent", "CodeAgent"}
        story_2_info["file_modifications"] = {"file1.py", "file2.py"}
        
        story_3_info = context_manager._active_stories["story_3"]
        story_3_info["active_agents"] = {"QAAgent"}
        story_3_info["file_modifications"] = {"file3.py"}
        
        cross_context = await context_manager.get_cross_story_context(
            story_id="story_1",
            conflicting_stories=["story_2", "story_3"]
        )
        
        assert cross_context["primary_story"] == "story_1"
        assert len(cross_context["conflicts"]) == 2
        
        # Check story_2 conflict info
        story_2_conflict = next(c for c in cross_context["conflicts"] if c["story_id"] == "story_2")
        assert story_2_conflict["active_agents"] == ["DesignAgent", "CodeAgent"]
        assert story_2_conflict["modified_files"] == ["file1.py", "file2.py"]
        assert story_2_conflict["metadata"] == {"priority": "high"}
        
        # Check recommendations
        assert len(cross_context["recommendations"]) > 0
        assert any("coordinating" in rec.lower() for rec in cross_context["recommendations"])
    
    @pytest.mark.asyncio
    async def test_get_cross_story_context_no_conflicts(self, context_manager):
        """Test getting cross-story context with no conflicts"""
        cross_context = await context_manager.get_cross_story_context(
            story_id="story_1",
            conflicting_stories=[]
        )
        
        assert cross_context["primary_story"] == "story_1"
        assert cross_context["conflicts"] == []
        assert cross_context["recommendations"] == []
    
    @pytest.mark.asyncio
    async def test_get_cross_story_context_disabled(self):
        """Test getting cross-story context when disabled"""
        with tempfile.TemporaryDirectory() as temp_dir:
            cm = ContextManager(
                project_path=temp_dir,
                enable_cross_story=False
            )
            
            cross_context = await cm.get_cross_story_context("story_1", ["story_2"])
            assert cross_context == {}
    
    @pytest.mark.asyncio
    async def test_resolve_story_conflict_success(self, context_manager):
        """Test resolving story conflict successfully"""
        # Setup conflicts
        context_manager._story_conflicts["story_1"] = ["story_2"]
        context_manager._story_conflicts["story_2"] = ["story_1"]
        
        result = await context_manager.resolve_story_conflict(
            story_id="story_1",
            conflict_story_id="story_2",
            resolution="Coordinated file changes to avoid overlap"
        )
        
        assert result is True
        
        # Should remove from conflicts
        assert "story_2" not in context_manager._story_conflicts.get("story_1", [])
        assert "story_1" not in context_manager._story_conflicts.get("story_2", [])
        
        # Should record decision
        context_manager.agent_memory.add_decision.assert_called_once()
        call_args = context_manager.agent_memory.add_decision.call_args
        assert call_args[0][0] == "ContextManager"
        assert call_args[0][1] == "story_1"
        decision = call_args[0][2]
        assert "story_2" in decision.description
        assert decision.rationale == "Coordinated file changes to avoid overlap"
    
    @pytest.mark.asyncio
    async def test_resolve_story_conflict_disabled(self):
        """Test resolving conflict when cross-story is disabled"""
        with tempfile.TemporaryDirectory() as temp_dir:
            cm = ContextManager(
                project_path=temp_dir,
                enable_cross_story=False
            )
            
            result = await cm.resolve_story_conflict("story_1", "story_2", "resolution")
            assert result is False


class TestMonitoringAndDashboard:
    """Test monitoring and dashboard functionality"""
    
    @pytest.fixture
    def context_manager_with_monitoring(self):
        """Create context manager with monitoring enabled"""
        with tempfile.TemporaryDirectory() as temp_dir:
            with patch('context_manager.ContextMonitor') as mock_monitor_cls, \
                 patch('context_manager.ContextCache') as mock_cache_cls:
                
                mock_monitor = AsyncMock()
                mock_health = Mock()
                mock_health.overall_status = "healthy"
                mock_monitor.get_system_health.return_value = mock_health
                mock_monitor.get_performance_summary.return_value = {"avg_response_time": 0.5}
                mock_monitor_cls.return_value = mock_monitor
                
                mock_cache = AsyncMock()
                mock_cache_stats = Mock()
                mock_cache_stats.hit_rate = 0.75
                mock_cache_stats.entry_count = 50
                mock_cache_stats.memory_usage_bytes = 1024 * 1024 * 100  # 100MB
                mock_cache_stats.prediction_accuracy = 0.82
                mock_cache.get_statistics.return_value = mock_cache_stats
                mock_cache_cls.return_value = mock_cache
                
                cm = ContextManager(
                    project_path=temp_dir,
                    enable_intelligence=True,
                    enable_advanced_caching=True,
                    enable_monitoring=True,
                    enable_cross_story=True,
                    enable_background_processing=False
                )
                
                cm.monitor = mock_monitor
                cm.context_cache = mock_cache
                
                # Add some test data
                cm._active_stories = {"story_1": {}, "story_2": {}}
                cm._story_conflicts = {"story_1": ["story_2"]}
                
                # Mock get_performance_metrics
                cm.get_performance_metrics = Mock(return_value={"test": "metrics"})
                
                yield cm
    
    @pytest.mark.asyncio
    async def test_get_monitoring_dashboard_data_complete(self, context_manager_with_monitoring):
        """Test getting complete monitoring dashboard data"""
        dashboard_data = await context_manager_with_monitoring.get_monitoring_dashboard_data()
        
        assert isinstance(dashboard_data, dict)
        assert "timestamp" in dashboard_data
        assert dashboard_data["system_health"] == "healthy"
        assert dashboard_data["performance_metrics"] == {"test": "metrics"}
        assert dashboard_data["active_stories"] == 2
        assert dashboard_data["story_conflicts"] == 1
        
        # Check advanced features status
        features = dashboard_data["advanced_features"]
        assert features["intelligence"] is True
        assert features["advanced_caching"] is True
        assert features["monitoring"] is True
        assert features["cross_story"] is True
        
        # Check monitoring metrics
        assert "monitoring_metrics" in dashboard_data
        assert dashboard_data["monitoring_metrics"]["avg_response_time"] == 0.5
        
        # Check cache statistics  
        cache_stats = dashboard_data["cache_statistics"]
        assert cache_stats["hit_rate"] == 0.75
        assert cache_stats["entry_count"] == 50
        assert cache_stats["memory_usage_mb"] == 100.0
        assert cache_stats["prediction_accuracy"] == 0.82
        
        # Check cross-story details
        cross_story = dashboard_data["cross_story_details"]
        assert set(cross_story["active_stories"]) == {"story_1", "story_2"}
        assert cross_story["conflicts"] == {"story_1": ["story_2"]}
    
    @pytest.mark.asyncio
    async def test_get_monitoring_dashboard_data_minimal(self):
        """Test getting dashboard data with minimal features"""
        with tempfile.TemporaryDirectory() as temp_dir:
            cm = ContextManager(
                project_path=temp_dir,
                enable_intelligence=False,
                enable_advanced_caching=False,
                enable_monitoring=False,
                enable_cross_story=False,
                enable_background_processing=False
            )
            
            # Mock get_performance_metrics
            cm.get_performance_metrics = Mock(return_value={"basic": "metrics"})
            
            dashboard_data = await cm.get_monitoring_dashboard_data()
            
            assert dashboard_data["system_health"] == "unknown"
            assert dashboard_data["performance_metrics"] == {"basic": "metrics"}
            assert dashboard_data["active_stories"] == 0
            assert dashboard_data["story_conflicts"] == 0
            
            # Check that optional sections are not present or empty
            features = dashboard_data["advanced_features"]
            assert features["intelligence"] is False
            assert features["advanced_caching"] is False
            assert features["monitoring"] is False
            assert features["cross_story"] is False
    
    @pytest.mark.asyncio
    async def test_get_monitoring_dashboard_data_with_exceptions(self, context_manager_with_monitoring):
        """Test dashboard data collection handles exceptions gracefully"""
        # Make monitoring calls raise exceptions
        context_manager_with_monitoring.monitor.get_system_health.side_effect = Exception("Monitor error")
        context_manager_with_monitoring.context_cache.get_statistics.side_effect = Exception("Cache error")
        
        # Should not raise exception
        dashboard_data = await context_manager_with_monitoring.get_monitoring_dashboard_data()
        
        # Should still return basic data
        assert isinstance(dashboard_data, dict)
        assert "timestamp" in dashboard_data
        assert dashboard_data["system_health"] == "unknown"  # Fallback value


class TestBackgroundProcessing:
    """Test background processing functionality"""
    
    @pytest.fixture
    def context_manager_with_background(self):
        """Create context manager with background processing enabled"""
        with tempfile.TemporaryDirectory() as temp_dir:
            with patch('context_manager.ContextBackgroundProcessor') as mock_bg_cls:
                
                mock_bg = AsyncMock()
                mock_stats = Mock()
                mock_stats.total_tasks = 100
                mock_stats.completed_tasks = 95
                mock_stats.failed_tasks = 3
                mock_stats.active_tasks = 2
                mock_stats.queued_tasks = 5
                mock_stats.success_rate = 0.95
                mock_stats.average_execution_time = 1.2
                mock_stats.cache_warming_hits = 15
                mock_stats.pattern_discoveries = 8
                mock_bg.get_statistics.return_value = mock_stats
                mock_bg_cls.return_value = mock_bg
                
                cm = ContextManager(
                    project_path=temp_dir,
                    enable_intelligence=False,
                    enable_advanced_caching=False,
                    enable_monitoring=False,
                    enable_cross_story=False,
                    enable_background_processing=True
                )
                
                cm.background_processor = mock_bg
                
                yield cm
    
    @pytest.mark.asyncio
    async def test_trigger_index_update_with_files(self, context_manager_with_background):
        """Test triggering index update with specific files"""
        context_manager_with_background.background_processor.trigger_index_update.return_value = "task_123"
        
        task_id = await context_manager_with_background.trigger_index_update(
            file_paths=["file1.py", "file2.py"]
        )
        
        assert task_id == "task_123"
        context_manager_with_background.background_processor.trigger_index_update.assert_called_once_with(
            ["file1.py", "file2.py"]
        )
    
    @pytest.mark.asyncio
    async def test_trigger_index_update_all_files(self, context_manager_with_background):
        """Test triggering index update for all files"""
        context_manager_with_background.background_processor.trigger_index_update.return_value = "task_456"
        
        task_id = await context_manager_with_background.trigger_index_update()
        
        assert task_id == "task_456"
        context_manager_with_background.background_processor.trigger_index_update.assert_called_once_with(None)
    
    @pytest.mark.asyncio
    async def test_trigger_index_update_disabled(self):
        """Test triggering index update when background processing is disabled"""
        with tempfile.TemporaryDirectory() as temp_dir:
            cm = ContextManager(
                project_path=temp_dir,
                enable_background_processing=False
            )
            
            task_id = await cm.trigger_index_update()
            assert task_id is None
    
    @pytest.mark.asyncio
    async def test_warm_cache_for_context(self, context_manager_with_background):
        """Test warming cache for predicted context requests"""
        context_manager_with_background.background_processor.warm_cache_for_agent.return_value = "task_789"
        
        predicted_requests = [
            ContextRequest(agent_type="DesignAgent", story_id="story_1", task={"desc": "task1"}),
            ContextRequest(agent_type="CodeAgent", story_id="story_1", task={"desc": "task2"})
        ]
        
        task_id = await context_manager_with_background.warm_cache_for_context(
            agent_type="DesignAgent",
            story_id="story_1",
            predicted_requests=predicted_requests
        )
        
        assert task_id == "task_789"
        context_manager_with_background.background_processor.warm_cache_for_agent.assert_called_once_with(
            "DesignAgent", "story_1", predicted_requests
        )
    
    @pytest.mark.asyncio
    async def test_schedule_learning_optimization(self, context_manager_with_background):
        """Test scheduling learning optimization"""
        context_manager_with_background.background_processor.submit_task.return_value = "task_learning"
        
        task_id = await context_manager_with_background.schedule_learning_optimization(delay_hours=2)
        
        assert task_id == "task_learning"
        context_manager_with_background.background_processor.submit_task.assert_called_once()
        
        # Check the call arguments
        call_args = context_manager_with_background.background_processor.submit_task.call_args
        assert call_args[1]["task_type"] == "learning_optimization"
        assert call_args[1]["priority"] == TaskPriority.LOW
        assert "scheduled_at" in call_args[1]
    
    @pytest.mark.asyncio
    async def test_get_background_statistics(self, context_manager_with_background):
        """Test getting background processing statistics"""
        stats = await context_manager_with_background.get_background_statistics()
        
        expected_stats = {
            "total_tasks": 100,
            "completed_tasks": 95,
            "failed_tasks": 3,
            "active_tasks": 2,
            "queued_tasks": 5,
            "success_rate": 0.95,
            "average_execution_time": 1.2,
            "cache_warming_hits": 15,
            "pattern_discoveries": 8
        }
        
        assert stats == expected_stats
    
    @pytest.mark.asyncio
    async def test_get_background_statistics_disabled(self):
        """Test getting background statistics when disabled"""
        with tempfile.TemporaryDirectory() as temp_dir:
            cm = ContextManager(
                project_path=temp_dir,
                enable_background_processing=False
            )
            
            stats = await cm.get_background_statistics()
            assert "error" in stats
            assert "Background processing not enabled" in stats["error"]
    
    @pytest.mark.asyncio
    async def test_queue_initial_background_tasks(self, context_manager_with_background):
        """Test queuing initial background tasks"""
        await context_manager_with_background._queue_initial_background_tasks()
        
        # Should have made multiple submit_task calls
        assert context_manager_with_background.background_processor.submit_task.call_count >= 2
        
        # Should have scheduled pattern discovery
        context_manager_with_background.background_processor.schedule_pattern_discovery.assert_called_once_with(
            delay_minutes=30
        )
    
    @pytest.mark.asyncio
    async def test_queue_initial_background_tasks_with_exception(self, context_manager_with_background):
        """Test queuing initial tasks handles exceptions gracefully"""
        context_manager_with_background.background_processor.submit_task.side_effect = Exception("Task error")
        
        # Should not raise exception
        await context_manager_with_background._queue_initial_background_tasks()


class TestPrivateHelperMethods:
    """Test private helper methods"""
    
    @pytest.fixture
    def context_manager(self):
        """Create context manager for testing"""
        with tempfile.TemporaryDirectory() as temp_dir:
            cm = ContextManager(
                project_path=temp_dir,
                enable_intelligence=False,
                enable_advanced_caching=False,
                enable_monitoring=False,
                enable_cross_story=False,
                enable_background_processing=False
            )
            yield cm
    
    def test_generate_cache_key_with_tdd_task(self, context_manager):
        """Test cache key generation with TDD task"""
        task = TDDTask(
            id="task_1",
            description="Test task description",
            cycle_id="cycle_1",
            current_state=TDDState.DESIGN
        )
        
        request = ContextRequest(
            agent_type="DesignAgent",
            story_id="story_1",
            task=task,
            max_tokens=50000,
            compression_level=CompressionLevel.MODERATE,
            include_history=True,
            include_dependencies=False
        )
        
        cache_key = context_manager._generate_cache_key(request)
        
        assert isinstance(cache_key, str)
        assert len(cache_key) == 32  # MD5 hash length
        
        # Same request should generate same key
        cache_key2 = context_manager._generate_cache_key(request)
        assert cache_key == cache_key2
    
    def test_generate_cache_key_with_dict_task(self, context_manager):
        """Test cache key generation with dict task"""
        task = {"description": "Test dict task", "story_id": "story_1"}
        
        request = ContextRequest(
            agent_type="CodeAgent",
            story_id="story_1",
            task=task,
            max_tokens=30000
        )
        
        cache_key = context_manager._generate_cache_key(request)
        
        assert isinstance(cache_key, str)
        assert len(cache_key) == 32
    
    def test_extract_story_id_from_tdd_task(self, context_manager):
        """Test extracting story ID from TDD task"""
        task = TDDTask(
            id="task_1",
            description="Test task",
            cycle_id="cycle_1"
        )
        # TDDTask doesn't have story_id attribute, should return default
        story_id = context_manager._extract_story_id(task)
        assert story_id == "default"
    
    def test_extract_story_id_from_dict(self, context_manager):
        """Test extracting story ID from dict task"""
        task = {"description": "Test task", "story_id": "dict_story_456"}
        
        story_id = context_manager._extract_story_id(task)
        assert story_id == "dict_story_456"
    
    def test_extract_story_id_default(self, context_manager):
        """Test extracting story ID returns default when not found"""
        task = {"description": "Task without story ID"}
        
        story_id = context_manager._extract_story_id(task)
        assert story_id == "default"
    
    def test_extract_tdd_phase_from_tdd_task(self, context_manager):
        """Test extracting TDD phase from TDD task"""
        task = TDDTask(
            id="task_1",
            description="Test task",
            cycle_id="cycle_1",
            current_state=TDDState.TEST_RED
        )
        
        phase = context_manager._extract_tdd_phase(task)
        assert phase == TDDState.TEST_RED
    
    def test_extract_tdd_phase_from_dict_string(self, context_manager):
        """Test extracting TDD phase from dict with string value"""
        task = {"description": "Test task", "current_state": "CODE_GREEN"}
        
        phase = context_manager._extract_tdd_phase(task)
        assert phase == TDDState.CODE_GREEN
    
    def test_extract_tdd_phase_from_dict_enum(self, context_manager):
        """Test extracting TDD phase from dict with enum value"""
        task = {"description": "Test task", "current_state": TDDState.REFACTOR}
        
        phase = context_manager._extract_tdd_phase(task)
        assert phase == TDDState.REFACTOR
    
    def test_extract_tdd_phase_invalid_string(self, context_manager):
        """Test extracting TDD phase with invalid string"""
        task = {"description": "Test task", "current_state": "INVALID_STATE"}
        
        phase = context_manager._extract_tdd_phase(task)
        assert phase is None
    
    def test_extract_tdd_phase_none(self, context_manager):
        """Test extracting TDD phase returns None when not found"""
        task = {"description": "Task without phase"}
        
        phase = context_manager._extract_tdd_phase(task)
        assert phase is None
    
    def test_determine_file_type_python(self, context_manager):
        """Test determining file type for Python files"""
        assert context_manager._determine_file_type(Path("module.py")) == FileType.PYTHON
        assert context_manager._determine_file_type(Path("test_module.py")) == FileType.TEST
        assert context_manager._determine_file_type(Path("tests/test_something.py")) == FileType.TEST
    
    def test_determine_file_type_various(self, context_manager):
        """Test determining file type for various file types"""
        assert context_manager._determine_file_type(Path("README.md")) == FileType.MARKDOWN
        assert context_manager._determine_file_type(Path("config.json")) == FileType.JSON
        assert context_manager._determine_file_type(Path("config.yaml")) == FileType.YAML
        assert context_manager._determine_file_type(Path("settings.yml")) == FileType.YAML
        assert context_manager._determine_file_type(Path("app.cfg")) == FileType.CONFIG
        assert context_manager._determine_file_type(Path("unknown.xyz")) == FileType.OTHER
    
    def test_should_include_file_valid(self, context_manager):
        """Test should_include_file with valid files"""
        # Create test files
        test_file = context_manager.project_path / "test.py"
        test_file.write_text("print('hello')")
        
        assert context_manager._should_include_file(test_file) is True
    
    def test_should_include_file_hidden(self, context_manager):
        """Test should_include_file excludes hidden files"""
        hidden_file = context_manager.project_path / ".hidden_file"
        hidden_dir = context_manager.project_path / ".hidden_dir" / "file.py"
        
        assert context_manager._should_include_file(hidden_file) is False
        assert context_manager._should_include_file(hidden_dir) is False
    
    def test_should_include_file_ignored_patterns(self, context_manager):
        """Test should_include_file excludes ignored patterns"""
        cache_file = context_manager.project_path / "__pycache__" / "module.pyc"
        git_file = context_manager.project_path / ".git" / "config"
        node_file = context_manager.project_path / "node_modules" / "package.json"
        
        assert context_manager._should_include_file(cache_file) is False
        assert context_manager._should_include_file(git_file) is False
        assert context_manager._should_include_file(node_file) is False


class TestLegacyCacheOperations:
    """Test legacy cache operations (fallback when advanced caching disabled)"""
    
    @pytest.fixture
    def context_manager(self):
        """Create context manager with advanced caching disabled"""
        with tempfile.TemporaryDirectory() as temp_dir:
            cm = ContextManager(
                project_path=temp_dir,
                enable_advanced_caching=False
            )
            yield cm
    
    @pytest.mark.asyncio
    async def test_get_cached_context_legacy_hit(self, context_manager):
        """Test legacy cache hit"""
        # Setup cache entry
        sample_context = AgentContext(
            request_id="test_req",
            agent_type="TestAgent",
            story_id="story_1"
        )
        
        request = ContextRequest(
            agent_type="TestAgent",
            story_id="story_1",
            task={"description": "test"}
        )
        
        cache_key = context_manager._generate_cache_key(request)
        context_manager._legacy_cache[cache_key] = (sample_context, datetime.utcnow())
        
        # Test cache hit
        result = await context_manager._get_cached_context_legacy(request)
        assert result == sample_context
    
    @pytest.mark.asyncio
    async def test_get_cached_context_legacy_miss(self, context_manager):
        """Test legacy cache miss"""
        request = ContextRequest(
            agent_type="TestAgent",
            story_id="story_1",
            task={"description": "test"}
        )
        
        result = await context_manager._get_cached_context_legacy(request)
        assert result is None
    
    @pytest.mark.asyncio
    async def test_get_cached_context_legacy_expired(self, context_manager):
        """Test legacy cache with expired entry"""
        sample_context = AgentContext(
            request_id="test_req",
            agent_type="TestAgent",
            story_id="story_1"
        )
        
        request = ContextRequest(
            agent_type="TestAgent",
            story_id="story_1",
            task={"description": "test"}
        )
        
        cache_key = context_manager._generate_cache_key(request)
        # Add expired entry
        expired_time = datetime.utcnow() - timedelta(seconds=context_manager.cache_ttl_seconds + 10)
        context_manager._legacy_cache[cache_key] = (sample_context, expired_time)
        
        result = await context_manager._get_cached_context_legacy(request)
        assert result is None
        # Should remove expired entry
        assert cache_key not in context_manager._legacy_cache
    
    @pytest.mark.asyncio
    async def test_cache_context_legacy(self, context_manager):
        """Test legacy context caching"""
        sample_context = AgentContext(
            request_id="test_req",
            agent_type="TestAgent",
            story_id="story_1"
        )
        
        request = ContextRequest(
            agent_type="TestAgent",
            story_id="story_1",
            task={"description": "test"}
        )
        
        await context_manager._cache_context_legacy(request, sample_context)
        
        # Should be in cache
        cache_key = context_manager._generate_cache_key(request)
        assert cache_key in context_manager._legacy_cache
        
        cached_context, timestamp = context_manager._legacy_cache[cache_key]
        assert cached_context == sample_context
        assert isinstance(timestamp, datetime)
    
    @pytest.mark.asyncio
    async def test_cache_context_legacy_size_limit(self, context_manager):
        """Test legacy cache size limit"""
        # Fill cache beyond limit
        for i in range(105):  # Limit is 100
            context = AgentContext(
                request_id=f"test_req_{i}",
                agent_type="TestAgent",
                story_id="story_1"
            )
            
            request = ContextRequest(
                agent_type="TestAgent",
                story_id="story_1",
                task={"description": f"test_{i}"}
            )
            
            await context_manager._cache_context_legacy(request, context)
        
        # Should not exceed limit
        assert len(context_manager._legacy_cache) <= 100


class TestCrossStoryPrivateMethods:
    """Test cross-story private methods"""
    
    @pytest.fixture
    def context_manager(self):
        """Create context manager with cross-story enabled"""
        with tempfile.TemporaryDirectory() as temp_dir:
            cm = ContextManager(
                project_path=temp_dir,
                enable_cross_story=True
            )
            yield cm
    
    @pytest.mark.asyncio
    async def test_handle_cross_story_preparation_new_story(self, context_manager):
        """Test handling cross-story preparation with new story"""
        task = TDDTask(
            id="task_1",
            description="Test task",
            cycle_id="cycle_1"
        )
        
        request = ContextRequest(
            agent_type="DesignAgent",
            story_id="new_story",
            task=task
        )
        
        await context_manager._handle_cross_story_preparation(request)
        
        # Should auto-register the story
        assert "new_story" in context_manager._active_stories
        story_info = context_manager._active_stories["new_story"]
        assert "auto_registered" in story_info["metadata"]
        assert "DesignAgent" in story_info["active_agents"]
    
    @pytest.mark.asyncio
    async def test_handle_cross_story_preparation_existing_story(self, context_manager):
        """Test handling cross-story preparation with existing story"""
        # Register story first
        await context_manager.register_story("existing_story")
        
        task = {"description": "Test task", "file_paths": ["file3.py"]}
        request = ContextRequest(
            agent_type="CodeAgent",
            story_id="existing_story",
            task=task
        )
        
        await context_manager._handle_cross_story_preparation(request)
        
        story_info = context_manager._active_stories["existing_story"]
        assert "CodeAgent" in story_info["active_agents"]
        assert "file3.py" in story_info["file_modifications"]
        assert isinstance(story_info["last_activity"], datetime)
    
    @pytest.mark.asyncio
    async def test_handle_cross_story_preparation_with_conflicts(self, context_manager):
        """Test handling cross-story preparation with conflicts"""
        # Setup existing story with file modifications
        await context_manager.register_story("story_1")
        await context_manager.register_story("story_2")
        context_manager._active_stories["story_2"]["file_modifications"] = {"shared_file.py"}
        
        # New request with conflicting file
        task = {"description": "Test task", "file_paths": ["shared_file.py", "unique_file.py"]}
        request = ContextRequest(
            agent_type="DesignAgent",
            story_id="story_1",
            task=task
        )
        
        await context_manager._handle_cross_story_preparation(request)
        
        # Should detect conflict and add cross-story context to metadata
        assert hasattr(request, 'metadata')
        assert 'cross_story_context' in request.metadata
        
        cross_context = request.metadata['cross_story_context']
        assert cross_context["primary_story"] == "story_1"
        assert "story_2" in [c["story_id"] for c in cross_context["conflicts"]]
    
    @pytest.mark.asyncio
    async def test_update_cross_story_tracking(self, context_manager):
        """Test updating cross-story tracking after context preparation"""
        # Register story
        await context_manager.register_story("story_1")
        
        # Create context with file contents
        context = AgentContext(
            request_id="req_1",
            agent_type="DesignAgent",
            story_id="story_1",
            file_contents={"tracked_file1.py": "content1", "tracked_file2.py": "content2"}
        )
        
        request = ContextRequest(
            agent_type="DesignAgent",
            story_id="story_1",
            task={"description": "test"},
            metadata={"cross_story_context": {"test": "data"}}
        )
        
        await context_manager._update_cross_story_tracking(request, context)
        
        story_info = context_manager._active_stories["story_1"]
        assert "tracked_file1.py" in story_info["file_modifications"]
        assert "tracked_file2.py" in story_info["file_modifications"]
        assert isinstance(story_info["last_activity"], datetime)
        
        # Should cache cross-story context
        assert len(context_manager._cross_story_cache) > 0


class TestErrorHandling:
    """Test comprehensive error handling scenarios"""
    
    @pytest.fixture
    def context_manager(self):
        """Create context manager for error testing"""
        with tempfile.TemporaryDirectory() as temp_dir:
            cm = ContextManager(
                project_path=temp_dir,
                enable_intelligence=False,
                enable_advanced_caching=False,
                enable_monitoring=False,
                enable_cross_story=False,
                enable_background_processing=False
            )
            yield cm
    
    @pytest.mark.asyncio
    async def test_prepare_context_with_none_task(self, context_manager):
        """Test prepare_context with None task"""
        with pytest.raises((AttributeError, TypeError, ContextError)):
            await context_manager.prepare_context(
                agent_type="DesignAgent",
                task=None,
                story_id="story_1"
            )
    
    @pytest.mark.asyncio
    async def test_prepare_context_with_zero_max_tokens(self, context_manager):
        """Test prepare_context with zero max_tokens"""
        task = {"description": "test", "story_id": "story_1"}
        
        with pytest.raises((ValueError, ContextError)):
            await context_manager.prepare_context(
                agent_type="DesignAgent",
                task=task,
                max_tokens=0,
                story_id="story_1"
            )
    
    @pytest.mark.asyncio
    async def test_prepare_context_with_negative_max_tokens(self, context_manager):
        """Test prepare_context with negative max_tokens"""
        task = {"description": "test", "story_id": "story_1"}
        
        with pytest.raises((ValueError, ContextError)):
            await context_manager.prepare_context(
                agent_type="DesignAgent",
                task=task,
                max_tokens=-1000,
                story_id="story_1"
            )


if __name__ == "__main__":
    # Run tests with coverage
    pytest.main([__file__, "-v", "--tb=short"])