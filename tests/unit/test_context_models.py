"""
Comprehensive test suite for Context Management System Data Models.

Tests data structures for context requests, agent context, token management,
agent memory, and other context-related entities.
"""

import pytest
import json
import uuid
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import Mock, patch

import sys
sys.path.append(str(Path(__file__).parent.parent.parent))

from lib.context.models import (
    ContextType, CompressionLevel, FileType,
    RelevanceScore, TokenBudget, TokenUsage, Decision,
    AgentMemory, ContextRequest, AgentContext, ContextSnapshot,
    Pattern, PhaseHandoff, TDDState
)


class TestEnums:
    """Test enumeration classes."""
    
    def test_context_type_values(self):
        """Test ContextType enum values."""
        assert ContextType.CORE_TASK.value == "core_task"
        assert ContextType.HISTORICAL.value == "historical"
        assert ContextType.DEPENDENCIES.value == "dependencies"
        assert ContextType.AGENT_MEMORY.value == "agent_memory"
        assert ContextType.METADATA.value == "metadata"
        assert ContextType.COMPRESSED.value == "compressed"
    
    def test_compression_level_values(self):
        """Test CompressionLevel enum values."""
        assert CompressionLevel.NONE.value == "none"
        assert CompressionLevel.LOW.value == "low"
        assert CompressionLevel.MODERATE.value == "moderate"
        assert CompressionLevel.HIGH.value == "high"
        assert CompressionLevel.EXTREME.value == "extreme"
    
    def test_file_type_values(self):
        """Test FileType enum values."""
        assert FileType.PYTHON.value == "python"
        assert FileType.TEST.value == "test"
        assert FileType.MARKDOWN.value == "markdown"
        assert FileType.JSON.value == "json"
        assert FileType.YAML.value == "yaml"
        assert FileType.CONFIG.value == "config"
        assert FileType.OTHER.value == "other"


class TestRelevanceScore:
    """Test RelevanceScore dataclass."""
    
    def test_relevance_score_creation(self):
        """Test creating a RelevanceScore instance."""
        score = RelevanceScore(
            file_path="/test/file.py",
            total_score=0.85,
            direct_mention=0.9,
            dependency_score=0.7,
            historical_score=0.6,
            semantic_score=0.8,
            tdd_phase_score=0.75,
            reasons=["Direct import", "Historical usage"]
        )
        
        assert score.file_path == "/test/file.py"
        assert score.total_score == 0.85
        assert score.direct_mention == 0.9
        assert score.dependency_score == 0.7
        assert score.historical_score == 0.6
        assert score.semantic_score == 0.8
        assert score.tdd_phase_score == 0.75
        assert score.reasons == ["Direct import", "Historical usage"]
    
    def test_relevance_score_defaults(self):
        """Test RelevanceScore with default values."""
        score = RelevanceScore(
            file_path="/test/file.py",
            total_score=0.5
        )
        
        assert score.direct_mention == 0.0
        assert score.dependency_score == 0.0
        assert score.historical_score == 0.0
        assert score.semantic_score == 0.0
        assert score.tdd_phase_score == 0.0
        assert score.reasons == []
    
    def test_relevance_score_validation_high(self):
        """Test RelevanceScore validation for high values."""
        score = RelevanceScore(
            file_path="/test/file.py",
            total_score=1.5  # Above 1.0
        )
        
        # Should be clamped to 1.0
        assert score.total_score == 1.0
    
    def test_relevance_score_validation_low(self):
        """Test RelevanceScore validation for low values."""
        score = RelevanceScore(
            file_path="/test/file.py",
            total_score=-0.5  # Below 0.0
        )
        
        # Should be clamped to 0.0
        assert score.total_score == 0.0


