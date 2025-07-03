"""
Multi-Project Configuration System

Manages configuration, discovery, and metadata for multiple projects
in the AI Agent TDD-Scrum workflow orchestration system.
"""

import os
import yaml
import json
import logging
from typing import Dict, List, Optional, Any, Set
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from pathlib import Path
from enum import Enum

logger = logging.getLogger(__name__)


class ProjectPriority(Enum):
    """Priority levels for project resource allocation"""
    CRITICAL = "critical"    # Production issues, urgent deadlines
    HIGH = "high"           # Important features, key milestones
    NORMAL = "normal"       # Regular development work
    LOW = "low"            # Maintenance, nice-to-have features


class ProjectStatus(Enum):
    """Current status of projects"""
    ACTIVE = "active"           # Actively being worked on
    PAUSED = "paused"          # Temporarily suspended
    MAINTENANCE = "maintenance" # Minimal activity, bug fixes only
    ARCHIVED = "archived"       # Completed or discontinued
    INITIALIZING = "initializing" # Being set up


@dataclass
class ProjectDependency:
    """Dependency relationship between projects"""
    target_project: str
    dependency_type: str  # "blocks", "enhances", "integrates_with"
    description: str
    criticality: str = "medium"  # "low", "medium", "high", "critical"


@dataclass
class ResourceLimits:
    """Resource allocation limits for a project"""
    max_parallel_agents: int = 3
    max_parallel_cycles: int = 2
    max_memory_mb: int = 1024
    max_disk_mb: int = 2048
    cpu_priority: float = 1.0  # Relative CPU priority (0.1 to 2.0)


@dataclass
class ProjectConfig:
    """Configuration for a single project"""
    name: str
    path: str
    git_url: Optional[str] = None
    description: str = ""
    priority: ProjectPriority = ProjectPriority.NORMAL
    status: ProjectStatus = ProjectStatus.ACTIVE
    
    # Team and ownership
    owner: Optional[str] = None
    team: List[str] = field(default_factory=list)
    slack_channel: Optional[str] = None
    discord_channel: Optional[str] = None
    
    # Resource allocation
    resource_limits: ResourceLimits = field(default_factory=ResourceLimits)
    
    # Dependencies and relationships
    dependencies: List[ProjectDependency] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    
    # Scheduling and workflow
    work_hours: Dict[str, str] = field(default_factory=lambda: {
        "timezone": "UTC",
        "start": "09:00",
        "end": "17:00",
        "days": ["monday", "tuesday", "wednesday", "thursday", "friday"]
    })
    
    # AI and automation settings
    ai_settings: Dict[str, Any] = field(default_factory=lambda: {
        "auto_approve_low_risk": True,
        "max_auto_retry": 3,
        "require_human_review": False,
        "context_sharing_enabled": True
    })
    
    # Metadata
    created_at: datetime = field(default_factory=datetime.utcnow)
    last_activity: Optional[datetime] = None
    version: str = "1.0"


@dataclass
class GlobalOrchestratorConfig:
    """Global configuration for multi-project orchestration"""
    # Global settings
    max_total_agents: int = 20
    max_concurrent_projects: int = 10
    resource_allocation_strategy: str = "fair_share"  # "fair_share", "priority_based", "dynamic"
    
    # Global resource limits
    global_memory_limit_gb: int = 8
    global_cpu_cores: int = 4
    global_disk_limit_gb: int = 50
    
    # Scheduling and coordination
    scheduling_interval_seconds: int = 30
    health_check_interval_seconds: int = 60
    resource_rebalance_interval_seconds: int = 300
    
    # Cross-project features
    enable_knowledge_sharing: bool = True
    enable_pattern_learning: bool = True
    enable_cross_project_insights: bool = True
    
    # Discord and monitoring
    global_discord_guild: Optional[str] = None
    monitoring_webhook_url: Optional[str] = None
    alert_channels: List[str] = field(default_factory=list)
    
    # Storage and persistence
    global_state_path: str = ".orch-global"
    backup_retention_days: int = 30
    enable_cloud_backup: bool = False
    
    # Security and access control
    enable_project_isolation: bool = True
    enable_audit_logging: bool = True
    secret_management_provider: str = "local"  # "local", "vault", "aws_secrets"


