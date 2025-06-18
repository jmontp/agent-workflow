"""
Migration command for transitioning from git-clone to pip-install workflow.

This module provides commands to migrate existing git-clone installations
to the new pip-based package installation system.
"""

import os
import sys
import shutil
import yaml
import json
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime
import click
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn

from .utils import (
    get_config_dir,
    print_success,
    print_warning,
    print_error,
    print_info,
    confirm_action,
    show_progress
)

console = Console()


@click.command("migrate")
@click.argument("source_path", type=click.Path(exists=True))
@click.option("--backup-first", is_flag=True, help="Create backup before migration")
@click.option("--import-projects", is_flag=True, help="Auto-discover and register projects")
@click.option("--preserve-config", is_flag=True, help="Keep existing configuration files")
@click.option("--dry-run", is_flag=True, help="Show migration plan without executing")
@click.pass_context
def migrate_command(ctx, source_path, backup_first, import_projects, preserve_config, dry_run):
    """Migrate from git-clone installation to pip package."""
    try:
        source_path = Path(source_path).resolve()
        
        # Validate source installation
        migration_plan = _analyze_source_installation(source_path)
        if not migration_plan["valid"]:
            print_error("Source installation is not valid or not found")
            for error in migration_plan["errors"]:
                print_error(f"  - {error}")
            return
        
        # Show migration plan
        if dry_run:
            _show_migration_plan(migration_plan, import_projects, preserve_config)
            return
        
        # Confirm migration
        console.print(Panel("Agent-Workflow Migration", style="blue"))
        console.print(f"[bold]Source:[/bold] {source_path}")
        console.print(f"[bold]Target:[/bold] {get_config_dir()}")
        
        if not confirm_action("Proceed with migration?"):
            print_info("Migration cancelled")
            return
        
        # Execute migration
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            
            migration_task = progress.add_task("Migrating installation...", total=None)
            
            # Create backup if requested
            if backup_first:
                progress.update(migration_task, description="Creating backup...")
                _create_backup(source_path)
            
            # Initialize new configuration
            progress.update(migration_task, description="Initializing new configuration...")
            _initialize_new_config(preserve_config)
            
            # Migrate configuration
            if preserve_config:
                progress.update(migration_task, description="Migrating configuration...")
                _migrate_configuration(source_path, migration_plan)
            
            # Import projects if requested
            if import_projects:
                progress.update(migration_task, description="Importing projects...")
                _import_projects(source_path, migration_plan)
            
            # Migrate custom scripts/data
            progress.update(migration_task, description="Migrating custom data...")
            _migrate_custom_data(source_path, migration_plan)
            
            progress.update(migration_task, description="Migration complete!", completed=True)
        
        print_success("Migration completed successfully!")
        _show_post_migration_steps(source_path)
        
    except Exception as e:
        print_error(f"Migration failed: {e}")
        if ctx.obj.get('verbose'):
            import traceback
            console.print(traceback.format_exc())
        sys.exit(1)


def _analyze_source_installation(source_path: Path) -> Dict[str, Any]:
    """Analyze source git-clone installation."""
    analysis = {
        "valid": False,
        "errors": [],
        "warnings": [],
        "config_files": [],
        "project_configs": [],
        "custom_scripts": [],
        "data_directories": [],
        "git_repo": False
    }
    
    # Check if it's a git repository
    if (source_path / ".git").exists():
        analysis["git_repo"] = True
    else:
        analysis["warnings"].append("Source is not a git repository")
    
    # Check for key directories and files
    expected_structure = {
        "lib": "Core library directory",
        "scripts": "Scripts directory", 
        "tests": "Tests directory",
        "docs_src": "Documentation source"
    }
    
    missing_dirs = []
    for dir_name, description in expected_structure.items():
        if not (source_path / dir_name).exists():
            missing_dirs.append(f"{dir_name} ({description})")
    
    if missing_dirs:
        analysis["errors"].append(f"Missing required directories: {', '.join(missing_dirs)}")
    else:
        analysis["valid"] = True
    
    # Find configuration files
    config_patterns = [
        "config*.yaml",
        "config*.yml", 
        "*.config.yaml",
        "orchestrator-config*.yaml"
    ]
    
    for pattern in config_patterns:
        config_files = list(source_path.glob(pattern))
        config_files.extend(list(source_path.rglob(pattern)))
        analysis["config_files"].extend([str(f) for f in config_files])
    
    # Find project configurations
    project_config_files = list(source_path.rglob("project-config*.yaml"))
    project_config_files.extend(list(source_path.rglob("**/projects.yaml")))
    analysis["project_configs"] = [str(f) for f in project_config_files]
    
    # Find custom scripts
    script_dirs = [source_path / "scripts", source_path / "tools"]
    for script_dir in script_dirs:
        if script_dir.exists():
            scripts = list(script_dir.glob("*.py"))
            scripts.extend(list(script_dir.glob("*.sh")))
            analysis["custom_scripts"].extend([str(s) for s in scripts])
    
    # Find data directories
    data_dirs = ["data", "logs", "state", ".orch-state"]
    for data_dir in data_dirs:
        full_path = source_path / data_dir
        if full_path.exists():
            analysis["data_directories"].append(str(full_path))
    
    return analysis


