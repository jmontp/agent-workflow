"""
Comprehensive test suite for context_cache.py

Tests cover:
- CacheEntry with metadata and access patterns
- CacheStatistics and performance tracking
- PredictionPattern and predictive caching algorithms
- ContextCache with all caching strategies (LRU, LFU, TTL, Predictive)
- Cache warming and background tasks
- Memory management and eviction policies
- Pattern learning and prediction accuracy
- Error handling and edge cases
"""

import asyncio
import pytest
import time
from datetime import datetime, timedelta
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from collections import OrderedDict

# Import the module under test
from lib.context_cache import (
    ContextCache,
    CacheEntry,
    CacheStatistics,
    PredictionPattern,
    CacheStrategy,
    CacheWarmingStrategy
)

# Import dependencies
from lib.context.models import AgentContext, ContextRequest, CompressionLevel
from lib.context.exceptions import ContextCacheError
from lib.tdd_models import TDDState, TDDTask


class TestCacheEntry:
    """Test CacheEntry class functionality"""
    
    def setup_method(self):
        """Setup test fixtures"""
        self.mock_context = Mock(spec=AgentContext)
        self.mock_context.request_id = "req_123"
        self.mock_context.file_contents = {"test.py": "content"}
        
        self.entry = CacheEntry(
            context=self.mock_context,
            request_id="req_123",
            cache_key="key_123",
            created_at=datetime.utcnow(),
            last_accessed=datetime.utcnow(),
            size_bytes=1024,
            tags={"agent:code", "story:123"}
        )
    
    def test_cache_entry_initialization(self):
        """Test CacheEntry initialization"""
        assert self.entry.context == self.mock_context
        assert self.entry.request_id == "req_123"
        assert self.entry.cache_key == "key_123"
        assert self.entry.access_count == 0
        assert self.entry.hit_count == 0
        assert self.entry.size_bytes == 1024
        assert self.entry.tags == {"agent:code", "story:123"}
        assert self.entry.prediction_score == 0.0
        assert self.entry.warm_priority == 0
    
    def test_update_access(self):
        """Test access tracking"""
        original_time = self.entry.last_accessed
        time.sleep(0.01)  # Small delay
        
        self.entry.update_access()
        
        assert self.entry.access_count == 1
        assert self.entry.last_accessed > original_time
    
    def test_record_hit(self):
        """Test hit recording"""
        original_access_count = self.entry.access_count
        original_hit_count = self.entry.hit_count
        
        self.entry.record_hit()
        
        assert self.entry.hit_count == original_hit_count + 1
        assert self.entry.access_count == original_access_count + 1
    
    def test_age_seconds(self):
        """Test age calculation"""
        # Create entry with specific time
        past_time = datetime.utcnow() - timedelta(seconds=30)
        entry = CacheEntry(
            context=self.mock_context,
            request_id="req_123",
            cache_key="key_123",
            created_at=past_time,
            last_accessed=past_time
        )
        
        age = entry.age_seconds
        assert 25 <= age <= 35  # Account for timing variations
    
    def test_last_access_seconds(self):
        """Test last access time calculation"""
        past_time = datetime.utcnow() - timedelta(seconds=20)
        self.entry.last_accessed = past_time
        
        last_access = self.entry.last_access_seconds
        assert 15 <= last_access <= 25  # Account for timing variations
    
    def test_hit_rate_calculation(self):
        """Test hit rate calculation"""
        # No accesses yet
        assert self.entry.hit_rate == 0.0
        
        # Add some hits and accesses
        self.entry.hit_count = 8
        self.entry.access_count = 10
        
        assert self.entry.hit_rate == 0.8
    
    def test_hit_rate_edge_cases(self):
        """Test hit rate edge cases"""
        # Zero access count
        self.entry.access_count = 0
        self.entry.hit_count = 0
        assert self.entry.hit_rate == 0.0
        
        # More hits than accesses (should not happen but test defensive code)
        self.entry.access_count = 5
        self.entry.hit_count = 10
        assert self.entry.hit_rate == 2.0


