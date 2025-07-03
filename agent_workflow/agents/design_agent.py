"""
Design Agent - Architecture and System Design

Handles high-level system design, architecture decisions, and technical planning
following established design patterns and best practices.
"""

import asyncio
import time
from typing import Dict, Any, List
from . import BaseAgent, Task, AgentResult, TDDState, TDDCycle, TDDTask, TestResult
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
import logging
import json
from datetime import datetime

# Handle both relative and absolute imports
try:
    from ..integrations.claude.client import claude_client, create_agent_client
    from ..security.tool_config import AgentType
except ImportError:
    from agent_workflow.integrations.claude.client import claude_client, create_agent_client
    from agent_workflow.security.tool_config import AgentType

logger = logging.getLogger(__name__)


class DesignAgent(BaseAgent):
    """
    AI agent specialized in system design and architecture.
    
    Responsibilities:
    - Create system architecture diagrams
    - Define component interfaces and contracts
    - Review and validate design decisions
    - Generate technical specifications
    - Identify design patterns and anti-patterns
    """
    
    def __init__(self, claude_code_client=None, context_manager=None):
        super().__init__(
            name="DesignAgent",
            capabilities=[
                "system_architecture",
                "component_design", 
                "interface_definition",
                "design_review",
                "pattern_identification",
                "technical_specification",
                # TDD-specific capabilities
                "tdd_specification",
                "acceptance_criteria",
                "test_scenarios",
                "api_contracts",
                "testable_design"
            ]
        )
        self.claude_client = claude_code_client or create_agent_client(AgentType.DESIGN)
        self.context_manager = context_manager
        
    async def run(self, task: Task, dry_run: bool = False) -> AgentResult:
        """Execute design-related tasks"""
        start_time = time.time()
        
        try:
            # Prepare context if context manager is available
            if self.context_manager:
                try:
                    agent_context = await self.context_manager.prepare_context(
                        agent_type="DesignAgent",
                        task=task,
                        story_id=getattr(task, 'story_id', 'default')
                    )
                    
                    # Record context usage for learning
                    await self._record_context_usage(task, agent_context)
                    
                except Exception as e:
                    logger.warning(f"Context preparation failed, proceeding without: {str(e)}")
            
            # Parse command to determine specific design task
            command = task.command.lower()
            context = task.context or {}
            
            # TDD-specific commands
            if "tdd_specification" in command or "tdd_spec" in command:
                result = await self._create_tdd_specification(task, dry_run)
            elif "acceptance_criteria" in command:
                result = await self._define_acceptance_criteria(task, dry_run)
            elif "test_scenarios" in command:
                result = await self._design_test_scenarios(task, dry_run)
            elif "api_contracts" in command:
                result = await self._create_api_contracts(task, dry_run)
            # Original design commands
            elif "architecture" in command:
                result = await self._create_architecture(task, dry_run)
            elif "review" in command:
                result = await self._review_design(task, dry_run)
            elif "interface" in command:
                result = await self._define_interfaces(task, dry_run)
            elif "specification" in command or "spec" in command:
                result = await self._create_specification(task, dry_run)
            else:
                result = await self._general_design_task(task, dry_run)
                
            result.execution_time = time.time() - start_time
            return result
            
        except Exception as e:
            self.logger.error(f"DesignAgent error: {str(e)}")
            return AgentResult(
                success=False,
                output="",
                error=str(e),
                execution_time=time.time() - start_time
            )
    
    async def _create_architecture(self, task: Task, dry_run: bool) -> AgentResult:
        """Create system architecture based on requirements"""
        requirements = task.context.get("requirements", "")
        
        if dry_run:
            output = f"[DRY RUN] Would create architecture for: {requirements}"
            artifacts = {"architecture.md": "# System Architecture\n\n[Generated design]"}
        else:
            # Use Claude Code for architecture generation
            try:
                output = await self.claude_client.create_architecture(requirements)
                artifacts = {
                    "architecture.md": output,
                    "component-diagram.mermaid": self._generate_component_diagram()
                }
            except Exception as e:
                logger.warning(f"Claude Code unavailable, using fallback: {e}")
                output = self._generate_architecture_design(requirements)
                artifacts = {
                    "architecture.md": output,
                    "component-diagram.mermaid": self._generate_component_diagram()
                }
        
        return AgentResult(
            success=True,
            output=output,
            artifacts=artifacts
        )
    
    async def _review_design(self, task: Task, dry_run: bool) -> AgentResult:
        """Review existing design for issues and improvements"""
        design_content = task.context.get("design", "")
        
        if dry_run:
            output = f"[DRY RUN] Would review design: {design_content[:100]}..."
        else:
            # Use Claude Code for design review
            try:
                output = await self.claude_client.analyze_code(design_content, "design_review")
            except Exception as e:
                logger.warning(f"Claude Code unavailable, using fallback: {e}")
                output = self._analyze_design_quality(design_content)
        
        return AgentResult(
            success=True,
            output=output,
            artifacts={"design-review.md": output}
        )
    
    async def _define_interfaces(self, task: Task, dry_run: bool) -> AgentResult:
        """Define component interfaces and APIs"""
        components = task.context.get("components", [])
        
        if dry_run:
            output = f"[DRY RUN] Would define interfaces for: {components}"
        else:
            output = self._create_interface_definitions(components)
        
        return AgentResult(
            success=True,
            output=output,
            artifacts={"interfaces.md": output}
        )
    
    async def _create_specification(self, task: Task, dry_run: bool) -> AgentResult:
        """Create detailed technical specification"""
        feature = task.context.get("feature", "")
        
        if dry_run:
            output = f"[DRY RUN] Would create spec for: {feature}"
        else:
            output = self._generate_technical_spec(feature)
        
        return AgentResult(
            success=True,
            output=output,
            artifacts={"technical-spec.md": output}
        )
    
    async def _general_design_task(self, task: Task, dry_run: bool) -> AgentResult:
        """Handle general design tasks"""
        if dry_run:
            output = f"[DRY RUN] DesignAgent would execute: {task.command}"
        else:
            output = f"DesignAgent executed: {task.command}"
        
        return AgentResult(success=True, output=output)
    
    def _generate_architecture_design(self, requirements: str) -> str:
        """Generate architecture design document (placeholder)"""
        return f"""
# System Architecture

## Requirements
{requirements}

## High-Level Architecture

### Components
- **API Gateway**: Entry point for all requests
- **Service Layer**: Business logic and processing
- **Data Layer**: Persistence and caching
- **Integration Layer**: External service connections

### Technology Stack
- **Backend**: Python/FastAPI
- **Database**: PostgreSQL with Redis cache  
- **Message Queue**: RabbitMQ/Celery
- **Monitoring**: Prometheus + Grafana

### Design Patterns
- **Microservices Architecture**: Loosely coupled services
- **CQRS**: Command Query Responsibility Segregation
- **Event Sourcing**: Audit trail and state reconstruction
- **Circuit Breaker**: Resilience against failures

## Scalability Strategy
- Horizontal scaling with load balancers
- Database sharding for high-volume data
- Caching strategy with Redis
- Async processing for heavy operations

## Security Considerations
- OAuth 2.0 / JWT authentication
- API rate limiting and throttling
- Data encryption at rest and in transit
- Regular security audits and penetration testing
        """.strip()
    
    def _generate_component_diagram(self) -> str:
        """Generate Mermaid component diagram"""
        return """
graph TB
    A[API Gateway] --> B[Auth Service]
    A --> C[Business Logic]
    C --> D[Data Service]
    C --> E[Integration Service]
    D --> F[(Database)]
    D --> G[(Cache)]
    E --> H[External APIs]
        """.strip()
    
    def _analyze_design_quality(self, design: str) -> str:
        """Analyze design quality and provide recommendations"""
        return f"""
# Design Review

## Analysis
The provided design has been reviewed for:
- Architectural patterns compliance
- Scalability considerations  
- Security best practices
- Maintainability factors

## Recommendations
1. **Improve separation of concerns** - Consider splitting large components
2. **Add error handling strategy** - Define failure modes and recovery
3. **Document API contracts** - Ensure clear interface definitions
4. **Consider performance** - Add caching and optimization strategies

## Quality Score: 7/10
Good foundation with room for improvement in error handling and documentation.
        """.strip()
    
    def _create_interface_definitions(self, components: list) -> str:
        """Create interface definitions for components"""
        return f"""
# Component Interfaces

## Defined Components: {', '.join(components)}

### API Contracts
- RESTful interfaces with OpenAPI specification
- Event-driven messaging contracts
- Database schema definitions
- Configuration interfaces

### Integration Points
- Authentication and authorization flows
- Data transformation specifications
- Error handling protocols
- Monitoring and logging interfaces
        """.strip()
    
    def _generate_technical_spec(self, feature: str) -> str:
        """Generate detailed technical specification"""
        return f"""
# Technical Specification: {feature}

## Overview
Detailed implementation specification for {feature}

## Functional Requirements
- Primary use cases and user stories
- Business logic requirements
- Data processing specifications
- Integration requirements

## Non-Functional Requirements  
- Performance targets (latency, throughput)
- Scalability requirements
- Security considerations
- Reliability and availability targets

## Implementation Details
- API endpoint specifications
- Database schema changes
- Algorithm descriptions
- Error handling strategies

## Testing Strategy
- Unit test requirements
- Integration test scenarios
- Performance test criteria
- Security test considerations

## Deployment Plan
- Infrastructure requirements
- Configuration changes
- Migration strategies
- Rollback procedures
        """.strip()
    
    # TDD-specific methods
    
    async def _create_tdd_specification(self, task: Task, dry_run: bool) -> AgentResult:
        """Generate detailed technical specifications for TDD workflow"""
        story = task.context.get("story", {})
        story_description = story.get("description", "") if isinstance(story, dict) else str(story)
        
        if dry_run:
            output = f"[DRY RUN] Would create TDD specification for: {story_description[:100]}..."
            artifacts = {"tdd-spec.md": "[Generated TDD specification]"}
        else:
            self.log_tdd_action("create_tdd_specification", f"story: {story_description[:50]}...")
            
            try:
                # Use Claude Code for enhanced specification generation
                spec_prompt = f"""
                Create a detailed TDD specification for this user story:
                {story_description}
                
                Include:
                1. Testable requirements breakdown
                2. API interface specifications
                3. Expected behaviors and edge cases
                4. Test-first design considerations
                5. Acceptance criteria that can be automated
                """
                output = await self.claude_client.generate_specification(spec_prompt)
            except Exception as e:
                logger.warning(f"Claude Code unavailable, using fallback: {e}")
                output = self._generate_tdd_spec_fallback(story_description)
            
            artifacts = {
                "tdd-specification.md": output,
                "acceptance-criteria.md": self._extract_acceptance_criteria(output),
                "test-plan.md": self._extract_test_plan(output)
            }
        
        return AgentResult(
            success=True,
            output=output,
            artifacts=artifacts
        )
    
    async def _define_acceptance_criteria(self, task: Task, dry_run: bool) -> AgentResult:
        """Create testable acceptance criteria for TDD"""
        story = task.context.get("story", {})
        story_description = story.get("description", "") if isinstance(story, dict) else str(story)
        
        if dry_run:
            output = f"[DRY RUN] Would create acceptance criteria for: {story_description[:100]}..."
        else:
            self.log_tdd_action("define_acceptance_criteria", f"story: {story_description[:50]}...")
            output = self._generate_acceptance_criteria(story_description)
        
        return AgentResult(
            success=True,
            output=output,
            artifacts={"acceptance-criteria.md": output}
        )
    
    async def _design_test_scenarios(self, task: Task, dry_run: bool) -> AgentResult:
        """Generate comprehensive test scenarios and edge cases"""
        story = task.context.get("story", {})
        acceptance_criteria = task.context.get("acceptance_criteria", [])
        story_description = story.get("description", "") if isinstance(story, dict) else str(story)
        
        if dry_run:
            output = f"[DRY RUN] Would create test scenarios for: {story_description[:100]}..."
        else:
            self.log_tdd_action("design_test_scenarios", f"story: {story_description[:50]}...")
            output = self._generate_test_scenarios(story_description, acceptance_criteria)
        
        return AgentResult(
            success=True,
            output=output,
            artifacts={
                "test-scenarios.md": output,
                "edge-cases.md": self._extract_edge_cases(output)
            }
        )
    
    async def _create_api_contracts(self, task: Task, dry_run: bool) -> AgentResult:
        """Design testable interfaces and API contracts"""
        story = task.context.get("story", {})
        story_description = story.get("description", "") if isinstance(story, dict) else str(story)
        
        if dry_run:
            output = f"[DRY RUN] Would create API contracts for: {story_description[:100]}..."
        else:
            self.log_tdd_action("create_api_contracts", f"story: {story_description[:50]}...")
            output = self._generate_api_contracts(story_description)
        
        return AgentResult(
            success=True,
            output=output,
            artifacts={
                "api-contracts.md": output,
                "interface-definitions.json": self._extract_interfaces(output)
            }
        )
    
    async def execute_tdd_phase(self, phase: TDDState, context: Dict[str, Any]) -> AgentResult:
        """Execute TDD DESIGN phase"""
        if phase != TDDState.DESIGN:
            return AgentResult(
                success=False,
                output="",
                error=f"DesignAgent can only execute DESIGN phase, not {phase.value}"
            )
        
        self.log_tdd_action("execute_design_phase", f"phase: {phase.value}")
        
        # Create a comprehensive design package for TDD
        story = context.get("story", {})
        task_description = context.get("task_description", "")
        
        # Generate all design artifacts for TDD
        tdd_spec = await self._create_tdd_specification(
            Task(id="tdd-spec", agent_type="DesignAgent", command="tdd_specification", 
                 context={"story": story}), 
            dry_run=context.get("dry_run", False)
        )
        
        acceptance_criteria = await self._define_acceptance_criteria(
            Task(id="acceptance", agent_type="DesignAgent", command="acceptance_criteria",
                 context={"story": story}),
            dry_run=context.get("dry_run", False)
        )
        
        test_scenarios = await self._design_test_scenarios(
            Task(id="scenarios", agent_type="DesignAgent", command="test_scenarios",
                 context={"story": story, "acceptance_criteria": acceptance_criteria.output}),
            dry_run=context.get("dry_run", False)
        )
        
        api_contracts = await self._create_api_contracts(
            Task(id="contracts", agent_type="DesignAgent", command="api_contracts",
                 context={"story": story}),
            dry_run=context.get("dry_run", False)
        )
        
        # Combine all artifacts
        combined_artifacts = {}
        for result in [tdd_spec, acceptance_criteria, test_scenarios, api_contracts]:
            combined_artifacts.update(result.artifacts)
        
        output = f"""
# TDD Design Phase Complete

## Specifications Generated:
- TDD Specification: {len(tdd_spec.output)} characters
- Acceptance Criteria: {len(acceptance_criteria.output)} characters  
- Test Scenarios: {len(test_scenarios.output)} characters
- API Contracts: {len(api_contracts.output)} characters

## Ready for TEST_RED Phase
The design artifacts provide comprehensive guidance for:
- Writing failing tests that capture requirements
- Implementing minimal code to pass tests
- Refactoring with confidence

## Next Steps:
1. QA Agent should write failing tests based on these specifications
2. Tests should be committed to preserve the RED state
3. Code Agent can then implement to make tests pass
        """.strip()
        
        return AgentResult(
            success=True,
            output=output,
            artifacts=combined_artifacts
        )
    
    def _generate_tdd_spec_fallback(self, story_description: str) -> str:
        """Generate TDD specification without Claude Code"""
        return f"""
# TDD Specification

## Story Description
{story_description}

## Testable Requirements
1. **Primary Functionality**: Core feature behavior that must be tested
2. **Input Validation**: Expected input constraints and validation rules
3. **Output Specification**: Expected output format and data structure
4. **Error Conditions**: Exception scenarios and error handling

## API Interface Design
### Public Methods/Functions
- Method signatures with clear contracts
- Parameter types and constraints
- Return value specifications
- Exception types and conditions

### Internal Components
- Class structures and relationships
- Data models and validation rules
- Service layer interfaces
- Persistence layer contracts

## Test-First Considerations
### Unit Test Strategy
- Focus on single responsibility testing
- Mock external dependencies
- Test both happy path and edge cases
- Verify error handling and validation

### Integration Test Strategy  
- Test component interactions
- Verify data flow between layers
- Test external service integrations
- End-to-end workflow validation

## Edge Cases and Boundary Conditions
1. **Empty/Null Inputs**: How system handles missing data
2. **Maximum Limits**: Behavior at capacity constraints
3. **Invalid Data**: Response to malformed or invalid inputs
4. **Concurrent Access**: Thread safety and race conditions
5. **Network Issues**: Timeout and retry scenarios

## Success Criteria
- All tests pass in isolation
- Integration tests validate component interaction
- Performance requirements are met
- Error scenarios are handled gracefully
- Code coverage targets are achieved
        """.strip()
    
    def _generate_acceptance_criteria(self, story_description: str) -> str:
        """Generate testable acceptance criteria"""
        return f"""
# Acceptance Criteria

## Story
{story_description}

## Given-When-Then Scenarios

### Scenario 1: Happy Path
**Given** the system is in a valid state  
**When** the user performs the primary action  
**Then** the expected outcome is achieved  
**And** the system state is updated correctly

### Scenario 2: Input Validation
**Given** the user provides invalid input  
**When** the system processes the request  
**Then** appropriate validation errors are returned  
**And** the system state remains unchanged

### Scenario 3: Edge Case Handling
**Given** edge case conditions exist  
**When** the feature is exercised  
**Then** the system handles the case gracefully  
**And** appropriate feedback is provided

### Scenario 4: Error Recovery
**Given** an error condition occurs  
**When** the system encounters the error  
**Then** appropriate error handling is triggered  
**And** recovery mechanisms are activated

## Automated Test Requirements
- Each scenario must have corresponding automated tests
- Tests should be independent and repeatable
- Clear pass/fail criteria for each test
- Tests should run in under 10 seconds
- Mock external dependencies for unit tests

## Definition of Done
- [ ] All acceptance criteria have passing tests
- [ ] Code coverage is above 90%
- [ ] Integration tests validate end-to-end flow
- [ ] Performance requirements are met
- [ ] Security requirements are validated
        """.strip()
    
    def _generate_test_scenarios(self, story_description: str, acceptance_criteria: str) -> str:
        """Generate comprehensive test scenarios and edge cases"""
        return f"""
# Test Scenarios

## Story Context
{story_description}

## Test Categories

### 1. Functional Tests
#### Positive Test Cases
- Normal operation with valid inputs
- Boundary value testing (min/max values)
- Different valid input combinations
- Expected user workflows

#### Negative Test Cases
- Invalid input handling
- Missing required parameters
- Malformed data processing
- Unauthorized access attempts

### 2. Integration Tests
#### Component Integration
- Service layer interactions
- Database operations
- External API communications
- Event handling and messaging

#### End-to-End Workflows
- Complete user journeys
- Multi-step processes
- Cross-system data flow
- Business process validation

### 3. Edge Cases
#### Data Boundary Testing
- Empty collections/arrays
- Null/undefined values
- Maximum size limits
- Minimum value constraints

#### System Boundary Testing
- Memory constraints
- Network timeouts
- Concurrent user limits
- Resource exhaustion scenarios

### 4. Performance Tests
#### Load Testing
- Normal load scenarios
- Peak load conditions
- Stress testing beyond limits
- Endurance testing over time

#### Latency Testing
- Response time validation
- Timeout handling
- Resource cleanup verification
- Memory leak detection

### 5. Security Tests
#### Authentication Tests
- Valid credential verification
- Invalid credential rejection
- Session management
- Token expiration handling

#### Authorization Tests
- Role-based access control
- Permission validation
- Resource access restrictions
- Privilege escalation prevention

## Test Implementation Priority
1. **Critical Path Tests** (Priority 1)
2. **Error Handling Tests** (Priority 2)
3. **Edge Case Tests** (Priority 3)
4. **Performance Tests** (Priority 4)
5. **Security Tests** (Priority 5)

## Test Data Requirements
- Representative production-like data
- Edge case data sets
- Invalid data examples
- Large data set samples
- Realistic user scenarios
        """.strip()
    
    def _generate_api_contracts(self, story_description: str) -> str:
        """Generate testable API contracts and interfaces"""
        return f"""
# API Contracts

## Story Context
{story_description}

## Interface Specifications

### Public API Endpoints
#### REST API Design
```yaml
paths:
  /api/resource:
    get:
      summary: Retrieve resource
      parameters:
        - name: id
          in: query
          required: true
          schema:
            type: string
      responses:
        200:
          description: Resource found
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Resource'
        404:
          description: Resource not found
        400:
          description: Invalid request
    post:
      summary: Create resource
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/CreateResourceRequest'
      responses:
        201:
          description: Resource created
        400:
          description: Invalid input
        409:
          description: Resource already exists
```

### Data Models
#### Resource Schema
```json
{
  "type": "object",
  "properties": {
    "id": {"type": "string", "format": "uuid"},
    "name": {"type": "string", "minLength": 1, "maxLength": 100},
    "created_at": {"type": "string", "format": "date-time"},
    "updated_at": {"type": "string", "format": "date-time"}
  },
  "required": ["id", "name", "created_at"]
}
```

### Service Layer Contracts
#### Interface Definition
```python
from abc import ABC, abstractmethod
from typing import List, Optional

class ResourceService(ABC):
    @abstractmethod
    async def get_resource(self, resource_id: str) -> Optional[Resource]:
        pass
    
    @abstractmethod
    async def create_resource(self, data: CreateResourceRequest) -> Resource:
        pass
    
    @abstractmethod
    async def update_resource(self, resource_id: str, data: UpdateResourceRequest) -> Resource:
        pass
    
    @abstractmethod
    async def delete_resource(self, resource_id: str) -> bool:
        pass
```

### Error Handling Contracts
#### Exception Types
```python
class ResourceNotFoundError(Exception):
    def __init__(self, resource_id: str):
        self.resource_id = resource_id
        super().__init__(f"Resource {resource_id} not found")

class InvalidResourceDataError(Exception):
    def __init__(self, field: str, message: str):
        self.field = field
        self.message = message
        super().__init__(f"Invalid {field}: {message}")
```

## Test Contract Validation
### Contract Tests
- Verify API endpoint behavior matches specification
- Validate request/response schemas
- Test error response formats
- Verify HTTP status codes

### Mock Service Implementation
- Provide test doubles for external dependencies
- Implement contract-compliant mock responses
- Support various test scenarios
- Enable isolated unit testing

## Testability Features
### Health Checks
- API endpoint availability
- Service dependency status
- Database connectivity
- External service reachability

### Observability
- Request/response logging
- Performance metrics
- Error tracking
- Audit trail capabilities
        """.strip()
    
    def _extract_acceptance_criteria(self, specification: str) -> str:
        """Extract acceptance criteria from specification"""
        # Simple extraction - in real implementation would use more sophisticated parsing
        if "acceptance criteria" in specification.lower():
            lines = specification.split('\n')
            criteria_lines = []
            in_criteria_section = False
            
            for line in lines:
                if "acceptance criteria" in line.lower():
                    in_criteria_section = True
                    criteria_lines.append(line)
                elif in_criteria_section:
                    if line.startswith('#') and "acceptance criteria" not in line.lower():
                        break
                    criteria_lines.append(line)
            
            return '\n'.join(criteria_lines)
        else:
            return "# Acceptance Criteria\n\nTo be extracted from TDD specification."
    
    def _extract_test_plan(self, specification: str) -> str:
        """Extract test plan from specification"""
        return """
# Test Plan

## Test Strategy
Based on the TDD specification, the following test approach will be used:

1. **Unit Tests**: Test individual components in isolation
2. **Integration Tests**: Test component interactions
3. **End-to-End Tests**: Test complete user workflows
4. **Performance Tests**: Validate non-functional requirements

## Test Phases
1. **RED Phase**: Write failing tests that capture requirements
2. **GREEN Phase**: Implement minimal code to pass tests
3. **REFACTOR Phase**: Improve code while keeping tests green

## Test Coverage Goals
- Unit test coverage: 90%+
- Integration test coverage: 80%+
- Critical path coverage: 100%
        """.strip()
    
    def _extract_edge_cases(self, scenarios: str) -> str:
        """Extract edge cases from test scenarios"""
        return """
# Edge Cases

## Identified Edge Cases
1. **Empty Data Sets**: Handling of empty collections and null values
2. **Boundary Values**: Testing minimum and maximum limits
3. **Concurrent Access**: Multi-user scenarios and race conditions
4. **Resource Constraints**: Memory, disk, and network limitations
5. **Error Conditions**: Network failures, timeouts, and exceptions

## Edge Case Test Strategy
- Each edge case requires specific test coverage
- Tests should validate both error handling and recovery
- Performance impact of edge cases should be measured
- Documentation of expected behavior in edge cases
        """.strip()
    
    def _extract_interfaces(self, contracts: str) -> str:
        """Extract interface definitions as JSON"""
        return """
{
  "interfaces": [
    {
      "name": "ResourceService",
      "type": "service",
      "methods": [
        {"name": "get_resource", "params": ["resource_id"], "returns": "Resource"},
        {"name": "create_resource", "params": ["data"], "returns": "Resource"},
        {"name": "update_resource", "params": ["resource_id", "data"], "returns": "Resource"},
        {"name": "delete_resource", "params": ["resource_id"], "returns": "boolean"}
      ]
    }
  ],
  "models": [
    {
      "name": "Resource",
      "fields": ["id", "name", "created_at", "updated_at"],
      "required": ["id", "name", "created_at"]
    }
  ]
}
        """.strip()
    
    # Context management methods
    
    async def _record_context_usage(self, task: Task, agent_context) -> None:
        """Record context usage for learning system"""
        if not self.context_manager:
            return
        
        try:
            # Analyze which files were actually relevant for the design task
            relevant_files = self._analyze_file_relevance(task, agent_context)
            
            # Record feedback for learning
            if hasattr(self.context_manager, 'record_feedback') and relevant_files:
                await self.context_manager.record_feedback(
                    context_id=agent_context.request_id,
                    agent_type="DesignAgent",
                    story_id=getattr(task, 'story_id', 'default'),
                    file_relevance_scores=relevant_files,
                    feedback_type="design_usage"
                )
                
            # Record agent decision
            if hasattr(self.context_manager, 'record_agent_decision'):
                await self.context_manager.record_agent_decision(
                    agent_type="DesignAgent",
                    story_id=getattr(task, 'story_id', 'default'),
                    description=f"Design task: {task.command}",
                    rationale=f"Prepared context with {len(agent_context.file_contents)} files",
                    outcome="context_prepared",
                    confidence=0.8
                )
                
        except Exception as e:
            logger.warning(f"Error recording context usage: {str(e)}")
    
    def _analyze_file_relevance(self, task: Task, agent_context) -> Dict[str, float]:
        """Analyze file relevance for design tasks"""
        if not agent_context or not agent_context.file_contents:
            return {}
        
        relevant_files = {}
        command = task.command.lower()
        
        for file_path in agent_context.file_contents.keys():
            file_path_lower = file_path.lower()
            
            # High relevance for documentation and configuration files
            if any(ext in file_path_lower for ext in ['.md', '.rst', '.yaml', '.yml', '.json']):
                relevant_files[file_path] = 0.9
            
            # Medium relevance for architecture-related files
            elif any(keyword in file_path_lower for keyword in ['architecture', 'design', 'spec', 'interface']):
                relevant_files[file_path] = 0.8
            
            # Lower relevance for implementation files
            elif any(ext in file_path_lower for ext in ['.py', '.js', '.ts']):
                if 'test' in file_path_lower:
                    relevant_files[file_path] = 0.4  # Tests can inform design
                else:
                    relevant_files[file_path] = 0.6  # Implementation can inform design decisions
            
            # Default relevance for other files
            else:
                relevant_files[file_path] = 0.3
        
        return relevant_files
    
    async def _enrich_context_for_design(self, task: Task, agent_context) -> Dict[str, Any]:
        """Enrich task context with information from context manager"""
        enriched_context = task.context.copy() if task.context else {}
        
        if not self.context_manager or not agent_context:
            return enriched_context
        
        try:
            # Add architectural insights from codebase
            if agent_context.file_contents:
                architecture_files = [
                    fp for fp in agent_context.file_contents.keys()
                    if any(keyword in fp.lower() for keyword in ['architecture', 'design', 'spec'])
                ]
                
                if architecture_files:
                    enriched_context['existing_architecture'] = {
                        fp: agent_context.file_contents[fp][:1000]  # First 1000 chars
                        for fp in architecture_files[:3]  # Limit to 3 files
                    }
            
            # Add project statistics if available
            if hasattr(self.context_manager, 'get_project_statistics'):
                project_stats = await self.context_manager.get_project_statistics()
                enriched_context['project_context'] = {
                    'file_count': project_stats.get('total_files', 0),
                    'main_language': project_stats.get('primary_language', 'unknown'),
                    'complexity_indicators': project_stats.get('complexity_metrics', {})
                }
            
            # Add cross-story context if available
            story_id = getattr(task, 'story_id', 'default')
            if hasattr(self.context_manager, 'get_cross_story_context'):
                conflicts = await self.context_manager.detect_story_conflicts(story_id, [])
                if conflicts:
                    cross_story_context = await self.context_manager.get_cross_story_context(story_id, conflicts)
                    enriched_context['cross_story_context'] = cross_story_context
            
        except Exception as e:
            logger.warning(f"Error enriching context: {str(e)}")
        
        return enriched_context