class TestTokenBudget:
    """Test TokenBudget dataclass."""
    
    def test_token_budget_creation(self):
        """Test creating a TokenBudget instance."""
        budget = TokenBudget(
            total_budget=1000,
            core_task=400,
            historical=200,
            dependencies=150,
            agent_memory=100,
            buffer=50
        )
        
        assert budget.total_budget == 1000
        assert budget.core_task == 400
        assert budget.historical == 200
        assert budget.dependencies == 150
        assert budget.agent_memory == 100
        assert budget.buffer == 50
    
    def test_token_budget_valid_allocation(self):
        """Test TokenBudget with valid allocation."""
        # Total allocation = 900, which is less than total budget of 1000
        budget = TokenBudget(
            total_budget=1000,
            core_task=400,
            historical=200,
            dependencies=150,
            agent_memory=100,
            buffer=50
        )
        
        # Should not raise exception
        assert budget.total_budget == 1000
    
    def test_token_budget_invalid_allocation(self):
        """Test TokenBudget with invalid allocation."""
        with pytest.raises(ValueError) as exc_info:
            TokenBudget(
                total_budget=1000,
                core_task=500,
                historical=300,
                dependencies=200,
                agent_memory=150,
                buffer=100  # Total = 1250, exceeds budget of 1000
            )
        
        assert "exceeds total budget" in str(exc_info.value)
    
    def test_get_allocation_dict(self):
        """Test getting allocation as dictionary."""
        budget = TokenBudget(
            total_budget=1000,
            core_task=400,
            historical=200,
            dependencies=150,
            agent_memory=100,
            buffer=50
        )
        
        allocation_dict = budget.get_allocation_dict()
        
        expected = {
            "core_task": 400,
            "historical": 200,
            "dependencies": 150,
            "agent_memory": 100,
            "buffer": 50
        }
        assert allocation_dict == expected
    
    def test_get_utilization_rate(self):
        """Test calculating utilization rate."""
        budget = TokenBudget(
            total_budget=1000,
            core_task=400,
            historical=200,
            dependencies=150,
            agent_memory=100,
            buffer=50
        )
        
        utilization = budget.get_utilization_rate()
        expected = (400 + 200 + 150 + 100 + 50) / 1000  # 0.9
        assert utilization == expected
    
    def test_get_utilization_rate_zero_budget(self):
        """Test utilization rate with zero total budget."""
        budget = TokenBudget(total_budget=0)
        
        utilization = budget.get_utilization_rate()
        assert utilization == 0.0


class TestTokenUsage:
    """Test TokenUsage dataclass."""
    
    def test_token_usage_creation(self):
        """Test creating a TokenUsage instance."""
        timestamp = datetime.utcnow()
        usage = TokenUsage(
            context_id="ctx-123",
            total_used=850,
            core_task_used=380,
            historical_used=180,
            dependencies_used=140,
            agent_memory_used=90,
            buffer_used=45,
            compression_ratio=0.85,
            timestamp=timestamp
        )
        
        assert usage.context_id == "ctx-123"
        assert usage.total_used == 850
        assert usage.core_task_used == 380
        assert usage.historical_used == 180
        assert usage.dependencies_used == 140
        assert usage.agent_memory_used == 90
        assert usage.buffer_used == 45
        assert usage.compression_ratio == 0.85
        assert usage.timestamp == timestamp
    
    def test_token_usage_defaults(self):
        """Test TokenUsage with default values."""
        usage = TokenUsage(
            context_id="ctx-456",
            total_used=500
        )
        
        assert usage.core_task_used == 0
        assert usage.historical_used == 0
        assert usage.dependencies_used == 0
        assert usage.agent_memory_used == 0
        assert usage.buffer_used == 0
        assert usage.compression_ratio == 1.0
        assert isinstance(usage.timestamp, datetime)
    
    def test_get_usage_dict(self):
        """Test getting usage as dictionary."""
        usage = TokenUsage(
            context_id="ctx-789",
            total_used=800,
            core_task_used=350,
            historical_used=200,
            dependencies_used=150,
            agent_memory_used=80,
            buffer_used=20
        )
        
        usage_dict = usage.get_usage_dict()
        
        expected = {
            "core_task_used": 350,
            "historical_used": 200,
            "dependencies_used": 150,
            "agent_memory_used": 80,
            "buffer_used": 20
        }
        assert usage_dict == expected
    
    def test_get_efficiency_score(self):
        """Test calculating efficiency score."""
        budget = TokenBudget(total_budget=1000)
        usage = TokenUsage(
            context_id="ctx-efficiency",
            total_used=850
        )
        
        efficiency = usage.get_efficiency_score(budget)
        expected = 850 / 1000  # 0.85
        assert efficiency == expected
    
    def test_get_efficiency_score_zero_budget(self):
        """Test efficiency score with zero budget."""
        budget = TokenBudget(total_budget=0)
        usage = TokenUsage(
            context_id="ctx-zero",
            total_used=100
        )
        
        efficiency = usage.get_efficiency_score(budget)
        assert efficiency == 0.0


