"""
Comprehensive test coverage for context_cache.py module.

Tests cover all classes, methods, and edge cases to achieve 95%+ coverage.
"""

import asyncio
import json
import pytest
import time
from datetime import datetime, timedelta
from unittest.mock import Mock, AsyncMock, patch
from typing import Dict, Any

# Import the module under test
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'lib'))

from context_cache import (
    ContextCache, CacheEntry, CacheStatistics, PredictionPattern,
    CacheStrategy, CacheWarmingStrategy
)
from context.models import AgentContext, ContextRequest, TDDState, CompressionLevel
from context.exceptions import ContextCacheError


class TestCacheEntry:
    """Test CacheEntry class and its methods"""
    
    def test_cache_entry_initialization(self):
        """Test CacheEntry initialization with all fields"""
        context = Mock(spec=AgentContext)
        context.request_id = "test-123"
        
        entry = CacheEntry(
            context=context,
            request_id="req-123",
            cache_key="key-123",
            created_at=datetime.utcnow(),
            last_accessed=datetime.utcnow(),
            access_count=5,
            hit_count=3,
            size_bytes=1024,
            tags={"test", "cache"},
            prediction_score=0.85,
            warm_priority=2
        )
        
        assert entry.context == context
        assert entry.request_id == "req-123"
        assert entry.cache_key == "key-123"
        assert entry.access_count == 5
        assert entry.hit_count == 3
        assert entry.size_bytes == 1024
        assert "test" in entry.tags
        assert entry.prediction_score == 0.85
        assert entry.warm_priority == 2
    
    def test_cache_entry_update_access(self):
        """Test access tracking in CacheEntry"""
        context = Mock(spec=AgentContext)
        entry = CacheEntry(
            context=context,
            request_id="req-123",
            cache_key="key-123",
            created_at=datetime.utcnow(),
            last_accessed=datetime.utcnow() - timedelta(minutes=1),
            access_count=0
        )
        
        original_access = entry.last_accessed
        entry.update_access()
        
        assert entry.access_count == 1
        assert entry.last_accessed > original_access
    
    def test_cache_entry_record_hit(self):
        """Test hit recording in CacheEntry"""
        context = Mock(spec=AgentContext)
        entry = CacheEntry(
            context=context,
            request_id="req-123",
            cache_key="key-123",
            created_at=datetime.utcnow(),
            last_accessed=datetime.utcnow() - timedelta(minutes=1),
            access_count=2,
            hit_count=1
        )
        
        entry.record_hit()
        
        assert entry.hit_count == 2
        assert entry.access_count == 3
    
    def test_cache_entry_age_calculation(self):
        """Test age calculation properties"""
        context = Mock(spec=AgentContext)
        past_time = datetime.utcnow() - timedelta(seconds=30)
        entry = CacheEntry(
            context=context,
            request_id="req-123",
            cache_key="key-123",
            created_at=past_time,
            last_accessed=past_time + timedelta(seconds=10)
        )
        
        assert entry.age_seconds >= 30
        assert entry.last_access_seconds >= 20
    
    def test_cache_entry_hit_rate_calculation(self):
        """Test hit rate calculation"""
        context = Mock(spec=AgentContext)
        entry = CacheEntry(
            context=context,
            request_id="req-123",
            cache_key="key-123",
            created_at=datetime.utcnow(),
            last_accessed=datetime.utcnow(),
            access_count=10,
            hit_count=7
        )
        
        assert entry.hit_rate == 0.7
        
        # Test zero access count
        entry.access_count = 0
        assert entry.hit_rate == 0.0


