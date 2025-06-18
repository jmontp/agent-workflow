"""
Comprehensive test suite for DesignAgent in agents/design_agent.py

Tests design agent functionality including architecture creation, design review,
TDD specifications, acceptance criteria, test scenarios, and API contracts.
"""

import pytest
import asyncio
import json
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from datetime import datetime
from typing import Dict, Any, List

# Import the modules under test
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "lib"))

from agents.design_agent import DesignAgent
from agents import Task, AgentResult, TaskStatus, TDDState, TDDCycle, TDDTask


class TestDesignAgentInitialization:
    """Test DesignAgent initialization and basic properties"""
    
    def test_design_agent_initialization_default(self):
        """Test DesignAgent initialization with default parameters"""
        agent = DesignAgent()
        
        assert agent.name == "DesignAgent"
        assert "system_architecture" in agent.capabilities
        assert "component_design" in agent.capabilities
        assert "tdd_specification" in agent.capabilities
        assert "acceptance_criteria" in agent.capabilities
        assert agent.claude_client is not None
        assert agent.context_manager is None
    
    def test_design_agent_initialization_with_clients(self):
        """Test DesignAgent initialization with custom clients"""
        mock_claude_client = Mock()
        mock_context_manager = Mock()
        
        agent = DesignAgent(
            claude_code_client=mock_claude_client,
            context_manager=mock_context_manager
        )
        
        assert agent.claude_client == mock_claude_client
        assert agent.context_manager == mock_context_manager
    
    def test_design_agent_capabilities(self):
        """Test DesignAgent has all expected capabilities"""
        agent = DesignAgent()
        
        expected_capabilities = [
            "system_architecture",
            "component_design", 
            "interface_definition",
            "design_review",
            "pattern_identification",
            "technical_specification",
            "tdd_specification",
            "acceptance_criteria",
            "test_scenarios",
            "api_contracts",
            "testable_design"
        ]
        
        for capability in expected_capabilities:
            assert capability in agent.capabilities


