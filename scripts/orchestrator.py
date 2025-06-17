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