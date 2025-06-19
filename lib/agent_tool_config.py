"""
Agent Tool Configuration

Defines which Claude Code tools each agent type is allowed to use.
This provides security boundaries to prevent agents from executing 
inappropriate or dangerous commands.
"""

from typing import Dict, List, Set, Any
from enum import Enum


class AgentType(Enum):
    """Agent types in the system"""
    ORCHESTRATOR = "Orchestrator"  # System orchestrator with full permissions
    DESIGN = "DesignAgent"
    CODE = "CodeAgent" 
    QA = "QAAgent"
    DATA = "DataAgent"


# Commands that most agents should not have access to (but orchestrator can)
RESTRICTED_COMMANDS = [
    "sudo", "su",  # Privilege escalation
    "chmod", "chown",  # Permission changes  
    "kill", "killall",  # Process termination
    "format", "fdisk",  # Disk operations
    "dd", "shred",  # Data destruction
    "curl", "wget",  # Network downloads (potential security risk)
    "ssh", "scp", "rsync",  # Remote access
    "npm publish", "pip install --user",  # Package publishing
    "docker run", "docker exec",  # Container operations
]

# Commands that should be restricted to orchestrator and select agents
ELEVATED_COMMANDS = [
    "rm", "rmdir", "del", "delete",  # File deletion (orchestrator only)
    "git push",  # Publishing changes (orchestrator only)
]

# Commands that orchestrator and code agent might need
CODE_MANAGEMENT_COMMANDS = [
    "git commit",  # Version control commits
    "git add",  # Stage changes
    "git reset",  # Reset changes
]

# TDD-specific commands that require special handling
TDD_COMMANDS = [
    "pytest --tb=short",  # TDD test execution with concise output
    "pytest -v",  # Verbose test execution for TDD validation
    "coverage run",  # Code coverage measurement for TDD
    "coverage report",  # Coverage reporting for TDD quality
    "git status --porcelain",  # Check working directory status for TDD commits
    "git diff --name-only",  # Check file changes for TDD validation
]

