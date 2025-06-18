#!/usr/bin/env python3
"""
Continuous Government Audit Compliance Monitor

Real-time monitoring system that tracks progress across all parallel work.
Generates alerts, updates dashboards, and monitors bottlenecks every 30 minutes.
"""

import subprocess
import json
import os
import sys
import time
import signal
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import threading
import xml.etree.ElementTree as ET


class ContinuousComplianceMonitor:
    """Continuous monitoring system for government audit compliance."""
    
    def __init__(self, update_interval: int = 1800):  # 30 minutes = 1800 seconds
        self.update_interval = update_interval
        self.target_coverage = 95.0
        self.target_compliant_modules = 20
        self.running = False
        self.last_scan_time = None
        self.historical_data = []
        self.alert_thresholds = {
            'coverage_drop': 2.0,  # Alert if coverage drops by 2%
            'stagnation_hours': 2,  # Alert if no progress for 2 hours
            'critical_modules': 5   # Alert if more than 5 critical modules
        }
        
        # Load historical data if available
        self.load_historical_data()
        
    def load_historical_data(self):
        """Load historical compliance data from disk."""
        try:
            if os.path.exists("compliance_history.json"):
                with open("compliance_history.json", "r") as f:
                    self.historical_data = json.load(f)
                print(f"📚 Loaded {len(self.historical_data)} historical data points")
        except Exception as e:
            print(f"⚠️  Could not load historical data: {e}")
            self.historical_data = []
    
    def save_historical_data(self):
        """Save historical compliance data to disk."""
        try:
            # Keep only last 168 data points (1 week at 30-min intervals)
            if len(self.historical_data) > 168:
                self.historical_data = self.historical_data[-168:]
            
            with open("compliance_history.json", "w") as f:
                json.dump(self.historical_data, f, indent=2)
        except Exception as e:
            print(f"⚠️  Could not save historical data: {e}")
    
    def check_disk_space(self) -> bool:
        """Check disk space and return False if critical."""
        try:
            result = subprocess.run(["df", "-h", "/mnt/c"], capture_output=True, text=True)
            for line in result.stdout.split('\n'):
                if '/mnt/c' in line:
                    if any(usage in line for usage in ['98%', '99%']):
                        return False
            return True
        except:
            return True
    
    def parse_coverage_xml(self) -> Optional[Dict]:
        """Parse coverage.xml for quick analysis."""
        if not os.path.exists("coverage.xml"):
            return None
        
        try:
            tree = ET.parse("coverage.xml")
            root = tree.getroot()
            
            # Extract overall metrics
            line_rate = float(root.get("line-rate", "0"))
            overall_pct = line_rate * 100
            total_lines = int(root.get("lines-valid", "0"))
            covered_lines = int(root.get("lines-covered", "0"))
            
            # Extract module-level data
            modules = {}
            compliant_count = 0
            
            for class_elem in root.findall(".//class"):
                filename = class_elem.get("filename")
                if filename:
                    lines = class_elem.findall("lines/line")
                    total_module_lines = len(lines)
                    covered_module_lines = len([line for line in lines if int(line.get("hits", "0")) > 0])
                    
                    if total_module_lines > 0:
                        module_coverage = (covered_module_lines / total_module_lines) * 100
                    else:
                        module_coverage = 100.0
                    
                    modules[filename] = {
                        "coverage": round(module_coverage, 1),
                        "total_lines": total_module_lines,
                        "covered_lines": covered_module_lines,
                        "missing_lines": total_module_lines - covered_module_lines
                    }
                    
                    if module_coverage >= self.target_coverage:
                        compliant_count += 1
            
            return {
                "timestamp": datetime.now().isoformat(),
                "overall_coverage": round(overall_pct, 1),
                "total_lines": total_lines,
                "covered_lines": covered_lines,
                "total_modules": len(modules),
                "compliant_modules": compliant_count,
                "compliance_rate": round((compliant_count / len(modules)) * 100, 1) if modules else 0,
                "modules": modules
            }
            
        except Exception as e:
            print(f"❌ Failed to parse coverage.xml: {e}")
            return None
    
    def detect_alerts(self, current_data: Dict) -> List[str]:
        """Detect conditions that require alerts."""
        alerts = []
        
        if len(self.historical_data) == 0:
            return alerts
        
        # Get last data point for comparison
        last_data = self.historical_data[-1]
        
        # Coverage drop alert
        coverage_change = current_data["overall_coverage"] - last_data["overall_coverage"]
        if coverage_change < -self.alert_thresholds["coverage_drop"]:
            alerts.append(f"🚨 COVERAGE DROP: {coverage_change:.1f}% decrease detected")
        
        # Stagnation alert
        stagnation_threshold = datetime.now() - timedelta(hours=self.alert_thresholds["stagnation_hours"])
        no_progress = True
        for data_point in reversed(self.historical_data[-4:]):  # Check last 2 hours
            point_time = datetime.fromisoformat(data_point["timestamp"])
            if point_time > stagnation_threshold:
                if data_point["overall_coverage"] != current_data["overall_coverage"]:
                    no_progress = False
                    break
        
        if no_progress and len(self.historical_data) >= 4:
            alerts.append(f"⚠️  STAGNATION: No progress for {self.alert_thresholds['stagnation_hours']} hours")
        
        # Critical modules alert
        critical_modules = []
        for module, data in current_data["modules"].items():
            if data["coverage"] < 50.0:  # Less than 50% coverage
                critical_modules.append(module)
        
        if len(critical_modules) > self.alert_thresholds["critical_modules"]:
            alerts.append(f"🔥 CRITICAL MODULES: {len(critical_modules)} modules with <50% coverage")
        
        # Progress velocity alert
        if len(self.historical_data) >= 6:  # Need at least 3 hours of data
            recent_progress = current_data["overall_coverage"] - self.historical_data[-6]["overall_coverage"]
            if recent_progress < 1.0:  # Less than 1% progress in 3 hours
                alerts.append(f"🐌 SLOW PROGRESS: Only {recent_progress:.1f}% improvement in 3 hours")
        
        return alerts
    
    def calculate_velocity(self, current_data: Dict) -> Dict:
        """Calculate progress velocity and ETA estimates."""
        if len(self.historical_data) < 2:
            return {"velocity": 0, "eta_hours": None, "eta_compliance": None}
        
        # Calculate velocity over last hour (2 data points)
        last_hour_data = self.historical_data[-2:]
        if len(last_hour_data) >= 2:
            time_diff = (datetime.fromisoformat(current_data["timestamp"]) - 
                        datetime.fromisoformat(last_hour_data[0]["timestamp"])).total_seconds() / 3600
            coverage_diff = current_data["overall_coverage"] - last_hour_data[0]["overall_coverage"]
            velocity = coverage_diff / time_diff if time_diff > 0 else 0
        else:
            velocity = 0
        
        # Estimate time to reach target
        remaining_coverage = self.target_coverage - current_data["overall_coverage"]
        eta_hours = remaining_coverage / velocity if velocity > 0 else None
        
        # Estimate time to reach module compliance target
        remaining_modules = self.target_compliant_modules - current_data["compliant_modules"]
        if len(self.historical_data) >= 4:
            module_velocity = (current_data["compliant_modules"] - self.historical_data[-4]["compliant_modules"]) / 2
            eta_compliance = remaining_modules / module_velocity if module_velocity > 0 else None
        else:
            eta_compliance = None
        
        return {
            "velocity": round(velocity, 2),
            "eta_hours": round(eta_hours, 1) if eta_hours else None,
            "eta_compliance": round(eta_compliance, 1) if eta_compliance else None
        }
    
    def identify_bottlenecks(self, current_data: Dict) -> List[str]:
        """Identify potential bottlenecks in the compliance process."""
        bottlenecks = []
        modules = current_data["modules"]
        
        # Identify modules with no progress
        if len(self.historical_data) >= 2:
            last_modules = self.historical_data[-1]["modules"]
            stagnant_modules = []
            
            for module, data in modules.items():
                if module in last_modules:
                    if data["coverage"] == last_modules[module]["coverage"]:
                        stagnant_modules.append(module)
            
            if len(stagnant_modules) > 10:
                bottlenecks.append(f"🔒 {len(stagnant_modules)} modules showing no progress")
        
        # Identify high-effort modules
        high_effort_modules = [m for m, d in modules.items() if d["missing_lines"] > 100]
        if len(high_effort_modules) > 5:
            bottlenecks.append(f"💪 {len(high_effort_modules)} modules require major effort (>100 lines)")
        
        # Check for concentration of work
        low_coverage_modules = [m for m, d in modules.items() if d["coverage"] < 20.0]
        if len(low_coverage_modules) > len(modules) * 0.7:  # More than 70% of modules
            bottlenecks.append(f"📊 {len(low_coverage_modules)} modules need initial coverage work")
        
        return bottlenecks
    
    def generate_priority_recommendations(self, current_data: Dict) -> List[str]:
        """Generate priority recommendations based on current state."""
        recommendations = []
        modules = current_data["modules"]
        
        # Quick wins (modules close to compliance)
        quick_wins = []
        for module, data in modules.items():
            gap = self.target_coverage - data["coverage"]
            if 0 < gap <= 10 and data["missing_lines"] <= 20:
                quick_wins.append((module, gap, data["missing_lines"]))
        
        quick_wins.sort(key=lambda x: (x[1], x[2]))  # Sort by gap, then effort
        
        if quick_wins:
            recommendations.append(f"🎯 QUICK WINS: Focus on {quick_wins[0][0]} (gap: {quick_wins[0][1]:.1f}%, {quick_wins[0][2]} lines)")
        
        # High-impact modules
        high_impact = []
        for module, data in modules.items():
            if data["total_lines"] > 50 and data["coverage"] < 50:
                impact_score = data["total_lines"] * (100 - data["coverage"])
                high_impact.append((module, impact_score, data["coverage"]))
        
        if high_impact:
            high_impact.sort(key=lambda x: x[1], reverse=True)
            recommendations.append(f"🚀 HIGH IMPACT: Prioritize {high_impact[0][0]} (impact score: {high_impact[0][1]:.0f})")
        
        # Balanced approach recommendation
        medium_modules = [m for m, d in modules.items() if 20 <= d["coverage"] < 80 and d["missing_lines"] <= 50]
        if len(medium_modules) >= 3:
            recommendations.append(f"⚖️  BALANCED: Work on {len(medium_modules)} medium-complexity modules in parallel")
        
        return recommendations[:3]  # Top 3 recommendations
    
    def generate_dashboard(self, current_data: Dict):
        """Generate and display the real-time compliance dashboard."""
        os.system('clear')  # Clear screen for fresh display
        
        print("🏛️" + "="*78 + "🏛️")
        print("   CONTINUOUS GOVERNMENT AUDIT COMPLIANCE MONITOR")
        print("🏛️" + "="*78 + "🏛️")
        
        # Header with key metrics
        now = datetime.now()
        print(f"🕐 Last Update: {now.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"📊 Overall Coverage: {current_data['overall_coverage']}% | Target: {self.target_coverage}%")
        print(f"🎯 Compliant Modules: {current_data['compliant_modules']}/{current_data['total_modules']} | Target: {self.target_compliant_modules}+")
        
        # Progress indicators
        overall_progress = int((current_data['overall_coverage'] / 100) * 50)
        compliance_progress = int((current_data['compliant_modules'] / self.target_compliant_modules) * 50)
        
        print(f"\n📈 COVERAGE PROGRESS:")
        bar1 = "█" * overall_progress + "░" * (50 - overall_progress)
        print(f"[{bar1}] {current_data['overall_coverage']}%")
        
        print(f"\n📈 MODULE COMPLIANCE:")
        bar2 = "█" * min(compliance_progress, 50) + "░" * (50 - min(compliance_progress, 50))
        print(f"[{bar2}] {current_data['compliant_modules']}/{self.target_compliant_modules}")
        
        # Velocity and ETA
        velocity = self.calculate_velocity(current_data)
        print(f"\n⚡ VELOCITY & ETA:")
        if velocity["velocity"] > 0:
            print(f"• Progress Rate: {velocity['velocity']:.2f}% per hour")
            if velocity["eta_hours"]:
                eta_time = now + timedelta(hours=velocity["eta_hours"])
                print(f"• ETA to 95%: {velocity['eta_hours']:.1f} hours ({eta_time.strftime('%m-%d %H:%M')})")
        else:
            print("• Progress Rate: Stagnant")
        
        # Alerts
        alerts = self.detect_alerts(current_data)
        if alerts:
            print(f"\n🚨 ALERTS ({len(alerts)}):")
            for alert in alerts[:3]:  # Show top 3 alerts
                print(f"  {alert}")
        
        # Bottlenecks
        bottlenecks = self.identify_bottlenecks(current_data)
        if bottlenecks:
            print(f"\n🔍 BOTTLENECKS:")
            for bottleneck in bottlenecks[:2]:  # Show top 2 bottlenecks
                print(f"  {bottleneck}")
        
        # Priority recommendations
        recommendations = self.generate_priority_recommendations(current_data)
        if recommendations:
            print(f"\n💡 PRIORITY ACTIONS:")
            for i, rec in enumerate(recommendations, 1):
                print(f"  {i}. {rec}")
        
        # Top modules needing attention
        print(f"\n📋 TOP PRIORITY MODULES:")
        print("-" * 80)
        priority_modules = []
        for module, data in current_data["modules"].items():
            if data["coverage"] < self.target_coverage:
                gap = self.target_coverage - data["coverage"]
                priority_score = gap + (data["missing_lines"] / 10)
                priority_modules.append((module, data["coverage"], gap, data["missing_lines"], priority_score))
        
        priority_modules.sort(key=lambda x: x[4], reverse=True)
        
        print(f"{'Module':<25} {'Coverage':<8} {'Gap':<6} {'Missing':<8} {'Priority':<8}")
        print("-" * 80)
        for module, coverage, gap, missing, priority in priority_modules[:8]:
            module_name = Path(module).stem if '/' in module else module
            print(f"{module_name:<25} {coverage:>6.1f}% {gap:>5.1f}% {missing:>6d} {priority:>7.1f}")
        
        # System status
        print(f"\n🔧 SYSTEM STATUS:")
        print(f"• Next scan in: {self.update_interval // 60} minutes")
        print(f"• Historical data points: {len(self.historical_data)}")
        print(f"• Monitoring since: {self.historical_data[0]['timestamp'][:16] if self.historical_data else 'First run'}")
        
        print("🏛️" + "="*78 + "🏛️")
        print("Press Ctrl+C to stop monitoring")
        print()
    
    def run_scan(self) -> Optional[Dict]:
        """Run a single compliance scan."""
        if not self.check_disk_space():
            print("🛑 Critical disk space - skipping scan")
            return None
        
        print("🔍 Running compliance scan...")
        current_data = self.parse_coverage_xml()
        
        if current_data:
            self.historical_data.append(current_data)
            self.save_historical_data()
            self.last_scan_time = datetime.now()
            return current_data
        else:
            print("❌ Failed to generate compliance data")
            return None
    
    def start_monitoring(self):
        """Start continuous monitoring loop."""
        self.running = True
        print("🚀 Starting continuous compliance monitoring...")
        print(f"📅 Update interval: {self.update_interval // 60} minutes")
        
        # Set up signal handler for graceful shutdown
        def signal_handler(sig, frame):
            print("\n🛑 Stopping compliance monitor...")
            self.running = False
        
        signal.signal(signal.SIGINT, signal_handler)
        
        # Initial scan
        current_data = self.run_scan()
        if current_data:
            self.generate_dashboard(current_data)
        
        # Monitoring loop
        while self.running:
            try:
                time.sleep(self.update_interval)
                
                if not self.running:
                    break
                
                current_data = self.run_scan()
                if current_data:
                    self.generate_dashboard(current_data)
                
            except KeyboardInterrupt:
                print("\n🛑 Stopping compliance monitor...")
                break
            except Exception as e:
                print(f"❌ Error in monitoring loop: {e}")
                time.sleep(60)  # Wait 1 minute before retrying
        
        print("✅ Compliance monitoring stopped")
    
    def generate_summary_report(self):
        """Generate a summary report of current compliance status."""
        current_data = self.parse_coverage_xml()
        if not current_data:
            print("❌ Cannot generate summary - no coverage data available")
            return
        
        print("\n📊 COMPLIANCE SUMMARY REPORT")
        print("=" * 60)
        print(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Overall Coverage: {current_data['overall_coverage']}%")
        print(f"Target: {self.target_coverage}%")
        print(f"Gap: {self.target_coverage - current_data['overall_coverage']:.1f} percentage points")
        print(f"Compliant Modules: {current_data['compliant_modules']}/{current_data['total_modules']}")
        print(f"Compliance Rate: {current_data['compliance_rate']}%")
        
        if self.historical_data:
            # Show progress over time
            print(f"\n📈 PROGRESS TREND (Last 24 Hours):")
            recent_data = [d for d in self.historical_data 
                          if datetime.fromisoformat(d['timestamp']) > datetime.now() - timedelta(hours=24)]
            
            if len(recent_data) >= 2:
                coverage_change = current_data['overall_coverage'] - recent_data[0]['overall_coverage']
                module_change = current_data['compliant_modules'] - recent_data[0]['compliant_modules']
                print(f"Coverage Change: {coverage_change:+.1f}%")
                print(f"New Compliant Modules: {module_change:+d}")
            else:
                print("Insufficient historical data for trend analysis")
        
        print("=" * 60)


def main():
    """Main entry point for continuous compliance monitoring."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Continuous Government Audit Compliance Monitor")
    parser.add_argument("--interval", type=int, default=1800, help="Update interval in seconds (default: 1800 = 30 minutes)")
    parser.add_argument("--summary", action="store_true", help="Generate summary report only")
    parser.add_argument("--once", action="store_true", help="Run single scan and exit")
    
    args = parser.parse_args()
    
    monitor = ContinuousComplianceMonitor(update_interval=args.interval)
    
    if args.summary:
        monitor.generate_summary_report()
    elif args.once:
        current_data = monitor.run_scan()
        if current_data:
            monitor.generate_dashboard(current_data)
    else:
        monitor.start_monitoring()


if __name__ == "__main__":
    main()