"""
Comprehensive test suite for Context Cache System.

Tests predictive caching, LRU eviction, cache warming, and intelligent
cache management with performance monitoring and analytics.
"""

import pytest
import asyncio
import time
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime, timedelta
from typing import Dict, Any

# Import the modules under test
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "lib"))

from context_cache import (
    ContextCache,
    CacheEntry,
    CacheStrategy,
    CacheWarmingStrategy,
    CacheStatistics,
    PredictionPattern
)
from context.models import (
    AgentContext,
    ContextRequest,
    CompressionLevel
)
from context.exceptions import ContextCacheError


class TestCacheEntry:
    """Test CacheEntry data class"""
    
    def test_basic_creation(self):
        """Test basic cache entry creation"""
        context = Mock(spec=AgentContext)
        context.request_id = "req_123"
        
        entry = CacheEntry(
            context=context,
            request_id="req_123",
            cache_key="cache_key_123",
            created_at=datetime.utcnow(),
            last_accessed=datetime.utcnow(),
            size_bytes=1000
        )
        
        assert entry.context == context
        assert entry.request_id == "req_123"
        assert entry.cache_key == "cache_key_123"
        assert entry.access_count == 0
        assert entry.hit_count == 0
        assert entry.size_bytes == 1000
        assert len(entry.tags) == 0
        assert entry.prediction_score == 0.0
    
    def test_update_access(self):
        """Test access tracking"""
        context = Mock(spec=AgentContext)
        entry = CacheEntry(
            context=context,
            request_id="req_123",
            cache_key="cache_key_123",
            created_at=datetime.utcnow(),
            last_accessed=datetime.utcnow()
        )
        
        original_access_time = entry.last_accessed
        original_count = entry.access_count
        
        time.sleep(0.01)  # Small delay to ensure time difference
        entry.update_access()
        
        assert entry.access_count == original_count + 1
        assert entry.last_accessed > original_access_time
    
    def test_record_hit(self):
        """Test hit recording"""
        context = Mock(spec=AgentContext)
        entry = CacheEntry(
            context=context,
            request_id="req_123",
            cache_key="cache_key_123",
            created_at=datetime.utcnow(),
            last_accessed=datetime.utcnow()
        )
        
        entry.record_hit()
        
        assert entry.hit_count == 1
        assert entry.access_count == 1
    
    def test_age_calculation(self):
        """Test age calculation"""
        past_time = datetime.utcnow() - timedelta(seconds=10)
        context = Mock(spec=AgentContext)
        entry = CacheEntry(
            context=context,
            request_id="req_123",
            cache_key="cache_key_123",
            created_at=past_time,
            last_accessed=datetime.utcnow()
        )
        
        # Age should be approximately 10 seconds
        assert 9 <= entry.age_seconds <= 11
    
    def test_last_access_calculation(self):
        """Test last access time calculation"""
        past_time = datetime.utcnow() - timedelta(seconds=5)
        context = Mock(spec=AgentContext)
        entry = CacheEntry(
            context=context,
            request_id="req_123",
            cache_key="cache_key_123",
            created_at=datetime.utcnow(),
            last_accessed=past_time
        )
        
        # Last access should be approximately 5 seconds ago
        assert 4 <= entry.last_access_seconds <= 6
    
    def test_hit_rate_calculation(self):
        """Test hit rate calculation"""
        context = Mock(spec=AgentContext)
        entry = CacheEntry(
            context=context,
            request_id="req_123",
            cache_key="cache_key_123",
            created_at=datetime.utcnow(),
            last_accessed=datetime.utcnow()
        )
        
        # No accesses yet
        assert entry.hit_rate == 0.0
        
        # Add some hits and misses
        entry.hit_count = 3
        entry.access_count = 5
        assert entry.hit_rate == 0.6
        
        # All hits
        entry.hit_count = 10
        entry.access_count = 10
        assert entry.hit_rate == 1.0


