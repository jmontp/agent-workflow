# Detailed File-by-File Migration Map

## Complete File Inventory and Migration Destinations

### Root Directory Files (14 files)

| File | Size Check | Content Type | Destination | Action |
|------|------------|--------------|-------------|---------|
| `README.md` | Essential | Quick start | Keep as-is | Enhance with doc links |
| `CLAUDE.md` | Critical | LLM context | Keep as-is | Enhance with migration notes |
| `AUDIT_COMPLIANCE_ACHIEVEMENT_REPORT.md` | Report | Compliance | `docs_src/archive/compliance/` | Archive |
| `CHAT_INTERFACE_TECHNICAL_SPEC.md` | Technical | Architecture | `docs_src/architecture/chat-interface-spec.md` | Move & update |
| `CONFIG_TEMPLATES.md` | User guide | Configuration | `docs_src/user-guide/configuration-templates.md` | Move |
| `DOCUMENTATION_AUDIT_CONSOLIDATED_REPORT.md` | Report | Audit | `docs_src/archive/audits/` | Archive |
| `DOCUMENTATION_INTEGRATION_SUMMARY.md` | Report | Status | `docs_src/archive/` | Archive |
| `DOCUMENTATION_LINK_AUDIT_REPORT.md` | Report | Audit | `docs_src/archive/audits/` | Archive |
| `DOCUMENTATION_STATUS_REPORT.md` | Report | Status | `docs_src/archive/` | Archive |
| `ERROR_HANDLING_IMPROVEMENTS.md` | Technical | Enhancement | `docs_src/architecture/error-handling-design.md` | Move |
| `PARALLEL_EXECUTION_PLAN.md` | Technical | Architecture | `docs_src/architecture/parallel-execution-design.md` | Move |
| `SOLO_DEVELOPER_EXPERIENCE_PLAN.md` | Planning | UX | `docs_src/planning/solo-dev-experience.md` | Move |
| `SOLO_DEV_ENHANCEMENT_SUMMARY.md` | Report | Summary | Extract insights → Archive | Extract & archive |
| `search_optimization_summary.md` | Report | Summary | Extract insights → Archive | Extract & archive |

### tools/visualizer/ Files (25 files)

#### User Documentation (8 files)
| File | Destination | Priority |
|------|-------------|----------|
| `MULTI_PROJECT_USER_GUIDE.md` | `docs_src/user-guide/multi-project-management.md` | HIGH |
| `TROUBLESHOOTING_CHAT.md` | `docs_src/user-guide/chat-troubleshooting.md` | HIGH |
| `MOBILE_TESTING_GUIDE.md` | `docs_src/user-guide/mobile-experience.md` | HIGH |
| `DEPLOYMENT_GUIDE.md` | `docs_src/deployment/visualizer-deployment.md` | HIGH |
| `DEPLOYMENT.md` | Merge with above | HIGH |
| `ACCESSIBILITY.md` | `docs_src/user-guide/accessibility.md` | MEDIUM |
| `DISCORD_INTERFACE_FIXES.md` | Extract fixes → troubleshooting | MEDIUM |
| `INTEGRATION_COMPLETE.md` | Extract key points → Archive | LOW |

#### Technical Documentation (10 files)
| File | Destination | Priority |
|------|-------------|----------|
| `API_DOCUMENTATION.md` | `docs_src/development/api/visualizer-api.md` | HIGH |
| `API_REFERENCE.md` | Merge with above | HIGH |
| `MULTI_PROJECT_API.md` | `docs_src/development/api/multi-project-api.md` | HIGH |
| `PROJECT_CHAT_ISOLATION.md` | `docs_src/architecture/chat-isolation-architecture.md` | MEDIUM |
| `STATE_SYNC_IMPLEMENTATION.md` | `docs_src/architecture/state-synchronization.md` | MEDIUM |
| `CHAT_FOUNDATION.md` | `docs_src/architecture/chat-foundation.md` | MEDIUM |
| `AGENT_INTERFACE_ENHANCEMENT.md` | `docs_src/architecture/agent-interface-design.md` | LOW |
| `ERROR_HANDLING_ANALYSIS.md` | Merge with error handling docs | LOW |
| `ERROR_HANDLING_CONSOLIDATION_REPORT.md` | Extract insights → Archive | LOW |
| `ERROR_HANDLING_INTEGRATION_GUIDE.md` | Merge with main error guide | LOW |

#### Reports & Summaries (6 files)
| File | Action |
|------|---------|
| `CHAT_DEBUG_SUMMARY.md` | Extract debugging tips → Archive |
| `COMPREHENSIVE_CACHE_ANALYSIS_REPORT.md` | Extract performance tips → Archive |
| `CSS_OPTIMIZATION_REPORT.md` | Extract optimization rules → Archive |
| `IMPLEMENTATION_SUMMARY.md` | Archive |
| `JAVASCRIPT_CONSOLIDATION_REPORT.md` | Extract best practices → Archive |
| `MOBILE_ENHANCEMENTS_SUMMARY.md` | Extract features → Archive |

#### CLAUDE.md (1 file)
| File | Action |
|------|---------|
| `CLAUDE.md` | Keep in place, extract troubleshooting to user guide |

### tests/ Directory Files (11 files)

