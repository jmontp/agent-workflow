#!/usr/bin/env python3
"""
Command Execution Integration Tests

Tests for comprehensive command execution flow including:
- All Discord bot commands in web interface
- Parameter validation and error handling
- State machine integration
- Command chaining and workflows
- Performance under load
"""

import pytest
import time
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List
from unittest.mock import Mock, patch, MagicMock

# Add paths for imports
import sys
visualizer_path = Path(__file__).parent.parent.parent / "tools" / "visualizer"
lib_path = Path(__file__).parent.parent.parent / "lib"
sys.path.insert(0, str(visualizer_path))
sys.path.insert(0, str(lib_path))

from app import app, socketio, chat_history
from command_processor import CommandProcessor, process_command


class TestCommandExecutionIntegration:
    """Integration tests for command execution"""
    
    @pytest.fixture(autouse=True)
    def setup_method(self):
        """Setup for each test method"""
        # Clear global state
        chat_history.clear()
        
        # Setup test client
        self.client = app.test_client()
        self.socketio_client = socketio.test_client(app)
        
        # Create command processor
        self.processor = CommandProcessor()
        
        yield
        
        # Cleanup
        if hasattr(self, 'socketio_client') and self.socketio_client.is_connected():
            self.socketio_client.disconnect()


class TestEpicCommands(TestCommandExecutionIntegration):
    """Test /epic command execution and validation"""
    
    def test_epic_command_success(self):
        """Test successful epic creation"""
        with patch.object(self.processor, 'orchestrator') as mock_orchestrator:
            mock_orchestrator.handle_command.return_value = {
                "success": True,
                "stories": ["Story 1", "Story 2", "Story 3"],
                "next_step": "Approve stories with /approve"
            }
            
            result = self.processor.process_command("/epic \"User Authentication System\"", "test_user")
            
            assert result["success"] is True
            assert "Epic Created" in result["response"]
            assert "User Authentication System" in result["response"]
            assert "Proposed Stories" in result["response"]
            assert "Next Step" in result["response"]
            
            mock_orchestrator.handle_command.assert_called_once_with(
                "/epic", "default", description="User Authentication System"
            )
    
    def test_epic_command_validation_errors(self):
        """Test epic command validation"""
        # Test missing description
        result = self.processor.process_command("/epic", "test_user")
        assert result["success"] is False
        assert "Epic description is required" in result["response"]
        
        # Test empty description
        result = self.processor.process_command("/epic \"\"", "test_user")
        assert result["success"] is False
        assert "Epic description is required" in result["response"]
    
    def test_epic_command_orchestrator_error(self):
        """Test epic command when orchestrator returns error"""
        with patch.object(self.processor, 'orchestrator') as mock_orchestrator:
            mock_orchestrator.handle_command.return_value = {
                "success": False,
                "error": "Invalid project state for epic creation"
            }
            
            result = self.processor.process_command("/epic \"Test Epic\"", "test_user")
            
            assert result["success"] is False
            assert "Invalid project state" in result["response"]
    
    def test_epic_command_orchestrator_exception(self):
        """Test epic command when orchestrator throws exception"""
        with patch.object(self.processor, 'orchestrator') as mock_orchestrator:
            mock_orchestrator.handle_command.side_effect = Exception("Database connection failed")
            
            result = self.processor.process_command("/epic \"Test Epic\"", "test_user")
            
            assert result["success"] is False
            assert "Error creating epic" in result["response"]
    
    def test_epic_command_without_orchestrator(self):
        """Test epic command when orchestrator is unavailable"""
        self.processor.orchestrator = None
        
        result = self.processor.process_command("/epic \"Test Epic\"", "test_user")
        
        assert result["success"] is True
        assert "Mock" in result["response"]
        assert result.get("mock") is True


