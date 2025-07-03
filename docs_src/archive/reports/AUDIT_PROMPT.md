# Audit Prompt for Refactoring Verification

**To the Auditing Agent (Gemini):**

"Hello Gemini. I need you to perform a comprehensive audit of the project's refactoring implementation. Assume this is a fresh start, and do not rely on any prior conversational context. Your goal is to verify that the refactoring plan, detailed in `REFACTORING_PLAN.md`, has been successfully and correctly implemented.

**Project Root Directory**: `/mnt/c/Users/jmontp/Documents/workspace/agent-workflow/`

**Verification Process**:

Proceed through the following checks systematically. For each check, use your available tools (`list_directory`, `read_file`, `search_file_content`) to gather evidence. Report your findings clearly, indicating `PASS`, `FAIL`, or `N/A` for each item, along with supporting details (e.g., file content snippets, directory listings, specific import lines).

---

### **Phase 1: Architectural Unification Audit**

#### **Epic 1.1: Migrate Core Data Models and State Machines**

1.  **File Relocation & Content Merge (`agent_workflow/core/models.py`)**:
    *   **Check 1.1.1.1**: Verify `/mnt/c/Users/jmontp/Documents/workspace/agent-workflow/agent_workflow/core/models.py` exists.
    *   **Check 1.1.1.2**: Read the content of `/mnt/c/Users/jmontp/Documents/workspace/agent-workflow/agent_workflow/core/models.py`.
    *   **Check 1.1.1.3**: Verify `Epic` class contains `tdd_requirements` and `tdd_constraints` fields and their `to_dict`/`from_dict` methods handle them.
    *   **Check 1.1.1.4**: Verify `Story` class contains `tdd_cycle_id`, `test_status`, `test_files`, `ci_status`, `test_coverage` fields and their `to_dict`/`from_dict` methods handle them.
    *   **Check 1.1.1.5**: Verify `Sprint` class contains `active_tdd_cycles` and `tdd_metrics` fields and their `to_dict`/`from_dict` methods handle them.
    *   **Check 1.1.1.6**: Verify `TDDState`, `TestStatus`, `CIStatus`, `TestFileStatus`, `TestResult`, `TestFile`, `TDDTask`, `TDDCycle` classes (and their `to_dict`/`from_dict`) are present in this file.
    *   **Check 1.1.1.7**: Verify `from .models import ...` is used for internal imports within this file where applicable.

2.  **Old File Deletion (Data Models)**:
    *   **Check 1.1.2.1**: Verify `/mnt/c/Users/jmontp/Documents/workspace/agent-workflow/lib/data_models.py` does NOT exist.
    *   **Check 1.1.2.2**: Verify `/mnt/c/Users/jmontp/Documents/workspace/agent-workflow/lib/tdd_models.py` does NOT exist.

3.  **File Relocation & Content Merge (`agent_workflow/core/state_machine.py`)**:
    *   **Check 1.1.3.1**: Verify `/mnt/c/Users/jmontp/Documents/workspace/agent-workflow/agent_workflow/core/state_machine.py` exists.
    *   **Check 1.1.3.2**: Read the content of `/mnt/c/Users/jmontp/Documents/workspace/agent-workflow/agent_workflow/core/state_machine.py`.
    *   **Check 1.1.3.3**: Verify `StateMachine` class contains logic from both original state machines (e.g., `active_tdd_cycles`, `tdd_sm` instance, `validate_command` handling `/tdd` commands).
    *   **Check 1.1.3.4**: Verify `TDDStateMachine` class is present within this file.
    *   **Check 1.1.3.5**: Verify imports for models point to `agent_workflow.core.models`.

4.  **Old File Deletion (State Machines)**:
    *   **Check 1.1.4.1**: Verify `/mnt/c/Users/jmontp/Documents/workspace/agent-workflow/lib/state_machine.py` does NOT exist.
    *   **Check 1.1.4.2**: Verify `/mnt/c/Users/jmontp/Documents/workspace/agent-workflow/lib/tdd_state_machine.py` does NOT exist.

