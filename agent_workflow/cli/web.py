"""
Web interface commands for agent-workflow CLI.

This module provides commands for starting and managing the web-based
visualization and monitoring interface.
"""

import os
import sys
import subprocess
import signal
from pathlib import Path
from typing import Optional
import click
from rich.console import Console
from rich.panel import Panel
from rich.live import Live
from rich.progress import Progress, SpinnerColumn, TextColumn

from .utils import (
    get_config_dir,
    print_success,
    print_warning,
    print_error,
    print_info,
    confirm_action
)

console = Console()

# Process tracking
WEB_PID_FILE = ".web-interface.pid"


@click.command("web")
@click.option("--port", type=int, default=5000, help="Web interface port")
@click.option("--host", default="localhost", help="Host to bind to")
@click.option("--daemon", is_flag=True, help="Run as background daemon")
@click.option("--debug", is_flag=True, help="Enable debug mode")
@click.option("--no-browser", is_flag=True, help="Don't open browser automatically")
@click.option("--log-level", type=click.Choice(["DEBUG", "INFO", "WARN", "ERROR"]),
              default="INFO", help="Set logging level")
@click.pass_context
def web_command(ctx, port, host, daemon, debug, no_browser, log_level):
    """Start the web visualization interface."""
    try:
        config_dir = get_config_dir()
        
        # Check if already running
        if _is_web_running(config_dir):
            print_warning("Web interface is already running!")
            pid = _get_web_pid(config_dir)
            print_info(f"Current PID: {pid}")
            print_info("Use 'aw web-stop' to stop")
            return
        
        # Start web interface
        console.print(Panel("Starting Agent-Workflow Web Interface", style="green"))
        
        if daemon:
            _start_web_daemon(port, host, debug, log_level, config_dir)
        else:
            _start_web_interactive(port, host, debug, no_browser, log_level, config_dir)
            
    except KeyboardInterrupt:
        print_info("Startup cancelled by user")
    except Exception as e:
        print_error(f"Failed to start web interface: {e}")
        if ctx.obj.get('verbose'):
            import traceback
            console.print(traceback.format_exc())
        sys.exit(1)


@click.command("web-stop")
@click.option("--force", is_flag=True, help="Force stop without graceful shutdown")
@click.pass_context
def web_stop_command(ctx, force):
    """Stop the web interface."""
    try:
        config_dir = get_config_dir()
        
        if not _is_web_running(config_dir):
            print_info("Web interface is not running")
            return
        
        pid = _get_web_pid(config_dir)
        
        console.print(Panel("Stopping Agent-Workflow Web Interface", style="yellow"))
        
        # Stop web interface process
        if force:
            _force_stop_web(pid)
        else:
            _graceful_stop_web(pid)
        
        # Cleanup
        _cleanup_web_files(config_dir)
        
        print_success("Web interface stopped successfully")
        
    except Exception as e:
        print_error(f"Failed to stop web interface: {e}")
        if ctx.obj.get('verbose'):
            import traceback
            console.print(traceback.format_exc())
        sys.exit(1)


@click.command("web-status")
@click.option("--verbose", is_flag=True, help="Show detailed status information")
@click.option("--json", "output_json", is_flag=True, help="Output in JSON format")
@click.pass_context
def web_status_command(ctx, verbose, output_json):
    """Display web interface status."""
    try:
        config_dir = get_config_dir()
        status_data = _get_web_status_data(config_dir, verbose)
        
        if output_json:
            import json
            console.print(json.dumps(status_data, indent=2))
        else:
            _show_web_status(status_data, verbose)
            
    except Exception as e:
        print_error(f"Failed to get web status: {e}")
        if ctx.obj.get('verbose'):
            import traceback
            console.print(traceback.format_exc())
        sys.exit(1)


def _is_web_running(config_dir: Path) -> bool:
    """Check if web interface is currently running."""
    pid_file = config_dir / WEB_PID_FILE
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


def _get_web_pid(config_dir: Path) -> Optional[int]:
    """Get web interface PID if running."""
    pid_file = config_dir / WEB_PID_FILE
    if pid_file.exists():
        try:
            with open(pid_file, 'r') as f:
                return int(f.read().strip())
        except (ValueError, OSError):
            pass
    return None


