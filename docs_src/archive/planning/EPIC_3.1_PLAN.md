# Epic 3.1 Plan: Enhance the CLI

**Objective**: Create a new `aw dev` command group within the `agent-workflow` CLI and integrate various development-related functionalities from the `tools/` directory as subcommands. This will make development tools more accessible and discoverable.

---

### **Part 1: Create `aw dev` Command Group**

**Summary**: Modify `agent_workflow/cli/main.py` to introduce a new `dev` command group.

**Destination File**:
*   `agent_workflow/cli/main.py`

**Step-by-Step Instructions**:

1.  **Open `agent_workflow/cli/main.py`**.
2.  **Add `dev` command group**: Locate the `@click.group` decorator for the main `cli` function. Add a new `click.group` for `dev` commands, similar to how other command groups are defined.
    ```python
    @click.group()
    def dev():
        """Development and utility commands."""
        pass

    # Add this to the main cli group
    cli.add_command(dev)
    ```
3.  **Verify**: After making changes, run `agent-orch --help` to ensure the `dev` command group appears in the help output.

---

### **Part 2: Integrate `analyze_coverage.py`**

**Summary**: Integrate the functionality from `tools/coverage/analyze_coverage.py` into a new `aw dev check-coverage` command.

**Source File**:
1.  `tools/coverage/analyze_coverage.py`

**Destination Files**:
1.  `agent_workflow/cli/dev.py` (new file for dev commands)
2.  `agent_workflow/cli/main.py`

**Step-by-Step Instructions**:

1.  **Create `agent_workflow/cli/dev.py`**: Create a new file `agent_workflow/cli/dev.py`.
2.  **Move `analyze_coverage` logic**: Copy the `analyze_coverage` function (and any helper functions it uses) from `tools/coverage/analyze_coverage.py` into `agent_workflow/cli/dev.py`.
3.  **Adapt to CLI**: Modify the `analyze_coverage` function to accept arguments from `click` and print output using `rich.console.Console`.
4.  **Define `check-coverage` command**: In `agent_workflow/cli/dev.py`, define the `check-coverage` command:
    ```python
    import click
    from .utils import print_info, print_success, print_warning, print_error
    # Import or adapt analyze_coverage logic

    @click.command("check-coverage")
    def check_coverage_command():
        """Analyze test coverage of the codebase."""
        print_info("Analyzing test coverage...")
        # Call the adapted analyze_coverage function
        # Print results using rich.console
        pass
    ```
5.  **Import into `main.py`**: In `agent_workflow/cli/main.py`, import `check_coverage_command` from `agent_workflow/cli/dev.py` and add it to the `dev` command group.
6.  **Delete Old File**: Delete `tools/coverage/analyze_coverage.py`.

---

### **Part 3: Integrate `audit_compliance_tracker.py`**

**Summary**: Integrate the functionality from `tools/compliance/audit_compliance_tracker.py` into a new `aw dev check-compliance` command.

**Source File**:
1.  `tools/compliance/audit_compliance_tracker.py`

**Destination File**:
1.  `agent_workflow/cli/dev.py`

**Step-by-Step Instructions**:

1.  **Move `ComplianceTracker` logic**: Copy the `ComplianceTracker` class (and any helper functions it uses) from `tools/compliance/audit_compliance_tracker.py` into `agent_workflow/cli/dev.py`.
2.  **Adapt to CLI**: Modify the `ComplianceTracker` methods to print output using `rich.console.Console`.
3.  **Define `check-compliance` command**: In `agent_workflow/cli/dev.py`, define the `check-compliance` command:
    ```python
    @click.command("check-compliance")
    def check_compliance_command():
        """Check government audit compliance status."""
        print_info("Checking compliance status...")
        # Instantiate and call ComplianceTracker.generate_dashboard()
        pass
    ```
4.  **Import into `main.py`**: In `agent_workflow/cli/main.py`, import `check_compliance_command` from `agent_workflow/cli/dev.py` and add it to the `dev` command group.
5.  **Delete Old File**: Delete `tools/compliance/audit_compliance_tracker.py`.

---

### **Part 4: Integrate `generate_api_docs.py`**

**Summary**: Integrate the functionality from `tools/documentation/generate_api_docs.py` into a new `aw dev generate-docs` command.

**Source File**:
1.  `tools/documentation/generate_api_docs.py`

**Destination File**:
1.  `agent_workflow/cli/dev.py`

**Step-by-Step Instructions**:

1.  **Move `APIDocGenerator` logic**: Copy the `APIDocGenerator` class (and any helper functions it uses) from `tools/documentation/generate_api_docs.py` into `agent_workflow/cli/dev.py`.
2.  **Adapt to CLI**: Modify the `APIDocGenerator` methods to accept arguments from `click` and print output using `rich.console.Console`.
3.  **Define `generate-docs` command**: In `agent_workflow/cli/dev.py`, define the `generate-docs` command:
    ```python
    @click.command("generate-docs")
    @click.option("--output", "-o", type=click.Path(), help="Output file path")
    @click.option("--format", type=click.Choice(["markdown", "openapi"]), default="markdown", help="Output format")
    def generate_docs_command(output: str, format: str):
        """Generate API documentation from source code."""
        print_info(f"Generating API documentation in {format} format...")
        # Instantiate and call APIDocGenerator methods
        pass
    ```
4.  **Import into `main.py`**: In `agent_workflow/cli/main.py`, import `generate_docs_command` from `agent_workflow/cli/dev.py` and add it to the `dev` command group.
5.  **Delete Old File**: Delete `tools/documentation/generate_api_docs.py`.

---

### **Acceptance Criteria**

*   A new `aw dev` command group is available in the CLI.
*   The `aw dev check-coverage` command correctly analyzes test coverage.
*   The `aw dev check-compliance` command correctly checks government audit compliance.
*   The `aw dev generate-docs` command correctly generates API documentation.
*   The `tools/coverage/analyze_coverage.py`, `tools/compliance/audit_compliance_tracker.py`, and `tools/documentation/generate_api_docs.py` files are deleted.
*   All relevant logic is moved into `agent_workflow/cli/dev.py`.
*   All commands function correctly and integrate with the `rich` library for output.