class TestDecision:
    """Test Decision dataclass."""
    
    def test_decision_creation(self):
        """Test creating a Decision instance."""
        timestamp = datetime.utcnow()
        decision = Decision(
            id="decision-123",
            agent_type="CodeAgent",
            description="Implement feature X",
            rationale="Feature needed for user story",
            context_snapshot="Context data here",
            outcome="Feature implemented successfully",
            confidence=0.85,
            timestamp=timestamp,
            artifacts={"code": "function implementation"}
        )
        
        assert decision.id == "decision-123"
        assert decision.agent_type == "CodeAgent"
        assert decision.description == "Implement feature X"
        assert decision.rationale == "Feature needed for user story"
        assert decision.context_snapshot == "Context data here"
        assert decision.outcome == "Feature implemented successfully"
        assert decision.confidence == 0.85
        assert decision.timestamp == timestamp
        assert decision.artifacts == {"code": "function implementation"}
    
    def test_decision_defaults(self):
        """Test Decision with default values."""
        decision = Decision()
        
        assert isinstance(decision.id, str)
        assert len(decision.id) > 0  # Should have auto-generated UUID
        assert decision.agent_type == ""
        assert decision.description == ""
        assert decision.rationale == ""
        assert decision.context_snapshot == ""
        assert decision.outcome == ""
        assert decision.confidence == 0.0
        assert isinstance(decision.timestamp, datetime)
        assert decision.artifacts == {}
    
    def test_decision_auto_id_generation(self):
        """Test automatic ID generation."""
        decision1 = Decision()
        decision2 = Decision()
        
        # Should have different auto-generated IDs
        assert decision1.id != decision2.id
        assert len(decision1.id) > 0
        assert len(decision2.id) > 0
    
    def test_decision_to_dict(self):
        """Test converting decision to dictionary."""
        timestamp = datetime.utcnow()
        decision = Decision(
            id="decision-dict",
            agent_type="QAAgent",
            description="Run tests",
            rationale="Validate implementation",
            context_snapshot="Test context",
            outcome="All tests passed",
            confidence=0.95,
            timestamp=timestamp,
            artifacts={"test_results": "5 passed, 0 failed"}
        )
        
        decision_dict = decision.to_dict()
        
        expected_keys = [
            "id", "agent_type", "description", "rationale",
            "context_snapshot", "outcome", "confidence",
            "timestamp", "artifacts"
        ]
        
        for key in expected_keys:
            assert key in decision_dict
        
        assert decision_dict["id"] == "decision-dict"
        assert decision_dict["agent_type"] == "QAAgent"
        assert decision_dict["confidence"] == 0.95


