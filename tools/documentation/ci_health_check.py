#!/usr/bin/env python3
"""
CI/CD Documentation Health Check

A lightweight version of the health check specifically designed for CI/CD pipelines.
Focuses on critical issues that would break the documentation build or user experience.

Exit codes:
- 0: No critical issues
- 1: High-severity issues found
- 2: Build-breaking issues found

Usage:
    python tools/documentation/ci_health_check.py
    python tools/documentation/ci_health_check.py --fail-on-medium
    python tools/documentation/ci_health_check.py --report-only
"""

import argparse
import json
import sys
from pathlib import Path

# Import from the main health check module
sys.path.append(str(Path(__file__).parent))
from health_check import DocumentationHealthChecker


def main():
    """Main CI/CD health check entry point."""
    parser = argparse.ArgumentParser(description='CI/CD Documentation Health Check')
    parser.add_argument(
        '--fail-on-medium',
        action='store_true',
        help='Fail on medium severity issues (default: only high severity)'
    )
    parser.add_argument(
        '--report-only',
        action='store_true',
        help='Generate report without failing (always exit 0)'
    )
    parser.add_argument(
        '--output',
        type=str,
        help='Output file for detailed report'
    )
    parser.add_argument(
        '--quiet',
        action='store_true',
        help='Suppress output (except for critical errors)'
    )
    
    args = parser.parse_args()
    
    # Run health check
    checker = DocumentationHealthChecker()
    
    if not args.quiet:
        print("🔍 Running CI/CD documentation health check...")
    
    # Use quick check for CI/CD (skip expensive link validation)
    report = checker.run_health_check(quick=True)
    
    # Analyze results
    summary = report['summary']
    high_issues = summary['high_severity_issues']
    medium_issues = summary['medium_severity_issues']
    
    # Determine exit code
    exit_code = 0
    
    if high_issues > 0:
        exit_code = 1
        if not args.quiet:
            print(f"❌ {high_issues} high-severity issues found")
    
    if args.fail_on_medium and medium_issues > 0:
        exit_code = max(exit_code, 1)
        if not args.quiet:
            print(f"⚠️  {medium_issues} medium-severity issues found")
    
    # Check for build-breaking issues
    build_breaking_issues = [
        issue for issue in report['issues_by_severity'].get('high', [])
        if issue['type'] in ['configuration', 'structure']
    ]
    
    if build_breaking_issues:
        exit_code = 2
        if not args.quiet:
            print(f"🚨 {len(build_breaking_issues)} build-breaking issues found")
    
    # Generate summary output
    if not args.quiet:
        print(f"📊 Documentation Health: Grade {summary['health_grade']} "
              f"({summary['quality_score']}/100)")
        print(f"📁 Files: {summary['total_files']} total, "
              f"{summary['navigation_coverage']}% in navigation")
        
        # Show critical issues
        if high_issues > 0:
            print("\n🔧 Critical Issues:")
            for issue in report['issues_by_severity'].get('high', [])[:5]:
                print(f"  • {issue['file_path']}: {issue['message']}")
        
        if exit_code == 0:
            print("✅ No critical documentation issues found")
        elif exit_code == 1:
            print("⚠️  Documentation issues found (see above)")
        elif exit_code == 2:
            print("🚨 Build-breaking documentation issues found")
    
    # Save detailed report if requested
    if args.output:
        with open(args.output, 'w') as f:
            json.dump(report, f, indent=2)
        if not args.quiet:
            print(f"📄 Detailed report saved to: {args.output}")
    
    # Exit with appropriate code (unless report-only mode)
    if args.report_only:
        return 0
    else:
        return exit_code


if __name__ == '__main__':
    sys.exit(main())