class TestApproveCommands(TestCommandExecutionIntegration):
    """Test /approve command execution and validation"""
    
    def test_approve_command_success(self):
        """Test successful approval of items"""
        with patch.object(self.processor, 'orchestrator') as mock_orchestrator:
            mock_orchestrator.handle_command.return_value = {
                "success": True,
                "approved_items": ["story-1", "story-2"],
                "next_step": "Start sprint with /sprint start"
            }
            
            result = self.processor.process_command("/approve story-1,story-2", "test_user")
            
            assert result["success"] is True
            assert "Approved 2 items" in result["response"]
            assert "story-1" in result["response"]
            assert "story-2" in result["response"]
            assert "Next Step" in result["response"]
    
    def test_approve_command_without_items(self):
        """Test approve command without specific items"""
        with patch.object(self.processor, 'orchestrator') as mock_orchestrator:
            mock_orchestrator.handle_command.return_value = {
                "success": True,
                "approved_items": ["pending-item-1"],
                "next_step": "Items approved"
            }
            
            result = self.processor.process_command("/approve", "test_user")
            
            assert result["success"] is True
            mock_orchestrator.handle_command.assert_called_once_with(
                "/approve", "default", item_ids=[]
            )
    
    def test_approve_command_with_whitespace_ids(self):
        """Test approve command with whitespace in item IDs"""
        with patch.object(self.processor, 'orchestrator') as mock_orchestrator:
            mock_orchestrator.handle_command.return_value = {
                "success": True,
                "approved_items": ["story-1", "story-2"],
                "next_step": "Continue"
            }
            
            result = self.processor.process_command("/approve  story-1 , story-2 ", "test_user")
            
            assert result["success"] is True
            mock_orchestrator.handle_command.assert_called_once_with(
                "/approve", "default", item_ids=["story-1", "story-2"]
            )


class TestSprintCommands(TestCommandExecutionIntegration):
    """Test /sprint command execution and validation"""
    
    def test_sprint_plan_command(self):
        """Test sprint planning command"""
        with patch.object(self.processor, 'orchestrator') as mock_orchestrator:
            mock_orchestrator.handle_command.return_value = {
                "success": True,
                "message": "Sprint planned with 3 stories",
                "next_step": "Start sprint with /sprint start"
            }
            
            result = self.processor.process_command("/sprint plan story-1,story-2,story-3", "test_user")
            
            assert result["success"] is True
            assert "Sprint Plan" in result["response"]
            assert "planned with 3 stories" in result["response"]
            
            mock_orchestrator.handle_command.assert_called_once_with(
                "/sprint plan", "default", story_ids=["story-1", "story-2", "story-3"]
            )
    
    def test_sprint_start_command(self):
        """Test sprint start command"""
        with patch.object(self.processor, 'orchestrator') as mock_orchestrator:
            mock_orchestrator.handle_command.return_value = {
                "success": True,
                "message": "Sprint started successfully",
                "next_step": "Monitor progress with /sprint status"
            }
            
            result = self.processor.process_command("/sprint start", "test_user")
            
            assert result["success"] is True
            assert "Sprint Start" in result["response"]
            assert "started successfully" in result["response"]
    
    def test_sprint_status_command(self):
        """Test sprint status command"""
        with patch.object(self.processor, 'orchestrator') as mock_orchestrator:
            mock_orchestrator.handle_command.return_value = {
                "success": True,
                "total_tasks": 10,
                "completed_tasks": 7,
                "failed_tasks": 1,
                "current_state": "SPRINT_ACTIVE",
                "pending_approvals": 2
            }
            
            result = self.processor.process_command("/sprint status", "test_user")
            
            assert result["success"] is True
            assert "Sprint Status" in result["response"]
            assert "Total Tasks: 10" in result["response"]
            assert "Completed: 7" in result["response"]
            assert "Failed: 1" in result["response"]
            assert "Current State: SPRINT_ACTIVE" in result["response"]
            assert "Pending Approvals: 2" in result["response"]
    
    def test_sprint_pause_and_resume(self):
        """Test sprint pause and resume commands"""
        with patch.object(self.processor, 'orchestrator') as mock_orchestrator:
            # Test pause
            mock_orchestrator.handle_command.return_value = {
                "success": True,
                "message": "Sprint paused",
                "next_step": "Resume with /sprint resume"
            }
            
            result = self.processor.process_command("/sprint pause", "test_user")
            assert result["success"] is True
            assert "Sprint Pause" in result["response"]
            
            # Test resume
            mock_orchestrator.handle_command.return_value = {
                "success": True,
                "message": "Sprint resumed",
                "next_step": "Monitor progress"
            }
            
            result = self.processor.process_command("/sprint resume", "test_user")
            assert result["success"] is True
            assert "Sprint Resume" in result["response"]
    
    def test_sprint_command_state_error(self):
        """Test sprint command with state machine error"""
        with patch.object(self.processor, 'orchestrator') as mock_orchestrator:
            mock_orchestrator.handle_command.return_value = {
                "success": False,
                "error": "Cannot start sprint - no stories planned",
                "hint": "Plan sprint first with /sprint plan",
                "current_state": "IDLE"
            }
            
            result = self.processor.process_command("/sprint start", "test_user")
            
            assert result["success"] is False
            assert "Command Failed" in result["response"]
            assert "Cannot start sprint" in result["response"]
            assert "Suggestion" in result["response"]
            assert "Current State" in result["response"]


