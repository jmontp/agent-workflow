"""
Orchestrator Service - Integration layer with the existing Orchestrator class
"""

import asyncio
import logging
import sys
import yaml
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime

from config import settings

# Add orchestrator paths to Python path
lib_path = Path(__file__).parent.parent.parent.parent / "lib"
scripts_path = Path(__file__).parent.parent.parent.parent / "scripts"
sys.path.insert(0, str(lib_path))
sys.path.insert(0, str(scripts_path))

try:
    from orchestrator import Orchestrator, Project, OrchestrationMode
    from state_machine import State, StateMachine
    from data_models import ProjectData, Epic, Story, Sprint
    from project_storage import ProjectStorage
    ORCHESTRATOR_AVAILABLE = True
except ImportError as e:
    logging.warning(f"Could not import orchestrator components: {e}")
    ORCHESTRATOR_AVAILABLE = False
    
    # Fallback classes for development
    class Orchestrator:
        def __init__(self, *args, **kwargs):
            pass
        async def handle_command(self, *args, **kwargs):
            return {"success": False, "error": "Orchestrator not available"}
    
    class Project:
        pass
    
    class OrchestrationMode:
        BLOCKING = "blocking"
        PARTIAL = "partial"
        AUTONOMOUS = "autonomous"
    
    class State:
        IDLE = "IDLE"


logger = logging.getLogger(__name__)