# Agent-specific tool configurations
AGENT_TOOL_CONFIG: Dict[AgentType, Dict[str, List[str]]] = {
    
    AgentType.ORCHESTRATOR: {
        "allowed_tools": [
            # Full access to all tools for system management
            "Read", "Write", "Edit", "MultiEdit",
            "Glob", "Grep", "LS", 
            "NotebookRead", "NotebookEdit",
            "TodoRead", "TodoWrite",
            "WebFetch", "WebSearch",
            "Task",  # Can spawn sub-agents
            # Full bash access including elevated commands
            "Bash(*)",  # Allow all bash commands
        ],
        "disallowed_tools": [
            # Still block the most dangerous system commands
            "Bash(sudo)", "Bash(su)",  # No privilege escalation
            "Bash(format)", "Bash(fdisk)",  # No disk formatting
            "Bash(dd)", "Bash(shred)",  # No data destruction
        ]
    },
    
    AgentType.DESIGN: {
        "allowed_tools": [
            "Read",  # Read files for analysis
            "Write",  # Create architecture documents
            "Glob",  # Find files by pattern
            "Grep",  # Search file contents
            "LS",  # List directories
            "WebFetch",  # Research documentation
            "WebSearch",  # Research best practices
            "Bash(ls)",  # List files
            "Bash(find)",  # Find files (safe search)
            "Bash(head)",  # Preview files
            "Bash(tail)",  # Preview files
            "Bash(cat)",  # Read files
            "Bash(tree)",  # Directory structure
            # TDD-specific tools for design phase
            "Bash(wc)",  # Count lines for specification sizing
            "Bash(grep -r)",  # Search for patterns across project
        ],
        "disallowed_tools": [
            "Edit",  # Should not modify existing code
            "MultiEdit",  # Should not modify existing code
            "NotebookEdit",  # Should not modify notebooks
            "TodoWrite",  # Should not manage todos
        ] + [f"Bash({cmd})" for cmd in RESTRICTED_COMMANDS + ELEVATED_COMMANDS]
    },
    
    AgentType.CODE: {
        "allowed_tools": [
            "Read",  # Read existing code
            "Write",  # Create new files
            "Edit",  # Modify existing code
            "MultiEdit",  # Multiple edits
            "Glob",  # Find code files
            "Grep",  # Search code
            "LS",  # List directories
            "Bash(python)",  # Run Python scripts
            "Bash(node)",  # Run Node.js
            "Bash(npm)",  # Package management
            "Bash(pip)",  # Python packages (limited)
            "Bash(pytest)",  # Run tests
            "Bash(pylint)",  # Code quality
            "Bash(flake8)",  # Code linting
            "Bash(black)",  # Code formatting
            "Bash(mypy)",  # Type checking
            "Bash(git status)",  # Check git status
            "Bash(git diff)",  # Check changes
            "Bash(git log)",  # Check history
            "Bash(git add)",  # Stage changes
            "Bash(git commit)",  # Commit changes
            "Bash(git reset)",  # Reset changes (limited)
            "Bash(ls)",  # List files
            "Bash(find)",  # Find files
            "Bash(grep)",  # Search files
            "Bash(head)",  # Preview files
            "Bash(tail)",  # Preview files
            "Bash(cat)",  # Read files
            "Bash(mkdir)",  # Create directories
            "Bash(cp)",  # Copy files (limited)
            "Bash(mv)",  # Move files (limited)
            # TDD-specific tools for CODE_GREEN and REFACTOR phases
            "Bash(pytest --tb=short)",  # Concise test output for TDD validation
            "Bash(pytest -v)",  # Verbose test execution for debugging
            "Bash(pytest --cov)",  # Coverage analysis during implementation
            "Bash(coverage run)",  # Code coverage measurement
            "Bash(coverage report)",  # Coverage reporting
            "Bash(coverage html)",  # HTML coverage reports
            "Bash(git status --porcelain)",  # Clean status checking for TDD commits
            "Bash(git diff --name-only)",  # File change validation
            "Bash(git diff --stat)",  # Summary of changes for commit preparation
            "Bash(isort)",  # Import sorting for code quality
            "Bash(autopep8)",  # Code formatting for refactoring
        ],
        "disallowed_tools": [
            "TodoWrite",  # Should not manage todos directly
        ] + [f"Bash({cmd})" for cmd in RESTRICTED_COMMANDS + ELEVATED_COMMANDS]
    },
    
    AgentType.QA: {
        "allowed_tools": [
            "Read",  # Read code and test files
            "Write",  # Create test files for TDD TEST_RED phase
            "Glob",  # Find test files
            "Grep",  # Search for test patterns
            "LS",  # List directories
            "Bash(pytest)",  # Run tests
            "Bash(coverage)",  # Coverage analysis
            "Bash(python -m pytest)",  # Run tests
            "Bash(python -m coverage)",  # Coverage analysis
            "Bash(pylint)",  # Code quality analysis
            "Bash(flake8)",  # Linting
            "Bash(mypy)",  # Type checking
            "Bash(bandit)",  # Security analysis
            "Bash(safety)",  # Dependency security
            "Bash(ls)",  # List files
            "Bash(find)",  # Find files
            "Bash(grep)",  # Search files
            "Bash(head)",  # Preview files
            "Bash(tail)",  # Preview files
            "Bash(cat)",  # Read files
            "Bash(wc)",  # Count lines/words
            "Bash(diff)",  # Compare files
            # TDD-specific tools for TEST_RED phase
            "Bash(pytest --tb=short)",  # Concise test failure output for TDD
            "Bash(pytest -v --tb=long)",  # Detailed test output for debugging
            "Bash(pytest --collect-only)",  # Test discovery for validation
            "Bash(pytest --dry-run)",  # Test syntax validation
            "Bash(pytest -k)",  # Selective test execution
            "Bash(python -m unittest)",  # Alternative test framework
            "Bash(python -c)",  # Quick Python execution for test validation
            "Bash(python -m py_compile)",  # Syntax checking for test files
        ],
        "disallowed_tools": [
            "Edit",  # Should not modify existing code (only create test files)
            "MultiEdit",  # Should not modify existing code
            "NotebookEdit",  # Should not modify notebooks
            "TodoWrite",  # Should not manage todos
            # TDD-specific restrictions for QA Agent
            "Bash(git add)",  # Should not stage files directly
            "Bash(git commit)",  # Should not commit changes
            "Bash(git push)",  # Should not push changes
        ] + [f"Bash({cmd})" for cmd in RESTRICTED_COMMANDS + ELEVATED_COMMANDS]
    },
    
    AgentType.DATA: {
        "allowed_tools": [
            "Read",  # Read data files
            "Write",  # Create reports and analysis
            "Glob",  # Find data files
            "Grep",  # Search data files
            "LS",  # List directories
            "NotebookRead",  # Read Jupyter notebooks
            "NotebookEdit",  # Create data analysis notebooks
            "Bash(python)",  # Run data scripts
            "Bash(jupyter)",  # Jupyter operations
            "Bash(pandas)",  # Data processing
            "Bash(numpy)",  # Numerical operations
            "Bash(matplotlib)",  # Visualization
            "Bash(seaborn)",  # Statistical visualization
            "Bash(sqlite3)",  # Database queries (read-only)
            "Bash(csvkit)",  # CSV processing
            "Bash(jq)",  # JSON processing
            "Bash(ls)",  # List files
            "Bash(find)",  # Find files
            "Bash(grep)",  # Search files
            "Bash(head)",  # Preview files
            "Bash(tail)",  # Preview files
            "Bash(cat)",  # Read files
            "Bash(wc)",  # Count records
            "Bash(sort)",  # Sort data
            "Bash(uniq)",  # Unique values
            "Bash(cut)",  # Extract columns
            "Bash(awk)",  # Text processing
            "Bash(sed)",  # Text processing
        ],
        "disallowed_tools": [
            "Edit",  # Should not modify source code
            "MultiEdit",  # Should not modify source code
            "TodoWrite",  # Should not manage todos
        ] + [f"Bash({cmd})" for cmd in RESTRICTED_COMMANDS + ELEVATED_COMMANDS + CODE_MANAGEMENT_COMMANDS]
    }
}


