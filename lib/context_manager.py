"""
Context Manager - Core Infrastructure Implementation

Central coordination engine for context management operations. Orchestrates context
pipeline (filter → compress → deliver) with token budget management and agent handoffs.
"""

import asyncio
import logging
import time
import hashlib
from typing import Dict, List, Optional, Any, Union
from datetime import datetime, timedelta
from pathlib import Path

try:
    from .context.models import (
        ContextRequest, 
        AgentContext, 
        TokenBudget, 
        TokenUsage,
        CompressionLevel,
        ContextType,
        ContextSnapshot,
        Decision,
        PhaseHandoff,
        FileType,
        RelevanceScore
    )
    from .context.exceptions import (
        ContextError, 
        TokenBudgetExceededError, 
        ContextNotFoundError,
        ContextTimeoutError
    )
    
    # Import concrete implementations
    from .token_calculator import TokenCalculator
    from .agent_memory import FileBasedAgentMemory
    
    # Import intelligence layer components
    from .context_filter import ContextFilter
    from .context_compressor import ContextCompressor
    from .context_index import ContextIndex
    
    # Import advanced features
    from .context_cache import ContextCache, CacheStrategy, CacheWarmingStrategy
    from .context_monitoring import ContextMonitor
    from .context_background import ContextBackgroundProcessor, TaskPriority
except ImportError:
    from context.models import (
        ContextRequest, 
        AgentContext, 
        TokenBudget, 
        TokenUsage,
        CompressionLevel,
        ContextType,
        ContextSnapshot,
        Decision,
        PhaseHandoff,
        FileType,
        RelevanceScore
    )
    from context.exceptions import (
        ContextError, 
        TokenBudgetExceededError, 
        ContextNotFoundError,
        ContextTimeoutError
    )
    
    # Import concrete implementations
    from token_calculator import TokenCalculator
    from agent_memory import FileBasedAgentMemory
    
    # Import intelligence layer components
    from context_filter import ContextFilter
    from context_compressor import ContextCompressor
    from context_index import ContextIndex
    
    # Import advanced features
    from context_cache import ContextCache, CacheStrategy, CacheWarmingStrategy
    from context_monitoring import ContextMonitor
    from context_background import ContextBackgroundProcessor, TaskPriority

# Import TDD models
try:
    from .tdd_models import TDDState, TDDTask, TDDCycle
except ImportError:
    from tdd_models import TDDState, TDDTask, TDDCycle

logger = logging.getLogger(__name__)


