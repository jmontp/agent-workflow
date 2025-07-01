#!/usr/bin/env python3
"""
Multi-Project System Test Runner

Comprehensive test runner for all multi-project integration tests.
Validates backend API, project switching, chat isolation, and responsive design.
"""

import os
import sys
import subprocess
import time
import json
import argparse
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# Test modules to run
TEST_MODULES = [
    "test_multi_project_backend",
    "test_project_switching", 
    "test_chat_isolation",
    "test_responsive_design"
]

# Test categories and their descriptions
TEST_CATEGORIES = {
    "backend": {
        "module": "test_multi_project_backend",
        "description": "Backend API endpoints and data integrity",
        "critical": True
    },
    "switching": {
        "module": "test_project_switching",
        "description": "Project switching and state synchronization",
        "critical": True
    },
    "isolation": {
        "module": "test_chat_isolation", 
        "description": "Chat isolation and security boundaries",
        "critical": True
    },
    "responsive": {
        "module": "test_responsive_design",
        "description": "Mobile responsiveness and accessibility",
        "critical": False
    }
}


class TestResult:
    """Container for test results"""
    
    def __init__(self, module: str, status: str, duration: float, 
                 passed: int = 0, failed: int = 0, errors: int = 0,
                 skipped: int = 0, output: str = ""):
        self.module = module
        self.status = status  # passed, failed, error, skipped
        self.duration = duration
        self.passed = passed
        self.failed = failed
        self.errors = errors
        self.skipped = skipped
        self.output = output
        self.timestamp = datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            "module": self.module,
            "status": self.status,
            "duration": self.duration,
            "passed": self.passed,
            "failed": self.failed,
            "errors": self.errors,
            "skipped": self.skipped,
            "timestamp": self.timestamp.isoformat(),
            "output": self.output
        }


