"""
Agent Tool Configuration

Defines which Claude Code tools each agent type is allowed to use.
This provides security boundaries to prevent agents from executing 
inappropriate or dangerous commands.
"""

from typing import Dict, List, Set
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
        ],
        "disallowed_tools": [
            "TodoWrite",  # Should not manage todos directly
        ] + [f"Bash({cmd})" for cmd in RESTRICTED_COMMANDS + ELEVATED_COMMANDS]
    },
    
    AgentType.QA: {
        "allowed_tools": [
            "Read",  # Read code and test files
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
        ],
        "disallowed_tools": [
            "Write",  # Should not create new code files
            "Edit",  # Should not modify existing code
            "MultiEdit",  # Should not modify existing code
            "NotebookEdit",  # Should not modify notebooks
            "TodoWrite",  # Should not manage todos
        ] + [f"Bash({cmd})" for cmd in RESTRICTED_COMMANDS + ELEVATED_COMMANDS + CODE_MANAGEMENT_COMMANDS]
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
    
    Args:
        agent_type: Type of agent
        tool_name: Name of the tool to check
        
    Returns:
        True if agent has access, False otherwise
    """
    allowed = get_allowed_tools(agent_type)
    disallowed = get_disallowed_tools(agent_type)
    
    # Check if explicitly disallowed
    if tool_name in disallowed:
        return False
    
    # Check if explicitly allowed
    if tool_name in allowed:
        return True
    
    # Check bash command patterns
    if tool_name.startswith("Bash("):
        cmd = tool_name[5:-1]  # Extract command from Bash(command)
        
        # Check if specific bash command is allowed
        for allowed_tool in allowed:
            if allowed_tool.startswith("Bash(") and cmd in allowed_tool:
                return True
        
        # Check if command is in restricted lists
        all_restricted = RESTRICTED_COMMANDS + ELEVATED_COMMANDS + CODE_MANAGEMENT_COMMANDS
        if any(restricted in cmd for restricted in all_restricted):
            return False
    
    # Default to not allowed if not explicitly permitted
    return False


def get_security_summary(agent_type: AgentType) -> Dict[str, any]:
    """Get security configuration summary for an agent"""
    return {
        "agent_type": agent_type.value,
        "allowed_tools_count": len(get_allowed_tools(agent_type)),
        "disallowed_tools_count": len(get_disallowed_tools(agent_type)),
        "allowed_tools": get_allowed_tools(agent_type),
        "disallowed_tools": get_disallowed_tools(agent_type)[:10],  # First 10 for brevity
        "restricted_commands_blocked": len(RESTRICTED_COMMANDS + ELEVATED_COMMANDS + CODE_MANAGEMENT_COMMANDS)
    }