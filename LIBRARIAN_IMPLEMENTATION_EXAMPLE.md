# Librarian Implementation Example

## Integration with Existing Context Manager

This example shows how to implement the Librarian interface as an extension of the existing Context Manager, maintaining backward compatibility while adding the natural librarian workflow.

## Core Implementation

```python
# context_manager_librarian.py

from context_manager import ContextManager, Context, ContextType
from dataclasses import dataclass
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import json

@dataclass
class ContextLibrarian:
    """
    The librarian interface for the Context Manager.
    Provides natural, conversational access to the codebase.
    """
    
    def __init__(self, context_manager: ContextManager):
        self.cm = context_manager
        self.checkouts: Dict[str, CheckoutRecord] = {}
        self.checkout_patterns = CheckoutPatternLearner()
        self.nlp_parser = NaturalLanguageParser()
        
    def request_context(
        self,
        query: str,
        intent: str = None,
        scope: str = "focused",
        agent_id: str = None,
        constraints: Dict[str, Any] = None
    ) -> ContextResponse:
        """
        Natural language interface to request context.
        
        The librarian understands queries like:
        - "I need to work on authentication"
        - "Show me how payments are processed"
        - "Help me fix the WebSocket timeout bug"
        """
        
        # Parse natural language query
        parsed = self.nlp_parser.parse_request(query, intent)
        
        # Extract concepts and keywords
        concepts = self._extract_concepts(parsed)
        
        # Build comprehensive context
        response = ContextResponse(
            primary_files=self._find_relevant_files(concepts, scope),
            related_docs=self._find_documentation(concepts),
            relevant_decisions=self._find_decisions(concepts),
            similar_work=self._find_similar_implementations(concepts),
            patterns=self._find_patterns(concepts),
            approach_suggestion=self._suggest_approach(parsed, concepts),
            warnings=self._check_warnings(concepts, agent_id),
            collaboration_notes=self._check_team_overlap(concepts, agent_id)
        )
        
        # Learn from this request
        self._record_request(agent_id, parsed, response)
        
        return response
    
    def _extract_concepts(self, parsed_request: ParsedRequest) -> List[str]:
        """Extract key concepts from the request."""
        
        concepts = []
        
        # Use existing concept extraction from Context Manager
        if hasattr(self.cm, 'concepts'):
            # Search concepts for matches
            for concept, locations in self.cm.concepts.items():
                if any(keyword in parsed_request.query.lower() 
                      for keyword in concept.lower().split('_')):
                    concepts.append(concept)
        
        # Add topic-specific concepts
        concepts.extend(parsed_request.topics)
        
        # Add intent-based concepts
        if parsed_request.intent == "test":
            concepts.extend(["test", "testing", "coverage", "mock"])
        elif parsed_request.intent == "fix":
            concepts.extend(["bug", "error", "exception", "fix"])
            
        return list(set(concepts))
    
    def _find_relevant_files(
        self, 
        concepts: List[str], 
        scope: str
    ) -> List[FileRecommendation]:
        """Find files relevant to the concepts."""
        
        recommendations = []
        
        # Use Context Manager's find_information
        results = self.cm.find_information(" ".join(concepts))
        
        for result in results[:20]:  # Limit based on scope
            # Check if it's a code file
            if result.location_type == "code":
                rec = FileRecommendation(
                    path=result.file_path,
                    relevance_score=self._calculate_relevance(result, concepts),
                    reason=f"Contains {result.match_type}: {result.context}",
                    key_sections=self._extract_key_sections(result),
                    checkout_status=self._check_checkout_status(result.file_path)
                )
                recommendations.append(rec)
                
        # Sort by relevance
        recommendations.sort(key=lambda r: r.relevance_score, reverse=True)
        
        # Limit based on scope
        if scope == "focused":
            return recommendations[:5]
        elif scope == "comprehensive":
            return recommendations[:15]
        else:  # exploratory
            return recommendations
    
    def checkout(
        self,
        resources: List[str],
        purpose: str,
        agent_id: str,
        duration: int = 30,
        exclusive: bool = False,
        auto_extend: bool = True
    ) -> CheckoutTicket:
        """Check out resources for work."""
        
        checkout_id = str(uuid.uuid4())
        available = []
        blocked = []
        
        # Check each resource
        for resource in resources:
            if self._can_checkout(resource, exclusive):
                available.append(resource)
            else:
                blocked.append(resource)
                
        # Handle conflicts
        if blocked and exclusive:
            conflict_info = self._get_conflict_info(blocked)
            raise CheckoutConflict(
                f"Resources are already checked out: {blocked}",
                current_holder=conflict_info['holder'],
                expected_available=conflict_info['available_at'],
                alternatives=self._suggest_alternatives(blocked)
            )
        
        # Create checkout record
        record = CheckoutRecord(
            checkout_id=checkout_id,
            agent_id=agent_id,
            resources=available,
            purpose=purpose,
            checkout_time=datetime.now(),
            expected_duration=duration,
            exclusive=exclusive,
            auto_extend=auto_extend
        )
        
        self.checkouts[checkout_id] = record
        
        # Log the checkout
        self.cm.add_context(Context(
            id=checkout_id,
            type=ContextType.EXECUTION,
            source=agent_id,
            timestamp=datetime.now(),
            data={
                'action': 'checkout',
                'resources': available,
                'purpose': purpose,
                'duration': duration
            }
        ))
        
        return CheckoutTicket(
            checkout_id=checkout_id,
            status="success" if not blocked else "partial",
            checked_out=available,
            unavailable=blocked,
            expires_at=datetime.now() + timedelta(minutes=duration)
        )
    
    def checkin(
        self,
        checkout_id: str,
        summary: str,
        changes: List[ChangeRecord] = None,
        learnings: List[str] = None,
        decisions: List[DecisionRecord] = None,
        blockers: List[str] = None,
        follow_up: List[str] = None
    ) -> CheckinReceipt:
        """Check in resources and capture learnings."""
        
        if checkout_id not in self.checkouts:
            raise InvalidCheckoutID(f"Checkout {checkout_id} not found")
            
        record = self.checkouts[checkout_id]
        
        # Calculate work metrics
        duration = (datetime.now() - record.checkout_time).seconds // 60
        
        # Log the checkin
        checkin_context = self.cm.add_context(Context(
            id=str(uuid.uuid4()),
            type=ContextType.EXECUTION,
            source=record.agent_id,
            timestamp=datetime.now(),
            data={
                'action': 'checkin',
                'checkout_id': checkout_id,
                'summary': summary,
                'duration_minutes': duration,
                'changes': [c.to_dict() for c in (changes or [])],
                'learnings': learnings or [],
                'decisions': [d.to_dict() for d in (decisions or [])],
                'blockers': blockers or [],
                'follow_up': follow_up or []
            },
            relationships=[checkout_id]  # Link to checkout
        ))
        
        # Log individual learnings for pattern detection
        for learning in (learnings or []):
            self.cm.add_context(Context(
                id=str(uuid.uuid4()),
                type=ContextType.DOCUMENTATION,
                source=record.agent_id,
                timestamp=datetime.now(),
                data={
                    'type': 'learning',
                    'content': learning,
                    'context': summary
                },
                relationships=[checkin_context]
            ))
        
        # Log decisions
        for decision in (decisions or []):
            self.cm.log_decision(
                decision=decision.decision,
                reasoning=decision.reasoning
            )
        
        # Learn from this checkout/checkin cycle
        self.checkout_patterns.learn_from_checkout(
            record=record,
            success=len(blockers or []) == 0,
            duration=duration
        )
        
        # Remove checkout record
        del self.checkouts[checkout_id]
        
        # Generate suggestions
        next_suggestions = self._generate_next_suggestions(
            summary, changes, learnings, follow_up
        )
        
        return CheckinReceipt(
            checkout_id=checkout_id,
            success=True,
            duration_minutes=duration,
            suggested_next_steps=next_suggestions
        )
    
    def suggest_next_task(
        self,
        agent_id: str = None,
        context: str = None,
        interests: List[str] = None,
        time_available: int = None
    ) -> List[TaskSuggestion]:
        """Suggest what to work on next."""
        
        suggestions = []
        
        # Get baseline suggestions from Context Manager
        cm_suggestions = self.cm.suggest_next_task()
        
        for cm_task in cm_suggestions:
            # Enhance with librarian intelligence
            estimated_time = self._estimate_task_time(cm_task)
            
            # Skip if not enough time
            if time_available and estimated_time > time_available:
                continue
                
            # Check interest match
            if interests:
                relevance = self._calculate_interest_match(cm_task, interests)
                if relevance < 0.3:
                    continue
            
            # Find required files
            required_files = self._identify_required_files(cm_task)
            
            # Check availability
            available = all(self._can_checkout(f, False) for f in required_files)
            
            if available:
                suggestion = TaskSuggestion(
                    task_id=str(uuid.uuid4()),
                    title=cm_task.get('title', cm_task.get('description', '')),
                    description=cm_task.get('details', ''),
                    priority=self._calculate_priority(cm_task),
                    estimated_time=estimated_time,
                    required_files=required_files,
                    why_suggested=cm_task.get('reason', 'Pattern-based suggestion')
                )
                suggestions.append(suggestion)
        
        # Sort by priority and relevance
        suggestions.sort(key=lambda s: (s.priority, -s.estimated_time))
        
        return suggestions
    
    def get_team_status(
        self,
        agent_id: str = None,
        include_checkouts: bool = True,
        include_recent: bool = True,
        time_window: int = 24
    ) -> TeamStatus:
        """Get awareness of team activity."""
        
        status = TeamStatus()
        
        # Active checkouts
        if include_checkouts:
            for checkout in self.checkouts.values():
                if checkout.agent_id != agent_id:  # Don't show own checkouts
                    status.active_checkouts.append({
                        'agent': checkout.agent_id,
                        'resources': checkout.resources,
                        'purpose': checkout.purpose,
                        'expires': checkout.checkout_time + timedelta(
                            minutes=checkout.expected_duration
                        )
                    })
        
        # Recent completions
        if include_recent:
            recent_contexts = self.cm.query_contexts(
                type_filter=ContextType.EXECUTION,
                since=datetime.now() - timedelta(hours=time_window)
            )
            
            for ctx in recent_contexts:
                if ctx.data.get('action') == 'checkin':
                    status.recent_completions.append({
                        'agent': ctx.source,
                        'summary': ctx.data.get('summary'),
                        'timestamp': ctx.timestamp,
                        'learnings': ctx.data.get('learnings', [])
                    })
        
        # Check for potential conflicts
        if agent_id and self._get_agent_interests(agent_id):
            interests = self._get_agent_interests(agent_id)
            for checkout in self.checkouts.values():
                if checkout.agent_id != agent_id:
                    overlap = self._calculate_overlap(
                        interests, 
                        checkout.resources
                    )
                    if overlap > 0.5:
                        status.potential_conflicts.append({
                            'agent': checkout.agent_id,
                            'overlap_score': overlap,
                            'resources': checkout.resources
                        })
        
        return status
```

