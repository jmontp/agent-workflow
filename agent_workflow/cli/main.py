#!/usr/bin/env python3
"""
Main CLI entry point for agent-workflow package.

This module provides the primary command-line interface with all core commands
and serves as the entry point for the 'agent-orch' and 'aw' console scripts.
"""

import os
import sys
import click
from pathlib import Path
from typing import Optional

# Add package root to path for development
package_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(package_root))

from agent_workflow import __version__, get_package_info
from agent_workflow.cli.utils import (
    check_system_requirements, 
    setup_logging,
    get_config_dir,
    print_banner,
    handle_cli_error
)

# Import command modules
try:
    from agent_workflow.cli.init import init_command
    from agent_workflow.cli.project import register_command, projects_command  
    from agent_workflow.cli.setup import setup_discord_command, setup_api_command, configure_command
    from agent_workflow.cli.orchestrator import start_command, stop_command, status_command
    from agent_workflow.cli.info import version_command, health_command
    from agent_workflow.cli.migrate import migrate_command
    from agent_workflow.cli.web import web_command, web_stop_command, web_status_command
    from agent_workflow.cli.config import config
except ImportError as e:
    # Graceful fallback if command modules aren't implemented yet
    init_command = None
    register_command = None
    projects_command = None
    setup_discord_command = None 
    setup_api_command = None
    configure_command = None
    start_command = None
    stop_command = None
    status_command = None
    version_command = None
    health_command = None
    migrate_command = None
    web_command = None
    web_stop_command = None
    web_status_command = None
    config = None


@click.group(name="agent-orch", invoke_without_command=True)
@click.option("--version", is_flag=True, help="Show version and exit")
@click.option("--verbose", "-v", is_flag=True, help="Enable verbose output")
@click.option("--config-dir", type=click.Path(), help="Custom configuration directory")
@click.option("--no-banner", is_flag=True, help="Suppress welcome banner")
@click.pass_context
def cli(ctx, version, verbose, config_dir, no_banner):
    """
    Agent-Workflow: AI Agent TDD-Scrum Orchestration Framework
    
    A comprehensive framework for coordinating AI agents in Test-Driven Development
    and Scrum workflows, with Human-in-the-Loop oversight and multi-project support.
    
    \b
    Quick Start:
      agent-orch init                    # Initialize global environment
      agent-orch register-project .      # Register current directory
      agent-orch start --discord         # Start with Discord integration
    
    \b
    Common Commands:
      init                Initialize global orchestrator environment
      register-project    Register project for orchestration  
      start              Start orchestration for projects
      status             Display orchestrator and project status
      configure          Interactive configuration management
    
    \b
    Integration Commands:
      setup-discord      Configure Discord bot integration
      setup-api          Configure AI provider integration
    
    \b
    Management Commands:
      projects           Manage registered projects
      health             System health check and diagnostics
      migrate            Migrate from git-clone installation
      web                Start web visualization interface
    
    Visit https://agent-workflow.readthedocs.io for comprehensive documentation.
    """
    # Ensure context object exists
    ctx.ensure_object(dict)
    
    # Store global options in context
    ctx.obj['verbose'] = verbose
    ctx.obj['config_dir'] = config_dir or get_config_dir()
    ctx.obj['no_banner'] = no_banner
    
    # Setup logging
    setup_logging(verbose=verbose)
    
    # Show version if requested
    if version:
        if version_command:
            ctx.invoke(version_command)
        else:
            click.echo(f"agent-workflow {__version__}")
        return
    
    # Show help if no command provided
    if ctx.invoked_subcommand is None:
        if not no_banner:
            print_banner()
        click.echo(ctx.get_help())
        
        # Show system status if available
        try:
            if status_command:
                click.echo("\n" + "="*60)
                click.echo("Current System Status:")
                click.echo("="*60)
                ctx.invoke(status_command, brief=True)
        except Exception:
            # Ignore errors in status display
            pass


# ============================================================================
# Core Commands
# ============================================================================

