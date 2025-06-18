#!/usr/bin/env python3
"""
Lightweight Government Audit Compliance Monitor

Quick monitoring script for tracking progress without heavy analysis.
Optimized for minimal disk usage and fast execution.
"""

import subprocess
import sys
import os
from datetime import datetime


def check_disk_space():
    """Check disk space and warn if critical."""
    try:
        result = subprocess.run(["df", "-h", "/mnt/c"], capture_output=True, text=True)
        for line in result.stdout.split('\n'):
            if 'Use%' in line or '/mnt/c' in line:
                if any(usage in line for usage in ['97%', '98%', '99%']):
                    print("🚨 CRITICAL: Disk space at >96%. Exercise extreme caution.")
                    return False
                elif any(usage in line for usage in ['95%', '96%']):
                    print("⚠️  WARNING: Disk space at >94%. Use minimal operations.")
                    return True
        return True
    except:
        return True


def quick_coverage_check():
    """Quick coverage check using existing coverage.xml."""
    if not os.path.exists("coverage.xml"):
        print("📊 No coverage.xml found. Run full analysis first.")
        return None
    
    try:
        import xml.etree.ElementTree as ET
        tree = ET.parse("coverage.xml")
        root = tree.getroot()
        
        # Extract key metrics
        line_rate = float(root.get("line-rate", "0"))
        overall_pct = line_rate * 100
        total_lines = int(root.get("lines-valid", "0"))
        covered_lines = int(root.get("lines-covered", "0"))
        
        # Count modules
        modules = root.findall(".//class")
        total_modules = len(modules)
        compliant_modules = 0
        
        for module in modules:
            module_lines = module.findall("lines/line")
            if module_lines:
                module_covered = len([line for line in module_lines if int(line.get("hits", "0")) > 0])
                module_total = len(module_lines)
                module_pct = (module_covered / module_total * 100) if module_total > 0 else 0
                if module_pct >= 95.0:
                    compliant_modules += 1
        
        return {
            "overall_coverage": overall_pct,
            "total_lines": total_lines,
            "covered_lines": covered_lines,
            "total_modules": total_modules,
            "compliant_modules": compliant_modules,
            "compliance_rate": (compliant_modules / total_modules * 100) if total_modules > 0 else 0
        }
        
    except Exception as e:
        print(f"❌ Failed to parse coverage data: {e}")
        return None


def main():
    """Main monitoring function."""
    print("🏛️  GOVERNMENT AUDIT COMPLIANCE MONITOR")
    print("=" * 50)
    print(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Check disk space first
    if not check_disk_space():
        print("🛑 Monitoring suspended due to critical disk space.")
        sys.exit(1)
    
    # Quick coverage check
    metrics = quick_coverage_check()
    if not metrics:
        print("❌ Unable to generate compliance metrics.")
        sys.exit(1)
    
    # Display key metrics
    print(f"\n📊 COMPLIANCE STATUS:")
    print(f"Overall Coverage: {metrics['overall_coverage']:.1f}%")
    print(f"Target: 95.0%")
    print(f"Gap: {95.0 - metrics['overall_coverage']:.1f} percentage points")
    
    print(f"\n🎯 MODULE COMPLIANCE:")
    print(f"Compliant Modules: {metrics['compliant_modules']}/{metrics['total_modules']}")
    print(f"Compliance Rate: {metrics['compliance_rate']:.1f}%")
    
    # Progress indicator
    progress = int((metrics['overall_coverage'] / 100) * 30)
    target_pos = int((95.0 / 100) * 30)
    bar = "█" * progress + "░" * (30 - progress)
    print(f"\n📈 Progress: [{bar}] {metrics['overall_coverage']:.1f}%")
    
    # Status assessment
    if metrics['overall_coverage'] >= 95.0:
        print("✅ AUDIT COMPLIANCE ACHIEVED!")
    elif metrics['overall_coverage'] >= 90.0:
        print("🔄 TIER 4 - Near compliance")
    elif metrics['overall_coverage'] >= 80.0:
        print("🔄 TIER 3 - Significant progress")
    elif metrics['overall_coverage'] >= 60.0:
        print("🔄 TIER 2 - Moderate coverage")
    else:
        print("🔄 TIER 1 - Initial phase")
    
    # Quick recommendations
    remaining_modules = metrics['total_modules'] - metrics['compliant_modules']
    if remaining_modules > 0:
        print(f"\n💡 Next Steps:")
        print(f"• {remaining_modules} modules need attention")
        print(f"• Run full tracker: python3 audit_compliance_tracker.py")
        print(f"• Focus on high-priority modules first")
    
    print("=" * 50)


if __name__ == "__main__":
    main()