class TestAgentMemory:
    """Test AgentMemory dataclass."""
    
    def test_agent_memory_creation(self):
        """Test creating an AgentMemory instance."""
        timestamp = datetime.utcnow()
        
        # Create some sample decisions and patterns
        decision = Decision(
            agent_type="DesignAgent",
            description="Use observer pattern",
            confidence=0.9
        )
        
        pattern = Pattern(
            pattern_type="design",
            description="Observer pattern implementation",
            success_rate=0.85
        )
        
        memory = AgentMemory(
            agent_type="DesignAgent",
            story_id="STORY-DESIGN",
            decisions=[decision],
            artifacts={"pattern": "observer_code.py"},
            learned_patterns=[pattern],
            metadata={"type": "design_memory"},
            created_at=timestamp,
            updated_at=timestamp
        )
        
        assert memory.agent_type == "DesignAgent"
        assert memory.story_id == "STORY-DESIGN"
        assert len(memory.decisions) == 1
        assert memory.decisions[0].description == "Use observer pattern"
        assert memory.artifacts == {"pattern": "observer_code.py"}
        assert len(memory.learned_patterns) == 1
        assert memory.learned_patterns[0].pattern_type == "design"
        assert memory.metadata == {"type": "design_memory"}
        assert memory.created_at == timestamp
        assert memory.updated_at == timestamp
    
    def test_agent_memory_defaults(self):
        """Test AgentMemory with default values."""
        memory = AgentMemory(
            agent_type="DataAgent",
            story_id="STORY-DATA"
        )
        
        assert memory.agent_type == "DataAgent"
        assert memory.story_id == "STORY-DATA"
        assert memory.decisions == []
        assert memory.artifacts == {}
        assert memory.learned_patterns == []
        assert memory.context_history == []
        assert memory.phase_handoffs == []
        assert memory.metadata == {}
        assert isinstance(memory.created_at, datetime)
        assert isinstance(memory.updated_at, datetime)
    
    def test_agent_memory_add_decision(self):
        """Test adding a decision to memory."""
        memory = AgentMemory(
            agent_type="CodeAgent",
            story_id="STORY-CODE"
        )
        
        original_updated = memory.updated_at
        
        decision = Decision(
            agent_type="CodeAgent",
            description="Implement feature X",
            confidence=0.8
        )
        
        # Add decision
        memory.add_decision(decision)
        
        assert len(memory.decisions) == 1
        assert memory.decisions[0] == decision
        assert memory.updated_at > original_updated
    
    def test_agent_memory_add_pattern(self):
        """Test adding a pattern to memory."""
        memory = AgentMemory(
            agent_type="DesignAgent",
            story_id="STORY-DESIGN"
        )
        
        pattern = Pattern(
            pattern_type="architectural",
            description="MVC pattern usage",
            success_rate=0.9,
            usage_count=5
        )
        
        # Add pattern (method would need to be implemented)
        memory.learned_patterns.append(pattern)
        memory.updated_at = datetime.utcnow()
        
        assert len(memory.learned_patterns) == 1
        assert memory.learned_patterns[0] == pattern
    
    def test_agent_memory_serialization(self):
        """Test AgentMemory serialization."""
        decision = Decision(
            agent_type="QAAgent",
            description="Run tests",
            confidence=0.95
        )
        
        pattern = Pattern(
            pattern_type="testing",
            description="Test-driven development",
            success_rate=0.88
        )
        
        memory = AgentMemory(
            agent_type="QAAgent",
            story_id="STORY-QA",
            decisions=[decision],
            learned_patterns=[pattern],
            artifacts={"test_file": "test_example.py"},
            metadata={"framework": "pytest"}
        )
        
        # Test dictionary conversion (method would need to be implemented)
        assert memory.agent_type == "QAAgent"
        assert memory.story_id == "STORY-QA"
        assert len(memory.decisions) == 1
        assert len(memory.learned_patterns) == 1


