"""
Configuration management commands for the agent-workflow CLI.

This module provides commands for validating, generating, and managing
configuration files and environment variables.
"""

import click
from pathlib import Path
from typing import Optional
from .utils import (
    console, 
    validate_config, 
    load_config_with_validation,
    print_success, 
    print_error, 
    print_warning,
    print_info
)


@click.group()
def config():
    """Configuration management commands."""
    pass


@config.command()
@click.option('--schema', '-s', default='all', help='Configuration schema to validate (all, orchestration, dependency)')
@click.option('--config-file', '-c', type=click.Path(exists=True), help='Specific config file to validate')
@click.option('--verbose', '-v', is_flag=True, help='Show detailed validation results')
def validate(schema: str, config_file: Optional[str], verbose: bool):
    """Validate system configuration and environment variables."""
    print_info("Validating system configuration...")
    
    if config_file:
        # Validate specific file
        results = load_config_with_validation(config_file, schema)
        
        if results['valid']:
            print_success(f"Configuration file {config_file} is valid")
        else:
            print_error(f"Configuration file {config_file} has errors:")
            for error in results['errors']:
                console.print(f"  [red]✗[/red] {error}")
        
        if verbose and results['warnings']:
            print_warning("Warnings:")
            for warning in results['warnings']:
                console.print(f"  [yellow]⚠[/yellow] {warning}")
    
    else:
        # Validate all configurations
        results = validate_config()
        
        if results['overall_valid']:
            print_success("All configurations are valid")
        else:
            print_error("Configuration validation failed")
        
        if verbose:
            # Show detailed results
            console.print("\n[bold]Validation Summary:[/bold]")
            console.print(f"  Total files: {results['summary']['total_files']}")
            console.print(f"  Valid files: {results['summary']['valid_files']}")
            console.print(f"  Environment variables: {results['summary']['total_env_vars']}")
            console.print(f"  Valid env vars: {results['summary']['valid_env_vars']}")
            
            # Show file-specific results
            if results['files']:
                console.print("\n[bold]Configuration Files:[/bold]")
                for filename, file_results in results['files'].items():
                    status = "✓" if file_results['valid'] else "✗"
                    color = "green" if file_results['valid'] else "red"
                    console.print(f"  [{color}]{status}[/{color}] {filename}")
                    
                    if not file_results['valid'] and file_results['errors']:
                        for error in file_results['errors']:
                            console.print(f"    [red]✗[/red] {error}")
            
            # Show environment variable results
            if results['env_vars']:
                console.print("\n[bold]Environment Variables:[/bold]")
                for schema_name, env_results in results['env_vars'].items():
                    status = "✓" if env_results['valid'] else "✗"
                    color = "green" if env_results['valid'] else "red"
                    console.print(f"  [{color}]{status}[/{color}] {schema_name}")
                    
                    if not env_results['valid'] and env_results['errors']:
                        for error in env_results['errors']:
                            console.print(f"    [red]✗[/red] {error}")


@config.command()
@click.option('--template', '-t', required=True, 
              type=click.Choice(['orch-dev', 'orch-prod', 'dependency', 'context', 'env']),
              help='Template type to generate')
@click.option('--output', '-o', type=click.Path(), help='Output file path')
@click.option('--format', 'output_format', type=click.Choice(['yaml', 'json', 'env']), default='yaml', help='Output format')
def generate(template: str, output: Optional[str], output_format: str):
    """Generate configuration templates."""
    try:
        from ..config.templates import ConfigTemplates
        
        # Determine output file if not specified
        if not output:
            if template == 'env':
                output = ".env.template"
                output_format = "env"
            elif template.startswith('orch-'):
                output = f"orch-config.{output_format}"
            else:
                output = f"{template}-config.{output_format}"
        
        # Generate template
        success = ConfigTemplates.save_template(template, output, output_format)
        
        if success:
            print_success(f"Generated {template} template: {output}")
            
            # Show usage instructions
            if template == 'env':
                console.print("\n[dim]Copy to .env and customize as needed[/dim]")
            else:
                console.print(f"\n[dim]Configuration saved to {output}[/dim]")
                console.print(f"[dim]Edit the file and place it in your configuration directory[/dim]")
        else:
            print_error(f"Failed to generate template: {template}")
        
    except ImportError:
        print_error("Configuration templates module not available")
    except Exception as e:
        print_error(f"Error generating template: {str(e)}")


