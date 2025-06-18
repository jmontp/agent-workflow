"""
Context Management System Data Models

Data structures for context requests, agent context, token management,
agent memory, and other context-related entities.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Union
from enum import Enum
from datetime import datetime
import json
import uuid

# Import TDD models for type hints
try:
    from ..tdd_models import TDDState, TDDTask, TDDCycle
except ImportError:
    from tdd_models import TDDState, TDDTask, TDDCycle


class ContextType(Enum):
    """Types of context content"""
    CORE_TASK = "core_task"
    HISTORICAL = "historical"
    DEPENDENCIES = "dependencies"
    AGENT_MEMORY = "agent_memory"
    METADATA = "metadata"
    COMPRESSED = "compressed"


class CompressionLevel(Enum):
    """Levels of context compression"""
    NONE = "none"
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"
    EXTREME = "extreme"


class FileType(Enum):
    """Types of files for context processing"""
    PYTHON = "python"
    TEST = "test"
    MARKDOWN = "markdown"
    JSON = "json"
    YAML = "yaml"
    CONFIG = "config"
    OTHER = "other"


@dataclass
class RelevanceScore:
    """Relevance scoring for files and content"""
    file_path: str
    total_score: float
    direct_mention: float = 0.0
    dependency_score: float = 0.0
    historical_score: float = 0.0
    semantic_score: float = 0.0
    tdd_phase_score: float = 0.0
    reasons: List[str] = field(default_factory=list)
    
    def __post_init__(self):
        # Ensure score is between 0 and 1
        self.total_score = max(0.0, min(1.0, self.total_score))


@dataclass
class TokenBudget:
    """Token budget allocation for context components"""
    total_budget: int
    core_task: int = 0
    historical: int = 0
    dependencies: int = 0
    agent_memory: int = 0
    buffer: int = 0
    
    def __post_init__(self):
        """Validate budget allocation"""
        allocated = self.core_task + self.historical + self.dependencies + self.agent_memory + self.buffer
        if allocated > self.total_budget:
            raise ValueError(f"Budget allocation ({allocated}) exceeds total budget ({self.total_budget})")
    
    def get_allocation_dict(self) -> Dict[str, int]:
        """Get budget allocation as dictionary"""
        return {
            "core_task": self.core_task,
            "historical": self.historical,
            "dependencies": self.dependencies,
            "agent_memory": self.agent_memory,
            "buffer": self.buffer
        }
    
    def get_utilization_rate(self) -> float:
        """Get budget utilization rate"""
        allocated = self.core_task + self.historical + self.dependencies + self.agent_memory + self.buffer
        return allocated / self.total_budget if self.total_budget > 0 else 0.0


@dataclass
class TokenUsage:
    """Actual token usage tracking"""
    context_id: str
    total_used: int
    core_task_used: int = 0
    historical_used: int = 0
    dependencies_used: int = 0
    agent_memory_used: int = 0
    buffer_used: int = 0
    compression_ratio: float = 1.0
    timestamp: datetime = field(default_factory=datetime.utcnow)
    
    def get_usage_dict(self) -> Dict[str, int]:
        """Get usage as dictionary"""
        return {
            "core_task_used": self.core_task_used,
            "historical_used": self.historical_used,
            "dependencies_used": self.dependencies_used,
            "agent_memory_used": self.agent_memory_used,
            "buffer_used": self.buffer_used
        }
    
    def get_efficiency_score(self, budget: TokenBudget) -> float:
        """Calculate token usage efficiency"""
        if budget.total_budget == 0:
            return 0.0
        return (self.total_used / budget.total_budget) if budget.total_budget > 0 else 0.0


@dataclass
class Decision:
    """Agent decision tracking"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    agent_type: str = ""
    description: str = ""
    rationale: str = ""
    context_snapshot: str = ""
    outcome: str = ""
    confidence: float = 0.0
    timestamp: datetime = field(default_factory=datetime.utcnow)
    artifacts: Dict[str, str] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            "id": self.id,
            "agent_type": self.agent_type,
            "description": self.description,
            "rationale": self.rationale,
            "context_snapshot": self.context_snapshot,
            "outcome": self.outcome,
            "confidence": self.confidence,
            "timestamp": self.timestamp.isoformat(),
            "artifacts": self.artifacts
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Decision':
        """Create from dictionary"""
        data = data.copy()
        if 'timestamp' in data and isinstance(data['timestamp'], str):
            data['timestamp'] = datetime.fromisoformat(data['timestamp'])
        return cls(**data)