@cli.command()
@click.option("--config-dir", type=click.Path(), help="Custom configuration directory")
@click.option("--force", is_flag=True, help="Overwrite existing configuration")
@click.option("--interactive", is_flag=True, help="Run interactive setup wizard")
@click.option("--minimal", is_flag=True, help="Create minimal configuration")
@click.option("--profile", type=click.Choice(["solo-engineer", "team-lead", "researcher"]), 
              help="Use predefined profile")
@click.option("--dry-run", is_flag=True, help="Show what would be created")
@click.pass_context
def init(ctx, config_dir, force, interactive, minimal, profile, dry_run):
    """Initialize global orchestrator environment."""
    if init_command:
        ctx.invoke(init_command, 
                  config_dir=config_dir, 
                  force=force, 
                  interactive=interactive,
                  minimal=minimal,
                  profile=profile,
                  dry_run=dry_run)
    else:
        handle_cli_error("init command not yet implemented")


@cli.command("register-project")
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
def register_project(ctx, path, name, mode, framework, validate, create_channel, 
                     language, repository, description, force):
    """Register existing project for orchestration."""
    if register_command:
        ctx.invoke(register_command,
                  path=path,
                  name=name,
                  mode=mode,
                  framework=framework,
                  validate=validate,
                  create_channel=create_channel,
                  language=language,
                  repository=repository,
                  description=description,
                  force=force)
    else:
        handle_cli_error("register-project command not yet implemented")


@cli.command()
@click.argument("subcommand", type=click.Choice(["list", "remove", "validate"]))
@click.argument("name", required=False)
@click.option("--verbose", is_flag=True, help="Show detailed information")
@click.pass_context
def projects(ctx, subcommand, name, verbose):
    """Manage registered projects."""
    if projects_command:
        ctx.invoke(projects_command, subcommand=subcommand, name=name, verbose=verbose)
    else:
        handle_cli_error("projects command not yet implemented")


# ============================================================================
# Orchestrator Control Commands  
# ============================================================================

@cli.command()
@click.argument("project", required=False)
@click.option("--mode", type=click.Choice(["blocking", "partial", "autonomous"]),
              help="Override orchestration mode")
@click.option("--discord", is_flag=True, help="Start with Discord bot integration")
@click.option("--daemon", is_flag=True, help="Run as background daemon")
@click.option("--log-level", type=click.Choice(["DEBUG", "INFO", "WARN", "ERROR"]),
              default="INFO", help="Set logging level")
@click.option("--config", type=click.Path(), help="Use custom configuration file")
@click.option("--port", type=int, default=8080, help="API port for status/control")
@click.option("--no-browser", is_flag=True, help="Don't open status page in browser")
@click.pass_context
def start(ctx, project, mode, discord, daemon, log_level, config, port, no_browser):
    """Start orchestration for projects."""
    if start_command:
        ctx.invoke(start_command,
                  project=project,
                  mode=mode,
                  discord=discord,
                  daemon=daemon,
                  log_level=log_level,
                  config=config,
                  port=port,
                  no_browser=no_browser)
    else:
        handle_cli_error("start command not yet implemented")


@cli.command()
@click.option("--force", is_flag=True, help="Force stop without graceful shutdown")
@click.option("--save-state", is_flag=True, help="Save current state before stopping")
@click.option("--project", help="Stop specific project only")
@click.pass_context
def stop(ctx, force, save_state, project):
    """Stop orchestrator and cleanup."""
    if stop_command:
        ctx.invoke(stop_command, force=force, save_state=save_state, project=project)
    else:
        handle_cli_error("stop command not yet implemented")


