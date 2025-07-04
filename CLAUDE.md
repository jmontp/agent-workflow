# Agent-Workflow Project Guide

## Project Overview

This is an autonomous software engineering company project that uses AI agents orchestrated through a Context Manager to build software with minimal human intervention. The system is designed to scale from assisting with 1-3 projects (current) to managing dozens of autonomous software companies (future).

## Project Structure

```
agent-workflow/
├── app.py                    # Minimal state machine demo (Flask + WebSocket)
├── templates/index.html      # Web interface
├── static/                   # Client-side JS and CSS
│   ├── app.js
│   └── style.css
├── docs/                     # All project documentation
│   ├── README.md            # Documentation overview
│   ├── project-evolution-guide/  # Main docs (READ IN ORDER)
│   │   ├── 01_AUTONOMOUS_SOFTWARE_COMPANY_VISION.md
│   │   ├── 02_IMPLEMENTATION_ROADMAP.md
│   │   ├── 03_CONTEXT_MANAGER_DEVELOPMENT_GUIDE.md
│   │   ├── 04_CONTEXT_MANAGER_V1_PLAN.md
│   │   ├── 05_AGENT_SPECIFICATIONS_EXPANDED.md
│   │   ├── 06_CONTEXT_MANAGER_V1_DESIGN.md     # NEW: Detailed design with TDD approach
│   │   └── 07_AGENT_DOCUMENTATION_STANDARD.md  # NEW: Unified documentation framework
│   ├── agents/              # Agent specifications
│   │   ├── README.md       # Agent overview
│   │   └── context-manager/ # Context Manager docs
│   │       ├── AGENT_SPECIFICATION.md    # Complete API spec
│   │       ├── BOOTSTRAP_GUIDE.md        # Self-improvement guide
│   │       ├── IMPLEMENTATION_NOTES.md   # Development learnings
│   │       └── README.md                 # Quick start
│   └── research/            # Deep research by complexity level
│       ├── simple/          # Current approach
│       ├── advanced/        # 1-2 year horizon
│       ├── future-advanced/ # 3-5 year vision
│       └── theoretical-limits/ # Long-term possibilities
└── CLAUDE.md               # This file
```

## Current Status

- ✅ Minimal state machine demo working (4 files)
- ✅ Comprehensive research completed
- ✅ Documentation organized with clear reading order
- ✅ Context Manager v1 design completed (TDD approach)
- ✅ Agent Documentation Standard established
- ✅ **Context Manager v1 IMPLEMENTED** with CLI, API, and bootstrap features
- 🎯 **Next**: Documentation intelligence features
- ⏳ Then: Web UI panel and Swiss Army Knife agent
- ⏳ Future: Build full agent suite

## Context Manager v1 Implementation Status

### Design Decisions Made
- **Architecture**: Separate module with clean interfaces
- **Storage**: JSON files for v1 (human-readable, debuggable)
- **Schema**: Python dataclasses with type safety
- **Pattern Detection**: Simple keyword/decision tracking
- **Testing**: TDD approach with tests written first

### Documentation Structure
All Context Manager documentation is organized in `docs/agents/context-manager/`:
- **AGENT_SPECIFICATION.md** - Complete API reference and behavioral specs
- **TECHNICAL_DESIGN.md** - Schema, storage, pattern detection, and API design
- **IMPLEMENTATION_PLAN.md** - Week-by-week implementation guide with code examples
- **BOOTSTRAP_GUIDE.md** - How Context Manager builds itself
- **IMPLEMENTATION_NOTES.md** - Real development learnings
- **README.md** - Quick overview and navigation

Related planning documents in `docs/project-evolution-guide/`:
- **03** - Where to stop development (skip neural fields)
- **04** - Original week 1 planning (now see IMPLEMENTATION_PLAN.md)
- **06** - Original design exploration (now see TECHNICAL_DESIGN.md)

### Bootstrap Process
The Context Manager is being built to document its own development:
```python
# Example of self-documentation in action
cm.log_decision(
    "Using JSON storage instead of SQLite",
    "Prioritizing debuggability and simplicity for v1"
)
```

## Development Approach