5.  **Unit Test Updates (Models)**:
    *   **Check 1.1.5.1**: Verify `/mnt/c/Users/jmontp/Documents/workspace/agent-workflow/tests/unit/test_models.py` exists.
    *   **Check 1.1.5.2**: Read the content of `/mnt/c/Users/jmontp/Documents/workspace/agent-workflow/tests/unit/test_models.py`.
    *   **Check 1.1.5.3**: Verify it contains test cases for both original data models and TDD models (e.g., `TestEpic`, `TestStory`, `TestSprint`, `TestTestResult`, `TestTDDTask`, `TestTDDCycle`).
    *   **Check 1.1.5.4**: Verify imports within `test_models.py` point to `agent_workflow.core.models`.

6.  **Old Unit Test Deletion (Models)**:
    *   **Check 1.1.6.1**: Verify `/mnt/c/Users/jmontp/Documents/workspace/agent-workflow/tests/unit/test_data_models.py` does NOT exist.
    *   **Check 1.1.6.2**: Verify `/mnt/c/Users/jmontp/Documents/workspace/agent-workflow/tests/unit/test_tdd_models.py` does NOT exist.

7.  **Unit Test Updates (State Machines)**:
    *   **Check 1.1.7.1**: Verify `/mnt/c/Users/jmontp/Documents/workspace/agent-workflow/tests/unit/test_state_machine.py` exists.
    *   **Check 1.1.7.2**: Read the content of `/mnt/c/Users/jmontp/Documents/workspace/agent-workflow/tests/unit/test_state_machine.py`.
    *   **Check 1.1.7.3**: Verify it contains test cases for both main `StateMachine` and `TDDStateMachine` (e.g., `TestStateMachineTDDIntegration` class, tests for commit commands).
    *   **Check 1.1.7.4**: Verify imports within `test_state_machine.py` point to `agent_workflow.core.state_machine` and `agent_workflow.core.models`.

8.  **Old Unit Test Deletion (State Machines)**:
    *   **Check 1.1.8.1**: Verify `/mnt/c/Users/jmontp/Documents/workspace/agent-workflow/tests/unit/test_tdd_state_machine.py` does NOT exist.

---

#### **Epic 1.2: Migrate Core Logic**

1.  **File Relocation & Import Update (`agent_workflow/core/storage.py`)**:
    *   **Check 1.2.1.1**: Verify `/mnt/c/Users/jmontp/Documents/workspace/agent-workflow/agent_workflow/core/storage.py` exists.
    *   **Check 1.2.1.2**: Read the content of `/mnt/c/Users/jmontp/Documents/workspace/agent-workflow/agent_workflow/core/storage.py`.
    *   **Check 1.2.1.3**: Verify imports for `ProjectData`, `Epic`, `Story`, `Sprint`, `TDDCycle` point to `agent_workflow.core.models`.

2.  **Old File Deletion (Project Storage)**:
    *   **Check 1.2.2.1**: Verify `/mnt/c/Users/jmontp/Documents/workspace/agent-workflow/lib/project_storage.py` does NOT exist.

3.  **File Relocation & Content Merge (`agent_workflow/core/orchestrator.py`)**:
    *   **Check 1.2.3.1**: Verify `/mnt/c/Users/jmontp/Documents/workspace/agent-workflow/agent_workflow/core/orchestrator.py` exists.
    *   **Check 1.2.3.2**: Read the content of `/mnt/c/Users/jmontp/Documents/workspace/agent-workflow/agent_workflow/core/orchestrator.py`.
    *   **Check 1.2.3.3**: Verify `Orchestrator` class contains logic for both single and multi-project orchestration (e.g., `self.orchestrators`, `self.global_config`, `_monitoring_loop`, `_scheduling_loop`, `_calculate_resource_allocation`, `handle_command` with all its sub-handlers).
    *   **Check 1.2.3.4**: Verify imports point to `agent_workflow.core.models`, `agent_workflow.core.state_machine`, `agent_workflow.core.storage`.