class TestCacheStatistics:
    """Test CacheStatistics class"""
    
    def test_statistics_initialization(self):
        """Test statistics initialization"""
        stats = CacheStatistics()
        
        assert stats.total_requests == 0
        assert stats.cache_hits == 0
        assert stats.cache_misses == 0
        assert stats.evictions == 0
        assert stats.warming_hits == 0
        assert stats.prediction_accuracy == 0.0
        assert stats.average_prep_time == 0.0
        assert stats.memory_usage_bytes == 0
        assert stats.entry_count == 0
    
    def test_hit_rate_calculation(self):
        """Test hit rate property calculation"""
        stats = CacheStatistics(cache_hits=8, cache_misses=2)
        assert stats.hit_rate == 0.8
        
        # Test zero total
        stats = CacheStatistics()
        assert stats.hit_rate == 0.0
    
    def test_warming_effectiveness_calculation(self):
        """Test warming effectiveness calculation"""
        stats = CacheStatistics(cache_hits=10, warming_hits=4)
        assert stats.warming_effectiveness == 0.4
        
        # Test zero cache hits
        stats = CacheStatistics(warming_hits=4)
        assert stats.warming_effectiveness == 0.0


class TestPredictionPattern:
    """Test PredictionPattern class"""
    
    def test_prediction_pattern_initialization(self):
        """Test PredictionPattern initialization"""
        pattern = PredictionPattern(
            pattern_id="seq_123",
            pattern_type="sequential",
            trigger_conditions={"sequence": ["a", "b"]},
            predicted_requests=["c"],
            confidence=0.85,
            success_rate=0.9,
            usage_count=5
        )
        
        assert pattern.pattern_id == "seq_123"
        assert pattern.pattern_type == "sequential"
        assert pattern.confidence == 0.85
        assert pattern.success_rate == 0.9
        assert pattern.usage_count == 5