def _show_migration_plan(plan: Dict[str, Any], import_projects: bool, preserve_config: bool) -> None:
    """Show what will be migrated without executing."""
    console.print(Panel("Migration Plan (Dry Run)", style="blue"))
    
    # Source analysis
    console.print("\n[bold]Source Analysis:[/bold]")
    if plan["valid"]:
        console.print("[green]✓ Valid agent-workflow installation detected[/green]")
    else:
        console.print("[red]✗ Invalid installation detected[/red]")
        for error in plan["errors"]:
            console.print(f"  [red]✗[/red] {error}")
    
    for warning in plan["warnings"]:
        console.print(f"  [yellow]⚠[/yellow] {warning}")
    
    # Migration steps
    console.print("\n[bold]Migration Steps:[/bold]")
    steps = [
        "Initialize new pip-based configuration",
    ]
    
    if preserve_config and plan["config_files"]:
        steps.append(f"Migrate {len(plan['config_files'])} configuration files")
    
    if import_projects:
        steps.append("Auto-discover and register projects")
    
    if plan["custom_scripts"]:
        steps.append(f"Migrate {len(plan['custom_scripts'])} custom scripts")
    
    if plan["data_directories"]:
        steps.append(f"Migrate {len(plan['data_directories'])} data directories")
    
    for i, step in enumerate(steps, 1):
        console.print(f"  {i}. {step}")
    
    # Files to migrate
    if plan["config_files"]:
        console.print("\n[bold]Configuration Files:[/bold]")
        for config_file in plan["config_files"][:5]:  # Show first 5
            console.print(f"  • {config_file}")
        if len(plan["config_files"]) > 5:
            console.print(f"  • ... and {len(plan['config_files']) - 5} more")
    
    if plan["project_configs"]:
        console.print("\n[bold]Project Configurations:[/bold]")
        for project_config in plan["project_configs"]:
            console.print(f"  • {project_config}")


def _create_backup(source_path: Path) -> None:
    """Create backup of source installation."""
    backup_name = f"agent-workflow-backup-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
    backup_path = source_path.parent / backup_name
    
    print_info(f"Creating backup at {backup_path}")
    
    try:
        shutil.copytree(source_path, backup_path)
        print_success(f"Backup created: {backup_path}")
    except Exception as e:
        print_error(f"Backup failed: {e}")
        raise


def _initialize_new_config(preserve_existing: bool) -> None:
    """Initialize new pip-based configuration."""
    config_dir = get_config_dir()
    
    if config_dir.exists() and not preserve_existing:
        print_warning(f"Configuration directory exists: {config_dir}")
        if not confirm_action("Overwrite existing configuration?"):
            print_error("Cannot proceed without overwriting configuration")
            sys.exit(1)
    
    # Create directory structure
    directories = [
        config_dir,
        config_dir / "projects",
        config_dir / "logs",
        config_dir / "templates",
        config_dir / "scripts"
    ]
    
    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)
    
    # Create initial configuration if not preserving
    if not preserve_existing or not (config_dir / "config.yaml").exists():
        _create_initial_config(config_dir)