class OrchestratorService:
    """
    Service layer that wraps the existing Orchestrator class and provides
    a clean interface for the FastAPI application.
    """
    
    def __init__(self):
        self.orchestrator: Optional[Orchestrator] = None
        self.initialized = False
        self.running = False
        self._background_task: Optional[asyncio.Task] = None
        self._command_history: List[Dict[str, Any]] = []
        self._active_commands: Dict[str, Dict[str, Any]] = {}
        
    async def initialize(self) -> None:
        """Initialize the orchestrator service"""
        try:
            if not ORCHESTRATOR_AVAILABLE:
                logger.warning("Orchestrator not available - running in mock mode")
                self.initialized = True
                return
            
            # Determine config path
            config_path = Path(settings.orchestrator_config_path)
            if not config_path.is_absolute():
                config_path = Path(__file__).parent.parent.parent.parent / config_path
            
            logger.info(f"Initializing orchestrator with config: {config_path}")
            
            # Initialize orchestrator
            self.orchestrator = Orchestrator(str(config_path))
            
            # Start background orchestrator loop
            self._background_task = asyncio.create_task(self._run_orchestrator_loop())
            
            self.initialized = True
            self.running = True
            logger.info("Orchestrator service initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize orchestrator service: {e}")
            raise
    
    async def shutdown(self) -> None:
        """Shutdown the orchestrator service"""
        logger.info("Shutting down orchestrator service...")
        
        self.running = False
        
        if self._background_task:
            self._background_task.cancel()
            try:
                await self._background_task
            except asyncio.CancelledError:
                pass
        
        if self.orchestrator:
            self.orchestrator.stop()
        
        logger.info("Orchestrator service shut down")
    
    async def _run_orchestrator_loop(self) -> None:
        """Run the orchestrator background loop"""
        if not self.orchestrator:
            return
        
        try:
            await self.orchestrator.run()
        except asyncio.CancelledError:
            logger.info("Orchestrator loop cancelled")
        except Exception as e:
            logger.error(f"Error in orchestrator loop: {e}")
    
    async def execute_command(
        self,
        command: str,
        project_name: str = "default",
        user_id: Optional[int] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Execute a command through the orchestrator"""
        if not self.initialized:
            raise RuntimeError("Orchestrator service not initialized")
        
        # Generate command ID
        command_id = f"cmd_{datetime.now().timestamp()}"
        
        # Record command start
        command_record = {
            "id": command_id,
            "command": command,
            "project_name": project_name,
            "user_id": user_id,
            "parameters": kwargs,
            "started_at": datetime.now(),
            "status": "running"
        }
        
        self._active_commands[command_id] = command_record
        self._command_history.append(command_record)
        
        try:
            if not self.orchestrator:
                # Mock mode
                result = {
                    "success": True,
                    "message": f"Mock execution of command: {command}",
                    "command_id": command_id,
                    "project_name": project_name
                }
            else:
                # Execute through orchestrator
                result = await self.orchestrator.handle_command(
                    command, project_name, **kwargs
                )
                result["command_id"] = command_id
            
            # Update command record
            command_record.update({
                "completed_at": datetime.now(),
                "status": "completed" if result.get("success") else "failed",
                "result": result
            })
            
            return result
            
        except Exception as e:
            # Update command record with error
            command_record.update({
                "completed_at": datetime.now(),
                "status": "failed",
                "error": str(e)
            })
            
            logger.error(f"Command execution failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "command_id": command_id
            }
            
        finally:
            # Remove from active commands
            self._active_commands.pop(command_id, None)
    
    def get_projects(self) -> List[Dict[str, Any]]:
        """Get list of all projects"""
        if not self.orchestrator:
            return [{
                "name": "default",
                "path": ".",
                "orchestration_mode": "blocking",
                "current_state": "IDLE",
                "active_tasks": 0,
                "pending_approvals": 0
            }]
        
        return [project.to_dict() for project in self.orchestrator.projects.values()]
    
    def get_project(self, project_name: str) -> Optional[Dict[str, Any]]:
        """Get specific project details"""
        if not self.orchestrator:
            if project_name == "default":
                return {
                    "name": "default",
                    "path": ".",
                    "orchestration_mode": "blocking",
                    "current_state": "IDLE",
                    "active_tasks": 0,
                    "pending_approvals": 0
                }
            return None
        
        project = self.orchestrator.projects.get(project_name)
        return project.to_dict() if project else None
    
    def get_project_state(self, project_name: str) -> Optional[Dict[str, Any]]:
        """Get project state machine information"""
        if not self.orchestrator:
            return {
                "current_state": "IDLE",
                "allowed_commands": ["/epic", "/state"],
                "transition_matrix": {},
                "mermaid_diagram": "graph TD\n    A[IDLE] --> B[BACKLOG_READY]"
            }
        
        project = self.orchestrator.projects.get(project_name)
        if not project:
            return None
        
        return project.state_machine.get_state_info()
    
    def get_system_status(self) -> Dict[str, Any]:
        """Get overall system status"""
        status = {
            "orchestrator_available": ORCHESTRATOR_AVAILABLE,
            "initialized": self.initialized,
            "running": self.running,
            "total_projects": len(self.get_projects()),
            "active_commands": len(self._active_commands),
            "command_history_count": len(self._command_history)
        }
        
        if self.orchestrator:
            # Add orchestrator-specific status
            active_tasks = sum(len(p.active_tasks) for p in self.orchestrator.projects.values())
            pending_approvals = sum(len(p.pending_approvals) for p in self.orchestrator.projects.values())
            
            status.update({
                "active_tasks": active_tasks,
                "pending_approvals": pending_approvals,
                "approval_queue_size": len(self.orchestrator.approval_queue)
            })
        
        return status
    
    def get_command_history(
        self,
        project_name: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> Dict[str, Any]:
        """Get command execution history"""
        history = self._command_history
        
        # Filter by project if specified
        if project_name:
            history = [cmd for cmd in history if cmd.get("project_name") == project_name]
        
        # Apply pagination
        total = len(history)
        history = history[offset:offset + limit]
        
        return {
            "commands": history,
            "total": total,
            "offset": offset,
            "limit": limit
        }
    
    def get_active_commands(self) -> List[Dict[str, Any]]:
        """Get currently running commands"""
        return list(self._active_commands.values())
    
    async def validate_command(
        self,
        command: str,
        project_name: str = "default"
    ) -> Dict[str, Any]:
        """Validate a command without executing it"""
        if not self.orchestrator:
            return {
                "valid": True,
                "message": "Command validation not available in mock mode"
            }
        
        project = self.orchestrator.projects.get(project_name)
        if not project:
            return {
                "valid": False,
                "error": f"Project not found: {project_name}",
                "available_projects": list(self.orchestrator.projects.keys())
            }
        
        # Validate against state machine
        result = project.state_machine.validate_command(command)
        
        return {
            "valid": result.success,
            "error_message": result.error_message,
            "hint": result.hint,
            "current_state": project.state_machine.current_state.value,
            "allowed_commands": project.state_machine.get_allowed_commands()
        }
    
    async def get_project_backlog(self, project_name: str) -> Dict[str, Any]:
        """Get project backlog data"""
        if not self.orchestrator:
            return {
                "epics": [],
                "stories": [],
                "sprints": []
            }
        
        project = self.orchestrator.projects.get(project_name)
        if not project:
            return {"error": f"Project not found: {project_name}"}
        
        try:
            project_data = project.storage.load_project_data()
            
            return {
                "epics": [epic.__dict__ for epic in project_data.epics],
                "stories": [story.__dict__ for story in project_data.stories],
                "sprints": [sprint.__dict__ for sprint in project_data.sprints]
            }
            
        except Exception as e:
            logger.error(f"Failed to load project backlog: {e}")
            return {"error": f"Failed to load backlog: {str(e)}"}
    
    def is_healthy(self) -> bool:
        """Check if the orchestrator service is healthy"""
        return self.initialized and (not ORCHESTRATOR_AVAILABLE or self.running)