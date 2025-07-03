# Epic 1.1 Plan: Migrate Core Data Models and State Machines

**Objective**: Consolidate the data models and state machines from the `lib` directory into the `agent_workflow/core` package. This will unify the core logic and remove redundant, legacy implementations.

---

### **Part 1: Data Model Migration**

**Summary**: Merge the contents of `lib/data_models.py` and `lib/tdd_models.py` into a single, comprehensive `agent_workflow/core/models.py`.

**Source Files**:
1.  `lib/data_models.py`
2.  `lib/tdd_models.py`
3.  `agent_workflow/core/data_models.py` (target for merge)

**Destination File**:
*   `agent_workflow/core/models.py` (This file will be created by renaming `agent_workflow/core/data_models.py` and then modifying it)

**Step-by-Step Instructions**:

1.  **Rename Destination File**: Rename `agent_workflow/core/data_models.py` to `agent_workflow/core/models.py`.
2.  **Read All Source Files**: Ingest the full content of `lib/data_models.py`, `lib/tdd_models.py`, and the newly renamed `agent_workflow/core/models.py`.
3.  **Merge `Epic` classes**:
    *   The `Epic` class in `lib/data_models.py` is more feature-rich.
    *   Modify the `Epic` class in `agent_workflow/core/models.py` to include all fields from the `lib` version, such as `tdd_requirements` and `tdd_constraints`.
    *   Ensure the final `Epic` class has a complete `to_dict` and `from_dict` method that handles all fields.
4.  **Merge `Story` classes**:
    *   Similarly, the `Story` class in `lib/data_models.py` contains TDD-specific fields (`tdd_cycle_id`, `test_status`, etc.).
    *   Add these fields to the `Story` class in `agent_workflow/core/models.py`.
5.  **Merge `Sprint` classes**:
    *   Add the TDD-related fields (`active_tdd_cycles`, `tdd_metrics`) from the `Sprint` class in `lib/data_models.py` to the one in `agent_workflow/core/models.py`.
6.  **Incorporate TDD Models**:
    *   Copy all classes from `lib/tdd_models.py` (e.g., `TDDState`, `TestStatus`, `CIStatus`, `TestFile`, `TDDTask`, `TDDCycle`) directly into `agent_workflow/core/models.py`.
7.  **Consolidate Enums**:
    *   Ensure all `Enum` classes (`EpicStatus`, `StoryStatus`, `SprintStatus`, etc.) are present in the final `agent_workflow/core/models.py`. Resolve any naming conflicts by choosing the more comprehensive version from the `lib` files.
8.  **Update Imports**: Review the newly created `agent_workflow/core/models.py` and ensure all internal type hints and imports (like `from enum import Enum`, `from typing import ...`) are correct and complete.
9.  **Delete Old Files**: After the merge is complete and verified by tests, delete `lib/data_models.py` and `lib/tdd_models.py`.

---

### **Part 2: State Machine Migration**

**Summary**: Merge `lib/state_machine.py` and `lib/tdd_state_machine.py` into a single, unified `agent_workflow/core/state_machine.py`.

**Source Files**:
1.  `lib/state_machine.py`
2.  `lib/tdd_state_machine.py`
3.  `agent_workflow/core/state_machine.py` (target for merge)

**Destination File**:
*   `agent_workflow/core/state_machine.py`

**Step-by-Step Instructions**:

1.  **Read All Source Files**: Ingest the full content of all three state machine files.
2.  **Unify State Machines**: Modify the `StateMachine` class in `agent_workflow/core/state_machine.py` to incorporate the logic from the other two files.
    *   The final `StateMachine` should manage the main workflow states (IDLE, SPRINT_ACTIVE, etc.).
    *   It should also be capable of managing the TDD sub-workflow states (DESIGN, TEST_RED, etc.). This can be achieved by adding methods and attributes to track the active TDD cycle and its state, similar to the logic in `lib/tdd_state_machine.py`.
3.  **Merge Transitions**: Consolidate the `TRANSITIONS` dictionaries from both `lib` state machine files into the `agent_workflow` version. Ensure all commands and state transitions are represented.
4.  **Update Methods**: Merge the methods for command validation, state transitions, and diagram generation. The final `StateMachine` should have a unified set of methods to handle both main workflow and TDD commands.
5.  **Delete Old Files**: After the merge is complete and verified by tests, delete `lib/state_machine.py` and `lib/tdd_state_machine.py`.

---

### **Part 3: Test Migration**

**Summary**: Consolidate the unit tests for the migrated models and state machines.

**Source Files**:
1.  `tests/unit/test_data_models.py`
2.  `tests/unit/test_tdd_models.py`
3.  `tests/unit/test_state_machine.py`
4.  `tests/unit/test_tdd_state_machine.py`

**Destination Files**:
1.  `tests/unit/test_models.py` (new file)
2.  `tests/unit/test_state_machine.py` (existing file to be updated)

**Step-by-Step Instructions**:

1.  **Merge Model Tests**:
    *   Create a new test file: `tests/unit/test_models.py`.
    *   Copy all test classes and methods from `tests/unit/test_data_models.py` and `tests/unit/test_tdd_models.py` into the new `test_models.py`.
    *   Update all imports in the new file to point to `agent_workflow.core.models`.
    *   Ensure the tests cover the unified `Epic`, `Story`, and `Sprint` classes, as well as the new TDD models.
2.  **Merge State Machine Tests**:
    *   Merge the test cases from `tests/unit/test_tdd_state_machine.py` into `tests/unit/test_state_machine.py`.
    *   Update the tests to target the new, unified `StateMachine` class in `agent_workflow.core.state_machine`.
    *   Ensure the tests validate both main workflow and TDD sub-workflow transitions.
3.  **Delete Old Test Files**: After the merge is complete and all tests pass, delete `tests/unit/test_data_models.py`, `tests/unit/test_tdd_models.py`, and `tests/unit/test_tdd_state_machine.py`.

---

### **Acceptance Criteria**

*   The `lib/data_models.py`, `lib/tdd_models.py`, `lib/state_machine.py`, and `lib/tdd_state_machine.py` files are deleted.
*   The `agent_workflow/core/models.py` file contains the complete, unified data models for the project.
*   The `agent_workflow/core/state_machine.py` file contains the single, unified state machine for the project.
*   The corresponding unit tests are merged, updated, and all pass successfully.
*   The project remains fully functional after these changes.
