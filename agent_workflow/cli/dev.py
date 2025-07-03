#!/usr/bin/env python3
"""
Development and utility commands for agent-workflow.

This module provides development tools integrated from the tools/ directory,
including coverage analysis, compliance tracking, and API documentation generation.
"""

import ast
import click
import json
import os
import subprocess
import sys
import xml.etree.ElementTree as ET
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass, field

# Add package root to path for development
package_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(package_root))

from agent_workflow.cli.utils import (
    print_info, 
    print_success, 
    print_warning, 
    print_error
)

# Initialize rich console for better output
from rich.console import Console
console = Console()


# ============================================================================
# Coverage Analysis (from tools/coverage/analyze_coverage.py)
# ============================================================================

def find_lib_files():
    """Find all Python files in the lib directory."""
    lib_files = []
    lib_path = Path("lib")
    if lib_path.exists():
        for root, dirs, files in os.walk('lib'):
            for file in files:
                if file.endswith('.py') and not file.startswith('__'):
                    lib_files.append(os.path.join(root, file))
    return sorted(lib_files)


def find_test_files():
    """Find all test files and extract what they're testing."""
    test_files = []
    for root, dirs, files in os.walk('tests'):
        for file in files:
            if file.startswith('test_') and file.endswith('.py'):
                test_files.append(os.path.join(root, file))
    return sorted(test_files)


def analyze_test_coverage():
    """Analyze which lib files have corresponding tests."""
    lib_files = find_lib_files()
    test_files = find_test_files()
    
    # Extract module names from test files
    tested_modules = set()
    for test_file in test_files:
        # Extract module name from test file
        basename = os.path.basename(test_file)
        if basename.startswith('test_'):
            module_name = basename[5:-3]  # Remove 'test_' prefix and '.py' suffix
            tested_modules.add(module_name)
    
    console.print("=== COVERAGE ANALYSIS ===\n", style="bold cyan")
    
    console.print("📁 LIB FILES FOUND:", style="bold")
    covered_files = []
    uncovered_files = []
    
    for lib_file in lib_files:
        # Extract module name from lib file
        relative_path = lib_file.replace('lib/', '').replace('/', '_')
        module_name = os.path.basename(lib_file)[:-3]  # Remove .py
        
        # Check if there's a test for this module
        has_test = False
        for tested in tested_modules:
            if tested == module_name or module_name in tested or tested in module_name:
                has_test = True
                break
        
        if has_test:
            covered_files.append(lib_file)
            console.print(f"✅ {lib_file}", style="green")
        else:
            uncovered_files.append(lib_file)
            console.print(f"❌ {lib_file}", style="red")
    
    console.print(f"\n📊 SUMMARY:", style="bold")
    console.print(f"Total lib files: {len(lib_files)}")
    console.print(f"Files with tests: {len(covered_files)} ({len(covered_files)/len(lib_files)*100:.1f}%)", 
                  style="green" if len(covered_files)/len(lib_files) > 0.8 else "yellow")
    console.print(f"Files without tests: {len(uncovered_files)} ({len(uncovered_files)/len(lib_files)*100:.1f}%)",
                  style="red" if len(uncovered_files) > 0 else "green")
    
    if uncovered_files:
        console.print(f"\n🎯 FILES NEEDING TESTS:", style="bold yellow")
        for file in uncovered_files:
            console.print(f"   - {file}")
    
    console.print(f"\n🧪 TEST FILES FOUND:", style="bold")
    for test_file in test_files:
        console.print(f"   - {test_file}")


# ============================================================================
# Compliance Tracking (from tools/compliance/audit_compliance_tracker.py)
# ============================================================================

