# Librarian API Specification

## Core API Methods

### 1. Request Context

```python
def request_context(
    self,
    query: str,                          # Natural language request
    intent: str = None,                  # Optional: "implement", "fix", "test", "document", "understand"
    scope: str = "focused",              # "focused", "comprehensive", "exploratory"
    agent_id: str = None,                # Agent making request
    constraints: Dict[str, Any] = None   # Time limits, file count limits, etc.
) -> ContextResponse:
    """
    Ask the librarian for relevant context.
    
    Examples:
        request_context("I need to add dark mode to the settings page")
        request_context("Show me how WebSocket authentication works", intent="understand")
        request_context("Fix the payment processing timeout bug", intent="fix")
    
    Returns:
        ContextResponse with recommended files, patterns, decisions, and guidance
    """
```

### 2. Checkout Resources

```python
def checkout(
    self,
    resources: List[str],          # Files/contexts to checkout
    purpose: str,                  # What you're doing with them
    agent_id: str,                 # Who's checking out
    duration: int = 30,            # Expected minutes needed
    exclusive: bool = False,       # Block others from editing
    auto_extend: bool = True       # Auto-extend if still active
) -> CheckoutTicket:
    """
    Check out resources for work.
    
    Examples:
        checkout(["auth.py", "auth_test.py"], "Adding OAuth support", "code_agent_1")
        checkout(["api/"], "Refactoring API structure", "code_agent_2", exclusive=True)
    
    Returns:
        CheckoutTicket with checkout_id and status
    """
```

### 3. Check In Work

```python
def checkin(
    self,
    checkout_id: str,                    # From checkout()
    summary: str,                        # What was accomplished
    changes: List[ChangeRecord] = None,  # What changed
    learnings: List[str] = None,         # Discoveries/insights
    decisions: List[DecisionRecord] = None,  # Decisions made
    blockers: List[str] = None,          # What prevented completion
    follow_up: List[str] = None          # Next steps needed
) -> CheckinReceipt:
    """
    Return checked out resources with work summary.
    
    Examples:
        checkin(
            "checkout_abc123",
            summary="Implemented OAuth2 with Google provider",
            changes=[
                ChangeRecord("auth.py", "added", ["google_oauth_handler()"]),
                ChangeRecord("config.py", "modified", ["Added GOOGLE_CLIENT_ID"])
            ],
            learnings=["Google OAuth requires specific redirect URI format"],
            follow_up=["Add OAuth for GitHub provider", "Update auth documentation"]
        )
    
    Returns:
        CheckinReceipt with suggestions for next steps
    """
```

### 4. Ask for Suggestions

```python
def suggest_next_task(
    self,
    agent_id: str = None,              # Get personalized suggestions
    context: str = None,               # Current situation
    interests: List[str] = None,       # Areas of interest
    time_available: int = None         # Minutes available
) -> List[TaskSuggestion]:
    """
    Get suggestions for what to work on next.
    
    Examples:
        suggest_next_task(agent_id="test_agent_1")
        suggest_next_task(context="Just finished auth module", interests=["security"])
    
    Returns:
        Prioritized list of suggested tasks with context
    """
```

### 5. Discover Related Context

```python
def discover_related(
    self,
    starting_point: str,               # File, concept, or component
    relationship_type: str = "all",    # "imports", "tests", "docs", "similar", "all"
    depth: int = 2,                    # How many levels to explore
    max_results: int = 20              # Limit results
) -> ContextGraph:
    """
    Explore relationships from a starting point.
    
    Examples:
        discover_related("user_model.py", "tests")
        discover_related("authentication", "all", depth=3)
    
    Returns:
        ContextGraph showing related files, docs, and patterns
    """
```

### 6. Search by Example

```python
def find_similar(
    self,
    example: str,                      # Code snippet or pattern
    language: str = None,              # Programming language
    context_type: str = "code"         # "code", "tests", "docs", "patterns"
) -> List[SimilarityMatch]:
    """
    Find similar implementations or patterns.
    
    Examples:
        find_similar("async def websocket_handler(websocket, path):")
        find_similar("@app.route('/api/users')", context_type="patterns")
    
    Returns:
        Ranked list of similar implementations with locations
    """
```

### 7. Get Team Awareness