## Natural Language Parser

```python
class NaturalLanguageParser:
    """Parse natural language requests into structured queries."""
    
    def __init__(self):
        self.intent_patterns = {
            'implement': [
                r'add\s+(\w+)',
                r'implement\s+(\w+)',
                r'create\s+(\w+)',
                r'build\s+(\w+)'
            ],
            'fix': [
                r'fix\s+(?:the\s+)?(\w+)',
                r'debug\s+(\w+)',
                r'resolve\s+(\w+)',
                r'repair\s+(\w+)'
            ],
            'test': [
                r'test\s+(\w+)',
                r'verify\s+(\w+)',
                r'validate\s+(\w+)'
            ],
            'understand': [
                r'how\s+does\s+(\w+)',
                r'explain\s+(\w+)',
                r'show\s+me\s+(\w+)',
                r'what\s+is\s+(\w+)'
            ],
            'document': [
                r'document\s+(\w+)',
                r'update\s+docs?\s+for\s+(\w+)',
                r'write\s+documentation'
            ]
        }
        
    def parse_request(self, query: str, intent: str = None) -> ParsedRequest:
        """Parse a natural language query."""
        
        # Detect intent if not provided
        if not intent:
            intent = self._detect_intent(query)
            
        # Extract topics and keywords
        topics = self._extract_topics(query)
        
        # Identify action verbs
        action = self._extract_action(query)
        
        # Extract constraints
        constraints = self._extract_constraints(query)
        
        return ParsedRequest(
            query=query,
            intent=intent,
            topics=topics,
            action=action,
            constraints=constraints
        )
```