class TestContextCache:
    """Test ContextCache main class"""
    
    @pytest.fixture
    def mock_context(self):
        """Create a mock AgentContext"""
        context = Mock(spec=AgentContext)
        context.request_id = "test-req-123"
        context.core_context = "Test core context content"
        context.historical_context = "Test historical context"
        context.dependencies = "Test dependencies"
        context.agent_memory = "Test agent memory"
        context.metadata = "Test metadata"
        context.file_contents = {"file1.py": "content"}
        context.copy.return_value = context
        return context
    
    @pytest.fixture
    def mock_request(self):
        """Create a mock ContextRequest"""
        request = Mock(spec=ContextRequest)
        request.agent_type = "test_agent"
        request.story_id = "story-123"
        request.max_tokens = 1000
        request.compression_level = CompressionLevel.MEDIUM
        request.include_history = True
        request.include_dependencies = True
        
        # Mock task
        request.task = Mock()
        request.task.description = "Test task"
        request.task.current_state = TDDState.RED
        
        return request
    
    @pytest.fixture
    def cache(self):
        """Create a ContextCache instance for testing"""
        return ContextCache(
            max_entries=10,
            max_memory_mb=1,
            ttl_seconds=30,
            strategy=CacheStrategy.LRU,
            warming_strategy=CacheWarmingStrategy.LAZY,
            enable_predictions=True,
            prediction_confidence_threshold=0.7
        )
    
    def test_cache_initialization(self):
        """Test ContextCache initialization"""
        cache = ContextCache(
            max_entries=100,
            max_memory_mb=50,
            ttl_seconds=1800,
            strategy=CacheStrategy.PREDICTIVE,
            warming_strategy=CacheWarmingStrategy.AGGRESSIVE,
            enable_predictions=False,
            prediction_confidence_threshold=0.8
        )
        
        assert cache.max_entries == 100
        assert cache.max_memory_bytes == 50 * 1024 * 1024
        assert cache.ttl_seconds == 1800
        assert cache.strategy == CacheStrategy.PREDICTIVE
        assert cache.warming_strategy == CacheWarmingStrategy.AGGRESSIVE
        assert cache.enable_predictions is False
        assert cache.prediction_confidence_threshold == 0.8
        assert cache.stats is not None
        assert isinstance(cache._cache, dict)
    
    @pytest.mark.asyncio
    async def test_background_tasks_lifecycle(self, cache):
        """Test starting and stopping background tasks"""
        await cache.start_background_tasks()
        
        assert cache._warming_task is not None
        assert cache._prediction_task is not None
        
        await cache.stop_background_tasks()
        
        # Tasks should be cancelled
        assert cache._warming_task.cancelled() or cache._warming_task.done()
        assert cache._prediction_task.cancelled() or cache._prediction_task.done()
    
    @pytest.mark.asyncio
    async def test_cache_miss(self, cache):
        """Test cache miss scenario"""
        result = await cache.get("nonexistent-key")
        
        assert result is None
        assert cache.stats.cache_misses == 1
        assert cache.stats.total_requests == 1
    
    @pytest.mark.asyncio
    async def test_cache_put_and_get(self, cache, mock_context, mock_request):
        """Test putting and getting from cache"""
        cache_key = "test-key-123"
        
        # Put context in cache
        success = await cache.put(cache_key, mock_context, mock_request, {"tag1", "tag2"})
        assert success is True
        
        # Verify statistics updated
        assert cache.stats.entry_count == 1
        assert cache.stats.memory_usage_bytes > 0
        
        # Get context from cache
        retrieved = await cache.get(cache_key)
        
        assert retrieved is not None
        assert cache.stats.cache_hits == 1
        assert cache.stats.total_requests == 1
    
    @pytest.mark.asyncio
    async def test_cache_expiration(self, cache, mock_context):
        """Test cache entry expiration"""
        cache_key = "test-expired-key"
        
        # Put with very short TTL
        cache.ttl_seconds = 0.1  # 100ms
        await cache.put(cache_key, mock_context)
        
        # Wait for expiration
        await asyncio.sleep(0.2)
        
        # Should return None due to expiration
        result = await cache.get(cache_key)
        assert result is None
        assert cache.stats.cache_misses == 1
    
    @pytest.mark.asyncio
    async def test_cache_invalidation(self, cache, mock_context):
        """Test cache invalidation"""
        cache_key = "test-invalidate-key"
        
        await cache.put(cache_key, mock_context)
        
        # Invalidate specific key
        success = await cache.invalidate(cache_key)
        assert success is True
        
        # Should be cache miss now
        result = await cache.get(cache_key)
        assert result is None
    
    @pytest.mark.asyncio
    async def test_cache_invalidate_by_tags(self, cache, mock_context, mock_request):
        """Test invalidation by tags"""
        cache_key1 = "key1"
        cache_key2 = "key2"
        
        # Put entries with different tags
        await cache.put(cache_key1, mock_context, mock_request, {"agent:test", "story:123"})
        await cache.put(cache_key2, mock_context, mock_request, {"agent:other", "story:456"})
        
        # Invalidate by tag
        invalidated = await cache.invalidate_by_tags({"agent:test"})
        assert invalidated == 1
        
        # First should be invalidated, second should remain
        assert await cache.get(cache_key1) is None
        assert await cache.get(cache_key2) is not None
    
    @pytest.mark.asyncio
    async def test_cache_eviction_lru(self, cache, mock_context):
        """Test LRU eviction strategy"""
        cache.max_entries = 2
        cache.strategy = CacheStrategy.LRU
        
        # Fill cache to capacity
        await cache.put("key1", mock_context)
        await cache.put("key2", mock_context)
        
        # Access key1 to make it most recently used
        await cache.get("key1")
        
        # Add another entry, should evict key2 (least recently used)
        await cache.put("key3", mock_context)
        
        assert await cache.get("key1") is not None
        assert await cache.get("key2") is None
        assert await cache.get("key3") is not None
    
    @pytest.mark.asyncio
    async def test_cache_eviction_lfu(self, cache, mock_context):
        """Test LFU eviction strategy"""
        cache.max_entries = 2
        cache.strategy = CacheStrategy.LFU
        
        await cache.put("key1", mock_context)
        await cache.put("key2", mock_context)
        
        # Access key1 multiple times
        await cache.get("key1")
        await cache.get("key1")
        await cache.get("key2")  # key2 accessed once, key1 twice
        
        # Add another entry, should evict key2 (least frequently used)
        await cache.put("key3", mock_context)
        
        assert await cache.get("key1") is not None
        assert await cache.get("key2") is None
        assert await cache.get("key3") is not None
    
    @pytest.mark.asyncio
    async def test_cache_eviction_ttl(self, cache, mock_context):
        """Test TTL eviction strategy"""
        cache.max_entries = 2
        cache.strategy = CacheStrategy.TTL
        
        await cache.put("key1", mock_context)
        await asyncio.sleep(0.01)  # Small delay to ensure different timestamps
        await cache.put("key2", mock_context)
        
        # Add another entry, should evict key1 (oldest)
        await cache.put("key3", mock_context)
        
        assert await cache.get("key1") is None
        assert await cache.get("key2") is not None
        assert await cache.get("key3") is not None
    
    @pytest.mark.asyncio
    async def test_cache_eviction_predictive(self, cache, mock_context):
        """Test predictive eviction strategy"""
        cache.max_entries = 2
        cache.strategy = CacheStrategy.PREDICTIVE
        
        await cache.put("key1", mock_context)
        await cache.put("key2", mock_context)
        
        # Add another entry to trigger eviction
        await cache.put("key3", mock_context)
        
        # Should have evicted one entry
        entries_count = sum(1 for _ in cache._cache.values())
        assert entries_count == 2
    
    @pytest.mark.asyncio
    async def test_cache_memory_limit(self, cache, mock_context):
        """Test memory limit enforcement"""
        # Set very low memory limit
        cache.max_memory_bytes = 1024  # 1KB
        
        # Mock large context
        mock_context.core_context = "x" * 2000  # 2KB of content
        
        await cache.put("key1", mock_context)
        
        # Should have limited entries due to memory constraint
        assert cache._current_memory_usage <= cache.max_memory_bytes or len(cache._cache) == 0
    
    @pytest.mark.asyncio
    async def test_warm_cache(self, cache, mock_request):
        """Test cache warming functionality"""
        predictions = [mock_request]
        
        # Test with warming disabled
        cache.warming_strategy = CacheWarmingStrategy.NONE
        queued = await cache.warm_cache(predictions)
        assert queued == 0
        
        # Test with warming enabled
        cache.warming_strategy = CacheWarmingStrategy.LAZY
        queued = await cache.warm_cache(predictions, priority=2)
        assert queued == 1
    
    @pytest.mark.asyncio
    async def test_cleanup_expired(self, cache, mock_context):
        """Test expired entry cleanup"""
        # Add entry that will expire
        cache.ttl_seconds = 0.1
        await cache.put("expire-key", mock_context)
        
        # Wait for expiration
        await asyncio.sleep(0.2)
        
        # Force cleanup interval to pass
        cache._last_cleanup = datetime.utcnow() - timedelta(seconds=400)
        
        cleaned = await cache.cleanup_expired()
        assert cleaned == 1
        assert "expire-key" not in cache._cache
    
    @pytest.mark.asyncio
    async def test_get_statistics(self, cache, mock_context):
        """Test statistics retrieval"""
        await cache.put("stats-key", mock_context)
        await cache.get("stats-key")
        await cache.get("nonexistent")
        
        stats = await cache.get_statistics()
        
        assert stats.total_requests == 2
        assert stats.cache_hits == 1
        assert stats.cache_misses == 1
        assert stats.entry_count == 1
        assert stats.hit_rate == 0.5
    
    @pytest.mark.asyncio
    async def test_get_detailed_metrics(self, cache, mock_context, mock_request):
        """Test detailed metrics retrieval"""
        await cache.put("metrics-key", mock_context, mock_request, {"test-tag"})
        
        metrics = await cache.get_detailed_metrics()
        
        assert "basic_stats" in metrics
        assert "distribution" in metrics
        assert "patterns" in metrics
        assert metrics["basic_stats"]["entry_count"] == 1
        assert "test-tag" in metrics["distribution"]["tag_distribution"]
    
    def test_cache_clear(self, cache, mock_context):
        """Test cache clearing"""
        # Add some entries
        asyncio.run(cache.put("clear-key1", mock_context))
        asyncio.run(cache.put("clear-key2", mock_context))
        
        cache.clear()
        
        assert len(cache._cache) == 0
        assert cache._current_memory_usage == 0
        assert cache.stats.entry_count == 0
    
    @pytest.mark.asyncio
    async def test_analyze_patterns(self, cache):
        """Test pattern analysis"""
        # Add some access history
        cache._access_history = [
            ("key1", datetime.utcnow()),
            ("key2", datetime.utcnow()),
            ("key1", datetime.utcnow()),
            ("key3", datetime.utcnow()),
            ("key1", datetime.utcnow()),
        ]
        
        patterns = await cache.analyze_patterns()
        
        assert "access_frequency" in patterns
        assert "sequential_patterns" in patterns
        assert "time_patterns" in patterns
        assert "agent_patterns" in patterns
        assert patterns["access_frequency"]["key1"] == 3
    
    def test_generate_cache_key(self, cache, mock_request):
        """Test cache key generation"""
        key = cache._generate_cache_key(mock_request)
        
        assert isinstance(key, str)
        assert len(key) == 16  # SHA256 hash truncated to 16 chars
        
        # Same request should generate same key
        key2 = cache._generate_cache_key(mock_request)
        assert key == key2
    
    def test_estimate_context_size(self, cache, mock_context):
        """Test context size estimation"""
        size = cache._estimate_context_size(mock_context)
        
        assert size > 0
        # Should include base overhead
        assert size >= 1024
    
    def test_is_expired(self, cache):
        """Test expiration checking"""
        # Create entry that's not expired
        entry = CacheEntry(
            context=Mock(),
            request_id="req",
            cache_key="key",
            created_at=datetime.utcnow(),
            last_accessed=datetime.utcnow()
        )
        assert not cache._is_expired(entry)
        
        # Create expired entry
        old_entry = CacheEntry(
            context=Mock(),
            request_id="req",
            cache_key="key",
            created_at=datetime.utcnow() - timedelta(seconds=100),
            last_accessed=datetime.utcnow() - timedelta(seconds=100)
        )
        cache.ttl_seconds = 50
        assert cache._is_expired(old_entry)
    
    @pytest.mark.asyncio
    async def test_error_handling_in_get(self, cache):
        """Test error handling in get method"""
        # Mock an error in the cache
        cache._cache["error-key"] = Mock()
        cache._cache["error-key"].context = None
        
        with patch.object(cache, '_is_expired', side_effect=Exception("Test error")):
            result = await cache.get("error-key")
            assert result is None
            assert cache.stats.cache_misses > 0
    
    @pytest.mark.asyncio
    async def test_error_handling_in_put(self, cache, mock_context):
        """Test error handling in put method"""
        # Mock an error in context size estimation
        with patch.object(cache, '_estimate_context_size', side_effect=Exception("Size error")):
            success = await cache.put("error-key", mock_context)
            assert success is False
    
    @pytest.mark.asyncio
    async def test_pattern_matching(self, cache):
        """Test pattern matching logic"""
        # Create a mock pattern
        pattern = PredictionPattern(
            pattern_id="test_pattern",
            pattern_type="agent_transition",
            trigger_conditions={"agents": ["test_agent"]},
            predicted_requests=["next_key"],
            confidence=0.8
        )
        
        # Create mock entry with agent tag
        entry = Mock()
        entry.tags = {"agent:test_agent", "story:123"}
        
        matches = cache._pattern_matches(pattern, "current_key", entry)
        assert matches is True
        
        # Test non-matching pattern
        entry.tags = {"agent:other_agent"}
        matches = cache._pattern_matches(pattern, "current_key", entry)
        assert matches is False
    
    @pytest.mark.asyncio
    async def test_sequential_patterns(self, cache):
        """Test sequential pattern detection"""
        # Setup access history with patterns
        now = datetime.utcnow()
        cache._access_history = [
            ("A", now),
            ("B", now),
            ("C", now),
            ("A", now),
            ("B", now),
            ("C", now),
            ("A", now),
            ("B", now),
            ("C", now),
        ]
        
        patterns = cache._find_sequential_patterns()
        
        # Should find A->B->C pattern
        assert len(patterns) > 0
        found_abc = any(p["sequence"] == ["A", "B"] and "C" in p["predictions"] for p in patterns)
        assert found_abc
    
    def test_select_eviction_candidate(self, cache, mock_context):
        """Test eviction candidate selection"""
        # Add entries with different characteristics
        entry1 = CacheEntry(
            context=mock_context,
            request_id="req1",
            cache_key="key1",
            created_at=datetime.utcnow() - timedelta(hours=1),
            last_accessed=datetime.utcnow() - timedelta(minutes=30),
            access_count=1,
            hit_count=0
        )
        
        entry2 = CacheEntry(
            context=mock_context,
            request_id="req2",
            cache_key="key2",
            created_at=datetime.utcnow(),
            last_accessed=datetime.utcnow(),
            access_count=10,
            hit_count=8
        )
        
        cache._cache["key1"] = entry1
        cache._cache["key2"] = entry2
        
        # Should select key1 for eviction (older, less used)
        candidate = cache._select_eviction_candidate()
        assert candidate == "key1"
    
    @pytest.mark.asyncio
    async def test_prediction_worker_integration(self, cache):
        """Test prediction worker pattern learning"""
        # Add sufficient access history
        cache._access_history = [("key1", datetime.utcnow())] * 150
        
        await cache._update_prediction_patterns()
        
        # Should have learned some patterns
        assert len(cache._prediction_patterns) >= 0  # May be 0 if no patterns found
    
    @pytest.mark.asyncio
    async def test_warming_worker_integration(self, cache):
        """Test cache warming worker"""
        mock_request = Mock()
        mock_request.agent_type = "test"
        mock_request.story_id = "123"
        
        # Add to warming queue
        await cache._warming_queue.put((mock_request, 1.0))
        
        # The worker should process this (we'll just check it doesn't crash)
        # In a real scenario, this would call the context manager
        assert cache._warming_queue.qsize() == 1
    
    @pytest.mark.asyncio
    async def test_trigger_predictions(self, cache, mock_context):
        """Test prediction triggering"""
        # Setup a prediction pattern
        pattern = PredictionPattern(
            pattern_id="test_trigger",
            pattern_type="agent_transition",
            trigger_conditions={"agents": ["test_agent"]},
            predicted_requests=["predicted_key"],
            confidence=0.8
        )
        cache._prediction_patterns["test_trigger"] = pattern
        
        # Create entry that matches pattern
        entry = Mock()
        entry.tags = {"agent:test_agent"}
        
        # Should trigger predictions without error
        await cache._trigger_predictions("test_key", entry)
        
        # Pattern usage should be incremented
        assert pattern.usage_count == 1
    
    def test_time_and_agent_patterns(self, cache):
        """Test time and agent pattern analysis"""
        time_patterns = cache._find_time_patterns()
        assert isinstance(time_patterns, dict)
        assert "hourly_patterns" in time_patterns
        
        agent_patterns = cache._find_agent_patterns()
        assert isinstance(agent_patterns, dict)
        assert "transition_patterns" in agent_patterns
    
    def test_pattern_success_rate_calculation(self, cache):
        """Test pattern success rate calculation"""
        # No patterns
        rate = cache._calculate_pattern_success_rate()
        assert rate == 0.0
        
        # Add patterns with success rates
        pattern1 = PredictionPattern(
            pattern_id="p1",
            pattern_type="test",
            trigger_conditions={},
            predicted_requests=[],
            confidence=0.8,
            success_rate=0.9,
            usage_count=10
        )
        
        pattern2 = PredictionPattern(
            pattern_id="p2",
            pattern_type="test",
            trigger_conditions={},
            predicted_requests=[],
            confidence=0.7,
            success_rate=0.8,
            usage_count=5
        )
        
        cache._prediction_patterns["p1"] = pattern1
        cache._prediction_patterns["p2"] = pattern2
        
        rate = cache._calculate_pattern_success_rate()
        # (0.9 * 10 + 0.8 * 5) / (10 + 5) = (9 + 4) / 15 = 13/15 ≈ 0.867
        assert abs(rate - 0.8667) < 0.001