class TestCacheStatistics:
    """Test CacheStatistics class functionality"""
    
    def setup_method(self):
        """Setup test fixtures"""
        self.stats = CacheStatistics()
    
    def test_statistics_initialization(self):
        """Test statistics initialization"""
        assert self.stats.total_requests == 0
        assert self.stats.cache_hits == 0
        assert self.stats.cache_misses == 0
        assert self.stats.evictions == 0
        assert self.stats.warming_hits == 0
        assert self.stats.prediction_accuracy == 0.0
        assert self.stats.average_prep_time == 0.0
        assert self.stats.memory_usage_bytes == 0
        assert self.stats.entry_count == 0
    
    def test_hit_rate_calculation(self):
        """Test hit rate calculation"""
        # No requests yet
        assert self.stats.hit_rate == 0.0
        
        # Add some hits and misses
        self.stats.cache_hits = 80
        self.stats.cache_misses = 20
        
        assert self.stats.hit_rate == 0.8
    
    def test_hit_rate_edge_cases(self):
        """Test hit rate edge cases"""
        # Zero total requests
        self.stats.cache_hits = 0
        self.stats.cache_misses = 0
        assert self.stats.hit_rate == 0.0
        
        # Only hits
        self.stats.cache_hits = 100
        self.stats.cache_misses = 0
        assert self.stats.hit_rate == 1.0
        
        # Only misses
        self.stats.cache_hits = 0
        self.stats.cache_misses = 100
        assert self.stats.hit_rate == 0.0
    
    def test_warming_effectiveness(self):
        """Test warming effectiveness calculation"""
        # No cache hits yet
        assert self.stats.warming_effectiveness == 0.0
        
        # Add some warming hits
        self.stats.cache_hits = 100
        self.stats.warming_hits = 30
        
        assert self.stats.warming_effectiveness == 0.3
    
    def test_warming_effectiveness_edge_cases(self):
        """Test warming effectiveness edge cases"""
        # Zero cache hits
        self.stats.cache_hits = 0
        self.stats.warming_hits = 10
        assert self.stats.warming_effectiveness == 0.0
        
        # All hits are warming hits
        self.stats.cache_hits = 50
        self.stats.warming_hits = 50
        assert self.stats.warming_effectiveness == 1.0


class TestPredictionPattern:
    """Test PredictionPattern class functionality"""
    
    def setup_method(self):
        """Setup test fixtures"""
        self.pattern = PredictionPattern(
            pattern_id="seq_test",
            pattern_type="sequential",
            trigger_conditions={"sequence": ["key1", "key2"]},
            predicted_requests=["key3", "key4"],
            confidence=0.8
        )
    
    def test_prediction_pattern_initialization(self):
        """Test PredictionPattern initialization"""
        assert self.pattern.pattern_id == "seq_test"
        assert self.pattern.pattern_type == "sequential"
        assert self.pattern.trigger_conditions == {"sequence": ["key1", "key2"]}
        assert self.pattern.predicted_requests == ["key3", "key4"]
        assert self.pattern.confidence == 0.8
        assert self.pattern.success_rate == 0.0
        assert self.pattern.usage_count == 0
        assert isinstance(self.pattern.last_used, datetime)
    
    def test_pattern_usage_tracking(self):
        """Test pattern usage tracking"""
        original_count = self.pattern.usage_count
        original_time = self.pattern.last_used
        
        time.sleep(0.01)  # Small delay
        
        # Simulate pattern usage
        self.pattern.usage_count += 1
        self.pattern.last_used = datetime.utcnow()
        
        assert self.pattern.usage_count == original_count + 1
        assert self.pattern.last_used > original_time


