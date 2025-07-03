"""
Context Cache - Predictive Caching System

Advanced caching system with LRU eviction, predictive preloading, and intelligent
cache warming for optimal context management performance.
"""

import asyncio
import logging
import time
import hashlib
from typing import Dict, List, Optional, Any, Set, Tuple
from datetime import datetime, timedelta
from collections import OrderedDict
from dataclasses import dataclass, field
from enum import Enum

try:
    from .context.models import (
        AgentContext, 
        ContextRequest, 
        TDDState,
        CompressionLevel
    )
    from .context.exceptions import ContextCacheError
    from .tdd_models import TDDTask
except ImportError:
    from context.models import (
        AgentContext, 
        ContextRequest, 
        TDDState,
        CompressionLevel
    )
    from context.exceptions import ContextCacheError
    from tdd_models import TDDTask

logger = logging.getLogger(__name__)


class CacheStrategy(Enum):
    """Cache strategy options"""
    LRU = "lru"  # Least Recently Used
    LFU = "lfu"  # Least Frequently Used
    TTL = "ttl"  # Time To Live
    PREDICTIVE = "predictive"  # Predictive caching


class CacheWarmingStrategy(Enum):
    """Cache warming strategy options"""
    NONE = "none"
    LAZY = "lazy"  # Warm on demand
    AGGRESSIVE = "aggressive"  # Proactive warming
    PATTERN_BASED = "pattern_based"  # Based on usage patterns


@dataclass
class CacheEntry:
    """Represents a cache entry with metadata"""
    
    context: AgentContext
    request_id: str
    cache_key: str
    created_at: datetime
    last_accessed: datetime
    access_count: int = 0
    hit_count: int = 0
    size_bytes: int = 0
    tags: Set[str] = field(default_factory=set)
    prediction_score: float = 0.0
    warm_priority: int = 0
    
    def update_access(self) -> None:
        """Update access statistics"""
        self.last_accessed = datetime.utcnow()
        self.access_count += 1
    
    def record_hit(self) -> None:
        """Record a cache hit"""
        self.hit_count += 1
        self.update_access()
    
    @property
    def age_seconds(self) -> float:
        """Get age of cache entry in seconds"""
        return (datetime.utcnow() - self.created_at).total_seconds()
    
    @property
    def last_access_seconds(self) -> float:
        """Get seconds since last access"""
        return (datetime.utcnow() - self.last_accessed).total_seconds()
    
    @property
    def hit_rate(self) -> float:
        """Calculate hit rate for this entry"""
        return self.hit_count / self.access_count if self.access_count > 0 else 0.0


@dataclass
class CacheStatistics:
    """Cache performance statistics"""
    
    total_requests: int = 0
    cache_hits: int = 0
    cache_misses: int = 0
    evictions: int = 0
    warming_hits: int = 0
    prediction_accuracy: float = 0.0
    average_prep_time: float = 0.0
    memory_usage_bytes: int = 0
    entry_count: int = 0
    
    @property
    def hit_rate(self) -> float:
        """Calculate overall hit rate"""
        total = self.cache_hits + self.cache_misses
        return self.cache_hits / total if total > 0 else 0.0
    
    @property
    def warming_effectiveness(self) -> float:
        """Calculate warming effectiveness"""
        return self.warming_hits / self.cache_hits if self.cache_hits > 0 else 0.0


@dataclass
class PredictionPattern:
    """Pattern for predictive caching"""
    
    pattern_id: str
    pattern_type: str  # "sequential", "frequent_pair", "agent_transition", "time_based"
    trigger_conditions: Dict[str, Any]
    predicted_requests: List[str]  # Cache keys to preload
    confidence: float
    success_rate: float = 0.0
    usage_count: int = 0
    last_used: datetime = field(default_factory=datetime.utcnow)


