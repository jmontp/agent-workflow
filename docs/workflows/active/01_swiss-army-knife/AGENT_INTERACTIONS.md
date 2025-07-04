# Swiss Army Knife Agent Interactions

This document specifies how agents communicate during the Swiss Army Knife workflow execution.

## Agent Communication Overview

The Swiss Army Knife workflow involves three participants:
1. **Human** - Initiates requests and reviews results
2. **Swiss Army Agent** - Executes all tasks
3. **Context Manager** - Provides memory and patterns

## Message Formats

### Base Message Structure

All inter-agent messages follow this format:

```python
{
    "message_id": "uuid-v4",
    "timestamp": "2024-01-20T10:30:00Z",
    "workflow": "swiss-army-knife",
    "workflow_version": "1.0",
    "state": "CURRENT_STATE",
    "sender": {
        "type": "agent|human|system",
        "id": "sender_identifier"
    },
    "recipient": {
        "type": "agent|human|system", 
        "id": "recipient_identifier"
    },
    "message_type": "request|response|update|error",
    "payload": {
        # Message-specific content
    },
    "context_refs": ["context_id_1", "context_id_2"],
    "correlation_id": "request_uuid"
}
```

## State-Specific Interactions

### 1. IDLE → REQUEST_RECEIVED

**Human → Swiss Army Agent**
```python
{
    "message_type": "request",
    "payload": {
        "action": "new_task",
        "task_description": "Create a function to validate email addresses",
        "parameters": {
            "language": "python",
            "style": "defensive",
            "include_tests": true
        },
        "urgency": "normal",
        "expected_duration": "5-10 minutes"
    }
}
```

**Swiss Army Agent → Context Manager**
```python
{
    "message_type": "request",
    "payload": {
        "action": "log_request",
        "request_id": "req_12345",
        "content": "Create a function to validate email addresses",
        "metadata": {
            "type": "code_generation",
            "complexity": "simple",
            "estimated_tokens": 500
        }
    }
}
```

### 2. REQUEST_RECEIVED → CONTEXT_SEARCH

**Swiss Army Agent → Context Manager**
```python
{
    "message_type": "request",
    "payload": {
        "action": "search_context",
        "queries": [
            "email validation function python",
            "regex email pattern",
            "email validation best practices"
        ],
        "filters": {
            "type": ["code", "pattern", "documentation"],
            "success_rate": ">0.8",
            "recency": "30d",
            "language": "python"
        },
        "max_results": 10,
        "timeout_ms": 5000
    }
}
```

**Context Manager → Swiss Army Agent**
```python
{
    "message_type": "response",
    "payload": {
        "action": "search_results",
        "results": [
            {
                "context_id": "ctx_789",
                "type": "code",
                "relevance_score": 0.95,
                "summary": "Email validation using regex with edge cases",
                "content": "import re\ndef validate_email(email):...",
                "metadata": {
                    "success_rate": 0.92,
                    "usage_count": 45,
                    "last_used": "2024-01-19"
                }
            },
            # ... more results
        ],
        "search_duration_ms": 2150,
        "total_matches": 23
    }
}
```

### 3. CONTEXT_SEARCH → EXECUTING

**Swiss Army Agent → Context Manager** (Progress Update)
```python
{
    "message_type": "update",
    "payload": {
        "action": "execution_progress",
        "request_id": "req_12345",
        "status": "in_progress",
        "progress_percentage": 30,
        "current_activity": "Applying email validation pattern",
        "patterns_used": ["ctx_789", "ctx_790"]
    }
}
```

### 4. EXECUTING → CONTEXT_UPDATE

**Swiss Army Agent → Context Manager** (Store Result)
```python
{
    "message_type": "request",
    "payload": {
        "action": "store_result",
        "request_id": "req_12345",
        "result": {
            "type": "code_generation",
            "success": true,
            "output": {
                "code": "def validate_email(email: str) -> bool:\n    ...",
                "tests": "def test_validate_email():\n    ...",
                "documentation": "Validates email addresses..."
            },
            "execution_metrics": {
                "duration_ms": 8500,
                "tokens_used": 1200,
                "patterns_applied": 3,
                "confidence": 0.88
            },
            "patterns_discovered": [
                {
                    "type": "edge_case",
                    "description": "Handle plus addressing",
                    "example": "user+tag@example.com"
                }
            ]
        },
        "context_links": ["ctx_789", "ctx_790"],
        "tags": ["email", "validation", "regex", "python"]
    }
}
```

**Context Manager → Swiss Army Agent**
```python
{
    "message_type": "response",
    "payload": {
        "action": "storage_confirmation",
        "context_id": "ctx_12345",
        "storage_status": "success",
        "indexes_updated": ["by_type", "by_tag", "by_pattern"],
        "pattern_analysis": {
            "new_patterns": 1,
            "confidence_updates": 2
        }
    }
}
```

