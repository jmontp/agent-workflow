"""
Orchestrator control commands for agent-workflow CLI.

This module provides commands for starting, stopping, and monitoring
the orchestrator process and project coordination.
"""

import os
import sys
import yaml
import json
import signal
import subprocess
import asyncio
from pathlib import Path
from typing import Optional, Dict, Any, List
from datetime import datetime
import click
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.live import Live
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

# Process tracking
ORCHESTRATOR_PID_FILE = ".orchestrator.pid"


@click.command("start")
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
def start_command(ctx, project, mode, discord, daemon, log_level, config, port, no_browser):
    """Start orchestration for projects."""
    try:
        config_dir = get_config_dir()
        config_file = config or config_dir / "config.yaml"
        
        if not Path(config_file).exists():
            print_error("Agent-workflow not initialized. Run 'agent-orch init' first.")
            return
        
        # Check if already running
        if _is_orchestrator_running(config_dir):
            print_warning("Orchestrator is already running!")
            pid = _get_orchestrator_pid(config_dir)
            print_info(f"Current PID: {pid}")
            print_info("Use 'agent-orch stop' to stop or 'agent-orch status' for details")
            return
        
        # Load configuration
        with open(config_file, 'r') as f:
            global_config = yaml.safe_load(f)
        
        # Validate configuration
        if discord and not global_config.get("discord", {}).get("enabled"):
            print_error("Discord integration not configured. Run 'agent-orch setup-discord' first.")
            return
        
        # Load projects
        projects = _load_projects(config_dir, project)
        if not projects:
            print_warning("No projects registered. Use 'agent-orch register-project' to register projects.")
            return
        
        # Start orchestrator
        console.print(Panel("Starting Agent-Workflow Orchestrator", style="green"))
        
        if daemon:
            _start_daemon(config_file, projects, mode, discord, log_level, port)
        else:
            _start_interactive(config_file, projects, mode, discord, log_level, port, no_browser)
            
    except KeyboardInterrupt:
        print_info("Startup cancelled by user")
    except Exception as e:
        print_error(f"Failed to start orchestrator: {e}")
        if ctx.obj.get('verbose'):
            import traceback
            console.print(traceback.format_exc())
        sys.exit(1)


@click.command("stop")
@click.option("--force", is_flag=True, help="Force stop without graceful shutdown")
@click.option("--save-state", is_flag=True, help="Save current state before stopping")
@click.option("--project", help="Stop specific project only")
@click.pass_context
def stop_command(ctx, force, save_state, project):
    """Stop orchestrator and cleanup."""
    try:
        config_dir = get_config_dir()
        
        if not _is_orchestrator_running(config_dir):
            print_info("Orchestrator is not running")
            return
        
        pid = _get_orchestrator_pid(config_dir)
        
        if project:
            print_info(f"Stopping project: {project}")
            # Would stop specific project
        else:
            console.print(Panel("Stopping Agent-Workflow Orchestrator", style="yellow"))
            
            if save_state:
                print_info("Saving current state...")
                _save_orchestrator_state(config_dir)
            
            # Stop orchestrator process
            if force:
                _force_stop_orchestrator(pid)
            else:
                _graceful_stop_orchestrator(pid)
            
            # Cleanup
            _cleanup_orchestrator_files(config_dir)
            
            print_success("Orchestrator stopped successfully")
            
    except Exception as e:
        print_error(f"Failed to stop orchestrator: {e}")
        if ctx.obj.get('verbose'):
            import traceback
            console.print(traceback.format_exc())
        sys.exit(1)


@click.command("status")
@click.option("--project", help="Show status for specific project")
@click.option("--verbose", is_flag=True, help="Show detailed status information")
@click.option("--json", "output_json", is_flag=True, help="Output in JSON format")
@click.option("--watch", is_flag=True, help="Continuously update status display")
@click.option("--health", is_flag=True, help="Include health check information")
@click.option("--brief", is_flag=True, help="Brief status summary")
@click.pass_context
def status_command(ctx, project, verbose, output_json, watch, health, brief):
    """Display orchestrator and project status."""
    try:
        config_dir = get_config_dir()
        
        if watch:
            _watch_status(config_dir, project, verbose, health)
        else:
            status_data = _get_status_data(config_dir, project, verbose, health)
            
            if output_json:
                console.print(json.dumps(status_data, indent=2))
            elif brief:
                _show_brief_status(status_data)
            else:
                _show_detailed_status(status_data, verbose)
                
    except Exception as e:
        print_error(f"Failed to get status: {e}")
        if ctx.obj.get('verbose'):
            import traceback
            console.print(traceback.format_exc())
        sys.exit(1)