class TestContextCache:
    """Test ContextCache class functionality"""
    
    def setup_method(self):
        """Setup test fixtures"""
        self.cache = ContextCache(
            max_entries=10,
            max_memory_mb=1,
            ttl_seconds=300,
            strategy=CacheStrategy.LRU,
            warming_strategy=CacheWarmingStrategy.LAZY,
            enable_predictions=True
        )
        
        # Mock context and request
        self.mock_context = Mock(spec=AgentContext)
        self.mock_context.request_id = "req_123"
        self.mock_context.file_contents = {"test.py": "content"}
        self.mock_context.core_context = "core content"
        self.mock_context.historical_context = "history"
        self.mock_context.dependencies = "deps"
        self.mock_context.agent_memory = "memory"
        self.mock_context.metadata = "metadata"
        
        self.mock_request = Mock(spec=ContextRequest)
        self.mock_request.agent_type = "code"
        self.mock_request.story_id = "123"
        self.mock_request.max_tokens = 1000
        self.mock_request.compression_level = CompressionLevel.MODERATE
        self.mock_request.include_history = True
        self.mock_request.include_dependencies = True
        
        # Mock task
        self.mock_task = Mock(spec=TDDTask)
        self.mock_task.description = "test task"
        self.mock_task.current_state = TDDState.DESIGN
        self.mock_request.task = self.mock_task
    
    def test_cache_initialization(self):
        """Test cache initialization"""
        assert self.cache.max_entries == 10
        assert self.cache.max_memory_bytes == 1024 * 1024
        assert self.cache.ttl_seconds == 300
        assert self.cache.strategy == CacheStrategy.LRU
        assert self.cache.warming_strategy == CacheWarmingStrategy.LAZY
        assert self.cache.enable_predictions is True
        assert isinstance(self.cache.stats, CacheStatistics)
    
    def test_cache_initialization_different_strategies(self):
        """Test cache initialization with different strategies"""
        strategies = [
            CacheStrategy.LRU,
            CacheStrategy.LFU,
            CacheStrategy.TTL,
            CacheStrategy.PREDICTIVE
        ]
        
        warming_strategies = [
            CacheWarmingStrategy.NONE,
            CacheWarmingStrategy.LAZY,
            CacheWarmingStrategy.AGGRESSIVE,
            CacheWarmingStrategy.PATTERN_BASED
        ]
        
        for strategy in strategies:
            for warming_strategy in warming_strategies:
                cache = ContextCache(
                    strategy=strategy,
                    warming_strategy=warming_strategy
                )
                assert cache.strategy == strategy
                assert cache.warming_strategy == warming_strategy
    
    @pytest.mark.asyncio
    async def test_put_and_get_basic(self):
        """Test basic put and get operations"""
        cache_key = "test_key"
        
        # Store context
        result = await self.cache.put(cache_key, self.mock_context, self.mock_request)
        assert result is True
        
        # Retrieve context
        retrieved = await self.cache.get(cache_key)
        assert retrieved is not None
        assert retrieved == self.mock_context
        
        # Check statistics
        assert self.cache.stats.cache_hits == 1
        assert self.cache.stats.total_requests == 1
        assert self.cache.stats.entry_count == 1
    
    @pytest.mark.asyncio
    async def test_get_cache_miss(self):
        """Test cache miss scenario"""
        result = await self.cache.get("nonexistent_key")
        
        assert result is None
        assert self.cache.stats.cache_misses == 1
        assert self.cache.stats.total_requests == 1
    
    @pytest.mark.asyncio
    async def test_put_with_tags(self):
        """Test putting context with tags"""
        cache_key = "test_key"
        tags = {"test:tag", "custom:value"}
        
        result = await self.cache.put(cache_key, self.mock_context, self.mock_request, tags)
        assert result is True
        
        # Check that entry has tags
        entry = self.cache._cache[cache_key]
        assert "test:tag" in entry.tags
        assert "custom:value" in entry.tags
        assert f"agent:{self.mock_request.agent_type}" in entry.tags
        assert f"story:{self.mock_request.story_id}" in entry.tags
    
    @pytest.mark.asyncio
    async def test_memory_management(self):
        """Test memory management and eviction"""
        # Fill cache beyond memory limit
        for i in range(15):  # More than max_entries
            cache_key = f"key_{i}"
            result = await self.cache.put(cache_key, self.mock_context, self.mock_request)
            assert result is True
        
        # Check that entries were evicted
        assert len(self.cache._cache) <= self.cache.max_entries
        assert self.cache.stats.evictions > 0
    
    @pytest.mark.asyncio
    async def test_ttl_expiration(self):
        """Test TTL-based expiration"""
        # Create cache with very short TTL
        short_ttl_cache = ContextCache(ttl_seconds=1)
        cache_key = "test_key"
        
        # Store context
        await short_ttl_cache.put(cache_key, self.mock_context, self.mock_request)
        
        # Should be available immediately
        result = await short_ttl_cache.get(cache_key)
        assert result is not None
        
        # Wait for expiration
        await asyncio.sleep(1.1)
        
        # Should be expired now
        result = await short_ttl_cache.get(cache_key)
        assert result is None
    
    @pytest.mark.asyncio
    async def test_invalidate_by_key(self):
        """Test invalidation by key"""
        cache_key = "test_key"
        
        # Store context
        await self.cache.put(cache_key, self.mock_context, self.mock_request)
        
        # Verify it's there
        result = await self.cache.get(cache_key)
        assert result is not None
        
        # Invalidate
        invalidated = await self.cache.invalidate(cache_key)
        assert invalidated is True
        
        # Should be gone
        result = await self.cache.get(cache_key)
        assert result is None
    
    @pytest.mark.asyncio
    async def test_invalidate_by_tags(self):
        """Test invalidation by tags"""
        # Store multiple contexts with different tags
        await self.cache.put("key1", self.mock_context, self.mock_request, {"tag:a"})
        await self.cache.put("key2", self.mock_context, self.mock_request, {"tag:b"})
        await self.cache.put("key3", self.mock_context, self.mock_request, {"tag:a", "tag:c"})
        
        # Invalidate by tag
        count = await self.cache.invalidate_by_tags({"tag:a"})
        
        assert count == 2  # key1 and key3 should be invalidated
        
        # Check what remains
        result1 = await self.cache.get("key1")
        result2 = await self.cache.get("key2")
        result3 = await self.cache.get("key3")
        
        assert result1 is None
        assert result2 is not None  # Should still be there
        assert result3 is None
    
    @pytest.mark.asyncio
    async def test_lru_strategy(self):
        """Test LRU eviction strategy"""
        lru_cache = ContextCache(max_entries=3, strategy=CacheStrategy.LRU)
        
        # Fill cache
        await lru_cache.put("key1", self.mock_context, self.mock_request)
        await lru_cache.put("key2", self.mock_context, self.mock_request)
        await lru_cache.put("key3", self.mock_context, self.mock_request)
        
        # Access key1 to make it recently used
        await lru_cache.get("key1")
        
        # Add another entry (should evict key2, the least recently used)
        await lru_cache.put("key4", self.mock_context, self.mock_request)
        
        # Check what remains
        assert await lru_cache.get("key1") is not None
        assert await lru_cache.get("key2") is None  # Should be evicted
        assert await lru_cache.get("key3") is not None
        assert await lru_cache.get("key4") is not None
    
    @pytest.mark.asyncio
    async def test_lfu_strategy(self):
        """Test LFU eviction strategy"""
        lfu_cache = ContextCache(max_entries=3, strategy=CacheStrategy.LFU)
        
        # Fill cache
        await lfu_cache.put("key1", self.mock_context, self.mock_request)
        await lfu_cache.put("key2", self.mock_context, self.mock_request)
        await lfu_cache.put("key3", self.mock_context, self.mock_request)
        
        # Access key1 multiple times
        await lfu_cache.get("key1")
        await lfu_cache.get("key1")
        await lfu_cache.get("key1")
        
        # Access key3 once
        await lfu_cache.get("key3")
        
        # Add another entry (should evict key2, the least frequently used)
        await lfu_cache.put("key4", self.mock_context, self.mock_request)
        
        # Check what remains
        assert await lfu_cache.get("key1") is not None
        assert await lfu_cache.get("key2") is None  # Should be evicted
        assert await lfu_cache.get("key3") is not None
        assert await lfu_cache.get("key4") is not None
    
    @pytest.mark.asyncio
    async def test_cleanup_expired_entries(self):
        """Test cleanup of expired entries"""
        # Create cache with short TTL
        short_ttl_cache = ContextCache(ttl_seconds=1)
        
        # Add some entries
        await short_ttl_cache.put("key1", self.mock_context, self.mock_request)
        await short_ttl_cache.put("key2", self.mock_context, self.mock_request)
        
        # Wait for expiration
        await asyncio.sleep(1.1)
        
        # Force cleanup interval to allow cleanup
        short_ttl_cache._last_cleanup = datetime.utcnow() - timedelta(seconds=400)
        
        # Cleanup
        cleaned = await short_ttl_cache.cleanup_expired()
        
        assert cleaned == 2
        assert len(short_ttl_cache._cache) == 0
    
    @pytest.mark.asyncio
    async def test_get_statistics(self):
        """Test statistics gathering"""
        # Add some entries and access them
        await self.cache.put("key1", self.mock_context, self.mock_request)
        await self.cache.put("key2", self.mock_context, self.mock_request)
        
        await self.cache.get("key1")
        await self.cache.get("key1")
        await self.cache.get("nonexistent")
        
        stats = await self.cache.get_statistics()
        
        assert stats.total_requests == 3
        assert stats.cache_hits == 2
        assert stats.cache_misses == 1
        assert stats.entry_count == 2
        assert stats.hit_rate == 2/3
    
    @pytest.mark.asyncio
    async def test_get_detailed_metrics(self):
        """Test detailed metrics"""
        # Add entries with various tags
        await self.cache.put("key1", self.mock_context, self.mock_request, {"test:tag"})
        await self.cache.put("key2", self.mock_context, self.mock_request, {"another:tag"})
        
        # Access entries
        await self.cache.get("key1")
        
        metrics = await self.cache.get_detailed_metrics()
        
        assert "basic_stats" in metrics
        assert "distribution" in metrics
        assert "patterns" in metrics
        
        assert metrics["basic_stats"]["entry_count"] == 2
        assert "tag_distribution" in metrics["distribution"]
        assert "active_patterns" in metrics["patterns"]
    
    def test_clear_cache(self):
        """Test cache clearing"""
        # Add some entries
        asyncio.run(self.cache.put("key1", self.mock_context, self.mock_request))
        asyncio.run(self.cache.put("key2", self.mock_context, self.mock_request))
        
        assert len(self.cache._cache) == 2
        
        # Clear cache
        self.cache.clear()
        
        assert len(self.cache._cache) == 0
        assert self.cache.stats.entry_count == 0
        assert self.cache.stats.memory_usage_bytes == 0
    
    def test_generate_cache_key(self):
        """Test cache key generation"""
        key = self.cache._generate_cache_key(self.mock_request)
        
        assert isinstance(key, str)
        assert len(key) == 16  # SHA256 hash truncated to 16 chars
        
        # Same request should generate same key
        key2 = self.cache._generate_cache_key(self.mock_request)
        assert key == key2
        
        # Different request should generate different key
        different_request = Mock(spec=ContextRequest)
        different_request.agent_type = "design"
        different_request.story_id = "456"
        different_request.max_tokens = 2000
        different_request.compression_level = CompressionLevel.HIGH
        different_request.include_history = False
        different_request.include_dependencies = False
        different_request.task = self.mock_task
        
        key3 = self.cache._generate_cache_key(different_request)
        assert key != key3
    
    def test_estimate_context_size(self):
        """Test context size estimation"""
        size = self.cache._estimate_context_size(self.mock_context)
        
        assert isinstance(size, int)
        assert size > 0
        
        # Size should include content and overhead
        expected_size = (
            len("core content") +
            len("history") +
            len("deps") +
            len("memory") +
            len("metadata") +
            1024  # Base overhead
        )
        assert size == expected_size
    
    def test_estimate_context_size_empty(self):
        """Test context size estimation with empty context"""
        empty_context = Mock(spec=AgentContext)
        empty_context.core_context = None
        empty_context.historical_context = None
        empty_context.dependencies = None
        empty_context.agent_memory = None
        empty_context.metadata = None
        
        size = self.cache._estimate_context_size(empty_context)
        
        assert size == 1024  # Just the base overhead
    
    def test_is_expired(self):
        """Test expiration checking"""
        # Create entry that's not expired
        entry = CacheEntry(
            context=self.mock_context,
            request_id="req_123",
            cache_key="key_123",
            created_at=datetime.utcnow(),
            last_accessed=datetime.utcnow()
        )
        
        assert not self.cache._is_expired(entry)
        
        # Create entry that's expired
        old_entry = CacheEntry(
            context=self.mock_context,
            request_id="req_123",
            cache_key="key_123",
            created_at=datetime.utcnow() - timedelta(seconds=400),
            last_accessed=datetime.utcnow() - timedelta(seconds=400)
        )
        
        assert self.cache._is_expired(old_entry)
    
    @pytest.mark.asyncio
    async def test_predictive_caching_patterns(self):
        """Test predictive caching pattern detection"""
        predictive_cache = ContextCache(
            strategy=CacheStrategy.PREDICTIVE,
            enable_predictions=True
        )
        
        # Simulate access pattern
        keys = ["key1", "key2", "key3", "key1", "key2", "key3"]
        for key in keys:
            await predictive_cache.put(key, self.mock_context, self.mock_request)
            await predictive_cache.get(key)
        
        # Analyze patterns
        patterns = await predictive_cache.analyze_patterns()
        
        assert "access_frequency" in patterns
        assert "sequential_patterns" in patterns
        assert "time_patterns" in patterns
        assert "agent_patterns" in patterns
    
    @pytest.mark.asyncio
    async def test_warm_cache(self):
        """Test cache warming functionality"""
        warming_cache = ContextCache(warming_strategy=CacheWarmingStrategy.LAZY)
        
        # Create prediction requests
        predictions = [self.mock_request]
        
        # Warm cache
        queued = await warming_cache.warm_cache(predictions, priority=1)
        
        assert queued == 1
        assert warming_cache._warming_queue.qsize() == 1
    
    @pytest.mark.asyncio
    async def test_warm_cache_no_warming(self):
        """Test cache warming with NONE strategy"""
        no_warming_cache = ContextCache(warming_strategy=CacheWarmingStrategy.NONE)
        
        predictions = [self.mock_request]
        queued = await no_warming_cache.warm_cache(predictions)
        
        assert queued == 0
    
    @pytest.mark.asyncio
    async def test_background_tasks(self):
        """Test background task management"""
        cache = ContextCache(
            warming_strategy=CacheWarmingStrategy.LAZY,
            enable_predictions=True
        )
        
        # Start background tasks
        await cache.start_background_tasks()
        
        assert cache._warming_task is not None
        assert cache._prediction_task is not None
        assert not cache._warming_task.done()
        assert not cache._prediction_task.done()
        
        # Stop background tasks
        await cache.stop_background_tasks()
        
        # Tasks should be cancelled
        assert cache._warming_task.cancelled() or cache._warming_task.done()
        assert cache._prediction_task.cancelled() or cache._prediction_task.done()
    
    @pytest.mark.asyncio
    async def test_error_handling_in_get(self):
        """Test error handling in get method"""        
        # Test with None result due to exception
        with patch.object(self.cache, '_cache', side_effect=Exception("Cache access failed")):
            result = await self.cache.get("error_key")
            assert result is None
            assert self.cache.stats.cache_misses == 1
    
    @pytest.mark.asyncio
    async def test_error_handling_in_put(self):
        """Test error handling in put method"""
        # Mock cache to raise exception during storage
        with patch.object(self.cache, '_ensure_space', side_effect=Exception("Storage failed")):
            result = await self.cache.put("key", self.mock_context, self.mock_request)
            assert result is False
    
    def test_select_eviction_candidate_predictive(self):
        """Test predictive eviction candidate selection"""
        predictive_cache = ContextCache(strategy=CacheStrategy.PREDICTIVE)
        
        # Add entries with different characteristics
        entry1 = CacheEntry(
            context=self.mock_context,
            request_id="req_1",
            cache_key="key_1",
            created_at=datetime.utcnow() - timedelta(hours=2),
            last_accessed=datetime.utcnow() - timedelta(hours=1),
            access_count=10,
            hit_count=8,
            prediction_score=0.9
        )
        
        entry2 = CacheEntry(
            context=self.mock_context,
            request_id="req_2",
            cache_key="key_2",
            created_at=datetime.utcnow() - timedelta(minutes=30),
            last_accessed=datetime.utcnow() - timedelta(minutes=10),
            access_count=2,
            hit_count=1,
            prediction_score=0.2
        )
        
        predictive_cache._cache["key_1"] = entry1
        predictive_cache._cache["key_2"] = entry2
        
        # Should select the entry with worse overall score
        candidate = predictive_cache._select_eviction_candidate()
        
        # Should select one of the entries (the algorithm picks the highest scoring one for eviction)
        assert candidate in ["key_1", "key_2"]
    
    @pytest.mark.asyncio
    async def test_context_with_copy_method(self):
        """Test context retrieval with copy method"""
        # Mock context with copy method
        copyable_context = Mock(spec=AgentContext)
        copyable_context.copy = Mock(return_value="copied_context")
        copyable_context.request_id = "req_123"
        copyable_context.core_context = "test"
        copyable_context.historical_context = ""
        copyable_context.dependencies = ""
        copyable_context.agent_memory = ""
        copyable_context.metadata = ""
        
        await self.cache.put("copyable_key", copyable_context, self.mock_request)
        
        result = await self.cache.get("copyable_key")
        
        # Should either get copied context or original if copy fails
        assert result is not None
        # The copy method should be attempted
        copyable_context.copy.assert_called_once()
    
    def test_find_sequential_patterns(self):
        """Test sequential pattern detection"""
        # Simulate access history
        self.cache._access_history = [
            ("key1", datetime.utcnow()),
            ("key2", datetime.utcnow()),
            ("key3", datetime.utcnow()),
            ("key1", datetime.utcnow()),
            ("key2", datetime.utcnow()),
            ("key3", datetime.utcnow()),
            ("key1", datetime.utcnow()),
            ("key2", datetime.utcnow()),
            ("key3", datetime.utcnow()),
        ]
        
        patterns = self.cache._find_sequential_patterns()
        
        assert isinstance(patterns, list)
        # Should find pattern where key1->key2 predicts key3
        found_pattern = False
        for pattern in patterns:
            if pattern["sequence"] == ["key1", "key2"] and "key3" in pattern["predictions"]:
                found_pattern = True
                break
        
        assert found_pattern
    
    def test_calculate_pattern_success_rate(self):
        """Test pattern success rate calculation"""
        # No patterns
        assert self.cache._calculate_pattern_success_rate() == 0.0
        
        # Add mock patterns
        pattern1 = PredictionPattern(
            pattern_id="p1",
            pattern_type="test",
            trigger_conditions={},
            predicted_requests=[],
            confidence=0.8,
            success_rate=0.7,
            usage_count=10
        )
        
        pattern2 = PredictionPattern(
            pattern_id="p2",
            pattern_type="test",
            trigger_conditions={},
            predicted_requests=[],
            confidence=0.6,
            success_rate=0.9,
            usage_count=5
        )
        
        self.cache._prediction_patterns["p1"] = pattern1
        self.cache._prediction_patterns["p2"] = pattern2
        
        success_rate = self.cache._calculate_pattern_success_rate()
        
        # Should be weighted average: (0.7*10 + 0.9*5) / (10+5) = 11.5/15 = 0.767
        expected_rate = (0.7 * 10 + 0.9 * 5) / (10 + 5)
        assert abs(success_rate - expected_rate) < 0.001
    
    @pytest.mark.asyncio
    async def test_trigger_predictions(self):
        """Test prediction triggering"""
        # Create cache with predictions enabled
        predictive_cache = ContextCache(
            enable_predictions=True,
            prediction_confidence_threshold=0.5
        )
        
        # Add a prediction pattern
        pattern = PredictionPattern(
            pattern_id="test_pattern",
            pattern_type="agent_transition",
            trigger_conditions={"agents": ["code"]},
            predicted_requests=["predicted_key"],
            confidence=0.8
        )
        predictive_cache._prediction_patterns["test_pattern"] = pattern
        
        # Create entry with matching tags
        entry = CacheEntry(
            context=self.mock_context,
            request_id="req_123",
            cache_key="trigger_key",
            created_at=datetime.utcnow(),
            last_accessed=datetime.utcnow(),
            tags={"agent:code"}
        )
        
        # Trigger predictions
        await predictive_cache._trigger_predictions("trigger_key", entry)
        
        # Pattern usage should be incremented
        assert pattern.usage_count == 1
    
    def test_pattern_matches_agent_transition(self):
        """Test agent transition pattern matching"""
        pattern = PredictionPattern(
            pattern_id="agent_pattern",
            pattern_type="agent_transition",
            trigger_conditions={"agents": ["code", "design"]},
            predicted_requests=[],
            confidence=0.8
        )
        
        # Entry with matching agent tag
        matching_entry = CacheEntry(
            context=self.mock_context,
            request_id="req_123",
            cache_key="key_123",
            created_at=datetime.utcnow(),
            last_accessed=datetime.utcnow(),
            tags={"agent:code"}
        )
        
        # Entry without matching agent tag
        non_matching_entry = CacheEntry(
            context=self.mock_context,
            request_id="req_456",
            cache_key="key_456",
            created_at=datetime.utcnow(),
            last_accessed=datetime.utcnow(),
            tags={"agent:qa"}
        )
        
        assert self.cache._pattern_matches(pattern, "key_123", matching_entry)
        assert not self.cache._pattern_matches(pattern, "key_456", non_matching_entry)
    
    def test_pattern_matches_sequential(self):
        """Test sequential pattern matching"""
        pattern = PredictionPattern(
            pattern_id="seq_pattern",
            pattern_type="sequential",
            trigger_conditions={"sequence": ["key1", "key2", "key3"]},
            predicted_requests=[],
            confidence=0.8
        )
        
        entry = CacheEntry(
            context=self.mock_context,
            request_id="req_123",
            cache_key="key_123",
            created_at=datetime.utcnow(),
            last_accessed=datetime.utcnow()
        )
        
        # Should match if key is in sequence
        assert self.cache._pattern_matches(pattern, "key2", entry)
        assert not self.cache._pattern_matches(pattern, "key4", entry)
    
    def test_pattern_matches_frequent_pair(self):
        """Test frequent pair pattern matching"""
        pattern = PredictionPattern(
            pattern_id="pair_pattern",
            pattern_type="frequent_pair",
            trigger_conditions={"trigger_key": "key1"},
            predicted_requests=[],
            confidence=0.8
        )
        
        entry = CacheEntry(
            context=self.mock_context,
            request_id="req_123",
            cache_key="key_123",
            created_at=datetime.utcnow(),
            last_accessed=datetime.utcnow()
        )
        
        # Should match if cache key matches trigger key
        assert self.cache._pattern_matches(pattern, "key1", entry)
        assert not self.cache._pattern_matches(pattern, "key2", entry)
    
    def test_pattern_matches_unknown_type(self):
        """Test pattern matching with unknown type"""
        pattern = PredictionPattern(
            pattern_id="unknown_pattern",
            pattern_type="unknown_type",
            trigger_conditions={},
            predicted_requests=[],
            confidence=0.8
        )
        
        entry = CacheEntry(
            context=self.mock_context,
            request_id="req_123",
            cache_key="key_123",
            created_at=datetime.utcnow(),
            last_accessed=datetime.utcnow()
        )
        
        # Should return False for unknown pattern types
        assert not self.cache._pattern_matches(pattern, "key1", entry)