@cli.command()
@click.option("--project", help="Show status for specific project")
@click.option("--verbose", is_flag=True, help="Show detailed status information")
@click.option("--json", "output_json", is_flag=True, help="Output in JSON format")
@click.option("--watch", is_flag=True, help="Continuously update status display")
@click.option("--health", is_flag=True, help="Include health check information")
@click.option("--brief", is_flag=True, help="Brief status summary")
@click.pass_context
def status(ctx, project, verbose, output_json, watch, health, brief):
    """Display orchestrator and project status."""
    if status_command:
        ctx.invoke(status_command,
                  project=project,
                  verbose=verbose,
                  output_json=output_json,
                  watch=watch,
                  health=health,
                  brief=brief)
    else:
        handle_cli_error("status command not yet implemented")


# ============================================================================
# Configuration Commands
# ============================================================================

@cli.command("setup-discord")
@click.option("--token", help="Discord bot token")
@click.option("--guild-id", help="Discord server ID")
@click.option("--interactive", is_flag=True, help="Interactive setup with validation")
@click.option("--test-connection", is_flag=True, help="Test connection after setup")
@click.option("--create-channels", is_flag=True, help="Auto-create project channels")
@click.option("--channel-prefix", default="orch", help="Channel naming prefix")
@click.pass_context
def setup_discord(ctx, token, guild_id, interactive, test_connection, create_channels, channel_prefix):
    """Configure Discord bot integration."""
    if setup_discord_command:
        ctx.invoke(setup_discord_command,
                  token=token,
                  guild_id=guild_id,
                  interactive=interactive,
                  test_connection=test_connection,
                  create_channels=create_channels,
                  channel_prefix=channel_prefix)
    else:
        handle_cli_error("setup-discord command not yet implemented")


@cli.command("setup-api")
@click.option("--provider", type=click.Choice(["claude", "openai", "local"]),
              default="claude", help="AI provider")
@click.option("--key", help="API key")
@click.option("--endpoint", help="Custom API endpoint")
@click.option("--model", help="Default model name")
@click.option("--interactive", is_flag=True, help="Interactive setup with validation")
@click.option("--test-connection", is_flag=True, help="Test API connection")
@click.option("--rate-limit", type=int, help="Requests per minute limit")
@click.pass_context
def setup_api(ctx, provider, key, endpoint, model, interactive, test_connection, rate_limit):
    """Configure AI provider integration."""
    if setup_api_command:
        ctx.invoke(setup_api_command,
                  provider=provider,
                  key=key,
                  endpoint=endpoint,
                  model=model,
                  interactive=interactive,
                  test_connection=test_connection,
                  rate_limit=rate_limit)
    else:
        handle_cli_error("setup-api command not yet implemented")


@cli.command()
@click.option("--section", type=click.Choice(["global", "discord", "api", "projects", "security"]),
              help="Configure specific section")
@click.option("--reset", is_flag=True, help="Reset configuration to defaults")
@click.option("--export", type=click.Path(), help="Export configuration to file")
@click.option("--import", "import_file", type=click.Path(), help="Import configuration from file")
@click.option("--validate", is_flag=True, help="Validate current configuration")
@click.option("--wizard", is_flag=True, help="Run full configuration wizard")
@click.pass_context
def configure(ctx, section, reset, export, import_file, validate, wizard):
    """Interactive configuration management."""
    if configure_command:
        ctx.invoke(configure_command,
                  section=section,
                  reset=reset,
                  export=export,
                  import_file=import_file,
                  validate=validate,
                  wizard=wizard)
    else:
        handle_cli_error("configure command not yet implemented")


# ============================================================================
# Information Commands
# ============================================================================

@cli.command()
@click.option("--check-updates", is_flag=True, help="Check for available updates")
@click.option("--verbose", is_flag=True, help="Show detailed system information")
@click.pass_context
def version(ctx, check_updates, verbose):
    """Display version and system information."""
    if version_command:
        ctx.invoke(version_command, check_updates=check_updates, verbose=verbose)
    else:
        # Fallback implementation
        click.echo(f"agent-workflow {__version__}")
        if verbose:
            pkg_info = get_package_info()
            click.echo(f"Python: {sys.version}")
            click.echo(f"Platform: {sys.platform}")
            click.echo(f"Repository: {pkg_info['repository']}")
            click.echo(f"Documentation: {pkg_info['documentation']}")


