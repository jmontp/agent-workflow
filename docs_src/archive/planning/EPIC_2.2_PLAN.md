# Epic 2.2 Plan: Refine Documentation

**Objective**: Transform 62 scattered documentation files into two professional streams: a task-oriented User Manual and an Engineering Reference with architecture decisions. Preserve critical troubleshooting knowledge in enhanced CLAUDE.md files for AI assistance.

---

### **Simple Summary**

Transform 62 scattered documentation files into two professional streams: a task-oriented User Manual and an Engineering Reference with architecture decisions. Preserve critical troubleshooting knowledge in enhanced CLAUDE.md files for AI assistance.

---

### **Two Documentation Streams**

1.  **User Manual (How to Use)**
    *   **Location**: `/docs_src/user-guide/visualizer/`
    *   **Structure**: Task-oriented, not feature-oriented
    *   **Contents**: Quick start, daily tasks, troubleshooting wizard
    *   **Format**: Visual-first with screenshots and videos

2.  **Engineering Reference (How It Works)**
    *   **Location**: `/docs_src/architecture/visualizer/`
    *   **Structure**: Component-based with decision records
    *   **Contents**: Architecture, APIs, patterns, integration guides
    *   **Format**: Technical diagrams and code examples

---

### **Migration Impact**

*   **Current**: 62 documentation files across repository
*   **Target**: ~25 organized documents
*   **Reduction**: 60% fewer files
*   **Knowledge Loss**: 0% - all valuable content preserved

---

### **Execution Plan (4 Weeks)**

**Week 1: Consolidate & Extract**

*   **Story 2.2.1.1**: Delete 8 summary/report files immediately (e.g., `AUDIT_COMPLIANCE_ACHIEVEMENT_REPORT.md`, `DOCUMENTATION_AUDIT_CONSOLIDATED_REPORT.md`, `DOCUMENTATION_LINK_AUDIT_REPORT.md`, `DOCUMENTATION_STATUS_REPORT.md`, `SOLO_DEV_ENHANCEMENT_SUMMARY.md`, `search_optimization_summary.md`, `link_audit_report.json`, `docs_health_report.html`).
*   **Story 2.2.1.2**: Extract critical troubleshooting patterns from existing documentation and prepare them for inclusion in `CLAUDE.md` files.
*   **Story 2.2.1.3**: Merge duplicate API documentation (e.g., from `docs_src/development/api-reference.md` and `tools/visualizer/API_REFERENCE.md`) into a single authoritative source.
*   **Story 2.2.1.4**: Merge deployment guides (e.g., `docs_src/deployment/discord-setup.md` and `tools/visualizer/DEPLOYMENT_GUIDE.md`) into a single authoritative source.

**Week 2: Create User Documentation**

*   **Story 2.2.2.1**: Create `docs_src/user-guide/visualizer/index.md` (Quick start hub).
*   **Story 2.2.2.2**: Create `docs_src/user-guide/visualizer/daily-tasks.md` (Common workflows).
*   **Story 2.2.2.3**: Create `docs_src/user-guide/visualizer/commands.md` (Command reference).
*   **Story 2.2.2.4**: Create `docs_src/user-guide/visualizer/troubleshooting.md` (Self-service fixes).
*   **Story 2.2.2.5**: Create `docs_src/user-guide/visualizer/integrations.md` (External tools).

**Week 3: Create Engineering Documentation**

*   **Story 2.2.3.1**: Create `docs_src/architecture/visualizer/overview.md` (System architecture).
*   **Story 2.2.3.2**: Create `docs_src/architecture/visualizer/decisions/` directory and populate with ADRs (e.g., `ADR-001-websocket.md`, `ADR-002-nuclear-css.md`, `ADR-003-multi-project.md`).
*   **Story 2.2.3.3**: Create `docs_src/architecture/visualizer/api-reference.md` (Complete API docs).
*   **Story 2.2.3.4**: Create `docs_src/architecture/visualizer/patterns.md` (Code patterns).
*   **Story 2.2.3.5**: Create `docs_src/architecture/visualizer/extending.md` (Integration guide).

**Week 4: Enhance AI Context**

*   **Story 2.2.4.1**: Update `CLAUDE.md` (root) with high-level implementation insights and troubleshooting patterns.
*   **Story 2.2.4.2**: Update `agent_workflow/CLAUDE.md` with package-specific insights.
*   **Story 2.2.4.3**: Update `docs_src/CLAUDE.md` with documentation architecture decisions and rationale.
*   **Story 2.2.4.4**: Update `lib/CLAUDE.md` (if not yet deleted) with legacy insights, or ensure its content is migrated to the new `agent_workflow` `CLAUDE.md`.
*   **Story 2.2.4.5**: Update `tools/visualizer/CLAUDE.md` with specific troubleshooting and architectural decisions for the visualizer.

---

### **Key Design Decisions**

**User Documentation Philosophy**

*   **Progressive Disclosure**: Basic → Advanced
*   **Task-Oriented**: "How do I..." not "Feature X does..."
*   **Visual Learning**: Screenshots for every major task
*   **Mobile-Friendly**: Responsive design throughout

**Engineering Documentation Philosophy**

*   **Decision Records**: Document WHY, not just HOW
*   **Pattern Library**: Reusable solutions with examples
*   **Integration Focus**: Clear extension points
*   **Maintenance Playbooks**: Operational procedures

**Content Migration Rules**

1.  **Summary files** → Extract insights to `CLAUDE.md`, then delete
2.  **Duplicate content** → Merge into single authoritative source
3.  **User content** → Task-oriented guides with visuals
4.  **Technical content** → Reference docs with code examples
5.  **Troubleshooting** → Both streams + `CLAUDE.md`

---

### **Success Metrics**

*   **Documentation findability**: 90% of answers within 2 clicks
*   **File reduction**: 60% fewer files to maintain
*   **Knowledge preservation**: 100% of valuable content retained
*   **AI assistance**: Enhanced `CLAUDE.md` improves development speed
*   **User success**: Reduced support tickets by 40%

---

### **Acceptance Criteria**

*   The `docs_src/user-guide/visualizer/` directory is created and populated with the specified user documentation files.
*   The `docs_src/architecture/visualizer/` directory is created and populated with the specified engineering documentation files, including the `decisions/` subdirectory.
*   All `CLAUDE.md` files are updated with relevant troubleshooting, architectural decisions, and implementation insights.
*   The 8 specified summary/report files are deleted from the root directory.
*   Duplicate API documentation and deployment guides are merged into single, authoritative sources.
*   The total number of documentation files is reduced by at least 60%.
*   All valuable content from the original 62 documentation files is preserved in the new structure or in `CLAUDE.md` files.
