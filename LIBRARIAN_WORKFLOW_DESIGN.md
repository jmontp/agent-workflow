# Context Manager Librarian Workflow Design

## Overview

The Context Manager acts as a knowledgeable librarian who helps agents navigate, check out, work with, and check in codebase context. This design approaches the system from an agent's perspective, making interactions feel natural and conversational.

## Core Librarian Metaphor

Just like a real librarian:
- **Knows the collection**: Understands what's available and where to find it
- **Provides recommendations**: Suggests relevant materials based on your needs
- **Prevents conflicts**: Tracks who has what checked out
- **Maintains order**: Ensures materials are returned properly
- **Learns preferences**: Gets better at helping over time
- **Proactive guidance**: Notices when materials need updating

## 1. How Agents Request Context

### Natural Language Requests

Agents interact with the librarian using natural, conversational requests:

```python
# Agent asks for help
librarian.request_context("I need to work on the authentication system")
librarian.request_context("Show me everything about the WebSocket implementation")
librarian.request_context("I want to add a new feature for user profiles")
```

### API Design

```python
class LibrarianRequest:
    """What an agent asks the librarian for"""
    intent: str  # "work_on", "understand", "modify", "create", "fix"
    topic: str   # Natural description of what they need
    scope: str   # "focused", "comprehensive", "exploratory"
    
class LibrarianResponse:
    """What the librarian provides"""
    checkouts: List[ContextCheckout]  # Files/contexts to check out
    suggestions: List[Suggestion]      # Additional recommendations
    warnings: List[Warning]           # Potential conflicts or issues
    guidance: str                     # Natural language advice
```

### Request Examples

```python
# Code Agent needs to implement a feature
response = librarian.request_context(
    intent="implement",
    topic="dark mode toggle in settings",
    scope="focused"
)
# Returns: Relevant settings files, CSS theme files, similar implementations

# Documentation Agent needs to update docs
response = librarian.request_context(
    intent="document",
    topic="new API endpoints for user management",
    scope="comprehensive"
)
# Returns: API files, existing API docs, documentation patterns

# QA Agent needs to test something
response = librarian.request_context(
    intent="test",
    topic="payment processing module",
    scope="comprehensive"
)
# Returns: Payment code, existing tests, test patterns, edge cases
```

## 2. How the Librarian Suggests What to Check Out

### Smart Recommendations

The librarian analyzes the request and provides intelligent suggestions:

```python
class ContextCheckout:
    """A piece of context the librarian recommends"""
    resource_type: str      # "file", "documentation", "decision", "pattern"
    path: str              # Location of the resource
    relevance_score: float # How relevant (0-1)
    reason: str            # Why this was suggested
    sections: List[str]    # Specific sections if applicable
    dependencies: List[str] # Related items you might also need
    
class Suggestion:
    """Additional recommendation from the librarian"""
    type: str              # "also_consider", "similar_work", "best_practice"
    description: str       # Natural language suggestion
    resources: List[str]   # Related resources
```

### Recommendation Engine

```python
def suggest_checkouts(self, request: LibrarianRequest) -> List[ContextCheckout]:
    """Librarian's recommendation logic"""
    
    # 1. Parse intent and extract key concepts
    concepts = self._extract_concepts(request.topic)
    
    # 2. Search across multiple dimensions
    checkouts = []
    
    # Find directly relevant files
    checkouts.extend(self._find_by_concepts(concepts))
    
    # Find related documentation
    checkouts.extend(self._find_related_docs(concepts))
    
    # Find past decisions and patterns
    checkouts.extend(self._find_relevant_decisions(concepts))
    
    # Find similar past work
    checkouts.extend(self._find_similar_implementations(concepts))
    
    # 3. Rank by relevance and return top results
    return self._rank_by_relevance(checkouts, request)
```

## 3. Conflict Prevention

### Checkout Tracking

