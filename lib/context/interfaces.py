"""
Context Management System Interfaces

Abstract interfaces for context management components to ensure
proper separation of concerns and testability.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any, Union
from .models import (
    ContextRequest,
    AgentContext,
    TokenBudget,
    TokenUsage,
    AgentMemory,
    RelevanceScore,
    CompressionLevel,
    FileType
)

# Import TDD models
try:
    from ..tdd_models import TDDState, TDDTask
except ImportError:
    from tdd_models import TDDState, TDDTask


class IContextFilter(ABC):
    """Interface for context filtering components"""
    
    @abstractmethod
    async def filter_relevant_files(
        self,
        task: Union[TDDTask, Dict[str, Any]],
        story_id: str,
        agent_type: str,
        tdd_phase: Optional[TDDState] = None,
        max_files: int = 100
    ) -> List[str]:
        """
        Filter and return relevant files for the given task.
        
        Args:
            task: Task to analyze for relevance
            story_id: Story ID for context isolation
            agent_type: Type of agent requesting context
            tdd_phase: Current TDD phase
            max_files: Maximum number of files to return
            
        Returns:
            List of relevant file paths
        """
        pass
    
    @abstractmethod
    async def get_relevance_scores(
        self,
        files: List[str],
        task: Union[TDDTask, Dict[str, Any]],
        story_id: str
    ) -> List[RelevanceScore]:
        """
        Calculate relevance scores for given files.
        
        Args:
            files: List of file paths to score
            task: Task for relevance calculation
            story_id: Story ID for context
            
        Returns:
            List of relevance scores
        """
        pass
    
    @abstractmethod
    async def update_historical_relevance(
        self,
        agent_type: str,
        files_used: List[str],
        task_success: bool
    ) -> None:
        """
        Update historical relevance data based on usage.
        
        Args:
            agent_type: Type of agent that used the files
            files_used: List of files that were used
            task_success: Whether the task was successful
        """
        pass


class ITokenCalculator(ABC):
    """Interface for token budget calculation and management"""
    
    @abstractmethod
    async def calculate_budget(
        self,
        total_tokens: int,
        agent_type: str,
        tdd_phase: Optional[TDDState] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> TokenBudget:
        """
        Calculate optimal token budget allocation.
        
        Args:
            total_tokens: Total token budget available
            agent_type: Type of agent requesting budget
            tdd_phase: Current TDD phase
            metadata: Additional metadata for budget calculation
            
        Returns:
            TokenBudget with allocation breakdown
        """
        pass
    
    @abstractmethod
    async def estimate_tokens(
        self,
        content: str,
        content_type: Optional[FileType] = None
    ) -> int:
        """
        Estimate token count for given content.
        
        Args:
            content: Content to analyze
            content_type: Type of content for more accurate estimation
            
        Returns:
            Estimated token count
        """
        pass
    
    @abstractmethod
    async def optimize_allocation(
        self,
        current_budget: TokenBudget,
        actual_usage: TokenUsage,
        context_quality: float
    ) -> TokenBudget:
        """
        Optimize budget allocation based on usage patterns.
        
        Args:
            current_budget: Current budget allocation
            actual_usage: Actual token usage
            context_quality: Quality score of the context
            
        Returns:
            Optimized budget allocation
        """
        pass


class IAgentMemory(ABC):
    """Interface for agent memory management"""
    
    @abstractmethod
    async def get_memory(
        self,
        agent_type: str,
        story_id: str
    ) -> Optional[AgentMemory]:
        """
        Retrieve agent memory for specific agent and story.
        
        Args:
            agent_type: Type of agent
            story_id: Story ID
            
        Returns:
            Agent memory if available
        """
        pass
    
    @abstractmethod
    async def store_memory(
        self,
        memory: AgentMemory
    ) -> None:
        """
        Store agent memory.
        
        Args:
            memory: Agent memory to store
        """
        pass
    
    @abstractmethod
    async def update_memory(
        self,
        agent_type: str,
        story_id: str,
        updates: Dict[str, Any]
    ) -> None:
        """
        Update existing agent memory.
        
        Args:
            agent_type: Type of agent
            story_id: Story ID
            updates: Updates to apply
        """
        pass
    
    @abstractmethod
    async def clear_memory(
        self,
        agent_type: str,
        story_id: Optional[str] = None
    ) -> None:
        """
        Clear agent memory.
        
        Args:
            agent_type: Type of agent
            story_id: Story ID (if None, clears all for agent)
        """
        pass


class IContextCompressor(ABC):
    """Interface for context compression"""
    
    @abstractmethod
    async def compress_contents(
        self,
        contents: Dict[str, str],
        target_tokens: int,
        compression_level: CompressionLevel = CompressionLevel.MODERATE,
        file_types: Optional[Dict[str, str]] = None
    ) -> Dict[str, str]:
        """
        Compress file contents to target token count.
        
        Args:
            contents: Dictionary of file path to content
            target_tokens: Target token count after compression
            compression_level: Level of compression to apply
            file_types: File type information for optimization
            
        Returns:
            Compressed contents dictionary
        """
        pass
    
    @abstractmethod
    async def compress_single_file(
        self,
        content: str,
        target_tokens: int,
        file_type: FileType = FileType.OTHER,
        compression_level: CompressionLevel = CompressionLevel.MODERATE
    ) -> str:
        """
        Compress single file content.
        
        Args:
            content: File content to compress
            target_tokens: Target token count
            file_type: Type of file for optimization
            compression_level: Level of compression
            
        Returns:
            Compressed content
        """
        pass
    
    @abstractmethod
    async def get_compression_ratio(
        self,
        original_content: str,
        compressed_content: str
    ) -> float:
        """
        Calculate compression ratio.
        
        Args:
            original_content: Original content
            compressed_content: Compressed content
            
        Returns:
            Compression ratio (0.0 to 1.0)
        """
        pass


class IContextIndex(ABC):
    """Interface for context indexing and search"""
    
    @abstractmethod
    async def build_index(
        self,
        project_path: str,
        force_rebuild: bool = False
    ) -> None:
        """
        Build or update project index.
        
        Args:
            project_path: Path to project root
            force_rebuild: Whether to force complete rebuild
        """
        pass
    
    @abstractmethod
    async def search_files(
        self,
        query: str,
        file_types: Optional[List[FileType]] = None,
        limit: int = 50
    ) -> List[str]:
        """
        Search for files matching query.
        
        Args:
            query: Search query
            file_types: File types to search in
            limit: Maximum results to return
            
        Returns:
            List of matching file paths
        """
        pass
    
    @abstractmethod
    async def get_dependencies(
        self,
        file_path: str
    ) -> List[str]:
        """
        Get dependencies for a specific file.
        
        Args:
            file_path: Path to file
            
        Returns:
            List of dependency file paths
        """
        pass
    
    @abstractmethod
    async def get_dependents(
        self,
        file_path: str
    ) -> List[str]:
        """
        Get files that depend on the specified file.
        
        Args:
            file_path: Path to file
            
        Returns:
            List of dependent file paths
        """
        pass


class IContextStorage(ABC):
    """Interface for context storage and persistence"""
    
    @abstractmethod
    async def store_context(
        self,
        context: AgentContext
    ) -> None:
        """
        Store prepared context.
        
        Args:
            context: Context to store
        """
        pass
    
    @abstractmethod
    async def retrieve_context(
        self,
        context_id: str
    ) -> Optional[AgentContext]:
        """
        Retrieve stored context.
        
        Args:
            context_id: ID of context to retrieve
            
        Returns:
            Stored context if found
        """
        pass
    
    @abstractmethod
    async def list_contexts(
        self,
        agent_type: Optional[str] = None,
        story_id: Optional[str] = None,
        limit: int = 100
    ) -> List[str]:
        """
        List stored context IDs.
        
        Args:
            agent_type: Filter by agent type
            story_id: Filter by story ID
            limit: Maximum results to return
            
        Returns:
            List of context IDs
        """
        pass
    
    @abstractmethod
    async def delete_context(
        self,
        context_id: str
    ) -> bool:
        """
        Delete stored context.
        
        Args:
            context_id: ID of context to delete
            
        Returns:
            True if deleted, False if not found
        """
        pass
    
    @abstractmethod
    async def cleanup_old_contexts(
        self,
        older_than_days: int = 30
    ) -> int:
        """
        Clean up old contexts.
        
        Args:
            older_than_days: Delete contexts older than this many days
            
        Returns:
            Number of contexts deleted
        """
        pass