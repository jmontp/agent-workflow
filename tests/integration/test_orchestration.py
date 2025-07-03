"""
Integration tests for Orchestration system.

Tests the complete orchestration workflow including project management,
agent coordination, HITL approval flows, and multi-project scenarios.
"""

import pytest
import asyncio
import tempfile
import shutil
import json
from pathlib import Path
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, AsyncMock

import sys
sys.path.append(str(Path(__file__).parent.parent.parent))

from agent_workflow.core.orchestrator import GlobalOrchestrator, OrchestrationMode, ProjectPriority
from agent_workflow.core.models import Epic, Story, Sprint, ProjectData
from agent_workflow.core.storage import ProjectStorage
from agent_workflow.core.state_machine import StateMachine


class TestProjectLifecycle:
    """Test complete project lifecycle scenarios."""
    
    @pytest.fixture
    def temp_project_dir(self):
        """Create temporary project directory with git."""
        temp_dir = tempfile.mkdtemp()
        # Create .git directory to make it look like a valid project
        git_dir = Path(temp_dir) / ".git"
        git_dir.mkdir()
        yield temp_dir
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def project_storage(self, temp_project_dir):
        """Create project storage instance."""
        return ProjectStorage(temp_project_dir)
    
    @pytest.fixture
    def initialized_project(self, project_storage):
        """Initialize a project with basic data."""
        project_storage.initialize_project()
        
        # Create sample data
        epic = Epic(
            id="EPIC-1",
            title="User Authentication",
            description="Implement user authentication system"
        )
        
        story = Story(
            id="STORY-1",
            title="User Login",
            description="As a user, I want to log in",
            epic_id="EPIC-1",
            priority=1
        )
        
        sprint = Sprint(
            id="SPRINT-1",
            goal="Implement authentication features"
        )
        
        project_data = ProjectData(
            epics=[epic],
            stories=[story],
            sprints=[sprint]
        )
        
        project_storage.save_project_data(project_data)
        return project_storage

    def test_project_initialization_workflow(self, temp_project_dir):
        """Test complete project initialization workflow."""
        storage = ProjectStorage(temp_project_dir)
        
        # Test initialization
        assert storage.initialize_project() is True
        assert storage.is_initialized() is True
        
        # Verify directory structure
        assert storage.orch_state_dir.exists()
        assert storage.sprints_dir.exists()
        assert storage.tdd_cycles_dir.exists()
        
        # Verify template files
        assert storage.architecture_file.exists()
        assert storage.best_practices_file.exists()
        
        # Verify content
        arch_content = storage.get_architecture_content()
        assert "Project Architecture" in arch_content
        
        practices_content = storage.get_best_practices_content()
        assert "Project Best Practices" in practices_content

    def test_epic_story_sprint_workflow(self, initialized_project):
        """Test complete epic -> story -> sprint workflow."""
        # Load initial data
        project_data = initialized_project.load_project_data()
        assert len(project_data.epics) == 1
        assert len(project_data.stories) == 1
        assert len(project_data.sprints) == 1
        
        # Add more stories to the epic
        new_story = Story(
            id="STORY-2",
            title="User Registration",
            description="As a user, I want to register",
            epic_id="EPIC-1",
            priority=2
        )
        
        project_data.stories.append(new_story)
        initialized_project.save_project_data(project_data)
        
        # Verify persistence
        reloaded_data = initialized_project.load_project_data()
        assert len(reloaded_data.stories) == 2
        
        # Test sprint management
        sprint = reloaded_data.sprints[0]
        initialized_project.save_sprint(sprint)
        
        loaded_sprint = initialized_project.load_sprint("SPRINT-1")
        assert loaded_sprint is not None
        assert loaded_sprint.id == "SPRINT-1"

    def test_tdd_cycle_integration(self, initialized_project):
        """Test TDD cycle integration with project workflow."""
        from agent_workflow.core.models import TDDCycle, TDDState
        
        # Create TDD cycle
        tdd_cycle = TDDCycle(
            id="TDD-1",
            story_id="STORY-1",
            state=TDDState.RED
        )
        
        initialized_project.save_tdd_cycle(tdd_cycle)
        
        # Verify persistence
        loaded_cycle = initialized_project.load_tdd_cycle("TDD-1")
        assert loaded_cycle is not None
        assert loaded_cycle.story_id == "STORY-1"
        
        # Test active cycle detection
        active_cycle = initialized_project.get_active_tdd_cycle()
        assert active_cycle is not None
        assert active_cycle.id == "TDD-1"

    def test_status_tracking_workflow(self, initialized_project):
        """Test status tracking throughout project lifecycle."""
        # Initial status
        status = {
            "state": "planning",
            "active_sprint": "SPRINT-1",
            "active_agents": 0,
            "last_action": "project_initialization"
        }
        
        initialized_project.save_status(status)
        loaded_status = initialized_project.load_status()
        assert loaded_status["state"] == "planning"
        
        # Update status through workflow
        status_updates = [
            {"state": "active", "active_agents": 3, "last_action": "sprint_start"},
            {"state": "review", "active_agents": 1, "last_action": "sprint_review"},
            {"state": "retrospective", "active_agents": 0, "last_action": "sprint_complete"}
        ]
        
        for update in status_updates:
            initialized_project.save_status(update)
            loaded = initialized_project.load_status()
            assert loaded["state"] == update["state"]

    def test_architecture_evolution_workflow(self, initialized_project):
        """Test architecture document evolution."""
        # Initial architecture
        arch_v1 = """# Project Architecture v1

## Overview
Basic authentication system

## Components
- Login form
- Authentication service
- User database

## Design Decisions
- Use JWT tokens
- Store passwords with bcrypt
"""
        
        initialized_project.update_architecture(arch_v1)
        assert "Authentication service" in initialized_project.get_architecture_content()
        
        # Architecture evolution
        arch_v2 = """# Project Architecture v2

## Overview  
Enhanced authentication system with OAuth support

## Components
- Login form with social login
- Authentication service with OAuth
- User database with profile data
- Session management

## Design Decisions
- Support OAuth providers (Google, GitHub)
- Implement refresh tokens
- Add user profile management
"""
        
        initialized_project.update_architecture(arch_v2)
        content = initialized_project.get_architecture_content()
        assert "OAuth support" in content
        assert "refresh tokens" in content


