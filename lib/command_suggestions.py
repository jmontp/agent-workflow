#!/usr/bin/env python3
"""
Command Suggestions System

Provides intelligent, context-aware command suggestions and autocomplete
functionality based on current workflow state, user patterns, and system context.
"""

import logging
import re
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from datetime import datetime

# Import state system components
try:
    from .state_machine import State, StateMachine
    from .state_broadcaster import broadcaster
except ImportError:
    # Fallback for standalone usage
    from state_machine import State, StateMachine
    from state_broadcaster import broadcaster

logger = logging.getLogger(__name__)


@dataclass
class CommandSuggestion:
    """Represents a command suggestion with metadata"""
    command: str
    description: str
    usage: str
    examples: List[str]
    priority: int
    available: bool
    reason: str  # Why this command is suggested
    parameters: List[Dict[str, Any]]  # Suggested parameters
    shortcuts: List[str]  # Keyboard shortcuts or aliases


@dataclass
class ParameterSuggestion:
    """Represents a parameter suggestion for a command"""
    name: str
    value: str
    description: str
    required: bool
    type: str  # "string", "number", "boolean", "choice"
    choices: Optional[List[str]] = None


class CommandSuggestionsEngine:
    """
    Intelligent command suggestions engine that provides context-aware
    autocomplete and command recommendations.
    """
    
    def __init__(self, state_machine: Optional[StateMachine] = None):
        self.state_machine = state_machine or StateMachine()
        self.command_patterns = self._initialize_command_patterns()
        self.parameter_patterns = self._initialize_parameter_patterns()
        self.user_patterns: Dict[str, Dict[str, Any]] = {}  # Track user command patterns
        self.recent_commands: List[Dict[str, Any]] = []
        
        logger.info("Command suggestions engine initialized")
    
    def _initialize_command_patterns(self) -> Dict[str, Dict[str, Any]]:
        """Initialize command patterns with metadata"""
        return {
            "/epic": {
                "description": "Define a new high-level initiative or feature",
                "usage": '/epic "Epic description"',
                "examples": [
                    '/epic "Implement user authentication system"',
                    '/epic "Add real-time chat functionality"',
                    '/epic "Improve application performance"'
                ],
                "parameters": [
                    {
                        "name": "description",
                        "type": "string",
                        "required": True,
                        "description": "High-level description of the epic",
                        "min_length": 10,
                        "max_length": 200
                    }
                ],
                "valid_states": ["IDLE", "BACKLOG_READY"],
                "shortcuts": ["ep", "epic"],
                "category": "planning"
            },
            "/approve": {
                "description": "Approve proposed stories or tasks",
                "usage": "/approve [story-ids]",
                "examples": [
                    "/approve",
                    "/approve story-1,story-2",
                    "/approve all"
                ],
                "parameters": [
                    {
                        "name": "story_ids",
                        "type": "choice",
                        "required": False,
                        "description": "Comma-separated story IDs to approve",
                        "choices": ["all", "pending"]
                    }
                ],
                "valid_states": ["BACKLOG_READY"],
                "shortcuts": ["app", "approve"],
                "category": "approval"
            },
            "/sprint": {
                "description": "Sprint lifecycle management",
                "usage": "/sprint <action> [parameters]",
                "examples": [
                    "/sprint plan story-1,story-2",
                    "/sprint start",
                    "/sprint status",
                    "/sprint pause",
                    "/sprint resume"
                ],
                "parameters": [
                    {
                        "name": "action",
                        "type": "choice",
                        "required": True,
                        "description": "Sprint action to perform",
                        "choices": ["plan", "start", "status", "pause", "resume"]
                    },
                    {
                        "name": "story_ids",
                        "type": "string",
                        "required": False,
                        "description": "Story IDs for sprint planning"
                    }
                ],
                "valid_states": ["BACKLOG_READY", "SPRINT_PLANNED", "SPRINT_ACTIVE", "SPRINT_PAUSED"],
                "shortcuts": ["sp", "sprint"],
                "category": "execution"
            },
            "/backlog": {
                "description": "Manage product and sprint backlog",
                "usage": "/backlog <action> [parameters]",
                "examples": [
                    "/backlog view",
                    '/backlog add_story "New feature description"',
                    "/backlog prioritize story-1,story-2"
                ],
                "parameters": [
                    {
                        "name": "action",
                        "type": "choice",
                        "required": True,
                        "description": "Backlog action to perform",
                        "choices": ["view", "add_story", "prioritize", "remove"]
                    },
                    {
                        "name": "description",
                        "type": "string",
                        "required": False,
                        "description": "Story description for add_story"
                    },
                    {
                        "name": "story_ids",
                        "type": "string",
                        "required": False,
                        "description": "Story IDs for prioritize/remove"
                    }
                ],
                "valid_states": ["IDLE", "BACKLOG_READY", "SPRINT_PLANNED", "SPRINT_ACTIVE", "SPRINT_PAUSED"],
                "shortcuts": ["bl", "backlog"],
                "category": "planning"
            },
            "/state": {
                "description": "Show current workflow state and available commands",
                "usage": "/state",
                "examples": ["/state"],
                "parameters": [],
                "valid_states": ["IDLE", "BACKLOG_READY", "SPRINT_PLANNED", "SPRINT_ACTIVE", "SPRINT_PAUSED", "SPRINT_REVIEW", "BLOCKED"],
                "shortcuts": ["st", "status"],
                "category": "information"
            },
            "/project": {
                "description": "Project management operations",
                "usage": "/project <action> [parameters]",
                "examples": [
                    "/project register /path/to/project",
                    "/project list",
                    "/project switch my-project"
                ],
                "parameters": [
                    {
                        "name": "action",
                        "type": "choice",
                        "required": True,
                        "description": "Project action to perform",
                        "choices": ["register", "list", "switch", "status"]
                    },
                    {
                        "name": "path_or_name",
                        "type": "string",
                        "required": False,
                        "description": "Project path or name"
                    }
                ],
                "valid_states": ["IDLE", "BACKLOG_READY"],
                "shortcuts": ["proj", "project"],
                "category": "setup"
            },
            "/request_changes": {
                "description": "Request changes to a pull request",
                "usage": '/request_changes "Change description"',
                "examples": [
                    '/request_changes "Please add unit tests"',
                    '/request_changes "Code review feedback: improve error handling"'
                ],
                "parameters": [
                    {
                        "name": "description",
                        "type": "string",
                        "required": True,
                        "description": "Description of requested changes"
                    }
                ],
                "valid_states": ["SPRINT_REVIEW"],
                "shortcuts": ["rc", "changes"],
                "category": "review"
            },
            "/help": {
                "description": "Show available commands and usage information",
                "usage": "/help [command]",
                "examples": [
                    "/help",
                    "/help epic",
                    "/help sprint"
                ],
                "parameters": [
                    {
                        "name": "command",
                        "type": "choice",
                        "required": False,
                        "description": "Specific command to get help for",
                        "choices": ["epic", "approve", "sprint", "backlog", "state", "project", "request_changes"]
                    }
                ],
                "valid_states": ["IDLE", "BACKLOG_READY", "SPRINT_PLANNED", "SPRINT_ACTIVE", "SPRINT_PAUSED", "SPRINT_REVIEW", "BLOCKED"],
                "shortcuts": ["h", "?"],
                "category": "information"
            }
        }
    
    def _initialize_parameter_patterns(self) -> Dict[str, List[str]]:
        """Initialize common parameter patterns"""
        return {
            "story_descriptions": [
                "Implement user login functionality",
                "Add password reset feature",
                "Create user profile page", 
                "Implement data validation",
                "Add error handling",
                "Create API endpoints",
                "Write unit tests",
                "Update documentation"
            ],
            "epic_descriptions": [
                "User authentication system",
                "Payment processing integration",
                "Real-time notifications",
                "Performance optimization",
                "Mobile app development",
                "Data analytics dashboard",
                "Security improvements",
                "User experience enhancements"
            ],
            "common_paths": [
                "/home/user/projects/",
                "/workspace/",
                "/dev/",
                "~/projects/"
            ]
        }
    
    def get_command_suggestions(self, partial_input: str = "", current_state: str = None, 
                              user_id: str = "default", project_name: str = "default",
                              limit: int = 10) -> List[CommandSuggestion]:
        """
        Get intelligent command suggestions based on current context.
        
        Args:
            partial_input: Partial command input from user
            current_state: Current workflow state
            user_id: User identifier for personalization
            project_name: Project context
            limit: Maximum number of suggestions
            
        Returns:
            List of command suggestions ordered by relevance
        """
        # Get current state if not provided
        if current_state is None:
            current_state = self.state_machine.current_state.value
        
        # Parse partial input
        parsed_input = self._parse_partial_input(partial_input)
        
        # Generate base suggestions
        suggestions = []
        
        if parsed_input["type"] == "command":
            suggestions = self._get_command_completions(
                parsed_input["command"], current_state, user_id
            )
        elif parsed_input["type"] == "parameter":
            suggestions = self._get_parameter_suggestions(
                parsed_input["command"], parsed_input["parameters"], current_state
            )
        else:
            # No input or invalid - show all available commands
            suggestions = self._get_all_available_commands(current_state, user_id)
        
        # Apply contextual ranking
        suggestions = self._apply_contextual_ranking(suggestions, current_state, user_id)
        
        # Apply user personalization
        suggestions = self._apply_user_personalization(suggestions, user_id)
        
        # Sort by priority and limit results
        suggestions.sort(key=lambda x: x.priority, reverse=True)
        
        return suggestions[:limit]
    
    def get_parameter_suggestions(self, command: str, parameter_name: str, current_value: str = "",
                                current_state: str = None, project_name: str = "default") -> List[ParameterSuggestion]:
        """
        Get parameter suggestions for a specific command parameter.
        
        Args:
            command: The command being typed
            parameter_name: Name of the parameter
            current_value: Current partial value
            current_state: Current workflow state
            project_name: Project context
            
        Returns:
            List of parameter suggestions
        """
        if current_state is None:
            current_state = self.state_machine.current_state.value
        
        command_pattern = self.command_patterns.get(command, {})
        parameters = command_pattern.get("parameters", [])
        
        # Find the parameter definition
        param_def = None
        for param in parameters:
            if param["name"] == parameter_name:
                param_def = param
                break
        
        if not param_def:
            return []
        
        suggestions = []
        
        if param_def["type"] == "choice":
            # Predefined choices
            choices = param_def.get("choices", [])
            for choice in choices:
                if choice.lower().startswith(current_value.lower()):
                    suggestions.append(ParameterSuggestion(
                        name=parameter_name,
                        value=choice,
                        description=f"Standard option: {choice}",
                        required=param_def.get("required", False),
                        type="choice"
                    ))
        
        elif param_def["type"] == "string":
            # Context-based string suggestions
            if parameter_name == "description":
                if command == "/epic":
                    patterns = self.parameter_patterns.get("epic_descriptions", [])
                elif command == "/backlog" and "story" in current_value.lower():
                    patterns = self.parameter_patterns.get("story_descriptions", [])
                else:
                    patterns = []
                
                for pattern in patterns:
                    if not current_value or pattern.lower().startswith(current_value.lower()):
                        suggestions.append(ParameterSuggestion(
                            name=parameter_name,
                            value=pattern,
                            description=f"Suggested description",
                            required=param_def.get("required", False),
                            type="string"
                        ))
            
            elif parameter_name in ["path", "path_or_name"]:
                patterns = self.parameter_patterns.get("common_paths", [])
                for pattern in patterns:
                    if not current_value or pattern.startswith(current_value):
                        suggestions.append(ParameterSuggestion(
                            name=parameter_name,
                            value=pattern,
                            description=f"Common path",
                            required=param_def.get("required", False),
                            type="string"
                        ))
        
        return suggestions[:5]  # Limit to 5 parameter suggestions
    
    def validate_command_input(self, command: str, current_state: str = None) -> Dict[str, Any]:
        """
        Validate command input and provide helpful error messages.
        
        Args:
            command: Full command string
            current_state: Current workflow state
            
        Returns:
            Validation result with errors and suggestions
        """
        if current_state is None:
            current_state = self.state_machine.current_state.value
        
        # Parse command
        parts = command.strip().split()
        if not parts or not parts[0].startswith('/'):
            return {
                "valid": False,
                "error": "Commands must start with '/'",
                "suggestions": ["/help", "/state", "/epic"],
                "hint": "Type '/' to see available commands"
            }
        
        base_command = parts[0]
        
        # Check if command exists
        if base_command not in self.command_patterns:
            similar_commands = self._find_similar_commands(base_command)
            return {
                "valid": False,
                "error": f"Unknown command: {base_command}",
                "suggestions": similar_commands,
                "hint": f"Did you mean: {', '.join(similar_commands[:3])}?"
            }
        
        command_pattern = self.command_patterns[base_command]
        
        # Check if command is valid in current state
        valid_states = command_pattern.get("valid_states", [])
        if current_state not in valid_states:
            return {
                "valid": False,
                "error": f"Command {base_command} not available in state {current_state}",
                "suggestions": self._get_valid_commands_for_state(current_state),
                "hint": f"Valid states for this command: {', '.join(valid_states)}"
            }
        
        # Validate parameters
        param_validation = self._validate_parameters(base_command, parts[1:], command_pattern)
        
        return {
            "valid": param_validation["valid"],
            "error": param_validation.get("error"),
            "suggestions": param_validation.get("suggestions", []),
            "hint": param_validation.get("hint"),
            "command_info": command_pattern
        }
    
    def track_user_command(self, user_id: str, command: str, success: bool, timestamp: str = None):
        """Track user command patterns for personalization"""
        if timestamp is None:
            timestamp = datetime.now().isoformat()
        
        if user_id not in self.user_patterns:
            self.user_patterns[user_id] = {
                "commands": [],
                "favorites": {},
                "success_rate": {},
                "last_activity": timestamp
            }
        
        user_data = self.user_patterns[user_id]
        
        # Add to command history
        user_data["commands"].append({
            "command": command,
            "success": success,
            "timestamp": timestamp
        })
        
        # Keep only last 50 commands
        if len(user_data["commands"]) > 50:
            user_data["commands"].pop(0)
        
        # Update favorites (frequency)
        base_command = command.split()[0]
        user_data["favorites"][base_command] = user_data["favorites"].get(base_command, 0) + 1
        
        # Update success rate
        if base_command not in user_data["success_rate"]:
            user_data["success_rate"][base_command] = {"total": 0, "success": 0}
        
        user_data["success_rate"][base_command]["total"] += 1
        if success:
            user_data["success_rate"][base_command]["success"] += 1
        
        user_data["last_activity"] = timestamp
        
        # Add to recent commands for global context
        self.recent_commands.append({
            "user_id": user_id,
            "command": command,
            "success": success,
            "timestamp": timestamp
        })
        
        # Keep only last 100 recent commands
        if len(self.recent_commands) > 100:
            self.recent_commands.pop(0)
    
    def get_error_prevention_hints(self, partial_command: str, current_state: str = None) -> List[str]:
        """Get hints to prevent common errors"""
        if current_state is None:
            current_state = self.state_machine.current_state.value
        
        hints = []
        
        # State-specific hints
        if current_state == "IDLE":
            hints.append("💡 Start with /epic to define your first initiative")
            if "/sprint" in partial_command:
                hints.append("⚠️ Create an epic before planning sprints")
        
        elif current_state == "BACKLOG_READY":
            hints.append("💡 Use /approve to approve stories, then /sprint plan")
            if "/epic" in partial_command:
                hints.append("ℹ️ You can add more epics or proceed with sprint planning")
        
        elif current_state == "SPRINT_ACTIVE":
            hints.append("💡 Use /sprint status to check progress")
            if "/epic" in partial_command:
                hints.append("⚠️ Pause the sprint before creating new epics")
        
        # Command-specific hints
        if '"/epic' in partial_command and '"' not in partial_command[partial_command.index('"/epic')+5:]:
            hints.append("⚠️ Epic description needs closing quotes")
        
        if "/sprint" in partial_command and len(partial_command.split()) == 1:
            hints.append("💡 Sprint needs an action: plan, start, status, pause, resume")
        
        return hints[:3]  # Return top 3 hints
    
    # =====================================================
    # Helper Methods
    # =====================================================
    
    def _parse_partial_input(self, partial_input: str) -> Dict[str, Any]:
        """Parse partial input to understand context"""
        if not partial_input.strip():
            return {"type": "empty", "command": None, "parameters": []}
        
        parts = partial_input.strip().split()
        
        if not parts[0].startswith('/'):
            return {"type": "invalid", "command": None, "parameters": []}
        
        if len(parts) == 1:
            return {"type": "command", "command": parts[0], "parameters": []}
        
        return {"type": "parameter", "command": parts[0], "parameters": parts[1:]}
    
    def _get_command_completions(self, partial_command: str, current_state: str, user_id: str) -> List[CommandSuggestion]:
        """Get command completions for partial command input"""
        suggestions = []
        
        for command, pattern in self.command_patterns.items():
            if command.startswith(partial_command):
                # Check if command is valid in current state
                valid_states = pattern.get("valid_states", [])
                available = current_state in valid_states
                
                suggestion = CommandSuggestion(
                    command=command,
                    description=pattern["description"],
                    usage=pattern["usage"],
                    examples=pattern["examples"],
                    priority=self._calculate_command_priority(command, current_state, user_id),
                    available=available,
                    reason=self._get_suggestion_reason(command, current_state, available),
                    parameters=[],
                    shortcuts=pattern.get("shortcuts", [])
                )
                suggestions.append(suggestion)
        
        return suggestions
    
    def _get_parameter_suggestions(self, command: str, current_params: List[str], current_state: str) -> List[CommandSuggestion]:
        """Get suggestions for command parameters"""
        # This would return suggestions for completing the current command
        # For now, return empty list as parameters are handled separately
        return []
    
    def _get_all_available_commands(self, current_state: str, user_id: str) -> List[CommandSuggestion]:
        """Get all commands available in current state"""
        suggestions = []
        
        for command, pattern in self.command_patterns.items():
            valid_states = pattern.get("valid_states", [])
            available = current_state in valid_states
            
            suggestion = CommandSuggestion(
                command=command,
                description=pattern["description"],
                usage=pattern["usage"],
                examples=pattern["examples"],
                priority=self._calculate_command_priority(command, current_state, user_id),
                available=available,
                reason=self._get_suggestion_reason(command, current_state, available),
                parameters=[],
                shortcuts=pattern.get("shortcuts", [])
            )
            suggestions.append(suggestion)
        
        return suggestions
    
    def _apply_contextual_ranking(self, suggestions: List[CommandSuggestion], current_state: str, user_id: str) -> List[CommandSuggestion]:
        """Apply contextual ranking to suggestions"""
        for suggestion in suggestions:
            # Boost priority for highly relevant commands
            if current_state == "IDLE" and suggestion.command == "/epic":
                suggestion.priority += 5
            elif current_state == "BACKLOG_READY" and suggestion.command in ["/approve", "/sprint"]:
                suggestion.priority += 3
            elif current_state == "SPRINT_ACTIVE" and suggestion.command == "/sprint":
                suggestion.priority += 4
            
            # Reduce priority for unavailable commands
            if not suggestion.available:
                suggestion.priority -= 10
        
        return suggestions
    
    def _apply_user_personalization(self, suggestions: List[CommandSuggestion], user_id: str) -> List[CommandSuggestion]:
        """Apply user-specific personalization"""
        if user_id not in self.user_patterns:
            return suggestions
        
        user_data = self.user_patterns[user_id]
        favorites = user_data.get("favorites", {})
        success_rates = user_data.get("success_rate", {})
        
        for suggestion in suggestions:
            command = suggestion.command
            
            # Boost frequently used commands
            frequency = favorites.get(command, 0)
            suggestion.priority += min(frequency * 0.5, 3)  # Max boost of 3
            
            # Boost commands with high success rate
            if command in success_rates:
                rate = success_rates[command]["success"] / max(success_rates[command]["total"], 1)
                suggestion.priority += rate * 2  # Max boost of 2
        
        return suggestions
    
    def _calculate_command_priority(self, command: str, current_state: str, user_id: str) -> int:
        """Calculate base priority for a command"""
        # Base priorities by category
        category_priorities = {
            "planning": 6,
            "execution": 8,
            "approval": 7,
            "information": 4,
            "setup": 3,
            "review": 5
        }
        
        pattern = self.command_patterns.get(command, {})
        category = pattern.get("category", "information")
        
        return category_priorities.get(category, 4)
    
    def _get_suggestion_reason(self, command: str, current_state: str, available: bool) -> str:
        """Get reason why command is suggested"""
        if not available:
            return f"Not available in {current_state} state"
        
        if current_state == "IDLE" and command == "/epic":
            return "Start by defining your first epic"
        elif current_state == "BACKLOG_READY" and command == "/approve":
            return "Approve stories to proceed with sprint planning"
        elif current_state == "SPRINT_ACTIVE" and command == "/sprint":
            return "Manage your active sprint"
        else:
            return "Available command"
    
    def _find_similar_commands(self, partial_command: str) -> List[str]:
        """Find commands similar to the partial input"""
        similar = []
        
        for command in self.command_patterns.keys():
            # Check if command contains the partial input
            if partial_command.lower() in command.lower():
                similar.append(command)
            # Check shortcuts
            pattern = self.command_patterns[command]
            for shortcut in pattern.get("shortcuts", []):
                if partial_command.lower() in shortcut.lower():
                    similar.append(command)
                    break
        
        return list(set(similar))  # Remove duplicates
    
    def _get_valid_commands_for_state(self, current_state: str) -> List[str]:
        """Get all valid commands for a specific state"""
        valid_commands = []
        
        for command, pattern in self.command_patterns.items():
            if current_state in pattern.get("valid_states", []):
                valid_commands.append(command)
        
        return valid_commands
    
    def _validate_parameters(self, command: str, params: List[str], pattern: Dict[str, Any]) -> Dict[str, Any]:
        """Validate command parameters"""
        expected_params = pattern.get("parameters", [])
        
        # For now, basic validation - can be expanded
        required_params = [p for p in expected_params if p.get("required", False)]
        
        if len(required_params) > len(params):
            missing = len(required_params) - len(params)
            return {
                "valid": False,
                "error": f"Missing {missing} required parameter(s)",
                "hint": f"Usage: {pattern['usage']}",
                "suggestions": [pattern['usage']]
            }
        
        return {"valid": True}


