# Epic 1.5 Plan: Finalize Migration and Cleanup

**Objective**: Complete the architectural unification by updating all remaining imports to the new `agent_workflow` package structure and removing the deprecated `lib` and `scripts` directories. This is a critical step to ensure a clean, single source of truth for the codebase.

---

### **Part 1: Update All Imports**

**Summary**: Systematically update all `import` statements across the entire `agent_workflow` package to reflect the new, unified structure. This is a project-wide change that requires careful attention to detail.

**Scope**:
*   All `.py` files within the `agent_workflow/` directory and its subdirectories.
*   All `.py` files within the `tests/` directory and its subdirectories.
*   All `.py` files within the `tools/` directory and its subdirectories (especially `tools/visualizer/`).

**Step-by-Step Instructions**:

1.  **Identify Old Imports**: Search for imports that still reference the old `lib` or `scripts` directories. Examples:
    *   `from lib.some_module import ...`
    *   `from scripts.some_script import ...`
    *   Relative imports within `lib` that now need to be absolute or relative to `agent_workflow`.
2.  **Map to New Structure**: For each identified old import, determine its new absolute path within the `agent_workflow` package. Refer to the migration plans for Epic 1.1, 1.2, 1.3, and 1.4 for the new locations of modules.
    *   `lib/data_models.py` -> `agent_workflow.core.models`
    *   `lib/tdd_models.py` -> `agent_workflow.core.models`
    *   `lib/state_machine.py` -> `agent_workflow.core.state_machine`
    *   `lib/tdd_state_machine.py` -> `agent_workflow.core.state_machine`
    *   `lib/project_storage.py` -> `agent_workflow.core.storage`
    *   `lib/global_orchestrator.py` -> `agent_workflow.core.orchestrator`
    *   `scripts/orchestrator.py` -> `agent_workflow.core.orchestrator`
    *   `scripts/multi_project_orchestrator.py` -> `agent_workflow.core.orchestrator` (merged into the main orchestrator)
    *   `lib/agents/*` -> `agent_workflow.agents.*`
    *   `lib/agent_tool_config.py` -> `agent_workflow.security.tool_config`
    *   `lib/context_*.py` -> `agent_workflow.context.*`
    *   `lib/discord_bot.py` -> `agent_workflow.integrations.discord.client`
    *   `lib/multi_project_discord_bot.py` -> `agent_workflow.integrations.discord.client`
    *   `lib/claude_client.py` -> `agent_workflow.integrations.claude.client`
3.  **Perform Replacements**: Systematically replace the old import statements with the new ones. Be mindful of relative vs. absolute imports based on the file's location.
    *   Example: `from lib.data_models import Epic` might become `from agent_workflow.core.models import Epic`.
    *   Example: In `agent_workflow/agents/code_agent.py`, `from ..claude_client import create_agent_client` might become `from ..integrations.claude.client import create_agent_client`.
4.  **Run Tests**: After each significant batch of import changes, run the entire test suite to catch any errors immediately. This is crucial for maintaining stability.

---

### **Part 2: Delete Deprecated Directories**

**Summary**: Remove the `lib` and `scripts` directories from the project, as all their functionalities will have been migrated.

**Step-by-Step Instructions**:

1.  **Verify Migration**: Ensure that all files and functionalities from `lib/` and `scripts/` have been successfully migrated to the `agent_workflow/` package and that all tests pass.
2.  **Delete `lib` Directory**: Remove the entire `lib/` directory from the project root.
3.  **Delete `scripts` Directory**: Remove the entire `scripts/` directory from the project root.
4.  **Update `.gitignore`**: Review and update the `.gitignore` file to remove any entries related to the `lib` or `scripts` directories if they are no longer needed.

---

### **Acceptance Criteria**

*   The `lib/` directory is completely removed from the project.
*   The `scripts/` directory is completely removed from the project.
*   All Python files in the project (within `agent_workflow/`, `tests/`, `tools/`) use the new, unified `agent_workflow` package structure for imports.
*   The entire test suite passes successfully after all import changes and directory deletions.
*   The project can be run and all core functionalities are accessible via the `agent-orch` (or `aw`) CLI commands.