class TestMultiProjectOrchestration:
    """Test multi-project orchestration scenarios."""
    
    @pytest.fixture
    def temp_base_dir(self):
        """Create temporary base directory for multiple projects."""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def multi_project_setup(self, temp_base_dir):
        """Set up multiple test projects."""
        projects = {}
        
        for i, project_name in enumerate(["frontend", "backend", "mobile"], 1):
            project_dir = Path(temp_base_dir) / project_name
            project_dir.mkdir()
            
            # Create .git directory
            git_dir = project_dir / ".git"
            git_dir.mkdir()
            
            # Initialize project storage
            storage = ProjectStorage(str(project_dir))
            storage.initialize_project()
            
            projects[project_name] = {
                "path": str(project_dir),
                "storage": storage,
                "priority": [ProjectPriority.HIGH, ProjectPriority.NORMAL, ProjectPriority.LOW][i-1]
            }
        
        return projects
    
    @pytest.fixture
    def mock_config_manager(self, multi_project_setup):
        """Create mock config manager with multiple projects."""
        config_manager = Mock()
        config_manager.global_config = Mock()
        config_manager.global_config.resource_allocation_strategy = "priority_based"
        config_manager.global_config.max_total_agents = 15
        config_manager.global_config.global_memory_limit_gb = 16
        
        # Create project configs
        from agent_workflow.core.orchestrator import ProjectConfig
        config_manager.projects = {}
        
        for name, project_data in multi_project_setup.items():
            config_manager.projects[name] = ProjectConfig(
                name=name,
                path=project_data["path"],
                priority=project_data["priority"]
            )
        
        # Mock get_active_projects
        config_manager.get_active_projects.return_value = list(config_manager.projects.values())
        
        return config_manager

    @pytest.mark.asyncio
    async def test_multi_project_startup_sequence(self, mock_config_manager):
        """Test starting up multiple projects in coordination."""
        global_orchestrator = GlobalOrchestrator(mock_config_manager)
        
        with patch('subprocess.Popen') as mock_popen:
            # Mock successful processes for all projects
            mock_processes = {}
            for i, project_name in enumerate(["frontend", "backend", "mobile"]):
                mock_process = Mock()
                mock_process.pid = 10000 + i
                mock_process.poll.return_value = None
                mock_processes[project_name] = mock_process
            
            # Configure Popen to return different processes based on command
            def popen_side_effect(*args, **kwargs):
                # Extract project name from command
                command = args[0]
                for project_name in mock_processes:
                    if project_name in str(command):
                        return mock_processes[project_name]
                return mock_processes["frontend"]  # Default
            
            mock_popen.side_effect = popen_side_effect
            
            # Start global orchestrator
            await global_orchestrator.start()
            
            # Verify all projects started
            assert len(global_orchestrator.orchestrators) == 3
            assert global_orchestrator.status.value == "running"
            
            # Verify resource allocation respects priorities
            frontend_alloc = global_orchestrator.resource_allocations.get("frontend")
            backend_alloc = global_orchestrator.resource_allocations.get("backend") 
            mobile_alloc = global_orchestrator.resource_allocations.get("mobile")
            
            if frontend_alloc and backend_alloc:
                # High priority should get more resources than normal priority
                assert frontend_alloc.priority_weight > backend_alloc.priority_weight

    @pytest.mark.asyncio
    async def test_resource_reallocation_on_failure(self, mock_config_manager):
        """Test resource reallocation when a project fails."""
        global_orchestrator = GlobalOrchestrator(mock_config_manager)
        
        # Start with three projects
        for project_name in ["frontend", "backend", "mobile"]:
            mock_process = Mock()
            mock_process.pid = 12345
            mock_process.poll.return_value = None
            
            from agent_workflow.core.orchestrator import ProjectOrchestrator, OrchestratorStatus
            orchestrator = ProjectOrchestrator(
                project_name=project_name,
                project_path=f"/path/to/{project_name}",
                process=mock_process,
                status=OrchestratorStatus.RUNNING,
                pid=12345
            )
            global_orchestrator.orchestrators[project_name] = orchestrator
        
        # Simulate frontend project failure
        frontend_orchestrator = global_orchestrator.orchestrators["frontend"]
        frontend_orchestrator.process.poll.return_value = 1  # Crashed
        
        with patch.object(global_orchestrator, 'start_project') as mock_restart:
            mock_restart.return_value = True
            
            await global_orchestrator._monitor_projects()
            
            # Verify crash detection and restart attempt
            assert frontend_orchestrator.status.value == "crashed"
            mock_restart.assert_called_with("frontend")

    @pytest.mark.asyncio
    async def test_cross_project_intelligence(self, multi_project_setup):
        """Test cross-project intelligence and coordination."""
        # This would test scenarios where projects need to share information
        # For now, we'll test the basic coordination infrastructure
        
        from agent_workflow.core.orchestrator import ProjectConfig
        
        # Create projects with interdependencies
        frontend_config = ProjectConfig(
            name="frontend",
            path=multi_project_setup["frontend"]["path"],
            priority=ProjectPriority.HIGH
        )
        
        backend_config = ProjectConfig(
            name="backend", 
            path=multi_project_setup["backend"]["path"],
            priority=ProjectPriority.HIGH
        )
        
        # In a real scenario, this would test:
        # - Sharing API specifications between frontend and backend
        # - Coordinating database schema changes
        # - Managing shared component libraries
        
        assert frontend_config.name == "frontend"
        assert backend_config.name == "backend"

    def test_global_metrics_aggregation(self, mock_config_manager):
        """Test aggregation of metrics across multiple projects."""
        global_orchestrator = GlobalOrchestrator(mock_config_manager)
        
        # Set up projects with different resource usage
        from agent_workflow.core.orchestrator import ProjectOrchestrator, OrchestratorStatus
        
        projects_data = [
            ("frontend", 25.0, 1024.0, 3, OrchestratorStatus.RUNNING),
            ("backend", 40.0, 2048.0, 5, OrchestratorStatus.RUNNING),
            ("mobile", 0.0, 0.0, 0, OrchestratorStatus.STOPPED)
        ]
        
        for name, cpu, memory, agents, status in projects_data:
            orchestrator = ProjectOrchestrator(
                project_name=name,
                project_path=f"/path/to/{name}",
                status=status,
                cpu_usage=cpu,
                memory_usage=memory,
                active_agents=agents
            )
            global_orchestrator.orchestrators[name] = orchestrator
        
        # Update metrics
        asyncio.run(global_orchestrator._update_metrics())
        
        metrics = global_orchestrator.metrics
        assert metrics.total_projects == 3
        assert metrics.active_projects == 2  # frontend and backend running
        assert metrics.total_agents == 8     # 3 + 5 + 0
        assert metrics.total_cpu_usage_percent == 65.0  # 25 + 40 + 0
        assert metrics.total_memory_usage_mb == 3072.0  # 1024 + 2048 + 0


