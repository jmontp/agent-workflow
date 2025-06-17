#!/usr/bin/env python3
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
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from enum import Enum

# Add lib directory to Python path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "lib"))

from state_machine import StateMachine, State, CommandResult
from agents import create_agent, get_available_agents, Task, TaskStatus, AgentResult
from project_storage import ProjectStorage
from data_models import ProjectData, Epic, Story, Sprint, EpicStatus, StoryStatus, SprintStatus
from tdd_state_machine import TDDStateMachine, TDDCommandResult
from tdd_models import TDDCycle, TDDTask, TDDState, TestResult, TestStatus

logger = logging.getLogger(__name__)


class OrchestrationMode(Enum):
    """Project orchestration modes"""
    BLOCKING = "blocking"      # Requires human approval
    PARTIAL = "partial"        # Quarantined output
    AUTONOMOUS = "autonomous"  # Full execution


@dataclass
class Project:
    """Project configuration and state"""
    name: str
    path: Path
    orchestration_mode: OrchestrationMode
    state_machine: StateMachine
    tdd_state_machine: TDDStateMachine
    active_tasks: List[Task]
    pending_approvals: List[str]
    storage: ProjectStorage
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert project to dictionary for serialization"""
        return {
            "name": self.name,
            "path": str(self.path),
            "orchestration_mode": self.orchestration_mode.value,
            "current_state": self.state_machine.current_state.value,
            "active_tasks": [asdict(task) for task in self.active_tasks],
            "pending_approvals": self.pending_approvals
        }


@dataclass
class ApprovalRequest:
    """Request for human approval"""
    id: str
    project_name: str
    task: Task
    reason: str
    created_at: datetime
    retry_count: int = 0


class Orchestrator:
    """
    Central orchestration engine for AI Agent TDD-Scrum workflow.
    
    Manages multiple projects, coordinates agents, enforces state machine,
    and implements Human-In-The-Loop approval workflows.
    """
    
    def __init__(self, config_path: str = "config/projects.yaml"):
        self.config_path = Path(config_path)
        self.projects: Dict[str, Project] = {}
        self.agents: Dict[str, Any] = {}
        self.approval_queue: List[ApprovalRequest] = []
        self.running = False
        
        # Initialize logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
        # Load configuration and initialize
        self._load_configuration()
        self._initialize_agents()
        self._load_project_states()
        
        logger.info("Orchestrator initialized successfully")
    
    def _load_configuration(self) -> None:
        """Load project configurations from YAML file"""
        try:
            if self.config_path.exists():
                with open(self.config_path, 'r') as f:
                    config = yaml.safe_load(f)
                    
                for project_config in config.get("projects", []):
                    project_name = project_config["name"]
                    project_path = Path(project_config["path"])
                    orchestration_mode = OrchestrationMode(project_config.get("orchestration", "blocking"))
                    
                    # Create project with state machine and storage
                    storage = ProjectStorage(str(project_path))
                    project = Project(
                        name=project_name,
                        path=project_path,
                        orchestration_mode=orchestration_mode,
                        state_machine=StateMachine(),
                        tdd_state_machine=TDDStateMachine(),
                        active_tasks=[],
                        pending_approvals=[],
                        storage=storage
                    )
                    
                    self.projects[project_name] = project
                    logger.info(f"Loaded project: {project_name} ({orchestration_mode.value})")
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
        default_project = Project(
            name="default",
            path=Path("."),
            orchestration_mode=OrchestrationMode.BLOCKING,
            state_machine=StateMachine(),
            tdd_state_machine=TDDStateMachine(),
            active_tasks=[],
            pending_approvals=[],
            storage=storage
        )
        self.projects["default"] = default_project
        logger.info("Created default project")
    
    def _initialize_agents(self) -> None:
        """Initialize AI agents"""
        try:
            available_agents = get_available_agents()
            for agent_type in available_agents:
                agent = create_agent(agent_type)
                self.agents[agent_type] = agent
                logger.info(f"Initialized agent: {agent_type}")
                
        except Exception as e:
            logger.error(f"Failed to initialize agents: {e}")
    
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
                        
                    # Restore active tasks
                    for task_data in state_data.get("active_tasks", []):
                        task = Task(
                            id=task_data["id"],
                            agent_type=task_data["agent_type"],
                            command=task_data["command"],
                            context=task_data.get("context", {}),
                            status=TaskStatus(task_data["status"])
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
                project.state_machine.current_state = validation_result.new_state
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
            
            # TODO: Use DesignAgent to decompose epic into stories
            design_agent = self.agents.get("DesignAgent")
            if design_agent:
                task = Task(
                    id=f"epic-{datetime.now().timestamp()}",
                    agent_type="DesignAgent",
                    command=f"Decompose epic into user stories: {description}",
                    context={"epic_id": new_epic.id, "epic_description": description}
                )
                
                result = await self._dispatch_task(task, project)
                if result.success:
                    return {
                        "success": True,
                        "message": f"Epic {new_epic.id} created: {new_epic.title}",
                        "epic_id": new_epic.id,
                        "title": new_epic.title,
                        "description": new_epic.description,
                        "next_step": "DesignAgent will propose user stories for approval"
                    }
            
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
        completed_tasks = len([t for t in project.active_tasks if t.status == TaskStatus.COMPLETED])
        failed_tasks = len([t for t in project.active_tasks if t.status == TaskStatus.FAILED])
        
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
        # TODO: Implement task pausing logic
        return {
            "success": True,
            "message": "Sprint paused - agent work halted",
            "next_step": "Use /sprint resume to continue"
        }
    
    def _resume_sprint(self, project: Project) -> Dict[str, Any]:
        """Resume sprint execution"""
        # TODO: Implement task resumption logic
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
    
    def _handle_tdd_status(self, project: Project, story_id: str = "", **kwargs) -> Dict[str, Any]:
        """Handle /tdd status command"""
        try:
            if story_id:
                # Get status for specific story
                project_data = project.storage.load_project_data()
                story = project_data.get_story_by_id(story_id)
                if not story:
                    return {
                        "success": False,
                        "error": f"Story not found: {story_id}"
                    }
                
                if story.tdd_cycle_id:
                    cycle = project.storage.load_tdd_cycle(story.tdd_cycle_id)
                    if cycle:
                        project.tdd_state_machine.set_active_cycle(cycle)
                        state_info = project.tdd_state_machine.get_state_info()
                        
                        return {
                            "success": True,
                            "cycle_info": cycle.get_progress_summary(),
                            "allowed_commands": state_info["allowed_commands"],
                            "next_suggested": state_info["next_suggested"],
                            "current_state": cycle.current_state.value
                        }
                
                return {
                    "success": True,
                    "message": f"No TDD cycle for story {story_id}",
                    "allowed_commands": [f"/tdd start {story_id}"]
                }
            
            # Get status for active cycle
            active_cycle = project.storage.get_active_tdd_cycle()
            
            if not active_cycle:
                return {
                    "success": True,
                    "message": "No active TDD cycle",
                    "allowed_commands": ["/tdd start <story_id>"]
                }
            
            # Get TDD state machine info
            project.tdd_state_machine.set_active_cycle(active_cycle)
            state_info = project.tdd_state_machine.get_state_info()
            
            return {
                "success": True,
                "cycle_info": active_cycle.get_progress_summary(),
                "allowed_commands": state_info["allowed_commands"],
                "next_suggested": state_info["next_suggested"],
                "current_state": active_cycle.current_state.value
            }
            
        except Exception as e:
            logger.error(f"Error getting TDD status: {e}")
            return {
                "success": False,
                "error": f"Failed to get TDD status: {e}"
            }
    
    async def _handle_tdd_next(self, project: Project, **kwargs) -> Dict[str, Any]:
        """Handle /tdd next command - auto-advance to next logical state"""
        try:
            active_cycle = project.storage.get_active_tdd_cycle()
            if not active_cycle:
                return {
                    "success": False,
                    "error": "No active TDD cycle",
                    "hint": "Start a TDD cycle with /tdd start <story_id>"
                }
            
            project.tdd_state_machine.set_active_cycle(active_cycle)
            
            # Validate and transition
            result = project.tdd_state_machine.transition("/tdd next")
            
            if result.success:
                # Save updated cycle
                project.storage.save_tdd_cycle(active_cycle)
                
                # Update story status
                project_data = project.storage.load_project_data()
                story = project_data.get_story_by_id(active_cycle.story_id)
                if story:
                    story.test_status = active_cycle.current_state.value
                    project.storage.save_project_data(project_data)
                
                return {
                    "success": True,
                    "message": f"Advanced to {active_cycle.current_state.value}",
                    "current_state": active_cycle.current_state.value,
                    "next_suggested": project.tdd_state_machine.get_next_suggested_command()
                }
            else:
                return {
                    "success": False,
                    "error": result.error_message,
                    "hint": result.hint,
                    "current_state": active_cycle.current_state.value,
                    "allowed_commands": project.tdd_state_machine.get_allowed_commands()
                }
                
        except Exception as e:
            logger.error(f"Error in TDD next: {e}")
            return {
                "success": False,
                "error": f"Failed to advance TDD state: {e}"
            }
    
    async def _handle_tdd_abort(self, project: Project, story_id: str = "", **kwargs) -> Dict[str, Any]:
        """Handle /tdd abort command"""
        try:
            if story_id:
                # Abort specific story's TDD cycle
                project_data = project.storage.load_project_data()
                story = project_data.get_story_by_id(story_id)
                if not story:
                    return {
                        "success": False,
                        "error": f"Story not found: {story_id}"
                    }
                
                if not story.tdd_cycle_id:
                    return {
                        "success": False,
                        "error": f"No TDD cycle found for story {story_id}"
                    }
                
                cycle = project.storage.load_tdd_cycle(story.tdd_cycle_id)
                if not cycle or cycle.is_complete():
                    return {
                        "success": False,
                        "error": f"No active TDD cycle for story {story_id}"
                    }
                
                # Mark cycle as complete (aborted)
                cycle.completed_at = datetime.now().isoformat()
                cycle.current_state = TDDState.COMMIT
                
                # Update story
                story.test_status = "aborted"
                project.storage.save_project_data(project_data)
                project.storage.save_tdd_cycle(cycle)
                
                return {
                    "success": True,
                    "message": f"TDD cycle {cycle.id} for story {story_id} aborted",
                    "next_step": "Start a new TDD cycle with /tdd start <story_id>"
                }
            
            # Abort active cycle
            active_cycle = project.storage.get_active_tdd_cycle()
            if not active_cycle:
                return {
                    "success": False,
                    "error": "No active TDD cycle to abort"
                }
            
            # Mark cycle as complete (aborted)
            active_cycle.completed_at = datetime.now().isoformat()
            active_cycle.current_state = TDDState.COMMIT
            
            # Update story
            project_data = project.storage.load_project_data()
            story = project_data.get_story_by_id(active_cycle.story_id)
            if story:
                story.test_status = "aborted"
                project.storage.save_project_data(project_data)
            
            # Save cycle and reset state machine
            project.storage.save_tdd_cycle(active_cycle)
            project.tdd_state_machine.reset()
            
            return {
                "success": True,
                "message": f"TDD cycle {active_cycle.id} aborted",
                "next_step": "Start a new TDD cycle with /tdd start <story_id>"
            }
            
        except Exception as e:
            logger.error(f"Error aborting TDD cycle: {e}")
            return {
                "success": False,
                "error": f"Failed to abort TDD cycle: {e}"
            }
    
    async def _handle_tdd_transition(self, action: str, project: Project, **kwargs) -> Dict[str, Any]:
        """Handle TDD state transition commands"""
        try:
            active_cycle = project.storage.get_active_tdd_cycle()
            if not active_cycle:
                return {
                    "success": False,
                    "error": "No active TDD cycle",
                    "hint": "Start a TDD cycle with /tdd start <story_id>"
                }
            
            project.tdd_state_machine.set_active_cycle(active_cycle)
            command = f"/tdd {action}"
            
            # Validate and transition
            result = project.tdd_state_machine.transition(command)
            
            if result.success:
                # Handle specific actions
                if action == "run_tests":
                    # Increment test run counter
                    active_cycle.total_test_runs += 1
                elif action == "refactor":
                    # Increment refactor counter
                    active_cycle.total_refactors += 1
                elif action == "commit":
                    # Complete current task or cycle
                    if active_cycle.get_current_task():
                        active_cycle.complete_current_task()
                
                # Save updated cycle
                project.storage.save_tdd_cycle(active_cycle)
                
                # Update story status
                project_data = project.storage.load_project_data()
                story = project_data.get_story_by_id(active_cycle.story_id)
                if story:
                    story.test_status = active_cycle.current_state.value
                    project.storage.save_project_data(project_data)
                
                return {
                    "success": True,
                    "message": f"TDD {action} completed",
                    "current_state": active_cycle.current_state.value,
                    "next_suggested": project.tdd_state_machine.get_next_suggested_command()
                }
            else:
                return {
                    "success": False,
                    "error": result.error_message,
                    "hint": result.hint,
                    "current_state": active_cycle.current_state.value,
                    "allowed_commands": project.tdd_state_machine.get_allowed_commands()
                }
                
        except Exception as e:
            logger.error(f"Error in TDD {action}: {e}")
            return {
                "success": False,
                "error": f"Failed to execute TDD {action}: {e}"
            }
    
    def _handle_tdd_logs(self, project: Project, story_id: str = "", **kwargs) -> Dict[str, Any]:
        """Handle /tdd logs command - show TDD cycle logs and metrics"""
        try:
            if story_id:
                # Get logs for specific story
                project_data = project.storage.load_project_data()
                story = project_data.get_story_by_id(story_id)
                if not story:
                    return {
                        "success": False,
                        "error": f"Story not found: {story_id}"
                    }
                
                if not story.tdd_cycle_id:
                    return {
                        "success": True,
                        "message": f"No TDD cycle logs for story {story_id}",
                        "logs_info": {}
                    }
                
                cycle = project.storage.load_tdd_cycle(story.tdd_cycle_id)
                if not cycle:
                    return {
                        "success": True,
                        "message": f"TDD cycle not found for story {story_id}",
                        "logs_info": {}
                    }
                
                # Generate logs info for specific cycle
                logs_info = {
                    "cycle_id": cycle.id,
                    "story_id": cycle.story_id,
                    "total_events": len(cycle.tasks) + cycle.total_test_runs + cycle.total_commits,
                    "last_activity": cycle.completed_at or "In progress",
                    "recent_events": [
                        f"Started cycle at {cycle.started_at}",
                        f"Total test runs: {cycle.total_test_runs}",
                        f"Total refactors: {cycle.total_refactors}",
                        f"Total commits: {cycle.total_commits}",
                        f"Current state: {cycle.current_state.value}"
                    ]
                }
                
                return {
                    "success": True,
                    "logs_info": logs_info
                }
            
            # Get logs for active cycle
            active_cycle = project.storage.get_active_tdd_cycle()
            if not active_cycle:
                return {
                    "success": True,
                    "message": "No active TDD cycle logs",
                    "logs_info": {}
                }
            
            # Generate logs info for active cycle
            logs_info = {
                "cycle_id": active_cycle.id,
                "story_id": active_cycle.story_id,
                "total_events": len(active_cycle.tasks) + active_cycle.total_test_runs + active_cycle.total_commits,
                "last_activity": "In progress",
                "recent_events": [
                    f"Started cycle at {active_cycle.started_at}",
                    f"Total test runs: {active_cycle.total_test_runs}",
                    f"Total refactors: {active_cycle.total_refactors}",
                    f"Total commits: {active_cycle.total_commits}",
                    f"Current state: {active_cycle.current_state.value}"
                ]
            }
            
            return {
                "success": True,
                "logs_info": logs_info
            }
            
        except Exception as e:
            logger.error(f"Error getting TDD logs: {e}")
            return {
                "success": False,
                "error": f"Failed to get TDD logs: {e}"
            }
    
    def _handle_tdd_overview(self, project: Project) -> Dict[str, Any]:
        """Handle /tdd overview command - dashboard view of all TDD cycles"""
        try:
            project_data = project.storage.load_project_data()
            
            # Get all TDD cycle files
            cycle_files = project.storage.list_tdd_cycle_files()
            
            active_cycles = 0
            completed_cycles = 0
            total_test_runs = 0
            total_refactors = 0
            total_commits = 0
            total_coverage = 0.0
            coverage_count = 0
            active_stories = []
            
            for cycle_id in cycle_files:
                cycle = project.storage.load_tdd_cycle(cycle_id)
                if cycle:
                    if cycle.is_complete():
                        completed_cycles += 1
                    else:
                        active_cycles += 1
                        # Find story for this cycle
                        story = project_data.get_story_by_id(cycle.story_id)
                        if story:
                            active_stories.append(f"{story.id}: {story.title[:30]}...")
                    
                    total_test_runs += cycle.total_test_runs
                    total_refactors += cycle.total_refactors
                    total_commits += cycle.total_commits
                    
                    if cycle.overall_test_coverage > 0:
                        total_coverage += cycle.overall_test_coverage
                        coverage_count += 1
            
            # Calculate metrics
            average_coverage = total_coverage / coverage_count if coverage_count > 0 else 0.0
            success_rate = (completed_cycles / (active_cycles + completed_cycles) * 100) if (active_cycles + completed_cycles) > 0 else 0.0
            
            overview_info = {
                "active_cycles": active_cycles,
                "completed_cycles": completed_cycles,
                "total_test_runs": total_test_runs,
                "total_refactors": total_refactors,
                "total_commits": total_commits,
                "average_coverage": average_coverage,
                "success_rate": success_rate,
                "active_stories": active_stories[:5]  # Limit to 5 most recent
            }
            
            return {
                "success": True,
                "overview_info": overview_info
            }
            
        except Exception as e:
            logger.error(f"Error getting TDD overview: {e}")
            return {
                "success": False,
                "error": f"Failed to get TDD overview: {e}"
            }
    
    async def _dispatch_task(self, task: Task, project: Project) -> AgentResult:
        """Dispatch task to appropriate agent"""
        agent = self.agents.get(task.agent_type)
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
            result = await agent._execute_with_retry(task, dry_run=True)
            return result
        
        else:  # AUTONOMOUS
            # Execute directly
            result = await agent._execute_with_retry(task, dry_run=False)
            return result
    
    async def _coordinate_tdd_agent_handoff(self, project: Project, from_state: str, to_state: str, cycle_id: str) -> Dict[str, Any]:
        """Coordinate agent handoffs during TDD state transitions"""
        try:
            # Define which agents handle which TDD states
            state_agents = {
                "design": "DesignAgent",
                "test_red": "QAAgent", 
                "code_green": "CodeAgent",
                "refactor": "CodeAgent",
                "commit": "CodeAgent"
            }
            
            from_agent = state_agents.get(from_state)
            to_agent = state_agents.get(to_state)
            
            if from_agent == to_agent:
                return {"success": True, "message": "No agent handoff needed"}
            
            # Load cycle context
            cycle = project.storage.load_tdd_cycle(cycle_id)
            if not cycle:
                return {"success": False, "error": "TDD cycle not found"}
            
            current_task = cycle.get_current_task()
            if not current_task:
                return {"success": False, "error": "No current task in TDD cycle"}
            
            # Create handoff context
            handoff_context = {
                "cycle_id": cycle_id,
                "story_id": cycle.story_id,
                "task_id": current_task.id,
                "from_state": from_state,
                "to_state": to_state,
                "task_description": current_task.description,
                "test_files": current_task.test_files,
                "source_files": current_task.source_files
            }
            
            # Queue task for new agent
            if to_agent and to_agent in self.agents:
                task = Task(
                    id=f"tdd-{to_state}-{datetime.now().timestamp()}",
                    agent_type=to_agent,
                    command=f"Continue TDD cycle in {to_state} state",
                    context=handoff_context
                )
                
                project.active_tasks.append(task)
                self._save_project_state(project)
                
                return {
                    "success": True,
                    "message": f"TDD handoff: {from_agent} → {to_agent}",
                    "task_id": task.id
                }
            
            return {"success": True, "message": "TDD transition completed"}
            
        except Exception as e:
            logger.error(f"Error in TDD agent handoff: {e}")
            return {"success": False, "error": str(e)}
    
    async def _monitor_tdd_resource_usage(self, project: Project) -> Dict[str, Any]:
        """Monitor and manage TDD cycle resource usage"""
        try:
            # Get all active TDD cycles
            cycle_files = project.storage.list_tdd_cycle_files()
            active_cycles = []
            
            for cycle_id in cycle_files:
                cycle = project.storage.load_tdd_cycle(cycle_id)
                if cycle and not cycle.is_complete():
                    active_cycles.append(cycle)
            
            # Check resource limits
            max_concurrent_cycles = 3  # Configurable limit
            if len(active_cycles) > max_concurrent_cycles:
                return {
                    "success": False,
                    "error": f"Too many active TDD cycles ({len(active_cycles)}). Maximum allowed: {max_concurrent_cycles}",
                    "hint": "Complete or abort some cycles before starting new ones"
                }
            
            # Monitor agent workload
            active_tdd_tasks = [t for t in project.active_tasks if "tdd" in t.command.lower()]
            
            resource_info = {
                "active_cycles": len(active_cycles),
                "max_cycles": max_concurrent_cycles,
                "active_tdd_tasks": len(active_tdd_tasks),
                "cycles_info": [
                    {
                        "id": cycle.id,
                        "story_id": cycle.story_id,
                        "state": cycle.current_state.value,
                        "started_at": cycle.started_at
                    }
                    for cycle in active_cycles
                ]
            }
            
            return {
                "success": True,
                "resource_info": resource_info
            }
            
        except Exception as e:
            logger.error(f"Error monitoring TDD resources: {e}")
            return {"success": False, "error": str(e)}
    
    async def _handle_tdd_failure_recovery(self, project: Project, cycle_id: str, error_info: Dict[str, Any]) -> Dict[str, Any]:
        """Handle TDD cycle failures and implement recovery workflows"""
        try:
            cycle = project.storage.load_tdd_cycle(cycle_id)
            if not cycle:
                return {"success": False, "error": "TDD cycle not found"}
            
            # Determine recovery strategy based on error type
            error_type = error_info.get("type", "unknown")
            retry_count = error_info.get("retry_count", 0)
            max_retries = 3
            
            if retry_count >= max_retries:
                # Escalate to human after max retries
                approval_request = ApprovalRequest(
                    id=f"tdd-failure-{cycle_id}",
                    project_name=project.name,
                    task=Task(
                        id=f"tdd-recovery-{cycle_id}",
                        agent_type="Orchestrator",
                        command=f"TDD cycle {cycle_id} requires human intervention",
                        context={"cycle_id": cycle_id, "error_info": error_info}
                    ),
                    reason=f"TDD cycle failed after {retry_count} retries: {error_type}",
                    created_at=datetime.now(),
                    retry_count=retry_count
                )
                
                self.approval_queue.append(approval_request)
                project.pending_approvals.append(approval_request.id)
                
                return {
                    "success": True,
                    "message": f"TDD failure escalated to human review: {approval_request.id}",
                    "recovery_action": "human_intervention"
                }
            
            # Implement automatic recovery strategies
            recovery_actions = {
                "test_failure": "Revert to last known good state and retry",
                "build_failure": "Check dependencies and retry",
                "timeout": "Increase timeout and retry",
                "agent_error": "Reset agent state and retry"
            }
            
            recovery_action = recovery_actions.get(error_type, "Generic retry")
            
            # Update error info for retry
            error_info["retry_count"] = retry_count + 1
            error_info["recovery_action"] = recovery_action
            
            return {
                "success": True,
                "message": f"TDD recovery initiated: {recovery_action}",
                "recovery_action": recovery_action,
                "retry_count": retry_count + 1
            }
            
        except Exception as e:
            logger.error(f"Error in TDD failure recovery: {e}")
            return {"success": False, "error": str(e)}
    
    async def _process_project_tasks(self, project: Project) -> None:
        """Background task processing for a project"""
        while project.active_tasks:
            for task in project.active_tasks[:]:  # Copy list to avoid modification during iteration
                if task.status == TaskStatus.PENDING:
                    result = await self._dispatch_task(task, project)
                    if result.success and task.status == TaskStatus.COMPLETED:
                        project.active_tasks.remove(task)
                        
            await asyncio.sleep(1)  # Prevent busy waiting
            self._save_project_state(project)
    
    async def run(self) -> None:
        """Main orchestrator event loop"""
        self.running = True
        logger.info("Orchestrator starting main event loop")
        
        try:
            while self.running:
                # Process all projects
                for project in self.projects.values():
                    await self._reconcile_project(project)
                
                # Process approval queue
                await self._process_approval_queue()
                
                await asyncio.sleep(5)  # Main loop interval
                
        except KeyboardInterrupt:
            logger.info("Orchestrator stopping...")
        finally:
            self.running = False
            logger.info("Orchestrator stopped")
    
    async def _reconcile_project(self, project: Project) -> None:
        """Reconcile project state and progress tasks"""
        # Auto-progress certain states
        if project.state_machine.can_auto_progress():
            # Continue processing active tasks
            if project.active_tasks:
                await self._process_project_tasks(project)
        
        # Check for state transitions
        if project.state_machine.current_state == State.SPRINT_ACTIVE:
            completed_tasks = [t for t in project.active_tasks if t.status == TaskStatus.COMPLETED]
            if len(completed_tasks) == len(project.active_tasks) and project.active_tasks:
                # All tasks complete - transition to review
                project.state_machine.force_state(State.SPRINT_REVIEW)
                logger.info(f"Project {project.name} transitioned to SPRINT_REVIEW")
                self._save_project_state(project)
    
    async def _process_approval_queue(self) -> None:
        """Process pending approval requests"""
        # TODO: Implement approval timeout and escalation logic
        pass
    
    def stop(self) -> None:
        """Stop the orchestrator"""
        self.running = False


async def main():
    """Main entry point"""
    orchestrator = Orchestrator()
    
    # Run orchestrator
    try:
        await orchestrator.run()
    except KeyboardInterrupt:
        logger.info("Shutting down gracefully...")
    finally:
        orchestrator.stop()


if __name__ == "__main__":
    asyncio.run(main())