class MultiProjectTestRunner:
    """Test runner for multi-project integration tests"""
    
    def __init__(self, verbose: bool = False, fast: bool = False):
        self.verbose = verbose
        self.fast = fast
        self.results: List[TestResult] = []
        self.start_time = time.time()
        
        # Test directory
        self.test_dir = Path(__file__).parent
        
        # Output directory for reports
        self.output_dir = self.test_dir / "reports"
        self.output_dir.mkdir(exist_ok=True)
    
    def run_test_module(self, module: str) -> TestResult:
        """Run a specific test module"""
        print(f"\n{'='*60}")
        print(f"Running {module}")
        print(f"{'='*60}")
        
        start_time = time.time()
        
        # Build pytest command
        cmd = [
            sys.executable, "-m", "pytest",
            str(self.test_dir / f"{module}.py"),
            "-v" if self.verbose else "-q",
            "--tb=short",
            "--disable-warnings"
        ]
        
        if self.fast:
            cmd.extend(["-x", "--maxfail=1"])  # Stop on first failure
        
        try:
            # Run test
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300 if self.fast else 600  # 5 or 10 minute timeout
            )
            
            duration = time.time() - start_time
            
            # Parse output for test counts
            passed, failed, errors, skipped = self._parse_pytest_output(result.stdout)
            
            # Determine status
            if result.returncode == 0:
                status = "passed"
            elif failed > 0 or errors > 0:
                status = "failed"
            else:
                status = "error"
            
            test_result = TestResult(
                module=module,
                status=status,
                duration=duration,
                passed=passed,
                failed=failed,
                errors=errors,
                skipped=skipped,
                output=result.stdout + "\n" + result.stderr
            )
            
            self._print_module_summary(test_result)
            
            return test_result
            
        except subprocess.TimeoutExpired:
            duration = time.time() - start_time
            return TestResult(
                module=module,
                status="timeout",
                duration=duration,
                output="Test timed out"
            )
            
        except Exception as e:
            duration = time.time() - start_time
            return TestResult(
                module=module,
                status="error",
                duration=duration,
                output=f"Error running test: {str(e)}"
            )
    
    def _parse_pytest_output(self, output: str) -> tuple:
        """Parse pytest output to extract test counts"""
        passed = failed = errors = skipped = 0
        
        # Look for pytest summary line
        lines = output.split('\n')
        for line in lines:
            if 'passed' in line and ('failed' in line or 'error' in line or 'skipped' in line):
                # Parse line like "5 passed, 2 failed, 1 error, 3 skipped"
                parts = line.split(',')
                for part in parts:
                    part = part.strip()
                    if 'passed' in part:
                        passed = int(part.split()[0])
                    elif 'failed' in part:
                        failed = int(part.split()[0])
                    elif 'error' in part:
                        errors = int(part.split()[0])
                    elif 'skipped' in part:
                        skipped = int(part.split()[0])
                break
            elif 'passed' in line and 'failed' not in line:
                # Just passed tests
                if ' passed' in line:
                    passed = int(line.split()[0])
        
        return passed, failed, errors, skipped
    
    def _print_module_summary(self, result: TestResult):
        """Print summary for a test module"""
        status_color = {
            "passed": "\033[92m",  # Green
            "failed": "\033[91m",  # Red
            "error": "\033[91m",   # Red
            "timeout": "\033[93m", # Yellow
            "skipped": "\033[93m"  # Yellow
        }
        reset_color = "\033[0m"
        
        color = status_color.get(result.status, "")
        
        print(f"\n{color}Module: {result.module}{reset_color}")
        print(f"Status: {color}{result.status.upper()}{reset_color}")
        print(f"Duration: {result.duration:.2f}s")
        print(f"Passed: {result.passed}, Failed: {result.failed}, "
              f"Errors: {result.errors}, Skipped: {result.skipped}")
        
        if result.status != "passed" and self.verbose:
            print(f"\nOutput:\n{result.output}")
    
    def run_all_tests(self, categories: List[str] = None) -> bool:
        """Run all or specified test categories"""
        if categories:
            modules_to_run = [TEST_CATEGORIES[cat]["module"] for cat in categories 
                            if cat in TEST_CATEGORIES]
        else:
            modules_to_run = TEST_MODULES
        
        print(f"Multi-Project Integration Test Suite")
        print(f"Running {len(modules_to_run)} test modules")
        print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Run each test module
        for module in modules_to_run:
            result = self.run_test_module(module)
            self.results.append(result)
        
        # Generate reports
        self._generate_summary_report()
        self._generate_json_report()
        
        # Print final summary
        self._print_final_summary()
        
        # Return success if all critical tests passed
        return self._all_critical_tests_passed()
    
    def _generate_summary_report(self):
        """Generate text summary report"""
        total_duration = time.time() - self.start_time
        
        report_path = self.output_dir / f"summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        
        with open(report_path, 'w') as f:
            f.write("Multi-Project Integration Test Summary\n")
            f.write("=" * 50 + "\n\n")
            
            f.write(f"Test Run: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Total Duration: {total_duration:.2f}s\n")
            f.write(f"Modules Tested: {len(self.results)}\n\n")
            
            # Overall status
            total_passed = sum(r.passed for r in self.results)
            total_failed = sum(r.failed for r in self.results)
            total_errors = sum(r.errors for r in self.results)
            total_skipped = sum(r.skipped for r in self.results)
            
            f.write(f"Overall Results:\n")
            f.write(f"  Passed: {total_passed}\n")
            f.write(f"  Failed: {total_failed}\n")
            f.write(f"  Errors: {total_errors}\n")
            f.write(f"  Skipped: {total_skipped}\n\n")
            
            # Module details
            f.write("Module Results:\n")
            f.write("-" * 30 + "\n")
            
            for result in self.results:
                f.write(f"\n{result.module}:\n")
                f.write(f"  Status: {result.status}\n")
                f.write(f"  Duration: {result.duration:.2f}s\n")
                f.write(f"  Passed: {result.passed}, Failed: {result.failed}\n")
                f.write(f"  Errors: {result.errors}, Skipped: {result.skipped}\n")
                
                if result.status != "passed":
                    f.write(f"  Output Preview:\n")
                    # Write first few lines of output
                    output_lines = result.output.split('\n')[:10]
                    for line in output_lines:
                        f.write(f"    {line}\n")
        
        print(f"\nSummary report saved to: {report_path}")
    
    def _generate_json_report(self):
        """Generate JSON report for programmatic access"""
        total_duration = time.time() - self.start_time
        
        report_data = {
            "test_run": {
                "timestamp": datetime.now().isoformat(),
                "total_duration": total_duration,
                "modules_tested": len(self.results)
            },
            "overall_stats": {
                "total_passed": sum(r.passed for r in self.results),
                "total_failed": sum(r.failed for r in self.results),
                "total_errors": sum(r.errors for r in self.results),
                "total_skipped": sum(r.skipped for r in self.results)
            },
            "module_results": [result.to_dict() for result in self.results],
            "test_categories": TEST_CATEGORIES
        }
        
        report_path = self.output_dir / f"results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        with open(report_path, 'w') as f:
            json.dump(report_data, f, indent=2)
        
        print(f"JSON report saved to: {report_path}")
    
    def _print_final_summary(self):
        """Print final summary to console"""
        total_duration = time.time() - self.start_time
        
        print(f"\n{'='*80}")
        print(f"MULTI-PROJECT INTEGRATION TEST SUMMARY")
        print(f"{'='*80}")
        
        print(f"Total Duration: {total_duration:.2f}s")
        print(f"Modules Tested: {len(self.results)}")
        
        # Count by status
        status_counts = {}
        for result in self.results:
            status_counts[result.status] = status_counts.get(result.status, 0) + 1
        
        print(f"\nModule Status:")
        for status, count in status_counts.items():
            print(f"  {status.title()}: {count}")
        
        # Test counts
        total_passed = sum(r.passed for r in self.results)
        total_failed = sum(r.failed for r in self.results)
        total_errors = sum(r.errors for r in self.results)
        total_skipped = sum(r.skipped for r in self.results)
        
        print(f"\nTest Counts:")
        print(f"  Passed: {total_passed}")
        print(f"  Failed: {total_failed}")
        print(f"  Errors: {total_errors}")
        print(f"  Skipped: {total_skipped}")
        
        # Failed modules
        failed_modules = [r.module for r in self.results if r.status in ["failed", "error", "timeout"]]
        if failed_modules:
            print(f"\nFailed Modules:")
            for module in failed_modules:
                print(f"  - {module}")
        
        # Overall result
        all_passed = self._all_critical_tests_passed()
        status_color = "\033[92m" if all_passed else "\033[91m"
        reset_color = "\033[0m"
        
        overall_status = "PASSED" if all_passed else "FAILED"
        print(f"\n{status_color}Overall Result: {overall_status}{reset_color}")
        
        print(f"{'='*80}")
    
    def _all_critical_tests_passed(self) -> bool:
        """Check if all critical tests passed"""
        critical_modules = [cat["module"] for cat in TEST_CATEGORIES.values() if cat["critical"]]
        
        for result in self.results:
            if result.module in critical_modules and result.status != "passed":
                return False
        
        return True
    
    def run_quick_validation(self) -> bool:
        """Run quick validation tests only"""
        print("Running quick validation of multi-project system...")
        
        # Run a subset of critical tests
        quick_tests = ["test_multi_project_backend::TestHealthAndStatus"]
        
        cmd = [
            sys.executable, "-m", "pytest",
            str(self.test_dir / "test_multi_project_backend.py::TestHealthAndStatus"),
            "-v", "--tb=short", "--disable-warnings"
        ]
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            
            if result.returncode == 0:
                print("✅ Quick validation PASSED")
                return True
            else:
                print("❌ Quick validation FAILED")
                if self.verbose:
                    print(result.stdout)
                    print(result.stderr)
                return False
                
        except Exception as e:
            print(f"❌ Quick validation ERROR: {e}")
            return False


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="Multi-Project Integration Test Runner")
    
    parser.add_argument(
        "--categories", "-c",
        nargs="+",
        choices=list(TEST_CATEGORIES.keys()),
        help="Test categories to run (default: all)"
    )
    
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Verbose output"
    )
    
    parser.add_argument(
        "--fast", "-f",
        action="store_true",
        help="Fast mode (stop on first failure)"
    )
    
    parser.add_argument(
        "--quick",
        action="store_true",
        help="Run quick validation only"
    )
    
    parser.add_argument(
        "--list-categories",
        action="store_true",
        help="List available test categories"
    )
    
    args = parser.parse_args()
    
    if args.list_categories:
        print("Available test categories:")
        for name, info in TEST_CATEGORIES.items():
            critical = " (CRITICAL)" if info["critical"] else ""
            print(f"  {name}: {info['description']}{critical}")
        return 0
    
    # Create test runner
    runner = MultiProjectTestRunner(verbose=args.verbose, fast=args.fast)
    
    if args.quick:
        success = runner.run_quick_validation()
        return 0 if success else 1
    
    # Run tests
    success = runner.run_all_tests(args.categories)
    
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())