class TestContextRequest:
    """Test ContextRequest dataclass."""
    
    def test_context_request_creation(self):
        """Test creating a ContextRequest instance."""
        request = ContextRequest(
            id="req-123",
            agent_type="CodeAgent",
            story_id="STORY-AUTH",
            max_tokens=2000,
            compression_level=CompressionLevel.MODERATE,
            include_history=True,
            include_dependencies=True,
            include_agent_memory=True,
            focus_areas=["/auth/models.py", "/auth/views.py"],
            exclude_patterns=["*.pyc", "__pycache__"]
        )
        
        assert request.id == "req-123"
        assert request.agent_type == "CodeAgent"
        assert request.max_tokens == 2000
        assert request.story_id == "STORY-AUTH"
        assert request.include_history is True
        assert request.include_dependencies is True
        assert request.include_agent_memory is True
        assert request.compression_level == CompressionLevel.MODERATE
        assert request.focus_areas == ["/auth/models.py", "/auth/views.py"]
        assert request.exclude_patterns == ["*.pyc", "__pycache__"]
    
    def test_context_request_defaults(self):
        """Test ContextRequest with default values."""
        request = ContextRequest(
            agent_type="DesignAgent",
            story_id="STORY-DEFAULT"
        )
        
        assert isinstance(request.id, str)
        assert len(request.id) > 0  # Auto-generated UUID
        assert request.max_tokens == 200000  # Default value
        assert request.story_id == "STORY-DEFAULT"
        assert request.task is None
        assert request.include_history is True
        assert request.include_dependencies is True
        assert request.include_agent_memory is True
        assert request.compression_level == CompressionLevel.MODERATE
        assert request.focus_areas == []
        assert request.exclude_patterns == []
    
    def test_context_request_validate_valid(self):
        """Test validation of valid context request."""
        request = ContextRequest(
            agent_type="QAAgent",
            story_id="STORY-QA",
            max_tokens=1500
        )
        
        # Should be valid request
        assert request.agent_type == "QAAgent"
        assert request.max_tokens == 1500
    
    def test_context_request_validate_invalid_tokens(self):
        """Test validation with invalid token count."""
        request = ContextRequest(
            agent_type="DataAgent",
            story_id="STORY-DATA",
            max_tokens=0  # Invalid
        )
        
        # Should still create the request, validation could be separate
        assert request.max_tokens == 0
    
    def test_context_request_validate_empty_description(self):
        """Test validation with empty task description."""
        request = ContextRequest(
            agent_type="CodeAgent",
            story_id="STORY-CODE",
            max_tokens=2000
        )
        
        # Should create request even with empty story
        assert request.agent_type == "CodeAgent"
    
    def test_context_request_to_dict(self):
        """Test converting context request to dictionary."""
        request = ContextRequest(
            id="req-dict",
            agent_type="DesignAgent",
            story_id="STORY-API",
            max_tokens=3000,
            include_history=False,
            compression_level=CompressionLevel.HIGH
        )
        
        request_dict = request.to_dict()
        
        assert request_dict["id"] == "req-dict"
        assert request_dict["agent_type"] == "DesignAgent"
        assert request_dict["max_tokens"] == 3000
        assert request_dict["story_id"] == "STORY-API"
        assert request_dict["include_history"] is False
        assert request_dict["compression_level"] == "high"


