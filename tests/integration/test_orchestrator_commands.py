"""
Integration tests for Orchestrator command handling.

Tests the complete workflow from command input through orchestrator
processing to agent coordination and state transitions.
"""

import unittest
import asyncio
import tempfile
import json
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock

import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "scripts"))
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "lib"))

from orchestrator import Orchestrator, OrchestrationMode
from state_machine import State


class TestOrchestratorCommands(unittest.TestCase):
    """Integration tests for orchestrator command handling"""
    
    def setUp(self):
        """Set up test orchestrator with temporary directory"""
        self.temp_dir = tempfile.mkdtemp()
        self.config_path = Path(self.temp_dir) / "test_projects.yaml"
        
        # Create test configuration
        test_config = {
            "projects": [
                {
                    "name": "test_project",
                    "path": str(self.temp_dir / "test_project"),
                    "orchestration": "blocking"
                }
            ]
        }
        
        import yaml
        with open(self.config_path, 'w') as f:
            yaml.dump(test_config, f)
        
        # Create project directory
        project_dir = Path(self.temp_dir) / "test_project"
        project_dir.mkdir(exist_ok=True)
        
        # Initialize orchestrator
        self.orchestrator = Orchestrator(str(self.config_path))
    
    def tearDown(self):
        """Clean up temporary files"""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    async def test_epic_command_workflow(self):
        """Test complete /epic command workflow"""
        # Test epic creation
        result = await self.orchestrator.handle_command(
            "/epic",
            "test_project",
            description="Build authentication system"
        )
        
        self.assertTrue(result["success"])
        self.assertIn("Epic created", result["message"])
        self.assertIn("stories", result)
        self.assertIn("next_step", result)
        
        # Verify state transition
        project = self.orchestrator.projects["test_project"]
        self.assertEqual(project.state_machine.current_state, State.BACKLOG_READY)
    
    async def test_approve_command_workflow(self):
        """Test /approve command workflow"""
        # First create an epic to have something to approve
        await self.orchestrator.handle_command(
            "/epic",
            "test_project", 
            description="Test epic"
        )
        
        # Add some pending approvals
        project = self.orchestrator.projects["test_project"]
        project.pending_approvals = ["AUTH-1", "AUTH-2"]
        
        # Test approval
        result = await self.orchestrator.handle_command(
            "/approve",
            "test_project",
            item_ids=["AUTH-1", "AUTH-2"]
        )
        
        self.assertTrue(result["success"])
        self.assertEqual(len(result["approved_items"]), 2)
        self.assertEqual(len(project.pending_approvals), 0)
    
    async def test_sprint_plan_workflow(self):
        """Test /sprint plan command workflow"""
        # Set up prerequisite state
        project = self.orchestrator.projects["test_project"]
        project.state_machine.force_state(State.BACKLOG_READY)
        
        # Test sprint planning
        result = await self.orchestrator.handle_command(
            "/sprint plan",
            "test_project",
            story_ids=["AUTH-1", "AUTH-2"]
        )
        
        self.assertTrue(result["success"])
        self.assertIn("Sprint planned", result["message"])
        self.assertEqual(project.state_machine.current_state, State.SPRINT_PLANNED)
    
    async def test_sprint_start_workflow(self):
        """Test /sprint start command workflow"""
        # Set up prerequisite state
        project = self.orchestrator.projects["test_project"]
        project.state_machine.force_state(State.SPRINT_PLANNED)
        
        # Test sprint start
        result = await self.orchestrator.handle_command(
            "/sprint start",
            "test_project"
        )
        
        self.assertTrue(result["success"])
        self.assertIn("Sprint started", result["message"])
        self.assertEqual(project.state_machine.current_state, State.SPRINT_ACTIVE)
        self.assertGreater(len(project.active_tasks), 0)
    
    async def test_sprint_status_workflow(self):
        """Test /sprint status command workflow"""
        # Set up prerequisite state
        project = self.orchestrator.projects["test_project"]
        project.state_machine.force_state(State.SPRINT_ACTIVE)
        
        # Test sprint status
        result = await self.orchestrator.handle_command(
            "/sprint status",
            "test_project"
        )
        
        self.assertTrue(result["success"])
        self.assertIn("total_tasks", result)
        self.assertIn("completed_tasks", result)
        self.assertIn("current_state", result)
    
    async def test_state_command_workflow(self):
        """Test /state command workflow"""
        result = await self.orchestrator.handle_command(
            "/state",
            "test_project"
        )
        
        self.assertTrue(result["success"])
        self.assertIn("state_info", result)
        self.assertIn("project_status", result)
        self.assertIn("mermaid_diagram", result)
        
        # Verify state info structure
        state_info = result["state_info"]
        self.assertIn("current_state", state_info)
        self.assertIn("allowed_commands", state_info)
        self.assertIn("transition_matrix", state_info)
    
    async def test_invalid_command_handling(self):
        """Test invalid command handling"""
        result = await self.orchestrator.handle_command(
            "/invalid_command",
            "test_project"
        )
        
        self.assertFalse(result["success"])
        self.assertIn("error", result)
        self.assertIn("Unknown command", result["error"])
    
    async def test_invalid_state_transition(self):
        """Test invalid state transition handling"""
        # Try to start sprint without planning
        project = self.orchestrator.projects["test_project"]
        project.state_machine.force_state(State.IDLE)
        
        result = await self.orchestrator.handle_command(
            "/sprint start",
            "test_project"
        )
        
        self.assertFalse(result["success"])
        self.assertIn("error", result)
        self.assertIn("hint", result)
        self.assertIn("current_state", result)
        self.assertIn("allowed_commands", result)
    
    async def test_nonexistent_project(self):
        """Test command on nonexistent project"""
        result = await self.orchestrator.handle_command(
            "/epic",
            "nonexistent_project",
            description="Test epic"
        )
        
        self.assertFalse(result["success"])
        self.assertIn("Project not found", result["error"])
        self.assertIn("available_projects", result)
    
    async def test_backlog_commands_workflow(self):
        """Test backlog command workflows"""
        # Test view backlog
        result = await self.orchestrator.handle_command(
            "/backlog view",
            "test_project"
        )
        
        self.assertTrue(result["success"])
        self.assertIn("items", result)
        
        # Test add story
        result = await self.orchestrator.handle_command(
            "/backlog add_story",
            "test_project",
            description="New user story",
            feature="AUTH"
        )
        
        self.assertTrue(result["success"])
        self.assertIn("story_id", result)
        
        # Test prioritize story
        result = await self.orchestrator.handle_command(
            "/backlog prioritize",
            "test_project",
            story_id="AUTH-1",
            priority="high"
        )
        
        self.assertTrue(result["success"])
    
    async def test_orchestration_modes(self):
        """Test different orchestration modes"""
        # Test blocking mode (default)
        project = self.orchestrator.projects["test_project"]
        self.assertEqual(project.orchestration_mode, OrchestrationMode.BLOCKING)
        
        # Create task and verify it goes to approval queue
        from agents import Task
        task = Task(
            id="test_task",
            agent_type="DesignAgent",
            command="Test command",
            context={}
        )
        
        result = await self.orchestrator._dispatch_task(task, project)
        self.assertTrue(result.success)
        self.assertIn("queued for approval", result.output)
        self.assertIn(task.id, project.pending_approvals)