def _create_initial_config(config_dir: Path) -> None:
    """Create initial configuration file."""
    config_data = {
        "version": "1.0",
        "created": datetime.now().isoformat(),
        "migrated_from_git": True,
        "global": {
            "installation_id": _generate_installation_id(),
            "user_profile": "solo-engineer",
            "default_mode": "blocking",
            "log_level": "INFO",
            "data_retention_days": 30,
            "max_concurrent_projects": 3
        },
        "ai_provider": {
            "provider": None,
            "model": None,
            "api_endpoint": None,
            "rate_limit": {
                "requests_per_minute": 50,
                "tokens_per_minute": 100000
            }
        },
        "discord": {
            "enabled": False,
            "guild_id": None,
            "channel_prefix": "orch",
            "bot_permissions": ["send_messages", "manage_channels", "embed_links"]
        },
        "security": {
            "agent_restrictions_enabled": True,
            "command_approval_required": True,
            "dangerous_commands_blocked": True,
            "credential_encryption_enabled": True
        },
        "projects": {
            "registry_path": str(config_dir / "projects" / "registry.yaml"),
            "auto_discovery": False,
            "validation_on_register": True,
            "max_concurrent": 3
        }
    }
    
    with open(config_dir / "config.yaml", 'w') as f:
        yaml.dump(config_data, f, default_flow_style=False, indent=2)
    
    # Create empty project registry
    registry_data = {"projects": {}}
    with open(config_dir / "projects" / "registry.yaml", 'w') as f:
        yaml.dump(registry_data, f, default_flow_style=False, indent=2)


def _migrate_configuration(source_path: Path, plan: Dict[str, Any]) -> None:
    """Migrate configuration from source installation."""
    config_dir = get_config_dir()
    
    # Load existing config if it exists
    config_file = config_dir / "config.yaml"
    if config_file.exists():
        with open(config_file, 'r') as f:
            new_config = yaml.safe_load(f)
    else:
        new_config = {}
    
    # Migrate from old configuration files
    for old_config_path in plan["config_files"]:
        try:
            with open(old_config_path, 'r') as f:
                old_config = yaml.safe_load(f)
            
            # Merge configurations intelligently
            _merge_configurations(new_config, old_config)
            
        except Exception as e:
            print_warning(f"Could not migrate config {old_config_path}: {e}")
    
    # Save merged configuration
    with open(config_file, 'w') as f:
        yaml.dump(new_config, f, default_flow_style=False, indent=2)


def _merge_configurations(target: Dict[str, Any], source: Dict[str, Any]) -> None:
    """Intelligently merge old configuration into new."""
    # Map old config keys to new structure
    key_mappings = {
        "orchestrator": "global",
        "bot": "discord",
        "ai": "ai_provider",
        "github": "github"
    }
    
    for old_key, new_key in key_mappings.items():
        if old_key in source:
            if new_key not in target:
                target[new_key] = {}
            
            # Merge the section
            if isinstance(source[old_key], dict):
                target[new_key].update(source[old_key])
    
    # Direct mappings for backwards compatibility
    direct_mappings = {
        "log_level": ["global", "log_level"],
        "max_projects": ["global", "max_concurrent_projects"],
        "discord_token": ["discord", "token"],
        "discord_guild": ["discord", "guild_id"]
    }
    
    for old_path, new_path in direct_mappings.items():
        if old_path in source:
            _set_nested_value(target, new_path, source[old_path])


def _set_nested_value(dictionary: Dict[str, Any], path: List[str], value: Any) -> None:
    """Set a nested dictionary value using a path."""
    current = dictionary
    for key in path[:-1]:
        if key not in current:
            current[key] = {}
        current = current[key]
    current[path[-1]] = value