```python
@dataclass
class CheckoutRecord:
    """Track who has what checked out"""
    checkout_id: str
    agent_id: str
    resources: List[str]      # Files/contexts checked out
    intent: str              # What they're doing
    checkout_time: datetime
    expected_duration: int   # Minutes
    exclusive: bool          # If True, no one else can modify
    
class CheckoutManager:
    def checkout(self, agent_id: str, resources: List[str], 
                 intent: str, exclusive: bool = False) -> CheckoutRecord:
        """Check out resources for an agent"""
        
        # Check for conflicts
        conflicts = self._check_conflicts(resources, exclusive)
        if conflicts:
            return self._handle_conflicts(conflicts, agent_id, intent)
            
        # Create checkout record
        record = CheckoutRecord(...)
        self._active_checkouts[record.checkout_id] = record
        
        return record
```

### Conflict Resolution

```python
def _handle_conflicts(self, conflicts: List[Conflict], 
                     agent_id: str, intent: str) -> CheckoutRecord:
    """Librarian mediates conflicts"""
    
    if all(c.type == "read_only" for c in conflicts):
        # Multiple agents can read simultaneously
        return self._create_shared_checkout(...)
        
    elif any(c.type == "exclusive" for c in conflicts):
        # Exclusive checkout in progress
        suggestions = self._suggest_alternatives(conflicts)
        raise CheckoutConflict(
            "These resources are exclusively checked out",
            current_holder=conflicts[0].agent_id,
            expected_available=conflicts[0].expected_return,
            alternatives=suggestions
        )
        
    else:
        # Coordinate between agents
        return self._coordinate_agents(conflicts, agent_id, intent)
```

## 4. Check-in Process

### Natural Check-in Flow

```python
# Agent completes work
checkin_summary = librarian.checkin(
    checkout_id="abc123",
    summary="Implemented dark mode toggle with theme persistence",
    changes=[
        FileChange("settings.py", "added", ["dark_mode_toggle()", "save_theme()"]),
        FileChange("styles.css", "modified", ["Added .dark-theme classes"]),
        DocChange("settings.md", "updated", ["Added dark mode section"])
    ],
    learnings=[
        "Theme switching requires WebSocket notification to all clients",
        "CSS variables make theme implementation much cleaner"
    ],
    follow_up_needed=[
        "Test theme persistence across sessions",
        "Document theme customization for users"
    ]
)
```

### What Gets Tracked

```python
@dataclass
class CheckinRecord:
    """Everything the librarian tracks from a check-in"""
    checkout_id: str
    agent_id: str
    timestamp: datetime
    
    # Work summary
    summary: str
    success: bool
    changes: List[Change]
    
    # Knowledge captured
    learnings: List[str]
    patterns_discovered: List[str]
    decisions_made: List[Decision]
    
    # Future work
    follow_up_tasks: List[str]
    documentation_gaps: List[str]
    suggested_refactors: List[str]
    
    # Metrics
    duration: int  # Minutes
    files_modified: int
    lines_changed: int
    tests_added: int
```

## 5. Learning from Checkouts

### Pattern Recognition

```python
class CheckoutPatternLearner:
    """Learn from successful and failed checkouts"""
    
    def analyze_checkout_patterns(self):
        """Find patterns in what agents check out together"""
        
        # Successful patterns
        successful_checkouts = self._get_successful_checkouts()
        self.success_patterns = {
            "authentication_work": ["auth.py", "middleware.py", "auth_tests.py"],
            "api_changes": ["routes.py", "models.py", "api_docs.md"],
            # ... learned combinations
        }
        
        # Failure patterns
        failed_checkouts = self._get_failed_checkouts()
        self.failure_patterns = {
            "missing_dependencies": ["Forgot to check out config files"],
            "incomplete_context": ["Didn't include related tests"],
            # ... learned gaps
        }
        
    def improve_recommendations(self, request: LibrarianRequest) -> List[str]:
        """Apply learned patterns to improve suggestions"""
        
        # Check if this matches a known successful pattern
        if pattern := self._match_success_pattern(request):
            return self._apply_pattern(pattern)
            
        # Avoid known failure patterns
        suggestions = self._base_suggestions(request)
        return self._avoid_failure_patterns(suggestions)
```

