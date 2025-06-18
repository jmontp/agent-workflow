"""
Agent Memory Management for Context System

Implements persistent storage of agent decisions and artifacts with context handoffs
between TDD phases. Provides memory retrieval based on relevance and recency.
"""

import asyncio
import json
import logging
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any, Union
from dataclasses import asdict

try:
    from .context.models import AgentMemory, Decision, PhaseHandoff, Pattern, ContextSnapshot
    from .context.interfaces import IAgentMemory
except ImportError:
    from context.models import AgentMemory, Decision, PhaseHandoff, Pattern, ContextSnapshot
    from context.interfaces import IAgentMemory

# Import TDD models
try:
    from .tdd_models import TDDState, TDDTask, TDDCycle
except ImportError:
    from tdd_models import TDDState, TDDTask, TDDCycle

logger = logging.getLogger(__name__)


class FileBasedAgentMemory(IAgentMemory):
    """
    File-based implementation of agent memory storage.
    
    Stores agent memories in JSON files within the project's .orch-state directory,
    providing persistence and retrieval of agent decisions, patterns, and context.
    """
    
    def __init__(self, base_path: str = ".orch-state"):
        """
        Initialize FileBasedAgentMemory.
        
        Args:
            base_path: Base directory for memory storage
        """
        self.base_path = Path(base_path)
        self.memory_dir = self.base_path / "agent_memory"
        
        # Create directories if they don't exist
        self.memory_dir.mkdir(parents=True, exist_ok=True)
        
        # In-memory cache for frequently accessed memories
        self._memory_cache: Dict[str, tuple[AgentMemory, datetime]] = {}
        self._cache_ttl = timedelta(minutes=30)
        
        # Performance tracking
        self._get_calls = 0
        self._store_calls = 0
        self._cache_hits = 0
        self._cache_misses = 0
        
        logger.info(f"AgentMemory initialized with storage at {self.memory_dir}")
    
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
        self._get_calls += 1
        cache_key = f"{agent_type}:{story_id}"
        
        # Check cache first
        if cache_key in self._memory_cache:
            memory, timestamp = self._memory_cache[cache_key]
            if datetime.utcnow() - timestamp < self._cache_ttl:
                self._cache_hits += 1
                logger.debug(f"Memory cache hit for {cache_key}")
                return memory
            else:
                # Remove expired entry
                del self._memory_cache[cache_key]
        
        self._cache_misses += 1
        
        # Load from file
        memory_file = self._get_memory_file_path(agent_type, story_id)
        
        if not memory_file.exists():
            logger.debug(f"No memory file found for {agent_type}:{story_id}")
            return None
        
        try:
            with open(memory_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            memory = AgentMemory.from_dict(data)
            
            # Cache the loaded memory
            self._memory_cache[cache_key] = (memory, datetime.utcnow())
            
            logger.debug(f"Loaded memory for {agent_type}:{story_id} from {memory_file}")
            return memory
            
        except Exception as e:
            logger.error(f"Failed to load memory from {memory_file}: {str(e)}")
            return None
    
    async def store_memory(self, memory: AgentMemory) -> None:
        """
        Store agent memory.
        
        Args:
            memory: Agent memory to store
        """
        self._store_calls += 1
        
        try:
            memory_file = self._get_memory_file_path(memory.agent_type, memory.story_id)
            
            # Ensure directory exists
            memory_file.parent.mkdir(parents=True, exist_ok=True)
            
            # Update timestamp
            memory.updated_at = datetime.utcnow()
            
            # Convert to dictionary and save
            data = memory.to_dict()
            
            with open(memory_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            # Update cache
            cache_key = f"{memory.agent_type}:{memory.story_id}"
            self._memory_cache[cache_key] = (memory, datetime.utcnow())
            
            logger.debug(f"Stored memory for {memory.agent_type}:{memory.story_id} to {memory_file}")
            
        except Exception as e:
            logger.error(f"Failed to store memory: {str(e)}")
            raise
    
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
        memory = await self.get_memory(agent_type, story_id)
        
        if memory is None:
            # Create new memory if it doesn't exist
            memory = AgentMemory(
                agent_type=agent_type,
                story_id=story_id
            )
        
        # Apply updates
        for key, value in updates.items():
            if hasattr(memory, key):
                setattr(memory, key, value)
            else:
                # Store in metadata if attribute doesn't exist
                memory.metadata[key] = value
        
        await self.store_memory(memory)
        
        logger.debug(f"Updated memory for {agent_type}:{story_id} with {len(updates)} changes")
    
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
        if story_id:
            # Clear specific story memory
            memory_file = self._get_memory_file_path(agent_type, story_id)
            if memory_file.exists():
                memory_file.unlink()
                logger.info(f"Cleared memory for {agent_type}:{story_id}")
            
            # Remove from cache
            cache_key = f"{agent_type}:{story_id}"
            if cache_key in self._memory_cache:
                del self._memory_cache[cache_key]
        else:
            # Clear all memories for agent
            agent_dir = self.memory_dir / agent_type
            if agent_dir.exists():
                for memory_file in agent_dir.glob("*.json"):
                    memory_file.unlink()
                
                # Remove empty directory
                try:
                    agent_dir.rmdir()
                except OSError:
                    pass  # Directory not empty
                
                logger.info(f"Cleared all memories for {agent_type}")
            
            # Clear from cache
            keys_to_remove = [key for key in self._memory_cache.keys() if key.startswith(f"{agent_type}:")]
            for key in keys_to_remove:
                del self._memory_cache[key]
    
    # Specialized methods for TDD workflow
    
    async def add_decision(
        self,
        agent_type: str,
        story_id: str,
        decision: Decision
    ) -> None:
        """Add a decision to agent memory"""
        memory = await self.get_memory(agent_type, story_id)
        
        if memory is None:
            memory = AgentMemory(agent_type=agent_type, story_id=story_id)
        
        memory.add_decision(decision)
        await self.store_memory(memory)
        
        logger.debug(f"Added decision {decision.id} to {agent_type}:{story_id}")
    
    async def add_pattern(
        self,
        agent_type: str,
        story_id: str,
        pattern: Pattern
    ) -> None:
        """Add a learned pattern to agent memory"""
        memory = await self.get_memory(agent_type, story_id)
        
        if memory is None:
            memory = AgentMemory(agent_type=agent_type, story_id=story_id)
        
        memory.add_pattern(pattern)
        await self.store_memory(memory)
        
        logger.debug(f"Added pattern {pattern.id} to {agent_type}:{story_id}")
    
    async def add_phase_handoff(
        self,
        agent_type: str,
        story_id: str,
        handoff: PhaseHandoff
    ) -> None:
        """Add a phase handoff record to agent memory"""
        memory = await self.get_memory(agent_type, story_id)
        
        if memory is None:
            memory = AgentMemory(agent_type=agent_type, story_id=story_id)
        
        memory.add_phase_handoff(handoff)
        await self.store_memory(memory)
        
        logger.debug(f"Added phase handoff {handoff.id} to {agent_type}:{story_id}")
    
    async def add_context_snapshot(
        self,
        agent_type: str,
        story_id: str,
        snapshot: ContextSnapshot
    ) -> None:
        """Add a context snapshot to agent memory"""
        memory = await self.get_memory(agent_type, story_id)
        
        if memory is None:
            memory = AgentMemory(agent_type=agent_type, story_id=story_id)
        
        memory.add_context_snapshot(snapshot)
        await self.store_memory(memory)
        
        logger.debug(f"Added context snapshot {snapshot.id} to {agent_type}:{story_id}")
    
    async def get_recent_decisions(
        self,
        agent_type: str,
        story_id: str,
        limit: int = 10
    ) -> List[Decision]:
        """Get recent decisions for an agent"""
        memory = await self.get_memory(agent_type, story_id)
        
        if memory is None:
            return []
        
        return memory.get_recent_decisions(limit)
    
    async def get_patterns_by_type(
        self,
        agent_type: str,
        story_id: str,
        pattern_type: str
    ) -> List[Pattern]:
        """Get patterns by type for an agent"""
        memory = await self.get_memory(agent_type, story_id)
        
        if memory is None:
            return []
        
        return memory.get_patterns_by_type(pattern_type)
    
    async def get_phase_handoffs(
        self,
        agent_type: str,
        story_id: str,
        from_phase: Optional[TDDState] = None,
        to_phase: Optional[TDDState] = None
    ) -> List[PhaseHandoff]:
        """Get phase handoffs with optional filtering"""
        memory = await self.get_memory(agent_type, story_id)
        
        if memory is None:
            return []
        
        handoffs = memory.phase_handoffs
        
        if from_phase:
            handoffs = [h for h in handoffs if h.from_phase == from_phase]
        
        if to_phase:
            handoffs = [h for h in handoffs if h.to_phase == to_phase]
        
        return sorted(handoffs, key=lambda h: h.timestamp, reverse=True)
    
    async def get_context_history(
        self,
        agent_type: str,
        story_id: str,
        tdd_phase: Optional[TDDState] = None,
        limit: int = 20
    ) -> List[ContextSnapshot]:
        """Get context history with optional filtering"""
        memory = await self.get_memory(agent_type, story_id)
        
        if memory is None:
            return []
        
        history = memory.context_history
        
        if tdd_phase:
            history = [h for h in history if h.tdd_phase == tdd_phase]
        
        # Sort by timestamp (most recent first) and apply limit
        return sorted(history, key=lambda h: h.timestamp, reverse=True)[:limit]
    
    # Memory analysis and insights
    
    async def get_memory_summary(
        self,
        agent_type: str,
        story_id: str
    ) -> Dict[str, Any]:
        """Get a summary of agent memory"""
        memory = await self.get_memory(agent_type, story_id)
        
        if memory is None:
            return {
                "exists": False,
                "agent_type": agent_type,
                "story_id": story_id
            }
        
        return {
            "exists": True,
            "agent_type": memory.agent_type,
            "story_id": memory.story_id,
            "created_at": memory.created_at.isoformat(),
            "updated_at": memory.updated_at.isoformat(),
            "decisions_count": len(memory.decisions),
            "patterns_count": len(memory.learned_patterns),
            "handoffs_count": len(memory.phase_handoffs),
            "context_snapshots_count": len(memory.context_history),
            "artifacts_count": len(memory.artifacts),
            "metadata_keys": list(memory.metadata.keys()),
            "recent_activity": self._get_recent_activity_summary(memory)
        }
    
    async def analyze_agent_patterns(
        self,
        agent_type: str,
        story_id: str
    ) -> Dict[str, Any]:
        """Analyze patterns in agent behavior"""
        memory = await self.get_memory(agent_type, story_id)
        
        if memory is None:
            return {"analysis": "No memory available"}
        
        analysis = {
            "pattern_types": {},
            "decision_confidence_avg": 0.0,
            "successful_patterns": [],
            "phase_transitions": {},
            "common_artifacts": {},
            "learning_progression": []
        }
        
        # Analyze pattern types
        for pattern in memory.learned_patterns:
            pattern_type = pattern.pattern_type
            if pattern_type not in analysis["pattern_types"]:
                analysis["pattern_types"][pattern_type] = {
                    "count": 0,
                    "avg_success_rate": 0.0,
                    "total_usage": 0
                }
            
            analysis["pattern_types"][pattern_type]["count"] += 1
            analysis["pattern_types"][pattern_type]["avg_success_rate"] += pattern.success_rate
            analysis["pattern_types"][pattern_type]["total_usage"] += pattern.usage_count
        
        # Calculate averages
        for pattern_type, data in analysis["pattern_types"].items():
            if data["count"] > 0:
                data["avg_success_rate"] /= data["count"]
        
        # Analyze decisions
        if memory.decisions:
            total_confidence = sum(d.confidence for d in memory.decisions)
            analysis["decision_confidence_avg"] = total_confidence / len(memory.decisions)
        
        # Analyze successful patterns
        analysis["successful_patterns"] = [
            {
                "pattern_type": p.pattern_type,
                "description": p.description,
                "success_rate": p.success_rate,
                "usage_count": p.usage_count
            }
            for p in memory.learned_patterns
            if p.success_rate > 0.8 and p.usage_count > 2
        ]
        
        # Analyze phase transitions
        for handoff in memory.phase_handoffs:
            transition = f"{handoff.from_phase.value if handoff.from_phase else 'none'} -> {handoff.to_phase.value if handoff.to_phase else 'none'}"
            analysis["phase_transitions"][transition] = analysis["phase_transitions"].get(transition, 0) + 1
        
        return analysis
    
    async def cleanup_old_memories(self, older_than_days: int = 90) -> int:
        """Clean up old memory files"""
        cutoff_date = datetime.utcnow() - timedelta(days=older_than_days)
        deleted_count = 0
        
        for agent_dir in self.memory_dir.iterdir():
            if not agent_dir.is_dir():
                continue
            
            for memory_file in agent_dir.glob("*.json"):
                try:
                    # Check file modification time
                    file_mtime = datetime.fromtimestamp(memory_file.stat().st_mtime)
                    
                    if file_mtime < cutoff_date:
                        memory_file.unlink()
                        deleted_count += 1
                        logger.debug(f"Deleted old memory file: {memory_file}")
                        
                except Exception as e:
                    logger.error(f"Error cleaning up memory file {memory_file}: {str(e)}")
        
        # Clear cache of deleted entries
        self._memory_cache.clear()
        
        logger.info(f"Cleaned up {deleted_count} old memory files")
        return deleted_count
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get performance metrics for memory operations"""
        cache_hit_rate = (
            self._cache_hits / (self._cache_hits + self._cache_misses)
            if (self._cache_hits + self._cache_misses) > 0 else 0.0
        )
        
        return {
            "get_calls": self._get_calls,
            "store_calls": self._store_calls,
            "cache_hits": self._cache_hits,
            "cache_misses": self._cache_misses,
            "cache_hit_rate": cache_hit_rate,
            "cached_memories": len(self._memory_cache),
            "storage_path": str(self.memory_dir)
        }
    
    # Private helper methods
    
    def _get_memory_file_path(self, agent_type: str, story_id: str) -> Path:
        """Get file path for agent memory"""
        # Handle None or empty story_id
        if not story_id or not story_id.strip():
            safe_story_id = "default"
        else:
            # Sanitize story_id for filename
            safe_story_id = "".join(c for c in story_id if c.isalnum() or c in '-_').strip()
            if not safe_story_id:
                safe_story_id = "default"
        
        return self.memory_dir / agent_type / f"{safe_story_id}.json"
    
    def _get_recent_activity_summary(self, memory: AgentMemory) -> Dict[str, Any]:
        """Get summary of recent activity in memory"""
        now = datetime.utcnow()
        last_week = now - timedelta(days=7)
        
        recent_decisions = [d for d in memory.decisions if d.timestamp >= last_week]
        recent_patterns = [p for p in memory.learned_patterns if p.timestamp >= last_week]
        recent_handoffs = [h for h in memory.phase_handoffs if h.timestamp >= last_week]
        recent_snapshots = [s for s in memory.context_history if s.timestamp >= last_week]
        
        return {
            "recent_decisions": len(recent_decisions),
            "recent_patterns": len(recent_patterns),
            "recent_handoffs": len(recent_handoffs),
            "recent_snapshots": len(recent_snapshots),
            "last_activity": memory.updated_at.isoformat() if memory.updated_at else None
        }