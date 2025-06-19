#!/usr/bin/env python3
"""
Government Audit Compliance Tracker

Real-time monitoring system for tracking test coverage across all lib modules.
Lightweight implementation optimized for disk space constraints.
"""

import subprocess
import json
import os
import sys
from datetime import datetime
from pathlib import Path


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
            print("📊 Using existing coverage.xml data...")
            return self._parse_coverage_xml()
        
        try:
            # Run coverage with minimal output
            cmd = [
                "python3", "-m", "pytest", 
                "--cov=lib", 
                "--cov-report=json:coverage_temp.json",
                "--tb=no", "-q",  # No traceback, quiet mode
                "tests/unit/test_context_filter.py",  # Test one representative file
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
            print("❌ Coverage analysis timed out")
            return None
        except Exception as e:
            print(f"❌ Coverage analysis failed: {e}")
            return None
    
    def _parse_coverage_xml(self):
        """Parse existing coverage.xml file for quick analysis."""
        try:
            import xml.etree.ElementTree as ET
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
            print(f"❌ Failed to parse coverage.xml: {e}")
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
        print("\n" + "="*80)
        print("🏛️  GOVERNMENT AUDIT COMPLIANCE TRACKER")
        print("="*80)
        print(f"📊 Target: {self.target_coverage}% Coverage | Current Tier: {self.current_tier}")
        print(f"🕐 Scan Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"📁 Modules Discovered: {len(self.modules)}")
        
        # Run coverage analysis
        print("\n🔍 Running coverage analysis...")
        coverage_data = self._run_coverage_quick()
        
        if not coverage_data:
            print("❌ Failed to generate coverage data")
            return
        
        # Calculate overall coverage
        overall_coverage = coverage_data.get("totals", {}).get("percent_covered", 0)
        print(f"📈 Overall Coverage: {overall_coverage:.1f}%")
        
        # Calculate module-specific coverage
        module_coverage = self._calculate_module_coverage(coverage_data)
        
        if not module_coverage:
            print("❌ No module coverage data available")
            return
        
        # Prioritize modules
        priority_list = self._prioritize_modules(module_coverage)
        
        # Calculate compliance metrics
        compliant_modules = len([m for m in module_coverage.values() if m["coverage"] >= self.target_coverage])
        total_modules = len(module_coverage)
        compliance_rate = (compliant_modules / total_modules) * 100 if total_modules > 0 else 0
        
        print(f"✅ Compliant Modules: {compliant_modules}/{total_modules} ({compliance_rate:.1f}%)")
        print(f"🎯 Distance to Goal: {self.target_coverage - overall_coverage:.1f} percentage points")
        
        # Show top priority modules
        print("\n📋 TOP PRIORITY MODULES (Highest Impact):")
        print("-" * 80)
        print(f"{'Module':<40} {'Coverage':<8} {'Gap':<6} {'Missing':<8} {'Effort':<6}")
        print("-" * 80)
        
        for i, item in enumerate(priority_list[:10]):  # Show top 10
            module_name = Path(item["module"]).name
            print(f"{module_name:<40} {item['coverage']:>6.1f}% {item['gap']:>5.1f}% {item['missing_lines']:>6d} {item['effort']:>6s}")
        
        if len(priority_list) > 10:
            print(f"... and {len(priority_list) - 10} more modules needing attention")
        
        # Effort estimation
        effort_estimate = self._estimate_completion_effort(priority_list)
        
        print("\n📊 EFFORT ESTIMATION:")
        print("-" * 40)
        print(f"Quick Wins (≤5 lines):     {effort_estimate['quick_wins']:>3d} modules")
        print(f"Medium Effort (6-15 lines): {effort_estimate['medium_effort']:>3d} modules")
        print(f"Major Effort (>15 lines):   {effort_estimate['major_effort']:>3d} modules")
        print(f"Total Missing Lines:        {effort_estimate['total_missing_lines']:>3d}")
        print(f"Estimated Hours:            {effort_estimate['estimated_hours']:>3.1f}")
        
        # Progress indicator
        progress_bar_length = 50
        progress = int((overall_coverage / 100) * progress_bar_length)
        target_pos = int((self.target_coverage / 100) * progress_bar_length)
        
        print(f"\n📈 PROGRESS TO 95% GOAL:")
        bar = "█" * progress + "░" * (progress_bar_length - progress)
        target_marker = "🎯" if target_pos != progress else ""
        print(f"[{bar}] {overall_coverage:.1f}% {target_marker}")
        
        # Show compliance status
        if overall_coverage >= self.target_coverage:
            print("🎉 COMPLIANCE ACHIEVED!")
        else:
            remaining = self.target_coverage - overall_coverage
            print(f"🔄 {remaining:.1f} percentage points remaining to achieve compliance")
        
        print("\n" + "="*80)


def main():
    """Main entry point for compliance tracker."""
    # Check disk space first
    try:
        result = subprocess.run(["df", "-h", "/mnt/c"], capture_output=True, text=True)
        if "97%" in result.stdout or "98%" in result.stdout or "99%" in result.stdout:
            print("⚠️  WARNING: Disk usage critical (>95%). Using minimal operations only.")
    except:
        pass
    
    tracker = ComplianceTracker()
    tracker.generate_dashboard()


if __name__ == "__main__":
    main()