def _is_orchestrator_running(config_dir: Path) -> bool:
    """Check if orchestrator is currently running."""
    pid_file = config_dir / ORCHESTRATOR_PID_FILE
    if not pid_file.exists():
        return False
    
    try:
        with open(pid_file, 'r') as f:
            pid = int(f.read().strip())
        
        # Check if process is still running
        os.kill(pid, 0)
        return True
    except (ValueError, OSError):
        # PID file exists but process is dead
        pid_file.unlink(missing_ok=True)
        return False


def _get_orchestrator_pid(config_dir: Path) -> Optional[int]:
    """Get orchestrator PID if running."""
    pid_file = config_dir / ORCHESTRATOR_PID_FILE
    if pid_file.exists():
        try:
            with open(pid_file, 'r') as f:
                return int(f.read().strip())
        except (ValueError, OSError):
            pass
    return None


def _load_projects(config_dir: Path, specific_project: Optional[str]) -> List[Dict[str, Any]]:
    """Load projects from registry."""
    registry_path = config_dir / "projects" / "registry.yaml"
    if not registry_path.exists():
        return []
    
    with open(registry_path, 'r') as f:
        registry = yaml.safe_load(f) or {"projects": {}}
    
    projects = []
    for project_name, project_data in registry["projects"].items():
        if specific_project is None or project_name == specific_project:
            projects.append(project_data)
    
    return projects


def _start_daemon(config_file: Path, projects: List[Dict], mode: Optional[str], 
                 discord: bool, log_level: str, port: int) -> None:
    """Start orchestrator as daemon process."""
    print_info("Starting orchestrator as daemon...")
    
    # Create daemon command
    cmd = [
        sys.executable, "-m", "agent_workflow.orchestrator",
        "--config", str(config_file),
        "--log-level", log_level,
        "--port", str(port)
    ]
    
    if discord:
        cmd.append("--discord")
    
    if mode:
        cmd.extend(["--mode", mode])
    
    # Start process
    process = subprocess.Popen(
        cmd,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        start_new_session=True
    )
    
    # Save PID
    config_dir = get_config_dir()
    pid_file = config_dir / ORCHESTRATOR_PID_FILE
    with open(pid_file, 'w') as f:
        f.write(str(process.pid))
    
    print_success(f"Orchestrator started as daemon (PID: {process.pid})")
    print_info(f"Status: agent-orch status")
    print_info(f"Stop: agent-orch stop")


def _start_interactive(config_file: Path, projects: List[Dict], mode: Optional[str],
                      discord: bool, log_level: str, port: int, no_browser: bool) -> None:
    """Start orchestrator in interactive mode."""
    print_info("Starting orchestrator in interactive mode...")
    
    # Show startup information
    table = Table(title="Startup Configuration")
    table.add_column("Setting", style="cyan")
    table.add_column("Value", style="white")
    
    table.add_row("Config", str(config_file))
    table.add_row("Projects", str(len(projects)))
    table.add_row("Mode", mode or "default")
    table.add_row("Discord", "enabled" if discord else "disabled")
    table.add_row("Log Level", log_level)
    table.add_row("Port", str(port))
    
    console.print(table)
    
    # Save PID for interactive mode too
    config_dir = get_config_dir()
    pid_file = config_dir / ORCHESTRATOR_PID_FILE
    with open(pid_file, 'w') as f:
        f.write(str(os.getpid()))
    
    try:
        print_success("Orchestrator started successfully!")
        print_info("Press Ctrl+C to stop")
        
        if not no_browser:
            print_info(f"Status page: http://localhost:{port}")
        
        # Main orchestrator loop - run asynchronously
        asyncio.run(_run_orchestrator_loop(projects, discord, log_level))
        
    finally:
        # Cleanup on exit
        _cleanup_orchestrator_files(config_dir)