@cli.command()
@click.option("--check-all", is_flag=True, help="Run comprehensive health check")
@click.option("--fix-issues", is_flag=True, help="Attempt to fix detected issues")
@click.option("--export-report", type=click.Path(), help="Export health report to file")
@click.option("--project", help="Check specific project health")
@click.pass_context
def health(ctx, check_all, fix_issues, export_report, project):
    """System health check and diagnostics."""
    if health_command:
        ctx.invoke(health_command,
                  check_all=check_all,
                  fix_issues=fix_issues,
                  export_report=export_report,
                  project=project)
    else:
        handle_cli_error("health command not yet implemented")


# ============================================================================
# Web Interface Commands
# ============================================================================

@cli.command()
@click.option("--port", type=int, default=5000, help="Web interface port")
@click.option("--host", default="localhost", help="Host to bind to")
@click.option("--daemon", is_flag=True, help="Run as background daemon")
@click.option("--debug", is_flag=True, help="Enable debug mode")
@click.option("--no-browser", is_flag=True, help="Don't open browser automatically")
@click.option("--log-level", type=click.Choice(["DEBUG", "INFO", "WARN", "ERROR"]),
              default="INFO", help="Set logging level")
@click.pass_context
def web(ctx, port, host, daemon, debug, no_browser, log_level):
    """Start the web visualization interface."""
    if web_command:
        ctx.invoke(web_command,
                  port=port,
                  host=host,
                  daemon=daemon,
                  debug=debug,
                  no_browser=no_browser,
                  log_level=log_level)
    else:
        handle_cli_error("web command not yet implemented")


@cli.command("web-stop")
@click.option("--force", is_flag=True, help="Force stop without graceful shutdown")
@click.pass_context
def web_stop(ctx, force):
    """Stop the web interface."""
    if web_stop_command:
        ctx.invoke(web_stop_command, force=force)
    else:
        handle_cli_error("web-stop command not yet implemented")


@cli.command("web-status")
@click.option("--verbose", is_flag=True, help="Show detailed status information")
@click.option("--json", "output_json", is_flag=True, help="Output in JSON format")
@click.pass_context
def web_status(ctx, verbose, output_json):
    """Display web interface status."""
    if web_status_command:
        ctx.invoke(web_status_command, verbose=verbose, output_json=output_json)
    else:
        handle_cli_error("web-status command not yet implemented")


# ============================================================================
# Configuration Management Commands
# ============================================================================

# Add configuration command group if available
if config:
    cli.add_command(config)


# ============================================================================
# Migration Commands
# ============================================================================

@cli.command("migrate-from-git")
@click.argument("source_path", type=click.Path(exists=True))
@click.option("--backup-first", is_flag=True, help="Create backup before migration")
@click.option("--import-projects", is_flag=True, help="Auto-discover and register projects")
@click.option("--preserve-config", is_flag=True, help="Keep existing configuration files")
@click.option("--dry-run", is_flag=True, help="Show migration plan without executing")
@click.pass_context
def migrate_from_git(ctx, source_path, backup_first, import_projects, preserve_config, dry_run):
    """Migrate from git-clone installation."""
    if migrate_command:
        ctx.invoke(migrate_command,
                  source_path=source_path,
                  backup_first=backup_first,
                  import_projects=import_projects,
                  preserve_config=preserve_config,
                  dry_run=dry_run)
    else:
        handle_cli_error("migrate-from-git command not yet implemented")


# ============================================================================
# Error Handling and Utilities
# ============================================================================

def main():
    """Main entry point for console scripts."""
    try:
        # Check system requirements before starting
        if not check_system_requirements():
            sys.exit(1)
            
        # Run CLI with error handling
        cli(obj={})
        
    except KeyboardInterrupt:
        click.echo("\nOperation cancelled by user.")
        sys.exit(130)
    except Exception as e:
        handle_cli_error(f"Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()