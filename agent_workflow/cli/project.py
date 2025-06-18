"""
Project management commands for agent-workflow CLI.

This module provides commands for registering, managing, and validating 
projects within the agent-workflow orchestration system.
"""

import os
import sys
import yaml
import json
from pathlib import Path
from typing import Optional, Dict, Any, List
from datetime import datetime
import click
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.prompt import Prompt, Confirm
from rich.progress import Progress, SpinnerColumn, TextColumn

from .utils import (
    get_config_dir,
    validate_project_path,
    get_project_info,
    print_success,
    print_warning,
    print_error,
    print_info,
    confirm_action
)

console = Console()

# Framework detection patterns
FRAMEWORK_PATTERNS = {
    "web": [
        ("package.json", ["react", "vue", "angular", "svelte"]),
        ("requirements.txt", ["flask", "django", "pyramid"]),
        ("Gemfile", ["rails", "sinatra"]),
        ("composer.json", ["laravel", "symfony"])
    ],
    "api": [
        ("requirements.txt", ["fastapi", "falcon", "tornado"]),
        ("package.json", ["express", "koa", "hapi"]),
        ("pom.xml", ["spring-boot", "jersey"]),
        ("go.mod", ["gin", "echo"])
    ],
    "ml": [
        ("requirements.txt", ["tensorflow", "pytorch", "sklearn", "pandas"]),
        ("environment.yml", ["tensorflow", "pytorch", "sklearn"]),
        ("pyproject.toml", ["tensorflow", "pytorch", "sklearn"])
    ],
    "mobile": [
        ("android/", None),
        ("ios/", None),
        ("package.json", ["react-native", "ionic", "cordova"]),
        ("pubspec.yaml", ["flutter"])
    ],
    "desktop": [
        ("package.json", ["electron"]),
        ("requirements.txt", ["tkinter", "kivy", "pyqt"]),
        ("*.pro", None),
        ("CMakeLists.txt", None)
    ]
}


@click.command("register")
@click.argument("path", type=click.Path(exists=True))
@click.argument("name", required=False)
@click.option("--mode", type=click.Choice(["blocking", "partial", "autonomous"]),
              help="Orchestration mode")
@click.option("--framework", type=click.Choice(["general", "web", "api", "ml", "mobile", "desktop"]),
              help="Project framework type")
@click.option("--validate", is_flag=True, help="Validate project structure")
@click.option("--create-channel", is_flag=True, help="Auto-create Discord channel")
@click.option("--language", help="Primary programming language")
@click.option("--repository", help="Git repository URL")
@click.option("--description", help="Project description")
@click.option("--force", is_flag=True, help="Overwrite existing registration")
@click.pass_context
def register_command(ctx, path, name, mode, framework, validate, create_channel, 
                    language, repository, description, force):
    """Register existing project for orchestration."""
    try:
        # Validate and normalize project path
        project_path = validate_project_path(path)
        
        # Get project name
        if not name:
            name = project_path.name
        
        # Check configuration
        config_dir = get_config_dir()
        if not (config_dir / "config.yaml").exists():
            print_error("Agent-workflow not initialized. Run 'agent-orch init' first.")
            return
        
        # Load existing registry
        registry_path = config_dir / "projects" / "registry.yaml"
        if registry_path.exists():
            with open(registry_path, 'r') as f:
                registry = yaml.safe_load(f) or {"projects": {}}
        else:
            registry = {"projects": {}}
        
        # Check if project already registered
        if name in registry["projects"] and not force:
            print_error(f"Project '{name}' already registered. Use --force to overwrite.")
            print_info(f"Current registration: {registry['projects'][name]['path']}")
            return
        
        # Analyze project
        project_info = get_project_info(project_path)
        
        # Validate project structure if requested
        if validate:
            validation_result = _validate_project_structure(project_path, project_info)
            if not validation_result["valid"] and not force:
                print_warning("Project validation failed:")
                for warning in validation_result["warnings"]:
                    print_warning(f"  - {warning}")
                if not confirm_action("Continue registration anyway?"):
                    return
        
        # Auto-detect framework if not specified
        if not framework:
            framework = _detect_framework(project_path)
        
        # Load global config for defaults
        with open(config_dir / "config.yaml", 'r') as f:
            global_config = yaml.safe_load(f)
        
        # Determine orchestration mode
        if not mode:
            mode = global_config.get("global", {}).get("default_mode", "blocking")
        
        # Create project registration
        project_registration = {
            "name": name,
            "path": str(project_path),
            "registered": datetime.now().isoformat(),
            "last_active": None,
            "mode": mode,
            "framework": framework,
            "discord_channel": f"#orch-{name}" if create_channel else None,
            "status": "idle",
            "metadata": {
                "language": language or _detect_language(project_path),
                "framework_detected": project_info["framework"],
                "repository": repository or _detect_repository(project_path),
                "description": description,
                "has_tests": project_info["has_tests"],
                "has_readme": project_info["has_readme"],
                "is_git_repo": project_info["is_git_repo"]
            }
        }
        
        # Update registry
        registry["projects"][name] = project_registration
        
        # Save registry
        registry_path.parent.mkdir(parents=True, exist_ok=True)
        with open(registry_path, 'w') as f:
            yaml.dump(registry, f, default_flow_style=False, indent=2)
        
        # Create project orchestration state directory
        state_dir = project_path / ".orch-state"
        state_dir.mkdir(exist_ok=True)
        
        # Create initial state file
        initial_state = {
            "current_state": "IDLE",
            "project_name": name,
            "orchestration_mode": mode,
            "last_updated": datetime.now().isoformat(),
            "active_tasks": [],
            "pending_approvals": []
        }
        
        with open(state_dir / "status.json", 'w') as f:
            json.dump(initial_state, f, indent=2)
        
        # Success message
        print_success(f"Project '{name}' registered successfully!")
        
        # Show registration summary
        _show_registration_summary(project_registration, validation_result if validate else None)
        
        # Show next steps
        _show_project_next_steps(name, create_channel)
        
    except Exception as e:
        print_error(f"Failed to register project: {e}")
        if ctx.obj.get('verbose'):
            import traceback
            console.print(traceback.format_exc())
        sys.exit(1)


