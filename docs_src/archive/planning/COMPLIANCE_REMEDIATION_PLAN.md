# Compliance Remediation Plan

**Purpose**: Address the remaining 16.5% compliance gap identified in the audit report to achieve 100% adherence to the original refactoring plan.

**Audit Results**: 83.5% compliance (86/103 checks passed)

## Executive Summary

This plan outlines parallel work streams for sub-agents to complete the remaining cleanup tasks. Each work stream is independent and can be executed simultaneously by different agents without file conflicts.

---

## Work Stream 1: Legacy File Cleanup in lib/

**Agent Type**: Cleanup Agent 1  
**Priority**: High  
**Estimated Time**: 30 minutes

### Objective
Remove or migrate the 19 remaining files in the `lib/` directory that should have been deleted or moved according to the refactoring plan.

### Tasks

1. **Review and Remove Legacy Files**
   ```
   Files to DELETE:
   - lib/simple_context_manager.py
   - lib/context_manager_factory.py
   - lib/context_monitoring.py
   - lib/context_config.py
   - lib/context_learning.py
   - lib/context_background.py
   - lib/discord_bot.py (if still exists)
   - lib/multi_project_discord_bot.py (if still exists)
   - lib/claude_client.py (if still exists)
   - lib/global_orchestrator.py (if still exists)
   ```

2. **Migrate Context Management Files**
   These files should be moved to `agent_workflow/context/` with proper renaming:
   ```
   MOVE operations:
   - lib/agent_memory.py → agent_workflow/context/memory.py
   - lib/token_calculator.py → agent_workflow/context/token_calculator.py
   - lib/context_cache.py → agent_workflow/context/cache.py (if not already there)
   - lib/context_compressor.py → agent_workflow/context/compressor.py (if not already there)
   - lib/context_filter.py → agent_workflow/context/filter.py (if not already there)
   - lib/context_index.py → agent_workflow/context/index.py (if not already there)
   - lib/context_manager.py → agent_workflow/context/manager.py (if not already there)
   ```

3. **Handle Special Cases**
   ```
   Files that may need special handling:
   - lib/project_storage.py - Check if this is different from agent_workflow/core/storage.py
     If duplicate → DELETE
     If unique functionality → Merge into core/storage.py then DELETE
   - lib/state_broadcaster.py - May be needed by visualizer
     If used by visualizer → KEEP (document why)
     If not used → DELETE
   - lib/multi_project_*.py files - Check if functionality exists in new architecture
     If migrated → DELETE
     If unique → Document and consider keeping
   ```

4. **Update Imports**
   After moving files, update any imports in the moved files to use absolute imports:
   - Change `from lib.X import Y` to `from agent_workflow.context.X import Y`
   - Change relative imports to absolute imports

### Verification
- Ensure `lib/` directory only contains `__pycache__` and `.orch-state` (if needed)
- Run quick import test on moved files

---

## Work Stream 2: Configuration Unification

**Agent Type**: Config Agent  
**Priority**: High  
**Estimated Time**: 20 minutes

### Objective
Complete the configuration unification by merging `orch-config.yaml` into `config.yml` and removing redundant config files.

### Tasks

1. **Analyze Configuration Files**
   ```bash
   # Read both files to understand their structure
   - Read orch-config.yaml
   - Read config.yml
   - Identify unique settings in each
   ```

2. **Merge Configuration**
   ```yaml
   # Merge orch-config.yaml settings into config.yml
   # Ensure all sections are preserved:
   - Global orchestration settings
   - Resource limits
   - Project configurations
   - Security settings
   - TDD workflow settings
   ```

3. **Update Configuration References**
   Search and update any code that references `orch-config.yaml`:
   ```bash
   # Files to check and update:
   - agent_workflow/core/orchestrator.py
   - agent_workflow/cli/config.py
   - Any other files that load configuration
   ```

4. **Delete Old Configuration**
   ```bash
   # After successful merge and verification:
   - DELETE orch-config.yaml
   - DELETE config.example.yml (if exists)
   - DELETE dependencies.yaml (already confirmed in audit)
   ```

### Verification
- Ensure only `config.yml` exists as the configuration file
- Test configuration loading in the application
- Verify all settings are accessible

---

## Work Stream 3: Scripts Directory Resolution

**Agent Type**: Scripts Agent  
**Priority**: Medium  
**Estimated Time**: 15 minutes

### Objective
Resolve the scripts directory situation based on the audit findings.

### Tasks

1. **Assess Current State**
   ```bash
   # Check what's actually in scripts/
   - List all files in scripts/
   - Determine if any scripts should be preserved
   ```

