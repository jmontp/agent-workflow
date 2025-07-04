# Minimal Viable Documentation for AI Agents: A Startup CTO Perspective

## Executive Summary

As a CTO who's scaled multiple startups from 0 to IPO, I've learned that documentation is a tool, not a trophy. In the AI agent era, we need to rethink documentation from first principles. The goal isn't comprehensive documentation—it's enabling rapid iteration while maintaining enough context for both humans and AI agents to be productive.

## 1. The Absolute Minimum Documentation Needed

### Core Documentation Requirements

**For AI Agents Pre-Product/Market Fit:**
- **README.md**: Your north star document explaining WHAT the agent does and WHY it exists
- **API Contract**: Clear input/output specifications that both humans and agents can parse
- **Environment Setup**: One-command setup instructions (docker-compose up should just work)
- **Error Catalog**: Common failure modes and recovery strategies

**Post-Product/Market Fit Additions:**
- **Architecture Decision Records (ADRs)**: Document WHY you made key technical choices
- **Integration Guides**: How your agent plays with others in the ecosystem
- **Performance Baselines**: What "normal" looks like for monitoring

### The Anti-Pattern to Avoid

Don't create:
- Lengthy design documents that become outdated before implementation
- Comprehensive API documentation for internal-only endpoints
- Tutorial content for features still in flux
- Documentation for documentation's sake

## 2. Documenting for Speed While Maintaining Quality

### README-Driven Development (RDD) for AI Agents

Drawing from Tom Preston-Werner's approach, but adapted for AI:

```markdown
# Agent Name

## What This Agent Does (1 sentence)
[Clear value proposition]

## Quick Start (30 seconds to first success)
```bash
docker run -e API_KEY=xxx our-agent
```

## Core Capabilities
- Intent: What triggers this agent
- Actions: What it can do
- Constraints: What it won't do

## Integration Example
```python
response = agent.execute({
    "intent": "analyze_code",
    "context": {...}
})
```
```

### Self-Documenting Patterns

**Pattern 1: Behavioral Documentation**
```python
class CodeAnalysisAgent:
    """
    Analyzes code for security vulnerabilities.
    
    Triggers on: Code commit, PR creation, manual scan
    Outputs: SecurityReport with severity levels
    Constraints: Read-only, 5min timeout, Python/JS only
    """
    
    def analyze(self, code: str) -> SecurityReport:
        # Implementation speaks for itself
        pass
```

**Pattern 2: Contract-First Design**
```yaml
# agent-contract.yaml
name: code-analysis-agent
version: 1.0
triggers:
  - event: code.commit
  - event: pr.created
capabilities:
  - analyze_security
  - suggest_fixes
constraints:
  - timeout: 300s
  - memory: 2GB
  - permissions: read-only
```

### Speed Hacks That Scale

1. **Documentation as Code**: Use tools like Swagger/OpenAPI for API specs that generate docs automatically
2. **Inline Everything**: Comments should explain WHY, not WHAT
3. **Video > Text**: A 2-minute Loom can replace 10 pages of setup docs
4. **Templates Over Guides**: Provide working examples people can copy and modify

## 3. When Documentation Debt is Acceptable

### The Startup Documentation Debt Matrix

| Stage | Acceptable Debt | Unacceptable Debt |
|-------|-----------------|-------------------|
| Pre-PMF | Everything except core API contracts | Security/compliance docs |
| Growth | Internal tool docs, edge cases | Customer-facing APIs, SLAs |
| Scale | Nice-to-have features | Architecture decisions, runbooks |
| IPO | Very little | Anything audit-related |

### Strategic Documentation Debt

**Take on debt when:**
- You're validating a hypothesis (might throw it away)
- The implementation is likely to change significantly
- You have <10 engineers who sit together
- The feature affects <5% of users
- You're in a competitive sprint

**Never take debt on:**
- Security boundaries and authentication flows
- Data privacy and compliance requirements
- Public API contracts
- Disaster recovery procedures
- Billing/payment logic

### Tracking Documentation Debt

```python
# In your code
@documentation_debt(
    reason="Rushing for TechCrunch demo",
    impact="New engineers will need handholding",
    payback_by="2024-Q2"
)
def complex_ml_pipeline():
    # TODO: Document the 7 stage preprocessing
    pass
```

## 4. Evolving Documentation as You Scale

### The Documentation Evolution Path

**Stage 1: Founder Mode (0-10 engineers)**
- README + code comments
- Weekly demo videos
- Slack threads as documentation
- Direct knowledge transfer

**Stage 2: Team Mode (10-50 engineers)**
- Automated API docs
- Architecture diagrams
- Onboarding checklists
- Team-specific runbooks

**Stage 3: Organization Mode (50-200 engineers)**
- Comprehensive docs site
- Video tutorials
- Regular documentation sprints
- Documentation owners per service

**Stage 4: Enterprise Mode (200+ engineers)**
- Full documentation team
- Automated documentation testing
- Documentation analytics
- AI-powered documentation search

### Signals It's Time to Level Up

1. **New engineer onboarding takes >1 week**
2. **Same questions in Slack every week**
3. **Production incidents due to misunderstanding**
4. **Customer support can't self-serve**
5. **You're losing deals due to "lack of documentation"**

## 5. Modern Documentation Practices from Fast-Moving Companies

### Stripe's Approach: Documentation as Product

- **Three-column layout**: Navigation, content, live code
- **Personalized examples**: API keys auto-inserted
- **Test mode built-in**: Safe experimentation
- **Friction logging**: Document the user journey, not just the API

Key takeaway: They invested in docs from day one, not after success.

### Vercel's Approach: Progressive Disclosure

- **Start simple**: Hide complexity until needed
- **Learn by doing**: Interactive tutorials
- **Community templates**: Let users document for you
- **Performance metrics**: 90% faster updates with Turbopack

Key takeaway: Documentation should match user expertise level.

### The AI-Native Future

Documentation is becoming:
- **Agent Instructions**: Docs aren't just for humans anymore
- **Interactive Systems**: Not static pages but queryable knowledge
- **Behavior-Focused**: What it does matters more than how
- **Model Context Protocol**: Standardized agent-tool communication

## Practical Implementation Plan

### Week 1: Foundation
```bash
# Create these files
touch README.md
touch CONTRIBUTING.md
touch API.md
touch QUICKSTART.md

# Set up automation
npm install --save-dev swagger-jsdoc
pip install mkdocs
```

### Week 2: Automation
- Set up OpenAPI/Swagger for API docs
- Configure CI/CD to check documentation coverage
- Create documentation templates
- Set up Loom for video docs

### Week 3: Culture
- Documentation in Definition of Done
- "Doc Star of the Week" recognition
- Documentation office hours
- README-driven development for new features

### Ongoing: Measure and Iterate
- Track time-to-first-success for new users
- Monitor documentation search queries
- Survey new hires on documentation gaps
- A/B test documentation approaches

## The Bottom Line

In the AI agent era, documentation isn't about writing more—it's about enabling faster iteration and better collaboration between humans and AI. Start with the minimum viable documentation that unblocks progress, automate everything you can, and only add documentation when the pain of not having it exceeds the cost of creating it.

Remember: Your documentation strategy should be as agile as your development process. Ship early, iterate often, and let your users (human and AI) tell you what they actually need.

The best documentation is the one that gets used, not the one that wins awards for completeness.