"""
AI Agent Library for TDD-Scrum Workflow

This module provides the base agent interface and specialized agent implementations
for coordinating software development tasks through AI assistance.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass
from enum import Enum
import logging
import asyncio
import time
from datetime import datetime
import json

# Import TDD models for type hints
try:
    from ..core.models import TDDState, TDDCycle, TDDTask, TestResult, TestFileStatus
    from ..core.state_machine import TDDStateMachine, TDDCommandResult
except ImportError:
    from agent_workflow.core.models import TDDState, TDDCycle, TDDTask, TestResult, TestFileStatus
    from agent_workflow.core.state_machine import TDDStateMachine, TDDCommandResult

logger = logging.getLogger(__name__)


class TaskStatus(Enum):
    """Status of agent tasks"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress" 
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class Task:
    """Task specification for agent execution"""
    id: str
    agent_type: str
    command: str
    context: Dict[str, Any]
    status: TaskStatus = TaskStatus.PENDING
    retry_count: int = 0
    max_retries: int = 3
    created_at: datetime = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.utcnow()


@dataclass 
class AgentResult:
    """Result of agent task execution"""
    success: bool
    output: str
    artifacts: Dict[str, str] = None  # Files created/modified
    error: Optional[str] = None
    execution_time: float = 0.0
    
    def __post_init__(self):
        if self.artifacts is None:
            self.artifacts = {}


