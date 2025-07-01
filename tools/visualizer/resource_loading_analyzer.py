#!/usr/bin/env python3
"""
Comprehensive Resource Loading and Cache Analysis Tool

This tool performs deep analysis of browser caching and resource loading
issues that may be causing the web interface to show wrong content.
"""

import os
import sys
import json
import time
import requests
import hashlib
from pathlib import Path
from datetime import datetime
from urllib.parse import urljoin
import subprocess

class ResourceLoadingAnalyzer:
    """Comprehensive analysis of resource loading and caching issues"""
    
    def __init__(self, base_url="http://localhost:5000"):
        self.base_url = base_url
        self.results = {
            "timestamp": datetime.now().isoformat(),
            "server_status": {},
            "static_files": {},
            "external_resources": {},
            "cache_headers": {},
            "resource_integrity": {},
            "loading_order": {},
            "potential_issues": []
        }
        
    def analyze_server_status(self):
        """Check if the server is running and responsive"""
        print("🔍 Analyzing server status...")
        
        try:
            start_time = time.time()
            response = requests.get(self.base_url, timeout=5)
            end_time = time.time()
            
            self.results["server_status"] = {
                "running": True,
                "status_code": response.status_code,
                "response_time_ms": round((end_time - start_time) * 1000, 2),
                "server_header": response.headers.get("Server", "Unknown"),
                "content_type": response.headers.get("Content-Type", "Unknown"),
                "content_length": len(response.content)
            }
            
            print(f"✅ Server running: {response.status_code} ({self.results['server_status']['response_time_ms']}ms)")
            
        except Exception as e:
            self.results["server_status"] = {
                "running": False,
                "error": str(e)
            }
            print(f"❌ Server not responding: {e}")
            
    def analyze_static_files(self):
        """Analyze all static files and their loading behavior"""
        print("🔍 Analyzing static file serving...")
        
        # Define critical static files
        static_files = [
            "visualizer.js",
            "css/discord-chat.css",
            "style.css",
            "js/chat-components.js", 
            "js/discord-chat.js",
            "js/project-manager.js",
            "js/mobile-enhancements.js",
            "js/ui-enhancements.js",
            "js/accessibility-enhancements.js",
            "js/chat-init-failsafe.js",
            "force-visualizer-mode.js",
            "emergency-modal-fix.css",
            "layout-fix.css"
        ]
        
        for file_path in static_files:
            file_url = urljoin(self.base_url + "/static/", file_path)
            file_info = self._analyze_static_file(file_url, file_path)
            self.results["static_files"][file_path] = file_info
            
            # Check for potential issues
            if file_info.get("status_code") != 200:
                self.results["potential_issues"].append({
                    "type": "missing_static_file",
                    "file": file_path,
                    "status": file_info.get("status_code", "error"),
                    "severity": "high"
                })
                
            if file_info.get("cache_control_effective", False):
                self.results["potential_issues"].append({
                    "type": "ineffective_cache_control",
                    "file": file_path,
                    "cache_control": file_info.get("cache_control"),
                    "severity": "medium"
                })
                
    def _analyze_static_file(self, url, file_path):
        """Analyze a single static file"""
        try:
            # Make initial request
            response = requests.get(url, timeout=5)
            
            # Calculate content hash for integrity checking
            content_hash = hashlib.sha256(response.content).hexdigest()[:16]
            
            # Check if file exists locally to compare
            local_path = Path(__file__).parent / "static" / file_path
            local_hash = None
            local_modified = None
            
            if local_path.exists():
                with open(local_path, 'rb') as f:
                    local_hash = hashlib.sha256(f.read()).hexdigest()[:16]
                local_modified = local_path.stat().st_mtime
                
            # Analyze cache headers
            cache_control = response.headers.get("Cache-Control", "")
            pragma = response.headers.get("Pragma", "")
            expires = response.headers.get("Expires", "")
            etag = response.headers.get("ETag", "")
            last_modified = response.headers.get("Last-Modified", "")
            
            # Test cache effectiveness by making second request
            time.sleep(0.1)  # Small delay
            response2 = requests.get(url, timeout=5)
            cache_effective = (response.content == response2.content and 
                             response.headers.get("ETag") == response2.headers.get("ETag"))
            
            file_info = {
                "status_code": response.status_code,
                "content_length": len(response.content),
                "content_hash": content_hash,
                "local_hash": local_hash,
                "local_modified": local_modified,
                "hash_match": content_hash == local_hash if local_hash else None,
                "content_type": response.headers.get("Content-Type"),
                "cache_control": cache_control,
                "pragma": pragma,
                "expires": expires,
                "etag": etag,
                "last_modified": last_modified,
                "cache_control_effective": "no-cache" in cache_control.lower() or "no-store" in cache_control.lower(),
                "cache_test_consistent": cache_effective
            }
            
            status = "✅" if response.status_code == 200 else "❌"
            hash_status = "✅" if file_info["hash_match"] else "⚠️" if local_hash else "❓"
            print(f"  {status} {file_path} ({response.status_code}) {hash_status}")
            
            return file_info
            
        except Exception as e:
            error_info = {
                "status_code": "error",
                "error": str(e)
            }
            print(f"  ❌ {file_path}: {e}")
            return error_info
            
    def analyze_external_resources(self):
        """Analyze external CDN resources"""
        print("🔍 Analyzing external resources...")
        
        external_resources = [
            "https://cdn.socket.io/4.7.2/socket.io.min.js",
            "https://cdn.jsdelivr.net/npm/mermaid@10.4.0/dist/mermaid.min.js"
        ]
        
        for url in external_resources:
            resource_name = url.split("/")[-1]
            
            try:
                start_time = time.time()
                response = requests.get(url, timeout=10)
                end_time = time.time()
                
                self.results["external_resources"][resource_name] = {
                    "url": url,
                    "status_code": response.status_code,
                    "response_time_ms": round((end_time - start_time) * 1000, 2),
                    "content_length": len(response.content),
                    "content_type": response.headers.get("Content-Type"),
                    "cache_control": response.headers.get("Cache-Control", ""),
                    "cdn_headers": {
                        "cf-ray": response.headers.get("cf-ray"),
                        "cf-cache-status": response.headers.get("cf-cache-status"),
                        "x-cache": response.headers.get("x-cache"),
                        "server": response.headers.get("server")
                    }
                }
                
                print(f"  ✅ {resource_name} ({response.status_code}, {self.results['external_resources'][resource_name]['response_time_ms']}ms)")
                
                # Check for CDN issues
                if response.status_code != 200:
                    self.results["potential_issues"].append({
                        "type": "external_resource_failure",
                        "resource": resource_name,
                        "url": url,
                        "status": response.status_code,
                        "severity": "high"
                    })
                    
                if self.results["external_resources"][resource_name]["response_time_ms"] > 5000:
                    self.results["potential_issues"].append({
                        "type": "slow_external_resource",
                        "resource": resource_name,
                        "response_time": self.results["external_resources"][resource_name]["response_time_ms"],
                        "severity": "medium"
                    })
                    
            except Exception as e:
                self.results["external_resources"][resource_name] = {
                    "url": url,
                    "error": str(e)
                }
                print(f"  ❌ {resource_name}: {e}")
                
                self.results["potential_issues"].append({
                    "type": "external_resource_error",
                    "resource": resource_name,
                    "url": url,
                    "error": str(e),
                    "severity": "critical"
                })
                
    def analyze_resource_loading_order(self):
        """Analyze the loading order of resources in the HTML"""
        print("🔍 Analyzing resource loading order...")
        
        try:
            response = requests.get(self.base_url, timeout=5)
            html_content = response.text
            
            # Extract script and link tags in order
            import re
            
            # Find all script and link tags
            script_pattern = r'<script[^>]*src=["\']([^"\']*)["\'][^>]*>'
            link_pattern = r'<link[^>]*href=["\']([^"\']*)["\'][^>]*>'
            
            scripts = re.findall(script_pattern, html_content)
            stylesheets = re.findall(link_pattern, html_content)
            
            self.results["loading_order"] = {
                "external_scripts_first": [],
                "local_scripts": [],
                "stylesheets": [],
                "script_count": len(scripts),
                "stylesheet_count": len(stylesheets)
            }
            
            for script in scripts:
                if script.startswith('http'):
                    self.results["loading_order"]["external_scripts_first"].append(script)
                else:
                    self.results["loading_order"]["local_scripts"].append(script)
                    
            self.results["loading_order"]["stylesheets"] = stylesheets
            
            print(f"  📄 Found {len(scripts)} scripts, {len(stylesheets)} stylesheets")
            
            # Check for potential loading order issues
            if len(self.results["loading_order"]["local_scripts"]) > 8:
                self.results["potential_issues"].append({
                    "type": "too_many_scripts",
                    "count": len(self.results["loading_order"]["local_scripts"]),
                    "recommendation": "Consider bundling scripts to reduce HTTP requests",
                    "severity": "low"
                })
                
        except Exception as e:
            self.results["loading_order"]["error"] = str(e)
            print(f"  ❌ Error analyzing loading order: {e}")
            
    def test_browser_cache_scenarios(self):
        """Test various browser cache scenarios"""
        print("🔍 Testing browser cache scenarios...")
        
        # Test cache busting
        test_file = "/static/visualizer.js"
        base_url = self.base_url + test_file
        
        scenarios = {
            "normal_request": base_url,
            "cache_buster_timestamp": f"{base_url}?t={int(time.time())}",
            "cache_buster_random": f"{base_url}?v={hashlib.md5(str(time.time()).encode()).hexdigest()[:8]}",
            "no_cache_header": base_url
        }
        
        cache_test_results = {}
        
        for scenario, url in scenarios.items():
            try:
                headers = {}
                if scenario == "no_cache_header":
                    headers["Cache-Control"] = "no-cache"
                    headers["Pragma"] = "no-cache"
                    
                response = requests.get(url, headers=headers, timeout=5)
                
                cache_test_results[scenario] = {
                    "status_code": response.status_code,
                    "content_length": len(response.content),
                    "response_headers": dict(response.headers),
                    "content_hash": hashlib.sha256(response.content).hexdigest()[:16]
                }
                
                print(f"  ✅ {scenario}: {response.status_code}")
                
            except Exception as e:
                cache_test_results[scenario] = {"error": str(e)}
                print(f"  ❌ {scenario}: {e}")
                
        self.results["cache_test_results"] = cache_test_results
        
        # Check if all cache busting methods return same content
        hashes = [result.get("content_hash") for result in cache_test_results.values() if "content_hash" in result]
        if len(set(hashes)) > 1:
            self.results["potential_issues"].append({
                "type": "inconsistent_cache_responses",
                "details": "Different cache busting methods returned different content",
                "severity": "high"
            })
            
    def detect_service_worker_issues(self):
        """Detect potential service worker caching issues"""
        print("🔍 Checking for service worker interference...")
        
        try:
            # Check if there's a service worker registration
            response = requests.get(self.base_url, timeout=5)
            html_content = response.text
            
            # Look for service worker registration
            sw_patterns = [
                r'navigator\.serviceWorker\.register',
                r'service-worker\.js',
                r'sw\.js',
                r'serviceworker\.js'
            ]
            
            sw_found = False
            for pattern in sw_patterns:
                if re.search(pattern, html_content, re.IGNORECASE):
                    sw_found = True
                    break
                    
            self.results["service_worker"] = {
                "detected": sw_found,
                "patterns_found": [p for p in sw_patterns if re.search(p, html_content, re.IGNORECASE)]
            }
            
            if sw_found:
                self.results["potential_issues"].append({
                    "type": "service_worker_detected",
                    "details": "Service worker may be caching resources aggressively",
                    "recommendation": "Clear service worker cache or disable for development",
                    "severity": "high"
                })
                print("  ⚠️ Service worker detected - potential caching interference")
            else:
                print("  ✅ No service worker detected")
                
        except Exception as e:
            self.results["service_worker"] = {"error": str(e)}
            
    def generate_cache_clearing_instructions(self):
        """Generate specific cache clearing instructions based on findings"""
        print("📋 Generating cache clearing instructions...")
        
        instructions = {
            "immediate_actions": [],
            "browser_specific": {},
            "developer_tools": [],
            "server_side": []
        }
        
        # Immediate actions based on findings
        if any(issue["type"] == "service_worker_detected" for issue in self.results["potential_issues"]):
            instructions["immediate_actions"].append({
                "action": "Clear service worker cache",
                "steps": [
                    "Open browser dev tools (F12)",
                    "Go to Application/Storage tab",
                    "Click 'Service Workers' in left sidebar",
                    "Click 'Unregister' for any service workers",
                    "Go to 'Cache Storage' and delete all caches"
                ]
            })
            
        if any(issue["type"] == "external_resource_failure" for issue in self.results["potential_issues"]):
            instructions["immediate_actions"].append({
                "action": "Check network connectivity",
                "steps": [
                    "Verify internet connection",
                    "Try accessing CDN URLs directly in browser",
                    "Check if corporate firewall is blocking CDN requests"
                ]
            })
            
        # Browser-specific instructions
        instructions["browser_specific"] = {
            "chrome": [
                "Press Ctrl+Shift+R (Windows/Linux) or Cmd+Shift+R (Mac) for hard refresh",
                "Or press F12 -> Network tab -> check 'Disable cache' -> refresh",
                "For deep clean: Settings -> Privacy and security -> Clear browsing data -> Cached images and files"
            ],
            "firefox": [
                "Press Ctrl+F5 (Windows/Linux) or Cmd+Shift+R (Mac) for hard refresh",
                "Or press F12 -> Network tab -> gear icon -> check 'Disable cache' -> refresh",
                "For deep clean: Settings -> Privacy & Security -> Cookies and Site Data -> Clear Data"
            ],
            "edge": [
                "Press Ctrl+Shift+R for hard refresh",
                "Or press F12 -> Network tab -> check 'Disable cache' -> refresh"
            ]
        }
        
        # Developer tools recommendations
        instructions["developer_tools"] = [
            "Enable 'Disable cache' in Network tab while dev tools are open",
            "Use 'Empty Cache and Hard Reload' option (right-click refresh button with dev tools open)",
            "Check Console tab for JavaScript errors during page load",
            "Monitor Network tab for failed resource requests (red entries)",
            "Use Application/Storage tab to clear all site data"
        ]
        
        # Server-side recommendations  
        if not any(file_info.get("cache_control_effective", False) for file_info in self.results["static_files"].values()):
            instructions["server_side"].append("Cache headers are properly configured for development")
        else:
            instructions["server_side"].append("Consider strengthening cache-busting headers")
            
        self.results["cache_clearing_instructions"] = instructions
        
    def create_automated_cache_cleaner(self):
        """Create an automated cache clearing script"""
        print("🔧 Creating automated cache cleaner...")
        
        cleaner_script = '''#!/usr/bin/env python3
"""
Automated Cache Cleaner for Browser Issues
Generated by Resource Loading Analyzer
"""

import os
import sys
import subprocess
import platform
from pathlib import Path

def clear_chrome_cache():
    """Clear Chrome cache for localhost"""
    system = platform.system()
    
    if system == "Windows":
        cache_paths = [
            os.path.expandvars(r"%LOCALAPPDATA%\\Google\\Chrome\\User Data\\Default\\Cache"),
            os.path.expandvars(r"%LOCALAPPDATA%\\Google\\Chrome\\User Data\\Default\\Code Cache"),
        ]
    elif system == "Linux":
        cache_paths = [
            os.path.expanduser("~/.cache/google-chrome/Default/Cache"),
            os.path.expanduser("~/.config/google-chrome/Default/Cache"),
        ]
    elif system == "Darwin":  # macOS
        cache_paths = [
            os.path.expanduser("~/Library/Caches/Google/Chrome/Default/Cache"),
        ]
    else:
        print(f"Unsupported system: {system}")
        return False
        
    for cache_path in cache_paths:
        if os.path.exists(cache_path):
            try:
                import shutil
                shutil.rmtree(cache_path)
                print(f"✅ Cleared: {cache_path}")
            except Exception as e:
                print(f"❌ Failed to clear {cache_path}: {e}")
                
    return True

def launch_browser_with_cache_disabled():
    """Launch browser with cache disabled"""
    system = platform.system()
    
    if system == "Windows":
        chrome_paths = [
            r"C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe",
            r"C:\\Program Files (x86)\\Google\\Chrome\\Application\\chrome.exe",
        ]
    elif system == "Linux":
        chrome_paths = [
            "/usr/bin/google-chrome",
            "/usr/bin/google-chrome-stable",
            "/usr/bin/chromium-browser",
        ]
    elif system == "Darwin":
        chrome_paths = [
            "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
        ]
    else:
        print(f"Unsupported system: {system}")
        return False
        
    chrome_exe = None
    for path in chrome_paths:
        if os.path.exists(path):
            chrome_exe = path
            break
            
    if not chrome_exe:
        print("❌ Chrome not found")
        return False
        
    args = [
        chrome_exe,
        "--disable-cache",
        "--disable-application-cache", 
        "--disable-offline-load-stale-cache",
        "--disk-cache-size=0",
        "--media-cache-size=0",
        "--aggressive-cache-discard",
        "http://localhost:5000"
    ]
    
    try:
        subprocess.Popen(args)
        print("✅ Chrome launched with cache disabled")
        return True
    except Exception as e:
        print(f"❌ Failed to launch Chrome: {e}")
        return False

if __name__ == "__main__":
    print("🧹 Automated Cache Cleaner")
    print("=" * 40)
    
    # Step 1: Clear cache
    print("📍 Clearing browser cache...")
    clear_chrome_cache()
    
    # Step 2: Launch browser
    print("📍 Launching browser with cache disabled...")
    launch_browser_with_cache_disabled()
    
    print("✅ Done! Check if the interface now works correctly.")
'''
        
        cleaner_path = Path(__file__).parent / "automated_cache_cleaner.py"
        cleaner_path.write_text(cleaner_script)
        
        # Make it executable on Unix-like systems
        if os.name != 'nt':
            os.chmod(cleaner_path, 0o755)
            
        print(f"✅ Created automated cache cleaner: {cleaner_path}")
        
        self.results["automated_cleaner"] = str(cleaner_path)
        
    def run_comprehensive_analysis(self):
        """Run all analysis components"""
        print("🚀 Starting comprehensive resource loading analysis...")
        print("=" * 60)
        
        self.analyze_server_status()
        self.analyze_static_files()
        self.analyze_external_resources()
        self.analyze_resource_loading_order()
        self.test_browser_cache_scenarios()
        self.detect_service_worker_issues()
        self.generate_cache_clearing_instructions()
        self.create_automated_cache_cleaner()
        
        return self.generate_report()
        
    def generate_report(self):
        """Generate comprehensive analysis report"""
        print("\n" + "=" * 60)
        print("📊 COMPREHENSIVE RESOURCE LOADING ANALYSIS REPORT")
        print("=" * 60)
        
        # Summary
        total_issues = len(self.results["potential_issues"])
        critical_issues = len([i for i in self.results["potential_issues"] if i.get("severity") == "critical"])
        high_issues = len([i for i in self.results["potential_issues"] if i.get("severity") == "high"])
        
        print(f"\n📈 SUMMARY:")
        print(f"  Total Issues Found: {total_issues}")
        print(f"  Critical: {critical_issues}, High: {high_issues}")
        print(f"  Server Status: {'✅ Running' if self.results['server_status'].get('running') else '❌ Down'}")
        print(f"  Static Files: {len([f for f in self.results['static_files'].values() if f.get('status_code') == 200])}/{len(self.results['static_files'])} OK")
        print(f"  External Resources: {len([r for r in self.results['external_resources'].values() if r.get('status_code') == 200])}/{len(self.results['external_resources'])} OK")
        
        # Issues breakdown
        if self.results["potential_issues"]:
            print(f"\n🚨 ISSUES FOUND:")
            for i, issue in enumerate(self.results["potential_issues"], 1):
                severity_icon = {"critical": "🔴", "high": "🟠", "medium": "🟡", "low": "🟢"}.get(issue.get("severity"), "⚪")
                print(f"  {i}. {severity_icon} {issue['type']}")
                if 'details' in issue:
                    print(f"     {issue['details']}")
                if 'recommendation' in issue:
                    print(f"     💡 {issue['recommendation']}")
        else:
            print(f"\n✅ NO CRITICAL ISSUES FOUND")
            
        # Recommendations
        print(f"\n💡 IMMEDIATE ACTIONS:")
        if critical_issues > 0:
            print("  1. 🔴 CRITICAL: Address critical issues immediately")
            print("  2. Run the automated cache cleaner script")
            print("  3. Test with browser dev tools cache disabled")
        elif high_issues > 0:
            print("  1. 🟠 HIGH: Clear browser cache completely")
            print("  2. Try different browser or incognito mode")
            print("  3. Check browser console for JavaScript errors")
        else:
            print("  1. ✅ System appears healthy")
            print("  2. Try hard refresh (Ctrl+Shift+R / Cmd+Shift+R)")
            print("  3. Clear browser cache as precaution")
            
        print(f"\n📋 NEXT STEPS:")
        print("  1. Use browser dev tools to monitor network requests")
        print("  2. Check browser console for JavaScript errors")
        print("  3. Test with cache disabled in dev tools")
        print("  4. Try the automated cache cleaner script")
        print("  5. Test with different browser or incognito mode")
        
        # Save detailed report
        report_path = Path(__file__).parent / f"resource_analysis_report_{int(time.time())}.json"
        with open(report_path, 'w') as f:
            json.dump(self.results, f, indent=2, default=str)
        print(f"\n📄 Detailed report saved: {report_path}")
        
        return self.results

def main():
    """Main entry point"""
    print("🔍 Resource Loading and Cache Analysis Tool")
    print("=" * 50)
    
    analyzer = ResourceLoadingAnalyzer()
    results = analyzer.run_comprehensive_analysis()
    
    print(f"\n🎯 Analysis complete. Check the detailed report for full results.")
    
    return results

if __name__ == "__main__":
    main()