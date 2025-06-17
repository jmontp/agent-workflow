"""
File-based persistence for project management data.

This module handles reading and writing project data to the .orch-state directory
within project repositories.
"""

import json
import os
from pathlib import Path
from typing import Optional, Dict, Any
from data_models import ProjectData, Epic, Story, Sprint


class ProjectStorage:
    """Handles persistent storage for project management data."""
    
    def __init__(self, project_path: str):
        """Initialize storage for a specific project."""
        self.project_path = Path(project_path)
        self.orch_state_dir = self.project_path / ".orch-state"
        self.backlog_file = self.orch_state_dir / "backlog.json"
        self.sprints_dir = self.orch_state_dir / "sprints"
        self.architecture_file = self.orch_state_dir / "architecture.md"
        self.best_practices_file = self.orch_state_dir / "best-practices.md"
        self.status_file = self.orch_state_dir / "status.json"
    
    def ensure_directories(self):
        """Create the .orch-state directory structure if it doesn't exist."""
        self.orch_state_dir.mkdir(exist_ok=True)
        self.sprints_dir.mkdir(exist_ok=True)
        
        # Create .gitkeep file in sprints directory
        gitkeep = self.sprints_dir / ".gitkeep"
        if not gitkeep.exists():
            gitkeep.touch()
    
    def initialize_project(self) -> bool:
        """Initialize a new project with default structure and files."""
        try:
            # Ensure directories exist
            self.ensure_directories()
            
            # Initialize empty backlog if it doesn't exist
            if not self.backlog_file.exists():
                empty_data = ProjectData()
                self.save_project_data(empty_data)
            
            # Create template architecture.md
            if not self.architecture_file.exists():
                arch_template = """# Project Architecture

## Overview
This document describes the architecture and design decisions for this project.

## Components
- [Component descriptions go here]

## Design Decisions
- [Key architectural decisions and rationale]

## Dependencies
- [External dependencies and integration points]

## Future Considerations
- [Planned improvements and technical debt]
"""
                self.architecture_file.write_text(arch_template)
            
            # Create template best-practices.md
            if not self.best_practices_file.exists():
                practices_template = """# Project Best Practices

## Code Standards
- [Coding conventions and style guidelines]

## Testing Strategy
- [Testing approaches and requirements]

## Git Workflow
- [Branch strategy and commit conventions]

## AI Agent Guidelines
- [Project-specific instructions for AI agents]

## Review Process
- [Code review and approval workflows]
"""
                self.best_practices_file.write_text(practices_template)
            
            return True
        except Exception as e:
            print(f"Error initializing project: {e}")
            return False
    
    def load_project_data(self) -> ProjectData:
        """Load project data from backlog.json."""
        if not self.backlog_file.exists():
            return ProjectData()
        
        try:
            with open(self.backlog_file, 'r') as f:
                data = json.load(f)
            return ProjectData.from_dict(data)
        except (json.JSONDecodeError, KeyError) as e:
            print(f"Error loading project data: {e}")
            return ProjectData()
    
    def save_project_data(self, project_data: ProjectData):
        """Save project data to backlog.json."""
        self.ensure_directories()
        
        try:
            with open(self.backlog_file, 'w') as f:
                json.dump(project_data.to_dict(), f, indent=2)
        except Exception as e:
            print(f"Error saving project data: {e}")
    
    def load_sprint(self, sprint_id: str) -> Optional[Sprint]:
        """Load a specific sprint from its JSON file."""
        sprint_file = self.sprints_dir / f"{sprint_id}.json"
        if not sprint_file.exists():
            return None
        
        try:
            with open(sprint_file, 'r') as f:
                data = json.load(f)
            return Sprint.from_dict(data)
        except (json.JSONDecodeError, KeyError) as e:
            print(f"Error loading sprint {sprint_id}: {e}")
            return None
    
    def save_sprint(self, sprint: Sprint):
        """Save a sprint to its individual JSON file."""
        self.ensure_directories()
        
        sprint_file = self.sprints_dir / f"{sprint.id}.json"
        try:
            with open(sprint_file, 'w') as f:
                json.dump(sprint.to_dict(), f, indent=2)
        except Exception as e:
            print(f"Error saving sprint {sprint.id}: {e}")
    
    def list_sprint_files(self) -> list[str]:
        """Get a list of all sprint JSON files."""
        if not self.sprints_dir.exists():
            return []
        
        return [f.stem for f in self.sprints_dir.glob("*.json")]
    
    def project_exists(self) -> bool:
        """Check if this appears to be a valid project with git."""
        git_dir = self.project_path / ".git"
        return git_dir.exists() and git_dir.is_dir()
    
    def is_initialized(self) -> bool:
        """Check if the project has been initialized with .orch-state."""
        return self.orch_state_dir.exists() and self.backlog_file.exists()
    
    def get_project_name(self) -> str:
        """Get the project name from the directory name."""
        return self.project_path.name
    
    def load_status(self) -> Dict[str, Any]:
        """Load project status from status.json."""
        if not self.status_file.exists():
            return {}
        
        try:
            with open(self.status_file, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            return {}
    
    def save_status(self, status: Dict[str, Any]):
        """Save project status to status.json."""
        self.ensure_directories()
        
        try:
            with open(self.status_file, 'w') as f:
                json.dump(status, f, indent=2)
        except Exception as e:
            print(f"Error saving status: {e}")
    
    def get_architecture_content(self) -> str:
        """Get the content of architecture.md."""
        if not self.architecture_file.exists():
            return ""
        return self.architecture_file.read_text()
    
    def update_architecture(self, content: str):
        """Update the architecture.md file."""
        self.ensure_directories()
        self.architecture_file.write_text(content)
    
    def get_best_practices_content(self) -> str:
        """Get the content of best-practices.md."""
        if not self.best_practices_file.exists():
            return ""
        return self.best_practices_file.read_text()
    
    def update_best_practices(self, content: str):
        """Update the best-practices.md file."""
        self.ensure_directories()
        self.best_practices_file.write_text(content)