@click.command("projects")
@click.argument("subcommand", type=click.Choice(["list", "remove", "validate"]))
@click.argument("name", required=False)
@click.option("--verbose", is_flag=True, help="Show detailed information")
@click.pass_context
def projects_command(ctx, subcommand, name, verbose):
    """Manage registered projects."""
    try:
        config_dir = get_config_dir()
        registry_path = config_dir / "projects" / "registry.yaml"
        
        if not registry_path.exists():
            print_warning("No projects registered yet. Use 'agent-orch register-project' to register projects.")
            return
        
        with open(registry_path, 'r') as f:
            registry = yaml.safe_load(f) or {"projects": {}}
        
        if subcommand == "list":
            _list_projects(registry, verbose)
        elif subcommand == "remove":
            if not name:
                print_error("Project name required for remove command")
                return
            _remove_project(registry, name, registry_path)
        elif subcommand == "validate":
            if not name:
                print_error("Project name required for validate command")
                return
            _validate_project_registration(registry, name)
            
    except Exception as e:
        print_error(f"Failed to manage projects: {e}")
        if ctx.obj.get('verbose'):
            import traceback
            console.print(traceback.format_exc())
        sys.exit(1)


def _validate_project_structure(project_path: Path, project_info: Dict[str, Any]) -> Dict[str, Any]:
    """Validate project structure and return results."""
    warnings = []
    errors = []
    
    # Check for git repository
    if not project_info["is_git_repo"]:
        warnings.append("Not a git repository - version control recommended")
    
    # Check for tests
    if not project_info["has_tests"]:
        warnings.append("No test directory found - testing framework recommended")
    
    # Check for documentation
    if not project_info["has_readme"]:
        warnings.append("No README file found - documentation recommended")
    
    # Check for dependencies file
    if not (project_info["has_requirements"] or project_info["has_package_json"]):
        warnings.append("No dependency file found (requirements.txt, package.json, etc.)")
    
    # Check directory permissions
    if not os.access(project_path, os.R_OK | os.W_OK):
        errors.append("Insufficient permissions - read/write access required")
    
    return {
        "valid": len(errors) == 0,
        "warnings": warnings,
        "errors": errors
    }