class BaseAgent(ABC):
    """
    Abstract base class for all AI agents.
    
    Provides common interface and functionality for task execution,
    error handling, and integration with the orchestrator.
    Enhanced with TDD context awareness and workflow integration.
    """
    
    def __init__(self, name: str, capabilities: List[str], context_manager: Optional[Any] = None):
        self.name = name
        self.capabilities = capabilities
        self.task_history: List[Task] = []
        self.logger = logging.getLogger(f"agent.{name}")
        
        # TDD context
        self.tdd_state_machine: Optional[TDDStateMachine] = None
        self.current_tdd_cycle: Optional[TDDCycle] = None
        self.current_tdd_task: Optional[TDDTask] = None
        
        # Context management
        self.context_manager = context_manager
        self._current_context: Optional[Any] = None  # Will store AgentContext when available
        
    @abstractmethod
    async def run(self, task: Task, dry_run: bool = False) -> AgentResult:
        """
        Execute a task assigned to this agent.
        
        Args:
            task: Task specification to execute
            dry_run: If True, simulate execution without making changes
            
        Returns:
            AgentResult with execution outcome
        """
        pass
    
    def validate_task(self, task: Task) -> bool:
        """
        Validate if this agent can handle the given task.
        
        Args:
            task: Task to validate
            
        Returns:
            True if agent can handle task, False otherwise
        """
        return task.agent_type == self.__class__.__name__
    
    def get_status(self) -> Dict[str, Any]:
        """Get current agent status and statistics"""
        return {
            "name": self.name,
            "capabilities": self.capabilities,
            "total_tasks": len(self.task_history),
            "completed_tasks": len([t for t in self.task_history if t.status == TaskStatus.COMPLETED]),
            "failed_tasks": len([t for t in self.task_history if t.status == TaskStatus.FAILED]),
        }
    
    async def _execute_with_retry(self, task: Task, dry_run: bool = False) -> AgentResult:
        """
        Execute task with retry logic.
        
        Args:
            task: Task to execute
            dry_run: Simulation mode flag
            
        Returns:
            AgentResult with final execution outcome
        """
        task.status = TaskStatus.IN_PROGRESS
        self.task_history.append(task)
        
        for attempt in range(task.max_retries):
            try:
                self.logger.info(f"Executing task {task.id}, attempt {attempt + 1}")
                result = await self.run(task, dry_run)
                
                if result.success:
                    task.status = TaskStatus.COMPLETED
                    task.retry_count = attempt
                    self.logger.info(f"Task {task.id} completed successfully")
                    return result
                else:
                    self.logger.warning(f"Task {task.id} failed, attempt {attempt + 1}: {result.error}")
                    
            except Exception as e:
                self.logger.error(f"Task {task.id} error, attempt {attempt + 1}: {str(e)}")
                result = AgentResult(success=False, output="", error=str(e))
        
        # All retries exhausted
        task.status = TaskStatus.FAILED
        task.retry_count = task.max_retries
        self.logger.error(f"Task {task.id} failed after {task.max_retries} attempts")
        return result
    
    def _log_task_execution(self, task: Task, result: AgentResult) -> None:
        """Log task execution details"""
        self.logger.info(
            f"Task {task.id} executed by {self.name}: "
            f"success={result.success}, time={result.execution_time:.2f}s"
        )
    
    # TDD-specific methods
    
    def set_tdd_context(self, state_machine: TDDStateMachine, cycle: Optional[TDDCycle] = None, task: Optional[TDDTask] = None) -> None:
        """Set TDD context for this agent"""
        self.tdd_state_machine = state_machine
        self.current_tdd_cycle = cycle
        self.current_tdd_task = task
        if cycle:
            self.logger.info(f"TDD context set: cycle={cycle.id}, state={cycle.current_state.value}")
    
    def get_tdd_state(self) -> Optional[TDDState]:
        """Get current TDD state"""
        if self.current_tdd_cycle:
            return self.current_tdd_cycle.current_state
        elif self.tdd_state_machine:
            return self.tdd_state_machine.current_state
        return None
    
    def validate_tdd_command(self, command: str) -> TDDCommandResult:
        """Validate TDD command against current state"""
        if not self.tdd_state_machine:
            return TDDCommandResult(
                success=False,
                error_message="No TDD state machine available",
                hint="Set TDD context before executing TDD commands"
            )
        
        return self.tdd_state_machine.validate_command(command, self.current_tdd_cycle)
    
    def can_execute_tdd_phase(self, phase: TDDState) -> bool:
        """Check if agent can execute specific TDD phase"""
        current_state = self.get_tdd_state()
        if not current_state:
            return False
        
        # Define which agents can execute which phases
        phase_permissions = {
            TDDState.DESIGN: ["DesignAgent"],
            TDDState.TEST_RED: ["QAAgent"],
            TDDState.CODE_GREEN: ["CodeAgent"],
            TDDState.REFACTOR: ["CodeAgent"],
            TDDState.COMMIT: ["CodeAgent", "Orchestrator"]
        }
        
        allowed_agents = phase_permissions.get(phase, [])
        return self.__class__.__name__ in allowed_agents or "Orchestrator" in self.__class__.__name__
    
    def get_tdd_context_info(self) -> Dict[str, Any]:
        """Get comprehensive TDD context information"""
        info = {
            "agent_name": self.name,
            "has_tdd_context": self.tdd_state_machine is not None,
            "current_state": None,
            "cycle_id": None,
            "task_id": None,
            "allowed_commands": [],
            "tdd_metrics": self._get_tdd_metrics()
        }
        
        if self.tdd_state_machine:
            info.update({
                "current_state": self.get_tdd_state().value if self.get_tdd_state() else None,
                "allowed_commands": self.tdd_state_machine.get_allowed_commands(self.current_tdd_cycle)
            })
        
        if self.current_tdd_cycle:
            info.update({
                "cycle_id": self.current_tdd_cycle.id,
                "story_id": self.current_tdd_cycle.story_id,
                "cycle_progress": self.current_tdd_cycle.get_progress_summary(),
                "cycle_health": self._assess_cycle_health()
            })
        
        if self.current_tdd_task:
            info.update({
                "task_id": self.current_tdd_task.id,
                "task_description": self.current_tdd_task.description,
                "task_state": self.current_tdd_task.current_state.value,
                "has_failing_tests": self.current_tdd_task.has_failing_tests(),
                "has_passing_tests": self.current_tdd_task.has_passing_tests(),
                "task_health": self._assess_task_health()
            })
        
        return info
    
    def _get_tdd_metrics(self) -> Dict[str, Any]:
        """Get TDD performance metrics for this agent"""
        tdd_tasks = [t for t in self.task_history if hasattr(t, 'context') and 
                    t.context and 'tdd_cycle' in str(t.context)]
        
        return {
            "total_tdd_tasks": len(tdd_tasks),
            "completed_tdd_tasks": len([t for t in tdd_tasks if t.status == TaskStatus.COMPLETED]),
            "failed_tdd_tasks": len([t for t in tdd_tasks if t.status == TaskStatus.FAILED]),
            "average_execution_time": self._calculate_average_execution_time(tdd_tasks),
            "success_rate": self._calculate_success_rate(tdd_tasks)
        }
    
    def _assess_cycle_health(self) -> Dict[str, Any]:
        """Assess health of current TDD cycle"""
        if not self.current_tdd_cycle:
            return {"status": "no_cycle", "score": 0}
        
        # Calculate health metrics
        total_tasks = len(self.current_tdd_cycle.tasks)
        completed_tasks = len([t for t in self.current_tdd_cycle.tasks 
                              if t.current_state in [TDDState.COMMIT]])
        
        health_score = (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0
        
        return {
            "status": "healthy" if health_score > 80 else "needs_attention" if health_score > 50 else "critical",
            "score": health_score,
            "total_tasks": total_tasks,
            "completed_tasks": completed_tasks,
            "current_state": self.current_tdd_cycle.current_state.value
        }
    
    def _assess_task_health(self) -> Dict[str, Any]:
        """Assess health of current TDD task"""
        if not self.current_tdd_task:
            return {"status": "no_task", "score": 0}
        
        # Analyze test results
        total_tests = len(self.current_tdd_task.test_results)
        passing_tests = len([t for t in self.current_tdd_task.test_results if t.passed])
        
        if total_tests == 0:
            return {"status": "no_tests", "score": 0}
        
        pass_rate = (passing_tests / total_tests * 100)
        
        # Determine status based on TDD phase expectations
        current_state = self.current_tdd_task.current_state
        if current_state == TDDState.TEST_RED:
            # In RED phase, tests should fail
            status = "healthy" if pass_rate < 20 else "unhealthy"
            score = 100 - pass_rate  # Lower pass rate is better in RED phase
        else:
            # In GREEN/REFACTOR phases, tests should pass
            status = "healthy" if pass_rate > 95 else "needs_attention" if pass_rate > 80 else "critical"
            score = pass_rate
        
        return {
            "status": status,
            "score": score,
            "total_tests": total_tests,
            "passing_tests": passing_tests,
            "pass_rate": pass_rate,
            "current_state": current_state.value
        }
    
    def _calculate_average_execution_time(self, tasks: List[Task]) -> float:
        """Calculate average execution time for tasks"""
        if not tasks:
            return 0.0
        
        total_time = sum(getattr(task, 'execution_time', 0) for task in tasks)
        return total_time / len(tasks)
    
    def _calculate_success_rate(self, tasks: List[Task]) -> float:
        """Calculate success rate for tasks"""
        if not tasks:
            return 0.0
        
        successful_tasks = len([t for t in tasks if t.status == TaskStatus.COMPLETED])
        return (successful_tasks / len(tasks)) * 100
    
    def is_tdd_enabled(self) -> bool:
        """Check if agent is operating in TDD mode"""
        return self.tdd_state_machine is not None
    
    def log_tdd_action(self, action: str, details: str = "") -> None:
        """Log TDD-specific actions for audit trail"""
        tdd_context = ""
        if self.current_tdd_cycle:
            tdd_context += f"[cycle:{self.current_tdd_cycle.id}]"
        if self.current_tdd_task:
            tdd_context += f"[task:{self.current_tdd_task.id}]"
        if self.get_tdd_state():
            tdd_context += f"[state:{self.get_tdd_state().value}]"
        
        self.logger.info(f"TDD {action} {tdd_context}: {details}")
    
    # Abstract TDD methods that specific agents should implement
    
    async def execute_tdd_phase(self, phase: TDDState, context: Dict[str, Any]) -> AgentResult:
        """
        Execute a specific TDD phase. Override in subclasses.
        
        Args:
            phase: The TDD phase to execute
            context: Context data for the phase execution
            
        Returns:
            AgentResult with phase execution outcome
        """
        if not self.can_execute_tdd_phase(phase):
            return AgentResult(
                success=False,
                output="",
                error=f"Agent {self.name} cannot execute TDD phase {phase.value}"
            )
        
        # Default implementation - subclasses should override
        return AgentResult(
            success=True,
            output=f"Agent {self.name} executed TDD phase {phase.value}",
            artifacts={}
        )
    
    async def handle_tdd_task(self, tdd_cycle: TDDCycle, phase: TDDState) -> AgentResult:
        """
        Main TDD task handler that coordinates phase execution.
        Optimized for better handoff and context management.
        
        Args:
            tdd_cycle: The current TDD cycle
            phase: The TDD phase to execute
            
        Returns:
            AgentResult with task execution outcome
        """
        execution_start = time.time()
        
        # Set TDD context
        self.current_tdd_cycle = tdd_cycle
        self.log_tdd_action("handle_tdd_task", f"phase: {phase.value}, cycle: {tdd_cycle.id}")
        
        # Validate phase transition
        validation_result = await self.validate_tdd_phase(tdd_cycle.current_state, phase)
        if not validation_result.success:
            return validation_result
        
        # Prepare context with optimizations
        context = await self.get_tdd_context(tdd_cycle.story_id)
        context.update({
            "tdd_cycle": tdd_cycle,
            "current_phase": phase,
            "story_id": tdd_cycle.story_id,
            "execution_start": execution_start,
            "agent_capabilities": self.capabilities
        })
        
        # Create context snapshot for handoff tracking
        await self.create_context_snapshot(
            f"Starting {phase.value} phase execution",
            tdd_cycle.story_id
        )
        
        try:
            # Execute the phase-specific logic
            result = await self.execute_tdd_phase(phase, context)
            
            # Record execution metrics
            execution_time = time.time() - execution_start
            result.execution_time = execution_time
            
            # Record decision for learning
            if result.success:
                await self.record_decision(
                    description=f"Successfully executed {phase.value} phase",
                    rationale=f"Phase completed within {execution_time:.2f}s",
                    outcome="success",
                    confidence=0.9,
                    artifacts=result.artifacts,
                    story_id=tdd_cycle.story_id
                )
                self.log_tdd_action("phase_completed", f"phase: {phase.value} completed successfully in {execution_time:.2f}s")
            else:
                await self.record_decision(
                    description=f"Failed to execute {phase.value} phase",
                    rationale=f"Error: {result.error}",
                    outcome="failure",
                    confidence=0.1,
                    artifacts={},
                    story_id=tdd_cycle.story_id
                )
                self.log_tdd_action("phase_failed", f"phase: {phase.value} failed: {result.error}")
            
            return result
            
        except Exception as e:
            execution_time = time.time() - execution_start
            error_msg = f"TDD task execution failed after {execution_time:.2f}s: {str(e)}"
            self.logger.error(error_msg)
            self.log_tdd_action("task_error", error_msg)
            
            # Record failure decision
            await self.record_decision(
                description=f"Exception in {phase.value} phase",
                rationale=f"Unhandled exception: {str(e)}",
                outcome="exception",
                confidence=0.0,
                artifacts={},
                story_id=tdd_cycle.story_id
            )
            
            return AgentResult(
                success=False,
                output="",
                error=error_msg,
                execution_time=execution_time
            )
    
    async def validate_tdd_phase(self, current_phase: TDDState, target_phase: TDDState) -> AgentResult:
        """
        Validate TDD phase transition.
        
        Args:
            current_phase: Current TDD phase
            target_phase: Target TDD phase to transition to
            
        Returns:
            AgentResult indicating if transition is valid
        """
        # Check if agent can execute the target phase
        if not self.can_execute_tdd_phase(target_phase):
            return AgentResult(
                success=False,
                output="",
                error=f"Agent {self.name} cannot execute TDD phase {target_phase.value}"
            )
        
        # Validate phase sequence using state machine
        if self.tdd_state_machine:
            # Use state machine validation
            command_map = {
                TDDState.DESIGN: "design",
                TDDState.TEST_RED: "write_test",
                TDDState.CODE_GREEN: "implement",
                TDDState.REFACTOR: "refactor",
                TDDState.COMMIT: "commit"
            }
            
            command = command_map.get(target_phase)
            if command:
                validation = self.tdd_state_machine.validate_command(command, self.current_tdd_cycle)
                if not validation.success:
                    return AgentResult(
                        success=False,
                        output="",
                        error=f"Invalid phase transition: {validation.error_message}"
                    )
        
        # Basic phase sequence validation
        valid_transitions = {
            TDDState.DESIGN: [TDDState.TEST_RED],
            TDDState.TEST_RED: [TDDState.CODE_GREEN],
            TDDState.CODE_GREEN: [TDDState.REFACTOR, TDDState.COMMIT],
            TDDState.REFACTOR: [TDDState.COMMIT, TDDState.TEST_RED],  # Can add more tests
            TDDState.COMMIT: [TDDState.DESIGN]  # Start new cycle
        }
        
        allowed_next = valid_transitions.get(current_phase, [])
        if target_phase not in allowed_next:
            return AgentResult(
                success=False,
                output="",
                error=f"Invalid TDD phase transition from {current_phase.value} to {target_phase.value}"
            )
        
        return AgentResult(
            success=True,
            output=f"Valid phase transition from {current_phase.value} to {target_phase.value}"
        )
    
    async def get_tdd_context(self, story_id: str) -> Dict[str, Any]:
        """
        Retrieve TDD-specific context for a story.
        
        Args:
            story_id: ID of the story to get context for
            
        Returns:
            Dictionary containing TDD context data
        """
        context = {
            "story_id": story_id,
            "agent_name": self.name,
            "agent_capabilities": self.capabilities,
            "tdd_state": self.get_tdd_state().value if self.get_tdd_state() else None,
            "has_tdd_context": self.is_tdd_enabled(),
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # Add cycle-specific context if available
        if self.current_tdd_cycle:
            context.update({
                "cycle_id": self.current_tdd_cycle.id,
                "cycle_state": self.current_tdd_cycle.current_state.value,
                "cycle_story_id": self.current_tdd_cycle.story_id,
                "cycle_tasks": len(self.current_tdd_cycle.tasks),
                "cycle_progress": self.current_tdd_cycle.get_progress_summary()
            })
            
            # Add task-specific context if available
            if self.current_tdd_task:
                context.update({
                    "task_id": self.current_tdd_task.id,
                    "task_description": self.current_tdd_task.description,
                    "task_state": self.current_tdd_task.current_state.value,
                    "task_test_results": {
                        "total_tests": len(self.current_tdd_task.test_results),
                        "failing_tests": len([t for t in self.current_tdd_task.test_results if not t.passed]),
                        "passing_tests": len([t for t in self.current_tdd_task.test_results if t.passed])
                    }
                })
        
        # Add agent-specific context extensions
        agent_context = await self._get_agent_specific_tdd_context(story_id)
        context.update(agent_context)
        
        return context
    
    async def _get_agent_specific_tdd_context(self, story_id: str) -> Dict[str, Any]:
        """
        Get agent-specific TDD context. Override in subclasses.
        
        Args:
            story_id: Story ID to get context for
            
        Returns:
            Agent-specific context dictionary
        """
        return {}
    
    # Context Management Methods
    
    async def prepare_context(
        self, 
        task: Union[TDDTask, Dict[str, Any]], 
        story_id: Optional[str] = None,
        max_tokens: Optional[int] = None
    ) -> Optional[Any]:
        """
        Prepare context for task execution using context manager.
        
        Args:
            task: Task to prepare context for
            story_id: Story ID for context isolation
            max_tokens: Maximum tokens for context
            
        Returns:
            AgentContext if context manager available, None otherwise
        """
        if not self.context_manager:
            self.logger.warning("No context manager available for context preparation")
            return None
        
        try:
            context = await self.context_manager.prepare_context(
                agent_type=self.__class__.__name__,
                task=task,
                max_tokens=max_tokens,
                story_id=story_id
            )
            
            self._current_context = context
            self.logger.info(f"Context prepared: {context.get_total_token_estimate()} tokens")
            return context
            
        except Exception as e:
            self.logger.error(f"Context preparation failed: {str(e)}")
            return None
    
    async def record_decision(
        self,
        description: str,
        rationale: str = "",
        outcome: str = "",
        confidence: float = 0.0,
        artifacts: Optional[Dict[str, str]] = None,
        story_id: Optional[str] = None
    ) -> Optional[str]:
        """
        Record a decision for learning and context handoffs.
        
        Args:
            description: Description of the decision
            rationale: Reasoning behind the decision
            outcome: Result of the decision
            confidence: Confidence level (0.0 to 1.0)
            artifacts: Associated artifacts
            story_id: Story ID (extracted from current context if not provided)
            
        Returns:
            Decision ID if recorded successfully, None otherwise
        """
        if not self.context_manager:
            return None
        
        # Extract story_id from current context if not provided
        if not story_id and self._current_context:
            story_id = getattr(self._current_context, 'story_id', 'default')
        
        story_id = story_id or 'default'
        
        try:
            decision_id = await self.context_manager.record_agent_decision(
                agent_type=self.__class__.__name__,
                story_id=story_id,
                description=description,
                rationale=rationale,
                outcome=outcome,
                confidence=confidence,
                artifacts=artifacts
            )
            
            self.logger.debug(f"Recorded decision {decision_id}")
            return decision_id
            
        except Exception as e:
            self.logger.error(f"Failed to record decision: {str(e)}")
            return None
    
    async def create_context_snapshot(
        self,
        summary: str = "",
        story_id: Optional[str] = None
    ) -> Optional[str]:
        """
        Create a snapshot of current context for historical reference.
        
        Args:
            summary: Optional summary description
            story_id: Story ID (extracted from current context if not provided)
            
        Returns:
            Snapshot ID if created successfully, None otherwise
        """
        if not self.context_manager or not self._current_context:
            return None
        
        # Extract story_id from current context if not provided
        if not story_id:
            story_id = getattr(self._current_context, 'story_id', 'default')
        
        try:
            snapshot_id = await self.context_manager.create_context_snapshot(
                agent_type=self.__class__.__name__,
                story_id=story_id,
                context=self._current_context,
                summary=summary or f"Context snapshot during {self.__class__.__name__} execution"
            )
            
            self.logger.debug(f"Created context snapshot {snapshot_id}")
            return snapshot_id
            
        except Exception as e:
            self.logger.error(f"Failed to create context snapshot: {str(e)}")
            return None
    
    async def get_context_history(
        self,
        story_id: Optional[str] = None,
        tdd_phase: Optional[TDDState] = None,
        limit: int = 10
    ) -> List[Any]:
        """
        Get historical context snapshots for this agent.
        
        Args:
            story_id: Story ID (extracted from current context if not provided)
            tdd_phase: Optional TDD phase filter
            limit: Maximum number of snapshots to return
            
        Returns:
            List of context snapshots
        """
        if not self.context_manager:
            return []
        
        # Extract story_id from current context if not provided
        if not story_id and self._current_context:
            story_id = getattr(self._current_context, 'story_id', 'default')
        
        story_id = story_id or 'default'
        
        try:
            return await self.context_manager.get_agent_context_history(
                agent_type=self.__class__.__name__,
                story_id=story_id,
                tdd_phase=tdd_phase,
                limit=limit
            )
        except Exception as e:
            self.logger.error(f"Failed to get context history: {str(e)}")
            return []
    
    async def get_recent_decisions(
        self,
        story_id: Optional[str] = None,
        limit: int = 10
    ) -> List[Any]:
        """
        Get recent decisions for this agent.
        
        Args:
            story_id: Story ID (extracted from current context if not provided)
            limit: Maximum number of decisions to return
            
        Returns:
            List of recent decisions
        """
        if not self.context_manager:
            return []
        
        # Extract story_id from current context if not provided
        if not story_id and self._current_context:
            story_id = getattr(self._current_context, 'story_id', 'default')
        
        story_id = story_id or 'default'
        
        try:
            return await self.context_manager.get_recent_decisions(
                agent_type=self.__class__.__name__,
                story_id=story_id,
                limit=limit
            )
        except Exception as e:
            self.logger.error(f"Failed to get recent decisions: {str(e)}")
            return []
    
    def get_current_context_info(self) -> Dict[str, Any]:
        """Get information about current context"""
        if not self._current_context:
            return {"has_context": False}
        
        return {
            "has_context": True,
            "request_id": getattr(self._current_context, 'request_id', None),
            "story_id": getattr(self._current_context, 'story_id', None),
            "tdd_phase": getattr(self._current_context, 'tdd_phase', None),
            "token_usage": getattr(self._current_context, 'token_usage', None),
            "preparation_time": getattr(self._current_context, 'preparation_time', None),
            "cache_hit": getattr(self._current_context, 'cache_hit', False),
            "compression_applied": getattr(self._current_context, 'compression_applied', False)
        }
    
    def handle_tdd_error(self, error: Exception, phase: TDDState, recovery_action: str = None) -> AgentResult:
        """
        Handle TDD-specific errors with appropriate recovery strategies.
        
        Args:
            error: The exception that occurred
            phase: The TDD phase where error occurred
            recovery_action: Optional recovery action to suggest
            
        Returns:
            AgentResult with error handling outcome
        """
        error_msg = str(error)
        self.log_tdd_action("error_handling", f"phase: {phase.value}, error: {error_msg}")
        
        # Determine recovery strategy based on phase and error type
        recovery_strategies = {
            TDDState.DESIGN: "Review requirements and simplify design specifications",
            TDDState.TEST_RED: "Verify test syntax and ensure tests fail for the right reasons",
            TDDState.CODE_GREEN: "Implement minimal solution to make tests pass",
            TDDState.REFACTOR: "Revert to working state and apply smaller refactoring steps",
            TDDState.COMMIT: "Resolve conflicts and ensure all tests pass before committing"
        }
        
        suggested_recovery = recovery_action or recovery_strategies.get(phase, "Review and retry")
        
        # Check if error is recoverable
        recoverable_errors = [
            "ImportError", "ModuleNotFoundError", "SyntaxError", 
            "AssertionError", "TypeError", "ValueError"
        ]
        
        is_recoverable = any(err_type in error_msg for err_type in recoverable_errors)
        
        return AgentResult(
            success=False,
            output=f"TDD {phase.value} phase error handled",
            error=error_msg,
            artifacts={
                "error_report.json": json.dumps({
                    "phase": phase.value,
                    "error_type": type(error).__name__,
                    "error_message": error_msg,
                    "is_recoverable": is_recoverable,
                    "suggested_recovery": suggested_recovery,
                    "agent": self.name,
                    "timestamp": datetime.utcnow().isoformat()
                }, indent=2)
            }
        )


# Import context management
try:
    from ..context.manager import ContextManager
except ImportError:
    # Graceful fallback if context manager is not available
    ContextManager = None

# Check for NO_AGENT_MODE environment variable
import os
NO_AGENT_MODE = os.getenv("NO_AGENT_MODE", "false").lower() == "true"

# Import specific agent implementations
if NO_AGENT_MODE:
    # Import mock agents when in NO_AGENT_MODE
    from .mock_agent import MockDesignAgent as DesignAgent
    from .mock_agent import MockCodeAgent as CodeAgent
    from .mock_agent import MockQAAgent as QAAgent
    from .mock_agent import MockDataAgent as DataAgent
    from .mock_agent import create_mock_agent
    logger.info("NO_AGENT_MODE enabled - using mock agents for testing")
else:
    # Import real agents for normal operation
    from .design_agent import DesignAgent
    from .code_agent import CodeAgent
    from .qa_agent import QAAgent
    from .data_agent import DataAgent

# Agent registry for dynamic instantiation
AGENT_REGISTRY: Dict[str, type] = {
    "DesignAgent": DesignAgent,
    "CodeAgent": CodeAgent,
    "QAAgent": QAAgent,
    "DataAgent": DataAgent,
}


def create_agent(agent_type: str, context_manager: Optional[Any] = None, **kwargs) -> BaseAgent:
    """Factory function to create agent instances"""
    if NO_AGENT_MODE:
        # Use mock agent factory in NO_AGENT_MODE
        return create_mock_agent(agent_type, context_manager=context_manager)
    
    if agent_type not in AGENT_REGISTRY:
        raise ValueError(f"Unknown agent type: {agent_type}")
    
    agent_class = AGENT_REGISTRY[agent_type]
    
    # Add context_manager to kwargs if provided
    if context_manager is not None:
        kwargs['context_manager'] = context_manager
    
    return agent_class(**kwargs)


def get_available_agents() -> List[str]:
    """Get list of available agent types"""
    return list(AGENT_REGISTRY.keys())