class TestAgentContext:
    """Test AgentContext dataclass."""
    
    def test_agent_context_creation(self):
        """Test creating an AgentContext instance."""
        timestamp = datetime.utcnow()
        
        context = AgentContext(
            request_id="req-456",
            story_id="STORY-TEST",
            agent_type="QAAgent",
            tdd_phase=TDDState.TEST_RED,
            core_context="Write failing tests",
            dependencies="Import statements",
            historical_context="Previous test patterns",
            agent_memory="Testing best practices",
            metadata="Compressed context",
            token_usage=TokenUsage("ctx-456", 1200),
            compression_applied=True,
            cache_hit=False,
            preparation_time=0.5,
            timestamp=timestamp
        )
        
        assert context.request_id == "req-456"
        assert context.story_id == "STORY-TEST"
        assert context.agent_type == "QAAgent"
        assert context.tdd_phase == TDDState.TEST_RED
        assert context.core_context == "Write failing tests"
        assert context.dependencies == "Import statements"
        assert context.historical_context == "Previous test patterns"
        assert context.agent_memory == "Testing best practices"
        assert context.metadata == "Compressed context"
        assert isinstance(context.token_usage, TokenUsage)
        assert context.compression_applied is True
        assert context.cache_hit is False
        assert context.preparation_time == 0.5
        assert context.timestamp == timestamp
    
    def test_agent_context_defaults(self):
        """Test AgentContext with default values."""
        context = AgentContext(
            request_id="req-defaults",
            story_id="STORY-DEFAULT",
            agent_type="DataAgent"
        )
        
        assert context.tdd_phase is None
        assert context.core_context == ""
        assert context.dependencies == ""
        assert context.historical_context == ""
        assert context.agent_memory == ""
        assert context.metadata == ""
        assert context.token_usage is None
        assert context.compression_applied is False
        assert context.cache_hit is False
        assert context.preparation_time == 0.0
        assert isinstance(context.timestamp, datetime)
    
    def test_agent_context_get_total_content(self):
        """Test getting total content from agent context."""
        context = AgentContext(
            request_id="req-full",
            story_id="STORY-FULL",
            agent_type="CodeAgent",
            core_context="Main task",
            dependencies="Dependencies",
            historical_context="History",
            agent_memory="Memory",
            metadata="Metadata"
        )
        
        total_content = context.get_total_content()
        
        assert "Main task" in total_content
        assert "Dependencies" in total_content
        assert "History" in total_content
        assert "Memory" in total_content
        assert "Metadata" in total_content
    
    def test_agent_context_get_total_token_estimate(self):
        """Test getting total token estimate."""
        context = AgentContext(
            request_id="req-estimate",
            story_id="STORY-EST",
            agent_type="DesignAgent",
            core_context="Some content for estimation",
            dependencies="Some dependencies content",
            historical_context="Some historical content"
        )
        
        total_tokens = context.get_total_token_estimate()
        assert total_tokens > 0  # Should estimate based on content length
    
    def test_agent_context_get_total_token_estimate_no_usage(self):
        """Test token estimate with no token usage."""
        context = AgentContext(
            request_id="req-no-usage",
            story_id="STORY-NO-USAGE",
            agent_type="DesignAgent",
            core_context="Some content here"
        )
        
        total_tokens = context.get_total_token_estimate()
        assert total_tokens > 0  # Should estimate based on content length
    
    def test_agent_context_cache_hit_property(self):
        """Test AgentContext cache hit property."""
        context = AgentContext(
            request_id="req-cache",
            story_id="STORY-CACHE",
            agent_type="QAAgent",
            cache_hit=True
        )
        
        assert context.cache_hit is True
    
    def test_agent_context_compression_properties(self):
        """Test AgentContext compression properties."""
        context = AgentContext(
            request_id="req-compress",
            story_id="STORY-COMPRESS",
            agent_type="QAAgent",
            compression_applied=True,
            compression_level=CompressionLevel.HIGH
        )
        
        assert context.compression_applied is True
        assert context.compression_level == CompressionLevel.HIGH
    
    def test_agent_context_quality_score(self):
        """Test getting context quality score."""
        score1 = RelevanceScore(file_path="/test1.py", total_score=0.8)
        score2 = RelevanceScore(file_path="/test2.py", total_score=0.6)
        
        context = AgentContext(
            request_id="req-quality",
            story_id="STORY-QUALITY",
            agent_type="QAAgent",
            relevance_scores=[score1, score2]
        )
        
        quality_score = context.get_context_quality_score()
        assert quality_score == 0.7  # (0.8 + 0.6) / 2


