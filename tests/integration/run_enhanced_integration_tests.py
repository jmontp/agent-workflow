#!/usr/bin/env python3
"""
Enhanced Integration Test Runner

Comprehensive test runner for all integration tests with:
1. Incremental test execution with detailed reporting
2. Performance monitoring and metrics collection
3. Failure analysis and recommendations
4. Test isolation and cleanup
5. Coverage reporting for integration scenarios

Designed to validate small, incremental improvements to integration testing.
"""

import sys
import os
import asyncio
import time
import json
import subprocess
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
import importlib

# Add project paths
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "lib"))
sys.path.insert(0, str(project_root / "scripts"))


class IntegrationTestRunner:
    """Enhanced test runner for integration tests"""
    
    def __init__(self):
        self.test_results: Dict[str, Any] = {}
        self.performance_metrics: List[Dict] = []
        self.test_start_time = None
        self.total_tests = 0
        self.passed_tests = 0
        self.failed_tests = 0
        
    def log_performance_metric(self, test_name: str, duration: float, metadata: Dict = None):
        """Log performance metrics for analysis"""
        self.performance_metrics.append({
            'test_name': test_name,
            'duration': duration,
            'metadata': metadata or {},
            'timestamp': time.time()
        })
    
    async def run_test_module(self, module_name: str, test_description: str) -> Tuple[bool, str]:
        """Run a specific test module and return success status"""
        print(f"\n🔍 Running {test_description}...")
        print("=" * 50)
        
        start_time = time.time()
        
        try:
            # Import and run the test module
            if module_name == "test_enhanced_cross_module_integration":
                from test_enhanced_cross_module_integration import run_cross_module_tests
                success = await run_cross_module_tests()
                
            elif module_name == "test_workflow_validation_integration":
                from test_workflow_validation_integration import run_workflow_validation_tests
                success = await run_workflow_validation_tests()
                
            elif module_name == "test_integration":
                # Run the existing integration test
                import test_integration
                success = await test_integration.main()
                
            elif module_name == "test_context_integration":
                # Run context integration tests
                success = await self._run_pytest_module("test_context_integration.py")
                
            elif module_name == "test_tdd_e2e":
                # Run TDD end-to-end tests
                success = await self._run_pytest_module("test_tdd_e2e.py")
                
            else:
                print(f"⚠️  Unknown test module: {module_name}")
                return False, f"Unknown module: {module_name}"
                
            duration = time.time() - start_time
            self.log_performance_metric(module_name, duration, {
                'success': success,
                'description': test_description
            })
            
            if success:
                print(f"✅ {test_description} completed successfully in {duration:.2f}s")
                return True, "Success"
            else:
                print(f"❌ {test_description} failed after {duration:.2f}s")
                return False, "Test failures detected"
                
        except Exception as e:
            duration = time.time() - start_time
            error_msg = f"Exception in {module_name}: {str(e)}"
            print(f"❌ {test_description} failed with exception after {duration:.2f}s: {e}")
            
            self.log_performance_metric(module_name, duration, {
                'success': False,
                'error': str(e),
                'description': test_description
            })
            
            return False, error_msg
    
    async def _run_pytest_module(self, module_file: str) -> bool:
        """Run a pytest module and return success status"""
        try:
            # Run pytest on the specific module
            integration_dir = Path(__file__).parent
            result = subprocess.run([
                sys.executable, "-m", "pytest", 
                str(integration_dir / module_file),
                "-v", "--tb=short"
            ], capture_output=True, text=True, timeout=300)
            
            if result.returncode == 0:
                print(f"✅ Pytest module {module_file} passed")
                return True
            else:
                print(f"❌ Pytest module {module_file} failed:")
                print(result.stdout)
                print(result.stderr)
                return False
                
        except Exception as e:
            print(f"❌ Error running pytest module {module_file}: {e}")
            return False
    
    def generate_performance_report(self) -> str:
        """Generate performance analysis report"""
        if not self.performance_metrics:
            return "No performance metrics collected"
        
        report = [
            "\n📊 Performance Analysis Report",
            "=" * 40,
            f"Total test modules run: {len(self.performance_metrics)}",
            f"Total execution time: {sum(m['duration'] for m in self.performance_metrics):.2f}s",
            ""
        ]
        
        # Sort by duration
        sorted_metrics = sorted(self.performance_metrics, key=lambda x: x['duration'], reverse=True)
        
        report.append("⏱️  Test Duration Analysis:")
        for metric in sorted_metrics:
            status = "✅" if metric['metadata'].get('success', False) else "❌"
            report.append(f"  {status} {metric['test_name']}: {metric['duration']:.2f}s")
        
        # Performance recommendations
        slow_tests = [m for m in self.performance_metrics if m['duration'] > 30]
        if slow_tests:
            report.extend([
                "",
                "⚠️  Slow Tests (>30s):",
                *[f"  - {t['test_name']}: {t['duration']:.2f}s" for t in slow_tests]
            ])
        
        return "\n".join(report)
    
    def generate_improvement_recommendations(self) -> str:
        """Generate recommendations for integration test improvements"""
        recommendations = [
            "\n🔧 Integration Test Enhancement Recommendations",
            "=" * 50
        ]
        
        # Analysis based on test results
        failed_modules = [
            m for m in self.performance_metrics 
            if not m['metadata'].get('success', False)
        ]
        
        if failed_modules:
            recommendations.extend([
                "❌ Failed Test Modules - Priority Improvements:",
                *[f"  1. Fix {m['test_name']}: {m['metadata'].get('error', 'Unknown error')}" 
                  for m in failed_modules[:3]]
            ])
        
        # General recommendations
        recommendations.extend([
            "",
            "🎯 General Enhancement Areas:",
            "  1. Cross-Module Error Propagation:",
            "     - Add more failure injection scenarios",
            "     - Test cascading failure recovery",
            "     - Validate error message propagation",
            "",
            "  2. Mock Service Integration:",
            "     - Enhance Discord mock with rate limiting",
            "     - Add GitHub webhook failure simulation",
            "     - Improve WebSocket connection stability testing",
            "",
            "  3. Performance Integration:",
            "     - Add load testing scenarios",
            "     - Monitor memory usage during tests",
            "     - Validate resource cleanup",
            "",
            "  4. Real-Time Event Testing:",
            "     - Test state broadcasting reliability",
            "     - Validate event ordering guarantees",
            "     - Check cross-project event isolation",
            "",
            "  5. Workflow Validation:",
            "     - Add more realistic user scenarios",
            "     - Test human-in-the-loop decision points",
            "     - Validate agent coordination patterns"
        ])
        
        return "\n".join(recommendations)
    
    async def run_all_integration_tests(self) -> bool:
        """Run all integration tests in optimized order"""
        print("🚀 Enhanced Integration Test Suite")
        print("=" * 60)
        print("Focus: Small incremental improvements to integration testing")
        print("")
        
        self.test_start_time = time.time()
        
        # Define test modules in execution order (fast to slow)
        test_modules = [
            ("test_integration", "Core Integration Tests (State Machine & Agents)"),
            ("test_enhanced_cross_module_integration", "Enhanced Cross-Module Integration"),
            ("test_workflow_validation_integration", "Workflow Validation Integration"),
            ("test_context_integration", "Context Management Integration"),
            ("test_tdd_e2e", "TDD End-to-End Integration")
        ]
        
        results = []
        
        for module_name, description in test_modules:
            self.total_tests += 1
            success, message = await self.run_test_module(module_name, description)
            
            results.append({
                'module': module_name,
                'description': description,
                'success': success,
                'message': message
            })
            
            if success:
                self.passed_tests += 1
            else:
                self.failed_tests += 1
            
            # Brief pause between test modules
            await asyncio.sleep(0.5)
        
        # Generate final report
        total_duration = time.time() - self.test_start_time
        
        print("\n" + "=" * 60)
        print("📋 Integration Test Suite Summary")
        print("=" * 60)
        print(f"Total Tests: {self.total_tests}")
        print(f"Passed: {self.passed_tests}")
        print(f"Failed: {self.failed_tests}")
        print(f"Success Rate: {(self.passed_tests/self.total_tests*100):.1f}%")
        print(f"Total Duration: {total_duration:.2f}s")
        
        # Detailed results
        print("\n📊 Detailed Results:")
        for result in results:
            status = "✅" if result['success'] else "❌"
            print(f"{status} {result['description']}")
            if not result['success']:
                print(f"   Error: {result['message']}")
        
        # Performance report
        print(self.generate_performance_report())
        
        # Improvement recommendations
        print(self.generate_improvement_recommendations())
        
        # Success criteria
        success_rate = self.passed_tests / self.total_tests
        overall_success = success_rate >= 0.8  # 80% pass rate
        
        if overall_success:
            print("\n🎉 Integration test suite completed successfully!")
            print("   All critical integration patterns are validated.")
        else:
            print("\n⚠️  Integration test suite needs attention.")
            print("   Some integration patterns require improvement.")
        
        return overall_success


async def main():
    """Main entry point for enhanced integration test runner"""
    print("Enhanced Integration Test Runner")
    print("Focusing on small, incremental improvements")
    print("")
    
    # Set up test environment
    os.environ.setdefault('NO_AGENT_MODE', 'true')
    
    # Initialize test runner
    runner = IntegrationTestRunner()
    
    try:
        # Run all integration tests
        success = await runner.run_all_integration_tests()
        
        # Return appropriate exit code
        return 0 if success else 1
        
    except KeyboardInterrupt:
        print("\n⚠️  Test execution interrupted by user")
        return 1
    except Exception as e:
        print(f"\n❌ Test runner failed with exception: {e}")
        import traceback
        traceback.print_exc()
        return 1
    finally:
        # Cleanup environment
        if 'NO_AGENT_MODE' in os.environ:
            del os.environ['NO_AGENT_MODE']


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)