def _detect_framework(project_path: Path) -> str:
    """Auto-detect project framework based on files and content."""
    for framework, patterns in FRAMEWORK_PATTERNS.items():
        for pattern_file, keywords in patterns:
            if pattern_file.endswith('/'):
                # Directory check
                if (project_path / pattern_file.rstrip('/')).exists():
                    return framework
            elif '*' in pattern_file:
                # Glob pattern check
                if list(project_path.glob(pattern_file)):
                    return framework
            else:
                # File content check
                file_path = project_path / pattern_file
                if file_path.exists():
                    if keywords is None:
                        return framework
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            content = f.read().lower()
                            if any(keyword in content for keyword in keywords):
                                return framework
                    except Exception:
                        continue
    
    return "general"


def _detect_language(project_path: Path) -> str:
    """Auto-detect primary programming language."""
    language_files = {
        "python": ["*.py", "requirements.txt", "setup.py", "pyproject.toml"],
        "javascript": ["*.js", "package.json", "*.ts"],
        "java": ["*.java", "pom.xml", "build.gradle"],
        "csharp": ["*.cs", "*.csproj", "*.sln"],
        "go": ["*.go", "go.mod"],
        "rust": ["*.rs", "Cargo.toml"],
        "ruby": ["*.rb", "Gemfile"],
        "php": ["*.php", "composer.json"],
        "cpp": ["*.cpp", "*.h", "CMakeLists.txt"],
        "swift": ["*.swift", "Package.swift"]
    }
    
    for language, patterns in language_files.items():
        for pattern in patterns:
            if list(project_path.glob(pattern)) or list(project_path.rglob(pattern)):
                return language
    
    return "unknown"


def _detect_repository(project_path: Path) -> Optional[str]:
    """Try to detect git repository URL."""
    git_config = project_path / ".git" / "config"
    if git_config.exists():
        try:
            with open(git_config, 'r') as f:
                content = f.read()
                # Simple regex to find remote origin URL
                import re
                match = re.search(r'url = (.+)', content)
                if match:
                    return match.group(1).strip()
        except Exception:
            pass
    
    return None


def _show_registration_summary(registration: Dict[str, Any], validation: Optional[Dict[str, Any]]) -> None:
    """Show project registration summary."""
    table = Table(title="Project Registration Summary")
    table.add_column("Property", style="cyan")
    table.add_column("Value", style="white")
    
    table.add_row("Name", registration["name"])
    table.add_row("Path", registration["path"])
    table.add_row("Framework", registration["framework"])
    table.add_row("Mode", registration["mode"])
    table.add_row("Language", registration["metadata"]["language"])
    
    if registration["metadata"]["repository"]:
        table.add_row("Repository", registration["metadata"]["repository"])
    
    table.add_row("Discord Channel", registration["discord_channel"] or "Not configured")
    
    console.print(table)
    
    if validation:
        if validation["warnings"]:
            console.print("\n[yellow]Warnings to address:[/yellow]")
            for warning in validation["warnings"]:
                print_warning(f"  - {warning}")


def _show_project_next_steps(name: str, discord_enabled: bool) -> None:
    """Show next steps after project registration."""
    console.print("\n[bold]Next Steps:[/bold]")
    
    steps = [
        f"Start orchestration: agent-orch start {name}",
        f"View project status: agent-orch status --project {name}"
    ]
    
    if discord_enabled:
        steps.append(f"Use Discord commands in #orch-{name}")
    else:
        steps.append("Setup Discord: agent-orch setup-discord")
    
    for i, step in enumerate(steps, 1):
        console.print(f"  {i}. {step}")


def _list_projects(registry: Dict[str, Any], verbose: bool) -> None:
    """List all registered projects."""
    projects = registry.get("projects", {})
    
    if not projects:
        print_info("No projects registered yet.")
        return
    
    if verbose:
        # Detailed view
        for project_name, project_data in projects.items():
            panel_content = []
            panel_content.append(f"[bold]Path:[/bold] {project_data['path']}")
            panel_content.append(f"[bold]Framework:[/bold] {project_data['framework']} ({project_data['metadata']['language']})")
            panel_content.append(f"[bold]Mode:[/bold] {project_data['mode']}")
            panel_content.append(f"[bold]Status:[/bold] {project_data['status']}")
            panel_content.append(f"[bold]Registered:[/bold] {project_data['registered'][:10]}")
            
            if project_data['last_active']:
                panel_content.append(f"[bold]Last Active:[/bold] {project_data['last_active'][:10]}")
            
            if project_data['metadata']['repository']:
                panel_content.append(f"[bold]Repository:[/bold] {project_data['metadata']['repository']}")
            
            console.print(Panel("\n".join(panel_content), title=f"Project: {project_name}"))
    else:
        # Table view
        table = Table(title="Registered Projects")
        table.add_column("Name", style="cyan")
        table.add_column("Status", style="green")
        table.add_column("Mode", style="yellow")
        table.add_column("Framework", style="blue")
        table.add_column("Path", style="dim")
        
        for project_name, project_data in projects.items():
            table.add_row(
                project_name,
                project_data["status"],
                project_data["mode"],
                f"{project_data['framework']} ({project_data['metadata']['language']})",
                project_data["path"]
            )
        
        console.print(table)
        console.print(f"\n[dim]Total: {len(projects)} projects registered[/dim]")