### Feedback Loop

```python
def process_checkin_feedback(self, checkin: CheckinRecord):
    """Learn from each check-in"""
    
    if checkin.success:
        # Record successful resource combinations
        self._record_success_pattern(
            intent=checkin.original_request.intent,
            resources=checkin.resources_used,
            duration=checkin.duration
        )
        
    else:
        # Learn from failures
        self._analyze_failure(
            missing_resources=checkin.suggested_missing,
            errors_encountered=checkin.errors,
            agent_feedback=checkin.feedback
        )
        
    # Update recommendation weights
    self._update_relevance_scores(checkin)
```

## 6. Proactive Guidance

### Suggesting Updates

```python
class ProactiveLibrarian:
    """Librarian notices what needs attention"""
    
    def suggest_needed_updates(self) -> List[UpdateSuggestion]:
        """Proactively suggest what needs work"""
        
        suggestions = []
        
        # Stale documentation
        stale_docs = self._find_stale_documentation()
        for doc in stale_docs:
            suggestions.append(UpdateSuggestion(
                type="documentation",
                urgency="medium",
                description=f"{doc.path} hasn't been updated in 30 days",
                affected_by=doc.related_code_changes
            ))
            
        # Missing tests
        untested_code = self._find_untested_code()
        for code in untested_code:
            suggestions.append(UpdateSuggestion(
                type="testing",
                urgency="high",
                description=f"{code.path} has no test coverage",
                complexity=self._estimate_test_complexity(code)
            ))
            
        # Technical debt
        debt_items = self._identify_technical_debt()
        for item in debt_items:
            suggestions.append(UpdateSuggestion(
                type="refactoring",
                urgency=item.urgency,
                description=item.description,
                effort_estimate=item.effort
            ))
            
        return sorted(suggestions, key=lambda s: s.priority_score)
```

### Daily Briefing

```python
def morning_briefing(self, agent_id: str) -> Briefing:
    """What the librarian tells you at the start of the day"""
    
    return Briefing(
        # Your unfinished work
        pending_checkouts=self._get_agent_checkouts(agent_id),
        
        # What others are working on
        team_activity=self._get_team_summary(),
        
        # Urgent items
        urgent_updates=self._get_urgent_items(),
        
        # Suggested focus for today
        suggested_tasks=self._suggest_daily_tasks(agent_id),
        
        # Relevant updates since last session
        recent_changes=self._get_relevant_changes(agent_id)
    )
```

## 7. Context Discovery

### Exploration Interface

```python
class ContextExplorer:
    """Help agents discover what's available"""
    
    def browse_topics(self) -> Dict[str, List[str]]:
        """Browse by topic/category"""
        return {
            "authentication": ["Files: 12", "Docs: 3", "Decisions: 8"],
            "api": ["Files: 45", "Docs: 12", "Patterns: 15"],
            "frontend": ["Files: 89", "Docs: 8", "Examples: 22"],
            # ...
        }
        
    def search_by_example(self, example_code: str) -> List[SimilarContext]:
        """Find similar implementations"""
        return self._find_similar_patterns(example_code)
        
    def explore_relationships(self, starting_point: str) -> ContextGraph:
        """Explore connected contexts"""
        return ContextGraph(
            root=starting_point,
            connections=self._build_connection_graph(starting_point),
            suggested_paths=self._suggest_exploration_paths()
        )
```

### Discovery Patterns