### Bootstrap Philosophy
The Context Manager will help build itself by:
1. Logging all development decisions
2. Learning patterns from its own development
3. Suggesting next features based on usage
4. Creating a self-improving foundation

### Key Principles
- **Context-First**: Everything flows through the Context Manager
- **Progressive Complexity**: Start simple, enhance based on real usage
- **Compliance Ready**: Built for FDA/medical device requirements
- **Self-Documenting**: Every decision logged with reasoning

## Quick Start for Development

1. **Understand the Vision** (30 min):
   ```
   Read: docs/project-evolution-guide/01_AUTONOMOUS_SOFTWARE_COMPANY_VISION.md
   ```

2. **Review Implementation Plan** (15 min):
   ```
   Read: docs/agents/context-manager/IMPLEMENTATION_PLAN.md
   ```

3. **Start Coding Context Manager v1**:
   ```python
   # Begin with ~150 lines in context_manager.py
   # Focus on bootstrap features:
   # - log_decision()
   # - suggest_next_task()
   # - basic persistence
   ```

4. **Run the Current Demo**:
   ```bash
   pip install flask flask-socketio
   python app.py
   # Open http://localhost:5000
   ```

## Using Gemini CLI for Large Codebase Analysis

When analyzing large codebases or multiple files that might exceed context limits, use the Gemini CLI with its massive
context window. Use `gemini -p` to leverage Google Gemini's large context capacity.

### File and Directory Inclusion Syntax

Use the `@` syntax to include files and directories in your Gemini prompts. The paths should be relative to WHERE you run the
  gemini command:

#### Examples:

**Single file analysis:**
```bash
gemini -p "@src/main.py Explain this file's purpose and structure"
```

**Multiple files:**
```bash
gemini -p "@package.json @src/index.js Analyze the dependencies used in the code"
```

**Entire directory:**
```bash
gemini -p "@src/ Summarize the architecture of this codebase"
```

**Multiple directories:**
```bash
gemini -p "@src/ @tests/ Analyze test coverage for the source code"
```

**Current directory and subdirectories:**
```bash
gemini -p "@./ Give me an overview of this entire project"

# Or use --all_files flag:
gemini --all_files -p "Analyze the project structure and dependencies"
```

### Implementation Verification Examples

**Check if a feature is implemented:**
```bash
gemini -p "@src/ @lib/ Has dark mode been implemented in this codebase? Show me the relevant files and functions"
```

**Verify authentication implementation:**
```bash
gemini -p "@src/ @middleware/ Is JWT authentication implemented? List all auth-related endpoints and middleware"
```

**Check for specific patterns:**
```bash
gemini -p "@src/ Are there any React hooks that handle WebSocket connections? List them with file paths"
```

**Verify error handling:**
```bash
gemini -p "@src/ @api/ Is proper error handling implemented for all API endpoints? Show examples of try-catch blocks"
```

**Check for rate limiting:**
```bash
gemini -p "@backend/ @middleware/ Is rate limiting implemented for the API? Show the implementation details"
```

**Verify caching strategy:**
```bash
gemini -p "@src/ @lib/ @services/ Is Redis caching implemented? List all cache-related functions and their usage"
```

**Check for specific security measures:**
```bash
gemini -p "@src/ @api/ Are SQL injection protections implemented? Show how user inputs are sanitized"
```

**Verify test coverage for features:**
```bash
gemini -p "@src/payment/ @tests/ Is the payment processing module fully tested? List all test cases"
```

### When to Use Gemini CLI

Use `gemini -p` when:
- Analyzing entire codebases or large directories
- Comparing multiple large files
- Need to understand project-wide patterns or architecture
- Current context window is insufficient for the task
- Working with files totaling more than 100KB
- Verifying if specific features, patterns, or security measures are implemented
- Checking for the presence of certain coding patterns across the entire codebase

### Important Notes

- Paths in @ syntax are relative to your current working directory when invoking gemini
- The CLI will include file contents directly in the context
- No need for --yolo flag for read-only analysis
- Gemini's context window can handle entire codebases that would overflow Claude's context
- When checking implementations, be specific about what you're looking for to get accurate results

## Project-Specific Context

### Medical Device Focus
This project will eventually build medical devices (ankle exoskeleton for OA), requiring:
- Early Documentation Agent for FDA compliance
- Comprehensive audit trails
- Requirement traceability
- Future hardware-specific agents (mechanical, electronics, firmware)