class TestDesignAgentTaskExecution:
    """Test DesignAgent run method and task routing"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.mock_claude_client = AsyncMock()
        self.mock_context_manager = AsyncMock()
        self.agent = DesignAgent(
            claude_code_client=self.mock_claude_client,
            context_manager=self.mock_context_manager
        )
    
    @pytest.mark.asyncio
    async def test_run_with_architecture_command(self):
        """Test run method with architecture command"""
        task = Task(
            id="arch-task",
            agent_type="DesignAgent",
            command="create architecture",
            context={"requirements": "Build a web service"}
        )
        
        with patch.object(self.agent, '_create_architecture') as mock_method:
            mock_method.return_value = AgentResult(success=True, output="Architecture created")
            
            result = await self.agent.run(task, dry_run=False)
            
            assert result.success is True
            assert result.execution_time > 0
            mock_method.assert_called_once_with(task, False)
    
    @pytest.mark.asyncio
    async def test_run_with_tdd_specification_command(self):
        """Test run method with TDD specification command"""
        task = Task(
            id="tdd-spec-task",
            agent_type="DesignAgent",
            command="create tdd_specification",
            context={"story": {"description": "User login feature"}}
        )
        
        with patch.object(self.agent, '_create_tdd_specification') as mock_method:
            mock_method.return_value = AgentResult(success=True, output="TDD spec created")
            
            result = await self.agent.run(task, dry_run=False)
            
            assert result.success is True
            mock_method.assert_called_once_with(task, False)
    
    @pytest.mark.asyncio
    async def test_run_with_acceptance_criteria_command(self):
        """Test run method with acceptance criteria command"""
        task = Task(
            id="ac-task",
            agent_type="DesignAgent",
            command="define acceptance_criteria",
            context={"story": {"description": "User registration"}}
        )
        
        with patch.object(self.agent, '_define_acceptance_criteria') as mock_method:
            mock_method.return_value = AgentResult(success=True, output="Criteria defined")
            
            result = await self.agent.run(task, dry_run=False)
            
            assert result.success is True
            mock_method.assert_called_once_with(task, False)
    
    @pytest.mark.asyncio
    async def test_run_with_test_scenarios_command(self):
        """Test run method with test scenarios command"""
        task = Task(
            id="scenarios-task",
            agent_type="DesignAgent",
            command="design test_scenarios",
            context={"story": {"description": "Password reset"}}
        )
        
        with patch.object(self.agent, '_design_test_scenarios') as mock_method:
            mock_method.return_value = AgentResult(success=True, output="Scenarios designed")
            
            result = await self.agent.run(task, dry_run=False)
            
            assert result.success is True
            mock_method.assert_called_once_with(task, False)
    
    @pytest.mark.asyncio
    async def test_run_with_api_contracts_command(self):
        """Test run method with API contracts command"""
        task = Task(
            id="api-task",
            agent_type="DesignAgent",
            command="create api_contracts",
            context={"story": {"description": "User profile API"}}
        )
        
        with patch.object(self.agent, '_create_api_contracts') as mock_method:
            mock_method.return_value = AgentResult(success=True, output="API contracts created")
            
            result = await self.agent.run(task, dry_run=False)
            
            assert result.success is True
            mock_method.assert_called_once_with(task, False)
    
    @pytest.mark.asyncio
    async def test_run_with_review_command(self):
        """Test run method with design review command"""
        task = Task(
            id="review-task",
            agent_type="DesignAgent",
            command="review design",
            context={"design": "Existing design content"}
        )
        
        with patch.object(self.agent, '_review_design') as mock_method:
            mock_method.return_value = AgentResult(success=True, output="Design reviewed")
            
            result = await self.agent.run(task, dry_run=False)
            
            assert result.success is True
            mock_method.assert_called_once_with(task, False)
    
    @pytest.mark.asyncio
    async def test_run_with_interface_command(self):
        """Test run method with interface definition command"""
        task = Task(
            id="interface-task",
            agent_type="DesignAgent",
            command="define interface",
            context={"components": ["ServiceA", "ServiceB"]}
        )
        
        with patch.object(self.agent, '_define_interfaces') as mock_method:
            mock_method.return_value = AgentResult(success=True, output="Interfaces defined")
            
            result = await self.agent.run(task, dry_run=False)
            
            assert result.success is True
            mock_method.assert_called_once_with(task, False)
    
    @pytest.mark.asyncio
    async def test_run_with_specification_command(self):
        """Test run method with technical specification command"""
        task = Task(
            id="spec-task",
            agent_type="DesignAgent",
            command="create specification",
            context={"feature": "User authentication"}
        )
        
        with patch.object(self.agent, '_create_specification') as mock_method:
            mock_method.return_value = AgentResult(success=True, output="Specification created")
            
            result = await self.agent.run(task, dry_run=False)
            
            assert result.success is True
            mock_method.assert_called_once_with(task, False)
    
    @pytest.mark.asyncio
    async def test_run_with_general_command(self):
        """Test run method with general/unknown command"""
        task = Task(
            id="general-task",
            agent_type="DesignAgent",
            command="unknown_command",
            context={}
        )
        
        with patch.object(self.agent, '_general_design_task') as mock_method:
            mock_method.return_value = AgentResult(success=True, output="General task completed")
            
            result = await self.agent.run(task, dry_run=False)
            
            assert result.success is True
            mock_method.assert_called_once_with(task, False)
    
    @pytest.mark.asyncio
    async def test_run_with_context_manager_preparation(self):
        """Test run method with context manager preparation"""
        task = Task(
            id="context-task",
            agent_type="DesignAgent",
            command="architecture",
            context={}
        )
        task.story_id = "story-123"
        
        mock_context = Mock()
        self.mock_context_manager.prepare_context.return_value = mock_context
        
        with patch.object(self.agent, '_create_architecture') as mock_arch:
            mock_arch.return_value = AgentResult(success=True, output="Architecture created")
            with patch.object(self.agent, '_record_context_usage') as mock_record:
                
                result = await self.agent.run(task, dry_run=False)
                
                assert result.success is True
                self.mock_context_manager.prepare_context.assert_called_once_with(
                    agent_type="DesignAgent",
                    task=task,
                    story_id="story-123"
                )
                mock_record.assert_called_once_with(task, mock_context)
    
    @pytest.mark.asyncio
    async def test_run_with_context_manager_exception(self):
        """Test run method handles context manager exceptions gracefully"""
        task = Task(
            id="context-error-task",
            agent_type="DesignAgent",
            command="architecture",
            context={}
        )
        
        self.mock_context_manager.prepare_context.side_effect = Exception("Context error")
        
        with patch.object(self.agent, '_create_architecture') as mock_arch:
            mock_arch.return_value = AgentResult(success=True, output="Architecture created")
            
            result = await self.agent.run(task, dry_run=False)
            
            # Should succeed despite context preparation failure
            assert result.success is True
            mock_arch.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_run_with_exception(self):
        """Test run method handles exceptions and returns error result"""
        task = Task(
            id="error-task",
            agent_type="DesignAgent",
            command="architecture",
            context={}
        )
        
        with patch.object(self.agent, '_create_architecture') as mock_method:
            mock_method.side_effect = Exception("Test exception")
            
            result = await self.agent.run(task, dry_run=False)
            
            assert result.success is False
            assert "Test exception" in result.error
            assert result.execution_time > 0


class TestArchitectureCreation:
    """Test DesignAgent architecture creation functionality"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.mock_claude_client = AsyncMock()
        self.agent = DesignAgent(claude_code_client=self.mock_claude_client)
    
    @pytest.mark.asyncio
    async def test_create_architecture_dry_run(self):
        """Test _create_architecture in dry run mode"""
        task = Task(
            id="arch-task",
            agent_type="DesignAgent",
            command="architecture",
            context={"requirements": "Build microservices"}
        )
        
        result = await self.agent._create_architecture(task, dry_run=True)
        
        assert result.success is True
        assert "[DRY RUN]" in result.output
        assert "architecture.md" in result.artifacts
        assert "# System Architecture" in result.artifacts["architecture.md"]
    
    @pytest.mark.asyncio
    async def test_create_architecture_with_claude_client(self):
        """Test _create_architecture with Claude client"""
        task = Task(
            id="arch-task",
            agent_type="DesignAgent", 
            command="architecture",
            context={"requirements": "Build a REST API"}
        )
        
        self.mock_claude_client.create_architecture.return_value = "Generated architecture"
        
        result = await self.agent._create_architecture(task, dry_run=False)
        
        assert result.success is True
        assert result.output == "Generated architecture"
        assert "architecture.md" in result.artifacts
        assert "component-diagram.mermaid" in result.artifacts
        self.mock_claude_client.create_architecture.assert_called_once_with("Build a REST API")
    
    @pytest.mark.asyncio
    async def test_create_architecture_claude_client_fallback(self):
        """Test _create_architecture fallback when Claude client fails"""
        task = Task(
            id="arch-task",
            agent_type="DesignAgent",
            command="architecture", 
            context={"requirements": "Build a web app"}
        )
        
        self.mock_claude_client.create_architecture.side_effect = Exception("Claude error")
        
        result = await self.agent._create_architecture(task, dry_run=False)
        
        assert result.success is True
        assert "System Architecture" in result.output
        assert "Build a web app" in result.output
        assert "architecture.md" in result.artifacts
        assert "component-diagram.mermaid" in result.artifacts
    
    def test_generate_architecture_design(self):
        """Test _generate_architecture_design method"""
        requirements = "Build a scalable e-commerce platform"
        
        architecture = self.agent._generate_architecture_design(requirements)
        
        assert "System Architecture" in architecture
        assert requirements in architecture
        assert "High-Level Architecture" in architecture
        assert "Components" in architecture
        assert "Technology Stack" in architecture
        assert "Design Patterns" in architecture
        assert "Scalability Strategy" in architecture
        assert "Security Considerations" in architecture
    
    def test_generate_component_diagram(self):
        """Test _generate_component_diagram method"""
        diagram = self.agent._generate_component_diagram()
        
        assert "graph TB" in diagram
        assert "API Gateway" in diagram
        assert "Database" in diagram
        assert "Cache" in diagram
        assert "-->" in diagram  # Mermaid syntax