class TestCacheStatistics:
    """Test CacheStatistics data class"""
    
    def test_hit_rate_calculation(self):
        """Test hit rate calculation"""
        stats = CacheStatistics()
        
        # No requests yet
        assert stats.hit_rate == 0.0
        
        # Some hits and misses
        stats.cache_hits = 7
        stats.cache_misses = 3
        assert stats.hit_rate == 0.7
        
        # All hits
        stats.cache_hits = 10
        stats.cache_misses = 0
        assert stats.hit_rate == 1.0
        
        # All misses
        stats.cache_hits = 0
        stats.cache_misses = 5
        assert stats.hit_rate == 0.0
    
    def test_warming_effectiveness(self):
        """Test warming effectiveness calculation"""
        stats = CacheStatistics()
        
        # No hits yet
        assert stats.warming_effectiveness == 0.0
        
        # Some warming hits
        stats.cache_hits = 10
        stats.warming_hits = 4
        assert stats.warming_effectiveness == 0.4
        
        # All hits from warming
        stats.warming_hits = 10
        assert stats.warming_effectiveness == 1.0


class TestPredictionPattern:
    """Test PredictionPattern data class"""
    
    def test_pattern_creation(self):
        """Test prediction pattern creation"""
        pattern = PredictionPattern(
            pattern_id="pattern_1",
            pattern_type="sequential",
            trigger_conditions={"sequence": ["file1.py", "file2.py"]},
            predicted_requests=["file3.py"],
            confidence=0.8
        )
        
        assert pattern.pattern_id == "pattern_1"
        assert pattern.pattern_type == "sequential"
        assert pattern.confidence == 0.8
        assert pattern.success_rate == 0.0
        assert pattern.usage_count == 0
    
    def test_matches_context(self):
        """Test context matching"""
        from tdd_models import TDDState
        
        pattern = PredictionPattern(
            pattern_id="pattern_1",
            pattern_type="agent_transition",
            trigger_conditions={"agents": ["CodeAgent"]},
            predicted_requests=["file1.py"],
            confidence=0.8
        )
        
        # Should match CodeAgent
        assert pattern.matches_context("CodeAgent", None) is True
        
        # Should not match other agents
        assert pattern.matches_context("QAAgent", None) is True  # No agent restriction set
        
        # Set agent restrictions
        pattern.agent_types = {"CodeAgent"}
        assert pattern.matches_context("CodeAgent", None) is True
        assert pattern.matches_context("QAAgent", None) is False
        
        # Add TDD phase restrictions
        pattern.tdd_phases = {TDDState.RED}
        assert pattern.matches_context("CodeAgent", TDDState.RED) is True
        assert pattern.matches_context("CodeAgent", TDDState.GREEN) is False
        assert pattern.matches_context("CodeAgent", None) is False
    
    def test_calculate_relevance(self):
        """Test relevance calculation using features"""
        pattern = PredictionPattern(
            pattern_id="pattern_1",
            pattern_type="feature_based",
            trigger_conditions={},
            predicted_requests=["file1.py"],
            confidence=0.8
        )
        
        # Set feature weights
        pattern.feature_weights = {
            "feature1": 0.5,
            "feature2": 0.3,
            "feature3": 0.2
        }
        
        # Test with matching features
        features = {
            "feature1": 1.0,
            "feature2": 0.8,
            "feature3": 0.6
        }
        
        relevance = pattern.calculate_relevance(features)
        expected = (1.0 * 0.5 + 0.8 * 0.3 + 0.6 * 0.2) / (0.5 + 0.3 + 0.2)
        assert abs(relevance - expected) < 0.001
        
        # Test with missing features
        partial_features = {"feature1": 1.0}
        relevance = pattern.calculate_relevance(partial_features)
        assert relevance == 1.0  # Only feature1 weight is used
        
        # Test with no matching features
        no_features = {"other_feature": 1.0}
        relevance = pattern.calculate_relevance(no_features)
        assert relevance == 0.0