### Agent Types (By Priority)
1. **Context Manager** (Week 1) - The nervous system
2. **Documentation Agent** (Week 2-3) - FDA compliance
3. **Design Agent** (Week 4) - Specifications
4. **Code Agent** (Week 4-5) - Implementation
5. **QA Agent** (Week 5-6) - Testing
6. Future: Regulatory, Hardware, Clinical agents

### Key Decisions Made
1. Bootstrap approach: Context Manager builds itself
2. Skip neural fields: Too complex for v1
3. Documentation Agent early: Critical for medical devices
4. Progressive complexity: Simple → Advanced → Future → Theoretical

## Useful Commands

```bash
# Run the current demo
python app.py

# Analyze project structure with Gemini
gemini -p "@docs/ Summarize the project evolution plan"

# Check implementation progress
gemini -p "@./ What has been implemented so far in this agent-workflow project?"

# Review research findings
gemini -p "@docs/research/ What are the key findings from the research phase?"
```

## Implementation Readiness Summary

### ✅ Documentation Complete
- Vision and roadmap established
- Context Manager fully specified
- TDD approach defined
- Bootstrap methodology documented
- File organization optimized

### 📁 Key Documentation Locations
- **Context Manager Spec**: `docs/agents/context-manager/AGENT_SPECIFICATION.md`
- **Technical Design**: `docs/agents/context-manager/TECHNICAL_DESIGN.md`
- **Implementation Plan**: `docs/agents/context-manager/IMPLEMENTATION_PLAN.md`

### 🎯 Ready to Start Coding
With comprehensive documentation in place, we're ready to begin Week 1 implementation following TDD principles and bootstrap methodology.

## Next Actions

### Immediate Tasks (Context Manager suggested documenting decisions ✓)
- [x] Document key decisions in CLAUDE.md
- [ ] Implement documentation intelligence features
- [ ] Create web UI panel for Context Manager
- [ ] Implement Swiss Army Knife agent
- [ ] Prune and consolidate codebase

### Week 2: Documentation Intelligence & Swiss Army Knife

**Documentation Intelligence**
- [ ] Implement DocPattern learning from existing docs
- [ ] Add update detection from code changes
- [ ] Create routing system by complexity
- [ ] Build quality metrics calculation

**Web UI Panel**
- [ ] Add Context Manager section to web interface
- [ ] Display recent contexts and patterns
- [ ] Show documentation health metrics
- [ ] Enable decision logging from UI

**Swiss Army Knife Agent**
- [ ] Create agent with TaskRequest/TaskResult schema
- [ ] Integrate with Context Manager for pattern learning
- [ ] Implement simple code generation and bug fixes
- [ ] Add to workflow state machine

### Documentation to Maintain
As you implement, update these sections in CLAUDE.md:
1. Design decisions made
2. Patterns discovered
3. Next features suggested by Context Manager
4. Test coverage status
5. Integration points completed

## Key Decisions Made (Tracked by Context Manager)

### Context Manager Implementation
1. **Created Context Manager v1 with CLI interface** - Need quick command-line access for logging decisions and bootstrap methodology requires self-documentation
2. **Use JSON storage for Context Manager** - Human-readable, debuggable, and sufficient for v1 performance requirements
3. **Design Context Manager as documentation intelligence hub** - Avoids content duplication and respects existing documentation structure
4. **Added Context Manager API endpoints to Flask app** - Need web API for agents and UI to interact with Context Manager
5. **Keep project-wide contexts in git for team collaboration** - Enables shared understanding and synchronized development across team members

### Architecture Patterns Emerging
- Bootstrap methodology working: CM suggested documenting decisions after detecting pattern
- Multi-project support built in from start with project_id
- Four interfaces (CLI, Web API, Python API, Web UI) for maximum flexibility
- Separation of project vs user contexts planned for future

### Self-Documentation Examples
```python
# Track why each decision was made
cm.log_decision("decision", "reasoning")

# Track problems encountered
cm.log_problem("issue", "attempted_solution")

# Track successful patterns
cm.log_pattern("pattern_name", "where_applied", "outcome")
```