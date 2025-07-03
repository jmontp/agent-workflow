# Epic 1.4 Plan: Migrate Context Management and Integrations

**Objective**: Migrate context management components and external integrations (Discord, Claude client) from the `lib` directory into the `agent_workflow` package. This will centralize these functionalities within the modern package structure.

---

### **Part 1: Context Management Migration**

**Summary**: Move all `context_*.py` files from `lib/` to a new `agent_workflow/context/` directory and update their dependencies.

**Source Files**:
*   All `.py` files within `lib/` that start with `context_` (e.g., `lib/context_manager.py`, `lib/context_filter.py`, `lib/context_compressor.py`, `lib/context_index.py`, `lib/context_cache.py`, `lib/context_background.py`, `lib/context_config.py`, `lib/context_exceptions.py`, `lib/context_infrastructure.py`, `lib/context_intelligence.py`, `lib/context_interfaces.py`, `lib/context_learning.py`, `lib/context_manager_factory.py`, `lib/context_monitoring.py`, `lib/context_models.py`)

**Destination Directory**:
*   `agent_workflow/context/` (This directory will be created if it doesn't exist)

**Step-by-Step Instructions**:

1.  **Create Destination Directory**: Ensure the `agent_workflow/context/` directory exists. If not, create it.
2.  **Move Files**: Move all `.py` files from `lib/` that start with `context_` into `agent_workflow/context/`.
3.  **Update Imports**: For each moved file in `agent_workflow/context/`:
    *   Review and update any relative imports that previously pointed to other `lib` modules. For example, if a context module imported `from .token_calculator import TokenCalculator`, it should be updated to `from ..token_calculator import TokenCalculator` (assuming `token_calculator.py` is moved to `agent_workflow/token_calculator.py` in a later epic, or `from ..core.token_calculator import TokenCalculator` if it's part of core).
    *   Ensure imports for `tdd_models` point to their new location (e.g., `from ..core.models import TDDState`).
4.  **Delete Old Files**: After all files are moved and their imports updated, delete the original `context_*.py` files from `lib/`.

---

### **Part 2: Discord Integration Migration**

**Summary**: Merge `lib/discord_bot.py` and `lib/multi_project_discord_bot.py` into a single, unified Discord client within `agent_workflow/integrations/discord/`.

**Source Files**:
1.  `lib/discord_bot.py`
2.  `lib/multi_project_discord_bot.py`

**Destination File**:
*   `agent_workflow/integrations/discord/client.py` (This file will be created)

**Step-by-Step Instructions**:

1.  **Create Destination Directory**: Ensure the `agent_workflow/integrations/discord/` directory exists. If not, create it.
2.  **Merge Logic**: Create a new file `agent_workflow/integrations/discord/client.py`.
    *   The new `client.py` should contain a single `DiscordClient` class (or similar name) that combines the functionalities of both `WorkflowBot` (from `lib/discord_bot.py`) and `MultiProjectDiscordBot` (from `lib/multi_project_discord_bot.py`).
    *   The unified client should support both single-project and multi-project modes, project-specific channels, and the full range of commands.
3.  **Update Imports**: Review and update all imports within the new `client.py` to point to their correct locations within the `agent_workflow` package (e.g., `from ..core.orchestrator import Orchestrator`, `from ..core.models import ProjectData`).
4.  **Delete Old Files**: After the merge is complete and verified by tests, delete `lib/discord_bot.py` and `lib/multi_project_discord_bot.py`.

---

### **Part 3: Claude Client Migration**

**Summary**: Move `lib/claude_client.py` to `agent_workflow/integrations/claude/client.py` and update its dependencies.

**Source File**:
1.  `lib/claude_client.py`

**Destination File**:
*   `agent_workflow/integrations/claude/client.py` (This file will be created by moving `lib/claude_client.py`)

**Step-by-Step Instructions**:

1.  **Create Destination Directory**: Ensure the `agent_workflow/integrations/claude/` directory exists. If not, create it.
2.  **Move File**: Move `lib/claude_client.py` to `agent_workflow/integrations/claude/client.py`.
3.  **Update Imports**: Open `agent_workflow/integrations/claude/client.py` and update its imports. For example, if it imports `AgentType` from `lib.agent_tool_config`, it should be updated to `from ...security.tool_config import AgentType`.
4.  **Delete Old File**: After the move is complete and verified by tests, delete `lib/claude_client.py`.

---

### **Part 4: Test Migration**

**Summary**: Consolidate and update the unit tests for the migrated context management components and integrations.

**Source Files**:
*   All `tests/unit/test_context_*.py` files (e.g., `test_context_manager.py`, `test_context_filter.py`, `test_context_compressor.py`, `test_context_index.py`, `test_context_cache.py`, etc.)
*   `tests/unit/test_discord_bot.py`
*   `tests/unit/test_multi_project_discord_bot.py`
*   `tests/unit/test_claude_client.py`

**Destination Files**:
1.  `tests/unit/test_context.py` (new file, consolidating all context tests)
2.  `tests/unit/test_integrations.py` (new file, consolidating integration tests)

**Step-by-Step Instructions**:

1.  **Migrate Context Tests**:
    *   Create a new test file: `tests/unit/test_context.py`.
    *   Copy all test classes and methods from all `tests/unit/test_context_*.py` files into the new `test_context.py`.
    *   Update all imports in the new file to point to `agent_workflow.context` and other relevant `agent_workflow` modules.
2.  **Migrate Integration Tests**:
    *   Create a new test file: `tests/unit/test_integrations.py`.
    *   Copy all test classes and methods from `tests/unit/test_discord_bot.py`, `tests/unit/test_multi_project_discord_bot.py`, and `tests/unit/test_claude_client.py` into the new `test_integrations.py`.
    *   Update all imports in the new file to point to `agent_workflow.integrations.discord.client` and `agent_workflow.integrations.claude.client`.
3.  **Delete Old Test Files**: After the migration is complete and all tests pass, delete all original `tests/unit/test_context_*.py` files, `tests/unit/test_discord_bot.py`, `tests/unit/test_multi_project_discord_bot.py`, and `tests/unit/test_claude_client.py`.

---

### **Acceptance Criteria**

*   All `context_*.py` files are deleted from `lib/`.
*   The `lib/discord_bot.py` and `lib/multi_project_discord_bot.py` files are deleted.
*   The `lib/claude_client.py` file is deleted.
*   The `agent_workflow/context/` directory contains all context management components.
*   The `agent_workflow/integrations/discord/client.py` file contains the unified Discord client.
*   The `agent_workflow/integrations/claude/client.py` file contains the Claude client.
*   The corresponding unit tests are migrated, updated, and all pass successfully.
*   The project remains fully functional after these changes.