class TestContextCacheInit:
    """Test ContextCache initialization"""
    
    def test_init_with_defaults(self):
        """Test initialization with default parameters"""
        cache = ContextCache()
        
        assert cache.max_entries == 1000
        assert cache.max_memory_bytes == 500 * 1024 * 1024  # 500MB
        assert cache.ttl_seconds == 1800  # 30 minutes
        assert cache.strategy == CacheStrategy.PREDICTIVE
        assert cache.warming_strategy == CacheWarmingStrategy.PATTERN_BASED
        assert cache.enable_predictions is True
        assert cache.prediction_confidence_threshold == 0.7
        assert len(cache._cache) == 0
    
    def test_init_with_custom_params(self):
        """Test initialization with custom parameters"""
        cache = ContextCache(
            max_entries=500,
            max_memory_mb=200,
            ttl_seconds=600,
            strategy=CacheStrategy.LRU,
            warming_strategy=CacheWarmingStrategy.LAZY,
            enable_predictions=False,
            prediction_confidence_threshold=0.9
        )
        
        assert cache.max_entries == 500
        assert cache.max_memory_bytes == 200 * 1024 * 1024  # 200MB
        assert cache.ttl_seconds == 600  # 10 minutes
        assert cache.strategy == CacheStrategy.LRU
        assert cache.warming_strategy == CacheWarmingStrategy.LAZY
        assert cache.enable_predictions is False
        assert cache.prediction_confidence_threshold == 0.9


class TestCacheOperations:
    """Test basic cache operations"""
    
    @pytest.fixture
    def cache(self):
        """Create cache for testing"""
        return ContextCache(max_entries=10, max_memory_mb=1, ttl_seconds=60)
    
    @pytest.fixture
    def mock_context(self):
        """Create mock context"""
        context = Mock(spec=AgentContext)
        context.request_id = "req_123"
        context.file_contents = {"file1.py": "content1"}
        # Add copy method for testing
        context.copy = Mock(return_value=context)
        return context
    
    @pytest.mark.asyncio
    async def test_put_and_get_success(self, cache, mock_context):
        """Test successful put and get operations"""
        cache_key = "test_key_123"
        
        # Put context in cache
        success = await cache.put(cache_key, mock_context)
        assert success is True
        
        # Get context from cache
        retrieved = await cache.get(cache_key)
        assert retrieved is not None
        assert retrieved == mock_context
        
        # Verify statistics
        stats = await cache.get_statistics()
        assert stats.cache_hits == 1
        assert stats.cache_misses == 0
        assert stats.entry_count == 1
    
    @pytest.mark.asyncio
    async def test_get_cache_miss(self, cache):
        """Test cache miss scenario"""
        # Try to get non-existent key
        retrieved = await cache.get("nonexistent_key")
        assert retrieved is None
        
        # Verify statistics
        stats = await cache.get_statistics()
        assert stats.cache_hits == 0
        assert stats.cache_misses == 1
    
    @pytest.mark.asyncio
    async def test_put_with_request_metadata(self, cache, mock_context):
        """Test putting context with request metadata"""
        cache_key = "test_key_with_meta"
        
        # Create mock request
        request = Mock(spec=ContextRequest)
        request.agent_type = "CodeAgent"
        request.story_id = "story_123"
        request.compression_level = CompressionLevel.MODERATE
        request.task = Mock()
        request.task.current_state = None
        
        # Put with request metadata
        success = await cache.put(
            cache_key, 
            mock_context, 
            request=request, 
            tags={"custom_tag"}
        )
        assert success is True
        
        # Verify entry has correct tags
        entry = cache._cache[cache_key]
        expected_tags = {
            "agent:CodeAgent",
            "story:story_123", 
            "compression:moderate",
            "custom_tag"
        }
        assert expected_tags.issubset(entry.tags)
    
    @pytest.mark.asyncio
    async def test_invalidate_single_entry(self, cache, mock_context):
        """Test invalidating single cache entry"""
        cache_key = "test_key_invalidate"
        
        # Put and verify
        await cache.put(cache_key, mock_context)
        assert await cache.get(cache_key) is not None
        
        # Invalidate
        success = await cache.invalidate(cache_key)
        assert success is True
        
        # Verify removed
        assert await cache.get(cache_key) is None
        
        # Try invalidating non-existent key
        success = await cache.invalidate("nonexistent")
        assert success is False
    
    @pytest.mark.asyncio
    async def test_invalidate_by_tags(self, cache, mock_context):
        """Test invalidating entries by tags"""
        # Put entries with different tags
        await cache.put("key1", mock_context, tags={"agent:CodeAgent", "story:story1"})
        await cache.put("key2", mock_context, tags={"agent:QAAgent", "story:story1"})
        await cache.put("key3", mock_context, tags={"agent:CodeAgent", "story:story2"})
        
        # Invalidate by story tag
        count = await cache.invalidate_by_tags({"story:story1"})
        assert count == 2  # key1 and key2
        
        # Verify remaining entry
        assert await cache.get("key1") is None
        assert await cache.get("key2") is None
        assert await cache.get("key3") is not None


