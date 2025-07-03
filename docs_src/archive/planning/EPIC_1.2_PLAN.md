# Epic 1.2 Plan: Migrate Core Logic

**Objective**: Migrate core logic components, specifically project storage and orchestrator functionality, from the `lib` and `scripts` directories into the `agent_workflow/core` package. This will centralize core functionalities within the modern package structure.

---

### **Part 1: Project Storage Migration**

**Summary**: Move `lib/project_storage.py` to `agent_workflow/core/storage.py` and update its dependencies.

**Source File**:
1.  `lib/project_storage.py`

**Destination File**:
*   `agent_workflow/core/storage.py` (This file will be created by moving `lib/project_storage.py`)

**Step-by-Step Instructions**:

1.  **Move File**: Move `lib/project_storage.py` to `agent_workflow/core/storage.py`.
2.  **Update Imports**: Open `agent_workflow/core/storage.py` and update its imports:
    *   Change `from lib.data_models import ProjectData, Epic, Story, Sprint` to `from .models import ProjectData, Epic, Story, Sprint`.
    *   Change `from lib.tdd_models import TDDCycle` to `from .models import TDDCycle`.
3.  **Delete Old File**: After the move is complete and verified by tests, delete `lib/project_storage.py`.

---

### **Part 2: Orchestrator Migration and Unification**

**Summary**: Merge the logic from `lib/global_orchestrator.py` and `scripts/orchestrator.py` into `agent_workflow/core/orchestrator.py`. The goal is to create a single, comprehensive orchestrator that handles both single-project and multi-project coordination.

**Source Files**:
1.  `lib/global_orchestrator.py`
2.  `scripts/orchestrator.py`
3.  `agent_workflow/core/orchestrator.py` (target for merge)

**Destination File**:
*   `agent_workflow/core/orchestrator.py`

**Step-by-Step Instructions**:

1.  **Read All Source Files**: Ingest the full content of all three orchestrator files.
2.  **Unify Orchestrator Class**: Modify the `Orchestrator` class in `agent_workflow/core/orchestrator.py` to incorporate the functionalities from `lib/global_orchestrator.py` and `scripts/orchestrator.py`.
    *   The `Orchestrator` class should manage both single-project workflows (like `scripts/orchestrator.py`) and multi-project coordination (like `lib/global_orchestrator.py`). This might involve adding a `mode` parameter to its initialization or methods to switch between single/multi-project contexts.
    *   Integrate resource allocation, scheduling, security, monitoring, and cross-project intelligence features from `lib/global_orchestrator.py`.
    *   Integrate the Human-in-the-Loop (HITL) approval processes and agent coordination logic from `scripts/orchestrator.py`.
3.  **Consolidate Configuration Loading**: Unify how the orchestrator loads its configuration, supporting both global and project-specific settings.
4.  **Update Internal References**: Ensure all internal references within the merged `orchestrator.py` point to the new `agent_workflow.core.models` and `agent_workflow.core.state_machine`.
5.  **Delete Old Files**: After the merge is complete and verified by tests, delete `lib/global_orchestrator.py` and `scripts/orchestrator.py`.

---

### **Part 3: Test Migration**

**Summary**: Consolidate the unit tests for the migrated project storage and orchestrator components.

**Source Files**:
1.  `tests/unit/test_project_storage.py`
2.  `tests/unit/test_global_orchestrator.py`
3.  `tests/integration/test_orchestrator_commands.py`
4.  `tests/integration/test_multi_project_orchestration.py`

**Destination Files**:
1.  `tests/unit/test_storage.py` (new file)
2.  `tests/unit/test_orchestrator.py` (new file)
3.  `tests/integration/test_orchestration.py` (new file)

**Step-by-Step Instructions**:

1.  **Migrate Project Storage Tests**:
    *   Create a new test file: `tests/unit/test_storage.py`.
    *   Copy all test classes and methods from `tests/unit/test_project_storage.py` into the new `test_storage.py`.
    *   Update all imports in the new file to point to `agent_workflow.core.storage` and `agent_workflow.core.models`.
2.  **Migrate Unit Orchestrator Tests**:
    *   Create a new test file: `tests/unit/test_orchestrator.py`.
    *   Copy all test classes and methods from `tests/unit/test_global_orchestrator.py` into the new `test_orchestrator.py`.
    *   Update all imports in the new file to point to `agent_workflow.core.orchestrator` and `agent_workflow.core.models`.
3.  **Migrate Integration Orchestration Tests**:
    *   Create a new test file: `tests/integration/test_orchestration.py`.
    *   Copy relevant integration tests from `tests/integration/test_orchestrator_commands.py` and `tests/integration/test_multi_project_orchestration.py` into the new `test_orchestration.py`.
    *   Ensure these tests cover the unified orchestrator's single-project and multi-project functionalities.
    *   Update all imports in the new file to point to `agent_workflow.core.orchestrator` and other relevant `agent_workflow.core` modules.
4.  **Delete Old Test Files**: After the migration is complete and all tests pass, delete `tests/unit/test_project_storage.py`, `tests/unit/test_global_orchestrator.py`, `tests/integration/test_orchestrator_commands.py`, and `tests/integration/test_multi_project_orchestration.py`.

---

### **Acceptance Criteria**

*   The `lib/project_storage.py`, `lib/global_orchestrator.py`, and `scripts/orchestrator.py` files are deleted.
*   The `agent_workflow/core/storage.py` file contains the complete project storage logic.
*   The `agent_workflow/core/orchestrator.py` file contains the single, unified orchestrator logic for both single and multi-project management.
*   The corresponding unit and integration tests are migrated, updated, and all pass successfully.
*   The project remains fully functional after these changes.
