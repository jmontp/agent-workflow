"""
AI Agent TDD-Scrum Workflow Orchestrator

Central coordination engine that manages workflows across multiple projects,
implements HITL approval gates, and coordinates specialized AI agents.
"""

import asyncio
import json
import yaml
import os
import logging
import subprocess
import signal
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any, Set, Tuple
from dataclasses import dataclass, field, asdict
from enum import Enum

# Graceful fallback for psutil
try:
    import psutil
except ImportError:
    psutil = None

# Import core components
from .models import ProjectData, Epic, Story, Sprint, EpicStatus, StoryStatus, SprintStatus
from .models import TDDCycle, TDDTask, TDDState, TestResult, TestStatus
from .state_machine import StateMachine, State, CommandResult, TDDStateMachine, TDDCommandResult
from .storage import ProjectStorage

logger = logging.getLogger(__name__)


class OrchestrationMode(Enum):
    """Project orchestration modes"""
    BLOCKING = "blocking"      # Requires human approval
    PARTIAL = "partial"        # Quarantined output
    AUTONOMOUS = "autonomous"  # Full execution
    COLLABORATIVE = "collaborative"  # Multi-user project support


class OrchestratorStatus(Enum):
    """Status of project orchestrators"""
    STOPPED = "stopped"
    STARTING = "starting"
    RUNNING = "running"
    PAUSING = "pausing"
    PAUSED = "paused"
    STOPPING = "stopping"
    ERROR = "error"
    CRASHED = "crashed"


class ProjectPriority(Enum):
    """Project priority levels"""
    CRITICAL = "critical"
    HIGH = "high"
    NORMAL = "normal"
    LOW = "low"


@dataclass
class ResourceLimits:
    """Resource limits for a project"""
    max_parallel_agents: int = 3
    max_memory_mb: int = 2048
    cpu_priority: float = 1.0


@dataclass
class ProjectConfig:
    """Project configuration"""
    name: str
    path: str
    orchestration_mode: OrchestrationMode = OrchestrationMode.BLOCKING
    priority: ProjectPriority = ProjectPriority.NORMAL
    discord_channel: Optional[str] = None
    resource_limits: ResourceLimits = field(default_factory=ResourceLimits)


