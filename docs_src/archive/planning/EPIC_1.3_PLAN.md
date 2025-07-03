# Epic 1.3 Plan: Migrate Agents and Security

**Objective**: Migrate AI agent implementations and the security configuration from the `lib` directory into the `agent_workflow` package. This will centralize agent-related logic and security definitions within the modern package structure.

---

### **Part 1: Agent Implementation Migration**

**Summary**: Move the agent implementations from `lib/agents/` to a new `agent_workflow/agents/` directory and update their dependencies.

**Source Files**:
*   All `.py` files within `lib/agents/` (e.g., `lib/agents/code_agent.py`, `lib/agents/design_agent.py`, `lib/agents/qa_agent.py`, `lib/agents/data_agent.py`, `lib/agents/mock_agent.py`)

**Destination Directory**:
*   `agent_workflow/agents/` (This directory will be created if it doesn't exist)

**Step-by-Step Instructions**:

1.  **Create Destination Directory**: Ensure the `agent_workflow/agents/` directory exists. If not, create it.
2.  **Move Files**: Move all `.py` files from `lib/agents/` to `agent_workflow/agents/`.
3.  **Update Imports**: For each moved file in `agent_workflow/agents/`:
    *   Review and update any relative imports that previously pointed to other `lib` modules. For example, if an agent imported `from ..context_manager import ContextManager`, it should be updated to `from ..context.manager import ContextManager` (assuming `ContextManager` is moved to `agent_workflow/context/manager.py` in Epic 1.4).
    *   Ensure imports for `tdd_models` and `tdd_state_machine` point to their new locations (e.g., `from ..core.models import TDDState` and `from ..core.state_machine import TDDStateMachine`).
4.  **Delete Old Directory**: After all files are moved and their imports updated, delete the `lib/agents/` directory.

---

### **Part 2: Agent Tool Configuration Migration**

**Summary**: Move `lib/agent_tool_config.py` to `agent_workflow/security/tool_config.py` and update its dependencies.

**Source File**:
1.  `lib/agent_tool_config.py`

**Destination File**:
*   `agent_workflow/security/tool_config.py` (This file will be created by moving `lib/agent_tool_config.py`)

**Step-by-Step Instructions**:

1.  **Create Destination Directory**: Ensure the `agent_workflow/security/` directory exists. If not, create it.
2.  **Move File**: Move `lib/agent_tool_config.py` to `agent_workflow/security/tool_config.py`.
3.  **Update Imports**: Open `agent_workflow/security/tool_config.py` and update its imports. For example, if it imports `AgentType` from a relative path, ensure it's correctly defined or imported from within the `agent_workflow` package structure.
4.  **Delete Old File**: After the move is complete and verified by tests, delete `lib/agent_tool_config.py`.

---

### **Part 3: Test Migration**

**Summary**: Consolidate and update the unit tests for the migrated agents and security configuration.

**Source Files**:
1.  `tests/unit/test_agent_tool_config.py`
2.  `tests/unit/test_agents_base_agent.py`
3.  `tests/unit/test_agents_code_agent.py`
4.  `tests/unit/test_agents_data_agent.py`
5.  `tests/unit/test_agents_design_agent.py`
6.  `tests/unit/test_agents_qa_agent.py`
7.  `tests/unit/test_mock_agent.py`

**Destination Files**:
1.  `tests/unit/test_agents.py` (new file, consolidating all agent tests)
2.  `tests/unit/test_security.py` (new file, consolidating security tests)

**Step-by-Step Instructions**:

1.  **Migrate Agent Tests**:
    *   Create a new test file: `tests/unit/test_agents.py`.
    *   Copy all test classes and methods from `tests/unit/test_agents_base_agent.py`, `tests/unit/test_agents_code_agent.py`, `tests/unit/test_agents_data_agent.py`, `tests/unit/test_agents_design_agent.py`, `tests/unit/test_agents_qa_agent.py`, and `tests/unit/test_mock_agent.py` into the new `test_agents.py`.
    *   Update all imports in the new file to point to `agent_workflow.agents` and other relevant `agent_workflow` modules.
2.  **Migrate Security Tests**:
    *   Create a new test file: `tests/unit/test_security.py`.
    *   Copy all test classes and methods from `tests/unit/test_agent_tool_config.py` into the new `test_security.py`.
    *   Update all imports in the new file to point to `agent_workflow.security.tool_config` and other relevant `agent_workflow` modules.
3.  **Delete Old Test Files**: After the migration is complete and all tests pass, delete `tests/unit/test_agent_tool_config.py`, `tests/unit/test_agents_base_agent.py`, `tests/unit/test_agents_code_agent.py`, `tests/unit/test_agents_data_agent.py`, `tests/unit/test_agents_design_agent.py`, `tests/unit/test_agents_qa_agent.py`, and `tests/unit/test_mock_agent.py`.

---

### **Acceptance Criteria**

*   The `lib/agents/` directory is deleted.
*   The `lib/agent_tool_config.py` file is deleted.
*   The `agent_workflow/agents/` directory contains all agent implementations.
*   The `agent_workflow/security/tool_config.py` file contains the agent tool configuration.
*   The corresponding unit tests are migrated, updated, and all pass successfully.
*   The project remains fully functional after these changes.