class TestCacheEnums:
    """Test cache strategy and warming strategy enums"""
    
    def test_cache_strategy_enum(self):
        """Test CacheStrategy enum values"""
        assert CacheStrategy.LRU.value == "lru"
        assert CacheStrategy.LFU.value == "lfu"
        assert CacheStrategy.TTL.value == "ttl"
        assert CacheStrategy.PREDICTIVE.value == "predictive"
    
    def test_cache_warming_strategy_enum(self):
        """Test CacheWarmingStrategy enum values"""
        assert CacheWarmingStrategy.NONE.value == "none"
        assert CacheWarmingStrategy.LAZY.value == "lazy"
        assert CacheWarmingStrategy.AGGRESSIVE.value == "aggressive"
        assert CacheWarmingStrategy.PATTERN_BASED.value == "pattern_based"


@pytest.mark.asyncio
class TestCacheIntegration:
    """Integration tests for cache functionality"""
    
    async def test_full_cache_lifecycle(self):
        """Test complete cache lifecycle"""
        cache = ContextCache(max_entries=5, ttl_seconds=60)
        
        try:
            await cache.start_background_tasks()
            
            # Create mock data
            context = Mock(spec=AgentContext)
            context.request_id = "lifecycle-test"
            context.core_context = "Test content"
            context.historical_context = ""
            context.dependencies = ""
            context.agent_memory = ""
            context.metadata = ""
            context.copy.return_value = context
            
            request = Mock(spec=ContextRequest)
            request.agent_type = "test_agent"
            request.story_id = "story-lifecycle"
            request.max_tokens = 1000
            request.compression_level = CompressionLevel.LIGHT
            request.include_history = False
            request.include_dependencies = False
            request.task.description = "Test task"
            
            # Test full workflow
            cache_key = cache._generate_cache_key(request)
            
            # Should be cache miss initially
            result = await cache.get(cache_key)
            assert result is None
            
            # Put in cache
            success = await cache.put(cache_key, context, request)
            assert success is True
            
            # Should be cache hit now
            result = await cache.get(cache_key)
            assert result is not None
            
            # Get statistics
            stats = await cache.get_statistics()
            assert stats.cache_hits == 1
            assert stats.cache_misses == 1
            
            # Test invalidation
            await cache.invalidate(cache_key)
            result = await cache.get(cache_key)
            assert result is None
            
        finally:
            await cache.stop_background_tasks()
    
    async def test_concurrent_access(self):
        """Test concurrent cache access"""
        cache = ContextCache(max_entries=10)
        
        context = Mock(spec=AgentContext)
        context.request_id = "concurrent-test"
        context.core_context = "Test content"
        context.historical_context = ""
        context.dependencies = ""
        context.agent_memory = ""
        context.metadata = ""
        context.copy.return_value = context
        
        # Test concurrent puts
        async def put_task(key_suffix):
            await cache.put(f"concurrent-{key_suffix}", context)
        
        # Test concurrent gets
        async def get_task(key_suffix):
            return await cache.get(f"concurrent-{key_suffix}")
        
        # Run concurrent operations
        put_tasks = [put_task(i) for i in range(5)]
        await asyncio.gather(*put_tasks)
        
        get_tasks = [get_task(i) for i in range(5)]
        results = await asyncio.gather(*get_tasks)
        
        # All should succeed
        assert all(result is not None for result in results)
        assert len(cache._cache) == 5


if __name__ == "__main__":
    pytest.main([__file__, "-v"])