```python
def common_discovery_patterns(self):
    """How agents typically explore"""
    
    return {
        "depth_first": [
            "Start with one file",
            "Follow imports/dependencies",
            "Explore related tests",
            "Check documentation"
        ],
        
        "breadth_first": [
            "Get overview of module",
            "List all related files",
            "Skim documentation",
            "Dive into specifics"
        ],
        
        "example_driven": [
            "Find similar implementation",
            "Study the pattern",
            "Locate where to apply",
            "Check for variants"
        ],
        
        "documentation_led": [
            "Read relevant docs",
            "Find referenced code",
            "Explore examples",
            "Check test cases"
        ]
    }
```

## Implementation Priority

### Phase 1: Basic Librarian (Week 1)
- Natural language request parsing
- Basic checkout/checkin
- Simple conflict detection
- File-based recommendations

### Phase 2: Smart Librarian (Week 2)
- Pattern learning from checkouts
- Relevance scoring
- Proactive suggestions
- Checkout analytics

### Phase 3: Collaborative Librarian (Week 3)
- Multi-agent coordination
- Shared checkouts
- Team awareness
- Knowledge synthesis

### Phase 4: Predictive Librarian (Week 4)
- Anticipate needs
- Suggest preventive updates
- Optimize team workflow
- Auto-organize knowledge

## Example Agent Interaction

```python
# Morning: Code Agent starts work
code_agent = Agent("code_agent_1")

# Ask librarian for help
librarian_response = cm.librarian.request_context(
    agent=code_agent,
    request="I need to add user notifications to the WebSocket system"
)

print(librarian_response.guidance)
# "I found 3 relevant areas for WebSocket notifications:
#  1. Current WebSocket implementation in websocket_handler.py
#  2. Existing notification patterns in notifications.py
#  3. Similar feature in chat_system.py
#  
#  Note: QA_Agent is currently testing WebSocket stability.
#  Suggest coordinating on changes."

# Agent checks out resources
checkout = cm.librarian.checkout(
    agent=code_agent,
    resources=librarian_response.recommended_files,
    intent="Add user notifications feature",
    exclusive=False  # Others can read
)

# ... Agent works on the feature ...

# Agent checks in work
cm.librarian.checkin(
    checkout_id=checkout.id,
    summary="Added real-time user notifications via WebSocket",
    changes=[...],
    learnings=[
        "Need to handle reconnection for notification delivery",
        "Browser notification API requires user permission"
    ],
    follow_up=[
        "Add notification preferences to user settings",
        "Implement notification history"
    ]
)

# Librarian learns and suggests
print(cm.librarian.suggest_next())
# "Based on your implementation, I suggest:
#  1. Update the WebSocket documentation with notification protocol
#  2. QA_Agent should test notification delivery reliability
#  3. Consider adding notification rate limiting"
```

## Success Metrics

### Librarian Effectiveness
- **Request Success Rate**: How often agents get useful context
- **Checkout Efficiency**: Time saved by good recommendations  
- **Conflict Reduction**: Fewer merge conflicts and duplicated work
- **Knowledge Capture**: Learnings preserved from each checkout
- **Proactive Hits**: How often suggestions are acted upon

### Agent Satisfaction
- **Context Relevance**: Agents get what they need
- **Discovery Speed**: Find information quickly
- **Collaboration**: Aware of team activities
- **Learning**: Build on previous work
- **Productivity**: Complete tasks faster

## Natural Language Examples

### Agent Requests
```
"Help me understand how authentication works"
"I need to fix the bug in payment processing"  
"Show me examples of good test coverage"
"What's the best way to add caching here?"
"Who else is working on the API right now?"
```

### Librarian Responses
```
"I found 3 authentication implementations. The OAuth2 in auth.py is most recent."
"Two agents have worked on payments recently. Check their learnings first."
"The user_service has 95% coverage - great example of testing patterns."
"Redis caching is used in 4 places. The session_cache.py has the cleanest pattern."
"API_Agent has routes.py checked out for 10 more minutes, but you can read it."
```

This librarian workflow makes the Context Manager feel like a helpful, knowledgeable colleague who understands the codebase and helps coordinate work efficiently.