def _import_projects(source_path: Path, plan: Dict[str, Any]) -> None:
    """Auto-discover and register projects from source installation."""
    config_dir = get_config_dir()
    registry_path = config_dir / "projects" / "registry.yaml"
    
    # Load existing registry
    if registry_path.exists():
        with open(registry_path, 'r') as f:
            registry = yaml.safe_load(f) or {"projects": {}}
    else:
        registry = {"projects": {}}
    
    # Discover projects from old configuration
    discovered_projects = []
    
    # Check for explicit project configurations
    for project_config_path in plan["project_configs"]:
        try:
            with open(project_config_path, 'r') as f:
                project_configs = yaml.safe_load(f)
            
            if "projects" in project_configs:
                for project in project_configs["projects"]:
                    if "path" in project:
                        discovered_projects.append({
                            "name": project.get("name", Path(project["path"]).name),
                            "path": project["path"],
                            "mode": project.get("orchestration", "blocking"),
                            "source": project_config_path
                        })
        except Exception as e:
            print_warning(f"Could not parse project config {project_config_path}: {e}")
    
    # Auto-discover from common project locations
    project_indicators = [".git", "package.json", "requirements.txt", "pom.xml", "Cargo.toml"]
    
    for root, dirs, files in os.walk(source_path):
        root_path = Path(root)
        
        # Skip certain directories
        if any(part.startswith('.') for part in root_path.parts):
            continue
        
        # Check if this looks like a project
        has_indicator = any((root_path / indicator).exists() for indicator in project_indicators)
        if has_indicator and root_path != source_path:
            project_name = root_path.name
            if project_name not in [p["name"] for p in discovered_projects]:
                discovered_projects.append({
                    "name": project_name,
                    "path": str(root_path),
                    "mode": "blocking",
                    "source": "auto-discovered"
                })
    
    # Register discovered projects
    for project in discovered_projects:
        if project["name"] not in registry["projects"]:
            registry["projects"][project["name"]] = {
                "name": project["name"],
                "path": project["path"],
                "registered": datetime.now().isoformat(),
                "last_active": None,
                "mode": project["mode"],
                "framework": "general",
                "status": "idle",
                "metadata": {
                    "language": "unknown",
                    "repository": None,
                    "migrated_from": project["source"]
                }
            }
            print_info(f"Registered project: {project['name']}")
    
    # Save updated registry
    with open(registry_path, 'w') as f:
        yaml.dump(registry, f, default_flow_style=False, indent=2)


def _migrate_custom_data(source_path: Path, plan: Dict[str, Any]) -> None:
    """Migrate custom scripts and data directories."""
    config_dir = get_config_dir()
    
    # Migrate custom scripts
    if plan["custom_scripts"]:
        scripts_dir = config_dir / "scripts"
        scripts_dir.mkdir(exist_ok=True)
        
        for script_path in plan["custom_scripts"]:
            script_file = Path(script_path)
            target_path = scripts_dir / script_file.name
            
            try:
                shutil.copy2(script_file, target_path)
                print_info(f"Migrated script: {script_file.name}")
            except Exception as e:
                print_warning(f"Could not migrate script {script_file.name}: {e}")
    
    # Migrate data directories
    for data_dir_path in plan["data_directories"]:
        data_dir = Path(data_dir_path)
        target_dir = config_dir / data_dir.name
        
        try:
            if not target_dir.exists():
                shutil.copytree(data_dir, target_dir)
                print_info(f"Migrated data directory: {data_dir.name}")
            else:
                print_warning(f"Skipped existing directory: {data_dir.name}")
        except Exception as e:
            print_warning(f"Could not migrate directory {data_dir.name}: {e}")


def _generate_installation_id() -> str:
    """Generate unique installation ID."""
    import uuid
    return str(uuid.uuid4())


def _show_post_migration_steps(source_path: Path) -> None:
    """Show steps to complete after migration."""
    console.print("\n[bold]Migration Complete![/bold]")
    console.print("Your agent-workflow installation has been migrated to the pip-based system.")
    
    next_steps = [
        "Verify configuration: agent-orch health --check-all",
        "Review migrated projects: agent-orch projects list --verbose",
        "Test the installation: agent-orch status",
        "Setup integrations: agent-orch setup-discord or agent-orch setup-api",
        f"Consider removing old installation: {source_path}"
    ]
    
    console.print("\n[bold]Next Steps:[/bold]")
    for i, step in enumerate(next_steps, 1):
        console.print(f"  {i}. {step}")
    
    console.print("\n[dim]For help with any command, run: agent-orch <command> --help[/dim]")