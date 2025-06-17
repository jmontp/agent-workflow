"""
AI Agent Library for TDD-Scrum Workflow

This module provides the base agent interface and specialized agent implementations
for coordinating software development tasks through AI assistance.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum
import logging
import asyncio
from datetime import datetime

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
    """
    
    def __init__(self, name: str, capabilities: List[str]):
        self.name = name
        self.capabilities = capabilities
        self.task_history: List[Task] = []
        self.logger = logging.getLogger(f"agent.{name}")
        
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


# Import specific agent implementations
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


def create_agent(agent_type: str, **kwargs) -> BaseAgent:
    """Factory function to create agent instances"""
    if agent_type not in AGENT_REGISTRY:
        raise ValueError(f"Unknown agent type: {agent_type}")
    
    agent_class = AGENT_REGISTRY[agent_type]
    return agent_class(**kwargs)


def get_available_agents() -> List[str]:
    """Get list of available agent types"""
    return list(AGENT_REGISTRY.keys())