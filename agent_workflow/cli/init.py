"""
Initialization command for agent-workflow CLI.

This module provides the 'agent-orch init' command for setting up
the global orchestrator environment and configuration.
"""

import os
import sys
import yaml
import json
from pathlib import Path
from typing import Optional, Dict, Any
import click
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt, Confirm
from rich.progress import Progress, SpinnerColumn, TextColumn

from .utils import (
    ensure_config_dir,
    print_success,
    print_warning,
    print_error,
    print_info,
    confirm_action
)

console = Console()

# User profiles with default configurations
USER_PROFILES = {
    "solo-engineer": {
        "description": "Human approval required for key decisions",
        "default_mode": "blocking",
        "max_concurrent_projects": 3,
        "approval_timeout": 300,
        "detailed_logging": False,
        "auto_discovery": False
    },
    "team-lead": {
        "description": "Manage multiple projects simultaneously",
        "default_mode": "partial", 
        "max_concurrent_projects": 10,
        "approval_timeout": 600,
        "detailed_logging": True,
        "auto_discovery": True
    },
    "researcher": {
        "description": "Autonomous operation for experiments",
        "default_mode": "autonomous",
        "max_concurrent_projects": 1,
        "approval_timeout": 60,
        "detailed_logging": True,
        "auto_discovery": False
    }
}


@click.command()
@click.option("--config-dir", type=click.Path(), help="Custom configuration directory")
@click.option("--force", is_flag=True, help="Overwrite existing configuration")
@click.option("--interactive", is_flag=True, help="Run interactive setup wizard")
@click.option("--minimal", is_flag=True, help="Create minimal configuration")
@click.option("--profile", type=click.Choice(list(USER_PROFILES.keys())), 
              help="Use predefined profile")
@click.option("--dry-run", is_flag=True, help="Show what would be created")
@click.pass_context
def init_command(ctx, config_dir, force, interactive, minimal, profile, dry_run):
    """Initialize global orchestrator environment."""
    try:
        # Determine configuration directory
        if config_dir:
            config_path = Path(config_dir).expanduser()
        else:
            config_path = ensure_config_dir()
        
        # Check for existing configuration
        config_file = config_path / "config.yaml"
        if config_file.exists() and not force:
            print_error(f"Configuration already exists at {config_file}")
            print_info("Use --force to overwrite or --config-dir to use different location")
            return
        
        # Show what would be created in dry-run mode
        if dry_run:
            _show_dry_run_plan(config_path, profile, minimal)
            return
        
        # Run interactive setup or use defaults
        if interactive:
            config_data = _run_interactive_setup(config_path)
        else:
            config_data = _create_default_config(profile, minimal)
        
        # Create directory structure and files
        _create_config_structure(config_path, config_data, force)
        
        print_success(f"Agent-workflow initialized at {config_path}")
        _show_next_steps()
        
    except Exception as e:
        print_error(f"Failed to initialize agent-workflow: {e}")
        if ctx.obj.get('verbose'):
            import traceback
            console.print(traceback.format_exc())
        sys.exit(1)


def _show_dry_run_plan(config_path: Path, profile: Optional[str], minimal: bool) -> None:
    """Show what would be created without actually creating it."""
    console.print(Panel("Initialization Plan (Dry Run)", style="blue"))
    
    # Directory structure
    dirs_to_create = [
        config_path,
        config_path / "projects",
        config_path / "logs",
        config_path / "templates"
    ]
    
    console.print("\n[bold]Directories to create:[/bold]")
    for dir_path in dirs_to_create:
        status = "exists" if dir_path.exists() else "new"
        color = "yellow" if status == "exists" else "green"
        console.print(f"  [{color}]{status}[/{color}] {dir_path}")
    
    # Files to create
    files_to_create = [
        "config.yaml",
        "credentials.key", 
        "projects/registry.yaml",
        "templates/project-config.yaml.template",
        "templates/config.yml.template"
    ]
    
    console.print("\n[bold]Files to create:[/bold]")
    for file_name in files_to_create:
        file_path = config_path / file_name
        status = "exists" if file_path.exists() else "new" 
        color = "yellow" if status == "exists" else "green"
        console.print(f"  [{color}]{status}[/{color}] {file_path}")
    
    # Configuration details
    if profile:
        profile_config = USER_PROFILES[profile]
        console.print(f"\n[bold]Profile:[/bold] {profile}")
        console.print(f"  Mode: {profile_config['default_mode']}")
        console.print(f"  Max projects: {profile_config['max_concurrent_projects']}")
    
    console.print(f"\n[bold]Setup type:[/bold] {'Minimal' if minimal else 'Full'}")