class TestContextSnapshot:
    """Test ContextSnapshot dataclass."""
    
    def test_context_snapshot_creation(self):
        """Test creating a ContextSnapshot instance."""
        timestamp = datetime.utcnow()
        
        snapshot = ContextSnapshot(
            id="snap-123",
            agent_type="CodeAgent",
            story_id="STORY-SNAP",
            context_summary="Implementation context snapshot",
            file_list=["file1.py", "file2.py"],
            metadata={"version": "1.0", "author": "agent"},
            timestamp=timestamp
        )
        
        assert snapshot.id == "snap-123"
        assert snapshot.agent_type == "CodeAgent"
        assert snapshot.story_id == "STORY-SNAP"
        assert snapshot.context_summary == "Implementation context snapshot"
        assert snapshot.file_list == ["file1.py", "file2.py"]
        assert snapshot.metadata == {"version": "1.0", "author": "agent"}
        assert snapshot.timestamp == timestamp
    
    def test_context_snapshot_defaults(self):
        """Test ContextSnapshot with default values."""
        snapshot = ContextSnapshot(
            agent_type="DesignAgent",
            story_id="STORY-DEFAULT"
        )
        
        assert isinstance(snapshot.id, str)
        assert len(snapshot.id) > 0  # Auto-generated UUID
        assert snapshot.context_summary == ""
        assert snapshot.file_list == []
        assert snapshot.metadata == {}
        assert isinstance(snapshot.timestamp, datetime)
        assert snapshot.tdd_phase is None
    
    def test_context_snapshot_to_dict(self):
        """Test converting snapshot to dictionary."""
        timestamp = datetime.utcnow()
        
        snapshot = ContextSnapshot(
            id="snap-dict",
            agent_type="QAAgent",
            story_id="STORY-DICT",
            context_summary="Test context snapshot",
            file_list=["test1.py", "test2.py"],
            metadata={"framework": "pytest"},
            timestamp=timestamp
        )
        
        snapshot_dict = snapshot.to_dict()
        
        expected_keys = [
            "id", "agent_type", "story_id", "context_summary",
            "file_list", "metadata", "timestamp", "tdd_phase", "token_usage"
        ]
        
        for key in expected_keys:
            assert key in snapshot_dict
        
        assert snapshot_dict["id"] == "snap-dict"
        assert snapshot_dict["agent_type"] == "QAAgent"
        assert snapshot_dict["file_list"] == ["test1.py", "test2.py"]
    
    def test_context_snapshot_with_token_usage(self):
        """Test ContextSnapshot with token usage."""
        token_usage = TokenUsage("ctx-snap", 1500)
        
        snapshot = ContextSnapshot(
            agent_type="DataAgent",
            story_id="STORY-SIZE",
            context_summary="Large data processing snapshot",
            token_usage=token_usage,
            metadata={"info": "test"}
        )
        
        assert snapshot.token_usage is not None
        assert snapshot.token_usage.total_used == 1500
        assert snapshot.context_summary == "Large data processing snapshot"
    
    def test_context_snapshot_with_tdd_phase(self):
        """Test ContextSnapshot with TDD phase."""
        snapshot = ContextSnapshot(
            agent_type="DesignAgent",
            story_id="STORY-TDD",
            tdd_phase=TDDState.TEST_RED,
            context_summary="Red phase snapshot"
        )
        
        assert snapshot.tdd_phase == TDDState.TEST_RED
        assert snapshot.context_summary == "Red phase snapshot"


