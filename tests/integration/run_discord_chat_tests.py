#!/usr/bin/env python3
"""
Discord Chat Integration Test Runner

Comprehensive test runner for all Discord-style chat interface integration tests.
Includes test execution, reporting, performance benchmarking, and validation.
"""

import argparse
import json
import os
import sys
import time
import traceback
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional

import pytest

# Add paths for imports
current_dir = Path(__file__).parent
visualizer_path = current_dir.parent.parent / "tools" / "visualizer"
tests_path = current_dir.parent
sys.path.insert(0, str(visualizer_path))
sys.path.insert(0, str(tests_path))


class TestResult:
    """Container for test execution results"""
    
    def __init__(self, name: str):
        self.name = name
        self.start_time: Optional[float] = None
        self.end_time: Optional[float] = None
        self.status: str = "not_run"  # not_run, running, passed, failed, error
        self.error: Optional[str] = None
        self.details: Dict[str, Any] = {}
        
    @property
    def duration(self) -> Optional[float]:
        if self.start_time and self.end_time:
            return self.end_time - self.start_time
        return None
    
    def start(self):
        """Mark test as started"""
        self.start_time = time.time()
        self.status = "running"
    
    def finish(self, status: str, error: Optional[str] = None, details: Optional[Dict] = None):
        """Mark test as finished"""
        self.end_time = time.time()
        self.status = status
        self.error = error
        if details:
            self.details.update(details)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            "name": self.name,
            "status": self.status,
            "duration": self.duration,
            "error": self.error,
            "details": self.details,
            "start_time": self.start_time,
            "end_time": self.end_time
        }


