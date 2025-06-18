"""
Core orchestrator module for agent-workflow package.

This module provides the main Orchestrator class that coordinates AI agents
and manages the TDD-Scrum workflow.
"""

import os
import asyncio
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class Orchestrator:
    """
    Main orchestrator for coordinating AI agents and managing workflows.
    
    The Orchestrator is responsible for:
    - Managing project lifecycles
    - Coordinating agent interactions
    - Handling Human-in-the-Loop approvals
    - Maintaining state across projects
    """
    
    def __init__(self, config_path: Optional[Path] = None):
        """
        Initialize the orchestrator.
        
        Args:
            config_path: Optional path to configuration file
        """
        self.config_path = config_path
        self.config = {}
        self.projects = {}
        self.running = False
        self.agents = {}
        
        if config_path and config_path.exists():
            self._load_configuration()
    
    def _load_configuration(self) -> None:
        """Load configuration from file."""
        try:
            import yaml
            with open(self.config_path, 'r') as f:
                self.config = yaml.safe_load(f)
            logger.info(f"Loaded configuration from {self.config_path}")
        except Exception as e:
            logger.error(f"Failed to load configuration: {e}")
            raise
    
    async def start(self, projects: List[Dict[str, Any]], mode: Optional[str] = None) -> None:
        """
        Start the orchestrator with specified projects.
        
        Args:
            projects: List of project configurations
            mode: Optional mode override
        """
        logger.info("Starting orchestrator...")
        self.running = True
        
        # Initialize projects
        for project in projects:
            await self._initialize_project(project, mode)
        
        # Start main coordination loop
        await self._coordination_loop()
    
    async def stop(self, save_state: bool = True) -> None:
        """
        Stop the orchestrator gracefully.
        
        Args:
            save_state: Whether to save current state
        """
        logger.info("Stopping orchestrator...")
        self.running = False
        
        if save_state:
            await self._save_state()
        
        # Cleanup agents
        for agent in self.agents.values():
            if hasattr(agent, 'cleanup'):
                await agent.cleanup()
    
    async def _initialize_project(self, project: Dict[str, Any], mode: Optional[str]) -> None:
        """Initialize a single project."""
        project_name = project["name"]
        project_path = Path(project["path"])
        
        logger.info(f"Initializing project: {project_name}")
        
        # Create project state
        self.projects[project_name] = {
            "config": project,
            "path": project_path,
            "mode": mode or project.get("mode", "blocking"),
            "state": "IDLE",
            "last_activity": datetime.now(),
            "active_tasks": [],
            "pending_approvals": []
        }
        
        # Initialize project state directory
        state_dir = project_path / ".orch-state"
        state_dir.mkdir(exist_ok=True)
    
    async def _coordination_loop(self) -> None:
        """Main coordination loop."""
        while self.running:
            try:
                # Monitor projects
                for project_name, project_data in self.projects.items():
                    await self._monitor_project(project_name, project_data)
                
                # Process pending approvals
                await self._process_approvals()
                
                # Coordinate agents
                await self._coordinate_agents()
                
                # Wait before next cycle
                await asyncio.sleep(5)
                
            except Exception as e:
                logger.error(f"Error in coordination loop: {e}")
                await asyncio.sleep(1)
    
    async def _monitor_project(self, project_name: str, project_data: Dict[str, Any]) -> None:
        """Monitor a single project."""
        try:
            # Check project health
            project_path = project_data["path"]
            if not project_path.exists():
                logger.warning(f"Project path not found: {project_path}")
                return
            
            # Update last activity
            project_data["last_activity"] = datetime.now()
            
            # Check for new tasks or changes
            await self._check_project_changes(project_name, project_data)
            
        except Exception as e:
            logger.error(f"Error monitoring project {project_name}: {e}")
    
    async def _check_project_changes(self, project_name: str, project_data: Dict[str, Any]) -> None:
        """Check for changes in project that require attention."""
        # This would implement more sophisticated change detection
        # For now, it's a placeholder
        pass
    
    async def _process_approvals(self) -> None:
        """Process pending Human-in-the-Loop approvals."""
        for project_name, project_data in self.projects.items():
            pending_approvals = project_data.get("pending_approvals", [])
            
            for approval in pending_approvals[:]:  # Copy list for safe iteration
                if await self._check_approval_timeout(approval):
                    # Handle timeout
                    await self._handle_approval_timeout(project_name, approval)
                    pending_approvals.remove(approval)
    
    async def _check_approval_timeout(self, approval: Dict[str, Any]) -> bool:
        """Check if an approval has timed out."""
        # Implement timeout logic
        return False
    
    async def _handle_approval_timeout(self, project_name: str, approval: Dict[str, Any]) -> None:
        """Handle approval timeout."""
        logger.warning(f"Approval timeout for project {project_name}: {approval['task']}")
    
    async def _coordinate_agents(self) -> None:
        """Coordinate agent interactions."""
        # This would implement agent coordination logic
        # For now, it's a placeholder
        pass
    
    async def _save_state(self) -> None:
        """Save current orchestrator state."""
        for project_name, project_data in self.projects.items():
            await self._save_project_state(project_name, project_data)
    
    async def _save_project_state(self, project_name: str, project_data: Dict[str, Any]) -> None:
        """Save state for a specific project."""
        try:
            project_path = project_data["path"]
            state_file = project_path / ".orch-state" / "status.json"
            
            state_data = {
                "project_name": project_name,
                "current_state": project_data["state"],
                "orchestration_mode": project_data["mode"],
                "last_updated": datetime.now().isoformat(),
                "active_tasks": project_data.get("active_tasks", []),
                "pending_approvals": project_data.get("pending_approvals", [])
            }
            
            import json
            with open(state_file, 'w') as f:
                json.dump(state_data, f, indent=2)
            
            logger.debug(f"Saved state for project: {project_name}")
            
        except Exception as e:
            logger.error(f"Failed to save state for project {project_name}: {e}")
    
    def get_status(self) -> Dict[str, Any]:
        """Get current orchestrator status."""
        return {
            "running": self.running,
            "projects": {
                name: {
                    "state": data["state"],
                    "mode": data["mode"],
                    "last_activity": data["last_activity"].isoformat(),
                    "active_tasks": len(data.get("active_tasks", [])),
                    "pending_approvals": len(data.get("pending_approvals", []))
                }
                for name, data in self.projects.items()
            },
            "timestamp": datetime.now().isoformat()
        }
    
    async def register_project(self, project_config: Dict[str, Any]) -> None:
        """Register a new project with the orchestrator."""
        project_name = project_config["name"]
        logger.info(f"Registering project: {project_name}")
        
        await self._initialize_project(project_config, None)
    
    async def unregister_project(self, project_name: str) -> None:
        """Unregister a project from the orchestrator."""
        if project_name in self.projects:
            logger.info(f"Unregistering project: {project_name}")
            del self.projects[project_name]
    
    async def execute_command(self, project_name: str, command: str, **kwargs) -> Dict[str, Any]:
        """
        Execute a command for a specific project.
        
        Args:
            project_name: Name of target project
            command: Command to execute
            **kwargs: Command arguments
            
        Returns:
            Dict containing execution results
        """
        if project_name not in self.projects:
            raise ValueError(f"Project not found: {project_name}")
        
        project_data = self.projects[project_name]
        
        # Route command to appropriate handler
        if command == "start_sprint":
            return await self._start_sprint(project_name, project_data, **kwargs)
        elif command == "approve_task":
            return await self._approve_task(project_name, project_data, **kwargs)
        elif command == "get_status":
            return await self._get_project_status(project_name, project_data)
        else:
            raise ValueError(f"Unknown command: {command}")
    
    async def _start_sprint(self, project_name: str, project_data: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        """Start a sprint for the project."""
        logger.info(f"Starting sprint for project: {project_name}")
        
        # Update project state
        project_data["state"] = "SPRINT_ACTIVE"
        
        return {
            "success": True,
            "message": f"Sprint started for project {project_name}",
            "project_state": project_data["state"]
        }
    
    async def _approve_task(self, project_name: str, project_data: Dict[str, Any], task_id: str) -> Dict[str, Any]:
        """Approve a pending task."""
        logger.info(f"Approving task {task_id} for project: {project_name}")
        
        # Remove from pending approvals
        pending_approvals = project_data.get("pending_approvals", [])
        pending_approvals = [a for a in pending_approvals if a.get("id") != task_id]
        project_data["pending_approvals"] = pending_approvals
        
        return {
            "success": True,
            "message": f"Task {task_id} approved for project {project_name}",
            "pending_approvals": len(pending_approvals)
        }
    
    async def _get_project_status(self, project_name: str, project_data: Dict[str, Any]) -> Dict[str, Any]:
        """Get detailed status for a project."""
        return {
            "project_name": project_name,
            "state": project_data["state"],
            "mode": project_data["mode"],
            "path": str(project_data["path"]),
            "last_activity": project_data["last_activity"].isoformat(),
            "active_tasks": project_data.get("active_tasks", []),
            "pending_approvals": project_data.get("pending_approvals", [])
        }