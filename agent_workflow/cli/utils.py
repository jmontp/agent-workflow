"""
Utility functions for CLI operations.

This module provides common utilities used across all CLI commands including
system checks, logging setup, error handling, and user interface helpers.
"""

import os
import sys
import logging
import platform
from pathlib import Path
from typing import Optional, Dict, Any
import click
from rich.console import Console
from rich.panel import Panel
from rich.text import Text

console = Console()


def _is_safe_path(path: Path) -> bool:
    """
    Validate that a path is safe and doesn't contain traversal attacks.
    
    Args:
        path: Path to validate
        
    Returns:
        bool: True if path is safe
    """
    try:
        # Resolve to absolute path
        resolved_path = path.resolve()
        
        # Check for suspicious patterns
        path_str = str(resolved_path)
        dangerous_patterns = ['..', '~/', '/etc/', '/usr/', '/var/', '/bin/', '/sbin/']
        
        # Allow paths under user home directory or system-appropriate config locations
        home_dir = Path.home().resolve()
        
        # On Windows, also allow AppData
        if platform.system() == "Windows":
            appdata_local = home_dir / "AppData" / "Local"
            appdata_roaming = home_dir / "AppData" / "Roaming"
            allowed_bases = [home_dir, appdata_local, appdata_roaming]
        else:
            # On Unix-like systems, allow ~/.config and ~/.local
            config_dir = home_dir / ".config"
            local_dir = home_dir / ".local"
            allowed_bases = [home_dir, config_dir, local_dir]
        
        # Check if path is under an allowed base directory
        for base in allowed_bases:
            try:
                resolved_path.relative_to(base)
                return True
            except ValueError:
                continue
        
        # If we get here, path is not under any allowed directory
        return False
        
    except (OSError, ValueError):
        return False


def check_system_requirements() -> bool:
    """
    Check if system meets minimum requirements for agent-workflow.
    
    Returns:
        bool: True if requirements are met, False otherwise
    """
    # Check Python version
    if sys.version_info < (3, 8):
        console.print(
            Panel(
                f"[red]Python 3.8+ required. Found: {sys.version}[/red]",
                title="System Requirements",
                border_style="red"
            )
        )
        return False
    
    # Check available memory (basic check)
    try:
        import psutil
        memory = psutil.virtual_memory()
        if memory.total < 1 * 1024 * 1024 * 1024:  # 1GB minimum
            console.print(
                Panel(
                    f"[yellow]Warning: Low memory detected ({memory.total // (1024**3)}GB). "
                    f"Recommended: 4GB+[/yellow]",
                    title="System Warning",
                    border_style="yellow"
                )
            )
    except ImportError:
        pass
    
    return True


def setup_logging(verbose: bool = False, log_file: Optional[str] = None) -> None:
    """
    Setup logging configuration for CLI operations.
    
    Args:
        verbose: Enable verbose logging
        log_file: Optional log file path
    """
    level = logging.DEBUG if verbose else logging.INFO
    
    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Setup console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)
    
    # Setup file handler if specified
    handlers = [console_handler]
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(formatter)
        handlers.append(file_handler)
    
    # Configure root logger
    logging.basicConfig(
        level=level,
        handlers=handlers,
        force=True
    )


def get_config_dir() -> Path:
    """
    Get the configuration directory path.
    
    Returns:
        Path: Configuration directory path
    """
    # Check environment variable first
    if config_dir := os.getenv("AGENT_WORKFLOW_CONFIG_DIR"):
        path = Path(config_dir).expanduser().resolve()
        # SECURITY: Validate path is safe and not attempting directory traversal
        if not _is_safe_path(path):
            raise ValueError(f"Unsafe configuration directory path: {config_dir}")
        return path
    
    # Use platform-appropriate default
    if platform.system() == "Windows":
        base_dir = Path.home() / "AppData" / "Local"
    else:
        base_dir = Path.home()
    
    return (base_dir / ".agent-workflow").resolve()


def ensure_config_dir(config_dir: Optional[Path] = None) -> Path:
    """
    Ensure configuration directory exists.
    
    Args:
        config_dir: Optional custom config directory
        
    Returns:
        Path: Created configuration directory
    """
    if config_dir is None:
        config_dir = get_config_dir()
    
    config_dir.mkdir(parents=True, exist_ok=True)
    return config_dir


def print_banner() -> None:
    """Print welcome banner for the CLI."""
    banner_text = Text()
    banner_text.append("Agent-Workflow", style="bold blue")
    banner_text.append(" v1.0.0\n", style="dim")
    banner_text.append("AI Agent TDD-Scrum Orchestration Framework", style="italic")
    
    console.print(
        Panel(
            banner_text,
            title="Welcome",
            border_style="blue",
            padding=(1, 2)
        )
    )


def handle_cli_error(message: str, exit_code: int = 1) -> None:
    """
    Handle CLI errors with consistent formatting.
    
    Args:
        message: Error message to display
        exit_code: Exit code to use
    """
    console.print(
        Panel(
            f"[red]{message}[/red]",
            title="Error",
            border_style="red"
        )
    )
    
    # Suggest help
    console.print(
        "\n[dim]Run 'agent-orch --help' for usage information.[/dim]"
    )
    
    sys.exit(exit_code)


def confirm_action(message: str, default: bool = False) -> bool:
    """
    Prompt user for confirmation.
    
    Args:
        message: Confirmation message
        default: Default response if user just presses Enter
        
    Returns:
        bool: User's confirmation response
    """
    default_text = "Y/n" if default else "y/N"
    response = click.prompt(
        f"{message} [{default_text}]",
        type=str,
        default="",
        show_default=False
    ).lower()
    
    if not response:
        return default
    
    return response.startswith('y')


