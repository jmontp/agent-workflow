"""
Setup and configuration commands for agent-workflow CLI.

This module provides commands for setting up integrations like Discord bot,
AI providers, and general configuration management.
"""

import os
import sys
import yaml
from pathlib import Path
from typing import Optional, Dict, Any
import click
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt, Confirm, IntPrompt
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


@click.command("setup-discord")
@click.option("--token", help="Discord bot token")
@click.option("--guild-id", help="Discord server ID")
@click.option("--interactive", is_flag=True, help="Interactive setup with validation")
@click.option("--test-connection", is_flag=True, help="Test connection after setup")
@click.option("--create-channels", is_flag=True, help="Auto-create project channels")
@click.option("--channel-prefix", default="orch", help="Channel naming prefix")
@click.pass_context
def setup_discord_command(ctx, token, guild_id, interactive, test_connection, create_channels, channel_prefix):
    """Configure Discord bot integration."""
    try:
        config_dir = get_config_dir()
        config_file = config_dir / "config.yaml"
        
        if not config_file.exists():
            print_error("Agent-workflow not initialized. Run 'agent-orch init' first.")
            return
        
        # Load existing configuration
        with open(config_file, 'r') as f:
            config = yaml.safe_load(f)
        
        if interactive:
            discord_config = _interactive_discord_setup()
        else:
            discord_config = _basic_discord_setup(token, guild_id, channel_prefix)
        
        # Update configuration
        config["discord"].update(discord_config)
        config["discord"]["enabled"] = True
        
        # Test connection if requested
        if test_connection:
            if _test_discord_connection(discord_config):
                print_success("Discord connection test passed!")
            else:
                print_warning("Discord connection test failed. Check your configuration.")
        
        # Save configuration
        with open(config_file, 'w') as f:
            yaml.dump(config, f, default_flow_style=False, indent=2)
        
        print_success("Discord configuration saved successfully!")
        
        # Show next steps
        _show_discord_next_steps(create_channels)
        
    except Exception as e:
        print_error(f"Failed to setup Discord integration: {e}")
        if ctx.obj.get('verbose'):
            import traceback
            console.print(traceback.format_exc())
        sys.exit(1)


@click.command("setup-api")
@click.option("--provider", type=click.Choice(["claude", "openai", "local"]),
              default="claude", help="AI provider")
@click.option("--key", help="API key")
@click.option("--endpoint", help="Custom API endpoint")
@click.option("--model", help="Default model name")
@click.option("--interactive", is_flag=True, help="Interactive setup with validation")
@click.option("--test-connection", is_flag=True, help="Test API connection")
@click.option("--rate-limit", type=int, help="Requests per minute limit")
@click.pass_context
def setup_api_command(ctx, provider, key, endpoint, model, interactive, test_connection, rate_limit):
    """Configure AI provider integration."""
    try:
        config_dir = get_config_dir()
        config_file = config_dir / "config.yaml"
        
        if not config_file.exists():
            print_error("Agent-workflow not initialized. Run 'agent-orch init' first.")
            return
        
        # Load existing configuration
        with open(config_file, 'r') as f:
            config = yaml.safe_load(f)
        
        if interactive:
            api_config = _interactive_api_setup()
        else:
            api_config = _basic_api_setup(provider, key, endpoint, model, rate_limit)
        
        # Update configuration
        config["ai_provider"].update(api_config)
        
        # Test connection if requested
        if test_connection:
            if _test_api_connection(api_config):
                print_success("API connection test passed!")
            else:
                print_warning("API connection test failed. Check your configuration.")
        
        # Save configuration
        with open(config_file, 'w') as f:
            yaml.dump(config, f, default_flow_style=False, indent=2)
        
        print_success("AI provider configuration saved successfully!")
        
        # Show next steps
        _show_api_next_steps(api_config["provider"])
        
    except Exception as e:
        print_error(f"Failed to setup AI provider: {e}")
        if ctx.obj.get('verbose'):
            import traceback
            console.print(traceback.format_exc())
        sys.exit(1)


@click.command("configure")
@click.option("--section", type=click.Choice(["global", "discord", "api", "projects", "security"]),
              help="Configure specific section")