```python
def get_team_status(
    self,
    agent_id: str = None,              # Your agent ID for personalized view
    include_checkouts: bool = True,     # Show active checkouts
    include_recent: bool = True,        # Show recent completions
    time_window: int = 24              # Hours to look back
) -> TeamStatus:
    """
    See what the team is working on.
    
    Examples:
        get_team_status()  # Full team overview
        get_team_status(agent_id="doc_agent_1")  # What affects my work
    
    Returns:
        TeamStatus with active work, potential conflicts, and collaboration opportunities
    """
```

### 8. Report Issues

```python
def report_issue(
    self,
    issue_type: str,                   # "stale_docs", "missing_tests", "code_smell", "bug"
    location: str,                     # Where the issue is
    description: str,                  # What's wrong
    severity: str = "medium",          # "low", "medium", "high", "critical"
    suggested_fix: str = None          # Optional suggestion
) -> IssueTicket:
    """
    Report issues found during work.
    
    Examples:
        report_issue("stale_docs", "api/README.md", "Endpoints have changed")
        report_issue("missing_tests", "payment.py", "No tests for refund logic", "high")
    
    Returns:
        IssueTicket for tracking
    """
```

## Data Structures

### ContextResponse

```python
@dataclass
class ContextResponse:
    """What the librarian returns for a context request"""
    
    # Recommended resources
    primary_files: List[FileRecommendation]      # Most relevant files
    related_docs: List[DocRecommendation]        # Relevant documentation  
    relevant_decisions: List[DecisionContext]    # Past decisions
    similar_work: List[PreviousWork]            # Similar implementations
    patterns: List[PatternExample]              # Relevant patterns
    
    # Guidance
    approach_suggestion: str                     # How to tackle this
    warnings: List[Warning]                     # Things to watch out for
    collaboration_notes: List[CollabNote]       # Who else is involved
    
    # Metadata
    confidence_score: float                     # How confident in recommendations
    alternative_approaches: List[str]           # Other ways to do this
    estimated_complexity: str                   # "simple", "moderate", "complex"
```

### FileRecommendation

```python
@dataclass  
class FileRecommendation:
    """A recommended file with context"""
    
    path: str                          # File path
    relevance_score: float            # 0-1 relevance
    reason: str                       # Why recommended
    key_sections: List[str]           # Important parts
    last_modified: datetime           # When last changed
    modified_by: str                  # Who changed it
    checkout_status: str              # "available", "read_only", "checked_out"
```

### CheckoutTicket

```python
@dataclass
class CheckoutTicket:
    """Confirmation of checkout"""
    
    checkout_id: str                   # Unique ID
    status: str                       # "success", "partial", "failed"  
    checked_out: List[str]            # What you got
    unavailable: List[str]            # What was blocked
    alternatives: List[str]           # Suggested alternatives
    expires_at: datetime              # When checkout expires
    warnings: List[str]               # Any concerns
```

### TaskSuggestion

```python
@dataclass
class TaskSuggestion:
    """A suggested task from the librarian"""
    
    task_id: str                      # Unique identifier
    title: str                        # Short description
    description: str                  # Full details
    priority: str                     # "critical", "high", "medium", "low"
    estimated_time: int               # Minutes
    required_files: List[str]         # What you'd need
    related_to: List[str]            # Connected work
    why_suggested: str               # Reasoning
    benefits: List[str]              # What this accomplishes
```

## Usage Examples

### Example 1: Code Agent Implementing Feature

```python
# Initialize librarian client
librarian = ContextLibrarian()

# 1. Request context for new feature
response = librarian.request_context(
    "Add real-time collaboration to the document editor",
    intent="implement",
    agent_id="code_agent_1"
)

print(f"Approach: {response.approach_suggestion}")
# "Start with the existing WebSocket infrastructure in realtime.py, 
#  then extend the document model to support concurrent edits"

# 2. Checkout recommended files
checkout = librarian.checkout(
    resources=[f.path for f in response.primary_files[:5]],
    purpose="Implement real-time collaboration",
    agent_id="code_agent_1",
    duration=120
)

# 3. Work on the feature...
# ... coding happens here ...

# 4. Check in work
receipt = librarian.checkin(
    checkout_id=checkout.checkout_id,
    summary="Added basic real-time collaboration with OT algorithm",
    changes=[
        ChangeRecord("document.py", "modified", ["Added operation transform"]),
        ChangeRecord("realtime.py", "modified", ["Added document sync protocol"]),
        ChangeRecord("collab.js", "created", ["Client-side OT implementation"])
    ],
    learnings=[
        "Operational Transform is complex but necessary for consistency",
        "Need to handle network partitions gracefully"
    ],
    follow_up=[
        "Add conflict resolution UI",
        "Implement presence indicators",
        "Add collaboration tests"
    ]
)

print(f"Next steps: {receipt.suggested_next_steps}")
```