class TestDesignReview:
    """Test DesignAgent design review functionality"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.mock_claude_client = AsyncMock()
        self.agent = DesignAgent(claude_code_client=self.mock_claude_client)
    
    @pytest.mark.asyncio
    async def test_review_design_dry_run(self):
        """Test _review_design in dry run mode"""
        task = Task(
            id="review-task",
            agent_type="DesignAgent",
            command="review",
            context={"design": "Existing design content"}
        )
        
        result = await self.agent._review_design(task, dry_run=True)
        
        assert result.success is True
        assert "[DRY RUN]" in result.output
        assert "design-review.md" in result.artifacts
    
    @pytest.mark.asyncio
    async def test_review_design_with_claude_client(self):
        """Test _review_design with Claude client"""
        task = Task(
            id="review-task",
            agent_type="DesignAgent",
            command="review",
            context={"design": "Design to review"}
        )
        
        self.mock_claude_client.analyze_code.return_value = "Design analysis complete"
        
        result = await self.agent._review_design(task, dry_run=False)
        
        assert result.success is True
        assert result.output == "Design analysis complete"
        assert "design-review.md" in result.artifacts
        self.mock_claude_client.analyze_code.assert_called_once_with("Design to review", "design_review")
    
    @pytest.mark.asyncio
    async def test_review_design_fallback(self):
        """Test _review_design fallback when Claude client fails"""
        task = Task(
            id="review-task",
            agent_type="DesignAgent",
            command="review",
            context={"design": "Design content"}
        )
        
        self.mock_claude_client.analyze_code.side_effect = Exception("Analysis error")
        
        result = await self.agent._review_design(task, dry_run=False)
        
        assert result.success is True
        assert "Design Review" in result.output
        assert "design-review.md" in result.artifacts
    
    def test_analyze_design_quality(self):
        """Test _analyze_design_quality method"""
        design_content = "Sample design content for analysis"
        
        analysis = self.agent._analyze_design_quality(design_content)
        
        assert "Design Review" in analysis
        assert "Analysis" in analysis
        assert "Recommendations" in analysis
        assert "Quality Score" in analysis
        assert "separation of concerns" in analysis
        assert "error handling" in analysis


class TestInterfaceDefinition:
    """Test DesignAgent interface definition functionality"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.agent = DesignAgent()
    
    @pytest.mark.asyncio
    async def test_define_interfaces_dry_run(self):
        """Test _define_interfaces in dry run mode"""
        task = Task(
            id="interface-task",
            agent_type="DesignAgent",
            command="interface",
            context={"components": ["UserService", "PaymentService"]}
        )
        
        result = await self.agent._define_interfaces(task, dry_run=True)
        
        assert result.success is True
        assert "[DRY RUN]" in result.output
        assert "UserService" in result.output
        assert "PaymentService" in result.output
    
    @pytest.mark.asyncio
    async def test_define_interfaces_normal(self):
        """Test _define_interfaces in normal mode"""
        task = Task(
            id="interface-task",
            agent_type="DesignAgent",
            command="interface",
            context={"components": ["AuthService", "DataService"]}
        )
        
        result = await self.agent._define_interfaces(task, dry_run=False)
        
        assert result.success is True
        assert "interfaces.md" in result.artifacts
        assert "Component Interfaces" in result.output
        assert "AuthService" in result.output
        assert "DataService" in result.output
    
    def test_create_interface_definitions(self):
        """Test _create_interface_definitions method"""
        components = ["ServiceA", "ServiceB", "ServiceC"]
        
        interfaces = self.agent._create_interface_definitions(components)
        
        assert "Component Interfaces" in interfaces
        assert "ServiceA, ServiceB, ServiceC" in interfaces
        assert "API Contracts" in interfaces
        assert "Integration Points" in interfaces
        assert "RESTful interfaces" in interfaces