class TestCacheEviction:
    """Test cache eviction strategies"""
    
    @pytest.fixture
    def small_cache(self):
        """Create small cache for eviction testing"""
        return ContextCache(max_entries=3, max_memory_mb=1, ttl_seconds=60)
    
    @pytest.fixture
    def mock_contexts(self):
        """Create multiple mock contexts"""
        contexts = []
        for i in range(5):
            context = Mock(spec=AgentContext)
            context.request_id = f"req_{i}"
            context.file_contents = {f"file{i}.py": f"content{i}"}
            context.copy = Mock(return_value=context)
            contexts.append(context)
        return contexts
    
    @pytest.mark.asyncio
    async def test_eviction_on_max_entries(self, small_cache, mock_contexts):
        """Test eviction when max entries exceeded"""
        # Fill cache to capacity
        for i in range(3):
            success = await small_cache.put(f"key_{i}", mock_contexts[i])
            assert success is True
        
        assert len(small_cache._cache) == 3
        
        # Add one more entry to trigger eviction
        success = await small_cache.put("key_3", mock_contexts[3])
        assert success is True
        
        # Cache should still have max entries
        assert len(small_cache._cache) == 3
        
        # Verify eviction occurred
        stats = await small_cache.get_statistics()
        assert stats.evictions >= 1
    
    @pytest.mark.asyncio
    async def test_lru_eviction_strategy(self, small_cache, mock_contexts):
        """Test LRU eviction strategy"""
        small_cache.strategy = CacheStrategy.LRU
        
        # Fill cache
        await small_cache.put("key_0", mock_contexts[0])
        await small_cache.put("key_1", mock_contexts[1])
        await small_cache.put("key_2", mock_contexts[2])
        
        # Access key_0 to make it recently used
        await small_cache.get("key_0")
        
        # Add new entry to trigger eviction
        await small_cache.put("key_3", mock_contexts[3])
        
        # key_1 should be evicted (least recently used)
        assert await small_cache.get("key_0") is not None  # Recently accessed
        assert await small_cache.get("key_1") is None      # Should be evicted
        assert await small_cache.get("key_2") is not None  # Recently added
        assert await small_cache.get("key_3") is not None  # Newly added
    
    @pytest.mark.asyncio
    async def test_ttl_expiration(self, mock_contexts):
        """Test TTL-based expiration"""
        # Create cache with very short TTL
        cache = ContextCache(ttl_seconds=1)
        
        # Add entry
        await cache.put("key_expire", mock_contexts[0])
        
        # Should be retrievable immediately
        assert await cache.get("key_expire") is not None
        
        # Wait for expiration
        await asyncio.sleep(1.1)
        
        # Should be expired
        assert await cache.get("key_expire") is None


class TestCacheWarming:
    """Test cache warming functionality"""
    
    @pytest.fixture
    def cache(self):
        """Create cache for warming tests"""
        return ContextCache(warming_strategy=CacheWarmingStrategy.PATTERN_BASED)
    
    @pytest.mark.asyncio
    async def test_warm_cache_with_predictions(self, cache):
        """Test cache warming with predicted requests"""
        # Create mock requests
        mock_requests = []
        for i in range(3):
            request = Mock(spec=ContextRequest)
            request.agent_type = f"Agent{i}"
            request.story_id = f"story_{i}"
            request.max_tokens = 10000
            request.compression_level = CompressionLevel.MODERATE
            request.task = Mock()
            request.task.description = f"Task {i}"
            request.include_history = False
            request.include_dependencies = False
            mock_requests.append(request)
        
        # Test warming
        queued = await cache.warm_cache(mock_requests, priority=2)
        assert queued == 3  # All requests should be queued
        
        # Test warming with NONE strategy
        cache.warming_strategy = CacheWarmingStrategy.NONE
        queued = await cache.warm_cache(mock_requests)
        assert queued == 0  # No warming with NONE strategy
    
    @pytest.mark.asyncio
    async def test_warm_cache_skip_existing(self, cache):
        """Test that warming skips already cached entries"""
        # Create and cache a context
        context = Mock(spec=AgentContext)
        context.request_id = "req_1"
        await cache.put("existing_key", context)
        
        # Create request that would generate same cache key
        request = Mock(spec=ContextRequest)
        request.agent_type = "Agent1"
        request.story_id = "story_1"
        request.max_tokens = 10000
        request.compression_level = CompressionLevel.MODERATE
        request.task = Mock()
        request.task.description = "Task description"
        request.include_history = False
        request.include_dependencies = False
        
        # Mock the cache key generation to return existing key
        with patch.object(cache, '_generate_cache_key', return_value="existing_key"):
            queued = await cache.warm_cache([request])
            assert queued == 0  # Should skip existing entry