class ContextCache:
    """
    Advanced context caching system with predictive capabilities.
    
    Features:
    - Multiple cache strategies (LRU, LFU, TTL, Predictive)
    - Intelligent cache warming
    - Performance monitoring and analytics
    - Predictive preloading based on usage patterns
    - Memory management with size limits
    """
    
    def __init__(
        self,
        max_entries: int = 1000,
        max_memory_mb: int = 500,
        ttl_seconds: int = 1800,  # 30 minutes
        strategy: CacheStrategy = CacheStrategy.PREDICTIVE,
        warming_strategy: CacheWarmingStrategy = CacheWarmingStrategy.PATTERN_BASED,
        enable_predictions: bool = True,
        prediction_confidence_threshold: float = 0.7
    ):
        """
        Initialize the context cache.
        
        Args:
            max_entries: Maximum number of cache entries
            max_memory_mb: Maximum memory usage in MB
            ttl_seconds: Time-to-live for cache entries
            strategy: Cache strategy to use
            warming_strategy: Cache warming strategy
            enable_predictions: Whether to enable predictive caching
            prediction_confidence_threshold: Minimum confidence for predictions
        """
        self.max_entries = max_entries
        self.max_memory_bytes = max_memory_mb * 1024 * 1024
        self.ttl_seconds = ttl_seconds
        self.strategy = strategy
        self.warming_strategy = warming_strategy
        self.enable_predictions = enable_predictions
        self.prediction_confidence_threshold = prediction_confidence_threshold
        
        # Cache storage
        self._cache: OrderedDict[str, CacheEntry] = OrderedDict()
        self._size_tracker: Dict[str, int] = {}
        
        # Statistics and monitoring
        self.stats = CacheStatistics()
        self._access_history: List[Tuple[str, datetime]] = []
        self._preparation_times: List[float] = []
        
        # Predictive caching
        self._prediction_patterns: Dict[str, PredictionPattern] = {}
        self._warming_queue: asyncio.Queue = asyncio.Queue()
        self._warming_task: Optional[asyncio.Task] = None
        self._prediction_task: Optional[asyncio.Task] = None
        
        # Performance tracking
        self._current_memory_usage = 0
        self._last_cleanup = datetime.utcnow()
        self._cleanup_interval = 300  # 5 minutes
        
        logger.info(
            f"ContextCache initialized: max_entries={max_entries}, "
            f"max_memory={max_memory_mb}MB, strategy={strategy.value}"
        )
    
    async def start_background_tasks(self) -> None:
        """Start background tasks for cache management"""
        if self.warming_strategy != CacheWarmingStrategy.NONE:
            self._warming_task = asyncio.create_task(self._warming_worker())
        
        if self.enable_predictions:
            self._prediction_task = asyncio.create_task(self._prediction_worker())
        
        logger.info("Context cache background tasks started")
    
    async def stop_background_tasks(self) -> None:
        """Stop background tasks"""
        if self._warming_task and not self._warming_task.done():
            self._warming_task.cancel()
            try:
                await self._warming_task
            except asyncio.CancelledError:
                pass
        
        if self._prediction_task and not self._prediction_task.done():
            self._prediction_task.cancel()
            try:
                await self._prediction_task
            except asyncio.CancelledError:
                pass
        
        logger.info("Context cache background tasks stopped")
    
    async def get(self, cache_key: str) -> Optional[AgentContext]:
        """
        Get context from cache.
        
        Args:
            cache_key: Cache key to retrieve
            
        Returns:
            Cached context if found, None otherwise
        """
        start_time = time.time()
        self.stats.total_requests += 1
        
        try:
            if cache_key not in self._cache:
                self.stats.cache_misses += 1
                self._record_access(cache_key, hit=False)
                return None
            
            entry = self._cache[cache_key]
            
            # Check TTL
            if self._is_expired(entry):
                await self._evict_entry(cache_key)
                self.stats.cache_misses += 1
                self._record_access(cache_key, hit=False)
                return None
            
            # Update access patterns
            entry.record_hit()
            self._move_to_end(cache_key)
            self._record_access(cache_key, hit=True)
            
            self.stats.cache_hits += 1
            if entry.warm_priority > 0:
                self.stats.warming_hits += 1
            
            # Trigger predictive caching
            if self.enable_predictions:
                await self._trigger_predictions(cache_key, entry)
            
            logger.debug(f"Cache hit for key {cache_key[:8]}...")
            return entry.context.copy() if hasattr(entry.context, 'copy') else entry.context
            
        except Exception as e:
            logger.error(f"Error retrieving from cache: {str(e)}")
            self.stats.cache_misses += 1
            return None
        finally:
            prep_time = time.time() - start_time
            self._preparation_times.append(prep_time)
    
    async def put(
        self,
        cache_key: str,
        context: AgentContext,
        request: Optional[ContextRequest] = None,
        tags: Optional[Set[str]] = None
    ) -> bool:
        """
        Store context in cache.
        
        Args:
            cache_key: Cache key for storage
            context: Context to cache
            request: Original context request
            tags: Optional tags for categorization
            
        Returns:
            True if stored successfully, False otherwise
        """
        try:
            # Calculate context size
            context_size = self._estimate_context_size(context)
            
            # Check if we need to make space
            await self._ensure_space(context_size)
            
            # Create cache entry
            entry = CacheEntry(
                context=context,
                request_id=context.request_id,
                cache_key=cache_key,
                created_at=datetime.utcnow(),
                last_accessed=datetime.utcnow(),
                size_bytes=context_size,
                tags=tags or set()
            )
            
            # Add request-specific tags
            if request:
                entry.tags.update({
                    f"agent:{request.agent_type}",
                    f"story:{request.story_id}",
                    f"compression:{request.compression_level.value}"
                })
                
                if hasattr(request.task, 'current_state') and request.task.current_state:
                    entry.tags.add(f"phase:{request.task.current_state.value}")
            
            # Store entry
            self._cache[cache_key] = entry
            self._size_tracker[cache_key] = context_size
            self._current_memory_usage += context_size
            self.stats.entry_count += 1
            self.stats.memory_usage_bytes = self._current_memory_usage
            
            logger.debug(f"Cached context with key {cache_key[:8]}... (size: {context_size} bytes)")
            return True
            
        except Exception as e:
            logger.error(f"Error storing in cache: {str(e)}")
            return False
    
    async def invalidate(self, cache_key: str) -> bool:
        """Invalidate specific cache entry"""
        if cache_key in self._cache:
            await self._evict_entry(cache_key)
            logger.debug(f"Invalidated cache key {cache_key[:8]}...")
            return True
        return False
    
    async def invalidate_by_tags(self, tags: Set[str]) -> int:
        """Invalidate cache entries matching any of the provided tags"""
        keys_to_remove = []
        
        for cache_key, entry in self._cache.items():
            if entry.tags.intersection(tags):
                keys_to_remove.append(cache_key)
        
        for key in keys_to_remove:
            await self._evict_entry(key)
        
        logger.info(f"Invalidated {len(keys_to_remove)} entries matching tags: {tags}")
        return len(keys_to_remove)
    
    async def warm_cache(
        self,
        predictions: List[ContextRequest],
        priority: int = 1
    ) -> int:
        """
        Warm cache with predicted requests.
        
        Args:
            predictions: List of predicted context requests
            priority: Priority level for warming (higher = more important)
            
        Returns:
            Number of entries queued for warming
        """
        if self.warming_strategy == CacheWarmingStrategy.NONE:
            return 0
        
        queued = 0
        for request in predictions:
            cache_key = self._generate_cache_key(request)
            
            # Don't warm if already cached
            if cache_key not in self._cache:
                await self._warming_queue.put((request, priority))
                queued += 1
        
        logger.debug(f"Queued {queued} entries for cache warming")
        return queued
    
    async def analyze_patterns(self) -> Dict[str, Any]:
        """Analyze cache usage patterns"""
        if not self._access_history:
            return {"error": "No access history available"}
        
        # Calculate access frequency patterns
        access_counts = {}
        for cache_key, _ in self._access_history:
            access_counts[cache_key] = access_counts.get(cache_key, 0) + 1
        
        # Find sequential patterns
        sequential_patterns = self._find_sequential_patterns()
        
        # Calculate time-based patterns
        time_patterns = self._find_time_patterns()
        
        # Agent transition patterns
        agent_patterns = self._find_agent_patterns()
        
        return {
            "access_frequency": dict(sorted(access_counts.items(), key=lambda x: x[1], reverse=True)[:10]),
            "sequential_patterns": sequential_patterns,
            "time_patterns": time_patterns,
            "agent_patterns": agent_patterns,
            "total_patterns": len(self._prediction_patterns),
            "pattern_success_rate": self._calculate_pattern_success_rate()
        }
    
    async def cleanup_expired(self) -> int:
        """Clean up expired cache entries"""
        if datetime.utcnow() - self._last_cleanup < timedelta(seconds=self._cleanup_interval):
            return 0
        
        expired_keys = []
        current_time = datetime.utcnow()
        
        for cache_key, entry in self._cache.items():
            if self._is_expired(entry):
                expired_keys.append(cache_key)
        
        for key in expired_keys:
            await self._evict_entry(key)
        
        self._last_cleanup = current_time
        logger.info(f"Cleaned up {len(expired_keys)} expired cache entries")
        return len(expired_keys)
    
    async def get_statistics(self) -> CacheStatistics:
        """Get comprehensive cache statistics"""
        # Update current statistics
        self.stats.memory_usage_bytes = self._current_memory_usage
        self.stats.entry_count = len(self._cache)
        
        if self._preparation_times:
            self.stats.average_prep_time = sum(self._preparation_times) / len(self._preparation_times)
        
        if self._prediction_patterns:
            total_predictions = sum(p.usage_count for p in self._prediction_patterns.values())
            successful_predictions = sum(
                p.success_rate * p.usage_count for p in self._prediction_patterns.values()
            )
            self.stats.prediction_accuracy = (
                successful_predictions / total_predictions if total_predictions > 0 else 0.0
            )
        
        return self.stats
    
    async def get_detailed_metrics(self) -> Dict[str, Any]:
        """Get detailed cache metrics"""
        stats = await self.get_statistics()
        
        # Entry distribution by age
        age_distribution = {}
        for entry in self._cache.values():
            age_bucket = int(entry.age_seconds // 300)  # 5-minute buckets
            age_distribution[age_bucket] = age_distribution.get(age_bucket, 0) + 1
        
        # Tag distribution
        tag_distribution = {}
        for entry in self._cache.values():
            for tag in entry.tags:
                tag_distribution[tag] = tag_distribution.get(tag, 0) + 1
        
        # Hit rate by entry
        hit_rates = [entry.hit_rate for entry in self._cache.values()]
        avg_hit_rate = sum(hit_rates) / len(hit_rates) if hit_rates else 0.0
        
        return {
            "basic_stats": {
                "hit_rate": stats.hit_rate,
                "entry_count": stats.entry_count,
                "memory_usage_mb": stats.memory_usage_bytes / (1024 * 1024),
                "average_prep_time": stats.average_prep_time,
                "prediction_accuracy": stats.prediction_accuracy
            },
            "distribution": {
                "age_buckets": age_distribution,
                "tag_distribution": dict(sorted(tag_distribution.items(), key=lambda x: x[1], reverse=True)[:10]),
                "average_entry_hit_rate": avg_hit_rate
            },
            "patterns": {
                "active_patterns": len(self._prediction_patterns),
                "warming_queue_size": self._warming_queue.qsize(),
                "warming_effectiveness": stats.warming_effectiveness
            }
        }
    
    def clear(self) -> None:
        """Clear all cache entries"""
        self._cache.clear()
        self._size_tracker.clear()
        self._current_memory_usage = 0
        self.stats.entry_count = 0
        self.stats.memory_usage_bytes = 0
        logger.info("Cache cleared")
    
    # Private methods
    
    def _generate_cache_key(self, request: ContextRequest) -> str:
        """Generate cache key from context request"""
        key_data = f"{request.agent_type}:{request.story_id}:{request.max_tokens}"
        
        if hasattr(request.task, 'description'):
            key_data += f":{request.task.description}"
        elif isinstance(request.task, dict) and 'description' in request.task:
            key_data += f":{request.task['description']}"
        
        key_data += f":{request.compression_level.value}:{request.include_history}:{request.include_dependencies}"
        
        return hashlib.sha256(key_data.encode()).hexdigest()[:16]
    
    def _estimate_context_size(self, context: AgentContext) -> int:
        """Estimate memory size of context in bytes"""
        size = 0
        
        # Estimate content sizes
        if context.core_context:
            size += len(context.core_context.encode('utf-8'))
        if context.historical_context:
            size += len(context.historical_context.encode('utf-8'))
        if context.dependencies:
            size += len(context.dependencies.encode('utf-8'))
        if context.agent_memory:
            size += len(context.agent_memory.encode('utf-8'))
        if context.metadata:
            size += len(context.metadata.encode('utf-8'))
        
        # Add overhead for object structure
        size += 1024  # Base overhead
        
        return size
    
    def _is_expired(self, entry: CacheEntry) -> bool:
        """Check if cache entry is expired"""
        return entry.age_seconds > self.ttl_seconds
    
    def _move_to_end(self, cache_key: str) -> None:
        """Move cache entry to end (most recently used)"""
        if self.strategy == CacheStrategy.LRU:
            self._cache.move_to_end(cache_key)
    
    async def _ensure_space(self, required_size: int) -> None:
        """Ensure sufficient space for new entry"""
        # Check memory limit
        while (self._current_memory_usage + required_size > self.max_memory_bytes and 
               len(self._cache) > 0):
            await self._evict_least_valuable()
        
        # Check entry count limit
        while len(self._cache) >= self.max_entries:
            await self._evict_least_valuable()
    
    async def _evict_least_valuable(self) -> None:
        """Evict least valuable cache entry based on strategy"""
        if not self._cache:
            return
        
        if self.strategy == CacheStrategy.LRU:
            # Evict least recently used
            cache_key = next(iter(self._cache))
        elif self.strategy == CacheStrategy.LFU:
            # Evict least frequently used
            cache_key = min(self._cache.keys(), key=lambda k: self._cache[k].access_count)
        elif self.strategy == CacheStrategy.TTL:
            # Evict oldest entry
            cache_key = min(self._cache.keys(), key=lambda k: self._cache[k].created_at)
        else:  # PREDICTIVE
            # Evict based on prediction score and access patterns
            cache_key = self._select_eviction_candidate()
        
        await self._evict_entry(cache_key)
    
    def _select_eviction_candidate(self) -> str:
        """Select best candidate for eviction using multiple factors"""
        scores = {}
        
        for cache_key, entry in self._cache.items():
            # Calculate eviction score (higher = more likely to evict)
            score = 0.0
            
            # Age factor (older = higher score)
            score += entry.age_seconds / 3600.0  # Hours
            
            # Access frequency factor (less frequent = higher score)
            score += 1.0 / (entry.access_count + 1)
            
            # Last access factor (longer ago = higher score)
            score += entry.last_access_seconds / 3600.0  # Hours
            
            # Hit rate factor (lower hit rate = higher score)
            score += (1.0 - entry.hit_rate) * 2.0
            
            # Prediction score factor (lower prediction = higher score)
            score += (1.0 - entry.prediction_score) * 1.5
            
            scores[cache_key] = score
        
        return max(scores.keys(), key=lambda k: scores[k])
    
    async def _evict_entry(self, cache_key: str) -> None:
        """Evict specific cache entry"""
        if cache_key in self._cache:
            entry = self._cache[cache_key]
            self._current_memory_usage -= entry.size_bytes
            del self._cache[cache_key]
            del self._size_tracker[cache_key]
            self.stats.evictions += 1
            self.stats.entry_count -= 1
    
    def _record_access(self, cache_key: str, hit: bool) -> None:
        """Record cache access for pattern analysis"""
        self._access_history.append((cache_key, datetime.utcnow()))
        
        # Limit history size
        if len(self._access_history) > 10000:
            self._access_history = self._access_history[-5000:]
    
    async def _trigger_predictions(self, cache_key: str, entry: CacheEntry) -> None:
        """Trigger predictive caching based on access"""
        # Find applicable patterns
        applicable_patterns = []
        
        for pattern in self._prediction_patterns.values():
            if self._pattern_matches(pattern, cache_key, entry):
                applicable_patterns.append(pattern)
        
        # Execute predictions with sufficient confidence
        for pattern in applicable_patterns:
            if pattern.confidence >= self.prediction_confidence_threshold:
                await self._execute_pattern_predictions(pattern)
    
    def _pattern_matches(self, pattern: PredictionPattern, cache_key: str, entry: CacheEntry) -> bool:
        """Check if pattern matches current access"""
        conditions = pattern.trigger_conditions
        
        if pattern.pattern_type == "agent_transition":
            return any(f"agent:{agent}" in entry.tags for agent in conditions.get("agents", []))
        elif pattern.pattern_type == "sequential":
            return cache_key in conditions.get("sequence", [])
        elif pattern.pattern_type == "frequent_pair":
            return cache_key == conditions.get("trigger_key")
        
        return False
    
    async def _execute_pattern_predictions(self, pattern: PredictionPattern) -> None:
        """Execute predictions for a pattern"""
        pattern.usage_count += 1
        pattern.last_used = datetime.utcnow()
        
        # Queue predictions for warming
        for cache_key in pattern.predicted_requests:
            if cache_key not in self._cache:
                # Create mock request for warming (simplified)
                mock_request = self._create_mock_request_from_key(cache_key)
                if mock_request:
                    await self._warming_queue.put((mock_request, pattern.confidence))
    
    def _create_mock_request_from_key(self, cache_key: str) -> Optional[ContextRequest]:
        """Create a mock request from cache key (simplified)"""
        # This is a simplified implementation
        # In practice, you'd need to store more metadata to reconstruct requests
        return None
    
    async def _warming_worker(self) -> None:
        """Background worker for cache warming"""
        while True:
            try:
                request, priority = await asyncio.wait_for(
                    self._warming_queue.get(), 
                    timeout=1.0
                )
                
                # Execute warming (this would call the context manager)
                # Placeholder for actual warming implementation
                logger.debug(f"Warming cache for {request.agent_type}:{request.story_id}")
                
            except asyncio.TimeoutError:
                continue
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in cache warming worker: {str(e)}")
    
    async def _prediction_worker(self) -> None:
        """Background worker for pattern learning"""
        while True:
            try:
                await asyncio.sleep(300)  # Run every 5 minutes
                await self._update_prediction_patterns()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in prediction worker: {str(e)}")
    
    async def _update_prediction_patterns(self) -> None:
        """Update prediction patterns based on access history"""
        if len(self._access_history) < 100:  # Need sufficient history
            return
        
        # Find sequential patterns
        sequential_patterns = self._find_sequential_patterns()
        for pattern_data in sequential_patterns:
            pattern_id = f"seq_{pattern_data['sequence']}"
            
            if pattern_id not in self._prediction_patterns:
                self._prediction_patterns[pattern_id] = PredictionPattern(
                    pattern_id=pattern_id,
                    pattern_type="sequential",
                    trigger_conditions={"sequence": pattern_data["sequence"]},
                    predicted_requests=pattern_data["predictions"],
                    confidence=pattern_data["confidence"]
                )
        
        logger.debug(f"Updated {len(self._prediction_patterns)} prediction patterns")
    
    def _find_sequential_patterns(self) -> List[Dict[str, Any]]:
        """Find sequential access patterns"""
        patterns = []
        
        # Analyze last 1000 accesses for sequences
        recent_accesses = self._access_history[-1000:]
        
        # Look for pairs and triplets
        for i in range(len(recent_accesses) - 2):
            seq = [recent_accesses[i][0], recent_accesses[i+1][0], recent_accesses[i+2][0]]
            
            # Count how often this sequence occurs
            count = 0
            for j in range(len(recent_accesses) - 2):
                check_seq = [recent_accesses[j][0], recent_accesses[j+1][0], recent_accesses[j+2][0]]
                if check_seq == seq:
                    count += 1
            
            if count >= 3:  # Minimum threshold
                confidence = min(count / 10.0, 1.0)  # Scale confidence
                patterns.append({
                    "sequence": seq[:2],
                    "predictions": [seq[2]],
                    "confidence": confidence,
                    "count": count
                })
        
        return patterns
    
    def _find_time_patterns(self) -> Dict[str, Any]:
        """Find time-based access patterns"""
        # Placeholder for time-based pattern analysis
        return {"hourly_patterns": {}, "daily_patterns": {}}
    
    def _find_agent_patterns(self) -> Dict[str, Any]:
        """Find agent transition patterns"""
        # Placeholder for agent transition pattern analysis
        return {"transition_patterns": {}}
    
    def _calculate_pattern_success_rate(self) -> float:
        """Calculate overall pattern prediction success rate"""
        if not self._prediction_patterns:
            return 0.0
        
        total_predictions = sum(p.usage_count for p in self._prediction_patterns.values())
        if total_predictions == 0:
            return 0.0
        
        successful_predictions = sum(
            p.success_rate * p.usage_count for p in self._prediction_patterns.values()
        )
        
        return successful_predictions / total_predictions