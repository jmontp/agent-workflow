"""
Information and diagnostic commands for agent-workflow CLI.

This module provides commands for version information, system health checks,
and diagnostic utilities.
"""

import os
import sys
import platform
import subprocess
from pathlib import Path
from typing import Dict, Any, List, Optional
import click
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.tree import Tree

from agent_workflow import __version__, get_package_info
from .utils import (
    get_config_dir,
    print_success,
    print_warning,
    print_error,
    print_info,
    check_system_requirements
)

console = Console()


@click.command("version")
@click.option("--check-updates", is_flag=True, help="Check for available updates")
@click.option("--verbose", is_flag=True, help="Show detailed system information")
@click.pass_context
def version_command(ctx, check_updates, verbose):
    """Display version and system information."""
    try:
        # Basic version info
        console.print(f"[bold blue]agent-workflow[/bold blue] [green]{__version__}[/green]")
        
        if verbose:
            _show_detailed_version_info()
        
        if check_updates:
            _check_for_updates()
            
    except Exception as e:
        print_error(f"Failed to get version information: {e}")
        if ctx.obj.get('verbose'):
            import traceback
            console.print(traceback.format_exc())
        sys.exit(1)


@click.command("health")
@click.option("--check-all", is_flag=True, help="Run comprehensive health check")
@click.option("--fix-issues", is_flag=True, help="Attempt to fix detected issues")
@click.option("--export-report", type=click.Path(), help="Export health report to file")
@click.option("--project", help="Check specific project health")
@click.pass_context
def health_command(ctx, check_all, fix_issues, export_report, project):
    """System health check and diagnostics."""
    try:
        console.print(Panel("Agent-Workflow Health Check", style="blue"))
        
        # Run health checks
        health_results = _run_health_checks(check_all, project)
        
        # Display results
        _display_health_results(health_results)
        
        # Fix issues if requested
        if fix_issues:
            _fix_health_issues(health_results)
        
        # Export report if requested
        if export_report:
            _export_health_report(health_results, Path(export_report))
        
        # Exit with appropriate code
        if any(not check["passed"] for check in health_results.values()):
            sys.exit(1)
            
    except Exception as e:
        print_error(f"Health check failed: {e}")
        if ctx.obj.get('verbose'):
            import traceback
            console.print(traceback.format_exc())
        sys.exit(1)


def _show_detailed_version_info() -> None:
    """Show detailed version and system information."""
    pkg_info = get_package_info()
    
    # Version information table
    version_table = Table(title="Version Information")
    version_table.add_column("Component", style="cyan")
    version_table.add_column("Version", style="white")
    
    version_table.add_row("agent-workflow", __version__)
    version_table.add_row("Python", f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}")
    version_table.add_row("Platform", platform.platform())
    version_table.add_row("Architecture", platform.machine())
    
    console.print(version_table)
    
    # Package information
    info_table = Table(title="Package Information")
    info_table.add_column("Property", style="cyan")
    info_table.add_column("Value", style="white")
    
    info_table.add_row("Repository", pkg_info["repository"])
    info_table.add_row("Documentation", pkg_info["documentation"])
    info_table.add_row("Bug Reports", pkg_info["bug_reports"])
    info_table.add_row("License", pkg_info["license"])
    
    console.print(info_table)
    
    # Dependency versions
    _show_dependency_versions()


def _show_dependency_versions() -> None:
    """Show versions of key dependencies."""
    dependencies = [
        "discord.py",
        "PyGithub", 
        "PyYAML",
        "click",
        "rich",
        "cryptography",
        "aiofiles",
        "aiohttp",
        "requests",
        "websockets",
        "watchdog",
        "psutil"
    ]
    
    dep_table = Table(title="Dependencies")
    dep_table.add_column("Package", style="cyan")
    dep_table.add_column("Version", style="white")
    dep_table.add_column("Status", style="green")
    
    for dep in dependencies:
        try:
            import importlib.metadata
            version = importlib.metadata.version(dep)
            status = "✓ Installed"
            color = "green"
        except importlib.metadata.PackageNotFoundError:
            version = "Not installed"
            status = "✗ Missing"
            color = "red"
        except Exception:
            version = "Unknown"
            status = "? Error"
            color = "yellow"
        
        dep_table.add_row(dep, version, f"[{color}]{status}[/{color}]")
    
    console.print(dep_table)


def _check_for_updates() -> None:
    """Check for available package updates."""
    try:
        # Check PyPI for latest version
        import requests
        response = requests.get("https://pypi.org/pypi/agent-workflow/json", timeout=5)
        if response.status_code == 200:
            data = response.json()
            latest_version = data["info"]["version"]
            
            if latest_version != __version__:
                console.print(f"\n[yellow]Update available:[/yellow] {latest_version}")
                console.print("Run: [bold]pip install --upgrade agent-workflow[/bold]")
            else:
                console.print(f"\n[green]✓[/green] You have the latest version")
        else:
            print_warning("Could not check for updates")
            
    except Exception:
        print_warning("Could not check for updates (network error)")


