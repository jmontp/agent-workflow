#!/usr/bin/env python3
"""
Context Manager v1 - The nervous system of the agent-workflow.
Tracks all context, learns patterns, and coordinates documentation.
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Set
from enum import Enum
from pathlib import Path
import json
import uuid
import os
from collections import Counter


# Schema definitions
class ContextType(Enum):
    """Types of context entries."""
    DEVELOPMENT = "development"
    PLANNING = "planning"
    EXECUTION = "execution"
    DOCUMENTATION = "documentation"
    CODE_CHANGE = "code_change"
    ERROR = "error"
    DECISION = "decision"


@dataclass
class Context:
    """Core context structure for all system interactions."""
    
    # Required fields
    id: str                    # UUID
    type: ContextType          # Enum
    source: str                # Agent or human identifier
    timestamp: datetime        # Creation time
    data: Dict[str, Any]      # Actual content
    
    # Optional metadata
    project_id: str = "default"  # For future multi-project support
    metadata: Dict[str, Any] = field(default_factory=dict)
    relationships: List[str] = field(default_factory=list)  # Related context IDs
    tags: List[str] = field(default_factory=list)          # Searchable tags
    ttl: Optional[int] = None                               # Time-to-live in seconds
    
    # Compliance fields
    requires_audit: bool = True
    sensitivity_level: str = "internal"  # internal|confidential|public
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            'id': self.id,
            'type': self.type.value,
            'source': self.source,
            'timestamp': self.timestamp.isoformat(),
            'data': self.data,
            'project_id': self.project_id,
            'metadata': self.metadata,
            'relationships': self.relationships,
            'tags': self.tags,
            'ttl': self.ttl,
            'requires_audit': self.requires_audit,
            'sensitivity_level': self.sensitivity_level
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Context':
        """Create Context from dictionary."""
        data['type'] = ContextType(data['type'])
        data['timestamp'] = datetime.fromisoformat(data['timestamp'])
        return cls(**data)


@dataclass
class DocMetadata:
    """Lightweight metadata for existing documentation files."""
    
    # File reference
    path: str                       # Path to actual .md file
    doc_type: str                   # Inferred type (readme, api_spec, etc.)
    last_analyzed: datetime         # When we last analyzed this doc
    
    # Intelligence data
    quality_scores: Dict[str, float] = field(default_factory=dict)
    staleness_indicators: List[str] = field(default_factory=list)
    
    # Relationships
    linked_contexts: List[str] = field(default_factory=list)    # Related events
    linked_docs: List[str] = field(default_factory=list)        # Related docs
    dependencies: Dict[str, List[str]] = field(default_factory=dict)  # Code dependencies
    
    # Update tracking
    pending_updates: List[Dict[str, Any]] = field(default_factory=list)
    
    def needs_update(self) -> bool:
        """Check if document likely needs updating."""
        return len(self.staleness_indicators) > 0 or len(self.pending_updates) > 0


class ContextManager:
    """Central context orchestration for agent-workflow system."""
    
    def __init__(self, base_dir: str = "./context_store", project_id: str = "default"):
        """Initialize Context Manager with storage directory."""
        self.base_dir = Path(base_dir)
        self.project_id = project_id
        self.project_dir = self.base_dir / project_id
        
        # In-memory caches
        self.contexts: Dict[str, Context] = {}
        self.doc_metadata: Dict[str, DocMetadata] = {}
        self.patterns: Dict[str, int] = {}
        self.audit_log: List[Dict[str, Any]] = []
        
        # Initialize storage
        self._init_storage()
        self._load_existing_data()
    
    def _init_storage(self):
        """Initialize directory structure."""
        # Context storage
        (self.project_dir / "contexts" / "active").mkdir(parents=True, exist_ok=True)
        (self.project_dir / "contexts" / "archive").mkdir(parents=True, exist_ok=True)
        (self.project_dir / "contexts" / "indices").mkdir(parents=True, exist_ok=True)
        
        # Doc metadata storage
        (self.project_dir / "doc_metadata" / "metadata").mkdir(parents=True, exist_ok=True)
        (self.project_dir / "doc_metadata" / "patterns").mkdir(parents=True, exist_ok=True)
        (self.project_dir / "doc_metadata" / "indices").mkdir(parents=True, exist_ok=True)
    
    def _load_existing_data(self):
        """Load existing contexts and metadata from storage."""
        # For v1, just load active contexts
        active_dir = self.project_dir / "contexts" / "active"
        for date_dir in active_dir.glob("*"):
            if date_dir.is_dir():
                for context_file in date_dir.glob("*.json"):
                    try:
                        with open(context_file, 'r') as f:
                            data = json.load(f)
                            context = Context.from_dict(data)
                            self.contexts[context.id] = context
                    except Exception as e:
                        print(f"Error loading context {context_file}: {e}")
    
    # Core context operations
    def add_context(self, context: Context) -> str:
        """Add new context to the system."""
        # Add to memory
        self.contexts[context.id] = context
        
        # Persist to disk
        date_str = context.timestamp.strftime("%Y-%m-%d")
        context_dir = self.project_dir / "contexts" / "active" / date_str
        context_dir.mkdir(parents=True, exist_ok=True)
        
        context_file = context_dir / f"{context.id}.json"
        with open(context_file, 'w') as f:
            json.dump(context.to_dict(), f, indent=2)
        
        # Add audit entry
        self._audit_operation("add_context", context.id, True)
        
        # Trigger pattern detection (async in production)
        self._detect_patterns([context])
        
        return context.id
    
    def get_context(self, context_id: str) -> Optional[Context]:
        """Retrieve context by ID."""
        return self.contexts.get(context_id)
    
    def query_contexts(self, 
                      query: str = None,
                      context_type: ContextType = None,
                      source: str = None,
                      since: datetime = None,
                      limit: int = 10) -> List[Context]:
        """Search contexts with filters."""
        results = list(self.contexts.values())
        
        # Apply filters
        if context_type:
            results = [c for c in results if c.type == context_type]
        if source:
            results = [c for c in results if c.source == source]
        if since:
            results = [c for c in results if c.timestamp >= since]
        if query:
            # Simple text search in data
            query_lower = query.lower()
            results = [c for c in results if 
                      query_lower in str(c.data).lower() or
                      query_lower in ' '.join(c.tags).lower()]
        
        # Sort by timestamp (newest first) and limit
        results.sort(key=lambda c: c.timestamp, reverse=True)
        return results[:limit]
    
    # Bootstrap features
    def log_decision(self, decision: str, reasoning: str) -> str:
        """Track development decisions for self-improvement."""
        context = Context(
            id=str(uuid.uuid4()),
            type=ContextType.DECISION,
            source="human",
            timestamp=datetime.now(),
            project_id=self.project_id,
            data={
                "decision": decision,
                "reasoning": reasoning
            },
            tags=["bootstrap", "decision"],
            metadata={
                "tokens": len(decision + reasoning) // 4  # Rough estimate
            }
        )
        return self.add_context(context)
    
    def log_error(self, error: str, context_info: Dict[str, Any] = None) -> str:
        """Log errors for pattern analysis."""
        context = Context(
            id=str(uuid.uuid4()),
            type=ContextType.ERROR,
            source="system",
            timestamp=datetime.now(),
            project_id=self.project_id,
            data={
                "error": error,
                "context": context_info or {}
            },
            tags=["error", "pattern-source"]
        )
        return self.add_context(context)
    
    def suggest_next_task(self) -> List[Dict[str, Any]]:
        """Generate task suggestions based on patterns."""
        suggestions = []
        
        # Analyze recent contexts
        recent = self.query_contexts(
            since=datetime.now() - timedelta(hours=24),
            limit=50
        )
        
        # Count context types
        type_counts = Counter(c.type for c in recent)
        
        # Simple heuristics for v1
        if type_counts[ContextType.ERROR] > 3:
            suggestions.append({
                "task": "Add error handling",
                "reason": f"Detected {type_counts[ContextType.ERROR]} errors in last 24h",
                "confidence": 0.8
            })
        
        if type_counts[ContextType.DECISION] > 5:
            suggestions.append({
                "task": "Document decisions in CLAUDE.md",
                "reason": "Multiple decisions made, should be documented",
                "confidence": 0.7
            })
        
        # Check for missing persistence
        if len(self.contexts) > 20 and not self._has_persistence():
            suggestions.append({
                "task": "Implement persistence",
                "reason": "Growing context count needs reliable storage",
                "confidence": 0.9
            })
        
        return suggestions
    
    # Pattern detection
    def _detect_patterns(self, contexts: List[Context]):
        """Simple pattern detection for v1."""
        for context in contexts:
            # Extract features
            if context.type == ContextType.DECISION:
                # Track decision keywords
                decision = context.data.get('decision', '').lower()
                for word in decision.split():
                    if len(word) > 4:  # Skip short words
                        self.patterns[f"decision_word:{word}"] = \
                            self.patterns.get(f"decision_word:{word}", 0) + 1
            
            elif context.type == ContextType.ERROR:
                # Track error patterns
                error = context.data.get('error', '')
                error_type = type(error).__name__ if not isinstance(error, str) else 'string'
                self.patterns[f"error_type:{error_type}"] = \
                    self.patterns.get(f"error_type:{error_type}", 0) + 1
    
    def get_patterns(self, min_occurrences: int = 3) -> Dict[str, int]:
        """Get significant patterns."""
        return {k: v for k, v in self.patterns.items() if v >= min_occurrences}
    
    # Utility methods
    def _audit_operation(self, operation: str, target: str, success: bool):
        """Add audit log entry."""
        self.audit_log.append({
            "timestamp": datetime.now().isoformat(),
            "operation": operation,
            "target": target,
            "success": success,
            "project_id": self.project_id
        })
    
    def _has_persistence(self) -> bool:
        """Check if persistence is properly configured."""
        return (self.project_dir / "contexts" / "active").exists()
    
    def get_stats(self) -> Dict[str, Any]:
        """Get current statistics."""
        type_counts = Counter(c.type for c in self.contexts.values())
        return {
            "total_contexts": len(self.contexts),
            "by_type": {t.value: type_counts[t] for t in ContextType},
            "patterns_detected": len(self.patterns),
            "significant_patterns": len(self.get_patterns()),
            "audit_entries": len(self.audit_log),
            "project_id": self.project_id
        }