def _start_web_daemon(port: int, host: str, debug: bool, log_level: str, config_dir: Path) -> None:
    """Start web interface as daemon process."""
    print_info("Starting web interface as daemon...")
    
    # Find the visualizer script
    # Look in the package tools directory
    package_root = Path(__file__).parent.parent.parent
    visualizer_script = package_root / "tools" / "visualizer" / "app.py"
    
    if not visualizer_script.exists():
        print_error(f"Visualizer script not found: {visualizer_script}")
        return
    
    # Create daemon command
    cmd = [
        sys.executable, str(visualizer_script),
        "--port", str(port),
        "--host", host,
        "--log-level", log_level
    ]
    
    if debug:
        cmd.append("--debug")
    
    # Start process
    process = subprocess.Popen(
        cmd,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        start_new_session=True
    )
    
    # Save PID
    pid_file = config_dir / WEB_PID_FILE
    with open(pid_file, 'w') as f:
        f.write(str(process.pid))
    
    print_success(f"Web interface started as daemon (PID: {process.pid})")
    print_info(f"Interface: http://{host}:{port}")
    print_info("Status: aw web-status")
    print_info("Stop: aw web-stop")


def _start_web_interactive(port: int, host: str, debug: bool, no_browser: bool, 
                          log_level: str, config_dir: Path) -> None:
    """Start web interface in interactive mode."""
    print_info("Starting web interface in interactive mode...")
    
    # Find the visualizer script
    package_root = Path(__file__).parent.parent.parent
    visualizer_script = package_root / "tools" / "visualizer" / "app.py"
    
    if not visualizer_script.exists():
        print_error(f"Visualizer script not found: {visualizer_script}")
        return
    
    # Save PID for interactive mode too
    pid_file = config_dir / WEB_PID_FILE
    with open(pid_file, 'w') as f:
        f.write(str(os.getpid()))
    
    try:
        print_success("Web interface starting...")
        print_info(f"Interface: http://{host}:{port}")
        print_info("Press Ctrl+C to stop")
        
        if not no_browser and host in ["localhost", "127.0.0.1"]:
            import webbrowser
            import time
            # Give the server a moment to start
            print_info("Opening browser...")
            time.sleep(2)
            webbrowser.open(f"http://{host}:{port}")
        
        # Start the visualizer directly
        env = os.environ.copy()
        env["FLASK_HOST"] = host
        env["FLASK_PORT"] = str(port)
        env["FLASK_DEBUG"] = "1" if debug else "0"
        
        subprocess.run([
            sys.executable, str(visualizer_script)
        ], env=env, check=True)
        
    except KeyboardInterrupt:
        print_info("\nGracefully shutting down...")
    except subprocess.CalledProcessError as e:
        print_error(f"Web interface failed: {e}")
    finally:
        # Cleanup on exit
        _cleanup_web_files(config_dir)


def _graceful_stop_web(pid: int) -> None:
    """Gracefully stop web interface process."""
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


def _force_stop_web(pid: int) -> None:
    """Force stop web interface process."""
    try:
        os.kill(pid, signal.SIGKILL)
        print_info("Forced web interface stop")
    except OSError:
        print_info("Process already stopped")


def _cleanup_web_files(config_dir: Path) -> None:
    """Cleanup web interface temporary files."""
    pid_file = config_dir / WEB_PID_FILE
    pid_file.unlink(missing_ok=True)


def _get_web_status_data(config_dir: Path, verbose: bool) -> dict:
    """Get web interface status data."""
    from datetime import datetime
    
    status_data = {
        "web_interface": {
            "running": _is_web_running(config_dir),
            "pid": _get_web_pid(config_dir),
            "url": None,
            "version": "1.0.0"
        },
        "system": {
            "config_dir": str(config_dir),
            "timestamp": datetime.now().isoformat()
        }
    }
    
    if status_data["web_interface"]["running"]:
        # Try to detect port from process
        status_data["web_interface"]["url"] = "http://localhost:5000"  # Default
    
    return status_data


def _show_web_status(status_data: dict, verbose: bool) -> None:
    """Show web interface status information."""
    web = status_data["web_interface"]
    
    # Web interface status panel
    web_info = []
    
    if web["running"]:
        web_info.append("[green]Status: Running ✓[/green]")
        web_info.append(f"PID: {web['pid']}")
        if web["url"]:
            web_info.append(f"URL: {web['url']}")
    else:
        web_info.append("[red]Status: Stopped ✗[/red]")
    
    web_info.append(f"Version: {web['version']}")
    
    console.print(Panel("\n".join(web_info), title="Web Interface Status", border_style="blue"))
    
    if not web["running"]:
        console.print(Panel(
            "Start the web interface with: [bold]aw web[/bold]",
            title="Quick Start",
            border_style="green"
        ))