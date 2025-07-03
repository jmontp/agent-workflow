# Content Extraction Guide - Preserving Institutional Knowledge

## Overview

This guide identifies specific valuable content that must be extracted from files before they are archived or removed. The goal is to preserve hard-won knowledge, implementation insights, and troubleshooting wisdom.

## High-Value Content by File

### 1. SOLO_DEV_ENHANCEMENT_SUMMARY.md
**Extract to**: `docs_src/user-guide/solo-developer-guide.md`

Key content to preserve:
- Quick command workflows for solo developers
- Productivity shortcuts discovered
- Common solo developer pain points and solutions
- Streamlined workflows without team overhead

### 2. search_optimization_summary.md
**Extract to**: `docs_src/development/performance-optimization.md`

Key content to preserve:
- Search performance benchmarks
- Optimization techniques that worked
- Index strategies
- Query optimization patterns

### 3. ERROR_HANDLING_IMPROVEMENTS.md
**Extract to**: `docs_src/architecture/error-handling-guide.md`

Key content to preserve:
- Error categorization system
- Recovery strategies by error type
- User-friendly error message templates
- Debugging workflows for common errors

### 4. CHAT_DEBUG_SUMMARY.md
**Extract to**: `docs_src/user-guide/chat-troubleshooting.md`

Key content to preserve:
- Common chat interface issues and fixes
- JavaScript debugging techniques
- WebSocket troubleshooting steps
- Browser-specific quirks and workarounds

### 5. COMPREHENSIVE_CACHE_ANALYSIS_REPORT.md
**Extract to**: `docs_src/development/performance-optimization.md`

Key content to preserve:
- Cache hit/miss ratio improvements
- Optimal cache sizing discoveries
- Cache invalidation strategies
- Performance impact measurements

### 6. CSS_OPTIMIZATION_REPORT.md
**Extract to**: `docs_src/development/frontend-best-practices.md`

Key content to preserve:
- CSS performance rules discovered
- Mobile-specific optimizations
- Critical CSS identification
- Loading strategy improvements

### 7. JAVASCRIPT_CONSOLIDATION_REPORT.md
**Extract to**: `docs_src/development/frontend-best-practices.md`

Key content to preserve:
- Module organization patterns
- Bundle size optimization techniques
- Lazy loading strategies
- Performance monitoring integration

### 8. Test Coverage Summaries (4 files)
**Extract to**: `docs_src/development/testing/coverage-insights.md`

Key content to preserve:
- Critical paths requiring 100% coverage
- Edge cases discovered through testing
- Performance test thresholds
- Integration test patterns that work

### 9. DISCORD_INTERFACE_FIXES.md
**Extract to**: `docs_src/user-guide/chat-troubleshooting.md`

Key content to preserve:
- Specific Discord UI compatibility fixes
- WebSocket reconnection strategies
- Message formatting edge cases
- Mobile keyboard handling solutions

### 10. ERROR_HANDLING_ANALYSIS.md
**Extract to**: `docs_src/architecture/error-handling-guide.md`

Key content to preserve:
- Error frequency analysis results
- Most impactful error fixes
- Error correlation patterns
- Monitoring integration points

## Troubleshooting Wisdom to Preserve

### From tools/visualizer/CLAUDE.md

Critical troubleshooting section about "Changes Not Reflecting After Code Updates":
```markdown
### 🔴 CRITICAL: Changes Not Reflecting After Code Updates

**Problem**: After making code changes to the visualizer, running `aw web` shows old version

**Root Causes**:
1. **Python Package Installation Mode**: Package installed in site-packages instead of editable mode
2. **Browser Cache**: Browser serving cached JavaScript/CSS files

**Solution**:
[Include full solution steps]
```

This MUST be preserved in user troubleshooting guide.

### From Various Implementation Summaries

Common patterns to extract:
1. **"Gotchas" sections** - Unexpected behaviors discovered
2. **"Lessons Learned" sections** - What worked/didn't work
3. **Performance measurements** - Actual numbers achieved
4. **Security considerations** - Vulnerabilities found and fixed
5. **Integration challenges** - How systems were made to work together

## Content Consolidation Templates

### For Troubleshooting Guides
```markdown
## [Problem Category]

### Symptoms
- [List of symptoms users see]

### Root Causes
1. [Technical cause 1]
2. [Technical cause 2]

### Solutions
#### Quick Fix
[Step-by-step quick solution]

#### Permanent Fix
[Step-by-step permanent solution]

### Prevention
[How to avoid this issue]
```

### For Architecture Decisions
```markdown
## [Decision Name]

### Context
[Why this decision was needed]

### Options Considered
1. [Option 1] - Pros/Cons
2. [Option 2] - Pros/Cons

### Decision
[What was chosen and why]

### Consequences
- [Positive outcomes]
- [Trade-offs accepted]
- [Future considerations]
```

### For Performance Optimizations
```markdown
## [Optimization Name]

### Baseline Performance
- Metric: [X ms/ops/etc]
- Conditions: [Test conditions]

### Optimization Applied
[Technical description]

### Results
- New Metric: [Y ms/ops/etc]
- Improvement: [Z%]
- Trade-offs: [Any downsides]

### Implementation Notes
[Special considerations]
```

## Extraction Priority Matrix

| Content Type | Priority | Destination | Value |
|--------------|----------|-------------|--------|
| Troubleshooting solutions | CRITICAL | User guides | Saves hours of debugging |
| Performance optimizations | HIGH | Dev guides | Maintains system speed |
| Architecture decisions | HIGH | Architecture docs | Prevents regression |
| Security fixes | HIGH | Security guide | Prevents vulnerabilities |
| Test insights | MEDIUM | Testing guide | Improves quality |
| UI/UX discoveries | MEDIUM | User guides | Enhances experience |
| Tool configurations | LOW | Dev guides | Helps setup |

## Validation Checklist

Before archiving any file, ensure:

- [ ] All troubleshooting solutions extracted
- [ ] Performance metrics preserved
- [ ] Architecture decisions documented
- [ ] Security considerations captured
- [ ] Integration patterns recorded
- [ ] Lessons learned incorporated
- [ ] Code examples updated
- [ ] Cross-references maintained

## Special Handling

### CLAUDE.md Files
These files contain critical context for AI assistants. When extracting:
1. Preserve all warning sections
2. Keep navigation helpers
3. Maintain troubleshooting sections
4. Update with new file locations

### Compliance Documents
These have legal/audit value:
1. Archive in `docs_src/archive/compliance/` 
2. Maintain full content unchanged
3. Add archive date and reason
4. Keep accessible but separate

### Test Reports
Consolidate but preserve:
1. Baseline metrics
2. Test methodologies
3. Coverage achievements
4. Critical test cases

## Post-Extraction Verification

After extracting content:
1. Search for TODO/FIXME comments
2. Check for hardcoded values to parameterize
3. Verify all links still work
4. Ensure examples are current
5. Update any outdated commands

This extraction process ensures no valuable knowledge is lost during the documentation migration.