class MultiProjectConfigManager:
    """
    Manages configuration for multiple projects and global orchestration settings.
    
    Handles project discovery, registration, configuration validation,
    and provides a unified interface for multi-project management.
    """
    
    def __init__(self, config_path: str = "config.yml"):
        """
        Initialize multi-project configuration manager.
        
        Args:
            config_path: Path to the global configuration file
        """
        self.config_path = Path(config_path)
        self.global_config: Optional[GlobalOrchestratorConfig] = None
        self.projects: Dict[str, ProjectConfig] = {}
        self.config_watchers: List[callable] = []
        
        # Load configuration if it exists
        if self.config_path.exists():
            self.load_configuration()
        else:
            self._create_default_configuration()
    
    def load_configuration(self) -> None:
        """Load configuration from disk"""
        try:
            with open(self.config_path, 'r') as f:
                config_data = yaml.safe_load(f)
            
            # Load global configuration
            global_config_data = config_data.get('global', {})
            self.global_config = GlobalOrchestratorConfig(**global_config_data)
            
            # Load project configurations
            projects_data = config_data.get('projects', {})
            self.projects = {}
            
            for project_name, project_data in projects_data.items():
                # Convert nested dictionaries to dataclass objects
                if 'resource_limits' in project_data:
                    project_data['resource_limits'] = ResourceLimits(**project_data['resource_limits'])
                
                if 'dependencies' in project_data:
                    dependencies = []
                    for dep_data in project_data['dependencies']:
                        dependencies.append(ProjectDependency(**dep_data))
                    project_data['dependencies'] = dependencies
                
                # Handle datetime fields
                if 'created_at' in project_data:
                    project_data['created_at'] = datetime.fromisoformat(project_data['created_at'])
                if 'last_activity' in project_data and project_data['last_activity']:
                    project_data['last_activity'] = datetime.fromisoformat(project_data['last_activity'])
                
                # Convert enum fields
                if 'priority' in project_data:
                    project_data['priority'] = ProjectPriority(project_data['priority'])
                if 'status' in project_data:
                    project_data['status'] = ProjectStatus(project_data['status'])
                
                self.projects[project_name] = ProjectConfig(name=project_name, **project_data)
            
            logger.info(f"Loaded configuration for {len(self.projects)} projects")
            
        except Exception as e:
            logger.error(f"Failed to load configuration: {str(e)}")
            self._create_default_configuration()
    
    def save_configuration(self) -> None:
        """Save current configuration to disk"""
        try:
            config_data = {
                'global': asdict(self.global_config),
                'projects': {}
            }
            
            # Convert projects to serializable format
            for project_name, project in self.projects.items():
                project_dict = asdict(project)
                
                # Convert datetime objects to ISO format
                if project_dict['created_at']:
                    project_dict['created_at'] = project.created_at.isoformat()
                if project_dict['last_activity']:
                    project_dict['last_activity'] = project.last_activity.isoformat()
                
                # Convert enums to values
                project_dict['priority'] = project.priority.value
                project_dict['status'] = project.status.value
                
                config_data['projects'][project_name] = project_dict
            
            # Create backup of existing configuration
            if self.config_path.exists():
                backup_path = self.config_path.with_suffix('.yaml.backup')
                self.config_path.rename(backup_path)
            
            # Save new configuration
            with open(self.config_path, 'w') as f:
                yaml.dump(config_data, f, default_flow_style=False, indent=2)
            
            logger.info("Configuration saved successfully")
            
        except Exception as e:
            logger.error(f"Failed to save configuration: {str(e)}")
            raise
    
    def register_project(
        self,
        name: str,
        path: str,
        **kwargs
    ) -> ProjectConfig:
        """
        Register a new project in the orchestration system.
        
        Args:
            name: Unique project name
            path: Absolute path to project directory
            **kwargs: Additional project configuration options
            
        Returns:
            ProjectConfig object for the registered project
        """
        if name in self.projects:
            raise ValueError(f"Project '{name}' is already registered")
        
        # Validate project path
        project_path = Path(path).resolve()
        if not project_path.exists():
            raise ValueError(f"Project path does not exist: {path}")
        
        # Create project configuration
        project_config = ProjectConfig(
            name=name,
            path=str(project_path),
            **kwargs
        )
        
        # Initialize project state directory
        state_dir = project_path / ".orch-state"
        state_dir.mkdir(exist_ok=True)
        
        # Create project-specific configuration file
        project_config_path = state_dir / "project-config.json"
        with open(project_config_path, 'w') as f:
            json.dump(asdict(project_config), f, indent=2, default=str)
        
        self.projects[name] = project_config
        self.save_configuration()
        
        logger.info(f"Registered project '{name}' at {path}")
        return project_config
    
    def discover_projects(self, search_paths: List[str]) -> List[Dict[str, str]]:
        """
        Discover potential projects in the specified paths.
        
        Args:
            search_paths: List of directory paths to search
            
        Returns:
            List of discovered project information
        """
        discovered = []
        
        for search_path in search_paths:
            search_dir = Path(search_path)
            if not search_dir.exists():
                continue
            
            # Look for git repositories and existing orch-state directories
            for item in search_dir.iterdir():
                if not item.is_dir():
                    continue
                
                project_info = {
                    'name': item.name,
                    'path': str(item.resolve()),
                    'type': 'unknown'
                }
                
                # Check for git repository
                if (item / ".git").exists():
                    project_info['type'] = 'git'
                    
                    # Try to get git remote URL
                    try:
                        import subprocess
                        result = subprocess.run(
                            ['git', 'remote', 'get-url', 'origin'],
                            cwd=item,
                            capture_output=True,
                            text=True
                        )
                        if result.returncode == 0:
                            project_info['git_url'] = result.stdout.strip()
                    except:
                        pass
                
                # Check for existing orchestration state
                if (item / ".orch-state").exists():
                    project_info['type'] = 'orch_existing'
                    
                    # Try to load existing configuration
                    config_file = item / ".orch-state" / "project-config.json"
                    if config_file.exists():
                        try:
                            with open(config_file, 'r') as f:
                                existing_config = json.load(f)
                            project_info['existing_config'] = existing_config
                        except:
                            pass
                
                # Check for common project indicators
                indicators = {
                    'package.json': 'nodejs',
                    'requirements.txt': 'python',
                    'Cargo.toml': 'rust',
                    'pom.xml': 'java',
                    'go.mod': 'go'
                }
                
                for indicator, project_type in indicators.items():
                    if (item / indicator).exists():
                        project_info['language'] = project_type
                        break
                
                discovered.append(project_info)
        
        return discovered
    
    def get_project(self, name: str) -> Optional[ProjectConfig]:
        """Get project configuration by name"""
        return self.projects.get(name)
    
    def list_projects(self) -> List[ProjectConfig]:
        """Get list of all registered projects"""
        return list(self.projects.values())
    
    def get_active_projects(self) -> List[ProjectConfig]:
        """Get list of currently active projects"""
        return [p for p in self.projects.values() if p.status == ProjectStatus.ACTIVE]
    
    def update_project_status(self, name: str, status: ProjectStatus) -> None:
        """Update project status"""
        if name not in self.projects:
            raise ValueError(f"Project '{name}' not found")
        
        self.projects[name].status = status
        self.projects[name].last_activity = datetime.utcnow()
        self.save_configuration()
    
    def add_project_dependency(
        self,
        project_name: str,
        target_project: str,
        dependency_type: str,
        description: str,
        criticality: str = "medium"
    ) -> None:
        """Add dependency relationship between projects"""
        if project_name not in self.projects:
            raise ValueError(f"Project '{project_name}' not found")
        if target_project not in self.projects:
            raise ValueError(f"Target project '{target_project}' not found")
        
        dependency = ProjectDependency(
            target_project=target_project,
            dependency_type=dependency_type,
            description=description,
            criticality=criticality
        )
        
        self.projects[project_name].dependencies.append(dependency)
        self.save_configuration()
    
    def get_project_dependencies(self, name: str) -> List[str]:
        """Get list of projects that this project depends on"""
        if name not in self.projects:
            return []
        
        return [dep.target_project for dep in self.projects[name].dependencies]
    
    def get_dependent_projects(self, name: str) -> List[str]:
        """Get list of projects that depend on this project"""
        dependents = []
        for project_name, project in self.projects.items():
            if any(dep.target_project == name for dep in project.dependencies):
                dependents.append(project_name)
        return dependents
    
    def validate_configuration(self) -> List[str]:
        """
        Validate the current configuration and return list of issues.
        
        Returns:
            List of validation error messages
        """
        issues = []
        
        # Validate global configuration
        if not self.global_config:
            issues.append("Global configuration is missing")
            return issues
        
        # Check resource limits make sense
        if self.global_config.max_concurrent_projects > self.global_config.max_total_agents:
            issues.append("Max concurrent projects exceeds max total agents")
        
        # Validate projects
        project_names = set()
        project_paths = set()
        
        for name, project in self.projects.items():
            # Check for duplicate names
            if name in project_names:
                issues.append(f"Duplicate project name: {name}")
            project_names.add(name)
            
            # Check for duplicate paths
            if project.path in project_paths:
                issues.append(f"Duplicate project path: {project.path}")
            project_paths.add(project.path)
            
            # Validate project path exists
            if not Path(project.path).exists():
                issues.append(f"Project path does not exist: {project.path} ({name})")
            
            # Validate dependencies exist
            for dep in project.dependencies:
                if dep.target_project not in self.projects:
                    issues.append(f"Project {name} depends on non-existent project: {dep.target_project}")
            
            # Check for circular dependencies
            if self._has_circular_dependency(name, set()):
                issues.append(f"Circular dependency detected involving project: {name}")
        
        return issues
    
    def _has_circular_dependency(self, project_name: str, visited: Set[str]) -> bool:
        """Check for circular dependencies starting from a project"""
        if project_name in visited:
            return True
        
        if project_name not in self.projects:
            return False
        
        visited.add(project_name)
        
        for dep in self.projects[project_name].dependencies:
            if self._has_circular_dependency(dep.target_project, visited.copy()):
                return True
        
        return False
    
    def _create_default_configuration(self) -> None:
        """Create default configuration"""
        self.global_config = GlobalOrchestratorConfig()
        self.projects = {}
        
        # Save default configuration
        try:
            self.save_configuration()
            logger.info("Created default configuration")
        except Exception as e:
            logger.error(f"Failed to create default configuration: {str(e)}")
    
    def export_configuration(self, export_path: str) -> None:
        """Export configuration to a file"""
        config_data = {
            'global': asdict(self.global_config),
            'projects': {name: asdict(project) for name, project in self.projects.items()}
        }
        
        with open(export_path, 'w') as f:
            json.dump(config_data, f, indent=2, default=str)
    
    def import_configuration(self, import_path: str) -> None:
        """Import configuration from a file"""
        with open(import_path, 'r') as f:
            config_data = json.load(f)
        
        # This would need more sophisticated merging logic in practice
        logger.warning("Configuration import is not fully implemented")