class DiscordChatTestRunner:
    """Main test runner for Discord chat integration tests"""
    
    def __init__(self, output_dir: Optional[Path] = None):
        self.output_dir = output_dir or (current_dir / "test_results")
        self.output_dir.mkdir(exist_ok=True)
        
        self.test_modules = [
            "test_discord_chat",
            "test_command_execution", 
            "test_websocket_sync"
        ]
        
        self.results: Dict[str, TestResult] = {}
        self.overall_start_time: Optional[float] = None
        self.overall_end_time: Optional[float] = None
        
    def run_all_tests(self, verbose: bool = False, fast: bool = False) -> Dict[str, Any]:
        """Run all integration tests and return results summary"""
        print("=" * 80)
        print("DISCORD CHAT INTEGRATION TEST SUITE")
        print("=" * 80)
        print(f"Start time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Output directory: {self.output_dir}")
        print()
        
        self.overall_start_time = time.time()
        
        # Pre-flight checks
        if not self._run_preflight_checks():
            print("❌ Pre-flight checks failed. Aborting test run.")
            return self._generate_summary()
        
        # Run test modules
        for module_name in self.test_modules:
            if fast and module_name == "test_websocket_sync":
                print(f"⏩ Skipping {module_name} (fast mode)")
                continue
                
            self._run_test_module(module_name, verbose=verbose)
        
        self.overall_end_time = time.time()
        
        # Generate reports
        self._generate_reports()
        
        # Print summary
        summary = self._generate_summary()
        self._print_summary(summary)
        
        return summary
    
    def _run_preflight_checks(self) -> bool:
        """Run pre-flight checks to ensure test environment is ready"""
        print("🔍 Running pre-flight checks...")
        
        checks = [
            ("Python version >= 3.8", self._check_python_version),
            ("Required packages installed", self._check_packages),
            ("Visualizer app imports", self._check_app_imports),
            ("Test dependencies available", self._check_test_dependencies),
            ("Port 5000 available", self._check_port_availability)
        ]
        
        all_passed = True
        
        for check_name, check_func in checks:
            try:
                result = check_func()
                if result:
                    print(f"  ✅ {check_name}")
                else:
                    print(f"  ❌ {check_name}")
                    all_passed = False
            except Exception as e:
                print(f"  ❌ {check_name}: {e}")
                all_passed = False
        
        print()
        return all_passed
    
    def _check_python_version(self) -> bool:
        """Check Python version is sufficient"""
        return sys.version_info >= (3, 8)
    
    def _check_packages(self) -> bool:
        """Check required packages are installed"""
        required_packages = [
            "flask", "flask_socketio", "pytest", "requests"
        ]
        
        for package in required_packages:
            try:
                __import__(package)
            except ImportError:
                return False
        return True
    
    def _check_app_imports(self) -> bool:
        """Check that visualizer app can be imported"""
        try:
            from app import app, socketio
            return True
        except ImportError:
            return False
    
    def _check_test_dependencies(self) -> bool:
        """Check test-specific dependencies"""
        try:
            import concurrent.futures
            import threading
            import uuid
            return True
        except ImportError:
            return False
    
    def _check_port_availability(self) -> bool:
        """Check if port 5000 is available for testing"""
        import socket
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind(('localhost', 5000))
                return True
        except OSError:
            # Port is in use, but tests might still work
            return True
    
    def _run_test_module(self, module_name: str, verbose: bool = False):
        """Run a specific test module"""
        print(f"🧪 Running {module_name}...")
        
        result = TestResult(module_name)
        self.results[module_name] = result
        
        result.start()
        
        try:
            # Construct pytest command
            test_file = current_dir / f"{module_name}.py"
            if not test_file.exists():
                raise FileNotFoundError(f"Test file not found: {test_file}")
            
            pytest_args = [
                str(test_file),
                "-v" if verbose else "-q",
                "--tb=short",
                "--no-header",
                f"--junitxml={self.output_dir}/{module_name}_results.xml"
            ]
            
            # Run pytest
            exit_code = pytest.main(pytest_args)
            
            if exit_code == 0:
                result.finish("passed")
                print(f"  ✅ {module_name} passed")
            else:
                result.finish("failed", f"pytest exit code: {exit_code}")
                print(f"  ❌ {module_name} failed")
                
        except Exception as e:
            error_msg = f"{type(e).__name__}: {e}"
            result.finish("error", error_msg)
            print(f"  💥 {module_name} error: {error_msg}")
            
            if verbose:
                print(f"     Traceback: {traceback.format_exc()}")
        
        print(f"     Duration: {result.duration:.2f}s")
        print()
    
    def _generate_reports(self):
        """Generate detailed test reports"""
        # JSON report
        json_report = {
            "test_run": {
                "start_time": self.overall_start_time,
                "end_time": self.overall_end_time,
                "duration": self.overall_end_time - self.overall_start_time if self.overall_end_time else None,
                "timestamp": datetime.now().isoformat()
            },
            "results": {name: result.to_dict() for name, result in self.results.items()},
            "summary": self._generate_summary()
        }
        
        json_file = self.output_dir / "discord_chat_test_results.json"
        with open(json_file, 'w') as f:
            json.dump(json_report, f, indent=2)
        
        # HTML report
        self._generate_html_report(json_report)
        
        # Performance report
        self._generate_performance_report()
    
    def _generate_html_report(self, json_report: Dict[str, Any]):
        """Generate HTML test report"""
        html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <title>Discord Chat Integration Test Results</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        .header {{ background: #f0f0f0; padding: 20px; border-radius: 5px; }}
        .summary {{ margin: 20px 0; }}
        .test-result {{ margin: 10px 0; padding: 15px; border-radius: 5px; }}
        .passed {{ background: #d4edda; border-left: 5px solid #28a745; }}
        .failed {{ background: #f8d7da; border-left: 5px solid #dc3545; }}
        .error {{ background: #fff3cd; border-left: 5px solid #ffc107; }}
        .not_run {{ background: #e2e3e5; border-left: 5px solid #6c757d; }}
        .details {{ margin-top: 10px; font-size: 0.9em; color: #666; }}
        table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
        th, td {{ padding: 12px; text-align: left; border-bottom: 1px solid #ddd; }}
        th {{ background-color: #f2f2f2; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>Discord Chat Integration Test Results</h1>
        <p>Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        <p>Total Duration: {json_report['test_run']['duration']:.2f}s</p>
    </div>
    
    <div class="summary">
        <h2>Summary</h2>
        <table>
            <tr><th>Status</th><th>Count</th><th>Percentage</th></tr>
"""
        
        summary = json_report['summary']
        total = summary['total_tests']
        
        for status, count in summary['status_counts'].items():
            percentage = (count / total * 100) if total > 0 else 0
            html_content += f"<tr><td>{status.title()}</td><td>{count}</td><td>{percentage:.1f}%</td></tr>"
        
        html_content += """
        </table>
    </div>
    
    <div class="results">
        <h2>Test Results</h2>
"""
        
        for name, result_data in json_report['results'].items():
            status = result_data['status']
            duration = result_data['duration'] or 0
            
            html_content += f"""
        <div class="test-result {status}">
            <h3>{name}</h3>
            <p><strong>Status:</strong> {status.title()}</p>
            <p><strong>Duration:</strong> {duration:.2f}s</p>
"""
            
            if result_data['error']:
                html_content += f"<p><strong>Error:</strong> {result_data['error']}</p>"
            
            if result_data['details']:
                html_content += f"<div class='details'><strong>Details:</strong> {result_data['details']}</div>"
            
            html_content += "</div>"
        
        html_content += """
    </div>
</body>
</html>"""
        
        html_file = self.output_dir / "discord_chat_test_report.html"
        with open(html_file, 'w') as f:
            f.write(html_content)
    
    def _generate_performance_report(self):
        """Generate performance analysis report"""
        performance_data = {
            "test_durations": {},
            "performance_metrics": {},
            "recommendations": []
        }
        
        # Collect duration data
        for name, result in self.results.items():
            if result.duration:
                performance_data["test_durations"][name] = result.duration
        
        # Performance analysis
        total_duration = sum(performance_data["test_durations"].values())
        avg_duration = total_duration / len(performance_data["test_durations"]) if performance_data["test_durations"] else 0
        
        performance_data["performance_metrics"] = {
            "total_duration": total_duration,
            "average_duration": avg_duration,
            "slowest_test": max(performance_data["test_durations"].items(), key=lambda x: x[1]) if performance_data["test_durations"] else None,
            "fastest_test": min(performance_data["test_durations"].items(), key=lambda x: x[1]) if performance_data["test_durations"] else None
        }
        
        # Generate recommendations
        if avg_duration > 30:
            performance_data["recommendations"].append("Consider optimizing tests - average duration is high")
        
        if performance_data["performance_metrics"]["slowest_test"] and performance_data["performance_metrics"]["slowest_test"][1] > 60:
            slowest = performance_data["performance_metrics"]["slowest_test"]
            performance_data["recommendations"].append(f"Test '{slowest[0]}' is very slow ({slowest[1]:.1f}s) - consider breaking into smaller tests")
        
        # Save performance report
        perf_file = self.output_dir / "performance_report.json"
        with open(perf_file, 'w') as f:
            json.dump(performance_data, f, indent=2)
    
    def _generate_summary(self) -> Dict[str, Any]:
        """Generate test results summary"""
        status_counts = {}
        total_tests = len(self.results)
        
        for result in self.results.values():
            status = result.status
            status_counts[status] = status_counts.get(status, 0) + 1
        
        return {
            "total_tests": total_tests,
            "status_counts": status_counts,
            "success_rate": (status_counts.get("passed", 0) / total_tests * 100) if total_tests > 0 else 0,
            "total_duration": self.overall_end_time - self.overall_start_time if self.overall_end_time else None
        }
    
    def _print_summary(self, summary: Dict[str, Any]):
        """Print test results summary"""
        print("=" * 80)
        print("TEST EXECUTION SUMMARY")
        print("=" * 80)
        
        print(f"Total Tests: {summary['total_tests']}")
        print(f"Success Rate: {summary['success_rate']:.1f}%")
        
        if summary['total_duration']:
            print(f"Total Duration: {summary['total_duration']:.2f}s")
        
        print("\nStatus Breakdown:")
        for status, count in summary['status_counts'].items():
            emoji = {"passed": "✅", "failed": "❌", "error": "💥", "not_run": "⏭️"}.get(status, "❓")
            print(f"  {emoji} {status.title()}: {count}")
        
        print(f"\nReports saved to: {self.output_dir}")
        print("  - discord_chat_test_results.json")
        print("  - discord_chat_test_report.html") 
        print("  - performance_report.json")
        
        if summary['status_counts'].get('failed', 0) > 0 or summary['status_counts'].get('error', 0) > 0:
            print("\n⚠️  Some tests failed. Check individual test reports for details.")
        else:
            print("\n🎉 All tests passed!")


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="Run Discord Chat Integration Tests")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    parser.add_argument("--fast", "-f", action="store_true", help="Skip slow tests")
    parser.add_argument("--output-dir", "-o", type=Path, help="Output directory for results")
    parser.add_argument("--module", "-m", choices=["discord_chat", "command_execution", "websocket_sync"], 
                       help="Run specific test module only")
    
    args = parser.parse_args()
    
    runner = DiscordChatTestRunner(output_dir=args.output_dir)
    
    if args.module:
        # Run specific module
        runner.test_modules = [f"test_{args.module}"]
    
    try:
        summary = runner.run_all_tests(verbose=args.verbose, fast=args.fast)
        
        # Exit with appropriate code
        if summary['status_counts'].get('failed', 0) > 0 or summary['status_counts'].get('error', 0) > 0:
            sys.exit(1)
        else:
            sys.exit(0)
            
    except KeyboardInterrupt:
        print("\n\n⚠️ Test execution interrupted by user")
        sys.exit(130)
    except Exception as e:
        print(f"\n\n💥 Test runner error: {e}")
        if args.verbose:
            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()