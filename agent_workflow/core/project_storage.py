"""
Project storage module for agent-workflow package.

This module provides file-based persistence for project management data
including epics, stories, sprints, and other workflow state.
"""

import os
import json
import yaml
import shutil
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime
import logging

from .models import ProjectData, Epic, Story, Sprint

logger = logging.getLogger(__name__)


class ProjectStorage:
    """
    File-based storage for project management data.
    
    Handles persistence of epics, stories, sprints, and other project data
    to the filesystem with backup and recovery capabilities.
    """
    
    def __init__(self, project_path: Path):
        """
        Initialize project storage.
        
        Args:
            project_path: Path to the project directory
        """
        self.project_path = Path(project_path)
        self.storage_dir = self.project_path / ".orch-state"
        self.data_file = self.storage_dir / "project_data.json"
        self.backup_dir = self.storage_dir / "backups"
        
        # Ensure directories exist
        self.storage_dir.mkdir(exist_ok=True)
        self.backup_dir.mkdir(exist_ok=True)
        
        self._project_data = None
    
    def initialize_project(self, project_name: str) -> ProjectData:
        """
        Initialize a new project with empty data.
        
        Args:
            project_name: Name of the project
            
        Returns:
            Initialized ProjectData instance
        """
        project_data = ProjectData(project_name=project_name)
        self.save_project_data(project_data)
        self._project_data = project_data
        
        logger.info(f"Initialized project storage for: {project_name}")
        return project_data
    
    def load_project_data(self) -> Optional[ProjectData]:
        """
        Load project data from storage.
        
        Returns:
            ProjectData instance or None if not found
        """
        if not self.data_file.exists():
            return None
        
        try:
            with open(self.data_file, 'r') as f:
                data_dict = json.load(f)
            
            project_data = ProjectData.from_dict(data_dict)
            self._project_data = project_data
            
            logger.debug(f"Loaded project data for: {project_data.project_name}")
            return project_data
            
        except Exception as e:
            logger.error(f"Failed to load project data: {e}")
            
            # Try to recover from backup
            return self._recover_from_backup()
    
    def save_project_data(self, project_data: ProjectData) -> bool:
        """
        Save project data to storage.
        
        Args:
            project_data: ProjectData instance to save
            
        Returns:
            True if saved successfully
        """
        try:
            # Create backup before saving
            if self.data_file.exists():
                self._create_backup()
            
            # Update timestamp
            project_data.updated = datetime.now()
            
            # Save to file
            with open(self.data_file, 'w') as f:
                json.dump(project_data.to_dict(), f, indent=2)
            
            self._project_data = project_data
            logger.debug(f"Saved project data for: {project_data.project_name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to save project data: {e}")
            return False
    
    def get_project_data(self) -> Optional[ProjectData]:
        """
        Get cached project data or load from storage.
        
        Returns:
            ProjectData instance or None
        """
        if self._project_data is None:
            self._project_data = self.load_project_data()
        
        return self._project_data
    
    def create_epic(self, title: str, description: str, **kwargs) -> Optional[Epic]:
        """
        Create and persist a new epic.
        
        Args:
            title: Epic title
            description: Epic description
            **kwargs: Additional epic properties
            
        Returns:
            Created Epic instance or None if failed
        """
        project_data = self.get_project_data()
        if not project_data:
            logger.error("No project data available")
            return None
        
        epic = project_data.create_epic(title, description, **kwargs)
        
        if self.save_project_data(project_data):
            logger.info(f"Created epic: {epic.id}")
            return epic
        
        return None
    
    def create_story(self, title: str, description: str, epic_id: Optional[str] = None, **kwargs) -> Optional[Story]:
        """
        Create and persist a new story.
        
        Args:
            title: Story title
            description: Story description
            epic_id: Optional epic ID to associate with
            **kwargs: Additional story properties
            
        Returns:
            Created Story instance or None if failed
        """
        project_data = self.get_project_data()
        if not project_data:
            logger.error("No project data available")
            return None
        
        story = project_data.create_story(title, description, epic_id, **kwargs)
        
        if self.save_project_data(project_data):
            logger.info(f"Created story: {story.id}")
            return story
        
        return None
    
    def create_sprint(self, name: str, description: str, **kwargs) -> Optional[Sprint]:
        """
        Create and persist a new sprint.
        
        Args:
            name: Sprint name
            description: Sprint description
            **kwargs: Additional sprint properties
            
        Returns:
            Created Sprint instance or None if failed
        """
        project_data = self.get_project_data()
        if not project_data:
            logger.error("No project data available")
            return None
        
        sprint = project_data.create_sprint(name, description, **kwargs)
        
        if self.save_project_data(project_data):
            logger.info(f"Created sprint: {sprint.id}")
            return sprint
        
        return None
    
    def update_story_status(self, story_id: str, status: str) -> bool:
        """
        Update story status and persist changes.
        
        Args:
            story_id: ID of story to update
            status: New status
            
        Returns:
            True if updated successfully
        """
        project_data = self.get_project_data()
        if not project_data or story_id not in project_data.stories:
            return False
        
        story = project_data.stories[story_id]
        from .models import StoryStatus
        
        try:
            story.status = StoryStatus(status)
            story.updated = datetime.now()
            
            return self.save_project_data(project_data)
        except ValueError:
            logger.error(f"Invalid story status: {status}")
            return False
    
    def add_story_to_sprint(self, story_id: str, sprint_id: str) -> bool:
        """
        Add story to sprint and persist changes.
        
        Args:
            story_id: ID of story to add
            sprint_id: ID of target sprint
            
        Returns:
            True if added successfully
        """
        project_data = self.get_project_data()
        if not project_data:
            return False
        
        if story_id not in project_data.stories or sprint_id not in project_data.sprints:
            return False
        
        # Update story
        story = project_data.stories[story_id]
        story.sprint_id = sprint_id
        story.updated = datetime.now()
        
        # Update sprint
        sprint = project_data.sprints[sprint_id]
        sprint.add_story(story_id)
        
        return self.save_project_data(project_data)
    
    def get_backlog_stories(self) -> List[Story]:
        """
        Get all backlog stories.
        
        Returns:
            List of Story instances in backlog
        """
        project_data = self.get_project_data()
        if not project_data:
            return []
        
        return project_data.get_backlog_stories()
    
    def get_sprint_stories(self, sprint_id: str) -> List[Story]:
        """
        Get all stories in a sprint.
        
        Args:
            sprint_id: Sprint ID
            
        Returns:
            List of Story instances in sprint
        """
        project_data = self.get_project_data()
        if not project_data or sprint_id not in project_data.sprints:
            return []
        
        sprint = project_data.sprints[sprint_id]
        return [project_data.stories[story_id] for story_id in sprint.stories 
                if story_id in project_data.stories]
    
    def export_data(self, export_path: Path, format: str = "json") -> bool:
        """
        Export project data to file.
        
        Args:
            export_path: Path to export file
            format: Export format ("json" or "yaml")
            
        Returns:
            True if exported successfully
        """
        project_data = self.get_project_data()
        if not project_data:
            return False
        
        try:
            data_dict = project_data.to_dict()
            
            with open(export_path, 'w') as f:
                if format.lower() == "yaml":
                    yaml.dump(data_dict, f, default_flow_style=False, indent=2)
                else:
                    json.dump(data_dict, f, indent=2)
            
            logger.info(f"Exported project data to: {export_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to export data: {e}")
            return False
    
    def import_data(self, import_path: Path) -> bool:
        """
        Import project data from file.
        
        Args:
            import_path: Path to import file
            
        Returns:
            True if imported successfully
        """
        if not import_path.exists():
            logger.error(f"Import file not found: {import_path}")
            return False
        
        try:
            with open(import_path, 'r') as f:
                if import_path.suffix.lower() in ['.yaml', '.yml']:
                    data_dict = yaml.safe_load(f)
                else:
                    data_dict = json.load(f)
            
            project_data = ProjectData.from_dict(data_dict)
            
            # Create backup before importing
            if self.data_file.exists():
                self._create_backup()
            
            if self.save_project_data(project_data):
                logger.info(f"Imported project data from: {import_path}")
                return True
            
        except Exception as e:
            logger.error(f"Failed to import data: {e}")
        
        return False
    
    def _create_backup(self) -> None:
        """Create backup of current data file."""
        if not self.data_file.exists():
            return
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = self.backup_dir / f"project_data_backup_{timestamp}.json"
        
        try:
            shutil.copy2(self.data_file, backup_file)
            logger.debug(f"Created backup: {backup_file}")
            
            # Clean up old backups (keep last 10)
            self._cleanup_old_backups()
            
        except Exception as e:
            logger.warning(f"Failed to create backup: {e}")
    
    def _cleanup_old_backups(self, keep_count: int = 10) -> None:
        """Clean up old backup files."""
        try:
            backup_files = list(self.backup_dir.glob("project_data_backup_*.json"))
            backup_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
            
            # Remove old backups
            for backup_file in backup_files[keep_count:]:
                backup_file.unlink()
                logger.debug(f"Removed old backup: {backup_file}")
                
        except Exception as e:
            logger.warning(f"Failed to cleanup backups: {e}")
    
    def _recover_from_backup(self) -> Optional[ProjectData]:
        """Attempt to recover data from most recent backup."""
        try:
            backup_files = list(self.backup_dir.glob("project_data_backup_*.json"))
            if not backup_files:
                logger.error("No backup files found for recovery")
                return None
            
            # Get most recent backup
            latest_backup = max(backup_files, key=lambda x: x.stat().st_mtime)
            logger.info(f"Attempting recovery from: {latest_backup}")
            
            with open(latest_backup, 'r') as f:
                data_dict = json.load(f)
            
            project_data = ProjectData.from_dict(data_dict)
            
            # Save recovered data as current
            self.save_project_data(project_data)
            
            logger.info("Successfully recovered from backup")
            return project_data
            
        except Exception as e:
            logger.error(f"Failed to recover from backup: {e}")
            return None
    
    def get_storage_info(self) -> Dict[str, Any]:
        """
        Get information about storage usage and status.
        
        Returns:
            Dictionary with storage information
        """
        info = {
            "storage_dir": str(self.storage_dir),
            "data_file_exists": self.data_file.exists(),
            "data_file_size": 0,
            "backup_count": 0,
            "total_backup_size": 0,
            "last_modified": None
        }
        
        try:
            if self.data_file.exists():
                stat = self.data_file.stat()
                info["data_file_size"] = stat.st_size
                info["last_modified"] = datetime.fromtimestamp(stat.st_mtime).isoformat()
            
            backup_files = list(self.backup_dir.glob("project_data_backup_*.json"))
            info["backup_count"] = len(backup_files)
            info["total_backup_size"] = sum(f.stat().st_size for f in backup_files)
            
        except Exception as e:
            logger.warning(f"Failed to get storage info: {e}")
        
        return info
    
    def validate_data_integrity(self) -> Dict[str, Any]:
        """
        Validate data integrity and relationships.
        
        Returns:
            Dictionary with validation results
        """
        project_data = self.get_project_data()
        if not project_data:
            return {"valid": False, "errors": ["No project data found"]}
        
        errors = []
        warnings = []
        
        # Check epic-story relationships
        for epic_id, epic in project_data.epics.items():
            for story_id in epic.stories:
                if story_id not in project_data.stories:
                    errors.append(f"Epic {epic_id} references non-existent story {story_id}")
                else:
                    story = project_data.stories[story_id]
                    if story.epic_id != epic_id:
                        warnings.append(f"Story {story_id} epic_id mismatch with epic {epic_id}")
        
        # Check sprint-story relationships
        for sprint_id, sprint in project_data.sprints.items():
            for story_id in sprint.stories:
                if story_id not in project_data.stories:
                    errors.append(f"Sprint {sprint_id} references non-existent story {story_id}")
                else:
                    story = project_data.stories[story_id]
                    if story.sprint_id != sprint_id:
                        warnings.append(f"Story {story_id} sprint_id mismatch with sprint {sprint_id}")
        
        # Check story dependencies
        for story_id, story in project_data.stories.items():
            for dep_id in story.dependencies:
                if dep_id not in project_data.stories:
                    errors.append(f"Story {story_id} depends on non-existent story {dep_id}")
        
        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings,
            "total_epics": len(project_data.epics),
            "total_stories": len(project_data.stories),
            "total_sprints": len(project_data.sprints)
        }