@config.command('list-templates')
def list_templates():
    """List available configuration templates."""
    try:
        from ..config.templates import ConfigTemplates
        
        templates = ConfigTemplates.list_templates()
        
        console.print("\n[bold]Available Configuration Templates:[/bold]")
        for name, description in templates.items():
            console.print(f"  [cyan]{name}[/cyan] - {description}")
        
        console.print("\n[dim]Use 'agent-orch config generate --template <name>' to create templates[/dim]")
        
    except ImportError:
        print_error("Configuration templates module not available")
    except Exception as e:
        print_error(f"Error listing templates: {str(e)}")


@config.command()
@click.option('--schema', '-s', help='Show environment variables for specific schema')
def show_env(schema: Optional[str]):
    """Show environment variable documentation."""
    try:
        from ..config import validator
        
        if schema:
            schemas = [schema] if schema in validator.schemas else []
            if not schemas:
                print_error(f"Unknown schema: {schema}")
                return
        else:
            schemas = validator.schemas.keys()
        
        for schema_name in schemas:
            schema_obj = validator.schemas[schema_name]
            console.print(f"\n[bold]{schema_obj.description}[/bold]")
            console.print(f"Schema: {schema_name}")
            console.print()
            
            if schema_obj.env_vars:
                for var_name, env_var in schema_obj.env_vars.items():
                    console.print(f"  [cyan]{env_var.name}[/cyan]")
                    console.print(f"    Description: {env_var.description}")
                    console.print(f"    Required: {'Yes' if env_var.required else 'No'}")
                    console.print(f"    Default: {env_var.default or 'None'}")
                    
                    # Show current value
                    import os
                    current_value = os.getenv(env_var.name, env_var.default)
                    if current_value:
                        console.print(f"    Current: {current_value}")
                    else:
                        console.print("    Current: [dim]Not set[/dim]")
                    console.print()
            else:
                console.print("  No environment variables defined")
                
    except ImportError:
        print_error("Configuration validation module not available")
    except Exception as e:
        print_error(f"Error showing environment variables: {str(e)}")


@config.command()
@click.option('--all', '-a', is_flag=True, help='Show all configuration files')
def list_files(all: bool):
    """List configuration files in the system."""
    from .utils import get_config_dir
    
    config_dir = get_config_dir()
    
    console.print(f"Configuration directory: [cyan]{config_dir}[/cyan]")
    console.print()
    
    # Common configuration files
    config_files = [
        ("orch-config.yaml", "Multi-project orchestration configuration"),
        (".dependency-config.yaml", "Dependency tracking configuration"),
        ("context_config.yaml", "Context management configuration"),
        ("logging.yaml", "Logging configuration")
    ]
    
    if all:
        # Search for all config files
        import glob
        all_configs = glob.glob(str(config_dir / "*.yaml")) + glob.glob(str(config_dir / "*.yml")) + glob.glob(str(config_dir / "*.json"))
        config_files.extend([(Path(f).name, "Configuration file") for f in all_configs])
    
    for filename, description in config_files:
        file_path = config_dir.parent / filename if filename.startswith('.') else config_dir / filename
        exists = file_path.exists()
        status = "✓" if exists else "✗"
        color = "green" if exists else "dim"
        
        console.print(f"  [{color}]{status}[/{color}] {filename}")
        console.print(f"    {description}")
        if exists:
            console.print(f"    Path: {file_path}")
        console.print()


if __name__ == '__main__':
    config()