def _remove_project(registry: Dict[str, Any], name: str, registry_path: Path) -> None:
    """Remove project from registry."""
    projects = registry.get("projects", {})
    
    if name not in projects:
        print_error(f"Project '{name}' not found in registry")
        return
    
    project_data = projects[name]
    
    # Show what will be removed
    console.print(Panel(
        f"[bold]Project:[/bold] {name}\n"
        f"[bold]Path:[/bold] {project_data['path']}\n"
        f"[bold]Discord Channel:[/bold] {project_data.get('discord_channel', 'None')}\n"
        f"[bold]Configuration:[/bold] Will be removed from registry\n"
        f"[bold]Project Files:[/bold] Will remain unchanged",
        title="Remove Project"
    ))
    
    if not confirm_action("Continue with removal?"):
        print_info("Removal cancelled")
        return
    
    # Remove from registry
    del projects[name]
    
    # Save updated registry
    with open(registry_path, 'w') as f:
        yaml.dump(registry, f, default_flow_style=False, indent=2)
    
    print_success(f"Project '{name}' removed from registry")
    print_info("Project files and .orch-state directory remain intact")


def _validate_project_registration(registry: Dict[str, Any], name: str) -> None:
    """Validate specific project registration."""
    projects = registry.get("projects", {})
    
    if name not in projects:
        print_error(f"Project '{name}' not found in registry")
        return
    
    project_data = projects[name]
    project_path = Path(project_data["path"])
    
    console.print(Panel(f"Validating project: {name}", style="blue"))
    
    # Validation checks
    checks = []
    
    # Path accessibility
    if project_path.exists() and project_path.is_dir():
        checks.append(("Path access", True, "Directory accessible"))
    else:
        checks.append(("Path access", False, f"Directory not found: {project_path}"))
    
    # Git repository
    if (project_path / ".git").exists():
        checks.append(("Git repository", True, "Valid git repository"))
    else:
        checks.append(("Git repository", False, "Not a git repository"))
    
    # Orchestration state
    state_dir = project_path / ".orch-state"
    if state_dir.exists():
        checks.append(("State directory", True, ".orch-state/ directory exists"))
        
        # Check state file
        state_file = state_dir / "status.json"
        if state_file.exists():
            try:
                with open(state_file, 'r') as f:
                    json.load(f)
                checks.append(("State file", True, "Valid status.json"))
            except Exception:
                checks.append(("State file", False, "Invalid status.json format"))
        else:
            checks.append(("State file", False, "Missing status.json"))
    else:
        checks.append(("State directory", False, "Missing .orch-state/ directory"))
    
    # Permissions
    if os.access(project_path, os.R_OK | os.W_OK):
        checks.append(("Permissions", True, "Read/write access confirmed"))
    else:
        checks.append(("Permissions", False, "Insufficient permissions"))
    
    # Display results
    table = Table(title=f"Validation Results: {name}")
    table.add_column("Check", style="cyan")
    table.add_column("Status", style="white")
    table.add_column("Details", style="dim")
    
    passed = 0
    for check_name, status, details in checks:
        status_icon = "✓" if status else "✗"
        status_color = "green" if status else "red"
        table.add_row(check_name, f"[{status_color}]{status_icon}[/{status_color}]", details)
        if status:
            passed += 1
    
    console.print(table)
    
    # Summary
    if passed == len(checks):
        print_success(f"Project '{name}' validation passed!")
    else:
        print_warning(f"Project '{name}' has {len(checks) - passed} validation issues")
        print_info("Consider re-registering the project to fix issues")