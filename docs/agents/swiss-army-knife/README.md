# Swiss Army Knife Agent Documentation

This directory contains documentation for the Swiss Army Knife Agent - a versatile, general-purpose execution agent that handles a wide variety of tasks.

## 📁 Documentation Structure

- **[AGENT_SPECIFICATION.md](AGENT_SPECIFICATION.md)** - Complete agent specification (Level 1)
  - API definition
  - Behavioral characteristics
  - Integration with Context Manager
  - Performance requirements
  - Testing strategy

## 🎯 Quick Overview

The Swiss Army Knife Agent is designed to be:
- **Versatile**: Handles code generation, bug fixes, documentation, and more
- **Fast**: Most tasks complete in under a minute
- **Learning**: Uses Context Manager patterns to improve over time
- **Practical**: Good enough for most tasks, not perfect for any

## 🔑 Key Concepts

### Task Types
1. **Code Generation**: Functions, classes up to 200 lines
2. **Bug Fixes**: Simple to moderate complexity
3. **Documentation**: Docstrings, comments, READMEs
4. **Refactoring**: Small-scale improvements
5. **Testing**: Unit test generation
6. **Analysis**: Basic code review

### Integration Flow
```
Request → Analyze → Search Context → Apply Patterns → Execute → Update Context
```

### When to Use
- Rapid prototyping
- Quick fixes
- Standard implementations
- Documentation updates
- Test generation

### When NOT to Use
- Mission-critical code
- Complex architecture
- Multi-file changes
- Deep domain expertise needed
- Performance optimization

## 📊 Current Status

- ✅ Specification completed
- 🔄 Implementation starting
- ⏳ Integration with workflow pending
- ⏳ Testing framework needed

## 🔗 Related Documentation

- [Swiss Army Knife Workflow](../../workflows/active/01_swiss-army-knife/) - The workflow using this agent
- [Context Manager](../context-manager/) - Provides patterns and memory
- [Agent Documentation Standard](../../project-evolution-guide/07_AGENT_DOCUMENTATION_STANDARD.md)

## 💡 Philosophy

> "Like a Swiss Army knife, this agent may not be the perfect tool for any single job, but it's good enough for most jobs and always available."

The agent embodies pragmatism over perfection, speed over completeness, and learning over static behavior.