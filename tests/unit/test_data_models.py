"""
Unit tests for Data Models.

Tests the core data models used for epic, story, and sprint management
in the AI Agent TDD-Scrum workflow system.
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent.parent))

from lib.data_models import Epic, Story, Sprint, EpicStatus, StoryStatus, SprintStatus, ProjectData


class TestStatuses:
    """Test the status enums."""
    
    def test_epic_status_values(self):
        """Test EpicStatus enum values."""
        assert EpicStatus.ACTIVE.value == "active"
        assert EpicStatus.COMPLETED.value == "completed"
        assert EpicStatus.ARCHIVED.value == "archived"
    
    def test_story_status_values(self):
        """Test StoryStatus enum values."""
        assert StoryStatus.BACKLOG.value == "backlog"
        assert StoryStatus.SPRINT.value == "sprint"
        assert StoryStatus.IN_PROGRESS.value == "in_progress"
        assert StoryStatus.DONE.value == "done"
    
    def test_sprint_status_values(self):
        """Test SprintStatus enum values."""
        assert SprintStatus.PLANNED.value == "planned"
        assert SprintStatus.ACTIVE.value == "active"
        assert SprintStatus.COMPLETED.value == "completed"


class TestEpic:
    """Test the Epic data model."""
    
    def test_epic_creation_with_defaults(self):
        """Test creating an Epic with default values."""
        epic = Epic(
            title="Build Authentication System",
            description="Implement user authentication and authorization"
        )
        
        assert epic.title == "Build Authentication System"
        assert epic.description == "Implement user authentication and authorization"
        assert epic.status == EpicStatus.ACTIVE
        assert isinstance(epic.id, str)
        assert isinstance(epic.created_at, str)
        assert epic.tdd_requirements == []
        assert epic.tdd_constraints == {}

    def test_epic_creation_with_custom_values(self):
        """Test creating an Epic with custom values."""
        epic = Epic(
            id="EPIC-2",
            title="Custom Epic",
            description="Custom description",
            status=EpicStatus.COMPLETED,
            tdd_requirements=["requirement1", "requirement2"],
            tdd_constraints={"constraint": "value"}
        )
        
        assert epic.id == "EPIC-2"
        assert epic.status == EpicStatus.COMPLETED
        assert epic.tdd_requirements == ["requirement1", "requirement2"]
        assert epic.tdd_constraints == {"constraint": "value"}

    def test_epic_serialization(self):
        """Test epic serialization to dictionary."""
        epic = Epic(
            id="EPIC-1",
            title="Test Epic",
            description="Test description",
            status=EpicStatus.ACTIVE,
            tdd_requirements=["req1"]
        )
        
        data = epic.to_dict()
        
        assert data["id"] == "EPIC-1"
        assert data["title"] == "Test Epic"
        assert data["status"] == "active"
        assert data["tdd_requirements"] == ["req1"]
        assert isinstance(data["created_at"], str)

    def test_epic_deserialization(self):
        """Test epic deserialization from dictionary."""
        data = {
            "id": "EPIC-1",
            "title": "Test Epic",
            "description": "Test description",
            "status": "active",
            "created_at": "2024-01-01T12:00:00",
            "tdd_requirements": ["req1", "req2"],
            "tdd_constraints": {"constraint": "value"}
        }
        
        epic = Epic.from_dict(data)
        
        assert epic.id == "EPIC-1"
        assert epic.title == "Test Epic"
        assert epic.status == EpicStatus.ACTIVE
        assert epic.tdd_requirements == ["req1", "req2"]
        assert epic.tdd_constraints == {"constraint": "value"}


class TestStory:
    """Test the Story data model."""
    
    def test_story_creation_with_defaults(self):
        """Test creating a Story with default values."""
        story = Story(
            title="User Login",
            description="As a user, I want to log in to access my account",
            epic_id="EPIC-1"
        )
        
        assert story.title == "User Login"
        assert story.description == "As a user, I want to log in to access my account"
        assert story.epic_id == "EPIC-1"
        assert story.status == StoryStatus.BACKLOG
        assert story.priority == 3
        assert isinstance(story.id, str)
        assert isinstance(story.created_at, str)
        assert story.sprint_id is None
        assert story.tdd_cycle_id is None
        assert story.test_status == "not_started"
        assert story.ci_status == "not_run"
        assert story.test_coverage == 0.0

    def test_story_creation_with_custom_values(self):
        """Test creating a Story with custom values."""
        story = Story(
            id="STORY-2",
            title="Custom Story",
            description="Custom description",
            epic_id="EPIC-1",
            status=StoryStatus.IN_PROGRESS,
            priority=1,
            sprint_id="SPRINT-1",
            tdd_cycle_id="CYCLE-1",
            test_status="green",
            ci_status="passed",
            test_coverage=85.5,
            acceptance_criteria=["AC1", "AC2"],
            test_files=["test1.py", "test2.py"]
        )
        
        assert story.id == "STORY-2"
        assert story.status == StoryStatus.IN_PROGRESS
        assert story.priority == 1
        assert story.sprint_id == "SPRINT-1"
        assert story.tdd_cycle_id == "CYCLE-1"
        assert story.test_status == "green"
        assert story.ci_status == "passed"
        assert story.test_coverage == 85.5
        assert story.acceptance_criteria == ["AC1", "AC2"]
        assert story.test_files == ["test1.py", "test2.py"]

    def test_story_serialization(self):
        """Test story serialization to dictionary."""
        story = Story(
            id="STORY-1",
            title="Test Story",
            description="Test description",
            epic_id="EPIC-1",
            status=StoryStatus.IN_PROGRESS,
            acceptance_criteria=["AC1"],
            test_files=["test.py"]
        )
        
        data = story.to_dict()
        
        assert data["id"] == "STORY-1"
        assert data["title"] == "Test Story"
        assert data["epic_id"] == "EPIC-1"
        assert data["status"] == "in_progress"
        assert data["acceptance_criteria"] == ["AC1"]
        assert data["test_files"] == ["test.py"]

    def test_story_deserialization(self):
        """Test story deserialization from dictionary."""
        data = {
            "id": "STORY-1",
            "title": "Test Story",
            "description": "Test description",
            "epic_id": "EPIC-1",
            "status": "in_progress",
            "priority": 1,
            "created_at": "2024-01-01T12:00:00",
            "sprint_id": "SPRINT-1",
            "tdd_cycle_id": "CYCLE-1",
            "test_status": "green",
            "ci_status": "passed",
            "test_coverage": 80.0,
            "acceptance_criteria": ["AC1", "AC2"],
            "test_files": ["test1.py"]
        }
        
        story = Story.from_dict(data)
        
        assert story.id == "STORY-1"
        assert story.title == "Test Story"
        assert story.epic_id == "EPIC-1"
        assert story.status == StoryStatus.IN_PROGRESS
        assert story.priority == 1
        assert story.sprint_id == "SPRINT-1"
        assert story.tdd_cycle_id == "CYCLE-1"
        assert story.test_status == "green"
        assert story.ci_status == "passed"
        assert story.test_coverage == 80.0
        assert story.acceptance_criteria == ["AC1", "AC2"]
        assert story.test_files == ["test1.py"]


class TestSprint:
    """Test the Sprint data model."""
    
    def test_sprint_creation_with_defaults(self):
        """Test creating a Sprint with default values."""
        sprint = Sprint(
            goal="Implement user authentication features"
        )
        
        assert sprint.goal == "Implement user authentication features"
        assert sprint.status == SprintStatus.PLANNED
        assert sprint.story_ids == []
        assert isinstance(sprint.id, str)
        assert isinstance(sprint.created_at, str)
        assert sprint.start_date is None
        assert sprint.end_date is None
        assert sprint.active_tdd_cycles == []
        assert sprint.tdd_metrics == {}

    def test_sprint_creation_with_custom_values(self):
        """Test creating a Sprint with custom values."""
        sprint = Sprint(
            id="SPRINT-2",
            goal="Custom goal",
            status=SprintStatus.ACTIVE,
            start_date="2024-01-01T00:00:00",
            end_date="2024-01-14T23:59:59",
            story_ids=["STORY-1", "STORY-2"],
            active_tdd_cycles=["CYCLE-1"],
            tdd_metrics={"coverage": 85.0}
        )
        
        assert sprint.id == "SPRINT-2"
        assert sprint.status == SprintStatus.ACTIVE
        assert sprint.start_date == "2024-01-01T00:00:00"
        assert sprint.end_date == "2024-01-14T23:59:59"
        assert sprint.story_ids == ["STORY-1", "STORY-2"]
        assert sprint.active_tdd_cycles == ["CYCLE-1"]
        assert sprint.tdd_metrics == {"coverage": 85.0}

    def test_sprint_serialization(self):
        """Test sprint serialization to dictionary."""
        sprint = Sprint(
            id="SPRINT-1",
            goal="Test goal",
            status=SprintStatus.ACTIVE,
            story_ids=["STORY-1"],
            active_tdd_cycles=["CYCLE-1"]
        )
        
        data = sprint.to_dict()
        
        assert data["id"] == "SPRINT-1"
        assert data["goal"] == "Test goal"
        assert data["status"] == "active"
        assert data["story_ids"] == ["STORY-1"]
        assert data["active_tdd_cycles"] == ["CYCLE-1"]

    def test_sprint_deserialization(self):
        """Test sprint deserialization from dictionary."""
        data = {
            "id": "SPRINT-1",
            "goal": "Test goal",
            "status": "active",
            "created_at": "2024-01-01T12:00:00",
            "start_date": "2024-01-01T00:00:00",
            "end_date": "2024-01-14T23:59:59",
            "story_ids": ["STORY-1", "STORY-2"],
            "active_tdd_cycles": ["CYCLE-1"],
            "tdd_metrics": {"coverage": 85.0}
        }
        
        sprint = Sprint.from_dict(data)
        
        assert sprint.id == "SPRINT-1"
        assert sprint.goal == "Test goal"
        assert sprint.status == SprintStatus.ACTIVE
        assert sprint.start_date == "2024-01-01T00:00:00"
        assert sprint.end_date == "2024-01-14T23:59:59"
        assert sprint.story_ids == ["STORY-1", "STORY-2"]
        assert sprint.active_tdd_cycles == ["CYCLE-1"]
        assert sprint.tdd_metrics == {"coverage": 85.0}


class TestProjectData:
    """Test the ProjectData container class."""
    
    def test_project_data_creation_with_defaults(self):
        """Test creating ProjectData with default values."""
        project_data = ProjectData()
        
        assert project_data.epics == []
        assert project_data.stories == []
        assert project_data.sprints == []
        assert "enabled" in project_data.tdd_settings
        assert project_data.tdd_settings["enabled"] is True

    def test_project_data_with_content(self):
        """Test ProjectData with epics, stories, and sprints."""
        epic = Epic(id="EPIC-1", title="Test Epic", description="Test")
        story = Story(id="STORY-1", title="Test Story", description="Test", epic_id="EPIC-1")
        sprint = Sprint(id="SPRINT-1", goal="Test Sprint")
        
        project_data = ProjectData(
            epics=[epic],
            stories=[story],
            sprints=[sprint]
        )
        
        assert len(project_data.epics) == 1
        assert len(project_data.stories) == 1
        assert len(project_data.sprints) == 1
        assert project_data.epics[0].id == "EPIC-1"
        assert project_data.stories[0].id == "STORY-1"
        assert project_data.sprints[0].id == "SPRINT-1"

    def test_get_epic_by_id(self):
        """Test finding epic by ID."""
        epic = Epic(id="EPIC-1", title="Test Epic", description="Test")
        project_data = ProjectData(epics=[epic])
        
        found_epic = project_data.get_epic_by_id("EPIC-1")
        assert found_epic is not None
        assert found_epic.id == "EPIC-1"
        
        not_found = project_data.get_epic_by_id("EPIC-999")
        assert not_found is None

    def test_get_story_by_id(self):
        """Test finding story by ID."""
        story = Story(id="STORY-1", title="Test Story", description="Test")
        project_data = ProjectData(stories=[story])
        
        found_story = project_data.get_story_by_id("STORY-1")
        assert found_story is not None
        assert found_story.id == "STORY-1"
        
        not_found = project_data.get_story_by_id("STORY-999")
        assert not_found is None

    def test_get_sprint_by_id(self):
        """Test finding sprint by ID."""
        sprint = Sprint(id="SPRINT-1", goal="Test Sprint")
        project_data = ProjectData(sprints=[sprint])
        
        found_sprint = project_data.get_sprint_by_id("SPRINT-1")
        assert found_sprint is not None
        assert found_sprint.id == "SPRINT-1"
        
        not_found = project_data.get_sprint_by_id("SPRINT-999")
        assert not_found is None

    def test_get_backlog_stories(self):
        """Test getting stories in backlog."""
        story1 = Story(id="STORY-1", title="Backlog Story", status=StoryStatus.BACKLOG)
        story2 = Story(id="STORY-2", title="Sprint Story", status=StoryStatus.SPRINT)
        project_data = ProjectData(stories=[story1, story2])
        
        backlog_stories = project_data.get_backlog_stories()
        assert len(backlog_stories) == 1
        assert backlog_stories[0].id == "STORY-1"

    def test_get_active_sprint(self):
        """Test getting active sprint."""
        sprint1 = Sprint(id="SPRINT-1", goal="Planned Sprint", status=SprintStatus.PLANNED)
        sprint2 = Sprint(id="SPRINT-2", goal="Active Sprint", status=SprintStatus.ACTIVE)
        project_data = ProjectData(sprints=[sprint1, sprint2])
        
        active_sprint = project_data.get_active_sprint()
        assert active_sprint is not None
        assert active_sprint.id == "SPRINT-2"

    def test_tdd_settings(self):
        """Test TDD settings functionality."""
        project_data = ProjectData()
        
        # Test default settings
        assert project_data.is_tdd_enabled() is True
        assert project_data.get_max_concurrent_tdd_cycles() == 3
        assert project_data.get_coverage_threshold() == 80.0
        
        # Test custom settings
        project_data.update_tdd_settings({"enabled": False, "max_concurrent_cycles": 5})
        assert project_data.is_tdd_enabled() is False
        assert project_data.get_max_concurrent_tdd_cycles() == 5

    def test_project_data_serialization(self):
        """Test ProjectData serialization."""
        epic = Epic(id="EPIC-1", title="Test Epic", description="Test")
        project_data = ProjectData(epics=[epic])
        
        data = project_data.to_dict()
        
        assert "epics" in data
        assert "stories" in data
        assert "sprints" in data
        assert "tdd_settings" in data
        assert len(data["epics"]) == 1
        assert data["epics"][0]["id"] == "EPIC-1"


class TestDataModelsEdgeCases:
    """Test edge cases and additional coverage for data models."""
    
    def test_epic_tdd_requirements_handling(self):
        """Test epic TDD requirements and constraints"""
        epic = Epic(
            title="TDD Epic",
            tdd_requirements=["100% test coverage", "BDD scenarios"],
            tdd_constraints={"framework": "pytest", "timeout": 30}
        )
        
        # Test serialization includes TDD fields
        data = epic.to_dict()
        assert data["tdd_requirements"] == ["100% test coverage", "BDD scenarios"]
        assert data["tdd_constraints"] == {"framework": "pytest", "timeout": 30}
        
        # Test deserialization
        epic_restored = Epic.from_dict(data)
        assert epic_restored.tdd_requirements == ["100% test coverage", "BDD scenarios"]
        assert epic_restored.tdd_constraints == {"framework": "pytest", "timeout": 30}
    
    def test_story_tdd_fields_comprehensive(self):
        """Test story TDD-specific fields comprehensively"""
        story = Story(
            title="TDD Story",
            tdd_cycle_id="cycle-123",
            test_status="green",
            test_files=["test_feature.py", "test_integration.py"],
            ci_status="passed", 
            test_coverage=95.5
        )
        
        # Verify all TDD fields
        assert story.tdd_cycle_id == "cycle-123"
        assert story.test_status == "green"
        assert story.test_files == ["test_feature.py", "test_integration.py"]
        assert story.ci_status == "passed"
        assert story.test_coverage == 95.5
        
        # Test serialization roundtrip
        data = story.to_dict()
        story_restored = Story.from_dict(data)
        
        assert story_restored.tdd_cycle_id == "cycle-123"
        assert story_restored.test_files == ["test_feature.py", "test_integration.py"]
        assert story_restored.ci_status == "passed"
        assert story_restored.test_coverage == 95.5
    
    def test_sprint_with_retrospective(self):
        """Test sprint with retrospective data"""
        retrospective = Retrospective(
            what_went_well=["Good test coverage", "Fast feedback"],
            what_to_improve=["More integration tests"],
            action_items=["Setup CI/CD pipeline"]
        )
        
        sprint = Sprint(
            goal="Complete authentication",
            retrospective=retrospective,
            active_tdd_cycles=["cycle-1", "cycle-2"],
            tdd_metrics={"total_cycles": 5, "success_rate": 0.8}
        )
        
        # Test serialization with retrospective
        data = sprint.to_dict()
        assert "retrospective" in data
        assert data["retrospective"]["what_went_well"] == ["Good test coverage", "Fast feedback"]
        assert data["active_tdd_cycles"] == ["cycle-1", "cycle-2"]
        assert data["tdd_metrics"]["success_rate"] == 0.8
        
        # Test deserialization
        sprint_restored = Sprint.from_dict(data)
        assert sprint_restored.retrospective is not None
        assert sprint_restored.retrospective.what_went_well == ["Good test coverage", "Fast feedback"]
        assert sprint_restored.active_tdd_cycles == ["cycle-1", "cycle-2"]
    
    def test_sprint_without_retrospective(self):
        """Test sprint serialization without retrospective"""
        sprint = Sprint(goal="Test sprint")
        
        # Should not include retrospective in serialization
        data = sprint.to_dict()
        assert "retrospective" not in data
        
        # Deserialization should work without retrospective
        sprint_restored = Sprint.from_dict(data)
        assert sprint_restored.retrospective is None
    
    def test_project_data_missing_tdd_settings_fallback(self):
        """Test ProjectData fallback when TDD settings are missing"""
        # Simulate data without TDD settings
        data = {
            "epics": [],
            "stories": [],
            "sprints": []
            # No tdd_settings
        }
        
        project_data = ProjectData.from_dict(data)
        
        # Should use defaults
        assert project_data.tdd_settings["enabled"] is True
        assert project_data.tdd_settings["max_concurrent_cycles"] == 3
        assert "test_directory_structure" in project_data.tdd_settings
    
    def test_all_models_have_unique_ids(self):
        """Test that all models generate unique IDs"""
        # Test multiple instances get unique IDs
        epics = [Epic(title=f"Epic {i}") for i in range(5)]
        stories = [Story(title=f"Story {i}") for i in range(5)]
        sprints = [Sprint(goal=f"Sprint {i}") for i in range(5)]
        
        # All IDs should be unique
        epic_ids = [epic.id for epic in epics]
        story_ids = [story.id for story in stories]
        sprint_ids = [sprint.id for sprint in sprints]
        
        assert len(set(epic_ids)) == 5
        assert len(set(story_ids)) == 5
        assert len(set(sprint_ids)) == 5
        
        # IDs should follow expected pattern
        for epic_id in epic_ids:
            assert epic_id.startswith("epic-")
        for story_id in story_ids:
            assert story_id.startswith("story-")
        for sprint_id in sprint_ids:
            assert sprint_id.startswith("sprint-")