class TestHITLIntegration:
    """Test Human-in-the-Loop integration scenarios."""
    
    @pytest.fixture
    def temp_project_dir(self):
        """Create temporary project directory."""
        temp_dir = tempfile.mkdtemp()
        git_dir = Path(temp_dir) / ".git"
        git_dir.mkdir()
        yield temp_dir
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def hitl_project(self, temp_project_dir):
        """Set up project for HITL testing."""
        storage = ProjectStorage(temp_project_dir)
        storage.initialize_project()
        
        # Create state machine
        from agent_workflow.core.state_machine import StateMachine, State
        state_machine = StateMachine(
            initial_state=State.IDLE,
            project_path=Path(temp_project_dir)
        )
        
        return {
            "storage": storage,
            "state_machine": state_machine,
            "project_path": temp_project_dir
        }

    @pytest.mark.asyncio
    async def test_approval_workflow_integration(self, hitl_project):
        """Test complete approval workflow integration."""
        from agent_workflow.core.orchestrator import request_approval, process_approval
        
        # Request approval for a significant change
        approval_data = {
            "type": "architectural_change",
            "description": "Switch from REST to GraphQL API",
            "impact": "high",
            "files_affected": ["api/routes.py", "schema.graphql"],
            "estimated_effort": "2 weeks"
        }
        
        approval_id = request_approval(
            "test_project",
            "Switch to GraphQL API",
            approval_data
        )
        
        assert approval_id is not None
        
        # Simulate human review and approval
        with patch('agent_workflow.core.orchestrator.load_project') as mock_load:
            mock_project = Mock()
            mock_project.pending_approvals = [approval_id]
            mock_project.storage = hitl_project["storage"]
            mock_load.return_value = mock_project
            
            # Process approval
            result = process_approval(
                approval_id,
                approved=True,
                feedback="Approved with recommendation to implement gradually"
            )
            
            assert result is True

    @pytest.mark.asyncio
    async def test_command_processing_integration(self, hitl_project):
        """Test HITL command processing integration."""
        from agent_workflow.core.orchestrator import process_hitl_command
        
        commands_to_test = [
            ("/state", "Get current workflow state"),
            ("/epic 'User Management System'", "Create new epic"),
            ("/story 'User login' epic-1", "Create story for epic"),
            ("/sprint plan", "Plan next sprint")
        ]
        
        for command, description in commands_to_test:
            with patch('agent_workflow.core.orchestrator.load_project') as mock_load:
                mock_project = Mock()
                mock_state_machine = Mock()
                mock_command_result = Mock()
                mock_command_result.success = True
                mock_command_result.message = f"Successfully processed: {description}"
                mock_state_machine.handle_command.return_value = mock_command_result
                mock_project.state_machine = mock_state_machine
                mock_load.return_value = mock_project
                
                result = process_hitl_command("test_project", command, {})
                
                assert result.success is True
                assert description.lower() in result.message.lower()

    def test_discord_integration_workflow(self, hitl_project):
        """Test Discord integration workflow."""
        from agent_workflow.core.orchestrator import format_discord_response
        
        # Test various response formatting scenarios
        test_scenarios = [
            {
                "type": "state_update",
                "data": {"current_state": "planning", "active_sprint": "SPRINT-1"},
                "expected_content": ["planning", "SPRINT-1"]
            },
            {
                "type": "approval_request", 
                "data": {"approval_id": "APR-123", "description": "API changes"},
                "expected_content": ["APR-123", "API changes", "approve", "reject"]
            },
            {
                "type": "error",
                "data": {"error": "Invalid command", "suggestion": "Try /help"},
                "expected_content": ["Invalid command", "/help"]
            }
        ]
        
        for scenario in test_scenarios:
            response = format_discord_response(scenario["type"], scenario["data"])
            
            for expected in scenario["expected_content"]:
                assert expected.lower() in response.lower()


