# Librarian Workflow: Advanced Scenarios & Edge Cases

## Complex Real-World Scenarios

### Scenario 1: Multi-Agent Architectural Refactoring

When multiple agents need to coordinate on a large refactoring:

```python
# Design Agent starts the refactoring planning
design_response = librarian.request_context(
    "Plan database migration from SQLite to PostgreSQL",
    intent="design",
    scope="comprehensive"
)

# Librarian responds with coordination plan
print(design_response.approach_suggestion)
"""
This is a major architectural change affecting 47 files across 8 modules.
I recommend a phased approach:

Phase 1: Design Agent creates migration plan (2 days)
Phase 2: Code Agents implement adapters (3 days)  
Phase 3: QA Agent validates data integrity (2 days)
Phase 4: Doc Agent updates all documentation (1 day)

Current blockers:
- API Agent has 5 database files checked out (available in 2 hours)
- Production deployment freeze until Friday

Similar migration: MongoDB to PostgreSQL (6 months ago)
- Took 2 weeks with 3 rollback attempts
- Key learning: Abstract database layer first
"""

# Librarian creates a "refactoring context" 
refactor_context = librarian.create_team_context(
    name="sqlite_to_postgres_migration",
    coordinator="design_agent_1",
    participants=["code_agent_1", "code_agent_2", "qa_agent_1", "doc_agent_1"],
    estimated_duration="8 days",
    checkpoints=[
        "adapter_layer_complete",
        "migration_scripts_tested",
        "rollback_plan_validated"
    ]
)
```

### Scenario 2: Emergency Production Bug

When a critical bug needs immediate attention:

```python
# Support Agent reports critical issue
emergency = librarian.emergency_request(
    "Payment processing is failing for all European customers!",
    severity="critical",
    agent_id="support_agent_1"
)

# Librarian enters emergency mode
print(emergency.immediate_actions)
"""
🚨 EMERGENCY MODE ACTIVATED 🚨

Potentially related recent changes:
1. Payment gateway update 3 hours ago by code_agent_2
2. Currency conversion fix yesterday by code_agent_1
3. Region detection update 2 days ago by code_agent_3

Immediate actions taken:
✓ Reserved all payment-related files for emergency fix
✓ Notified all agents with payment file checkouts
✓ Located last known working version (commit a4f3c2)

Relevant files for debugging:
- payment_gateway.py (modified 3 hours ago)
- currency_converter.py (error logs show exceptions)
- region_detector.py (might be misidentifying EU)
- payment_processor_test.py (3 tests were disabled!)

Similar incident: Payment timeout for Asian customers (2 months ago)
- Root cause: Timezone calculation error
- Fix: Added region-specific timeout handling
"""

# Librarian coordinates emergency response
emergency_checkout = librarian.emergency_checkout(
    resources=emergency.critical_files,
    agent_id="code_agent_1",
    purpose="Fix European payment processing",
    override_conflicts=True  # Force checkout
)

# Other agents are notified
# QA_Agent_1: "Your test checkout of payment_tests.py was overridden for emergency"
# Code_Agent_2: "Your payment gateway changes might be related - please standby"
```

### Scenario 3: Knowledge Gap Detection

When the librarian notices missing knowledge:

```python
# Developer asks about undocumented system
response = librarian.request_context(
    "How does the rate limiting system work?"
)

# Librarian detects knowledge gap
print(response.warnings)
"""
⚠️ KNOWLEDGE GAP DETECTED ⚠️

I found rate limiting implementation but very limited documentation:
- rate_limiter.py exists but has no docstrings
- No documentation mentions rate limiting
- No tests found for rate limiting
- Configuration seems hardcoded

What I found:
- Basic token bucket implementation in rate_limiter.py
- Used in 3 API endpoints (inconsistently)
- No monitoring or metrics

Recommendations:
1. This needs immediate documentation
2. Tests are critical for this security feature
3. Consider standardizing the implementation
"""

# Librarian proactively creates documentation task
doc_task = librarian.create_knowledge_task(
    title="Document rate limiting system",
    priority="high",
    reason="Security feature with no documentation",
    suggested_contents=[
        "How rate limiting works",
        "Configuration options",
        "Per-endpoint limits",
        "Monitoring and alerts",
        "Testing procedures"
    ]
)
```

### Scenario 4: Learning from Failure

When things go wrong, the librarian learns:

