# Epic 3.2 Plan: Unify Configuration

**Objective**: Consolidate all project configuration into a single, well-documented `config.yml` file and remove the custom dependency tracking system. This will simplify configuration management and reduce codebase complexity.

---

### **Part 1: Consolidate Configuration Files**

**Summary**: Merge relevant settings from `orch-config.yaml`, `config.example.yml`, and potentially other scattered configuration snippets into a single `config.yml` file. The `config.example.yml` will serve as the primary template.

**Source Files**:
1.  `orch-config.yaml`
2.  `config.example.yml`

**Destination File**:
*   `config.yml` (This file will be created/updated based on `config.example.yml`)

**Step-by-Step Instructions**:

1.  **Analyze `orch-config.yaml`**: Read the contents of `orch-config.yaml` to identify global orchestration settings, resource limits, and project definitions.
2.  **Analyze `config.example.yml`**: Read the contents of `config.example.yml` to understand the intended structure and default values for various sections (orchestrator, multi-project, discord, tdd, agents, security, logging, development).
3.  **Create/Update `config.yml`**: Create a new `config.yml` file (or update the existing `config.example.yml` and rename it) that incorporates all relevant settings from `orch-config.yaml` into the structure defined by `config.example.yml`.
    *   Map `orch-config.yaml`'s `global` section settings (e.g., `max_concurrent_projects`, `resource_allocation_strategy`) into the `orchestrator` or `global` section of `config.yml`.
    *   Map `orch-config.yaml`'s `projects` section into the `multi-project` section of `config.yml`.
    *   Ensure all default values and comments from `config.example.yml` are preserved.
4.  **Remove Redundancy**: Eliminate any duplicate or conflicting settings, prioritizing the more comprehensive or recent values.
5.  **Update References**: Ensure that the application (especially the orchestrator and CLI) loads its configuration from this new `config.yml` file.
6.  **Delete Old File**: After the consolidation is complete and verified, delete `orch-config.yaml`.

---

### **Part 2: Remove Custom Dependency Tracking System**

**Summary**: Delete the custom dependency tracking system, including `dependencies.yaml` and the `tools/dependencies/` directory. This system adds complexity and can be replaced by standard Python tooling and practices.

**Source Files/Directories**:
1.  `dependencies.yaml`
2.  `tools/dependencies/` (entire directory)

**Step-by-Step Instructions**:

1.  **Identify Usage**: Search the codebase for any remaining references to `dependencies.yaml` or modules within `tools/dependencies/`.
    *   If any critical functionality relies on this system, it must be re-evaluated or replaced with standard Python dependency management (e.g., `pip-tools` for managing `requirements.txt` and `pyproject.toml`).
2.  **Delete Files**: Delete `dependencies.yaml` from the project root.
3.  **Delete Directory**: Delete the entire `tools/dependencies/` directory.
4.  **Update `.gitignore`**: Review and update the `.gitignore` file to remove any entries related to `dependencies.yaml` or `tools/dependencies/`.

---

### **Acceptance Criteria**

*   A single `config.yml` file exists in the project root, containing all relevant configuration settings.
*   The `orch-config.yaml` file is deleted.
*   The `dependencies.yaml` file is deleted.
*   The `tools/dependencies/` directory is deleted.
*   The project loads its configuration from the new `config.yml` file.
*   All core functionalities (orchestration, agents, CLI) continue to work correctly with the unified configuration.
*   The project no longer relies on the custom dependency tracking system.