## Pattern Learning

```python
class CheckoutPatternLearner:
    """Learn from checkout patterns to improve recommendations."""
    
    def __init__(self):
        self.successful_patterns = []
        self.failure_patterns = []
        self.file_associations = {}  # Which files are often checked out together
        
    def learn_from_checkout(
        self,
        record: CheckoutRecord,
        success: bool,
        duration: int
    ):
        """Learn from a checkout/checkin cycle."""
        
        pattern = {
            'resources': record.resources,
            'purpose': record.purpose,
            'duration': duration,
            'success': success,
            'timestamp': datetime.now()
        }
        
        if success:
            self.successful_patterns.append(pattern)
            self._update_file_associations(record.resources, positive=True)
        else:
            self.failure_patterns.append(pattern)
            self._update_file_associations(record.resources, positive=False)
            
        # Prune old patterns
        self._prune_old_patterns()
        
    def suggest_additional_files(self, files: List[str]) -> List[str]:
        """Suggest files that are often checked out together."""
        
        suggestions = set()
        
        for file in files:
            if file in self.file_associations:
                # Get files frequently checked out with this one
                associated = self.file_associations[file]
                for assoc_file, score in associated.items():
                    if score > 0.5 and assoc_file not in files:
                        suggestions.add(assoc_file)
                        
        return list(suggestions)
```

