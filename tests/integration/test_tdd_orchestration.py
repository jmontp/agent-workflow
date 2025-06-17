"""
Integration tests for TDD orchestration features.

Tests the integration between the orchestrator, TDD state machine, Discord bot,
and project storage for TDD workflow management.
"""

import pytest
import asyncio
import tempfile
import shutil
from pathlib import Path
from unittest.mock import MagicMock, AsyncMock, patch
import sys

# Add lib directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "lib"))
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "scripts"))

from orchestrator import Orchestrator, Project, OrchestrationMode
from state_machine import StateMachine, State
from tdd_state_machine import TDDStateMachine, TDDState
from tdd_models import TDDCycle, TDDTask
from data_models import ProjectData, Story, StoryStatus
from project_storage import ProjectStorage


class TestTDDOrchestration:
    """Integration tests for TDD orchestration"""
    
    @pytest.fixture
    def temp_project_dir(self):
        """Create a temporary project directory"""
        temp_dir = tempfile.mkdtemp()
        # Create git directory to simulate a git repo
        git_dir = Path(temp_dir) / ".git"
        git_dir.mkdir()
        yield temp_dir
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def mock_agents(self):
        """Mock agents for testing"""
        mock_agents = {
            "DesignAgent": MagicMock(),
            "CodeAgent": MagicMock(),
            "QAAgent": MagicMock(),
            "DataAgent": MagicMock()
        }
        
        # Configure agents with async methods
        for agent in mock_agents.values():
            agent._execute_with_retry = AsyncMock()
            agent._execute_with_retry.return_value.success = True
            agent._execute_with_retry.return_value.output = "Mock agent output"
            agent._execute_with_retry.return_value.error = None
        
        return mock_agents
    
    @pytest.fixture
    def orchestrator(self, temp_project_dir, mock_agents):
        """Create orchestrator with test project"""
        # Create test config
        config_dir = Path(temp_project_dir) / "config"
        config_dir.mkdir()
        
        with patch('orchestrator.get_available_agents', return_value=list(mock_agents.keys())):
            with patch('orchestrator.create_agent', side_effect=lambda agent_type: mock_agents[agent_type]):
                orchestrator = Orchestrator.__new__(Orchestrator)
                orchestrator.config_path = Path("test_config.yaml")
                orchestrator.projects = {}
                orchestrator.agents = mock_agents
                orchestrator.approval_queue = []
                orchestrator.running = False
                
                # Create test project
                storage = ProjectStorage(temp_project_dir)
                storage.initialize_project()
                
                project = Project(
                    name="test_project",
                    path=Path(temp_project_dir),
                    orchestration_mode=OrchestrationMode.AUTONOMOUS,
                    state_machine=StateMachine(),
                    tdd_state_machine=TDDStateMachine(),
                    active_tasks=[],
                    pending_approvals=[],
                    storage=storage
                )
                
                orchestrator.projects["test_project"] = project
                
                # Initialize project data with test story
                project_data = ProjectData()
                test_story = Story(
                    id="TEST-001",
                    title="Test user authentication",
                    description="Implement user login functionality",
                    acceptance_criteria=["User can login with email/password", "Invalid credentials show error"],
                    status=StoryStatus.SPRINT
                )
                project_data.stories.append(test_story)
                storage.save_project_data(project_data)
                
                return orchestrator
    
    @pytest.mark.asyncio
    async def test_tdd_cycle_lifecycle(self, orchestrator):
        """Test complete TDD cycle lifecycle"""
        project = orchestrator.projects["test_project"]
        
        # Test 1: Start TDD cycle
        result = await orchestrator.handle_command(
            "/tdd start", "test_project", 
            story_id="TEST-001", 
            task_description="Implement login validation"
        )
        
        assert result["success"] is True
        assert "cycle_id" in result
        assert result["story_id"] == "TEST-001"
        assert result["current_state"] == "design"
        
        cycle_id = result["cycle_id"]
        
        # Test 2: Check TDD status
        result = await orchestrator.handle_command("/tdd status", "test_project")
        
        assert result["success"] is True
        assert result["cycle_info"]["cycle_id"] == cycle_id
        assert result["current_state"] == "design"
        assert "/tdd test" in result["allowed_commands"]
        
        # Test 3: Transition through TDD states
        # Design -> Test
        result = await orchestrator.handle_command("/tdd test", "test_project")
        assert result["success"] is True
        assert result["current_state"] == "test_red"
        
        # Test -> Code
        result = await orchestrator.handle_command("/tdd code", "test_project")
        assert result["success"] is True
        assert result["current_state"] == "code_green"
        
        # Code -> Refactor
        result = await orchestrator.handle_command("/tdd refactor", "test_project")
        assert result["success"] is True
        assert result["current_state"] == "refactor"
        
        # Refactor -> Commit
        result = await orchestrator.handle_command("/tdd commit", "test_project")
        assert result["success"] is True
        assert result["current_state"] == "commit"
        
        # Test 4: Verify cycle completion
        cycle = project.storage.load_tdd_cycle(cycle_id)
        assert cycle is not None
        assert cycle.get_current_task().is_complete()
    
    @pytest.mark.asyncio
    async def test_tdd_logs_and_overview(self, orchestrator):
        """Test TDD logs and overview commands"""
        project = orchestrator.projects["test_project"]
        
        # Start a TDD cycle first
        await orchestrator.handle_command(
            "/tdd start", "test_project", 
            story_id="TEST-001", 
            task_description="Test task"
        )
        
        # Test logs command
        result = await orchestrator.handle_command("/tdd logs", "test_project")
        
        assert result["success"] is True
        assert "logs_info" in result
        logs_info = result["logs_info"]
        assert "cycle_id" in logs_info
        assert "story_id" in logs_info
        assert logs_info["story_id"] == "TEST-001"
        
        # Test overview command
        result = await orchestrator.handle_command("/tdd overview", "test_project")
        
        assert result["success"] is True
        assert "overview_info" in result
        overview_info = result["overview_info"]
        assert overview_info["active_cycles"] == 1
        assert overview_info["completed_cycles"] == 0
        assert len(overview_info["active_stories"]) > 0
    
    @pytest.mark.asyncio
    async def test_tdd_abort_functionality(self, orchestrator):
        """Test TDD cycle abort functionality"""
        project = orchestrator.projects["test_project"]
        
        # Start TDD cycle
        result = await orchestrator.handle_command(
            "/tdd start", "test_project", 
            story_id="TEST-001"
        )
        cycle_id = result["cycle_id"]
        
        # Abort the cycle
        result = await orchestrator.handle_command("/tdd abort", "test_project")
        
        assert result["success"] is True
        assert "aborted" in result["message"]
        
        # Verify cycle is marked as complete
        cycle = project.storage.load_tdd_cycle(cycle_id)
        assert cycle.is_complete()
        
        # Verify story status updated
        project_data = project.storage.load_project_data()
        story = project_data.get_story_by_id("TEST-001")
        assert story.test_status == "aborted"
    
    @pytest.mark.asyncio
    async def test_tdd_resource_monitoring(self, orchestrator):
        """Test TDD resource usage monitoring"""
        project = orchestrator.projects["test_project"]
        
        # Test resource monitoring method
        resource_info = await orchestrator._monitor_tdd_resource_usage(project)
        
        assert resource_info["success"] is True
        assert "resource_info" in resource_info
        assert "active_cycles" in resource_info["resource_info"]
        assert "max_cycles" in resource_info["resource_info"]
        assert resource_info["resource_info"]["max_cycles"] == 3
    
    @pytest.mark.asyncio
    async def test_tdd_failure_recovery(self, orchestrator):
        """Test TDD failure recovery mechanisms"""
        project = orchestrator.projects["test_project"]
        
        # Start a TDD cycle
        result = await orchestrator.handle_command(
            "/tdd start", "test_project", 
            story_id="TEST-001"
        )
        cycle_id = result["cycle_id"]
        
        # Simulate failure recovery
        error_info = {
            "type": "test_failure",
            "retry_count": 1,
            "error_message": "Test execution failed"
        }
        
        recovery_result = await orchestrator._handle_tdd_failure_recovery(
            project, cycle_id, error_info
        )
        
        assert recovery_result["success"] is True
        assert "recovery_action" in recovery_result
        assert recovery_result["retry_count"] == 2
    
    @pytest.mark.asyncio
    async def test_tdd_agent_handoff(self, orchestrator):
        """Test agent handoffs during TDD transitions"""
        project = orchestrator.projects["test_project"]
        
        # Start TDD cycle
        result = await orchestrator.handle_command(
            "/tdd start", "test_project", 
            story_id="TEST-001"
        )
        cycle_id = result["cycle_id"]
        
        # Test agent handoff
        handoff_result = await orchestrator._coordinate_tdd_agent_handoff(
            project, "design", "test_red", cycle_id
        )
        
        assert handoff_result["success"] is True
        # Should create handoff from DesignAgent to QAAgent
        assert "DesignAgent" in handoff_result["message"]
        assert "QAAgent" in handoff_result["message"]
    
    @pytest.mark.asyncio
    async def test_tdd_state_machine_integration(self, orchestrator):
        """Test TDD state machine integration with main workflow"""
        project = orchestrator.projects["test_project"]
        
        # Set sprint to active state
        project.state_machine.force_state(State.SPRINT_ACTIVE)
        
        # Start TDD cycle - should register with main state machine
        result = await orchestrator.handle_command(
            "/tdd start", "test_project", 
            story_id="TEST-001"
        )
        
        assert result["success"] is True
        
        # Check that TDD cycle is tracked in main state machine
        tdd_status = project.state_machine.get_tdd_workflow_status()
        assert tdd_status["active_tdd_cycles"] == 1
        assert "TEST-001" in tdd_status["tdd_cycles_by_story"]
        assert tdd_status["sprint_tdd_coordination"]["sprint_allows_tdd"] is True
    
    @pytest.mark.asyncio
    async def test_multiple_concurrent_tdd_cycles(self, orchestrator):
        """Test handling multiple concurrent TDD cycles"""
        project = orchestrator.projects["test_project"]
        
        # Add another story
        project_data = project.storage.load_project_data()
        story2 = Story(
            id="TEST-002",
            title="Test user registration",
            description="Implement user signup",
            acceptance_criteria=["User can register with email"],
            status=StoryStatus.SPRINT
        )
        project_data.stories.append(story2)
        project.storage.save_project_data(project_data)
        
        # Start first TDD cycle
        result1 = await orchestrator.handle_command(
            "/tdd start", "test_project", 
            story_id="TEST-001"
        )
        assert result1["success"] is True
        
        # Start second TDD cycle
        result2 = await orchestrator.handle_command(
            "/tdd start", "test_project", 
            story_id="TEST-002"
        )
        assert result2["success"] is True
        
        # Check overview shows both cycles
        result = await orchestrator.handle_command("/tdd overview", "test_project")
        overview_info = result["overview_info"]
        assert overview_info["active_cycles"] == 2
        assert len(overview_info["active_stories"]) == 2
    
    def test_tdd_data_model_enhancements(self, orchestrator):
        """Test TDD-enhanced data models"""
        project = orchestrator.projects["test_project"]
        project_data = project.storage.load_project_data()
        
        # Test TDD settings
        assert project_data.is_tdd_enabled() is True
        assert project_data.get_max_concurrent_tdd_cycles() == 3
        assert project_data.get_coverage_threshold() == 80.0
        
        # Test test directory configuration
        tdd_dir = project_data.get_test_directory_for_type("tdd")
        assert tdd_dir == "tests/tdd"
        
        unit_dir = project_data.get_test_directory_for_type("unit")
        assert unit_dir == "tests/unit"
        
        # Test stories ready for TDD
        ready_stories = project_data.get_stories_ready_for_tdd()
        assert len(ready_stories) == 1  # TEST-001 has acceptance criteria
        assert ready_stories[0].id == "TEST-001"
    
    def test_project_storage_tdd_enhancements(self, orchestrator):
        """Test enhanced project storage for TDD"""
        project = orchestrator.projects["test_project"]
        storage = project.storage
        
        # Test TDD metrics storage
        test_metrics = {
            "total_cycles": 5,
            "success_rate": 0.8,
            "average_coverage": 85.5
        }
        storage.save_tdd_metrics(test_metrics)
        loaded_metrics = storage.load_tdd_metrics()
        assert loaded_metrics == test_metrics
        
        # Test test file tracking
        storage.track_test_file("TEST-001", "/path/to/test_auth.py", "created")
        tracked_files = storage.get_tracked_test_files("TEST-001")
        assert len(tracked_files) == 1
        assert tracked_files[0]["file_path"] == "/path/to/test_auth.py"
        assert tracked_files[0]["status"] == "created"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])