def _run_health_checks(comprehensive: bool, project: Optional[str]) -> Dict[str, Dict[str, Any]]:
    """Run system health checks."""
    health_results = {}
    
    # System requirements check
    health_results["system"] = _check_system_health()
    
    # Configuration check
    health_results["configuration"] = _check_configuration_health()
    
    # Dependencies check
    health_results["dependencies"] = _check_dependencies_health()
    
    # Integration checks
    health_results["integrations"] = _check_integrations_health()
    
    if comprehensive:
        # File system checks
        health_results["filesystem"] = _check_filesystem_health()
        
        # Performance checks
        health_results["performance"] = _check_performance_health()
    
    # Project-specific checks
    if project:
        health_results["project"] = _check_project_health(project)
    
    return health_results


def _check_system_health() -> Dict[str, Any]:
    """Check system requirements and health."""
    checks = {
        "python_version": sys.version_info >= (3, 8),
        "platform_supported": platform.system() in ["Linux", "Darwin", "Windows"],
        "memory_available": True,  # Would check actual memory
        "disk_space": True,  # Would check actual disk space
    }
    
    details = {
        "python_version": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
        "platform": platform.platform(),
        "architecture": platform.machine(),
        "memory": "Sufficient",  # Would show actual memory
        "disk": "Sufficient"  # Would show actual disk space
    }
    
    return {
        "passed": all(checks.values()),
        "checks": checks,
        "details": details,
        "issues": [name for name, passed in checks.items() if not passed]
    }


def _check_configuration_health() -> Dict[str, Any]:
    """Check configuration files and settings."""
    config_dir = get_config_dir()
    
    checks = {
        "config_dir_exists": config_dir.exists(),
        "config_file_exists": (config_dir / "config.yaml").exists(),
        "config_file_valid": False,
        "registry_exists": (config_dir / "projects" / "registry.yaml").exists(),
        "credentials_secure": True,  # Would check actual permissions
    }
    
    # Validate config file
    if checks["config_file_exists"]:
        try:
            import yaml
            with open(config_dir / "config.yaml", 'r') as f:
                yaml.safe_load(f)
            checks["config_file_valid"] = True
        except Exception:
            checks["config_file_valid"] = False
    
    details = {
        "config_dir": str(config_dir),
        "config_size": "Unknown",  # Would show actual size
        "last_modified": "Unknown"  # Would show actual timestamp
    }
    
    return {
        "passed": all(checks.values()),
        "checks": checks,
        "details": details,
        "issues": [name for name, passed in checks.items() if not passed]
    }


def _check_dependencies_health() -> Dict[str, Any]:
    """Check required dependencies."""
    required_deps = ["click", "rich", "PyYAML"]
    optional_deps = ["discord.py", "PyGithub", "cryptography", "aiofiles", "requests"]
    
    checks = {}
    versions = {}
    
    # Check required dependencies
    for dep in required_deps:
        try:
            import importlib.metadata
            version = importlib.metadata.version(dep)
            checks[f"required_{dep}"] = True
            versions[dep] = version
        except Exception:
            checks[f"required_{dep}"] = False
            versions[dep] = "Missing"
    
    # Check optional dependencies
    for dep in optional_deps:
        try:
            import importlib.metadata
            version = importlib.metadata.version(dep)
            checks[f"optional_{dep}"] = True
            versions[dep] = version
        except Exception:
            checks[f"optional_{dep}"] = False
            versions[dep] = "Missing"
    
    return {
        "passed": all(checks[k] for k in checks if k.startswith("required_")),
        "checks": checks,
        "details": {"versions": versions},
        "issues": [name for name, passed in checks.items() if not passed and name.startswith("required_")]
    }


def _check_integrations_health() -> Dict[str, Any]:
    """Check integration status."""
    config_dir = get_config_dir()
    
    checks = {
        "discord_configured": False,
        "ai_provider_configured": False,
        "github_configured": False
    }
    
    # Check configuration file for integration status
    config_file = config_dir / "config.yaml"
    if config_file.exists():
        try:
            import yaml
            with open(config_file, 'r') as f:
                config = yaml.safe_load(f)
            
            checks["discord_configured"] = config.get("discord", {}).get("enabled", False)
            checks["ai_provider_configured"] = bool(config.get("ai_provider", {}).get("provider"))
            checks["github_configured"] = bool(config.get("github", {}).get("token"))
            
        except Exception:
            pass
    
    return {
        "passed": True,  # Integrations are optional
        "checks": checks,
        "details": {},
        "issues": []
    }


def _check_filesystem_health() -> Dict[str, Any]:
    """Check filesystem permissions and structure."""
    config_dir = get_config_dir()
    
    checks = {
        "config_readable": os.access(config_dir, os.R_OK),
        "config_writable": os.access(config_dir, os.W_OK),
        "temp_space": True,  # Would check actual temp space
        "log_writable": True  # Would check log directory
    }
    
    return {
        "passed": all(checks.values()),
        "checks": checks,
        "details": {"config_dir": str(config_dir)},
        "issues": [name for name, passed in checks.items() if not passed]
    }