class TestBacklogCommands(TestCommandExecutionIntegration):
    """Test /backlog command execution and validation"""
    
    def test_backlog_view_command(self):
        """Test backlog view command"""
        with patch.object(self.processor, 'orchestrator') as mock_orchestrator:
            mock_orchestrator.handle_command.return_value = {
                "success": True,
                "backlog_items": [
                    {"id": "story-1", "title": "User login", "priority": "high"},
                    {"id": "story-2", "title": "Password reset", "priority": "medium"}
                ]
            }
            
            result = self.processor.process_command("/backlog view", "test_user")
            
            assert result["success"] is True
            assert "Backlog View" in result["response"]
    
    def test_backlog_add_story_command(self):
        """Test adding story to backlog"""
        with patch.object(self.processor, 'orchestrator') as mock_orchestrator:
            mock_orchestrator.handle_command.return_value = {
                "success": True,
                "story_id": "story-123",
                "message": "Story added to backlog"
            }
            
            result = self.processor.process_command("/backlog add_story \"New feature description\"", "test_user")
            
            assert result["success"] is True
            assert "Backlog Add_story" in result["response"]
            
            mock_orchestrator.handle_command.assert_called_once_with(
                "/backlog add_story", "default", description="New feature description"
            )
    
    def test_backlog_prioritize_command(self):
        """Test prioritizing backlog items"""
        with patch.object(self.processor, 'orchestrator') as mock_orchestrator:
            mock_orchestrator.handle_command.return_value = {
                "success": True,
                "prioritized_items": ["story-1", "story-2"],
                "message": "Items prioritized"
            }
            
            result = self.processor.process_command("/backlog prioritize story-1,story-2", "test_user")
            
            assert result["success"] is True
            assert "Backlog Prioritize" in result["response"]
            
            mock_orchestrator.handle_command.assert_called_once_with(
                "/backlog prioritize", "default", story_ids=["story-1", "story-2"]
            )


class TestStateCommands(TestCommandExecutionIntegration):
    """Test /state command execution and validation"""
    
    def test_state_command_success(self):
        """Test successful state retrieval"""
        with patch.object(self.processor, 'orchestrator') as mock_orchestrator:
            mock_orchestrator.handle_command.return_value = {
                "success": True,
                "state_info": {
                    "current_state": "SPRINT_ACTIVE",
                    "description": "Sprint is currently running with active tasks",
                    "allowed_commands": ["/sprint status", "/sprint pause", "/approve"]
                },
                "mermaid_diagram": "graph TD; A[IDLE] --> B[SPRINT_ACTIVE]"
            }
            
            result = self.processor.process_command("/state", "test_user")
            
            assert result["success"] is True
            assert "Current Workflow State" in result["response"]
            assert "State: SPRINT_ACTIVE" in result["response"]
            assert "Description:" in result["response"]
            assert "Allowed Commands:" in result["response"]
            assert "/sprint status" in result["response"]
            assert "State Diagram:" in result["response"]
            assert "mermaid" in result["response"]
    
    def test_state_command_minimal_info(self):
        """Test state command with minimal information"""
        with patch.object(self.processor, 'orchestrator') as mock_orchestrator:
            mock_orchestrator.handle_command.return_value = {
                "success": True,
                "state_info": {
                    "current_state": "IDLE"
                }
            }
            
            result = self.processor.process_command("/state", "test_user")
            
            assert result["success"] is True
            assert "State: IDLE" in result["response"]
            assert "Description: No description" in result["response"]