def get_allowed_tools(agent_type: AgentType) -> List[str]:
    """Get list of allowed tools for an agent type"""
    config = AGENT_TOOL_CONFIG.get(agent_type, {})
    return config.get("allowed_tools", [])


def get_disallowed_tools(agent_type: AgentType) -> List[str]:
    """Get list of disallowed tools for an agent type"""
    config = AGENT_TOOL_CONFIG.get(agent_type, {})
    
    # Flatten the disallowed tools list (some entries might be lists)
    disallowed = []
    for item in config.get("disallowed_tools", []):
        if isinstance(item, list):
            disallowed.extend(item)
        else:
            disallowed.append(item)
    
    return disallowed


def get_claude_tool_args(agent_type: AgentType) -> List[str]:
    """
    Get Claude CLI arguments for tool restrictions.
    
    Returns list of arguments to pass to claude command, e.g.:
    ["--allowedTools", "Read Write Glob", "--disallowedTools", "Bash(rm) Edit"]
    """
    args = []
    
    allowed = get_allowed_tools(agent_type)
    if allowed:
        args.extend(["--allowedTools", " ".join(allowed)])
    
    disallowed = get_disallowed_tools(agent_type)
    if disallowed:
        args.extend(["--disallowedTools", " ".join(disallowed)])
    
    return args