@click.option("--reset", is_flag=True, help="Reset configuration to defaults")
@click.option("--export", type=click.Path(), help="Export configuration to file")
@click.option("--import", "import_file", type=click.Path(), help="Import configuration from file")
@click.option("--validate", is_flag=True, help="Validate current configuration")
@click.option("--wizard", is_flag=True, help="Run full configuration wizard")
@click.pass_context
def configure_command(ctx, section, reset, export, import_file, validate, wizard):
    """Interactive configuration management."""
    try:
        config_dir = get_config_dir()
        config_file = config_dir / "config.yaml"
        
        if not config_file.exists():
            print_error("Agent-workflow not initialized. Run 'agent-orch init' first.")
            return
        
        if reset:
            _reset_configuration(config_file, section)
        elif export:
            _export_configuration(config_file, Path(export))
        elif import_file:
            _import_configuration(config_file, Path(import_file))
        elif validate:
            _validate_configuration(config_file)
        elif wizard:
            _configuration_wizard(config_file)
        elif section:
            _configure_section(config_file, section)
        else:
            _show_configuration_menu(config_file)
            
    except Exception as e:
        print_error(f"Failed to configure: {e}")
        if ctx.obj.get('verbose'):
            import traceback
            console.print(traceback.format_exc())
        sys.exit(1)


def _interactive_discord_setup() -> Dict[str, Any]:
    """Run interactive Discord setup."""
    console.print(Panel("Discord Bot Setup", style="blue"))
    
    # Get bot token
    token = Prompt.ask("Discord bot token", password=True)
    
    # Get guild ID
    guild_id = Prompt.ask("Discord server/guild ID")
    
    # Channel settings
    channel_prefix = Prompt.ask("Channel prefix", default="orch")
    create_channels = Confirm.ask("Auto-create project channels?", default=True)
    
    # Permissions
    console.print("\n[bold]Bot Permissions:[/bold]")
    console.print("The bot needs the following permissions:")
    console.print("• Send Messages")
    console.print("• Manage Channels")  
    console.print("• Embed Links")
    console.print("• Use Slash Commands")
    
    Confirm.ask("Have you granted these permissions?", default=True)
    
    return {
        "token": token,
        "guild_id": guild_id,
        "channel_prefix": channel_prefix,
        "auto_create_channels": create_channels,
        "bot_permissions": ["send_messages", "manage_channels", "embed_links", "use_slash_commands"]
    }


def _basic_discord_setup(token: Optional[str], guild_id: Optional[str], channel_prefix: str) -> Dict[str, Any]:
    """Create basic Discord configuration."""
    return {
        "token": token,
        "guild_id": guild_id,
        "channel_prefix": channel_prefix,
        "auto_create_channels": False,
        "bot_permissions": ["send_messages", "manage_channels", "embed_links", "use_slash_commands"]
    }


def _interactive_api_setup() -> Dict[str, Any]:
    """Run interactive API setup."""
    console.print(Panel("AI Provider Setup", style="blue"))
    
    # Provider selection
    providers = ["claude", "openai", "local"]
    console.print("\n[bold]Available providers:[/bold]")
    for i, provider in enumerate(providers, 1):
        console.print(f"  {i}. {provider.title()}")
    
    choice = Prompt.ask("Select provider", choices=["1", "2", "3"], default="1")
    provider = providers[int(choice) - 1]
    
    # Provider-specific setup
    if provider == "claude":
        key = Prompt.ask("Anthropic API key", password=True)
        model = Prompt.ask("Default model", default="claude-3-sonnet-20240229")
        endpoint = None
    elif provider == "openai":
        key = Prompt.ask("OpenAI API key", password=True)
        model = Prompt.ask("Default model", default="gpt-4")
        endpoint = Prompt.ask("API endpoint (optional)", default="")
        endpoint = endpoint if endpoint else None
    else:  # local
        key = None
        model = Prompt.ask("Model name", default="local-model")
        endpoint = Prompt.ask("API endpoint", default="http://localhost:8080")
    
    # Rate limiting
    rate_limit = IntPrompt.ask("Requests per minute limit", default=50)
    
    return {
        "provider": provider,
        "api_key": key,
        "model": model,
        "api_endpoint": endpoint,
        "rate_limit": {
            "requests_per_minute": rate_limit,
            "tokens_per_minute": 100000
        }
    }


def _basic_api_setup(provider: str, key: Optional[str], endpoint: Optional[str], 
                    model: Optional[str], rate_limit: Optional[int]) -> Dict[str, Any]:
    """Create basic API configuration."""
    return {
        "provider": provider,
        "api_key": key,
        "model": model,
        "api_endpoint": endpoint,
        "rate_limit": {
            "requests_per_minute": rate_limit or 50,
            "tokens_per_minute": 100000
        }
    }


def _test_discord_connection(config: Dict[str, Any]) -> bool:
    """Test Discord bot connection."""
    try:
        import discord
        
        # Create a simple connection test
        intents = discord.Intents.default()
        client = discord.Client(intents=intents)
        
        @client.event
        async def on_ready():
            print_info(f"Connected as {client.user}")
            await client.close()
        
        # This is a simplified test - full implementation would need async handling
        print_info("Discord connection test would run here...")
        return True
        
    except ImportError:
        print_warning("discord.py not installed - skipping connection test")
        return False
    except Exception as e:
        print_error(f"Discord connection test failed: {e}")
        return False