class TestProjectCommands(TestCommandExecutionIntegration):
    """Test /project command execution and validation"""
    
    def test_project_register_command(self):
        """Test project registration command"""
        with patch.object(self.processor, 'orchestrator') as mock_orchestrator:
            mock_orchestrator.handle_command.return_value = {
                "success": True,
                "project_id": "proj-123",
                "message": "Project registered successfully"
            }
            
            result = self.processor.process_command("/project register /path/to/project", "test_user")
            
            assert result["success"] is True
            assert "Project Registered" in result["response"]
            assert "/path/to/project" in result["response"]
            
            mock_orchestrator.handle_command.assert_called_once_with(
                "/project register", "default", path="/path/to/project"
            )
    
    def test_project_register_missing_path(self):
        """Test project register without path"""
        result = self.processor.process_command("/project register", "test_user")
        
        assert result["success"] is False
        assert "Project path is required" in result["response"]
    
    def test_project_unknown_action(self):
        """Test project command with unknown action"""
        result = self.processor.process_command("/project unknown_action", "test_user")
        
        assert result["success"] is False
        assert "Unknown project action" in result["response"]


class TestRequestChangesCommands(TestCommandExecutionIntegration):
    """Test /request_changes command execution and validation"""
    
    def test_request_changes_command(self):
        """Test request changes command"""
        with patch.object(self.processor, 'orchestrator') as mock_orchestrator:
            mock_orchestrator.handle_command.return_value = {
                "success": True,
                "change_request_id": "cr-123",
                "message": "Changes requested"
            }
            
            result = self.processor.process_command("/request_changes \"Please add unit tests\"", "test_user")
            
            assert result["success"] is True
            assert "Changes Requested" in result["response"]
            assert "Please add unit tests" in result["response"]
            
            mock_orchestrator.handle_command.assert_called_once_with(
                "/request_changes", "default", description="Please add unit tests"
            )
    
    def test_request_changes_missing_description(self):
        """Test request changes without description"""
        result = self.processor.process_command("/request_changes", "test_user")
        
        assert result["success"] is False
        assert "Change description is required" in result["response"]


class TestHelpCommands(TestCommandExecutionIntegration):
    """Test /help command execution and validation"""
    
    def test_help_general(self):
        """Test general help command"""
        result = self.processor.process_command("/help", "test_user")
        
        assert result["success"] is True
        assert "Agent Workflow Commands" in result["response"]
        assert "Available Commands:" in result["response"]
        assert "/epic" in result["response"]
        assert "/sprint" in result["response"]
        assert "/help" in result["response"]
        assert "Tips:" in result["response"]
        assert "Project States:" in result["response"]
    
    def test_help_specific_command(self):
        """Test help for specific command"""
        result = self.processor.process_command("/help epic", "test_user")
        
        assert result["success"] is True
        assert "Help: /epic" in result["response"]
        assert "Description:" in result["response"]
        assert "Usage:" in result["response"]
        assert "Examples:" in result["response"]
    
    def test_help_specific_command_with_slash(self):
        """Test help for specific command with slash prefix"""
        result = self.processor.process_command("/help /sprint", "test_user")
        
        assert result["success"] is True
        assert "Help: /sprint" in result["response"]
    
    def test_help_unknown_command(self):
        """Test help for unknown command"""
        result = self.processor.process_command("/help unknown_cmd", "test_user")
        
        assert result["success"] is False
        assert "Unknown command" in result["response"]


class TestCommandValidationAndErrors(TestCommandExecutionIntegration):
    """Test command validation and error scenarios"""
    
    def test_invalid_command_format(self):
        """Test commands that don't start with /"""
        result = self.processor.process_command("epic test", "test_user")
        
        assert result["success"] is False
        assert "Commands must start with `/`" in result["response"]
        assert "Type `/help`" in result["response"]
    
    def test_unknown_command(self):
        """Test completely unknown commands"""
        result = self.processor.process_command("/unknown_command", "test_user")
        
        assert result["success"] is False
        assert "Unknown command" in result["response"]
        assert "/unknown_command" in result["response"]
        assert "suggestions" in result
    
    def test_command_suggestions(self):
        """Test command suggestions for partial matches"""
        result = self.processor.process_command("/sp", "test_user")
        
        assert result["success"] is False
        suggestions = result.get("suggestions", [])
        assert "/sprint" in suggestions
    
    def test_command_pattern_edge_cases(self):
        """Test command pattern matching edge cases"""
        # Test case insensitive matching
        with patch.object(self.processor, 'orchestrator') as mock_orchestrator:
            mock_orchestrator.handle_command.return_value = {"success": True}
            
            result = self.processor.process_command("/HELP", "test_user")
            assert result["success"] is True
            
            result = self.processor.process_command("/Help", "test_user")
            assert result["success"] is True
    
    def test_command_processor_exception_handling(self):
        """Test general exception handling in command processor"""
        with patch.object(self.processor, '_handle_epic_command', side_effect=Exception("Handler crashed")):
            result = self.processor.process_command("/epic \"test\"", "test_user")
            
            assert result["success"] is False
            assert "Error processing command" in result["response"]
            assert "Handler crashed" in result["response"]