2. **Handle Based on Findings**
   
   **Option A**: If scripts/ should be completely empty (except __pycache__)
   ```bash
   - Keep scripts/CLAUDE.md if it contains valuable documentation
   - Or move scripts/CLAUDE.md content to main CLAUDE.md and delete
   - Ensure scripts/ is otherwise empty
   ```
   
   **Option B**: If some scripts should remain
   ```bash
   - Document why they remain in scripts/CLAUDE.md
   - Ensure they don't duplicate functionality in agent_workflow/
   ```

3. **Create Simple Runner Scripts (if needed)**
   If users need simple entry points:
   ```python
   # scripts/orchestrator.py (minimal wrapper)
   #!/usr/bin/env python3
   """Simple wrapper for backward compatibility."""
   from agent_workflow.cli.main import cli
   
   if __name__ == "__main__":
       cli()
   ```

### Verification
- Scripts directory contains only necessary files
- Any remaining scripts are documented
- No duplication with agent_workflow functionality

---

## Work Stream 4: Web Visualizer Import Updates

**Agent Type**: Visualizer Agent  
**Priority**: Medium  
**Estimated Time**: 25 minutes

### Objective
Complete the import updates in the web visualizer to use the new `agent_workflow` package structure.

### Tasks

1. **Update tools/visualizer/app.py Imports**
   ```python
   # Update all imports to prefer agent_workflow package:
   
   # Change from:
   try:
       from lib.state_broadcaster import StateBroadcaster
   except ImportError:
       # fallback
   
   # To:
   try:
       from agent_workflow.core.state_broadcaster import StateBroadcaster
   except ImportError:
       try:
           from lib.state_broadcaster import StateBroadcaster
       except ImportError:
           # fallback
   ```

2. **Update Import Patterns**
   Ensure consistent import pattern throughout app.py:
   - Primary: Try agent_workflow package
   - Secondary: Try lib (for backward compatibility)
   - Tertiary: Use mock/fallback

3. **Check Other Visualizer Files**
   ```bash
   # Check for imports in:
   - tools/visualizer/static/js/*.js (if any Python imports)
   - tools/visualizer/templates/*.html (if any Python references)
   - tools/visualizer/test_*.py files
   ```

4. **Update Visualizer Documentation**
   Update tools/visualizer/CLAUDE.md to reflect new import structure

### Verification
- Run `aw web --debug` and verify no import errors
- Check that all functionality works with new imports
- Ensure graceful fallbacks still function

---

## Work Stream 5: Documentation Cleanup

**Agent Type**: Docs Agent  
**Priority**: Low  
**Estimated Time**: 20 minutes

### Objective
Move remaining planning and report documents from root to appropriate archive locations.

### Tasks

1. **Identify Root Documentation Files**
   ```bash
   # Files mentioned in audit that should be moved:
   - CHAT_INTERFACE_TECHNICAL_SPEC.md
   - ERROR_HANDLING_IMPROVEMENTS.md
   - SOLO_DEVELOPER_EXPERIENCE_PLAN.md
   - Other *_REPORT.md or *_PLAN.md files
   ```

2. **Move to Archive**
   ```bash
   # Create directories if needed:
   - docs_src/archive/planning/
   - docs_src/archive/reports/
   
   # Move files:
   - Planning documents → docs_src/archive/planning/
   - Report documents → docs_src/archive/reports/
   - Keep only essential files in root (README.md, CLAUDE.md, etc.)
   ```

3. **Update References**
   - Check if any documentation references these files
   - Update paths in CLAUDE.md or other docs if needed
   - Add index file in archive directories explaining the files

### Verification
- Root directory is clean and professional
- All planning/report docs are properly archived
- Essential files remain accessible

---

## Execution Plan

### Parallel Execution Strategy

All 5 work streams can be executed in parallel since they touch different files:

1. **Stream 1** (Cleanup Agent 1): Works only in `lib/` directory
2. **Stream 2** (Config Agent): Works on config files in root
3. **Stream 3** (Scripts Agent): Works only in `scripts/` directory
4. **Stream 4** (Visualizer Agent): Works only in `tools/visualizer/`
5. **Stream 5** (Docs Agent): Works on root `.md` files and `docs_src/`

### Coordination Points

No coordination needed between agents - all work streams are independent.

### Success Criteria

After all work streams complete:
1. Re-run the audit agent to verify 100% compliance
2. Test system functionality with `aw` commands
3. Verify web interface works properly
4. Ensure all tests still pass

### Rollback Plan

If any issues arise:
1. Git diff to review all changes
2. Selectively revert problematic changes
3. Document any files that must remain for system functionality

---

## Final Notes

- Total estimated time: ~110 minutes with parallel execution
- Actual time with 5 parallel agents: ~30 minutes
- Each agent should commit their changes separately for easy tracking
- After completion, update CLAUDE.md with final state documentation

This plan ensures complete compliance with the original refactoring plan while maintaining system functionality.