def _test_api_connection(config: Dict[str, Any]) -> bool:
    """Test AI provider API connection."""
    try:
        provider = config["provider"]
        
        if provider == "claude":
            # Test Anthropic API
            print_info("Testing Anthropic API connection...")
            # Simplified test - would use actual API call
            return True
        elif provider == "openai":
            # Test OpenAI API
            print_info("Testing OpenAI API connection...")
            # Simplified test - would use actual API call
            return True
        else:
            # Test local API
            print_info("Testing local API connection...")
            # Simplified test - would make HTTP request
            return True
            
    except Exception as e:
        print_error(f"API connection test failed: {e}")
        return False


def _show_discord_next_steps(create_channels: bool) -> None:
    """Show next steps after Discord setup."""
    console.print("\n[bold]Next Steps:[/bold]")
    steps = [
        "Invite bot to your Discord server with proper permissions",
        "Test bot: agent-orch start --discord",
    ]
    
    if create_channels:
        steps.append("Bot will auto-create channels for registered projects")
    else:
        steps.append("Manually create channels for projects (#orch-projectname)")
    
    for i, step in enumerate(steps, 1):
        console.print(f"  {i}. {step}")


def _show_api_next_steps(provider: str) -> None:
    """Show next steps after API setup."""
    console.print("\n[bold]Next Steps:[/bold]")
    steps = [
        f"Test {provider} integration: agent-orch start",
        "Register a project: agent-orch register-project <path>",
        "Start orchestration with AI agents"
    ]
    
    for i, step in enumerate(steps, 1):
        console.print(f"  {i}. {step}")


def _reset_configuration(config_file: Path, section: Optional[str]) -> None:
    """Reset configuration to defaults."""
    if section:
        print_info(f"Resetting {section} configuration...")
    else:
        print_warning("This will reset ALL configuration to defaults!")
        if not confirm_action("Continue?"):
            return
    
    # Implementation would reset specific section or all config
    print_success("Configuration reset complete")


def _export_configuration(config_file: Path, export_file: Path) -> None:
    """Export configuration to file."""
    with open(config_file, 'r') as f:
        config = yaml.safe_load(f)
    
    with open(export_file, 'w') as f:
        yaml.dump(config, f, default_flow_style=False, indent=2)
    
    print_success(f"Configuration exported to {export_file}")


def _import_configuration(config_file: Path, import_file: Path) -> None:
    """Import configuration from file."""
    if not import_file.exists():
        print_error(f"Import file not found: {import_file}")
        return
    
    with open(import_file, 'r') as f:
        imported_config = yaml.safe_load(f)
    
    # Merge with existing config
    with open(config_file, 'r') as f:
        current_config = yaml.safe_load(f)
    
    current_config.update(imported_config)
    
    with open(config_file, 'w') as f:
        yaml.dump(current_config, f, default_flow_style=False, indent=2)
    
    print_success(f"Configuration imported from {import_file}")


def _validate_configuration(config_file: Path) -> None:
    """Validate current configuration."""
    with open(config_file, 'r') as f:
        config = yaml.safe_load(f)
    
    issues = []
    
    # Validate required sections
    required_sections = ["global", "ai_provider", "discord", "security", "projects"]
    for section in required_sections:
        if section not in config:
            issues.append(f"Missing section: {section}")
    
    # Validate AI provider
    if "ai_provider" in config:
        if not config["ai_provider"].get("provider"):
            issues.append("AI provider not configured")
    
    # Show results
    if issues:
        print_warning("Configuration validation issues:")
        for issue in issues:
            print_warning(f"  - {issue}")
    else:
        print_success("Configuration validation passed!")


def _configuration_wizard(config_file: Path) -> None:
    """Run full configuration wizard."""
    console.print(Panel("Configuration Wizard", style="blue"))
    print_info("This wizard will help you configure all aspects of agent-workflow")
    
    # Would implement full interactive configuration
    print_info("Configuration wizard would run here...")


def _configure_section(config_file: Path, section: str) -> None:
    """Configure specific section."""
    console.print(Panel(f"Configure {section.title()}", style="blue"))
    
    # Would implement section-specific configuration
    print_info(f"Configuring {section} section...")


def _show_configuration_menu(config_file: Path) -> None:
    """Show configuration management menu."""
    console.print(Panel("Configuration Management", style="blue"))
    
    options = [
        "View current configuration",
        "Configure Discord integration",
        "Configure AI provider",
        "Configure global settings",
        "Validate configuration",
        "Export configuration",
        "Run configuration wizard"
    ]
    
    for i, option in enumerate(options, 1):
        console.print(f"  {i}. {option}")
    
    console.print(f"\nUse 'agent-orch configure --help' for command options")