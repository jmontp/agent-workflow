# Epic 4.2 Plan: Update Final Documentation

**Objective**: Update the main `README.md` and the root `CLAUDE.md` to reflect the new, simplified project structure and CLI-first workflow. This ensures that the primary entry points for human and AI developers are accurate and helpful after the refactoring.

---

### **Part 1: Update Main `README.md`**

**Summary**: Revise the `README.md` file to provide an up-to-date overview of the refactored project, focusing on the new structure, CLI usage, and key features.

**Destination File**:
*   `README.md`

**Step-by-Step Instructions**:

1.  **Review Existing Content**: Read the current `README.md` to understand its existing sections (e.g., project overview, quick start, installation, usage, development).
2.  **Update Project Overview**: Rewrite the project overview to clearly state that the project is now a single, unified Python package (`agent-workflow`). Emphasize the benefits of the refactoring (simplicity, maintainability).
3.  **Revise Quick Start/Installation**: Update the quick start and installation instructions to reflect the new `pip install agent-workflow` (or `pip install -e .` for development) and the `aw init` command. Remove any references to cloning the `lib` or `scripts` directories.
4.  **Update Usage Section**: Focus on the `agent-orch` (or `aw`) CLI as the primary interface. Provide examples for key commands like `aw start`, `aw status`, `aw projects`, and the new `aw dev` commands.
5.  **Update Development Section**: Describe the new, consolidated project structure (e.g., `agent_workflow/core`, `agent_workflow/agents`, `agent_workflow/context`). Explain how to contribute to the unified codebase.
6.  **Remove Obsolete Information**: Delete any sections or references that are no longer relevant due to the refactoring (e.g., detailed explanations of the dual architecture, references to specific `lib` or `scripts` files).
7.  **Link to New Documentation**: Ensure prominent links to the new User Manual (`docs_src/user-guide/visualizer/`) and Engineering Reference (`docs_src/architecture/visualizer/`) are included.

---

### **Part 2: Update Root `CLAUDE.md`**

**Summary**: Enhance the root `CLAUDE.md` file to serve as the primary guide for AI agents working on the refactored project. It should provide a concise, high-level overview of the new architecture and key development patterns.

**Destination File**:
*   `CLAUDE.md`

**Step-by-Step Instructions**:

1.  **Review Existing Content**: Read the current root `CLAUDE.md`.
2.  **Update Repository Overview**: Clearly state the new, unified architecture. Explain that all core logic is now within the `agent_workflow` package.
3.  **Revise Repository Structure**: Provide an updated, simplified directory structure diagram that reflects the post-refactoring layout (e.g., `agent_workflow/`, `docs_src/`, `tests/`, `tools/visualizer/`).
4.  **Update Core System Architecture**: Describe the key components and their new locations within the `agent_workflow` package (e.g., `agent_workflow.core.orchestrator`, `agent_workflow.core.state_machine`, `agent_workflow.context`).
5.  **Refine Development Workflow**: Emphasize the CLI-first development workflow using `aw` commands. Highlight the new `aw dev` commands for common development tasks.
6.  **Integrate Troubleshooting Patterns**: Incorporate the critical troubleshooting patterns and insights extracted during Epic 2.2 into relevant sections of the `CLAUDE.md`. This makes it a valuable resource for AI agents encountering issues.
7.  **Add Architectural Decisions**: Briefly summarize key architectural decisions and their rationale, especially those that might impact how an AI agent approaches a task.
8.  **Remove Obsolete Information**: Delete any sections or references that are no longer relevant (e.g., detailed explanations of the `lib` directory, redundant `CLAUDE.md` references).

---

### **Acceptance Criteria**

*   The `README.md` accurately describes the refactored project, its new structure, and CLI-first usage.
*   The root `CLAUDE.md` provides a clear, concise guide for AI agents, reflecting the new architecture and development patterns.
*   Both `README.md` and `CLAUDE.md` are free of references to the old `lib` and `scripts` directories.
*   All links within these files are updated and functional.
*   The overall project documentation is consistent with the refactored codebase.