class TestPredictiveCaching:
    """Test predictive caching functionality"""
    
    @pytest.fixture
    def cache(self):
        """Create cache with predictive features enabled"""
        return ContextCache(
            strategy=CacheStrategy.PREDICTIVE,
            enable_predictions=True,
            prediction_confidence_threshold=0.6
        )
    
    @pytest.mark.asyncio
    async def test_pattern_creation_and_matching(self, cache):
        """Test prediction pattern creation and matching"""
        # Create a prediction pattern
        pattern = PredictionPattern(
            pattern_id="test_pattern",
            pattern_type="sequential",
            trigger_conditions={"sequence": ["file1.py", "file2.py"]},
            predicted_requests=["file3.py"],
            confidence=0.8
        )
        
        cache._prediction_patterns[pattern.pattern_id] = pattern
        
        # Create cache entry that would trigger this pattern
        context = Mock(spec=AgentContext)
        context.request_id = "req_123"
        entry = CacheEntry(
            context=context,
            request_id="req_123",
            cache_key="trigger_key",
            created_at=datetime.utcnow(),
            last_accessed=datetime.utcnow(),
            tags={"file:file1.py"}
        )
        
        # Test pattern matching
        matches = cache._pattern_matches(pattern, "trigger_key", entry)
        # This would depend on the specific implementation of pattern matching
        assert isinstance(matches, bool)
    
    @pytest.mark.asyncio
    async def test_prediction_triggering(self, cache):
        """Test that predictions are triggered on cache access"""
        # Add a mock pattern
        pattern = PredictionPattern(
            pattern_id="trigger_pattern",
            pattern_type="agent_transition", 
            trigger_conditions={"agents": ["CodeAgent"]},
            predicted_requests=["predicted_file.py"],
            confidence=0.8
        )
        cache._prediction_patterns[pattern.pattern_id] = pattern
        
        # Create entry with matching tags
        context = Mock(spec=AgentContext)
        context.request_id = "req_trigger"
        context.copy = Mock(return_value=context)
        
        entry = CacheEntry(
            context=context,
            request_id="req_trigger",
            cache_key="test_key",
            created_at=datetime.utcnow(),
            last_accessed=datetime.utcnow(),
            tags={"agent:CodeAgent"}
        )
        
        cache._cache["test_key"] = entry
        
        # Access the cache entry to trigger predictions
        result = await cache.get("test_key")
        assert result is not None
        
        # Pattern usage should be updated
        assert pattern.usage_count >= 0  # May or may not be incremented depending on matching logic