def validate_agent_access(agent_type: AgentType, tool_name: str) -> bool:
    """
    Validate if an agent type has access to a specific tool.
    Optimized for better performance with caching.
    
    Args:
        agent_type: Type of agent
        tool_name: Name of the tool to check
        
    Returns:
        True if agent has access, False otherwise
    """
    # Cache validation results for performance
    cache_key = f"{agent_type.value}:{tool_name}"
    if hasattr(validate_agent_access, '_cache'):
        if cache_key in validate_agent_access._cache:
            return validate_agent_access._cache[cache_key]
    else:
        validate_agent_access._cache = {}
    
    # Perform validation
    allowed = get_allowed_tools(agent_type)
    disallowed = get_disallowed_tools(agent_type)
    
    result = False
    
    # Check if explicitly disallowed (fastest check first)
    if tool_name in disallowed:
        result = False
    # Check if explicitly allowed
    elif tool_name in allowed:
        result = True
    # Check bash command patterns
    elif tool_name.startswith("Bash("):
        cmd = tool_name[5:-1]  # Extract command from Bash(command)
        
        # Check if specific bash command is allowed
        for allowed_tool in allowed:
            if allowed_tool.startswith("Bash(") and cmd in allowed_tool:
                result = True
                break
        
        # Check if command is in restricted lists (only if not already allowed)
        if not result:
            all_restricted = RESTRICTED_COMMANDS + ELEVATED_COMMANDS + CODE_MANAGEMENT_COMMANDS
            if any(restricted in cmd for restricted in all_restricted):
                result = False
    # Default to not allowed if not explicitly permitted
    else:
        result = False
    
    # Cache the result
    validate_agent_access._cache[cache_key] = result
    return result


def get_security_summary(agent_type: AgentType) -> Dict[str, any]:
    """Get security configuration summary for an agent"""
    return {
        "agent_type": agent_type.value,
        "allowed_tools_count": len(get_allowed_tools(agent_type)),
        "disallowed_tools_count": len(get_disallowed_tools(agent_type)),
        "allowed_tools": get_allowed_tools(agent_type),
        "disallowed_tools": get_disallowed_tools(agent_type)[:10],  # First 10 for brevity
        "restricted_commands_blocked": len(RESTRICTED_COMMANDS + ELEVATED_COMMANDS + CODE_MANAGEMENT_COMMANDS),
        "tdd_capabilities": get_tdd_capabilities(agent_type)
    }


def get_tdd_capabilities(agent_type: AgentType) -> Dict[str, any]:
    """Get TDD-specific capabilities for an agent type"""
    tdd_capabilities = {
        AgentType.ORCHESTRATOR: {
            "can_coordinate_tdd_cycles": True,
            "can_manage_all_phases": True,
            "tdd_phases": ["DESIGN", "TEST_RED", "CODE_GREEN", "REFACTOR", "COMMIT"],
            "special_permissions": ["full_git_access", "cross_agent_coordination"]
        },
        AgentType.DESIGN: {
            "can_coordinate_tdd_cycles": False,
            "can_manage_all_phases": False,
            "tdd_phases": ["DESIGN"],
            "capabilities": [
                "tdd_specification_creation",
                "acceptance_criteria_definition",
                "test_scenario_design",
                "api_contract_creation",
                "testable_architecture_design"
            ],
            "restrictions": ["read_only_code_access", "no_test_execution", "no_code_modification"]
        },
        AgentType.CODE: {
            "can_coordinate_tdd_cycles": False,
            "can_manage_all_phases": False,
            "tdd_phases": ["CODE_GREEN", "REFACTOR", "COMMIT"],
            "capabilities": [
                "minimal_implementation_creation",
                "test_driven_development",
                "code_refactoring_with_test_preservation",
                "tdd_commit_management",
                "green_state_validation"
            ],
            "test_tools": ["pytest", "coverage", "quality_analysis"],
            "git_permissions": ["add", "commit", "status", "diff"]
        },
        AgentType.QA: {
            "can_coordinate_tdd_cycles": False,
            "can_manage_all_phases": False,
            "tdd_phases": ["TEST_RED"],
            "capabilities": [
                "failing_test_creation",
                "comprehensive_test_suite_generation",
                "test_red_state_validation",
                "test_coverage_analysis",
                "test_organization_and_structure"
            ],
            "test_frameworks": ["pytest", "unittest", "coverage"],
            "restrictions": ["cannot_modify_implementation_code", "cannot_commit_changes"]
        },
        AgentType.DATA: {
            "can_coordinate_tdd_cycles": False,
            "can_manage_all_phases": False,
            "tdd_phases": [],
            "capabilities": [
                "tdd_metrics_analysis",
                "test_coverage_reporting",
                "quality_metrics_visualization",
                "tdd_cycle_performance_analysis"
            ],
            "restrictions": ["read_only_access", "no_code_modification", "no_test_execution"]
        }
    }
    
    return tdd_capabilities.get(agent_type, {
        "can_coordinate_tdd_cycles": False,
        "can_manage_all_phases": False,
        "tdd_phases": [],
        "capabilities": [],
        "restrictions": ["no_tdd_access"]
    })