def _run_interactive_setup(config_path: Path) -> Dict[str, Any]:
    """Run interactive setup wizard."""
    console.print(Panel("Agent-Workflow Setup Wizard", style="blue"))
    
    config_data = {}
    
    # Step 1: Configuration directory confirmation
    console.print("\n[bold]Step 1/6: Configuration Directory[/bold]")
    console.print(f"Configuration will be stored in: [cyan]{config_path}[/cyan]")
    
    if not Confirm.ask("Is this location acceptable?", default=True):
        custom_path = Prompt.ask("Enter custom path")
        config_path = Path(custom_path).expanduser()
        config_data["config_path"] = str(config_path)
    
    # Step 2: User profile selection
    console.print("\n[bold]Step 2/6: User Profile Selection[/bold]")
    console.print("Choose your workflow profile:")
    
    for i, (profile_name, profile_config) in enumerate(USER_PROFILES.items(), 1):
        console.print(f"  [{i}] {profile_name.title().replace('-', ' ')}")
        console.print(f"      {profile_config['description']}")
    
    while True:
        choice = Prompt.ask("Select profile", choices=["1", "2", "3"], default="1")
        profile_names = list(USER_PROFILES.keys())
        selected_profile = profile_names[int(choice) - 1]
        break
    
    config_data.update(USER_PROFILES[selected_profile])
    config_data["user_profile"] = selected_profile
    
    # Step 3: Create sample project
    console.print("\n[bold]Step 3/6: Sample Project[/bold]")
    if Confirm.ask("Would you like to register the current directory as a sample project?", default=False):
        current_dir = Path.cwd()
        config_data["sample_project"] = {
            "name": current_dir.name,
            "path": str(current_dir)
        }
    
    # Step 4: Integration setup prompts
    console.print("\n[bold]Step 4/6: Integration Setup[/bold]")
    config_data["setup_integrations"] = {}
    
    config_data["setup_integrations"]["discord"] = Confirm.ask(
        "Configure Discord bot integration now?", default=False
    )
    
    config_data["setup_integrations"]["ai_provider"] = Confirm.ask(
        "Configure AI provider integration now?", default=False
    )
    
    # Step 5: Advanced settings
    console.print("\n[bold]Step 5/6: Advanced Settings[/bold]")
    if Confirm.ask("Configure advanced settings?", default=False):
        config_data["log_level"] = Prompt.ask(
            "Log level", 
            choices=["DEBUG", "INFO", "WARN", "ERROR"], 
            default="INFO"
        )
        config_data["data_retention_days"] = int(Prompt.ask(
            "Data retention (days)", 
            default="30"
        ))
    
    # Step 6: Confirmation
    console.print("\n[bold]Step 6/6: Confirmation[/bold]")
    console.print("Configuration summary:")
    console.print(f"  Profile: {config_data['user_profile']}")
    console.print(f"  Mode: {config_data['default_mode']}")
    console.print(f"  Max projects: {config_data['max_concurrent_projects']}")
    
    if not Confirm.ask("Proceed with initialization?", default=True):
        print_info("Initialization cancelled")
        sys.exit(0)
    
    return config_data


def _create_default_config(profile: Optional[str], minimal: bool) -> Dict[str, Any]:
    """Create default configuration data."""
    if profile and profile in USER_PROFILES:
        config_data = USER_PROFILES[profile].copy()
        config_data["user_profile"] = profile
    else:
        config_data = USER_PROFILES["solo-engineer"].copy()
        config_data["user_profile"] = "solo-engineer"
    
    # Add minimal flag
    config_data["minimal_setup"] = minimal
    
    return config_data