class TestOrchestratorStateManagement(unittest.TestCase):
    """Test orchestrator state persistence and recovery"""
    
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.config_path = Path(self.temp_dir) / "test_projects.yaml"
        
        # Create test configuration
        test_config = {
            "projects": [
                {
                    "name": "test_project",
                    "path": str(self.temp_dir / "test_project"),
                    "orchestration": "blocking"
                }
            ]
        }
        
        import yaml
        with open(self.config_path, 'w') as f:
            yaml.dump(test_config, f)
        
        # Create project directory
        project_dir = Path(self.temp_dir) / "test_project"
        project_dir.mkdir(exist_ok=True)
    
    def tearDown(self):
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    async def test_state_persistence(self):
        """Test state is persisted to disk"""
        orchestrator = Orchestrator(str(self.config_path))
        
        # Execute command that changes state
        await orchestrator.handle_command(
            "/epic",
            "test_project",
            description="Test epic"
        )
        
        # Verify state file was created
        project = orchestrator.projects["test_project"]
        state_file = project.path / ".orch-state" / "status.json"
        self.assertTrue(state_file.exists())
        
        # Verify state content
        with open(state_file, 'r') as f:
            state_data = json.load(f)
        
        self.assertEqual(state_data["current_state"], "BACKLOG_READY")
        self.assertEqual(state_data["name"], "test_project")
    
    async def test_state_recovery(self):
        """Test state is recovered on orchestrator restart"""
        # First orchestrator instance
        orchestrator1 = Orchestrator(str(self.config_path))
        await orchestrator1.handle_command(
            "/epic",
            "test_project",
            description="Test epic"
        )
        
        project1 = orchestrator1.projects["test_project"]
        original_state = project1.state_machine.current_state
        
        # Create second orchestrator instance (simulating restart)
        orchestrator2 = Orchestrator(str(self.config_path))
        project2 = orchestrator2.projects["test_project"]
        
        # Verify state was recovered
        self.assertEqual(project2.state_machine.current_state, original_state)


class TestOrchestratorErrorHandling(unittest.TestCase):
    """Test orchestrator error handling and resilience"""
    
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.orchestrator = Orchestrator()  # Use default configuration
    
    def tearDown(self):
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    async def test_missing_command_parameters(self):
        """Test handling of missing required parameters"""
        # Epic without description
        result = await self.orchestrator.handle_command(
            "/epic",
            "default"
        )
        
        self.assertFalse(result["success"])
        self.assertIn("description is required", result["error"])
    
    async def test_agent_failure_handling(self):
        """Test handling of agent execution failures"""
        # Mock agent failure
        with patch.object(self.orchestrator.agents["DesignAgent"], "_execute_with_retry") as mock_execute:
            mock_execute.return_value = AsyncMock(success=False, error="Agent failed")
            
            # This would normally succeed but agent fails
            result = await self.orchestrator.handle_command(
                "/epic",
                "default",
                description="Test epic"
            )
            
            # Should still succeed at orchestrator level even if agent fails
            self.assertTrue(result["success"])
    
    async def test_concurrent_command_handling(self):
        """Test concurrent command execution"""
        # Execute multiple commands concurrently
        tasks = [
            self.orchestrator.handle_command("/state", "default"),
            self.orchestrator.handle_command("/state", "default"),
            self.orchestrator.handle_command("/state", "default")
        ]
        
        results = await asyncio.gather(*tasks)
        
        # All should succeed
        for result in results:
            self.assertTrue(result["success"])


def run_async_test(coro):
    """Helper to run async tests"""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


# Convert async test methods to sync for unittest
def make_sync_test(async_method):
    def sync_method(self):
        return run_async_test(async_method(self))
    return sync_method


# Apply sync wrapper to all async test methods
for test_class in [TestOrchestratorCommands, TestOrchestratorStateManagement, TestOrchestratorErrorHandling]:
    for attr_name in dir(test_class):
        attr = getattr(test_class, attr_name)
        if attr_name.startswith('test_') and asyncio.iscoroutinefunction(attr):
            setattr(test_class, attr_name, make_sync_test(attr))


if __name__ == "__main__":
    unittest.main()