4.  **Old File Deletion (Orchestrators)**:
    *   **Check 1.2.4.1**: Verify `/mnt/c/Users/jmontp/Documents/workspace/agent-workflow/lib/global_orchestrator.py` does NOT exist.
    *   **Check 1.2.4.2**: Verify `/mnt/c/Users/jmontp/Documents/workspace/agent-workflow/scripts/orchestrator.py` does NOT exist.

5.  **Unit Test Updates (Project Storage)**:
    *   **Check 1.2.5.1**: Verify `/mnt/c/Users/jmontp/Documents/workspace/agent-workflow/tests/unit/test_storage.py` exists.
    *   **Check 1.2.5.2**: Read the content of `/mnt/c/Users/jmontp/Documents/workspace/agent-workflow/tests/unit/test_storage.py`.
    *   **Check 1.2.5.3**: Verify imports point to `agent_workflow.core.storage` and `agent_workflow.core.models`.

6.  **Unit Test Updates (Orchestrators)**:
    *   **Check 1.2.6.1**: Verify `/mnt/c/Users/jmontp/Documents/workspace/agent-workflow/tests/unit/test_orchestrator.py` exists.
    *   **Check 1.2.6.2**: Read the content of `/mnt/c/Users/jmontp/Documents/workspace/agent-workflow/tests/unit/test_orchestrator.py`.
    *   **Check 1.2.6.3**: Verify it contains tests for both single and multi-project orchestration logic (e.g., `TestGlobalOrchestrator` and `TestSingleProjectOrchestrator` classes, or their merged equivalents).
    *   **Check 1.2.6.4**: Verify imports point to `agent_workflow.core.orchestrator`.

7.  **Old Unit Test Deletion (Global Orchestrator)**:
    *   **Check 1.2.7.1**: Verify `/mnt/c/Users/jmontp/Documents/workspace/agent-workflow/tests/unit/test_global_orchestrator.py` does NOT exist.

---

#### **Epic 1.3: Migrate Agents and Security**

1.  **Agent Files Relocation**:
    *   **Check 1.3.1.1**: Verify `/mnt/c/Users/jmontp/Documents/workspace/agent-workflow/agent_workflow/agents/` directory exists.
    *   **Check 1.3.1.2**: List contents of `/mnt/c/Users/jmontp/Documents/workspace/agent-workflow/agent_workflow/agents/` and verify agent files (`code_agent.py`, `design_agent.py`, `qa_agent.py`, `data_agent.py`, `mock_agent.py`) are present.
    *   **Check 1.3.1.3**: Verify `/mnt/c/Users/jmontp/Documents/workspace/agent-workflow/lib/agents/` directory does NOT exist.

2.  **Security Tool Config Relocation**:
    *   **Check 1.3.2.1**: Verify `/mnt/c/Users/jmontp/Documents/workspace/agent-workflow/agent_workflow/security/tool_config.py` exists.
    *   **Check 1.3.2.2**: Read the content of `/mnt/c/Users/jmontp/Documents/workspace/agent-workflow/agent_workflow/security/tool_config.py`.
    *   **Check 1.3.2.3**: Verify `AGENT_TOOL_CONFIG` dictionary is present.
    *   **Check 1.3.2.4**: Verify `/mnt/c/Users/jmontp/Documents/workspace/agent-workflow/lib/agent_tool_config.py` does NOT exist.