class TestTechnicalSpecification:
    """Test DesignAgent technical specification functionality"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.agent = DesignAgent()
    
    @pytest.mark.asyncio
    async def test_create_specification_dry_run(self):
        """Test _create_specification in dry run mode"""
        task = Task(
            id="spec-task",
            agent_type="DesignAgent",
            command="specification",
            context={"feature": "User authentication"}
        )
        
        result = await self.agent._create_specification(task, dry_run=True)
        
        assert result.success is True
        assert "[DRY RUN]" in result.output
        assert "User authentication" in result.output
    
    @pytest.mark.asyncio
    async def test_create_specification_normal(self):
        """Test _create_specification in normal mode"""
        task = Task(
            id="spec-task",
            agent_type="DesignAgent",
            command="specification",
            context={"feature": "Password reset"}
        )
        
        result = await self.agent._create_specification(task, dry_run=False)
        
        assert result.success is True
        assert "technical-spec.md" in result.artifacts
        assert "Password reset" in result.output
    
    def test_generate_technical_spec(self):
        """Test _generate_technical_spec method"""
        feature = "Two-factor authentication"
        
        spec = self.agent._generate_technical_spec(feature)
        
        assert f"Technical Specification: {feature}" in spec
        assert "Overview" in spec
        assert "Functional Requirements" in spec
        assert "Non-Functional Requirements" in spec
        assert "Implementation Details" in spec
        assert "Testing Strategy" in spec
        assert "Deployment Plan" in spec


class TestTDDSpecificationCreation:
    """Test DesignAgent TDD specification functionality"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.mock_claude_client = AsyncMock()
        self.agent = DesignAgent(claude_code_client=self.mock_claude_client)
    
    @pytest.mark.asyncio
    async def test_create_tdd_specification_dry_run(self):
        """Test _create_tdd_specification in dry run mode"""
        task = Task(
            id="tdd-spec-task",
            agent_type="DesignAgent",
            command="tdd_specification",
            context={"story": {"description": "User can log in with email and password"}}
        )
        
        result = await self.agent._create_tdd_specification(task, dry_run=True)
        
        assert result.success is True
        assert "[DRY RUN]" in result.output
        assert "tdd-spec.md" in result.artifacts
    
    @pytest.mark.asyncio
    async def test_create_tdd_specification_with_claude_client(self):
        """Test _create_tdd_specification with Claude client"""
        task = Task(
            id="tdd-spec-task",
            agent_type="DesignAgent",
            command="tdd_specification",
            context={"story": {"description": "User registration with validation"}}
        )
        
        self.mock_claude_client.generate_specification.return_value = "Generated TDD specification"
        
        with patch.object(self.agent, 'log_tdd_action') as mock_log:
            result = await self.agent._create_tdd_specification(task, dry_run=False)
            
            assert result.success is True
            assert result.output == "Generated TDD specification"
            assert "tdd-specification.md" in result.artifacts
            assert "acceptance-criteria.md" in result.artifacts
            assert "test-plan.md" in result.artifacts
            mock_log.assert_called_once()
            self.mock_claude_client.generate_specification.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_create_tdd_specification_fallback(self):
        """Test _create_tdd_specification fallback when Claude client fails"""
        task = Task(
            id="tdd-spec-task",
            agent_type="DesignAgent",
            command="tdd_specification",
            context={"story": {"description": "User profile management"}}
        )
        
        self.mock_claude_client.generate_specification.side_effect = Exception("Generation error")
        
        with patch.object(self.agent, 'log_tdd_action'):
            result = await self.agent._create_tdd_specification(task, dry_run=False)
            
            assert result.success is True
            assert "TDD Specification" in result.output
            assert "User profile management" in result.output
            assert "tdd-specification.md" in result.artifacts
    
    @pytest.mark.asyncio
    async def test_create_tdd_specification_with_string_story(self):
        """Test _create_tdd_specification with story as string"""
        task = Task(
            id="tdd-spec-task",
            agent_type="DesignAgent",
            command="tdd_specification",
            context={"story": "Simple string story description"}
        )
        
        self.mock_claude_client.generate_specification.return_value = "String story specification"
        
        result = await self.agent._create_tdd_specification(task, dry_run=False)
        
        assert result.success is True
        # Verify string story was handled correctly
        spec_call_args = self.mock_claude_client.generate_specification.call_args[0][0]
        assert "Simple string story description" in spec_call_args
    
    def test_generate_tdd_spec_fallback(self):
        """Test _generate_tdd_spec_fallback method"""
        story_description = "User can search for products by category"
        
        spec = self.agent._generate_tdd_spec_fallback(story_description)
        
        assert "TDD Specification" in spec
        assert story_description in spec
        assert "Testable Requirements" in spec
        assert "API Interface Design" in spec
        assert "Test-First Considerations" in spec
        assert "Edge Cases and Boundary Conditions" in spec
        assert "Success Criteria" in spec
    
    def test_extract_acceptance_criteria(self):
        """Test _extract_acceptance_criteria method"""
        specification_with_criteria = """
        # TDD Specification
        
        ## Acceptance Criteria
        
        - User must enter valid email
        - Password must be at least 8 characters
        
        ## Other Section
        
        More content here
        """
        
        criteria = self.agent._extract_acceptance_criteria(specification_with_criteria)
        
        assert "Acceptance Criteria" in criteria
        assert "User must enter valid email" in criteria
        assert "Password must be at least 8 characters" in criteria
        assert "Other Section" not in criteria
    
    def test_extract_acceptance_criteria_not_found(self):
        """Test _extract_acceptance_criteria when criteria not found"""
        specification_without_criteria = """
        # TDD Specification
        
        ## Overview
        
        Some overview content
        """
        
        criteria = self.agent._extract_acceptance_criteria(specification_without_criteria)
        
        assert "# Acceptance Criteria" in criteria
        assert "To be extracted" in criteria
    
    def test_extract_test_plan(self):
        """Test _extract_test_plan method"""
        spec = "Sample specification"
        
        test_plan = self.agent._extract_test_plan(spec)
        
        assert "# Test Plan" in test_plan
        assert "Test Strategy" in test_plan
        assert "Unit Tests" in test_plan
        assert "Integration Tests" in test_plan
        assert "RED Phase" in test_plan
        assert "GREEN Phase" in test_plan
        assert "REFACTOR Phase" in test_plan