class TestCommandPerformance(TestCommandExecutionIntegration):
    """Test command execution performance"""
    
    def test_command_processing_speed(self):
        """Test that commands process within reasonable time"""
        start_time = time.time()
        
        result = self.processor.process_command("/help", "test_user")
        
        end_time = time.time()
        processing_time = end_time - start_time
        
        assert result["success"] is True
        # Should process within 100ms
        assert processing_time < 0.1
    
    def test_concurrent_command_processing(self):
        """Test handling multiple concurrent commands"""
        import threading
        import concurrent.futures
        
        def process_command_thread(command, user_id):
            return self.processor.process_command(command, user_id)
        
        commands = [
            ("/help", "user1"),
            ("/state", "user2"), 
            ("/help epic", "user3"),
            ("/help sprint", "user4"),
            ("/help", "user5")
        ]
        
        start_time = time.time()
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(process_command_thread, cmd, user) for cmd, user in commands]
            results = [future.result() for future in futures]
        
        end_time = time.time()
        
        # All commands should succeed
        for result in results:
            assert result["success"] is True
        
        # Should complete within reasonable time even with concurrency
        assert (end_time - start_time) < 1.0
    
    def test_repeated_command_execution(self):
        """Test repeated execution of same command"""
        # Execute same command multiple times
        for i in range(100):
            result = self.processor.process_command("/help", f"user_{i}")
            assert result["success"] is True
        
        # Processor should remain stable
        assert self.processor.command_patterns is not None
        assert len(self.processor.command_patterns) > 0


class TestCommandChaining(TestCommandExecutionIntegration):
    """Test command chaining and workflow sequences"""
    
    def test_epic_to_sprint_workflow(self):
        """Test typical epic -> approve -> sprint workflow"""
        with patch.object(self.processor, 'orchestrator') as mock_orchestrator:
            # Step 1: Create epic
            mock_orchestrator.handle_command.return_value = {
                "success": True,
                "stories": ["story-1", "story-2"],
                "next_step": "Approve stories with /approve"
            }
            
            result1 = self.processor.process_command("/epic \"Test Feature\"", "test_user")
            assert result1["success"] is True
            
            # Step 2: Approve stories
            mock_orchestrator.handle_command.return_value = {
                "success": True,
                "approved_items": ["story-1", "story-2"],
                "next_step": "Plan sprint with /sprint plan"
            }
            
            result2 = self.processor.process_command("/approve story-1,story-2", "test_user")
            assert result2["success"] is True
            
            # Step 3: Plan sprint
            mock_orchestrator.handle_command.return_value = {
                "success": True,
                "message": "Sprint planned",
                "next_step": "Start sprint with /sprint start"
            }
            
            result3 = self.processor.process_command("/sprint plan story-1,story-2", "test_user")
            assert result3["success"] is True
            
            # Step 4: Start sprint
            mock_orchestrator.handle_command.return_value = {
                "success": True,
                "message": "Sprint started",
                "next_step": "Monitor with /sprint status"
            }
            
            result4 = self.processor.process_command("/sprint start", "test_user")
            assert result4["success"] is True
            
            # Verify all orchestrator calls were made
            assert mock_orchestrator.handle_command.call_count == 4
    
    def test_command_state_dependencies(self):
        """Test commands that depend on specific states"""
        with patch.object(self.processor, 'orchestrator') as mock_orchestrator:
            # Simulate trying to start sprint without planning
            mock_orchestrator.handle_command.return_value = {
                "success": False,
                "error": "Cannot start sprint - no stories planned",
                "hint": "Plan sprint first with /sprint plan",
                "current_state": "IDLE"
            }
            
            result = self.processor.process_command("/sprint start", "test_user")
            
            assert result["success"] is False
            assert "Cannot start sprint" in result["response"]
            assert "Plan sprint first" in result["response"]


def run_command_execution_tests():
    """Run all command execution tests"""
    pytest.main([__file__, "-v", "--tb=short"])


if __name__ == "__main__":
    run_command_execution_tests()