3.  **Unit Test Updates (Agents & Security)**:
    *   **Check 1.3.3.1**: Verify `/mnt/c/Users/jmontp/Documents/workspace/agent-workflow/tests/unit/test_agent_tool_config.py` exists.
    *   **Check 1.3.3.2**: Read the content of `/mnt/c/Users/jmontp/Documents/workspace/agent-workflow/tests/unit/test_agent_tool_config.py`.
    *   **Check 1.3.3.3**: Verify imports point to `agent_workflow.security.tool_config`.
    *   **Check 1.3.3.4**: Verify `tests/unit/test_agents.py` exists (or `test_code_agent.py`, `test_design_agent.py`, etc. are updated).
    *   **Check 1.3.3.5**: Read relevant agent test files and verify imports point to `agent_workflow.agents`.

---

#### **Epic 1.4: Migrate Context Management and Integrations**

1.  **Context Files Relocation**:
    *   **Check 1.4.1.1**: Verify `/mnt/c/Users/jmontp/Documents/workspace/agent-workflow/agent_workflow/context/` directory exists.
    *   **Check 1.4.1.2**: List contents of `/mnt/c/Users/jmontp/Documents/workspace/agent-workflow/agent_workflow/context/` and verify context files (`context_manager.py`, `context_filter.py`, `context_compressor.py`, `context_index.py`, `context_cache.py`, `agent_memory.py`, `token_calculator.py`, etc.) are present.
    *   **Check 1.4.1.3**: Verify `/mnt/c/Users/jmontp/Documents/workspace/agent-workflow/lib/context_manager.py`, `lib/context_filter.py`, `lib/context_compressor.py`, `lib/context_index.py`, `lib/context_cache.py`, `lib/agent_memory.py`, `lib/token_calculator.py` (and other `lib/context_*.py` files) do NOT exist.

2.  **Discord Client Relocation & Merge**:
    *   **Check 1.4.2.1**: Verify `/mnt/c/Users/jmontp/Documents/workspace/agent-workflow/agent_workflow/integrations/discord/` directory exists.
    *   **Check 1.4.2.2**: List contents of `/mnt/c/Users/jmontp/Documents/workspace/agent-workflow/agent_workflow/integrations/discord/` and verify a single, merged Discord client file (e.g., `client.py` or `bot.py`) is present.
    *   **Check 1.4.2.3**: Verify `/mnt/c/Users/jmontp/Documents/workspace/agent-workflow/lib/discord_bot.py` and `lib/multi_project_discord_bot.py` do NOT exist.

3.  **Claude Client Relocation**:
    *   **Check 1.4.3.1**: Verify `/mnt/c/Users/jmontp/Documents/workspace/agent-workflow/agent_workflow/integrations/claude/` directory exists.
    *   **Check 1.4.3.2**: Verify `/mnt/c/Users/jmontp/Documents/workspace/agent-workflow/agent_workflow/integrations/claude/client.py` (or similar) exists.
    *   **Check 1.4.3.3**: Verify `/mnt/c/Users/jmontp/Documents/workspace/agent-workflow/lib/claude_client.py` does NOT exist.

4.  **Unit Test Updates (Context & Integrations)**:
    *   **Check 1.4.4.1**: Verify relevant unit tests (e.g., `tests/unit/test_context_manager.py`, `tests/unit/test_agent_memory.py`, `tests/unit/test_discord_bot.py`, `tests/unit/test_claude_client.py`) exist and their imports point to the new `agent_workflow` paths.

---

#### **Epic 1.5: Finalize Migration and Cleanup**

1.  **Overall `lib` and `scripts` Directory Deletion**:
    *   **Check 1.5.1.1**: List contents of `/mnt/c/Users/jmontp/Documents/workspace/agent-workflow/lib/` and verify it is empty or contains only `__pycache__` and `.orch-state`.
    *   **Check 1.5.1.2**: List contents of `/mnt/c/Users/jmontp/Documents/workspace/agent-workflow/scripts/` and verify it is empty or contains only `__pycache__`.

