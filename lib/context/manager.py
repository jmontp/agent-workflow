"""
Context Manager - Central coordination component for context preparation

The ContextManager orchestrates context preparation for agent tasks by coordinating
between filtering, compression, caching, and other context management components.
"""

import asyncio
import logging
import time
from typing import Dict, List, Optional, Any, Union
from datetime import datetime, timedelta
import os
import json

from .models import (
    ContextRequest, 
    AgentContext, 
    TokenBudget, 
    TokenUsage,
    CompressionLevel,
    ContextType,
    ContextSnapshot
)
from .exceptions import (
    ContextError, 
    TokenBudgetExceededError, 
    ContextNotFoundError,
    ContextTimeoutError
)

# Import interfaces that will be implemented
from .interfaces import (
    IContextFilter,
    ITokenCalculator, 
    IAgentMemory,
    IContextCompressor,
    IContextIndex,
    IContextStorage
)

# Import TDD models
try:
    from ..tdd_models import TDDState, TDDTask, TDDCycle
except ImportError:
    from tdd_models import TDDState, TDDTask, TDDCycle

logger = logging.getLogger(__name__)


class ContextManager:
    """
    Central coordinator for context management operations.
    
    Manages the lifecycle of context preparation, coordinates between different
    context processing components, and provides caching and optimization.
    """
    
    def __init__(
        self,
        context_filter: Optional[IContextFilter] = None,
        token_calculator: Optional[ITokenCalculator] = None,
        agent_memory: Optional[IAgentMemory] = None,
        context_compressor: Optional[IContextCompressor] = None,
        context_index: Optional[IContextIndex] = None,
        context_storage: Optional[IContextStorage] = None,
        cache_ttl_seconds: int = 300,  # 5 minutes default
        max_preparation_time: int = 30  # 30 seconds timeout
    ):
        """
        Initialize ContextManager with component dependencies.
        
        Args:
            context_filter: Component for filtering relevant files
            token_calculator: Component for token budget management
            agent_memory: Component for agent memory management
            context_compressor: Component for content compression
            context_index: Component for content indexing and search
            context_storage: Component for context persistence
            cache_ttl_seconds: Time-to-live for context cache in seconds
            max_preparation_time: Maximum time for context preparation in seconds
        """
        self.context_filter = context_filter
        self.token_calculator = token_calculator
        self.agent_memory = agent_memory
        self.context_compressor = context_compressor
        self.context_index = context_index
        self.context_storage = context_storage
        
        self.cache_ttl_seconds = cache_ttl_seconds
        self.max_preparation_time = max_preparation_time
        
        # In-memory cache for contexts
        self._context_cache: Dict[str, tuple[AgentContext, datetime]] = {}
        
        # Performance metrics
        self._preparation_times: List[float] = []
        self._cache_hits = 0
        self._cache_misses = 0
        self._total_requests = 0
        
        logger.info("ContextManager initialized with all components")
    
    async def prepare_context(
        self, 
        agent_type: str, 
        task: Union[TDDTask, Dict[str, Any]], 
        max_tokens: int = 200000,
        story_id: Optional[str] = None,
        **kwargs
    ) -> AgentContext:
        """
        Prepare context for agent task execution.
        
        Args:
            agent_type: Type of agent requesting context
            task: Task to be executed (TDDTask or dict)
            max_tokens: Maximum tokens allowed for context
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
        self._total_requests += 1
        
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
            
            # Check cache first
            cached_context = await self._get_cached_context(request)
            if cached_context:
                self._cache_hits += 1
                cached_context.cache_hit = True
                logger.info(f"Context cache hit for request {request.id}")
                return cached_context
            
            self._cache_misses += 1
            
            # Prepare context with timeout
            context = await asyncio.wait_for(
                self._prepare_context_internal(request),
                timeout=self.max_preparation_time
            )
            
            # Cache the prepared context
            await self._cache_context(request, context)
            
            preparation_time = time.time() - start_time
            context.preparation_time = preparation_time
            self._preparation_times.append(preparation_time)
            
            logger.info(
                f"Context prepared for {agent_type} in {preparation_time:.2f}s, "
                f"tokens: {context.get_total_token_estimate()}/{max_tokens}"
            )
            
            return context
            
        except asyncio.TimeoutError:
            error_msg = f"Context preparation timed out after {self.max_preparation_time}s"
            logger.error(error_msg)
            raise ContextTimeoutError(
                error_msg, 
                operation="prepare_context",
                timeout_seconds=self.max_preparation_time
            )
        except Exception as e:
            logger.error(f"Context preparation failed: {str(e)}")
            raise ContextError(f"Context preparation failed: {str(e)}")
    
    async def _prepare_context_internal(self, request: ContextRequest) -> AgentContext:
        """Internal context preparation logic"""
        
        # Initialize context
        context = AgentContext(
            request_id=request.id,
            agent_type=request.agent_type,
            story_id=request.story_id,
            tdd_phase=self._extract_tdd_phase(request.task)
        )
        
        # Step 1: Calculate token budget
        if self.token_calculator:
            budget = await self.token_calculator.calculate_budget(
                total_tokens=request.max_tokens,
                agent_type=request.agent_type,
                tdd_phase=context.tdd_phase,
                metadata=request.metadata
            )
            context.token_budget = budget
        else:
            # Default budget allocation
            context.token_budget = self._create_default_budget(request.max_tokens)
        
        # Step 2: Filter relevant files
        relevant_files = []
        if self.context_filter:
            relevant_files = await self.context_filter.filter_relevant_files(
                task=request.task,
                story_id=request.story_id,
                agent_type=request.agent_type,
                tdd_phase=context.tdd_phase
            )
            context.relevance_scores = await self.context_filter.get_relevance_scores(
                files=relevant_files,
                task=request.task,
                story_id=request.story_id
            )
        
        # Step 3: Load file contents
        file_contents = await self._load_file_contents(relevant_files)
        context.file_contents = file_contents
        
        # Step 4: Apply compression if needed
        if self.context_compressor and request.compression_level != CompressionLevel.NONE:
            compressed_contents = await self.context_compressor.compress_contents(
                contents=file_contents,
                target_tokens=context.token_budget.core_task,
                compression_level=request.compression_level,
                file_types=self._detect_file_types(relevant_files)
            )
            context.core_context = self._format_core_context(compressed_contents)
            context.compression_applied = True
            context.compression_level = request.compression_level
        else:
            context.core_context = self._format_core_context(file_contents)
        
        # Step 5: Add dependencies context
        if request.include_dependencies and context.token_budget.dependencies > 0:
            context.dependencies = await self._prepare_dependencies_context(
                relevant_files=relevant_files,
                token_budget=context.token_budget.dependencies
            )
        
        # Step 6: Add historical context
        if request.include_history and context.token_budget.historical > 0:
            context.historical_context = await self._prepare_historical_context(
                story_id=request.story_id,
                agent_type=request.agent_type,
                token_budget=context.token_budget.historical
            )
        
        # Step 7: Add agent memory
        if request.include_agent_memory and self.agent_memory and context.token_budget.agent_memory > 0:
            memory = await self.agent_memory.get_memory(
                agent_type=request.agent_type,
                story_id=request.story_id
            )
            context.agent_memory = await self._format_agent_memory(
                memory=memory,
                token_budget=context.token_budget.agent_memory
            )
        
        # Step 8: Calculate actual token usage
        context.token_usage = self._calculate_token_usage(context)
        
        # Validate token budget
        if context.token_usage.total_used > request.max_tokens:
            raise TokenBudgetExceededError(
                f"Context exceeds token budget: {context.token_usage.total_used} > {request.max_tokens}",
                requested_tokens=context.token_usage.total_used,
                available_tokens=request.max_tokens
            )
        
        return context
    
    async def update_context(self, context_id: str, changes: Dict[str, Any]) -> None:
        """
        Update existing context with changes.
        
        Args:
            context_id: ID of context to update
            changes: Dictionary of changes to apply
        """
        # Check if context exists in cache
        for cache_key, (cached_context, timestamp) in self._context_cache.items():
            if cached_context.request_id == context_id:
                # Apply changes
                for key, value in changes.items():
                    if hasattr(cached_context, key):
                        setattr(cached_context, key, value)
                
                # Update timestamp
                self._context_cache[cache_key] = (cached_context, datetime.utcnow())
                logger.info(f"Context {context_id} updated with {len(changes)} changes")
                return
        
        logger.warning(f"Context {context_id} not found for update")
    
    async def invalidate_context(self, context_id: str) -> None:
        """
        Invalidate specific context from cache.
        
        Args:
            context_id: ID of context to invalidate
        """
        keys_to_remove = []
        for cache_key, (cached_context, _) in self._context_cache.items():
            if cached_context.request_id == context_id:
                keys_to_remove.append(cache_key)
        
        for key in keys_to_remove:
            del self._context_cache[key]
        
        logger.info(f"Context {context_id} invalidated from cache")
    
    async def get_agent_memory(self, agent_type: str, story_id: str) -> Optional[Any]:
        """
        Get agent memory for specific agent and story.
        
        Args:
            agent_type: Type of agent
            story_id: Story ID
            
        Returns:
            Agent memory if available
        """
        if self.agent_memory:
            return await self.agent_memory.get_memory(agent_type, story_id)
        return None
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get performance metrics for context management"""
        avg_preparation_time = (
            sum(self._preparation_times) / len(self._preparation_times)
            if self._preparation_times else 0.0
        )
        
        cache_hit_rate = (
            self._cache_hits / (self._cache_hits + self._cache_misses)
            if (self._cache_hits + self._cache_misses) > 0 else 0.0
        )
        
        return {
            "total_requests": self._total_requests,
            "cache_hits": self._cache_hits,
            "cache_misses": self._cache_misses,
            "cache_hit_rate": cache_hit_rate,
            "average_preparation_time": avg_preparation_time,
            "max_preparation_time": max(self._preparation_times) if self._preparation_times else 0.0,
            "min_preparation_time": min(self._preparation_times) if self._preparation_times else 0.0,
            "cached_contexts": len(self._context_cache)
        }
    
    async def cleanup_cache(self) -> int:
        """Clean up expired cache entries"""
        current_time = datetime.utcnow()
        expired_keys = []
        
        for cache_key, (context, timestamp) in self._context_cache.items():
            if current_time - timestamp > timedelta(seconds=self.cache_ttl_seconds):
                expired_keys.append(cache_key)
        
        for key in expired_keys:
            del self._context_cache[key]
        
        logger.info(f"Cleaned up {len(expired_keys)} expired cache entries")
        return len(expired_keys)
    
    # Private helper methods
    
    async def _get_cached_context(self, request: ContextRequest) -> Optional[AgentContext]:
        """Check if context is available in cache"""
        cache_key = self._generate_cache_key(request)
        
        if cache_key in self._context_cache:
            context, timestamp = self._context_cache[cache_key]
            
            # Check if cache entry is still valid
            if datetime.utcnow() - timestamp < timedelta(seconds=self.cache_ttl_seconds):
                return context
            else:
                # Remove expired entry
                del self._context_cache[cache_key]
        
        return None
    
    async def _cache_context(self, request: ContextRequest, context: AgentContext) -> None:
        """Cache prepared context"""
        cache_key = self._generate_cache_key(request)
        self._context_cache[cache_key] = (context, datetime.utcnow())
    
    def _generate_cache_key(self, request: ContextRequest) -> str:
        """Generate cache key for context request"""
        # Simple cache key based on agent type, story, and task description
        task_desc = ""
        if hasattr(request.task, 'description'):
            task_desc = str(request.task.description)
        elif isinstance(request.task, dict) and 'description' in request.task:
            task_desc = str(request.task['description'])
        
        return f"{request.agent_type}:{request.story_id}:{hash(task_desc)}"
    
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
    
    def _create_default_budget(self, total_tokens: int) -> TokenBudget:
        """Create default token budget allocation"""
        return TokenBudget(
            total_budget=total_tokens,
            core_task=int(total_tokens * 0.40),
            historical=int(total_tokens * 0.25),
            dependencies=int(total_tokens * 0.20),
            agent_memory=int(total_tokens * 0.10),
            buffer=int(total_tokens * 0.05)
        )
    
    async def _load_file_contents(self, file_paths: List[str]) -> Dict[str, str]:
        """Load contents of relevant files"""
        contents = {}
        
        for file_path in file_paths:
            try:
                if os.path.exists(file_path):
                    with open(file_path, 'r', encoding='utf-8') as f:
                        contents[file_path] = f.read()
                else:
                    logger.warning(f"File not found: {file_path}")
            except Exception as e:
                logger.error(f"Error reading file {file_path}: {str(e)}")
        
        return contents
    
    def _detect_file_types(self, file_paths: List[str]) -> Dict[str, str]:
        """Detect file types for compression optimization"""
        file_types = {}
        
        for file_path in file_paths:
            if file_path.endswith('.py'):
                if 'test' in file_path.lower() or file_path.endswith('_test.py'):
                    file_types[file_path] = 'test'
                else:
                    file_types[file_path] = 'python'
            elif file_path.endswith('.md'):
                file_types[file_path] = 'markdown'
            elif file_path.endswith(('.json', '.yaml', '.yml')):
                file_types[file_path] = 'config'
            else:
                file_types[file_path] = 'other'
        
        return file_types
    
    def _format_core_context(self, file_contents: Dict[str, str]) -> str:
        """Format core context from file contents"""
        if not file_contents:
            return ""
        
        formatted_parts = []
        for file_path, content in file_contents.items():
            formatted_parts.append(f"### {file_path}")
            formatted_parts.append("```")
            formatted_parts.append(content)
            formatted_parts.append("```")
            formatted_parts.append("")  # Empty line
        
        return "\n".join(formatted_parts)
    
    async def _prepare_dependencies_context(self, relevant_files: List[str], token_budget: int) -> str:
        """Prepare dependencies context"""
        # This would be implemented with actual dependency analysis
        # For now, return a placeholder
        if not relevant_files:
            return ""
        
        dependencies_info = []
        dependencies_info.append("### Dependencies Analysis")
        dependencies_info.append(f"Analyzed {len(relevant_files)} files for dependencies")
        
        return "\n".join(dependencies_info)
    
    async def _prepare_historical_context(self, story_id: str, agent_type: str, token_budget: int) -> str:
        """Prepare historical context"""
        # This would be implemented with actual historical data
        # For now, return a placeholder
        historical_info = []
        historical_info.append("### Historical Context")
        historical_info.append(f"Story: {story_id}, Agent: {agent_type}")
        
        return "\n".join(historical_info)
    
    async def _format_agent_memory(self, memory: Any, token_budget: int) -> str:
        """Format agent memory for context"""
        if not memory:
            return ""
        
        memory_parts = []
        memory_parts.append("### Agent Memory")
        
        if hasattr(memory, 'get_recent_decisions'):
            recent_decisions = memory.get_recent_decisions(limit=5)
            if recent_decisions:
                memory_parts.append("#### Recent Decisions:")
                for decision in recent_decisions:
                    memory_parts.append(f"- {decision.description}: {decision.outcome}")
        
        return "\n".join(memory_parts)
    
    def _calculate_token_usage(self, context: AgentContext) -> TokenUsage:
        """Calculate actual token usage for context"""
        # Simple token estimation: ~4 characters per token
        
        core_tokens = len(context.core_context) // 4 if context.core_context else 0
        deps_tokens = len(context.dependencies) // 4 if context.dependencies else 0
        hist_tokens = len(context.historical_context) // 4 if context.historical_context else 0
        memory_tokens = len(context.agent_memory) // 4 if context.agent_memory else 0
        metadata_tokens = len(context.metadata) // 4 if context.metadata else 0
        
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