# Global suggestions engine instance
_suggestions_engine = None

def get_suggestions_engine(state_machine: Optional[StateMachine] = None) -> CommandSuggestionsEngine:
    """Get global suggestions engine instance"""
    global _suggestions_engine
    if _suggestions_engine is None:
        _suggestions_engine = CommandSuggestionsEngine(state_machine)
    return _suggestions_engine


# Convenience functions
def get_command_suggestions(partial_input: str = "", current_state: str = None, 
                          user_id: str = "default", project_name: str = "default",
                          limit: int = 10) -> List[Dict[str, Any]]:
    """Convenience function to get command suggestions"""
    engine = get_suggestions_engine()
    suggestions = engine.get_command_suggestions(partial_input, current_state, user_id, project_name, limit)
    
    # Convert to dictionaries for JSON serialization
    return [
        {
            "command": s.command,
            "description": s.description,
            "usage": s.usage,
            "examples": s.examples,
            "priority": s.priority,
            "available": s.available,
            "reason": s.reason,
            "shortcuts": s.shortcuts
        }
        for s in suggestions
    ]


def validate_command_input(command: str, current_state: str = None) -> Dict[str, Any]:
    """Convenience function to validate command input"""
    engine = get_suggestions_engine()
    return engine.validate_command_input(command, current_state)


def get_error_prevention_hints(partial_command: str, current_state: str = None) -> List[str]:
    """Convenience function to get error prevention hints"""
    engine = get_suggestions_engine()
    return engine.get_error_prevention_hints(partial_command, current_state)


def track_user_command(user_id: str, command: str, success: bool, timestamp: str = None):
    """Convenience function to track user command patterns"""
    engine = get_suggestions_engine()
    engine.track_user_command(user_id, command, success, timestamp)