### Example 2: QA Agent Testing Feature

```python
# QA Agent wants to test the collaboration feature
qa_response = librarian.request_context(
    "Test the new real-time collaboration feature",
    intent="test",
    agent_id="qa_agent_1"
)

# See who worked on it
team_status = librarian.get_team_status(agent_id="qa_agent_1")
print(f"Recent work: {team_status.recent_completions}")

# Find similar test examples
similar_tests = librarian.find_similar(
    example="""
    async def test_concurrent_edits():
        # Test multiple users editing simultaneously
    """,
    context_type="tests"
)

# Checkout test files and implementation
test_checkout = librarian.checkout(
    resources=qa_response.primary_files + ["tests/"],
    purpose="Testing real-time collaboration",
    agent_id="qa_agent_1"
)
```

### Example 3: Documentation Agent Updating Docs

```python
# Doc agent notices stale documentation
doc_response = librarian.request_context(
    "Update documentation for the new collaboration feature",
    intent="document",
    agent_id="doc_agent_1"
)

# Check what changed recently
recent_changes = librarian.discover_related(
    starting_point="realtime.py",
    relationship_type="all",
    depth=1
)

# Report stale documentation
issue = librarian.report_issue(
    issue_type="stale_docs",
    location="docs/editor.md",
    description="Missing documentation for real-time collaboration",
    suggested_fix="Add section on collaboration protocol and OT algorithm"
)

# Checkout docs to update
doc_checkout = librarian.checkout(
    resources=["docs/editor.md", "docs/api.md"],
    purpose="Update collaboration documentation",
    agent_id="doc_agent_1"
)
```

### Example 4: Morning Briefing

```python
# Start of day - get oriented
suggestions = librarian.suggest_next_task(
    agent_id="code_agent_1",
    time_available=240  # 4 hours
)

for i, task in enumerate(suggestions[:3], 1):
    print(f"{i}. {task.title}")
    print(f"   Priority: {task.priority}")
    print(f"   Time: {task.estimated_time} min")
    print(f"   Why: {task.why_suggested}")
    print()

# Check team status
team = librarian.get_team_status(agent_id="code_agent_1")
print(f"Active checkouts: {len(team.active_checkouts)}")
print(f"Potential conflicts: {team.conflict_warnings}")
```

## Error Handling

### Common Exceptions

```python
class CheckoutConflict(Exception):
    """Resource is already checked out exclusively"""
    current_holder: str
    expected_available: datetime
    alternatives: List[str]

class InvalidCheckoutID(Exception):
    """Checkout ID not found or expired"""
    checkout_id: str
    
class InsufficientContext(Exception):
    """Not enough context to make recommendations"""
    query: str
    suggestions: List[str]  # How to improve query

class ResourceNotFound(Exception):
    """Requested resource doesn't exist"""
    resource: str
    similar_resources: List[str]
```

### Error Examples

```python
try:
    checkout = librarian.checkout(["critical_config.py"], "Modify config", "agent_1", exclusive=True)
except CheckoutConflict as e:
    print(f"Conflict: {e.current_holder} has this until {e.expected_available}")
    print(f"Try these instead: {e.alternatives}")

try:
    response = librarian.request_context("fix the thing")
except InsufficientContext as e:
    print(f"Too vague. Try: {e.suggestions}")
    # ["fix the authentication thing", "fix the payment processing thing", ...]
```

## Configuration

```python
@dataclass
class LibrarianConfig:
    """Configure librarian behavior"""
    
    # Checkout settings
    default_checkout_duration: int = 30        # Minutes
    max_checkout_duration: int = 240          # 4 hours
    auto_extend_active: bool = True           # Extend if actively editing
    
    # Recommendation settings  
    max_recommendations: int = 10             # Per category
    relevance_threshold: float = 0.3          # Minimum score
    include_archived: bool = False            # Include old code
    
    # Team awareness
    team_update_frequency: int = 5            # Minutes
    conflict_check_radius: int = 2            # File relationship depth
    
    # Learning settings
    pattern_min_occurrences: int = 3          # To consider a pattern
    success_threshold: float = 0.8            # To mark pattern successful
```

This API provides a natural, conversational interface for agents to interact with the Context Manager as a helpful librarian, making the codebase feel accessible and well-organized.