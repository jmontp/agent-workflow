"""
Agent-Workflow: AI Agent TDD-Scrum Orchestration Framework

A comprehensive framework for coordinating AI agents in Test-Driven Development
and Scrum workflows, with Human-in-the-Loop oversight and multi-project support.
"""

__version__ = "1.0.0"
__author__ = "Agent-Workflow Contributors"
__email__ = "contact@agent-workflow.dev"
__description__ = "AI Agent TDD-Scrum Orchestration Framework"

# Import core components for package-level access
try:
    from .core.orchestrator import Orchestrator
    from .core.state_machine import StateMachine, State
    from .core.project_storage import ProjectStorage
    from .core.data_models import ProjectData, Epic, Story, Sprint
    __all__ = [
        "Orchestrator",
        "StateMachine", 
        "State",
        "ProjectStorage",
        "ProjectData",
        "Epic",
        "Story", 
        "Sprint",
    ]
except ImportError as e:
    # Graceful degradation if core components aren't available yet
    __all__ = []

# Package metadata
__package_metadata__ = {
    "name": "agent-workflow",
    "version": __version__,
    "description": __description__,
    "author": __author__,
    "author_email": __email__,
    "url": "https://github.com/jmontp/agent-workflow",
    "documentation": "https://agent-workflow.readthedocs.io",
    "repository": "https://github.com/jmontp/agent-workflow",
    "bug_reports": "https://github.com/jmontp/agent-workflow/issues",
    "license": "MIT",
    "keywords": ["ai", "agents", "tdd", "scrum", "orchestration", "workflow"],
    "python_requires": ">=3.8",
}

def get_version() -> str:
    """Get the package version."""
    return __version__

def get_package_info() -> dict:
    """Get comprehensive package information."""
    return __package_metadata__.copy()