class TestAcceptanceCriteria:
    """Test DesignAgent acceptance criteria functionality"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.agent = DesignAgent()
    
    @pytest.mark.asyncio
    async def test_define_acceptance_criteria_dry_run(self):
        """Test _define_acceptance_criteria in dry run mode"""
        task = Task(
            id="ac-task",
            agent_type="DesignAgent",
            command="acceptance_criteria",
            context={"story": {"description": "User can change password"}}
        )
        
        result = await self.agent._define_acceptance_criteria(task, dry_run=True)
        
        assert result.success is True
        assert "[DRY RUN]" in result.output
        assert "User can change password" in result.output
    
    @pytest.mark.asyncio
    async def test_define_acceptance_criteria_normal(self):
        """Test _define_acceptance_criteria in normal mode"""
        task = Task(
            id="ac-task",
            agent_type="DesignAgent",
            command="acceptance_criteria",
            context={"story": {"description": "User can view order history"}}
        )
        
        with patch.object(self.agent, 'log_tdd_action') as mock_log:
            result = await self.agent._define_acceptance_criteria(task, dry_run=False)
            
            assert result.success is True
            assert "acceptance-criteria.md" in result.artifacts
            mock_log.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_define_acceptance_criteria_with_string_story(self):
        """Test _define_acceptance_criteria with story as string"""
        task = Task(
            id="ac-task",
            agent_type="DesignAgent",
            command="acceptance_criteria",
            context={"story": "User downloads invoice"}
        )
        
        result = await self.agent._define_acceptance_criteria(task, dry_run=False)
        
        assert result.success is True
        assert "User downloads invoice" in result.output
    
    def test_generate_acceptance_criteria(self):
        """Test _generate_acceptance_criteria method"""
        story_description = "User can filter search results by price range"
        
        criteria = self.agent._generate_acceptance_criteria(story_description)
        
        assert "# Acceptance Criteria" in criteria
        assert story_description in criteria
        assert "Given-When-Then Scenarios" in criteria
        assert "Scenario 1: Happy Path" in criteria
        assert "Scenario 2: Input Validation" in criteria
        assert "Scenario 3: Edge Case Handling" in criteria
        assert "Scenario 4: Error Recovery" in criteria
        assert "Automated Test Requirements" in criteria
        assert "Definition of Done" in criteria


class TestTestScenarios:
    """Test DesignAgent test scenarios functionality"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.agent = DesignAgent()
    
    @pytest.mark.asyncio
    async def test_design_test_scenarios_dry_run(self):
        """Test _design_test_scenarios in dry run mode"""
        task = Task(
            id="scenarios-task",
            agent_type="DesignAgent",
            command="test_scenarios",
            context={
                "story": {"description": "User can add items to cart"},
                "acceptance_criteria": ["Item must be in stock", "User must be logged in"]
            }
        )
        
        result = await self.agent._design_test_scenarios(task, dry_run=True)
        
        assert result.success is True
        assert "[DRY RUN]" in result.output
        assert "User can add items to cart" in result.output
    
    @pytest.mark.asyncio
    async def test_design_test_scenarios_normal(self):
        """Test _design_test_scenarios in normal mode"""
        task = Task(
            id="scenarios-task",
            agent_type="DesignAgent",
            command="test_scenarios",
            context={
                "story": {"description": "User can checkout with payment"},
                "acceptance_criteria": ["Payment must be validated", "Order must be created"]
            }
        )
        
        with patch.object(self.agent, 'log_tdd_action') as mock_log:
            result = await self.agent._design_test_scenarios(task, dry_run=False)
            
            assert result.success is True
            assert "test-scenarios.md" in result.artifacts
            assert "edge-cases.md" in result.artifacts
            mock_log.assert_called_once()
    
    def test_generate_test_scenarios(self):
        """Test _generate_test_scenarios method"""
        story_description = "User can cancel subscription"
        acceptance_criteria = ["User must be logged in", "Subscription must be active"]
        
        scenarios = self.agent._generate_test_scenarios(story_description, acceptance_criteria)
        
        assert "# Test Scenarios" in scenarios
        assert story_description in scenarios
        assert "Test Categories" in scenarios
        assert "1. Functional Tests" in scenarios
        assert "2. Integration Tests" in scenarios
        assert "3. Edge Cases" in scenarios
        assert "4. Performance Tests" in scenarios
        assert "5. Security Tests" in scenarios
        assert "Positive Test Cases" in scenarios
        assert "Negative Test Cases" in scenarios
        assert "Test Implementation Priority" in scenarios
    
    def test_extract_edge_cases(self):
        """Test _extract_edge_cases method"""
        scenarios = "Sample test scenarios content"
        
        edge_cases = self.agent._extract_edge_cases(scenarios)
        
        assert "# Edge Cases" in edge_cases
        assert "Identified Edge Cases" in edge_cases
        assert "Empty Data Sets" in edge_cases
        assert "Boundary Values" in edge_cases
        assert "Concurrent Access" in edge_cases
        assert "Resource Constraints" in edge_cases
        assert "Error Conditions" in edge_cases
        assert "Edge Case Test Strategy" in edge_cases