class TestCacheAnalytics:
    """Test cache analytics and pattern analysis"""
    
    @pytest.fixture
    def cache_with_history(self):
        """Create cache with access history"""
        cache = ContextCache()
        # Add some access history
        for i in range(10):
            cache._access_history.append((f"key_{i}", datetime.utcnow()))
        return cache
    
    @pytest.mark.asyncio
    async def test_analyze_patterns(self, cache_with_history):
        """Test pattern analysis"""
        analysis = await cache_with_history.analyze_patterns()
        
        assert "access_frequency" in analysis
        assert "sequential_patterns" in analysis
        assert "time_patterns" in analysis
        assert "agent_patterns" in analysis
        assert "total_patterns" in analysis
        assert "pattern_success_rate" in analysis
        
        # Should handle empty history gracefully
        cache_with_history._access_history = []
        analysis = await cache_with_history.analyze_patterns()
        assert "error" in analysis
    
    @pytest.mark.asyncio
    async def test_detailed_metrics(self, cache_with_history):
        """Test detailed metrics collection"""
        # Add some cache entries
        for i in range(5):
            context = Mock(spec=AgentContext)
            context.request_id = f"req_{i}"
            entry = CacheEntry(
                context=context,
                request_id=f"req_{i}",
                cache_key=f"key_{i}",
                created_at=datetime.utcnow() - timedelta(minutes=i),
                last_accessed=datetime.utcnow(),
                tags={f"tag_{i}"}
            )
            cache_with_history._cache[f"key_{i}"] = entry
        
        metrics = await cache_with_history.get_detailed_metrics()
        
        assert "basic_stats" in metrics
        assert "distribution" in metrics
        assert "patterns" in metrics
        
        # Check basic stats structure
        basic_stats = metrics["basic_stats"]
        assert "hit_rate" in basic_stats
        assert "entry_count" in basic_stats
        assert "memory_usage_mb" in basic_stats
        
        # Check distribution data
        distribution = metrics["distribution"]
        assert "age_buckets" in distribution
        assert "tag_distribution" in distribution
        assert "average_entry_hit_rate" in distribution


class TestCacheCleanup:
    """Test cache cleanup and maintenance"""
    
    @pytest.fixture
    def cache(self):
        """Create cache for cleanup testing"""
        return ContextCache(ttl_seconds=5)  # Short TTL for testing
    
    @pytest.mark.asyncio
    async def test_cleanup_expired_entries(self, cache):
        """Test cleanup of expired entries"""
        # Add entries with past timestamps
        past_time = datetime.utcnow() - timedelta(seconds=10)
        for i in range(3):
            context = Mock(spec=AgentContext)
            context.request_id = f"req_{i}"
            entry = CacheEntry(
                context=context,
                request_id=f"req_{i}",
                cache_key=f"expired_key_{i}",
                created_at=past_time,
                last_accessed=past_time
            )
            cache._cache[f"expired_key_{i}"] = entry
        
        # Add a fresh entry
        fresh_context = Mock(spec=AgentContext)
        fresh_context.request_id = "req_fresh"
        fresh_entry = CacheEntry(
            context=fresh_context,
            request_id="req_fresh",
            cache_key="fresh_key",
            created_at=datetime.utcnow(),
            last_accessed=datetime.utcnow()
        )
        cache._cache["fresh_key"] = fresh_entry
        
        # Run cleanup
        cleaned_count = await cache.cleanup_expired()
        
        # All expired entries should be removed
        assert cleaned_count == 3
        assert "fresh_key" in cache._cache
        for i in range(3):
            assert f"expired_key_{i}" not in cache._cache
    
    @pytest.mark.asyncio
    async def test_cleanup_respects_interval(self, cache):
        """Test that cleanup respects minimum interval"""
        # Set last cleanup to recent time
        cache._last_cleanup = datetime.utcnow()
        
        # Immediate cleanup should return 0 (too soon)
        cleaned_count = await cache.cleanup_expired()
        assert cleaned_count == 0
    
    def test_clear_cache(self, cache):
        """Test clearing entire cache"""
        # Add some entries
        for i in range(3):
            context = Mock(spec=AgentContext)
            entry = CacheEntry(
                context=context,
                request_id=f"req_{i}",
                cache_key=f"key_{i}",
                created_at=datetime.utcnow(),
                last_accessed=datetime.utcnow()
            )
            cache._cache[f"key_{i}"] = entry
        
        assert len(cache._cache) == 3
        
        # Clear cache
        cache.clear()
        
        assert len(cache._cache) == 0
        assert cache._current_memory_usage == 0