def validate_tdd_phase_access(agent_type: AgentType, tdd_phase: str) -> bool:
    """
    Validate if an agent type has access to a specific TDD phase.
    
    Args:
        agent_type: Type of agent
        tdd_phase: TDD phase to check (DESIGN, TEST_RED, CODE_GREEN, REFACTOR, COMMIT)
        
    Returns:
        True if agent has access to the phase, False otherwise
    """
    capabilities = get_tdd_capabilities(agent_type)
    return tdd_phase in capabilities.get("tdd_phases", [])


def get_tdd_tool_restrictions(agent_type: AgentType) -> Dict[str, List[str]]:
    """
    Get TDD-specific tool restrictions for an agent type.
    
    Args:
        agent_type: Type of agent
        
    Returns:
        Dictionary with TDD tool restrictions
    """
    base_restrictions = {
        "pytest_restrictions": [],
        "git_restrictions": [],
        "file_access_restrictions": [],
        "special_tdd_tools": []
    }
    
    if agent_type == AgentType.DESIGN:
        return {
            "pytest_restrictions": ["cannot_execute_tests"],
            "git_restrictions": ["read_only_git_access"],
            "file_access_restrictions": ["cannot_modify_existing_code", "can_create_documentation"],
            "special_tdd_tools": ["specification_generation", "acceptance_criteria_creation"]
        }
    elif agent_type == AgentType.QA:
        return {
            "pytest_restrictions": ["can_execute_tests", "can_create_test_files"],
            "git_restrictions": ["cannot_commit", "cannot_push"],
            "file_access_restrictions": ["can_create_test_files", "cannot_modify_implementation"],
            "special_tdd_tools": ["test_file_generation", "red_state_validation"]
        }
    elif agent_type == AgentType.CODE:
        return {
            "pytest_restrictions": ["can_execute_tests", "can_validate_green_state"],
            "git_restrictions": ["can_add", "can_commit", "cannot_push"],
            "file_access_restrictions": ["can_modify_implementation", "cannot_modify_tests"],
            "special_tdd_tools": ["minimal_implementation", "refactoring_tools", "commit_management"]
        }
    elif agent_type == AgentType.ORCHESTRATOR:
        return {
            "pytest_restrictions": ["full_test_access"],
            "git_restrictions": ["full_git_access"],
            "file_access_restrictions": ["full_file_access"],
            "special_tdd_tools": ["cycle_coordination", "phase_management", "cross_agent_communication"]
        }
    
    return base_restrictions


