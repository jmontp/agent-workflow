"""
File-based persistence for project management data.

This module handles reading and writing project data to the .orch-state directory
within project repositories.
"""

import json
import os
import tempfile
import logging
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from .models import ProjectData, Epic, Story, Sprint, TDDCycle

logger = logging.getLogger(__name__)


class ProjectStorage:
    """Handles persistent storage for project management data."""
    
    def __init__(self, project_path: str):
        """Initialize storage for a specific project."""
        self.project_path = Path(project_path)
        self.orch_state_dir = self.project_path / ".orch-state"
        self.backlog_file = self.orch_state_dir / "backlog.json"
        self.sprints_dir = self.orch_state_dir / "sprints"
        self.tdd_cycles_dir = self.orch_state_dir / "tdd_cycles"
        self.architecture_file = self.orch_state_dir / "architecture.md"
        self.best_practices_file = self.orch_state_dir / "best-practices.md"
        self.status_file = self.orch_state_dir / "status.json"
    
    def ensure_directories(self):
        """Create the .orch-state directory structure if it doesn't exist."""
        self.orch_state_dir.mkdir(exist_ok=True)
        self.sprints_dir.mkdir(exist_ok=True)
        self.tdd_cycles_dir.mkdir(exist_ok=True)
        
        # Create .gitkeep files in directories
        gitkeep = self.sprints_dir / ".gitkeep"
        if not gitkeep.exists():
            gitkeep.touch()
        
        tdd_gitkeep = self.tdd_cycles_dir / ".gitkeep"
        if not tdd_gitkeep.exists():
            tdd_gitkeep.touch()
    
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
        """Load project data from backlog.json with error recovery."""
        if not self.backlog_file.exists():
            logger.info(f"Project data file does not exist: {self.backlog_file}")
            return ProjectData()
        
        # Try loading main file
        try:
            with open(self.backlog_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Validate basic structure
            if not isinstance(data, dict):
                raise ValueError("Project data must be a dictionary")
                
            return ProjectData.from_dict(data)
            
        except (json.JSONDecodeError, KeyError, ValueError) as e:
            logger.error(f"Error loading project data: {e}")
            
            # Try to recover from backup if it exists
            backup_file = self.backlog_file.with_suffix('.backup')
            if backup_file.exists():
                logger.info("Attempting to recover from backup file")
                try:
                    with open(backup_file, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    return ProjectData.from_dict(data)
                except Exception as backup_error:
                    logger.error(f"Backup recovery failed: {backup_error}")
            
            # Return empty project data as last resort
            logger.warning("Returning empty ProjectData due to load failures")
            return ProjectData()
    
    def _atomic_write_json(self, file_path: Path, data: Dict[str, Any]) -> bool:
        """Atomically write JSON data to prevent corruption."""
        try:
            # Write to temporary file first
            temp_file = file_path.with_suffix('.tmp')
            with open(temp_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
                f.flush()
                os.fsync(f.fileno())  # Force write to disk
            
            # Atomic move
            temp_file.replace(file_path)
            logger.debug(f"Successfully wrote {file_path}")
            return True
        except Exception as e:
            logger.error(f"Error writing {file_path}: {e}")
            # Clean up temp file if it exists
            if 'temp_file' in locals() and temp_file.exists():
                temp_file.unlink(missing_ok=True)
            return False

    def save_project_data(self, project_data: ProjectData):
        """Save project data to backlog.json with automatic backup."""
        self.ensure_directories()
        
        # Create backup if original file exists
        if self.backlog_file.exists():
            self._create_backup(self.backlog_file)
        
        success = self._atomic_write_json(self.backlog_file, project_data.to_dict())
        if not success:
            logger.warning(f"Failed to save project data to {self.backlog_file}")
    
    def _create_backup(self, file_path: Path) -> bool:
        """Create a backup of an existing file."""
        try:
            backup_path = file_path.with_suffix('.backup')
            if file_path.exists():
                import shutil
                shutil.copy2(file_path, backup_path)
                logger.debug(f"Created backup: {backup_path}")
                return True
        except Exception as e:
            logger.error(f"Failed to create backup for {file_path}: {e}")
        return False
    
    def load_sprint(self, sprint_id: str) -> Optional[Sprint]:
        """Load a specific sprint from its JSON file with validation."""
        sprint_file = self.sprints_dir / f"{sprint_id}.json"
        if not sprint_file.exists():
            logger.debug(f"Sprint file does not exist: {sprint_file}")
            return None
        
        try:
            with open(sprint_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Basic validation
            if not isinstance(data, dict) or 'id' not in data:
                raise ValueError(f"Invalid sprint data structure in {sprint_file}")
            
            if data['id'] != sprint_id:
                logger.warning(f"Sprint ID mismatch: file={sprint_id}, data={data['id']}")
            
            return Sprint.from_dict(data)
            
        except (json.JSONDecodeError, KeyError, ValueError) as e:
            logger.error(f"Error loading sprint {sprint_id}: {e}")
            
            # Try to recover from backup
            backup_file = sprint_file.with_suffix('.backup')
            if backup_file.exists():
                logger.info(f"Attempting to recover sprint {sprint_id} from backup")
                try:
                    with open(backup_file, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    return Sprint.from_dict(data)
                except Exception as backup_error:
                    logger.error(f"Sprint backup recovery failed: {backup_error}")
            
            return None
    
    def save_sprint(self, sprint: Sprint):
        """Save a sprint to its individual JSON file with backup."""
        self.ensure_directories()
        
        sprint_file = self.sprints_dir / f"{sprint.id}.json"
        
        # Create backup if file exists
        if sprint_file.exists():
            self._create_backup(sprint_file)
        
        success = self._atomic_write_json(sprint_file, sprint.to_dict())
        if not success:
            logger.warning(f"Failed to save sprint {sprint.id} to {sprint_file}")
    
    def list_sprint_files(self) -> list[str]:
        """Get a list of all sprint JSON files."""
        if not self.sprints_dir.exists():
            return []
        
        return [f.stem for f in self.sprints_dir.glob("*.json")]
    
    def load_tdd_cycle(self, cycle_id: str):
        """Load a specific TDD cycle from its JSON file."""
        cycle_file = self.tdd_cycles_dir / f"{cycle_id}.json"
        if not cycle_file.exists():
            return None
        
        try:
            with open(cycle_file, 'r') as f:
                data = json.load(f)
            return TDDCycle.from_dict(data)
        except (json.JSONDecodeError, KeyError) as e:
            print(f"Error loading TDD cycle {cycle_id}: {e}")
            return None
    
    def save_tdd_cycle(self, cycle):
        """Save a TDD cycle to its individual JSON file with backup and validation."""
        self.ensure_directories()
        
        cycle_file = self.tdd_cycles_dir / f"{cycle.id}.json"
        
        # Validate cycle data before saving
        if not hasattr(cycle, 'id') or not cycle.id:
            logger.error("Cannot save TDD cycle without valid ID")
            return
            
        # Create backup if file exists
        if cycle_file.exists():
            self._create_backup(cycle_file)
        
        success = self._atomic_write_json(cycle_file, cycle.to_dict())
        if not success:
            logger.warning(f"Failed to save TDD cycle {cycle.id} to {cycle_file}")
        else:
            logger.debug(f"Successfully saved TDD cycle {cycle.id}")
    
    def list_tdd_cycle_files(self) -> list[str]:
        """Get a list of all TDD cycle JSON files."""
        if not self.tdd_cycles_dir.exists():
            return []
        
        return [f.stem for f in self.tdd_cycles_dir.glob("*.json")]
    
    def get_active_tdd_cycle(self):
        """Get the currently active TDD cycle (always fresh from disk)."""
        cycle_files = self.list_tdd_cycle_files()
        # Sort by modification time to get most recently modified first
        cycle_files_with_time = []
        for cycle_id in cycle_files:
            cycle_file = self.tdd_cycles_dir / f"{cycle_id}.json"
            if cycle_file.exists():
                mtime = cycle_file.stat().st_mtime
                cycle_files_with_time.append((cycle_id, mtime))
        
        # Sort by modification time (newest first)
        cycle_files_with_time.sort(key=lambda x: x[1], reverse=True)
        
        for cycle_id, _ in cycle_files_with_time:
            cycle = self.load_tdd_cycle(cycle_id)
            if cycle and not cycle.is_complete():
                return cycle
        return None
    
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
    
    def save_tdd_metrics(self, metrics: Dict[str, Any]):
        """Save TDD performance metrics to disk"""
        self.ensure_directories()
        metrics_file = self.orch_state_dir / "tdd_metrics.json"
        
        try:
            with open(metrics_file, 'w') as f:
                json.dump(metrics, f, indent=2)
        except Exception as e:
            print(f"Error saving TDD metrics: {e}")
    
    def load_tdd_metrics(self) -> Dict[str, Any]:
        """Load TDD performance metrics from disk"""
        metrics_file = self.orch_state_dir / "tdd_metrics.json"
        if not metrics_file.exists():
            return {}
        
        try:
            with open(metrics_file, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            return {}
    
    def save_tdd_cycle_state(self, cycle_id: str, state_data: Dict[str, Any]):
        """Save TDD cycle state synchronization data"""
        self.ensure_directories()
        state_file = self.tdd_cycles_dir / f"{cycle_id}_state.json"
        
        try:
            with open(state_file, 'w') as f:
                json.dump(state_data, f, indent=2)
        except Exception as e:
            print(f"Error saving TDD cycle state: {e}")
    
    def load_tdd_cycle_state(self, cycle_id: str) -> Dict[str, Any]:
        """Load TDD cycle state synchronization data"""
        state_file = self.tdd_cycles_dir / f"{cycle_id}_state.json"
        if not state_file.exists():
            return {}
        
        try:
            with open(state_file, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            return {}
    
    def get_interrupted_tdd_cycles(self) -> list[str]:
        """Get list of TDD cycles that were interrupted and need recovery"""
        interrupted = []
        cycle_files = self.list_tdd_cycle_files()
        
        for cycle_id in cycle_files:
            cycle = self.load_tdd_cycle(cycle_id)
            if cycle and not cycle.is_complete():
                # Check if cycle has been inactive for too long
                state_data = self.load_tdd_cycle_state(cycle_id)
                if state_data.get("needs_recovery", False):
                    interrupted.append(cycle_id)
        
        return interrupted
    
    def track_test_file(self, story_id: str, test_file_path: str, status: str = "created"):
        """Track test files created by TDD cycles"""
        self.ensure_directories()
        tracking_file = self.orch_state_dir / "test_file_tracking.json"
        
        # Load existing tracking data
        tracking_data = {}
        if tracking_file.exists():
            try:
                with open(tracking_file, 'r') as f:
                    tracking_data = json.load(f)
            except (json.JSONDecodeError, FileNotFoundError):
                tracking_data = {}
        
        # Add or update test file entry
        if story_id not in tracking_data:
            tracking_data[story_id] = []
        
        # Update existing entry or add new one
        updated = False
        for entry in tracking_data[story_id]:
            if entry["file_path"] == test_file_path:
                entry["status"] = status
                entry["updated_at"] = datetime.now().isoformat()
                updated = True
                break
        
        if not updated:
            tracking_data[story_id].append({
                "file_path": test_file_path,
                "status": status,
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat()
            })
        
        # Save updated tracking data
        try:
            with open(tracking_file, 'w') as f:
                json.dump(tracking_data, f, indent=2)
        except Exception as e:
            print(f"Error saving test file tracking: {e}")
    
    def get_tracked_test_files(self, story_id: str = None) -> Dict[str, Any]:
        """Get tracked test files for a story or all stories"""
        tracking_file = self.orch_state_dir / "test_file_tracking.json"
        if not tracking_file.exists():
            return {} if story_id else {}
        
        try:
            with open(tracking_file, 'r') as f:
                tracking_data = json.load(f)
                
            if story_id:
                return tracking_data.get(story_id, [])
            else:
                return tracking_data
                
        except (json.JSONDecodeError, FileNotFoundError):
            return {} if story_id else {}
    
    def backup_tdd_cycle(self, cycle_id: str) -> bool:
        """Create backup of TDD cycle for recovery purposes"""
        try:
            cycle = self.load_tdd_cycle(cycle_id)
            if not cycle:
                return False
            
            backup_dir = self.orch_state_dir / "backups" / "tdd_cycles"
            backup_dir.mkdir(parents=True, exist_ok=True)
            
            backup_file = backup_dir / f"{cycle_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            
            with open(backup_file, 'w') as f:
                json.dump(cycle.to_dict(), f, indent=2)
            
            return True
            
        except Exception as e:
            print(f"Error backing up TDD cycle {cycle_id}: {e}")
            return False
    
    def restore_tdd_cycle_from_backup(self, cycle_id: str, backup_timestamp: str = None):
        """Restore TDD cycle from backup"""
        try:
            backup_dir = self.orch_state_dir / "backups" / "tdd_cycles"
            if not backup_dir.exists():
                return None
            
            # Find backup file
            if backup_timestamp:
                backup_file = backup_dir / f"{cycle_id}_{backup_timestamp}.json"
            else:
                # Find most recent backup
                backup_files = list(backup_dir.glob(f"{cycle_id}_*.json"))
                if not backup_files:
                    return None
                backup_file = sorted(backup_files)[-1]  # Most recent
            
            if not backup_file.exists():
                return None
            
            with open(backup_file, 'r') as f:
                data = json.load(f)
            
            return TDDCycle.from_dict(data)
            
        except Exception as e:
            print(f"Error restoring TDD cycle {cycle_id}: {e}")
            return None
    
    def cleanup_old_tdd_backups(self, days_to_keep: int = 30):
        """Clean up old TDD cycle backups"""
        try:
            backup_dir = self.orch_state_dir / "backups" / "tdd_cycles"
            if not backup_dir.exists():
                return
            
            cutoff_time = datetime.now() - timedelta(days=days_to_keep)
            cleaned_count = 0
            
            for backup_file in backup_dir.glob("*.json"):
                if backup_file.stat().st_mtime < cutoff_time.timestamp():
                    backup_file.unlink()
                    cleaned_count += 1
            
            logger.info(f"Cleaned up {cleaned_count} old TDD cycle backups")
            
        except Exception as e:
            logger.error(f"Error cleaning up TDD backups: {e}")
    
    def check_storage_health(self) -> Dict[str, Any]:
        """Check storage system health and return diagnostic info."""
        health_info = {
            "status": "healthy",
            "issues": [],
            "warnings": [],
            "directories": {},
            "files": {},
            "disk_usage": {}
        }
        
        try:
            # Check directory structure
            directories = [
                self.orch_state_dir,
                self.sprints_dir,
                self.tdd_cycles_dir
            ]
            
            for directory in directories:
                health_info["directories"][str(directory)] = {
                    "exists": directory.exists(),
                    "writable": os.access(directory, os.W_OK) if directory.exists() else False
                }
                
                if not directory.exists():
                    health_info["issues"].append(f"Missing directory: {directory}")
                elif not os.access(directory, os.W_OK):
                    health_info["issues"].append(f"Directory not writable: {directory}")
            
            # Check critical files
            critical_files = [self.backlog_file, self.status_file]
            for file_path in critical_files:
                if file_path.exists():
                    try:
                        # Basic file validation
                        with open(file_path, 'r') as f:
                            json.load(f)
                        health_info["files"][str(file_path)] = {"status": "valid"}
                    except json.JSONDecodeError:
                        health_info["issues"].append(f"Corrupted JSON file: {file_path}")
                        health_info["files"][str(file_path)] = {"status": "corrupted"}
            
            # Calculate disk usage
            if self.orch_state_dir.exists():
                total_size = sum(f.stat().st_size for f in self.orch_state_dir.rglob('*') if f.is_file())
                health_info["disk_usage"]["total_bytes"] = total_size
                health_info["disk_usage"]["total_mb"] = round(total_size / (1024 * 1024), 2)
            
            # Set overall status
            if health_info["issues"]:
                health_info["status"] = "degraded" if len(health_info["issues"]) < 3 else "unhealthy"
            
        except Exception as e:
            health_info["status"] = "error"
            health_info["issues"].append(f"Health check failed: {e}")
            logger.error(f"Storage health check failed: {e}")
        
        return health_info