2.  **No Old Imports in `agent_workflow/`**:
    *   **Check 1.5.2.1**: Search for `from lib.` in all `.py` files under `/mnt/c/Users/jmontp/Documents/workspace/agent-workflow/agent_workflow/` (recursively).
    *   **Check 1.5.2.2**: Search for `from scripts.` in all `.py` files under `/mnt/c/Users/jmontp/Documents/workspace/agent-workflow/agent_workflow/` (recursively).

---

### **Phase 2: Codebase and Documentation Consolidation Audit**

#### **Epic 2.1: Consolidate Test Suite**

1.  **Test File Merges**:
    *   **Check 2.1.1.1**: Verify `/mnt/c/Users/jmontp/Documents/workspace/agent-workflow/tests/unit/test_agent_memory.py` contains tests from `test_agent_memory_comprehensive.py`, `test_agent_memory_enhanced_coverage.py`, `test_agent_memory_final_coverage.py`.
    *   **Check 2.1.1.2**: Verify `/mnt/c/Users/jmontp/Documents/workspace/agent-workflow/tests/unit/test_context_manager.py` contains tests from its various coverage/comprehensive files.
    *   **Check 2.1.1.3**: Verify other similar consolidations (e.g., `test_context_filter.py`, `test_context_index.py`, `test_token_calculator.py`, `test_multi_project_security.py`).

2.  **Redundant Test File Deletion**:
    *   **Check 2.1.2.1**: Verify `tests/unit/test_agent_memory_comprehensive.py`, `test_agent_memory_enhanced_coverage.py`, `test_agent_memory_final_coverage.py` (and similar redundant files) do NOT exist.

---

#### **Epic 2.2: Refine Documentation**

1.  **User Manual Structure**:
    *   **Check 2.2.1.1**: Verify `/mnt/c/Users/jmontp/Documents/workspace/agent-workflow/docs_src/user-guide/visualizer/` directory exists.
    *   **Check 2.2.1.2**: List its contents and verify expected files (`index.md`, `daily-tasks.md`, `commands.md`, `troubleshooting.md`, `integrations.md`) are present.

2.  **Engineering Reference Structure**:
    *   **Check 2.2.2.1**: Verify `/mnt/c/Users/jmontp/Documents/workspace/agent-workflow/docs_src/architecture/visualizer/` directory exists.
    *   **Check 2.2.2.2**: List its contents and verify expected files (`overview.md`, `decisions/`, `api-reference.md`, `patterns.md`, `extending.md`) are present.

3.  **AI Context (`CLAUDE.md`) Updates**:
    *   **Check 2.2.3.1**: Read the content of `/mnt/c/Users/jmontp/Documents/workspace/agent-workflow/CLAUDE.md`.
    *   **Check 2.2.3.2**: Verify it contains consolidated implementation insights, troubleshooting patterns, and architectural decisions.
    *   **Check 2.2.3.3**: Verify other `CLAUDE.md` files (e.g., in `lib/`, `scripts/`, `tools/`) are either deleted or significantly reduced/redirected.

4.  **Root Directory Cleanup**:
    *   **Check 2.2.4.1**: Verify `CHAT_INTERFACE_TECHNICAL_SPEC.md`, `ERROR_HANDLING_IMPROVEMENTS.md`, `SOLO_DEVELOPER_EXPERIENCE_PLAN.md` (and similar planning/report files) do NOT exist in the root.
    *   **Check 2.2.4.2**: Verify these files (or their content) have been moved to `/mnt/c/Users/jmontp/Documents/workspace/agent-workflow/docs_src/archive/planning/`.

---

### **Phase 3: Tooling and Configuration Streamlining Audit**

#### **Epic 3.1: Enhance the CLI**

1.  **New `aw dev` Command Group**:
    *   **Check 3.1.1.1**: Read `/mnt/c/Users/jmontp/Documents/workspace/agent-workflow/agent_workflow/cli/main.py`.
    *   **Check 3.1.1.2**: Verify the `cli` group has a new command or group for `dev`.