class ContextManager:
    """
    Core context management infrastructure.
    
    Provides central coordination for context preparation, token budget management,
    agent memory integration, and context pipeline orchestration. Designed as the
    foundation for intelligent context filtering and compression layers.
    """
    
    def __init__(
        self,
        project_path: Optional[str] = None,
        max_tokens: int = 200000,
        cache_ttl_seconds: int = 300,
        max_preparation_time: int = 30,
        enable_intelligence: bool = True,
        enable_advanced_caching: bool = True,
        enable_monitoring: bool = True,
        enable_cross_story: bool = True,
        enable_background_processing: bool = True,
        cache_strategy: CacheStrategy = CacheStrategy.PREDICTIVE,
        warming_strategy: CacheWarmingStrategy = CacheWarmingStrategy.PATTERN_BASED,
        background_workers: int = 4
    ):
        """
        Initialize ContextManager with core infrastructure and advanced features.
        
        Args:
            project_path: Path to project root for context operations
            max_tokens: Maximum token limit for context (Claude Code default)
            cache_ttl_seconds: Time-to-live for context cache in seconds
            max_preparation_time: Maximum time for context preparation in seconds
            enable_intelligence: Whether to enable intelligent filtering and compression
            enable_advanced_caching: Whether to enable predictive caching system
            enable_monitoring: Whether to enable performance monitoring
            enable_cross_story: Whether to enable cross-story context management
            enable_background_processing: Whether to enable background processing
            cache_strategy: Caching strategy to use
            warming_strategy: Cache warming strategy
            background_workers: Number of background worker threads
        """
        self.project_path = Path(project_path) if project_path else Path.cwd()
        self.max_tokens = max_tokens
        self.cache_ttl_seconds = cache_ttl_seconds
        self.max_preparation_time = max_preparation_time
        self.enable_intelligence = enable_intelligence
        self.enable_advanced_caching = enable_advanced_caching
        self.enable_monitoring = enable_monitoring
        self.enable_cross_story = enable_cross_story
        self.enable_background_processing = enable_background_processing
        
        # Initialize core components
        self.token_calculator = TokenCalculator(max_tokens=max_tokens)
        self.agent_memory = FileBasedAgentMemory(
            base_path=str(self.project_path / ".orch-state")
        )
        
        # Initialize advanced caching system
        if self.enable_advanced_caching:
            self.context_cache = ContextCache(
                max_entries=1000,
                max_memory_mb=500,
                ttl_seconds=cache_ttl_seconds,
                strategy=cache_strategy,
                warming_strategy=warming_strategy,
                enable_predictions=True
            )
        else:
            self.context_cache = None
        
        # Initialize monitoring system
        if self.enable_monitoring:
            self.monitor = ContextMonitor(
                collection_interval=5,
                retention_hours=24,
                enable_system_metrics=True,
                enable_alerts=True
            )
        else:
            self.monitor = None
        
        # Initialize background processing system
        if self.enable_background_processing:
            self.background_processor = ContextBackgroundProcessor(
                project_path=str(self.project_path),
                max_workers=background_workers,
                max_queue_size=1000,
                enable_auto_tasks=True
            )
            # Set component references
            self.background_processor.set_component_references(
                context_manager=self,
                learning_system=None,  # Will be set when learning is enabled
                cache_system=self.context_cache,
                monitoring_system=self.monitor
            )
        else:
            self.background_processor = None
        
        # Cross-story context management
        self._active_stories: Dict[str, Dict[str, Any]] = {}
        self._story_conflicts: Dict[str, List[str]] = {}
        self._cross_story_cache: Dict[str, AgentContext] = {}
        
        # Initialize intelligence layer components
        if self.enable_intelligence:
            self.context_filter = ContextFilter(
                project_path=str(self.project_path),
                agent_memory=self.agent_memory,
                token_calculator=self.token_calculator
            )
            self.context_compressor = ContextCompressor(
                token_calculator=self.token_calculator
            )
            self.context_index = ContextIndex(
                project_path=str(self.project_path),
                token_calculator=self.token_calculator
            )
        else:
            self.context_filter = None
            self.context_compressor = None
            self.context_index = None
        
        # Legacy in-memory context cache (for fallback)
        self._legacy_cache: Dict[str, tuple[AgentContext, datetime]] = {}
        
        # Performance metrics
        self._preparation_times: List[float] = []
        self._cache_hits = 0
        self._cache_misses = 0
        self._total_requests = 0
        
        # Active context tracking
        self._active_contexts: Dict[str, AgentContext] = {}
        
        logger.info(
            f"ContextManager initialized for project: {self.project_path} "
            f"(intelligence: {enable_intelligence}, caching: {enable_advanced_caching}, "
            f"monitoring: {enable_monitoring}, cross-story: {enable_cross_story}, "
            f"background: {enable_background_processing})"
        )
    
    async def start(self) -> None:
        """Start background services for advanced features"""
        if self.enable_advanced_caching and self.context_cache:
            await self.context_cache.start_background_tasks()
        
        if self.enable_monitoring and self.monitor:
            await self.monitor.start_monitoring()
        
        if self.enable_background_processing and self.background_processor:
            await self.background_processor.start()
            
            # Queue initial background tasks
            await self._queue_initial_background_tasks()
        
        logger.info("ContextManager advanced services started")
    
    async def stop(self) -> None:
        """Stop background services"""
        if self.enable_background_processing and self.background_processor:
            await self.background_processor.stop()
        
        if self.enable_advanced_caching and self.context_cache:
            await self.context_cache.stop_background_tasks()
        
        if self.enable_monitoring and self.monitor:
            await self.monitor.stop_monitoring()
        
        logger.info("ContextManager services stopped")
    
    async def prepare_context(
        self,
        agent_type: str,
        task: Union[TDDTask, Dict[str, Any]],
        max_tokens: Optional[int] = None,
        story_id: Optional[str] = None,
        **kwargs
    ) -> AgentContext:
        """
        Prepare context for agent task execution with advanced features.
        
        Args:
            agent_type: Type of agent requesting context
            task: Task to be executed (TDDTask or dict)
            max_tokens: Maximum tokens allowed (defaults to instance max)
            story_id: Story ID for context isolation
            **kwargs: Additional context preparation options
            
        Returns:
            AgentContext with prepared content
            
        Raises:
            ContextError: If context preparation fails
            TokenBudgetExceededError: If token budget is exceeded
            ContextTimeoutError: If preparation times out
        """
        start_time = time.time()
        operation_id = None
        
        if self.enable_monitoring and self.monitor:
            operation_id = self.monitor.record_operation_start("context_preparation")
        
        self._total_requests += 1
        
        # Use default max_tokens if not specified
        max_tokens = max_tokens or self.max_tokens
        
        try:
            # Create context request
            request = ContextRequest(
                agent_type=agent_type,
                story_id=story_id or self._extract_story_id(task),
                task=task,
                max_tokens=max_tokens,
                **kwargs
            )
            
            logger.info(f"Preparing context for {agent_type}, request_id: {request.id}")
            
            # Check cross-story conflicts if enabled
            if self.enable_cross_story:
                await self._handle_cross_story_preparation(request)
            
            # Check advanced cache first
            cached_context = None
            if self.enable_advanced_caching and self.context_cache:
                cache_key = self._generate_cache_key(request)
                cached_context = await self.context_cache.get(cache_key)
            else:
                # Fallback to legacy cache
                cached_context = await self._get_cached_context_legacy(request)
            
            if cached_context:
                self._cache_hits += 1
                cached_context.cache_hit = True
                logger.info(f"Context cache hit for request {request.id}")
                
                # Record monitoring metrics
                if self.enable_monitoring and self.monitor:
                    duration = time.time() - start_time
                    self.monitor.record_context_preparation(request, cached_context, duration, True)
                    if operation_id:
                        self.monitor.record_operation_end(operation_id, True)
                
                return cached_context
            
            self._cache_misses += 1
            
            # Prepare context with timeout
            context = await asyncio.wait_for(
                self._prepare_context_internal(request),
                timeout=self.max_preparation_time
            )
            
            # Cache the prepared context
            if self.enable_advanced_caching and self.context_cache:
                cache_key = self._generate_cache_key(request)
                await self.context_cache.put(cache_key, context, request)
            else:
                # Fallback to legacy cache
                await self._cache_context_legacy(request, context)
            
            # Track as active context
            self._active_contexts[context.request_id] = context
            
            # Update cross-story tracking
            if self.enable_cross_story:
                await self._update_cross_story_tracking(request, context)
            
            preparation_time = time.time() - start_time
            context.preparation_time = preparation_time
            self._preparation_times.append(preparation_time)
            
            # Record monitoring metrics
            if self.enable_monitoring and self.monitor:
                self.monitor.record_context_preparation(request, context, preparation_time, True)
                if operation_id:
                    self.monitor.record_operation_end(operation_id, True)
            
            logger.info(
                f"Context prepared for {agent_type} in {preparation_time:.2f}s, "
                f"tokens: {context.get_total_token_estimate()}/{max_tokens}"
            )
            
            return context
            
        except asyncio.TimeoutError:
            error_msg = f"Context preparation timed out after {self.max_preparation_time}s"
            logger.error(error_msg)
            
            # Record monitoring metrics
            if self.enable_monitoring and self.monitor and operation_id:
                self.monitor.record_operation_end(operation_id, False)
            
            raise ContextTimeoutError(
                error_msg, 
                operation="prepare_context",
                timeout_seconds=self.max_preparation_time
            )
        except Exception as e:
            logger.error(f"Context preparation failed: {str(e)}")
            
            # Record monitoring metrics
            if self.enable_monitoring and self.monitor and operation_id:
                self.monitor.record_operation_end(operation_id, False)
            
            raise ContextError(f"Context preparation failed: {str(e)}")
    
    async def record_agent_decision(
        self,
        agent_type: str,
        story_id: str,
        description: str,
        rationale: str = "",
        outcome: str = "",
        confidence: float = 0.0,
        artifacts: Optional[Dict[str, str]] = None
    ) -> str:
        """
        Record an agent decision for learning and handoffs.
        
        Args:
            agent_type: Type of agent making decision
            story_id: Story ID for context
            description: Description of the decision
            rationale: Reasoning behind the decision
            outcome: Result of the decision
            confidence: Confidence level (0.0 to 1.0)
            artifacts: Associated artifacts
            
        Returns:
            Decision ID for reference
        """
        decision = Decision(
            agent_type=agent_type,
            description=description,
            rationale=rationale,
            outcome=outcome,
            confidence=confidence,
            artifacts=artifacts or {}
        )
        
        await self.agent_memory.add_decision(agent_type, story_id, decision)
        
        logger.info(f"Recorded decision {decision.id} for {agent_type}:{story_id}")
        return decision.id
    
    async def record_phase_handoff(
        self,
        from_agent: str,
        to_agent: str,
        from_phase: TDDState,
        to_phase: TDDState,
        story_id: str,
        artifacts: Optional[Dict[str, str]] = None,
        context_summary: str = "",
        handoff_notes: str = ""
    ) -> str:
        """
        Record a TDD phase handoff between agents.
        
        Args:
            from_agent: Agent handing off
            to_agent: Agent receiving handoff
            from_phase: Source TDD phase
            to_phase: Target TDD phase
            story_id: Story ID for context
            artifacts: Handoff artifacts
            context_summary: Summary of context
            handoff_notes: Additional handoff notes
            
        Returns:
            Handoff ID for reference
        """
        handoff = PhaseHandoff(
            from_phase=from_phase,
            to_phase=to_phase,
            from_agent=from_agent,
            to_agent=to_agent,
            artifacts=artifacts or {},
            context_summary=context_summary,
            handoff_notes=handoff_notes
        )
        
        # Record handoff in both agents' memories
        await self.agent_memory.add_phase_handoff(from_agent, story_id, handoff)
        await self.agent_memory.add_phase_handoff(to_agent, story_id, handoff)
        
        logger.info(
            f"Recorded phase handoff {handoff.id}: "
            f"{from_agent}({from_phase.value}) -> {to_agent}({to_phase.value})"
        )
        return handoff.id
    
    async def create_context_snapshot(
        self,
        agent_type: str,
        story_id: str,
        context: AgentContext,
        summary: str = ""
    ) -> str:
        """
        Create a snapshot of current context for historical reference.
        
        Args:
            agent_type: Type of agent
            story_id: Story ID
            context: Current context to snapshot
            summary: Optional summary description
            
        Returns:
            Snapshot ID for reference
        """
        snapshot = ContextSnapshot(
            agent_type=agent_type,
            story_id=story_id,
            tdd_phase=context.tdd_phase,
            context_summary=summary or f"Context snapshot for {agent_type}",
            file_list=list(context.file_contents.keys()),
            token_usage=context.token_usage,
            metadata={
                "preparation_time": context.preparation_time,
                "compression_applied": context.compression_applied,
                "compression_level": context.compression_level.value,
                "cache_hit": context.cache_hit
            }
        )
        
        await self.agent_memory.add_context_snapshot(agent_type, story_id, snapshot)
        
        logger.debug(f"Created context snapshot {snapshot.id} for {agent_type}:{story_id}")
        return snapshot.id
    
    async def get_agent_context_history(
        self,
        agent_type: str,
        story_id: str,
        tdd_phase: Optional[TDDState] = None,
        limit: int = 10
    ) -> List[ContextSnapshot]:
        """
        Get historical context snapshots for an agent.
        
        Args:
            agent_type: Type of agent
            story_id: Story ID
            tdd_phase: Optional TDD phase filter
            limit: Maximum number of snapshots to return
            
        Returns:
            List of context snapshots
        """
        return await self.agent_memory.get_context_history(
            agent_type, story_id, tdd_phase, limit
        )
    
    async def get_recent_decisions(
        self,
        agent_type: str,
        story_id: str,
        limit: int = 10
    ) -> List[Decision]:
        """
        Get recent decisions for an agent.
        
        Args:
            agent_type: Type of agent
            story_id: Story ID
            limit: Maximum number of decisions to return
            
        Returns:
            List of recent decisions
        """
        return await self.agent_memory.get_recent_decisions(agent_type, story_id, limit)
    
    async def get_phase_handoffs(
        self,
        agent_type: str,
        story_id: str,
        from_phase: Optional[TDDState] = None,
        to_phase: Optional[TDDState] = None
    ) -> List[PhaseHandoff]:
        """
        Get phase handoffs for an agent.
        
        Args:
            agent_type: Type of agent
            story_id: Story ID
            from_phase: Optional source phase filter
            to_phase: Optional target phase filter
            
        Returns:
            List of phase handoffs
        """
        return await self.agent_memory.get_phase_handoffs(
            agent_type, story_id, from_phase, to_phase
        )
    
    async def analyze_agent_learning(
        self,
        agent_type: str,
        story_id: str
    ) -> Dict[str, Any]:
        """
        Analyze learning patterns for an agent.
        
        Args:
            agent_type: Type of agent
            story_id: Story ID
            
        Returns:
            Analysis of agent learning patterns
        """
        return await self.agent_memory.analyze_agent_patterns(agent_type, story_id)
    
    async def optimize_token_budget(
        self,
        context: AgentContext,
        actual_usage: TokenUsage,
        quality_score: float
    ) -> TokenBudget:
        """
        Optimize token budget based on usage patterns.
        
        Args:
            context: Current context
            actual_usage: Actual token usage
            quality_score: Quality assessment of context
            
        Returns:
            Optimized token budget
        """
        if not context.token_budget:
            raise ValueError("Context must have token budget for optimization")
        
        return await self.token_calculator.optimize_allocation(
            context.token_budget,
            actual_usage,
            quality_score
        )
    
    async def invalidate_context(self, context_id: str) -> None:
        """
        Invalidate specific context from cache.
        
        Args:
            context_id: ID of context to invalidate
        """
        keys_to_remove = []
        for cache_key, (cached_context, _) in self._legacy_cache.items():
            if cached_context.request_id == context_id:
                keys_to_remove.append(cache_key)
        
        for key in keys_to_remove:
            del self._legacy_cache[key]
        
        # Remove from active contexts
        if context_id in self._active_contexts:
            del self._active_contexts[context_id]
        
        logger.info(f"Context {context_id} invalidated")
    
    async def cleanup_cache(self) -> int:
        """Clean up expired cache entries"""
        current_time = datetime.utcnow()
        expired_keys = []
        
        for cache_key, (context, timestamp) in self._legacy_cache.items():
            if current_time - timestamp > timedelta(seconds=self.cache_ttl_seconds):
                expired_keys.append(cache_key)
        
        for key in expired_keys:
            del self._legacy_cache[key]
        
        logger.info(f"Cleaned up {len(expired_keys)} expired cache entries")
        return len(expired_keys)
    
    async def build_context_index(self, force_rebuild: bool = False) -> None:
        """
        Build or update the context index for intelligent filtering.
        
        Args:
            force_rebuild: Whether to force a complete rebuild
        """
        if not self.enable_intelligence or not self.context_index:
            logger.warning("Context index not available - intelligence layer disabled")
            return
        
        await self.context_index.build_index(force_rebuild=force_rebuild)
    
    async def search_codebase(
        self,
        query: str,
        search_type: str = "all",
        max_results: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Search the codebase using the context index.
        
        Args:
            query: Search query
            search_type: Type of search ('all', 'functions', 'classes', 'imports', 'content')
            max_results: Maximum number of results
            
        Returns:
            List of search results
        """
        if not self.enable_intelligence or not self.context_index:
            logger.warning("Context index not available - intelligence layer disabled")
            return []
        
        search_results = await self.context_index.search_files(
            query=query,
            search_type=search_type,
            max_results=max_results,
            include_content=True
        )
        
        # Convert to dictionary format
        return [
            {
                "file_path": result.file_path,
                "relevance_score": result.relevance_score,
                "match_type": result.match_type,
                "matches": result.matches,
                "context": result.context
            }
            for result in search_results
        ]
    
    async def get_file_dependencies(
        self,
        file_path: str,
        depth: int = 1,
        include_reverse: bool = False
    ) -> Dict[str, Any]:
        """
        Get dependency information for a file.
        
        Args:
            file_path: Path to the file
            depth: Depth of dependency traversal
            include_reverse: Whether to include reverse dependencies
            
        Returns:
            Dictionary with dependency information
        """
        if not self.enable_intelligence or not self.context_index:
            logger.warning("Context index not available - intelligence layer disabled")
            return {"error": "Context index not available"}
        
        return await self.context_index.get_file_dependencies(
            file_path=file_path,
            depth=depth,
            include_reverse=include_reverse
        )
    
    async def get_file_relevance_explanation(
        self,
        file_path: str,
        request: ContextRequest
    ) -> Dict[str, Any]:
        """
        Get detailed explanation of why a file is relevant to a context request.
        
        Args:
            file_path: Path to the file
            request: Context request to analyze against
            
        Returns:
            Dictionary with detailed relevance breakdown
        """
        if not self.enable_intelligence or not self.context_filter:
            logger.warning("Context filter not available - intelligence layer disabled")
            return {"error": "Context filter not available"}
        
        return await self.context_filter.get_file_relevance_explanation(
            file_path=file_path,
            request=request
        )
    
    async def estimate_compression_potential(
        self,
        content: str,
        file_type: FileType,
        compression_level: CompressionLevel
    ) -> Dict[str, Any]:
        """
        Estimate compression potential for content.
        
        Args:
            content: Content to analyze
            file_type: Type of file
            compression_level: Target compression level
            
        Returns:
            Dictionary with compression analysis
        """
        if not self.enable_intelligence or not self.context_compressor:
            logger.warning("Context compressor not available - intelligence layer disabled")
            return {"error": "Context compressor not available"}
        
        return await self.context_compressor.estimate_compression_potential(
            content=content,
            file_type=file_type,
            compression_level=compression_level
        )
    
    async def get_project_statistics(self) -> Dict[str, Any]:
        """Get comprehensive project statistics from the context index"""
        if not self.enable_intelligence or not self.context_index:
            logger.warning("Context index not available - intelligence layer disabled")
            return {"error": "Context index not available"}
        
        return await self.context_index.get_project_statistics()
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get comprehensive performance metrics"""
        avg_preparation_time = (
            sum(self._preparation_times) / len(self._preparation_times)
            if self._preparation_times else 0.0
        )
        
        cache_hit_rate = (
            self._cache_hits / (self._cache_hits + self._cache_misses)
            if (self._cache_hits + self._cache_misses) > 0 else 0.0
        )
        
        # Get component metrics
        token_metrics = self.token_calculator.get_performance_metrics()
        memory_metrics = self.agent_memory.get_performance_metrics()
        
        result = {
            "context_manager": {
                "total_requests": self._total_requests,
                "cache_hits": self._cache_hits,
                "cache_misses": self._cache_misses,
                "cache_hit_rate": cache_hit_rate,
                "average_preparation_time": avg_preparation_time,
                "max_preparation_time": max(self._preparation_times) if self._preparation_times else 0.0,
                "min_preparation_time": min(self._preparation_times) if self._preparation_times else 0.0,
                "cached_contexts": len(self._legacy_cache),
                "active_contexts": len(self._active_contexts),
                "intelligence_enabled": self.enable_intelligence
            },
            "token_calculator": token_metrics,
            "agent_memory": memory_metrics
        }
        
        # Add intelligence layer metrics if available
        if self.enable_intelligence:
            if self.context_filter:
                result["context_filter"] = self.context_filter.get_performance_metrics()
            
            if self.context_compressor:
                result["context_compressor"] = self.context_compressor.get_performance_metrics()
            
            if self.context_index:
                result["context_index"] = self.context_index.get_performance_metrics()
        
        return result
    
    # Cross-story context management methods
    
    async def register_story(
        self,
        story_id: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Register a new story for cross-story context management.
        
        Args:
            story_id: Unique story identifier
            metadata: Optional story metadata
        """
        if not self.enable_cross_story:
            return
        
        self._active_stories[story_id] = {
            "registered_at": datetime.utcnow(),
            "metadata": metadata or {},
            "active_agents": set(),
            "file_modifications": set(),
            "last_activity": datetime.utcnow()
        }
        
        logger.info(f"Registered story {story_id} for cross-story management")
    
    async def unregister_story(self, story_id: str) -> None:
        """Unregister a story from cross-story management"""
        if not self.enable_cross_story or story_id not in self._active_stories:
            return
        
        # Clean up associated data
        del self._active_stories[story_id]
        
        # Remove from conflicts
        self._story_conflicts.pop(story_id, None)
        for conflicts in self._story_conflicts.values():
            if story_id in conflicts:
                conflicts.remove(story_id)
        
        # Clean up cross-story cache
        keys_to_remove = [k for k in self._cross_story_cache.keys() if story_id in k]
        for key in keys_to_remove:
            del self._cross_story_cache[key]
        
        logger.info(f"Unregistered story {story_id} from cross-story management")
    
    async def detect_story_conflicts(
        self,
        story_id: str,
        file_paths: List[str]
    ) -> List[str]:
        """
        Detect conflicts between stories based on file modifications.
        
        Args:
            story_id: Story to check for conflicts
            file_paths: Files being modified by this story
            
        Returns:
            List of conflicting story IDs
        """
        if not self.enable_cross_story:
            return []
        
        conflicts = []
        
        for other_story_id, story_info in self._active_stories.items():
            if other_story_id == story_id:
                continue
            
            # Check for file overlap
            other_files = story_info.get("file_modifications", set())
            if set(file_paths).intersection(other_files):
                conflicts.append(other_story_id)
        
        # Update conflict tracking
        if conflicts:
            self._story_conflicts[story_id] = conflicts
            for conflict_story in conflicts:
                if conflict_story not in self._story_conflicts:
                    self._story_conflicts[conflict_story] = []
                if story_id not in self._story_conflicts[conflict_story]:
                    self._story_conflicts[conflict_story].append(story_id)
        
        return conflicts
    
    async def get_cross_story_context(
        self,
        story_id: str,
        conflicting_stories: List[str]
    ) -> Dict[str, Any]:
        """
        Get context information about conflicting stories.
        
        Args:
            story_id: Primary story ID
            conflicting_stories: List of conflicting story IDs
            
        Returns:
            Dictionary with cross-story context information
        """
        if not self.enable_cross_story:
            return {}
        
        cross_context = {
            "primary_story": story_id,
            "conflicts": [],
            "recommendations": []
        }
        
        for conflict_story in conflicting_stories:
            if conflict_story in self._active_stories:
                story_info = self._active_stories[conflict_story]
                conflict_info = {
                    "story_id": conflict_story,
                    "active_agents": list(story_info.get("active_agents", set())),
                    "modified_files": list(story_info.get("file_modifications", set())),
                    "last_activity": story_info.get("last_activity", datetime.utcnow()).isoformat(),
                    "metadata": story_info.get("metadata", {})
                }
                cross_context["conflicts"].append(conflict_info)
        
        # Generate recommendations
        if len(conflicting_stories) > 0:
            cross_context["recommendations"] = [
                "Consider coordinating with conflicting stories before making changes",
                "Review recent changes in conflicting stories",
                "Ensure test coverage for shared file modifications"
            ]
        
        return cross_context
    
    async def resolve_story_conflict(
        self,
        story_id: str,
        conflict_story_id: str,
        resolution: str
    ) -> bool:
        """
        Record resolution of a story conflict.
        
        Args:
            story_id: Primary story ID
            conflict_story_id: Conflicting story ID
            resolution: Description of how conflict was resolved
            
        Returns:
            True if resolution was recorded successfully
        """
        if not self.enable_cross_story:
            return False
        
        # Remove from active conflicts
        if story_id in self._story_conflicts:
            if conflict_story_id in self._story_conflicts[story_id]:
                self._story_conflicts[story_id].remove(conflict_story_id)
        
        if conflict_story_id in self._story_conflicts:
            if story_id in self._story_conflicts[conflict_story_id]:
                self._story_conflicts[conflict_story_id].remove(story_id)
        
        # Record resolution in agent memory
        await self.agent_memory.add_decision(
            "ContextManager",
            story_id,
            Decision(
                agent_type="ContextManager",
                description=f"Resolved conflict with story {conflict_story_id}",
                rationale=resolution,
                outcome="conflict_resolved",
                confidence=1.0,
                artifacts={"conflict_story": conflict_story_id}
            )
        )
        
        logger.info(f"Resolved conflict between stories {story_id} and {conflict_story_id}: {resolution}")
        return True
    
    async def get_monitoring_dashboard_data(self) -> Dict[str, Any]:
        """Get comprehensive monitoring data for dashboard display"""
        dashboard_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "system_health": "unknown",
            "performance_metrics": {},
            "cache_statistics": {},
            "active_stories": len(self._active_stories),
            "story_conflicts": len(self._story_conflicts),
            "advanced_features": {
                "intelligence": self.enable_intelligence,
                "advanced_caching": self.enable_advanced_caching,
                "monitoring": self.enable_monitoring,
                "cross_story": self.enable_cross_story
            }
        }
        
        # Get performance metrics
        dashboard_data["performance_metrics"] = self.get_performance_metrics()
        
        # Get monitoring data if available
        if self.enable_monitoring and self.monitor:
            try:
                health = self.monitor.get_system_health()
                dashboard_data["system_health"] = health.overall_status
                dashboard_data["monitoring_metrics"] = await self.monitor.get_performance_summary()
            except Exception as e:
                logger.warning(f"Error getting monitoring data: {str(e)}")
        
        # Get cache statistics
        if self.enable_advanced_caching and self.context_cache:
            try:
                cache_stats = await self.context_cache.get_statistics()
                dashboard_data["cache_statistics"] = {
                    "hit_rate": cache_stats.hit_rate,
                    "entry_count": cache_stats.entry_count,
                    "memory_usage_mb": cache_stats.memory_usage_bytes / (1024 * 1024),
                    "prediction_accuracy": cache_stats.prediction_accuracy
                }
            except Exception as e:
                logger.warning(f"Error getting cache statistics: {str(e)}")
        
        # Cross-story information
        if self.enable_cross_story:
            dashboard_data["cross_story_details"] = {
                "active_stories": list(self._active_stories.keys()),
                "conflicts": dict(self._story_conflicts),
                "story_metadata": {
                    story_id: info.get("metadata", {}) 
                    for story_id, info in self._active_stories.items()
                }
            }
        
        return dashboard_data
    
    # Background processing methods
    
    async def trigger_index_update(self, file_paths: Optional[List[str]] = None) -> Optional[str]:
        """Trigger background index update"""
        if self.enable_background_processing and self.background_processor:
            return await self.background_processor.trigger_index_update(file_paths)
        return None
    
    async def warm_cache_for_context(
        self,
        agent_type: str,
        story_id: str,
        predicted_requests: List[ContextRequest]
    ) -> Optional[str]:
        """Queue cache warming for predicted context requests"""
        if self.enable_background_processing and self.background_processor:
            return await self.background_processor.warm_cache_for_agent(
                agent_type, story_id, predicted_requests
            )
        return None
    
    async def schedule_learning_optimization(self, delay_hours: int = 1) -> Optional[str]:
        """Schedule learning system optimization"""
        if self.enable_background_processing and self.background_processor:
            from datetime import timedelta
            scheduled_time = datetime.utcnow() + timedelta(hours=delay_hours)
            
            return await self.background_processor.submit_task(
                task_type="learning_optimization",
                priority=TaskPriority.LOW,
                scheduled_at=scheduled_time
            )
        return None
    
    async def get_background_statistics(self) -> Dict[str, Any]:
        """Get background processing statistics"""
        if self.enable_background_processing and self.background_processor:
            stats = await self.background_processor.get_statistics()
            return {
                "total_tasks": stats.total_tasks,
                "completed_tasks": stats.completed_tasks,
                "failed_tasks": stats.failed_tasks,
                "active_tasks": stats.active_tasks,
                "queued_tasks": stats.queued_tasks,
                "success_rate": stats.success_rate,
                "average_execution_time": stats.average_execution_time,
                "cache_warming_hits": stats.cache_warming_hits,
                "pattern_discoveries": stats.pattern_discoveries
            }
        return {"error": "Background processing not enabled"}
    
    async def _queue_initial_background_tasks(self) -> None:
        """Queue initial background tasks on startup"""
        if not (self.enable_background_processing and self.background_processor):
            return
        
        try:
            # Queue index update
            await self.background_processor.submit_task(
                task_type="index_update",
                priority=TaskPriority.MEDIUM,
                force_rebuild=False
            )
            
            # Queue cache cleanup
            await self.background_processor.submit_task(
                task_type="cache_cleanup",
                priority=TaskPriority.LOW
            )
            
            # Schedule pattern discovery
            await self.background_processor.schedule_pattern_discovery(delay_minutes=30)
            
            logger.info("Queued initial background tasks")
            
        except Exception as e:
            logger.warning(f"Error queuing initial background tasks: {str(e)}")
    
    # Private implementation methods
    
    async def _prepare_context_internal(self, request: ContextRequest) -> AgentContext:
        """Internal context preparation implementation with intelligence layer integration"""
        
        # Initialize context
        context = AgentContext(
            request_id=request.id,
            agent_type=request.agent_type,
            story_id=request.story_id,
            tdd_phase=self._extract_tdd_phase(request.task)
        )
        
        # Step 1: Calculate token budget
        budget = await self.token_calculator.calculate_budget(
            total_tokens=request.max_tokens,
            agent_type=request.agent_type,
            tdd_phase=context.tdd_phase,
            metadata=request.metadata
        )
        context.token_budget = budget
        
        # Step 2: Gather relevant files (intelligent filtering if available)
        if self.enable_intelligence and self.context_filter:
            relevant_files = await self._gather_relevant_files_intelligent(request, context)
        else:
            relevant_files = await self._gather_relevant_files_basic(request, context)
        
        # Step 3: Load and process file contents
        file_contents = await self._load_file_contents(relevant_files)
        context.file_contents = file_contents
        
        # Step 4: Apply intelligent compression if enabled
        if self.enable_intelligence and self.context_compressor:
            context.core_context = await self._format_core_context_compressed(
                file_contents, budget.core_task, request
            )
        else:
            context.core_context = self._format_core_context(file_contents, budget.core_task)
        
        # Step 5: Add agent memory context
        if request.include_agent_memory and budget.agent_memory > 0:
            context.agent_memory = await self._format_agent_memory_context(
                request.agent_type, request.story_id, budget.agent_memory
            )
        
        # Step 6: Add historical context
        if request.include_history and budget.historical > 0:
            if self.enable_intelligence and self.context_index:
                context.historical_context = await self._format_historical_context_intelligent(
                    request.story_id, request.agent_type, budget.historical, request
                )
            else:
                context.historical_context = await self._format_historical_context(
                    request.story_id, request.agent_type, budget.historical
                )
        
        # Step 7: Add dependencies context
        if request.include_dependencies and budget.dependencies > 0:
            if self.enable_intelligence and self.context_index:
                context.dependencies = await self._format_dependencies_context_intelligent(
                    relevant_files, budget.dependencies, request
                )
            else:
                context.dependencies = await self._format_dependencies_context(
                    relevant_files, budget.dependencies
                )
        
        # Step 8: Calculate actual token usage
        context.token_usage = await self._calculate_token_usage(context)
        
        # Step 9: Apply compression if token budget exceeded
        if context.token_usage.total_used > request.max_tokens:
            if self.enable_intelligence and self.context_compressor:
                context = await self._apply_intelligent_compression(context, request)
            else:
                context = await self._apply_basic_compression(context, request.max_tokens)
        
        # Step 10: Track file access for learning
        if self.enable_intelligence and self.context_index:
            for file_path in context.file_contents.keys():
                await self.context_index.track_file_access(file_path)
        
        return context
    
    async def _gather_relevant_files_intelligent(
        self,
        request: ContextRequest,
        context: AgentContext
    ) -> List[str]:
        """Gather relevant files using intelligent filtering"""
        try:
            # Get candidate files using basic patterns
            candidate_files = await self._gather_candidate_files(request.agent_type)
            
            # Apply intelligent filtering
            relevance_scores = await self.context_filter.filter_relevant_files(
                request=request,
                candidate_files=candidate_files,
                max_files=20,
                min_score_threshold=0.1
            )
            
            # Store relevance scores in context
            context.relevance_scores = relevance_scores
            
            # Return sorted file paths
            return [score.file_path for score in relevance_scores]
            
        except Exception as e:
            logger.warning(f"Error in intelligent file filtering: {str(e)}")
            # Fallback to basic implementation
            return await self._gather_relevant_files_basic(request, context)
    
    async def _gather_relevant_files_basic(
        self, 
        request: ContextRequest, 
        context: AgentContext
    ) -> List[str]:
        """Gather relevant files for context (basic implementation)"""
        
        candidate_files = await self._gather_candidate_files(request.agent_type)
        
        # Sort by relevance (most recently modified first for now)
        candidate_files.sort(key=lambda f: Path(f).stat().st_mtime, reverse=True)
        
        logger.debug(f"Found {len(candidate_files)} relevant files for {request.agent_type}")
        return candidate_files[:20]  # Limit to top 20 files
    
    async def _gather_candidate_files(self, agent_type: str) -> List[str]:
        """Gather candidate files based on agent type patterns"""
        relevant_files = []
        
        # Common patterns based on agent type
        patterns = {
            "DesignAgent": ["*.md", "*.rst", "requirements*.txt", "*.yaml", "*.yml"],
            "CodeAgent": ["*.py", "*.js", "*.ts", "*.java", "*.cpp", "*.c", "*.h"],
            "QAAgent": ["test_*.py", "*_test.py", "test/*.py", "tests/*.py"],
            "DataAgent": ["*.csv", "*.json", "*.xml", "data/*", "*.sql"]
        }
        
        agent_patterns = patterns.get(agent_type, ["*.py", "*.md"])
        
        # Search for files matching patterns
        for pattern in agent_patterns:
            try:
                for file_path in self.project_path.rglob(pattern):
                    if self._should_include_file(file_path):
                        relevant_files.append(str(file_path))
                        if len(relevant_files) >= 100:  # Limit to prevent overflow
                            break
            except Exception as e:
                logger.warning(f"Error searching for pattern {pattern}: {str(e)}")
        
        return relevant_files
    
    async def _format_core_context_compressed(
        self,
        file_contents: Dict[str, str],
        token_budget: int,
        request: ContextRequest
    ) -> str:
        """Format core context with intelligent compression"""
        if not file_contents:
            return ""
        
        formatted_parts = []
        current_tokens = 0
        
        for file_path, content in file_contents.items():
            # Determine file type
            file_type = self._determine_file_type(Path(file_path))
            
            # Calculate target tokens for this file
            estimated_tokens = await self.token_calculator.estimate_tokens(content)
            
            if current_tokens + estimated_tokens > token_budget:
                # Apply compression to fit budget
                remaining_tokens = token_budget - current_tokens
                if remaining_tokens > 100:  # Only compress if we have reasonable space
                    try:
                        compressed_content, compression_ratio = await self.context_compressor.compress_content(
                            content=content,
                            file_path=file_path,
                            file_type=file_type,
                            compression_level=request.compression_level,
                            target_tokens=remaining_tokens,
                            preserve_structure=True
                        )
                        
                        formatted_parts.append(f"### {file_path}")
                        formatted_parts.append(f"# Compression ratio: {compression_ratio:.2f}")
                        formatted_parts.append("```")
                        formatted_parts.append(compressed_content)
                        formatted_parts.append("```")
                        formatted_parts.append("")
                        
                        current_tokens += await self.token_calculator.estimate_tokens(compressed_content)
                        
                    except Exception as e:
                        logger.warning(f"Error compressing {file_path}: {str(e)}")
                        # Fallback to truncation
                        char_limit = remaining_tokens * 4
                        truncated_content = content[:char_limit] + "\n... [truncated]"
                        
                        formatted_parts.append(f"### {file_path}")
                        formatted_parts.append("```")
                        formatted_parts.append(truncated_content)
                        formatted_parts.append("```")
                        formatted_parts.append("")
                        
                        current_tokens += remaining_tokens
                break
            else:
                # Content fits without compression
                formatted_parts.append(f"### {file_path}")
                formatted_parts.append("```")
                formatted_parts.append(content)
                formatted_parts.append("```")
                formatted_parts.append("")
                
                current_tokens += estimated_tokens
        
        return "\n".join(formatted_parts)
    
    async def _format_historical_context_intelligent(
        self,
        story_id: str,
        agent_type: str,
        token_budget: int,
        request: ContextRequest
    ) -> str:
        """Format historical context using context index"""
        try:
            # Get recent context snapshots
            snapshots = await self.agent_memory.get_context_history(
                agent_type, story_id, limit=10
            )
            
            if not snapshots:
                return ""
            
            historical_parts = []
            historical_parts.append("### Historical Context")
            
            for snapshot in snapshots[:3]:  # Limit to recent snapshots
                historical_parts.append(f"#### {snapshot.tdd_phase.value if snapshot.tdd_phase else 'Unknown'} Phase")
                historical_parts.append(f"Files: {', '.join(snapshot.file_list[:5])}")
                if len(snapshot.file_list) > 5:
                    historical_parts.append(f"... and {len(snapshot.file_list) - 5} more files")
                historical_parts.append(f"Context: {snapshot.context_summary}")
                historical_parts.append("")
            
            historical_content = "\n".join(historical_parts)
            
            # Truncate if exceeds budget
            estimated_tokens = await self.token_calculator.estimate_tokens(historical_content)
            if estimated_tokens > token_budget:
                char_limit = token_budget * 4
                historical_content = historical_content[:char_limit] + "\n... [truncated]"
            
            return historical_content
            
        except Exception as e:
            logger.warning(f"Error formatting intelligent historical context: {str(e)}")
            return await self._format_historical_context(story_id, agent_type, token_budget)
    
    async def _format_dependencies_context_intelligent(
        self,
        relevant_files: List[str],
        token_budget: int,
        request: ContextRequest
    ) -> str:
        """Format dependencies context using context index"""
        try:
            dependencies_parts = []
            dependencies_parts.append("### Dependencies Analysis")
            
            # Analyze dependencies for relevant files
            for file_path in relevant_files[:5]:  # Limit analysis
                try:
                    dep_info = await self.context_index.get_file_dependencies(
                        file_path=file_path,
                        depth=1,
                        include_reverse=True
                    )
                    
                    if dep_info.get("dependency_count", 0) > 0 or dep_info.get("reverse_dependency_count", 0) > 0:
                        dependencies_parts.append(f"#### {file_path}")
                        dependencies_parts.append(f"Dependencies: {dep_info.get('dependency_count', 0)}")
                        dependencies_parts.append(f"Reverse dependencies: {dep_info.get('reverse_dependency_count', 0)}")
                        
                        if dep_info.get("direct_dependencies"):
                            dependencies_parts.append(f"Imports: {', '.join(dep_info['direct_dependencies'][:3])}")
                        
                        dependencies_parts.append("")
                        
                except Exception as e:
                    logger.debug(f"Error analyzing dependencies for {file_path}: {str(e)}")
                    continue
            
            dependencies_content = "\n".join(dependencies_parts)
            
            # Truncate if exceeds budget
            estimated_tokens = await self.token_calculator.estimate_tokens(dependencies_content)
            if estimated_tokens > token_budget:
                char_limit = token_budget * 4
                dependencies_content = dependencies_content[:char_limit] + "\n... [truncated]"
            
            return dependencies_content
            
        except Exception as e:
            logger.warning(f"Error formatting intelligent dependencies context: {str(e)}")
            return await self._format_dependencies_context(relevant_files, token_budget)
    
    async def _apply_intelligent_compression(
        self,
        context: AgentContext,
        request: ContextRequest
    ) -> AgentContext:
        """Apply intelligent compression to context"""
        try:
            current_usage = context.token_usage.total_used
            max_tokens = request.max_tokens
            
            if current_usage <= max_tokens:
                return context
            
            logger.info(f"Applying intelligent compression: {current_usage} -> {max_tokens} tokens")
            
            # Determine compression level based on how much we need to compress
            compression_ratio_needed = max_tokens / current_usage
            
            if compression_ratio_needed > 0.8:
                compression_level = CompressionLevel.LOW
            elif compression_ratio_needed > 0.6:
                compression_level = CompressionLevel.MODERATE
            elif compression_ratio_needed > 0.4:
                compression_level = CompressionLevel.HIGH
            else:
                compression_level = CompressionLevel.EXTREME
            
            # Apply compression to different context components
            components_to_compress = [
                ("core_context", 0.6),      # 60% of budget for core context
                ("historical_context", 0.15), # 15% for historical
                ("dependencies", 0.15),      # 15% for dependencies
                ("agent_memory", 0.1)        # 10% for agent memory
            ]
            
            for component_name, budget_ratio in components_to_compress:
                component_content = getattr(context, component_name, "")
                if not component_content:
                    continue
                
                target_tokens = int(max_tokens * budget_ratio)
                
                try:
                    # Apply compression
                    compressed_content, ratio = await self.context_compressor.compress_content(
                        content=component_content,
                        file_path=f"context_{component_name}",
                        file_type=FileType.MARKDOWN,  # Treat context as markdown
                        compression_level=compression_level,
                        target_tokens=target_tokens
                    )
                    
                    setattr(context, component_name, compressed_content)
                    
                except Exception as e:
                    logger.warning(f"Error compressing {component_name}: {str(e)}")
                    # Fallback to simple truncation
                    char_limit = target_tokens * 4
                    truncated = component_content[:char_limit] + "\n... [compressed]"
                    setattr(context, component_name, truncated)
            
            # Recalculate token usage
            context.token_usage = await self._calculate_token_usage(context)
            context.compression_applied = True
            context.compression_level = compression_level
            
            final_tokens = context.token_usage.total_used
            logger.info(f"Intelligent compression completed: {current_usage} -> {final_tokens} tokens")
            
            return context
            
        except Exception as e:
            logger.error(f"Error in intelligent compression: {str(e)}")
            # Fallback to basic compression
            return await self._apply_basic_compression(context, request.max_tokens)
    
    def _determine_file_type(self, path: Path) -> FileType:
        """Determine file type from path"""
        suffix = path.suffix.lower()
        name = path.name.lower()
        
        if suffix == '.py':
            if 'test' in name or name.startswith('test_') or path.parent.name == 'tests':
                return FileType.TEST
            else:
                return FileType.PYTHON
        elif suffix in ['.md', '.rst']:
            return FileType.MARKDOWN
        elif suffix == '.json':
            return FileType.JSON
        elif suffix in ['.yml', '.yaml']:
            return FileType.YAML
        elif suffix in ['.cfg', '.ini', '.conf', '.toml']:
            return FileType.CONFIG
        else:
            return FileType.OTHER
    
    def _should_include_file(self, file_path: Path) -> bool:
        """Determine if file should be included in context"""
        
        # Skip hidden files and directories
        if any(part.startswith('.') for part in file_path.parts):
            return False
        
        # Skip common ignore patterns
        ignore_patterns = [
            '__pycache__', '.git', '.venv', 'venv', 'node_modules',
            '.pytest_cache', '.coverage', 'build', 'dist'
        ]
        
        if any(pattern in str(file_path) for pattern in ignore_patterns):
            return False
        
        # Check file size (skip very large files)
        try:
            if file_path.stat().st_size > 100_000:  # 100KB limit
                return False
        except OSError:
            return False
        
        return True
    
    async def _load_file_contents(self, file_paths: List[str]) -> Dict[str, str]:
        """Load contents of relevant files"""
        contents = {}
        
        for file_path in file_paths:
            try:
                path = Path(file_path)
                if path.exists() and path.is_file():
                    with open(path, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()
                        # Estimate tokens and skip if too large
                        estimated_tokens = await self.token_calculator.estimate_tokens(content)
                        if estimated_tokens < 10000:  # Skip very large files
                            contents[file_path] = content
                        else:
                            logger.debug(f"Skipping large file {file_path} ({estimated_tokens} tokens)")
                else:
                    logger.warning(f"File not found or not readable: {file_path}")
            except Exception as e:
                logger.error(f"Error reading file {file_path}: {str(e)}")
        
        return contents
    
    def _format_core_context(self, file_contents: Dict[str, str], token_budget: int) -> str:
        """Format core context from file contents"""
        if not file_contents:
            return ""
        
        formatted_parts = []
        current_tokens = 0
        
        for file_path, content in file_contents.items():
            # Estimate tokens for this file
            estimated_tokens = len(content) // 4  # Simple estimation
            
            if current_tokens + estimated_tokens > token_budget:
                # Truncate content to fit budget
                remaining_tokens = token_budget - current_tokens
                char_limit = remaining_tokens * 4
                content = content[:char_limit] + "\n... [truncated]"
            
            formatted_parts.append(f"### {file_path}")
            formatted_parts.append("```")
            formatted_parts.append(content)
            formatted_parts.append("```")
            formatted_parts.append("")
            
            current_tokens += estimated_tokens
            if current_tokens >= token_budget:
                break
        
        return "\n".join(formatted_parts)
    
    async def _format_agent_memory_context(
        self, 
        agent_type: str, 
        story_id: str, 
        token_budget: int
    ) -> str:
        """Format agent memory for context"""
        memory = await self.agent_memory.get_memory(agent_type, story_id)
        
        if not memory:
            return ""
        
        memory_parts = []
        memory_parts.append("### Agent Memory")
        
        # Recent decisions
        recent_decisions = memory.get_recent_decisions(limit=5)
        if recent_decisions:
            memory_parts.append("#### Recent Decisions:")
            for decision in recent_decisions:
                memory_parts.append(f"- {decision.description}: {decision.outcome}")
        
        # Learned patterns
        if memory.learned_patterns:
            memory_parts.append("#### Learned Patterns:")
            for pattern in memory.learned_patterns[:3]:  # Top 3 patterns
                memory_parts.append(f"- {pattern.pattern_type}: {pattern.description}")
        
        # Recent handoffs
        recent_handoffs = [h for h in memory.phase_handoffs[-3:]]
        if recent_handoffs:
            memory_parts.append("#### Recent Phase Handoffs:")
            for handoff in recent_handoffs:
                memory_parts.append(
                    f"- {handoff.from_phase.value if handoff.from_phase else 'none'} -> "
                    f"{handoff.to_phase.value if handoff.to_phase else 'none'}: {handoff.context_summary}"
                )
        
        memory_content = "\n".join(memory_parts)
        
        # Truncate if exceeds budget
        estimated_tokens = len(memory_content) // 4
        if estimated_tokens > token_budget:
            char_limit = token_budget * 4
            memory_content = memory_content[:char_limit] + "\n... [truncated]"
        
        return memory_content
    
    async def _format_historical_context(
        self, 
        story_id: str, 
        agent_type: str, 
        token_budget: int
    ) -> str:
        """Format historical context (placeholder implementation)"""
        return f"### Historical Context\nStory: {story_id}, Agent: {agent_type}\n[Historical context placeholder]"
    
    async def _format_dependencies_context(
        self, 
        relevant_files: List[str], 
        token_budget: int
    ) -> str:
        """Format dependencies context (placeholder implementation)"""
        return f"### Dependencies\nAnalyzed {len(relevant_files)} files\n[Dependencies analysis placeholder]"
    
    async def _calculate_token_usage(self, context: AgentContext) -> TokenUsage:
        """Calculate actual token usage for context"""
        core_tokens = await self.token_calculator.estimate_tokens(context.core_context or "")
        deps_tokens = await self.token_calculator.estimate_tokens(context.dependencies or "")
        hist_tokens = await self.token_calculator.estimate_tokens(context.historical_context or "")
        memory_tokens = await self.token_calculator.estimate_tokens(context.agent_memory or "")
        metadata_tokens = await self.token_calculator.estimate_tokens(context.metadata or "")
        
        total_tokens = core_tokens + deps_tokens + hist_tokens + memory_tokens + metadata_tokens
        
        return TokenUsage(
            context_id=context.request_id,
            total_used=total_tokens,
            core_task_used=core_tokens,
            historical_used=hist_tokens,
            dependencies_used=deps_tokens,
            agent_memory_used=memory_tokens,
            buffer_used=metadata_tokens
        )
    
    async def _apply_basic_compression(
        self, 
        context: AgentContext, 
        max_tokens: int
    ) -> AgentContext:
        """Apply basic compression when context exceeds token limit"""
        current_usage = context.token_usage.total_used
        
        if current_usage <= max_tokens:
            return context
        
        # Calculate compression ratio needed
        compression_ratio = max_tokens / current_usage
        
        # Apply proportional reduction to each component
        if context.core_context:
            char_limit = int(len(context.core_context) * compression_ratio)
            context.core_context = context.core_context[:char_limit] + "\n... [compressed]"
        
        if context.historical_context:
            char_limit = int(len(context.historical_context) * compression_ratio)
            context.historical_context = context.historical_context[:char_limit] + "\n... [compressed]"
        
        if context.dependencies:
            char_limit = int(len(context.dependencies) * compression_ratio)
            context.dependencies = context.dependencies[:char_limit] + "\n... [compressed]"
        
        if context.agent_memory:
            char_limit = int(len(context.agent_memory) * compression_ratio)
            context.agent_memory = context.agent_memory[:char_limit] + "\n... [compressed]"
        
        # Recalculate token usage
        context.token_usage = await self._calculate_token_usage(context)
        context.compression_applied = True
        context.compression_level = CompressionLevel.MODERATE
        
        logger.info(f"Applied basic compression: {current_usage} -> {context.token_usage.total_used} tokens")
        
        return context
    
    
    def _generate_cache_key(self, request: ContextRequest) -> str:
        """Generate cache key for context request"""
        # Create cache key from request properties
        key_data = f"{request.agent_type}:{request.story_id}:{request.max_tokens}"
        
        # Add task description if available
        if hasattr(request.task, 'description'):
            key_data += f":{request.task.description}"
        elif isinstance(request.task, dict) and 'description' in request.task:
            key_data += f":{request.task['description']}"
        
        # Add options
        key_data += f":{request.compression_level.value}:{request.include_history}:{request.include_dependencies}"
        
        # Hash to create manageable key
        return hashlib.md5(key_data.encode()).hexdigest()
    
    def _extract_story_id(self, task: Union[TDDTask, Dict[str, Any]]) -> str:
        """Extract story ID from task"""
        if hasattr(task, 'story_id'):
            return task.story_id
        elif isinstance(task, dict) and 'story_id' in task:
            return task['story_id']
        return "default"
    
    def _extract_tdd_phase(self, task: Union[TDDTask, Dict[str, Any]]) -> Optional[TDDState]:
        """Extract TDD phase from task"""
        if hasattr(task, 'current_state'):
            return task.current_state
        elif isinstance(task, dict) and 'current_state' in task:
            state_value = task['current_state']
            if isinstance(state_value, str):
                try:
                    return TDDState(state_value)
                except ValueError:
                    pass
            elif isinstance(state_value, TDDState):
                return state_value
        return None
    
    # Cross-story management private methods
    
    async def _handle_cross_story_preparation(self, request: ContextRequest) -> None:
        """Handle cross-story concerns during context preparation"""
        story_id = request.story_id
        
        # Register agent activity
        if story_id in self._active_stories:
            self._active_stories[story_id]["active_agents"].add(request.agent_type)
            self._active_stories[story_id]["last_activity"] = datetime.utcnow()
        else:
            # Auto-register story if not already registered
            await self.register_story(story_id, {"auto_registered": True})
            self._active_stories[story_id]["active_agents"].add(request.agent_type)
        
        # Extract file paths from task if available
        file_paths = []
        if hasattr(request.task, 'file_paths'):
            file_paths = request.task.file_paths
        elif isinstance(request.task, dict) and 'file_paths' in request.task:
            file_paths = request.task['file_paths']
        
        if file_paths:
            # Update file modification tracking
            self._active_stories[story_id]["file_modifications"].update(file_paths)
            
            # Check for conflicts
            conflicts = await self.detect_story_conflicts(story_id, file_paths)
            
            if conflicts:
                logger.warning(
                    f"Story {story_id} has potential conflicts with stories: {conflicts}"
                )
                
                # Add cross-story context to request metadata
                cross_context = await self.get_cross_story_context(story_id, conflicts)
                if not hasattr(request, 'metadata'):
                    request.metadata = {}
                request.metadata['cross_story_context'] = cross_context
    
    async def _update_cross_story_tracking(
        self, 
        request: ContextRequest, 
        context: AgentContext
    ) -> None:
        """Update cross-story tracking after context preparation"""
        story_id = request.story_id
        
        if story_id in self._active_stories:
            # Update file tracking with actual files used
            if context.file_contents:
                file_paths = list(context.file_contents.keys())
                self._active_stories[story_id]["file_modifications"].update(file_paths)
            
            # Update activity timestamp
            self._active_stories[story_id]["last_activity"] = datetime.utcnow()
            
            # Cache cross-story context for future use
            if hasattr(request, 'metadata') and 'cross_story_context' in request.metadata:
                cache_key = f"cross_story_{story_id}_{hash(str(sorted(context.file_contents.keys())))}"
                self._cross_story_cache[cache_key] = context
    
    # Updated cache methods for fallback
    
    async def _get_cached_context_legacy(self, request: ContextRequest) -> Optional[AgentContext]:
        """Check legacy cache for context (fallback when advanced caching disabled)"""
        cache_key = self._generate_cache_key(request)
        
        if cache_key in self._legacy_cache:
            context, timestamp = self._legacy_cache[cache_key]
            
            # Check if cache entry is still valid
            if datetime.utcnow() - timestamp < timedelta(seconds=self.cache_ttl_seconds):
                return context
            else:
                # Remove expired entry
                del self._legacy_cache[cache_key]
        
        return None
    
    async def _cache_context_legacy(self, request: ContextRequest, context: AgentContext) -> None:
        """Cache context in legacy cache (fallback)"""
        cache_key = self._generate_cache_key(request)
        self._legacy_cache[cache_key] = (context, datetime.utcnow())
        
        # Limit cache size
        if len(self._legacy_cache) > 100:
            # Remove oldest entries
            oldest_key = min(self._legacy_cache.keys(), 
                           key=lambda k: self._legacy_cache[k][1])
            del self._legacy_cache[oldest_key]