class TestAPIContracts:
    """Test DesignAgent API contracts functionality"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.agent = DesignAgent()
    
    @pytest.mark.asyncio
    async def test_create_api_contracts_dry_run(self):
        """Test _create_api_contracts in dry run mode"""
        task = Task(
            id="api-task",
            agent_type="DesignAgent",
            command="api_contracts",
            context={"story": {"description": "User management API"}}
        )
        
        result = await self.agent._create_api_contracts(task, dry_run=True)
        
        assert result.success is True
        assert "[DRY RUN]" in result.output
        assert "User management API" in result.output
    
    @pytest.mark.asyncio
    async def test_create_api_contracts_normal(self):
        """Test _create_api_contracts in normal mode"""
        task = Task(
            id="api-task",
            agent_type="DesignAgent",
            command="api_contracts",
            context={"story": {"description": "Product catalog API"}}
        )
        
        with patch.object(self.agent, 'log_tdd_action') as mock_log:
            result = await self.agent._create_api_contracts(task, dry_run=False)
            
            assert result.success is True
            assert "api-contracts.md" in result.artifacts
            assert "interface-definitions.json" in result.artifacts
            mock_log.assert_called_once()
    
    def test_generate_api_contracts(self):
        """Test _generate_api_contracts method"""
        story_description = "Order processing API"
        
        contracts = self.agent._generate_api_contracts(story_description)
        
        assert "# API Contracts" in contracts
        assert story_description in contracts
        assert "Interface Specifications" in contracts
        assert "Public API Endpoints" in contracts
        assert "REST API Design" in contracts
        assert "Data Models" in contracts
        assert "Service Layer Contracts" in contracts
        assert "Error Handling Contracts" in contracts
        assert "Test Contract Validation" in contracts
        assert "Testability Features" in contracts
    
    def test_extract_interfaces(self):
        """Test _extract_interfaces method"""
        contracts = "Sample API contracts content"
        
        interfaces = self.agent._extract_interfaces(contracts)
        
        # Parse as JSON to validate structure
        interface_data = json.loads(interfaces)
        
        assert "interfaces" in interface_data
        assert "models" in interface_data
        assert len(interface_data["interfaces"]) > 0
        assert len(interface_data["models"]) > 0
        
        # Check specific interface structure
        resource_service = interface_data["interfaces"][0]
        assert resource_service["name"] == "ResourceService"
        assert resource_service["type"] == "service"
        assert "methods" in resource_service
        
        # Check specific model structure
        resource_model = interface_data["models"][0]
        assert resource_model["name"] == "Resource"
        assert "fields" in resource_model
        assert "required" in resource_model


class TestTDDPhaseExecution:
    """Test DesignAgent TDD phase execution functionality"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.agent = DesignAgent()
        self.mock_cycle = Mock()
        self.mock_cycle.id = "cycle-1"
        self.mock_cycle.story_id = "story-1"
    
    @pytest.mark.asyncio
    async def test_execute_tdd_phase_design_phase(self):
        """Test execute_tdd_phase for DESIGN phase"""
        context = {
            "story": {"description": "User authentication feature"},
            "task_description": "Design user auth",
            "dry_run": False
        }
        
        # Mock the individual design methods
        with patch.object(self.agent, '_create_tdd_specification') as mock_spec:
            with patch.object(self.agent, '_define_acceptance_criteria') as mock_criteria:
                with patch.object(self.agent, '_design_test_scenarios') as mock_scenarios:
                    with patch.object(self.agent, '_create_api_contracts') as mock_contracts:
                        
                        # Setup mock returns
                        mock_spec.return_value = AgentResult(
                            success=True, output="Spec created", artifacts={"tdd-spec.md": "spec"}
                        )
                        mock_criteria.return_value = AgentResult(
                            success=True, output="Criteria defined", artifacts={"criteria.md": "criteria"}
                        )
                        mock_scenarios.return_value = AgentResult(
                            success=True, output="Scenarios designed", artifacts={"scenarios.md": "scenarios"}
                        )
                        mock_contracts.return_value = AgentResult(
                            success=True, output="Contracts created", artifacts={"contracts.md": "contracts"}
                        )
                        
                        result = await self.agent.execute_tdd_phase(TDDState.DESIGN, context)
                        
                        assert result.success is True
                        assert "TDD Design Phase Complete" in result.output
                        assert "Ready for TEST_RED Phase" in result.output
                        
                        # Check all artifacts were combined
                        assert "tdd-spec.md" in result.artifacts
                        assert "criteria.md" in result.artifacts
                        assert "scenarios.md" in result.artifacts
                        assert "contracts.md" in result.artifacts
                        
                        # Verify all methods were called
                        mock_spec.assert_called_once()
                        mock_criteria.assert_called_once()
                        mock_scenarios.assert_called_once()
                        mock_contracts.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_execute_tdd_phase_wrong_phase(self):
        """Test execute_tdd_phase with wrong phase"""
        result = await self.agent.execute_tdd_phase(TDDState.CODE_GREEN, {})
        
        assert result.success is False
        assert "can only execute DESIGN phase" in result.error
    
    @pytest.mark.asyncio
    async def test_execute_tdd_phase_with_logging(self):
        """Test execute_tdd_phase includes proper logging"""
        context = {"story": {"description": "Test story"}}
        
        with patch.object(self.agent, 'log_tdd_action') as mock_log:
            with patch.object(self.agent, '_create_tdd_specification') as mock_spec:
                with patch.object(self.agent, '_define_acceptance_criteria') as mock_criteria:
                    with patch.object(self.agent, '_design_test_scenarios') as mock_scenarios:
                        with patch.object(self.agent, '_create_api_contracts') as mock_contracts:
                            
                            # Setup minimal mock returns
                            for mock_method in [mock_spec, mock_criteria, mock_scenarios, mock_contracts]:
                                mock_method.return_value = AgentResult(
                                    success=True, output="test", artifacts={}
                                )
                            
                            await self.agent.execute_tdd_phase(TDDState.DESIGN, context)
                            
                            mock_log.assert_called_with("execute_design_phase", "phase: DESIGN")