@dataclass
class PhaseHandoff:
    """TDD phase handoff tracking"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    from_phase: TDDState = None
    to_phase: TDDState = None
    from_agent: str = ""
    to_agent: str = ""
    artifacts: Dict[str, str] = field(default_factory=dict)
    context_summary: str = ""
    handoff_notes: str = ""
    timestamp: datetime = field(default_factory=datetime.utcnow)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            "id": self.id,
            "from_phase": self.from_phase.value if self.from_phase else None,
            "to_phase": self.to_phase.value if self.to_phase else None,
            "from_agent": self.from_agent,
            "to_agent": self.to_agent,
            "artifacts": self.artifacts,
            "context_summary": self.context_summary,
            "handoff_notes": self.handoff_notes,
            "timestamp": self.timestamp.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'PhaseHandoff':
        """Create from dictionary"""
        data = data.copy()
        if 'timestamp' in data and isinstance(data['timestamp'], str):
            data['timestamp'] = datetime.fromisoformat(data['timestamp'])
        if 'from_phase' in data and data['from_phase']:
            data['from_phase'] = TDDState(data['from_phase'])
        if 'to_phase' in data and data['to_phase']:
            data['to_phase'] = TDDState(data['to_phase'])
        return cls(**data)


@dataclass
class Pattern:
    """Learned pattern tracking"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    pattern_type: str = ""
    description: str = ""
    context_conditions: List[str] = field(default_factory=list)
    success_rate: float = 0.0
    usage_count: int = 0
    examples: List[str] = field(default_factory=list)
    timestamp: datetime = field(default_factory=datetime.utcnow)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            "id": self.id,
            "pattern_type": self.pattern_type,
            "description": self.description,
            "context_conditions": self.context_conditions,
            "success_rate": self.success_rate,
            "usage_count": self.usage_count,
            "examples": self.examples,
            "timestamp": self.timestamp.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Pattern':
        """Create from dictionary"""
        data = data.copy()
        if 'timestamp' in data and isinstance(data['timestamp'], str):
            data['timestamp'] = datetime.fromisoformat(data['timestamp'])
        return cls(**data)


@dataclass
class ContextSnapshot:
    """Snapshot of context at a specific point in time"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    agent_type: str = ""
    story_id: str = ""
    tdd_phase: Optional[TDDState] = None
    context_summary: str = ""
    file_list: List[str] = field(default_factory=list)
    token_usage: Optional[TokenUsage] = None
    timestamp: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            "id": self.id,
            "agent_type": self.agent_type,
            "story_id": self.story_id,
            "tdd_phase": self.tdd_phase.value if self.tdd_phase else None,
            "context_summary": self.context_summary,
            "file_list": self.file_list,
            "token_usage": self.token_usage.get_usage_dict() if self.token_usage else None,
            "timestamp": self.timestamp.isoformat(),
            "metadata": self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ContextSnapshot':
        """Create from dictionary"""
        data = data.copy()
        if 'timestamp' in data and isinstance(data['timestamp'], str):
            data['timestamp'] = datetime.fromisoformat(data['timestamp'])
        if 'tdd_phase' in data and data['tdd_phase']:
            data['tdd_phase'] = TDDState(data['tdd_phase'])
        # Note: token_usage reconstruction would need TokenUsage.from_dict if needed
        if 'token_usage' in data and data['token_usage']:
            data['token_usage'] = None  # Simplified for now
        return cls(**data)


@dataclass
class AgentMemory:
    """Agent memory storage"""
    agent_type: str
    story_id: str
    decisions: List[Decision] = field(default_factory=list)
    artifacts: Dict[str, str] = field(default_factory=dict)
    learned_patterns: List[Pattern] = field(default_factory=list)
    context_history: List[ContextSnapshot] = field(default_factory=list)
    phase_handoffs: List[PhaseHandoff] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    
    def add_decision(self, decision: Decision) -> None:
        """Add a decision to memory"""
        self.decisions.append(decision)
        self.updated_at = datetime.utcnow()
    
    def add_pattern(self, pattern: Pattern) -> None:
        """Add a learned pattern to memory"""
        self.learned_patterns.append(pattern)
        self.updated_at = datetime.utcnow()
    
    def add_context_snapshot(self, snapshot: ContextSnapshot) -> None:
        """Add a context snapshot to history"""
        self.context_history.append(snapshot)
        # Keep only last 100 snapshots to manage memory
        if len(self.context_history) > 100:
            self.context_history = self.context_history[-100:]
        self.updated_at = datetime.utcnow()
    
    def add_phase_handoff(self, handoff: PhaseHandoff) -> None:
        """Add a phase handoff record"""
        self.phase_handoffs.append(handoff)
        self.updated_at = datetime.utcnow()
    
    def get_recent_decisions(self, limit: int = 10) -> List[Decision]:
        """Get recent decisions"""
        return sorted(self.decisions, key=lambda d: d.timestamp, reverse=True)[:limit]
    
    def get_patterns_by_type(self, pattern_type: str) -> List[Pattern]:
        """Get patterns by type"""
        return [p for p in self.learned_patterns if p.pattern_type == pattern_type]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            "agent_type": self.agent_type,
            "story_id": self.story_id,
            "decisions": [d.to_dict() for d in self.decisions],
            "artifacts": self.artifacts,
            "learned_patterns": [p.to_dict() for p in self.learned_patterns],
            "context_history": [c.to_dict() for c in self.context_history],
            "phase_handoffs": [h.to_dict() for h in self.phase_handoffs],
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AgentMemory':
        """Create from dictionary"""
        data = data.copy()
        
        # Convert timestamps
        for field_name in ['created_at', 'updated_at']:
            if field_name in data and isinstance(data[field_name], str):
                data[field_name] = datetime.fromisoformat(data[field_name])
        
        # Convert nested objects
        if 'decisions' in data:
            data['decisions'] = [Decision.from_dict(d) for d in data['decisions']]
        if 'learned_patterns' in data:
            data['learned_patterns'] = [Pattern.from_dict(p) for p in data['learned_patterns']]
        if 'context_history' in data:
            data['context_history'] = [ContextSnapshot.from_dict(c) for c in data['context_history']]
        if 'phase_handoffs' in data:
            data['phase_handoffs'] = [PhaseHandoff.from_dict(h) for h in data['phase_handoffs']]
        
        return cls(**data)


@dataclass
class ContextRequest:
    """Request for context preparation"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    agent_type: str = ""
    story_id: str = ""
    task: Optional[Union[TDDTask, Dict[str, Any]]] = None
    max_tokens: int = 200000  # Default Claude Code limit
    compression_level: CompressionLevel = CompressionLevel.MODERATE
    include_history: bool = True
    include_dependencies: bool = True
    include_agent_memory: bool = True
    focus_areas: List[str] = field(default_factory=list)
    exclude_patterns: List[str] = field(default_factory=list)
    timestamp: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        task_dict = None
        if self.task:
            if hasattr(self.task, 'to_dict'):
                task_dict = self.task.to_dict()
            elif isinstance(self.task, dict):
                task_dict = self.task
        
        return {
            "id": self.id,
            "agent_type": self.agent_type,
            "story_id": self.story_id,
            "task": task_dict,
            "max_tokens": self.max_tokens,
            "compression_level": self.compression_level.value,
            "include_history": self.include_history,
            "include_dependencies": self.include_dependencies,
            "include_agent_memory": self.include_agent_memory,
            "focus_areas": self.focus_areas,
            "exclude_patterns": self.exclude_patterns,
            "timestamp": self.timestamp.isoformat(),
            "metadata": self.metadata
        }