def _create_config_structure(config_path: Path, config_data: Dict[str, Any], force: bool) -> None:
    """Create the configuration directory structure and files."""
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console
    ) as progress:
        
        # Create directories
        task = progress.add_task("Creating directory structure...", total=None)
        
        directories = [
            config_path,
            config_path / "projects", 
            config_path / "logs",
            config_path / "templates"
        ]
        
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
        
        progress.update(task, description="Creating configuration files...")
        
        # Create main configuration file
        config_file_data = {
            "version": "1.0",
            "created": _get_timestamp(),
            "last_updated": _get_timestamp(),
            "global": {
                "installation_id": _generate_installation_id(),
                "user_profile": config_data.get("user_profile", "solo-engineer"),
                "default_mode": config_data.get("default_mode", "blocking"),
                "log_level": config_data.get("log_level", "INFO"),
                "data_retention_days": config_data.get("data_retention_days", 30),
                "max_concurrent_projects": config_data.get("max_concurrent_projects", 3)
            },
            "ai_provider": {
                "provider": None,
                "model": None,
                "api_endpoint": None,
                "rate_limit": {
                    "requests_per_minute": 50,
                    "tokens_per_minute": 100000
                },
                "credentials_encrypted": False
            },
            "discord": {
                "enabled": False,
                "guild_id": None,
                "channel_prefix": "orch",
                "bot_permissions": ["send_messages", "manage_channels", "embed_links"],
                "credentials_encrypted": False
            },
            "security": {
                "agent_restrictions_enabled": True,
                "command_approval_required": config_data.get("default_mode") == "blocking",
                "dangerous_commands_blocked": True,
                "credential_encryption_enabled": True
            },
            "projects": {
                "registry_path": str(config_path / "projects" / "registry.yaml"),
                "auto_discovery": config_data.get("auto_discovery", False),
                "validation_on_register": True,
                "max_concurrent": config_data.get("max_concurrent_projects", 3)
            }
        }
        
        with open(config_path / "config.yaml", 'w') as f:
            yaml.dump(config_file_data, f, default_flow_style=False, indent=2)
        
        # Create empty project registry
        registry_data = {"projects": {}}
        with open(config_path / "projects" / "registry.yaml", 'w') as f:
            yaml.dump(registry_data, f, default_flow_style=False, indent=2)
        
        # Generate encryption key
        _generate_encryption_key(config_path / "credentials.key")
        
        # Create template files
        _create_template_files(config_path / "templates")
        
        # Register sample project if requested
        if "sample_project" in config_data:
            _register_sample_project(config_path, config_data["sample_project"])
        
        progress.update(task, description="Initialization complete!", completed=True)


def _generate_installation_id() -> str:
    """Generate unique installation ID."""
    import uuid
    return str(uuid.uuid4())


def _get_timestamp() -> str:
    """Get current timestamp in ISO format."""
    from datetime import datetime
    return datetime.now().isoformat()


def _generate_encryption_key(key_path: Path) -> None:
    """Generate encryption key for credentials."""
    try:
        from cryptography.fernet import Fernet
        key = Fernet.generate_key()
        with open(key_path, 'wb') as f:
            f.write(key)
        # Set restrictive permissions
        os.chmod(key_path, 0o600)
    except ImportError:
        # Fallback: create placeholder file
        with open(key_path, 'w') as f:
            f.write("# Encryption key placeholder - install 'cryptography' package for encryption\n")


def _create_template_files(templates_path: Path) -> None:
    """Create configuration template files."""
    
    # Project configuration template
    project_template = {
        "name": "${PROJECT_NAME}",
        "path": "${PROJECT_PATH}",
        "mode": "${ORCHESTRATION_MODE}",
        "framework": "${PROJECT_FRAMEWORK}",
        "language": "${PRIMARY_LANGUAGE}",
        "repository": "${GIT_REPOSITORY_URL}",
        "description": "${PROJECT_DESCRIPTION}",
        "discord_channel": "${DISCORD_CHANNEL}",
        "created": "${CREATION_TIMESTAMP}",
        "metadata": {
            "framework_version": None,
            "dependencies": [],
            "test_framework": None,
            "ci_cd": None
        }
    }
    
    with open(templates_path / "project-config.yaml.template", 'w') as f:
        yaml.dump(project_template, f, default_flow_style=False, indent=2)
    
    # Orchestrator configuration template
    orch_template = {
        "projects": [
            {
                "name": "${PROJECT_NAME}",
                "path": "${PROJECT_PATH}",
                "orchestration": "${ORCHESTRATION_MODE}"
            }
        ]
    }
    
    with open(templates_path / "config.yml.template", 'w') as f:
        yaml.dump(orch_template, f, default_flow_style=False, indent=2)


def _register_sample_project(config_path: Path, project_data: Dict[str, str]) -> None:
    """Register sample project in the registry."""
    registry_path = config_path / "projects" / "registry.yaml"
    
    with open(registry_path, 'r') as f:
        registry = yaml.safe_load(f)
    
    registry["projects"][project_data["name"]] = {
        "name": project_data["name"],
        "path": project_data["path"],
        "registered": _get_timestamp(),
        "last_active": None,
        "mode": "blocking",
        "framework": "general",
        "status": "idle",
        "metadata": {
            "language": "unknown",
            "repository": None
        }
    }
    
    with open(registry_path, 'w') as f:
        yaml.dump(registry, f, default_flow_style=False, indent=2)


def _show_next_steps() -> None:
    """Show next steps after successful initialization."""
    next_steps = [
        "Configure AI provider: agent-orch setup-api --interactive",
        "Configure Discord (optional): agent-orch setup-discord --interactive", 
        "Register your first project: agent-orch register-project <path>",
        "Start orchestration: agent-orch start --discord"
    ]
    
    console.print("\n[bold]Next Steps:[/bold]")
    for i, step in enumerate(next_steps, 1):
        console.print(f"  {i}. {step}")
    
    console.print("\n[dim]For help with any command, run: agent-orch <command> --help[/dim]")