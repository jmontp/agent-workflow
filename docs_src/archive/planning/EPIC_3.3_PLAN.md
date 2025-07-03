# Epic 3.3 Plan: Update Web Visualizer

**Objective**: Update the web visualizer's backend to use the new, unified `agent_workflow` package APIs. This will ensure the visualizer functions correctly with the refactored codebase and leverages the new, centralized logic.

---

### **Part 1: Update Visualizer Backend Imports**

**Summary**: Modify `tools/visualizer/app.py` to replace old `lib` imports with references to the new `agent_workflow` package structure.

**Source File**:
*   `tools/visualizer/app.py`

**Step-by-Step Instructions**:

1.  **Open `tools/visualizer/app.py`**.
2.  **Identify and Replace Imports**: Systematically go through the file and replace imports that point to the old `lib` directory with their new `agent_workflow` equivalents. This will involve:
    *   Changing `from lib.state_broadcaster import broadcaster` to `from agent_workflow.integrations.broadcaster import broadcaster` (assuming `state_broadcaster.py` is moved/merged into `agent_workflow/integrations/broadcaster.py` in a previous epic).
    *   Changing `from lib.agent_interfaces import interface_manager` to `from agent_workflow.integrations.agent_interfaces import interface_manager`.
    *   Changing `from lib.security import ...` to `from agent_workflow.security import ...`.
    *   Changing `from lib.multi_project_config import MultiProjectConfigManager` to `from agent_workflow.config.multi_project import MultiProjectConfigManager`.
    *   Changing `from lib.collaboration_manager import ...` to `from agent_workflow.integrations.collaboration import ...`.
    *   Changing `from lib.command_processor import CommandProcessor` to `from agent_workflow.cli.command_processor import CommandProcessor`.
    *   Changing `from lib.state_machine import StateMachine` to `from agent_workflow.core.state_machine import StateMachine`.
    *   Changing `from lib.tdd_models import ...` to `from agent_workflow.core.models import ...`.
    *   Changing `from lib.data_models import ...` to `from agent_workflow.core.models import ...`.
    *   Changing `from lib.context_manager_factory import ...` to `from agent_workflow.context.factory import ...`.
3.  **Update Internal Logic**: Review the code where these imported modules are used. Ensure that function calls and object instantiations are compatible with the new API of the `agent_workflow` package. This might involve minor adjustments to arguments or return values if the API has changed during the merge process.

---

### **Part 2: Test Visualizer Functionality**

**Summary**: Verify that the web visualizer functions correctly with the refactored backend.

**Source Files**:
*   `tools/visualizer/test_chat.py`
*   `tools/visualizer/test_final_fixes.py`
*   `tests/integration/test_responsive_design.py` (if applicable to visualizer)

**Step-by-Step Instructions**:

1.  **Run Visualizer Tests**: Execute the existing tests for the visualizer:
    *   `python tools/visualizer/test_chat.py`
    *   `python tools/visualizer/test_final_fixes.py`
2.  **Manual Verification**: Start the visualizer (`aw web`) and manually test its key functionalities:
    *   Verify real-time state updates.
    *   Test chat commands and responses.
    *   Check multi-project switching (if enabled).
    *   Ensure all UI elements (diagrams, logs, etc.) display correctly.
    *   Verify responsiveness on different screen sizes.

---

### **Acceptance Criteria**

*   The `tools/visualizer/app.py` file no longer imports from the `lib/` directory.
*   All imports in `tools/visualizer/app.py` correctly point to the `agent_workflow` package structure.
*   The web visualizer starts and runs without errors.
*   All automated tests for the visualizer pass successfully.
*   Manual testing confirms that all visualizer functionalities (real-time updates, chat, commands, multi-project support) work as expected with the refactored backend.