## Example Usage in Practice

```python
# Initialize the librarian
cm = ContextManager(base_dir="./aw_docs")
librarian = ContextLibrarian(cm)

# Agent requests context naturally
agent = "code_agent_1"

# Morning start
team_status = librarian.get_team_status(agent_id=agent)
print(f"Team Activity Summary:")
print(f"- {len(team_status.active_checkouts)} active checkouts")
print(f"- {len(team_status.recent_completions)} recent completions")

# Request context for a task
response = librarian.request_context(
    "I need to add user notification preferences to the settings page",
    agent_id=agent
)

print(f"\nLibrarian suggests: {response.approach_suggestion}")
print(f"\nRecommended files:")
for file in response.primary_files[:3]:
    print(f"  - {file.path} ({file.reason})")

# Checkout resources
try:
    checkout = librarian.checkout(
        resources=[f.path for f in response.primary_files[:3]],
        purpose="Add notification preferences",
        agent_id=agent,
        duration=60
    )
    print(f"\nChecked out {len(checkout.checked_out)} files")
    print(f"Checkout ID: {checkout.checkout_id}")
    
except CheckoutConflict as e:
    print(f"\nConflict: {e}")
    print(f"Try again after: {e.expected_available}")
    print(f"Or try these alternatives: {e.alternatives}")

# ... Work happens here ...

# Check in work with learnings
receipt = librarian.checkin(
    checkout_id=checkout.checkout_id,
    summary="Added notification preferences with email/SMS/push options",
    changes=[
        ChangeRecord("settings.py", "modified", 
                    ["Added NotificationPreferences model"]),
        ChangeRecord("forms.py", "modified", 
                    ["Added NotificationPreferencesForm"]),
        ChangeRecord("templates/settings.html", "modified", 
                    ["Added preferences UI"])
    ],
    learnings=[
        "SMS notifications require Twilio integration",
        "Push notifications need service worker setup",
        "Email preferences should respect unsubscribe laws"
    ],
    follow_up=[
        "Implement SMS provider integration",
        "Add service worker for push notifications",
        "Create notification preview feature"
    ]
)

print(f"\nCheckin complete!")
print(f"Duration: {receipt.duration_minutes} minutes")
print(f"\nSuggested next steps:")
for step in receipt.suggested_next_steps:
    print(f"  - {step}")

# Get suggestions for next task
suggestions = librarian.suggest_next_task(
    agent_id=agent,
    context="Just finished notification preferences",
    time_available=120
)

print(f"\nLibrarian suggests these tasks:")
for i, task in enumerate(suggestions[:3], 1):
    print(f"{i}. {task.title}")
    print(f"   Time: {task.estimated_time} min")
    print(f"   Why: {task.why_suggested}")
```

This implementation shows how the librarian metaphor translates into practical code that makes the Context Manager more approachable and natural for agents to use.