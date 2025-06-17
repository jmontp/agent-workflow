#!/usr/bin/env python3
"""
Comprehensive Test Suite Runner for TDD Implementation.

This module orchestrates the execution of all test suites including:
- End-to-End TDD workflow tests
- Performance and load testing
- Security and compliance validation
- Edge case and error testing
- User acceptance testing
- Regression testing
- Test reporting and automation
"""

import asyncio
import time
import json
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional
import subprocess
import argparse

# Add project paths to sys.path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "lib"))
sys.path.insert(0, str(project_root / "scripts"))

# Import test suites
from test_tdd_e2e import run_comprehensive_tdd_tests
from performance.test_tdd_performance import test_tdd_cycle_performance
from security.test_tdd_security import SecurityTestSuite
from edge_cases.test_tdd_edge_cases import EdgeCaseTestSuite
from acceptance.test_tdd_user_acceptance import UserAcceptanceTestSuite
from regression.test_tdd_regression import RegressionTestSuite


class TestSuiteRunner:
    """Comprehensive test suite orchestrator"""
    
    def __init__(self):
        self.test_results: Dict[str, Any] = {}
        self.start_time: Optional[float] = None
        self.end_time: Optional[float] = None
        
    async def run_all_tests(self, test_categories: Optional[List[str]] = None) -> Dict[str, Any]:
        """Run all test suites or specific categories"""
        self.start_time = time.time()
        
        print("="*80)
        print("COMPREHENSIVE TDD TEST SUITE EXECUTION - PHASE 6")
        print("="*80)
        print(f"Start time: {time.strftime('%Y-%m-%d %H:%M:%S')}")
        print()
        
        # Define all available test categories
        all_categories = {
            "e2e": self._run_e2e_tests,
            "performance": self._run_performance_tests,
            "security": self._run_security_tests,
            "edge_cases": self._run_edge_case_tests,
            "acceptance": self._run_acceptance_tests,
            "regression": self._run_regression_tests
        }
        
        # Determine which tests to run
        if test_categories is None:
            test_categories = list(all_categories.keys())
        
        # Run tests
        overall_success = True
        for category in test_categories:
            if category in all_categories:
                print(f"\n{'='*60}")
                print(f"RUNNING {category.upper().replace('_', ' ')} TESTS")
                print(f"{'='*60}")
                
                try:
                    test_func = all_categories[category]
                    result = await test_func()
                    self.test_results[category] = result
                    
                    if not result.get("success", False):
                        overall_success = False
                        print(f"❌ {category.upper()} TESTS FAILED")
                    else:
                        print(f"✅ {category.upper()} TESTS PASSED")
                        
                except Exception as e:
                    self.test_results[category] = {"success": False, "error": str(e)}
                    overall_success = False
                    print(f"❌ {category.upper()} TESTS FAILED WITH EXCEPTION: {e}")
            else:
                print(f"⚠️ Unknown test category: {category}")
        
        self.end_time = time.time()
        
        # Generate comprehensive report
        report = self._generate_comprehensive_report(overall_success)
        
        return {
            "success": overall_success,
            "test_results": self.test_results,
            "comprehensive_report": report
        }
    
    async def _run_e2e_tests(self) -> Dict[str, Any]:
        """Run end-to-end tests"""
        try:
            return await run_comprehensive_tdd_tests()
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def _run_performance_tests(self) -> Dict[str, Any]:
        """Run performance tests"""
        try:
            return await test_tdd_cycle_performance()
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def _run_security_tests(self) -> Dict[str, Any]:
        """Run security tests"""
        try:
            suite = SecurityTestSuite()
            return await suite.run_comprehensive_security_tests()
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def _run_edge_case_tests(self) -> Dict[str, Any]:
        """Run edge case tests"""
        try:
            suite = EdgeCaseTestSuite()
            return await suite.run_comprehensive_edge_case_tests()
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def _run_acceptance_tests(self) -> Dict[str, Any]:
        """Run user acceptance tests"""
        try:
            suite = UserAcceptanceTestSuite()
            return await suite.run_comprehensive_user_acceptance_tests()
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def _run_regression_tests(self) -> Dict[str, Any]:
        """Run regression tests"""
        try:
            suite = RegressionTestSuite()
            return await suite.run_comprehensive_regression_tests()
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _generate_comprehensive_report(self, overall_success: bool) -> Dict[str, Any]:
        """Generate comprehensive test report"""
        total_duration = self.end_time - self.start_time if self.end_time and self.start_time else 0
        
        report = {
            "overall_success": overall_success,
            "total_duration_seconds": total_duration,
            "test_categories": len(self.test_results),
            "passed_categories": sum(1 for r in self.test_results.values() if r.get("success")),
            "failed_categories": sum(1 for r in self.test_results.values() if not r.get("success")),
            "category_results": {},
            "quality_metrics": {},
            "production_readiness": {},
            "recommendations": []
        }
        
        # Analyze each category
        for category, result in self.test_results.items():
            category_analysis = self._analyze_category_result(category, result)
            report["category_results"][category] = category_analysis
        
        # Calculate quality metrics
        report["quality_metrics"] = self._calculate_quality_metrics()
        
        # Assess production readiness
        report["production_readiness"] = self._assess_production_readiness()
        
        # Generate recommendations
        report["recommendations"] = self._generate_recommendations()
        
        return report
    
    def _analyze_category_result(self, category: str, result: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze individual test category result"""
        analysis = {
            "success": result.get("success", False),
            "error": result.get("error"),
            "key_metrics": {},
            "critical_issues": [],
            "recommendations": []
        }
        
        # Category-specific analysis
        if category == "performance" and result.get("success"):
            perf_data = result.get("performance_report", {})
            analysis["key_metrics"] = {
                "overall_score": perf_data.get("overall_score", 0),
                "performance_scores": perf_data.get("performance_scores", {})
            }
            
            if perf_data.get("overall_score", 0) < 80:
                analysis["critical_issues"].append("Performance below acceptable threshold")
        
        elif category == "security" and result.get("success"):
            security_data = result.get("security_summary", {})
            analysis["key_metrics"] = {
                "security_issues": len(security_data.get("security_issues", [])),
                "compliance_issues": len(security_data.get("compliance_issues", []))
            }
            
            if security_data.get("security_issues"):
                analysis["critical_issues"].append("Security vulnerabilities detected")
        
        elif category == "acceptance" and result.get("success"):
            uat_data = result.get("user_acceptance_summary", {})
            analysis["key_metrics"] = {
                "user_satisfaction_score": uat_data.get("user_satisfaction_score", 0),
                "usability_issues": len(uat_data.get("usability_issues", []))
            }
            
            if uat_data.get("user_satisfaction_score", 0) < 75:
                analysis["critical_issues"].append("User satisfaction below acceptable level")
        
        elif category == "regression" and result.get("success"):
            regression_data = result.get("regression_summary", {})
            analysis["key_metrics"] = {
                "backward_compatibility_score": regression_data.get("backward_compatibility_score", 0),
                "breaking_changes": len(regression_data.get("breaking_changes", []))
            }
            
            if regression_data.get("breaking_changes"):
                analysis["critical_issues"].append("Breaking changes detected")
        
        elif category == "edge_cases" and result.get("success"):
            edge_data = result.get("edge_case_summary", {})
            analysis["key_metrics"] = {
                "resilience_score": edge_data.get("resilience_score", 0),
                "critical_issues": len(edge_data.get("critical_issues", []))
            }
            
            if edge_data.get("resilience_score", 0) < 80:
                analysis["critical_issues"].append("System resilience below acceptable level")
        
        return analysis
    
    def _calculate_quality_metrics(self) -> Dict[str, Any]:
        """Calculate overall quality metrics"""
        metrics = {
            "test_coverage_score": 0,
            "reliability_score": 0,
            "performance_score": 0,
            "security_score": 0,
            "usability_score": 0,
            "overall_quality_score": 0
        }
        
        # Extract scores from test results
        scores = []
        
        # Performance score
        perf_result = self.test_results.get("performance", {})
        if perf_result.get("success") and "performance_report" in perf_result:
            perf_score = perf_result["performance_report"].get("overall_score", 0)
            metrics["performance_score"] = perf_score
            scores.append(perf_score)
        
        # Security score
        security_result = self.test_results.get("security", {})
        if security_result.get("success"):
            security_summary = security_result.get("security_summary", {})
            total_tests = security_summary.get("total_tests", 1)
            passed_tests = security_summary.get("passed_tests", 0)
            security_score = (passed_tests / total_tests) * 100 if total_tests > 0 else 0
            metrics["security_score"] = security_score
            scores.append(security_score)
        
        # Usability score
        acceptance_result = self.test_results.get("acceptance", {})
        if acceptance_result.get("success"):
            uat_summary = acceptance_result.get("user_acceptance_summary", {})
            usability_score = uat_summary.get("user_satisfaction_score", 0)
            metrics["usability_score"] = usability_score
            scores.append(usability_score)
        
        # Reliability score (from edge cases)
        edge_result = self.test_results.get("edge_cases", {})
        if edge_result.get("success"):
            edge_summary = edge_result.get("edge_case_summary", {})
            reliability_score = edge_summary.get("resilience_score", 0)
            metrics["reliability_score"] = reliability_score
            scores.append(reliability_score)
        
        # Test coverage score (based on test category completion)
        total_categories = len(self.test_results)
        passed_categories = sum(1 for r in self.test_results.values() if r.get("success"))
        coverage_score = (passed_categories / total_categories) * 100 if total_categories > 0 else 0
        metrics["test_coverage_score"] = coverage_score
        scores.append(coverage_score)
        
        # Overall quality score
        if scores:
            metrics["overall_quality_score"] = sum(scores) / len(scores)
        
        return metrics
    
    def _assess_production_readiness(self) -> Dict[str, Any]:
        """Assess overall production readiness"""
        readiness = {
            "ready_for_production": False,
            "readiness_score": 0,
            "critical_blockers": [],
            "minor_issues": [],
            "requirements_met": {}
        }
        
        # Define production readiness requirements
        requirements = {
            "all_tests_pass": all(r.get("success", False) for r in self.test_results.values()),
            "performance_acceptable": self._check_performance_requirement(),
            "security_validated": self._check_security_requirement(),
            "user_satisfaction": self._check_user_satisfaction_requirement(),
            "backward_compatibility": self._check_backward_compatibility_requirement(),
            "reliability_proven": self._check_reliability_requirement()
        }
        
        readiness["requirements_met"] = requirements
        
        # Calculate readiness score
        met_requirements = sum(1 for met in requirements.values() if met)
        total_requirements = len(requirements)
        readiness["readiness_score"] = (met_requirements / total_requirements) * 100
        
        # Determine production readiness
        if readiness["readiness_score"] >= 95:
            readiness["ready_for_production"] = True
        elif readiness["readiness_score"] >= 85:
            readiness["ready_for_production"] = False
            readiness["minor_issues"].append("Minor quality issues need resolution")
        else:
            readiness["ready_for_production"] = False
            readiness["critical_blockers"].append("Significant quality issues block production deployment")
        
        # Identify specific blockers
        for requirement, met in requirements.items():
            if not met:
                if requirement in ["all_tests_pass", "security_validated"]:
                    readiness["critical_blockers"].append(f"Critical requirement not met: {requirement}")
                else:
                    readiness["minor_issues"].append(f"Requirement not fully met: {requirement}")
        
        return readiness
    
    def _check_performance_requirement(self) -> bool:
        """Check if performance requirements are met"""
        perf_result = self.test_results.get("performance", {})
        if not perf_result.get("success"):
            return False
        
        perf_report = perf_result.get("performance_report", {})
        return perf_report.get("overall_score", 0) >= 80
    
    def _check_security_requirement(self) -> bool:
        """Check if security requirements are met"""
        security_result = self.test_results.get("security", {})
        if not security_result.get("success"):
            return False
        
        security_summary = security_result.get("security_summary", {})
        return len(security_summary.get("security_issues", [])) == 0
    
    def _check_user_satisfaction_requirement(self) -> bool:
        """Check if user satisfaction requirements are met"""
        acceptance_result = self.test_results.get("acceptance", {})
        if not acceptance_result.get("success"):
            return False
        
        uat_summary = acceptance_result.get("user_acceptance_summary", {})
        return uat_summary.get("user_satisfaction_score", 0) >= 75
    
    def _check_backward_compatibility_requirement(self) -> bool:
        """Check if backward compatibility requirements are met"""
        regression_result = self.test_results.get("regression", {})
        if not regression_result.get("success"):
            return False
        
        regression_summary = regression_result.get("regression_summary", {})
        return len(regression_summary.get("breaking_changes", [])) == 0
    
    def _check_reliability_requirement(self) -> bool:
        """Check if reliability requirements are met"""
        edge_result = self.test_results.get("edge_cases", {})
        if not edge_result.get("success"):
            return False
        
        edge_summary = edge_result.get("edge_case_summary", {})
        return edge_summary.get("resilience_score", 0) >= 80
    
    def _generate_recommendations(self) -> List[str]:
        """Generate actionable recommendations"""
        recommendations = []
        
        # Analyze each test category for recommendations
        for category, result in self.test_results.items():
            if not result.get("success"):
                recommendations.append(f"Fix failing {category} tests before production deployment")
            
            # Category-specific recommendations
            if category == "performance":
                perf_report = result.get("performance_report", {})
                if perf_report.get("overall_score", 100) < 80:
                    recommendations.append("Optimize performance to meet production requirements")
            
            elif category == "security":
                security_summary = result.get("security_summary", {})
                if security_summary.get("security_issues"):
                    recommendations.append("Address all security vulnerabilities before deployment")
            
            elif category == "acceptance":
                uat_summary = result.get("user_acceptance_summary", {})
                if uat_summary.get("user_satisfaction_score", 100) < 75:
                    recommendations.append("Improve user experience based on acceptance test feedback")
        
        # Overall recommendations
        quality_metrics = self._calculate_quality_metrics()
        if quality_metrics["overall_quality_score"] < 85:
            recommendations.append("Improve overall system quality before production release")
        
        return list(set(recommendations))  # Remove duplicates
    
    def save_report(self, report: Dict[str, Any], filename: Optional[str] = None) -> Path:
        """Save comprehensive test report to file"""
        if filename is None:
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            filename = f"tdd_comprehensive_test_report_{timestamp}.json"
        
        report_path = Path(__file__).parent / "reports" / filename
        report_path.parent.mkdir(exist_ok=True)
        
        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2, default=str)
        
        return report_path
    
    def print_summary_report(self, report: Dict[str, Any]):
        """Print a summary of the test results"""
        print("\n" + "="*80)
        print("COMPREHENSIVE TEST SUITE SUMMARY")
        print("="*80)
        
        # Overall status
        if report["overall_success"]:
            print("🎉 OVERALL STATUS: ALL TESTS PASSED!")
        else:
            print("❌ OVERALL STATUS: SOME TESTS FAILED")
        
        # Basic metrics
        print(f"\nTest Execution Summary:")
        print(f"  Total Duration: {report['total_duration_seconds']:.1f} seconds")
        print(f"  Test Categories: {report['test_categories']}")
        print(f"  Passed Categories: {report['passed_categories']}")
        print(f"  Failed Categories: {report['failed_categories']}")
        
        # Quality metrics
        quality = report.get("quality_metrics", {})
        print(f"\nQuality Metrics:")
        print(f"  Overall Quality Score: {quality.get('overall_quality_score', 0):.1f}/100")
        print(f"  Performance Score: {quality.get('performance_score', 0):.1f}/100")
        print(f"  Security Score: {quality.get('security_score', 0):.1f}/100")
        print(f"  Usability Score: {quality.get('usability_score', 0):.1f}/100")
        print(f"  Reliability Score: {quality.get('reliability_score', 0):.1f}/100")
        
        # Production readiness
        readiness = report.get("production_readiness", {})
        print(f"\nProduction Readiness:")
        if readiness.get("ready_for_production"):
            print("  ✅ READY FOR PRODUCTION")
        else:
            print("  ❌ NOT READY FOR PRODUCTION")
        print(f"  Readiness Score: {readiness.get('readiness_score', 0):.1f}/100")
        
        if readiness.get("critical_blockers"):
            print(f"  Critical Blockers:")
            for blocker in readiness["critical_blockers"]:
                print(f"    • {blocker}")
        
        # Recommendations
        recommendations = report.get("recommendations", [])
        if recommendations:
            print(f"\nRecommendations:")
            for rec in recommendations:
                print(f"  • {rec}")
        
        print("\n" + "="*80)


async def main():
    """Main test execution function"""
    parser = argparse.ArgumentParser(description="Run comprehensive TDD test suite")
    parser.add_argument(
        "--categories", 
        nargs="*", 
        choices=["e2e", "performance", "security", "edge_cases", "acceptance", "regression"],
        help="Specific test categories to run (default: all)"
    )
    parser.add_argument(
        "--save-report", 
        action="store_true",
        help="Save detailed report to file"
    )
    parser.add_argument(
        "--report-file",
        type=str,
        help="Custom filename for the report"
    )
    
    args = parser.parse_args()
    
    # Create test runner
    runner = TestSuiteRunner()
    
    try:
        # Run tests
        result = await runner.run_all_tests(args.categories)
        
        # Print summary
        runner.print_summary_report(result["comprehensive_report"])
        
        # Save detailed report if requested
        if args.save_report:
            report_path = runner.save_report(result, args.report_file)
            print(f"\nDetailed report saved to: {report_path}")
        
        # Return appropriate exit code
        return 0 if result["success"] else 1
        
    except Exception as e:
        print(f"\n❌ COMPREHENSIVE TEST SUITE FAILED: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))