class ComplianceTracker:
    """Lightweight compliance tracking system for government audit requirements."""
    
    def __init__(self):
        self.target_coverage = 95.0
        self.current_tier = 3
        self.modules = self._discover_modules()
        
    def _discover_modules(self):
        """Discover all Python modules in lib directory."""
        lib_path = Path("lib")
        modules = []
        
        if not lib_path.exists():
            console.print("⚠️  lib directory not found, checking agent_workflow package...", style="yellow")
            # Check agent_workflow package instead
            aw_path = Path("agent_workflow")
            if aw_path.exists():
                for py_file in aw_path.rglob("*.py"):
                    if py_file.name != "__init__.py" and "test" not in py_file.parts:
                        modules.append(str(py_file))
            return sorted(modules)
        
        # Main lib modules
        for py_file in lib_path.glob("*.py"):
            if py_file.name != "__init__.py":
                modules.append(str(py_file))
        
        # Submodules
        for subdir in lib_path.glob("*/"):
            if subdir.is_dir():
                for py_file in subdir.glob("*.py"):
                    if py_file.name != "__init__.py":
                        modules.append(str(py_file))
        
        return sorted(modules)
    
    def _run_coverage_quick(self):
        """Run coverage analysis with minimal disk usage."""
        # First, try to use existing coverage data
        if os.path.exists("coverage.xml"):
            console.print("📊 Using existing coverage.xml data...", style="blue")
            return self._parse_coverage_xml()
        
        try:
            # Run coverage with minimal output
            cmd = [
                "python3", "-m", "pytest", 
                "--cov=lib", 
                "--cov-report=json:coverage_temp.json",
                "--tb=no", "-q",  # No traceback, quiet mode
                "tests/unit/",  # Test unit files
                "--maxfail=1"  # Stop after first failure
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            
            if os.path.exists("coverage_temp.json"):
                with open("coverage_temp.json", "r") as f:
                    coverage_data = json.load(f)
                # Clean up immediately
                os.remove("coverage_temp.json")
                return coverage_data
            
            return None
            
        except subprocess.TimeoutExpired:
            console.print("❌ Coverage analysis timed out", style="red")
            return None
        except Exception as e:
            console.print(f"❌ Coverage analysis failed: {e}", style="red")
            return None
    
    def _parse_coverage_xml(self):
        """Parse existing coverage.xml file for quick analysis."""
        try:
            tree = ET.parse("coverage.xml")
            root = tree.getroot()
            
            # Extract coverage data from XML
            coverage_data = {"files": {}}
            
            # Parse each class (file) in the coverage report
            for class_elem in root.findall(".//class"):
                filename = class_elem.get("filename")
                if filename:
                    # Add lib/ prefix to match expected format
                    full_path = f"lib/{filename}"
                    
                    lines = class_elem.findall("lines/line")
                    total_lines = len(lines)
                    covered_lines = len([line for line in lines if int(line.get("hits", "0")) > 0])
                    
                    coverage_data["files"][full_path] = {
                        "num_statements": total_lines,
                        "missing_lines": total_lines - covered_lines,
                        "covered_lines": covered_lines
                    }
            
            # Calculate overall coverage from root attributes
            root_line_rate = float(root.get("line-rate", "0"))
            overall_pct = root_line_rate * 100
            
            coverage_data["totals"] = {
                "percent_covered": overall_pct,
                "num_statements": int(root.get("lines-valid", "0")),
                "covered_lines": int(root.get("lines-covered", "0"))
            }
            
            return coverage_data
            
        except Exception as e:
            console.print(f"❌ Failed to parse coverage.xml: {e}", style="red")
            return None
    
    def _calculate_module_coverage(self, coverage_data):
        """Calculate coverage for each module."""
        if not coverage_data or "files" not in coverage_data:
            return {}
        
        module_coverage = {}
        files_data = coverage_data["files"]
        
        for module_path in self.modules:
            # Normalize path for comparison
            normalized_path = module_path.replace("\\", "/")
            
            if normalized_path in files_data:
                file_data = files_data[normalized_path]
                total_lines = file_data.get("num_statements", 0)
                covered_lines = total_lines - file_data.get("missing_lines", 0)
                
                if total_lines > 0:
                    coverage_pct = (covered_lines / total_lines) * 100
                else:
                    coverage_pct = 100.0
                
                module_coverage[module_path] = {
                    "coverage": round(coverage_pct, 1),
                    "total_lines": total_lines,
                    "covered_lines": covered_lines,
                    "missing_lines": file_data.get("missing_lines", 0),
                    "gap_to_target": max(0, round(self.target_coverage - coverage_pct, 1))
                }
        
        return module_coverage
    
    def _prioritize_modules(self, module_coverage):
        """Prioritize modules based on coverage gaps and effort."""
        priority_list = []
        
        for module_path, data in module_coverage.items():
            gap = data["gap_to_target"]
            missing_lines = data["missing_lines"]
            
            # Calculate priority score (higher = more urgent)
            if gap > 0:
                # Weight by gap size and effort required
                effort_factor = min(missing_lines / 10, 5.0)  # Cap effort factor
                priority_score = gap * (1 + effort_factor)
                
                priority_list.append({
                    "module": module_path,
                    "coverage": data["coverage"],
                    "gap": gap,
                    "missing_lines": missing_lines,
                    "priority_score": round(priority_score, 1),
                    "effort": "LOW" if missing_lines <= 5 else "MED" if missing_lines <= 15 else "HIGH"
                })
        
        # Sort by priority score (highest first)
        priority_list.sort(key=lambda x: x["priority_score"], reverse=True)
        return priority_list
    
    def _estimate_completion_effort(self, priority_list):
        """Estimate total effort to reach compliance."""
        total_missing_lines = sum(item["missing_lines"] for item in priority_list)
        
        # Estimate effort categories
        quick_wins = len([item for item in priority_list if item["effort"] == "LOW"])
        medium_effort = len([item for item in priority_list if item["effort"] == "MED"])
        major_effort = len([item for item in priority_list if item["effort"] == "HIGH"])
        
        return {
            "total_modules_needing_work": len(priority_list),
            "total_missing_lines": total_missing_lines,
            "quick_wins": quick_wins,
            "medium_effort": medium_effort,
            "major_effort": major_effort,
            "estimated_hours": round(total_missing_lines * 0.5, 1)  # 0.5 hours per missing line
        }
    
    def generate_dashboard(self):
        """Generate compliance dashboard."""
        console.print("\n" + "="*80, style="bold cyan")
        console.print("🏛️  GOVERNMENT AUDIT COMPLIANCE TRACKER", style="bold cyan")
        console.print("="*80, style="bold cyan")
        console.print(f"📊 Target: {self.target_coverage}% Coverage | Current Tier: {self.current_tier}")
        console.print(f"🕐 Scan Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        console.print(f"📁 Modules Discovered: {len(self.modules)}")
        
        # Run coverage analysis
        console.print("\n🔍 Running coverage analysis...", style="blue")
        coverage_data = self._run_coverage_quick()
        
        if not coverage_data:
            console.print("❌ Failed to generate coverage data", style="red")
            return
        
        # Calculate overall coverage
        overall_coverage = coverage_data.get("totals", {}).get("percent_covered", 0)
        console.print(f"📈 Overall Coverage: {overall_coverage:.1f}%", 
                      style="green" if overall_coverage >= self.target_coverage else "yellow")
        
        # Calculate module-specific coverage
        module_coverage = self._calculate_module_coverage(coverage_data)
        
        if not module_coverage:
            console.print("❌ No module coverage data available", style="red")
            return
        
        # Prioritize modules
        priority_list = self._prioritize_modules(module_coverage)
        
        # Calculate compliance metrics
        compliant_modules = len([m for m in module_coverage.values() if m["coverage"] >= self.target_coverage])
        total_modules = len(module_coverage)
        compliance_rate = (compliant_modules / total_modules) * 100 if total_modules > 0 else 0
        
        console.print(f"✅ Compliant Modules: {compliant_modules}/{total_modules} ({compliance_rate:.1f}%)",
                      style="green" if compliance_rate >= 90 else "yellow")
        console.print(f"🎯 Distance to Goal: {self.target_coverage - overall_coverage:.1f} percentage points")
        
        # Show top priority modules
        console.print("\n📋 TOP PRIORITY MODULES (Highest Impact):", style="bold")
        console.print("-" * 80)
        console.print(f"{'Module':<40} {'Coverage':<8} {'Gap':<6} {'Missing':<8} {'Effort':<6}")
        console.print("-" * 80)
        
        for i, item in enumerate(priority_list[:10]):  # Show top 10
            module_name = Path(item["module"]).name
            console.print(f"{module_name:<40} {item['coverage']:>6.1f}% {item['gap']:>5.1f}% {item['missing_lines']:>6d} {item['effort']:>6s}")
        
        if len(priority_list) > 10:
            console.print(f"... and {len(priority_list) - 10} more modules needing attention")
        
        # Effort estimation
        effort_estimate = self._estimate_completion_effort(priority_list)
        
        console.print("\n📊 EFFORT ESTIMATION:", style="bold")
        console.print("-" * 40)
        console.print(f"Quick Wins (≤5 lines):     {effort_estimate['quick_wins']:>3d} modules")
        console.print(f"Medium Effort (6-15 lines): {effort_estimate['medium_effort']:>3d} modules")
        console.print(f"Major Effort (>15 lines):   {effort_estimate['major_effort']:>3d} modules")
        console.print(f"Total Missing Lines:        {effort_estimate['total_missing_lines']:>3d}")
        console.print(f"Estimated Hours:            {effort_estimate['estimated_hours']:>3.1f}")
        
        # Progress indicator
        progress_bar_length = 50
        progress = int((overall_coverage / 100) * progress_bar_length)
        target_pos = int((self.target_coverage / 100) * progress_bar_length)
        
        console.print(f"\n📈 PROGRESS TO 95% GOAL:", style="bold")
        bar = "█" * progress + "░" * (progress_bar_length - progress)
        target_marker = "🎯" if target_pos != progress else ""
        console.print(f"[{bar}] {overall_coverage:.1f}% {target_marker}")
        
        # Show compliance status
        if overall_coverage >= self.target_coverage:
            console.print("🎉 COMPLIANCE ACHIEVED!", style="bold green")
        else:
            remaining = self.target_coverage - overall_coverage
            console.print(f"🔄 {remaining:.1f} percentage points remaining to achieve compliance", style="yellow")
        
        console.print("\n" + "="*80, style="bold cyan")


# ============================================================================
# API Documentation Generation (from tools/documentation/generate_api_docs.py)
# ============================================================================

@dataclass
class APIMethod:
    """Represents a method/function in the API."""
    name: str
    signature: str
    docstring: Optional[str]
    parameters: List[Dict[str, Any]]
    return_type: Optional[str]
    is_async: bool
    is_abstract: bool
    decorators: List[str] = field(default_factory=list)


@dataclass
class APIClass:
    """Represents a class in the API."""
    name: str
    module: str
    docstring: Optional[str]
    base_classes: List[str]
    methods: List[APIMethod]
    attributes: List[Dict[str, Any]]
    is_abstract: bool


@dataclass
class APIModule:
    """Represents a module in the API."""
    name: str
    path: str
    docstring: Optional[str]
    classes: List[APIClass]
    functions: List[APIMethod]
    constants: List[Dict[str, Any]]


class APIDocGenerator:
    """Generate API documentation from Python source code."""
    
    def __init__(self, include_private: bool = False):
        self.include_private = include_private
        self.modules: List[APIModule] = []
    
    def extract_module_info(self, module_path: Path) -> APIModule:
        """Extract API information from a Python module."""
        with open(module_path, 'r') as f:
            source = f.read()
        
        tree = ast.parse(source)
        
        module = APIModule(
            name=module_path.stem,
            path=str(module_path),
            docstring=ast.get_docstring(tree),
            classes=[],
            functions=[],
            constants=[]
        )
        
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                if not self.include_private and node.name.startswith('_'):
                    continue
                module.classes.append(self.extract_class_info(node))
            
            elif isinstance(node, ast.FunctionDef) and node.col_offset == 0:
                if not self.include_private and node.name.startswith('_'):
                    continue
                module.functions.append(self.extract_method_info(node))
            
            elif isinstance(node, ast.Assign) and node.col_offset == 0:
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        if not self.include_private and target.id.startswith('_'):
                            continue
                        module.constants.append({
                            'name': target.id,
                            'value': ast.unparse(node.value) if hasattr(ast, 'unparse') else str(node.value)
                        })
        
        return module
    
    def extract_class_info(self, node: ast.ClassDef) -> APIClass:
        """Extract information from a class definition."""
        base_classes = []
        for base in node.bases:
            if isinstance(base, ast.Name):
                base_classes.append(base.id)
            elif isinstance(base, ast.Attribute):
                base_classes.append(ast.unparse(base) if hasattr(ast, 'unparse') else str(base))
        
        methods = []
        attributes = []
        
        for item in node.body:
            if isinstance(item, ast.FunctionDef):
                if not self.include_private and item.name.startswith('_') and item.name != '__init__':
                    continue
                methods.append(self.extract_method_info(item))
            
            elif isinstance(item, ast.AnnAssign) and isinstance(item.target, ast.Name):
                if not self.include_private and item.target.id.startswith('_'):
                    continue
                attributes.append({
                    'name': item.target.id,
                    'type': ast.unparse(item.annotation) if hasattr(ast, 'unparse') else str(item.annotation),
                    'default': ast.unparse(item.value) if item.value and hasattr(ast, 'unparse') else None
                })
        
        is_abstract = any(
            isinstance(dec, ast.Name) and dec.id == 'abstractmethod'
            for item in node.body
            if isinstance(item, ast.FunctionDef)
            for dec in item.decorator_list
        )
        
        return APIClass(
            name=node.name,
            module='',  # Will be set later
            docstring=ast.get_docstring(node),
            base_classes=base_classes,
            methods=methods,
            attributes=attributes,
            is_abstract=is_abstract
        )
    
    def extract_method_info(self, node: ast.FunctionDef) -> APIMethod:
        """Extract information from a method/function definition."""
        parameters = []
        
        for arg in node.args.args:
            param = {'name': arg.arg}
            
            # Get type annotation
            if arg.annotation:
                param['type'] = ast.unparse(arg.annotation) if hasattr(ast, 'unparse') else str(arg.annotation)
            
            parameters.append(param)
        
        # Get return type
        return_type = None
        if node.returns:
            return_type = ast.unparse(node.returns) if hasattr(ast, 'unparse') else str(node.returns)
        
        # Get decorators
        decorators = []
        is_abstract = False
        for dec in node.decorator_list:
            if isinstance(dec, ast.Name):
                decorators.append(dec.id)
                if dec.id == 'abstractmethod':
                    is_abstract = True
            elif isinstance(dec, ast.Attribute):
                decorators.append(ast.unparse(dec) if hasattr(ast, 'unparse') else str(dec))
        
        # Build signature
        params = []
        for i, arg in enumerate(node.args.args):
            param_str = arg.arg
            if arg.annotation:
                param_str += f": {ast.unparse(arg.annotation) if hasattr(ast, 'unparse') else str(arg.annotation)}"
            
            # Check for default values
            defaults_offset = len(node.args.args) - len(node.args.defaults)
            if i >= defaults_offset:
                default_idx = i - defaults_offset
                default_value = ast.unparse(node.args.defaults[default_idx]) if hasattr(ast, 'unparse') else str(node.args.defaults[default_idx])
                param_str += f" = {default_value}"
            
            params.append(param_str)
        
        signature = f"{node.name}({', '.join(params)})"
        if return_type:
            signature += f" -> {return_type}"
        
        return APIMethod(
            name=node.name,
            signature=signature,
            docstring=ast.get_docstring(node),
            parameters=parameters,
            return_type=return_type,
            is_async=isinstance(node, ast.AsyncFunctionDef),
            is_abstract=is_abstract,
            decorators=decorators
        )
    
    def scan_directory(self, directory: Path) -> List[APIModule]:
        """Scan a directory for Python modules."""
        modules = []
        
        for py_file in directory.rglob("*.py"):
            if py_file.name == '__init__.py':
                continue
            if 'test' in py_file.parts or 'tests' in py_file.parts:
                continue
            
            try:
                module = self.extract_module_info(py_file)
                modules.append(module)
            except Exception as e:
                console.print(f"Error processing {py_file}: {e}", style="red")
        
        return modules
    
    def generate_markdown(self, modules: List[APIModule]) -> str:
        """Generate Markdown documentation."""
        lines = ["# API Reference (Auto-Generated)\n"]
        lines.append("> Generated from source code\n")
        
        # Group modules by package
        packages: Dict[str, List[APIModule]] = {}
        for module in modules:
            parts = Path(module.path).parts
            if 'lib' in parts:
                idx = parts.index('lib')
                package = '.'.join(parts[idx+1:-1]) if len(parts) > idx + 2 else 'lib'
            elif 'agent_workflow' in parts:
                idx = parts.index('agent_workflow')
                package = '.'.join(parts[idx+1:-1]) if len(parts) > idx + 2 else 'agent_workflow'
            else:
                package = 'scripts'
            
            if package not in packages:
                packages[package] = []
            packages[package].append(module)
        
        # Generate documentation for each package
        for package, package_modules in sorted(packages.items()):
            lines.append(f"\n## Package: {package}\n")
            
            for module in sorted(package_modules, key=lambda m: m.name):
                lines.append(f"\n### Module: {module.name}\n")
                
                if module.docstring:
                    lines.append(f"{module.docstring}\n")
                
                # Classes
                if module.classes:
                    lines.append("\n#### Classes\n")
                    
                    for cls in module.classes:
                        lines.append(f"\n##### {cls.name}\n")
                        
                        if cls.docstring:
                            lines.append(f"{cls.docstring}\n")
                        
                        if cls.base_classes:
                            lines.append(f"**Inherits from:** {', '.join(cls.base_classes)}\n")
                        
                        if cls.is_abstract:
                            lines.append("**Abstract Class**\n")
                        
                        # Attributes
                        if cls.attributes:
                            lines.append("\n**Attributes:**\n")
                            for attr in cls.attributes:
                                attr_str = f"- `{attr['name']}"
                                if 'type' in attr:
                                    attr_str += f": {attr['type']}"
                                attr_str += "`"
                                if 'default' in attr and attr['default']:
                                    attr_str += f" (default: {attr['default']})"
                                lines.append(attr_str)
                            lines.append("")
                        
                        # Methods
                        if cls.methods:
                            lines.append("\n**Methods:**\n")
                            for method in cls.methods:
                                lines.append(f"\n`{method.signature}`\n")
                                
                                if method.is_async:
                                    lines.append("*(async method)*\n")
                                
                                if method.is_abstract:
                                    lines.append("*(abstract method)*\n")
                                
                                if method.docstring:
                                    lines.append(f"{method.docstring}\n")
                
                # Module-level functions
                if module.functions:
                    lines.append("\n#### Functions\n")
                    
                    for func in module.functions:
                        lines.append(f"\n`{func.signature}`\n")
                        
                        if func.is_async:
                            lines.append("*(async function)*\n")
                        
                        if func.docstring:
                            lines.append(f"{func.docstring}\n")
                
                # Constants
                if module.constants:
                    lines.append("\n#### Constants\n")
                    
                    for const in module.constants:
                        lines.append(f"- `{const['name']}` = `{const['value']}`")
                    lines.append("")
        
        return '\n'.join(lines)
    
    def generate_openapi(self, modules: List[APIModule]) -> Dict[str, Any]:
        """Generate OpenAPI specification."""
        openapi = {
            "openapi": "3.0.0",
            "info": {
                "title": "AI Agent TDD-Scrum Workflow API",
                "version": "1.0.0",
                "description": "API for orchestrating AI agents in TDD-Scrum workflow"
            },
            "paths": {},
            "components": {
                "schemas": {}
            }
        }
        
        # Extract REST API endpoints if any
        # This is a simplified example - real implementation would need more parsing
        
        for module in modules:
            for cls in module.classes:
                if 'Agent' in cls.name:
                    # Create schema for agent
                    schema = {
                        "type": "object",
                        "properties": {
                            "name": {"type": "string"},
                            "capabilities": {
                                "type": "array",
                                "items": {"type": "string"}
                            }
                        }
                    }
                    
                    openapi["components"]["schemas"][cls.name] = schema
                    
                    # Create endpoint for agent
                    path = f"/agents/{cls.name.lower()}"
                    openapi["paths"][path] = {
                        "post": {
                            "summary": f"Execute {cls.name} task",
                            "requestBody": {
                                "content": {
                                    "application/json": {
                                        "schema": {
                                            "$ref": f"#/components/schemas/{cls.name}Task"
                                        }
                                    }
                                }
                            },
                            "responses": {
                                "200": {
                                    "description": "Task completed successfully"
                                }
                            }
                        }
                    }
        
        return openapi


# ============================================================================
# CLI Commands
# ============================================================================

@click.group()
def dev():
    """Development and utility commands."""
    pass


@dev.command("check-coverage")
def check_coverage_command():
    """Analyze test coverage of the codebase."""
    print_info("Analyzing test coverage...")
    analyze_test_coverage()


@dev.command("check-compliance")
def check_compliance_command():
    """Check government audit compliance status."""
    print_info("Checking compliance status...")
    
    # Check disk space first
    try:
        result = subprocess.run(["df", "-h", "/mnt/c"], capture_output=True, text=True)
        if "97%" in result.stdout or "98%" in result.stdout or "99%" in result.stdout:
            print_warning("Disk usage critical (>95%). Using minimal operations only.")
    except:
        pass
    
    tracker = ComplianceTracker()
    tracker.generate_dashboard()


@dev.command("generate-docs")
@click.option("--output", "-o", type=click.Path(), help="Output file path")
@click.option("--format", type=click.Choice(["markdown", "openapi"]), default="markdown", help="Output format")
@click.option("--include-private", is_flag=True, help="Include private methods and attributes")
@click.option("--directory", default="lib", help="Directory to scan (default: lib)")
def generate_docs_command(output: str, format: str, include_private: bool, directory: str):
    """Generate API documentation from source code."""
    print_info(f"Generating API documentation in {format} format...")
    
    # Get the project root
    project_root = Path.cwd()
    target_dir = project_root / directory
    
    # If lib doesn't exist, try agent_workflow
    if not target_dir.exists() and directory == "lib":
        target_dir = project_root / "agent_workflow"
        if target_dir.exists():
            print_info("lib directory not found, using agent_workflow package instead")
        else:
            print_error(f"Neither lib nor agent_workflow directory exists")
            return
    
    if not target_dir.exists():
        print_error(f"Directory {target_dir} does not exist")
        return
    
    # Generate documentation
    generator = APIDocGenerator(include_private=include_private)
    modules = generator.scan_directory(target_dir)
    
    if not modules:
        print_warning("No modules found to document")
        return
    
    print_info(f"Found {len(modules)} modules to document")
    
    if format == 'markdown':
        output_content = generator.generate_markdown(modules)
    else:  # openapi
        output_dict = generator.generate_openapi(modules)
        output_content = json.dumps(output_dict, indent=2)
    
    # Write output
    if output:
        with open(output, 'w') as f:
            f.write(output_content)
        print_success(f"Documentation written to {output}")
    else:
        console.print(output_content)


if __name__ == "__main__":
    dev()