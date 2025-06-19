"""
Simple Context Manager - Performance-Optimized Implementation

Provides a lightweight context management implementation focused on performance
for high-frequency agent interactions, especially in mock/demo scenarios.
"""

import asyncio
import logging
import time
from pathlib import Path
from typing import Dict, List, Optional, Any, Union
from datetime import datetime

try:
    from .context.models import (
        ContextRequest, 
        AgentContext, 
        TokenBudget, 
        TokenUsage,
        CompressionLevel,
        ContextType,
        TDDState
    )
    from .context.exceptions import (
        ContextError, 
        TokenBudgetExceededError, 
        ContextTimeoutError
    )
    from .token_calculator import TokenCalculator
    from .tdd_models import TDDTask
except ImportError:
    from context.models import (
        ContextRequest, 
        AgentContext, 
        TokenBudget, 
        TokenUsage,
        CompressionLevel,
        ContextType,
        TDDState
    )
    from context.exceptions import (
        ContextError, 
        TokenBudgetExceededError, 
        ContextTimeoutError
    )
    from token_calculator import TokenCalculator
    from tdd_models import TDDTask

logger = logging.getLogger(__name__)


class SimpleContextManager:
    """
    Lightweight context manager optimized for performance.
    
    Provides minimal overhead context management with simple token-based
    truncation for high-frequency agent interactions and mock scenarios.
    """
    
    def __init__(
        self,
        project_path: Optional[str] = None,
        max_tokens: int = 200000,
        max_files: int = 10,
        max_file_size: int = 50000,  # Character limit per file
        enable_caching: bool = False,
        cache_size: int = 50
    ):
        """
        Initialize SimpleContextManager with minimal overhead.
        
        Args:
            project_path: Path to project root
            max_tokens: Maximum token limit
            max_files: Maximum number of files to include
            max_file_size: Maximum characters per file
            enable_caching: Whether to enable simple caching
            cache_size: Number of contexts to cache
        """
        self.project_path = Path(project_path) if project_path else Path.cwd()
        self.max_tokens = max_tokens
        self.max_files = max_files
        self.max_file_size = max_file_size
        self.enable_caching = enable_caching
        self.cache_size = cache_size
        
        # Initialize minimal token calculator
        self.token_calculator = TokenCalculator(max_tokens=max_tokens)
        
        # Simple in-memory cache
        self._cache: Dict[str, tuple[AgentContext, float]] = {}
        self._cache_ttl = 300  # 5 minutes
        
        # Performance metrics
        self._request_count = 0
        self._cache_hits = 0
        self._total_preparation_time = 0.0
        
        logger.info(f"SimpleContextManager initialized for project: {self.project_path}")
    
    async def prepare_context(
        self,
        agent_type: str,
        task: Union[TDDTask, Dict[str, Any]],
        max_tokens: Optional[int] = None,
        story_id: Optional[str] = None,
        **kwargs
    ) -> AgentContext:
        """
        Prepare context with simple, fast processing.
        
        Args:
            agent_type: Type of agent requesting context
            task: Task to be executed
            max_tokens: Maximum tokens allowed
            story_id: Story ID for context
            **kwargs: Additional options (mostly ignored for simplicity)
            
        Returns:
            AgentContext with prepared content
        """
        start_time = time.time()
        self._request_count += 1
        
        # Use default max_tokens if not specified
        max_tokens = max_tokens or self.max_tokens
        story_id = story_id or self._extract_story_id(task)
        
        # Generate simple cache key
        cache_key = f"{agent_type}:{story_id}:{max_tokens}"
        
        # Check cache if enabled
        if self.enable_caching:
            cached_context = self._get_cached_context(cache_key)
            if cached_context:
                self._cache_hits += 1
                logger.debug(f"Cache hit for {agent_type}:{story_id}")
                return cached_context
        
        try:
            # Create context request
            request = ContextRequest(
                agent_type=agent_type,
                story_id=story_id,
                task=task,
                max_tokens=max_tokens,
                compression_level=CompressionLevel.LOW,  # Always use minimal compression
                include_history=False,  # Disable history for performance
                include_dependencies=False,  # Disable dependencies for performance
                include_agent_memory=False  # Disable agent memory for performance
            )
            
            # Prepare context with fast implementation
            context = await self._prepare_context_fast(request)
            
            # Cache the result if enabled
            if self.enable_caching:
                self._cache_context(cache_key, context)
            
            preparation_time = time.time() - start_time
            context.preparation_time = preparation_time
            self._total_preparation_time += preparation_time
            
            logger.debug(
                f"Simple context prepared for {agent_type} in {preparation_time:.3f}s, "
                f"tokens: {context.get_total_token_estimate()}/{max_tokens}"
            )
            
            return context
            
        except Exception as e:
            logger.error(f"Simple context preparation failed: {str(e)}")
            raise ContextError(f"Simple context preparation failed: {str(e)}")
    
    async def _prepare_context_fast(self, request: ContextRequest) -> AgentContext:
        """Fast context preparation implementation"""
        # Initialize context
        context = AgentContext(
            request_id=request.id,
            agent_type=request.agent_type,
            story_id=request.story_id,
            tdd_phase=self._extract_tdd_phase(request.task)
        )
        
        # Simple token budget calculation (equal distribution)
        budget = TokenBudget(
            total=request.max_tokens,
            core_task=int(request.max_tokens * 0.8),  # 80% for core content
            historical=0,  # Disabled for performance
            dependencies=0,  # Disabled for performance
            agent_memory=0,  # Disabled for performance
            buffer=int(request.max_tokens * 0.2)  # 20% buffer
        )
        context.token_budget = budget
        
        # Get relevant files quickly
        relevant_files = await self._get_relevant_files_fast(request.agent_type)
        
        # Load and process files with truncation
        file_contents = await self._load_files_with_truncation(relevant_files, budget.core_task)
        context.file_contents = file_contents
        
        # Format core context simply
        context.core_context = self._format_context_simple(file_contents)
        
        # Calculate token usage
        context.token_usage = await self._calculate_token_usage_fast(context)
        
        # Apply truncation if needed
        if context.token_usage.total_used > request.max_tokens:
            context = await self._apply_simple_truncation(context, request.max_tokens)
        
        return context
    
    async def _get_relevant_files_fast(self, agent_type: str) -> List[str]:
        """Get relevant files using simple patterns and fast filesystem operations"""
        relevant_files = []
        
        # Simple agent-based patterns
        patterns = {
            "DesignAgent": ["*.md", "*.rst", "*.txt"],
            "CodeAgent": ["*.py", "*.js", "*.ts"],
            "QAAgent": ["test_*.py", "*_test.py", "*.py"],
            "DataAgent": ["*.csv", "*.json", "*.py"],
            "Orchestrator": ["*.py", "*.md", "*.yaml", "*.yml"]
        }
        
        agent_patterns = patterns.get(agent_type, ["*.py"])
        
        # Quick file search with limits
        for pattern in agent_patterns:
            try:
                for file_path in self.project_path.rglob(pattern):
                    if self._should_include_file_fast(file_path):
                        relevant_files.append(str(file_path))
                        if len(relevant_files) >= self.max_files:
                            break
                if len(relevant_files) >= self.max_files:
                    break
            except Exception as e:
                logger.debug(f"Error searching pattern {pattern}: {e}")
        
        # Sort by modification time (most recent first)
        try:
            relevant_files.sort(key=lambda f: Path(f).stat().st_mtime, reverse=True)
        except Exception as e:
            logger.debug(f"Error sorting files: {e}")
        
        return relevant_files[:self.max_files]
    
    def _should_include_file_fast(self, file_path: Path) -> bool:
        """Fast file inclusion check with minimal filesystem operations"""
        # Quick string-based checks
        path_str = str(file_path)
        
        # Skip hidden files and common ignore patterns
        if any(part.startswith('.') for part in file_path.parts):
            return False
        
        # Quick pattern exclusions
        exclusions = ['__pycache__', 'node_modules', '.git', 'venv', '.venv', 'build', 'dist']
        if any(exclude in path_str for exclude in exclusions):
            return False
        
        # Check if file exists and is readable (minimal stat call)
        try:
            stat = file_path.stat()
            return stat.st_size > 0 and stat.st_size < 200000  # Skip very large files
        except (OSError, PermissionError):
            return False
    
    async def _load_files_with_truncation(self, file_paths: List[str], token_budget: int) -> Dict[str, str]:
        """Load files with aggressive truncation for performance"""
        contents = {}
        current_tokens = 0
        tokens_per_file = token_budget // max(len(file_paths), 1)
        
        for file_path in file_paths:
            if current_tokens >= token_budget:
                break
                
            try:
                path = Path(file_path)
                if not path.exists():
                    continue
                
                # Read file with size limit
                with open(path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read(self.max_file_size)  # Truncate at character level
                
                # Estimate tokens quickly (rough approximation)
                estimated_tokens = len(content) // 4
                
                # Truncate if exceeds per-file budget
                if estimated_tokens > tokens_per_file:
                    char_limit = tokens_per_file * 4
                    content = content[:char_limit] + "\n... [truncated for performance]"
                    estimated_tokens = tokens_per_file
                
                contents[file_path] = content
                current_tokens += estimated_tokens
                
                logger.debug(f"Loaded {file_path}: {estimated_tokens} tokens")
                
            except Exception as e:
                logger.debug(f"Error loading {file_path}: {e}")
        
        return contents
    
    def _format_context_simple(self, file_contents: Dict[str, str]) -> str:
        """Simple context formatting without advanced processing"""
        if not file_contents:
            return "No relevant files found."
        
        parts = []
        parts.append("# Project Context\n")
        
        for file_path, content in file_contents.items():
            # Simple file header
            relative_path = str(Path(file_path).relative_to(self.project_path))
            parts.append(f"## {relative_path}\n")
            parts.append("```")
            parts.append(content)
            parts.append("```\n")
        
        return "\n".join(parts)
    
    async def _calculate_token_usage_fast(self, context: AgentContext) -> TokenUsage:
        """Fast token usage calculation with approximation"""
        # Quick estimation: 4 characters ≈ 1 token
        core_tokens = len(context.core_context or "") // 4
        
        return TokenUsage(
            context_id=context.request_id,
            total_used=core_tokens,
            core_task_used=core_tokens,
            historical_used=0,
            dependencies_used=0,
            agent_memory_used=0,
            buffer_used=0
        )
    
    async def _apply_simple_truncation(self, context: AgentContext, max_tokens: int) -> AgentContext:
        """Apply simple truncation to fit token budget"""
        current_tokens = context.token_usage.total_used
        
        if current_tokens <= max_tokens:
            return context
        
        # Calculate truncation ratio
        ratio = max_tokens / current_tokens
        
        # Truncate core context
        if context.core_context:
            char_limit = int(len(context.core_context) * ratio)
            context.core_context = context.core_context[:char_limit] + "\n... [truncated to fit token budget]"
        
        # Recalculate token usage
        context.token_usage = await self._calculate_token_usage_fast(context)
        context.compression_applied = True
        context.compression_level = CompressionLevel.HIGH
        
        logger.debug(f"Applied truncation: {current_tokens} -> {context.token_usage.total_used} tokens")
        
        return context
    
    def _get_cached_context(self, cache_key: str) -> Optional[AgentContext]:
        """Get context from simple cache"""
        if cache_key in self._cache:
            context, timestamp = self._cache[cache_key]
            if time.time() - timestamp < self._cache_ttl:
                return context
            else:
                del self._cache[cache_key]
        return None
    
    def _cache_context(self, cache_key: str, context: AgentContext):
        """Cache context with simple LRU eviction"""
        # Clean up expired entries
        current_time = time.time()
        expired_keys = [
            k for k, (_, ts) in self._cache.items() 
            if current_time - ts > self._cache_ttl
        ]
        for key in expired_keys:
            del self._cache[key]
        
        # Evict oldest if cache full
        if len(self._cache) >= self.cache_size:
            oldest_key = min(self._cache.keys(), key=lambda k: self._cache[k][1])
            del self._cache[oldest_key]
        
        # Add new entry
        self._cache[cache_key] = (context, current_time)
    
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
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get performance metrics for the simple context manager"""
        avg_preparation_time = (
            self._total_preparation_time / self._request_count 
            if self._request_count > 0 else 0.0
        )
        
        cache_hit_rate = (
            self._cache_hits / self._request_count 
            if self._request_count > 0 else 0.0
        )
        
        return {
            "context_manager_type": "simple",
            "total_requests": self._request_count,
            "cache_hits": self._cache_hits,
            "cache_hit_rate": cache_hit_rate,
            "average_preparation_time": avg_preparation_time,
            "cached_contexts": len(self._cache),
            "max_tokens": self.max_tokens,
            "max_files": self.max_files,
            "max_file_size": self.max_file_size,
            "caching_enabled": self.enable_caching
        }
    
    async def cleanup_cache(self) -> int:
        """Clean up expired cache entries"""
        current_time = time.time()
        expired_keys = [
            k for k, (_, ts) in self._cache.items() 
            if current_time - ts > self._cache_ttl
        ]
        
        for key in expired_keys:
            del self._cache[key]
        
        logger.debug(f"Cleaned up {len(expired_keys)} expired cache entries")
        return len(expired_keys)
    
    # Compatibility methods for interface consistency
    
    async def start(self) -> None:
        """Start the context manager (no-op for simple manager)"""
        logger.info("SimpleContextManager started")
    
    async def stop(self) -> None:
        """Stop the context manager (no-op for simple manager)"""
        logger.info("SimpleContextManager stopped")
    
    async def invalidate_context(self, context_id: str) -> None:
        """Invalidate specific context from cache"""
        keys_to_remove = []
        for cache_key, (cached_context, _) in self._cache.items():
            if cached_context.request_id == context_id:
                keys_to_remove.append(cache_key)
        
        for key in keys_to_remove:
            del self._cache[key]
        
        logger.debug(f"Context {context_id} invalidated")
    
    # Placeholder methods for interface compatibility
    
    async def record_agent_decision(self, *args, **kwargs) -> str:
        """No-op implementation for compatibility"""
        return "simple-decision-id"
    
    async def record_phase_handoff(self, *args, **kwargs) -> str:
        """No-op implementation for compatibility"""
        return "simple-handoff-id"
    
    async def create_context_snapshot(self, *args, **kwargs) -> str:
        """No-op implementation for compatibility"""
        return "simple-snapshot-id"
    
    async def get_agent_context_history(self, *args, **kwargs) -> List:
        """No-op implementation for compatibility"""
        return []
    
    async def get_recent_decisions(self, *args, **kwargs) -> List:
        """No-op implementation for compatibility"""
        return []
    
    async def get_phase_handoffs(self, *args, **kwargs) -> List:
        """No-op implementation for compatibility"""
        return []
    
    async def analyze_agent_learning(self, *args, **kwargs) -> Dict[str, Any]:
        """No-op implementation for compatibility"""
        return {"message": "Learning analysis not available in simple mode"}
    
    async def optimize_token_budget(self, *args, **kwargs):
        """No-op implementation for compatibility"""
        return None
    
    async def build_context_index(self, *args, **kwargs) -> None:
        """No-op implementation for compatibility"""
        pass
    
    async def search_codebase(self, *args, **kwargs) -> List[Dict[str, Any]]:
        """No-op implementation for compatibility"""
        return []
    
    async def get_file_dependencies(self, *args, **kwargs) -> Dict[str, Any]:
        """No-op implementation for compatibility"""
        return {"message": "Dependencies not available in simple mode"}
    
    async def get_file_relevance_explanation(self, *args, **kwargs) -> Dict[str, Any]:
        """No-op implementation for compatibility"""
        return {"message": "Relevance explanation not available in simple mode"}
    
    async def estimate_compression_potential(self, *args, **kwargs) -> Dict[str, Any]:
        """No-op implementation for compatibility"""
        return {"message": "Compression estimation not available in simple mode"}
    
    async def get_project_statistics(self) -> Dict[str, Any]:
        """No-op implementation for compatibility"""
        return {"message": "Project statistics not available in simple mode"}