### 5. CONTEXT_UPDATE → HUMAN_REVIEW

**Swiss Army Agent → Human** (Present Results)
```python
{
    "message_type": "response",
    "payload": {
        "action": "task_complete",
        "request_id": "req_12345",
        "result": {
            "success": true,
            "output_type": "code",
            "content": {
                "code": "def validate_email(email: str) -> bool:\n    ...",
                "tests": "def test_validate_email():\n    ...",
                "documentation": "..."
            },
            "metadata": {
                "execution_time": "8.5 seconds",
                "confidence": "88%",
                "patterns_used": ["Email regex pattern", "Defensive programming"],
                "context_relevance": "High"
            },
            "suggestions": [
                "Consider adding internationalized domain support",
                "Could cache compiled regex for performance"
            ]
        },
        "review_options": ["approve", "reject", "modify"]
    }
}
```

### 6. HUMAN_REVIEW → IDLE

**Human → Swiss Army Agent** (Review Decision)
```python
{
    "message_type": "request",
    "payload": {
        "action": "review_decision",
        "request_id": "req_12345",
        "decision": "approve",
        "feedback": {
            "satisfaction": "high",
            "comments": "Good edge case handling",
            "suggestions": "Add type hints to test functions"
        }
    }
}
```

**Swiss Army Agent → Context Manager** (Log Decision)
```python
{
    "message_type": "request",
    "payload": {
        "action": "log_review",
        "request_id": "req_12345",
        "context_id": "ctx_12345",
        "review_result": {
            "decision": "approve",
            "satisfaction": "high",
            "feedback": "Good edge case handling",
            "review_duration_ms": 25000
        },
        "pattern_feedback": {
            "ctx_789": {"effectiveness": "high"},
            "ctx_790": {"effectiveness": "medium"}
        }
    }
}
```

## Error Message Format

```python
{
    "message_type": "error",
    "payload": {
        "error_code": "CONTEXT_SEARCH_TIMEOUT",
        "error_message": "Context search exceeded 5s timeout",
        "severity": "warning|error|critical",
        "recoverable": true,
        "suggested_action": "proceed_without_context",
        "error_context": {
            "state": "CONTEXT_SEARCH",
            "duration_ms": 5001,
            "partial_results": 3
        }
    }
}
```

## Async Communication Patterns

### Fire-and-Forget Updates
Progress updates and non-critical logs:
```python
{
    "message_type": "update",
    "require_ack": false,
    "payload": {
        "action": "progress",
        "message": "Analyzing patterns..."
    }
}
```

### Request-Response with Timeout
Critical operations requiring confirmation:
```python
{
    "message_type": "request",
    "require_ack": true,
    "timeout_ms": 5000,
    "retry_policy": {
        "max_retries": 3,
        "backoff_ms": [100, 500, 1000]
    },
    "payload": {...}
}
```

## Message Queue Behavior

### Priority Levels
1. **Critical**: Error messages, abort commands
2. **High**: State transitions, search requests
3. **Normal**: Progress updates, logs
4. **Low**: Metrics, analytics

### Delivery Guarantees
- **State Transitions**: At-least-once delivery
- **Context Storage**: Exactly-once with idempotency
- **Progress Updates**: At-most-once (can be dropped)
- **Error Messages**: At-least-once with deduplication

## WebSocket Events

For real-time UI updates:

```javascript
// Server → Client
{
    "event": "state_changed",
    "data": {
        "workflow": "swiss-army-knife",
        "old_state": "EXECUTING",
        "new_state": "CONTEXT_UPDATE",
        "request_id": "req_12345"
    }
}

{
    "event": "progress_update",
    "data": {
        "request_id": "req_12345",
        "percentage": 75,
        "message": "Generating test cases..."
    }
}

// Client → Server
{
    "event": "abort_request",
    "data": {
        "request_id": "req_12345",
        "reason": "User cancelled"
    }
}
```

## Integration Testing Points

### Message Validation Tests
1. Schema compliance for all message types
2. Required fields presence
3. Timestamp format validation
4. UUID format validation
5. Payload structure per message type

### Communication Flow Tests
1. Happy path: Full workflow execution
2. Context timeout: Proceed without context
3. Storage failure: Continue to review
4. User abort: Clean state return
5. Agent unavailable: Graceful degradation

### Performance Tests
1. Message throughput: >100 msg/sec
2. Latency: <50ms average
3. Queue depth: <1000 messages
4. Memory usage: <100MB
5. Connection stability: 99.9% uptime

---

*Clear communication protocols ensure reliable workflow execution. Every message is structured, validated, and traceable.*