```python
# Agent reports failed implementation
failure_report = librarian.report_failure(
    checkout_id="checkout_123",
    what_went_wrong="WebSocket implementation caused memory leak",
    attempted_approach="Used global connection pool",
    time_wasted=480,  # 8 hours
    root_cause="Connections were never closed"
)

# Librarian learns and prevents future failures
print(failure_report.librarian_response)
"""
Thank you for reporting this failure. I've learned:

1. ❌ Pattern marked as problematic:
   - Global WebSocket connection pools without cleanup
   - Added to anti-patterns list

2. 📚 Documentation updated:
   - Added warning to WebSocket guide
   - Created cleanup checklist

3. 🔍 Similar code found:
   - database_pool.py might have same issue
   - redis_connections.py uses similar pattern

4. 🎯 Future recommendations updated:
   - Will now suggest connection lifecycle management
   - Will include cleanup code in WebSocket examples
   - Will recommend the connection manager pattern

5. 📊 Team notified:
   - QA team alerted to test for memory leaks
   - Architecture team notified of pattern issue

Your time wasn't wasted - this learning will save others hours!
"""

# Next agent working with WebSockets gets warning
next_response = librarian.request_context(
    "Implement WebSocket chat feature"
)

print(next_response.warnings[0])
"""
⚠️ Recent failure with WebSocket memory leak!
code_agent_3 discovered global connection pools cause leaks.
Always implement connection cleanup. See new WebSocket best practices guide.
"""
```

### Scenario 5: Cross-Project Pattern Recognition

When the librarian notices patterns across projects:

```python
# Librarian performs weekly pattern analysis
patterns = librarian.analyze_cross_project_patterns()

print(patterns.discovered_patterns[0])
"""
📊 PATTERN DISCOVERED: Authentication Evolution

I've noticed a consistent pattern across 4 projects:

1. Project Alpha (6 months ago):
   - Started with basic auth → Added JWT → Added OAuth2
   - Time: 3 weeks of refactoring

2. Project Beta (4 months ago):
   - Started with basic auth → Added JWT → Added OAuth2
   - Time: 3 weeks of refactoring

3. Project Gamma (2 months ago):
   - Started with basic auth → Added JWT → Added OAuth2
   - Time: 3 weeks of refactoring

4. Project Delta (current):
   - Just implemented basic auth...

RECOMMENDATION for Project Delta:
Skip the evolutionary steps and implement OAuth2 directly!

I can provide:
- Standard OAuth2 implementation template
- Configuration patterns that worked
- Common pitfalls to avoid
- Test suites from previous projects
"""

# Librarian proactively suggests to current project
suggestion = librarian.proactive_suggestion(
    agent_id="code_agent_current_project",
    context="Working on Project Delta authentication"
)

print(suggestion.message)
"""
Based on patterns from Projects Alpha, Beta, and Gamma,
I strongly recommend implementing OAuth2 directly instead
of basic auth. This will save approximately 3 weeks of 
refactoring. Would you like me to check out the OAuth2
template and examples?
"""
```

### Scenario 6: Intelligent Merge Conflict Resolution

When multiple agents need to modify the same critical file:

```python
# Two agents need the same file
agent1_request = librarian.request_context(
    "Add user preferences to settings"
)
agent2_request = librarian.request_context(
    "Add admin controls to settings"
)

# Librarian detects potential conflict
conflict_resolution = librarian.resolve_checkout_conflict(
    resource="settings.py",
    agents=["code_agent_1", "code_agent_2"],
    intents=["add user preferences", "add admin controls"]
)

print(conflict_resolution.strategy)
"""
🤝 COLLABORATIVE CHECKOUT SUGGESTED

Both agents need to modify settings.py for different features.

Analysis:
- Agent 1: Adding to user_preferences section (lines 45-89)
- Agent 2: Adding to admin_panel section (lines 120-156)
- Overlap risk: Low (different sections)

Recommended approach:
1. Coordinate changes using feature flags
2. Agent 1 works on user_preferences branch
3. Agent 2 works on admin_controls branch
4. Use new SettingsSection base class for both
5. Merge sequentially with integration tests

I've prepared:
- Shared interface definition
- Integration test template
- Merge order recommendation

Would you like me to set up collaborative checkout?
"""

# Set up collaborative work
collab = librarian.setup_collaboration(
    agents=["code_agent_1", "code_agent_2"],
    shared_resources=["settings.py"],
    coordination_plan=conflict_resolution.strategy,
    merge_strategy="sequential",
    notification_channel="slack#settings-update"
)
```

### Scenario 7: Predictive Dependency Management

When the librarian anticipates cascading changes:

```python
# Agent makes a seemingly simple request
response = librarian.request_context(
    "Rename User model to Account"
)

# Librarian predicts cascade
print(response.warnings)
"""
⚠️ CASCADE ANALYSIS: Renaming User → Account

This change will trigger updates in:

Direct impacts (must change):
- 47 files directly import User model
- 132 references in templates
- 23 test files use User fixtures
- 8 API endpoints return User objects

Indirect impacts (might break):
- Authentication middleware expects User
- Caching keys use "user_" prefix
- Frontend expects 'user' in API responses
- Analytics tracks "user_events"

Suggested approach:
1. Create Account model inheriting from User (backward compatible)
2. Add deprecation warnings to User model
3. Update in phases:
   - Phase 1: Core model and database
   - Phase 2: Internal references  
   - Phase 3: API with versioning
   - Phase 4: Frontend with feature flag
   - Phase 5: Remove User model

Estimated effort: 3-4 days (not 1 hour!)

Similar refactoring: Product → Item (3 months ago)
- Took 5 days with 2 rollbacks
- Key learning: API versioning crucial
```