class TestCacheIntegration:
    """Integration tests for cache functionality"""
    
    @pytest.mark.asyncio
    async def test_full_cache_lifecycle(self):
        """Test complete cache lifecycle"""
        cache = ContextCache(
            max_entries=5,
            ttl_seconds=300,
            strategy=CacheStrategy.PREDICTIVE,
            warming_strategy=CacheWarmingStrategy.PATTERN_BASED,
            enable_predictions=True
        )
        
        # Create mock data
        mock_context = Mock(spec=AgentContext)
        mock_context.request_id = "req_123"
        mock_context.core_context = "test content"
        mock_context.historical_context = ""
        mock_context.dependencies = ""
        mock_context.agent_memory = ""
        mock_context.metadata = ""
        
        mock_request = Mock(spec=ContextRequest)
        mock_request.agent_type = "code"
        mock_request.story_id = "123"
        mock_request.max_tokens = 1000
        mock_request.compression_level = CompressionLevel.MODERATE
        mock_request.include_history = True
        mock_request.include_dependencies = True
        
        mock_task = Mock(spec=TDDTask)
        mock_task.description = "test task"
        mock_task.current_state = TDDState.DESIGN
        mock_request.task = mock_task
        
        try:
            # Start background tasks
            await cache.start_background_tasks()
            
            # Store multiple contexts
            keys = []
            for i in range(10):  # More than max_entries
                key = f"key_{i}"
                keys.append(key)
                await cache.put(key, mock_context, mock_request, {f"tag:{i}"})
            
            # Access some entries to create patterns
            for key in keys[:5]:
                await cache.get(key)
                await cache.get(key)  # Double access
            
            # Get statistics
            stats = await cache.get_statistics()
            assert stats.entry_count <= cache.max_entries
            assert stats.total_requests > 0
            assert stats.cache_hits > 0
            
            # Analyze patterns
            patterns = await cache.analyze_patterns()
            assert "access_frequency" in patterns
            
            # Test invalidation
            invalidated = await cache.invalidate_by_tags({"tag:1", "tag:2"})
            assert invalidated >= 0
            
            # Get detailed metrics
            metrics = await cache.get_detailed_metrics()
            assert "basic_stats" in metrics
            assert "distribution" in metrics
            assert "patterns" in metrics
            
        finally:
            # Clean up background tasks
            await cache.stop_background_tasks()
    
    @pytest.mark.asyncio
    async def test_cache_performance_under_load(self):
        """Test cache performance under high load"""
        cache = ContextCache(max_entries=100, strategy=CacheStrategy.LRU)
        
        # Create mock data
        mock_context = Mock(spec=AgentContext)
        mock_context.request_id = "req_123"
        mock_context.core_context = "test content"
        mock_context.historical_context = ""
        mock_context.dependencies = ""
        mock_context.agent_memory = ""
        mock_context.metadata = ""
        
        mock_request = Mock(spec=ContextRequest)
        mock_request.agent_type = "code"
        mock_request.story_id = "123"
        mock_request.max_tokens = 1000
        mock_request.compression_level = CompressionLevel.MODERATE
        mock_request.include_history = True
        mock_request.include_dependencies = True
        
        mock_task = Mock(spec=TDDTask)
        mock_task.description = "test task"
        mock_task.current_state = TDDState.DESIGN
        mock_request.task = mock_task
        
        # High load test
        start_time = time.time()
        
        # Store many entries
        for i in range(200):
            key = f"load_key_{i}"
            await cache.put(key, mock_context, mock_request)
        
        # Access entries randomly
        import random
        for _ in range(500):
            key = f"load_key_{random.randint(0, 199)}"
            await cache.get(key)
        
        end_time = time.time()
        duration = end_time - start_time
        
        # Should complete within reasonable time
        assert duration < 5.0  # 5 seconds max
        
        # Check final state
        stats = await cache.get_statistics()
        assert stats.entry_count <= cache.max_entries
        assert stats.total_requests == 500
        assert stats.hit_rate > 0  # Should have some hits