async def _run_orchestrator_loop(projects: List[Dict], discord: bool, log_level: str) -> None:
    """Main orchestrator execution loop."""
    # Import the orchestrator
    try:
        from agent_workflow.core.orchestrator import Orchestrator
        
        # Create orchestrator instance
        orchestrator = Orchestrator(mode="multi" if len(projects) > 1 else "single")
        
        # Run orchestrator with state broadcaster
        await orchestrator.run(projects, start_broadcaster=True, broadcaster_port=8080)
        
    except ImportError:
        # Fallback to simplified version if orchestrator not available
        print_info("Using simplified orchestrator loop...")
        try:
            while True:
                # Monitor projects
                for project in projects:
                    _check_project_status(project)
                
                # Process Discord commands if enabled
                if discord:
                    _process_discord_commands()
                
                # Wait before next cycle
                await asyncio.sleep(5)
                
        except KeyboardInterrupt:
            print_info("\nGracefully shutting down...")
    except KeyboardInterrupt:
        print_info("\nGracefully shutting down...")


def _check_project_status(project: Dict[str, Any]) -> None:
    """Check status of a single project."""
    # Simplified project monitoring
    project_path = Path(project["path"])
    if not project_path.exists():
        print_warning(f"Project path not found: {project_path}")


def _process_discord_commands() -> None:
    """Process Discord bot commands."""
    # Simplified Discord processing
    pass


def _graceful_stop_orchestrator(pid: int) -> None:
    """Gracefully stop orchestrator process."""
    try:
        os.kill(pid, signal.SIGTERM)
        print_info("Sent graceful shutdown signal...")
        
        # Wait for graceful shutdown
        import time
        for _ in range(10):  # Wait up to 10 seconds
            try:
                os.kill(pid, 0)
                time.sleep(1)
            except OSError:
                break
        else:
            # Force kill if still running
            print_warning("Graceful shutdown timeout, forcing stop...")
            os.kill(pid, signal.SIGKILL)
            
    except OSError:
        print_info("Process already stopped")


def _force_stop_orchestrator(pid: int) -> None:
    """Force stop orchestrator process."""
    try:
        os.kill(pid, signal.SIGKILL)
        print_info("Forced orchestrator stop")
    except OSError:
        print_info("Process already stopped")


def _save_orchestrator_state(config_dir: Path) -> None:
    """Save current orchestrator state."""
    state_file = config_dir / "orchestrator_state.json"
    state_data = {
        "timestamp": datetime.now().isoformat(),
        "status": "stopping",
        "projects": []
    }
    
    with open(state_file, 'w') as f:
        json.dump(state_data, f, indent=2)


def _cleanup_orchestrator_files(config_dir: Path) -> None:
    """Cleanup orchestrator temporary files."""
    pid_file = config_dir / ORCHESTRATOR_PID_FILE
    pid_file.unlink(missing_ok=True)


def _get_status_data(config_dir: Path, project: Optional[str], 
                    verbose: bool, health: bool) -> Dict[str, Any]:
    """Get comprehensive status data."""
    status_data = {
        "orchestrator": {
            "running": _is_orchestrator_running(config_dir),
            "pid": _get_orchestrator_pid(config_dir),
            "uptime": None,
            "version": "1.0.0"
        },
        "projects": {},
        "system": {
            "config_dir": str(config_dir),
            "timestamp": datetime.now().isoformat()
        }
    }
    
    # Add project status
    projects = _load_projects(config_dir, project)
    for proj in projects:
        project_status = _get_project_status(proj)
        status_data["projects"][proj["name"]] = project_status
    
    # Add health information if requested
    if health:
        status_data["health"] = _get_health_data()
    
    return status_data


def _get_project_status(project: Dict[str, Any]) -> Dict[str, Any]:
    """Get status for a single project."""
    project_path = Path(project["path"])
    state_file = project_path / ".orch-state" / "status.json"
    
    project_status = {
        "name": project["name"],
        "path": project["path"],
        "exists": project_path.exists(),
        "mode": project["mode"],
        "framework": project["framework"],
        "state": "UNKNOWN",
        "last_active": project.get("last_active"),
        "active_tasks": [],
        "pending_approvals": []
    }
    
    # Load project state if available
    if state_file.exists():
        try:
            with open(state_file, 'r') as f:
                state_data = json.load(f)
            project_status.update({
                "state": state_data.get("current_state", "UNKNOWN"),
                "active_tasks": state_data.get("active_tasks", []),
                "pending_approvals": state_data.get("pending_approvals", [])
            })
        except Exception:
            pass
    
    return project_status


