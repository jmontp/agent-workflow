# Context Manager v1 Implementation Plan

## Overview

Building a minimal but powerful Context Manager that can bootstrap its own development and serve as the foundation for agent orchestration. Special emphasis on documentation and audit trails for future regulatory compliance.

## Week 1: Core Foundation

### Day 1-2: Basic Structure
```python
# context_manager.py (~150 lines max)
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List, Optional, Any
import json
import uuid

@dataclass
class Context:
    id: str
    type: str  # development|planning|execution|documentation
    source: str  # human|agent|system
    timestamp: datetime
    data: Dict[str, Any]
    metadata: Dict[str, Any]
    
    def to_json(self):
        """Serialize for storage and audit"""
        pass

class ContextManager:
    def __init__(self):
        self.contexts: Dict[str, Context] = {}
        self.history: List[Context] = []
        self.patterns: Dict[str, int] = {}
        self.audit_log: List[Dict] = []
        
    # Core Features for Bootstrap
    def log_decision(self, decision: str, reasoning: str) -> str:
        """Track development decisions for self-improvement"""
        context = Context(
            id=str(uuid.uuid4()),
            type="development",
            source="human",
            timestamp=datetime.now(),
            data={
                "decision": decision,
                "reasoning": reasoning
            },
            metadata={
                "tokens": len(decision + reasoning) // 4
            }
        )
        return self.add_context(context)
    
    def add_context(self, context: Context) -> str:
        """Add context with audit trail"""
        self.contexts[context.id] = context
        self.history.append(context)
        self._audit_transaction("add", context)
        self._detect_patterns(context)
        return context.id
    
    def get_context(self, context_id: str) -> Optional[Context]:
        """Retrieve context by ID"""
        return self.contexts.get(context_id)
    
    def suggest_next_task(self) -> List[str]:
        """Use patterns to suggest development tasks"""
        # Simple pattern matching on recent decisions
        recent = self.history[-10:]
        suggestions = []
        
        # Example pattern detection
        if self._count_type(recent, "development") > 5:
            suggestions.append("Consider adding persistence - many decisions to track")
        
        if self._count_mentions(recent, "error") > 2:
            suggestions.append("Add error handling based on recent issues")
            
        return suggestions
    
    def _detect_patterns(self, context: Context):
        """Learn from context usage"""
        # Track common words/concepts
        text = json.dumps(context.data)
        for word in text.split():
            if len(word) > 4:  # Skip small words
                self.patterns[word] = self.patterns.get(word, 0) + 1
    
    def _audit_transaction(self, action: str, context: Context):
        """Audit trail for compliance"""
        self.audit_log.append({
            "timestamp": datetime.now().isoformat(),
            "action": action,
            "context_id": context.id,
            "context_type": context.type,
            "source": context.source
        })
```

### Day 3-4: Integration with Flask App
```python
# Enhanced app.py integration
from context_manager import ContextManager

cm = ContextManager()

@app.route('/api/context/decision', methods=['POST'])
def log_decision():
    """Log development decision"""
    data = request.json
    context_id = cm.log_decision(
        data['decision'],
        data['reasoning']
    )
    return jsonify({"context_id": context_id})

@app.route('/api/context/suggest')
def suggest_tasks():
    """Get task suggestions"""
    suggestions = cm.suggest_next_task()
    return jsonify({"suggestions": suggestions})

@app.route('/api/context/audit')
def get_audit_log():
    """Compliance-friendly audit trail"""
    return jsonify({"audit_log": cm.audit_log})

# Add to state machine transitions
@socketio.on('command')
def handle_command(data):
    command = data.get('command', '').lower()
    
    # Log the command as context
    cm.add_context(Context(
        id=str(uuid.uuid4()),
        type="execution",
        source="human",
        timestamp=datetime.now(),
        data={"command": command},
        metadata={"state": workflow_sm.current_state.value}
    ))
    
    # ... existing command handling
```

### Day 5: Basic Persistence
```python
# Simple file-based persistence for bootstrap phase
import pickle

class ContextManager:
    def save_state(self, filepath="context_state.pkl"):
        """Save state for development continuity"""
        state = {
            "contexts": self.contexts,
            "history": self.history,
            "patterns": self.patterns,
            "audit_log": self.audit_log
        }
        with open(filepath, 'wb') as f:
            pickle.dump(state, f)
    
    def load_state(self, filepath="context_state.pkl"):
        """Load previous state"""
        try:
            with open(filepath, 'rb') as f:
                state = pickle.load(f)
                self.contexts = state["contexts"]
                self.history = state["history"]
                self.patterns = state["patterns"]
                self.audit_log = state["audit_log"]
        except FileNotFoundError:
            pass  # Fresh start
```

## Week 1 Deliverables

### Bootstrap Features ✓
- [x] Log development decisions
- [x] Track patterns in usage
- [x] Suggest next tasks
- [x] Basic persistence
- [x] Audit trail (compliance foundation)

### Integration ✓
- [x] REST API endpoints
- [x] WebSocket integration
- [x] State machine context tracking

### Documentation Focus ✓
- [x] Every decision logged with reasoning
- [x] Audit trail for all context operations
- [x] Pattern detection for self-improvement

## Usage During Development

### Example: Building Context Manager
```python
# Day 1
cm.log_decision(
    "Starting with simple dict storage",
    "Need quick iteration, will add Redis later"
)

# Day 2
cm.log_decision(
    "Adding audit trail early",
    "Medical device compliance requires full traceability"
)

# Day 3
suggestions = cm.suggest_next_task()
# Returns: ["Add persistence - many decisions to track"]

# Day 4
cm.log_decision(
    "Implementing file-based persistence",
    "Based on suggestion, need to maintain state between sessions"
)
```

## Week 2-3 Enhancements

### Only After Bootstrap Success:
1. Redis integration for working memory
2. PostgreSQL for historical storage
3. Advanced pattern recognition
4. Context scoring and pruning
5. Integration with Documentation Agent

## Success Criteria

### Week 1 Complete When:
1. Can track its own development decisions
2. Suggests useful next steps based on patterns
3. Maintains audit trail for all operations
4. Persists state between sessions
5. Integrates with existing Flask app

### Ready for Agents When:
1. Stable context flow established
2. Pattern detection improving suggestions
3. No context explosion (staying under limits)
4. Clean API for agent integration
5. Documentation patterns captured

## Key Design Decisions

1. **Start Ultra-Simple**: <200 lines, basic dict storage
2. **Documentation First**: Audit trail from day one
3. **Self-Bootstrapping**: Use it to build itself
4. **Compliance Ready**: FDA traceability built-in
5. **Pattern Learning**: Simple but effective

## Next Steps After V1

1. Use patterns learned to design Documentation Agent
2. Enhance storage with Redis/PostgreSQL  
3. Add context scoring and pruning
4. Implement control loop from Context Engineering
5. Build agent communication protocols

This plan gives us a working Context Manager in one week that genuinely helps its own development while laying the foundation for a compliant, scalable system.