2.  **Tool Integration into CLI**:
    *   **Check 3.1.2.1**: Verify `agent_workflow/cli/config.py`, `agent_workflow/cli/info.py`, `agent_workflow/cli/init.py`, `agent_workflow/cli/migrate.py`, `agent_workflow/cli/orchestrator.py`, `agent_workflow/cli/project.py`, `agent_workflow/cli/setup.py`, `agent_workflow/cli/web.py` exist and their imports are updated to the new `agent_workflow` package structure.
    *   **Check 3.1.2.2**: Verify `tools/coverage/analyze_coverage.py`, `tools/compliance/audit_compliance_tracker.py`, `tools/documentation/generate_api_docs.py` still exist (they are integrated, not deleted).

---

#### **Epic 3.2: Unify Configuration**

1.  **Configuration Consolidation**:
    *   **Check 3.2.1.1**: Verify `/mnt/c/Users/jmontp/Documents/workspace/agent-workflow/config.yml` exists.
    *   **Check 3.2.1.2**: Read the content of `/mnt/c/Users/jmontp/Documents/workspace/agent-workflow/config.yml` and verify it contains merged settings from `orch-config.yaml` and `config.example.yml`.

2.  **Old Configuration Deletion**:
    *   **Check 3.2.2.1**: Verify `/mnt/c/Users/jmontp/Documents/workspace/agent-workflow/orch-config.yaml` does NOT exist.
    *   **Check 3.2.2.2**: Verify `/mnt/c/Users/jmontp/Documents/workspace/agent-workflow/dependencies.yaml` does NOT exist.
    *   **Check 3.2.2.3**: Verify `/mnt/c/Users/jmontp/Documents/workspace/agent-workflow/tools/dependencies/` directory does NOT exist.

---

#### **Epic 3.3: Update Web Visualizer**

1.  **Visualizer Backend Update**:
    *   **Check 3.3.1.1**: Verify `/mnt/c/Users/jmontp/Documents/workspace/agent-workflow/tools/visualizer/app.py` exists.
    *   **Check 3.3.1.2**: Read the content of `/mnt/c/Users/jmontp/Documents/workspace/agent-workflow/tools/visualizer/app.py`.
    *   **Check 3.3.1.3**: Verify imports within `app.py` point to the new `agent_workflow` package structure (e.g., `from agent_workflow.core.orchestrator import ...`).

---

### **Phase 4: Final Review and Validation Audit**

1.  **Overall `lib` and `scripts` Directory Status**:
    *   **Check 4.1.1.1**: List contents of `/mnt/c/Users/jmontp/Documents/workspace/agent-workflow/lib/` and verify it is empty or contains only `__pycache__` and `.orch-state`.
    *   **Check 4.1.1.2**: List contents of `/mnt/c/Users/jmontp/Documents/workspace/agent-workflow/scripts/` and verify it is empty or contains only `__pycache__`.

2.  **No Old Imports Remaining**:
    *   **Check 4.1.2.1**: Search for the string `from lib.` within all `.py` files in `/mnt/c/Users/jmontp/Documents/workspace/agent-workflow/agent_workflow/` (recursively). Report any findings.
    *   **Check 4.1.2.2**: Search for the string `from scripts.` within all `.py` files in `/mnt/c/Users/jmontp/Documents/workspace/agent-workflow/agent_workflow/` (recursively). Report any findings.

3.  **Final Documentation Updates**:
    *   **Check 4.1.3.1**: Read `/mnt/c/Users/jmontp/Documents/workspace/agent-workflow/README.md`. Verify it reflects the new structure and CLI-first workflow.
    *   **Check 4.1.3.2**: Read `/mnt/c/Users/jmontp/Documents/workspace/agent-workflow/CLAUDE.md`. Verify it is updated as the primary guide for AI agents.

---"