@dataclass
class AgentContext:
    """Prepared context for agent execution"""
    request_id: str
    agent_type: str
    story_id: str
    core_context: str = ""
    dependencies: str = ""
    historical_context: str = ""
    agent_memory: str = ""
    metadata: str = ""
    token_budget: Optional[TokenBudget] = None
    token_usage: Optional[TokenUsage] = None
    relevance_scores: List[RelevanceScore] = field(default_factory=list)
    file_contents: Dict[str, str] = field(default_factory=dict)
    compression_applied: bool = False
    compression_level: CompressionLevel = CompressionLevel.NONE
    preparation_time: float = 0.0
    cache_hit: bool = False
    tdd_phase: Optional[TDDState] = None
    timestamp: datetime = field(default_factory=datetime.utcnow)
    
    def get_total_content(self) -> str:
        """Get all context content combined"""
        content_parts = []
        
        if self.core_context:
            content_parts.append("## Core Task Context")
            content_parts.append(self.core_context)
        
        if self.dependencies:
            content_parts.append("## Dependencies")
            content_parts.append(self.dependencies)
        
        if self.historical_context:
            content_parts.append("## Historical Context")
            content_parts.append(self.historical_context)
        
        if self.agent_memory:
            content_parts.append("## Agent Memory")
            content_parts.append(self.agent_memory)
        
        if self.metadata:
            content_parts.append("## Metadata")
            content_parts.append(self.metadata)
        
        return "\n\n".join(content_parts)
    
    def get_total_token_estimate(self) -> int:
        """Estimate total tokens in context"""
        # Simple estimation: ~4 characters per token
        total_content = self.get_total_content()
        return len(total_content) // 4
    
    def get_context_quality_score(self) -> float:
        """Calculate context quality score based on relevance"""
        if not self.relevance_scores:
            return 0.0
        
        total_score = sum(score.total_score for score in self.relevance_scores)
        return total_score / len(self.relevance_scores)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            "request_id": self.request_id,
            "agent_type": self.agent_type,
            "story_id": self.story_id,
            "core_context": self.core_context,
            "dependencies": self.dependencies,
            "historical_context": self.historical_context,
            "agent_memory": self.agent_memory,
            "metadata": self.metadata,
            "token_budget": self.token_budget.get_allocation_dict() if self.token_budget else None,
            "token_usage": self.token_usage.get_usage_dict() if self.token_usage else None,
            "relevance_scores": [
                {
                    "file_path": score.file_path,
                    "total_score": score.total_score,
                    "direct_mention": score.direct_mention,
                    "dependency_score": score.dependency_score,
                    "historical_score": score.historical_score,
                    "semantic_score": score.semantic_score,
                    "tdd_phase_score": score.tdd_phase_score,
                    "reasons": score.reasons
                }
                for score in self.relevance_scores
            ],
            "compression_applied": self.compression_applied,
            "compression_level": self.compression_level.value,
            "preparation_time": self.preparation_time,
            "cache_hit": self.cache_hit,
            "tdd_phase": self.tdd_phase.value if self.tdd_phase else None,
            "timestamp": self.timestamp.isoformat()
        }