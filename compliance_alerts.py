#!/usr/bin/env python3
"""
Government Audit Compliance Alert System

Automated alert system for monitoring compliance progress and identifying
critical issues that require immediate attention.
"""

import json
import os
import smtplib
import sys
from datetime import datetime, timedelta
from email.mime.text import MimeText
from email.mime.multipart import MimeMultipart
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import xml.etree.ElementTree as ET


class ComplianceAlertSystem:
    """Automated alert system for compliance monitoring."""
    
    def __init__(self):
        self.alert_config = {
            'coverage_drop_threshold': 2.0,        # Alert if coverage drops by 2%
            'stagnation_hours': 3,                 # Alert if no progress for 3 hours
            'critical_coverage_threshold': 30.0,   # Alert if module coverage drops below 30%
            'velocity_threshold': 0.5,             # Alert if velocity drops below 0.5% per hour
            'module_regression_count': 3,          # Alert if 3+ modules regress
            'eta_extension_hours': 12,             # Alert if ETA extends by 12+ hours
        }
        
        self.alert_history = []
        self.load_alert_history()
        
        # Load compliance history for analysis
        self.compliance_history = []
        self.load_compliance_history()
    
    def load_alert_history(self):
        """Load alert history from disk."""
        try:
            if os.path.exists("alert_history.json"):
                with open("alert_history.json", "r") as f:
                    self.alert_history = json.load(f)
        except Exception as e:
            print(f"⚠️  Could not load alert history: {e}")
            self.alert_history = []
    
    def save_alert_history(self):
        """Save alert history to disk."""
        try:
            # Keep only last 7 days of alerts
            cutoff_time = datetime.now() - timedelta(days=7)
            self.alert_history = [
                alert for alert in self.alert_history
                if datetime.fromisoformat(alert['timestamp']) > cutoff_time
            ]
            
            with open("alert_history.json", "w") as f:
                json.dump(self.alert_history, f, indent=2)
        except Exception as e:
            print(f"⚠️  Could not save alert history: {e}")
    
    def load_compliance_history(self):
        """Load compliance history for analysis."""
        try:
            if os.path.exists("compliance_history.json"):
                with open("compliance_history.json", "r") as f:
                    self.compliance_history = json.load(f)
        except Exception as e:
            print(f"⚠️  Could not load compliance history: {e}")
            self.compliance_history = []
    
    def get_current_compliance_data(self) -> Optional[Dict]:
        """Get current compliance data from coverage.xml."""
        if not os.path.exists("coverage.xml"):
            return None
        
        try:
            tree = ET.parse("coverage.xml")
            root = tree.getroot()
            
            # Extract overall metrics
            line_rate = float(root.get("line-rate", "0"))
            overall_pct = line_rate * 100
            
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
                    
                    if module_coverage >= 95.0:
                        compliant_count += 1
            
            return {
                "timestamp": datetime.now().isoformat(),
                "overall_coverage": round(overall_pct, 1),
                "total_modules": len(modules),
                "compliant_modules": compliant_count,
                "compliance_rate": round((compliant_count / len(modules)) * 100, 1) if modules else 0,
                "modules": modules
            }
            
        except Exception as e:
            print(f"❌ Failed to parse coverage data: {e}")
            return None
    
    def detect_coverage_drop_alert(self, current_data: Dict) -> Optional[Dict]:
        """Detect significant coverage drops."""
        if len(self.compliance_history) < 2:
            return None
        
        last_coverage = self.compliance_history[-1]["overall_coverage"]
        coverage_drop = last_coverage - current_data["overall_coverage"]
        
        if coverage_drop >= self.alert_config['coverage_drop_threshold']:
            return {
                "type": "COVERAGE_DROP",
                "severity": "HIGH",
                "message": f"Coverage dropped by {coverage_drop:.1f}% from {last_coverage:.1f}% to {current_data['overall_coverage']:.1f}%",
                "details": {
                    "previous_coverage": last_coverage,
                    "current_coverage": current_data["overall_coverage"],
                    "drop_amount": coverage_drop
                }
            }
        return None
    
    def detect_stagnation_alert(self, current_data: Dict) -> Optional[Dict]:
        """Detect periods of no progress."""
        if len(self.compliance_history) < 6:  # Need at least 3 hours of data (6 x 30min intervals)
            return None
        
        # Check if coverage has remained the same for the stagnation period
        stagnation_start_index = -1 * (self.alert_config['stagnation_hours'] * 2)  # 2 intervals per hour
        recent_history = self.compliance_history[stagnation_start_index:]
        
        if all(data["overall_coverage"] == current_data["overall_coverage"] for data in recent_history):
            return {
                "type": "STAGNATION",
                "severity": "MEDIUM",
                "message": f"No progress for {self.alert_config['stagnation_hours']} hours at {current_data['overall_coverage']:.1f}% coverage",
                "details": {
                    "stagnation_hours": self.alert_config['stagnation_hours'],
                    "stuck_coverage": current_data["overall_coverage"]
                }
            }
        return None
    
    def detect_critical_module_alert(self, current_data: Dict) -> Optional[Dict]:
        """Detect modules with critically low coverage."""
        critical_modules = []
        
        for module, data in current_data["modules"].items():
            if data["coverage"] < self.alert_config['critical_coverage_threshold']:
                critical_modules.append({
                    "module": module,
                    "coverage": data["coverage"]
                })
        
        if len(critical_modules) > 5:  # More than 5 critical modules
            return {
                "type": "CRITICAL_MODULES",
                "severity": "HIGH",
                "message": f"{len(critical_modules)} modules with coverage below {self.alert_config['critical_coverage_threshold']}%",
                "details": {
                    "critical_count": len(critical_modules),
                    "threshold": self.alert_config['critical_coverage_threshold'],
                    "modules": critical_modules[:10]  # Show top 10
                }
            }
        return None
    
    def detect_velocity_alert(self, current_data: Dict) -> Optional[Dict]:
        """Detect slow progress velocity."""
        if len(self.compliance_history) < 4:  # Need at least 2 hours of data
            return None
        
        # Calculate velocity over last 2 hours
        two_hours_ago_data = self.compliance_history[-4]
        time_diff_hours = 2.0  # 4 intervals * 30 minutes = 2 hours
        coverage_diff = current_data["overall_coverage"] - two_hours_ago_data["overall_coverage"]
        velocity = coverage_diff / time_diff_hours
        
        if velocity < self.alert_config['velocity_threshold']:
            return {
                "type": "SLOW_VELOCITY",
                "severity": "MEDIUM",
                "message": f"Progress velocity is {velocity:.2f}% per hour (threshold: {self.alert_config['velocity_threshold']}%)",
                "details": {
                    "velocity": velocity,
                    "threshold": self.alert_config['velocity_threshold'],
                    "time_period_hours": time_diff_hours
                }
            }
        return None
    
    def detect_module_regression_alert(self, current_data: Dict) -> Optional[Dict]:
        """Detect modules that have regressed in coverage."""
        if len(self.compliance_history) < 1:
            return None
        
        last_data = self.compliance_history[-1]
        regressed_modules = []
        
        for module, current_module_data in current_data["modules"].items():
            if module in last_data["modules"]:
                last_coverage = last_data["modules"][module]["coverage"]
                current_coverage = current_module_data["coverage"]
                
                if current_coverage < last_coverage - 1.0:  # Regressed by more than 1%
                    regressed_modules.append({
                        "module": module,
                        "previous_coverage": last_coverage,
                        "current_coverage": current_coverage,
                        "regression": last_coverage - current_coverage
                    })
        
        if len(regressed_modules) >= self.alert_config['module_regression_count']:
            return {
                "type": "MODULE_REGRESSION",
                "severity": "HIGH",
                "message": f"{len(regressed_modules)} modules have regressed in coverage",
                "details": {
                    "regressed_count": len(regressed_modules),
                    "modules": regressed_modules
                }
            }
        return None
    
    def detect_eta_extension_alert(self, current_data: Dict) -> Optional[Dict]:
        """Detect if ETA to compliance has extended significantly."""
        if len(self.compliance_history) < 12:  # Need at least 6 hours of data
            return None
        
        # Calculate current velocity
        six_hours_ago_data = self.compliance_history[-12]
        coverage_diff = current_data["overall_coverage"] - six_hours_ago_data["overall_coverage"]
        velocity = coverage_diff / 6.0  # 6 hours
        
        if velocity <= 0:
            return None  # No progress, will be caught by stagnation alert
        
        # Calculate current ETA
        remaining_coverage = 95.0 - current_data["overall_coverage"]
        current_eta_hours = remaining_coverage / velocity
        
        # Calculate what the ETA was 6 hours ago
        old_remaining = 95.0 - six_hours_ago_data["overall_coverage"]
        old_eta_hours = old_remaining / velocity if velocity > 0 else float('inf')
        
        # Check if ETA has extended significantly
        eta_extension = current_eta_hours - (old_eta_hours - 6)  # Subtract 6 hours that have passed
        
        if eta_extension > self.alert_config['eta_extension_hours']:
            return {
                "type": "ETA_EXTENSION",
                "severity": "MEDIUM",
                "message": f"ETA to compliance extended by {eta_extension:.1f} hours (now {current_eta_hours:.1f} hours)",
                "details": {
                    "current_eta_hours": current_eta_hours,
                    "extension_hours": eta_extension,
                    "velocity": velocity
                }
            }
        return None
    
    def check_all_alerts(self, current_data: Dict) -> List[Dict]:
        """Check all alert conditions and return list of active alerts."""
        alerts = []
        
        # Check each alert type
        alert_checks = [
            self.detect_coverage_drop_alert,
            self.detect_stagnation_alert,
            self.detect_critical_module_alert,
            self.detect_velocity_alert,
            self.detect_module_regression_alert,
            self.detect_eta_extension_alert
        ]
        
        for check_func in alert_checks:
            try:
                alert = check_func(current_data)
                if alert:
                    alert["timestamp"] = datetime.now().isoformat()
                    alerts.append(alert)
            except Exception as e:
                print(f"❌ Error in alert check {check_func.__name__}: {e}")
        
        return alerts
    
    def should_send_alert(self, alert: Dict) -> bool:
        """Determine if an alert should be sent (avoid spam)."""
        alert_type = alert["type"]
        
        # Check if we've sent this type of alert recently
        recent_threshold = datetime.now() - timedelta(hours=2)
        recent_alerts = [
            a for a in self.alert_history
            if a["type"] == alert_type and datetime.fromisoformat(a["timestamp"]) > recent_threshold
        ]
        
        # Don't send duplicate alerts within 2 hours
        if recent_alerts:
            return False
        
        return True
    
    def format_alert_message(self, alerts: List[Dict]) -> str:
        """Format alerts into a readable message."""
        if not alerts:
            return ""
        
        message = "🚨 GOVERNMENT AUDIT COMPLIANCE ALERT\n"
        message += "=" * 50 + "\n"
        message += f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        
        # Group alerts by severity
        high_alerts = [a for a in alerts if a["severity"] == "HIGH"]
        medium_alerts = [a for a in alerts if a["severity"] == "MEDIUM"]
        
        if high_alerts:
            message += "🔥 HIGH SEVERITY ALERTS:\n"
            for i, alert in enumerate(high_alerts, 1):
                message += f"{i}. [{alert['type']}] {alert['message']}\n"
            message += "\n"
        
        if medium_alerts:
            message += "⚠️  MEDIUM SEVERITY ALERTS:\n"
            for i, alert in enumerate(medium_alerts, 1):
                message += f"{i}. [{alert['type']}] {alert['message']}\n"
            message += "\n"
        
        message += "🔗 Actions Required:\n"
        message += "• Review compliance dashboard\n"
        message += "• Check module priorities\n"
        message += "• Investigate bottlenecks\n"
        message += "• Run: python3 continuous_compliance_monitor.py --once\n"
        
        return message
    
    def send_console_alert(self, alerts: List[Dict]):
        """Send alerts to console."""
        if not alerts:
            return
        
        print("\n" + "🚨" * 20)
        print(self.format_alert_message(alerts))
        print("🚨" * 20 + "\n")
    
    def log_alerts(self, alerts: List[Dict]):
        """Log alerts to history and file."""
        for alert in alerts:
            self.alert_history.append(alert)
        
        if alerts:
            self.save_alert_history()
            
            # Also append to alert log file
            try:
                with open("compliance_alerts.log", "a") as f:
                    for alert in alerts:
                        f.write(f"{alert['timestamp']} [{alert['severity']}] {alert['type']}: {alert['message']}\n")
            except Exception as e:
                print(f"⚠️  Could not write to alert log: {e}")
    
    def generate_alert_summary(self) -> str:
        """Generate a summary of recent alerts."""
        if not self.alert_history:
            return "No alerts in history."
        
        # Count alerts by type in last 24 hours
        recent_threshold = datetime.now() - timedelta(hours=24)
        recent_alerts = [
            a for a in self.alert_history
            if datetime.fromisoformat(a["timestamp"]) > recent_threshold
        ]
        
        if not recent_alerts:
            return "No alerts in last 24 hours."
        
        alert_counts = {}
        for alert in recent_alerts:
            alert_type = alert["type"]
            alert_counts[alert_type] = alert_counts.get(alert_type, 0) + 1
        
        summary = f"📊 ALERT SUMMARY (Last 24 Hours): {len(recent_alerts)} total alerts\n"
        for alert_type, count in sorted(alert_counts.items()):
            summary += f"• {alert_type}: {count}\n"
        
        return summary
    
    def run_alert_check(self):
        """Run a single alert check cycle."""
        print("🔍 Running compliance alert check...")
        
        current_data = self.get_current_compliance_data()
        if not current_data:
            print("❌ Cannot run alert check - no compliance data available")
            return
        
        # Check all alerts
        alerts = self.check_all_alerts(current_data)
        
        # Filter out alerts we shouldn't send
        actionable_alerts = [alert for alert in alerts if self.should_send_alert(alert)]
        
        if actionable_alerts:
            print(f"🚨 {len(actionable_alerts)} active alerts detected!")
            self.send_console_alert(actionable_alerts)
            self.log_alerts(actionable_alerts)
        else:
            print("✅ No active alerts")
        
        # Always log all alerts for history
        if alerts:
            self.log_alerts(alerts)
        
        return actionable_alerts
    
    def run_continuous_alerts(self, check_interval: int = 900):  # 15 minutes
        """Run continuous alert monitoring."""
        print(f"🚀 Starting continuous alert monitoring (every {check_interval//60} minutes)")
        
        import time
        import signal
        
        running = True
        
        def signal_handler(sig, frame):
            nonlocal running
            print("\n🛑 Stopping alert monitoring...")
            running = False
        
        signal.signal(signal.SIGINT, signal_handler)
        
        while running:
            try:
                self.run_alert_check()
                time.sleep(check_interval)
            except KeyboardInterrupt:
                break
            except Exception as e:
                print(f"❌ Error in alert monitoring: {e}")
                time.sleep(60)  # Wait 1 minute before retrying
        
        print("✅ Alert monitoring stopped")


def main():
    """Main entry point for compliance alert system."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Government Audit Compliance Alert System")
    parser.add_argument("--check", action="store_true", help="Run single alert check")
    parser.add_argument("--continuous", action="store_true", help="Run continuous alert monitoring")
    parser.add_argument("--summary", action="store_true", help="Show alert summary")
    parser.add_argument("--interval", type=int, default=900, help="Check interval in seconds (default: 900 = 15 minutes)")
    
    args = parser.parse_args()
    
    alert_system = ComplianceAlertSystem()
    
    if args.summary:
        print(alert_system.generate_alert_summary())
    elif args.check:
        alert_system.run_alert_check()
    elif args.continuous:
        alert_system.run_continuous_alerts(args.interval)
    else:
        # Default: run single check
        alert_system.run_alert_check()


if __name__ == "__main__":
    main()