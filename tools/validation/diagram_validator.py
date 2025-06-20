#!/usr/bin/env python3
"""
Mermaid Diagram Validation System

Validates Mermaid diagrams for syntax correctness, theme consistency,
and state machine alignment to prevent documentation inconsistencies.

Usage:
    python tools/validation/diagram_validator.py [--fix] [--verbose]
    
Features:
- Syntax validation for common Mermaid diagram types
- Theme consistency checking (dark theme enforcement)
- State machine diagram validation against source code
- Basic diagram structure validation
- Optional auto-fixing of common issues
"""

import re
import os
import sys
import argparse
import json
from pathlib import Path
from typing import List, Dict, Set, Tuple, Optional
from dataclasses import dataclass
from enum import Enum


class ValidationLevel(Enum):
    ERROR = "ERROR"
    WARNING = "WARNING" 
    INFO = "INFO"


@dataclass
class ValidationIssue:
    level: ValidationLevel
    file_path: str
    line_number: int
    issue_type: str
    message: str
    suggestion: Optional[str] = None


class MermaidDiagramValidator:
    """Validates Mermaid diagrams for syntax, theme, and content consistency."""
    
    # Known state machine states from lib/state_machine.py
    VALID_STATES = {
        "IDLE", "BACKLOG_READY", "SPRINT_PLANNED", "SPRINT_ACTIVE", 
        "SPRINT_PAUSED", "SPRINT_REVIEW", "BLOCKED"
    }
    
    # Valid commands from state machine
    VALID_COMMANDS = {
        "/epic", "/approve", "/sprint plan", "/sprint start", "/sprint status",
        "/sprint pause", "/sprint resume", "/request_changes", "/suggest_fix",
        "/skip_task", "/feedback"
    }
    
    # Required Mermaid theme configuration
    REQUIRED_THEME = "dark"
    
    def __init__(self, docs_path: str = "docs_src", verbose: bool = False):
        self.docs_path = Path(docs_path)
        self.verbose = verbose
        self.issues: List[ValidationIssue] = []
        
    def validate_all_diagrams(self) -> List[ValidationIssue]:
        """Validate all Mermaid diagrams in the documentation."""
        self.issues.clear()
        
        # Find all markdown files with Mermaid diagrams
        diagram_files = self._find_diagram_files()
        
        if self.verbose:
            print(f"Found {len(diagram_files)} files with Mermaid diagrams")
            
        for file_path in diagram_files:
            self._validate_file_diagrams(file_path)
            
        return self.issues
    
    def _find_diagram_files(self) -> List[Path]:
        """Find all markdown files containing Mermaid diagrams."""
        diagram_files = []
        
        for md_file in self.docs_path.rglob("*.md"):
            try:
                content = md_file.read_text(encoding='utf-8')
                if "```mermaid" in content:
                    diagram_files.append(md_file)
            except Exception as e:
                self._add_issue(
                    ValidationLevel.WARNING,
                    str(md_file), 
                    0,
                    "file_read_error",
                    f"Could not read file: {e}"
                )
        
        return diagram_files
    
    def _validate_file_diagrams(self, file_path: Path) -> None:
        """Validate all Mermaid diagrams in a single file."""
        try:
            content = file_path.read_text(encoding='utf-8')
            lines = content.split('\n')
            
            # Find all Mermaid code blocks
            in_mermaid = False
            mermaid_start_line = 0
            current_diagram = []
            
            for line_num, line in enumerate(lines, 1):
                if line.strip().startswith("```mermaid"):
                    in_mermaid = True
                    mermaid_start_line = line_num
                    current_diagram = [line]
                elif in_mermaid and line.strip() == "```":
                    current_diagram.append(line)
                    # Validate this diagram
                    self._validate_diagram_block(
                        file_path, 
                        mermaid_start_line,
                        current_diagram
                    )
                    in_mermaid = False
                    current_diagram = []
                elif in_mermaid:
                    current_diagram.append(line)
                    
        except Exception as e:
            self._add_issue(
                ValidationLevel.ERROR,
                str(file_path),
                0, 
                "file_processing_error",
                f"Error processing file: {e}"
            )
    
    def _validate_diagram_block(self, file_path: Path, start_line: int, diagram_lines: List[str]) -> None:
        """Validate a single Mermaid diagram block."""
        diagram_content = '\n'.join(diagram_lines)
        
        # Basic syntax validation
        self._validate_basic_syntax(file_path, start_line, diagram_content)
        
        # Theme validation
        self._validate_theme(file_path, start_line, diagram_content)
        
        # Diagram type specific validation
        self._validate_diagram_type(file_path, start_line, diagram_content)
        
        # State machine specific validation
        if "stateDiagram" in diagram_content:
            self._validate_state_diagram(file_path, start_line, diagram_content)
    
    def _validate_basic_syntax(self, file_path: Path, start_line: int, content: str) -> None:
        """Validate basic Mermaid syntax patterns."""
        # Check for common syntax errors
        
        # Missing diagram type declaration
        lines = content.strip().split('\n')[1:-1]  # Remove ```mermaid and ```
        non_empty_lines = [line for line in lines if line.strip() and not line.strip().startswith('%%')]
        
        if not non_empty_lines:
            self._add_issue(
                ValidationLevel.ERROR,
                str(file_path),
                start_line,
                "empty_diagram",
                "Mermaid diagram block is empty"
            )
            return
            
        first_content_line = non_empty_lines[0].strip()
        
        # Check for valid diagram type
        valid_diagram_types = [
            "stateDiagram", "flowchart", "graph", "sequenceDiagram", 
            "classDiagram", "erDiagram", "journey", "gantt"
        ]
        
        if not any(first_content_line.startswith(dt) for dt in valid_diagram_types):
            self._add_issue(
                ValidationLevel.WARNING,
                str(file_path),
                start_line + 1,
                "missing_diagram_type",
                f"No clear diagram type found. Line: '{first_content_line}'",
                "Add diagram type like 'stateDiagram-v2' or 'flowchart TD'"
            )
        
        # Check for unmatched brackets
        bracket_count = content.count('[') - content.count(']')
        if bracket_count != 0:
            self._add_issue(
                ValidationLevel.ERROR,
                str(file_path),
                start_line,
                "unmatched_brackets",
                f"Unmatched brackets: {abs(bracket_count)} {'extra [' if bracket_count > 0 else 'missing ]'}"
            )
        
        # Check for unmatched parentheses
        paren_count = content.count('(') - content.count(')')
        if paren_count != 0:
            self._add_issue(
                ValidationLevel.ERROR,
                str(file_path),
                start_line,
                "unmatched_parentheses", 
                f"Unmatched parentheses: {abs(paren_count)} {'extra (' if paren_count > 0 else 'missing )'}"
            )
    
    def _validate_theme(self, file_path: Path, start_line: int, content: str) -> None:
        """Validate Mermaid theme configuration."""
        # Check for theme initialization
        theme_pattern = r"%%\{init:\s*\{[^}]*'theme':\s*'([^']+)'[^}]*\}\}%%"
        theme_match = re.search(theme_pattern, content)
        
        if not theme_match:
            self._add_issue(
                ValidationLevel.WARNING,
                str(file_path),
                start_line + 1,
                "missing_theme",
                "No theme configuration found",
                f"Add: %%{{init: {{'theme': '{self.REQUIRED_THEME}'}}}}%%"
            )
        else:
            theme = theme_match.group(1)
            if theme != self.REQUIRED_THEME:
                self._add_issue(
                    ValidationLevel.ERROR,
                    str(file_path),
                    start_line + 1,
                    "incorrect_theme",
                    f"Theme '{theme}' should be '{self.REQUIRED_THEME}'",
                    f"Change to: %%{{init: {{'theme': '{self.REQUIRED_THEME}'}}}}%%"
                )
    
    def _validate_diagram_type(self, file_path: Path, start_line: int, content: str) -> None:
        """Validate diagram type specific patterns."""
        if "stateDiagram" in content:
            # Prefer stateDiagram-v2 for better syntax
            if "stateDiagram-v2" not in content:
                self._add_issue(
                    ValidationLevel.INFO,
                    str(file_path),
                    start_line,
                    "old_state_diagram_syntax",
                    "Consider using 'stateDiagram-v2' for better syntax support"
                )
        
        # Check for flowchart direction
        if "flowchart" in content:
            if not re.search(r"flowchart\s+(TD|TB|BT|RL|LR)", content):
                self._add_issue(
                    ValidationLevel.WARNING,
                    str(file_path),
                    start_line,
                    "missing_flowchart_direction",
                    "Flowchart missing direction (TD, TB, BT, RL, LR)",
                    "Add direction like: flowchart TD"
                )
    
    def _validate_state_diagram(self, file_path: Path, start_line: int, content: str) -> None:
        """Validate state diagram against known state machine."""
        # Extract states mentioned in the diagram
        mentioned_states = set()
        
        # Find state names in transitions (e.g., "IDLE --> BACKLOG_READY")
        transition_pattern = r"(\w+)\s*-->\s*(\w+)"
        for match in re.finditer(transition_pattern, content):
            mentioned_states.add(match.group(1))
            mentioned_states.add(match.group(2))
        
        # Find states in standalone definitions
        state_definition_pattern = r"^\s*(\w+)\s*:"
        for line in content.split('\n'):
            match = re.match(state_definition_pattern, line.strip())
            if match:
                mentioned_states.add(match.group(1))
        
        # Remove special Mermaid keywords
        mentioned_states.discard("[*]")  # Start/end state
        mentioned_states.discard("note")
        
        # Check for unknown states
        unknown_states = mentioned_states - self.VALID_STATES
        if unknown_states:
            self._add_issue(
                ValidationLevel.WARNING,
                str(file_path),
                start_line,
                "unknown_states",
                f"Unknown states found: {', '.join(sorted(unknown_states))}",
                f"Valid states: {', '.join(sorted(self.VALID_STATES))}"
            )
        
        # Check for missing critical states in primary workflow diagrams
        if "IDLE" in mentioned_states and len(mentioned_states & self.VALID_STATES) > 3:
            # This looks like a primary workflow diagram
            critical_states = {"IDLE", "BACKLOG_READY", "SPRINT_ACTIVE", "SPRINT_REVIEW"}
            missing_critical = critical_states - mentioned_states
            if missing_critical:
                self._add_issue(
                    ValidationLevel.INFO,
                    str(file_path),
                    start_line,
                    "missing_critical_states",
                    f"Primary workflow diagram missing states: {', '.join(sorted(missing_critical))}"
                )
        
        # Validate command references in transitions
        command_pattern = r":\s*([/]\w+[^:\n]*)"
        for match in re.finditer(command_pattern, content):
            command = match.group(1).strip()
            # Extract base command (e.g., "/sprint start" from "/sprint start (conditions)")
            base_command = re.match(r"(/\w+(?:\s+\w+)?)", command)
            if base_command:
                cmd = base_command.group(1)
                if cmd not in self.VALID_COMMANDS:
                    self._add_issue(
                        ValidationLevel.INFO,
                        str(file_path),
                        start_line,
                        "unrecognized_command",
                        f"Command '{cmd}' not in recognized command list",
                        f"Valid commands: {', '.join(sorted(self.VALID_COMMANDS))}"
                    )
    
    def _add_issue(self, level: ValidationLevel, file_path: str, line_number: int,
                  issue_type: str, message: str, suggestion: str = None) -> None:
        """Add a validation issue to the results."""
        self.issues.append(ValidationIssue(
            level=level,
            file_path=file_path,
            line_number=line_number,
            issue_type=issue_type,
            message=message,
            suggestion=suggestion
        ))
    
    def fix_common_issues(self) -> int:
        """Auto-fix common diagram issues where possible."""
        fixes_applied = 0
        
        # Group issues by file for efficient processing
        issues_by_file = {}
        for issue in self.issues:
            if issue.file_path not in issues_by_file:
                issues_by_file[issue.file_path] = []
            issues_by_file[issue.file_path].append(issue)
        
        for file_path, file_issues in issues_by_file.items():
            if self._fix_file_issues(file_path, file_issues):
                fixes_applied += 1
        
        return fixes_applied
    
    def _fix_file_issues(self, file_path: str, issues: List[ValidationIssue]) -> bool:
        """Fix issues in a single file."""
        try:
            path_obj = Path(file_path)
            content = path_obj.read_text(encoding='utf-8')
            original_content = content
            
            # Fix missing theme configurations
            for issue in issues:
                if issue.issue_type == "missing_theme" and issue.suggestion:
                    # Find the mermaid block and add theme
                    lines = content.split('\n')
                    for i, line in enumerate(lines):
                        if line.strip().startswith("```mermaid"):
                            # Insert theme on next line if not already there
                            if i + 1 < len(lines) and "%%{init:" not in lines[i + 1]:
                                lines.insert(i + 1, "%%{init: {'theme': 'dark'}}%%")
                                content = '\n'.join(lines)
                                break
                
                # Fix incorrect themes
                elif issue.issue_type == "incorrect_theme":
                    theme_pattern = r"%%\{init:\s*\{[^}]*'theme':\s*'[^']+'"
                    content = re.sub(
                        theme_pattern,
                        f"%%{{init: {{'theme': '{self.REQUIRED_THEME}'",
                        content
                    )
            
            # Write back if changes were made
            if content != original_content:
                path_obj.write_text(content, encoding='utf-8')
                if self.verbose:
                    print(f"Fixed issues in: {file_path}")
                return True
                
        except Exception as e:
            print(f"Error fixing file {file_path}: {e}")
        
        return False
    
    def generate_report(self) -> str:
        """Generate a detailed validation report."""
        if not self.issues:
            return "✅ All Mermaid diagrams validated successfully - no issues found!"
        
        # Group issues by level
        errors = [i for i in self.issues if i.level == ValidationLevel.ERROR]
        warnings = [i for i in self.issues if i.level == ValidationLevel.WARNING]
        info = [i for i in self.issues if i.level == ValidationLevel.INFO]
        
        report = []
        report.append("# Mermaid Diagram Validation Report")
        report.append("")
        report.append(f"**Summary:** {len(errors)} errors, {len(warnings)} warnings, {len(info)} info")
        report.append("")
        
        # Report errors first
        if errors:
            report.append("## ❌ Errors (Must Fix)")
            report.append("")
            for issue in errors:
                report.append(f"**{Path(issue.file_path).name}:{issue.line_number}** - {issue.message}")
                if issue.suggestion:
                    report.append(f"  💡 *Suggestion: {issue.suggestion}*")
                report.append("")
        
        # Then warnings
        if warnings:
            report.append("## ⚠️ Warnings (Should Fix)")
            report.append("")
            for issue in warnings:
                report.append(f"**{Path(issue.file_path).name}:{issue.line_number}** - {issue.message}")
                if issue.suggestion:
                    report.append(f"  💡 *Suggestion: {issue.suggestion}*")
                report.append("")
        
        # Finally info items
        if info:
            report.append("## ℹ️ Information (Optional)")
            report.append("")
            for issue in info:
                report.append(f"**{Path(issue.file_path).name}:{issue.line_number}** - {issue.message}")
                if issue.suggestion:
                    report.append(f"  💡 *Suggestion: {issue.suggestion}*")
                report.append("")
        
        return '\n'.join(report)