## Advanced Librarian Intelligence Features

### 1. Contextual Code Generation
```python
# Librarian can suggest code based on patterns
code_suggestion = librarian.suggest_implementation(
    "Add caching to get_user_profile function",
    context="High traffic endpoint"
)

print(code_suggestion.implementation)
"""
Based on your caching patterns, here's a consistent implementation:

```python
from cache_utils import redis_cache, cache_key_generator
from metrics import cache_metrics

@redis_cache(ttl=300, prefix="user_profile")
@cache_metrics.track
def get_user_profile(user_id: int) -> UserProfile:
    # Your existing implementation
    pass
```

This follows your established patterns:
- 5-minute TTL for user data (from your cache config)
- Redis for caching (your standard)
- Metrics tracking (required by your monitoring setup)
- Cache key includes version prefix (for cache busting)
"""
```

### 2. Performance Impact Prediction
```python
# Librarian predicts performance implications
perf_analysis = librarian.analyze_performance_impact(
    "Add full-text search to products table"
)

print(perf_analysis.prediction)
"""
📊 PERFORMANCE IMPACT ANALYSIS

Based on similar implementations:
- Product table: 2.3M rows
- Search index size: ~450MB
- Indexing time: ~45 minutes

Expected impacts:
1. Initial indexing: 45-min database lock
2. Insert performance: -12% (trigger overhead)  
3. Search performance: +2000% vs LIKE queries
4. Storage increase: +450MB
5. Memory usage: +200MB (search cache)

Recommendations:
- Schedule indexing during maintenance window
- Use batch updates to minimize trigger impact
- Consider read replica for search queries
- Monitor disk space (currently 78% full)

Similar implementation: Blog post search (6 months ago)
- Actual impact matched predictions ±10%
"""
```

### 3. Security Vulnerability Detection
```python
# Librarian spots security concerns
security_check = librarian.security_review(
    checkout_id="checkout_789",
    changes=["Added user input to SQL query"]
)

print(security_check.alert)
"""
🔒 SECURITY ALERT: SQL Injection Risk

Detected concerning pattern in your changes:
```python
query = f"SELECT * FROM users WHERE name = '{user_input}'"
```

This is vulnerable to SQL injection!

Secure alternatives in your codebase:
1. Using parameterized queries (auth/db.py:45)
2. Using ORM queries (models/user.py:23)
3. Using prepared statements (db/utils.py:89)

Required fixes:
- Use parameterized queries
- Add input validation
- Add security test case
- Update security documentation

Blocking checkin until security issue resolved.
"""
```

## Librarian Personality Traits

### Encouraging During Difficulties
```python
# When agent is struggling
struggle_response = librarian.request_context(
    "I can't figure out why this test keeps failing",
    context="Working on it for 3 hours"
)

print(struggle_response.encouragement)
"""
I see you've been working hard on this! Let me help:

Similar test failures solved recently:
1. Timezone issue in date assertions (2 days ago)
   - Fixed by using UTC throughout
2. Async timing in integration tests (1 week ago)
   - Fixed with proper await statements
3. Test isolation problem (2 weeks ago)
   - Fixed by resetting database between tests

Quick debugging checklist:
□ Run test in isolation
□ Check test database state
□ Verify mock configurations
□ Look for timing dependencies

You're not alone - qa_agent_2 fought similar test last month
and documented the solution in testing_gotchas.md

Sometimes a short break helps too! ☕
"""
```

### Celebrating Successes
```python
# When major milestone completed
success = librarian.checkin(
    checkout_id="major_feature",
    summary="Completed real-time collaboration feature"
)

print(success.celebration)
"""
🎉 FANTASTIC WORK! 🎉

You've successfully implemented real-time collaboration!

Impact of your work:
- 17 files elegantly updated
- 0 conflicts despite complexity
- 95% test coverage achieved
- Documentation already current

Your learnings will help others:
- OT algorithm explanation saved
- WebSocket patterns documented
- Performance optimizations noted

Team notifications sent:
- PM notified of feature completion
- QA team ready for testing
- Doc team aware of new feature

This implementation will be referenced as the gold standard
for real-time features. Take a moment to celebrate! 🎊
"""
```

These advanced scenarios show how the Librarian becomes an intelligent, helpful, and even empathetic assistant that not only manages code context but actively helps developers succeed in complex real-world situations.