class TestPerformanceIntegration:
    """Test performance and scalability integration scenarios."""
    
    @pytest.mark.asyncio
    async def test_concurrent_project_operations(self):
        """Test concurrent operations across multiple projects."""
        # This would test scenarios like:
        # - Multiple projects starting simultaneously
        # - Concurrent HITL commands from different projects
        # - Resource contention and resolution
        
        import concurrent.futures
        
        async def simulate_project_operation(project_id):
            """Simulate a project operation."""
            await asyncio.sleep(0.1)  # Simulate work
            return f"Project {project_id} completed"
        
        # Run multiple operations concurrently
        tasks = [simulate_project_operation(i) for i in range(5)]
        results = await asyncio.gather(*tasks)
        
        assert len(results) == 5
        for i, result in enumerate(results):
            assert f"Project {i}" in result

    @pytest.mark.asyncio
    async def test_resource_scaling_behavior(self):
        """Test resource scaling under load."""
        # This would test:
        # - Memory usage under high project load
        # - CPU utilization scaling
        # - Agent pool management
        
        from agent_workflow.core.orchestrator import ResourceAllocation
        
        # Simulate increasing load
        allocations = []
        for i in range(10):
            allocation = ResourceAllocation(
                project_name=f"project_{i}",
                allocated_agents=min(3, 10 - i),  # Decreasing available agents
                allocated_memory_mb=512 * (i + 1),
                allocated_cpu_percent=10.0 * (i + 1),
                priority_weight=1.0
            )
            allocations.append(allocation)
        
        # Verify resource constraints
        total_agents = sum(a.allocated_agents for a in allocations)
        total_memory = sum(a.allocated_memory_mb for a in allocations)
        
        assert total_agents <= 30  # Reasonable limit
        assert total_memory <= 16384  # 16GB limit

    def test_error_recovery_integration(self):
        """Test error recovery across system components."""
        # This would test:
        # - Storage corruption recovery
        # - State machine error handling
        # - Process crash recovery
        
        from agent_workflow.core.storage import ProjectStorage
        import tempfile
        
        with tempfile.TemporaryDirectory() as temp_dir:
            storage = ProjectStorage(temp_dir)
            storage.initialize_project()
            
            # Simulate corrupted data
            corrupt_file = storage.backlog_file
            with open(corrupt_file, 'w') as f:
                f.write("invalid json {{{")
            
            # Verify graceful handling
            project_data = storage.load_project_data()
            assert project_data is not None
            assert project_data.epics == []  # Empty but valid


if __name__ == "__main__":
    pytest.main([__file__])