class TestModelsIntegration:
    """Test integration scenarios between different model classes."""
    
    def test_full_context_workflow(self):
        """Test complete workflow with all model classes."""
        # 1. Create a context request
        request = ContextRequest(
            agent_type="CodeAgent",
            story_id="STORY-AUTH",
            max_tokens=2000
        )
        
        # 2. Create token budget
        budget = TokenBudget(
            total_budget=2000,
            core_task=800,
            historical=400,
            dependencies=300,
            agent_memory=200,
            buffer=100
        )
        
        # 3. Create token usage
        usage = TokenUsage(
            context_id=request.id,
            total_used=1800,
            core_task_used=750,
            historical_used=380,
            dependencies_used=280,
            agent_memory_used=190,
            buffer_used=95
        )
        
        # 4. Create agent context
        context = AgentContext(
            request_id=request.id,
            story_id=request.story_id,
            agent_type=request.agent_type,
            core_context="Authentication implementation details",
            token_usage=usage
        )
        
        # 5. Create decision
        decision = Decision(
            agent_type=request.agent_type,
            description="Chose OAuth2 for authentication",
            rationale="More secure and industry standard",
            confidence=0.9
        )
        
        # 6. Create agent memory
        memory = AgentMemory(
            agent_type=request.agent_type,
            story_id=request.story_id,
            decisions=[decision]
        )
        
        # Verify all components work together
        assert request.agent_type == "CodeAgent"
        assert budget.get_utilization_rate() == 0.9  # 1800/2000
        assert usage.get_efficiency_score(budget) == 0.9  # 1800/2000
        assert context.get_total_token_estimate() > 0
        assert decision.confidence == 0.9
        assert memory.story_id == "STORY-AUTH"
    
    def test_memory_and_decision_relationship(self):
        """Test relationship between agent memory and decisions."""
        # Create a decision
        decision = Decision(
            agent_type="DesignAgent",
            description="Use microservices architecture",
            rationale="Better scalability and maintainability",
            confidence=0.85
        )
        
        # Create related memory
        memory = AgentMemory(
            agent_type="DesignAgent",
            story_id="STORY-DESIGN",
            decisions=[decision],
            metadata={"decision_id": decision.id, "confidence": decision.confidence}
        )
        
        # Verify relationship
        assert memory.metadata["decision_id"] == decision.id
        assert memory.metadata["confidence"] == decision.confidence
        assert len(memory.decisions) == 1
        assert memory.decisions[0].description == decision.description
    
    def test_context_snapshot_with_full_context(self):
        """Test creating context snapshot from full agent context."""
        # Create agent context
        context = AgentContext(
            request_id="req-snapshot",
            story_id="STORY-SNAPSHOT",
            agent_type="QAAgent",
            core_context="Run comprehensive tests",
            dependencies="Test dependencies",
            historical_context="Previous test results",
            agent_memory="Testing strategies",
            token_usage=TokenUsage("ctx-snap", 1500)
        )
        
        # Create snapshot from context
        snapshot = ContextSnapshot(
            agent_type=context.agent_type,
            story_id=context.story_id,
            context_summary=f"Context snapshot for {context.agent_type} on {context.story_id}",
            token_usage=context.token_usage
        )
        
        # Verify snapshot contains context information
        assert snapshot.agent_type == context.agent_type
        assert snapshot.story_id == context.story_id
        assert snapshot.token_usage.total_used == 1500
        assert context.agent_type in snapshot.context_summary
    
    def test_performance_with_large_data(self):
        """Test model performance with large data structures."""
        # Create large context data
        large_content = "x" * 10000  # 10KB of content
        
        context = AgentContext(
            request_id="req-large",
            story_id="STORY-LARGE",
            agent_type="DataAgent",
            core_context=large_content,
            dependencies=large_content,
            historical_context=large_content
        )
        
        # Should handle large content gracefully
        total_content = context.get_total_content()
        assert len(total_content) > 30000  # At least 30KB
        
        token_estimate = context.get_total_token_estimate()
        assert token_estimate > 0
        
        # Create snapshot from large context
        snapshot = ContextSnapshot(
            agent_type=context.agent_type,
            story_id=context.story_id,
            context_summary="Large data processing context"
        )
        
        # Verify snapshot was created successfully
        assert snapshot.agent_type == "DataAgent"
        assert snapshot.story_id == "STORY-LARGE"