def format_table_data(headers: list, rows: list) -> str:
    """
    Format data as a table using rich.
    
    Args:
        headers: List of column headers
        rows: List of row data
        
    Returns:
        str: Formatted table string
    """
    from rich.table import Table
    
    table = Table()
    
    # Add columns
    for header in headers:
        table.add_column(header, style="cyan")
    
    # Add rows
    for row in rows:
        table.add_row(*[str(cell) for cell in row])
    
    # Capture table output
    with console.capture() as capture:
        console.print(table)
    
    return capture.get()


def format_status_info(status_data: Dict[str, Any]) -> str:
    """
    Format status information with rich formatting.
    
    Args:
        status_data: Dictionary containing status information
        
    Returns:
        str: Formatted status string
    """
    from rich.tree import Tree
    
    tree = Tree("System Status")
    
    for key, value in status_data.items():
        if isinstance(value, dict):
            branch = tree.add(f"[bold]{key}[/bold]")
            for sub_key, sub_value in value.items():
                status_icon = "✓" if sub_value else "✗"
                color = "green" if sub_value else "red"
                branch.add(f"[{color}]{status_icon} {sub_key}[/{color}]")
        else:
            status_icon = "✓" if value else "✗"
            color = "green" if value else "red"
            tree.add(f"[{color}]{status_icon} {key}[/{color}]")
    
    with console.capture() as capture:
        console.print(tree)
    
    return capture.get()


def validate_config() -> Dict[str, Any]:
    """
    Validate system configuration including environment variables and config files.
    
    Returns:
        Dict containing validation results
    """
    try:
        from ..config import validate_environment_variables
        return validate_environment_variables("all")
    except ImportError:
        # Fallback validation if config module not available
        return {
            "overall_valid": True,
            "files": {},
            "env_vars": {},
            "summary": {"total_files": 0, "valid_files": 0, "total_env_vars": 0, "valid_env_vars": 0}
        }


def load_config_with_validation(config_path: str, schema: str = "orchestration") -> Dict[str, Any]:
    """
    Load and validate configuration file.
    
    Args:
        config_path: Path to configuration file
        schema: Schema name to validate against
        
    Returns:
        Dict with config data and validation results
    """
    try:
        from ..config import validator
        return validator.validate_config_file(config_path, schema)
    except ImportError:
        # Fallback - load without validation
        try:
            import yaml
            with open(config_path, 'r') as f:
                return {
                    "valid": True,
                    "errors": [],
                    "warnings": [],
                    "config": yaml.safe_load(f) or {}
                }
        except Exception as e:
            return {
                "valid": False,
                "errors": [str(e)],
                "warnings": [],
                "config": {}
            }


def validate_project_path(path: str) -> Path:
    """
    Validate and normalize project path.
    
    Args:
        path: Project path string
        
    Returns:
        Path: Validated project path
        
    Raises:
        click.BadParameter: If path is invalid
    """
    project_path = Path(path).resolve()
    
    if not project_path.exists():
        raise click.BadParameter(f"Path does not exist: {path}")
    
    if not project_path.is_dir():
        raise click.BadParameter(f"Path is not a directory: {path}")
    
    return project_path


def get_project_info(project_path: Path) -> Dict[str, Any]:
    """
    Analyze project directory and extract information.
    
    Args:
        project_path: Path to project directory
        
    Returns:
        Dict containing project information
    """
    info = {
        "name": project_path.name,
        "path": str(project_path),
        "is_git_repo": (project_path / ".git").exists(),
        "has_requirements": (project_path / "requirements.txt").exists(),
        "has_package_json": (project_path / "package.json").exists(),
        "has_tests": any([
            (project_path / "tests").exists(),
            (project_path / "test").exists(),
            any(project_path.glob("**/test_*.py")),
            any(project_path.glob("**/*_test.py"))
        ]),
        "has_readme": any([
            (project_path / "README.md").exists(),
            (project_path / "README.rst").exists(),
            (project_path / "README.txt").exists()
        ]),
        "framework": "general"
    }
    
    # Detect framework
    if (project_path / "package.json").exists():
        info["framework"] = "web"
    elif info["has_requirements"]:
        try:
            with open(project_path / "requirements.txt", "r") as f:
                content = f.read().lower()
                if any(fw in content for fw in ["flask", "django", "fastapi"]):
                    info["framework"] = "web" if "flask" in content or "django" in content else "api"
                elif any(fw in content for fw in ["tensorflow", "pytorch", "sklearn"]):
                    info["framework"] = "ml"
        except Exception:
            pass
    
    return info


def print_success(message: str) -> None:
    """Print success message with formatting."""
    console.print(f"[green]✓[/green] {message}")


def print_warning(message: str) -> None:
    """Print warning message with formatting."""
    console.print(f"[yellow]⚠[/yellow] {message}")


def print_error(message: str) -> None:
    """Print error message with formatting."""
    console.print(f"[red]✗[/red] {message}")


def print_info(message: str) -> None:
    """Print info message with formatting."""
    console.print(f"[blue]ℹ[/blue] {message}")


def show_progress(description: str):
    """
    Context manager for showing progress.
    
    Args:
        description: Description of the operation
    """
    from rich.progress import Progress, SpinnerColumn, TextColumn
    
    return Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
        transient=True
    )