@dataclass
class Project:
    """Project configuration and state"""
    name: str
    path: Path
    orchestration_mode: OrchestrationMode
    priority: ProjectPriority
    state_machine: StateMachine
    tdd_state_machine: TDDStateMachine
    active_tasks: List[Any]  # Task objects
    pending_approvals: List[str]
    storage: ProjectStorage
    context_manager: Optional[Any] = None  # Will be ContextManager when available
    discord_channel: Optional[str] = None
    resource_limits: ResourceLimits = field(default_factory=ResourceLimits)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert project to dictionary for serialization"""
        return {
            "name": self.name,
            "path": str(self.path),
            "orchestration_mode": self.orchestration_mode.value,
            "priority": self.priority.value,
            "current_state": self.state_machine.current_state.value,
            "active_tasks": [asdict(task) for task in self.active_tasks],
            "pending_approvals": self.pending_approvals,
            "discord_channel": self.discord_channel
        }


@dataclass
class ApprovalRequest:
    """Request for human approval"""
    id: str
    project_name: str
    task: Any  # Task object
    reason: str
    created_at: datetime
    retry_count: int = 0


@dataclass
class ProjectOrchestrator:
    """Information about a running project orchestrator"""
    project_name: str
    project_path: str
    process: Optional[subprocess.Popen] = None
    status: OrchestratorStatus = OrchestratorStatus.STOPPED
    pid: Optional[int] = None
    start_time: Optional[datetime] = None
    last_heartbeat: Optional[datetime] = None
    cpu_usage: float = 0.0
    memory_usage: float = 0.0
    active_agents: int = 0
    current_sprint: Optional[str] = None
    backlog_size: int = 0
    error_count: int = 0
    restart_count: int = 0


@dataclass
class ResourceAllocation:
    """Resource allocation for a project"""
    project_name: str
    allocated_agents: int
    allocated_memory_mb: int
    allocated_cpu_percent: float
    priority_weight: float
    usage_history: List[Tuple[datetime, Dict[str, float]]] = field(default_factory=list)


@dataclass
class GlobalMetrics:
    """Global orchestration metrics"""
    total_projects: int = 0
    active_projects: int = 0
    total_agents: int = 0
    total_memory_usage_mb: float = 0.0
    total_cpu_usage_percent: float = 0.0
    total_stories_in_progress: int = 0
    total_stories_completed: int = 0
    average_cycle_time_hours: float = 0.0
    cross_project_insights: int = 0
    resource_efficiency: float = 0.0


class Task:
    """Task representation for agent execution"""
    def __init__(self, id: str, agent_type: str, command: str, context: Dict[str, Any] = None, status: str = "PENDING"):
        self.id = id
        self.agent_type = agent_type
        self.command = command
        self.context = context or {}
        self.status = status


class AgentResult:
    """Result from agent execution"""
    def __init__(self, success: bool, output: str = "", error: str = ""):
        self.success = success
        self.output = output
        self.error = error


class Orchestrator:
    """
    Central orchestration engine for AI Agent TDD-Scrum workflow.
    
    Manages multiple projects, coordinates agents, enforces state machine,
    and implements Human-In-The-Loop approval workflows with multi-project
    coordination capabilities.
    """
    
    def __init__(self, config_path: str = "config/projects.yaml", mode: str = "single"):
        """
        Initialize the orchestrator.
        
        Args:
            config_path: Path to configuration file
            mode: Orchestration mode ('single' or 'multi')
        """
        self.config_path = Path(config_path)
        self.mode = mode  # 'single' or 'multi' project mode
        self.projects: Dict[str, Project] = {}
        self.agents: Dict[str, Any] = {}
        self.approval_queue: List[ApprovalRequest] = []
        self.running = False
        
        # Multi-project orchestration attributes
        self.orchestrators: Dict[str, ProjectOrchestrator] = {}
        self.resource_allocations: Dict[str, ResourceAllocation] = {}
        self.status = OrchestratorStatus.STOPPED
        self.start_time: Optional[datetime] = None
        self.metrics = GlobalMetrics()
        
        # Global configuration settings
        self.global_config = {
            "max_total_agents": 12,
            "max_concurrent_projects": 5,
            "global_memory_limit_gb": 8,
            "resource_allocation_strategy": "priority_based",
            "scheduling_interval_seconds": 30,
            "resource_rebalance_interval_seconds": 300,
            "health_check_interval_seconds": 60,
            "global_state_path": ".orch-global-state",
            "global_discord_guild": None
        }
        
        # Background tasks
        self._monitoring_task: Optional[asyncio.Task] = None
        self._scheduling_task: Optional[asyncio.Task] = None
        self._resource_balancing_task: Optional[asyncio.Task] = None
        self._health_check_task: Optional[asyncio.Task] = None
        
        # Cross-project knowledge and insights
        self.shared_patterns: Dict[str, Any] = {}
        self.cross_project_insights: List[Dict[str, Any]] = []
        self.global_best_practices: Dict[str, Any] = {}
        
        # Event system for coordination
        self.event_queue: asyncio.Queue = asyncio.Queue()
        self.event_handlers: Dict[str, List] = {}
        
        # Initialize logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
        # Initialize state broadcaster
        self.state_broadcaster = None
        self._broadcaster_task = None
        
        # Load configuration and initialize
        self._load_configuration()
        self._initialize_agents()
        self._load_project_states()
        
        logger.info(f"Orchestrator initialized successfully in {mode} mode")
    
    def _load_configuration(self) -> None:
        """Load project configurations from YAML file"""
        try:
            if self.config_path.exists():
                with open(self.config_path, 'r') as f:
                    config = yaml.safe_load(f)
                    
                # Load global configuration if present
                if "global" in config:
                    self.global_config.update(config["global"])
                    
                for project_config in config.get("projects", []):
                    project_name = project_config["name"]
                    project_path = Path(project_config["path"])
                    orchestration_mode = OrchestrationMode(project_config.get("orchestration", "blocking"))
                    priority = ProjectPriority(project_config.get("priority", "normal"))
                    
                    # Create project with state machine and storage
                    storage = ProjectStorage(str(project_path))
                    
                    # Initialize context manager for project if available
                    context_manager = None
                    try:
                        # Try to import and initialize context manager
                        # This will be updated when context is migrated
                        pass
                    except Exception as e:
                        logger.warning(f"Failed to initialize context manager for {project_name}: {str(e)}")
                    
                    # Parse resource limits
                    resource_config = project_config.get("resources", {})
                    resource_limits = ResourceLimits(
                        max_parallel_agents=resource_config.get("max_parallel_agents", 3),
                        max_memory_mb=resource_config.get("max_memory_mb", 2048),
                        cpu_priority=resource_config.get("cpu_priority", 1.0)
                    )
                    
                    project = Project(
                        name=project_name,
                        path=project_path,
                        orchestration_mode=orchestration_mode,
                        priority=priority,
                        state_machine=StateMachine(),
                        tdd_state_machine=TDDStateMachine(),
                        active_tasks=[],
                        pending_approvals=[],
                        storage=storage,
                        context_manager=context_manager,
                        discord_channel=project_config.get("discord_channel"),
                        resource_limits=resource_limits
                    )
                    
                    self.projects[project_name] = project
                    logger.info(f"Loaded project: {project_name} ({orchestration_mode.value}, {priority.value})")
            else:
                logger.warning(f"Configuration file not found: {self.config_path}")
                # Create default project
                self._create_default_project()
                
        except Exception as e:
            logger.error(f"Failed to load configuration: {e}")
            self._create_default_project()
    
    def _create_default_project(self) -> None:
        """Create default project configuration"""
        storage = ProjectStorage(".")
        
        # Initialize context manager for default project if available
        context_manager = None
        try:
            # This will be updated when context is migrated
            pass
        except Exception as e:
            logger.warning(f"Failed to initialize context manager for default project: {str(e)}")
        
        default_project = Project(
            name="default",
            path=Path("."),
            orchestration_mode=OrchestrationMode.BLOCKING,
            priority=ProjectPriority.NORMAL,
            state_machine=StateMachine(),
            tdd_state_machine=TDDStateMachine(),
            active_tasks=[],
            pending_approvals=[],
            storage=storage,
            context_manager=context_manager
        )
        self.projects["default"] = default_project
        logger.info("Created default project")
    
    def _initialize_agents(self) -> None:
        """Initialize AI agents"""
        try:
            # This will be updated when agents are migrated
            # For now, create placeholder agent registry
            agent_types = ["DesignAgent", "CodeAgent", "QAAgent", "DataAgent", "MockAgent"]
            for agent_type in agent_types:
                # Create placeholder agent
                self.agents[agent_type] = {"type": agent_type, "available": True}
                logger.info(f"Initialized agent: {agent_type}")
                
        except Exception as e:
            logger.error(f"Failed to initialize agents: {e}")
    
    def _get_agent_for_project(self, agent_type: str, project: Project):
        """Get agent instance configured for specific project"""
        agent = self.agents.get(agent_type)
        if agent and project.context_manager:
            # Set context manager for this project if available
            agent["context_manager"] = project.context_manager
        return agent
    
    def _load_project_states(self) -> None:
        """Load persisted project states"""
        for project in self.projects.values():
            state_file = project.path / ".orch-state" / "status.json"
            if state_file.exists():
                try:
                    with open(state_file, 'r') as f:
                        state_data = json.load(f)
                        
                    # Restore state machine state
                    if "current_state" in state_data:
                        project.state_machine.force_state(State(state_data["current_state"]))
                        
                    # Restore active tasks (simplified for now)
                    for task_data in state_data.get("active_tasks", []):
                        task = Task(
                            id=task_data["id"],
                            agent_type=task_data["agent_type"],
                            command=task_data["command"],
                            context=task_data.get("context", {}),
                            status=task_data["status"]
                        )
                        project.active_tasks.append(task)
                    
                    project.pending_approvals = state_data.get("pending_approvals", [])
                    logger.info(f"Restored state for project: {project.name}")
                    
                except Exception as e:
                    logger.error(f"Failed to load state for {project.name}: {e}")
    
    def _save_project_state(self, project: Project) -> None:
        """Save project state to disk"""
        state_dir = project.path / ".orch-state"
        state_dir.mkdir(exist_ok=True)
        
        state_file = state_dir / "status.json"
        try:
            with open(state_file, 'w') as f:
                json.dump(project.to_dict(), f, indent=2, default=str)
            logger.debug(f"Saved state for project: {project.name}")
            
        except Exception as e:
            logger.error(f"Failed to save state for {project.name}: {e}")
    
    async def run(self, projects: Optional[List[Dict[str, Any]]] = None, mode: Optional[str] = None, 
                  start_broadcaster: bool = True, broadcaster_port: int = 8080) -> None:
        """
        Run the orchestrator with state broadcaster integration.
        
        This is the main entry point that starts both the orchestrator and state broadcaster
        for real-time updates to the web interface.
        
        Args:
            projects: Optional list of project configurations
            mode: Optional mode override
            start_broadcaster: Whether to start the state broadcaster WebSocket server
            broadcaster_port: Port for the state broadcaster WebSocket server
        """
        logger.info(f"Running orchestrator with state broadcaster on port {broadcaster_port}")
        
        try:
            # Start state broadcaster first
            if start_broadcaster:
                await self._start_state_broadcaster(broadcaster_port)
            
            # Start orchestrator
            await self.start(projects, mode)
            
            # Keep running until stopped
            while self.running:
                await asyncio.sleep(1)
                
        except KeyboardInterrupt:
            logger.info("Received interrupt signal, shutting down...")
        except Exception as e:
            logger.error(f"Error in orchestrator run loop: {e}")
            raise
        finally:
            await self.stop()
    
    async def start(self, projects: Optional[List[Dict[str, Any]]] = None, mode: Optional[str] = None) -> None:
        """
        Start the orchestrator with specified projects.
        
        Args:
            projects: Optional list of project configurations
            mode: Optional mode override
        """
        if self.status != OrchestratorStatus.STOPPED:
            logger.warning("Orchestrator already running")
            return
        
        self.status = OrchestratorStatus.STARTING
        logger.info(f"Starting orchestrator in {self.mode} mode...")
        
        try:
            # Initialize global state directory
            global_state_path = Path(self.global_config["global_state_path"])
            global_state_path.mkdir(exist_ok=True)
            
            if self.mode == "multi":
                # Start background tasks for multi-project mode
                self._monitoring_task = asyncio.create_task(self._monitoring_loop())
                self._scheduling_task = asyncio.create_task(self._scheduling_loop())
                self._resource_balancing_task = asyncio.create_task(self._resource_balancing_loop())
                self._health_check_task = asyncio.create_task(self._health_check_loop())
                
                # Start active projects
                await self._start_active_projects()
            
            self.status = OrchestratorStatus.RUNNING
            self.start_time = datetime.utcnow()
            self.running = True
            
            logger.info("Orchestrator started successfully")
            
        except Exception as e:
            self.status = OrchestratorStatus.ERROR
            logger.error(f"Failed to start orchestrator: {str(e)}")
            raise
    
    async def stop(self, save_state: bool = True) -> None:
        """
        Stop the orchestrator gracefully.
        
        Args:
            save_state: Whether to save current state
        """
        if self.status == OrchestratorStatus.STOPPED:
            return
        
        self.status = OrchestratorStatus.STOPPING
        logger.info("Stopping orchestrator...")
        
        try:
            # Stop state broadcaster first
            await self._stop_state_broadcaster()
            
            if self.mode == "multi":
                # Stop all project orchestrators
                await self._stop_all_projects()
                
                # Cancel background tasks
                tasks = [
                    self._monitoring_task,
                    self._scheduling_task,
                    self._resource_balancing_task,
                    self._health_check_task
                ]
                
                for task in tasks:
                    if task:
                        task.cancel()
                        try:
                            await task
                        except asyncio.CancelledError:
                            pass
            
            if save_state:
                await self._save_state()
            
            # Cleanup agents
            for agent in self.agents.values():
                if hasattr(agent, 'cleanup'):
                    await agent.cleanup()
            
            self.status = OrchestratorStatus.STOPPED
            self.running = False
            logger.info("Orchestrator stopped")
            
        except Exception as e:
            self.status = OrchestratorStatus.ERROR
            logger.error(f"Error stopping orchestrator: {str(e)}")
    
    async def start_project(self, project_name: str) -> bool:
        """
        Start orchestrator for a specific project.
        
        Args:
            project_name: Name of project to start
            
        Returns:
            True if started successfully, False otherwise
        """
        if project_name not in self.projects:
            logger.error(f"Project '{project_name}' not found")
            return False
        
        project = self.projects[project_name]
        
        if project_name in self.orchestrators:
            current_status = self.orchestrators[project_name].status
            if current_status in [OrchestratorStatus.RUNNING, OrchestratorStatus.STARTING]:
                logger.warning(f"Project '{project_name}' is already running")
                return True
        
        try:
            # Calculate resource allocation
            allocation = await self._calculate_resource_allocation(project)
            self.resource_allocations[project_name] = allocation
            
            # Create orchestrator tracking object
            orchestrator = ProjectOrchestrator(
                project_name=project_name,
                project_path=str(project.path),
                status=OrchestratorStatus.RUNNING,
                start_time=datetime.utcnow()
            )
            
            self.orchestrators[project_name] = orchestrator
            
            logger.info(f"Started project orchestrator for '{project_name}'")
            return True
                
        except Exception as e:
            logger.error(f"Failed to start project '{project_name}': {str(e)}")
            if project_name in self.orchestrators:
                self.orchestrators[project_name].status = OrchestratorStatus.ERROR
            return False
    
    async def stop_project(self, project_name: str) -> bool:
        """
        Stop orchestrator for a specific project.
        
        Args:
            project_name: Name of project to stop
            
        Returns:
            True if stopped successfully, False otherwise
        """
        if project_name not in self.orchestrators:
            logger.warning(f"Project '{project_name}' is not running")
            return True
        
        orchestrator = self.orchestrators[project_name]
        
        try:
            orchestrator.status = OrchestratorStatus.STOPPING
            
            # Clean up resource allocation
            if project_name in self.resource_allocations:
                del self.resource_allocations[project_name]
            
            orchestrator.status = OrchestratorStatus.STOPPED
            
            logger.info(f"Stopped project orchestrator for '{project_name}'")
            return True
            
        except Exception as e:
            logger.error(f"Failed to stop project '{project_name}': {str(e)}")
            orchestrator.status = OrchestratorStatus.ERROR
            return False
    
    async def handle_command(self, command: str, project_name: str = "default", **kwargs) -> Dict[str, Any]:
        """
        Handle incoming commands from Discord or other interfaces.
        
        Args:
            command: The command to execute
            project_name: Target project name
            **kwargs: Additional command parameters
            
        Returns:
            Command execution result
        """
        try:
            project = self.projects.get(project_name)
            if not project:
                return {
                    "success": False,
                    "error": f"Project not found: {project_name}",
                    "available_projects": list(self.projects.keys())
                }
            
            # Skip main state machine validation for TDD commands and introspection commands
            skip_main_validation = command.startswith("/tdd") or command.startswith("/state")
            
            if not skip_main_validation:
                # Validate command against state machine
                validation_result = project.state_machine.validate_command(command)
                if not validation_result.success:
                    return {
                        "success": False,
                        "error": validation_result.error_message,
                        "hint": validation_result.hint,
                        "current_state": project.state_machine.current_state.value,
                        "allowed_commands": project.state_machine.get_allowed_commands()
                    }
            else:
                # Create successful validation result for skipped commands
                validation_result = CommandResult(success=True)
            
            # Execute command
            result = await self._execute_command(command, project, **kwargs)
            
            # Transition state if command was successful
            if result["success"] and validation_result.new_state:
                # Broadcast state transition if broadcaster is available
                old_state = project.state_machine.current_state
                project.state_machine.transition(command, project_name)
                new_state = project.state_machine.current_state
                
                # Broadcast the transition
                await self._broadcast_state_transition(old_state, new_state, project_name)
                
                self._save_project_state(project)
            
            return result
            
        except Exception as e:
            logger.error(f"Error handling command '{command}': {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _execute_command(self, command: str, project: Project, **kwargs) -> Dict[str, Any]:
        """Execute specific command logic"""
        try:
            if command.startswith("/epic"):
                return await self._handle_epic_command(project, **kwargs)
            elif command.startswith("/approve"):
                return await self._handle_approve_command(project, **kwargs)
            elif command.startswith("/sprint"):
                return await self._handle_sprint_command(command, project, **kwargs)
            elif command.startswith("/backlog"):
                return await self._handle_backlog_command(command, project, **kwargs)
            elif command.startswith("/request_changes"):
                return await self._handle_request_changes(project, **kwargs)
            elif command.startswith("/suggest_fix"):
                return await self._handle_suggest_fix(project, **kwargs)
            elif command.startswith("/skip_task"):
                return await self._handle_skip_task(project, **kwargs)
            elif command.startswith("/feedback"):
                return await self._handle_feedback(project, **kwargs)
            elif command.startswith("/state"):
                return self._handle_state_command(project)
            elif command.startswith("/tdd"):
                return await self._handle_tdd_command(command, project, **kwargs)
            else:
                return {
                    "success": False,
                    "error": f"Unknown command: {command}"
                }
                
        except Exception as e:
            logger.error(f"Error executing command '{command}': {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    # Command handlers (simplified versions for now)
    async def _handle_epic_command(self, project: Project, description: str = "", title: str = "", **kwargs) -> Dict[str, Any]:
        """Handle /epic command - create high-level initiative"""
        if not description and not title:
            return {
                "success": False,
                "error": "Epic title or description is required"
            }
        
        try:
            project_data = project.storage.load_project_data()
            
            # Create new epic
            new_epic = Epic(
                title=title or description[:50] + "..." if len(description) > 50 else description,
                description=description,
                status=EpicStatus.ACTIVE
            )
            
            project_data.epics.append(new_epic)
            project.storage.save_project_data(project_data)
            
            return {
                "success": True,
                "message": f"Epic {new_epic.id} created: {new_epic.title}",
                "epic_id": new_epic.id,
                "title": new_epic.title,
                "description": new_epic.description,
                "next_step": "Add stories with /backlog add_story"
            }
            
        except Exception as e:
            logger.error(f"Error creating epic: {e}")
            return {
                "success": False,
                "error": f"Failed to create epic: {e}"
            }
    
    async def _handle_approve_command(self, project: Project, item_ids: List[str] = None, **kwargs) -> Dict[str, Any]:
        """Handle /approve command - approve pending items"""
        if not item_ids:
            item_ids = project.pending_approvals
        
        approved_items = []
        for item_id in item_ids:
            if item_id in project.pending_approvals:
                project.pending_approvals.remove(item_id)
                approved_items.append(item_id)
        
        self._save_project_state(project)
        
        return {
            "success": True,
            "message": f"Approved {len(approved_items)} items",
            "approved_items": approved_items,
            "next_step": "Use /sprint plan to plan next sprint"
        }
    
    async def _handle_sprint_command(self, command: str, project: Project, **kwargs) -> Dict[str, Any]:
        """Handle /sprint commands - sprint lifecycle management"""
        if "plan" in command:
            return await self._plan_sprint(project, **kwargs)
        elif "start" in command:
            return await self._start_sprint(project, **kwargs)
        elif "status" in command:
            return self._get_sprint_status(project)
        elif "pause" in command:
            return self._pause_sprint(project)
        elif "resume" in command:
            return self._resume_sprint(project)
        else:
            return {
                "success": False,
                "error": "Unknown sprint command"
            }
    
    async def _plan_sprint(self, project: Project, story_ids: List[str] = None, **kwargs) -> Dict[str, Any]:
        """Plan sprint with selected stories"""
        if not story_ids:
            story_ids = ["AUTH-1", "AUTH-2"]  # Placeholder
        
        return {
            "success": True,
            "message": f"Sprint planned with {len(story_ids)} stories",
            "stories": story_ids,
            "next_step": "Use /sprint start to begin sprint execution"
        }
    
    async def _start_sprint(self, project: Project, **kwargs) -> Dict[str, Any]:
        """Start sprint execution"""
        # Create tasks for QA Agent to write tests first (TDD approach)
        qa_task = Task(
            id=f"tests-{datetime.now().timestamp()}",
            agent_type="QAAgent",
            command="Create failing tests for sprint stories",
            context={"stories": ["AUTH-1", "AUTH-2"]}
        )
        
        project.active_tasks.append(qa_task)
        self._save_project_state(project)
        
        # Start background task processing
        asyncio.create_task(self._process_project_tasks(project))
        
        return {
            "success": True,
            "message": "Sprint started - agents are now working",
            "active_tasks": len(project.active_tasks),
            "next_step": "Monitor progress with /sprint status"
        }
    
    def _get_sprint_status(self, project: Project) -> Dict[str, Any]:
        """Get current sprint status"""
        completed_tasks = len([t for t in project.active_tasks if t.status == "COMPLETED"])
        failed_tasks = len([t for t in project.active_tasks if t.status == "FAILED"])
        
        return {
            "success": True,
            "message": f"Sprint status for {project.name}",
            "total_tasks": len(project.active_tasks),
            "completed_tasks": completed_tasks,
            "failed_tasks": failed_tasks,
            "current_state": project.state_machine.current_state.value,
            "pending_approvals": len(project.pending_approvals)
        }
    
    def _pause_sprint(self, project: Project) -> Dict[str, Any]:
        """Pause sprint execution"""
        return {
            "success": True,
            "message": "Sprint paused - agent work halted",
            "next_step": "Use /sprint resume to continue"
        }
    
    def _resume_sprint(self, project: Project) -> Dict[str, Any]:
        """Resume sprint execution"""
        asyncio.create_task(self._process_project_tasks(project))
        
        return {
            "success": True,
            "message": "Sprint resumed - agents continuing work",
            "next_step": "Monitor progress with /sprint status"
        }
    
    async def _handle_backlog_command(self, command: str, project: Project, **kwargs) -> Dict[str, Any]:
        """Handle /backlog commands - backlog management"""
        if "view" in command:
            return self._view_backlog(project, **kwargs)
        elif "add_story" in command:
            return self._add_story(project, **kwargs)
        elif "prioritize" in command:
            return self._prioritize_story(project, **kwargs)
        else:
            return {
                "success": False,
                "error": "Unknown backlog command"
            }
    
    def _view_backlog(self, project: Project, backlog_type: str = "product", **kwargs) -> Dict[str, Any]:
        """View product or sprint backlog"""
        try:
            project_data = project.storage.load_project_data()
            
            if backlog_type == "sprint":
                # Show current sprint backlog
                active_sprint = project_data.get_active_sprint()
                if not active_sprint:
                    return {
                        "success": False,
                        "error": "No active sprint found"
                    }
                
                stories = project_data.get_stories_by_sprint(active_sprint.id)
                items = [
                    {
                        "id": story.id,
                        "title": story.title,
                        "status": story.status.value,
                        "priority": story.priority
                    }
                    for story in stories
                ]
                return {
                    "success": True,
                    "backlog_type": "sprint",
                    "sprint_id": active_sprint.id,
                    "sprint_goal": active_sprint.goal,
                    "items": items
                }
            else:
                # Show product backlog
                backlog_stories = project_data.get_backlog_stories()
                items = [
                    {
                        "id": story.id,
                        "title": story.title,
                        "description": story.description,
                        "priority": story.priority,
                        "epic_id": story.epic_id
                    }
                    for story in sorted(backlog_stories, key=lambda s: s.priority)
                ]
                
                return {
                    "success": True,
                    "backlog_type": "product",
                    "items": items,
                    "total_stories": len(items)
                }
                
        except Exception as e:
            logger.error(f"Error viewing backlog: {e}")
            return {
                "success": False,
                "error": f"Failed to load backlog: {e}"
            }
    
    def _add_story(self, project: Project, description: str = "", title: str = "", epic_id: str = "", priority: int = 3, **kwargs) -> Dict[str, Any]:
        """Add story to backlog"""
        if not description and not title:
            return {
                "success": False,
                "error": "Story title or description is required"
            }
        
        try:
            project_data = project.storage.load_project_data()
            
            # Validate epic_id if provided
            if epic_id and not project_data.get_epic_by_id(epic_id):
                return {
                    "success": False,
                    "error": f"Epic not found: {epic_id}"
                }
            
            # Create new story
            new_story = Story(
                title=title or description[:50] + "..." if len(description) > 50 else description,
                description=description,
                epic_id=epic_id if epic_id else None,
                priority=priority,
                status=StoryStatus.BACKLOG
            )
            
            project_data.stories.append(new_story)
            project.storage.save_project_data(project_data)
            
            return {
                "success": True,
                "message": f"Story {new_story.id} created",
                "story_id": new_story.id,
                "title": new_story.title,
                "description": new_story.description
            }
            
        except Exception as e:
            logger.error(f"Error adding story: {e}")
            return {
                "success": False,
                "error": f"Failed to add story: {e}"
            }
    
    def _prioritize_story(self, project: Project, story_id: str = "", priority: int = None, **kwargs) -> Dict[str, Any]:
        """Prioritize story in backlog"""
        if not story_id:
            return {
                "success": False,
                "error": "Story ID is required"
            }
        
        if priority is None or priority < 1 or priority > 5:
            return {
                "success": False,
                "error": "Priority must be between 1 (highest) and 5 (lowest)"
            }
        
        try:
            project_data = project.storage.load_project_data()
            story = project_data.get_story_by_id(story_id)
            
            if not story:
                return {
                    "success": False,
                    "error": f"Story not found: {story_id}"
                }
            
            old_priority = story.priority
            story.priority = priority
            project.storage.save_project_data(project_data)
            
            return {
                "success": True,
                "message": f"Story {story_id} priority updated from {old_priority} to {priority}",
                "story_id": story_id,
                "old_priority": old_priority,
                "new_priority": priority
            }
            
        except Exception as e:
            logger.error(f"Error prioritizing story: {e}")
            return {
                "success": False,
                "error": f"Failed to prioritize story: {e}"
            }
    
    async def _handle_request_changes(self, project: Project, description: str = "", **kwargs) -> Dict[str, Any]:
        """Handle request for changes during review"""
        return {
            "success": True,
            "message": f"Change request created: {description}",
            "next_step": "Changes will be added to backlog"
        }
    
    async def _handle_suggest_fix(self, project: Project, description: str = "", **kwargs) -> Dict[str, Any]:
        """Handle fix suggestion for blocked task"""
        return {
            "success": True,
            "message": f"Fix suggestion received: {description}",
            "next_step": "CodeAgent will attempt to apply fix"
        }
    
    async def _handle_skip_task(self, project: Project, **kwargs) -> Dict[str, Any]:
        """Handle skip task command"""
        return {
            "success": True,
            "message": "Current blocked task skipped",
            "next_step": "Moving to next task in sprint"
        }
    
    async def _handle_feedback(self, project: Project, description: str = "", **kwargs) -> Dict[str, Any]:
        """Handle sprint feedback/retrospective"""
        return {
            "success": True,
            "message": f"Sprint feedback recorded: {description}",
            "next_step": "Sprint complete - ready for next epic"
        }
    
    def _handle_state_command(self, project: Project) -> Dict[str, Any]:
        """Handle state inspection command"""
        return {
            "success": True,
            "state_info": project.state_machine.get_state_info(),
            "project_status": {
                "name": project.name,
                "orchestration_mode": project.orchestration_mode.value,
                "priority": project.priority.value,
                "active_tasks": len(project.active_tasks),
                "pending_approvals": len(project.pending_approvals)
            },
            "mermaid_diagram": project.state_machine.get_mermaid_diagram()
        }
    
    async def _handle_tdd_command(self, command: str, project: Project, **kwargs) -> Dict[str, Any]:
        """Handle TDD commands"""
        try:
            # Parse TDD subcommand
            parts = command.split()
            if len(parts) < 2:
                return {
                    "success": False,
                    "error": "TDD command requires action (e.g., /tdd start, /tdd status)"
                }
            
            action = parts[1]
            
            if action == "start":
                return await self._handle_tdd_start(project, **kwargs)
            elif action == "status":
                return self._handle_tdd_status(project, **kwargs)
            elif action == "next":
                return await self._handle_tdd_next(project)
            elif action == "abort":
                return await self._handle_tdd_abort(project, **kwargs)
            elif action == "logs":
                return self._handle_tdd_logs(project, **kwargs)
            elif action == "overview":
                return self._handle_tdd_overview(project)
            elif action in ["design", "test", "code", "refactor", "commit", "run_tests"]:
                return await self._handle_tdd_transition(action, project, **kwargs)
            else:
                return {
                    "success": False,
                    "error": f"Unknown TDD action: {action}",
                    "available_actions": ["start", "status", "next", "abort", "logs", "overview", "design", "test", "code", "refactor", "commit", "run_tests"]
                }
                
        except Exception as e:
            logger.error(f"Error handling TDD command '{command}': {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    # TDD command handlers (simplified implementations)
    async def _handle_tdd_start(self, project: Project, story_id: str = "", task_description: str = "", **kwargs) -> Dict[str, Any]:
        """Handle /tdd start command"""
        if not story_id:
            return {
                "success": False,
                "error": "Story ID is required to start TDD cycle",
                "hint": "Use: /tdd start <story_id>"
            }
        
        try:
            # Load project data
            project_data = project.storage.load_project_data()
            story = project_data.get_story_by_id(story_id)
            
            if not story:
                return {
                    "success": False,
                    "error": f"Story not found: {story_id}",
                    "available_stories": [s.id for s in project_data.stories]
                }
            
            # Check if story already has an active TDD cycle
            if story.tdd_cycle_id:
                existing_cycle = project.storage.load_tdd_cycle(story.tdd_cycle_id)
                if existing_cycle and not existing_cycle.is_complete():
                    return {
                        "success": False,
                        "error": f"Story {story_id} already has an active TDD cycle: {existing_cycle.id}",
                        "hint": "Use /tdd status to see current cycle or /tdd abort to cancel it"
                    }
            
            # Create new TDD cycle
            cycle = TDDCycle(story_id=story_id)
            
            # Create initial task
            if task_description:
                task = TDDTask(description=task_description)
                cycle.add_task(task)
                cycle.start_task(task.id)
            
            # Set up TDD state machine
            project.tdd_state_machine.set_active_cycle(cycle)
            
            # Update story
            story.tdd_cycle_id = cycle.id
            story.test_status = "design"
            
            # Save data
            project.storage.save_tdd_cycle(cycle)
            project.storage.save_project_data(project_data)
            
            return {
                "success": True,
                "message": f"TDD cycle started for story {story_id}",
                "cycle_id": cycle.id,
                "story_id": story_id,
                "current_state": cycle.current_state.value,
                "next_step": "Use /tdd design to create detailed specifications"
            }
            
        except Exception as e:
            logger.error(f"Error starting TDD cycle: {e}")
            return {
                "success": False,
                "error": f"Failed to start TDD cycle: {e}"
            }
    
    # Additional TDD handlers would be implemented here...
    def _handle_tdd_status(self, project: Project, **kwargs) -> Dict[str, Any]:
        """Handle /tdd status command"""
        return {
            "success": True,
            "message": "TDD status functionality to be implemented",
            "current_state": "design"
        }
    
    async def _handle_tdd_next(self, project: Project, **kwargs) -> Dict[str, Any]:
        """Handle /tdd next command"""
        return {
            "success": True,
            "message": "TDD next functionality to be implemented"
        }
    
    async def _handle_tdd_abort(self, project: Project, **kwargs) -> Dict[str, Any]:
        """Handle /tdd abort command"""
        return {
            "success": True,
            "message": "TDD abort functionality to be implemented"
        }
    
    async def _handle_tdd_transition(self, action: str, project: Project, **kwargs) -> Dict[str, Any]:
        """Handle TDD transition commands"""
        return {
            "success": True,
            "message": f"TDD {action} functionality to be implemented"
        }
    
    def _handle_tdd_logs(self, project: Project, **kwargs) -> Dict[str, Any]:
        """Handle /tdd logs command"""
        return {
            "success": True,
            "message": "TDD logs functionality to be implemented"
        }
    
    def _handle_tdd_overview(self, project: Project) -> Dict[str, Any]:
        """Handle /tdd overview command"""
        return {
            "success": True,
            "message": "TDD overview functionality to be implemented"
        }
    
    # Multi-project orchestration methods
    
    async def _start_active_projects(self) -> None:
        """Start orchestrators for all active projects"""
        for project_name in self.projects.keys():
            try:
                await self.start_project(project_name)
            except Exception as e:
                logger.error(f"Failed to start project '{project_name}': {str(e)}")
    
    async def _stop_all_projects(self) -> None:
        """Stop all running project orchestrators"""
        stop_tasks = []
        for project_name in list(self.orchestrators.keys()):
            stop_tasks.append(asyncio.create_task(self.stop_project(project_name)))
        
        if stop_tasks:
            await asyncio.gather(*stop_tasks, return_exceptions=True)
    
    async def _calculate_resource_allocation(self, project: Project) -> ResourceAllocation:
        """Calculate resource allocation for a project"""
        # Priority-based allocation
        priority_weights = {
            ProjectPriority.CRITICAL: 2.0,
            ProjectPriority.HIGH: 1.5,
            ProjectPriority.NORMAL: 1.0,
            ProjectPriority.LOW: 0.5
        }
        
        priority_weight = priority_weights.get(project.priority, 1.0)
        
        # Calculate base allocation
        total_active = len([p for p in self.projects.values() if p.name in self.orchestrators])
        
        if self.global_config["resource_allocation_strategy"] == "fair_share":
            base_agents = self.global_config["max_total_agents"] // max(total_active, 1)
            base_memory = (self.global_config["global_memory_limit_gb"] * 1024) // max(total_active, 1)
            base_cpu = 100.0 / max(total_active, 1)
        else:  # priority_based
            total_weight = sum(priority_weights.get(p.priority, 1.0) for p in self.projects.values())
            weight_ratio = priority_weight / max(total_weight, 1.0)
            base_agents = int(self.global_config["max_total_agents"] * weight_ratio)
            base_memory = int(self.global_config["global_memory_limit_gb"] * 1024 * weight_ratio)
            base_cpu = 100.0 * weight_ratio
        
        # Apply project-specific limits
        allocated_agents = min(base_agents, project.resource_limits.max_parallel_agents)
        allocated_memory = min(base_memory, project.resource_limits.max_memory_mb)
        allocated_cpu = min(base_cpu, 100.0) * project.resource_limits.cpu_priority
        
        return ResourceAllocation(
            project_name=project.name,
            allocated_agents=allocated_agents,
            allocated_memory_mb=allocated_memory,
            allocated_cpu_percent=allocated_cpu,
            priority_weight=priority_weight
        )
    
    # Background monitoring loops
    
    async def _monitoring_loop(self) -> None:
        """Background monitoring loop"""
        logger.info("Started global monitoring loop")
        
        while self.status in [OrchestratorStatus.RUNNING, OrchestratorStatus.PAUSED]:
            try:
                await self._update_orchestrator_status()
                await self._collect_metrics()
                await self._detect_cross_project_patterns()
                await asyncio.sleep(self.global_config["scheduling_interval_seconds"])
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Monitoring loop error: {str(e)}")
                await asyncio.sleep(self.global_config["scheduling_interval_seconds"] * 2)
    
    async def _scheduling_loop(self) -> None:
        """Background scheduling and coordination loop"""
        logger.info("Started global scheduling loop")
        
        while self.status in [OrchestratorStatus.RUNNING, OrchestratorStatus.PAUSED]:
            try:
                await self._optimize_project_scheduling()
                await self._handle_project_dependencies()
                await asyncio.sleep(self.global_config["scheduling_interval_seconds"])
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Scheduling loop error: {str(e)}")
    
    async def _resource_balancing_loop(self) -> None:
        """Background resource balancing loop"""
        logger.info("Started resource balancing loop")
        
        while self.status in [OrchestratorStatus.RUNNING, OrchestratorStatus.PAUSED]:
            try:
                await self._rebalance_resources()
                await asyncio.sleep(self.global_config["resource_rebalance_interval_seconds"])
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Resource balancing error: {str(e)}")
    
    async def _health_check_loop(self) -> None:
        """Background health check loop"""
        logger.info("Started health check loop")
        
        while self.status in [OrchestratorStatus.RUNNING, OrchestratorStatus.PAUSED]:
            try:
                await self._check_orchestrator_health()
                await self._restart_failed_orchestrators()
                await asyncio.sleep(self.global_config["health_check_interval_seconds"])
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Health check error: {str(e)}")
    
    # Helper methods for background operations (simplified implementations)
    
    async def _update_orchestrator_status(self) -> None:
        """Update status of all orchestrators"""
        for name, orchestrator in self.orchestrators.items():
            orchestrator.last_heartbeat = datetime.utcnow()
    
    async def _collect_metrics(self) -> None:
        """Collect global metrics"""
        self.metrics.total_projects = len(self.projects)
        self.metrics.active_projects = len([
            o for o in self.orchestrators.values()
            if o.status == OrchestratorStatus.RUNNING
        ])
        self.metrics.total_agents = sum(o.active_agents for o in self.orchestrators.values())
        self.metrics.total_memory_usage_mb = sum(o.memory_usage for o in self.orchestrators.values())
        self.metrics.total_cpu_usage_percent = sum(o.cpu_usage for o in self.orchestrators.values())
    
    async def _detect_cross_project_patterns(self) -> None:
        """Detect patterns that could be shared across projects"""
        # Placeholder for cross-project intelligence
        pass
    
    async def _optimize_project_scheduling(self) -> None:
        """Optimize scheduling across projects"""
        # Placeholder for intelligent scheduling
        pass
    
    async def _handle_project_dependencies(self) -> None:
        """Handle inter-project dependencies"""
        # Placeholder for dependency coordination
        pass
    
    async def _rebalance_resources(self) -> None:
        """Rebalance resources across projects"""
        # Placeholder for dynamic resource rebalancing
        pass
    
    async def _check_orchestrator_health(self) -> None:
        """Check health of all orchestrators"""
        current_time = datetime.utcnow()
        
        for name, orchestrator in self.orchestrators.items():
            if orchestrator.status == OrchestratorStatus.RUNNING:
                # Check for heartbeat timeout
                if orchestrator.last_heartbeat:
                    time_since_heartbeat = current_time - orchestrator.last_heartbeat
                    if time_since_heartbeat > timedelta(minutes=5):
                        logger.warning(f"No heartbeat from project '{name}' for {time_since_heartbeat}")
    
    async def _restart_failed_orchestrators(self) -> None:
        """Restart orchestrators that have failed"""
        for name, orchestrator in self.orchestrators.items():
            if orchestrator.status == OrchestratorStatus.CRASHED:
                if orchestrator.restart_count < 3:  # Max 3 restart attempts
                    logger.info(f"Attempting to restart crashed orchestrator for '{name}'")
                    orchestrator.restart_count += 1
                    await self.stop_project(name)
                    await asyncio.sleep(5)  # Wait before restart
                    await self.start_project(name)
    
    async def _dispatch_task(self, task: Task, project: Project) -> AgentResult:
        """Dispatch task to appropriate agent"""
        agent = self._get_agent_for_project(task.agent_type, project)
        if not agent:
            return AgentResult(
                success=False,
                output="",
                error=f"Agent not available: {task.agent_type}"
            )
        
        # Check orchestration mode
        if project.orchestration_mode == OrchestrationMode.BLOCKING:
            # Add to approval queue
            approval_request = ApprovalRequest(
                id=task.id,
                project_name=project.name,
                task=task,
                reason="Blocking mode requires approval",
                created_at=datetime.now()
            )
            self.approval_queue.append(approval_request)
            project.pending_approvals.append(task.id)
            
            return AgentResult(
                success=True,
                output=f"Task queued for approval: {task.id}"
            )
        
        elif project.orchestration_mode == OrchestrationMode.PARTIAL:
            # Execute but quarantine output
            # Placeholder for agent execution
            return AgentResult(
                success=True,
                output="Task executed in quarantine mode"
            )
        
        else:  # AUTONOMOUS
            # Execute directly
            # Placeholder for agent execution
            return AgentResult(
                success=True,
                output="Task executed autonomously"
            )
    
    async def _process_project_tasks(self, project: Project) -> None:
        """Background task processing for a project"""
        while project.active_tasks:
            for task in project.active_tasks[:]:  # Copy list to avoid modification during iteration
                if task.status == "PENDING":
                    result = await self._dispatch_task(task, project)
                    if result.success and task.status == "COMPLETED":
                        project.active_tasks.remove(task)
                        
            await asyncio.sleep(1)  # Prevent busy waiting
            self._save_project_state(project)
    
    async def _save_state(self) -> None:
        """Save current orchestrator state."""
        for project_name, project_data in self.projects.items():
            self._save_project_state(project_data)
    
    async def get_global_status(self) -> Dict[str, Any]:
        """Get comprehensive global orchestration status"""
        await self._collect_metrics()
        
        return {
            "global_orchestrator": {
                "status": self.status.value,
                "mode": self.mode,
                "uptime_seconds": (datetime.utcnow() - self.start_time).total_seconds() if self.start_time else 0,
                "configuration": {
                    "max_total_agents": self.global_config["max_total_agents"],
                    "max_concurrent_projects": self.global_config["max_concurrent_projects"],
                    "resource_allocation_strategy": self.global_config["resource_allocation_strategy"]
                }
            },
            "projects": {
                name: {
                    "status": orch.status.value if name in self.orchestrators else "stopped",
                    "orchestration_mode": project.orchestration_mode.value,
                    "priority": project.priority.value,
                    "active_tasks": len(project.active_tasks),
                    "pending_approvals": len(project.pending_approvals)
                }
                for name, project in self.projects.items()
                for orch in [self.orchestrators.get(name, ProjectOrchestrator("", ""))]
            },
            "resource_allocations": {
                name: {
                    "allocated_agents": alloc.allocated_agents,
                    "allocated_memory_mb": alloc.allocated_memory_mb,
                    "allocated_cpu_percent": alloc.allocated_cpu_percent,
                    "priority_weight": alloc.priority_weight
                }
                for name, alloc in self.resource_allocations.items()
            },
            "global_metrics": {
                "total_projects": self.metrics.total_projects,
                "active_projects": self.metrics.active_projects,
                "total_agents": self.metrics.total_agents,
                "total_memory_usage_mb": self.metrics.total_memory_usage_mb,
                "total_cpu_usage_percent": self.metrics.total_cpu_usage_percent,
                "total_stories_in_progress": self.metrics.total_stories_in_progress,
                "total_stories_completed": self.metrics.total_stories_completed,
                "average_cycle_time_hours": self.metrics.average_cycle_time_hours,
                "cross_project_insights": self.metrics.cross_project_insights,
                "resource_efficiency": self.metrics.resource_efficiency
            },
            "cross_project_insights": self.cross_project_insights[-10:],  # Last 10 insights
            "shared_patterns": len(self.shared_patterns)
        }
    
    def get_status(self) -> Dict[str, Any]:
        """Get current orchestrator status."""
        return {
            "running": self.running,
            "status": self.status.value,
            "mode": self.mode,
            "projects": {
                name: {
                    "state": "RUNNING" if name in self.orchestrators else "STOPPED",
                    "mode": project.orchestration_mode.value,
                    "priority": project.priority.value,
                    "active_tasks": len(project.active_tasks),
                    "pending_approvals": len(project.pending_approvals)
                }
                for name, project in self.projects.items()
            },
            "timestamp": datetime.now().isoformat()
        }
    
    async def register_project(self, project_config: Dict[str, Any]) -> None:
        """Register a new project with the orchestrator."""
        project_name = project_config["name"]
        logger.info(f"Registering project: {project_name}")
        
        project_path = Path(project_config["path"])
        orchestration_mode = OrchestrationMode(project_config.get("orchestration", "blocking"))
        priority = ProjectPriority(project_config.get("priority", "normal"))
        
        # Create project with state machine and storage
        storage = ProjectStorage(str(project_path))
        
        # Parse resource limits
        resource_config = project_config.get("resources", {})
        resource_limits = ResourceLimits(
            max_parallel_agents=resource_config.get("max_parallel_agents", 3),
            max_memory_mb=resource_config.get("max_memory_mb", 2048),
            cpu_priority=resource_config.get("cpu_priority", 1.0)
        )
        
        project = Project(
            name=project_name,
            path=project_path,
            orchestration_mode=orchestration_mode,
            priority=priority,
            state_machine=StateMachine(),
            tdd_state_machine=TDDStateMachine(),
            active_tasks=[],
            pending_approvals=[],
            storage=storage,
            discord_channel=project_config.get("discord_channel"),
            resource_limits=resource_limits
        )
        
        self.projects[project_name] = project
    
    async def unregister_project(self, project_name: str) -> None:
        """Unregister a project from the orchestrator."""
        if project_name in self.projects:
            logger.info(f"Unregistering project: {project_name}")
            
            # Stop project if running
            if project_name in self.orchestrators:
                await self.stop_project(project_name)
            
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
        return await self.handle_command(command, project_name, **kwargs)
    
    # State broadcaster integration methods
    
    async def _start_state_broadcaster(self, port: int = 8080) -> None:
        """Start the state broadcaster WebSocket server."""
        try:
            # Import the state broadcaster - try multiple import strategies
            import sys
            from pathlib import Path
            
            # Add lib to path for state broadcaster import
            lib_path = Path(__file__).parent.parent.parent / "lib"
            if str(lib_path) not in sys.path:
                sys.path.insert(0, str(lib_path))
            
            # Try different import paths
            StatebroadCaster = None
            try:
                from lib.state_broadcaster import StatebroadCaster
            except ImportError:
                try:
                    import state_broadcaster
                    StatebroadCaster = state_broadcaster.StatebroadCaster
                except ImportError:
                    # Try relative import from current directory
                    import importlib.util
                    spec = importlib.util.spec_from_file_location("state_broadcaster", lib_path / "state_broadcaster.py")
                    if spec and spec.loader:
                        module = importlib.util.module_from_spec(spec)
                        spec.loader.exec_module(module)
                        StatebroadCaster = module.StatebroadCaster
            
            if not StatebroadCaster:
                raise ImportError("Could not import StatebroadCaster from any location")
            
            # Initialize broadcaster instance
            self.state_broadcaster = StatebroadCaster()
            
            # Start the WebSocket server
            await self.state_broadcaster.start_server(port)
            logger.info(f"State broadcaster WebSocket server started on port {port}")
            
        except ImportError as e:
            logger.warning(f"State broadcaster not available: {e}")
            self.state_broadcaster = None
        except Exception as e:
            logger.error(f"Failed to start state broadcaster: {e}")
            self.state_broadcaster = None
    
    async def _stop_state_broadcaster(self) -> None:
        """Stop the state broadcaster WebSocket server."""
        if self.state_broadcaster:
            try:
                await self.state_broadcaster.stop_server()
                logger.info("State broadcaster stopped")
            except Exception as e:
                logger.error(f"Error stopping state broadcaster: {e}")
            finally:
                self.state_broadcaster = None
    
    async def _broadcast_state_transition(self, old_state, new_state, project_name: str = "default") -> None:
        """Broadcast state transition to connected clients."""
        if self.state_broadcaster:
            try:
                self.state_broadcaster.emit_workflow_transition(old_state, new_state, project_name)
            except Exception as e:
                logger.error(f"Error broadcasting state transition: {e}")
    
    async def _broadcast_tdd_transition(self, story_id: str, old_state, new_state, project_name: str = "default", cycle_id: str = None) -> None:
        """Broadcast TDD state transition to connected clients."""
        if self.state_broadcaster:
            try:
                self.state_broadcaster.emit_tdd_transition(story_id, old_state, new_state, project_name, cycle_id)
            except Exception as e:
                logger.error(f"Error broadcasting TDD transition: {e}")
    
    async def _broadcast_agent_activity(self, agent_type: str, story_id: str, action: str, status: str, project_name: str = "default") -> None:
        """Broadcast agent activity to connected clients."""
        if self.state_broadcaster:
            try:
                self.state_broadcaster.emit_agent_activity(agent_type, story_id, action, status, project_name)
            except Exception as e:
                logger.error(f"Error broadcasting agent activity: {e}")


async def main():
    """Main entry point"""
    orchestrator = Orchestrator()
    
    # Run orchestrator with state broadcaster
    try:
        await orchestrator.run()
    except KeyboardInterrupt:
        logger.info("Shutting down gracefully...")
    finally:
        await orchestrator.stop()


if __name__ == "__main__":
    asyncio.run(main())