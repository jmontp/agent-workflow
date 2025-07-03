# Epic 2.1 Plan: Consolidate Test Suite

**Objective**: Reduce the number of test files by merging redundant, coverage-focused test files into single, comprehensive test files per module. This will simplify the test suite structure and improve maintainability.

---

### **Part 1: Consolidate Unit Tests**

**Summary**: For each core module in `agent_workflow`, merge all corresponding `test_*_coverage.py`, `test_*_comprehensive.py`, `test_*_final_coverage.py`, etc., files into a single, comprehensive `test_*.py` file.

**Scope**:
*   All `test_*.py` files within `tests/unit/` that are variations of a core module's test (e.g., `test_agent_memory.py`, `test_agent_memory_comprehensive.py`, `test_agent_memory_enhanced_coverage.py`, `test_agent_memory_final_coverage.py`).

**Step-by-Step Instructions (per module)**:

1.  **Identify Target Module**: Choose a core module (e.g., `agent_workflow/core/models.py` after Epic 1.1, or `agent_workflow/context/manager.py` after Epic 1.4).
2.  **Identify Related Test Files**: Locate all unit test files in `tests/unit/` that test this module and its sub-components. This typically includes files with names like:
    *   `test_module_name.py`
    *   `test_module_name_comprehensive.py`
    *   `test_module_name_coverage.py`
    *   `test_module_name_final_coverage.py`
    *   `test_module_name_audit_compliance.py`
    *   `test_module_name_enhanced_coverage.py`
    *   `test_module_name_critical_coverage.py`
    *   `test_module_name_government_audit_final.py`
3.  **Choose Primary Test File**: Select one of these files as the primary destination for the merged tests (e.g., `test_module_name.py`). If a `test_module_name.py` doesn't exist, create it.
4.  **Merge Test Cases**: For each identified related test file (excluding the primary one):
    *   Read the content of the related test file.
    *   Carefully copy all unique test classes, test methods, fixtures, and helper functions into the primary test file.
    *   Ensure that no test cases are lost and that all assertions and test logic are correctly transferred.
    *   Resolve any naming conflicts for classes, methods, or fixtures by renaming them if necessary, ensuring clarity and uniqueness.
    *   Update imports within the primary test file to correctly reference the `agent_workflow` package structure (e.g., `from agent_workflow.core.models import ...`).
5.  **Verify Functionality**: After merging, run the primary test file to ensure all tests pass. It is highly recommended to run the entire unit test suite (`pytest tests/unit/`) to catch any unintended side effects.
6.  **Delete Redundant Files**: Once the primary test file is updated and verified, delete all the redundant test files that were merged into it.

**Parallelization Strategy**: This epic can be highly parallelized. Different agents can work on consolidating tests for different core modules simultaneously, as long as they are working on distinct sets of test files.

---

### **Acceptance Criteria**

*   The `tests/unit/` directory contains significantly fewer test files, with redundant files merged.
*   Each core module in `agent_workflow` has a single, comprehensive unit test file in `tests/unit/`.
*   All test cases from the original redundant files are preserved in the merged files.
*   All merged unit test files pass successfully.
*   The overall unit test coverage of the `agent_workflow` package is maintained or improved.