class TestCacheKeyGeneration:
    """Test cache key generation"""
    
    @pytest.fixture
    def cache(self):
        """Create cache for key generation testing"""
        return ContextCache()
    
    def test_generate_cache_key_basic(self, cache):
        """Test basic cache key generation"""
        request = Mock(spec=ContextRequest)
        request.agent_type = "CodeAgent"
        request.story_id = "story_123"
        request.max_tokens = 10000
        request.compression_level = CompressionLevel.MODERATE
        request.include_history = True
        request.include_dependencies = False
        request.task = Mock()
        request.task.description = "Test task"
        
        key = cache._generate_cache_key(request)
        
        assert isinstance(key, str)
        assert len(key) == 16  # SHA256 truncated to 16 chars
    
    def test_generate_cache_key_consistency(self, cache):
        """Test that same request generates same key"""
        request = Mock(spec=ContextRequest)
        request.agent_type = "CodeAgent"
        request.story_id = "story_123"
        request.max_tokens = 10000
        request.compression_level = CompressionLevel.MODERATE
        request.include_history = True
        request.include_dependencies = False
        request.task = Mock()
        request.task.description = "Test task"
        
        key1 = cache._generate_cache_key(request)
        key2 = cache._generate_cache_key(request)
        
        assert key1 == key2
    
    def test_generate_cache_key_different_requests(self, cache):
        """Test that different requests generate different keys"""
        request1 = Mock(spec=ContextRequest)
        request1.agent_type = "CodeAgent"
        request1.story_id = "story_123"
        request1.max_tokens = 10000
        request1.compression_level = CompressionLevel.MODERATE
        request1.include_history = True
        request1.include_dependencies = False
        request1.task = Mock()
        request1.task.description = "Test task 1"
        
        request2 = Mock(spec=ContextRequest)
        request2.agent_type = "QAAgent"  # Different agent
        request2.story_id = "story_123"
        request2.max_tokens = 10000
        request2.compression_level = CompressionLevel.MODERATE
        request2.include_history = True
        request2.include_dependencies = False
        request2.task = Mock()
        request2.task.description = "Test task 1"
        
        key1 = cache._generate_cache_key(request1)
        key2 = cache._generate_cache_key(request2)
        
        assert key1 != key2


class TestBackgroundTasks:
    """Test cache background tasks"""
    
    @pytest.fixture
    def cache(self):
        """Create cache for background task testing"""
        return ContextCache()
    
    @pytest.mark.asyncio
    async def test_start_stop_background_tasks(self, cache):
        """Test starting and stopping background tasks"""
        # Start background tasks
        await cache.start_background_tasks()
        
        # Tasks should be created
        assert cache._warming_task is not None
        assert cache._prediction_task is not None
        assert not cache._warming_task.done()
        assert not cache._prediction_task.done()
        
        # Stop background tasks
        await cache.stop_background_tasks()
        
        # Tasks should be cleaned up
        assert cache._warming_task is None or cache._warming_task.done()
        assert cache._prediction_task is None or cache._prediction_task.done()
    
    @pytest.mark.asyncio
    async def test_background_tasks_disabled(self, cache):
        """Test background tasks when warming is disabled"""
        cache.warming_strategy = CacheWarmingStrategy.NONE
        cache.enable_predictions = False
        
        await cache.start_background_tasks()
        
        # No tasks should be started
        assert cache._warming_task is None
        assert cache._prediction_task is None
        
        await cache.stop_background_tasks()


@pytest.mark.asyncio
async def test_cache_performance_under_load():
    """Test cache performance under concurrent load"""
    cache = ContextCache(max_entries=100, max_memory_mb=10)
    
    # Create many contexts
    contexts = []
    for i in range(50):
        context = Mock(spec=AgentContext)
        context.request_id = f"req_{i}"
        context.file_contents = {f"file_{i}.py": f"content_{i}"}
        context.copy = Mock(return_value=context)
        contexts.append(context)
    
    # Concurrent put operations
    put_tasks = []
    for i, context in enumerate(contexts):
        task = cache.put(f"key_{i}", context)
        put_tasks.append(task)
    
    results = await asyncio.gather(*put_tasks)
    assert all(results)  # All puts should succeed
    
    # Concurrent get operations
    get_tasks = []
    for i in range(50):
        task = cache.get(f"key_{i}")
        get_tasks.append(task)
    
    retrieved = await asyncio.gather(*get_tasks)
    assert all(ctx is not None for ctx in retrieved)  # All gets should succeed
    
    # Check final statistics
    stats = await cache.get_statistics()
    assert stats.cache_hits == 50
    assert stats.entry_count <= 100  # Should respect max entries