def main():
    """Main entry point for the diagram validator."""
    parser = argparse.ArgumentParser(
        description="Validate Mermaid diagrams for syntax, theme, and content consistency"
    )
    parser.add_argument(
        "--docs-path", 
        default="docs_src",
        help="Path to documentation directory (default: docs_src)"
    )
    parser.add_argument(
        "--fix",
        action="store_true",
        help="Automatically fix common issues where possible"
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose output"
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output results in JSON format"
    )
    parser.add_argument(
        "--exit-code",
        action="store_true",
        help="Exit with error code if issues found (useful for CI)"
    )
    
    args = parser.parse_args()
    
    # Validate arguments
    docs_path = Path(args.docs_path)
    if not docs_path.exists():
        print(f"Error: Documentation path '{docs_path}' does not exist")
        sys.exit(1)
    
    # Run validation
    validator = MermaidDiagramValidator(str(docs_path), args.verbose)
    issues = validator.validate_all_diagrams()
    
    # Apply fixes if requested
    if args.fix and issues:
        fixes_applied = validator.fix_common_issues()
        if args.verbose:
            print(f"Applied fixes to {fixes_applied} files")
        
        # Re-validate after fixes
        validator.issues.clear()
        issues = validator.validate_all_diagrams()
    
    # Output results
    if args.json:
        result = {
            "summary": {
                "total_issues": len(issues),
                "errors": len([i for i in issues if i.level == ValidationLevel.ERROR]),
                "warnings": len([i for i in issues if i.level == ValidationLevel.WARNING]),
                "info": len([i for i in issues if i.level == ValidationLevel.INFO])
            },
            "issues": [
                {
                    "level": issue.level.value,
                    "file": issue.file_path,
                    "line": issue.line_number,
                    "type": issue.issue_type,
                    "message": issue.message,
                    "suggestion": issue.suggestion
                }
                for issue in issues
            ]
        }
        print(json.dumps(result, indent=2))
    else:
        print(validator.generate_report())
    
    # Exit with appropriate code
    if args.exit_code:
        error_count = len([i for i in issues if i.level == ValidationLevel.ERROR])
        sys.exit(error_count)


if __name__ == "__main__":
    main()