def validate_tdd_tool_access(agent_type: AgentType, tool_name: str, tdd_context: Dict[str, any] = None) -> Dict[str, any]:
    """
    Validate tool access in TDD context with detailed reasoning.
    
    Args:
        agent_type: Type of agent
        tool_name: Name of the tool to validate
        tdd_context: Optional TDD context (phase, cycle info, etc.)
        
    Returns:
        Dictionary with validation result and reasoning
    """
    base_access = validate_agent_access(agent_type, tool_name)
    tdd_restrictions = get_tdd_tool_restrictions(agent_type)
    current_phase = tdd_context.get("current_phase") if tdd_context else None
    
    result = {
        "allowed": base_access,
        "agent_type": agent_type.value,
        "tool_name": tool_name,
        "current_phase": current_phase,
        "reasoning": [],
        "tdd_specific_restrictions": [],
        "recommendations": []
    }
    
    # Add base access reasoning
    if base_access:
        result["reasoning"].append(f"Tool {tool_name} is in allowed tools for {agent_type.value}")
    else:
        result["reasoning"].append(f"Tool {tool_name} is not in allowed tools for {agent_type.value}")
    
    # Add TDD-specific validations
    if "pytest" in tool_name.lower():
        if "cannot_execute_tests" in tdd_restrictions["pytest_restrictions"]:
            result["allowed"] = False
            result["tdd_specific_restrictions"].append("Agent cannot execute tests in TDD workflow")
        elif "can_execute_tests" in tdd_restrictions["pytest_restrictions"]:
            result["reasoning"].append("Agent has TDD test execution permissions")
    
    if "git" in tool_name.lower():
        git_restrictions = tdd_restrictions["git_restrictions"]
        if "read_only_git_access" in git_restrictions and any(cmd in tool_name for cmd in ["add", "commit", "push"]):
            result["allowed"] = False
            result["tdd_specific_restrictions"].append("Agent has read-only git access in TDD workflow")
        elif "cannot_commit" in git_restrictions and "commit" in tool_name:
            result["allowed"] = False
            result["tdd_specific_restrictions"].append("Agent cannot commit in TDD workflow")
        elif "cannot_push" in git_restrictions and "push" in tool_name:
            result["allowed"] = False
            result["tdd_specific_restrictions"].append("Agent cannot push in TDD workflow")
    
    # Add phase-specific recommendations
    if current_phase:
        phase_valid = validate_tdd_phase_access(agent_type, current_phase)
        if not phase_valid:
            result["recommendations"].append(f"Agent should not be active in {current_phase} phase")
        else:
            result["recommendations"].append(f"Agent is properly configured for {current_phase} phase")
    
    return result


def validate_agent_command_security(agent_type: AgentType, command: str) -> Dict[str, Any]:
    """
    Comprehensive security validation for agent commands.
    
    Args:
        agent_type: Type of agent requesting command
        command: Command to validate
        
    Returns:
        Dictionary with validation result and security assessment
    """
    import re
    
    result = {
        "allowed": False,
        "agent_type": agent_type.value,
        "command": command,
        "security_violations": [],
        "recommendations": [],
        "risk_level": "low"
    }
    
    # SECURITY: Basic command sanitization
    if not isinstance(command, str) or len(command) > 500:
        result["security_violations"].append("Invalid command format or length")
        result["risk_level"] = "high"
        return result
    
    # Check for dangerous patterns
    dangerous_patterns = [
        r'rm\s+-rf\s+/',           # Recursive force delete
        r'sudo\s+',                # Privilege escalation
        r'curl\s+.*\|\s*sh',       # Remote code execution
        r'wget\s+.*\|\s*sh',       # Remote code execution
        r'eval\s*\(',              # Code evaluation
        r'exec\s*\(',              # Code execution
        r'\.\./',                  # Path traversal
        r'\$\(',                   # Command substitution
        r'`',                      # Command substitution
        r'&&\s*rm\s+',            # Chained dangerous commands
        r'\|\s*rm\s+',            # Piped dangerous commands
    ]
    
    for pattern in dangerous_patterns:
        if re.search(pattern, command, re.IGNORECASE):
            result["security_violations"].append(f"Dangerous pattern detected: {pattern}")
            result["risk_level"] = "critical"
    
    # Apply agent-specific restrictions
    base_access = validate_agent_access(agent_type, f"Bash({command})")
    result["allowed"] = base_access and len(result["security_violations"]) == 0
    
    # Add agent-specific recommendations
    if agent_type == AgentType.DESIGN:
        if any(word in command.lower() for word in ['edit', 'write', 'modify', 'delete']):
            result["recommendations"].append("Design agents should use read-only operations")
    
    elif agent_type == AgentType.QA:
        if 'git push' in command.lower() or 'git commit' in command.lower():
            result["recommendations"].append("QA agents should not commit or push changes")
    
    elif agent_type == AgentType.DATA:
        if any(word in command.lower() for word in ['sudo', 'install', 'remove']):
            result["recommendations"].append("Data agents should focus on analysis operations")
    
    # Set risk level based on violations
    if result["security_violations"]:
        if len(result["security_violations"]) > 2:
            result["risk_level"] = "critical"
        elif any("dangerous" in v.lower() for v in result["security_violations"]):
            result["risk_level"] = "high"
        else:
            result["risk_level"] = "medium"
    
    return result