def _get_health_data() -> Dict[str, Any]:
    """Get system health data."""
    return {
        "cpu_usage": 0.0,  # Would get actual CPU usage
        "memory_usage": 0.0,  # Would get actual memory usage
        "disk_space": 0.0,  # Would get actual disk usage
        "dependencies": {
            "discord.py": True,  # Would check actual dependencies
            "PyGithub": True,
            "PyYAML": True
        }
    }


def _show_brief_status(status_data: Dict[str, Any]) -> None:
    """Show brief status summary."""
    orchestrator = status_data["orchestrator"]
    projects = status_data["projects"]
    
    # Orchestrator status
    status_icon = "🟢" if orchestrator["running"] else "🔴"
    status_text = "Running" if orchestrator["running"] else "Stopped"
    console.print(f"{status_icon} Orchestrator: {status_text}")
    
    if orchestrator["running"] and orchestrator["pid"]:
        console.print(f"   PID: {orchestrator['pid']}")
    
    # Projects summary
    if projects:
        active_projects = len([p for p in projects.values() if p["state"] != "IDLE"])
        console.print(f"📁 Projects: {len(projects)} registered, {active_projects} active")
    else:
        console.print("📁 Projects: None registered")


def _show_detailed_status(status_data: Dict[str, Any], verbose: bool) -> None:
    """Show detailed status information."""
    # Orchestrator status panel
    orchestrator = status_data["orchestrator"]
    orch_info = []
    
    if orchestrator["running"]:
        orch_info.append("[green]Status: Running ✓[/green]")
        orch_info.append(f"PID: {orchestrator['pid']}")
    else:
        orch_info.append("[red]Status: Stopped ✗[/red]")
    
    orch_info.append(f"Version: {orchestrator['version']}")
    orch_info.append(f"Config: {status_data['system']['config_dir']}")
    
    console.print(Panel("\n".join(orch_info), title="Orchestrator Status", border_style="blue"))
    
    # Projects status
    projects = status_data["projects"]
    if projects:
        table = Table(title="Projects Status")
        table.add_column("Name", style="cyan")
        table.add_column("State", style="green")
        table.add_column("Mode", style="yellow") 
        table.add_column("Framework", style="blue")
        table.add_column("Active Tasks", style="magenta")
        
        for project in projects.values():
            table.add_row(
                project["name"],
                project["state"],
                project["mode"],
                project["framework"],
                str(len(project["active_tasks"]))
            )
        
        console.print(table)
    else:
        console.print(Panel("No projects registered", title="Projects", border_style="yellow"))
    
    # Health information if available
    if "health" in status_data:
        health_info = []
        health = status_data["health"]
        
        for dep, status in health["dependencies"].items():
            status_icon = "✓" if status else "✗"
            color = "green" if status else "red"
            health_info.append(f"[{color}]{dep}: {status_icon}[/{color}]")
        
        console.print(Panel("\n".join(health_info), title="System Health", border_style="green"))


def _watch_status(config_dir: Path, project: Optional[str], verbose: bool, health: bool) -> None:
    """Continuously watch and update status display."""
    def generate_status():
        while True:
            status_data = _get_status_data(config_dir, project, verbose, health)
            yield status_data
    
    console.print("Watching status... Press Ctrl+C to exit")
    
    try:
        with Live(auto_refresh=False) as live:
            for status_data in generate_status():
                # Create status display
                from rich.console import Group
                
                # Brief status
                orchestrator = status_data["orchestrator"]
                status_icon = "🟢" if orchestrator["running"] else "🔴"
                status_text = "Running" if orchestrator["running"] else "Stopped"
                
                status_display = Group(
                    f"{status_icon} Orchestrator: {status_text}",
                    f"Timestamp: {status_data['system']['timestamp'][:19]}"
                )
                
                live.update(status_display, refresh=True)
                
                import time
                time.sleep(2)  # Update every 2 seconds
                
    except KeyboardInterrupt:
        console.print("\nStopped watching status")