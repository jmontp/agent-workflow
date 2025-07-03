# Epic 4.1 Plan: Full System Validation

**Objective**: Ensure the refactored project is stable, fully functional, and meets all quality standards. This involves running the entire automated test suite and performing manual verification of key functionalities.

---

### **Part 1: Run Comprehensive Automated Test Suite**

**Summary**: Execute all automated tests (unit, integration, acceptance, performance, security, edge cases, regression) to confirm that no functionality has been broken during the refactoring process.

**Tool**:
*   `tests/run_comprehensive_tests.py`

**Step-by-Step Instructions**:

1.  **Navigate to Project Root**: Ensure the current working directory is the project root (`/mnt/c/Users/jmontp/Documents/workspace/agent-workflow/`).
2.  **Execute Comprehensive Test Runner**: Run the main test script with all categories enabled:
    ```bash
    python tests/run_comprehensive_tests.py --categories e2e performance security edge_cases acceptance regression
    ```
3.  **Analyze Results**: Carefully review the output of the test runner.
    *   **Success Criteria**: All tests must pass (`✅ ALL COMPREHENSIVE TDD TESTS PASSED!`).
    *   **Failure Handling**: If any tests fail (`❌ SOME COMPREHENSIVE TESTS FAILED!`), identify the failing tests and the root cause of the failures. These must be addressed and fixed before proceeding.
4.  **Generate and Review Report**: Generate a detailed report for further analysis:
    ```bash
    python tests/run_comprehensive_tests.py --categories e2e performance security edge_cases acceptance regression --save-report --report-file final_validation_report.json
    ```
    *   Review `final_validation_report.json` for any warnings, performance regressions, or security issues that might not cause a test to fail but indicate areas for improvement.

**Parallelization Strategy**: The `run_comprehensive_tests.py` script itself can execute categories in parallel if configured (e.g., using `pytest-xdist` internally). However, for this final validation, it's best to run it as a single, comprehensive job to get a consolidated report.

---

### **Part 2: Manual Verification of CLI and Web Visualizer**

**Summary**: Perform manual testing of the Command Line Interface (CLI) and the Web Visualizer to ensure user-facing functionalities are working as expected and provide a good user experience.

**Tools**:
*   `agent-orch` (or `aw`) CLI commands
*   Web browser for `aw web`

**Step-by-Step Instructions**:

1.  **Verify CLI Commands**:
    *   **Basic Commands**: Run `aw --help`, `aw init --dry-run`, `aw status`, `aw version --verbose`.
    *   **Project Management**: If projects are registered, run `aw projects list --verbose`, `aw register-project <path> --dry-run`.
    *   **Orchestrator Control**: Start the orchestrator (`aw start --discord` or `aw start --daemon`), verify it's running (`aw status`), and then stop it (`aw stop`).
    *   **Configuration**: Run `aw configure --wizard` (if implemented) or `aw config validate`.
    *   **Development Commands**: If Epic 3.1 is completed, test the new `aw dev check-coverage`, `aw dev check-compliance`, and `aw dev generate-docs` commands.
    *   **Error Handling**: Test invalid commands or commands in incorrect states to ensure graceful error messages.
2.  **Verify Web Visualizer**:
    *   **Start Visualizer**: Run `aw web`.
    *   **Access UI**: Open a web browser and navigate to `http://localhost:5000` (or the configured port).
    *   **Real-time Updates**: Start an orchestration process (e.g., `aw start`) and observe if the visualizer updates in real-time (state changes, logs, TDD cycle progress).
    *   **Chat Functionality**: Test sending chat messages and commands through the web interface. Verify bot responses.
    *   **Multi-Project Support**: If multi-project is enabled, test switching between projects and verify that the UI reflects the correct project context.
    *   **UI Elements**: Check that all diagrams (Mermaid), tables, and other UI components render correctly and are interactive.
    *   **Responsiveness**: Test the UI on different browser sizes or device emulators to ensure responsiveness.
    *   **Error Display**: Simulate an error (if possible) and verify that it's displayed correctly in the visualizer.

---

### **Acceptance Criteria**

*   All automated tests in `tests/run_comprehensive_tests.py` pass successfully.
*   All core CLI commands (`init`, `start`, `stop`, `status`, `projects`, `configure`, `version`, `health`) function as expected.
*   The web visualizer starts without errors and displays real-time updates from the orchestrator.
*   Chat commands and multi-project switching work correctly in the web UI.
*   The user experience of both the CLI and Web Visualizer is smooth and intuitive.
*   No critical bugs or regressions are identified during manual testing.