class TestContextRecording:
    """Test DesignAgent context recording functionality"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.mock_context_manager = AsyncMock()
        self.agent = DesignAgent(context_manager=self.mock_context_manager)
    
    @pytest.mark.asyncio
    async def test_record_context_usage_success(self):
        """Test _record_context_usage with successful recording"""
        task = Mock()
        task.story_id = "story-123"
        
        mock_context = Mock()
        mock_context.request_id = "req-456"
        mock_context.file_contents = {
            "docs/architecture.md": "content",
            "src/main.py": "code",
            "tests/test_main.py": "tests"
        }
        
        await self.agent._record_context_usage(task, mock_context)
        
        # Verify feedback recording was called
        self.mock_context_manager.record_feedback.assert_called_once()
        call_args = self.mock_context_manager.record_feedback.call_args
        assert call_args[1]["context_id"] == "req-456"
        assert call_args[1]["agent_type"] == "DesignAgent"
        assert call_args[1]["story_id"] == "story-123"
        assert call_args[1]["feedback_type"] == "design_usage"
        
        # Verify decision recording was called
        self.mock_context_manager.record_agent_decision.assert_called_once()
        decision_args = self.mock_context_manager.record_agent_decision.call_args
        assert decision_args[1]["agent_type"] == "DesignAgent"
        assert decision_args[1]["story_id"] == "story-123"
        assert "Design task" in decision_args[1]["description"]
    
    @pytest.mark.asyncio
    async def test_record_context_usage_no_context_manager(self):
        """Test _record_context_usage without context manager"""
        agent = DesignAgent()  # No context manager
        task = Mock()
        mock_context = Mock()
        
        # Should not raise exception
        await agent._record_context_usage(task, mock_context)
    
    @pytest.mark.asyncio
    async def test_record_context_usage_exception(self):
        """Test _record_context_usage handles exceptions gracefully"""
        task = Mock()
        mock_context = Mock()
        mock_context.file_contents = {}
        
        self.mock_context_manager.record_feedback.side_effect = Exception("Recording error")
        
        # Should not raise exception, just log warning
        await self.agent._record_context_usage(task, mock_context)
    
    def test_analyze_file_relevance(self):
        """Test _analyze_file_relevance method"""
        task = Mock()
        task.command = "architecture review"
        
        mock_context = Mock()
        mock_context.file_contents = {
            "docs/architecture.md": "content",
            "README.md": "readme",
            "config.yaml": "config",
            "src/main.py": "code",
            "src/architecture/design.py": "arch code",
            "tests/test_main.py": "tests",
            "data/sample.csv": "data"
        }
        
        relevance = self.agent._analyze_file_relevance(task, mock_context)
        
        # Documentation files should have high relevance
        assert relevance["docs/architecture.md"] == 0.9
        assert relevance["README.md"] == 0.9
        assert relevance["config.yaml"] == 0.9
        
        # Architecture-related files should have high relevance
        assert relevance["src/architecture/design.py"] == 0.8
        
        # Implementation files should have medium relevance
        assert relevance["src/main.py"] == 0.6
        
        # Test files should have lower relevance
        assert relevance["tests/test_main.py"] == 0.4
        
        # Other files should have default relevance
        assert relevance["data/sample.csv"] == 0.3
    
    def test_analyze_file_relevance_no_context(self):
        """Test _analyze_file_relevance with no context"""
        task = Mock()
        relevance = self.agent._analyze_file_relevance(task, None)
        assert relevance == {}
        
        mock_context = Mock()
        mock_context.file_contents = None
        relevance = self.agent._analyze_file_relevance(task, mock_context)
        assert relevance == {}


class TestGeneralDesignTasks:
    """Test DesignAgent general task functionality"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.agent = DesignAgent()
    
    @pytest.mark.asyncio
    async def test_general_design_task_dry_run(self):
        """Test _general_design_task in dry run mode"""
        task = Task(
            id="general-task",
            agent_type="DesignAgent",
            command="custom_design_command",
            context={}
        )
        
        result = await self.agent._general_design_task(task, dry_run=True)
        
        assert result.success is True
        assert "[DRY RUN]" in result.output
        assert "custom_design_command" in result.output
    
    @pytest.mark.asyncio
    async def test_general_design_task_normal(self):
        """Test _general_design_task in normal mode"""
        task = Task(
            id="general-task",
            agent_type="DesignAgent",
            command="another_command",
            context={}
        )
        
        result = await self.agent._general_design_task(task, dry_run=False)
        
        assert result.success is True
        assert "DesignAgent executed: another_command" in result.output


if __name__ == "__main__":
    pytest.main([__file__])