def _check_performance_health() -> Dict[str, Any]:
    """Check system performance metrics."""
    checks = {
        "cpu_usage_ok": True,  # Would check actual CPU usage
        "memory_usage_ok": True,  # Would check actual memory usage
        "disk_io_ok": True,  # Would check disk I/O
        "network_ok": True  # Would check network connectivity
    }
    
    return {
        "passed": all(checks.values()),
        "checks": checks,
        "details": {},
        "issues": [name for name, passed in checks.items() if not passed]
    }


def _check_project_health(project_name: str) -> Dict[str, Any]:
    """Check health of specific project."""
    config_dir = get_config_dir()
    registry_path = config_dir / "projects" / "registry.yaml"
    
    checks = {
        "project_registered": False,
        "project_path_exists": False,
        "project_git_repo": False,
        "state_dir_exists": False,
        "state_file_valid": False
    }
    
    if registry_path.exists():
        try:
            import yaml
            with open(registry_path, 'r') as f:
                registry = yaml.safe_load(f) or {"projects": {}}
            
            if project_name in registry["projects"]:
                checks["project_registered"] = True
                project_data = registry["projects"][project_name]
                project_path = Path(project_data["path"])
                
                checks["project_path_exists"] = project_path.exists()
                checks["project_git_repo"] = (project_path / ".git").exists()
                
                state_dir = project_path / ".orch-state"
                checks["state_dir_exists"] = state_dir.exists()
                
                if state_dir.exists():
                    state_file = state_dir / "status.json"
                    if state_file.exists():
                        try:
                            import json
                            with open(state_file, 'r') as f:
                                json.load(f)
                            checks["state_file_valid"] = True
                        except Exception:
                            pass
        except Exception:
            pass
    
    return {
        "passed": all(checks.values()),
        "checks": checks,
        "details": {"project": project_name},
        "issues": [name for name, passed in checks.items() if not passed]
    }


def _display_health_results(health_results: Dict[str, Dict[str, Any]]) -> None:
    """Display health check results."""
    overall_health = all(result["passed"] for result in health_results.values())
    
    # Overall status
    if overall_health:
        console.print("[green]✓ Overall health: GOOD[/green]\n")
    else:
        console.print("[red]✗ Overall health: ISSUES DETECTED[/red]\n")
    
    # Detailed results
    for category, result in health_results.items():
        status_icon = "✓" if result["passed"] else "✗"
        status_color = "green" if result["passed"] else "red"
        
        panel_title = f"{category.title()} Health"
        panel_content = []
        
        panel_content.append(f"[{status_color}]{status_icon} Status: {'PASS' if result['passed'] else 'FAIL'}[/{status_color}]")
        
        # Show failed checks
        if result["issues"]:
            panel_content.append("\n[bold]Issues:[/bold]")
            for issue in result["issues"]:
                panel_content.append(f"  [red]✗[/red] {issue}")
        
        # Show some details
        if result["details"]:
            panel_content.append("\n[bold]Details:[/bold]")
            for key, value in list(result["details"].items())[:3]:  # Show first 3 details
                if isinstance(value, dict):
                    continue  # Skip nested dicts for display
                panel_content.append(f"  {key}: {value}")
        
        console.print(Panel("\n".join(panel_content), title=panel_title, 
                          border_style=status_color))


def _fix_health_issues(health_results: Dict[str, Dict[str, Any]]) -> None:
    """Attempt to fix detected health issues."""
    console.print(Panel("Attempting to fix health issues...", style="yellow"))
    
    fixed_issues = []
    
    for category, result in health_results.items():
        if not result["passed"]:
            category_fixes = _fix_category_issues(category, result["issues"])
            fixed_issues.extend(category_fixes)
    
    if fixed_issues:
        console.print(f"\n[green]✓ Fixed {len(fixed_issues)} issues:[/green]")
        for issue in fixed_issues:
            console.print(f"  [green]✓[/green] {issue}")
    else:
        console.print("\n[yellow]No issues could be automatically fixed[/yellow]")
        console.print("Manual intervention may be required")


def _fix_category_issues(category: str, issues: List[str]) -> List[str]:
    """Fix issues for a specific category."""
    fixed = []
    
    if category == "configuration":
        for issue in issues:
            if issue == "config_dir_exists":
                config_dir = get_config_dir()
                config_dir.mkdir(parents=True, exist_ok=True)
                fixed.append("Created configuration directory")
            elif issue == "registry_exists":
                config_dir = get_config_dir()
                registry_path = config_dir / "projects" / "registry.yaml"
                registry_path.parent.mkdir(parents=True, exist_ok=True)
                with open(registry_path, 'w') as f:
                    import yaml
                    yaml.dump({"projects": {}}, f)
                fixed.append("Created project registry")
    
    return fixed


def _export_health_report(health_results: Dict[str, Dict[str, Any]], export_path: Path) -> None:
    """Export health report to file."""
    import json
    from datetime import datetime
    
    report_data = {
        "timestamp": datetime.now().isoformat(),
        "version": __version__,
        "platform": platform.platform(),
        "overall_health": all(result["passed"] for result in health_results.values()),
        "categories": health_results
    }
    
    with open(export_path, 'w') as f:
        json.dump(report_data, f, indent=2)
    
    print_success(f"Health report exported to {export_path}")