#### Integration Test Docs (6 files)
| File | Destination |
|------|-------------|
| `tests/integration/README_MULTI_PROJECT_TESTS.md` | `docs_src/development/testing/multi-project-testing.md` |
| `tests/integration/INTEGRATION_TEST_ANALYSIS.md` | `docs_src/development/testing/integration-test-analysis.md` |
| `tests/integration/DISCORD_CHAT_TESTING_GUIDE.md` | `docs_src/development/testing/discord-chat-testing.md` |
| `tests/integration/INTEGRATION_TEST_ENHANCEMENTS_SUMMARY.md` | Extract insights → Archive |
| `tests/integration/manual_testing_checklist.md` | `docs_src/development/testing/manual-testing-checklist.md` |
| `tests/integration/CLAUDE.md` | Keep for test context |

#### Unit Test Docs (4 files)
| File | Destination |
|------|-------------|
| `tests/unit/AGENT_MEMORY_COVERAGE_SUMMARY.md` | Consolidate into coverage report |
| `tests/unit/PROJECT_STORAGE_COVERAGE_SUMMARY.md` | Consolidate into coverage report |
| `tests/unit/TEST_SUMMARY.md` | Consolidate into coverage report |
| `tests/unit/CLAUDE.md` | Keep for test context |

#### Other Test Docs (2 files)
| File | Destination |
|------|-------------|
| `tests/README.md` | `docs_src/development/testing/testing-overview.md` |
| `tests/CLAUDE.md` | Keep for test context |

### tools/ Directory Files (5 files)

| File | Destination |
|------|-------------|
| `tools/CLAUDE.md` | Keep, enhance with tool descriptions |
| `tools/dependencies/README.md` | `docs_src/development/tools/dependency-tracking.md` |
| `tools/dependencies/IMPLEMENTATION_SUMMARY.md` | Archive |
| `tools/dependencies/CLAUDE.md` | Keep for context |
| `tools/documentation/README.md` | `docs_src/development/tools/documentation-generation.md` |
| `tools/validation/README.md` | `docs_src/development/tools/validation-tools.md` |
| `tools/README_DOCS_CI.md` | `docs_src/deployment/docs-ci-cd.md` |

### Other CLAUDE.md Files (3 files)

| File | Action |
|------|---------|
| `agent_workflow/CLAUDE.md` | Keep - package documentation |
| `lib/CLAUDE.md` | Keep - library documentation |
| `scripts/CLAUDE.md` | Keep - script documentation |

## Content Extraction Plan

### High-Value Content to Extract Before Archiving

1. **From Summary Files**:
   - Performance optimization techniques
   - Debugging strategies that worked
   - Architecture decisions and rationale
   - Lessons learned
   - Best practices discovered

2. **From Report Files**:
   - Compliance requirements met
   - Coverage metrics achieved
   - Critical bugs found and fixed
   - Performance benchmarks

3. **From Implementation Files**:
   - API design patterns
   - Security considerations
   - Integration patterns
   - Error handling strategies

## Consolidation Groups

### Group 1: Chat/Discord Interface (10 files → 3 files)
**Combine into**:
- `chat-interface-guide.md` (user guide)
- `chat-architecture.md` (technical)
- `chat-troubleshooting.md` (support)

### Group 2: Multi-Project System (5 files → 2 files)
**Combine into**:
- `multi-project-guide.md` (user guide)
- `multi-project-architecture.md` (technical)

### Group 3: Test Coverage Reports (4 files → 1 file)
**Combine into**:
- `test-coverage-analysis.md` (comprehensive report)

### Group 4: Error Handling (4 files → 1 file)
**Combine into**:
- `error-handling-guide.md` (comprehensive guide)

### Group 5: API Documentation (3 files → 2 files)
**Combine into**:
- `visualizer-api-reference.md`
- `multi-project-api-reference.md`

## Migration Execution Checklist

### Pre-Migration
- [ ] Create backup branch
- [ ] Inventory all files
- [ ] Verify docs_src structure
- [ ] Set up redirect mapping

### Phase 1: High Priority User Docs (Week 1)
- [ ] Migrate troubleshooting guides
- [ ] Migrate user guides
- [ ] Update navigation
- [ ] Test documentation build

### Phase 2: Technical Docs (Week 2)
- [ ] Migrate API documentation
- [ ] Migrate architecture docs
- [ ] Consolidate technical specs
- [ ] Update cross-references

### Phase 3: Test & Tool Docs (Week 3)
- [ ] Consolidate test reports
- [ ] Migrate tool documentation
- [ ] Update development guides
- [ ] Archive old reports

### Phase 4: Cleanup (Week 4)
- [ ] Enhance CLAUDE.md files
- [ ] Archive completed work
- [ ] Remove migrated files
- [ ] Final link validation

### Post-Migration
- [ ] Run link checker
- [ ] Update README.md
- [ ] Create migration notes
- [ ] Announce completion

## Expected Outcomes

### Before Migration
- 62 scattered files
- No clear organization
- Duplicate content
- Hard to find information
- Inconsistent formatting

### After Migration
- ~25 well-organized files
- Clear user/developer separation
- No duplicate content
- Easy navigation
- Consistent formatting
- Enhanced CLAUDE.md files
- Preserved institutional knowledge